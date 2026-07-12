from __future__ import annotations

import argparse
import copy
import csv
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import (
    active_neighbor_coords,
    component_labels,
    geometry_from_mask,
    write_csv,
)
from continuation import clone_world
from experiment_db import artifact_hash
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from iota_rig import World, load_config
from phase_free_class_matrix import run_to_checkpoint
from phase_free_constraint_transport import ledger_error
from phase_source_minimization_audit import clamp_stored_phase, phase_source_patch
from predecessor_region_lineage import parse_coords


LOOKBACK = 64
FOLLOWUP = 256
MINIMUM_SEEDS = 6
DEFAULT_TRANSPORT = Path(
    "output/findings/finding072/local_affordance_combined_transport_events.csv"
)
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding074/pre_articulation_channel"
)

CASE_FIELDS = [
    "candidate_id",
    "selected_channel",
    "channel_index",
    "channel_id",
    "init_seed",
    "variant",
    "sample_index",
    "continuation_seed",
    "checkpoint_tick",
    "split_offset",
    "rebridge_offset",
    "original_bridge",
    "successor_bridge_cells",
    "strict_constraint_transport",
    "single_original_bridge",
    "original_active_pre_split",
    "original_inactive_post_split",
    "single_removal_component_delta",
    "actual_split_component_delta",
    "actual_split_largest_delta",
    "precursor_found",
    "precursor_offset",
    "precursor_age_at_split",
    "precursor_event_index",
    "precursor_gate_ordinal",
    "precursor_source",
    "precursor_target",
    "precursor_candidate_order",
    "precursor_candidate_step",
    "precursor_available_A_before",
    "precursor_transfer_probability",
    "precursor_gate_draw",
    "precursor_target_depleted",
    "death_tick_outgoing_transfers",
    "rebridge_activation_count",
    "rebridge_event_index",
    "rebridge_gate_ordinal",
    "rebridge_source",
    "rebridge_target",
    "rebridge_candidate_order",
    "rebridge_candidate_step",
    "rebridge_available_A_before",
    "rebridge_transfer_probability",
    "rebridge_gate_draw",
    "natural_split_lifetime",
    "transplant_target",
    "transplant_rank_key",
    "factual_target_pre_state",
    "factual_target_post_state",
    "transplant_pre_state",
    "eligible_channel",
    "eligibility_failures",
    "payload_zero",
    "ledger_exact",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze factual pre-articulation channels before intervention."
    )
    parser.add_argument("--transport-csv", type=Path, default=DEFAULT_TRANSPORT)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument(
        "--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG
    )
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def coord_text(coord: tuple[int, int, int] | None) -> str:
    return "" if coord is None else ":".join(str(value) for value in coord)


def state_record(world: World, coord: tuple[int, int, int]) -> dict[str, Any]:
    return {
        "active": int(bool(world.active[coord])),
        "A": int(world.A[coord]),
        "R": int(world.R[coord]),
        "V": int(world.V[coord]),
        "P": int(world.P[coord]),
        "latent_A": int(world.latent_A[coord]),
        "angular_L": float(world.angular_L[coord]),
    }


def state_text(world: World, coord: tuple[int, int, int]) -> str:
    return json.dumps(state_record(world, coord), sort_keys=True, separators=(",", ":"))


def config_for_seed(canonical: dict[str, Any], seed: int) -> dict[str, Any]:
    cfg = copy.deepcopy(canonical)
    cfg.setdefault("init", {})["seed"] = int(seed)
    cfg.setdefault("experiment", {})["objective"] = (
        f"finding074_pre_articulation_seed{int(seed)}"
    )
    return cfg


def candidate_id(event: dict[str, str]) -> str:
    return (
        f"f074-seed{int(event['init_seed']):03d}-"
        f"sample{int(event['sample_index']):02d}-"
        f"split{int(event['start_offset']):03d}-"
        f"rebridge{int(event['rebridge_offset']):03d}"
    )


def ordinal_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    gate_ordinal = 0
    for event_index, row in enumerate(rows):
        normalized = dict(row)
        normalized["event_index"] = event_index
        if "gate_draw" in row:
            normalized["gate_ordinal"] = gate_ordinal
            gate_ordinal += 1
        else:
            normalized["gate_ordinal"] = ""
        output.append(normalized)
    return output


def target_coord(
    anchor: tuple[int, int, int],
    delta: tuple[int, int, int],
    size: int,
    wrap: bool,
) -> tuple[int, int, int] | None:
    coord = tuple(anchor[index] + delta[index] for index in range(3))
    if wrap:
        return tuple(value % size for value in coord)
    return coord if all(0 <= value < size for value in coord) else None


