"""Algorithmically separate full-ledger replay from a clean result checkpoint."""

from __future__ import annotations

from fractions import Fraction
from math import isqrt
from typing import Any, Sequence

from mpmath import mp

from .authorization import RegisteredVerificationPermit, validate_verification_permit
from .independent_registered import (
    IndependentRegisteredEvaluator,
    _interval_value,
    _observation_steps,
    spectral_norm_from_gram,
)
from .independent_states import build_independent_state
from .ledger import FAILURE_CONTROL_IDS, validate_result_ledger
from .protocol import (
    CONFIRMATION_SCENARIOS,
    CONFIRMATION_STATES,
    DEVELOPMENT_SCENARIOS,
    DEVELOPMENT_STATES,
    INDEPENDENT_DPS,
    INPUT_R_MAX,
    INPUT_R_MIN,
    PHYSICAL_LENGTH,
    REGISTERED_SIZES,
    SPEC_DIR_REF,
    TARGET_R_CUTOFF,
)
from .spec import SymmetryQCASpecError, load_json, parse_fraction


def _number(value: str):
    try:
        result = mp.mpf(value)
    except (TypeError, ValueError) as exc:
        raise SymmetryQCASpecError("independent verifier found an invalid number") from exc
    if not mp.isfinite(result):
        raise SymmetryQCASpecError("independent verifier found a non-finite number")
    return result


def _require_enclosed(value: Any, claimed: str, label: str, *, allowance: Any = 0) -> None:
    if value > _number(claimed) + allowance:
        raise SymmetryQCASpecError(f"independent replay escaped {label} enclosure")


def _require_close_enclosure(
    value: Any, claimed: str, label: str, *, allowance: Any
) -> None:
    _require_enclosed(value, claimed, label, allowance=allowance)
    if _number(claimed) > value + allowance:
        raise SymmetryQCASpecError(f"{label} enclosure is not replay-tight")


def _smallest_factor(size: int) -> int:
    for factor in range(2, isqrt(size) + 1):
        if size % factor == 0:
            return factor
    return size


def _dft(values: Sequence[Any]) -> list[Any]:
    """Arbitrary-length negative-sign mixed-radix DFT at mpmath precision."""

    size = len(values)
    if size == 1:
        return [values[0]]
    factor = _smallest_factor(size)
    if factor == size:
        return [
            mp.fsum(
                values[source] * mp.exp(-2j * mp.pi * target * source / size)
                for source in range(size)
            )
            for target in range(size)
        ]
    quotient = size // factor
    subtransforms = [
        _dft([values[factor * index + offset] for index in range(quotient)])
        for offset in range(factor)
    ]
    return [
        mp.fsum(
            mp.exp(-2j * mp.pi * target * offset / size)
            * subtransforms[offset][target % quotient]
            for offset in range(factor)
        )
        for target in range(size)
    ]


def _probabilities(state: mp.matrix, n_sites: int) -> tuple[list[Any], list[Any]]:
    position = [
        abs(state[2 * site, 0]) ** 2 + abs(state[2 * site + 1, 0]) ** 2
        for site in range(n_sites)
    ]
    normalization = mp.sqrt(n_sites)
    right = _dft([state[2 * site, 0] for site in range(n_sites)])
    left = _dft([state[2 * site + 1, 0] for site in range(n_sites)])
    momentum = [
        (abs(right[index]) ** 2 + abs(left[index]) ** 2) / n_sites
        for index in range(n_sites)
    ]
    # Keep the normalization visible in the algorithmic derivation.
    if normalization <= 0:  # pragma: no cover - positive registered N
        raise SymmetryQCASpecError("independent DFT normalization is invalid")
    return position, momentum


def _current(state: mp.matrix, n_sites: int):
    return mp.fsum(
        abs(state[2 * site, 0]) ** 2 - abs(state[2 * site + 1, 0]) ** 2
        for site in range(n_sites)
    )


