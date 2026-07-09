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
from rotation_branch_lineage import counter_to_vector, js_distance, mean_for, phase_rows, phase_summary
from rotation_lineage_persistence import assign_families, counts_text
from rotational_recursion_diagnostic import metric_from_world, row_for_snapshots


MASK_NAMES = ("active", "depleted", "active_interface", "depleted_interface", "interface_union")

SAMPLE_FIELDNAMES = [
    "variant",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "phase",
    "family",
    "family_path",
    "bounded_nonrunaway",
    "ledger_exact",
    "early_stop_reason",
    "active_iotas",
    "depleted_cells",
    "active_interface_cells",
    "depleted_interface_cells",
    "interface_union_cells",
    "active_depleted_adjacency",
    "depleted_active_adjacency",
    "largest_coherence_cube26",
    "coherence_count_cube26",
    "coherence_ratio_cube26",
    "top1_component_fraction_cube26",
    "component_size_entropy_cube26",
    "rotation_events_per_tick",
    "angular_momentum_biased_rotation_events_per_tick",
    "persistent_interface_v_changed_fraction",
    "persistent_interface_changed_transition_entropy",
    "active_interface_turnover_fraction",
]

PAIR_FIELDNAMES = [
    "variant",
    "checkpoint_tick",
    "phase",
    "sample_i",
    "sample_j",
    "family_i",
    "family_j",
    "family_path_i",
    "family_path_j",
    "same_phase_family",
    "same_full_path",
    "phase_transition_distance",
    "active_jaccard_distance",
    "depleted_jaccard_distance",
    "active_interface_jaccard_distance",
    "depleted_interface_jaccard_distance",
    "interface_union_jaccard_distance",
    "active_count_abs_delta",
    "depleted_count_abs_delta",
    "active_interface_count_abs_delta",
    "interface_union_count_abs_delta",
    "largest_component_abs_delta",
    "component_count_abs_delta",
    "component_entropy_abs_delta",
]

SUMMARY_FIELDNAMES = [
    "variant",
    "checkpoint_tick",
    "phase",
    "samples",
    "phase_family_count",
    "phase_family_table",
    "full_path_count",
    "full_path_table",
    "all_pair_count",
    "same_family_pair_count",
    "different_family_pair_count",
    "same_path_pair_count",
    "different_path_pair_count",
    "mean_all_active_jaccard_distance",
    "mean_same_family_active_jaccard_distance",
    "mean_different_family_active_jaccard_distance",
    "active_family_distance_gap",
    "mean_all_depleted_jaccard_distance",
    "mean_same_family_depleted_jaccard_distance",
    "mean_different_family_depleted_jaccard_distance",
    "depleted_family_distance_gap",
    "mean_all_active_interface_jaccard_distance",
    "mean_same_family_active_interface_jaccard_distance",
    "mean_different_family_active_interface_jaccard_distance",
    "active_interface_family_distance_gap",
    "mean_all_interface_union_jaccard_distance",
    "mean_same_family_interface_union_jaccard_distance",
    "mean_different_family_interface_union_jaccard_distance",
    "interface_union_family_distance_gap",
    "mean_phase_transition_distance",
    "pearson_transition_active_distance",
    "pearson_transition_interface_union_distance",
    "mean_all_largest_component_abs_delta",
    "mean_all_component_count_abs_delta",
    "mean_all_component_entropy_abs_delta",
    "mean_active_depleted_adjacency",
    "mean_largest_coherence_cube26",
    "mean_coherence_count_cube26",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure whether directional lineages predict active/depleted morphology."
    )
    parser.add_argument("--variant", required=True)
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


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def pack_mask(mask: np.ndarray) -> np.ndarray:
    return np.packbits(np.asarray(mask, dtype=np.bool_).ravel())


def unpack_mask(packed: np.ndarray, size: int) -> np.ndarray:
    return np.unpackbits(packed, count=size).astype(np.bool_)


def jaccard_distance(first: np.ndarray, second: np.ndarray) -> float:
    union = int(np.count_nonzero(first | second))
    if union <= 0:
        return 0.0
    intersection = int(np.count_nonzero(first & second))
    return 1.0 - float(intersection / union)