def transplant_choice(
    world: World,
    precursor_source: tuple[int, int, int],
    factual_target: tuple[int, int, int],
    forbidden: set[tuple[int, int, int]],
) -> tuple[tuple[int, int, int] | None, str]:
    factual_geometry = geometry_from_mask(
        world.active, factual_target, bool(world.wrap)
    )
    ranked: list[tuple[tuple[int, ...], tuple[int, int, int]]] = []
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            for dz in range(-2, 3):
                if dx == dy == dz == 0:
                    continue
                coord = target_coord(
                    factual_target, (dx, dy, dz), world.size, bool(world.wrap)
                )
                if coord is None or coord in forbidden or coord == precursor_source:
                    continue
                if bool(world.active[coord]) or int(world.latent_A[coord]) > 0:
                    continue
                geometry = geometry_from_mask(world.active, coord, bool(world.wrap))
                key = (
                    abs(int(geometry["face6_neighbors"]) - int(factual_geometry["face6_neighbors"])),
                    abs(int(geometry["cube26_neighbors"]) - int(factual_geometry["cube26_neighbors"])),
                    abs(int(geometry["cube26_components"]) - int(factual_geometry["cube26_components"])),
                    max(abs(dx), abs(dy), abs(dz)),
                    coord[0],
                    coord[1],
                    coord[2],
                )
                ranked.append((key, coord))
    if not ranked:
        return None, ""
    key, coord = min(ranked)
    return coord, ":".join(str(value) for value in key)


def successful_activation(
    rows: list[dict[str, Any]], target: tuple[int, int, int]
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("status") == "succeeded"
        and tuple(row["target"]) == target
        and bool(row.get("target_activated"))
    ]


