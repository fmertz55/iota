"""Clean-checkpoint independent replay of a committed result ledger."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Sequence

from mpmath import mp

from .authorization import RegisteredVerificationPermit, validate_verification_permit
from .independent_registered import (
    IndependentRegisteredEvaluator,
    _interval_value,
    _observation_steps,
)
from .independent_states import build_independent_state
from .ledger import validate_result_ledger
from .metrics import spectral_norm_from_gram, total_variation
from .protocol import (
    CONFIRMATION_SCENARIOS,
    CONFIRMATION_STATES,
    DEVELOPMENT_SCENARIOS,
    DEVELOPMENT_STATES,
    INDEPENDENT_DPS,
    PHYSICAL_LENGTH,
    REGISTERED_OBSERVATION_TIMES,
    REGISTERED_SIZES,
    SPEC_DIR_REF,
    TARGET_R_CUTOFF,
)
from .spec import QuantumDiracSpecError, load_json


def _number(value: str):
    result = mp.mpf(value)
    if not mp.isfinite(result):
        raise QuantumDiracSpecError("independent verifier found a non-finite number")
    return result


def _close(left, right, *, tolerance="1e-75") -> bool:
    return abs(mp.mpf(left) - mp.mpf(right)) <= mp.mpf(tolerance)


def _fft(values: list[Any]) -> list[Any]:
    size = len(values)
    result = list(values)
    target = 0
    for source in range(1, size):
        bit = size >> 1
        while target & bit:
            target ^= bit
            bit >>= 1
        target ^= bit
        if source < target:
            result[source], result[target] = result[target], result[source]
    length = 2
    while length <= size:
        root = mp.exp(-2j * mp.pi / length)
        half = length // 2
        for start in range(0, size, length):
            twiddle = mp.mpc(1)
            for offset in range(half):
                even = result[start + offset]
                odd = twiddle * result[start + offset + half]
                result[start + offset] = even + odd
                result[start + offset + half] = even - odd
                twiddle *= root
        length *= 2
    normalization = mp.sqrt(size)
    return [value / normalization for value in result]


def _probabilities(state: mp.matrix, n_sites: int) -> tuple[list[Any], list[Any]]:
    position = [
        abs(state[2 * site, 0]) ** 2 + abs(state[2 * site + 1, 0]) ** 2
        for site in range(n_sites)
    ]
    right = _fft([state[2 * site, 0] for site in range(n_sites)])
    left = _fft([state[2 * site + 1, 0] for site in range(n_sites)])
    momentum = [abs(right[index]) ** 2 + abs(left[index]) ** 2 for index in range(n_sites)]
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


def _norm_residual(state: mp.matrix):
    return abs(mp.fsum(abs(state[row, 0]) ** 2 for row in range(state.rows)) - 1)


def _fidelity(left: mp.matrix, right: mp.matrix):
    overlap = mp.fsum(mp.conj(left[row, 0]) * right[row, 0] for row in range(left.rows))
    return abs(overlap) ** 2


def _metrics(candidate: mp.matrix, target: mp.matrix, n_sites: int) -> dict[str, Any]:
    candidate_position, candidate_momentum = _probabilities(candidate, n_sites)
    target_position, target_momentum = _probabilities(target, n_sites)
    return {
        "position_tv_upper": total_variation(candidate_position, target_position),
        "momentum_tv_upper": total_variation(candidate_momentum, target_momentum),
        "total_current_error_upper": abs(
            _current(candidate, n_sites) - _current(target, n_sites)
        ),
        "local_current_l1_upper": mp.fsum(
            abs(left - right)
            for left, right in zip(
                _local_current(candidate, n_sites), _local_current(target, n_sites)
            )
        ),
        "infidelity_upper": max(mp.mpf("0"), 1 - _fidelity(candidate, target)),
        "candidate_norm_residual_upper": _norm_residual(candidate),
        "target_norm_residual_upper": _norm_residual(target),
    }


def _scenario_record(permit: RegisteredVerificationPermit, scenario_id: str) -> dict[str, Any]:
    spec = load_json(permit.root / SPEC_DIR_REF / "scenarios.json")
    return next(
        record
        for record in spec["development"] + spec["confirmation"]
        if record["id"] == scenario_id
    )


def _tail(record: dict[str, Any]):
    if not record["potential"]:
        return mp.mpf("0")
    return 2 * mp.exp(mp.mpf("0.5")) * mp.mpf("0.5") ** 61 / mp.factorial(61)


def _verify_witnesses(
    permit: RegisteredVerificationPermit,
    *,
    scenario_id: str,
    state_ids: tuple[str, ...],
    ledger_records: Sequence[dict[str, Any]],
) -> None:
    n_sites = REGISTERED_SIZES[-1]
    evaluator = IndependentRegisteredEvaluator(permit, n_sites=n_sites)
    candidate_outputs = evaluator.candidate_outputs(scenario_id)
    target_outputs = {
        step: evaluator.embed_target(value)
        for step, value in evaluator.target_outputs(scenario_id).items()
    }
    scenario = _scenario_record(permit, scenario_id)
    initial_mass = _interval_value(scenario["mass"], Fraction(0))
    observation_steps = _observation_steps(Fraction(PHYSICAL_LENGTH, n_sites))
    for state_id, claimed in zip(state_ids, ledger_records):
        state = build_independent_state(
            permit,
            state_id=state_id,
            initial_mass=initial_mass,
            dps=INDEPENDENT_DPS,
        )
        allowance = 4 * _number(
            max(
                (
                    item["independent_state_disagreement_upper"]
                    for item in claimed["observations"]
                ),
                key=_number,
            )
        ) + mp.mpf("1e-70")
        for step, observation in zip(observation_steps, claimed["observations"]):
            candidate = candidate_outputs[step] * state.coefficients
            target = target_outputs[step] * state.coefficients
            replay = _metrics(candidate, target, n_sites)
            for field, value in replay.items():
                if value > _number(observation[field]) + allowance:
                    raise QuantumDiracSpecError(
                        f"independent witness replay exceeds {field} enclosure"
                    )
        if state_id.endswith("ZITTER"):
            candidate_series = evaluator.candidate_state_series(
                scenario_id, state.coefficients
            )
            target_series = evaluator.target_state_series(scenario_id, state.coefficients)
            if len(claimed["zitter_current_series"]) != len(candidate_series):
                raise QuantumDiracSpecError("independent Zitterbewegung series length mismatch")
            for entry in claimed["zitter_current_series"]:
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
                    raise QuantumDiracSpecError("independent candidate-current replay escaped enclosure")
                if not (
                    _number(entry["target_current_lower"]) - allowance
                    <= target_current
                    <= _number(entry["target_current_upper"]) + allowance
                ):
                    raise QuantumDiracSpecError("independent target-current replay escaped enclosure")


def verify_ledger_independently(
    permit: RegisteredVerificationPermit,
    ledger: dict[str, Any],
) -> None:
    validate_verification_permit(permit)
    validate_result_ledger(ledger, expected_stage=permit.stage)
    scenario_ids = (
        DEVELOPMENT_SCENARIOS
        if permit.stage == "development"
        else CONFIRMATION_SCENARIOS
    )
    state_ids = DEVELOPMENT_STATES if permit.stage == "development" else CONFIRMATION_STATES
    with mp.workdps(INDEPENDENT_DPS):
        for scenario_id, scenario_result in zip(scenario_ids, ledger["scenario_results"]):
            scenario = _scenario_record(permit, scenario_id)
            tail = _tail(scenario)
            for n_sites, refinement in zip(
                REGISTERED_SIZES, scenario_result["operator"]["refinements"]
            ):
                evaluator = IndependentRegisteredEvaluator(permit, n_sites=n_sites)
                candidate = evaluator.candidate_outputs(scenario_id)
                target = {
                    step: evaluator.embed_target(value)
                    for step, value in evaluator.target_outputs(scenario_id).items()
                }
                steps = _observation_steps(Fraction(PHYSICAL_LENGTH, n_sites))
                for step, observation in zip(steps, refinement["observations"]):
                    distance = spectral_norm_from_gram(
                        candidate[step] - target[step], dps=INDEPENDENT_DPS
                    ) + tail
                    if not _close(distance, observation["independent_distance"]):
                        raise QuantumDiracSpecError(
                            "independent operator replay differs from the committed ledger"
                        )
            _verify_witnesses(
                permit,
                scenario_id=scenario_id,
                state_ids=state_ids,
                ledger_records=scenario_result["witnesses"],
            )
        cross = ledger["aggregate"]["development_free_light_holdout_witnesses"]
        if permit.stage == "confirmation":
            _verify_witnesses(
                permit,
                scenario_id=DEVELOPMENT_SCENARIOS[0],
                state_ids=CONFIRMATION_STATES,
                ledger_records=cross["witnesses"],
            )
