from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import independent_persistence_screen as reusable
from component_bridge_causal_trace import write_csv
from expression_handoff_branch_ensemble import build_branch_state
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from iota_rig import load_config
from local_affordance_features import event_for, read_csv, selected_sources
from local_affordance_screen import configure_reusable
from phase_free_class_matrix import run_to_checkpoint
from realization_necessity import file_sha256
from sequential_realization_cut import (
    CASE_FIELDS,
    NEXT_SELECTOR_FIELDS,
    branch_key,
    parse_selector,
    run_chain,
)
from temporal_gate_replication import verify_sham


DEFAULT_OUTPUT_DIR = Path("output/findings/finding071")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the committed Finding 071 depth-1 affordance veto."
    )
    parser.add_argument("--split", choices=("discovery", "confirmation"), required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--freeze-summary", type=Path, required=True)
    parser.add_argument("--selector", type=Path, required=True)
    parser.add_argument("--expected-selector-sha256", required=True)
    parser.add_argument(
        "--screen-summary",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "local_affordance_screen_summary.json",
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "local_affordance_screen_source_manifest.csv",
    )
    parser.add_argument(
        "--transport-csv",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "local_affordance_screen_transport_events.csv",
    )
    parser.add_argument(
        "--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG
    )
    parser.add_argument("--expected-source-manifest-sha256", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_reusable()
    actual_source_hash = file_sha256(args.source_manifest)
    selector_hash = file_sha256(args.selector)
    freeze = json.loads(args.freeze_summary.read_text(encoding="utf-8"))
    checks = {
        "source_hash": actual_source_hash == args.expected_source_manifest_sha256,
        "selector_argument": selector_hash == args.expected_selector_sha256,
        "selector_freeze": selector_hash == freeze.get("selectors_sha256"),
        "split": freeze.get("split") == args.split,
        "factual_only": freeze.get("counterfactual_outcomes_run") is False,
        "measurement_support": freeze.get("measurement_support_gate_met") is True,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Finding 071 veto freeze failed: {checks}")

    selector_rows = read_csv(args.selector)
    keys = [branch_key(row) for row in selector_rows]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Finding 071 selector manifest contains duplicates")
    expected_cohort = f"local_affordance_{args.split}"
    if any(
        row["selection_rule_version"] != "f071-first-unique-inherited-child-v1"
        or row["cohort"] != expected_cohort
        or int(row["natural_child_multiplicity"]) != 1
        or int(row["inheritance_join_verified"]) != 1
        or int(row["payload_zero"]) != 1
        or int(row["ledger_exact"]) != 1
        or int(row["lineage_collision"]) != 0
        for row in selector_rows
    ):
        raise RuntimeError("Finding 071 selector provenance failed")

    sources = selected_sources(args)
    source_ids = {row["source_id"] for row in selector_rows}
    sources = [row for row in sources if row["source_id"] in source_ids]
    transports = read_csv(args.transport_csv)
    canonical = load_config(args.canonical_config)
    specs: dict[tuple[str, str], dict[str, Any]] = {}
    for source in sources:
        seed = int(source["init_seed"])
        event = event_for(source, transports)
        cfg = reusable.config_for_seed(canonical, seed)
        checkpoint = run_to_checkpoint(
            cfg, event["variant"], int(event["checkpoint_tick"])
        )
        specs[(expected_cohort, source["source_id"])] = {
            "event": event,
            "branch_offset": int(event["rebridge_offset"]),
            "cfg": cfg,
            "checkpoint": checkpoint,
        }

    parent_chain_sha256 = hashlib.sha256(selector_hash.encode("ascii")).hexdigest()
    base_cache: dict[tuple[str, str], tuple[Any, ...]] = {}
    cases: list[dict[str, Any]] = []
    next_selectors: list[dict[str, Any]] = []
    for source_row in sorted(selector_rows, key=branch_key):
        source_key = (source_row["cohort"], source_row["source_id"])
        spec = specs.get(source_key)
        if spec is None:
            raise RuntimeError(f"Finding 071 source specification missing: {source_key}")
        if source_key not in base_cache:
            base_cache[source_key] = build_branch_state(
                spec["event"],
                spec["branch_offset"],
                spec["checkpoint"],
                spec["cfg"],
            )
        parsed = parse_selector(source_row)
        if verify_sham(
            base_cache[source_key][0],
            spec["event"],
            spec["cfg"],
            int(source_row["branch_seed"]),
            parsed,
        ) != 1:
            raise RuntimeError("Finding 071 matched sham failed")
        case, next_selector = run_chain(
            1,
            source_row,
            [parsed],
            parent_chain_sha256,
            spec,
            base_cache[source_key],
        )
        cases.append(case)
        if next_selector is not None:
            next_selectors.append(next_selector)

    prefix = args.output_prefix
    cases_path = prefix.with_name(prefix.name + "_cases.csv")
    next_path = prefix.with_name(prefix.name + "_next_selectors.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(cases_path, CASE_FIELDS, cases)
    write_csv(next_path, NEXT_SELECTOR_FIELDS, next_selectors)
    endpoints = Counter(row["stage_endpoint"] for row in cases)
    summary = {
        "finding": "071D",
        "split": args.split,
        "protocol": "depth-1 retained-amplitude local affordance veto",
        "source_manifest_sha256": actual_source_hash,
        "freeze_summary_sha256": file_sha256(args.freeze_summary),
        "selector_sha256": selector_hash,
        "parent_chain_sha256": parent_chain_sha256,
        "input_branches": len(cases),
        "stage_endpoints": dict(sorted(endpoints.items())),
        "next_selectors": len(next_selectors),
        "all_matched_shams_exact": True,
        "all_selectors_matched": all(int(row["selectors_matched"]) == 1 for row in cases),
        "all_selector_identities_exact": all(
            int(row["all_selector_identities_exact"]) for row in cases
        ),
        "all_payload_zero": all(
            int(row["payload_zero_all_offsets"]) for row in cases
        ),
        "all_ledger_exact": all(
            int(row["ledger_exact_all_offsets"]) for row in cases
        ),
        "collision_cases": sum(int(row["lineage_collision"]) for row in cases),
        "transient_child_lineage_losses": sum(
            int(row["next_child_observed"]) == 1
            and row["stage_endpoint"] == "lineage_loss"
            for row in cases
        ),
        "child_bearing_source_censoring": sum(
            int(row["next_child_observed"]) == 1
            and row["stage_endpoint"] == "source_survival_censored"
            for row in cases
        ),
        "cases_csv": str(cases_path),
        "next_selectors_csv": str(next_path),
    }
    summary["next_selectors_sha256"] = file_sha256(next_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
