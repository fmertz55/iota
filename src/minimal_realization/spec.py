from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DESIGN_FILENAMES = (
    "candidate.schema.json",
    "operator_alphabet.json",
    "topology.json",
    "causal_cone.json",
    "proto_object_detector.json",
    "detector_fixtures.json",
    "partitions.json",
    "lower_shell_exclusions.json",
    "lower_shell_null.json",
    "result.schema.json",
    "search_plan.json",
)


class SpecError(ValueError):
    pass


@dataclass(frozen=True)
class DesignAudit:
    spec_dir: Path
    contract_version: str
    search_id: str
    status: str
    hashes: dict[str, str]


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SpecError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise SpecError(f"non-finite JSON number {value!r} is forbidden")


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(
                handle,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecError(f"{path}: {exc}") from exc
    if type(value) is not dict:
        raise SpecError(f"{path}: root must be an object")
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SpecError(message)


def _require_json_equal(actual: Any, expected: Any, message: str) -> None:
    _require(canonical_json(actual) == canonical_json(expected), message)


def audit_design(spec_dir: Path) -> DesignAudit:
    spec_dir = spec_dir.resolve()
    documents: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for filename in DESIGN_FILENAMES:
        path = spec_dir / filename
        documents[filename] = load_json(path)
        hashes[filename] = sha256_file(path)

    for filename, document in documents.items():
        _require(
            document.get("contract_version") == "0.2-draft",
            f"{filename}: wrong contract version",
        )

    schema = documents["candidate.schema.json"]
    schema_properties = schema["properties"]
    _require(schema.get("type") == "object", "candidate.schema.json: root type mismatch")
    _require(schema.get("additionalProperties") is False, "candidate.schema.json: root must be closed")
    _require_json_equal(
        schema.get("required"),
        [
            "contract_version",
            "grammar_id",
            "candidate_id",
            "status",
            "primitive_accounting",
            "primitives",
            "laws",
            "clock",
            "substrate",
            "initial_condition",
            "proto_object_detector",
            "maps",
            "randomness",
            "data_class",
        ],
        "candidate.schema.json: required fields mismatch",
    )
    _require(schema_properties["contract_version"].get("const") == "0.2-draft", "candidate.schema.json: version mismatch")
    _require(schema_properties["grammar_id"].get("const") == "MIR-BOOLEAN-PRODUCTION-ROW-V0.2", "candidate.schema.json: grammar mismatch")
    _require(schema_properties["clock"]["properties"]["tick_unit"].get("const") == "elementary_causal_layer", "candidate.schema.json: tick unit mismatch")
    _require(schema_properties["laws"].get("maxItems") == 4, "candidate.schema.json: law bound mismatch")
    law_properties = schema_properties["laws"]["items"]["properties"]
    _require(law_properties["operator"].get("const") == "emit_one_if_signature", "candidate.schema.json: operator mismatch")
    _require_json_equal(law_properties["input_ports"].get("const"), ["self", "predecessor"], "candidate.schema.json: input ports mismatch")
    _require_json_equal(law_properties["signature"].get("enum"), ["00", "01", "10", "11"], "candidate.schema.json: signatures mismatch")
    _require(law_properties["governed_degree"].get("const") == "event", "candidate.schema.json: governed degree mismatch")
    _require(law_properties["duration_ticks"].get("const") == 1, "candidate.schema.json: duration mismatch")
    _require(law_properties["write_count"].get("const") == 1, "candidate.schema.json: write count mismatch")
    primitive_items = schema_properties["primitives"]["prefixItems"]
    _require_json_equal(
        [item["properties"] for item in primitive_items],
        [
            {"id": {"const": "event"}, "scope": {"const": "dynamic"}, "alphabet": {"const": [0, 1]}},
            {"id": {"const": "predecessor"}, "scope": {"const": "relation"}, "alphabet": {"const": [0, 1]}},
        ],
        "candidate.schema.json: primitive inventory mismatch",
    )
    expected_accounting = {
        "normalized_n_p": 2,
        "dynamic_kind_count": 1,
        "relation_kind_count": 1,
        "exogenous_kind_count": 0,
        "candidate_supplied_bits": 0,
        "seed_nonquiescent_instances": 1,
        "dynamic_storage_bits_per_layer": 64,
        "relation_instances": 64,
        "site_evaluations_per_layer": 64,
    }
    _require_json_equal(
        {key: item.get("const") for key, item in schema_properties["primitive_accounting"]["properties"].items()},
        expected_accounting,
        "candidate.schema.json: accounting constants mismatch",
    )
    _require(schema_properties["primitive_accounting"].get("additionalProperties") is False, "candidate.schema.json: accounting must be closed")
    _require_json_equal(schema_properties["maps"]["properties"], {"initialization": {"const": "single_active_translation"}, "readout": {"const": "MIR-ISOLATED-DYAD-OUTWARD-EFFECT-V0.2"}, "intervention": {"const": "matched_dyad_relocation"}}, "candidate.schema.json: maps mismatch")
    _require_json_equal(schema_properties["randomness"]["properties"], {"kind": {"const": "none"}, "exogenous_channel_count": {"const": 0}}, "candidate.schema.json: randomness mismatch")
    _require(schema_properties["data_class"].get("const") == "development", "candidate.schema.json: data class mismatch")
    _require_json_equal(
        schema_properties["clock"]["properties"],
        {
            "tick_unit": {"const": "elementary_causal_layer"},
            "causal_layers_per_tick": {"const": 1},
            "within_tick_cascade": {"const": False},
            "max_relation_hops_per_tick": {"const": 1},
        },
        "candidate.schema.json: clock mismatch",
    )
    _require(schema_properties["substrate"]["properties"]["ref"].get("const") == "topology.json", "candidate.schema.json: topology ref mismatch")
    _require(schema_properties["proto_object_detector"]["properties"]["ref"].get("const") == "proto_object_detector.json", "candidate.schema.json: detector ref mismatch")
    _require(len(schema.get("allOf", [])) == 2, "candidate.schema.json: status/reference conditions missing")
    zero_condition = schema["allOf"][0]
    _require(zero_condition["then"]["properties"]["candidate_id"].get("const") == "MIR-P2-L0-NONE", "candidate.schema.json: zero-row id condition mismatch")
    _require(zero_condition["then"]["properties"]["status"].get("const") == "analytically_excluded", "candidate.schema.json: zero-row status condition mismatch")
    _require("exclusion_reason" in zero_condition["then"].get("required", []), "candidate.schema.json: zero-row exclusion reason missing")
    frozen_condition = schema["allOf"][1]
    _require(frozen_condition["then"]["properties"]["substrate"]["properties"]["sha256"].get("pattern") == "^[0-9a-f]{64}$", "candidate.schema.json: frozen substrate hash condition mismatch")

    alphabet = documents["operator_alphabet.json"]
    _require_json_equal(alphabet.get("state_alphabet"), [0, 1], "operator_alphabet.json: state alphabet mismatch")
    _require_json_equal(
        alphabet.get("input_ports"),
        [
            {"id": "self", "source": "event at the governed locus in layer t"},
            {"id": "predecessor", "source": "event at the unique directed predecessor in layer t"},
        ],
        "operator_alphabet.json: input ports mismatch",
    )
    _require(alphabet.get("fan_in") == 2, "operator_alphabet.json: fan-in must be two")
    _require(alphabet.get("signatures") == ["00", "01", "10", "11"], "operator_alphabet.json: signature order mismatch")
    _require(alphabet["candidate_rule_space"].get("candidate_count") == 16, "operator_alphabet.json: candidate count mismatch")
    _require(alphabet["operator"].get("id") == "emit_one_if_signature", "operator_alphabet.json: operator mismatch")
    _require(alphabet["operator"].get("arity") == 2, "operator_alphabet.json: operator arity mismatch")
    _require(alphabet.get("unmatched_signature_semantics") == "fresh output remains quiescent at value 0", "operator_alphabet.json: unmatched semantics mismatch")
    _require(alphabet.get("row_arbitration") == "signatures are exact and mutually exclusive", "operator_alphabet.json: arbitration mismatch")
    _require_json_equal(
        alphabet["candidate_rule_space"].get("shell_sizes_by_n_l"),
        {"0": 1, "1": 4, "2": 6, "3": 4, "4": 1},
        "operator_alphabet.json: shell sizes mismatch",
    )

    topology = documents["topology.json"]
    _require_json_equal(topology.get("loci"), {"count": 64, "labels": "integers 0 through 63", "boundary": "periodic"}, "topology.json: loci mismatch")
    _require_json_equal(
        topology.get("relation_schema"),
        {
            "id": "predecessor",
            "alphabet": [0, 1],
            "directed": True,
            "definition": "predecessor(i) = (i - 1) mod 64",
            "edge_orientation": "predecessor(i) to i",
            "instance_count": 64,
            "candidate_specific_edge_bits": 0,
            "temporality": "fixed timeless member of candidate topology G, not carried dynamic state",
        },
        "topology.json: relation schema mismatch",
    )
    _require_json_equal(
        topology.get("schedule"),
        {
            "kind": "synchronous_atomic_layer",
            "read_layer": "t",
            "write_layer": "t+1",
            "within_tick_cascade": False,
            "maximum_relation_hops_per_tick": 1,
        },
        "topology.json: schedule mismatch",
    )
    _require_json_equal(
        topology.get("group_action"),
        {"id": "cycle_translation", "definition": "tau_k(i) = (i + k) mod 64", "order": 64},
        "topology.json: group action mismatch",
    )
    _require_json_equal(
        topology.get("initial_condition_family"),
        {
            "id": "single_active_translation",
            "canonical_active_locus": 0,
            "active_count": 1,
            "all_other_events": 0,
            "contains_proto_object": False,
            "candidate_supplied_bits": 0,
            "accounting_note": "the common one-event seed is reported as N_P_seed=1; canonical origin choice costs no candidate-specific address bits under cycle translation symmetry",
        },
        "topology.json: initial family mismatch",
    )
    _require_json_equal(
        topology.get("resource_envelope"),
        {
            "dynamic_channel_schemas": 1,
            "relation_channel_schemas": 1,
            "dynamic_storage_bits_per_layer": 64,
            "relation_instances": 64,
            "site_evaluations_per_layer": 64,
            "causal_radius": 1,
            "substrate_size": 64,
        },
        "topology.json: resource envelope mismatch",
    )

    cone = documents["causal_cone.json"]
    _require(cone.get("formation_horizon_ticks") == 16, "causal_cone.json: horizon mismatch")
    _require_json_equal(cone.get("required_layers"), {"first": 0, "last": 18, "count": 19}, "causal_cone.json: required layers mismatch")
    _require(cone.get("seed_support") == [0], "causal_cone.json: seed support mismatch")
    _require(cone.get("persistence_confirmation_lag_ticks") == 1, "causal_cone.json: persistence lag mismatch")
    _require(cone.get("causal_endpoint_lag_ticks") == 2, "causal_cone.json: endpoint lag mismatch")
    _require_json_equal(
        cone.get("baseline"),
        {"id": "matched_all_zero", "initial_event_count": 0, "law_and_topology": "identical to the seeded trajectory"},
        "causal_cone.json: baseline mismatch",
    )
    _require_json_equal(cone.get("formation_times_tested"), {"minimum": 1, "maximum": 16}, "causal_cone.json: tested times mismatch")
    _require(cone.get("forward_cone_definition") == "locus j is in the layer-t cone when j = d mod 64 for an integer d with 0 <= d <= t", "causal_cone.json: forward cone mismatch")
    _require(cone.get("no_wrap_condition") == "the maximum forward distance 18 is less than the 64-locus cycle length", "causal_cone.json: no-wrap condition mismatch")
    _require(cone.get("attribution_rule") == "every active witness and successor-witness locus must be 1 in the seeded trajectory and 0 in the matched all-zero trajectory", "causal_cone.json: attribution rule mismatch")

    detector = documents["proto_object_detector.json"]
    _require(detector["matched_interventions"].get("normal_evolution_ticks_after_application") == 2, "proto_object_detector.json: causal lag mismatch")
    _require(detector["reachable_future_variable"].get("locus_offset_from_anchor") == 3, "proto_object_detector.json: endpoint mismatch")
    _require(detector["read_only"] is True, "proto_object_detector.json: detector must be read-only")
    _require(detector.get("detector_id") == "MIR-ISOLATED-DYAD-OUTWARD-EFFECT-V0.2", "proto_object_detector.json: detector id mismatch")
    _require(detector.get("state_encoding") == "length-64 binary vector indexed modulo 64", "proto_object_detector.json: state encoding mismatch")
    expected_pattern = [
        {"offset": -1, "value": 0},
        {"offset": 0, "value": 1},
        {"offset": 1, "value": 1},
        {"offset": 2, "value": 0},
    ]
    _require(detector["role"].get("required_pattern") == expected_pattern, "proto_object_detector.json: role pattern mismatch")
    _require(detector["succession"].get("eligible_successor_anchor_offsets") == [0, 1], "proto_object_detector.json: successor offsets mismatch")
    _require(detector["succession"].get("confirmation_lag_ticks") == 1, "proto_object_detector.json: successor lag mismatch")
    _require(detector["succession"].get("predicate") == "isolated_active_dyad", "proto_object_detector.json: successor predicate mismatch")
    _require(detector["succession"].get("seed_attribution_required") is True, "proto_object_detector.json: successor attribution mismatch")
    _require_json_equal(
        detector.get("formation"),
        {
            "initial_state_must_fail": True,
            "time_order": "ascending from 1 through 16",
            "qualification": "the first full role, succession, attribution, and outward-effect pass defines formation",
        },
        "proto_object_detector.json: formation semantics mismatch",
    )
    _require_json_equal(
        detector.get("seed_attribution"),
        {"baseline": "matched_all_zero", "requirement": "both active witness loci equal 0 in the baseline at the same layer"},
        "proto_object_detector.json: seed attribution mismatch",
    )
    _require(detector["succession"].get("selection_order") == "smallest nonnegative forward anchor offset", "proto_object_detector.json: successor selection mismatch")
    interventions = detector["matched_interventions"]
    _require(interventions.get("window_offsets") == [0, 1, 2], "proto_object_detector.json: intervention window mismatch")
    _require(interventions.get("natural_precondition") == [1, 1, 0], "proto_object_detector.json: natural precondition mismatch")
    _require(interventions.get("external_eligibility_guard") == {"offset": 3, "value": 0}, "proto_object_detector.json: external guard mismatch")
    _require(interventions.get("role_preserving_sham") == [0, 1, 1], "proto_object_detector.json: sham mismatch")
    _require(interventions.get("role_breaking_arm") == [1, 0, 1], "proto_object_detector.json: breaking arm mismatch")
    _require(interventions.get("hamming_distance_from_natural_each") == 2, "proto_object_detector.json: intervention distance mismatch")
    _require(interventions.get("active_count_in_window_each") == 2, "proto_object_detector.json: intervention active-count mismatch")
    _require(interventions.get("application_layer") == "formation layer t", "proto_object_detector.json: intervention layer mismatch")
    _require(interventions.get("outside_window") == "unchanged, including the quiescent offset +3 guard", "proto_object_detector.json: outside-window semantics mismatch")
    _require(interventions.get("law_topology_schedule") == "unchanged", "proto_object_detector.json: intervention law/topology mismatch")
    _require(detector["reachable_future_variable"].get("observation_layer") == "t+2", "proto_object_detector.json: observation layer mismatch")
    _require_json_equal(detector["reachable_future_variable"].get("alphabet"), [0, 1], "proto_object_detector.json: endpoint alphabet mismatch")
    _require_json_equal(
        detector.get("tie_breaking"),
        {"formation_time": "earliest", "anchor": "smallest forward distance from the translated seed origin", "successor": "smallest eligible forward offset"},
        "proto_object_detector.json: tie breaking mismatch",
    )
    _require(detector["reachable_future_variable"].get("id") == "first_forward_external_event_at_t_plus_2", "proto_object_detector.json: endpoint id mismatch")
    _require(detector["reachable_future_variable"].get("pass_rule") == "role-preserving sham and role-breaking arm have different exact values", "proto_object_detector.json: endpoint pass rule mismatch")
    _require(detector.get("candidate_pass_rule") == "the earliest formation time with an attributed dyad, an attributed eligible successor dyad, and a passing outward causal endpoint is T_proto", "proto_object_detector.json: candidate pass rule mismatch")
    _require(detector.get("failure_value") == "right_censored_gt_16 unless a separate analytic or exact-cycle proof establishes nonproduction", "proto_object_detector.json: failure semantics mismatch")

    fixtures = documents["detector_fixtures.json"]
    _require(len(fixtures.get("role_cases", [])) >= 5, "detector_fixtures.json: missing role cases")
    _require(any(case.get("id") == "nonquiescent_external_guard_is_ineligible" for case in fixtures.get("intervention_cases", [])), "detector_fixtures.json: missing external-guard case")

    result_schema = documents["result.schema.json"]
    _require(result_schema.get("type") == "object", "result.schema.json: root type mismatch")
    _require(result_schema.get("additionalProperties") is False, "result.schema.json: root must be closed")
    result_properties = result_schema["properties"]
    _require(result_properties["contract_version"].get("const") == "0.2-draft", "result.schema.json: version mismatch")
    _require(result_properties["data_class"].get("const") == "development", "result.schema.json: data class mismatch")
    _require_json_equal(result_properties["translation_offsets"].get("const"), list(range(48)), "result.schema.json: development allocation mismatch")
    _require(result_properties["held_out_accessed"].get("const") is False, "result.schema.json: held-out access must be false")
    _require_json_equal(result_properties["held_out_offsets_evaluated"].get("const"), [], "result.schema.json: held-out offsets must be empty")
    _require(result_properties["formation_horizon_ticks"].get("const") == 16, "result.schema.json: horizon mismatch")
    _require(result_properties["candidate_results"].get("minItems") == 16, "result.schema.json: candidate minimum mismatch")
    _require(result_properties["candidate_results"].get("maxItems") == 16, "result.schema.json: candidate maximum mismatch")
    _require_json_equal(
        result_properties["evaluated_shells"].get("enum"),
        [[1], [1, 2], [1, 2, 3], [1, 2, 3, 4]],
        "result.schema.json: evaluated-shell alternatives mismatch",
    )
    _require_json_equal(
        result_properties["stopping_reason"].get("enum"),
        [
            "first_shell_with_pass_by_H16_completed",
            "all_bounded_shells_completed_without_pass_by_H16",
        ],
        "result.schema.json: stopping reasons mismatch",
    )
    _require(len(result_schema.get("allOf", [])) == 5, "result.schema.json: shell-allocation conditions mismatch")
    candidate_result_schema = result_schema["$defs"]["candidate_result"]
    _require(candidate_result_schema.get("additionalProperties") is False, "result.schema.json: candidate results must be closed")
    _require(len(candidate_result_schema.get("oneOf", [])) == 4, "result.schema.json: candidate status branches mismatch")

    partitions = documents["partitions.json"]
    development = partitions["development"]["translation_offsets"]
    held_out = partitions["held_out"]["translation_offsets"]
    _require((development["first"], development["last"], development["count"]) == (0, 47, 48), "partitions.json: development allocation mismatch")
    _require((held_out["first"], held_out["last"], held_out["count"]) == (48, 63, 16), "partitions.json: held-out allocation mismatch")
    _require(partitions.get("analysis_unit") == "translation of the single-active initial condition on the fixed directed cycle", "partitions.json: analysis unit mismatch")
    _require(partitions["development"].get("access") == "allowed only after the development run seal passes", "partitions.json: development access mismatch")
    _require(partitions["held_out"].get("access") == "forbidden in v0.2-draft", "partitions.json: held-out access mismatch")
    _require(partitions.get("expected_invariance") == "every translation must give the exactly translated trajectory and identical detector result", "partitions.json: invariance rule mismatch")
    _require(partitions.get("interpretation_limit") == "the reserved offsets are algebraically implied by exact cycle-translation equivariance; the split is implementation bookkeeping only and cannot provide confirmation or statistical generalization", "partitions.json: interpretation limit mismatch")

    plan = documents["search_plan.json"]
    _require(plan.get("status") == "outcomes_sealed", "search_plan.json: outcomes must remain sealed")
    _require(plan.get("fixed_normalized_n_p") == 2, "search_plan.json: N_P mismatch")
    _require("reserved translation offsets 48..63 are algebraically implied by equivariance and cannot provide independent confirmation" in plan.get("claim_limits", []), "search_plan.json: reserved-offset claim limit missing")
    _require_json_equal(plan.get("objective_order"), ["normalized_n_p", "atomic_n_l", "t_proto"], "search_plan.json: objective order mismatch")
    _require(plan["enumeration"].get("candidate_count_maximum") == 16, "search_plan.json: candidate budget mismatch")
    _require(plan["enumeration"].get("signature_order") == ["00", "01", "10", "11"], "search_plan.json: enumeration order mismatch")
    _require_json_equal(plan["enumeration"].get("shell_sizes_by_n_l"), {"0": 1, "1": 4, "2": 6, "3": 4, "4": 1}, "search_plan.json: shell sizes mismatch")
    _require_json_equal(plan["development_run"].get("translation_offsets"), {"first": 0, "last": 47, "count": 48}, "search_plan.json: development offsets mismatch")
    _require(plan["development_run"].get("formation_horizon_ticks") == 16, "search_plan.json: formation horizon mismatch")
    _require(plan["enumeration"].get("candidate_order") == "increasing law count, then lexicographic ordered signature tuple", "search_plan.json: candidate order mismatch")
    _require(plan["development_run"].get("last_required_layer") == 18, "search_plan.json: required layer mismatch")
    _require(plan["development_run"].get("eligibility_endpoint") == "formation_by_H16", "search_plan.json: bounded endpoint mismatch")
    _require(plan["development_run"].get("outcome_arithmetic") == "exact deterministic", "search_plan.json: outcome arithmetic mismatch")
    _require(plan["development_run"].get("seeded_base_site_evaluation_budget_maximum") == 884736, "search_plan.json: seeded budget mismatch")
    _require(plan["development_run"].get("matched_baseline_base_site_evaluation_budget_maximum") == 884736, "search_plan.json: baseline budget mismatch")
    _require(plan["development_run"].get("development_open_manifest_path") == "experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/development_open_manifest.json", "search_plan.json: development-open path mismatch")
    _require(plan["development_run"].get("result_schema") == "result.schema.json", "search_plan.json: result schema ref mismatch")
    _require(plan["development_run"].get("result_path") == "output/minimal_realization/MIR-REFERENCE-SEARCH-001/development_results.json", "search_plan.json: result path mismatch")
    _require(plan["development_run"].get("translation_pass_aggregation") == "all 48 development translations must have exactly translated seeded trajectories, translation-invariant matched baselines, and identical pass status and T_proto with translated anchors; any mismatch is an implementation failure", "search_plan.json: translation aggregation mismatch")
    _require(plan["development_run"].get("stopping_rule") == "for the bounded endpoint only, evaluate every candidate in the first shell containing a pass by H=16, then stop; if no bounded shell passes, stop after N_L=4 with all 15 evaluated N_L=1..4 candidates right-censored and N_L=0 retained as analytically excluded", "search_plan.json: stopping rule mismatch")
    _require(plan["held_out_run"].get("runner_command_available") is False, "search_plan.json: held-out runner must be unavailable")
    expected_refs = {
        "atomic_operator_alphabet": "operator_alphabet.json",
        "charged_topology": "topology.json",
        "registered_causal_cone": "causal_cone.json",
        "held_out_allocation": "partitions.json",
    }
    for key, expected in expected_refs.items():
        _require(plan["frozen_design_choices"].get(key) == expected, f"search_plan.json: {key} ref mismatch")
    _require(plan.get("remaining_open_seal_requirements") == ["record_outcome_free_preregistration_commit"], "search_plan.json: remaining seal requirements mismatch")
    _require(plan.get("opening_rule") == "this immutable search plan remains outcomes_sealed; only a separate development_open manifest created after the outcome-free preregistration commit and itself committed may authorize the fixed development run", "search_plan.json: opening rule mismatch")

    exclusions = documents["lower_shell_exclusions.json"]
    exclusion_records = exclusions.get("exclusions", [])
    _require([item.get("id") for item in exclusion_records] == ["MIR-EXCLUDE-NP0", "MIR-EXCLUDE-NP1", "MIR-EXCLUDE-NP2-NL0"], "lower_shell_exclusions.json: exclusion set mismatch")
    _require_json_equal([item.get("quantified_shell") for item in exclusion_records], [{"normalized_n_p": 0, "atomic_n_l": "all"}, {"normalized_n_p": 1, "atomic_n_l": "all"}, {"normalized_n_p": 2, "atomic_n_l": 0}], "lower_shell_exclusions.json: quantified shells mismatch")
    null_candidate = documents["lower_shell_null.json"]
    _require(null_candidate.get("candidate_id") == "MIR-P2-L0-NONE", "lower_shell_null.json: candidate id mismatch")
    _require(null_candidate.get("laws") == [], "lower_shell_null.json: null candidate has laws")

    from .detector import FORMATION_HORIZON, LAST_REQUIRED_LAYER
    from .dynamics import CYCLE_SIZE
    from .search import SIGNATURE_ORDER, enumerate_rule_rows

    _require(CYCLE_SIZE == topology["loci"]["count"], "implementation/spec cycle-size mismatch")
    _require(FORMATION_HORIZON == cone["formation_horizon_ticks"], "implementation/spec horizon mismatch")
    _require(LAST_REQUIRED_LAYER == cone["required_layers"]["last"], "implementation/spec last-layer mismatch")
    _require(list(SIGNATURE_ORDER) == alphabet["signatures"], "implementation/spec signature-order mismatch")
    _require(len(enumerate_rule_rows()) == alphabet["candidate_rule_space"]["candidate_count"], "implementation/spec rule-space mismatch")

    return DesignAudit(
        spec_dir=spec_dir,
        contract_version="0.2-draft",
        search_id=plan["search_id"],
        status=plan["status"],
        hashes=hashes,
    )