def pearson(first: list[float], second: list[float]) -> float | str:
    if len(first) < 2 or len(second) < 2:
        return ""
    first_array = np.array(first, dtype=np.float64)
    second_array = np.array(second, dtype=np.float64)
    if float(np.std(first_array)) <= 0.0 or float(np.std(second_array)) <= 0.0:
        return ""
    return float(np.corrcoef(first_array, second_array)[0, 1])


def mean_or_blank(values: list[float]) -> float | str:
    return float(np.mean(values)) if values else ""


def gap_or_blank(different: list[float], same: list[float]) -> float | str:
    if not different or not same:
        return ""
    return float(np.mean(different) - np.mean(same))


def active_depleted_adjacency(snapshot_masks: dict[str, np.ndarray], mask_size: int) -> tuple[float, float]:
    active = unpack_mask(snapshot_masks["active"], mask_size)
    depleted = unpack_mask(snapshot_masks["depleted"], mask_size)
    active_interface = unpack_mask(snapshot_masks["active_interface"], mask_size)
    depleted_interface = unpack_mask(snapshot_masks["depleted_interface"], mask_size)
    active_count = int(np.count_nonzero(active))
    depleted_count = int(np.count_nonzero(depleted))
    return (
        float(np.count_nonzero(active_interface) / active_count) if active_count else 0.0,
        float(np.count_nonzero(depleted_interface) / depleted_count) if depleted_count else 0.0,
    )


def run_morphology_task(task: dict[str, Any]) -> dict[str, Any]:
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
    boundary_metrics = {0: collect_metrics(world, checkpoint_tick)}
    phase_masks: list[dict[str, np.ndarray] | None] = [None] * phase_count
    mask_size = int(world.active.size)
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
            phase_index = min((offset - 1) // phase_length, phase_count - 1)
            boundary_metrics[(phase_index + 1) * phase_length] = collect_metrics(
                world,
                checkpoint_tick + offset,
            )
            boundary_snapshot = take_snapshot(world, checkpoint_tick + offset, connectivity)
            phase_masks[phase_index] = {
                "active": pack_mask(boundary_snapshot.active),
                "depleted": pack_mask(boundary_snapshot.depleted),
                "active_interface": pack_mask(boundary_snapshot.active_interface),
                "depleted_interface": pack_mask(boundary_snapshot.depleted_interface),
                "interface_union": pack_mask(boundary_snapshot.interface_union),
            }
        if early_stop_reason:
            break

    final_metric = collect_metrics(world, checkpoint_tick + final_offset)
    final_snapshot = take_snapshot(world, checkpoint_tick + final_offset, connectivity)
    final_masks = {
        "active": pack_mask(final_snapshot.active),
        "depleted": pack_mask(final_snapshot.depleted),
        "active_interface": pack_mask(final_snapshot.active_interface),
        "depleted_interface": pack_mask(final_snapshot.depleted_interface),
        "interface_union": pack_mask(final_snapshot.interface_union),
    }
    for phase in range(1, phase_count + 1):
        boundary = phase * phase_length
        if boundary not in boundary_metrics:
            boundary_metrics[boundary] = final_metric
        if phase_masks[phase - 1] is None:
            phase_masks[phase - 1] = final_masks

    phase_summaries: list[dict[str, Any]] = []
    vector_count = len(world.vectors)
    for phase_index in range(phase_count):
        start_offset = phase_index * phase_length
        end_offset = (phase_index + 1) * phase_length
        phase_summaries.append(
            phase_summary(
                phase_rows(rows, start_offset, end_offset, checkpoint_tick),
                counters_by_phase[phase_index],
                boundary_metrics[start_offset],
                boundary_metrics[end_offset],
                connectivity,
                top_limit,
            )
        )

    return {
        "checkpoint_tick": checkpoint_tick,
        "sample_index": int(task["sample_index"]),
        "continuation_seed": int(task["continuation_seed"]),
        "early_stop_reason": early_stop_reason,
        "bounded_nonrunaway": not bool(early_stop_reason),
        "ledger_exact": abs(float(final_metric.get("ledger_error", 0.0))) == 0.0,
        "phases": phase_summaries,
        "boundary_metrics": [boundary_metrics[(phase + 1) * phase_length] for phase in range(phase_count)],
        "_phase_counters": counters_by_phase,
        "_phase_vectors": [counter_to_vector(counter, vector_count) for counter in counters_by_phase],
        "_phase_masks": phase_masks,
        "_mask_size": mask_size,
    }


def run_tasks(tasks: list[dict[str, Any]], workers: int) -> list[dict[str, Any]]:
    if workers <= 1:
        return [run_morphology_task(task) for task in tasks]
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(run_morphology_task, task) for task in tasks]
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: (int(row["checkpoint_tick"]), int(row["sample_index"])))
    return rows


