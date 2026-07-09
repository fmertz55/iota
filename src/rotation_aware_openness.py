from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np

from continuation import (
    classify_outcome,
    clone_world,
    connectivity_metric,
    deterministic_continuation_seed,
    entropy_from_counts,
    load_checkpoint,
    save_checkpoint,
)
from experiment_db import artifact_hash, config_hash
from front_turnover_diagnostic import accumulate_counts, take_snapshot
from iota_rig import World, init_world, load_config, step
from metrics import collect_metrics
from rotational_recursion_diagnostic import CandidateContext, metric_from_world, row_for_snapshots
from v02_candidate_diagnostics import structure_rows


RAW_FIELDNAMES = [
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "horizon",
    "final_tick",
    "final_offset",
    "early_stop_reason",
    "rotation_class",
    "rotation_signature",
    "bounded_nonrunaway",
    "ledger_exact",
    "active_iotas",
    "depleted_cells",
    "total_A",
    "active_A",
    "latent_A",
    "ledger_error",
    "classification",
    "largest_coherence_cube26",
    "coherence_ratio_cube26",
    "coherence_count_cube26",
    "component_size_entropy_cube26",
    "top_active_vector_entropy",
    "active_adjacent_to_depleted_fraction",
    "late_rotation_events_per_tick",
    "late_rotation_events_on_residual_entry_per_tick",
    "late_rotation_events_on_secondary_exchange_per_tick",
    "late_residual_participations_per_tick",
    "late_deactivation_events_per_tick",
    "late_residual_deactivation_balance",
    "late_active_turnover_fraction",
    "late_active_interface_turnover_fraction",
    "late_persistent_active_v_changed_fraction",
    "late_persistent_interface_v_changed_fraction",
    "late_persistent_active_changed_transition_entropy",
    "late_persistent_interface_changed_transition_entropy",
    "late_persistent_active_candidate_turnover",
    "late_persistent_interface_candidate_turnover",
    "late_active_vector_entropy",
    "late_active_interface_vector_entropy",
    "late_new_active_vector_entropy",
    "late_new_active_source_vector_match_fraction",
    "late_active_candidate_target_turnover",
    "late_active_interface_candidate_target_turnover",
    "late_interface_changed_transition_families",
    "late_interface_changed_transition_count",
    "active_vector_tv_distance_from_checkpoint",
    "active_interface_vector_tv_distance_from_checkpoint",
    "new_active_vector_state_count",
    "final_active_vector_state_count",
    "window_rows",
]

