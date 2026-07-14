"""Strict canonical result-ledger validation and atomic persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mpmath import mp

from .metrics import refinement_gate
from .protocol import (
    ABSOLUTE_DISTANCE_THRESHOLDS,
    CONFIRMATION_SCENARIOS,
    CONFIRMATION_STATES,
    DEVELOPMENT_SCENARIOS,
    DEVELOPMENT_STATES,
    INFIDELITY_MAX,
    INDEPENDENT_LIBRARY_VERSION,
    LOCAL_CURRENT_L1_MAX,
    MOMENTUM_TV_MAX,
    NUMERICAL_NORM_RESIDUAL_MAX,
    PARITY_NUMERICAL_RESIDUAL_MAX,
    POSITION_TV_MAX,
    PRIMARY_LIBRARY_VERSION,
    PROTOCOL_VERSION,
    REFINEMENT_MARGIN,
    REFINEMENT_RATIO,
    REGISTERED_OBSERVATION_TIMES,
    REGISTERED_SIZES,
    SEARCH_ID,
    TIME_REVERSAL_FINE_MAX,
    TOTAL_CURRENT_ERROR_MAX,
    ZITTER_CURRENT_SUP_MAX,
)
from .spec import QuantumDiracSpecError, write_canonical_json_once


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
    "candidate_manifest",
    "scenario_manifest",
    "state_manifest",
    "partition_manifest",
}


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise QuantumDiracSpecError(f"{label} has missing or unexpected fields")
    return value


def _decimal(value: Any, label: str):
    if type(value) is not str or not value:
        raise QuantumDiracSpecError(f"{label} must be a decimal string")
    try:
        number = mp.mpf(value)
    except (ValueError, TypeError) as exc:
        raise QuantumDiracSpecError(f"{label} is not a finite decimal") from exc
    if not mp.isfinite(number):
        raise QuantumDiracSpecError(f"{label} is not finite")
    return number


def _nonnegative(value: Any, label: str):
    number = _decimal(value, label)
    if number < 0:
        raise QuantumDiracSpecError(f"{label} must be nonnegative")
    return number


def _binding(value: Any, label: str) -> None:
    binding = _exact(value, {"path", "sha256"}, label)
    if type(binding["path"]) is not str or not binding["path"]:
        raise QuantumDiracSpecError(f"{label} path is invalid")
    digest = binding["sha256"]
    if (
        type(digest) is not str
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise QuantumDiracSpecError(f"{label} digest is invalid")


def _validate_observation(value: Any, expected_time: str) -> bool:
    record = _exact(
        value,
        {
            "time",
            "position_tv_upper",
            "momentum_tv_upper",
            "total_current_error_upper",
            "local_current_l1_upper",
            "infidelity_upper",
            "candidate_norm_residual_upper",
            "target_norm_residual_upper",
            "independent_state_disagreement_upper",
            "gates",
            "pass",
        },
        "witness observation",
    )
    if record["time"] != expected_time:
        raise QuantumDiracSpecError("witness observation time order mismatch")
    thresholds = {
        "position_tv": ("position_tv_upper", POSITION_TV_MAX),
        "momentum_tv": ("momentum_tv_upper", MOMENTUM_TV_MAX),
        "total_current": ("total_current_error_upper", TOTAL_CURRENT_ERROR_MAX),
        "local_current": ("local_current_l1_upper", LOCAL_CURRENT_L1_MAX),
        "infidelity": ("infidelity_upper", INFIDELITY_MAX),
        "candidate_norm": (
            "candidate_norm_residual_upper",
            NUMERICAL_NORM_RESIDUAL_MAX,
        ),
        "target_norm": ("target_norm_residual_upper", NUMERICAL_NORM_RESIDUAL_MAX),
        "independent_state_agreement": (
            "independent_state_disagreement_upper",
            "1e-11",
        ),
    }
    gates = _exact(record["gates"], set(thresholds), "witness gates")
    expected_gates = {}
    for gate, (field, threshold) in thresholds.items():
        expected_gates[gate] = _nonnegative(record[field], field) <= mp.mpf(threshold)
    if gates != expected_gates or record["pass"] is not all(expected_gates.values()):
        raise QuantumDiracSpecError("witness gate classification mismatch")
    return record["pass"]


def _validate_witness(value: Any, expected_state: str, macrosteps: int) -> bool:
    record = _exact(
        value,
        {
            "state_id",
            "observations",
            "zitter_current_series",
            "zitter_sup_error_upper",
            "zitter_pass",
            "coherence_negative_fixture",
            "pass",
        },
        "witness record",
    )
    if record["state_id"] != expected_state:
        raise QuantumDiracSpecError("witness state order mismatch")
    observations = record["observations"]
    if type(observations) is not list or len(observations) != 4:
        raise QuantumDiracSpecError("witness observation count mismatch")
    observation_results = [
        _validate_observation(item, time)
        for item, time in zip(observations, REGISTERED_OBSERVATION_TIMES)
    ]
    observation_pass = all(observation_results)
    series = record["zitter_current_series"]
    if expected_state.endswith("ZITTER"):
        if type(series) is not list or len(series) != macrosteps:
            raise QuantumDiracSpecError("Zitterbewegung series is incomplete")
        errors = []
        for expected_step, item in enumerate(series, start=1):
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
            if entry["step"] != expected_step or type(entry["time"]) is not str:
                raise QuantumDiracSpecError("Zitterbewegung step order mismatch")
            if _decimal(entry["candidate_current_lower"], "candidate current lower") > _decimal(
                entry["candidate_current_upper"], "candidate current upper"
            ):
                raise QuantumDiracSpecError("candidate current interval is reversed")
            if _decimal(entry["target_current_lower"], "target current lower") > _decimal(
                entry["target_current_upper"], "target current upper"
            ):
                raise QuantumDiracSpecError("target current interval is reversed")
            errors.append(_nonnegative(entry["error_upper"], "Zitterbewegung error"))
        supremum = _nonnegative(record["zitter_sup_error_upper"], "Zitterbewegung supremum")
        if supremum < max(errors):
            raise QuantumDiracSpecError("Zitterbewegung supremum is below a series entry")
        zitter_pass = supremum <= mp.mpf(ZITTER_CURRENT_SUP_MAX)
    else:
        if series != [] or record["zitter_sup_error_upper"] is not None:
            raise QuantumDiracSpecError("non-Zitterbewegung witness contains a current series")
        zitter_pass = True
    if record["zitter_pass"] is not zitter_pass:
        raise QuantumDiracSpecError("Zitterbewegung gate classification mismatch")
    negative = _exact(
        record["coherence_negative_fixture"],
        {"applicable", "maximum_position_entry_change_lower", "pass"},
        "coherence negative fixture",
    )
    if negative["applicable"]:
        changed = _nonnegative(
            negative["maximum_position_entry_change_lower"],
            "coherence position change",
        ) > 0
        if negative["pass"] is not changed:
            raise QuantumDiracSpecError("coherence negative-fixture classification mismatch")
    elif negative != {
        "applicable": False,
        "maximum_position_entry_change_lower": None,
        "pass": True,
    }:
        raise QuantumDiracSpecError("inapplicable coherence fixture is malformed")
    required_negative = not expected_state.endswith("INTERFERENCE") or negative["pass"]
    expected_pass = observation_pass and zitter_pass and required_negative
    if record["pass"] is not expected_pass:
        raise QuantumDiracSpecError("witness aggregate classification mismatch")
    return expected_pass


def _validate_scenario(value: Any, scenario_id: str, state_ids: tuple[str, ...]) -> bool:
    record = _exact(
        value,
        {
            "scenario_id",
            "operator",
            "witnesses",
            "maximum_independent_state_disagreement_upper",
            "symmetry_and_structure",
            "pass",
        },
        "scenario result",
    )
    if record["scenario_id"] != scenario_id:
        raise QuantumDiracSpecError("scenario result order mismatch")
    operator = _exact(
        record["operator"],
        {"refinements", "refinement_pass", "certified_contains_independent", "pass"},
        "operator result",
    )
    refinements = operator["refinements"]
    if type(refinements) is not list or len(refinements) != 3:
        raise QuantumDiracSpecError("operator refinement count mismatch")
    maxima = []
    absolute_passes = []
    certified_contains = True
    for n_sites, refinement in zip(REGISTERED_SIZES, refinements):
        item = _exact(
            refinement,
            {
                "n_sites",
                "delta",
                "observations",
                "scenario_max_upper",
                "absolute_threshold",
                "absolute_pass",
                "resources",
            },
            "operator refinement",
        )
        if item["n_sites"] != n_sites or item["absolute_threshold"] != ABSOLUTE_DISTANCE_THRESHOLDS[n_sites]:
            raise QuantumDiracSpecError("operator refinement identity mismatch")
        observations = item["observations"]
        if type(observations) is not list or len(observations) != 4:
            raise QuantumDiracSpecError("operator observation count mismatch")
        observation_values = []
        for expected_time, observation in zip(REGISTERED_OBSERVATION_TIMES, observations):
            entry = _exact(
                observation,
                {
                    "time",
                    "operator_norm_upper",
                    "target_tail_upper",
                    "numeric_bound",
                    "certified_distance_upper",
                    "independent_distance",
                    "certified_contains_independent",
                },
                "operator observation",
            )
            if entry["time"] != expected_time or entry["numeric_bound"] != "0":
                raise QuantumDiracSpecError("operator observation identity mismatch")
            distance = _nonnegative(entry["certified_distance_upper"], "certified distance")
            independent = _nonnegative(entry["independent_distance"], "independent distance")
            contains = distance >= independent
            if entry["certified_contains_independent"] is not contains:
                raise QuantumDiracSpecError("certified containment classification mismatch")
            certified_contains &= contains
            observation_values.append(distance)
        maximum = _nonnegative(item["scenario_max_upper"], "scenario maximum")
        if maximum < max(observation_values):
            raise QuantumDiracSpecError("scenario maximum is below an observation")
        maxima.append(maximum)
        absolute = maximum <= mp.mpf(ABSOLUTE_DISTANCE_THRESHOLDS[n_sites])
        if item["absolute_pass"] is not absolute:
            raise QuantumDiracSpecError("absolute operator gate classification mismatch")
        absolute_passes.append(absolute)
        resources = _exact(
            item["resources"],
            {
                "n_sites",
                "macrosteps",
                "active_potential_steps",
                "elementary_layers",
                "gate_work",
                "occupation_modes",
                "occupied_modes",
                "local_hilbert_dimension",
            },
            "resource accounting",
        )
        if resources["n_sites"] != n_sites:
            raise QuantumDiracSpecError("resource accounting identity mismatch")
        for key in (
            "macrosteps",
            "active_potential_steps",
            "elementary_layers",
            "gate_work",
            "occupation_modes",
            "occupied_modes",
            "local_hilbert_dimension",
        ):
            if type(resources[key]) is not int or resources[key] < 0:
                raise QuantumDiracSpecError("resource accounting value is invalid")
        if (
            resources["macrosteps"] != n_sites // 8
            or resources["active_potential_steps"] > resources["macrosteps"]
            or resources["elementary_layers"]
            != 3 * resources["macrosteps"] + resources["active_potential_steps"]
            or resources["gate_work"] != n_sites * resources["elementary_layers"]
            or resources["occupation_modes"] != 2 * n_sites
            or resources["occupied_modes"] != 1
            or resources["local_hilbert_dimension"] != 4
        ):
            raise QuantumDiracSpecError("resource accounting arithmetic mismatch")
    refinement_passed = refinement_gate(
        *maxima,
        ratio=mp.mpf(REFINEMENT_RATIO),
        margin=mp.mpf(REFINEMENT_MARGIN),
    )
    if operator["refinement_pass"] is not refinement_passed:
        raise QuantumDiracSpecError("operator refinement classification mismatch")
    if operator["certified_contains_independent"] is not certified_contains:
        raise QuantumDiracSpecError("operator containment aggregate mismatch")
    operator_pass = all(absolute_passes) and refinement_passed and certified_contains
    if operator["pass"] is not operator_pass:
        raise QuantumDiracSpecError("operator aggregate classification mismatch")
    witnesses = record["witnesses"]
    if type(witnesses) is not list or len(witnesses) != len(state_ids):
        raise QuantumDiracSpecError("scenario witness allocation mismatch")
    witness_results = [
        _validate_witness(item, state_id, REGISTERED_SIZES[-1] // 8)
        for item, state_id in zip(witnesses, state_ids)
    ]
    witness_pass = all(witness_results)
    disagreement = _nonnegative(
        record["maximum_independent_state_disagreement_upper"],
        "maximum independent state disagreement",
    )
    structure = _exact(
        record["symmetry_and_structure"],
        {
            "refinements",
            "time_reversal_refinement_pass",
            "time_reversal_fine_pass",
            "pass",
        },
        "symmetry result",
    )
    symmetry_refinements = structure["refinements"]
    if type(symmetry_refinements) is not list or len(symmetry_refinements) != 3:
        raise QuantumDiracSpecError("symmetry refinement count mismatch")
    time_reversal_values = []
    local_structure_pass = True
    for n_sites, item in zip(REGISTERED_SIZES, symmetry_refinements):
        symmetry = _exact(
            item,
            {
                "n_sites",
                "unitarity_abstract_exact",
                "causal_support_structural_exact",
                "massless_cone_boundaries_attained",
                "parity_abstract_exact",
                "parity_residual_upper",
                "parity_pass",
                "time_reversal_domain",
                "time_reversal_residual_upper",
                "norm_residual_upper",
                "norm_pass",
            },
            "symmetry refinement",
        )
        if item["n_sites"] != n_sites or item["time_reversal_domain"] != "registered_K_in":
            raise QuantumDiracSpecError("symmetry domain mismatch")
        if not all(
            item[key]
            for key in (
                "unitarity_abstract_exact",
                "causal_support_structural_exact",
                "massless_cone_boundaries_attained",
                "parity_abstract_exact",
            )
        ):
            raise QuantumDiracSpecError("exact structural certificate is false")
        parity = _nonnegative(item["parity_residual_upper"], "parity residual")
        norm = _nonnegative(item["norm_residual_upper"], "norm residual")
        if item["parity_pass"] is not (parity <= mp.mpf(PARITY_NUMERICAL_RESIDUAL_MAX)):
            raise QuantumDiracSpecError("parity classification mismatch")
        if item["norm_pass"] is not (norm <= mp.mpf(NUMERICAL_NORM_RESIDUAL_MAX)):
            raise QuantumDiracSpecError("norm classification mismatch")
        local_structure_pass &= item["parity_pass"] and item["norm_pass"]
        time_reversal_values.append(
            _nonnegative(item["time_reversal_residual_upper"], "time-reversal residual")
        )
    tr_refinement = refinement_gate(
        *time_reversal_values,
        ratio=mp.mpf(REFINEMENT_RATIO),
        margin=mp.mpf(REFINEMENT_MARGIN),
    )
    tr_fine = time_reversal_values[-1] <= mp.mpf(TIME_REVERSAL_FINE_MAX)
    if structure["time_reversal_refinement_pass"] is not tr_refinement or structure[
        "time_reversal_fine_pass"
    ] is not tr_fine:
        raise QuantumDiracSpecError("time-reversal classification mismatch")
    structure_pass = (
        local_structure_pass
        and tr_refinement
        and tr_fine
        and disagreement <= mp.mpf("1e-11")
    )
    if structure["pass"] is not structure_pass:
        raise QuantumDiracSpecError("structure aggregate classification mismatch")
    expected_pass = operator_pass and witness_pass and structure_pass
    if record["pass"] is not expected_pass:
        raise QuantumDiracSpecError("scenario aggregate classification mismatch")
    return expected_pass


def _validate_cross_witnesses(value: Any, state_ids: tuple[str, ...]) -> bool:
    record = _exact(
        value,
        {
            "scenario_id",
            "state_partition",
            "witnesses",
            "maximum_independent_state_disagreement_upper",
            "pass",
        },
        "confirmation cross-witness record",
    )
    if record["scenario_id"] != DEVELOPMENT_SCENARIOS[0] or record["state_partition"] != "confirmation":
        raise QuantumDiracSpecError("confirmation cross-witness identity mismatch")
    witnesses = record["witnesses"]
    if type(witnesses) is not list or len(witnesses) != len(state_ids):
        raise QuantumDiracSpecError("confirmation cross-witness allocation mismatch")
    witness_results = [
        _validate_witness(item, state_id, REGISTERED_SIZES[-1] // 8)
        for item, state_id in zip(witnesses, state_ids)
    ]
    witnesses_pass = all(witness_results)
    disagreement = _nonnegative(
        record["maximum_independent_state_disagreement_upper"],
        "cross-witness independent disagreement",
    )
    expected = witnesses_pass and disagreement <= mp.mpf("1e-11")
    if record["pass"] is not expected:
        raise QuantumDiracSpecError("confirmation cross-witness classification mismatch")
    return expected


def validate_result_ledger(value: Any, *, expected_stage: str | None = None) -> dict[str, Any]:
    ledger = _exact(value, LEDGER_KEYS, "result ledger")
    if ledger["protocol_version"] != PROTOCOL_VERSION or ledger["search_id"] != SEARCH_ID:
        raise QuantumDiracSpecError("result ledger identity mismatch")
    stage = ledger["stage"]
    if stage not in ("development", "confirmation") or (
        expected_stage is not None and stage != expected_stage
    ):
        raise QuantumDiracSpecError("result ledger stage mismatch")
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
        },
        "numerics",
    )
    if (
        numerics["primary_backend"] != "python-flint Arb/Acb"
        or numerics["primary_library_version"] != PRIMARY_LIBRARY_VERSION
        or numerics["primary_precision_bits"] != 256
        or numerics["primary_rounding"] != "outward_ball_enclosures"
        or numerics["independent_backend"] != "mpmath"
        or numerics["independent_library_version"] != INDEPENDENT_LIBRARY_VERSION
        or numerics["independent_decimal_digits"] != 110
        or numerics["binary64_registered_dynamics"] is not False
    ):
        raise QuantumDiracSpecError("registered numerical declaration mismatch")
    scenario_ids = DEVELOPMENT_SCENARIOS if stage == "development" else CONFIRMATION_SCENARIOS
    state_ids = DEVELOPMENT_STATES if stage == "development" else CONFIRMATION_STATES
    results = ledger["scenario_results"]
    if type(results) is not list or len(results) != len(scenario_ids):
        raise QuantumDiracSpecError("scenario result allocation mismatch")
    passes = [
        _validate_scenario(record, scenario_id, state_ids)
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
            "development_free_light_holdout_witnesses",
            "failure_controls",
            "classification",
        },
        "result aggregate",
    )
    if stage == "confirmation":
        cross_pass = _validate_cross_witnesses(
            aggregate["development_free_light_holdout_witnesses"],
            CONFIRMATION_STATES,
        )
    else:
        if aggregate["development_free_light_holdout_witnesses"] is not None:
            raise QuantumDiracSpecError("development ledger contains holdout cross-witnesses")
        cross_pass = True
    stage_pass = all(passes) and cross_pass
    if (
        aggregate["scenario_count"] != len(results)
        or aggregate["scenario_pass_count"] != sum(passes)
        or aggregate["all_scenarios_complete"] is not True
        or aggregate["stage_pass"] is not stage_pass
        or aggregate["confirmation_authorized"] is not (stage == "development" and stage_pass)
    ):
        raise QuantumDiracSpecError("result aggregate counts or gates mismatch")
    if stage == "development":
        expected_status = (
            "development_passed"
            if stage_pass
            else "development_gate_failed_confirmation_unopened"
        )
        if aggregate["failure_controls"] != []:
            raise QuantumDiracSpecError("development ledger contains post-confirmation controls")
    else:
        expected_status = (
            "constructive_sufficiency_passed_frozen_dirac_sector"
            if stage_pass
            else "development_passed_confirmation_failed"
        )
        controls = aggregate["failure_controls"]
        if stage_pass:
            if type(controls) is not list or [item.get("id") for item in controls] != [
                "HIGH-K",
                "HIGH-MASS",
                "LONG-HORIZON",
                "FINITE-RING",
                "DEPHASED",
            ]:
                raise QuantumDiracSpecError("confirmation failure controls are incomplete")
            for item in controls:
                _exact(item, {"id", "metric", "value"}, "failure control")
                if type(item["metric"]) is not str or not item["metric"]:
                    raise QuantumDiracSpecError("failure-control metric is invalid")
            for item in controls[:3]:
                _nonnegative(item["value"], "failure-control value")
            if controls[3] != {
                "id": "FINITE-RING",
                "metric": "massless_directional_recurrence_steps",
                "value": "256",
            }:
                raise QuantumDiracSpecError("finite-ring failure control is malformed")
            if controls[4] != {
                "id": "DEPHASED",
                "metric": "coherence_removed_controls_reported_in_witness_records",
                "value": "true",
            }:
                raise QuantumDiracSpecError("dephased failure control is malformed")
        elif controls != []:
            raise QuantumDiracSpecError("failed confirmation contains non-gating controls")
    if ledger["status"] != expected_status or aggregate["classification"] != expected_status:
        raise QuantumDiracSpecError("terminal result classification mismatch")
    return ledger


def write_result_ledger(path: Path, value: dict[str, Any], *, stage: str) -> None:
    validate_result_ledger(value, expected_stage=stage)
    write_canonical_json_once(path, value)