def family_path(row: dict[str, Any]) -> str:
    return "->".join(str(int(value)) for value in row["families"])


def sample_rows(rows: list[dict[str, Any]], variant: str, phase_count: int) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for row in rows:
        path = family_path(row)
        for phase_index in range(phase_count):
            phase = phase_index + 1
            metric = row["boundary_metrics"][phase_index]
            masks = row["_phase_masks"][phase_index]
            active_adjacency, depleted_adjacency = active_depleted_adjacency(masks, int(row["_mask_size"]))
            output_rows.append(
                {
                    "variant": variant,
                    "checkpoint_tick": row["checkpoint_tick"],
                    "sample_index": row["sample_index"],
                    "continuation_seed": row["continuation_seed"],
                    "phase": phase,
                    "family": row["families"][phase_index],
                    "family_path": path,
                    "bounded_nonrunaway": row["bounded_nonrunaway"],
                    "ledger_exact": row["ledger_exact"],
                    "early_stop_reason": row["early_stop_reason"],
                    "active_iotas": metric.get("active_iotas", 0.0),
                    "depleted_cells": metric.get("depleted_cells", 0.0),
                    "active_interface_cells": int(np.count_nonzero(unpack_mask(masks["active_interface"], int(row["_mask_size"])))),
                    "depleted_interface_cells": int(np.count_nonzero(unpack_mask(masks["depleted_interface"], int(row["_mask_size"])))),
                    "interface_union_cells": int(np.count_nonzero(unpack_mask(masks["interface_union"], int(row["_mask_size"])))),
                    "active_depleted_adjacency": active_adjacency,
                    "depleted_active_adjacency": depleted_adjacency,
                    "largest_coherence_cube26": metric.get("largest_coherence_cube26", 0.0),
                    "coherence_count_cube26": metric.get("coherence_count_cube26", 0.0),
                    "coherence_ratio_cube26": metric.get("coherence_ratio_cube26", 0.0),
                    "top1_component_fraction_cube26": metric.get("top1_component_fraction_cube26", 0.0),
                    "component_size_entropy_cube26": metric.get("component_size_entropy_cube26", 0.0),
                    "rotation_events_per_tick": row["phases"][phase_index].get("rotation_events_per_tick", 0.0),
                    "angular_momentum_biased_rotation_events_per_tick": row["phases"][phase_index].get(
                        "angular_momentum_biased_rotation_events_per_tick",
                        0.0,
                    ),
                    "persistent_interface_v_changed_fraction": row["phases"][phase_index].get(
                        "persistent_interface_v_changed_fraction",
                        0.0,
                    ),
                    "persistent_interface_changed_transition_entropy": row["phases"][phase_index].get(
                        "persistent_interface_changed_transition_entropy",
                        0.0,
                    ),
                    "active_interface_turnover_fraction": row["phases"][phase_index].get(
                        "active_interface_turnover_fraction",
                        0.0,
                    ),
                }
            )
    return output_rows


