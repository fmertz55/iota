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
    load_registry,
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