SUMMARY_FIELDNAMES = [
    "checkpoint_tick",
    "samples",
    "bounded_nonrunaway_count",
    "ledger_exact_count",
    "runaway_count",
    "rotation_class_counts",
    "rotation_class_entropy",
    "rotation_class_openness",
    "rotation_effective_classes",
    "rotation_signature_counts",
    "rotation_signature_entropy",
    "rotation_signature_openness",
    "rotation_effective_signatures",
    "bounded_rotation_signature_counts",
    "bounded_rotation_signature_entropy",
    "bounded_rotation_signature_openness",
    "bounded_rotation_effective_signatures",
    "base_active_iotas",
    "base_depleted_cells",
    "base_ledger_error",
    "base_classification",
    "mean_active_iotas",
    "std_active_iotas",
    "mean_depleted_cells",
    "mean_late_rotation_events_per_tick",
    "mean_late_persistent_interface_v_changed_fraction",
    "mean_late_persistent_interface_changed_transition_entropy",
    "mean_late_persistent_interface_candidate_turnover",
    "mean_late_active_interface_turnover_fraction",
    "mean_late_active_interface_candidate_target_turnover",
    "mean_active_vector_tv_distance_from_checkpoint",
    "mean_active_interface_vector_tv_distance_from_checkpoint",
    "mean_new_active_vector_state_count",
    "max_abs_ledger_error",
    "checkpoint_state_path",
    "checkpoint_state_sha256",
    "checkpoint_state_bytes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate rotation-aware openness from checkpoint continuations."
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--ticks", type=int, default=None)
    parser.add_argument("--checkpoint-every", type=int, default=512)
    parser.add_argument("--checkpoint-ticks", type=int, nargs="+", default=None)
    parser.add_argument("--horizon", type=int, default=256)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--connectivity", choices=["face6", "face18", "cube26"], default="cube26")
    parser.add_argument("--rotation-sample-every", type=int, default=16)
    parser.add_argument("--late-window", type=int, default=128)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--stop-active-iotas", type=int, default=0)
    parser.add_argument("--min-active", type=int, default=1000)
    parser.add_argument("--absorber-lcf", type=float, default=0.95)
    parser.add_argument("--high-dominant-lcf", type=float, default=0.90)
    parser.add_argument("--collapse-active-iotas", type=int, default=100)
    parser.add_argument("--rotation-dead-events-per-tick", type=float, default=0.0)
    parser.add_argument("--rotation-dead-v-change", type=float, default=0.0)
    parser.add_argument("--canalized-entropy-max", type=float, default=0.25)
    parser.add_argument("--canalized-candidate-turnover-max", type=float, default=0.0005)
    parser.add_argument("--directional-drift-vector-tv", type=float, default=0.10)
    parser.add_argument("--directional-drift-vector-entropy", type=float, default=0.75)
    parser.add_argument("--directional-drift-new-vector-states", type=int, default=1)
    parser.add_argument("--branching-transition-families", type=int, default=4)
    parser.add_argument("--branching-entropy", type=float, default=1.0)
    parser.add_argument("--branching-v-change", type=float, default=0.005)
    parser.add_argument("--branching-candidate-turnover", type=float, default=0.001)
    parser.add_argument("--no-save-checkpoints", action="store_true")
    return parser.parse_args()


def checkpoint_schedule(args: argparse.Namespace, cfg: dict[str, Any]) -> list[int]:
    ticks = int(args.ticks if args.ticks is not None else cfg.get("run", {}).get("ticks", 2048))
    if args.checkpoint_ticks is not None:
        values = sorted({int(value) for value in args.checkpoint_ticks})
    else:
        if int(args.checkpoint_every) <= 0:
            raise SystemExit("--checkpoint-every must be positive")
        values = list(range(0, ticks + 1, int(args.checkpoint_every)))
    invalid = [value for value in values if value < 0 or value > ticks]
    if invalid:
        raise SystemExit(f"checkpoint ticks must be within [0, {ticks}], got {invalid}")
    if values[-1] != ticks and args.checkpoint_ticks is None:
        values.append(ticks)
    return sorted(set(values))


def count_bin(value: float) -> str:
    numeric = int(float(value))
    if numeric <= 0:
        return "0"
    if numeric < 32:
        return "1-31"
    if numeric < 128:
        return "32-127"
    if numeric < 512:
        return "128-511"
    if numeric < 1000:
        return "512-999"
    if numeric < 2000:
        return "1000-1999"
    if numeric < 4000:
        return "2000-3999"
    return "4000+"


def rate_bin(value: float) -> str:
    numeric = max(0.0, float(value))
    if numeric == 0.0:
        return "0"
    if numeric < 0.5:
        return "0-0.5"
    if numeric < 1.0:
        return "0.5-1"
    if numeric < 2.0:
        return "1-2"
    if numeric < 4.0:
        return "2-4"
    if numeric < 8.0:
        return "4-8"
    return "8+"


def small_fraction_bin(value: float) -> str:
    numeric = max(0.0, min(1.0, float(value)))
    if numeric == 0.0:
        return "0"
    if numeric < 0.001:
        return "0-0.001"
    if numeric < 0.005:
        return "0.001-0.005"
    if numeric < 0.01:
        return "0.005-0.01"
    if numeric < 0.025:
        return "0.01-0.025"
    if numeric < 0.05:
        return "0.025-0.05"
    if numeric < 0.1:
        return "0.05-0.1"
    return "0.1+"


def entropy_bin(value: float) -> str:
    numeric = max(0.0, float(value))
    if numeric == 0.0:
        return "0"
    if numeric < 0.25:
        return "0-0.25"
    if numeric < 0.75:
        return "0.25-0.75"
    if numeric < 1.5:
        return "0.75-1.5"
    if numeric < 3.0:
        return "1.5-3.0"
    return "3.0+"


def transition_count_bin(value: float) -> str:
    numeric = int(float(value))
    if numeric <= 0:
        return "0"
    if numeric < 4:
        return "1-3"
    if numeric < 8:
        return "4-7"
    if numeric < 16:
        return "8-15"
    if numeric < 32:
        return "16-31"
    return "32+"


def counts_text(counts: Counter[str]) -> str:
    return ";".join(f"{key}:{counts[key]}" for key in sorted(counts))


def normalized_sample_entropy(counts: Counter[str], samples: int) -> float:
    if samples <= 1:
        return 0.0
    return float(entropy_from_counts(counts) / math.log(samples))


def build_context(cfg: dict[str, Any], world: World) -> CandidateContext:
    constants = cfg.get("constants", {})
    return CandidateContext(
        vectors=world.vectors.copy(),
        vector_behaviors=tuple(world.vector_behaviors),
        wrap=bool(world.wrap),
        size=int(world.size),
        valence=max(1, int(constants.get("valence", 1))),
        neighbor_mode=str(constants.get("neighbor_mode", "cube26")),
        decay_mode=str(constants.get("decay_mode", "inverse_square")),
        residual_participation_probability=float(
            constants.get(
                "residual_participation_probability",
                constants.get("depleted_reactivation_probability", 0.0),
            )
        ),
        residual_participation_secondary_only=bool(
            constants.get(
                "residual_participation_secondary_only",
                constants.get("depleted_reactivation_secondary_only", True),
            )
        ),
    )


def active_structure_for(world: World, tick: int, connectivity: str) -> dict[str, Any]:
    for row in structure_rows(world, tick):
        if row["connectivity"] == connectivity and row["mask"] == "active":
            return row
    return {}


def mean_for(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row.get(key, 0.0) or 0.0) for row in rows]
    return float(np.mean(values)) if values else 0.0


