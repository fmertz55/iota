from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import component_labels, csv_bool, write_csv
from continuation import clone_world
from iota_rig import World, load_config
from phase_free_class_matrix import analyze_transition, run_to_checkpoint, snapshot_stats
from phase_free_constraint_transport import (
    active_coords,
    component_coord_sets,
    ledger_error,
    neighbor_label_set,
    pair_distances,
    pair_reachability,
)
from phase_source_minimization_audit import clamp_stored_phase, discover_config, phase_source_patch


CASE_FIELDNAMES = [
    "init_seed",
    "variant",
    "sample_index",
    "continuation_seed",
    "start_offset",
    "rebridge_offset",
    "horizon",
    "finding060_constraint_transport",
    "predecessor_region_count",
    "predecessor_region_sizes",
    "relation_reachable_at_rebridge",
    "address_lineages_alive_at_rebridge",
    "continuous_relation_lifetime",
    "first_lineage_loss_offset",
    "first_relation_loss_offset",
    "second_rebridge_offset",
    "second_successor_cells",
    "prior_bridge_absent_at_second_rebridge",
    "second_successor_role_critical",
    "second_successor_disjoint",
    "second_strict_transport",
    "payload_zero_all_offsets",
    "ledger_exact_all_offsets",
]

TIMELINE_FIELDNAMES = [
    "init_seed",
    "variant",
    "sample_index",
    "start_offset",
    "offset",
    "region_0_active_addresses",
    "region_1_active_addresses",
    "all_address_lineages_alive",
    "reachable_pair_fraction",
    "mean_shortest_path",
    "prior_bridge_active_cells",
    "payload_nonzero",
    "ledger_error",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Follow Finding 060 predecessor address lineages beyond rebridge."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument(
        "--event-csv",
        default="output/findings/finding060/phase_free_constraint_transport_events.csv",
    )
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--horizon", type=int, default=1024)
    parser.add_argument("--strict-only", action="store_true")
    return parser.parse_args()


def parse_coords(value: str) -> set[tuple[int, int, int]]:
    coords: set[tuple[int, int, int]] = set()
    for item in str(value).split(";"):
        if not item or item.startswith("..."):
            continue
        parts = item.split(":")
        if len(parts) == 3:
            coords.add(tuple(int(part) for part in parts))
    return coords


def read_events(path: Path, strict_only: bool) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["predecessor_bridge_role_critical"] == "1"
            and (not strict_only or row["constraint_transport"] == "1")
        ]
    return sorted(
        rows,
        key=lambda row: (
            int(row["init_seed"]),
            row["variant"],
            int(row["sample_index"]),
            int(row["start_offset"]),
        ),
    )


def reconstruct_regions(
    before: World,
    split: World,
) -> tuple[list[set[tuple[int, int, int]]], set[tuple[int, int, int]]]:
    before_stats = snapshot_stats(before)
    split_stats = snapshot_stats(split)
    transition = analyze_transition(
        before.active,
        split.active,
        before_stats,
        split_stats,
        bool(before.wrap),
    )
    original_bridge = set(transition["lost_bridge_if_restored"])
    without_original = before.active.copy()
    for coord in original_bridge:
        without_original[coord] = False
    labels, _, _, _ = component_labels(without_original, bool(before.wrap), "cube26")
    predecessor_labels: set[int] = set()
    for coord in original_bridge:
        predecessor_labels.update(neighbor_label_set(labels, coord, bool(before.wrap)))
    return component_coord_sets(labels, predecessor_labels), original_bridge


def current_relation(
    world: World,
    regions: list[set[tuple[int, int, int]]],
) -> tuple[list[set[tuple[int, int, int]]], bool, float, float | str]:
    descendants = [active_coords(world.active, region) for region in regions]
    alive = bool(descendants) and all(descendants)
    labels, _, _, _ = component_labels(world.active, bool(world.wrap), "cube26")
    reachability, _ = pair_reachability(labels, descendants)
    distances = pair_distances(world.active, descendants, bool(world.wrap))
    finite = [float(value) for value in distances if value is not None]
    mean_distance: float | str = "" if not finite else float(sum(finite) / len(finite))
    return descendants, alive, reachability, mean_distance


