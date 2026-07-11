from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from component_bridge_causal_trace import write_csv
from experiment_db import artifact_hash
from expression_handoff_branch_ensemble import build_branch_state
from independent_geometry_screen import (
    DEFAULT_CANONICAL_CONFIG,
    config_for_seed,
)
from iota_rig import World, load_config
from phase_free_class_matrix import run_to_checkpoint
from temporal_gate_replication import (
    AGGREGATE_FIELDS,
    FAILURE_LABELS,
    REPLAY_FIELDS,
    aggregate,
    causal_label,
    freeze_selector,
    run_intervention,
    verify_sham,
)
from terminal_candidate_ledger import CASE_FIELDS, CANDIDATE_FIELDS, run_case


SAMPLES = tuple(range(32))
HORIZON = 256
BRANCH_SEED_BASE = 2_026_071_300
SOURCE_CASE_FIELDS = ["source_id", *CASE_FIELDS]
SOURCE_CANDIDATE_FIELDS = ["source_id", *CANDIDATE_FIELDS]
SOURCE_REPLAY_FIELDS = ["source_id", *REPLAY_FIELDS]
SOURCE_AGGREGATE_FIELDS = ["source_id", "init_seed", "event_start_offset", *AGGREGATE_FIELDS]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply the frozen temporal protocol to independent source geometries.")
    parser.add_argument("--output-prefix", type=Path, default=Path("output/findings/finding067/independent_temporal_replication"))
    parser.add_argument("--screen-summary", type=Path, default=Path("output/findings/finding067/independent_geometry_screen_summary.json"))
    parser.add_argument("--source-manifest", type=Path, default=Path("output/findings/finding067/independent_geometry_screen_source_manifest.csv"))
    parser.add_argument("--transport-csv", type=Path, default=Path("output/findings/finding067/independent_geometry_screen_transport_events.csv"))
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def selected_sources(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    summary = json.loads(args.screen_summary.read_text(encoding="utf-8"))
    if not summary.get("screen_complete") or summary.get("intervention_outcomes_inspected_for_selection"):
        raise RuntimeError("independent screen is incomplete or selection-contaminated")
    sources = [row for row in read_csv(args.source_manifest) if int(row["frozen_source_selected"]) == 1]
    if len({int(row["init_seed"]) for row in sources}) != len(sources):
        raise RuntimeError("primary manifest selected more than one source per initialization seed")
    transports = read_csv(args.transport_csv)
    return sources, transports, summary


def event_for(source: dict[str, str], transports: list[dict[str, str]]) -> dict[str, str]:
    matches = [
        row for row in transports
        if int(row["init_seed"]) == int(source["init_seed"])
        and int(row["sample_index"]) == int(source["sample_index"])
        and int(row["start_offset"]) == int(source["start_offset"])
        and int(row["rebridge_offset"]) == int(source["rebridge_offset"])
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one frozen transport event for {source['source_id']}, found {len(matches)}")
    return matches[0]


def source_aggregates(sources: list[dict[str, str]], replays: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for source in sources:
        selected = [row for row in replays if row["source_id"] == source["source_id"]]
        for row in aggregate(selected):
            output.append({
                "source_id": source["source_id"],
                "init_seed": int(source["init_seed"]),
                "event_start_offset": int(source["start_offset"]),
                **row,
            })
    return output


def main() -> None:
    args = parse_args()
    sources, transports, screen_summary = selected_sources(args)
    canonical = load_config(args.canonical_config)
    natural_cases: list[dict[str, Any]] = []
    natural_candidates: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    for source in sources:
        source_id = source["source_id"]
        source_index = int(source["source_index"])
        seed = int(source["init_seed"])
        event = event_for(source, transports)
        cfg = config_for_seed(canonical, seed)
        checkpoint: World = run_to_checkpoint(cfg, event["variant"], int(event["checkpoint_tick"]))
        branch_offset = int(event["rebridge_offset"])
        base = build_branch_state(event, branch_offset, checkpoint, cfg)
        for sample in SAMPLES:
            branch_seed = BRANCH_SEED_BASE + source_index * 10_000 + sample
            case, candidates = run_case(
                event, branch_offset, *base, sample, branch_seed, HORIZON, cfg,
                allow_censored=True,
            )
            case["source_id"] = source_id
            natural_cases.append(case)
            for row in candidates:
                row["source_id"] = source_id
            natural_candidates.extend(candidates)
            finding066_label = str(case["outcome_class"])
            if finding066_label not in FAILURE_LABELS:
                continue
            label = causal_label(candidates)
            if label is None:
                raise RuntimeError(f"no frozen causal label for {source_id} branch {branch_seed}")
            selector = freeze_selector(label, case, candidates)
            verify_sham(base[0], event, cfg, branch_seed, selector)
            replay = run_intervention(event, branch_offset, *base, branch_seed, selector, HORIZON, cfg)
            terminal = replay["terminal_offset"]
            delay = "" if terminal == "" else int(terminal) - int(case["terminal_offset"])
            replay_rows.append({
                "source_id": source_id, "init_seed": seed,
                "event_start_offset": int(event["start_offset"]), "branch_sample": sample,
                "branch_seed": branch_seed, "finding066_outcome_label": finding066_label,
                "natural_label": label, "natural_terminal_offset": int(case["terminal_offset"]),
                "selector_event_index": selector["event_index"],
                "selector_source": ":".join(map(str, selector["source"])),
                "selector_target": ":".join(map(str, selector["target"])),
                "selector_candidate_order": selector["candidate_order"],
                "natural_gate_draw": selector["gate_draw"],
                "natural_transfer_probability": selector["transfer_probability"],
                "natural_gate_passed": int(selector["natural_gate_passed"]),
                "forced_gate_passed": int(selector["forced_gate_passed"]),
                "sham_exact": 1, "override_matches": replay["override_matches"],
                "capacity_retained_after_intervention": int(replay["capacity_retained"]),
                "later_singleton_candidate_evaluated": int(replay["later_candidate_evaluated"]),
                "preempted_target_available_at_singleton_evaluation": int(replay["preempted_target_available"]),
                "immediate_child_count": replay["immediate_child_count"],
                "route_reopened": int(replay["route_reopened"]),
                "postintervention_address_loss_observed": int(replay["observed"]),
                "postintervention_terminal_offset": terminal, "address_loss_delay": delay,
                "eventual_handoff": int(replay["handoff"]),
                "eventual_death_tick_child_count": replay["death_tick_child_count"],
                "lineage_collision": int(replay["collision"]),
                "payload_zero_all_offsets": int(replay["payload_zero"]),
                "ledger_exact_all_offsets": int(replay["ledger_exact"]),
            })
        print(f"independent source={source_id} seed={seed} branches={len(SAMPLES)}", flush=True)

    prefix = args.output_prefix
    cases_path = prefix.with_name(prefix.name + "_natural_cases.csv")
    candidates_path = prefix.with_name(prefix.name + "_natural_candidates.csv")
    replays_path = prefix.with_name(prefix.name + "_replays.csv")
    aggregate_path = prefix.with_name(prefix.name + "_source_aggregate.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    aggregates = source_aggregates(sources, replay_rows)
    write_csv(cases_path, SOURCE_CASE_FIELDS, natural_cases)
    write_csv(candidates_path, SOURCE_CANDIDATE_FIELDS, natural_candidates)
    write_csv(replays_path, SOURCE_REPLAY_FIELDS, replay_rows)
    write_csv(aggregate_path, SOURCE_AGGREGATE_FIELDS, aggregates)
    summary = {
        "protocol": "frozen Finding 067A intervention semantics applied at rebridge",
        "source_manifest_path": str(args.source_manifest),
        "source_manifest_sha256": artifact_hash(args.source_manifest),
        "screen_summary_sha256": artifact_hash(args.screen_summary),
        "screen_complete": bool(screen_summary["screen_complete"]),
        "selected_sources": len(sources),
        "independent_initialization_seeds": len({int(row["init_seed"]) for row in sources}),
        "branches_per_source": len(SAMPLES), "horizon_from_rebridge": HORIZON,
        "natural_branches": len(natural_cases),
        "natural_outcome_labels": dict(sorted(Counter(row["outcome_class"] for row in natural_cases).items())),
        "eligible_replays": len(replay_rows),
        "all_shams_exact": all(int(row["sham_exact"]) for row in replay_rows),
        "all_exactly_one_override": all(int(row["override_matches"]) == 1 for row in replay_rows),
        "all_payload_zero": all(int(row["payload_zero_all_offsets"]) for row in replay_rows),
        "all_ledger_exact": all(int(row["ledger_exact_all_offsets"]) for row in replay_rows),
        "collision_replays": sum(int(row["lineage_collision"]) for row in replay_rows),
        "source_aggregate": aggregates,
        "natural_cases_csv": str(cases_path), "natural_candidates_csv": str(candidates_path),
        "replays_csv": str(replays_path), "source_aggregate_csv": str(aggregate_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