def sum_for(rows: list[dict[str, Any]], key: str) -> float:
    return float(sum(float(row.get(key, 0.0) or 0.0) for row in rows))


def vector_distribution(snapshot: Any, mask: np.ndarray, vector_count: int) -> np.ndarray:
    if int(np.count_nonzero(mask)) <= 0:
        return np.zeros(vector_count, dtype=np.float64)
    values = (snapshot.V[mask].astype(np.int64) % vector_count)
    counts = np.bincount(values, minlength=vector_count).astype(np.float64)
    total = float(np.sum(counts))
    return counts / total if total > 0.0 else counts


def vector_tv_distance(
    previous: Any,
    current: Any,
    previous_mask: np.ndarray,
    current_mask: np.ndarray,
    vector_count: int,
) -> float:
    previous_distribution = vector_distribution(previous, previous_mask, vector_count)
    current_distribution = vector_distribution(current, current_mask, vector_count)
    return float(0.5 * np.sum(np.abs(previous_distribution - current_distribution)))


def vector_state_set(snapshot: Any, mask: np.ndarray, vector_count: int) -> set[int]:
    if int(np.count_nonzero(mask)) <= 0:
        return set()
    return {int(value) % vector_count for value in snapshot.V[mask].tolist()}


def changed_interface_transition_counter(previous: Any, current: Any) -> Counter[tuple[int, int]]:
    mask = previous.active_interface & current.active_interface
    if int(np.count_nonzero(mask)) <= 0:
        return Counter()
    previous_vectors = previous.V[mask].astype(np.int64)
    current_vectors = current.V[mask].astype(np.int64)
    changed = previous_vectors != current_vectors
    return Counter(
        (int(before), int(after))
        for before, after in zip(
            previous_vectors[changed].tolist(),
            current_vectors[changed].tolist(),
            strict=False,
        )
    )