def causal_gained_cells(
    previous_active: np.ndarray,
    world: World,
    regions: list[set[tuple[int, int, int]]],
) -> set[tuple[int, int, int]]:
    gained = {
        tuple(int(value) for value in coord)
        for coord in np.argwhere(world.active & ~previous_active)
    }
    descendants = [active_coords(world.active, region) for region in regions]
    causal: set[tuple[int, int, int]] = set()
    for coord in gained:
        if any(coord in region for region in descendants):
            continue
        removed = world.active.copy()
        removed[coord] = False
        labels, _, _, _ = component_labels(removed, bool(world.wrap), "cube26")
        reachability, _ = pair_reachability(labels, descendants)
        if reachability < 1.0:
            causal.add(coord)
    return causal


def coords_text(coords: set[tuple[int, int, int]]) -> str:
    return ";".join(":".join(str(value) for value in coord) for coord in sorted(coords))


def replay(
    args: argparse.Namespace,
    event: dict[str, str],
    checkpoint: World,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    seed = int(event["init_seed"])
    variant = event["variant"]
    sample = int(event["sample_index"])
    continuation_seed = int(event["continuation_seed"])
    start_offset = int(event["start_offset"])
    rebridge_offset = int(event["rebridge_offset"])
    prior_bridge = parse_coords(event["successor_bridge_cells"])
    world = clone_world(checkpoint, continuation_seed)
    snapshots: dict[int, World] = {}
    timeline: list[dict[str, Any]] = []
    regions: list[set[tuple[int, int, int]]] = []
    payload_zero = True
    ledger_exact = True
    continuous_lifetime = 0
    first_lineage_loss: int | str = ""
    first_relation_loss: int | str = ""
    second_rebridge: int | str = ""
    second_successor: set[tuple[int, int, int]] = set()
    prior_absent = False
    previous_active = world.active.copy()
    loss_seen = False
    lineage_terminated = False
    reachable_at_rebridge = False
    alive_at_rebridge = False

    with phase_source_patch(variant):
        clamp_stored_phase(world, variant)
        for offset in range(int(args.horizon) + 1):
            payload_zero = payload_zero and int(np.count_nonzero(world.P)) == 0
            ledger_exact = ledger_exact and ledger_error(world) == 0.0
            if offset in {start_offset - 1, start_offset}:
                snapshots[offset] = clone_world(world, continuation_seed)
            if offset == start_offset:
                regions, reconstructed_bridge = reconstruct_regions(
                    snapshots[start_offset - 1], snapshots[start_offset]
                )
                if reconstructed_bridge != parse_coords(event["original_bridge_cells"]):
                    raise RuntimeError(
                        f"bridge reconstruction mismatch seed={seed} sample={sample} offset={start_offset}"
                    )

            if regions and offset >= rebridge_offset:
                descendants, alive, reachability, mean_distance = current_relation(world, regions)
                if offset == rebridge_offset:
                    reachable_at_rebridge = reachability == 1.0
                    alive_at_rebridge = alive
                if first_lineage_loss == "" and not alive:
                    first_lineage_loss = offset
                    lineage_terminated = True
                relation_alive = alive and reachability == 1.0
                if not loss_seen and not lineage_terminated and relation_alive:
                    continuous_lifetime += 1
                elif not loss_seen and not lineage_terminated and alive and not relation_alive:
                    loss_seen = True
                    first_relation_loss = offset
                elif (
                    loss_seen
                    and not lineage_terminated
                    and second_rebridge == ""
                    and relation_alive
                ):
                    candidate = causal_gained_cells(previous_active, world, regions)
                    if candidate:
                        second_rebridge = offset
                        second_successor = candidate
                        prior_absent = not any(bool(world.active[coord]) for coord in prior_bridge)

                sizes = [len(region) for region in descendants]
                timeline.append(
                    {
                        "init_seed": seed,
                        "variant": variant,
                        "sample_index": sample,
                        "start_offset": start_offset,
                        "offset": offset,
                        "region_0_active_addresses": sizes[0] if sizes else 0,
                        "region_1_active_addresses": sizes[1] if len(sizes) > 1 else 0,
                        "all_address_lineages_alive": csv_bool(alive),
                        "reachable_pair_fraction": reachability,
                        "mean_shortest_path": mean_distance,
                        "prior_bridge_active_cells": sum(
                            bool(world.active[coord]) for coord in prior_bridge
                        ),
                        "payload_nonzero": int(np.count_nonzero(world.P)),
                        "ledger_error": ledger_error(world),
                    }
                )

            if offset < int(args.horizon):
                previous_active = world.active.copy()
                iota_rig.step(world, cfg)
                clamp_stored_phase(world, variant)

    successor_critical = bool(second_successor)
    successor_disjoint = bool(second_successor) and not bool(prior_bridge & second_successor)
    second_strict = bool(
        second_rebridge != ""
        and prior_absent
        and successor_critical
        and successor_disjoint
        and payload_zero
        and ledger_exact
    )
    case = {
        "init_seed": seed,
        "variant": variant,
        "sample_index": sample,
        "continuation_seed": continuation_seed,
        "start_offset": start_offset,
        "rebridge_offset": rebridge_offset,
        "horizon": int(args.horizon),
        "finding060_constraint_transport": event["constraint_transport"],
        "predecessor_region_count": len(regions),
        "predecessor_region_sizes": ";".join(str(len(region)) for region in regions),
        "relation_reachable_at_rebridge": csv_bool(reachable_at_rebridge),
        "address_lineages_alive_at_rebridge": csv_bool(alive_at_rebridge),
        "continuous_relation_lifetime": continuous_lifetime,
        "first_lineage_loss_offset": first_lineage_loss,
        "first_relation_loss_offset": first_relation_loss,
        "second_rebridge_offset": second_rebridge,
        "second_successor_cells": coords_text(second_successor),
        "prior_bridge_absent_at_second_rebridge": csv_bool(prior_absent),
        "second_successor_role_critical": csv_bool(successor_critical),
        "second_successor_disjoint": csv_bool(successor_disjoint),
        "second_strict_transport": csv_bool(second_strict),
        "payload_zero_all_offsets": csv_bool(payload_zero),
        "ledger_exact_all_offsets": csv_bool(ledger_exact),
    }
    return case, timeline


def main() -> None:
    args = parse_args()
    events = read_events(Path(args.event_csv), bool(args.strict_only))
    keys = sorted({(int(row["init_seed"]), row["variant"]) for row in events})
    configs: dict[int, dict[str, Any]] = {}
    checkpoints: dict[tuple[int, str], World] = {}
    for seed, variant in keys:
        configs.setdefault(seed, load_config(discover_config(args.config_dir, seed)))
        print(f"checkpoint seed={seed} variant={variant}", flush=True)
        checkpoints[(seed, variant)] = run_to_checkpoint(
            configs[seed], variant, int(args.checkpoint_tick)
        )

    cases: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    for event in events:
        key = (int(event["init_seed"]), event["variant"])
        case, rows = replay(args, event, checkpoints[key], configs[key[0]])
        cases.append(case)
        timeline.extend(rows)
        print(
            f"event seed={case['init_seed']} sample={case['sample_index']} "
            f"offset={case['start_offset']} lifetime={case['continuous_relation_lifetime']} "
            f"second_transport={case['second_strict_transport']}",
            flush=True,
        )

    prefix = Path(args.output_prefix)
    case_path = prefix.with_name(prefix.name + "_cases.csv")
    timeline_path = prefix.with_name(prefix.name + "_timeline.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(case_path, CASE_FIELDNAMES, cases)
    write_csv(timeline_path, TIMELINE_FIELDNAMES, timeline)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "cases": len(cases),
        "strict_input_cases": sum(int(row["finding060_constraint_transport"]) for row in cases),
        "second_strict_transport_cases": sum(int(row["second_strict_transport"]) for row in cases),
        "all_payload_zero": all(int(row["payload_zero_all_offsets"]) for row in cases),
        "all_ledger_exact": all(int(row["ledger_exact_all_offsets"]) for row in cases),
        "case_csv": str(case_path),
        "timeline_csv": str(timeline_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
