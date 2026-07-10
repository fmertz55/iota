from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import component_labels, csv_bool, write_csv
from continuation import clone_world, deterministic_continuation_seed
from iota_rig import World, load_config
from phase_source_minimization_audit import (
    discover_config,
    phase_source_patch,
    clamp_stored_phase,
)


VARIANTS = (
    "zero_phase",
    "takeover_only_vector_phase",
    "rotation_only_vector_phase",
    "takeover_rotation_vector_phase",
)

SNAPSHOT_FIELDNAMES = [
    "variant",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "offset",
    "tick",
    "active_iotas",
    "component_count",
    "largest_component",
    "top_component_sizes",
    "nonzero_payload_iotas",
    "ledger_error",
]

TRANSITION_FIELDNAMES = [
    "variant",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "offset_from",
    "offset_to",
    "component_count_before",
    "component_count_after",
    "component_delta",
    "largest_before",
    "largest_after",
    "largest_delta",
    "active_before",
    "active_after",
    "active_delta",
    "gained_count",
    "lost_count",
    "gained_coords",
    "lost_coords",
    "lost_articulation_before_count",
    "lost_articulation_before_coords",
    "gained_bridge_if_removed_count",
    "gained_isolated_if_removed_count",
    "lost_bridge_if_restored_count",
    "lost_isolated_if_restored_count",
    "gained_bridge_if_removed_coords",
    "gained_isolated_if_removed_coords",
    "lost_bridge_if_restored_coords",
    "lost_isolated_if_restored_coords",
]

SUMMARY_FIELDNAMES = [
    "variant",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "signal_offsets",
    "first_signal_offset",
    "vanish_offset",
    "checkpoint_component_count",
    "checkpoint_largest_component",
    "min_component_count_window",
    "max_component_count_window",
    "max_component_delta_transition",
    "min_component_delta_transition",
    "max_gained_bridge_if_removed_count",
    "max_lost_bridge_if_restored_count",
    "payload_zero_all_snapshots",
    "ledger_exact_all_snapshots",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trace active-set topology around the no-stored-phase component signal."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--seed", type=int, default=46)
    parser.add_argument("--variants", nargs="+", choices=VARIANTS, default=list(VARIANTS))
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--sample-index", type=int, default=6)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--window-start", type=int, default=128)
    parser.add_argument("--window-end", type=int, default=145)
    parser.add_argument("--coord-limit", type=int, default=16)
    return parser.parse_args()


def coord_key(coord: tuple[int, int, int]) -> tuple[int, int, int]:
    return int(coord[0]), int(coord[1]), int(coord[2])


def coords_from_active(active: np.ndarray) -> set[tuple[int, int, int]]:
    return {coord_key(tuple(coord)) for coord in np.argwhere(active)}


def coords_text(coords: set[tuple[int, int, int]], limit: int) -> str:
    ordered = sorted(coords)
    clipped = ordered[: int(limit)]
    suffix = "" if len(ordered) <= int(limit) else f";...+{len(ordered) - int(limit)}"
    return ";".join(f"{x}:{y}:{z}" for x, y, z in clipped) + suffix


def ledger_error(world: World) -> float:
    active_total = int(np.sum(world.A[world.active], dtype=np.int64))
    latent_total = int(np.sum(world.latent_A[~world.active], dtype=np.int64))
    return float(active_total + latent_total - int(world.initial_total_A))


def component_snapshot(active: np.ndarray, wrap: bool) -> tuple[np.ndarray, dict[int, int], int, int]:
    labels, sizes, count, largest = component_labels(active, bool(wrap), "cube26")
    return labels, sizes, int(count), int(largest)


def top_component_sizes(sizes: dict[int, int], limit: int = 8) -> str:
    return ";".join(str(size) for size in sorted(sizes.values(), reverse=True)[:limit])


