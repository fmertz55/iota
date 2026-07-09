from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from front_turnover_diagnostic import (
    COUNT_KEYS,
    Snapshot,
    accumulate_counts,
    fraction,
    mask_delta,
    take_snapshot,
)
from iota_rig import (
    candidate_neighbor_steps,
    decay,
    init_world,
    load_config,
    step,
)


FIELDNAMES = [
    "tick",
    "previous_tick",
    "window_ticks",
    "active_iotas",
    "depleted_cells",
    "active_interface_cells",
    "amplitude_transfers",
    "deactivation_events",
    "residual_participations",
    "rotation_events",
    "rotation_events_on_residual_entry",
    "rotation_events_on_secondary_exchange",
    "angular_momentum_updates",
    "angular_momentum_biased_rotation_events",
    "angular_momentum_bias_abs_sum",
    "angular_momentum_observed_turn_abs_sum",
    "angular_momentum_secondary_bias_sources",
    "angular_momentum_secondary_bias_selected_candidates",
    "angular_momentum_nonzero_cells",
    "angular_momentum_mean_abs_active",
    "angular_momentum_mean_signed_active",
    "angular_momentum_max_abs",
    "amplitude_transfers_per_tick",
    "deactivation_events_per_tick",
    "residual_participations_per_tick",
    "rotation_events_per_tick",
    "rotation_events_on_residual_entry_per_tick",
    "rotation_events_on_secondary_exchange_per_tick",
    "angular_momentum_updates_per_tick",
    "angular_momentum_biased_rotation_events_per_tick",
    "angular_momentum_secondary_bias_sources_per_tick",
    "angular_momentum_secondary_bias_selected_candidates_per_tick",
    "active_new_cells",
    "active_lost_cells",
    "active_turnover_fraction",
    "active_interface_new_cells",
    "active_interface_lost_cells",
    "active_interface_turnover_fraction",
    "persistent_active_cells",
    "persistent_active_v_changed",
    "persistent_active_v_changed_fraction",
    "persistent_active_transition_entropy",
    "persistent_active_changed_transition_entropy",
    "persistent_active_candidate_turnover_mean",
    "persistent_active_candidate_jaccard_mean",
    "persistent_interface_cells",
    "persistent_interface_v_changed",
    "persistent_interface_v_changed_fraction",
    "persistent_interface_transition_entropy",
    "persistent_interface_changed_transition_entropy",
    "persistent_interface_candidate_turnover_mean",
    "persistent_interface_candidate_jaccard_mean",
    "active_vector_entropy",
    "active_vector_dominant_fraction",
    "active_interface_vector_entropy",
    "active_interface_vector_dominant_fraction",
    "new_active_vector_entropy",
    "new_active_vector_dominant_fraction",
    "new_active_source_vector_match_fraction",
    "active_candidate_targets_previous",
    "active_candidate_targets_current",
    "active_candidate_target_jaccard",
    "active_candidate_target_turnover",
    "active_interface_candidate_targets_previous",
    "active_interface_candidate_targets_current",
    "active_interface_candidate_target_jaccard",
    "active_interface_candidate_target_turnover",
    "interface_radial_alignment_mean",
    "interface_tangential_alignment_mean",
]


SUMMARY_KEYS = [
    "rows",
    "first_tick",
    "last_tick",
    "mean_active_turnover_fraction",
    "mean_active_interface_turnover_fraction",
    "mean_residual_participations_per_tick",
    "mean_deactivation_events_per_tick",
    "mean_rotation_events_per_tick",
    "mean_rotation_events_on_residual_entry_per_tick",
    "mean_rotation_events_on_secondary_exchange_per_tick",
    "mean_angular_momentum_updates_per_tick",
    "mean_angular_momentum_biased_rotation_events_per_tick",
    "mean_angular_momentum_secondary_bias_sources_per_tick",
    "mean_angular_momentum_secondary_bias_selected_candidates_per_tick",
    "mean_angular_momentum_mean_abs_active",
    "max_angular_momentum_max_abs",
    "mean_persistent_active_v_changed_fraction",
    "mean_persistent_interface_v_changed_fraction",
    "max_persistent_active_v_changed_fraction",
    "max_persistent_interface_v_changed_fraction",
    "mean_persistent_active_transition_entropy",
    "mean_persistent_interface_transition_entropy",
    "mean_persistent_active_changed_transition_entropy",
    "mean_persistent_interface_changed_transition_entropy",
    "mean_active_vector_entropy",
    "mean_active_interface_vector_entropy",
    "mean_new_active_vector_entropy",
    "mean_active_vector_dominant_fraction",
    "mean_active_interface_vector_dominant_fraction",
    "mean_new_active_source_vector_match_fraction",
    "mean_persistent_active_candidate_turnover",
    "mean_persistent_interface_candidate_turnover",
    "mean_active_candidate_target_turnover",
    "mean_active_interface_candidate_target_turnover",
    "mean_interface_radial_alignment",
    "mean_interface_tangential_alignment",
]


