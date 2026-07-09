from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np

from continuation import clone_world, deterministic_continuation_seed, load_checkpoint
from front_turnover_diagnostic import accumulate_counts, take_snapshot
from iota_rig import load_config, step
from metrics import collect_metrics
from rotation_aware_openness import build_context, changed_interface_transition_counter
from rotation_branch_lineage import (
    cluster_vectors,
    counter_to_vector,
    js_distance,
    mean_for,
    metric_value,
    phase_rows,
    phase_summary,
    top_transitions,
)
from rotational_recursion_diagnostic import metric_from_world, row_for_snapshots


PHASE_BASE_FIELDNAMES = [
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "phase",
    "phase_start_offset",
    "phase_end_offset",
    "family",
    "bounded_nonrunaway",
    "ledger_exact",
    "early_stop_reason",
    "transition_count",
    "transition_families",
    "top_transitions",
    "rotation_events_per_tick",
    "angular_momentum_updates_per_tick",
    "angular_momentum_biased_rotation_events_per_tick",
    "angular_momentum_mean_abs_active",
    "angular_momentum_max_abs",
    "residual_participations_per_tick",
    "deactivation_events_per_tick",
    "persistent_interface_v_changed_fraction",
    "persistent_interface_changed_transition_entropy",
    "persistent_interface_candidate_turnover",
    "active_interface_turnover_fraction",
    "active_interface_candidate_target_turnover",
    "active_delta",
    "depleted_delta",
    "component_count_delta",
    "largest_component_delta",
    "component_entropy_delta",
    "final_active_iotas",
    "final_depleted_cells",
]

FAMILY_FIELDNAMES = [
    "checkpoint_tick",
    "phase",
    "family",
    "size",
    "samples",
    "mean_rotation_events_per_tick",
    "mean_angular_momentum_updates_per_tick",
    "mean_angular_momentum_biased_rotation_events_per_tick",
    "mean_angular_momentum_mean_abs_active",
    "mean_angular_momentum_max_abs",
    "mean_persistent_interface_v_changed_fraction",
    "mean_persistent_interface_changed_transition_entropy",
    "mean_persistent_interface_candidate_turnover",
    "mean_active_interface_turnover_fraction",
    "mean_active_interface_candidate_target_turnover",
    "mean_active_delta",
    "mean_depleted_delta",
    "mean_component_count_delta",
    "mean_largest_component_delta",
    "mean_component_entropy_delta",
    "mean_final_active_iotas",
    "mean_final_depleted_cells",
    "transition_count",
    "transition_families",
    "top_transitions",
]

SUMMARY_BASE_FIELDNAMES = [
    "checkpoint_tick",
    "samples",
    "bounded_nonrunaway_count",
    "ledger_exact_count",
    "runaway_count",
    "phase_count",
    "combined_family_count",
    "full_path_table",
    "stable_full_path_count",
    "stable_full_path_fraction",
    "phase2_persists_to_end_count",
    "phase2_persists_to_end_fraction",
    "mean_adjacent_phase_distance",
    "mean_within_family_distance",
    "mean_between_family_distance",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Track whether directional transition families persist across multiple phases."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint-state-dir", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--checkpoint-ticks", type=int, nargs="+", required=True)
    parser.add_argument("--horizon", type=int, default=1024)
    parser.add_argument("--phase-length", type=int, default=256)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--sample-every", type=int, default=16)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--connectivity", choices=["face6", "face18", "cube26"], default="cube26")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--stop-active-iotas", type=int, default=0)
    parser.add_argument("--cluster-distance-threshold", type=float, default=0.55)
    parser.add_argument("--top-transitions", type=int, default=8)
    return parser.parse_args()


