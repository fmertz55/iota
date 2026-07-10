from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import component_labels, csv_bool, write_csv
from continuation import clone_world, deterministic_continuation_seed
from iota_rig import World, candidate_neighbor_steps, load_config
from phase_source_minimization_audit import (
    clamp_stored_phase,
    discover_config,
    phase_source_patch,
)


DEFAULT_SEEDS = (42, 43, 44, 45, 46, 56)
DEFAULT_SAMPLES = tuple(range(8))
DEFAULT_VARIANTS = (
    "zero_phase",
    "takeover_only_vector_phase",
    "takeover_rotation_vector_phase",
)

CASE_FIELDNAMES = [
    "init_seed",
    "variant",
    "sample_index",
    "checkpoint_tick",
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
    "signal_interval_count",
    "case_class",
    "class_a_event_count",
    "class_b_event_count",
    "non_bridge_event_count",
    "bridge_unresolved_event_count",
    "first_signal_start",
    "first_signal_class",
]

SIGNAL_FIELDNAMES = [
    "init_seed",
    "variant",
    "sample_index",
    "checkpoint_tick",
    "horizon",
    "continuation_seed",
    "start_offset",
    "end_offset",
    "duration",
    "rebridged",
    "rebridge_offset",
    "rebridge_delay",
    "event_class",
    "start_component_count",
    "end_component_count",
    "start_active",
    "end_active",
    "start_largest",
    "end_largest",
    "start_bridge_loss_count",
    "start_articulation_before_loss_count",
    "start_lost_bridge_coords",
    "start_lost_articulation_coords",
    "original_bridge_any_returned",
    "original_bridge_all_returned",
    "post_rebridge_bridge_path_coords",
    "bridge_path_jaccard",
    "structural_displacement",
    "same_bridge_restoration",
]

AGGREGATE_FIELDNAMES = [
    "variant",
    "cases",
    "no_signal_cases",
    "class_a_cases",
    "class_b_cases",
    "non_bridge_signal_cases",
    "bridge_unresolved_cases",
    "signal_intervals",
    "class_a_events",
    "class_b_events",
    "non_bridge_events",
    "bridge_unresolved_events",
    "mean_signal_duration",
    "mean_rebridge_delay",
    "mean_bridge_path_jaccard",
    "mean_structural_displacement",
    "original_bridge_any_return_rate",
    "payload_zero_cases",
    "ledger_exact_cases",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify no-stored-phase component signals as A/B/non-bridge/no-signal."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--sample-indices", nargs="+", type=int, default=list(DEFAULT_SAMPLES))
    parser.add_argument("--variants", nargs="+", default=list(DEFAULT_VARIANTS))
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--horizon", type=int, default=600)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--coord-limit", type=int, default=32)
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


def component_snapshot(active: np.ndarray, wrap: bool) -> tuple[np.ndarray, dict[int, int], int, int]:
    labels, sizes, count, largest = component_labels(active, bool(wrap), "cube26")
    return labels, sizes, int(count), int(largest)


def snapshot_stats(world: World) -> dict[str, Any]:
    labels, _, count, largest = component_snapshot(world.active, bool(world.wrap))
    return {
        "labels": labels,
        "active": int(np.count_nonzero(world.active)),
        "component_count": count,
        "largest": largest,
        "payload_nonzero": int(np.count_nonzero(world.active & (world.P != 0))),
        "ledger_error": ledger_error(world),
    }


def neighbor_label_set(
    labels: np.ndarray,
    coord: tuple[int, int, int],
    wrap: bool,
) -> set[int]:
    size = labels.shape[0]
    x, y, z = coord
    labels_seen: set[int] = set()
    for raw_delta in candidate_neighbor_steps("cube26"):
        dx, dy, dz = (int(value) for value in raw_delta)
        nx, ny, nz = x + dx, y + dy, z + dz
        if wrap:
            nx %= size
            ny %= size
            nz %= size
        elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
            continue
        label = int(labels[nx, ny, nz])
        if label >= 0:
            labels_seen.add(label)
    return labels_seen


