from __future__ import annotations

import argparse
import csv
import json
from collections import deque
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import component_labels, csv_bool, write_csv
from continuation import clone_world
from iota_rig import World, candidate_neighbor_steps, load_config
from phase_free_class_matrix import (
    analyze_transition,
    jaccard,
    neighbor_label_set,
    rebridge_path_cells,
    run_to_checkpoint,
    snapshot_stats,
)
from phase_source_minimization_audit import clamp_stored_phase, discover_config, phase_source_patch


EVENT_FIELDNAMES = [
    "init_seed",
    "variant",
    "sample_index",
    "continuation_seed",
    "checkpoint_tick",
    "start_offset",
    "rebridge_offset",
    "duration",
    "original_bridge_cells",
    "successor_bridge_cells",
    "original_bridge_returned_cells",
    "bridge_path_jaccard",
    "structural_displacement",
    "postloss_implicated_region_count",
    "postloss_new_region_count",
    "predecessor_region_count",
    "predecessor_region_sizes",
    "persistent_predecessor_region_sizes",
    "minimum_region_persistence",
    "region_pair_count",
    "preloss_reachable_pair_fraction",
    "original_removed_reachable_pair_fraction",
    "split_reachable_pair_fraction",
    "rebridge_reachable_pair_fraction",
    "successor_removed_reachable_pair_fraction",
    "successor_role_reachability_drop",
    "mean_preloss_shortest_path",
    "mean_rebridge_shortest_path",
    "preloss_flow_accessibility",
    "rebridge_flow_accessibility",
    "flow_accessibility_ratio",
    "same_regions_reconnected",
    "predecessor_bridge_role_critical",
    "successor_bridge_role_critical",
    "constraint_transport",
    "payload_zero_all_observed_offsets",
    "ledger_exact_all_observed_offsets",
]

AGGREGATE_FIELDNAMES = [
    "variant",
    "events",
    "same_regions_reconnected_events",
    "predecessor_bridge_role_critical_events",
    "successor_bridge_role_critical_events",
    "constraint_transport_events",
    "complete_bridge_displacement_events",
    "mean_minimum_region_persistence",
    "mean_rebridge_reachable_pair_fraction",
    "mean_successor_role_reachability_drop",
    "mean_preloss_shortest_path",
    "mean_rebridge_shortest_path",
    "mean_flow_accessibility_ratio",
    "payload_zero_events",
    "ledger_exact_events",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay Class B events and test transport of the bridge's relational role."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument(
        "--signal-csv",
        default="output/findings/finding059/phase_free_class_matrix_signals.csv",
    )
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--coord-limit", type=int, default=64)
    parser.add_argument("--limit-events", type=int)
    return parser.parse_args()


def parse_int(value: Any) -> int:
    return int(str(value).strip())


def read_class_b_events(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["event_class"] == "class_b"]
    return sorted(
        rows,
        key=lambda row: (
            parse_int(row["init_seed"]),
            str(row["variant"]),
            parse_int(row["sample_index"]),
            parse_int(row["start_offset"]),
        ),
    )


def coords_text(coords: set[tuple[int, int, int]], limit: int) -> str:
    ordered = sorted(coords)
    clipped = ordered[: int(limit)]
    suffix = "" if len(ordered) <= int(limit) else f";...+{len(ordered) - int(limit)}"
    return ";".join(f"{x}:{y}:{z}" for x, y, z in clipped) + suffix


def ledger_error(world: World) -> float:
    active_total = int(np.sum(world.A[world.active], dtype=np.int64))
    latent_total = int(np.sum(world.latent_A[~world.active], dtype=np.int64))
    return float(active_total + latent_total - int(world.initial_total_A))


def component_coord_sets(labels: np.ndarray, label_ids: set[int]) -> list[set[tuple[int, int, int]]]:
    regions: list[set[tuple[int, int, int]]] = []
    for label in sorted(label_ids):
        regions.append(
            {
                tuple(int(value) for value in coord)
                for coord in np.argwhere(labels == int(label))
            }
        )
    return regions


def active_coords(mask: np.ndarray, coords: set[tuple[int, int, int]]) -> set[tuple[int, int, int]]:
    return {coord for coord in coords if bool(mask[coord])}


def pair_reachability(
    labels: np.ndarray,
    regions: list[set[tuple[int, int, int]]],
) -> tuple[float, list[bool]]:
    pair_results: list[bool] = []
    region_labels = [
        {int(labels[coord]) for coord in region if int(labels[coord]) >= 0}
        for region in regions
    ]
    for left, right in combinations(region_labels, 2):
        pair_results.append(bool(left & right))
    if not pair_results:
        return 0.0, []
    return float(sum(pair_results) / len(pair_results)), pair_results


