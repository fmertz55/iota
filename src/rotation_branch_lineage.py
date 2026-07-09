from __future__ import annotations

import argparse
import csv
import json
import math
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
from rotational_recursion_diagnostic import metric_from_world, row_for_snapshots


LINEAGE_FIELDNAMES = [
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "early_stop_reason",
    "bounded_nonrunaway",
    "ledger_exact",
    "phase1_family",
    "phase2_family",
    "same_family",
    "phase_matrix_distance",
    "phase1_transition_count",
    "phase1_transition_families",
    "phase1_top_transitions",
    "phase1_rotation_events_per_tick",
    "phase1_angular_momentum_updates_per_tick",
    "phase1_angular_momentum_biased_rotation_events_per_tick",
    "phase1_angular_momentum_mean_abs_active",
    "phase1_angular_momentum_max_abs",
    "phase1_residual_participations_per_tick",
    "phase1_deactivation_events_per_tick",
    "phase1_persistent_interface_v_changed_fraction",
    "phase1_persistent_interface_changed_transition_entropy",
    "phase1_persistent_interface_candidate_turnover",
    "phase1_active_interface_turnover_fraction",
    "phase1_active_interface_candidate_target_turnover",
    "phase1_active_delta",
    "phase1_depleted_delta",
    "phase1_component_count_delta",
    "phase1_largest_component_delta",
    "phase1_component_entropy_delta",
    "phase1_final_active_iotas",
    "phase1_final_depleted_cells",
    "phase2_transition_count",
    "phase2_transition_families",
    "phase2_top_transitions",
    "phase2_rotation_events_per_tick",
    "phase2_angular_momentum_updates_per_tick",
    "phase2_angular_momentum_biased_rotation_events_per_tick",
    "phase2_angular_momentum_mean_abs_active",
    "phase2_angular_momentum_max_abs",
    "phase2_residual_participations_per_tick",
    "phase2_deactivation_events_per_tick",
    "phase2_persistent_interface_v_changed_fraction",
    "phase2_persistent_interface_changed_transition_entropy",
    "phase2_persistent_interface_candidate_turnover",
    "phase2_active_interface_turnover_fraction",
    "phase2_active_interface_candidate_target_turnover",
    "phase2_active_delta",
    "phase2_depleted_delta",
    "phase2_component_count_delta",
    "phase2_largest_component_delta",
    "phase2_component_entropy_delta",
    "phase2_final_active_iotas",
    "phase2_final_depleted_cells",
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

SUMMARY_FIELDNAMES = [
    "checkpoint_tick",
    "samples",
    "bounded_nonrunaway_count",
    "ledger_exact_count",
    "runaway_count",
    "combined_family_count",
    "phase1_family_count",
    "phase2_family_count",
    "same_family_count",
    "same_family_fraction",
    "lineage_table",
    "mean_phase_matrix_distance",
    "mean_within_family_distance",
    "mean_between_family_distance",
    "phase1_mean_rotation_events_per_tick",
    "phase2_mean_rotation_events_per_tick",
    "phase1_mean_angular_momentum_updates_per_tick",
    "phase2_mean_angular_momentum_updates_per_tick",
    "phase1_mean_angular_momentum_biased_rotation_events_per_tick",
    "phase2_mean_angular_momentum_biased_rotation_events_per_tick",
    "phase1_mean_angular_momentum_mean_abs_active",
    "phase2_mean_angular_momentum_mean_abs_active",
    "phase1_mean_persistent_interface_v_changed_fraction",
    "phase2_mean_persistent_interface_v_changed_fraction",
    "phase1_mean_transition_entropy",
    "phase2_mean_transition_entropy",
    "phase1_mean_candidate_turnover",
    "phase2_mean_candidate_turnover",
    "phase1_mean_active_interface_turnover",
    "phase2_mean_active_interface_turnover",
    "phase1_mean_active_interface_candidate_target_turnover",
    "phase2_mean_active_interface_candidate_target_turnover",
    "phase1_mean_component_count_delta",
    "phase2_mean_component_count_delta",
    "phase1_mean_largest_component_delta",
    "phase2_mean_largest_component_delta",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cluster rotation-transition matrices into branch lineages."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint-state-dir", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--checkpoint-ticks", type=int, nargs="+", required=True)
    parser.add_argument("--horizon", type=int, default=512)
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


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def mean_for(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row.get(key, 0.0) or 0.0) for row in rows]
    return float(np.mean(values)) if values else 0.0


def metric_value(metric: dict[str, Any], key: str, connectivity: str) -> float:
    if connectivity == "face6":
        return float(metric[key])
    return float(metric[f"{key}_{connectivity}"])


def phase_rows(rows: list[dict[str, Any]], start_offset: int, end_offset: int, checkpoint_tick: int) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if start_offset < int(row["tick"]) - checkpoint_tick <= end_offset
    ]