def analyze_transition(
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
        _, _, before_without_count, _ = component_snapshot(before_without, wrap)
        if before_without_count > int(before_stats["component_count"]):
            lost_articulation_before.add(coord)

        after_with = after_active.copy()
        after_with[coord] = True
        _, _, after_with_count, _ = component_snapshot(after_with, wrap)
        if after_with_count < int(after_stats["component_count"]):
            lost_bridge_if_restored.add(coord)

    gained_bridge_if_removed: set[tuple[int, int, int]] = set()
    for coord in gained:
        after_without = after_active.copy()
        after_without[coord] = False
        _, _, after_without_count, _ = component_snapshot(after_without, wrap)
        if after_without_count > int(after_stats["component_count"]):
            gained_bridge_if_removed.add(coord)

    return {
        "gained": gained,
        "lost": lost,
        "lost_articulation_before": lost_articulation_before,
        "lost_bridge_if_restored": lost_bridge_if_restored,
        "gained_bridge_if_removed": gained_bridge_if_removed,
        "component_delta": int(after_stats["component_count"]) - int(before_stats["component_count"]),
    }


def rebridge_path_cells(
    signal_before_stats: dict[str, Any],
    rebridge_after_active: np.ndarray,
    rebridge_transition: dict[str, Any],
    wrap: bool,
) -> set[tuple[int, int, int]]:
    path_cells = set(rebridge_transition["gained_bridge_if_removed"])
    labels_before = signal_before_stats["labels"]
    for coord in rebridge_transition["gained"]:
        if len(neighbor_label_set(labels_before, coord, wrap)) >= 2:
            path_cells.add(coord)
    if not path_cells and int(rebridge_transition["component_delta"]) < 0:
        path_cells.update(rebridge_transition["gained"])
    return {coord for coord in path_cells if bool(rebridge_after_active[coord])}


def jaccard(left: set[tuple[int, int, int]], right: set[tuple[int, int, int]]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return float(len(left & right) / len(union))


def classify_signal(
    args: argparse.Namespace,
    signal_open: dict[str, Any],
    end_stats: dict[str, Any],
    end_offset: int,
    rebridge_offset: int | str,
    rebridge_active: np.ndarray,
    rebridge_transition: dict[str, Any] | None,
    wrap: bool,
) -> dict[str, Any]:
    start_transition = signal_open.get("start_transition")
    start_stats = signal_open["start_stats"]
    start_offset = int(signal_open["start_offset"])
    start_bridge_cells: set[tuple[int, int, int]] = set()
    start_articulation_cells: set[tuple[int, int, int]] = set()
    if start_transition is not None:
        start_bridge_cells = set(start_transition["lost_bridge_if_restored"])
        start_articulation_cells = set(start_transition["lost_articulation_before"])

    rebridged = rebridge_offset != ""
    returned_cells = {coord for coord in start_bridge_cells if bool(rebridge_active[coord])}
    post_path_cells: set[tuple[int, int, int]] = set()
    if rebridged and rebridge_transition is not None:
        post_path_cells = rebridge_path_cells(
            signal_open["previous_signal_stats"],
            rebridge_active,
            rebridge_transition,
            wrap,
        )
    bridge_j = jaccard(start_bridge_cells, post_path_cells) if start_bridge_cells else 0.0
    same_bridge_restoration = (
        rebridged
        and bool(start_bridge_cells)
        and start_bridge_cells == returned_cells
    )

    if not start_bridge_cells:
        event_class = "non_bridge"
    elif not rebridged:
        event_class = "bridge_unresolved"
    elif len(start_bridge_cells) == 1 and same_bridge_restoration:
        event_class = "class_a"
    else:
        event_class = "class_b"

    return {
        "start_offset": start_offset,
        "end_offset": int(end_offset),
        "duration": int(end_offset) - start_offset + 1,
        "rebridged": csv_bool(rebridged),
        "rebridge_offset": rebridge_offset,
        "rebridge_delay": "" if not rebridged else int(rebridge_offset) - start_offset,
        "event_class": event_class,
        "start_component_count": int(start_stats["component_count"]),
        "end_component_count": int(end_stats["component_count"]),
        "start_active": int(start_stats["active"]),
        "end_active": int(end_stats["active"]),
        "start_largest": int(start_stats["largest"]),
        "end_largest": int(end_stats["largest"]),
        "start_bridge_loss_count": len(start_bridge_cells),
        "start_articulation_before_loss_count": len(start_articulation_cells),
        "start_lost_bridge_coords": coords_text(start_bridge_cells, int(args.coord_limit)),
        "start_lost_articulation_coords": coords_text(start_articulation_cells, int(args.coord_limit)),
        "original_bridge_any_returned": csv_bool(bool(returned_cells)),
        "original_bridge_all_returned": csv_bool(
            bool(start_bridge_cells) and returned_cells == start_bridge_cells
        ),
        "post_rebridge_bridge_path_coords": coords_text(post_path_cells, int(args.coord_limit)),
        "bridge_path_jaccard": bridge_j,
        "structural_displacement": float(1.0 - bridge_j),
        "same_bridge_restoration": csv_bool(same_bridge_restoration),
    }


def run_to_checkpoint(cfg: dict[str, Any], variant: str, checkpoint_tick: int) -> World:
    with phase_source_patch(variant):
        world = iota_rig.init_world(cfg)
        clamp_stored_phase(world, variant)
        for _ in range(int(checkpoint_tick)):
            iota_rig.step(world, cfg)
            clamp_stored_phase(world, variant)
        return clone_world(world, 0)


def run_continuation_case(
    args: argparse.Namespace,
    cfg: dict[str, Any],
    seed: int,
    variant: str,
    checkpoint_world: World,
    sample_index: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    continuation_seed = deterministic_continuation_seed(
        int(args.rng_seed_base),
        int(args.checkpoint_tick),
        int(sample_index),
    )
    signal_rows: list[dict[str, Any]] = []
    payload_zero_all = True
    ledger_exact_all = True
    max_abs_ledger_error = 0.0
    previous_active: np.ndarray | None = None
    previous_stats: dict[str, Any] | None = None
    checkpoint_stats: dict[str, Any] | None = None
    final_stats: dict[str, Any] | None = None
    signal_open: dict[str, Any] | None = None

    with phase_source_patch(variant):
        world = clone_world(checkpoint_world, continuation_seed)
        clamp_stored_phase(world, variant)
        wrap = bool(world.wrap)
        for offset in range(0, int(args.horizon) + 1):
            stats = snapshot_stats(world)
            if offset == 0:
                checkpoint_stats = stats
            payload_zero_all = payload_zero_all and int(stats["payload_nonzero"]) == 0
            ledger_exact_all = ledger_exact_all and abs(float(stats["ledger_error"])) == 0.0
            max_abs_ledger_error = max(max_abs_ledger_error, abs(float(stats["ledger_error"])))

            transition = None
            if previous_active is not None and previous_stats is not None:
                raw_delta = int(stats["component_count"]) - int(previous_stats["component_count"])
                if raw_delta != 0:
                    transition = analyze_transition(
                        previous_active,
                        world.active,
                        previous_stats,
                        stats,
                        wrap,
                    )

            baseline_count = int(checkpoint_stats["component_count"])
            in_signal = int(stats["component_count"]) != baseline_count
            if in_signal:
                if signal_open is None:
                    signal_open = {
                        "start_offset": offset,
                        "start_stats": stats.copy(),
                        "start_transition": transition,
                        "previous_signal_stats": stats.copy(),
                    }
                else:
                    signal_open["previous_signal_stats"] = stats.copy()
            elif signal_open is not None:
                signal_rows.append(
                    {
                        "init_seed": int(seed),
                        "variant": variant,
                        "sample_index": int(sample_index),
                        "checkpoint_tick": int(args.checkpoint_tick),
                        "horizon": int(args.horizon),
                        "continuation_seed": continuation_seed,
                        **classify_signal(
                            args,
                            signal_open,
                            previous_stats if previous_stats is not None else stats,
                            offset - 1,
                            offset,
                            world.active,
                            transition,
                            wrap,
                        ),
                    }
                )
                signal_open = None

            previous_active = world.active.copy()
            previous_stats = stats
            final_stats = stats

            if offset >= int(args.horizon):
                break
            iota_rig.step(world, cfg)
            clamp_stored_phase(world, variant)

    if signal_open is not None and previous_stats is not None and final_stats is not None:
        signal_rows.append(
            {
                "init_seed": int(seed),
                "variant": variant,
                "sample_index": int(sample_index),
                "checkpoint_tick": int(args.checkpoint_tick),
                "horizon": int(args.horizon),
                "continuation_seed": continuation_seed,
                **classify_signal(
                    args,
                    signal_open,
                    final_stats,
                    int(args.horizon),
                    "",
                    previous_active if previous_active is not None else checkpoint_world.active,
                    None,
                    bool(checkpoint_world.wrap),
                ),
            }
        )

    if checkpoint_stats is None or final_stats is None:
        raise RuntimeError("missing stats")
    class_counts = {
        "class_a": sum(1 for row in signal_rows if row["event_class"] == "class_a"),
        "class_b": sum(1 for row in signal_rows if row["event_class"] == "class_b"),
        "non_bridge": sum(1 for row in signal_rows if row["event_class"] == "non_bridge"),
        "bridge_unresolved": sum(1 for row in signal_rows if row["event_class"] == "bridge_unresolved"),
    }
    if not signal_rows:
        case_class = "no_signal"
    elif class_counts["class_a"] > 0:
        case_class = "class_a"
    elif class_counts["class_b"] > 0:
        case_class = "class_b"
    elif class_counts["non_bridge"] > 0:
        case_class = "non_bridge"
    else:
        case_class = "bridge_unresolved"

    case_row = {
        "init_seed": int(seed),
        "variant": variant,
        "sample_index": int(sample_index),
        "checkpoint_tick": int(args.checkpoint_tick),
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
        "signal_interval_count": len(signal_rows),
        "case_class": case_class,
        "class_a_event_count": class_counts["class_a"],
        "class_b_event_count": class_counts["class_b"],
        "non_bridge_event_count": class_counts["non_bridge"],
        "bridge_unresolved_event_count": class_counts["bridge_unresolved"],
        "first_signal_start": "" if not signal_rows else int(signal_rows[0]["start_offset"]),
        "first_signal_class": "" if not signal_rows else str(signal_rows[0]["event_class"]),
    }
    return case_row, signal_rows


def numeric_mean(values: list[Any]) -> str:
    numeric = [float(value) for value in values if value != ""]
    return "" if not numeric else str(float(mean(numeric)))


def aggregate_rows(case_rows: list[dict[str, Any]], signal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    variants = sorted({str(row["variant"]) for row in case_rows})
    for variant in variants:
        cases = [row for row in case_rows if str(row["variant"]) == variant]
        signals = [row for row in signal_rows if str(row["variant"]) == variant]
        bridge_signals = [row for row in signals if int(row["start_bridge_loss_count"]) > 0]
        rows.append(
            {
                "variant": variant,
                "cases": len(cases),
                "no_signal_cases": sum(1 for row in cases if row["case_class"] == "no_signal"),
                "class_a_cases": sum(1 for row in cases if row["case_class"] == "class_a"),
                "class_b_cases": sum(1 for row in cases if row["case_class"] == "class_b"),
                "non_bridge_signal_cases": sum(1 for row in cases if row["case_class"] == "non_bridge"),
                "bridge_unresolved_cases": sum(1 for row in cases if row["case_class"] == "bridge_unresolved"),
                "signal_intervals": len(signals),
                "class_a_events": sum(1 for row in signals if row["event_class"] == "class_a"),
                "class_b_events": sum(1 for row in signals if row["event_class"] == "class_b"),
                "non_bridge_events": sum(1 for row in signals if row["event_class"] == "non_bridge"),
                "bridge_unresolved_events": sum(1 for row in signals if row["event_class"] == "bridge_unresolved"),
                "mean_signal_duration": numeric_mean([row["duration"] for row in signals]),
                "mean_rebridge_delay": numeric_mean([row["rebridge_delay"] for row in signals]),
                "mean_bridge_path_jaccard": numeric_mean([row["bridge_path_jaccard"] for row in bridge_signals]),
                "mean_structural_displacement": numeric_mean(
                    [row["structural_displacement"] for row in bridge_signals]
                ),
                "original_bridge_any_return_rate": numeric_mean(
                    [row["original_bridge_any_returned"] for row in bridge_signals]
                ),
                "payload_zero_cases": sum(int(row["payload_zero_all_offsets"]) for row in cases),
                "ledger_exact_cases": sum(int(row["ledger_exact_all_offsets"]) for row in cases),
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    output_prefix = Path(args.output_prefix)
    case_rows: list[dict[str, Any]] = []
    signal_rows: list[dict[str, Any]] = []

    checkpoint_cache: dict[tuple[int, str], World] = {}
    config_cache: dict[int, dict[str, Any]] = {}
    for seed in args.seeds:
        config_cache[int(seed)] = load_config(discover_config(args.config_dir, int(seed)))
        for variant in args.variants:
            print(f"checkpoint seed={seed} variant={variant}", flush=True)
            checkpoint_cache[(int(seed), str(variant))] = run_to_checkpoint(
                config_cache[int(seed)],
                str(variant),
                int(args.checkpoint_tick),
            )

    for seed in args.seeds:
        for variant in args.variants:
            checkpoint_world = checkpoint_cache[(int(seed), str(variant))]
            for sample_index in args.sample_indices:
                case_row, case_signals = run_continuation_case(
                    args,
                    config_cache[int(seed)],
                    int(seed),
                    str(variant),
                    checkpoint_world,
                    int(sample_index),
                )
                case_rows.append(case_row)
                signal_rows.extend(case_signals)
                print(
                    f"case seed={seed} variant={variant} sample={sample_index} "
                    f"class={case_row['case_class']} signals={case_row['signal_interval_count']}",
                    flush=True,
                )

    aggregate = aggregate_rows(case_rows, signal_rows)
    case_path = output_prefix.with_name(output_prefix.name + "_cases.csv")
    signal_path = output_prefix.with_name(output_prefix.name + "_signals.csv")
    aggregate_path = output_prefix.with_name(output_prefix.name + "_aggregate.csv")
    write_csv(case_path, CASE_FIELDNAMES, case_rows)
    write_csv(signal_path, SIGNAL_FIELDNAMES, signal_rows)
    write_csv(aggregate_path, AGGREGATE_FIELDNAMES, aggregate)
    json_path = output_prefix.with_name(output_prefix.name + "_summary.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "case_csv": str(case_path),
                "signal_csv": str(signal_path),
                "aggregate_csv": str(aggregate_path),
                "aggregate": aggregate,
            },
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")


if __name__ == "__main__":
    main()