@dataclass(frozen=True)
class CandidateContext:
    vectors: np.ndarray
    vector_behaviors: tuple[str, ...]
    wrap: bool
    size: int
    valence: int
    neighbor_mode: str
    decay_mode: str
    residual_participation_probability: float
    residual_participation_secondary_only: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure rotational recursion and candidate-neighborhood novelty."
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--ticks", type=int, default=None)
    parser.add_argument("--sample-every", type=int, default=1)
    parser.add_argument("--sample-ticks", type=int, nargs="+", default=None)
    parser.add_argument("--connectivity", choices=["face6", "face18", "cube26"], default="cube26")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--stop-active-iotas", type=int, default=0)
    return parser.parse_args()


def configure(args: argparse.Namespace) -> dict[str, Any]:
    config = copy.deepcopy(load_config(args.config))
    if args.seed is not None:
        config.setdefault("init", {})["seed"] = int(args.seed)
    return config


def sample_schedule(args: argparse.Namespace, ticks: int) -> list[int]:
    if args.sample_ticks:
        values = sorted({int(value) for value in args.sample_ticks})
        return [value for value in values if 0 <= value <= ticks]
    if int(args.sample_every) <= 0:
        raise SystemExit("--sample-every must be positive")
    values = list(range(0, ticks + 1, int(args.sample_every)))
    if values[-1] != ticks:
        values.append(ticks)
    return values


