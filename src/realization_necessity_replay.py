from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from component_bridge_causal_trace import write_csv
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from realization_necessity import (
    AGGREGATE_FIELDS,
    CANDIDATE_OUTPUT_FIELDS,
    FROZEN_MANIFEST_SHA256,
    REPLAY_FIELDS,
    aggregate_rows,
    build_source_specs,
    coord,
    file_sha256,
    run_veto,
    text_coord,
)
from temporal_gate_replication import verify_sham
from terminal_candidate_ledger import CANDIDATE_FIELDS


VETO_CANDIDATE_FIELDS = [
    "cohort", "source_id", "branch_sample", "branch_seed", "event_index",
    *[field for field in CANDIDATE_FIELDS if field != "event_index"],
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay a committed Finding 068 selector manifest.")
    parser.add_argument("--output-prefix", type=Path, default=Path("output/findings/finding068/realization_necessity"))
    parser.add_argument("--selector-manifest", type=Path, default=Path("output/findings/finding068/realization_necessity_selectors.csv"))
    parser.add_argument("--freeze-summary", type=Path, default=Path("output/findings/finding068/realization_necessity_freeze_summary.json"))
    parser.add_argument("--expected-selector-sha256", required=True)
    parser.add_argument("--event-csv", type=Path, default=Path("output/findings/finding060/phase_free_constraint_transport_events.csv"))
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--source-manifest", type=Path, default=Path("output/findings/finding067/independent_geometry_screen_source_manifest.csv"))
    parser.add_argument("--transport-csv", type=Path, default=Path("output/findings/finding067/independent_geometry_screen_transport_events.csv"))
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_selector(row: dict[str, str]) -> dict[str, Any]:
    return {
        "relative": int(row["terminal_relative"]),
        "event_index": int(row["event_index"]),
        "gate_ordinal": int(row["gate_ordinal"]),
        "source": coord(row["source"]),
        "target": coord(row["target"]),
        "candidate_order": int(row["candidate_order"]),
        "candidate_step": coord(row["candidate_step"]),
        "available_A_before": int(row["available_A_before"]),
        "target_active_at_tick_start": bool(int(row["target_active_at_tick_start"])),
        "target_active_at_evaluation": bool(int(row["target_active_at_evaluation"])),
        "target_depleted_at_evaluation": bool(int(row["target_depleted_at_evaluation"])),
        "target_latent_at_evaluation": bool(int(row["target_latent_at_evaluation"])),
        "influence": float(row["influence"]),
        "residual_bias_multiplier": float(row["residual_bias_multiplier"]),
        "transfer_probability": float(row["transfer_probability"]),
        "gate_draw": float(row["gate_draw"]),
        "natural_gate_passed": True,
        "forced_gate_passed": False,
    }


def normalized_candidates(
    raw: list[dict[str, Any]], row: dict[str, str]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, candidate in enumerate(raw):
        normalized = {field: candidate.get(field, "") for field in CANDIDATE_FIELDS}
        normalized.update({
            "cohort": row["cohort"], "source_id": row["source_id"],
            "branch_sample": int(row["branch_sample"]),
            "branch_seed": int(row["branch_seed"]), "event_index": index,
            "source": text_coord(tuple(candidate["source"])),
            "target": text_coord(tuple(candidate["target"])),
            "candidate_step": text_coord(tuple(candidate.get("candidate_step", ()))),
        })
        output.append(normalized)
    return output


def main() -> None:
    args = parse_args()
    actual_hash = file_sha256(args.selector_manifest)
    if actual_hash != args.expected_selector_sha256:
        raise RuntimeError(f"selector manifest hash mismatch: {actual_hash}")
    freeze = json.loads(args.freeze_summary.read_text(encoding="utf-8"))
    if freeze.get("counterfactual_outcomes_run") is not False:
        raise RuntimeError("selector freeze summary is not factual-only")
    if freeze.get("selectors_sha256") != actual_hash:
        raise RuntimeError("freeze summary and selector manifest disagree")
    if freeze.get("frozen_independent_manifest_sha256") != FROZEN_MANIFEST_SHA256:
        raise RuntimeError("independent source freeze changed")

    selector_rows = read_csv(args.selector_manifest)
    source_specs = build_source_specs(args)
    specs = {(spec["cohort"], spec["source_id"]): spec for spec in source_specs}
    replays: list[dict[str, Any]] = []
    veto_candidates: list[dict[str, Any]] = []
    base_cache: dict[tuple[str, str], tuple[Any, ...]] = {}
    for row in selector_rows:
        key = (row["cohort"], row["source_id"])
        spec = specs[key]
        if key not in base_cache:
            from expression_handoff_branch_ensemble import build_branch_state

            base_cache[key] = build_branch_state(
                spec["event"], spec["branch_offset"], spec["checkpoint"], spec["cfg"]
            )
        base = base_cache[key]
        selector = parse_selector(row)
        branch_seed = int(row["branch_seed"])
        sham_matches = verify_sham(
            base[0], spec["event"], spec["cfg"], branch_seed, selector
        )
        replay = run_veto(
            spec["event"], spec["branch_offset"], *base, branch_seed, selector, spec["cfg"]
        )
        veto_candidates.extend(normalized_candidates(replay["candidate_rows"], row))
        terminal = replay["terminal_offset"]
        delay = "" if terminal == "" else int(terminal) - int(row["natural_terminal_offset"])
        immediate_targets = [tuple(item["target"]) for item in replay["immediate_children"]]
        replays.append({
            "cohort": row["cohort"], "source_id": row["source_id"],
            "init_seed": int(row["init_seed"]),
            "event_start_offset": int(row["event_start_offset"]),
            "branch_sample": int(row["branch_sample"]), "branch_seed": branch_seed,
            "natural_terminal_offset": int(row["natural_terminal_offset"]),
            "selector_event_index": int(row["event_index"]),
            "selector_source": row["source"], "selector_target": row["target"],
            "selector_candidate_order": int(row["candidate_order"]),
            "natural_gate_draw": float(row["gate_draw"]),
            "natural_transfer_probability": float(row["transfer_probability"]),
            "sham_exact": int(sham_matches == 1),
            "override_matches": replay["override_matches"],
            "sham_steps_compared": int(row["terminal_relative"]) + 1,
            "world_and_rng_exact": int(sham_matches == 1),
            "selector_identity_exact": int(replay["selector_identity_exact"]),
            "targeted_event_suppressed": int(replay["targeted_event_suppressed"]),
            "source_capacity_retained_after_veto": int(replay["source_capacity_retained"]),
            "immediate_alternate_child_count": len(immediate_targets),
            "immediate_alternate_child_targets": ";".join(text_coord(value) for value in immediate_targets),
            "first_alternate_child_delay": replay["first_alternate_child_delay"],
            "first_alternate_child_target": text_coord(replay["first_alternate_child_target"]),
            "selected_target_later_inherited": int(replay["selected_target_later_inherited"]),
            "postveto_address_loss_observed": int(replay["observed"]),
            "postveto_terminal_offset": terminal, "address_loss_delay": delay,
            "eventual_handoff": int(replay["handoff"]),
            "alternate_child_timing": replay["alternate_child_timing"],
            "address_endpoint": replay["address_endpoint"],
            "lineage_collision": int(replay["collision"]),
            "payload_zero_all_offsets": int(replay["payload_zero"]),
            "ledger_exact_all_offsets": int(replay["ledger_exact"]),
        })
    natural_cases = read_csv(Path(freeze["natural_cases_csv"]))
    aggregate = aggregate_rows(natural_cases, replays)
    prefix = args.output_prefix
    replays_path = prefix.with_name(prefix.name + "_replays.csv")
    candidates_path = prefix.with_name(prefix.name + "_veto_candidates.csv")
    aggregate_path = prefix.with_name(prefix.name + "_aggregate.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(replays_path, REPLAY_FIELDS, replays)
    write_csv(candidates_path, VETO_CANDIDATE_FIELDS, veto_candidates)
    write_csv(aggregate_path, AGGREGATE_FIELDS, aggregate)
    timing = Counter(row["alternate_child_timing"] for row in replays)
    endpoints = Counter(row["address_endpoint"] for row in replays)
    summary = {
        "protocol": "committed-selector first natural ancestry-child gate veto",
        "selector_manifest_path": str(args.selector_manifest),
        "selector_manifest_sha256": actual_hash,
        "freeze_summary_path": str(args.freeze_summary),
        "eligible_vetoes": len(replays),
        "alternate_child_timing": dict(sorted(timing.items())),
        "address_endpoints": dict(sorted(endpoints.items())),
        "eventual_handoffs": sum(int(row["eventual_handoff"]) for row in replays),
        "targeted_events_suppressed": sum(int(row["targeted_event_suppressed"]) for row in replays),
        "all_shams_exact": all(int(row["sham_exact"]) for row in replays),
        "all_world_and_rng_exact_through_selector": all(int(row["world_and_rng_exact"]) for row in replays),
        "all_selector_identities_exact": all(int(row["selector_identity_exact"]) for row in replays),
        "all_exactly_one_override": all(int(row["override_matches"]) == 1 for row in replays),
        "all_payload_zero": all(int(row["payload_zero_all_offsets"]) for row in replays),
        "all_ledger_exact": all(int(row["ledger_exact_all_offsets"]) for row in replays),
        "collision_replays": sum(int(row["lineage_collision"]) for row in replays),
        "aggregate": aggregate,
        "replays_csv": str(replays_path), "veto_candidates_csv": str(candidates_path),
        "aggregate_csv": str(aggregate_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