def selector_fields(prefix: str, row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {
            f"{prefix}_event_index": "",
            f"{prefix}_gate_ordinal": "",
            f"{prefix}_source": "",
            f"{prefix}_target": "",
            f"{prefix}_candidate_order": "",
            f"{prefix}_candidate_step": "",
            f"{prefix}_available_A_before": "",
            f"{prefix}_transfer_probability": "",
            f"{prefix}_gate_draw": "",
        }
    return {
        f"{prefix}_event_index": int(row["event_index"]),
        f"{prefix}_gate_ordinal": int(row["gate_ordinal"]),
        f"{prefix}_source": coord_text(tuple(row["source"])),
        f"{prefix}_target": coord_text(tuple(row["target"])),
        f"{prefix}_candidate_order": int(row["candidate_order"]),
        f"{prefix}_candidate_step": coord_text(tuple(row["candidate_step"])),
        f"{prefix}_available_A_before": int(row["available_A_before"]),
        f"{prefix}_transfer_probability": float(row["transfer_probability"]),
        f"{prefix}_gate_draw": float(row["gate_draw"]),
    }


def audit_event(
    event: dict[str, str], checkpoint: World, cfg: dict[str, Any]
) -> dict[str, Any]:
    split_offset = int(event["start_offset"])
    rebridge_offset = int(event["rebridge_offset"])
    original_cells = sorted(parse_coords(event["original_bridge_cells"]))
    successor_cells = set(parse_coords(event["successor_bridge_cells"]))
    original = original_cells[0] if len(original_cells) == 1 else None
    world = clone_world(checkpoint, int(event["continuation_seed"]))
    activations: list[tuple[int, dict[str, Any], str, str, str]] = []
    split_pre: World | None = None
    split_post: World | None = None
    split_candidates: list[dict[str, Any]] = []
    rebridge_activations: list[dict[str, Any]] = []
    payload_zero = True
    exact = True
    baseline_count: int | None = None
    split_lifetime = 0
    split_still_open = False
    final_offset = split_offset + FOLLOWUP

    try:
        with phase_source_patch(event["variant"]):
            clamp_stored_phase(world, event["variant"])
            for next_offset in range(1, final_offset + 1):
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                pre = clone_world(world, int(event["continuation_seed"]))
                candidates: list[dict[str, Any]] = []
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = candidates.append
                iota_rig.step(world, cfg)
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
                clamp_stored_phase(world, event["variant"])
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                normalized = ordinal_candidates(candidates)
                if original is not None:
                    for row in successful_activation(normalized, original):
                        if bool(row.get("target_depleted_at_evaluation")):
                            forbidden = {original, *successor_cells, tuple(row["source"])}
                            transplant, rank_key = transplant_choice(
                                pre, tuple(row["source"]), original, forbidden
                            )
                            activations.append(
                                (
                                    next_offset,
                                    row,
                                    state_text(pre, original),
                                    state_text(world, original),
                                    json.dumps(
                                        {
                                            "coord": coord_text(transplant),
                                            "rank_key": rank_key,
                                            "pre_state": (
                                                "" if transplant is None else state_text(pre, transplant)
                                            ),
                                        },
                                        sort_keys=True,
                                        separators=(",", ":"),
                                    ),
                                )
                            )
                if next_offset == split_offset:
                    split_pre = pre
                    split_post = clone_world(world, int(event["continuation_seed"]))
                    split_candidates = normalized
                    _, _, baseline_count, _ = component_labels(
                        pre.active, bool(pre.wrap), "cube26"
                    )
                    _, _, post_count, _ = component_labels(
                        world.active, bool(world.wrap), "cube26"
                    )
                    split_still_open = post_count > baseline_count
                    split_lifetime = int(split_still_open)
                elif next_offset > split_offset and split_still_open:
                    _, _, count, _ = component_labels(
                        world.active, bool(world.wrap), "cube26"
                    )
                    if baseline_count is not None and count > baseline_count:
                        split_lifetime += 1
                    else:
                        split_still_open = False
                if next_offset == rebridge_offset:
                    for cell in successor_cells:
                        rebridge_activations.extend(
                            successful_activation(normalized, cell)
                        )
    finally:
        iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None

    precursor_data = [
        item
        for item in activations
        if split_offset - LOOKBACK <= item[0] < split_offset
    ]
    precursor = max(precursor_data, key=lambda item: item[0]) if precursor_data else None
    precursor_row = None if precursor is None else precursor[1]
    rebridge_row = rebridge_activations[0] if len(rebridge_activations) == 1 else None
    failures: list[str] = []
    if len(original_cells) != 1:
        failures.append("original_bridge_not_singleton")
    original_active_pre = bool(original is not None and split_pre is not None and split_pre.active[original])
    original_inactive_post = bool(original is not None and split_post is not None and not split_post.active[original])
    removal_delta = 0
    actual_delta = 0
    largest_delta = 0
    if original is not None and split_pre is not None and split_post is not None:
        _, _, pre_count, pre_largest = component_labels(
            split_pre.active, bool(split_pre.wrap), "cube26"
        )
        removed = split_pre.active.copy()
        removed[original] = False
        _, _, removed_count, _ = component_labels(
            removed, bool(split_pre.wrap), "cube26"
        )
        _, _, post_count, post_largest = component_labels(
            split_post.active, bool(split_post.wrap), "cube26"
        )
        removal_delta = removed_count - pre_count
        actual_delta = post_count - pre_count
        largest_delta = post_largest - pre_largest
    outgoing = 0
    if original is not None:
        outgoing = sum(
            row.get("status") == "succeeded" and tuple(row["source"]) == original
            for row in split_candidates
        )
    checks = {
        "original_active_pre": original_active_pre,
        "original_inactive_post": original_inactive_post,
        "single_removal_articulation": removal_delta > 0,
        "actual_split": actual_delta > 0,
        "precursor": precursor is not None,
        "outgoing": outgoing > 0,
        "natural_rebridge_activation": len(rebridge_activations) >= 1,
        "payload": payload_zero,
        "ledger": exact,
    }
    failures.extend(name for name, passed in checks.items() if not passed)
    transplant_payload = {} if precursor is None else json.loads(precursor[4])
    row: dict[str, Any] = {
        "candidate_id": candidate_id(event),
        "selected_channel": 0,
        "channel_index": "",
        "channel_id": "",
        "init_seed": int(event["init_seed"]),
        "variant": event["variant"],
        "sample_index": int(event["sample_index"]),
        "continuation_seed": int(event["continuation_seed"]),
        "checkpoint_tick": int(event["checkpoint_tick"]),
        "split_offset": split_offset,
        "rebridge_offset": rebridge_offset,
        "original_bridge": coord_text(original),
        "successor_bridge_cells": event["successor_bridge_cells"],
        "strict_constraint_transport": int(event["constraint_transport"]),
        "single_original_bridge": int(len(original_cells) == 1),
        "original_active_pre_split": int(original_active_pre),
        "original_inactive_post_split": int(original_inactive_post),
        "single_removal_component_delta": removal_delta,
        "actual_split_component_delta": actual_delta,
        "actual_split_largest_delta": largest_delta,
        "precursor_found": int(precursor is not None),
        "precursor_offset": "" if precursor is None else precursor[0],
        "precursor_age_at_split": "" if precursor is None else split_offset - precursor[0],
        **selector_fields("precursor", precursor_row),
        "precursor_target_depleted": (
            "" if precursor_row is None else int(bool(precursor_row["target_depleted_at_evaluation"]))
        ),
        "death_tick_outgoing_transfers": outgoing,
        "rebridge_activation_count": len(rebridge_activations),
        **selector_fields("rebridge", rebridge_row),
        "natural_split_lifetime": split_lifetime,
        "transplant_target": transplant_payload.get("coord", ""),
        "transplant_rank_key": transplant_payload.get("rank_key", ""),
        "factual_target_pre_state": "" if precursor is None else precursor[2],
        "factual_target_post_state": "" if precursor is None else precursor[3],
        "transplant_pre_state": transplant_payload.get("pre_state", ""),
        "eligible_channel": int(not failures and bool(transplant_payload.get("coord"))),
        "eligibility_failures": ";".join(
            [*failures, *([] if transplant_payload.get("coord") else ["no_transplant_target"])]
        ),
        "payload_zero": int(payload_zero),
        "ledger_exact": int(exact),
    }
    if not transplant_payload.get("coord"):
        row["eligible_channel"] = 0
    return row


def run_seed_job(job: tuple[str, int, list[dict[str, str]]]) -> list[dict[str, Any]]:
    canonical_path, seed, events = job
    canonical = load_config(canonical_path)
    cfg = config_for_seed(canonical, seed)
    checkpoint = run_to_checkpoint(
        cfg, events[0]["variant"], int(events[0]["checkpoint_tick"])
    )
    rows: list[dict[str, Any]] = []
    for event in events:
        row = audit_event(event, checkpoint, cfg)
        rows.append(row)
        print(
            f"f074 factual seed={seed} sample={event['sample_index']} "
            f"split={event['start_offset']} eligible={row['eligible_channel']} "
            f"failures={row['eligibility_failures']}",
            flush=True,
        )
    return rows


def main() -> None:
    args = parse_args()
    if not 1 <= int(args.workers) <= 4:
        raise ValueError("--workers must be 1..4")
    transports = read_csv(args.transport_csv)
    strict = [row for row in transports if int(row["constraint_transport"]) == 1]
    grouped: dict[int, list[dict[str, str]]] = {}
    for event in strict:
        grouped.setdefault(int(event["init_seed"]), []).append(event)
    jobs = [
        (
            str(args.canonical_config),
            seed,
            sorted(
                events,
                key=lambda row: (
                    int(row["sample_index"]),
                    int(row["start_offset"]),
                    int(row["rebridge_offset"]),
                ),
            ),
        )
        for seed, events in sorted(grouped.items())
    ]
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=int(args.workers)) as executor:
        for result in executor.map(run_seed_job, jobs):
            rows.extend(result)
    eligible_by_seed: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        if int(row["eligible_channel"]) == 1:
            eligible_by_seed.setdefault(int(row["init_seed"]), []).append(row)
    selected = [
        min(
            candidates,
            key=lambda row: (
                int(row["sample_index"]),
                int(row["split_offset"]),
                int(row["rebridge_offset"]),
                int(row["precursor_offset"]),
                row["precursor_source"],
                row["precursor_target"],
            ),
        )
        for _, candidates in sorted(eligible_by_seed.items())
    ]
    for index, row in enumerate(selected, start=1):
        row["selected_channel"] = 1
        row["channel_index"] = index
        row["channel_id"] = f"f074-channel-{index:03d}"
    rows.sort(
        key=lambda row: (
            int(row["init_seed"]),
            int(row["sample_index"]),
            int(row["split_offset"]),
        )
    )
    cases_path = args.output_prefix.with_name(args.output_prefix.name + "_cases.csv")
    manifest_path = args.output_prefix.with_name(
        args.output_prefix.name + "_manifest.csv"
    )
    summary_path = args.output_prefix.with_name(
        args.output_prefix.name + "_summary.json"
    )
    write_csv(cases_path, CASE_FIELDS, rows)
    write_csv(manifest_path, CASE_FIELDS, selected)
    summary = {
        "finding": "074A",
        "protocol": "factual pre-articulation channel screen",
        "screen_complete": True,
        "counterfactual_outcomes_run": False,
        "transport_csv": str(args.transport_csv),
        "transport_csv_sha256": artifact_hash(args.transport_csv),
        "canonical_config": str(args.canonical_config),
        "canonical_config_sha256": artifact_hash(args.canonical_config),
        "strict_transport_events": len(strict),
        "strict_initialization_seeds": len(grouped),
        "eligible_channels": sum(int(row["eligible_channel"]) for row in rows),
        "selected_channels": len(selected),
        "selected_initialization_seeds": [int(row["init_seed"]) for row in selected],
        "minimum_independent_seeds": MINIMUM_SEEDS,
        "intervention_support_gate_met": len(selected) >= MINIMUM_SEEDS,
        "failure_counts": dict(
            sorted(
                Counter(
                    failure
                    for row in rows
                    for failure in str(row["eligibility_failures"]).split(";")
                    if failure
                ).items()
            )
        ),
        "all_payload_zero": all(int(row["payload_zero"]) for row in rows),
        "all_ledgers_exact": all(int(row["ledger_exact"]) for row in rows),
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