def _local_current(state: mp.matrix, n_sites: int) -> list[Any]:
    return [
        abs(state[2 * site, 0]) ** 2 - abs(state[2 * site + 1, 0]) ** 2
        for site in range(n_sites)
    ]


def _metrics(candidate: mp.matrix, target: mp.matrix, n_sites: int) -> dict[str, Any]:
    candidate_position, candidate_momentum = _probabilities(candidate, n_sites)
    target_position, target_momentum = _probabilities(target, n_sites)
    candidate_local = _local_current(candidate, n_sites)
    target_local = _local_current(target, n_sites)
    overlap = mp.fsum(
        mp.conj(candidate[row, 0]) * target[row, 0]
        for row in range(candidate.rows)
    )
    return {
        "position_tv_max": mp.fsum(
            abs(left - right)
            for left, right in zip(candidate_position, target_position)
        )
        / 2,
        "momentum_tv_max": mp.fsum(
            abs(left - right)
            for left, right in zip(candidate_momentum, target_momentum)
        )
        / 2,
        "total_current_error_max": abs(
            _current(candidate, n_sites) - _current(target, n_sites)
        ),
        "local_current_l1_max": mp.fsum(
            abs(left - right)
            for left, right in zip(candidate_local, target_local)
        ),
        "infidelity_max": max(mp.mpf(0), 1 - abs(overlap) ** 2),
    }