def pair_rows(rows: list[dict[str, Any]], variant: str, phase_count: int) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for checkpoint_tick in sorted({int(row["checkpoint_tick"]) for row in rows}):
        checkpoint_rows = [row for row in rows if int(row["checkpoint_tick"]) == checkpoint_tick]
        for phase_index in range(phase_count):
            phase = phase_index + 1
            for first_index, first in enumerate(checkpoint_rows):
                for second in checkpoint_rows[first_index + 1 :]:
                    mask_size = int(first["_mask_size"])
                    first_masks = first["_phase_masks"][phase_index]
                    second_masks = second["_phase_masks"][phase_index]
                    distances = {
                        f"{name}_jaccard_distance": jaccard_distance(
                            unpack_mask(first_masks[name], mask_size),
                            unpack_mask(second_masks[name], mask_size),
                        )
                        for name in MASK_NAMES
                    }
                    first_metric = first["boundary_metrics"][phase_index]
                    second_metric = second["boundary_metrics"][phase_index]
                    output_rows.append(
                        {
                            "variant": variant,
                            "checkpoint_tick": checkpoint_tick,
                            "phase": phase,
                            "sample_i": first["sample_index"],
                            "sample_j": second["sample_index"],
                            "family_i": first["families"][phase_index],
                            "family_j": second["families"][phase_index],
                            "family_path_i": family_path(first),
                            "family_path_j": family_path(second),
                            "same_phase_family": int(first["families"][phase_index])
                            == int(second["families"][phase_index]),
                            "same_full_path": family_path(first) == family_path(second),
                            "phase_transition_distance": js_distance(
                                first["_phase_vectors"][phase_index],
                                second["_phase_vectors"][phase_index],
                            ),
                            **distances,
                            "active_count_abs_delta": abs(
                                float(first_metric.get("active_iotas", 0.0))
                                - float(second_metric.get("active_iotas", 0.0))
                            ),
                            "depleted_count_abs_delta": abs(
                                float(first_metric.get("depleted_cells", 0.0))
                                - float(second_metric.get("depleted_cells", 0.0))
                            ),
                            "active_interface_count_abs_delta": abs(
                                int(np.count_nonzero(unpack_mask(first_masks["active_interface"], mask_size)))
                                - int(np.count_nonzero(unpack_mask(second_masks["active_interface"], mask_size)))
                            ),
                            "interface_union_count_abs_delta": abs(
                                int(np.count_nonzero(unpack_mask(first_masks["interface_union"], mask_size)))
                                - int(np.count_nonzero(unpack_mask(second_masks["interface_union"], mask_size)))
                            ),
                            "largest_component_abs_delta": abs(
                                float(first_metric.get("largest_coherence_cube26", 0.0))
                                - float(second_metric.get("largest_coherence_cube26", 0.0))
                            ),
                            "component_count_abs_delta": abs(
                                float(first_metric.get("coherence_count_cube26", 0.0))
                                - float(second_metric.get("coherence_count_cube26", 0.0))
                            ),
                            "component_entropy_abs_delta": abs(
                                float(first_metric.get("component_size_entropy_cube26", 0.0))
                                - float(second_metric.get("component_size_entropy_cube26", 0.0))
                            ),
                        }
                    )
    return output_rows