def trace_variant(args: argparse.Namespace, cfg: dict[str, Any], variant: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    continuation_seed = deterministic_continuation_seed(
        int(args.rng_seed_base),
        int(args.checkpoint_tick),
        int(args.sample_index),
    )
    snapshots: list[dict[str, Any]] = []
    transition_rows: list[dict[str, Any]] = []
    active_by_offset: dict[int, np.ndarray] = {}
    component_by_offset: dict[int, tuple[dict[int, int], int, int]] = {}
    wrap = False

    with phase_source_patch(variant):
        world = iota_rig.init_world(cfg)
        clamp_stored_phase(world, variant)
        wrap = bool(world.wrap)
        end_tick = int(args.checkpoint_tick) + int(args.window_end)
        for tick in range(0, end_tick + 1):
            if tick == int(args.checkpoint_tick):
                world = clone_world(world, continuation_seed)
                clamp_stored_phase(world, variant)
            offset = tick - int(args.checkpoint_tick)
            if int(args.window_start) <= offset <= int(args.window_end):
                _, sizes, count, largest = component_snapshot(world.active, bool(world.wrap))
                active_by_offset[offset] = world.active.copy()
                component_by_offset[offset] = (sizes, count, largest)
                snapshots.append(
                    {
                        "variant": variant,
                        "init_seed": int(args.seed),
                        "checkpoint_tick": int(args.checkpoint_tick),
                        "sample_index": int(args.sample_index),
                        "continuation_seed": continuation_seed,
                        "offset": offset,
                        "tick": tick,
                        "active_iotas": int(np.count_nonzero(world.active)),
                        "component_count": count,
                        "largest_component": largest,
                        "top_component_sizes": top_component_sizes(sizes),
                        "nonzero_payload_iotas": int(np.count_nonzero(world.active & (world.P != 0))),
                        "ledger_error": ledger_error(world),
                    }
                )
            if tick >= end_tick:
                break
            clamp_stored_phase(world, variant)
            iota_rig.step(world, cfg)
            clamp_stored_phase(world, variant)

    for offset in range(int(args.window_start) + 1, int(args.window_end) + 1):
        before = active_by_offset[offset - 1]
        after = active_by_offset[offset]
        before_sizes, before_count, before_largest = component_by_offset[offset - 1]
        after_sizes, after_count, after_largest = component_by_offset[offset]
        before_coords = coords_from_active(before)
        after_coords = coords_from_active(after)
        gained = after_coords - before_coords
        lost = before_coords - after_coords

        gained_bridge: set[tuple[int, int, int]] = set()
        gained_isolated: set[tuple[int, int, int]] = set()
        for coord in gained:
            test_active = after.copy()
            test_active[coord] = False
            _, _, test_count, _ = component_snapshot(test_active, wrap)
            if test_count > after_count:
                gained_bridge.add(coord)
            if test_count < after_count:
                gained_isolated.add(coord)

        lost_articulation_before: set[tuple[int, int, int]] = set()
        lost_bridge: set[tuple[int, int, int]] = set()
        lost_isolated: set[tuple[int, int, int]] = set()
        for coord in lost:
            before_without = before.copy()
            before_without[coord] = False
            _, _, before_without_count, _ = component_snapshot(before_without, wrap)
            if before_without_count > before_count:
                lost_articulation_before.add(coord)

            test_active = after.copy()
            test_active[coord] = True
            _, _, test_count, _ = component_snapshot(test_active, wrap)
            if test_count < after_count:
                lost_bridge.add(coord)
            if test_count > after_count:
                lost_isolated.add(coord)

        transition_rows.append(
            {
                "variant": variant,
                "init_seed": int(args.seed),
                "checkpoint_tick": int(args.checkpoint_tick),
                "sample_index": int(args.sample_index),
                "continuation_seed": continuation_seed,
                "offset_from": offset - 1,
                "offset_to": offset,
                "component_count_before": before_count,
                "component_count_after": after_count,
                "component_delta": int(after_count - before_count),
                "largest_before": before_largest,
                "largest_after": after_largest,
                "largest_delta": int(after_largest - before_largest),
                "active_before": int(np.count_nonzero(before)),
                "active_after": int(np.count_nonzero(after)),
                "active_delta": int(np.count_nonzero(after) - np.count_nonzero(before)),
                "gained_count": len(gained),
                "lost_count": len(lost),
                "gained_coords": coords_text(gained, int(args.coord_limit)),
                "lost_coords": coords_text(lost, int(args.coord_limit)),
                "lost_articulation_before_count": len(lost_articulation_before),
                "lost_articulation_before_coords": coords_text(lost_articulation_before, int(args.coord_limit)),
                "gained_bridge_if_removed_count": len(gained_bridge),
                "gained_isolated_if_removed_count": len(gained_isolated),
                "lost_bridge_if_restored_count": len(lost_bridge),
                "lost_isolated_if_restored_count": len(lost_isolated),
                "gained_bridge_if_removed_coords": coords_text(gained_bridge, int(args.coord_limit)),
                "gained_isolated_if_removed_coords": coords_text(gained_isolated, int(args.coord_limit)),
                "lost_bridge_if_restored_coords": coords_text(lost_bridge, int(args.coord_limit)),
                "lost_isolated_if_restored_coords": coords_text(lost_isolated, int(args.coord_limit)),
            }
        )
    return snapshots, transition_rows


def build_summary(args: argparse.Namespace, variant: str, snapshots: list[dict[str, Any]], transitions: list[dict[str, Any]]) -> dict[str, Any]:
    checkpoint_count = int(snapshots[0]["component_count"]) if snapshots else 0
    checkpoint_largest = int(snapshots[0]["largest_component"]) if snapshots else 0
    signal_offsets = [
        int(row["offset"])
        for row in snapshots
        if int(row["component_count"]) != checkpoint_count
    ]
    vanish_offset = ""
    if signal_offsets:
        for row in snapshots:
            if int(row["offset"]) > signal_offsets[0] and int(row["component_count"]) == checkpoint_count:
                vanish_offset = int(row["offset"])
                break
    return {
        "variant": variant,
        "init_seed": int(args.seed),
        "checkpoint_tick": int(args.checkpoint_tick),
        "sample_index": int(args.sample_index),
        "continuation_seed": deterministic_continuation_seed(
            int(args.rng_seed_base),
            int(args.checkpoint_tick),
            int(args.sample_index),
        ),
        "signal_offsets": ";".join(str(offset) for offset in signal_offsets),
        "first_signal_offset": "" if not signal_offsets else signal_offsets[0],
        "vanish_offset": vanish_offset,
        "checkpoint_component_count": checkpoint_count,
        "checkpoint_largest_component": checkpoint_largest,
        "min_component_count_window": min(int(row["component_count"]) for row in snapshots),
        "max_component_count_window": max(int(row["component_count"]) for row in snapshots),
        "max_component_delta_transition": max(int(row["component_delta"]) for row in transitions),
        "min_component_delta_transition": min(int(row["component_delta"]) for row in transitions),
        "max_gained_bridge_if_removed_count": max(
            int(row["gained_bridge_if_removed_count"]) for row in transitions
        ),
        "max_lost_bridge_if_restored_count": max(
            int(row["lost_bridge_if_restored_count"]) for row in transitions
        ),
        "payload_zero_all_snapshots": csv_bool(
            all(int(row["nonzero_payload_iotas"]) == 0 for row in snapshots)
        ),
        "ledger_exact_all_snapshots": csv_bool(
            all(abs(float(row["ledger_error"])) == 0.0 for row in snapshots)
        ),
    }


def main() -> None:
    args = parse_args()
    cfg = load_config(discover_config(args.config_dir, int(args.seed)))
    output_prefix = Path(args.output_prefix)
    all_snapshots: list[dict[str, Any]] = []
    all_transitions: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for variant in args.variants:
        snapshots, transitions = trace_variant(args, cfg, variant)
        all_snapshots.extend(snapshots)
        all_transitions.extend(transitions)
        summary = build_summary(args, variant, snapshots, transitions)
        summaries.append(summary)
        print(
            f"variant={variant} signal={summary['signal_offsets'] or 'none'} "
            f"max_bridge_gain={summary['max_gained_bridge_if_removed_count']} "
            f"max_lost_bridge={summary['max_lost_bridge_if_restored_count']}"
        )

    snapshot_path = output_prefix.with_name(output_prefix.name + "_snapshots.csv")
    transition_path = output_prefix.with_name(output_prefix.name + "_transitions.csv")
    summary_path = output_prefix.with_name(output_prefix.name + "_summary.csv")
    write_csv(snapshot_path, SNAPSHOT_FIELDNAMES, all_snapshots)
    write_csv(transition_path, TRANSITION_FIELDNAMES, all_transitions)
    write_csv(summary_path, SUMMARY_FIELDNAMES, summaries)
    payload = {
        "snapshot_csv": str(snapshot_path),
        "transition_csv": str(transition_path),
        "summary_csv": str(summary_path),
        "summary_by_variant": {str(row["variant"]): row for row in summaries},
    }
    json_path = output_prefix.with_name(output_prefix.name + "_summary.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
