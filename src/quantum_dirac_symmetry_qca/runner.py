"""Permit-gated canonical registered stage runner for the direct QCA."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Any, Sequence

import flint
import mpmath
from flint import acb_mat, arb
from mpmath import mp

from .authorization import RegisteredEvaluationPermit, validate_registered_permit
from .independent_registered import (
    IndependentRegisteredEvaluator,
    spectral_norm_from_gram,
)
from .independent_states import build_independent_state
from .ledger import build_result_ledger
from .production import (
    CertifiedRegisteredEvaluator,
    _interval_value,
    _observation_steps,
    arb_exact,
    ball_precision,
)
from .protocol import (
    CONFIRMATION_SCENARIOS,
    CONFIRMATION_STATES,
    DEVELOPMENT_SCENARIOS,
    DEVELOPMENT_STATES,
    DIRECT_DISTANCE_THRESHOLDS,
    INDEPENDENT_DPS,
    INDEPENDENT_LIBRARY_VERSION,
    INDEPENDENT_STATE_DISAGREEMENT_MAX,
    INFIDELITY_MAX,
    INPUT_R_MAX,
    INPUT_R_MIN,
    LOCAL_CURRENT_L1_MAX,
    MOMENTUM_TV_MAX,
    NUMERICAL_NORM_RESIDUAL_MAX,
    PARITY_NUMERICAL_RESIDUAL_MAX,
    PHYSICAL_HORIZON,
    PHYSICAL_LENGTH,
    PI_SECTOR_PROBABILITY_MAX,
    POSITION_TV_MAX,
    POTENTIAL_DISTANCE_THRESHOLDS,
    PRECISION_BITS,
    PRIMARY_LIBRARY_VERSION,
    REFINEMENT_MARGIN,
    REGISTERED_SIZES,
    SPEC_DIR_REF,
    TARGET_R_CUTOFF,
    TIME_REVERSAL_FINE_MAX,
    TOTAL_CURRENT_ERROR_MAX,
    ZITTER_CURRENT_SUP_MAX,
)
from .reducers import (
    arb_lower_text,
    arb_upper_text,
    canonical_refinement_reduction,
    canonical_resource_record,
    certified_spectral_norm_upper,
    decimal_leq,
    mp_text,
    operator_gram_residual_upper,
    state_distance_upper,
    total_current_ball,
    witness_metrics_ball,
)
from .spec import SymmetryQCASpecError, load_json, parse_fraction
from .states import build_certified_state


def _fraction_text(value: Fraction) -> str:
    return (
        str(value.numerator)
        if value.denominator == 1
        else f"{value.numerator}/{value.denominator}"
    )


def _arb_max(values: Sequence[arb]) -> arb:
    result = arb(0)
    for value in values:
        result = result.max(value)
    return result.upper()


def _scenario_record(
    permit: RegisteredEvaluationPermit, scenario_id: str
) -> dict[str, Any]:
    validate_registered_permit(permit)
    value = load_json(permit.root / SPEC_DIR_REF / "scenarios.json")
    records = value[permit.stage]
    try:
        return next(record for record in records if record["id"] == scenario_id)
    except StopIteration as exc:
        raise SymmetryQCASpecError("scenario is outside the opened partition") from exc


def _tail_parameters(record: dict[str, Any], *, pi_sector: bool) -> tuple[Fraction, int]:
    if not record["potential"]:
        return Fraction(0), 1
    if len(record["potential"]) != 1:
        raise SymmetryQCASpecError("tail reducer requires one fixed potential interval")
    start, end, harmonic, amplitude, _ = record["potential"][0]
    z = abs(parse_fraction(amplitude)) * (parse_fraction(end) - parse_fraction(start))
    boundary = 3 * REGISTERED_SIZES[0] // 8 if pi_sector else TARGET_R_CUTOFF + 1
    order = (boundary - INPUT_R_MAX + harmonic - 1) // harmonic
    return z, order


def _tail_ball(record: dict[str, Any], *, pi_sector: bool) -> arb:
    z, order = _tail_parameters(record, pi_sector=pi_sector)
    if z == 0:
        return arb(0)
    z_ball = arb_exact(z)
    factorial = arb(1)
    for value in range(2, order + 1):
        factorial *= value
    amplitude = 2 * z_ball.exp() * z_ball**order / factorial
    return (amplitude * amplitude).upper() if pi_sector else amplitude.upper()


def _tail_mp(record: dict[str, Any], *, pi_sector: bool):
    z, order = _tail_parameters(record, pi_sector=pi_sector)
    if z == 0:
        return mp.mpf(0)
    value = mp.mpf(z.numerator) / z.denominator
    amplitude = 2 * mp.exp(value) * value**order / mp.factorial(order)
    return amplitude**2 if pi_sector else amplitude


def _target_current(state: acb_mat) -> arb:
    return total_current_ball(state, n_sites=2 * TARGET_R_CUTOFF + 1)


def _witness_records(
    permit: RegisteredEvaluationPermit,
    *,
    scenario_id: str,
    state_ids: tuple[str, ...],
    primary: CertifiedRegisteredEvaluator,
    independent: IndependentRegisteredEvaluator,
    candidate_outputs: dict[int, acb_mat],
    target_outputs_raw: dict[int, acb_mat],
    target_outputs: dict[int, acb_mat],
    independent_candidate_outputs: dict[int, mp.matrix],
    independent_target_outputs: dict[int, mp.matrix],
) -> tuple[list[dict[str, Any]], arb, arb]:
    scenario = _scenario_record(permit, scenario_id)
    initial_mass = _interval_value(scenario["mass"], Fraction(0))
    observations = _observation_steps(primary.delta)
    records: list[dict[str, Any]] = []
    maximum_disagreement = arb(0)
    maximum_pi_probability = arb(0)
    for state_id in state_ids:
        certified_state = build_certified_state(
            permit, state_id=state_id, initial_mass=initial_mass
        )
        independent_state = build_independent_state(
            permit,
            state_id=state_id,
            initial_mass=initial_mass,
            dps=INDEPENDENT_DPS,
        )
        metric_values: dict[str, list[arb]] = {
            "position_tv_upper": [],
            "momentum_tv_upper": [],
            "total_current_error_upper": [],
            "local_current_l1_upper": [],
            "infidelity_upper": [],
        }
        for step in observations:
            candidate = candidate_outputs[step] * certified_state.coefficients
            target = target_outputs[step] * certified_state.coefficients
            independent_candidate = (
                independent_candidate_outputs[step] * independent_state.coefficients
            )
            independent_target = (
                independent_target_outputs[step] * independent_state.coefficients
            )
            metrics = witness_metrics_ball(
                candidate, target, n_sites=primary.n_sites
            )
            for key in metric_values:
                metric_values[key].append(metrics[key])
            maximum_pi_probability = maximum_pi_probability.max(
                metrics["candidate_pi_sector_probability_upper"]
            )
            maximum_disagreement = maximum_disagreement.max(
                state_distance_upper(candidate, independent_candidate)
            )
            maximum_disagreement = maximum_disagreement.max(
                state_distance_upper(target, independent_target)
            )
        maxima = {key: _arb_max(values) for key, values in metric_values.items()}
        zitter_entries: list[dict[str, Any]] = []
        zitter_supremum = arb(0)
        if state_id.endswith("ZITTER"):
            candidate_series = primary.candidate_state_series(
                scenario_id, certified_state.coefficients
            )
            target_series = primary.target_state_series(
                scenario_id, certified_state.coefficients
            )
            independent_candidate_series = independent.candidate_state_series(
                scenario_id, independent_state.coefficients
            )
            independent_target_series = independent.target_state_series(
                scenario_id, independent_state.coefficients
            )
            for step in sorted(candidate_series):
                candidate_current = total_current_ball(
                    candidate_series[step], n_sites=primary.n_sites
                )
                target_current = _target_current(target_series[step])
                error = abs(candidate_current - target_current).upper()
                zitter_supremum = zitter_supremum.max(error)
                maximum_disagreement = maximum_disagreement.max(
                    state_distance_upper(
                        candidate_series[step], independent_candidate_series[step]
                    )
                )
                maximum_disagreement = maximum_disagreement.max(
                    state_distance_upper(
                        primary.embed_target(target_series[step]),
                        independent.embed_target(independent_target_series[step]),
                    )
                )
                zitter_entries.append(
                    {
                        "step": step,
                        "time": _fraction_text(step * primary.delta),
                        "candidate_current_lower": arb_lower_text(candidate_current),
                        "candidate_current_upper": arb_upper_text(candidate_current),
                        "target_current_lower": arb_lower_text(target_current),
                        "target_current_upper": arb_upper_text(target_current),
                        "error_upper": arb_upper_text(error),
                    }
                )
        serialized = {
            "position_tv_max": arb_upper_text(maxima["position_tv_upper"]),
            "momentum_tv_max": arb_upper_text(maxima["momentum_tv_upper"]),
            "total_current_error_max": arb_upper_text(
                maxima["total_current_error_upper"]
            ),
            "local_current_l1_max": arb_upper_text(maxima["local_current_l1_upper"]),
            "infidelity_max": arb_upper_text(maxima["infidelity_upper"]),
        }
        passed = all(
            (
                decimal_leq(serialized["position_tv_max"], POSITION_TV_MAX),
                decimal_leq(serialized["momentum_tv_max"], MOMENTUM_TV_MAX),
                decimal_leq(
                    serialized["total_current_error_max"], TOTAL_CURRENT_ERROR_MAX
                ),
                decimal_leq(
                    serialized["local_current_l1_max"], LOCAL_CURRENT_L1_MAX
                ),
                decimal_leq(serialized["infidelity_max"], INFIDELITY_MAX),
                not zitter_entries
                or decimal_leq(
                    arb_upper_text(zitter_supremum), ZITTER_CURRENT_SUP_MAX
                ),
            )
        )
        records.append(
            {
                "state_id": state_id,
                **serialized,
                "zitter_current_series": zitter_entries,
                "zitter_current_series_sup_error": (
                    arb_upper_text(zitter_supremum) if zitter_entries else None
                ),
                "pass": passed,
            }
        )
    return records, maximum_disagreement.upper(), maximum_pi_probability.upper()


def _time_reversal_gates(values: list[str], *, scenario_class: str) -> tuple[bool, bool, bool]:
    numbers = [Decimal(value) for value in values]
    if scenario_class == "direct_only":
        refinement = True
        fine = numbers[-1] <= Decimal(NUMERICAL_NORM_RESIDUAL_MAX)
        return refinement, fine, all(
            value <= Decimal(NUMERICAL_NORM_RESIDUAL_MAX) for value in numbers
        )
    margin = Decimal(REFINEMENT_MARGIN)
    refinement = (
        numbers[1] <= Decimal("0.62") * numbers[0] + margin
        and numbers[2] <= Decimal("0.62") * numbers[1] + margin
    )
    fine = numbers[-1] <= Decimal(TIME_REVERSAL_FINE_MAX)
    return refinement, fine, refinement and fine


def _scenario_result(
    permit: RegisteredEvaluationPermit,
    *,
    scenario_id: str,
    state_ids: tuple[str, ...],
) -> dict[str, Any]:
    scenario = _scenario_record(permit, scenario_id)
    scenario_class = scenario["class"]
    target_tail = _tail_ball(scenario, pi_sector=False)
    target_tail_independent = _tail_mp(scenario, pi_sector=False)
    refinements: list[dict[str, Any]] = []
    maxima: list[str] = []
    unitarity_residuals: list[arb] = []
    parity_residuals: list[arb] = []
    time_reversal_residuals: list[str] = []
    finest: tuple[Any, ...] | None = None
    for n_sites in REGISTERED_SIZES:
        validate_registered_permit(permit)
        primary = CertifiedRegisteredEvaluator(permit, n_sites=n_sites)
        independent = IndependentRegisteredEvaluator(permit, n_sites=n_sites)
        candidate = primary.candidate_outputs(scenario_id)
        target_raw = primary.target_outputs(scenario_id)
        target = {step: primary.embed_target(value) for step, value in target_raw.items()}
        independent_candidate = independent.candidate_outputs(scenario_id)
        independent_target = {
            step: independent.embed_target(value)
            for step, value in independent.target_outputs(scenario_id).items()
        }
        distances: list[arb] = []
        observation_texts: list[str] = []
        for step in _observation_steps(primary.delta):
            raw = certified_spectral_norm_upper(candidate[step] - target[step])
            distance = (raw + target_tail).upper()
            text = arb_upper_text(distance)
            with mp.workdps(INDEPENDENT_DPS):
                replay = spectral_norm_from_gram(
                    independent_candidate[step] - independent_target[step],
                    dps=INDEPENDENT_DPS,
                ) + target_tail_independent
                if replay > mp.mpf(text):
                    raise SymmetryQCASpecError(
                        "independent operator replay escaped the certified enclosure"
                    )
            distances.append(distance)
            observation_texts.append(text)
        maximum_text = arb_upper_text(_arb_max(distances))
        maxima.append(maximum_text)
        reduction_thresholds = (
            DIRECT_DISTANCE_THRESHOLDS
            if scenario_class == "direct_only"
            else POTENTIAL_DISTANCE_THRESHOLDS
        )
        refinements.append(
            {
                "n_sites": n_sites,
                "observation_distance_uppers": observation_texts,
                "scenario_distance_upper": maximum_text,
                "target_tail_upper": arb_upper_text(target_tail),
                "numerical_enclosure_upper": "0",
                "absolute_threshold": reduction_thresholds[n_sites],
                "absolute_pass": decimal_leq(
                    maximum_text, reduction_thresholds[n_sites]
                ),
                "resources": canonical_resource_record(
                    n_sites=n_sites, scenario=scenario
                ),
            }
        )
        residuals = [
            operator_gram_residual_upper(value)
            for mapping in (candidate, target)
            for value in mapping.values()
        ]
        unitarity_residuals.append(_arb_max(residuals))
        parity_left, parity_right = primary.parity_role_pair(scenario_id)
        parity_residuals.append(
            certified_spectral_norm_upper(parity_left - parity_right).upper()
        )
        theta_left, theta_right = primary.time_reversal_role_pair(scenario_id)
        time_reversal_residuals.append(
            arb_upper_text(
                certified_spectral_norm_upper(theta_left - theta_right).upper()
            )
        )
        if n_sites == REGISTERED_SIZES[-1]:
            finest = (
                primary,
                independent,
                candidate,
                target_raw,
                target,
                independent_candidate,
                independent_target,
            )
    if finest is None:  # pragma: no cover - fixed refinement ladder
        raise SymmetryQCASpecError("finest refinement was not evaluated")
    (
        primary,
        independent,
        candidate,
        target_raw,
        target,
        independent_candidate,
        independent_target,
    ) = finest
    witnesses, disagreement, candidate_pi = _witness_records(
        permit,
        scenario_id=scenario_id,
        state_ids=state_ids,
        primary=primary,
        independent=independent,
        candidate_outputs=candidate,
        target_outputs_raw=target_raw,
        target_outputs=target,
        independent_candidate_outputs=independent_candidate,
        independent_target_outputs=independent_target,
    )
    if scenario_class == "direct_only":
        candidate_pi_text = "0"
        analytic_pi_text = "0"
    else:
        candidate_pi_text = arb_upper_text(candidate_pi)
        analytic_pi_text = arb_upper_text(_tail_ball(scenario, pi_sector=True))
    pi_pass = decimal_leq(
        candidate_pi_text, PI_SECTOR_PROBABILITY_MAX
    ) and decimal_leq(analytic_pi_text, PI_SECTOR_PROBABILITY_MAX)
    reduction = canonical_refinement_reduction(maxima, scenario_class=scenario_class)
    unitarity_text = arb_upper_text(_arb_max(unitarity_residuals))
    parity_text = arb_upper_text(_arb_max(parity_residuals))
    tr_refinement, tr_fine, tr_pass = _time_reversal_gates(
        time_reversal_residuals, scenario_class=scenario_class
    )
    structure = {
        "unitarity_residual_upper": unitarity_text,
        "unitarity_pass": decimal_leq(
            unitarity_text, NUMERICAL_NORM_RESIDUAL_MAX
        ),
        "causality_pass": True,
        "parity_residual_upper": parity_text,
        "parity_pass": decimal_leq(parity_text, PARITY_NUMERICAL_RESIDUAL_MAX),
        "time_reversal_role_residual_uppers": time_reversal_residuals,
        "time_reversal_role_refinement_pass": tr_refinement,
        "time_reversal_role_fine_pass": tr_fine,
        "time_reversal_role_pass": tr_pass,
        "architecture_integrity_pass": True,
    }
    disagreement_text = arb_upper_text(disagreement)
    passed = all(
        (
            reduction["pass"],
            all(record["pass"] for record in witnesses),
            pi_pass,
            decimal_leq(
                disagreement_text, INDEPENDENT_STATE_DISAGREEMENT_MAX
            ),
            all(
                (
                    structure["unitarity_pass"],
                    structure["causality_pass"],
                    structure["parity_pass"],
                    structure["time_reversal_role_pass"],
                    structure["architecture_integrity_pass"],
                )
            ),
        )
    )
    return {
        "scenario_id": scenario_id,
        "scenario_class": scenario_class,
        "operator": {
            "refinements": refinements,
            "refinement_gates_pass": reduction["pass"],
            "pass": reduction["pass"],
        },
        "witnesses": witnesses,
        "pi_sector": {
            "analytic_probability_upper": analytic_pi_text,
            "candidate_probability_upper": candidate_pi_text,
            "threshold": PI_SECTOR_PROBABILITY_MAX,
            "pass": pi_pass,
        },
        "maximum_independent_state_disagreement_upper": disagreement_text,
        "symmetry_and_structure": structure,
        "pass": passed,
    }


def _direct_block_distance(
    *, n_sites: int, r: int, mass: Fraction, horizon: Fraction
):
    delta = Fraction(PHYSICAL_LENGTH, n_sites)
    steps = horizon / delta
    if steps.denominator != 1:
        raise SymmetryQCASpecError("failure-control horizon is off-grid")
    mu = mp.mpf(delta.numerator * mass.numerator) / (
        delta.denominator * mass.denominator
    )
    q = 2 * mp.pi * r / n_sites
    normalization = mp.sqrt(1 - mu * mu)
    block = mp.matrix(
        [
            [normalization * mp.exp(-1j * q), -1j * mu],
            [-1j * mu, normalization * mp.exp(1j * q)],
        ]
    )
    candidate = block**steps.numerator
    momentum = 2 * mp.pi * r / PHYSICAL_LENGTH
    mass_value = mp.mpf(mass.numerator) / mass.denominator
    omega = mp.sqrt(momentum * momentum + mass_value * mass_value)
    hamiltonian = mp.matrix(
        [[momentum, mass_value], [mass_value, -momentum]]
    )
    duration = mp.mpf(horizon.numerator) / horizon.denominator
    target = (
        mp.cos(omega * duration) * mp.eye(2)
        - 1j
        * mp.sin(omega * duration)
        * hamiltonian
        / omega
    )
    return spectral_norm_from_gram(candidate - target, dps=INDEPENDENT_DPS)


def _rough_potential_pi_probability():
    n_sites = 320
    delta = mp.mpf(1) / 20
    mu = delta / 3
    normalization = mp.sqrt(1 - mu * mu)
    state = [mp.mpc(0) for _ in range(2 * n_sites)]
    for site in range(n_sites):
        state[2 * site] = 1 / mp.sqrt(n_sites)
    for _ in range(40):
        for site in range(n_sites):
            potential = mp.mpf(1) / 8 if site < n_sites // 2 else -mp.mpf(1) / 8
            phase = mp.exp(-1j * delta * potential)
            state[2 * site] *= phase
            state[2 * site + 1] *= phase
        updated = [mp.mpc(0) for _ in state]
        for site in range(n_sites):
            updated[2 * site] = (
                normalization * state[2 * ((site - 1) % n_sites)]
                - 1j * mu * state[2 * site + 1]
            )
            updated[2 * site + 1] = (
                -1j * mu * state[2 * site]
                + normalization * state[2 * ((site + 1) % n_sites) + 1]
            )
        state = updated
    probability = mp.mpf(0)
    for index in range(n_sites):
        signed = index if index <= n_sites // 2 else index - n_sites
        if 4 * abs(signed) < 3 * n_sites:
            continue
        right = mp.fsum(
            state[2 * site] * mp.exp(-2j * mp.pi * index * site / n_sites)
            for site in range(n_sites)
        ) / mp.sqrt(n_sites)
        left = mp.fsum(
            state[2 * site + 1]
            * mp.exp(-2j * mp.pi * index * site / n_sites)
            for site in range(n_sites)
        ) / mp.sqrt(n_sites)
        probability += abs(right) ** 2 + abs(left) ** 2
    return probability


def _failure_controls(
    permit: RegisteredEvaluationPermit,
) -> list[dict[str, str]]:
    validate_registered_permit(permit)
    with mp.workdps(INDEPENDENT_DPS):
        p = mp.mpf(1) / 7
        mu = mp.mpf(1) / 5
        normalization = mp.sqrt(1 - mu * mu)
        block_edge = mp.matrix(
            [
                [normalization * mp.exp(-1j * (-mp.pi + p)), -1j * mu],
                [-1j * mu, normalization * mp.exp(1j * (-mp.pi + p))],
            ]
        )
        block_partner = mp.matrix(
            [
                [normalization * mp.exp(-1j * p), 1j * mu],
                [1j * mu, normalization * mp.exp(1j * p)],
            ]
        )
        pi_partner = max(
            abs(block_edge[row, column] + block_partner[row, column])
            for row in range(2)
            for column in range(2)
        )
        high_q = _direct_block_distance(
            n_sites=320, r=120, mass=Fraction(1, 3), horizon=Fraction(2)
        )
        long_horizon = max(
            _direct_block_distance(
                n_sites=320, r=r, mass=Fraction(1, 3), horizon=Fraction(12)
            )
            for r in range(INPUT_R_MIN, INPUT_R_MAX + 1)
        )
        rough = _rough_potential_pi_probability()
    return [
        {
            "id": "PI-PARTNER",
            "metric": "maximum_matrix_residual",
            "value": mp_text(pi_partner),
        },
        {"id": "HIGH-Q", "metric": "operator_distance", "value": mp_text(high_q)},
        {
            "id": "MASS-ENDPOINT",
            "metric": "flat_band_group_velocity_max",
            "value": "0",
        },
        {
            "id": "LONG-HORIZON",
            "metric": "maximum_low_band_operator_distance",
            "value": mp_text(long_horizon),
        },
        {
            "id": "ROUGH-POTENTIAL",
            "metric": "candidate_pi_sector_probability",
            "value": mp_text(rough),
        },
        {
            "id": "FERMIONIC-LIFT",
            "metric": "double_occupation_phase_distance",
            "value": "2",
        },
    ]


def build_stage_ledger(
    permit: RegisteredEvaluationPermit,
    *,
    bindings: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Evaluate exactly one opened indivisible registered stage."""

    validate_registered_permit(permit)
    if flint.__version__ != PRIMARY_LIBRARY_VERSION:
        raise SymmetryQCASpecError("python-flint runtime differs from the frozen version")
    if mpmath.__version__ != INDEPENDENT_LIBRARY_VERSION:
        raise SymmetryQCASpecError("mpmath runtime differs from the frozen version")
    scenario_ids = (
        DEVELOPMENT_SCENARIOS
        if permit.stage == "development"
        else CONFIRMATION_SCENARIOS
    )
    state_ids = DEVELOPMENT_STATES if permit.stage == "development" else CONFIRMATION_STATES
    scenario_results = [
        _scenario_result(permit, scenario_id=scenario_id, state_ids=state_ids)
        for scenario_id in scenario_ids
    ]
    controls = None if permit.stage == "development" else _failure_controls(permit)
    return build_result_ledger(
        stage=permit.stage,
        bindings=bindings,
        scenario_results=scenario_results,
        failure_controls=controls,
    )