def classify_rotation_future(row: dict[str, Any], args_dict: dict[str, Any]) -> str:
    active = int(float(row["active_iotas"]))
    if not bool(row["ledger_exact"]):
        return "ledger_violation"
    if str(row["early_stop_reason"]) or (
        int(args_dict["stop_active_iotas"]) > 0
        and active >= int(args_dict["stop_active_iotas"])
    ):
        return "rotational_ignition"
    if active <= int(args_dict["collapse_active_iotas"]):
        return "rotational_collapse"

    rotation_rate = float(row["late_rotation_events_per_tick"])
    v_change = float(row["late_persistent_interface_v_changed_fraction"])
    changed_entropy = float(row["late_persistent_interface_changed_transition_entropy"])
    candidate_turnover = float(row["late_persistent_interface_candidate_turnover"])
    vector_tv = float(row["active_interface_vector_tv_distance_from_checkpoint"])
    active_vector_entropy = float(row["late_active_vector_entropy"])
    new_vector_count = int(float(row["new_active_vector_state_count"]))
    transition_families = int(float(row["late_interface_changed_transition_families"]))

    if (
        rotation_rate <= float(args_dict["rotation_dead_events_per_tick"])
        and v_change <= float(args_dict["rotation_dead_v_change"])
    ):
        return "rotation_dead"
    if (
        transition_families >= int(args_dict["branching_transition_families"])
        and changed_entropy >= float(args_dict["branching_entropy"])
        and v_change >= float(args_dict["branching_v_change"])
        and candidate_turnover >= float(args_dict["branching_candidate_turnover"])
    ):
        return "rotational_branching"
    if (
        vector_tv >= float(args_dict["directional_drift_vector_tv"])
        or active_vector_entropy >= float(args_dict["directional_drift_vector_entropy"])
        or new_vector_count >= int(args_dict["directional_drift_new_vector_states"])
    ):
        return "directional_drift"
    if (
        changed_entropy <= float(args_dict["canalized_entropy_max"])
        and candidate_turnover <= float(args_dict["canalized_candidate_turnover_max"])
    ):
        return "canalized_rotation"
    return "directional_drift"


def rotation_signature(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row["rotation_class"]),
            count_bin(float(row["active_iotas"])),
            count_bin(float(row["depleted_cells"])),
            rate_bin(float(row["late_rotation_events_per_tick"])),
            small_fraction_bin(float(row["late_persistent_interface_v_changed_fraction"])),
            entropy_bin(float(row["late_persistent_interface_changed_transition_entropy"])),
            entropy_bin(float(row["late_active_interface_vector_entropy"])),
            small_fraction_bin(float(row["active_interface_vector_tv_distance_from_checkpoint"])),
            transition_count_bin(float(row["new_active_vector_state_count"])),
            small_fraction_bin(float(row["late_persistent_interface_candidate_turnover"])),
            transition_count_bin(float(row["late_interface_changed_transition_families"])),
            small_fraction_bin(float(row["late_residual_deactivation_balance"])),
        ]
    )