def entropy_from_counter(counter: Counter[Any]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counter.values():
        if count <= 0:
            continue
        probability = count / total
        entropy -= probability * math.log2(probability)
    return float(entropy)


def entropy_for_values(values: np.ndarray, minlength: int | None = None) -> tuple[float, float]:
    if values.size == 0:
        return 0.0, 0.0
    if minlength is None:
        counts = Counter(int(value) for value in values.tolist())
        total = sum(counts.values())
        dominant_fraction = max(counts.values()) / total if total else 0.0
        return entropy_from_counter(counts), float(dominant_fraction)
    counts_array = np.bincount(values.astype(np.int64), minlength=minlength)
    total = int(np.sum(counts_array))
    if total <= 0:
        return 0.0, 0.0
    probabilities = counts_array[counts_array > 0].astype(np.float64) / total
    entropy = float(-np.sum(probabilities * np.log2(probabilities)))
    dominant_fraction = float(np.max(counts_array) / total)
    return entropy, dominant_fraction


def vector_step_for_snapshot(
    snapshot: Snapshot,
    context: CandidateContext,
    coord: tuple[int, int, int],
) -> tuple[int, int, int, str]:
    x_coord, y_coord, z_coord = coord
    vector_index = int(snapshot.V[x_coord, y_coord, z_coord]) % len(context.vectors)
    amplitude = int(snapshot.A[x_coord, y_coord, z_coord])
    reach = int(snapshot.R[x_coord, y_coord, z_coord])
    payload = int(snapshot.P[x_coord, y_coord, z_coord])
    behavior = context.vector_behaviors[vector_index]
    dx_value, dy_value, dz_value = context.vectors[vector_index]
    if behavior == "reflect":
        return -int(dx_value), -int(dy_value), -int(dz_value), behavior
    if behavior == "diffuse":
        diffuse_index = (vector_index + amplitude + reach + payload) % len(context.vectors)
        diffuse_dx, diffuse_dy, diffuse_dz = context.vectors[diffuse_index]
        return int(diffuse_dx), int(diffuse_dy), int(diffuse_dz), behavior
    return int(dx_value), int(dy_value), int(dz_value), behavior


def target_for_step(
    coord: tuple[int, int, int],
    step_vector: tuple[int, int, int],
    context: CandidateContext,
) -> tuple[int, int, int] | None:
    x_coord, y_coord, z_coord = coord
    dx_value, dy_value, dz_value = step_vector
    target_x = x_coord + dx_value
    target_y = y_coord + dy_value
    target_z = z_coord + dz_value
    if context.wrap:
        return target_x % context.size, target_y % context.size, target_z % context.size
    if not (0 <= target_x < context.size and 0 <= target_y < context.size and 0 <= target_z < context.size):
        return None
    return target_x, target_y, target_z


def candidate_targets_for_coord(
    snapshot: Snapshot,
    context: CandidateContext,
    coord: tuple[int, int, int],
) -> frozenset[tuple[int, int, int]]:
    x_coord, y_coord, z_coord = coord
    amplitude = int(snapshot.A[x_coord, y_coord, z_coord])
    reach = int(snapshot.R[x_coord, y_coord, z_coord])
    if amplitude <= 0 or reach <= 0 or context.valence <= 0:
        return frozenset()

    primary = vector_step_for_snapshot(snapshot, context, coord)
    candidate_steps: list[tuple[int, int, int, str]] = [primary]
    seen_steps = {primary[:3]}
    if context.valence > 1:
        behavior = primary[3]
        for raw_step in candidate_neighbor_steps(context.neighbor_mode):
            step_key = tuple(int(value) for value in raw_step)
            if step_key in seen_steps:
                continue
            seen_steps.add(step_key)
            distance = math.sqrt(sum(value * value for value in step_key))
            if distance <= max(reach, 1):
                candidate_steps.append((*step_key, behavior))

    candidates: list[tuple[float, int, tuple[int, int, int]]] = []
    seen_targets: set[tuple[int, int, int]] = set()
    for order, (dx_value, dy_value, dz_value, behavior) in enumerate(candidate_steps):
        target = target_for_step(coord, (dx_value, dy_value, dz_value), context)
        if target is None or target in seen_targets:
            continue
        if (
            bool(snapshot.depleted[target])
            and context.residual_participation_probability <= 0.0
        ):
            continue
        if (
            bool(snapshot.depleted[target])
            and context.residual_participation_secondary_only
            and order == 0
        ):
            continue
        seen_targets.add(target)
        distance = math.sqrt(dx_value**2 + dy_value**2 + dz_value**2)
        influence = (amplitude / 7.0) * decay(distance, reach, context.decay_mode)
        if behavior == "diffuse":
            influence *= 0.5
        if influence <= 0:
            continue
        candidates.append((float(influence), int(order), target))

    candidates.sort(key=lambda row: (-row[0], row[1]))
    primary_targets = [target for _, order, target in candidates if order == 0]
    selected: list[tuple[int, int, int]] = []
    if primary_targets:
        selected.append(primary_targets[0])
    additional_slots = max(0, int(context.valence) - len(selected))
    for _, order, target in candidates:
        if order == 0:
            continue
        if len(selected) >= additional_slots + (1 if primary_targets else 0):
            break
        selected.append(target)
    return frozenset(selected)


def coords_for_mask(mask: np.ndarray) -> list[tuple[int, int, int]]:
    return [tuple(int(value) for value in coord) for coord in np.argwhere(mask)]


def candidate_union_for_mask(
    snapshot: Snapshot,
    context: CandidateContext,
    mask: np.ndarray,
) -> set[tuple[int, int, int]]:
    targets: set[tuple[int, int, int]] = set()
    for coord in coords_for_mask(mask):
        targets.update(candidate_targets_for_coord(snapshot, context, coord))
    return targets


def jaccard(previous: set[Any] | frozenset[Any], current: set[Any] | frozenset[Any]) -> float:
    union_count = len(previous | current)
    if union_count == 0:
        return 1.0
    return float(len(previous & current) / union_count)


def mean_candidate_jaccard(
    previous: Snapshot,
    current: Snapshot,
    context: CandidateContext,
    mask: np.ndarray,
) -> tuple[float, float]:
    values: list[float] = []
    for coord in coords_for_mask(mask):
        previous_targets = candidate_targets_for_coord(previous, context, coord)
        current_targets = candidate_targets_for_coord(current, context, coord)
        values.append(jaccard(previous_targets, current_targets))
    if not values:
        return 1.0, 0.0
    mean_jaccard = float(np.mean(values))
    return mean_jaccard, float(1.0 - mean_jaccard)


def transition_stats(
    previous: Snapshot,
    current: Snapshot,
    mask: np.ndarray,
) -> dict[str, float]:
    cells = int(np.count_nonzero(mask))
    if cells <= 0:
        return {
            "cells": 0.0,
            "changed": 0.0,
            "changed_fraction": 0.0,
            "transition_entropy": 0.0,
            "changed_transition_entropy": 0.0,
        }
    previous_vectors = previous.V[mask].astype(np.int64)
    current_vectors = current.V[mask].astype(np.int64)
    changed_mask = previous_vectors != current_vectors
    transition_counter = Counter(zip(previous_vectors.tolist(), current_vectors.tolist(), strict=False))
    changed_counter = Counter(
        zip(previous_vectors[changed_mask].tolist(), current_vectors[changed_mask].tolist(), strict=False)
    )
    changed = int(np.count_nonzero(changed_mask))
    return {
        "cells": float(cells),
        "changed": float(changed),
        "changed_fraction": fraction(changed, cells),
        "transition_entropy": entropy_from_counter(transition_counter),
        "changed_transition_entropy": entropy_from_counter(changed_counter),
    }


def source_vector_match_fraction(
    previous: Snapshot,
    current: Snapshot,
    context: CandidateContext,
    new_active_mask: np.ndarray,
) -> float:
    new_coords = coords_for_mask(new_active_mask)
    if not new_coords:
        return 0.0
    previous_active_coords = coords_for_mask(previous.active)
    source_vector_by_target: dict[tuple[int, int, int], set[int]] = {coord: set() for coord in new_coords}
    new_coord_set = set(new_coords)
    for source_coord in previous_active_coords:
        source_targets = candidate_targets_for_coord(previous, context, source_coord)
        overlap_targets = source_targets & new_coord_set
        if not overlap_targets:
            continue
        source_vector = int(previous.V[source_coord]) % len(context.vectors)
        for target in overlap_targets:
            source_vector_by_target[target].add(source_vector)
    matched = 0
    for coord in new_coords:
        current_vector = int(current.V[coord]) % len(context.vectors)
        if current_vector in source_vector_by_target.get(coord, set()):
            matched += 1
    return fraction(matched, len(new_coords))


def interface_alignment(
    snapshot: Snapshot,
    context: CandidateContext,
    connectivity: str,
) -> tuple[float, float]:
    neighbor_steps = [tuple(int(value) for value in step_values) for step_values in candidate_neighbor_steps(connectivity)]
    radial_values: list[float] = []
    tangential_values: list[float] = []
    for coord in coords_for_mask(snapshot.active_interface):
        active_step = vector_step_for_snapshot(snapshot, context, coord)[:3]
        step_norm = math.sqrt(sum(value * value for value in active_step))
        if step_norm == 0.0:
            continue
        radial_vectors: list[np.ndarray] = []
        for neighbor_step in neighbor_steps:
            target = target_for_step(coord, neighbor_step, context)
            if target is not None and bool(snapshot.depleted[target]):
                radial_vectors.append(np.array(neighbor_step, dtype=np.float64))
        if not radial_vectors:
            continue
        radial = np.mean(radial_vectors, axis=0)
        radial_norm = float(np.linalg.norm(radial))
        if radial_norm == 0.0:
            continue
        step_vector = np.array(active_step, dtype=np.float64)
        alignment = float(np.dot(step_vector, radial) / (step_norm * radial_norm))
        alignment = max(-1.0, min(1.0, alignment))
        radial_values.append(alignment)
        tangential_values.append(math.sqrt(max(0.0, 1.0 - alignment * alignment)))
    if not radial_values:
        return 0.0, 0.0
    return float(np.mean(radial_values)), float(np.mean(tangential_values))


def metric_from_world(world: Any, extras: dict[str, float]) -> dict[str, float]:
    active = world.active
    inactive = ~active
    active_amplitude = int(np.sum(world.A[active], dtype=np.int64))
    latent_amplitude = int(np.sum(world.latent_A[inactive], dtype=np.int64))
    total_amplitude = active_amplitude + latent_amplitude
    metric = {
        "active_iotas": float(np.count_nonzero(active)),
        "depleted_cells": float(np.count_nonzero(inactive & (world.latent_A == 0))),
        "total_A": float(total_amplitude),
        "ledger_error": float(total_amplitude - int(world.initial_total_A)),
    }
    for key in COUNT_KEYS:
        metric[key] = float(extras.get(key, 0.0))
    angular_L = getattr(world, "angular_L", None)
    if angular_L is not None:
        abs_L = np.abs(angular_L)
        active_abs_L = abs_L[active]
        active_L = angular_L[active]
        metric["angular_momentum_nonzero_cells"] = float(np.count_nonzero(abs_L > 1e-6))
        metric["angular_momentum_mean_abs_active"] = float(active_abs_L.mean()) if active_abs_L.size else 0.0
        metric["angular_momentum_mean_signed_active"] = float(active_L.mean()) if active_L.size else 0.0
        metric["angular_momentum_max_abs"] = float(abs_L.max()) if abs_L.size else 0.0
    else:
        metric["angular_momentum_nonzero_cells"] = 0.0
        metric["angular_momentum_mean_abs_active"] = 0.0
        metric["angular_momentum_mean_signed_active"] = 0.0
        metric["angular_momentum_max_abs"] = 0.0
    return metric


def row_for_snapshots(
    previous: Snapshot,
    current: Snapshot,
    context: CandidateContext,
    metric: dict[str, float],
    connectivity: str,
) -> dict[str, Any]:
    active_delta = mask_delta("active", previous.active, current.active)
    interface_delta = mask_delta("active_interface", previous.active_interface, current.active_interface)
    persistent_active = previous.active & current.active
    persistent_interface = previous.active_interface & current.active_interface
    new_active = current.active & ~previous.active

    active_transition = transition_stats(previous, current, persistent_active)
    interface_transition = transition_stats(previous, current, persistent_interface)
    active_entropy, active_dominant = entropy_for_values(current.V[current.active], len(context.vectors))
    interface_entropy, interface_dominant = entropy_for_values(
        current.V[current.active_interface],
        len(context.vectors),
    )
    new_entropy, new_dominant = entropy_for_values(current.V[new_active], len(context.vectors))
    previous_active_targets = candidate_union_for_mask(previous, context, previous.active)
    current_active_targets = candidate_union_for_mask(current, context, current.active)
    previous_interface_targets = candidate_union_for_mask(previous, context, previous.active_interface)
    current_interface_targets = candidate_union_for_mask(current, context, current.active_interface)
    active_candidate_jaccard = jaccard(previous_active_targets, current_active_targets)
    interface_candidate_jaccard = jaccard(previous_interface_targets, current_interface_targets)
    persistent_active_candidate_jaccard, persistent_active_candidate_turnover = mean_candidate_jaccard(
        previous,
        current,
        context,
        persistent_active,
    )
    persistent_interface_candidate_jaccard, persistent_interface_candidate_turnover = mean_candidate_jaccard(
        previous,
        current,
        context,
        persistent_interface,
    )
    radial_alignment, tangential_alignment = interface_alignment(current, context, connectivity)
    window_ticks = current.tick - previous.tick
    return {
        "tick": current.tick,
        "previous_tick": previous.tick,
        "window_ticks": window_ticks,
        "active_iotas": int(metric["active_iotas"]),
        "depleted_cells": int(metric["depleted_cells"]),
        "active_interface_cells": int(np.count_nonzero(current.active_interface)),
        "amplitude_transfers": float(metric.get("amplitude_transfers", 0.0)),
        "deactivation_events": float(metric.get("deactivation_events", 0.0)),
        "residual_participations": float(metric.get("residual_participations", metric.get("depleted_reactivations", 0.0))),
        "rotation_events": float(metric.get("rotation_events", 0.0)),
        "rotation_events_on_residual_entry": float(metric.get("rotation_events_on_residual_entry", 0.0)),
        "rotation_events_on_secondary_exchange": float(metric.get("rotation_events_on_secondary_exchange", 0.0)),
        "angular_momentum_updates": float(metric.get("angular_momentum_updates", 0.0)),
        "angular_momentum_biased_rotation_events": float(
            metric.get("angular_momentum_biased_rotation_events", 0.0)
        ),
        "angular_momentum_bias_abs_sum": float(metric.get("angular_momentum_bias_abs_sum", 0.0)),
        "angular_momentum_observed_turn_abs_sum": float(
            metric.get("angular_momentum_observed_turn_abs_sum", 0.0)
        ),
        "angular_momentum_secondary_bias_sources": float(
            metric.get("angular_momentum_secondary_bias_sources", 0.0)
        ),
        "angular_momentum_secondary_bias_selected_candidates": float(
            metric.get("angular_momentum_secondary_bias_selected_candidates", 0.0)
        ),
        "angular_momentum_nonzero_cells": float(metric.get("angular_momentum_nonzero_cells", 0.0)),
        "angular_momentum_mean_abs_active": float(metric.get("angular_momentum_mean_abs_active", 0.0)),
        "angular_momentum_mean_signed_active": float(metric.get("angular_momentum_mean_signed_active", 0.0)),
        "angular_momentum_max_abs": float(metric.get("angular_momentum_max_abs", 0.0)),
        "amplitude_transfers_per_tick": fraction(metric.get("amplitude_transfers", 0.0), window_ticks),
        "deactivation_events_per_tick": fraction(metric.get("deactivation_events", 0.0), window_ticks),
        "residual_participations_per_tick": fraction(
            metric.get("residual_participations", metric.get("depleted_reactivations", 0.0)),
            window_ticks,
        ),
        "rotation_events_per_tick": fraction(metric.get("rotation_events", 0.0), window_ticks),
        "rotation_events_on_residual_entry_per_tick": fraction(
            metric.get("rotation_events_on_residual_entry", 0.0),
            window_ticks,
        ),
        "rotation_events_on_secondary_exchange_per_tick": fraction(
            metric.get("rotation_events_on_secondary_exchange", 0.0),
            window_ticks,
        ),
        "angular_momentum_updates_per_tick": fraction(metric.get("angular_momentum_updates", 0.0), window_ticks),
        "angular_momentum_biased_rotation_events_per_tick": fraction(
            metric.get("angular_momentum_biased_rotation_events", 0.0),
            window_ticks,
        ),
        "angular_momentum_secondary_bias_sources_per_tick": fraction(
            metric.get("angular_momentum_secondary_bias_sources", 0.0),
            window_ticks,
        ),
        "angular_momentum_secondary_bias_selected_candidates_per_tick": fraction(
            metric.get("angular_momentum_secondary_bias_selected_candidates", 0.0),
            window_ticks,
        ),
        "active_new_cells": active_delta["active_new_cells"],
        "active_lost_cells": active_delta["active_lost_cells"],
        "active_turnover_fraction": active_delta["active_turnover_fraction"],
        "active_interface_new_cells": interface_delta["active_interface_new_cells"],
        "active_interface_lost_cells": interface_delta["active_interface_lost_cells"],
        "active_interface_turnover_fraction": interface_delta["active_interface_turnover_fraction"],
        "persistent_active_cells": active_transition["cells"],
        "persistent_active_v_changed": active_transition["changed"],
        "persistent_active_v_changed_fraction": active_transition["changed_fraction"],
        "persistent_active_transition_entropy": active_transition["transition_entropy"],
        "persistent_active_changed_transition_entropy": active_transition["changed_transition_entropy"],
        "persistent_active_candidate_turnover_mean": persistent_active_candidate_turnover,
        "persistent_active_candidate_jaccard_mean": persistent_active_candidate_jaccard,
        "persistent_interface_cells": interface_transition["cells"],
        "persistent_interface_v_changed": interface_transition["changed"],
        "persistent_interface_v_changed_fraction": interface_transition["changed_fraction"],
        "persistent_interface_transition_entropy": interface_transition["transition_entropy"],
        "persistent_interface_changed_transition_entropy": interface_transition["changed_transition_entropy"],
        "persistent_interface_candidate_turnover_mean": persistent_interface_candidate_turnover,
        "persistent_interface_candidate_jaccard_mean": persistent_interface_candidate_jaccard,
        "active_vector_entropy": active_entropy,
        "active_vector_dominant_fraction": active_dominant,
        "active_interface_vector_entropy": interface_entropy,
        "active_interface_vector_dominant_fraction": interface_dominant,
        "new_active_vector_entropy": new_entropy,
        "new_active_vector_dominant_fraction": new_dominant,
        "new_active_source_vector_match_fraction": source_vector_match_fraction(previous, current, context, new_active),
        "active_candidate_targets_previous": len(previous_active_targets),
        "active_candidate_targets_current": len(current_active_targets),
        "active_candidate_target_jaccard": active_candidate_jaccard,
        "active_candidate_target_turnover": 1.0 - active_candidate_jaccard,
        "active_interface_candidate_targets_previous": len(previous_interface_targets),
        "active_interface_candidate_targets_current": len(current_interface_targets),
        "active_interface_candidate_target_jaccard": interface_candidate_jaccard,
        "active_interface_candidate_target_turnover": 1.0 - interface_candidate_jaccard,
        "interface_radial_alignment_mean": radial_alignment,
        "interface_tangential_alignment_mean": tangential_alignment,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})
        handle.flush()
        os.fsync(handle.fileno())


