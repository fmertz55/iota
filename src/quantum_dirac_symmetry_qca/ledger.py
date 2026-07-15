"""Strict canonical result ledgers and atomic exactly-once persistence.

The registered evaluator is intentionally absent from this module.  It accepts
only already-reduced records, derives every aggregate classification itself,
and refuses malformed or self-inconsistent scientific claims before bytes can
be written.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from typing import Any, Sequence

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
    PROTOCOL_VERSION,
    REFINEMENT_MARGIN,
    REGISTERED_SIZES,
    SEARCH_ID,
    TIME_REVERSAL_FINE_MAX,
    TOTAL_CURRENT_ERROR_MAX,
    ZITTER_CURRENT_SUP_MAX,
)
from .spec import SymmetryQCASpecError, write_canonical_json_once


LEDGER_KEYS = {
    "protocol_version",
    "search_id",
    "stage",
    "status",
    "bindings",
    "numerics",
    "scenario_results",
    "aggregate",
}

BINDING_KEYS = {
    "open_manifest",
    "outcome_seal",
    "result_schema",
    "contract",
    "protocol",
    "candidate",
    "target",
    "maps",
    "scenarios",
    "states",
    "partitions",
}

SCENARIO_CLASSES = {
    "DEV-DIRECT-FREE-POS": "direct_only",
    "DEV-DIRECT-FREE-NEG": "direct_only",
    "DEV-DIRECT-SIGN-QUENCH": "direct_only",
    "DEV-DIRECT-POTENTIAL-H2": "potential_split",
    "HOLDOUT-DIRECT-MASS-PULSE": "direct_only",
    "HOLDOUT-DIRECT-POTENTIAL-H3": "potential_split",
}

POTENTIAL_ACTIVE_STEPS = {
    "DEV-DIRECT-POTENTIAL-H2": {320: 20, 640: 40, 1280: 80},
    "HOLDOUT-DIRECT-POTENTIAL-H3": {320: 24, 640: 48, 1280: 96},
}

FAILURE_CONTROL_IDS = (
    "PI-PARTNER",
    "HIGH-Q",
    "MASS-ENDPOINT",
    "LONG-HORIZON",
    "ROUGH-POTENTIAL",
    "FERMIONIC-LIFT",
)

FAILURE_CONTROL_METRICS = {
    "PI-PARTNER": "maximum_matrix_residual",
    "HIGH-Q": "operator_distance",
    "MASS-ENDPOINT": "flat_band_group_velocity_max",
    "LONG-HORIZON": "maximum_low_band_operator_distance",
    "ROUGH-POTENTIAL": "candidate_pi_sector_probability",
    "FERMIONIC-LIFT": "double_occupation_phase_distance",
}


def _refinement_reduction(
    maxima: Sequence[Decimal], *, scenario_class: str
) -> dict[str, Any]:
    if len(maxima) != 3:
        raise SymmetryQCASpecError("refinement reducer requires three maxima")
    if scenario_class == "direct_only":
        thresholds = DIRECT_DISTANCE_THRESHOLDS
        ratio = Decimal("0.35")
    elif scenario_class == "potential_split":
        thresholds = POTENTIAL_DISTANCE_THRESHOLDS
        ratio = Decimal("0.62")
    else:  # pragma: no cover - fixed scenario map
        raise SymmetryQCASpecError("unknown scenario class")
    absolute = [
        value <= Decimal(thresholds[size])
        for size, value in zip(REGISTERED_SIZES, maxima)
    ]
    near_zero = all(value <= Decimal("1e-12") for value in maxima)
    margin = Decimal(REFINEMENT_MARGIN)
    successive = [
        near_zero or maxima[1] <= ratio * maxima[0] + margin,
        near_zero or maxima[2] <= ratio * maxima[1] + margin,
    ]
    return {"pass": all(absolute) and all(successive)}


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise SymmetryQCASpecError(f"{label} has missing or unexpected fields")
    return value


def _number(value: Any, label: str, *, nonnegative: bool = True) -> Decimal:
    if type(value) is not str or not value:
        raise SymmetryQCASpecError(f"{label} must be a decimal string")
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise SymmetryQCASpecError(f"{label} is not a finite decimal") from exc
    if not result.is_finite() or nonnegative and result < 0:
        raise SymmetryQCASpecError(f"{label} is outside its finite domain")
    return result


def _binding(value: Any, label: str) -> None:
    record = _exact(value, {"path", "sha256"}, label)
    if type(record["path"]) is not str or not record["path"]:
        raise SymmetryQCASpecError(f"{label} path is invalid")
    digest = record["sha256"]
    if (
        type(digest) is not str
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise SymmetryQCASpecError(f"{label} digest is invalid")


def _fraction_text(value: Fraction) -> str:
    return (
        str(value.numerator)
        if value.denominator == 1
        else f"{value.numerator}/{value.denominator}"
    )


def _validate_resources(
    value: Any, *, scenario_id: str, n_sites: int
) -> None:
    record = _exact(
        value,
        {
            "n_sites",
            "macrosteps",
            "active_potential_steps",
            "elementary_layers",
            "gate_work",
            "occupation_qubits",
            "ancillas",
            "causal_radius_per_macrostep",
        },
        "resource record",
    )
    macrosteps = n_sites * PHYSICAL_HORIZON // PHYSICAL_LENGTH
    active = POTENTIAL_ACTIVE_STEPS.get(scenario_id, {}).get(n_sites, 0)
    expected = {
        "n_sites": n_sites,
        "macrosteps": macrosteps,
        "active_potential_steps": active,
        "elementary_layers": 2 * macrosteps + active,
        "gate_work": n_sites * (2 * macrosteps + active),
        "occupation_qubits": 2 * n_sites,
        "ancillas": 0,
        "causal_radius_per_macrostep": 1,
    }
    if record != expected:
        raise SymmetryQCASpecError("resource accounting differs from the frozen clock")


def _validate_refinement(
    value: Any,
    *,
    scenario_id: str,
    scenario_class: str,
    n_sites: int,
) -> Decimal:
    record = _exact(
        value,
        {
            "n_sites",
            "observation_distance_uppers",
            "scenario_distance_upper",
            "target_tail_upper",
            "numerical_enclosure_upper",
            "absolute_threshold",
            "absolute_pass",
            "resources",
        },
        "operator refinement",
    )
    if record["n_sites"] != n_sites:
        raise SymmetryQCASpecError("operator refinement size order mismatch")
    observations = record["observation_distance_uppers"]
    if type(observations) is not list or len(observations) != 5:
        raise SymmetryQCASpecError("operator refinement must contain five observations")
    values = [
        _number(item, "operator observation distance") for item in observations
    ]
    maximum = _number(record["scenario_distance_upper"], "scenario distance")
    if maximum != max(values):
        raise SymmetryQCASpecError("scenario distance is not the canonical observation maximum")
    _number(record["target_tail_upper"], "target tail")
    numerical = _number(
        record["numerical_enclosure_upper"], "numerical enclosure"
    )
    if numerical > Decimal("1e-10"):
        raise SymmetryQCASpecError("numerical enclosure exceeds its fixed budget")
    thresholds = (
        DIRECT_DISTANCE_THRESHOLDS
        if scenario_class == "direct_only"
        else POTENTIAL_DISTANCE_THRESHOLDS
    )
    threshold = thresholds[n_sites]
    if record["absolute_threshold"] != threshold:
        raise SymmetryQCASpecError("operator absolute threshold mismatch")
    expected_pass = maximum <= Decimal(threshold)
    if record["absolute_pass"] is not expected_pass:
        raise SymmetryQCASpecError("operator absolute classification mismatch")
    _validate_resources(record["resources"], scenario_id=scenario_id, n_sites=n_sites)
    return maximum


def _validate_zitter_series(value: Any, *, required: bool) -> Decimal | None:
    if type(value) is not list:
        raise SymmetryQCASpecError("Zitterbewegung series must be an array")
    if not required:
        if value:
            raise SymmetryQCASpecError("non-Zitterbewegung witness contains a series")
        return None
    macrosteps = REGISTERED_SIZES[-1] * PHYSICAL_HORIZON // PHYSICAL_LENGTH
    if len(value) != macrosteps:
        raise SymmetryQCASpecError("Zitterbewegung series is incomplete")
    maximum = Decimal(0)
    delta = Fraction(PHYSICAL_LENGTH, REGISTERED_SIZES[-1])
    for step, item in enumerate(value, start=1):
        entry = _exact(
            item,
            {
                "step",
                "time",
                "candidate_current_lower",
                "candidate_current_upper",
                "target_current_lower",
                "target_current_upper",
                "error_upper",
            },
            "Zitterbewegung entry",
        )
        if entry["step"] != step or entry["time"] != _fraction_text(step * delta):
            raise SymmetryQCASpecError("Zitterbewegung step or time order mismatch")
        candidate_lower = _number(
            entry["candidate_current_lower"],
            "candidate current lower",
            nonnegative=False,
        )
        candidate_upper = _number(
            entry["candidate_current_upper"],
            "candidate current upper",
            nonnegative=False,
        )
        target_lower = _number(
            entry["target_current_lower"], "target current lower", nonnegative=False
        )
        target_upper = _number(
            entry["target_current_upper"], "target current upper", nonnegative=False
        )
        if candidate_lower > candidate_upper or target_lower > target_upper:
            raise SymmetryQCASpecError("Zitterbewegung current interval is reversed")
        maximum = max(maximum, _number(entry["error_upper"], "current error"))
    return maximum


def _validate_witness(value: Any, *, state_id: str) -> bool:
    record = _exact(
        value,
        {
            "state_id",
            "position_tv_max",
            "momentum_tv_max",
            "total_current_error_max",
            "local_current_l1_max",
            "infidelity_max",
            "zitter_current_series",
            "zitter_current_series_sup_error",
            "pass",
        },
        "witness record",
    )
    if record["state_id"] != state_id:
        raise SymmetryQCASpecError("witness state order mismatch")
    checks = (
        _number(record["position_tv_max"], "position TV")
        <= Decimal(POSITION_TV_MAX),
        _number(record["momentum_tv_max"], "momentum TV")
        <= Decimal(MOMENTUM_TV_MAX),
        _number(record["total_current_error_max"], "total current error")
        <= Decimal(TOTAL_CURRENT_ERROR_MAX),
        _number(record["local_current_l1_max"], "local current L1")
        <= Decimal(LOCAL_CURRENT_L1_MAX),
        _number(record["infidelity_max"], "infidelity") <= Decimal(INFIDELITY_MAX),
    )
    required = state_id.endswith("ZITTER")
    series_maximum = _validate_zitter_series(
        record["zitter_current_series"], required=required
    )
    if required:
        supremum = _number(
            record["zitter_current_series_sup_error"], "Zitterbewegung supremum"
        )
        if supremum != series_maximum:
            raise SymmetryQCASpecError(
                "Zitterbewegung supremum is not the canonical series maximum"
            )
        zitter_pass = supremum <= Decimal(ZITTER_CURRENT_SUP_MAX)
    else:
        if record["zitter_current_series_sup_error"] is not None:
            raise SymmetryQCASpecError(
                "non-Zitterbewegung witness contains a supremum"
            )
        zitter_pass = True
    expected = all(checks) and zitter_pass
    if record["pass"] is not expected:
        raise SymmetryQCASpecError("witness classification mismatch")
    return expected


def _time_reversal_pass(values: Sequence[Decimal], *, scenario_class: str) -> bool:
    if len(values) != 3:
        raise SymmetryQCASpecError("time-reversal role requires three refinements")
    if scenario_class == "direct_only":
        return all(value <= Decimal(NUMERICAL_NORM_RESIDUAL_MAX) for value in values)
    margin = Decimal(REFINEMENT_MARGIN)
    ratio = Decimal("0.62")
    refinement = (
        values[1] <= ratio * values[0] + margin
        and values[2] <= ratio * values[1] + margin
    )
    return refinement and values[-1] <= Decimal(TIME_REVERSAL_FINE_MAX)


def _validate_structure(value: Any, *, scenario_class: str) -> bool:
    record = _exact(
        value,
        {
            "unitarity_residual_upper",
            "unitarity_pass",
            "causality_pass",
            "parity_residual_upper",
            "parity_pass",
            "time_reversal_role_residual_uppers",
            "time_reversal_role_refinement_pass",
            "time_reversal_role_fine_pass",
            "time_reversal_role_pass",
            "architecture_integrity_pass",
        },
        "symmetry and structure record",
    )
    unitarity = _number(record["unitarity_residual_upper"], "unitarity residual")
    parity = _number(record["parity_residual_upper"], "parity residual")
    if record["unitarity_pass"] is not (
        unitarity <= Decimal(NUMERICAL_NORM_RESIDUAL_MAX)
    ):
        raise SymmetryQCASpecError("unitarity classification mismatch")
    if record["parity_pass"] is not (
        parity <= Decimal(PARITY_NUMERICAL_RESIDUAL_MAX)
    ):
        raise SymmetryQCASpecError("parity classification mismatch")
    residuals = record["time_reversal_role_residual_uppers"]
    if type(residuals) is not list or len(residuals) != 3:
        raise SymmetryQCASpecError("time-reversal residual allocation mismatch")
    values = [_number(item, "time-reversal residual") for item in residuals]
    if scenario_class == "direct_only":
        refinement_pass = True
    else:
        margin = Decimal(REFINEMENT_MARGIN)
        refinement_pass = (
            values[1] <= Decimal("0.62") * values[0] + margin
            and values[2] <= Decimal("0.62") * values[1] + margin
        )
    fine_pass = (
        values[-1] <= Decimal(NUMERICAL_NORM_RESIDUAL_MAX)
        if scenario_class == "direct_only"
        else values[-1] <= Decimal(TIME_REVERSAL_FINE_MAX)
    )
    role_pass = _time_reversal_pass(values, scenario_class=scenario_class)
    if (
        record["time_reversal_role_refinement_pass"] is not refinement_pass
        or record["time_reversal_role_fine_pass"] is not fine_pass
        or record["time_reversal_role_pass"] is not role_pass
    ):
        raise SymmetryQCASpecError("time-reversal role classification mismatch")
    return all(
        (
            record["unitarity_pass"],
            record["causality_pass"],
            record["parity_pass"],
            role_pass,
            record["architecture_integrity_pass"],
        )
    )


def _validate_scenario(
    value: Any, *, scenario_id: str, state_ids: tuple[str, ...]
) -> bool:
    record = _exact(
        value,
        {
            "scenario_id",
            "scenario_class",
            "operator",
            "witnesses",
            "pi_sector",
            "maximum_independent_state_disagreement_upper",
            "symmetry_and_structure",
            "pass",
        },
        "scenario result",
    )
    scenario_class = SCENARIO_CLASSES[scenario_id]
    if (
        record["scenario_id"] != scenario_id
        or record["scenario_class"] != scenario_class
    ):
        raise SymmetryQCASpecError("scenario identity or class mismatch")
    operator = _exact(
        record["operator"],
        {"refinements", "refinement_gates_pass", "pass"},
        "operator result",
    )
    refinements = operator["refinements"]
    if type(refinements) is not list or len(refinements) != 3:
        raise SymmetryQCASpecError("operator refinement allocation mismatch")
    maxima = [
        _validate_refinement(
            item,
            scenario_id=scenario_id,
            scenario_class=scenario_class,
            n_sites=n_sites,
        )
        for item, n_sites in zip(refinements, REGISTERED_SIZES)
    ]
    reduction = _refinement_reduction(maxima, scenario_class=scenario_class)
    if (
        operator["refinement_gates_pass"] is not reduction["pass"]
        or operator["pass"] is not reduction["pass"]
    ):
        raise SymmetryQCASpecError("operator refinement classification mismatch")
    witnesses = record["witnesses"]
    if type(witnesses) is not list or len(witnesses) != len(state_ids):
        raise SymmetryQCASpecError("scenario witness allocation mismatch")
    witness_pass = all(
        _validate_witness(item, state_id=state_id)
        for item, state_id in zip(witnesses, state_ids)
    )
    pi = _exact(
        record["pi_sector"],
        {
            "analytic_probability_upper",
            "candidate_probability_upper",
            "threshold",
            "pass",
        },
        "pi-sector record",
    )
    analytic = _number(pi["analytic_probability_upper"], "analytic pi tail")
    candidate = _number(pi["candidate_probability_upper"], "candidate pi probability")
    if pi["threshold"] != PI_SECTOR_PROBABILITY_MAX:
        raise SymmetryQCASpecError("pi-sector threshold mismatch")
    if scenario_class == "direct_only" and (analytic != 0 or candidate != 0):
        raise SymmetryQCASpecError("zero-potential pi-sector values must be exact zero")
    pi_pass = (
        analytic <= Decimal(PI_SECTOR_PROBABILITY_MAX)
        and candidate <= Decimal(PI_SECTOR_PROBABILITY_MAX)
    )
    if pi["pass"] is not pi_pass:
        raise SymmetryQCASpecError("pi-sector classification mismatch")
    disagreement = _number(
        record["maximum_independent_state_disagreement_upper"],
        "maximum independent state disagreement",
    )
    agreement_pass = disagreement <= Decimal(INDEPENDENT_STATE_DISAGREEMENT_MAX)
    structure_pass = _validate_structure(
        record["symmetry_and_structure"], scenario_class=scenario_class
    )
    expected = (
        operator["pass"]
        and witness_pass
        and pi_pass
        and agreement_pass
        and structure_pass
    )
    if record["pass"] is not expected:
        raise SymmetryQCASpecError("scenario aggregate classification mismatch")
    return expected


def _validate_failure_controls(value: Any, *, stage: str) -> None:
    if stage == "development":
        if value is not None:
            raise SymmetryQCASpecError("development ledger contains failure controls")
        return
    if type(value) is not list or len(value) != len(FAILURE_CONTROL_IDS):
        raise SymmetryQCASpecError("confirmation failure controls are incomplete")
    for expected_id, item in zip(FAILURE_CONTROL_IDS, value):
        record = _exact(item, {"id", "metric", "value"}, "failure control")
        if (
            record["id"] != expected_id
            or record["metric"] != FAILURE_CONTROL_METRICS[expected_id]
        ):
            raise SymmetryQCASpecError("failure-control identity or order mismatch")
        _number(record["value"], "failure-control value")


def validate_result_ledger(
    value: Any, *, expected_stage: str | None = None
) -> dict[str, Any]:
    ledger = _exact(value, LEDGER_KEYS, "result ledger")
    if (
        ledger["protocol_version"] != PROTOCOL_VERSION
        or ledger["search_id"] != SEARCH_ID
    ):
        raise SymmetryQCASpecError("result ledger identity mismatch")
    stage = ledger["stage"]
    if stage not in ("development", "confirmation") or (
        expected_stage is not None and stage != expected_stage
    ):
        raise SymmetryQCASpecError("result ledger stage mismatch")
    bindings = _exact(ledger["bindings"], BINDING_KEYS, "result bindings")
    for label, binding in bindings.items():
        _binding(binding, label)
    numerics = _exact(
        ledger["numerics"],
        {
            "primary_backend",
            "primary_library_version",
            "primary_precision_bits",
            "primary_rounding",
            "independent_backend",
            "independent_library_version",
            "independent_decimal_digits",
            "binary64_registered_dynamics",
            "target_tail_formula",
            "pi_tail_formula",
        },
        "numerics",
    )
    expected_numerics = {
        "primary_backend": "python-flint Arb/Acb",
        "primary_library_version": PRIMARY_LIBRARY_VERSION,
        "primary_precision_bits": PRECISION_BITS,
        "primary_rounding": "outward_ball_enclosures",
        "independent_backend": "mpmath",
        "independent_library_version": INDEPENDENT_LIBRARY_VERSION,
        "independent_decimal_digits": INDEPENDENT_DPS,
        "binary64_registered_dynamics": False,
        "target_tail_formula": "2 exp(z) z^s/s!",
        "pi_tail_formula": "2 exp(z) z^s/s!",
    }
    if numerics != expected_numerics:
        raise SymmetryQCASpecError("registered numerical declaration mismatch")
    scenario_ids = (
        DEVELOPMENT_SCENARIOS if stage == "development" else CONFIRMATION_SCENARIOS
    )
    state_ids = DEVELOPMENT_STATES if stage == "development" else CONFIRMATION_STATES
    results = ledger["scenario_results"]
    if type(results) is not list or len(results) != len(scenario_ids):
        raise SymmetryQCASpecError("scenario result allocation mismatch")
    passes = [
        _validate_scenario(record, scenario_id=scenario_id, state_ids=state_ids)
        for record, scenario_id in zip(results, scenario_ids)
    ]
    aggregate = _exact(
        ledger["aggregate"],
        {
            "scenario_count",
            "scenario_pass_count",
            "all_scenarios_complete",
            "stage_pass",
            "confirmation_authorized",
            "failure_controls",
            "classification",
        },
        "result aggregate",
    )
    stage_pass = all(passes)
    if (
        aggregate["scenario_count"] != len(results)
        or aggregate["scenario_pass_count"] != sum(passes)
        or aggregate["all_scenarios_complete"] is not True
        or aggregate["stage_pass"] is not stage_pass
        or aggregate["confirmation_authorized"]
        is not (stage == "development" and stage_pass)
    ):
        raise SymmetryQCASpecError("result aggregate counts or gates mismatch")
    _validate_failure_controls(aggregate["failure_controls"], stage=stage)
    if stage == "development":
        status = (
            "development_passed"
            if stage_pass
            else "development_gate_failed_confirmation_unopened"
        )
    else:
        status = (
            "constructive_sufficiency_passed_direct_symmetry_qca_sector"
            if stage_pass
            else "development_passed_confirmation_failed"
        )
    if ledger["status"] != status or aggregate["classification"] != status:
        raise SymmetryQCASpecError("terminal result classification mismatch")
    return ledger


def build_result_ledger(
    *,
    stage: str,
    bindings: dict[str, dict[str, str]],
    scenario_results: list[dict[str, Any]],
    failure_controls: list[dict[str, str]] | None,
) -> dict[str, Any]:
    """Derive a complete canonical ledger from already-reduced stage records."""

    if stage not in ("development", "confirmation"):
        raise SymmetryQCASpecError("stage must be development or confirmation")
    stage_pass = all(
        type(record) is dict and record.get("pass") is True
        for record in scenario_results
    )
    if stage == "development":
        status = (
            "development_passed"
            if stage_pass
            else "development_gate_failed_confirmation_unopened"
        )
    else:
        status = (
            "constructive_sufficiency_passed_direct_symmetry_qca_sector"
            if stage_pass
            else "development_passed_confirmation_failed"
        )
    ledger = {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "stage": stage,
        "status": status,
        "bindings": bindings,
        "numerics": {
            "primary_backend": "python-flint Arb/Acb",
            "primary_library_version": PRIMARY_LIBRARY_VERSION,
            "primary_precision_bits": PRECISION_BITS,
            "primary_rounding": "outward_ball_enclosures",
            "independent_backend": "mpmath",
            "independent_library_version": INDEPENDENT_LIBRARY_VERSION,
            "independent_decimal_digits": INDEPENDENT_DPS,
            "binary64_registered_dynamics": False,
            "target_tail_formula": "2 exp(z) z^s/s!",
            "pi_tail_formula": "2 exp(z) z^s/s!",
        },
        "scenario_results": scenario_results,
        "aggregate": {
            "scenario_count": len(scenario_results),
            "scenario_pass_count": sum(
                type(record) is dict and record.get("pass") is True
                for record in scenario_results
            ),
            "all_scenarios_complete": True,
            "stage_pass": stage_pass,
            "confirmation_authorized": stage == "development" and stage_pass,
            "failure_controls": failure_controls,
            "classification": status,
        },
    }
    return validate_result_ledger(ledger, expected_stage=stage)


def write_result_ledger(
    path: Path, value: dict[str, Any], *, stage: str
) -> None:
    """Validate, fsync, and atomically create a result without clobbering."""

    validate_result_ledger(value, expected_stage=stage)
    write_canonical_json_once(path, value)
