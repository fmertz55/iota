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
    clamp_stored_phase,
    discover_config,
    phase_source_patch,
)


DEFAULT_SEEDS = (42, 43, 44, 45, 46, 56)
DEFAULT_VARIANTS = (
    "zero_phase",
    "vector_step_only_vector_phase",
    "takeover_only_vector_phase",
    "rotation_only_vector_phase",
    "takeover_rotation_vector_phase",
)

SUMMARY_FIELDNAMES = [
    "init_seed",
    "variant",
    "checkpoint_tick",
    "sample_index",
    "horizon",
    "continuation_seed",
    "checkpoint_active",
    "checkpoint_component_count",
    "checkpoint_largest_component",
    "final_active",
    "final_component_count",
    "final_largest_component",
    "payload_zero_all_offsets",
    "ledger_exact_all_offsets",
    "max_abs_ledger_error",
    "any_component_signal",
    "signal_interval_count",
    "signal_offsets",
    "first_signal_start",
    "first_signal_end",
    "first_signal_duration",
    "max_abs_component_delta",
    "component_split_transition_count",
    "component_rebridge_transition_count",
    "bridge_loss_event_count",
    "bridge_loss_rebridge_interval_count",
    "first_bridge_loss_offset",
    "first_bridge_loss_coords",
    "bridge_loss_coords",
    "articulation_before_loss_count",
    "articulation_before_loss_coords",
    "rebridge_count",
    "first_rebridge_delay",
    "event_class_pass",
]

EVENT_FIELDNAMES = [
    "init_seed",
    "variant",
    "checkpoint_tick",
    "sample_index",
    "horizon",
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
    "lost_bridge_if_restored_count",
    "lost_bridge_if_restored_coords",
    "gained_bridge_if_removed_count",
    "gained_bridge_if_removed_coords",
]

SIGNAL_FIELDNAMES = [
    "init_seed",
    "variant",
    "checkpoint_tick",
    "sample_index",
    "horizon",
    "continuation_seed",
    "start_offset",
    "end_offset",
    "duration",
    "rebridged",
    "rebridge_offset",
    "rebridge_delay",
    "max_abs_component_delta",
    "start_component_count",
    "end_component_count",
    "start_active",
    "end_active",
    "start_largest",
    "end_largest",
    "start_top_component_sizes",
    "end_top_component_sizes",
    "bridge_loss_at_start",
    "bridge_loss_coords_at_start",
    "articulation_before_loss_at_start",
    "articulation_before_loss_coords_at_start",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed robustness audit for no-stored-phase bridge-loss component events."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--variants", nargs="+", default=list(DEFAULT_VARIANTS))
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--sample-index", type=int, default=6)
    parser.add_argument("--horizon", type=int, default=600)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--coord-limit", type=int, default=24)
    return parser.parse_args()


def coords_from_active(active: np.ndarray) -> set[tuple[int, int, int]]:
    return {tuple(int(value) for value in coord) for coord in np.argwhere(active)}


def coords_text(coords: set[tuple[int, int, int]], limit: int) -> str:
    ordered = sorted(coords)
    clipped = ordered[: int(limit)]
    suffix = "" if len(ordered) <= int(limit) else f";...+{len(ordered) - int(limit)}"
    return ";".join(f"{x}:{y}:{z}" for x, y, z in clipped) + suffix


def ledger_error(world: World) -> float:
    active_total = int(np.sum(world.A[world.active], dtype=np.int64))
    latent_total = int(np.sum(world.latent_A[~world.active], dtype=np.int64))
    return float(active_total + latent_total - int(world.initial_total_A))


def component_snapshot(active: np.ndarray, wrap: bool) -> tuple[dict[int, int], int, int]:
    _, sizes, count, largest = component_labels(active, bool(wrap), "cube26")
    return sizes, int(count), int(largest)


def top_component_sizes(sizes: dict[int, int], limit: int = 8) -> str:
    return ";".join(str(size) for size in sorted(sizes.values(), reverse=True)[:limit])