def shortest_path(
    active: np.ndarray,
    sources: set[tuple[int, int, int]],
    targets: set[tuple[int, int, int]],
    wrap: bool,
) -> int | None:
    source_set = active_coords(active, sources)
    target_set = active_coords(active, targets)
    if not source_set or not target_set:
        return None
    if source_set & target_set:
        return 0
    steps = tuple(
        (int(dx), int(dy), int(dz))
        for dx, dy, dz in candidate_neighbor_steps("cube26")
    )
    size = int(active.shape[0])
    queue = deque((coord, 0) for coord in source_set)
    visited = set(source_set)
    while queue:
        (x, y, z), distance = queue.popleft()
        for dx, dy, dz in steps:
            neighbor = (x + dx, y + dy, z + dz)
            if wrap:
                neighbor = tuple(value % size for value in neighbor)
            elif not all(0 <= value < size for value in neighbor):
                continue
            if neighbor in visited or not bool(active[neighbor]):
                continue
            if neighbor in target_set:
                return distance + 1
            visited.add(neighbor)
            queue.append((neighbor, distance + 1))
    return None


def pair_distances(
    active: np.ndarray,
    regions: list[set[tuple[int, int, int]]],
    wrap: bool,
) -> list[int | None]:
    return [
        shortest_path(active, regions[left], regions[right], wrap)
        for left, right in combinations(range(len(regions)), 2)
    ]


def mean_distance(distances: list[int | None]) -> float | str:
    finite = [int(distance) for distance in distances if distance is not None]
    return "" if not finite else float(mean(finite))


def flow_accessibility(distances: list[int | None]) -> float:
    if not distances:
        return 0.0
    return float(
        sum(0.0 if distance is None else 1.0 / max(int(distance), 1) for distance in distances)
        / len(distances)
    )