def dynamic_lineage_fieldnames(phase_count: int) -> list[str]:
    fields = [
        "checkpoint_tick",
        "sample_index",
        "continuation_seed",
        "bounded_nonrunaway",
        "ledger_exact",
        "early_stop_reason",
        "family_path",
        "unique_family_count",
        "family_switch_count",
        "phase2_persists_to_end",
        "adjacent_phase_distances",
        "mean_adjacent_phase_distance",
    ]
    fields.extend(f"phase{phase}_family" for phase in range(1, phase_count + 1))
    fields.extend(f"phase{phase}_transition_count" for phase in range(1, phase_count + 1))
    fields.extend(f"phase{phase}_rotation_events_per_tick" for phase in range(1, phase_count + 1))
    fields.extend(f"phase{phase}_angular_momentum_updates_per_tick" for phase in range(1, phase_count + 1))
    fields.extend(
        f"phase{phase}_angular_momentum_biased_rotation_events_per_tick"
        for phase in range(1, phase_count + 1)
    )
    fields.extend(f"phase{phase}_angular_momentum_mean_abs_active" for phase in range(1, phase_count + 1))
    fields.extend(f"phase{phase}_persistent_interface_v_changed_fraction" for phase in range(1, phase_count + 1))
    fields.extend(f"phase{phase}_transition_entropy" for phase in range(1, phase_count + 1))
    fields.extend(f"phase{phase}_candidate_turnover" for phase in range(1, phase_count + 1))
    fields.extend(f"phase{phase}_active_interface_turnover" for phase in range(1, phase_count + 1))
    fields.extend(f"phase{phase}_component_count_delta" for phase in range(1, phase_count + 1))
    fields.extend(f"phase{phase}_largest_component_delta" for phase in range(1, phase_count + 1))
    return fields


def dynamic_summary_fieldnames(phase_count: int) -> list[str]:
    fields = list(SUMMARY_BASE_FIELDNAMES)
    for phase in range(1, phase_count + 1):
        fields.extend(
            [
                f"phase{phase}_family_count",
                f"phase{phase}_family_table",
                f"phase{phase}_mean_rotation_events_per_tick",
                f"phase{phase}_mean_angular_momentum_updates_per_tick",
                f"phase{phase}_mean_angular_momentum_biased_rotation_events_per_tick",
                f"phase{phase}_mean_angular_momentum_mean_abs_active",
                f"phase{phase}_mean_persistent_interface_v_changed_fraction",
                f"phase{phase}_mean_transition_entropy",
                f"phase{phase}_mean_candidate_turnover",
                f"phase{phase}_mean_active_interface_turnover",
                f"phase{phase}_mean_active_interface_candidate_target_turnover",
                f"phase{phase}_mean_component_count_delta",
                f"phase{phase}_mean_largest_component_delta",
            ]
        )
    return fields


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def counts_text(counts: Counter[str] | Counter[int]) -> str:
    return ";".join(f"{key}:{counts[key]}" for key in sorted(counts))


def run_phase_task(task: dict[str, Any]) -> dict[str, Any]:
    cfg = load_config(task["config"])
    checkpoint_tick = int(task["checkpoint_tick"])
    checkpoint_path = Path(task["checkpoint_state_dir"]) / f"checkpoint_tick_{checkpoint_tick:06d}.npz"
    checkpoint = load_checkpoint(checkpoint_path)
    world = clone_world(checkpoint, int(task["continuation_seed"]))
    context = build_context(cfg, world)
    connectivity = str(task["connectivity"])
    phase_length = int(task["phase_length"])
    horizon = int(task["horizon"])
    phase_count = horizon // phase_length
    sample_every = max(1, int(task["sample_every"]))
    top_limit = int(task["top_transitions"])

    previous_snapshot = take_snapshot(world, checkpoint_tick, connectivity)
    pending_extras: dict[str, float] = {}
    rows: list[dict[str, Any]] = []
    counters_by_phase = [Counter() for _ in range(phase_count)]
    boundary_metrics = {
        0: collect_metrics(world, checkpoint_tick),
    }
    early_stop_reason = ""
    final_offset = 0

    for offset in range(1, horizon + 1):
        extras = step(world, cfg)
        accumulate_counts(pending_extras, extras)
        final_offset = offset
        active_count = int(world.active.sum())
        if int(task["stop_active_iotas"]) > 0 and active_count >= int(task["stop_active_iotas"]):
            early_stop_reason = f"active_iotas >= {task['stop_active_iotas']}"
        should_sample = (
            offset % sample_every == 0
            or offset % phase_length == 0
            or bool(early_stop_reason)
        )
        if should_sample:
            tick = checkpoint_tick + offset
            current_snapshot = take_snapshot(world, tick, connectivity)
            metric = metric_from_world(world, pending_extras)
            row = row_for_snapshots(previous_snapshot, current_snapshot, context, metric, connectivity)
            rows.append(row)
            phase_index = min((offset - 1) // phase_length, phase_count - 1)
            counters_by_phase[phase_index].update(
                changed_interface_transition_counter(previous_snapshot, current_snapshot)
            )
            previous_snapshot = current_snapshot
            pending_extras = {}
        if offset % phase_length == 0 or early_stop_reason:
            boundary_metrics[offset] = collect_metrics(world, checkpoint_tick + offset)
        if early_stop_reason:
            break

    final_metric = collect_metrics(world, checkpoint_tick + final_offset)
    for phase in range(1, phase_count + 1):
        boundary = phase * phase_length
        if boundary not in boundary_metrics:
            boundary_metrics[boundary] = final_metric

    phase_summaries: list[dict[str, Any]] = []
    vector_count = len(world.vectors)
    for phase_index in range(phase_count):
        start_offset = phase_index * phase_length
        end_offset = (phase_index + 1) * phase_length
        summary = phase_summary(
            phase_rows(rows, start_offset, end_offset, checkpoint_tick),
            counters_by_phase[phase_index],
            boundary_metrics[start_offset],
            boundary_metrics[end_offset],
            connectivity,
            top_limit,
        )
        phase_summaries.append(summary)

    return {
        "checkpoint_tick": checkpoint_tick,
        "sample_index": int(task["sample_index"]),
        "continuation_seed": int(task["continuation_seed"]),
        "early_stop_reason": early_stop_reason,
        "bounded_nonrunaway": not bool(early_stop_reason),
        "ledger_exact": abs(float(final_metric.get("ledger_error", 0.0))) == 0.0,
        "phases": phase_summaries,
        "_phase_counters": counters_by_phase,
        "_phase_vectors": [counter_to_vector(counter, vector_count) for counter in counters_by_phase],
    }


def run_tasks(tasks: list[dict[str, Any]], workers: int) -> list[dict[str, Any]]:
    if workers <= 1:
        return [run_phase_task(task) for task in tasks]
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(run_phase_task, task) for task in tasks]
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: (int(row["checkpoint_tick"]), int(row["sample_index"])))
    return rows