def snapshot_stats(world: World) -> dict[str, Any]:
    sizes, count, largest = component_snapshot(world.active, bool(world.wrap))
    return {
        "active": int(np.count_nonzero(world.active)),
        "component_count": count,
        "largest": largest,
        "top_sizes": top_component_sizes(sizes),
        "payload_nonzero": int(np.count_nonzero(world.active & (world.P != 0))),
        "ledger_error": ledger_error(world),
    }


def analyze_transition(
    args: argparse.Namespace,
    seed: int,
    variant: str,
    continuation_seed: int,
    offset_to: int,
    before_active: np.ndarray,
    after_active: np.ndarray,
    before_stats: dict[str, Any],
    after_stats: dict[str, Any],
    wrap: bool,
) -> dict[str, Any]:
    before_coords = coords_from_active(before_active)
    after_coords = coords_from_active(after_active)
    gained = after_coords - before_coords
    lost = before_coords - after_coords

    lost_articulation_before: set[tuple[int, int, int]] = set()
    lost_bridge_if_restored: set[tuple[int, int, int]] = set()
    for coord in lost:
        before_without = before_active.copy()
        before_without[coord] = False
        _, before_without_count, _ = component_snapshot(before_without, wrap)
        if before_without_count > int(before_stats["component_count"]):
            lost_articulation_before.add(coord)

        after_with = after_active.copy()
        after_with[coord] = True
        _, after_with_count, _ = component_snapshot(after_with, wrap)
        if after_with_count < int(after_stats["component_count"]):
            lost_bridge_if_restored.add(coord)

    gained_bridge_if_removed: set[tuple[int, int, int]] = set()
    for coord in gained:
        after_without = after_active.copy()
        after_without[coord] = False
        _, after_without_count, _ = component_snapshot(after_without, wrap)
        if after_without_count > int(after_stats["component_count"]):
            gained_bridge_if_removed.add(coord)

    return {
        "init_seed": int(seed),
        "variant": variant,
        "checkpoint_tick": int(args.checkpoint_tick),
        "sample_index": int(args.sample_index),
        "horizon": int(args.horizon),
        "continuation_seed": continuation_seed,
        "offset_from": int(offset_to - 1),
        "offset_to": int(offset_to),
        "component_count_before": int(before_stats["component_count"]),
        "component_count_after": int(after_stats["component_count"]),
        "component_delta": int(after_stats["component_count"]) - int(before_stats["component_count"]),
        "largest_before": int(before_stats["largest"]),
        "largest_after": int(after_stats["largest"]),
        "largest_delta": int(after_stats["largest"]) - int(before_stats["largest"]),
        "active_before": int(before_stats["active"]),
        "active_after": int(after_stats["active"]),
        "active_delta": int(after_stats["active"]) - int(before_stats["active"]),
        "gained_count": len(gained),
        "lost_count": len(lost),
        "gained_coords": coords_text(gained, int(args.coord_limit)),
        "lost_coords": coords_text(lost, int(args.coord_limit)),
        "lost_articulation_before_count": len(lost_articulation_before),
        "lost_articulation_before_coords": coords_text(lost_articulation_before, int(args.coord_limit)),
        "lost_bridge_if_restored_count": len(lost_bridge_if_restored),
        "lost_bridge_if_restored_coords": coords_text(lost_bridge_if_restored, int(args.coord_limit)),
        "gained_bridge_if_removed_count": len(gained_bridge_if_removed),
        "gained_bridge_if_removed_coords": coords_text(gained_bridge_if_removed, int(args.coord_limit)),
    }


def should_keep_event(row: dict[str, Any]) -> bool:
    return (
        int(row["component_delta"]) != 0
        or int(row["lost_articulation_before_count"]) != 0
        or int(row["lost_bridge_if_restored_count"]) != 0
        or int(row["gained_bridge_if_removed_count"]) != 0
    )