def replay_event(
    args: argparse.Namespace,
    event: dict[str, Any],
    checkpoint: World,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    seed = parse_int(event["init_seed"])
    variant = str(event["variant"])
    sample_index = parse_int(event["sample_index"])
    continuation_seed = parse_int(event["continuation_seed"])
    start_offset = parse_int(event["start_offset"])
    rebridge_offset = parse_int(event["rebridge_offset"])
    snapshots: dict[int, World] = {}
    payload_zero = True
    ledger_exact = True

    with phase_source_patch(variant):
        world = clone_world(checkpoint, continuation_seed)
        clamp_stored_phase(world, variant)
        for offset in range(rebridge_offset + 1):
            payload_zero = payload_zero and int(np.count_nonzero(world.P)) == 0
            ledger_exact = ledger_exact and ledger_error(world) == 0.0
            if offset in {start_offset - 1, start_offset, rebridge_offset - 1, rebridge_offset}:
                snapshots[offset] = clone_world(world, continuation_seed)
            if offset < rebridge_offset:
                iota_rig.step(world, cfg)
                clamp_stored_phase(world, variant)

    before = snapshots[start_offset - 1]
    split = snapshots[start_offset]
    rebridge_before = snapshots[rebridge_offset - 1]
    rebridge = snapshots[rebridge_offset]
    before_stats = snapshot_stats(before)
    split_stats = snapshot_stats(split)
    rebridge_before_stats = snapshot_stats(rebridge_before)
    rebridge_stats = snapshot_stats(rebridge)
    split_transition = analyze_transition(
        before.active,
        split.active,
        before_stats,
        split_stats,
        bool(split.wrap),
    )
    rebridge_transition = analyze_transition(
        rebridge_before.active,
        rebridge.active,
        rebridge_before_stats,
        rebridge_stats,
        bool(rebridge.wrap),
    )
    original_bridge = set(split_transition["lost_bridge_if_restored"])
    successor_bridge = rebridge_path_cells(
        rebridge_before_stats,
        rebridge.active,
        rebridge_transition,
        bool(rebridge.wrap),
    )
    postloss_implicated_labels: set[int] = set()
    for coord in original_bridge:
        postloss_implicated_labels.update(
            neighbor_label_set(split_stats["labels"], coord, bool(split.wrap))
        )
    postloss_regions = component_coord_sets(
        split_stats["labels"],
        postloss_implicated_labels,
    )
    postloss_new_regions = sum(
        not active_coords(before.active, region) for region in postloss_regions
    )

    before_without_original = before.active.copy()
    for coord in original_bridge:
        before_without_original[coord] = False
    original_removed_labels, _, _, _ = component_labels(
        before_without_original,
        bool(before.wrap),
        "cube26",
    )
    predecessor_labels: set[int] = set()
    for coord in original_bridge:
        predecessor_labels.update(
            neighbor_label_set(original_removed_labels, coord, bool(before.wrap))
        )
    regions = component_coord_sets(original_removed_labels, predecessor_labels)
    split_regions = [active_coords(split.active, region) for region in regions]
    persistent_regions = [active_coords(rebridge.active, region) for region in regions]
    persistence = [
        float(len(persistent) / len(region)) if region else 0.0
        for region, persistent in zip(regions, persistent_regions)
    ]

    before_labels, _, _, _ = component_labels(before.active, bool(before.wrap), "cube26")
    rebridge_labels = rebridge_stats["labels"]
    preloss_reachability, _ = pair_reachability(before_labels, regions)
    original_removed_reachability, _ = pair_reachability(original_removed_labels, regions)
    split_reachability, _ = pair_reachability(split_stats["labels"], split_regions)
    rebridge_reachability, _ = pair_reachability(rebridge_labels, persistent_regions)
    without_successor = rebridge.active.copy()
    for coord in successor_bridge:
        without_successor[coord] = False
    without_labels, _, _, _ = component_labels(
        without_successor,
        bool(rebridge.wrap),
        "cube26",
    )
    without_reachability, _ = pair_reachability(without_labels, persistent_regions)
    reachability_drop = max(0.0, rebridge_reachability - without_reachability)

    preloss_distances = pair_distances(before.active, regions, bool(before.wrap))
    rebridge_distances = pair_distances(rebridge.active, persistent_regions, bool(rebridge.wrap))
    preloss_accessibility = flow_accessibility(preloss_distances)
    rebridge_accessibility = flow_accessibility(rebridge_distances)
    accessibility_ratio = (
        float(rebridge_accessibility / preloss_accessibility)
        if preloss_accessibility > 0.0
        else 0.0
    )
    returned = active_coords(rebridge.active, original_bridge)
    bridge_j = jaccard(original_bridge, successor_bridge)
    same_regions = bool(regions) and rebridge_reachability == 1.0
    predecessor_role_critical = (
        len(regions) >= 2
        and preloss_reachability == 1.0
        and original_removed_reachability < 1.0
    )
    role_critical = reachability_drop > 0.0
    constraint_transport = (
        predecessor_role_critical
        and split_reachability < 1.0
        and same_regions
        and bridge_j < 1.0
    )

    return {
        "init_seed": seed,
        "variant": variant,
        "sample_index": sample_index,
        "continuation_seed": continuation_seed,
        "checkpoint_tick": int(args.checkpoint_tick),
        "start_offset": start_offset,
        "rebridge_offset": rebridge_offset,
        "duration": rebridge_offset - start_offset,
        "original_bridge_cells": coords_text(original_bridge, int(args.coord_limit)),
        "successor_bridge_cells": coords_text(successor_bridge, int(args.coord_limit)),
        "original_bridge_returned_cells": coords_text(returned, int(args.coord_limit)),
        "bridge_path_jaccard": bridge_j,
        "structural_displacement": float(1.0 - bridge_j),
        "postloss_implicated_region_count": len(postloss_regions),
        "postloss_new_region_count": postloss_new_regions,
        "predecessor_region_count": len(regions),
        "predecessor_region_sizes": ";".join(str(len(region)) for region in regions),
        "persistent_predecessor_region_sizes": ";".join(
            str(len(region)) for region in persistent_regions
        ),
        "minimum_region_persistence": min(persistence, default=0.0),
        "region_pair_count": len(preloss_distances),
        "preloss_reachable_pair_fraction": preloss_reachability,
        "original_removed_reachable_pair_fraction": original_removed_reachability,
        "split_reachable_pair_fraction": split_reachability,
        "rebridge_reachable_pair_fraction": rebridge_reachability,
        "successor_removed_reachable_pair_fraction": without_reachability,
        "successor_role_reachability_drop": reachability_drop,
        "mean_preloss_shortest_path": mean_distance(preloss_distances),
        "mean_rebridge_shortest_path": mean_distance(rebridge_distances),
        "preloss_flow_accessibility": preloss_accessibility,
        "rebridge_flow_accessibility": rebridge_accessibility,
        "flow_accessibility_ratio": accessibility_ratio,
        "same_regions_reconnected": csv_bool(same_regions),
        "predecessor_bridge_role_critical": csv_bool(predecessor_role_critical),
        "successor_bridge_role_critical": csv_bool(role_critical),
        "constraint_transport": csv_bool(constraint_transport),
        "payload_zero_all_observed_offsets": csv_bool(payload_zero),
        "ledger_exact_all_observed_offsets": csv_bool(ledger_exact),
    }


def mean_value(rows: list[dict[str, Any]], field: str) -> str:
    values = [float(row[field]) for row in rows if row[field] != ""]
    return "" if not values else str(float(mean(values)))


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for variant in sorted({str(row["variant"]) for row in rows}):
        selected = [row for row in rows if str(row["variant"]) == variant]
        output.append(
            {
                "variant": variant,
                "events": len(selected),
                "same_regions_reconnected_events": sum(
                    int(row["same_regions_reconnected"]) for row in selected
                ),
                "predecessor_bridge_role_critical_events": sum(
                    int(row["predecessor_bridge_role_critical"]) for row in selected
                ),
                "successor_bridge_role_critical_events": sum(
                    int(row["successor_bridge_role_critical"]) for row in selected
                ),
                "constraint_transport_events": sum(
                    int(row["constraint_transport"]) for row in selected
                ),
                "complete_bridge_displacement_events": sum(
                    float(row["bridge_path_jaccard"]) == 0.0 for row in selected
                ),
                "mean_minimum_region_persistence": mean_value(
                    selected, "minimum_region_persistence"
                ),
                "mean_rebridge_reachable_pair_fraction": mean_value(
                    selected, "rebridge_reachable_pair_fraction"
                ),
                "mean_successor_role_reachability_drop": mean_value(
                    selected, "successor_role_reachability_drop"
                ),
                "mean_preloss_shortest_path": mean_value(
                    selected, "mean_preloss_shortest_path"
                ),
                "mean_rebridge_shortest_path": mean_value(
                    selected, "mean_rebridge_shortest_path"
                ),
                "mean_flow_accessibility_ratio": mean_value(
                    selected, "flow_accessibility_ratio"
                ),
                "payload_zero_events": sum(
                    int(row["payload_zero_all_observed_offsets"]) for row in selected
                ),
                "ledger_exact_events": sum(
                    int(row["ledger_exact_all_observed_offsets"]) for row in selected
                ),
            }
        )
    return output


def main() -> None:
    args = parse_args()
    output_prefix = Path(args.output_prefix)
    events = read_class_b_events(Path(args.signal_csv))
    if args.limit_events is not None:
        events = events[: int(args.limit_events)]
    checkpoint_keys = sorted({(parse_int(row["init_seed"]), str(row["variant"])) for row in events})
    configs: dict[int, dict[str, Any]] = {}
    checkpoints: dict[tuple[int, str], World] = {}
    for seed, variant in checkpoint_keys:
        if seed not in configs:
            configs[seed] = load_config(discover_config(args.config_dir, seed))
        print(f"checkpoint seed={seed} variant={variant}", flush=True)
        checkpoints[(seed, variant)] = run_to_checkpoint(
            configs[seed],
            variant,
            int(args.checkpoint_tick),
        )

    event_rows: list[dict[str, Any]] = []
    for event in events:
        seed = parse_int(event["init_seed"])
        variant = str(event["variant"])
        row = replay_event(
            args,
            event,
            checkpoints[(seed, variant)],
            configs[seed],
        )
        event_rows.append(row)
        print(
            f"event seed={seed} variant={variant} sample={row['sample_index']} "
            f"offset={row['start_offset']} transport={row['constraint_transport']} "
            f"reach={row['rebridge_reachable_pair_fraction']}",
            flush=True,
        )

    aggregate_rows = aggregate(event_rows)
    event_path = output_prefix.with_name(output_prefix.name + "_events.csv")
    aggregate_path = output_prefix.with_name(output_prefix.name + "_aggregate.csv")
    write_csv(event_path, EVENT_FIELDNAMES, event_rows)
    write_csv(aggregate_path, AGGREGATE_FIELDNAMES, aggregate_rows)
    summary_path = output_prefix.with_name(output_prefix.name + "_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "event_csv": str(event_path),
                "aggregate_csv": str(aggregate_path),
                "events": len(event_rows),
                "aggregate": aggregate_rows,
                "all_constraint_transport": all(
                    int(row["constraint_transport"]) for row in event_rows
                ),
                "all_payload_zero": all(
                    int(row["payload_zero_all_observed_offsets"]) for row in event_rows
                ),
                "all_ledger_exact": all(
                    int(row["ledger_exact_all_observed_offsets"]) for row in event_rows
                ),
            },
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")


if __name__ == "__main__":
    main()