def summarize_pairs(
    lineage_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    samples: list[dict[str, Any]],
    variant: str,
    phase_count: int,
) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    for checkpoint_tick in sorted({int(row["checkpoint_tick"]) for row in lineage_rows}):
        checkpoint_rows = [row for row in lineage_rows if int(row["checkpoint_tick"]) == checkpoint_tick]
        path_counts = Counter(family_path(row) for row in checkpoint_rows)
        for phase in range(1, phase_count + 1):
            phase_index = phase - 1
            phase_pairs = [
                row
                for row in pairwise_rows
                if int(row["checkpoint_tick"]) == checkpoint_tick and int(row["phase"]) == phase
            ]
            same_family = [row for row in phase_pairs if bool(row["same_phase_family"])]
            different_family = [row for row in phase_pairs if not bool(row["same_phase_family"])]
            same_path = [row for row in phase_pairs if bool(row["same_full_path"])]
            different_path = [row for row in phase_pairs if not bool(row["same_full_path"])]
            phase_sample_rows = [
                row
                for row in samples
                if int(row["checkpoint_tick"]) == checkpoint_tick and int(row["phase"]) == phase
            ]
            family_counts = Counter(int(row["families"][phase_index]) for row in checkpoint_rows)

            def values(source_rows: list[dict[str, Any]], key: str) -> list[float]:
                return [float(row[key]) for row in source_rows]

            transition_distances = values(phase_pairs, "phase_transition_distance")
            active_distances = values(phase_pairs, "active_jaccard_distance")
            interface_distances = values(phase_pairs, "interface_union_jaccard_distance")
            output = {
                "variant": variant,
                "checkpoint_tick": checkpoint_tick,
                "phase": phase,
                "samples": len(checkpoint_rows),
                "phase_family_count": len(family_counts),
                "phase_family_table": counts_text(family_counts),
                "full_path_count": len(path_counts),
                "full_path_table": counts_text(path_counts),
                "all_pair_count": len(phase_pairs),
                "same_family_pair_count": len(same_family),
                "different_family_pair_count": len(different_family),
                "same_path_pair_count": len(same_path),
                "different_path_pair_count": len(different_path),
                "mean_phase_transition_distance": mean_or_blank(transition_distances),
                "pearson_transition_active_distance": pearson(transition_distances, active_distances),
                "pearson_transition_interface_union_distance": pearson(transition_distances, interface_distances),
                "mean_all_largest_component_abs_delta": mean_or_blank(
                    values(phase_pairs, "largest_component_abs_delta")
                ),
                "mean_all_component_count_abs_delta": mean_or_blank(values(phase_pairs, "component_count_abs_delta")),
                "mean_all_component_entropy_abs_delta": mean_or_blank(
                    values(phase_pairs, "component_entropy_abs_delta")
                ),
                "mean_active_depleted_adjacency": mean_or_blank(
                    [float(row["active_depleted_adjacency"]) for row in phase_sample_rows]
                ),
                "mean_largest_coherence_cube26": mean_or_blank(
                    [float(row["largest_coherence_cube26"]) for row in phase_sample_rows]
                ),
                "mean_coherence_count_cube26": mean_or_blank(
                    [float(row["coherence_count_cube26"]) for row in phase_sample_rows]
                ),
            }
            for mask_prefix in ("active", "depleted", "active_interface", "interface_union"):
                key = f"{mask_prefix}_jaccard_distance"
                output[f"mean_all_{key}"] = mean_or_blank(values(phase_pairs, key))
                output[f"mean_same_family_{key}"] = mean_or_blank(values(same_family, key))
                output[f"mean_different_family_{key}"] = mean_or_blank(values(different_family, key))
                output[f"{mask_prefix}_family_distance_gap"] = gap_or_blank(
                    values(different_family, key),
                    values(same_family, key),
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
    samples = sample_rows(rows, str(args.variant), phase_count)
    pairs = pair_rows(rows, str(args.variant), phase_count)
    summary_rows = summarize_pairs(rows, pairs, samples, str(args.variant), phase_count)

    output_prefix = Path(args.output_prefix)
    sample_path = output_prefix.with_name(output_prefix.name + "_samples.csv")
    pair_path = output_prefix.with_name(output_prefix.name + "_pairs.csv")
    family_path = output_prefix.with_name(output_prefix.name + "_families.csv")
    summary_path = output_prefix.with_name(output_prefix.name + "_summary.csv")
    json_path = output_prefix.with_name(output_prefix.name + "_summary.json")

    write_csv(sample_path, SAMPLE_FIELDNAMES, samples)
    write_csv(pair_path, PAIR_FIELDNAMES, pairs)
    write_csv(family_path, [
        "checkpoint_tick",
        "phase",
        "family",
        "size",
        "samples",
        "mean_rotation_events_per_tick",
        "mean_angular_momentum_biased_rotation_events_per_tick",
        "mean_persistent_interface_v_changed_fraction",
        "mean_persistent_interface_changed_transition_entropy",
        "transition_count",
        "transition_families",
        "top_transitions",
    ], family_rows)
    write_csv(summary_path, SUMMARY_FIELDNAMES, summary_rows)

    payload = {
        "variant": args.variant,
        "config_path": args.config,
        "checkpoint_state_dir": args.checkpoint_state_dir,
        "output_prefix": output_prefix.as_posix(),
        "sample_path": sample_path.as_posix(),
        "pair_path": pair_path.as_posix(),
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