def run_continuation_task(task: dict[str, Any]) -> dict[str, Any]:
    cfg = load_config(task["config_path"])
    checkpoint = load_checkpoint(task["checkpoint_path"])
    world = clone_world(checkpoint, int(task["continuation_seed"]))
    checkpoint_tick = int(task["checkpoint_tick"])
    connectivity = str(task["connectivity"])
    context = build_context(cfg, world)
    checkpoint_snapshot = take_snapshot(world, checkpoint_tick, connectivity)
    previous_snapshot = checkpoint_snapshot
    pending_extras: dict[str, float] = {}
    window_rows: list[dict[str, Any]] = []
    transition_counters: list[tuple[int, Counter[tuple[int, int]]]] = []
    early_stop_reason = ""
    final_tick = checkpoint_tick

    sample_every = max(1, int(task["rotation_sample_every"]))
    horizon = int(task["horizon"])
    for offset in range(1, horizon + 1):
        extras = step(world, cfg)
        accumulate_counts(pending_extras, extras)
        final_tick = checkpoint_tick + offset
        active_count = int(world.active.sum())
        if int(task["stop_active_iotas"]) > 0 and active_count >= int(task["stop_active_iotas"]):
            early_stop_reason = f"active_iotas >= {task['stop_active_iotas']}"
        should_sample = offset % sample_every == 0 or offset == horizon or bool(early_stop_reason)
        if should_sample:
            current_snapshot = take_snapshot(world, final_tick, connectivity)
            metric = metric_from_world(world, pending_extras)
            row = row_for_snapshots(previous_snapshot, current_snapshot, context, metric, connectivity)
            window_rows.append(row)
            transition_counters.append(
                (
                    final_tick,
                    changed_interface_transition_counter(previous_snapshot, current_snapshot),
                )
            )
            previous_snapshot = current_snapshot
            pending_extras = {}
        if early_stop_reason:
            break

    final_snapshot = previous_snapshot
    final_metric = collect_metrics(world, final_tick)
    final_structure = active_structure_for(world, final_tick, connectivity)
    late_start = final_tick - min(int(task["late_window"]), max(0, final_tick - checkpoint_tick))
    late_rows = [row for row in window_rows if int(row["tick"]) >= late_start]
    if not late_rows and window_rows:
        late_rows = [window_rows[-1]]

    late_transition_counter: Counter[tuple[int, int]] = Counter()
    for tick, counter in transition_counters:
        if tick >= late_start:
            late_transition_counter.update(counter)

    vector_count = len(world.vectors)
    checkpoint_active_states = vector_state_set(checkpoint_snapshot, checkpoint_snapshot.active, vector_count)
    final_active_states = vector_state_set(final_snapshot, final_snapshot.active, vector_count)
    residual_rate = mean_for(late_rows, "residual_participations_per_tick")
    deactivation_rate = mean_for(late_rows, "deactivation_events_per_tick")
    residual_balance = abs(residual_rate - deactivation_rate) / max(residual_rate, deactivation_rate, 1e-12)
    ledger_error = float(final_metric.get("ledger_error", 0.0))
    ledger_exact = abs(ledger_error) == 0.0
    bounded_nonrunaway = ledger_exact and not early_stop_reason
    if int(task["stop_active_iotas"]) > 0:
        bounded_nonrunaway = bounded_nonrunaway and int(final_metric["active_iotas"]) < int(task["stop_active_iotas"])

    row = {
        "checkpoint_tick": checkpoint_tick,
        "sample_index": int(task["sample_index"]),
        "continuation_seed": int(task["continuation_seed"]),
        "horizon": horizon,
        "final_tick": final_tick,
        "final_offset": final_tick - checkpoint_tick,
        "early_stop_reason": early_stop_reason,
        "rotation_class": "",
        "rotation_signature": "",
        "bounded_nonrunaway": bounded_nonrunaway,
        "ledger_exact": ledger_exact,
        "active_iotas": int(final_metric["active_iotas"]),
        "depleted_cells": float(final_metric.get("depleted_cells", 0.0)),
        "total_A": float(final_metric.get("total_A", 0.0)),
        "active_A": float(final_metric.get("active_A", 0.0)),
        "latent_A": float(final_metric.get("latent_A", 0.0)),
        "ledger_error": ledger_error,
        "classification": classify_outcome(
            final_metric,
            connectivity,
            int(task["min_active"]),
            float(task["absorber_lcf"]),
            float(task["high_dominant_lcf"]),
        ),
        "largest_coherence_cube26": int(final_metric["largest_coherence_cube26"]),
        "coherence_ratio_cube26": float(final_metric["coherence_ratio_cube26"]),
        "coherence_count_cube26": int(final_metric["coherence_count_cube26"]),
        "component_size_entropy_cube26": float(final_metric["component_size_entropy_cube26"]),
        "top_active_vector_entropy": float(final_structure.get("top_active_vector_entropy", 0.0) or 0.0),
        "active_adjacent_to_depleted_fraction": float(
            final_structure.get("active_adjacent_to_depleted_fraction", 0.0) or 0.0
        ),
        "late_rotation_events_per_tick": mean_for(late_rows, "rotation_events_per_tick"),
        "late_rotation_events_on_residual_entry_per_tick": mean_for(
            late_rows,
            "rotation_events_on_residual_entry_per_tick",
        ),
        "late_rotation_events_on_secondary_exchange_per_tick": mean_for(
            late_rows,
            "rotation_events_on_secondary_exchange_per_tick",
        ),
        "late_residual_participations_per_tick": residual_rate,
        "late_deactivation_events_per_tick": deactivation_rate,
        "late_residual_deactivation_balance": residual_balance,
        "late_active_turnover_fraction": mean_for(late_rows, "active_turnover_fraction"),
        "late_active_interface_turnover_fraction": mean_for(late_rows, "active_interface_turnover_fraction"),
        "late_persistent_active_v_changed_fraction": mean_for(
            late_rows,
            "persistent_active_v_changed_fraction",
        ),
        "late_persistent_interface_v_changed_fraction": mean_for(
            late_rows,
            "persistent_interface_v_changed_fraction",
        ),
        "late_persistent_active_changed_transition_entropy": mean_for(
            late_rows,
            "persistent_active_changed_transition_entropy",
        ),
        "late_persistent_interface_changed_transition_entropy": mean_for(
            late_rows,
            "persistent_interface_changed_transition_entropy",
        ),
        "late_persistent_active_candidate_turnover": mean_for(
            late_rows,
            "persistent_active_candidate_turnover_mean",
        ),
        "late_persistent_interface_candidate_turnover": mean_for(
            late_rows,
            "persistent_interface_candidate_turnover_mean",
        ),
        "late_active_vector_entropy": mean_for(late_rows, "active_vector_entropy"),
        "late_active_interface_vector_entropy": mean_for(late_rows, "active_interface_vector_entropy"),
        "late_new_active_vector_entropy": mean_for(late_rows, "new_active_vector_entropy"),
        "late_new_active_source_vector_match_fraction": mean_for(
            late_rows,
            "new_active_source_vector_match_fraction",
        ),
        "late_active_candidate_target_turnover": mean_for(late_rows, "active_candidate_target_turnover"),
        "late_active_interface_candidate_target_turnover": mean_for(
            late_rows,
            "active_interface_candidate_target_turnover",
        ),
        "late_interface_changed_transition_families": len(late_transition_counter),
        "late_interface_changed_transition_count": sum(late_transition_counter.values()),
        "active_vector_tv_distance_from_checkpoint": vector_tv_distance(
            checkpoint_snapshot,
            final_snapshot,
            checkpoint_snapshot.active,
            final_snapshot.active,
            vector_count,
        ),
        "active_interface_vector_tv_distance_from_checkpoint": vector_tv_distance(
            checkpoint_snapshot,
            final_snapshot,
            checkpoint_snapshot.active_interface,
            final_snapshot.active_interface,
            vector_count,
        ),
        "new_active_vector_state_count": len(final_active_states - checkpoint_active_states),
        "final_active_vector_state_count": len(final_active_states),
        "window_rows": len(window_rows),
    }
    row["rotation_class"] = classify_rotation_future(row, task)
    row["rotation_signature"] = rotation_signature(row)
    return row


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def summarize_checkpoint(
    checkpoint_tick: int,
    base_metric: dict[str, Any],
    rows: list[dict[str, Any]],
    state_artifact: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    class_counts = Counter(str(row["rotation_class"]) for row in rows)
    signature_counts = Counter(str(row["rotation_signature"]) for row in rows)
    bounded_rows = [row for row in rows if bool(row["bounded_nonrunaway"])]
    bounded_signature_counts = Counter(str(row["rotation_signature"]) for row in bounded_rows)
    samples = len(rows)
    active_values = np.array([float(row["active_iotas"]) for row in rows], dtype=np.float64)
    depleted_values = np.array([float(row["depleted_cells"]) for row in rows], dtype=np.float64)
    ledger_errors = np.array([float(row["ledger_error"]) for row in rows], dtype=np.float64)
    class_entropy = entropy_from_counts(class_counts)
    signature_entropy = entropy_from_counts(signature_counts)
    bounded_signature_entropy = entropy_from_counts(bounded_signature_counts)
    return {
        "checkpoint_tick": checkpoint_tick,
        "samples": samples,
        "bounded_nonrunaway_count": len(bounded_rows),
        "ledger_exact_count": sum(1 for row in rows if bool(row["ledger_exact"])),
        "runaway_count": sum(1 for row in rows if str(row["early_stop_reason"])),
        "rotation_class_counts": counts_text(class_counts),
        "rotation_class_entropy": class_entropy,
        "rotation_class_openness": normalized_sample_entropy(class_counts, samples),
        "rotation_effective_classes": float(np.exp(class_entropy)) if rows else 0.0,
        "rotation_signature_counts": counts_text(signature_counts),
        "rotation_signature_entropy": signature_entropy,
        "rotation_signature_openness": normalized_sample_entropy(signature_counts, samples),
        "rotation_effective_signatures": float(np.exp(signature_entropy)) if rows else 0.0,
        "bounded_rotation_signature_counts": counts_text(bounded_signature_counts),
        "bounded_rotation_signature_entropy": bounded_signature_entropy,
        "bounded_rotation_signature_openness": normalized_sample_entropy(
            bounded_signature_counts,
            len(bounded_rows),
        ),
        "bounded_rotation_effective_signatures": (
            float(np.exp(bounded_signature_entropy)) if bounded_rows else 0.0
        ),
        "base_active_iotas": int(base_metric["active_iotas"]),
        "base_depleted_cells": float(base_metric.get("depleted_cells", 0.0)),
        "base_ledger_error": float(base_metric.get("ledger_error", 0.0)),
        "base_classification": classify_outcome(
            base_metric,
            args.connectivity,
            int(args.min_active),
            float(args.absorber_lcf),
            float(args.high_dominant_lcf),
        ),
        "mean_active_iotas": float(np.mean(active_values)) if len(active_values) else 0.0,
        "std_active_iotas": float(np.std(active_values)) if len(active_values) else 0.0,
        "mean_depleted_cells": float(np.mean(depleted_values)) if len(depleted_values) else 0.0,
        "mean_late_rotation_events_per_tick": mean_for(rows, "late_rotation_events_per_tick"),
        "mean_late_persistent_interface_v_changed_fraction": mean_for(
            rows,
            "late_persistent_interface_v_changed_fraction",
        ),
        "mean_late_persistent_interface_changed_transition_entropy": mean_for(
            rows,
            "late_persistent_interface_changed_transition_entropy",
        ),
        "mean_late_persistent_interface_candidate_turnover": mean_for(
            rows,
            "late_persistent_interface_candidate_turnover",
        ),
        "mean_late_active_interface_turnover_fraction": mean_for(
            rows,
            "late_active_interface_turnover_fraction",
        ),
        "mean_late_active_interface_candidate_target_turnover": mean_for(
            rows,
            "late_active_interface_candidate_target_turnover",
        ),
        "mean_active_vector_tv_distance_from_checkpoint": mean_for(
            rows,
            "active_vector_tv_distance_from_checkpoint",
        ),
        "mean_active_interface_vector_tv_distance_from_checkpoint": mean_for(
            rows,
            "active_interface_vector_tv_distance_from_checkpoint",
        ),
        "mean_new_active_vector_state_count": mean_for(rows, "new_active_vector_state_count"),
        "max_abs_ledger_error": float(np.max(np.abs(ledger_errors))) if len(ledger_errors) else 0.0,
        **state_artifact,
    }


def task_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        key: value
        for key, value in vars(args).items()
        if key
        not in {
            "checkpoint_ticks",
            "checkpoint_every",
            "ticks",
            "output_prefix",
            "workers",
            "no_save_checkpoints",
        }
    }


