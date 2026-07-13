from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from component_bridge_causal_trace import write_csv
from experiment_db import artifact_hash
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from iota_rig import load_config
from phase_free_class_matrix import run_to_checkpoint
from successor_graph_rewire_audit import FIELDS as AUDIT_FIELDS
from successor_graph_rewire_audit import audit_channel
from successor_graph_role_audit import config_for_seed


DEFAULT_CASES = Path("output/findings/finding079/factorial_channel_cases.csv")
DEFAULT_OUTPUT_PREFIX = Path("output/findings/finding079/factorial_common_donor")
FROZEN_CASES_SHA256 = "6ac39d7af9833b5690a962dc8813e928e3ee106f695775367f7249188eedad94"
MINIMUM_INDEPENDENT_CHANNELS = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze Finding 079 common-donor pairs without branch outcomes."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def read_csv_with_fields(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


IDENTITY_FIELDS = {"channel_id", "init_seed", "sample_index", "precursor_offset"}
AUDIT_EXTRA = [field for field in AUDIT_FIELDS if field not in IDENTITY_FIELDS]
OUTPUT_EXTRA = [
    "paired_channel_selected", "paired_channel_index", "paired_channel_id",
    *[f"rewire_{field}" for field in AUDIT_EXTRA],
]


def selection_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(row["sample_index"]), int(row["split_offset"]),
        int(row["rebridge_offset"]), int(row["precursor_offset"]),
        row["precursor_source"], row["precursor_target"],
    )


def run_seed_job(
    job: tuple[str, int, list[dict[str, str]]]
) -> list[tuple[dict[str, str], dict[str, Any]]]:
    config_path, seed, cases = job
    canonical = load_config(config_path)
    cfg = config_for_seed(canonical, seed)
    checkpoint = run_to_checkpoint(
        cfg, cases[0]["variant"], int(cases[0]["checkpoint_tick"])
    )
    output: list[tuple[dict[str, str], dict[str, Any]]] = []
    for case in cases:
        labeled = dict(case)
        labeled["channel_id"] = case["candidate_id"]
        audit = audit_channel(labeled, checkpoint, cfg)
        output.append((case, audit))
        print(
            f"f079 donor {case['candidate_id']} preserve={audit['role_preserving_swaps']} "
            f"break={audit['role_breaking_swaps']} paired={audit['paired_swap_available']} "
            f"protected={audit['preserve_moves_protected_cell']}/"
            f"{audit['break_moves_protected_cell']}",
            flush=True,
        )
    return output


def main() -> None:
    args = parse_args()
    if artifact_hash(args.cases) != FROZEN_CASES_SHA256:
        raise RuntimeError("Finding 079 frozen precursor cases changed")
    if not 1 <= int(args.workers) <= 4:
        raise ValueError("--workers must be 1..4")
    base_fields, cases = read_csv_with_fields(args.cases)
    eligible = [row for row in cases if int(row["eligible_channel"]) == 1]
    grouped: dict[int, list[dict[str, str]]] = {}
    for row in eligible:
        grouped.setdefault(int(row["init_seed"]), []).append(row)
    jobs = [
        (str(args.canonical_config), seed, sorted(rows, key=selection_key))
        for seed, rows in sorted(grouped.items())
    ]
    merged: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=int(args.workers)) as executor:
        for result in executor.map(run_seed_job, jobs):
            for case, audit in result:
                row: dict[str, Any] = {
                    **case,
                    "paired_channel_selected": 0,
                    "paired_channel_index": "",
                    "paired_channel_id": "",
                }
                row.update({f"rewire_{field}": audit[field] for field in AUDIT_EXTRA})
                merged.append(row)
    eligible_pairs: dict[int, list[dict[str, Any]]] = {}
    for row in merged:
        if (
            int(row["rewire_paired_swap_available"]) == 1
            and int(row["rewire_preserve_moves_protected_cell"]) == 0
            and int(row["rewire_break_moves_protected_cell"]) == 0
        ):
            eligible_pairs.setdefault(int(row["init_seed"]), []).append(row)
    selected = [
        min(rows, key=selection_key) for _, rows in sorted(eligible_pairs.items())
    ]
    for index, row in enumerate(selected, start=1):
        row["paired_channel_selected"] = 1
        row["paired_channel_index"] = index
        row["paired_channel_id"] = f"f079-channel-{index:03d}"
    merged.sort(key=selection_key)
    fields = [*base_fields, *OUTPUT_EXTRA]
    cases_path = args.output_prefix.with_name(args.output_prefix.name + "_cases.csv")
    manifest_path = args.output_prefix.with_name(args.output_prefix.name + "_manifest.csv")
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.json")
    write_csv(cases_path, fields, merged)
    write_csv(manifest_path, fields, selected)
    summary = {
        "finding": "079C",
        "protocol": "outcome-sealed common-donor factorial support freeze",
        "counterfactual_branch_outcomes_run": False,
        "precursor_cases": str(args.cases),
        "precursor_cases_sha256": artifact_hash(args.cases),
        "eligible_precursor_events": len(eligible),
        "eligible_precursor_seeds": len(grouped),
        "events_with_common_donor_pair": sum(
            int(row["rewire_paired_swap_available"]) for row in merged
        ),
        "selected_independent_channels": len(selected),
        "selected_initialization_seeds": [int(row["init_seed"]) for row in selected],
        "minimum_independent_channels": MINIMUM_INDEPENDENT_CHANNELS,
        "common_donor_support_gate_met": len(selected) >= MINIMUM_INDEPENDENT_CHANNELS,
        "all_target_poststates_exact": all(
            int(row["rewire_target_poststate_exact"]) for row in merged
        ),
        "all_payload_zero": all(int(row["rewire_payload_zero"]) for row in merged),
        "all_ledgers_exact": all(int(row["rewire_ledger_exact"]) for row in merged),
        "cases_csv": str(cases_path),
        "cases_sha256": artifact_hash(cases_path),
        "manifest_csv": str(manifest_path),
        "manifest_sha256": artifact_hash(manifest_path),
        "worker_processes": int(args.workers),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