def assign_families(
    rows: list[dict[str, Any]],
    phase_count: int,
    threshold: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    family_rows: list[dict[str, Any]] = []
    for checkpoint_tick in sorted({int(row["checkpoint_tick"]) for row in rows}):
        checkpoint_rows = [row for row in rows if int(row["checkpoint_tick"]) == checkpoint_tick]
        entries: list[tuple[dict[str, Any], int, np.ndarray]] = []
        entry_indices: dict[tuple[int, int], int] = {}
        for row in checkpoint_rows:
            for phase_index, vector in enumerate(row["_phase_vectors"]):
                entry_indices[(id(row), phase_index)] = len(entries)
                entries.append((row, phase_index, vector))

        labels, distances = cluster_vectors([entry[2] for entry in entries], threshold)
        for index, (row, phase_index, _) in enumerate(entries):
            row.setdefault("families", [0] * phase_count)[phase_index] = labels[index]

        for row in checkpoint_rows:
            adjacent_distances: list[float] = []
            for phase_index in range(phase_count - 1):
                first = entry_indices[(id(row), phase_index)]
                second = entry_indices[(id(row), phase_index + 1)]
                adjacent_distances.append(distances[first][second])
            row["adjacent_phase_distances"] = adjacent_distances
            row["mean_adjacent_phase_distance"] = float(np.mean(adjacent_distances)) if adjacent_distances else 0.0

        family_members: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
        family_counters: dict[tuple[int, int], Counter[tuple[int, int]]] = defaultdict(Counter)
        for row in checkpoint_rows:
            for phase_index in range(phase_count):
                family = int(row["families"][phase_index])
                key = (phase_index, family)
                family_members[key].append(row)
                family_counters[key].update(row["_phase_counters"][phase_index])

        for (phase_index, family), members in sorted(family_members.items()):
            phase_metrics = [member["phases"][phase_index] for member in members]
            counter = family_counters[(phase_index, family)]
            family_rows.append(
                {
                    "checkpoint_tick": checkpoint_tick,
                    "phase": phase_index + 1,
                    "family": family,
                    "size": len(members),
                    "samples": ";".join(str(member["sample_index"]) for member in members),
                    "mean_rotation_events_per_tick": mean_for(phase_metrics, "rotation_events_per_tick"),
                    "mean_angular_momentum_updates_per_tick": mean_for(
                        phase_metrics,
                        "angular_momentum_updates_per_tick",
                    ),
                    "mean_angular_momentum_biased_rotation_events_per_tick": mean_for(
                        phase_metrics,
                        "angular_momentum_biased_rotation_events_per_tick",
                    ),
                    "mean_angular_momentum_mean_abs_active": mean_for(
                        phase_metrics,
                        "angular_momentum_mean_abs_active",
                    ),
                    "mean_angular_momentum_max_abs": mean_for(
                        phase_metrics,
                        "angular_momentum_max_abs",
                    ),
                    "mean_persistent_interface_v_changed_fraction": mean_for(
                        phase_metrics,
                        "persistent_interface_v_changed_fraction",
                    ),
                    "mean_persistent_interface_changed_transition_entropy": mean_for(
                        phase_metrics,
                        "persistent_interface_changed_transition_entropy",
                    ),
                    "mean_persistent_interface_candidate_turnover": mean_for(
                        phase_metrics,
                        "persistent_interface_candidate_turnover",
                    ),
                    "mean_active_interface_turnover_fraction": mean_for(
                        phase_metrics,
                        "active_interface_turnover_fraction",
                    ),
                    "mean_active_interface_candidate_target_turnover": mean_for(
                        phase_metrics,
                        "active_interface_candidate_target_turnover",
                    ),
                    "mean_active_delta": mean_for(phase_metrics, "active_delta"),
                    "mean_depleted_delta": mean_for(phase_metrics, "depleted_delta"),
                    "mean_component_count_delta": mean_for(phase_metrics, "component_count_delta"),
                    "mean_largest_component_delta": mean_for(phase_metrics, "largest_component_delta"),
                    "mean_component_entropy_delta": mean_for(phase_metrics, "component_entropy_delta"),
                    "mean_final_active_iotas": mean_for(phase_metrics, "final_active_iotas"),
                    "mean_final_depleted_cells": mean_for(phase_metrics, "final_depleted_cells"),
                    "transition_count": int(sum(counter.values())),
                    "transition_families": len(counter),
                    "top_transitions": top_transitions(counter, 8),
                }
            )
    return rows, family_rows


def lineage_output_row(row: dict[str, Any], phase_count: int) -> dict[str, Any]:
    family_path = "->".join(str(int(value)) for value in row["families"])
    output = {
        "checkpoint_tick": row["checkpoint_tick"],
        "sample_index": row["sample_index"],
        "continuation_seed": row["continuation_seed"],
        "bounded_nonrunaway": row["bounded_nonrunaway"],
        "ledger_exact": row["ledger_exact"],
        "early_stop_reason": row["early_stop_reason"],
        "family_path": family_path,
        "unique_family_count": len(set(row["families"])),
        "family_switch_count": sum(
            1
            for phase_index in range(phase_count - 1)
            if int(row["families"][phase_index]) != int(row["families"][phase_index + 1])
        ),
        "phase2_persists_to_end": (
            all(int(value) == int(row["families"][1]) for value in row["families"][1:])
            if phase_count >= 2
            else True
        ),
        "adjacent_phase_distances": ";".join(f"{value:.6f}" for value in row["adjacent_phase_distances"]),
        "mean_adjacent_phase_distance": row["mean_adjacent_phase_distance"],
    }
    for phase_index in range(phase_count):
        phase = phase_index + 1
        metrics = row["phases"][phase_index]
        output[f"phase{phase}_family"] = row["families"][phase_index]
        output[f"phase{phase}_transition_count"] = metrics["transition_count"]
        output[f"phase{phase}_rotation_events_per_tick"] = metrics["rotation_events_per_tick"]
        output[f"phase{phase}_angular_momentum_updates_per_tick"] = metrics[
            "angular_momentum_updates_per_tick"
        ]
        output[f"phase{phase}_angular_momentum_biased_rotation_events_per_tick"] = metrics[
            "angular_momentum_biased_rotation_events_per_tick"
        ]
        output[f"phase{phase}_angular_momentum_mean_abs_active"] = metrics[
            "angular_momentum_mean_abs_active"
        ]
        output[f"phase{phase}_persistent_interface_v_changed_fraction"] = metrics[
            "persistent_interface_v_changed_fraction"
        ]
        output[f"phase{phase}_transition_entropy"] = metrics["persistent_interface_changed_transition_entropy"]
        output[f"phase{phase}_candidate_turnover"] = metrics["persistent_interface_candidate_turnover"]
        output[f"phase{phase}_active_interface_turnover"] = metrics["active_interface_turnover_fraction"]
        output[f"phase{phase}_component_count_delta"] = metrics["component_count_delta"]
        output[f"phase{phase}_largest_component_delta"] = metrics["largest_component_delta"]
    return output


def pairwise_distances(rows: list[dict[str, Any]], phase_count: int) -> tuple[float, float]:
    entries: list[tuple[int, np.ndarray]] = []
    for row in rows:
        for phase_index in range(phase_count):
            entries.append((int(row["families"][phase_index]), row["_phase_vectors"][phase_index]))
    within: list[float] = []
    between: list[float] = []
    for first in range(len(entries)):
        for second in range(first + 1, len(entries)):
            distance = js_distance(entries[first][1], entries[second][1])
            if entries[first][0] == entries[second][0]:
                within.append(distance)
            else:
                between.append(distance)
    return (
        float(np.mean(within)) if within else 0.0,
        float(np.mean(between)) if between else 0.0,
    )


def summarize(rows: list[dict[str, Any]], phase_count: int) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    for checkpoint_tick in sorted({int(row["checkpoint_tick"]) for row in rows}):
        checkpoint_rows = [row for row in rows if int(row["checkpoint_tick"]) == checkpoint_tick]
        family_sets = [
            Counter(int(row["families"][phase_index]) for row in checkpoint_rows)
            for phase_index in range(phase_count)
        ]
        combined_families = set().union(*(set(counter) for counter in family_sets))
        path_counts = Counter("->".join(str(value) for value in row["families"]) for row in checkpoint_rows)
        stable_full_path_count = sum(1 for row in checkpoint_rows if len(set(row["families"])) == 1)
        phase2_persists_count = sum(
            1
            for row in checkpoint_rows
            if phase_count >= 2 and all(int(value) == int(row["families"][1]) for value in row["families"][1:])
        )
        within_distance, between_distance = pairwise_distances(checkpoint_rows, phase_count)
        output = {
            "checkpoint_tick": checkpoint_tick,
            "samples": len(checkpoint_rows),
            "bounded_nonrunaway_count": sum(1 for row in checkpoint_rows if bool(row["bounded_nonrunaway"])),
            "ledger_exact_count": sum(1 for row in checkpoint_rows if bool(row["ledger_exact"])),
            "runaway_count": sum(1 for row in checkpoint_rows if str(row["early_stop_reason"])),
            "phase_count": phase_count,
            "combined_family_count": len(combined_families),
            "full_path_table": counts_text(path_counts),
            "stable_full_path_count": stable_full_path_count,
            "stable_full_path_fraction": stable_full_path_count / len(checkpoint_rows) if checkpoint_rows else 0.0,
            "phase2_persists_to_end_count": phase2_persists_count,
            "phase2_persists_to_end_fraction": (
                phase2_persists_count / len(checkpoint_rows) if checkpoint_rows else 0.0
            ),
            "mean_adjacent_phase_distance": mean_for(checkpoint_rows, "mean_adjacent_phase_distance"),
            "mean_within_family_distance": within_distance,
            "mean_between_family_distance": between_distance,
        }
        for phase_index in range(phase_count):
            phase = phase_index + 1
            phase_metrics = [row["phases"][phase_index] for row in checkpoint_rows]
            output[f"phase{phase}_family_count"] = len(family_sets[phase_index])
            output[f"phase{phase}_family_table"] = counts_text(family_sets[phase_index])
            output[f"phase{phase}_mean_rotation_events_per_tick"] = mean_for(
                phase_metrics,
                "rotation_events_per_tick",
            )
            output[f"phase{phase}_mean_angular_momentum_updates_per_tick"] = mean_for(
                phase_metrics,
                "angular_momentum_updates_per_tick",
            )
            output[f"phase{phase}_mean_angular_momentum_biased_rotation_events_per_tick"] = mean_for(
                phase_metrics,
                "angular_momentum_biased_rotation_events_per_tick",
            )
            output[f"phase{phase}_mean_angular_momentum_mean_abs_active"] = mean_for(
                phase_metrics,
                "angular_momentum_mean_abs_active",
            )
            output[f"phase{phase}_mean_persistent_interface_v_changed_fraction"] = mean_for(
                phase_metrics,
                "persistent_interface_v_changed_fraction",
            )
            output[f"phase{phase}_mean_transition_entropy"] = mean_for(
                phase_metrics,
                "persistent_interface_changed_transition_entropy",
            )
            output[f"phase{phase}_mean_candidate_turnover"] = mean_for(
                phase_metrics,
                "persistent_interface_candidate_turnover",
            )
            output[f"phase{phase}_mean_active_interface_turnover"] = mean_for(
                phase_metrics,
                "active_interface_turnover_fraction",
            )
            output[f"phase{phase}_mean_active_interface_candidate_target_turnover"] = mean_for(
                phase_metrics,
                "active_interface_candidate_target_turnover",
            )
            output[f"phase{phase}_mean_component_count_delta"] = mean_for(
                phase_metrics,
                "component_count_delta",
            )
            output[f"phase{phase}_mean_largest_component_delta"] = mean_for(
                phase_metrics,
                "largest_component_delta",
            )
        summary_rows.append(output)
    return summary_rows


def main() -> None:
    args = parse_args()
    if int(args.horizon) % int(args.phase_length) != 0:
        raise SystemExit("--horizon must be divisible by --phase-length")
    phase_count = int(args.horizon) // int(args.phase_length)
    if phase_count < 2:
        raise SystemExit("at least two phases are required")

    output_prefix = Path(args.output_prefix)
    phase_path = output_prefix.with_name(output_prefix.name + "_phases.csv")
    lineage_path = output_prefix.with_name(output_prefix.name + "_lineages.csv")
    family_path = output_prefix.with_name(output_prefix.name + "_families.csv")
    summary_path = output_prefix.with_name(output_prefix.name + "_summary.csv")
    json_path = output_prefix.with_name(output_prefix.name + "_summary.json")

    tasks: list[dict[str, Any]] = []
    for checkpoint_tick in sorted({int(value) for value in args.checkpoint_ticks}):
        for sample_index in range(int(args.samples)):
            tasks.append(
                {
                    **vars(args),
                    "checkpoint_tick": checkpoint_tick,
                    "sample_index": sample_index,
                    "continuation_seed": deterministic_continuation_seed(
                        int(args.rng_seed_base),
                        checkpoint_tick,
                        sample_index,
                    ),
                }
            )

    rows = run_tasks(tasks, max(1, int(args.workers)))
    rows, family_rows = assign_families(rows, phase_count, float(args.cluster_distance_threshold))
    phase_rows_out: list[dict[str, Any]] = []
    for row in rows:
        for phase_index, metrics in enumerate(row["phases"]):
            phase_rows_out.append(
                {
                    "checkpoint_tick": row["checkpoint_tick"],
                    "sample_index": row["sample_index"],
                    "continuation_seed": row["continuation_seed"],
                    "phase": phase_index + 1,
                    "phase_start_offset": phase_index * int(args.phase_length),
                    "phase_end_offset": (phase_index + 1) * int(args.phase_length),
                    "family": row["families"][phase_index],
                    "bounded_nonrunaway": row["bounded_nonrunaway"],
                    "ledger_exact": row["ledger_exact"],
                    "early_stop_reason": row["early_stop_reason"],
                    **metrics,
                }
            )
    lineage_rows = [lineage_output_row(row, phase_count) for row in rows]
    summary_rows = summarize(rows, phase_count)

    write_csv(phase_path, PHASE_BASE_FIELDNAMES, phase_rows_out)
    write_csv(lineage_path, dynamic_lineage_fieldnames(phase_count), lineage_rows)
    write_csv(family_path, FAMILY_FIELDNAMES, family_rows)
    write_csv(summary_path, dynamic_summary_fieldnames(phase_count), summary_rows)
    payload = {
        "config_path": args.config,
        "checkpoint_state_dir": args.checkpoint_state_dir,
        "output_prefix": output_prefix.as_posix(),
        "phase_path": phase_path.as_posix(),
        "lineage_path": lineage_path.as_posix(),
        "family_path": family_path.as_posix(),
        "summary_path": summary_path.as_posix(),
        "checkpoint_ticks": sorted({int(value) for value in args.checkpoint_ticks}),
        "samples": int(args.samples),
        "horizon": int(args.horizon),
        "phase_length": int(args.phase_length),
        "phase_count": phase_count,
        "sample_every": int(args.sample_every),
        "connectivity": args.connectivity,
        "cluster_distance_threshold": float(args.cluster_distance_threshold),
        "summary_rows": summary_rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