def counter_to_vector(counter: Counter[tuple[int, int]], vector_count: int) -> np.ndarray:
    output = np.zeros(vector_count * vector_count, dtype=np.float64)
    total = sum(counter.values())
    if total <= 0:
        return output
    for (before, after), count in counter.items():
        index = (int(before) % vector_count) * vector_count + (int(after) % vector_count)
        output[index] += float(count)
    return output / float(total)


def js_distance(first: np.ndarray, second: np.ndarray) -> float:
    first_total = float(np.sum(first))
    second_total = float(np.sum(second))
    if first_total <= 0.0 and second_total <= 0.0:
        return 0.0
    if first_total <= 0.0 or second_total <= 0.0:
        return 1.0
    first_prob = first / first_total
    second_prob = second / second_total
    midpoint = 0.5 * (first_prob + second_prob)
    mask_first = first_prob > 0
    mask_second = second_prob > 0
    divergence = 0.5 * float(np.sum(first_prob[mask_first] * np.log(first_prob[mask_first] / midpoint[mask_first])))
    divergence += 0.5 * float(
        np.sum(second_prob[mask_second] * np.log(second_prob[mask_second] / midpoint[mask_second]))
    )
    return float(math.sqrt(max(0.0, divergence / math.log(2.0))))


def cluster_vectors(vectors: list[np.ndarray], threshold: float) -> tuple[list[int], list[list[float]]]:
    count = len(vectors)
    parent = list(range(count))
    distances = [[0.0 for _ in range(count)] for _ in range(count)]

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        first_root = find(first)
        second_root = find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    for first in range(count):
        for second in range(first + 1, count):
            distance = js_distance(vectors[first], vectors[second])
            distances[first][second] = distance
            distances[second][first] = distance
            if distance <= threshold:
                union(first, second)

    root_to_family: dict[int, int] = {}
    labels: list[int] = []
    for index in range(count):
        root = find(index)
        if root not in root_to_family:
            root_to_family[root] = len(root_to_family)
        labels.append(root_to_family[root])
    return labels, distances


def top_transitions(counter: Counter[tuple[int, int]], limit: int) -> str:
    return ";".join(
        f"{before}>{after}:{count}"
        for (before, after), count in counter.most_common(limit)
    )


def phase_summary(
    rows: list[dict[str, Any]],
    counter: Counter[tuple[int, int]],
    start_metric: dict[str, Any],
    end_metric: dict[str, Any],
    connectivity: str,
    top_limit: int,
) -> dict[str, Any]:
    return {
        "transition_count": int(sum(counter.values())),
        "transition_families": int(len(counter)),
        "top_transitions": top_transitions(counter, top_limit),
        "rotation_events_per_tick": mean_for(rows, "rotation_events_per_tick"),
        "angular_momentum_updates_per_tick": mean_for(rows, "angular_momentum_updates_per_tick"),
        "angular_momentum_biased_rotation_events_per_tick": mean_for(
            rows,
            "angular_momentum_biased_rotation_events_per_tick",
        ),
        "angular_momentum_mean_abs_active": mean_for(rows, "angular_momentum_mean_abs_active"),
        "angular_momentum_max_abs": mean_for(rows, "angular_momentum_max_abs"),
        "residual_participations_per_tick": mean_for(rows, "residual_participations_per_tick"),
        "deactivation_events_per_tick": mean_for(rows, "deactivation_events_per_tick"),
        "persistent_interface_v_changed_fraction": mean_for(rows, "persistent_interface_v_changed_fraction"),
        "persistent_interface_changed_transition_entropy": mean_for(
            rows,
            "persistent_interface_changed_transition_entropy",
        ),
        "persistent_interface_candidate_turnover": mean_for(
            rows,
            "persistent_interface_candidate_turnover_mean",
        ),
        "active_interface_turnover_fraction": mean_for(rows, "active_interface_turnover_fraction"),
        "active_interface_candidate_target_turnover": mean_for(
            rows,
            "active_interface_candidate_target_turnover",
        ),
        "active_delta": float(end_metric["active_iotas"]) - float(start_metric["active_iotas"]),
        "depleted_delta": float(end_metric.get("depleted_cells", 0.0)) - float(start_metric.get("depleted_cells", 0.0)),
        "component_count_delta": (
            metric_value(end_metric, "coherence_count", connectivity)
            - metric_value(start_metric, "coherence_count", connectivity)
        ),
        "largest_component_delta": (
            metric_value(end_metric, "largest_coherence", connectivity)
            - metric_value(start_metric, "largest_coherence", connectivity)
        ),
        "component_entropy_delta": (
            metric_value(end_metric, "component_size_entropy", connectivity)
            - metric_value(start_metric, "component_size_entropy", connectivity)
        ),
        "final_active_iotas": float(end_metric["active_iotas"]),
        "final_depleted_cells": float(end_metric.get("depleted_cells", 0.0)),
    }


