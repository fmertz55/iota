from __future__ import annotations

import csv
import math
import sys

from build_evidence import outputs
from evidence_common import (
    ROOT,
    evidence_metrics,
    load_gc001,
    load_gc002,
    load_gc003,
    load_gc004,
    load_gc005,
    load_gc006,
    load_gc007,
    load_gc008,
    load_gc009,
    load_registry,
    sha256,
    strict_events,
)


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    definitions = load_registry(ROOT / "evidence" / "definitions.yaml")
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    definition_ids = [item["id"] for item in definitions.get("definitions", [])]
    if len(definition_ids) != len(set(definition_ids)):
        fail("definition IDs must be unique", errors)

    claim_ids = [item["id"] for item in claims.get("claims", [])]
    if len(claim_ids) != len(set(claim_ids)):
        fail("claim IDs must be unique", errors)

    for claim in claims.get("claims", []):
        for definition_id in claim.get("definitions", []):
            if definition_id not in definition_ids:
                fail(f"{claim['id']} references unknown definition {definition_id}", errors)
        for relative in [
            *claim.get("evidence", []),
            *claim.get("supporting_analysis", []),
            claim.get("analysis", ""),
            claim.get("instrumentation", ""),
        ]:
            if not relative:
                continue
            if not relative or not (ROOT / relative).is_file():
                fail(f"{claim['id']} references missing file {relative}", errors)

    claim, summary, events = load_gc001()
    metrics = evidence_metrics(summary, events)
    for name, expected in claim["expected"].items():
        if name.startswith("strict_") and name not in metrics:
            continue
        if metrics.get(name) != expected:
            fail(f"GC-001 expected {name}={expected!r}, observed {metrics.get(name)!r}", errors)

    strict = strict_events(events)
    strict_checks = {
        "bridge_path_jaccard": "strict_bridge_jaccard",
        "preloss_reachable_pair_fraction": "strict_preloss_reachability",
        "split_reachable_pair_fraction": "strict_split_reachability",
        "rebridge_reachable_pair_fraction": "strict_rebridge_reachability",
        "successor_removed_reachable_pair_fraction": "strict_successor_removed_reachability",
        "mean_preloss_shortest_path": "strict_preloss_shortest_path",
        "mean_rebridge_shortest_path": "strict_rebridge_shortest_path",
    }
    for index, row in enumerate(strict, start=1):
        for column, expected_name in strict_checks.items():
            observed = float(row[column])
            expected = float(claim["expected"][expected_name])
            if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=1e-12):
                fail(f"GC-001 strict event {index} {column}={observed}, expected {expected}", errors)

    _, gc002_summary, gc002_cases = load_gc002()
    gc002_strict = [
        row for row in gc002_cases if row["finding060_constraint_transport"] == "1"
    ]
    gc002_failures = [
        row for row in gc002_cases if row["finding060_constraint_transport"] == "0"
    ]
    observed_lifetimes = [int(row["continuous_relation_lifetime"]) for row in gc002_strict]
    if observed_lifetimes != [9, 3, 51]:
        fail(f"GC-002 strict lifetimes changed: {observed_lifetimes}", errors)
    if any(int(row["continuous_relation_lifetime"]) != 0 for row in gc002_failures):
        fail("GC-002 role-bearing failure acquired positive relation lifetime", errors)
    if int(gc002_summary["second_strict_transport_cases"]) != 0:
        fail("GC-002 second strict transport count changed", errors)
    if not gc002_summary["all_payload_zero"] or not gc002_summary["all_ledger_exact"]:
        fail("GC-002 safety invariant failed", errors)

    _, gc003_summary, gc003_cases = load_gc003()
    gc003_strict = [
        row for row in gc003_cases if row["finding060_constraint_transport"] == "1"
    ]
    gc003_failures = [
        row for row in gc003_cases if row["finding060_constraint_transport"] == "0"
    ]
    expression_lifetimes = [
        int(row["expression_relation_lifetime"]) for row in gc003_strict
    ]
    if expression_lifetimes != [170, 601, 51]:
        fail(f"GC-003 expression lifetimes changed: {expression_lifetimes}", errors)
    survival = [
        int(row["singleton_expression_survives_address_loss"]) for row in gc003_strict
    ]
    if survival != [1, 1, 0]:
        fail(f"GC-003 singleton survival pattern changed: {survival}", errors)
    if any(int(row["expression_relation_lifetime"]) != 0 for row in gc003_failures):
        fail("GC-003 role-bearing failure acquired positive expression lifetime", errors)
    if not gc003_summary["instrumentation_equivalence_passed"]:
        fail("GC-003 instrumentation equivalence gate failed", errors)
    if int(gc003_summary["lineage_collision_cases"]) != 0:
        fail("GC-003 contains a lineage collision", errors)
    if int(gc003_summary["second_strict_transport_cases"]) != 0:
        fail("GC-003 second strict transport count changed", errors)
    if not gc003_summary["all_payload_zero"] or not gc003_summary["all_ledger_exact"]:
        fail("GC-003 safety invariant failed", errors)
    with (ROOT / "output/findings/finding062/expression_lineage_ancestry.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        gc003_ancestry = list(csv.DictReader(handle))
    first_handoff = [
        row
        for row in gc003_ancestry
        if row["init_seed"] == "46"
        and row["start_offset"] == "61"
        and row["offset"] == "74"
        and row["lineage_role"] == "singleton"
    ]
    if len(first_handoff) != 1:
        fail(f"GC-003 expected one first singleton handoff, observed {len(first_handoff)}", errors)
    elif (
        first_handoff[0]["source"] != "17:28:25"
        or first_handoff[0]["target"] != "17:29:25"
        or first_handoff[0]["source_active_after"] != "0"
        or first_handoff[0]["target_depleted_before"] != "1"
    ):
        fail(f"GC-003 first singleton handoff changed: {first_handoff[0]}", errors)

    _, gc004_summary, gc004_aggregate = load_gc004()
    gc004_counts = [
        (int(row["handoff_successes"]), int(row["eligible_address_loss_branches"]))
        for row in gc004_aggregate
    ]
    if gc004_counts != [(16, 32), (29, 32), (28, 32)]:
        fail(f"GC-004 handoff counts changed: {gc004_counts}", errors)
    if any(int(row["censored_branches"]) != 0 for row in gc004_aggregate):
        fail("GC-004 acquired censored address-loss branches", errors)
    if any(int(row["ambiguous_collision_branches"]) != 0 for row in gc004_aggregate):
        fail("GC-004 contains ambiguous lineage collisions", errors)
    comparisons = gc004_summary["comparisons"]
    expected_p = [
        0.0007517055787029017,
        0.002514409181299679,
        1.0,
    ]
    observed_p = [float(row["fisher_exact_two_sided_p"]) for row in comparisons]
    if any(
        not math.isclose(observed, expected, rel_tol=0.0, abs_tol=1e-15)
        for observed, expected in zip(observed_p, expected_p)
    ):
        fail(f"GC-004 Fisher comparisons changed: {observed_p}", errors)
    if not gc004_summary["all_payload_zero"] or not gc004_summary["all_ledger_exact"]:
        fail("GC-004 safety invariant failed", errors)

    _, gc005_summary = load_gc005()
    gc005_model = gc005_summary["model"]
    if (
        gc005_model["feature"] != "singleton_lineage_size"
        or not math.isclose(float(gc005_model["threshold"]), 1.5)
        or gc005_model["direction"] != "gt_positive"
    ):
        fail(f"GC-005 frozen model changed: {gc005_model}", errors)
    held = gc005_summary["held_out_metrics"]
    confusion_values = (
        int(held["true_positive"]),
        int(held["false_positive"]),
        int(held["true_negative"]),
        int(held["false_negative"]),
    )
    if confusion_values != (13, 0, 12, 23):
        fail(f"GC-005 held-out confusion changed: {confusion_values}", errors)
    if not math.isclose(
        float(gc005_summary["held_out_fisher_exact_two_sided_p"]),
        0.02101034894988829,
        rel_tol=0.0,
        abs_tol=1e-15,
    ):
        fail("GC-005 held-out Fisher association changed", errors)
    if int(gc005_summary["collision_rows"]) != 0:
        fail("GC-005 contains lineage collision rows", errors)
    if not gc005_summary["all_payload_zero"] or not gc005_summary["all_ledger_exact"]:
        fail("GC-005 safety invariant failed", errors)

    _, gc006_summary = load_gc006()
    gc006_model = gc006_summary["model"]
    if (
        gc006_model["feature"] != "cube26_active_neighbors"
        or not math.isclose(float(gc006_model["threshold"]), 1.5)
        or gc006_model["direction"] != "le_positive"
    ):
        fail(f"GC-006 frozen model changed: {gc006_model}", errors)
    confirmation = gc006_summary["confirmation_metrics"]
    confirmation_confusion = (
        int(confirmation["true_positive"]),
        int(confirmation["false_positive"]),
        int(confirmation["true_negative"]),
        int(confirmation["false_negative"]),
    )
    if confirmation_confusion != (39, 12, 8, 12):
        fail(f"GC-006 confirmation confusion changed: {confirmation_confusion}", errors)
    if int(gc006_summary["confirmation_eligible_single_address_rows"]) != 71:
        fail("GC-006 eligible confirmation count changed", errors)
    if int(gc006_summary["confirmation_excluded_preexisting_descendant_rows"]) != 25:
        fail("GC-006 excluded confirmation count changed", errors)
    if not math.isclose(
        float(gc006_summary["confirmation_fisher_exact_two_sided_p"]),
        0.24025519393948105,
        rel_tol=0.0,
        abs_tol=1e-15,
    ):
        fail("GC-006 confirmation Fisher result changed", errors)
    if int(gc006_summary["collision_rows"]) != 0:
        fail("GC-006 contains lineage collision rows", errors)
    if not gc006_summary["all_payload_zero"] or not gc006_summary["all_ledger_exact"]:
        fail("GC-006 safety invariant failed", errors)

    _, gc007_summary, gc007_replay = load_gc007()
    expected_classes = {
        "activated_child": 57,
        "gate_failed": 3,
        "preexisting_descendant": 16,
        "source_exhausted": 19,
        "target_preempted": 1,
    }
    if int(gc007_summary["branches"]) != 96 or gc007_summary["outcome_classes"] != expected_classes:
        fail(f"GC-007 terminal accounting changed: {gc007_summary['outcome_classes']}", errors)
    if not gc007_summary["equivalence_gate_passed"] or not gc007_summary["all_cases_accounted"]:
        fail("GC-007 equivalence or accounting gate failed", errors)
    if int(gc007_summary["collision_cases"]) != 0:
        fail("GC-007 contains lineage collision cases", errors)
    if not gc007_summary["all_payload_zero"] or not gc007_summary["all_ledger_exact"]:
        fail("GC-007 safety invariant failed", errors)
    if not gc007_replay["exactly_one_gate_overridden"] or not gc007_replay["handoff_flipped"]:
        fail("GC-007 causal replay no longer flips handoff", errors)
    if gc007_replay["frozen_intervention"]["natural_gate_passed"]:
        fail("GC-007 frozen intervention was not a naturally failed gate", errors)

    _, gc008_same, gc008_screen, gc008_independent = load_gc008()
    same_by_label = {row["natural_label"]: row for row in gc008_same["aggregate"]}
    expected_same = {
        "gate_failed": (6, 6, 6, 6),
        "source_exhausted": (30, 30, 3, 28),
        "target_preempted": (0, 0, 0, 0),
    }
    for label, expected in expected_same.items():
        row = same_by_label[label]
        observed = (
            int(row["eligible_replays"]), int(row["route_reopened"]),
            int(row["immediate_child"]), int(row["eventual_handoff"]),
        )
        if observed != expected:
            fail(f"GC-008 same-state {label} changed: {observed}", errors)
    if int(gc008_same["natural_branches"]) != 192 or int(gc008_same["eligible_replays"]) != 36:
        fail("GC-008 same-state cohort size changed", errors)
    if not all(
        gc008_same[key]
        for key in (
            "all_shams_exact", "all_exactly_one_override", "all_payload_zero",
            "all_ledger_exact", "all_natural_payload_zero", "all_natural_ledger_exact",
        )
    ) or int(gc008_same["collision_replays"]) != 0:
        fail("GC-008 same-state safety or intervention invariant failed", errors)

    screen_expected = (128, 128, 29, 4, 4, 2)
    screen_observed = (
        int(gc008_screen["cases"]), int(gc008_screen["unique_continuation_streams"]),
        int(gc008_screen["class_b_candidates"]), int(gc008_screen["strict_transport_events"]),
        int(gc008_screen["singleton_eligible_sources"]), int(gc008_screen["frozen_primary_sources"]),
    )
    if screen_observed != screen_expected or not gc008_screen["screen_complete"]:
        fail(f"GC-008 independent screen changed: {screen_observed}", errors)
    if not all(
        gc008_screen[key]
        for key in (
            "all_classification_payload_zero", "all_classification_ledgers_exact",
            "all_transport_payload_zero", "all_transport_ledgers_exact",
        )
    ):
        fail("GC-008 independent screen safety invariant failed", errors)

    if (
        int(gc008_independent["selected_sources"]) != 2
        or int(gc008_independent["natural_branches"]) != 64
        or int(gc008_independent["eligible_replays"]) != 10
        or gc008_independent["source_manifest_sha256"]
        != "15ed649a3db93492e1b2cbe4ea72261c10717cf2cdb6a07f6df6eb25b59d717e"
    ):
        fail("GC-008 independent causal cohort or frozen manifest changed", errors)
    frozen_manifest = ROOT / "output/findings/finding067/independent_geometry_screen_source_manifest.csv"
    if sha256(frozen_manifest) != "15ed649a3db93492e1b2cbe4ea72261c10717cf2cdb6a07f6df6eb25b59d717e":
        fail("GC-008 frozen source-manifest bytes changed", errors)
    independent_rows = {
        (row["source_id"], row["natural_label"]): row
        for row in gc008_independent["source_aggregate"]
    }
    independent_expected = {
        ("f067b-source-001", "source_exhausted"): (1, 1, 0, 0),
        ("f067b-source-002", "gate_failed"): (8, 8, 8, 8),
        ("f067b-source-002", "target_preempted"): (1, 1, 0, 1),
    }
    for key, expected in independent_expected.items():
        row = independent_rows[key]
        observed = (
            int(row["eligible_replays"]), int(row["route_reopened"]),
            int(row["immediate_child"]), int(row["eventual_handoff"]),
        )
        if observed != expected:
            fail(f"GC-008 independent {key} changed: {observed}", errors)
    if not all(
        gc008_independent[key]
        for key in ("all_shams_exact", "all_exactly_one_override", "all_payload_zero", "all_ledger_exact")
    ) or int(gc008_independent["collision_replays"]) != 0:
        fail("GC-008 independent safety or intervention invariant failed", errors)

    _, gc009_freeze, gc009_summary, gc009_replays = load_gc009()
    selector_hash = "9e4a70d8d0b829b4a4b288da69b8a740c398b5c161a0e5a26a7605015e8c8cb0"
    if (
        gc009_freeze["counterfactual_outcomes_run"] is not False
        or int(gc009_freeze["natural_branches"]) != 256
        or int(gc009_freeze["eligible_selectors"]) != 164
        or gc009_freeze["natural_child_multiplicity"] != {"1": 164}
        or gc009_freeze["selectors_sha256"] != selector_hash
    ):
        fail("GC-009 factual selector freeze changed", errors)
    selector_path = ROOT / "output/findings/finding068/realization_necessity_selectors.csv"
    if sha256(selector_path) != selector_hash:
        fail("GC-009 committed selector-manifest bytes changed", errors)
    if gc009_summary["selector_manifest_sha256"] != selector_hash:
        fail("GC-009 replay did not consume frozen selector manifest", errors)
    if gc009_summary["alternate_child_timing"] != {"delayed": 117, "none": 42, "same_tick": 5}:
        fail("GC-009 alternate-child timing changed", errors)
    if gc009_summary["address_endpoints"] != {
        "handoff_at_first_address_loss": 122,
        "lineage_loss_at_first_address_loss": 42,
    }:
        fail("GC-009 address endpoints changed", errors)
    if len(gc009_replays) != 164:
        fail("GC-009 replay count changed", errors)
    capacity_retained = sum(int(row["source_capacity_retained_after_veto"]) for row in gc009_replays)
    first_same_target = sum(
        row["first_alternate_child_target"] != ""
        and row["first_alternate_child_target"] == row["selector_target"]
        for row in gc009_replays
    )
    timing_endpoint_mismatches = sum(
        (row["alternate_child_timing"] == "none")
        != (row["address_endpoint"] == "lineage_loss_at_first_address_loss")
        for row in gc009_replays
    )
    if capacity_retained != 161 or first_same_target != 17 or timing_endpoint_mismatches != 0:
        fail(
            "GC-009 mediator details changed: "
            f"capacity={capacity_retained} same_target={first_same_target} mismatches={timing_endpoint_mismatches}",
            errors,
        )
    expected_sources = {
        "original-seed46-start61": (33, 17),
        "original-seed46-start420": (39, 31),
        "original-seed56-start106": (36, 31),
        "f067b-source-001": (30, 23),
        "f067b-source-002": (26, 20),
    }
    observed_sources = {
        source_id: (
            sum(row["source_id"] == source_id for row in gc009_replays),
            sum(row["source_id"] == source_id and int(row["eventual_handoff"]) == 1 for row in gc009_replays),
        )
        for source_id in expected_sources
    }
    if observed_sources != expected_sources:
        fail(f"GC-009 per-source outcomes changed: {observed_sources}", errors)
    if not all(
        gc009_summary[key]
        for key in (
            "all_shams_exact", "all_world_and_rng_exact_through_selector",
            "all_selector_identities_exact", "all_exactly_one_override",
            "all_payload_zero", "all_ledger_exact",
        )
    ) or int(gc009_summary["collision_replays"]) != 0:
        fail("GC-009 safety or intervention invariant failed", errors)

    for path, expected_content in outputs().items():
        if not path.is_file():
            fail(f"generated file missing: {path.relative_to(ROOT)}", errors)
        elif path.read_text(encoding="utf-8") != expected_content:
            fail(f"generated file stale: {path.relative_to(ROOT)}", errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Evidence valid: {len(claim_ids)} claim(s), {len(definition_ids)} definition(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