def run_tasks(tasks: list[dict[str, Any]], workers: int) -> list[dict[str, Any]]:
    if workers <= 1:
        return [run_continuation_task(task) for task in tasks]
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(run_continuation_task, task) for task in tasks]
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: (int(row["checkpoint_tick"]), int(row["sample_index"])))
    return rows


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    checkpoint_ticks = checkpoint_schedule(args, cfg)
    output_prefix = Path(args.output_prefix)
    raw_path = output_prefix.with_name(output_prefix.name + "_raw.csv")
    summary_path = output_prefix.with_name(output_prefix.name + "_summary.csv")
    json_path = output_prefix.with_name(output_prefix.name + "_summary.json")
    state_dir = output_prefix.with_name(output_prefix.name + "_states")
    state_dir.mkdir(parents=True, exist_ok=True)

    max_tick = max(checkpoint_ticks)
    checkpoint_set = set(checkpoint_ticks)
    world = init_world(cfg)
    checkpoints: dict[int, dict[str, Any]] = {}
    for tick in range(0, max_tick + 1):
        if tick in checkpoint_set:
            base_metric = collect_metrics(world, tick)
            state_path = state_dir / f"checkpoint_tick_{tick:06d}.npz"
            if not args.no_save_checkpoints:
                save_checkpoint(
                    world,
                    state_path,
                    {
                        "checkpoint_tick": tick,
                        "config_hash": config_hash(cfg),
                        "samples": args.samples,
                        "horizon": args.horizon,
                    },
                )
                state_artifact = {
                    "checkpoint_state_path": state_path.as_posix(),
                    "checkpoint_state_sha256": artifact_hash(state_path),
                    "checkpoint_state_bytes": str(state_path.stat().st_size),
                }
            else:
                save_checkpoint(world, state_path, {"checkpoint_tick": tick, "temporary": True})
                state_artifact = {
                    "checkpoint_state_path": "",
                    "checkpoint_state_sha256": "",
                    "checkpoint_state_bytes": "",
                }
            checkpoints[tick] = {
                "base_metric": base_metric,
                "state_path": state_path,
                "state_artifact": state_artifact,
            }
        if tick < max_tick:
            step(world, cfg)

    raw_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    base_task_args = task_args(args)
    workers = max(1, int(args.workers))
    for checkpoint_tick in checkpoint_ticks:
        tasks: list[dict[str, Any]] = []
        checkpoint_path = checkpoints[checkpoint_tick]["state_path"]
        for sample_index in range(int(args.samples)):
            tasks.append(
                {
                    **base_task_args,
                    "config_path": args.config,
                    "checkpoint_path": checkpoint_path.as_posix(),
                    "checkpoint_tick": checkpoint_tick,
                    "sample_index": sample_index,
                    "continuation_seed": deterministic_continuation_seed(
                        int(args.rng_seed_base),
                        checkpoint_tick,
                        sample_index,
                    ),
                }
            )
        checkpoint_rows = run_tasks(tasks, workers)
        raw_rows.extend(checkpoint_rows)
        summary_rows.append(
            summarize_checkpoint(
                checkpoint_tick,
                checkpoints[checkpoint_tick]["base_metric"],
                checkpoint_rows,
                checkpoints[checkpoint_tick]["state_artifact"],
                args,
            )
        )
        write_csv(raw_path, RAW_FIELDNAMES, raw_rows)
        write_csv(summary_path, SUMMARY_FIELDNAMES, summary_rows)
        json_path.write_text(
            json.dumps(
                {
                    "config_path": args.config,
                    "config_hash": config_hash(cfg),
                    "raw_path": raw_path.as_posix(),
                    "summary_path": summary_path.as_posix(),
                    "checkpoint_ticks": checkpoint_ticks,
                    "samples": args.samples,
                    "horizon": args.horizon,
                    "connectivity": args.connectivity,
                    "rotation_sample_every": args.rotation_sample_every,
                    "late_window": args.late_window,
                    "workers": workers,
                    "summary_rows": summary_rows,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        class_counts = Counter(str(row["rotation_class"]) for row in checkpoint_rows)
        signature_counts = Counter(str(row["rotation_signature"]) for row in checkpoint_rows)
        print(
            f"checkpoint={checkpoint_tick} classes={counts_text(class_counts)} "
            f"signatures={len(signature_counts)} bounded={summary_rows[-1]['bounded_nonrunaway_count']}"
        )

    raw_rows.sort(key=lambda row: (int(row["checkpoint_tick"]), int(row["sample_index"])))
    write_csv(raw_path, RAW_FIELDNAMES, raw_rows)
    write_csv(summary_path, SUMMARY_FIELDNAMES, summary_rows)
    json_path.write_text(
        json.dumps(
            {
                "config_path": args.config,
                "config_hash": config_hash(cfg),
                "raw_path": raw_path.as_posix(),
                "summary_path": summary_path.as_posix(),
                "checkpoint_ticks": checkpoint_ticks,
                "samples": args.samples,
                "horizon": args.horizon,
                "connectivity": args.connectivity,
                "rotation_sample_every": args.rotation_sample_every,
                "late_window": args.late_window,
                "workers": workers,
                "summary_rows": summary_rows,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(json_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