def run_case(
    args: argparse.Namespace,
    seed: int,
    variant: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    cfg = load_config(discover_config(args.config_dir, int(seed)))
    continuation_seed = deterministic_continuation_seed(
        int(args.rng_seed_base),
        int(args.checkpoint_tick),
        int(args.sample_index),
    )
    interesting_events: list[dict[str, Any]] = []
    signal_rows: list[dict[str, Any]] = []
    signal_offsets: list[int] = []
    bridge_loss_coords: set[tuple[int, int, int]] = set()
    articulation_coords: set[tuple[int, int, int]] = set()
    signal_open: dict[str, Any] | None = None
    previous_active: np.ndarray | None = None
    previous_stats: dict[str, Any] | None = None

    payload_zero_all = True
    ledger_exact_all = True
    max_abs_ledger_error = 0.0
    checkpoint_stats: dict[str, Any] | None = None
    final_stats: dict[str, Any] | None = None
    split_transition_count = 0
    rebridge_transition_count = 0
    bridge_loss_event_count = 0
    bridge_loss_rebridge_interval_count = 0
    max_abs_component_delta = 0
    first_bridge_loss_offset: int | None = None
    first_rebridge_delay: int | None = None

    with phase_source_patch(variant):
        world = iota_rig.init_world(cfg)
        clamp_stored_phase(world, variant)
        wrap = bool(world.wrap)
        end_tick = int(args.checkpoint_tick) + int(args.horizon)
        for tick in range(0, end_tick + 1):
            if tick == int(args.checkpoint_tick):
                world = clone_world(world, continuation_seed)
                clamp_stored_phase(world, variant)
            if tick >= int(args.checkpoint_tick):
                offset = tick - int(args.checkpoint_tick)
                stats = snapshot_stats(world)
                if offset == 0:
                    checkpoint_stats = stats
                payload_zero_all = payload_zero_all and int(stats["payload_nonzero"]) == 0
                ledger_exact_all = ledger_exact_all and abs(float(stats["ledger_error"])) == 0.0
                max_abs_ledger_error = max(max_abs_ledger_error, abs(float(stats["ledger_error"])))

                transition: dict[str, Any] | None = None
                if previous_active is not None and previous_stats is not None:
                    transition = analyze_transition(
                        args,
                        int(seed),
                        variant,
                        continuation_seed,
                        offset,
                        previous_active,
                        world.active,
                        previous_stats,
                        stats,
                        wrap,
                    )
                    max_abs_component_delta = max(
                        max_abs_component_delta,
                        abs(int(transition["component_delta"])),
                    )
                    if int(transition["component_delta"]) > 0:
                        split_transition_count += 1
                    if int(transition["component_delta"]) < 0:
                        rebridge_transition_count += 1
                    if int(transition["lost_bridge_if_restored_count"]) > 0:
                        bridge_loss_event_count += 1
                        bridge_loss_coords.update(parse_coords(str(transition["lost_bridge_if_restored_coords"])))
                        if first_bridge_loss_offset is None:
                            first_bridge_loss_offset = offset
                    if int(transition["lost_articulation_before_count"]) > 0:
                        articulation_coords.update(parse_coords(str(transition["lost_articulation_before_coords"])))
                    if should_keep_event(transition):
                        interesting_events.append(transition)

                checkpoint_count = int(checkpoint_stats["component_count"])
                in_signal = int(stats["component_count"]) != checkpoint_count
                if in_signal:
                    signal_offsets.append(offset)
                    if signal_open is None:
                        signal_open = {
                            "start_offset": offset,
                            "start_stats": stats.copy(),
                            "start_transition": transition,
                            "max_abs_delta": abs(int(stats["component_count"]) - checkpoint_count),
                        }
                    else:
                        signal_open["max_abs_delta"] = max(
                            int(signal_open["max_abs_delta"]),
                            abs(int(stats["component_count"]) - checkpoint_count),
                        )
                elif signal_open is not None:
                    signal_row = close_signal_row(
                        args,
                        int(seed),
                        variant,
                        continuation_seed,
                        signal_open,
                        previous_stats if previous_stats is not None else stats,
                        offset - 1,
                        offset,
                    )
                    signal_rows.append(signal_row)
                    if int(signal_row["bridge_loss_at_start"]) == 1:
                        bridge_loss_rebridge_interval_count += 1
                        if first_rebridge_delay is None:
                            first_rebridge_delay = int(signal_row["rebridge_delay"])
                    signal_open = None

                previous_active = world.active.copy()
                previous_stats = stats
                final_stats = stats

            if tick >= end_tick:
                break
            clamp_stored_phase(world, variant)
            iota_rig.step(world, cfg)
            clamp_stored_phase(world, variant)

    if signal_open is not None and previous_stats is not None:
        signal_rows.append(
            close_signal_row(
                args,
                int(seed),
                variant,
                continuation_seed,
                signal_open,
                previous_stats,
                int(args.horizon),
                "",
            )
        )

    if checkpoint_stats is None or final_stats is None:
        raise RuntimeError("missing checkpoint/final stats")
    summary = {
        "init_seed": int(seed),
        "variant": variant,
        "checkpoint_tick": int(args.checkpoint_tick),
        "sample_index": int(args.sample_index),
        "horizon": int(args.horizon),
        "continuation_seed": continuation_seed,
        "checkpoint_active": int(checkpoint_stats["active"]),
        "checkpoint_component_count": int(checkpoint_stats["component_count"]),
        "checkpoint_largest_component": int(checkpoint_stats["largest"]),
        "final_active": int(final_stats["active"]),
        "final_component_count": int(final_stats["component_count"]),
        "final_largest_component": int(final_stats["largest"]),
        "payload_zero_all_offsets": csv_bool(payload_zero_all),
        "ledger_exact_all_offsets": csv_bool(ledger_exact_all),
        "max_abs_ledger_error": max_abs_ledger_error,
        "any_component_signal": csv_bool(bool(signal_offsets)),
        "signal_interval_count": len(signal_rows),
        "signal_offsets": ";".join(str(offset) for offset in signal_offsets),
        "first_signal_start": "" if not signal_rows else int(signal_rows[0]["start_offset"]),
        "first_signal_end": "" if not signal_rows else int(signal_rows[0]["end_offset"]),
        "first_signal_duration": "" if not signal_rows else int(signal_rows[0]["duration"]),
        "max_abs_component_delta": max_abs_component_delta,
        "component_split_transition_count": split_transition_count,
        "component_rebridge_transition_count": rebridge_transition_count,
        "bridge_loss_event_count": bridge_loss_event_count,
        "bridge_loss_rebridge_interval_count": bridge_loss_rebridge_interval_count,
        "first_bridge_loss_offset": "" if first_bridge_loss_offset is None else first_bridge_loss_offset,
        "first_bridge_loss_coords": coords_text(set() if first_bridge_loss_offset is None else bridge_loss_coords, int(args.coord_limit)),
        "bridge_loss_coords": coords_text(bridge_loss_coords, int(args.coord_limit)),
        "articulation_before_loss_count": len(articulation_coords),
        "articulation_before_loss_coords": coords_text(articulation_coords, int(args.coord_limit)),
        "rebridge_count": rebridge_transition_count,
        "first_rebridge_delay": "" if first_rebridge_delay is None else first_rebridge_delay,
        "event_class_pass": csv_bool(bridge_loss_rebridge_interval_count > 0),
    }
    return summary, interesting_events, signal_rows


def parse_coords(text: str) -> set[tuple[int, int, int]]:
    coords: set[tuple[int, int, int]] = set()
    if not text:
        return coords
    for item in text.split(";"):
        if not item or item.startswith("...+"):
            continue
        parts = item.split(":")
        if len(parts) != 3:
            continue
        coords.add((int(parts[0]), int(parts[1]), int(parts[2])))
    return coords


def close_signal_row(
    args: argparse.Namespace,
    seed: int,
    variant: str,
    continuation_seed: int,
    signal_open: dict[str, Any],
    end_stats: dict[str, Any],
    end_offset: int,
    rebridge_offset: int | str,
) -> dict[str, Any]:
    start_stats = signal_open["start_stats"]
    start_transition = signal_open.get("start_transition")
    bridge_loss_at_start = (
        start_transition is not None
        and int(start_transition["lost_bridge_if_restored_count"]) > 0
    )
    articulation_at_start = (
        start_transition is not None
        and int(start_transition["lost_articulation_before_count"]) > 0
    )
    start_offset = int(signal_open["start_offset"])
    return {
        "init_seed": int(seed),
        "variant": variant,
        "checkpoint_tick": int(args.checkpoint_tick),
        "sample_index": int(args.sample_index),
        "horizon": int(args.horizon),
        "continuation_seed": continuation_seed,
        "start_offset": start_offset,
        "end_offset": int(end_offset),
        "duration": int(end_offset) - start_offset + 1,
        "rebridged": csv_bool(rebridge_offset != ""),
        "rebridge_offset": rebridge_offset,
        "rebridge_delay": "" if rebridge_offset == "" else int(rebridge_offset) - start_offset,
        "max_abs_component_delta": int(signal_open["max_abs_delta"]),
        "start_component_count": int(start_stats["component_count"]),
        "end_component_count": int(end_stats["component_count"]),
        "start_active": int(start_stats["active"]),
        "end_active": int(end_stats["active"]),
        "start_largest": int(start_stats["largest"]),
        "end_largest": int(end_stats["largest"]),
        "start_top_component_sizes": str(start_stats["top_sizes"]),
        "end_top_component_sizes": str(end_stats["top_sizes"]),
        "bridge_loss_at_start": csv_bool(bridge_loss_at_start),
        "bridge_loss_coords_at_start": (
            "" if start_transition is None else str(start_transition["lost_bridge_if_restored_coords"])
        ),
        "articulation_before_loss_at_start": csv_bool(articulation_at_start),
        "articulation_before_loss_coords_at_start": (
            "" if start_transition is None else str(start_transition["lost_articulation_before_coords"])
        ),
    }


def aggregate_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    variants = sorted({str(row["variant"]) for row in summary_rows})
    for variant in variants:
        subset = [row for row in summary_rows if str(row["variant"]) == variant]
        rows.append(
            {
                "variant": variant,
                "cases": len(subset),
                "component_signal_cases": sum(int(row["any_component_signal"]) for row in subset),
                "event_class_pass_cases": sum(int(row["event_class_pass"]) for row in subset),
                "bridge_loss_events": sum(int(row["bridge_loss_event_count"]) for row in subset),
                "rebridge_transitions": sum(int(row["rebridge_count"]) for row in subset),
                "payload_zero_cases": sum(int(row["payload_zero_all_offsets"]) for row in subset),
                "ledger_exact_cases": sum(int(row["ledger_exact_all_offsets"]) for row in subset),
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    output_prefix = Path(args.output_prefix)
    summary_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    signal_rows: list[dict[str, Any]] = []
    for seed in args.seeds:
        for variant in args.variants:
            summary, events, signals = run_case(args, int(seed), str(variant))
            summary_rows.append(summary)
            event_rows.extend(events)
            signal_rows.extend(signals)
            print(
                f"seed={seed} variant={variant} "
                f"signal={summary['any_component_signal']} "
                f"bridge_loss={summary['bridge_loss_event_count']} "
                f"event_pass={summary['event_class_pass']}"
            )

    aggregate_fieldnames = [
        "variant",
        "cases",
        "component_signal_cases",
        "event_class_pass_cases",
        "bridge_loss_events",
        "rebridge_transitions",
        "payload_zero_cases",
        "ledger_exact_cases",
    ]
    summary_path = output_prefix.with_name(output_prefix.name + "_summary.csv")
    event_path = output_prefix.with_name(output_prefix.name + "_events.csv")
    signal_path = output_prefix.with_name(output_prefix.name + "_signals.csv")
    aggregate_path = output_prefix.with_name(output_prefix.name + "_aggregate.csv")
    write_csv(summary_path, SUMMARY_FIELDNAMES, summary_rows)
    write_csv(event_path, EVENT_FIELDNAMES, event_rows)
    write_csv(signal_path, SIGNAL_FIELDNAMES, signal_rows)
    write_csv(aggregate_path, aggregate_fieldnames, aggregate_rows(summary_rows))
    payload = {
        "summary_csv": str(summary_path),
        "event_csv": str(event_path),
        "signal_csv": str(signal_path),
        "aggregate_csv": str(aggregate_path),
        "aggregate": aggregate_rows(summary_rows),
    }
    json_path = output_prefix.with_name(output_prefix.name + "_summary.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