def run_lineage_task(task: dict[str, Any]) -> dict[str, Any]:
    cfg = load_config(task["config"])
    checkpoint_tick = int(task["checkpoint_tick"])
    checkpoint_path = Path(task["checkpoint_state_dir"]) / f"checkpoint_tick_{checkpoint_tick:06d}.npz"
    checkpoint = load_checkpoint(checkpoint_path)
    world = clone_world(checkpoint, int(task["continuation_seed"]))
    context = build_context(cfg, world)
    connectivity = str(task["connectivity"])
    phase_length = int(task["phase_length"])
    horizon = int(task["horizon"])
    sample_every = max(1, int(task["sample_every"]))
    top_limit = int(task["top_transitions"])

    previous_snapshot = take_snapshot(world, checkpoint_tick, connectivity)
    pending_extras: dict[str, float] = {}
    rows: list[dict[str, Any]] = []
    counters_by_phase = {
        "phase1": Counter(),
        "phase2": Counter(),
    }
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
            or offset in {phase_length, horizon}
            or bool(early_stop_reason)
        )
        if should_sample:
            tick = checkpoint_tick + offset
            current_snapshot = take_snapshot(world, tick, connectivity)
            metric = metric_from_world(world, pending_extras)
            row = row_for_snapshots(previous_snapshot, current_snapshot, context, metric, connectivity)
            rows.append(row)
            counter = changed_interface_transition_counter(previous_snapshot, current_snapshot)
            if offset <= phase_length:
                counters_by_phase["phase1"].update(counter)
            else:
                counters_by_phase["phase2"].update(counter)
            previous_snapshot = current_snapshot
            pending_extras = {}
        if offset in {phase_length, horizon} or early_stop_reason:
            boundary_metrics[offset] = collect_metrics(world, checkpoint_tick + offset)
        if early_stop_reason:
            break

    if phase_length not in boundary_metrics:
        boundary_metrics[phase_length] = collect_metrics(world, checkpoint_tick + final_offset)
    if horizon not in boundary_metrics:
        boundary_metrics[horizon] = collect_metrics(world, checkpoint_tick + final_offset)

    first_rows = phase_rows(rows, 0, phase_length, checkpoint_tick)
    second_rows = phase_rows(rows, phase_length, horizon, checkpoint_tick)
    phase1 = phase_summary(
        first_rows,
        counters_by_phase["phase1"],
        boundary_metrics[0],
        boundary_metrics[phase_length],
        connectivity,
        top_limit,
    )
    phase2 = phase_summary(
        second_rows,
        counters_by_phase["phase2"],
        boundary_metrics[phase_length],
        boundary_metrics[horizon],
        connectivity,
        top_limit,
    )
    vector_count = len(world.vectors)
    return {
        "checkpoint_tick": checkpoint_tick,
        "sample_index": int(task["sample_index"]),
        "continuation_seed": int(task["continuation_seed"]),
        "early_stop_reason": early_stop_reason,
        "bounded_nonrunaway": not bool(early_stop_reason),
        "ledger_exact": abs(float(boundary_metrics[horizon].get("ledger_error", 0.0))) == 0.0,
        "phase1": phase1,
        "phase2": phase2,
        "_phase1_counter": counters_by_phase["phase1"],
        "_phase2_counter": counters_by_phase["phase2"],
        "_phase1_vector": counter_to_vector(counters_by_phase["phase1"], vector_count),
        "_phase2_vector": counter_to_vector(counters_by_phase["phase2"], vector_count),
    }


def run_tasks(tasks: list[dict[str, Any]], workers: int) -> list[dict[str, Any]]:
    if workers <= 1:
        return [run_lineage_task(task) for task in tasks]
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(run_lineage_task, task) for task in tasks]
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: (int(row["checkpoint_tick"]), int(row["sample_index"])))
    return rows