def _pi_probability(state: mp.matrix, n_sites: int):
    _, momentum = _probabilities(state, n_sites)
    return mp.fsum(
        probability
        for index, probability in enumerate(momentum)
        if 4 * abs(index if index <= n_sites // 2 else index - n_sites)
        >= 3 * n_sites
    )


def _scenario_record(
    permit: RegisteredVerificationPermit, scenario_id: str
) -> dict[str, Any]:
    validate_verification_permit(permit)
    records = load_json(permit.root / SPEC_DIR_REF / "scenarios.json")[permit.stage]
    try:
        return next(record for record in records if record["id"] == scenario_id)
    except StopIteration as exc:
        raise SymmetryQCASpecError("independent scenario is outside the stage") from exc


def _tail(record: dict[str, Any], *, pi_sector: bool):
    if not record["potential"]:
        return mp.mpf(0)
    start, end, harmonic, amplitude, _ = record["potential"][0]
    z_fraction = abs(parse_fraction(amplitude)) * (
        parse_fraction(end) - parse_fraction(start)
    )
    z = mp.mpf(z_fraction.numerator) / z_fraction.denominator
    boundary = 3 * REGISTERED_SIZES[0] // 8 if pi_sector else TARGET_R_CUTOFF + 1
    order = (boundary - INPUT_R_MAX + harmonic - 1) // harmonic
    amplitude_tail = 2 * mp.exp(z) * z**order / mp.factorial(order)
    return amplitude_tail**2 if pi_sector else amplitude_tail


def _gram_residual(columns: mp.matrix):
    gram = columns.H * columns - mp.eye(columns.cols)
    return spectral_norm_from_gram(gram, dps=INDEPENDENT_DPS)


def _verify_witnesses(
    permit: RegisteredVerificationPermit,
    *,
    scenario_id: str,
    state_ids: tuple[str, ...],
    claimed_result: dict[str, Any],
    evaluator: IndependentRegisteredEvaluator,
    candidate_outputs: dict[int, mp.matrix],
    target_outputs: dict[int, mp.matrix],
) -> None:
    n_sites = REGISTERED_SIZES[-1]
    scenario = _scenario_record(permit, scenario_id)
    initial_mass = _interval_value(scenario["mass"], Fraction(0))
    observations = _observation_steps(Fraction(PHYSICAL_LENGTH, n_sites))
    scenario_pi = mp.mpf(0)
    claimed_records = claimed_result["witnesses"]
    allowance = (
        10 * _number(claimed_result["maximum_independent_state_disagreement_upper"])
        + mp.mpf("1e-65")
    )
    for state_id, claimed in zip(state_ids, claimed_records):
        state = build_independent_state(
            permit,
            state_id=state_id,
            initial_mass=initial_mass,
            dps=INDEPENDENT_DPS,
        )
        maxima = {
            "position_tv_max": mp.mpf(0),
            "momentum_tv_max": mp.mpf(0),
            "total_current_error_max": mp.mpf(0),
            "local_current_l1_max": mp.mpf(0),
            "infidelity_max": mp.mpf(0),
        }
        for step in observations:
            candidate = candidate_outputs[step] * state.coefficients
            target = target_outputs[step] * state.coefficients
            replay = _metrics(candidate, target, n_sites)
            for key, value in replay.items():
                maxima[key] = max(maxima[key], value)
            scenario_pi = max(scenario_pi, _pi_probability(candidate, n_sites))
        for key, value in maxima.items():
            _require_close_enclosure(value, claimed[key], key, allowance=allowance)
        if state_id.endswith("ZITTER"):
            candidate_series = evaluator.candidate_state_series(
                scenario_id, state.coefficients
            )
            target_series = evaluator.target_state_series(
                scenario_id, state.coefficients
            )
            entries = claimed["zitter_current_series"]
            if len(entries) != len(candidate_series):
                raise SymmetryQCASpecError(
                    "independent Zitterbewegung series length mismatch"
                )
            errors = []
            for entry in entries:
                step = entry["step"]
                candidate_current = _current(candidate_series[step], n_sites)
                target_current = _current(
                    target_series[step], 2 * TARGET_R_CUTOFF + 1
                )
                if not (
                    _number(entry["candidate_current_lower"]) - allowance
                    <= candidate_current
                    <= _number(entry["candidate_current_upper"]) + allowance
                ):
                    raise SymmetryQCASpecError(
                        "independent candidate current escaped its interval"
                    )
                if not (
                    _number(entry["target_current_lower"]) - allowance
                    <= target_current
                    <= _number(entry["target_current_upper"]) + allowance
                ):
                    raise SymmetryQCASpecError(
                        "independent target current escaped its interval"
                    )
                errors.append(abs(candidate_current - target_current))
            _require_close_enclosure(
                max(errors),
                claimed["zitter_current_series_sup_error"],
                "Zitterbewegung supremum",
                allowance=allowance,
            )
    claimed_pi = claimed_result["pi_sector"]["candidate_probability_upper"]
    if scenario["class"] == "potential_split":
        _require_close_enclosure(
            scenario_pi,
            claimed_pi,
            "candidate pi-sector probability",
            allowance=mp.mpf("1e-65"),
        )


def _verify_structure(
    permit: RegisteredVerificationPermit,
    *,
    scenario_id: str,
    claimed: dict[str, Any],
    replays: dict[
        int,
        tuple[
            IndependentRegisteredEvaluator,
            dict[int, mp.matrix],
            dict[int, mp.matrix],
        ],
    ],
) -> None:
    unitarity = mp.mpf(0)
    parity = mp.mpf(0)
    time_reversal: list[Any] = []
    for n_sites in REGISTERED_SIZES:
        evaluator, candidate, target = replays[n_sites]
        unitarity = max(
            unitarity,
            *(_gram_residual(value) for value in candidate.values()),
            *(_gram_residual(value) for value in target.values()),
        )
        parity_left, parity_right = evaluator.parity_role_pair(scenario_id)
        parity = max(
            parity,
            spectral_norm_from_gram(
                parity_left - parity_right, dps=INDEPENDENT_DPS
            ),
        )
        theta_left, theta_right = evaluator.time_reversal_role_pair(scenario_id)
        time_reversal.append(
            spectral_norm_from_gram(
                theta_left - theta_right, dps=INDEPENDENT_DPS
            )
        )
    allowance = mp.mpf("1e-65")
    _require_close_enclosure(
        unitarity,
        claimed["unitarity_residual_upper"],
        "unitarity residual",
        allowance=allowance,
    )
    _require_close_enclosure(
        parity,
        claimed["parity_residual_upper"],
        "parity residual",
        allowance=allowance,
    )
    for value, enclosure in zip(
        time_reversal, claimed["time_reversal_role_residual_uppers"]
    ):
        _require_close_enclosure(
            value, enclosure, "time-reversal role residual", allowance=allowance
        )
    candidate_spec = load_json(permit.root / SPEC_DIR_REF / "candidate.json")
    if candidate_spec.get("gate_order") != [
        "scalar_phase_if_active",
        "edge_scatter",
        "on_site_swap",
    ]:
        raise SymmetryQCASpecError("independent architecture check found gate-order drift")


def _direct_block_distance(
    *, n_sites: int, r: int, mass: Fraction, horizon: Fraction
):
    delta = Fraction(PHYSICAL_LENGTH, n_sites)
    steps = horizon / delta
    mu = mp.mpf(delta.numerator * mass.numerator) / (
        delta.denominator * mass.denominator
    )
    q = 2 * mp.pi * r / n_sites
    normalization = mp.sqrt(1 - mu * mu)
    step = mp.matrix(
        [
            [normalization * mp.exp(-1j * q), -1j * mu],
            [-1j * mu, normalization * mp.exp(1j * q)],
        ]
    )
    candidate = step**steps.numerator
    momentum = 2 * mp.pi * r / PHYSICAL_LENGTH
    mass_value = mp.mpf(mass.numerator) / mass.denominator
    energy = mp.sqrt(momentum**2 + mass_value**2)
    generator = mp.matrix([[momentum, mass_value], [mass_value, -momentum]])
    duration = mp.mpf(horizon.numerator) / horizon.denominator
    target = (
        mp.cos(energy * duration) * mp.eye(2)
        - 1j * mp.sin(energy * duration) * generator / energy
    )
    return spectral_norm_from_gram(candidate - target, dps=INDEPENDENT_DPS)


def _rough_probability():
    size = 320
    delta = mp.mpf(1) / 20
    mu = delta / 3
    normalization = mp.sqrt(1 - mu**2)
    vector = [mp.mpc(0) for _ in range(2 * size)]
    for site in range(size):
        vector[2 * site] = 1 / mp.sqrt(size)
    for _ in range(40):
        phased = list(vector)
        for site in range(size):
            potential = mp.mpf(1) / 8 if site < size // 2 else -mp.mpf(1) / 8
            phase = mp.exp(-1j * delta * potential)
            phased[2 * site] *= phase
            phased[2 * site + 1] *= phase
        vector = [mp.mpc(0) for _ in vector]
        for site in range(size):
            vector[2 * site] = (
                normalization * phased[2 * ((site - 1) % size)]
                - 1j * mu * phased[2 * site + 1]
            )
            vector[2 * site + 1] = (
                -1j * mu * phased[2 * site]
                + normalization * phased[2 * ((site + 1) % size) + 1]
            )
    right = _dft([vector[2 * site] for site in range(size)])
    left = _dft([vector[2 * site + 1] for site in range(size)])
    return mp.fsum(
        (abs(right[index]) ** 2 + abs(left[index]) ** 2) / size
        for index in range(size)
        if 4 * abs(index if index <= size // 2 else index - size) >= 3 * size
    )


def _failure_control_values() -> list[Any]:
    p = mp.mpf(1) / 7
    mu = mp.mpf(1) / 5
    normalization = mp.sqrt(1 - mu**2)
    edge = mp.matrix(
        [
            [normalization * mp.exp(-1j * (-mp.pi + p)), -1j * mu],
            [-1j * mu, normalization * mp.exp(1j * (-mp.pi + p))],
        ]
    )
    partner = mp.matrix(
        [
            [normalization * mp.exp(-1j * p), 1j * mu],
            [1j * mu, normalization * mp.exp(1j * p)],
        ]
    )
    return [
        max(
            abs(edge[row, column] + partner[row, column])
            for row in range(2)
            for column in range(2)
        ),
        _direct_block_distance(
            n_sites=320, r=120, mass=Fraction(1, 3), horizon=Fraction(2)
        ),
        mp.mpf(0),
        max(
            _direct_block_distance(
                n_sites=320, r=r, mass=Fraction(1, 3), horizon=Fraction(12)
            )
            for r in range(INPUT_R_MIN, INPUT_R_MAX + 1)
        ),
        _rough_probability(),
        mp.mpf(2),
    ]


def verify_ledger_independently(
    permit: RegisteredVerificationPermit,
    ledger: dict[str, Any],
) -> None:
    """Replay every numerical family without importing a primary constructor."""

    validate_verification_permit(permit)
    validate_result_ledger(ledger, expected_stage=permit.stage)
    scenario_ids = (
        DEVELOPMENT_SCENARIOS
        if permit.stage == "development"
        else CONFIRMATION_SCENARIOS
    )
    state_ids = DEVELOPMENT_STATES if permit.stage == "development" else CONFIRMATION_STATES
    with mp.workdps(INDEPENDENT_DPS):
        for scenario_id, result in zip(scenario_ids, ledger["scenario_results"]):
            scenario = _scenario_record(permit, scenario_id)
            target_tail = _tail(scenario, pi_sector=False)
            analytic_pi = _tail(scenario, pi_sector=True)
            replays: dict[
                int,
                tuple[
                    IndependentRegisteredEvaluator,
                    dict[int, mp.matrix],
                    dict[int, mp.matrix],
                ],
            ] = {}
            for n_sites in REGISTERED_SIZES:
                evaluator = IndependentRegisteredEvaluator(permit, n_sites=n_sites)
                candidate = evaluator.candidate_outputs(scenario_id)
                target = {
                    step: evaluator.embed_target(value)
                    for step, value in evaluator.target_outputs(scenario_id).items()
                }
                replays[n_sites] = evaluator, candidate, target
            _require_close_enclosure(
                target_tail,
                result["operator"]["refinements"][0]["target_tail_upper"],
                "target tail",
                allowance=mp.mpf("1e-65"),
            )
            _require_close_enclosure(
                analytic_pi,
                result["pi_sector"]["analytic_probability_upper"],
                "analytic pi tail",
                allowance=mp.mpf("1e-65"),
            )
            for n_sites, refinement in zip(
                REGISTERED_SIZES, result["operator"]["refinements"]
            ):
                _, candidate, target = replays[n_sites]
                for step, enclosure in zip(
                    _observation_steps(Fraction(PHYSICAL_LENGTH, n_sites)),
                    refinement["observation_distance_uppers"],
                ):
                    distance = spectral_norm_from_gram(
                        candidate[step] - target[step], dps=INDEPENDENT_DPS
                    ) + target_tail
                    _require_close_enclosure(
                        distance,
                        enclosure,
                        "operator distance",
                        allowance=mp.mpf("1e-65"),
                    )
            _verify_witnesses(
                permit,
                scenario_id=scenario_id,
                state_ids=state_ids,
                claimed_result=result,
                evaluator=replays[REGISTERED_SIZES[-1]][0],
                candidate_outputs=replays[REGISTERED_SIZES[-1]][1],
                target_outputs=replays[REGISTERED_SIZES[-1]][2],
            )
            _verify_structure(
                permit,
                scenario_id=scenario_id,
                claimed=result["symmetry_and_structure"],
                replays=replays,
            )
        if permit.stage == "confirmation":
            controls = ledger["aggregate"]["failure_controls"]
            if tuple(item["id"] for item in controls) != FAILURE_CONTROL_IDS:
                raise SymmetryQCASpecError("independent failure-control order mismatch")
            for claimed, replay in zip(controls, _failure_control_values()):
                if abs(_number(claimed["value"]) - replay) > mp.mpf("1e-65"):
                    raise SymmetryQCASpecError(
                        "independent failure-control replay differs from the ledger"
                    )