def mean_for(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row.get(key, 0.0) or 0.0) for row in rows]
    return float(np.mean(values)) if values else 0.0


def max_for(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row.get(key, 0.0) or 0.0) for row in rows]
    return float(np.max(values)) if values else 0.0


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {key: 0.0 for key in SUMMARY_KEYS}
    return {
        "rows": len(rows),
        "first_tick": int(rows[0]["tick"]),
        "last_tick": int(rows[-1]["tick"]),
        "mean_active_turnover_fraction": mean_for(rows, "active_turnover_fraction"),
        "mean_active_interface_turnover_fraction": mean_for(rows, "active_interface_turnover_fraction"),
        "mean_residual_participations_per_tick": mean_for(rows, "residual_participations_per_tick"),
        "mean_deactivation_events_per_tick": mean_for(rows, "deactivation_events_per_tick"),
        "mean_rotation_events_per_tick": mean_for(rows, "rotation_events_per_tick"),
        "mean_rotation_events_on_residual_entry_per_tick": mean_for(
            rows,
            "rotation_events_on_residual_entry_per_tick",
        ),
        "mean_rotation_events_on_secondary_exchange_per_tick": mean_for(
            rows,
            "rotation_events_on_secondary_exchange_per_tick",
        ),
        "mean_angular_momentum_updates_per_tick": mean_for(rows, "angular_momentum_updates_per_tick"),
        "mean_angular_momentum_biased_rotation_events_per_tick": mean_for(
            rows,
            "angular_momentum_biased_rotation_events_per_tick",
        ),
        "mean_angular_momentum_secondary_bias_sources_per_tick": mean_for(
            rows,
            "angular_momentum_secondary_bias_sources_per_tick",
        ),
        "mean_angular_momentum_secondary_bias_selected_candidates_per_tick": mean_for(
            rows,
            "angular_momentum_secondary_bias_selected_candidates_per_tick",
        ),
        "mean_angular_momentum_mean_abs_active": mean_for(rows, "angular_momentum_mean_abs_active"),
        "max_angular_momentum_max_abs": max_for(rows, "angular_momentum_max_abs"),
        "mean_persistent_active_v_changed_fraction": mean_for(rows, "persistent_active_v_changed_fraction"),
        "mean_persistent_interface_v_changed_fraction": mean_for(rows, "persistent_interface_v_changed_fraction"),
        "max_persistent_active_v_changed_fraction": max_for(rows, "persistent_active_v_changed_fraction"),
        "max_persistent_interface_v_changed_fraction": max_for(rows, "persistent_interface_v_changed_fraction"),
        "mean_persistent_active_transition_entropy": mean_for(rows, "persistent_active_transition_entropy"),
        "mean_persistent_interface_transition_entropy": mean_for(rows, "persistent_interface_transition_entropy"),
        "mean_persistent_active_changed_transition_entropy": mean_for(
            rows,
            "persistent_active_changed_transition_entropy",
        ),
        "mean_persistent_interface_changed_transition_entropy": mean_for(
            rows,
            "persistent_interface_changed_transition_entropy",
        ),
        "mean_active_vector_entropy": mean_for(rows, "active_vector_entropy"),
        "mean_active_interface_vector_entropy": mean_for(rows, "active_interface_vector_entropy"),
        "mean_new_active_vector_entropy": mean_for(rows, "new_active_vector_entropy"),
        "mean_active_vector_dominant_fraction": mean_for(rows, "active_vector_dominant_fraction"),
        "mean_active_interface_vector_dominant_fraction": mean_for(rows, "active_interface_vector_dominant_fraction"),
        "mean_new_active_source_vector_match_fraction": mean_for(rows, "new_active_source_vector_match_fraction"),
        "mean_persistent_active_candidate_turnover": mean_for(rows, "persistent_active_candidate_turnover_mean"),
        "mean_persistent_interface_candidate_turnover": mean_for(rows, "persistent_interface_candidate_turnover_mean"),
        "mean_active_candidate_target_turnover": mean_for(rows, "active_candidate_target_turnover"),
        "mean_active_interface_candidate_target_turnover": mean_for(rows, "active_interface_candidate_target_turnover"),
        "mean_interface_radial_alignment": mean_for(rows, "interface_radial_alignment_mean"),
        "mean_interface_tangential_alignment": mean_for(rows, "interface_tangential_alignment_mean"),
    }