def assign_families(rows: list[dict[str, Any]], threshold: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    family_rows: list[dict[str, Any]] = []
    for checkpoint_tick in sorted({int(row["checkpoint_tick"]) for row in rows}):
        checkpoint_rows = [row for row in rows if int(row["checkpoint_tick"]) == checkpoint_tick]
        entries: list[tuple[dict[str, Any], str, np.ndarray]] = []
        entry_indices: dict[tuple[int, str], int] = {}
        for row in checkpoint_rows:
            entry_indices[(id(row), "phase1")] = len(entries)
            entries.append((row, "phase1", row["_phase1_vector"]))
            entry_indices[(id(row), "phase2")] = len(entries)
            entries.append((row, "phase2", row["_phase2_vector"]))
        labels, distances = cluster_vectors([entry[2] for entry in entries], threshold)
        for index, (row, phase, _) in enumerate(entries):
            row[f"{phase}_family"] = labels[index]
        for row in checkpoint_rows:
            phase1_index = entry_indices[(id(row), "phase1")]
            phase2_index = entry_indices[(id(row), "phase2")]
            row["phase_matrix_distance"] = distances[phase1_index][phase2_index]

        family_members: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
        family_counters: dict[tuple[str, int], Counter[tuple[int, int]]] = defaultdict(Counter)
        for row in checkpoint_rows:
            for phase in ("phase1", "phase2"):
                family = int(row[f"{phase}_family"])
                key = (phase, family)
                family_members[key].append(row)
                family_counters[key].update(row[f"_{phase}_counter"])
        for (phase, family), members in sorted(family_members.items()):
            phase_metrics = [member[phase] for member in members]
            counter = family_counters[(phase, family)]
            family_rows.append(
                {
                    "checkpoint_tick": checkpoint_tick,
                    "phase": phase,
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


def lineage_output_row(row: dict[str, Any]) -> dict[str, Any]:
    output = {
        "checkpoint_tick": row["checkpoint_tick"],
        "sample_index": row["sample_index"],
        "continuation_seed": row["continuation_seed"],
        "early_stop_reason": row["early_stop_reason"],
        "bounded_nonrunaway": row["bounded_nonrunaway"],
        "ledger_exact": row["ledger_exact"],
        "phase1_family": row["phase1_family"],
        "phase2_family": row["phase2_family"],
        "same_family": int(row["phase1_family"]) == int(row["phase2_family"]),
        "phase_matrix_distance": row["phase_matrix_distance"],
    }
    for phase in ("phase1", "phase2"):
        for key, value in row[phase].items():
            output[f"{phase}_{key}"] = value
    return output


def mean_pairwise_distances(rows: list[dict[str, Any]]) -> tuple[float, float]:
    entries: list[tuple[int, np.ndarray]] = []
    for row in rows:
        entries.append((int(row["phase1_family"]), row["_phase1_vector"]))
        entries.append((int(row["phase2_family"]), row["_phase2_vector"]))
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


def summarize(rows: list[dict[str, Any]], family_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    for checkpoint_tick in sorted({int(row["checkpoint_tick"]) for row in rows}):
        checkpoint_rows = [row for row in rows if int(row["checkpoint_tick"]) == checkpoint_tick]
        phase1_families = Counter(int(row["phase1_family"]) for row in checkpoint_rows)
        phase2_families = Counter(int(row["phase2_family"]) for row in checkpoint_rows)
        combined_families = set(phase1_families) | set(phase2_families)
        lineage_counts = Counter(
            f"{int(row['phase1_family'])}->{int(row['phase2_family'])}"
            for row in checkpoint_rows
        )
        same_family_count = sum(
            1 for row in checkpoint_rows if int(row["phase1_family"]) == int(row["phase2_family"])
        )
        within_distance, between_distance = mean_pairwise_distances(checkpoint_rows)
        phase1_metrics = [row["phase1"] for row in checkpoint_rows]
        phase2_metrics = [row["phase2"] for row in checkpoint_rows]
        summary_rows.append(
            {
                "checkpoint_tick": checkpoint_tick,
                "samples": len(checkpoint_rows),
                "bounded_nonrunaway_count": sum(1 for row in checkpoint_rows if bool(row["bounded_nonrunaway"])),
                "ledger_exact_count": sum(1 for row in checkpoint_rows if bool(row["ledger_exact"])),
                "runaway_count": sum(1 for row in checkpoint_rows if str(row["early_stop_reason"])),
                "combined_family_count": len(combined_families),
                "phase1_family_count": len(phase1_families),
                "phase2_family_count": len(phase2_families),
                "same_family_count": same_family_count,
                "same_family_fraction": same_family_count / len(checkpoint_rows) if checkpoint_rows else 0.0,
                "lineage_table": ";".join(f"{key}:{lineage_counts[key]}" for key in sorted(lineage_counts)),
                "mean_phase_matrix_distance": mean_for(checkpoint_rows, "phase_matrix_distance"),
                "mean_within_family_distance": within_distance,
                "mean_between_family_distance": between_distance,
                "phase1_mean_rotation_events_per_tick": mean_for(phase1_metrics, "rotation_events_per_tick"),
                "phase2_mean_rotation_events_per_tick": mean_for(phase2_metrics, "rotation_events_per_tick"),
                "phase1_mean_angular_momentum_updates_per_tick": mean_for(
                    phase1_metrics,
                    "angular_momentum_updates_per_tick",
                ),
                "phase2_mean_angular_momentum_updates_per_tick": mean_for(
                    phase2_metrics,
                    "angular_momentum_updates_per_tick",
                ),
                "phase1_mean_angular_momentum_biased_rotation_events_per_tick": mean_for(
                    phase1_metrics,
                    "angular_momentum_biased_rotation_events_per_tick",
                ),
                "phase2_mean_angular_momentum_biased_rotation_events_per_tick": mean_for(
                    phase2_metrics,
                    "angular_momentum_biased_rotation_events_per_tick",
                ),
                "phase1_mean_angular_momentum_mean_abs_active": mean_for(
                    phase1_metrics,
                    "angular_momentum_mean_abs_active",
                ),
                "phase2_mean_angular_momentum_mean_abs_active": mean_for(
                    phase2_metrics,
                    "angular_momentum_mean_abs_active",
                ),
                "phase1_mean_persistent_interface_v_changed_fraction": mean_for(
                    phase1_metrics,
                    "persistent_interface_v_changed_fraction",
                ),
                "phase2_mean_persistent_interface_v_changed_fraction": mean_for(
                    phase2_metrics,
                    "persistent_interface_v_changed_fraction",
                ),
                "phase1_mean_transition_entropy": mean_for(
                    phase1_metrics,
                    "persistent_interface_changed_transition_entropy",
                ),
                "phase2_mean_transition_entropy": mean_for(
                    phase2_metrics,
                    "persistent_interface_changed_transition_entropy",
                ),
                "phase1_mean_candidate_turnover": mean_for(
                    phase1_metrics,
                    "persistent_interface_candidate_turnover",
                ),
                "phase2_mean_candidate_turnover": mean_for(
                    phase2_metrics,
                    "persistent_interface_candidate_turnover",
                ),
                "phase1_mean_active_interface_turnover": mean_for(
                    phase1_metrics,
                    "active_interface_turnover_fraction",
                ),
                "phase2_mean_active_interface_turnover": mean_for(
                    phase2_metrics,
                    "active_interface_turnover_fraction",
                ),
                "phase1_mean_active_interface_candidate_target_turnover": mean_for(
                    phase1_metrics,
                    "active_interface_candidate_target_turnover",
                ),
                "phase2_mean_active_interface_candidate_target_turnover": mean_for(
                    phase2_metrics,
                    "active_interface_candidate_target_turnover",
                ),
                "phase1_mean_component_count_delta": mean_for(phase1_metrics, "component_count_delta"),
                "phase2_mean_component_count_delta": mean_for(phase2_metrics, "component_count_delta"),
                "phase1_mean_largest_component_delta": mean_for(phase1_metrics, "largest_component_delta"),
                "phase2_mean_largest_component_delta": mean_for(phase2_metrics, "largest_component_delta"),
            }
        )
    return summary_rows


def main() -> None:
    args = parse_args()
    output_prefix = Path(args.output_prefix)
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
    rows, family_rows = assign_families(rows, float(args.cluster_distance_threshold))
    summary_rows = summarize(rows, family_rows)
    lineage_rows = [lineage_output_row(row) for row in rows]

    write_csv(lineage_path, LINEAGE_FIELDNAMES, lineage_rows)
    write_csv(family_path, FAMILY_FIELDNAMES, family_rows)
    write_csv(summary_path, SUMMARY_FIELDNAMES, summary_rows)
    payload = {
        "config_path": args.config,
        "checkpoint_state_dir": args.checkpoint_state_dir,
        "output_prefix": output_prefix.as_posix(),
        "lineage_path": lineage_path.as_posix(),
        "family_path": family_path.as_posix(),
        "summary_path": summary_path.as_posix(),
        "checkpoint_ticks": sorted({int(value) for value in args.checkpoint_ticks}),
        "samples": int(args.samples),
        "horizon": int(args.horizon),
        "phase_length": int(args.phase_length),
        "sample_every": int(args.sample_every),
        "connectivity": args.connectivity,
        "cluster_distance_threshold": float(args.cluster_distance_threshold),
        "summary_rows": summary_rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
