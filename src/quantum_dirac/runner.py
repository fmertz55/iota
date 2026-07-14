"""Canonical registered stage runner for the quantum-Dirac experiment."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import flint
import mpmath
from flint import acb, acb_mat, arb
from mpmath import mp

from .authorization import RegisteredEvaluationPermit, validate_registered_permit
from .certified import (
    CertifiedRegisteredEvaluator,
    arb_exact,
    ball_precision,
    certified_input_basis,
    certified_spectral_norm_upper,
    embed_certified_target,
)
from .independent_registered import IndependentRegisteredEvaluator
from .independent_states import build_independent_state
from .metrics import decimal_leq, refinement_gate, spectral_norm_from_gram
from .production import _interval_value, _observation_steps
from .protocol import (
    ABSOLUTE_DISTANCE_THRESHOLDS,
    CONFIRMATION_SCENARIOS,
    CONFIRMATION_STATES,
    DEVELOPMENT_SCENARIOS,
    DEVELOPMENT_STATES,
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
    POSITION_TV_MAX,
    PRECISION_BITS,
    PRIMARY_LIBRARY_VERSION,
    PROTOCOL_VERSION,
    REFINEMENT_MARGIN,
    REFINEMENT_RATIO,
    REGISTERED_OBSERVATION_TIMES,
    REGISTERED_SIZES,
    SEARCH_ID,
    SPEC_DIR_REF,
    TARGET_R_CUTOFF,
    TIME_REVERSAL_FINE_MAX,
    TOTAL_CURRENT_ERROR_MAX,
    ZITTER_CURRENT_SUP_MAX,
)
from .reducers import (
    arb_lower_text,
    arb_upper_text,
    build_certified_state,
    mp_text,
    operator_gram_residual_upper,
    parity_ball,
    position_probabilities_ball,
    state_distance_upper,
    theta_ball,
    total_current_ball,
    witness_metrics_ball,
)
from .spec import QuantumDiracSpecError, load_json, parse_fraction


def _upper_gate(value: arb, threshold: str) -> tuple[str, bool]:
    """Classify exactly the canonical serialized outward upper enclosure."""

    text = arb_upper_text(value)
    return text, decimal_leq(text, threshold)


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _scenario_record(permit: RegisteredEvaluationPermit, scenario_id: str) -> dict[str, Any]:
    validate_registered_permit(permit)
    spec = load_json(permit.root / SPEC_DIR_REF / "scenarios.json")
    records = spec["development"] + spec["confirmation"]
    try:
        return next(record for record in records if record["id"] == scenario_id)
    except StopIteration as exc:
        raise QuantumDiracSpecError("registered scenario record is missing") from exc


def _target_tail(record: dict[str, Any]) -> arb:
    if not record["potential"]:
        return arb(0)
    lam = arb_exact("1/2")
    factorial = arb(1)
    for value in range(2, 62):
        factorial *= value
    return 2 * lam.exp() * lam**61 / factorial


def _tail_mp(record: dict[str, Any]):
    if not record["potential"]:
        return mp.mpf("0")
    lam = mp.mpf("0.5")
    return 2 * mp.exp(lam) * lam**61 / mp.factorial(61)


def _ball_max(values: list[arb]) -> arb:
    result = arb(0)
    for value in values:
        result = result.max(value)
    return result.upper()


def _matrix_state(columns: acb_mat, coefficients: acb_mat) -> acb_mat:
    return columns * coefficients


def _mp_matrix_state(columns: mp.matrix, coefficients: mp.matrix) -> mp.matrix:
    return columns * coefficients


def _interference_negative_control(
    evaluator: CertifiedRegisteredEvaluator,
    state_definition,
) -> dict[str, Any]:
    if len(state_definition.incoherent_components) != 2:
        return {"applicable": False, "maximum_position_entry_change_lower": None, "pass": True}
    basis = certified_input_basis(n_sites=evaluator.n_sites)
    coherent = basis * state_definition.coefficients
    first = basis * state_definition.incoherent_components[0]
    second = basis * state_definition.incoherent_components[1]
    coherent_probabilities = position_probabilities_ball(
        coherent, n_sites=evaluator.n_sites
    )
    first_probabilities = position_probabilities_ball(first, n_sites=evaluator.n_sites)
    second_probabilities = position_probabilities_ball(second, n_sites=evaluator.n_sites)
    maximum_lower = arb(0)
    for coherent_value, first_value, second_value in zip(
        coherent_probabilities, first_probabilities, second_probabilities
    ):
        mixture = (first_value + second_value) / 2
        lower = abs(coherent_value - mixture).lower()
        maximum_lower = maximum_lower.max(lower)
    lower_text = arb_lower_text(maximum_lower)
    passed = not decimal_leq(lower_text, "0")
    return {
        "applicable": True,
        "maximum_position_entry_change_lower": lower_text,
        "pass": passed,
    }


def _witness_records(
    permit: RegisteredEvaluationPermit,
    *,
    scenario_id: str,
    state_ids: tuple[str, ...],
    primary: CertifiedRegisteredEvaluator,
    independent: IndependentRegisteredEvaluator,
    primary_candidate_outputs: dict[int, acb_mat],
    primary_target_outputs: dict[int, acb_mat],
    independent_candidate_outputs: dict[int, mp.matrix],
    independent_target_outputs: dict[int, mp.matrix],
) -> tuple[list[dict[str, Any]], arb]:
    scenario = _scenario_record(permit, scenario_id)
    initial_mass = _interval_value(scenario["mass"], Fraction(0))
    observations = _observation_steps(primary.delta)
    records: list[dict[str, Any]] = []
    maximum_disagreement = arb(0)
    for state_id in state_ids:
        certified_state = build_certified_state(
            permit,
            state_id=state_id,
            initial_mass=initial_mass,
        )
        independent_state = build_independent_state(
            permit,
            state_id=state_id,
            initial_mass=initial_mass,
            dps=INDEPENDENT_DPS,
        )
        observation_records: list[dict[str, Any]] = []
        state_pass = True
        for time_text, step in zip(REGISTERED_OBSERVATION_TIMES, observations):
            candidate_state = _matrix_state(
                primary_candidate_outputs[step], certified_state.coefficients
            )
            # The target output supplied to this reducer is already embedded.
            target_state = _matrix_state(
                primary_target_outputs[step], certified_state.coefficients
            )
            independent_candidate_state = _mp_matrix_state(
                independent_candidate_outputs[step], independent_state.coefficients
            )
            independent_target_state = _mp_matrix_state(
                independent_target_outputs[step], independent_state.coefficients
            )
            metrics = witness_metrics_ball(
                candidate_state,
                target_state,
                n_sites=primary.n_sites,
            )
            candidate_disagreement = state_distance_upper(
                candidate_state, independent_candidate_state
            )
            target_disagreement = state_distance_upper(
                target_state, independent_target_state
            )
            disagreement = candidate_disagreement.max(target_disagreement).upper()
            maximum_disagreement = maximum_disagreement.max(disagreement)
            serialized_metrics = {
                key: arb_upper_text(value) for key, value in metrics.items()
            }
            disagreement_text = arb_upper_text(disagreement)
            thresholds = {
                "position_tv": ("position_tv_upper", POSITION_TV_MAX),
                "momentum_tv": ("momentum_tv_upper", MOMENTUM_TV_MAX),
                "total_current": (
                    "total_current_error_upper",
                    TOTAL_CURRENT_ERROR_MAX,
                ),
                "local_current": ("local_current_l1_upper", LOCAL_CURRENT_L1_MAX),
                "infidelity": ("infidelity_upper", INFIDELITY_MAX),
                "candidate_norm": (
                    "candidate_norm_residual_upper",
                    NUMERICAL_NORM_RESIDUAL_MAX,
                ),
                "target_norm": (
                    "target_norm_residual_upper",
                    NUMERICAL_NORM_RESIDUAL_MAX,
                ),
            }
            gates = {
                gate: decimal_leq(serialized_metrics[field], threshold)
                for gate, (field, threshold) in thresholds.items()
            }
            gates["independent_state_agreement"] = decimal_leq(
                disagreement_text, INDEPENDENT_STATE_DISAGREEMENT_MAX
            )
            passed = all(gates.values())
            state_pass &= passed
            observation_records.append(
                {
                    "time": time_text,
                    **serialized_metrics,
                    "independent_state_disagreement_upper": disagreement_text,
                    "gates": gates,
                    "pass": passed,
                }
            )
        zitter_series: list[dict[str, Any]] = []
        zitter_sup = arb(0)
        if state_id.endswith("ZITTER"):
            candidate_series = primary.candidate_state_series(
                scenario_id, certified_state.coefficients
            )
            target_series = primary.target_state_series(
                scenario_id, certified_state.coefficients
            )
            for step in sorted(candidate_series):
                candidate_current = total_current_ball(
                    candidate_series[step], n_sites=primary.n_sites
                )
                target_current = total_current_ball(
                    target_series[step], n_sites=2 * TARGET_R_CUTOFF + 1
                )
                error = abs(candidate_current - target_current).upper()
                zitter_sup = zitter_sup.max(error)
                zitter_series.append(
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
            zitter_text, zitter_pass = _upper_gate(
                zitter_sup, ZITTER_CURRENT_SUP_MAX
            )
            state_pass &= zitter_pass
        else:
            zitter_pass = True
        negative = _interference_negative_control(primary, certified_state)
        if state_id.endswith("INTERFERENCE"):
            state_pass &= negative["pass"]
        records.append(
            {
                "state_id": state_id,
                "observations": observation_records,
                "zitter_current_series": zitter_series,
                "zitter_sup_error_upper": (
                    zitter_text if zitter_series else None
                ),
                "zitter_pass": zitter_pass,
                "coherence_negative_fixture": negative,
                "pass": state_pass,
            }
        )
    return records, maximum_disagreement.upper()


def _resource_record(record: dict[str, Any], n_sites: int) -> dict[str, Any]:
    delta = Fraction(PHYSICAL_LENGTH, n_sites)
    steps = PHYSICAL_HORIZON / delta
    if steps.denominator != 1:
        raise QuantumDiracSpecError("resource macrostep count is not integral")
    active = 0
    for step in range(steps.numerator):
        time = step * delta
        for start, end, _, _ in record["potential"]:
            if parse_fraction(start) <= time < parse_fraction(end):
                active += 1
                break
    elementary_layers = 3 * steps.numerator + active
    return {
        "n_sites": n_sites,
        "macrosteps": steps.numerator,
        "active_potential_steps": active,
        "elementary_layers": elementary_layers,
        "gate_work": n_sites * elementary_layers,
        "occupation_modes": 2 * n_sites,
        "occupied_modes": 1,
        "local_hilbert_dimension": 4,
    }


def _symmetry_record(
    primary: CertifiedRegisteredEvaluator,
    scenario_id: str,
    candidate_outputs: dict[int, acb_mat],
    embedded_target_outputs: dict[int, acb_mat],
) -> dict[str, Any]:
    basis = certified_input_basis(n_sites=primary.n_sites)
    final = candidate_outputs[max(candidate_outputs)]
    parity_left = parity_ball(final, n_sites=primary.n_sites)
    parity_right = primary.candidate_final_from(
        scenario_id,
        parity_ball(basis, n_sites=primary.n_sites),
        reflected_potential=True,
    )
    parity_residual = certified_spectral_norm_upper(parity_left - parity_right).upper()
    theta_input = theta_ball(basis, n_sites=primary.n_sites)
    theta_forward = primary.candidate_final_from(scenario_id, theta_input)
    time_reversal_left = theta_ball(theta_forward, n_sites=primary.n_sites)
    time_reversal_right = primary.candidate_reversed_schedule_adjoint(scenario_id)
    time_reversal_residual = certified_spectral_norm_upper(
        time_reversal_left - time_reversal_right
    ).upper()
    norm_values: list[arb] = []
    for step in sorted(candidate_outputs):
        norm_values.append(operator_gram_residual_upper(candidate_outputs[step]))
        norm_values.append(operator_gram_residual_upper(embedded_target_outputs[step]))
    norm_residual = _ball_max(norm_values)
    parity_text, parity_pass = _upper_gate(
        parity_residual, PARITY_NUMERICAL_RESIDUAL_MAX
    )
    time_reversal_text = arb_upper_text(time_reversal_residual)
    norm_text, norm_pass = _upper_gate(
        norm_residual, NUMERICAL_NORM_RESIDUAL_MAX
    )
    return {
        "n_sites": primary.n_sites,
        "unitarity_abstract_exact": True,
        "causal_support_structural_exact": True,
        "massless_cone_boundaries_attained": True,
        "parity_abstract_exact": True,
        "parity_residual_upper": parity_text,
        "parity_pass": parity_pass,
        "time_reversal_domain": "registered_K_in",
        "time_reversal_residual_upper": time_reversal_text,
        "norm_residual_upper": norm_text,
        "norm_pass": norm_pass,
        "_time_reversal_text": time_reversal_text,
    }


def _scenario_result(
    permit: RegisteredEvaluationPermit,
    scenario_id: str,
    state_ids: tuple[str, ...],
) -> dict[str, Any]:
    scenario = _scenario_record(permit, scenario_id)
    tail = _target_tail(scenario)
    refinements: list[dict[str, Any]] = []
    symmetry_records: list[dict[str, Any]] = []
    finest_payload = None
    distance_maxima: list[str] = []
    tr_values: list[str] = []
    certified_contains_independent = True
    for n_sites in REGISTERED_SIZES:
        validate_registered_permit(permit)
        primary = CertifiedRegisteredEvaluator(permit, n_sites=n_sites)
        independent = IndependentRegisteredEvaluator(permit, n_sites=n_sites)
        primary_candidate = primary.candidate_outputs(scenario_id)
        primary_target_raw = primary.target_outputs(scenario_id)
        primary_target = {
            step: embed_certified_target(value, n_sites=n_sites)
            for step, value in primary_target_raw.items()
        }
        independent_candidate = independent.candidate_outputs(scenario_id)
        independent_target_raw = independent.target_outputs(scenario_id)
        independent_target = {
            step: independent.embed_target(value)
            for step, value in independent_target_raw.items()
        }
        observations: list[dict[str, Any]] = []
        distances: list[arb] = []
        with ball_precision():
            for time_text, step in zip(
                REGISTERED_OBSERVATION_TIMES, _observation_steps(primary.delta)
            ):
                raw_norm = certified_spectral_norm_upper(
                    primary_candidate[step] - primary_target[step]
                )
                distance = (raw_norm + tail).upper()
                distances.append(distance)
                with mp.workdps(INDEPENDENT_DPS):
                    independent_distance = spectral_norm_from_gram(
                        independent_candidate[step] - independent_target[step],
                        dps=INDEPENDENT_DPS,
                    ) + _tail_mp(scenario)
                raw_norm_text = arb_upper_text(raw_norm)
                tail_text = arb_upper_text(tail)
                distance_text = arb_upper_text(distance)
                independent_text = mp_text(independent_distance)
                contained = decimal_leq(independent_text, distance_text)
                certified_contains_independent &= contained
                observations.append(
                    {
                        "time": time_text,
                        "operator_norm_upper": raw_norm_text,
                        "target_tail_upper": tail_text,
                        "numeric_bound": "0",
                        "certified_distance_upper": distance_text,
                        "independent_distance": independent_text,
                        "certified_contains_independent": contained,
                    }
                )
        maximum = _ball_max(distances)
        maximum_text, absolute_pass = _upper_gate(
            maximum, ABSOLUTE_DISTANCE_THRESHOLDS[n_sites]
        )
        distance_maxima.append(maximum_text)
        absolute_threshold = ABSOLUTE_DISTANCE_THRESHOLDS[n_sites]
        symmetry = _symmetry_record(
            primary, scenario_id, primary_candidate, primary_target
        )
        tr_values.append(symmetry.pop("_time_reversal_text"))
        symmetry_records.append(symmetry)
        refinements.append(
            {
                "n_sites": n_sites,
                "delta": _fraction_text(Fraction(PHYSICAL_LENGTH, n_sites)),
                "observations": observations,
                "scenario_max_upper": maximum_text,
                "absolute_threshold": absolute_threshold,
                "absolute_pass": absolute_pass,
                "resources": _resource_record(scenario, n_sites),
            }
        )
        if n_sites == REGISTERED_SIZES[-1]:
            finest_payload = (
                primary,
                independent,
                primary_candidate,
                primary_target,
                independent_candidate,
                independent_target,
            )
    if finest_payload is None:
        raise QuantumDiracSpecError("finest registered refinement was not evaluated")
    distance_refinement_pass = refinement_gate(
        *distance_maxima,
        ratio=REFINEMENT_RATIO,
        margin=REFINEMENT_MARGIN,
    )
    tr_refinement_pass = refinement_gate(
        *tr_values,
        ratio=REFINEMENT_RATIO,
        margin=REFINEMENT_MARGIN,
    )
    tr_fine_pass = decimal_leq(tr_values[-1], TIME_REVERSAL_FINE_MAX)
    (
        primary,
        independent,
        primary_candidate,
        primary_target,
        independent_candidate,
        independent_target,
    ) = finest_payload
    witnesses, disagreement = _witness_records(
        permit,
        scenario_id=scenario_id,
        state_ids=state_ids,
        primary=primary,
        independent=independent,
        primary_candidate_outputs=primary_candidate,
        primary_target_outputs=primary_target,
        independent_candidate_outputs=independent_candidate,
        independent_target_outputs=independent_target,
    )
    disagreement_text, disagreement_pass = _upper_gate(
        disagreement, INDEPENDENT_STATE_DISAGREEMENT_MAX
    )
    structure_pass = (
        all(record["parity_pass"] and record["norm_pass"] for record in symmetry_records)
        and tr_fine_pass
        and tr_refinement_pass
        and disagreement_pass
    )
    operator_pass = (
        all(record["absolute_pass"] for record in refinements)
        and distance_refinement_pass
        and certified_contains_independent
    )
    witness_pass = all(record["pass"] for record in witnesses)
    return {
        "scenario_id": scenario_id,
        "operator": {
            "refinements": refinements,
            "refinement_pass": distance_refinement_pass,
            "certified_contains_independent": certified_contains_independent,
            "pass": operator_pass,
        },
        "witnesses": witnesses,
        "maximum_independent_state_disagreement_upper": disagreement_text,
        "symmetry_and_structure": {
            "refinements": symmetry_records,
            "time_reversal_refinement_pass": tr_refinement_pass,
            "time_reversal_fine_pass": tr_fine_pass,
            "pass": structure_pass,
        },
        "pass": operator_pass and witness_pass and structure_pass,
    }


def _free_block_distance(*, n_sites: int, r: int, mass: Fraction, horizon: Fraction):
    with mp.workdps(INDEPENDENT_DPS):
        delta = Fraction(PHYSICAL_LENGTH, n_sites)
        steps = horizon / delta
        if steps.denominator != 1:
            raise QuantumDiracSpecError("negative-control horizon is off-grid")
        angle = mp.mpf(delta.numerator) / delta.denominator
        momentum = 2 * mp.pi * r / PHYSICAL_LENGTH
        coin_angle = angle * _mp_mass(mass)
        coin = mp.matrix(
            [
                [mp.cos(coin_angle), -1j * mp.sin(coin_angle)],
                [-1j * mp.sin(coin_angle), mp.cos(coin_angle)],
            ]
        )
        shift = mp.matrix(
            [[mp.exp(-1j * angle * momentum), 0], [0, mp.exp(1j * angle * momentum)]]
        )
        candidate = (shift * coin) ** steps.numerator
        omega = mp.sqrt(momentum**2 + _mp_mass(mass) ** 2)
        hamiltonian = mp.matrix(
            [[momentum, _mp_mass(mass)], [_mp_mass(mass), -momentum]]
        )
        target = (
            mp.cos(omega * _mp_fraction(horizon)) * mp.eye(2)
            - 1j * mp.sin(omega * _mp_fraction(horizon)) * hamiltonian / omega
        )
        return spectral_norm_from_gram(candidate - target, dps=INDEPENDENT_DPS)


def _mp_fraction(value: Fraction):
    return mp.mpf(value.numerator) / value.denominator


def _mp_mass(value: Fraction):
    return _mp_fraction(value)


def _failure_controls() -> list[dict[str, Any]]:
    high_k = max(
        _free_block_distance(
            n_sites=256, r=r, mass=Fraction(1, 2), horizon=Fraction(2)
        )
        for r in (-48, 48)
    )
    high_mass = max(
        _free_block_distance(
            n_sites=256, r=r, mass=Fraction(8), horizon=Fraction(2)
        )
        for r in range(INPUT_R_MIN, INPUT_R_MAX + 1)
    )
    long_horizon = max(
        _free_block_distance(
            n_sites=256, r=r, mass=Fraction(1, 2), horizon=Fraction(16)
        )
        for r in range(INPUT_R_MIN, INPUT_R_MAX + 1)
    )
    return [
        {"id": "HIGH-K", "metric": "operator_distance", "value": mp_text(high_k)},
        {"id": "HIGH-MASS", "metric": "operator_distance", "value": mp_text(high_mass)},
        {"id": "LONG-HORIZON", "metric": "operator_distance", "value": mp_text(long_horizon)},
        {
            "id": "FINITE-RING",
            "metric": "massless_directional_recurrence_steps",
            "value": "256",
        },
        {
            "id": "DEPHASED",
            "metric": "coherence_removed_controls_reported_in_witness_records",
            "value": "true",
        },
    ]


def _confirmation_cross_witnesses(
    permit: RegisteredEvaluationPermit,
) -> dict[str, Any]:
    n_sites = REGISTERED_SIZES[-1]
    scenario_id = DEVELOPMENT_SCENARIOS[0]
    primary = CertifiedRegisteredEvaluator(permit, n_sites=n_sites)
    independent = IndependentRegisteredEvaluator(permit, n_sites=n_sites)
    primary_candidate = primary.candidate_outputs(scenario_id)
    primary_target = {
        step: embed_certified_target(value, n_sites=n_sites)
        for step, value in primary.target_outputs(scenario_id).items()
    }
    independent_candidate = independent.candidate_outputs(scenario_id)
    independent_target = {
        step: independent.embed_target(value)
        for step, value in independent.target_outputs(scenario_id).items()
    }
    witnesses, disagreement = _witness_records(
        permit,
        scenario_id=scenario_id,
        state_ids=CONFIRMATION_STATES,
        primary=primary,
        independent=independent,
        primary_candidate_outputs=primary_candidate,
        primary_target_outputs=primary_target,
        independent_candidate_outputs=independent_candidate,
        independent_target_outputs=independent_target,
    )
    disagreement_text, disagreement_pass = _upper_gate(
        disagreement, INDEPENDENT_STATE_DISAGREEMENT_MAX
    )
    passed = all(record["pass"] for record in witnesses) and disagreement_pass
    return {
        "scenario_id": scenario_id,
        "state_partition": "confirmation",
        "witnesses": witnesses,
        "maximum_independent_state_disagreement_upper": disagreement_text,
        "pass": passed,
    }


def build_stage_ledger(
    permit: RegisteredEvaluationPermit,
    *,
    bindings: dict[str, dict[str, str]],
) -> dict[str, Any]:
    validate_registered_permit(permit)
    if flint.__version__ != PRIMARY_LIBRARY_VERSION:
        raise QuantumDiracSpecError("python-flint runtime differs from the frozen version")
    if mpmath.__version__ != INDEPENDENT_LIBRARY_VERSION:
        raise QuantumDiracSpecError("mpmath runtime differs from the frozen version")
    scenario_ids = (
        DEVELOPMENT_SCENARIOS
        if permit.stage == "development"
        else CONFIRMATION_SCENARIOS
    )
    state_ids = DEVELOPMENT_STATES if permit.stage == "development" else CONFIRMATION_STATES
    scenario_results = [
        _scenario_result(permit, scenario_id, state_ids)
        for scenario_id in scenario_ids
    ]
    cross_witnesses = (
        None
        if permit.stage == "development"
        else _confirmation_cross_witnesses(permit)
    )
    stage_pass = all(record["pass"] for record in scenario_results) and (
        cross_witnesses is None or cross_witnesses["pass"]
    )
    if permit.stage == "development":
        status = (
            "development_passed"
            if stage_pass
            else "development_gate_failed_confirmation_unopened"
        )
        failure_controls: list[dict[str, Any]] = []
    else:
        status = (
            "constructive_sufficiency_passed_frozen_dirac_sector"
            if stage_pass
            else "development_passed_confirmation_failed"
        )
        failure_controls = _failure_controls() if stage_pass else []
    ledger = {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "stage": permit.stage,
        "status": status,
        "bindings": bindings,
        "numerics": {
            "primary_backend": "python-flint Arb/Acb",
            "primary_library_version": flint.__version__,
            "primary_precision_bits": PRECISION_BITS,
            "primary_rounding": "outward_ball_enclosures",
            "independent_backend": "mpmath",
            "independent_library_version": mpmath.__version__,
            "independent_decimal_digits": INDEPENDENT_DPS,
            "binary64_registered_dynamics": False,
            "target_tail_formula": "2*exp(1/2)*(1/2)^61/61! for potential scenarios",
        },
        "scenario_results": scenario_results,
        "aggregate": {
            "scenario_count": len(scenario_results),
            "scenario_pass_count": sum(record["pass"] for record in scenario_results),
            "all_scenarios_complete": True,
            "stage_pass": stage_pass,
            "confirmation_authorized": permit.stage == "development" and stage_pass,
            "development_free_light_holdout_witnesses": cross_witnesses,
            "failure_controls": failure_controls,
            "classification": status,
        },
    }
    from .ledger import validate_result_ledger

    validate_result_ledger(ledger, expected_stage=permit.stage)
    return ledger
