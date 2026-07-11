from __future__ import annotations

import math
import sys

from build_evidence import outputs
from evidence_common import ROOT, evidence_metrics, load_gc001, load_registry, strict_events


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
        for relative in [*claim.get("evidence", []), claim.get("analysis", "")]:
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
