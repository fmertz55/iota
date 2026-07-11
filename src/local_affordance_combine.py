from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from component_bridge_causal_trace import write_csv
from experiment_db import artifact_hash
from independent_geometry_screen import (
    CASE_FIELDNAMES,
    CONFIG_FIELDNAMES,
    SEED_AGGREGATE_FIELDNAMES,
    SIGNAL_FIELDNAMES,
    SOURCE_MANIFEST_FIELDNAMES,
    TRANSPORT_FIELDNAMES,
    artifact_paths,
)
from local_affordance_features import read_csv


DEFAULT_F071 = Path("output/findings/finding071/local_affordance_screen")
DEFAULT_F072 = Path("output/findings/finding072/local_affordance_acquisition")
DEFAULT_OUTPUT = Path("output/findings/finding072/local_affordance_combined")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze the Finding 072 combined discovery/confirmation cohort."
    )
    parser.add_argument("--finding071-prefix", type=Path, default=DEFAULT_F071)
    parser.add_argument("--finding072-prefix", type=Path, default=DEFAULT_F072)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-f071-source-sha256", required=True)
    parser.add_argument("--expected-f072-source-sha256", required=True)
    return parser.parse_args()


def path(prefix: Path, suffix: str) -> Path:
    return prefix.with_name(prefix.name + suffix)


def main() -> None:
    args = parse_args()
    f071_summary = json.loads(
        path(args.finding071_prefix, "_summary.json").read_text(encoding="utf-8")
    )
    f072_summary = json.loads(
        path(args.finding072_prefix, "_summary.json").read_text(encoding="utf-8")
    )
    f071_source_path = path(args.finding071_prefix, "_source_manifest.csv")
    f072_source_path = path(args.finding072_prefix, "_source_manifest.csv")
    checks = {
        "f071_hash": artifact_hash(f071_source_path)
        == args.expected_f071_source_sha256,
        "f072_hash": artifact_hash(f072_source_path)
        == args.expected_f072_source_sha256,
        "f071_stopped": f071_summary.get("source_support_gate_met") is False,
        "f072_complete": f072_summary.get("screen_complete") is True,
        "f072_acquisition": f072_summary.get("acquisition_batch") is True,
        "f072_gate": f072_summary.get("acquisition_gate_met") is True,
        "responses_unrun": f072_summary.get("affordance_responses_run") is False,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Finding 072 combined freeze failed: {checks}")

    suffix_fields = {
        "_cases.csv": CASE_FIELDNAMES,
        "_signals.csv": SIGNAL_FIELDNAMES,
        "_transport_events.csv": TRANSPORT_FIELDNAMES,
        "_source_manifest.csv": SOURCE_MANIFEST_FIELDNAMES,
        "_seed_aggregate.csv": SEED_AGGREGATE_FIELDNAMES,
        "_config_manifest.csv": CONFIG_FIELDNAMES,
    }
    combined: dict[str, list[dict[str, Any]]] = {}
    for suffix in suffix_fields:
        combined[suffix] = [
            *read_csv(path(args.finding071_prefix, suffix)),
            *read_csv(path(args.finding072_prefix, suffix)),
        ]

    source_rows = combined["_source_manifest.csv"]
    selected = [row for row in source_rows if int(row["frozen_source_selected"]) == 1]
    selected.sort(key=lambda row: int(row["init_seed"]))
    for index, row in enumerate(selected, start=1):
        row["source_index"] = index
    for index, row in enumerate(source_rows, start=1):
        row["candidate_index"] = index
    discovery = [row for row in selected if int(row["init_seed"]) <= 168]
    confirmation = [row for row in selected if int(row["init_seed"]) >= 169]
    new_confirmation = [row for row in selected if int(row["init_seed"]) >= 233]
    support = len(discovery) >= 6 and len(confirmation) >= 6 and len(new_confirmation) >= 3
    if not support:
        raise RuntimeError("Finding 072 combined source-support gate changed")

    paths = artifact_paths(args.output_prefix)
    for suffix, fields in suffix_fields.items():
        key = {
            "_cases.csv": "case_csv",
            "_signals.csv": "signal_csv",
            "_transport_events.csv": "transport_csv",
            "_source_manifest.csv": "source_manifest_csv",
            "_seed_aggregate.csv": "seed_aggregate_csv",
            "_config_manifest.csv": "config_manifest_csv",
        }[suffix]
        write_csv(paths[key], fields, combined[suffix])

    summary = {
        "finding": "072B",
        "screen_complete": True,
        "combined_cohort_freeze": True,
        "protocol_frozen_before_affordance_responses": True,
        "affordance_branch_or_veto_outcomes_inspected_for_selection": False,
        "source_support_gate_met": True,
        "minimum_sources_per_split": 6,
        "frozen_primary_sources": len(selected),
        "discovery_sources": len(discovery),
        "confirmation_sources": len(confirmation),
        "new_confirmation_sources": len(new_confirmation),
        "selected_initialization_seeds": [int(row["init_seed"]) for row in selected],
        "finding071_source_manifest_sha256": artifact_hash(f071_source_path),
        "finding072_source_manifest_sha256": artifact_hash(f072_source_path),
        "cases": len(combined["_cases.csv"]),
        "signal_intervals": len(combined["_signals.csv"]),
        "class_b_candidates": len(combined["_transport_events.csv"]),
        "strict_transport_events": sum(
            int(row["constraint_transport"])
            for row in combined["_transport_events.csv"]
        ),
        "singleton_eligible_sources": sum(
            int(row["singleton_eligible"]) for row in source_rows
        ),
        "all_classification_payload_zero": all(
            int(row["payload_zero_all_offsets"])
            for row in combined["_cases.csv"]
        ),
        "all_classification_ledgers_exact": all(
            int(row["ledger_exact_all_offsets"])
            for row in combined["_cases.csv"]
        ),
        "all_transport_payload_zero": all(
            int(row["payload_zero_all_observed_offsets"])
            for row in combined["_transport_events.csv"]
        ),
        "all_transport_ledgers_exact": all(
            int(row["ledger_exact_all_observed_offsets"])
            for row in combined["_transport_events.csv"]
        ),
        "artifacts": {
            name: {"path": str(value), "sha256": artifact_hash(value)}
            for name, value in paths.items()
            if name != "summary_json"
        },
        "affordance_responses_run": False,
    }
    paths["summary_json"].parent.mkdir(parents=True, exist_ok=True)
    paths["summary_json"].write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