def main() -> None:
    args = parse_args()
    config = configure(args)
    ticks = int(args.ticks if args.ticks is not None else config.get("run", {}).get("ticks", 2048))
    sample_ticks = sample_schedule(args, ticks)
    if len(sample_ticks) < 2:
        raise SystemExit("at least two sample ticks are required")
    sample_tick_set = set(sample_ticks)
    output_prefix = Path(args.output_prefix)
    rows_path = output_prefix.with_name(output_prefix.name + "_rows.csv")
    summary_path = output_prefix.with_name(output_prefix.name + "_summary.json")

    constants = config.get("constants", {})
    world = init_world(config)
    context = CandidateContext(
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
    previous_snapshot: Snapshot | None = None
    pending_extras: dict[str, float] = {}
    rows: list[dict[str, Any]] = []
    final_tick = ticks
    early_stop_reason = ""

    for tick in range(0, ticks + 1):
        if tick in sample_tick_set:
            current_snapshot = take_snapshot(world, tick, args.connectivity)
            if previous_snapshot is not None:
                metric = metric_from_world(world, pending_extras)
                rows.append(
                    row_for_snapshots(
                        previous_snapshot,
                        current_snapshot,
                        context,
                        metric,
                        args.connectivity,
                    )
                )
                pending_extras = {}
            else:
                pending_extras = {}
            previous_snapshot = current_snapshot
        if tick == ticks:
            break
        extras = step(world, config)
        accumulate_counts(pending_extras, extras)
        active_count = int(world.active.sum())
        if int(args.stop_active_iotas) > 0 and active_count >= int(args.stop_active_iotas):
            final_tick = tick + 1
            early_stop_reason = f"active_iotas >= {args.stop_active_iotas}"
            break

    write_csv(rows_path, rows)
    payload = {
        "config_path": args.config,
        "output_prefix": output_prefix.as_posix(),
        "rows_path": rows_path.as_posix(),
        "sample_ticks": sample_ticks,
        "final_tick": final_tick,
        "early_stop_reason": early_stop_reason,
        "connectivity": args.connectivity,
        "summary": summarize(rows),
        "final_row": rows[-1] if rows else {},
    }
    summary_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
