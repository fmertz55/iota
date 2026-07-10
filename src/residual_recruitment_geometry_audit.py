from __future__ import annotations

import argparse
import copy
import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from iota_rig import (
    World,
    angular_momentum_residual_score,
    candidate_neighbor_steps,
    classify_residual_target_geometry,
    clamp_probability,
    init_world,
    load_config,
    local_candidates,
    step,
)
from metrics import collect_metrics


CLASS_FIELDNAMES = [
    "tick",
    "class",
    "eligible_candidates",
    "unique_targets",
    "base_probability_sum",
    "biased_probability_sum",
    "base_probability_share",
    "biased_probability_share",
    "selection_lift",
    "score_sum",
    "score_mean",
    "base_weighted_score_mean",
    "biased_weighted_score_mean",
    "multiplier_sum",
    "multiplier_mean",
    "multiplier_max",
    "positive_bias_candidates",
    "negative_bias_candidates",
    "neutral_bias_candidates",
    "face6_neighbor_mean",
    "face18_neighbor_mean",
    "cube26_neighbor_mean",
    "face6_component_mean",
    "cube26_component_mean",
]

TICK_FIELDNAMES = [
    "tick",
    "active_iotas",
    "depleted_cells",
    "depleted_interface_sites",
    "eligible_candidates",
    "unique_targets",
    "base_probability_sum",
    "biased_probability_sum",
    "probability_delta",
    "positive_bias_candidates",
    "negative_bias_candidates",
    "neutral_bias_candidates",
    "component_bridge_cube26_targets",
    "local_bridge_face6_targets",
    "tip_seed_targets",
    "flat_front_targets",
    "concave_fill_targets",
    "mean_score",
    "base_weighted_score_mean",
    "biased_weighted_score_mean",
    "mean_multiplier",
    "max_multiplier",
    "largest_coherence_cube26",
    "coherence_count_cube26",
    "component_size_entropy_cube26",
    "ledger_error",
]

TARGET_FIELDNAMES = [
    "tick",
    "target_x",
    "target_y",
    "target_z",
    "class",
    "eligible_candidate_count",
    "base_probability_sum",
    "biased_probability_sum",
    "max_multiplier",
    "max_score",
    "face6_neighbors",
    "face18_neighbors",
    "cube26_neighbors",
    "face6_components",
    "cube26_components",
    "is_component_bridge_cube26",
    "is_local_bridge_face6",
    "is_tip_seed",
    "is_flat_front",
    "is_concave_fill",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit residual-recruitment geometry opportunities and contrast bias."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--ticks", type=int, default=None)
    parser.add_argument("--sample-every", type=int, default=16)
    parser.add_argument("--sample-ticks", type=int, nargs="+", default=None)
    parser.add_argument("--connectivity", choices=["face6", "face18", "cube26"], default="cube26")
    parser.add_argument("--target-limit", type=int, default=0, help="Write top N targets per tick; 0 writes all.")
    parser.add_argument("--stop-active-iotas", type=int, default=0)
    return parser.parse_args()


def sample_schedule(args: argparse.Namespace, ticks: int) -> list[int]:
    if args.sample_ticks:
        values = sorted({int(value) for value in args.sample_ticks})
    else:
        if int(args.sample_every) <= 0:
            raise SystemExit("--sample-every must be positive")
        values = list(range(0, ticks + 1, int(args.sample_every)))
    values = [value for value in values if 0 <= value <= ticks]
    if 0 not in values:
        values.insert(0, 0)
    if ticks not in values:
        values.append(ticks)
    return sorted(set(values))


def shifted_mask(mask: np.ndarray, delta: tuple[int, int, int], wrap: bool) -> np.ndarray:
    if wrap:
        return np.roll(mask, shift=tuple(-value for value in delta), axis=(0, 1, 2))

    size = int(mask.shape[0])
    output = np.zeros_like(mask, dtype=bool)
    source_slices: list[slice] = []
    target_slices: list[slice] = []
    for offset in delta:
        if offset > 0:
            source_slices.append(slice(0, size - offset))
            target_slices.append(slice(offset, size))
        elif offset < 0:
            source_slices.append(slice(-offset, size))
            target_slices.append(slice(0, size + offset))
        else:
            source_slices.append(slice(None))
            target_slices.append(slice(None))
    output[tuple(source_slices)] = mask[tuple(target_slices)]
    return output


def adjacent_to_mask(mask: np.ndarray, connectivity: str, wrap: bool) -> np.ndarray:
    adjacent = np.zeros_like(mask, dtype=bool)
    for raw_delta in candidate_neighbor_steps(connectivity):
        delta = tuple(int(value) for value in raw_delta)
        adjacent |= shifted_mask(mask, delta, wrap)
    return adjacent


def active_neighbor_coords(
    world: World,
    target: tuple[int, int, int],
    connectivity: str,
) -> list[tuple[int, int, int]]:
    size = world.size
    tx, ty, tz = target
    coords: list[tuple[int, int, int]] = []
    for raw_delta in candidate_neighbor_steps(connectivity):
        dx, dy, dz = (int(value) for value in raw_delta)
        nx, ny, nz = tx + dx, ty + dy, tz + dz
        if world.wrap:
            nx %= size
            ny %= size
            nz %= size
        elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
            continue
        if bool(world.active[nx, ny, nz]):
            coords.append((nx, ny, nz))
    return coords


def local_component_count(
    coords: list[tuple[int, int, int]],
    connectivity: str,
    size: int,
    wrap: bool,
) -> int:
    remaining = set(coords)
    if not remaining:
        return 0
    neighbors = tuple(
        (int(dx), int(dy), int(dz))
        for dx, dy, dz in candidate_neighbor_steps(connectivity)
    )
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            x, y, z = stack.pop()
            for dx, dy, dz in neighbors:
                nx, ny, nz = x + dx, y + dy, z + dz
                if wrap:
                    nx %= size
                    ny %= size
                    nz %= size
                elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
                    continue
                neighbor = (nx, ny, nz)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def classify_target_geometry(
    world: World,
    target: tuple[int, int, int],
) -> dict[str, Any]:
    return classify_residual_target_geometry(world, target)


def legacy_classify_target_geometry(
    world: World,
    target: tuple[int, int, int],
) -> dict[str, Any]:
    face6_coords = active_neighbor_coords(world, target, "face6")
    face18_coords = active_neighbor_coords(world, target, "face18")
    cube26_coords = active_neighbor_coords(world, target, "cube26")
    face6_count = len(face6_coords)
    face18_count = len(face18_coords)
    cube26_count = len(cube26_coords)
    face6_components = local_component_count(face6_coords, "face6", world.size, world.wrap)
    cube26_components = local_component_count(cube26_coords, "cube26", world.size, world.wrap)

    is_component_bridge_cube26 = cube26_components >= 2
    is_local_bridge_face6 = face6_components >= 2
    is_tip_seed = cube26_count <= 2
    is_flat_front = face6_count == 1 and cube26_count >= 9
    is_concave_fill = face6_count >= 4 or cube26_count >= 18

    if is_component_bridge_cube26:
        class_name = "component_bridge_cube26"
    elif is_local_bridge_face6:
        class_name = "local_bridge_face6"
    elif is_concave_fill:
        class_name = "concave_fill"
    elif is_tip_seed:
        class_name = "tip_seed"
    elif face6_count == 0:
        class_name = "diagonal_shear"
    elif is_flat_front:
        class_name = "flat_front"
    elif face6_count == 1:
        class_name = "edge_extension"
    elif face6_count in {2, 3}:
        class_name = "ridge_or_corner_fill"
    else:
        class_name = "interface_fill"

    return {
        "class": class_name,
        "face6_neighbors": face6_count,
        "face18_neighbors": face18_count,
        "cube26_neighbors": cube26_count,
        "face6_components": face6_components,
        "cube26_components": cube26_components,
        "is_component_bridge_cube26": is_component_bridge_cube26,
        "is_local_bridge_face6": is_local_bridge_face6,
        "is_tip_seed": is_tip_seed,
        "is_flat_front": is_flat_front,
        "is_concave_fill": is_concave_fill,
    }


def weighted_mean(total: float, weight: float) -> float:
    return float(total / weight) if weight else 0.0


def new_bucket() -> dict[str, Any]:
    return {
        "eligible_candidates": 0.0,
        "targets": set(),
        "base_probability_sum": 0.0,
        "biased_probability_sum": 0.0,
        "score_sum": 0.0,
        "score_max": -1.0e30,
        "base_weighted_score_sum": 0.0,
        "biased_weighted_score_sum": 0.0,
        "multiplier_sum": 0.0,
        "multiplier_max": 0.0,
        "positive_bias_candidates": 0.0,
        "negative_bias_candidates": 0.0,
        "neutral_bias_candidates": 0.0,
        "face6_neighbor_sum": 0.0,
        "face18_neighbor_sum": 0.0,
        "cube26_neighbor_sum": 0.0,
        "face6_component_sum": 0.0,
        "cube26_component_sum": 0.0,
    }


def add_entry(
    bucket: dict[str, Any],
    target: tuple[int, int, int],
    geometry: dict[str, Any],
    base_probability: float,
    biased_probability: float,
    score: float,
    multiplier: float,
) -> None:
    bucket["eligible_candidates"] += 1.0
    bucket["targets"].add(target)
    bucket["base_probability_sum"] += float(base_probability)
    bucket["biased_probability_sum"] += float(biased_probability)
    bucket["score_sum"] += float(score)
    bucket["score_max"] = max(float(bucket["score_max"]), float(score))
    bucket["base_weighted_score_sum"] += float(base_probability * score)
    bucket["biased_weighted_score_sum"] += float(biased_probability * score)
    bucket["multiplier_sum"] += float(multiplier)
    bucket["multiplier_max"] = max(float(bucket["multiplier_max"]), float(multiplier))
    if multiplier > 1.0 + 1e-12:
        bucket["positive_bias_candidates"] += 1.0
    elif multiplier < 1.0 - 1e-12:
        bucket["negative_bias_candidates"] += 1.0
    else:
        bucket["neutral_bias_candidates"] += 1.0
    bucket["face6_neighbor_sum"] += float(geometry["face6_neighbors"])
    bucket["face18_neighbor_sum"] += float(geometry["face18_neighbors"])
    bucket["cube26_neighbor_sum"] += float(geometry["cube26_neighbors"])
    bucket["face6_component_sum"] += float(geometry["face6_components"])
    bucket["cube26_component_sum"] += float(geometry["cube26_components"])


def bucket_row(
    tick: int,
    class_name: str,
    bucket: dict[str, Any],
    total_base: float,
    total_biased: float,
) -> dict[str, Any]:
    count = float(bucket["eligible_candidates"])
    base_sum = float(bucket["base_probability_sum"])
    biased_sum = float(bucket["biased_probability_sum"])
    unique_targets = bucket.get("unique_targets_override")
    if unique_targets is None:
        unique_targets = len(bucket["targets"])
    base_share = weighted_mean(base_sum, total_base)
    biased_share = weighted_mean(biased_sum, total_biased)
    return {
        "tick": int(tick),
        "class": class_name,
        "eligible_candidates": count,
        "unique_targets": unique_targets,
        "base_probability_sum": base_sum,
        "biased_probability_sum": biased_sum,
        "base_probability_share": base_share,
        "biased_probability_share": biased_share,
        "selection_lift": weighted_mean(biased_share, base_share),
        "score_sum": float(bucket["score_sum"]),
        "score_mean": weighted_mean(float(bucket["score_sum"]), count),
        "base_weighted_score_mean": weighted_mean(
            float(bucket["base_weighted_score_sum"]),
            base_sum,
        ),
        "biased_weighted_score_mean": weighted_mean(
            float(bucket["biased_weighted_score_sum"]),
            biased_sum,
        ),
        "multiplier_sum": float(bucket["multiplier_sum"]),
        "multiplier_mean": weighted_mean(float(bucket["multiplier_sum"]), count),
        "multiplier_max": float(bucket["multiplier_max"]),
        "positive_bias_candidates": float(bucket["positive_bias_candidates"]),
        "negative_bias_candidates": float(bucket["negative_bias_candidates"]),
        "neutral_bias_candidates": float(bucket["neutral_bias_candidates"]),
        "face6_neighbor_mean": weighted_mean(float(bucket["face6_neighbor_sum"]), count),
        "face18_neighbor_mean": weighted_mean(float(bucket["face18_neighbor_sum"]), count),
        "cube26_neighbor_mean": weighted_mean(float(bucket["cube26_neighbor_sum"]), count),
        "face6_component_mean": weighted_mean(float(bucket["face6_component_sum"]), count),
        "cube26_component_mean": weighted_mean(float(bucket["cube26_component_sum"]), count),
    }


def audit_tick(
    world: World,
    cfg: dict[str, Any],
    tick: int,
    connectivity: str,
    target_limit: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    constants = cfg.get("constants", {})
    kA = float(constants.get("amplitude_coupling", 0.125))
    decay_mode = str(constants.get("decay_mode", "inverse_square"))
    valence = max(1, int(constants.get("valence", 1)))
    bond_probability = clamp_probability(float(constants.get("bond_probability", 1.0)))
    neighbor_mode = str(constants.get("neighbor_mode", "cube26"))
    residual_probability = clamp_probability(
        float(
            constants.get(
                "residual_participation_probability",
                constants.get("depleted_reactivation_probability", 0.0),
            )
        )
    )
    residual_secondary_only = bool(
        constants.get(
            "residual_participation_secondary_only",
            constants.get("depleted_reactivation_secondary_only", True),
        )
    )
    angular_enabled = bool(constants.get("angular_momentum_enabled", False))
    angular_cap = max(0.0, float(constants.get("angular_momentum_cap", 0.0)))
    residual_bias_enabled = (
        angular_enabled
        and angular_cap > 0.0
        and bool(constants.get("angular_momentum_residual_bias_enabled", False))
    )
    strength = max(0.0, float(constants.get("angular_momentum_residual_bias_strength", 0.0)))
    residual_bias_enabled = residual_bias_enabled and strength > 0.0
    mean_preserving = bool(constants.get("angular_momentum_residual_bias_mean_preserving", True))
    preserve_behavior = bool(constants.get("angular_momentum_residual_bias_preserve_behavior", True))
    score_mode = str(constants.get("angular_momentum_residual_bias_score_mode", "source_L_alignment"))
    raw_geometry_weights = constants.get("angular_momentum_residual_geometry_weights", {})
    if raw_geometry_weights is None:
        raw_geometry_weights = {}
    if not isinstance(raw_geometry_weights, dict):
        raise ValueError("angular_momentum_residual_geometry_weights must be a mapping")
    geometry_classes = (
        "component_bridge_cube26",
        "local_bridge_face6",
        "flat_front",
        "edge_extension",
        "tip_seed",
        "diagonal_shear",
        "concave_fill",
        "ridge_or_corner_fill",
        "interface_fill",
    )
    geometry_weights = {
        class_name: float(
            constants.get(
                f"angular_momentum_residual_geometry_{class_name}_weight",
                raw_geometry_weights.get(class_name, 0.0),
            )
        )
        for class_name in geometry_classes
    }
    support_terms = (
        "cube26_neighbor_support",
        "face6_neighbor_support",
        "multi_component_support",
        "supported_bridge",
        "non_articulation_support",
        "dangling_articulation_risk",
        "source_neighbor_support",
        "source_amplitude_support",
        "source_exhaustion_risk",
        "source_articulation_risk",
    )
    for term in support_terms:
        geometry_weights[term] = float(
            constants.get(
                f"angular_momentum_residual_{term}_weight",
                raw_geometry_weights.get(term, 0.0),
            )
        )

    old_L = (
        world.angular_L.astype(np.float32, copy=True)
        if world.angular_L is not None
        else np.zeros(world.active.shape, dtype=np.float32)
    )
    next_active = world.active.copy()
    next_latent_A = world.latent_A.astype(np.int64, copy=True)
    depleted = (~world.active) & (world.latent_A == 0)
    depleted_interface = depleted & adjacent_to_mask(world.active, connectivity, world.wrap)
    metrics = collect_metrics(world, tick, {})

    class_buckets: dict[str, dict[str, Any]] = defaultdict(new_bucket)
    total_bucket = new_bucket()
    target_buckets: dict[tuple[int, int, int], dict[str, Any]] = defaultdict(new_bucket)
    target_geometry: dict[tuple[int, int, int], dict[str, Any]] = {}

    rng_state = copy.deepcopy(world.rng.bit_generator.state)
    try:
        for x, y, z in np.argwhere(world.active):
            a = int(world.A[x, y, z])
            r = int(world.R[x, y, z])
            if a <= 0 or r == 0:
                continue
            v_idx = int(world.V[x, y, z]) % len(world.vectors)
            p = int(world.P[x, y, z])
            candidates = local_candidates(
                world,
                int(x),
                int(y),
                int(z),
                v_idx,
                a,
                r,
                p,
                decay_mode,
                valence,
                bond_probability,
                neighbor_mode,
            )

            entries: list[tuple[dict[str, Any], float, float, float]] = []
            for candidate in candidates:
                tx, ty, tz = candidate["target"]
                target_depleted = (
                    not bool(next_active[tx, ty, tz])
                    and int(next_latent_A[tx, ty, tz]) <= 0
                )
                if not target_depleted:
                    continue
                if residual_probability <= 0.0:
                    continue
                if residual_secondary_only and int(candidate["order"]) == 0:
                    continue
                influence = float(candidate["influence"])
                if influence <= 0.0:
                    continue
                base_probability = clamp_probability(kA * influence) * residual_probability
                if base_probability <= 0.0:
                    continue
                score = (
                    angular_momentum_residual_score(
                        world,
                        old_L,
                        int(x),
                        int(y),
                        int(z),
                        v_idx,
                        a,
                        r,
                        p,
                        candidate,
                        angular_cap,
                        preserve_behavior,
                        score_mode,
                        geometry_weights,
                    )
                    if residual_bias_enabled
                    else 0.0
                )
                raw_multiplier = max(0.0, 1.0 + strength * score) if residual_bias_enabled else 1.0
                entries.append((candidate, base_probability, score, raw_multiplier))

            base_sum = sum(base_probability for _, base_probability, _, _ in entries)
            raw_biased_sum = sum(
                base_probability * raw_multiplier
                for _, base_probability, _, raw_multiplier in entries
            )
            normalizer = raw_biased_sum / base_sum if mean_preserving and base_sum > 0.0 else 1.0
            force_unbiased = False
            if normalizer <= 1e-12:
                normalizer = 1.0
                force_unbiased = True

            for candidate, base_probability, score, raw_multiplier in entries:
                multiplier = 1.0 if force_unbiased else raw_multiplier / normalizer
                biased_probability = base_probability * multiplier
                target = tuple(int(value) for value in candidate["target"])
                geometry = target_geometry.get(target)
                if geometry is None:
                    geometry = classify_target_geometry(world, target)
                    target_geometry[target] = geometry
                add_entry(
                    class_buckets[str(geometry["class"])],
                    target,
                    geometry,
                    base_probability,
                    biased_probability,
                    score,
                    multiplier,
                )
                add_entry(
                    target_buckets[target],
                    target,
                    geometry,
                    base_probability,
                    biased_probability,
                    score,
                    multiplier,
                )
                add_entry(
                    total_bucket,
                    target,
                    geometry,
                    base_probability,
                    biased_probability,
                    score,
                    multiplier,
                )
    finally:
        world.rng.bit_generator.state = rng_state

    total_base = float(total_bucket["base_probability_sum"])
    total_biased = float(total_bucket["biased_probability_sum"])
    class_rows = [
        bucket_row(tick, class_name, bucket, total_base, total_biased)
        for class_name, bucket in sorted(class_buckets.items())
    ]

    target_rows: list[dict[str, Any]] = []
    sorted_targets = sorted(
        target_buckets.items(),
        key=lambda item: float(item[1]["biased_probability_sum"]),
        reverse=True,
    )
    if target_limit > 0:
        sorted_targets = sorted_targets[:target_limit]
    for target, bucket in sorted_targets:
        geometry = target_geometry[target]
        target_rows.append(
            {
                "tick": int(tick),
                "target_x": target[0],
                "target_y": target[1],
                "target_z": target[2],
                "class": geometry["class"],
                "eligible_candidate_count": float(bucket["eligible_candidates"]),
                "base_probability_sum": float(bucket["base_probability_sum"]),
                "biased_probability_sum": float(bucket["biased_probability_sum"]),
                "max_multiplier": float(bucket["multiplier_max"]),
                "max_score": float(bucket["score_max"]),
                "face6_neighbors": geometry["face6_neighbors"],
                "face18_neighbors": geometry["face18_neighbors"],
                "cube26_neighbors": geometry["cube26_neighbors"],
                "face6_components": geometry["face6_components"],
                "cube26_components": geometry["cube26_components"],
                "is_component_bridge_cube26": geometry["is_component_bridge_cube26"],
                "is_local_bridge_face6": geometry["is_local_bridge_face6"],
                "is_tip_seed": geometry["is_tip_seed"],
                "is_flat_front": geometry["is_flat_front"],
                "is_concave_fill": geometry["is_concave_fill"],
            }
        )

    target_class_counts = Counter(str(geometry["class"]) for geometry in target_geometry.values())
    tick_row = {
        "tick": int(tick),
        "active_iotas": int(np.count_nonzero(world.active)),
        "depleted_cells": int(np.count_nonzero(depleted)),
        "depleted_interface_sites": int(np.count_nonzero(depleted_interface)),
        "eligible_candidates": float(total_bucket["eligible_candidates"]),
        "unique_targets": len(total_bucket["targets"]),
        "base_probability_sum": total_base,
        "biased_probability_sum": total_biased,
        "probability_delta": float(total_biased - total_base),
        "positive_bias_candidates": float(total_bucket["positive_bias_candidates"]),
        "negative_bias_candidates": float(total_bucket["negative_bias_candidates"]),
        "neutral_bias_candidates": float(total_bucket["neutral_bias_candidates"]),
        "component_bridge_cube26_targets": target_class_counts.get("component_bridge_cube26", 0),
        "local_bridge_face6_targets": target_class_counts.get("local_bridge_face6", 0),
        "tip_seed_targets": target_class_counts.get("tip_seed", 0),
        "flat_front_targets": target_class_counts.get("flat_front", 0),
        "concave_fill_targets": target_class_counts.get("concave_fill", 0),
        "mean_score": weighted_mean(float(total_bucket["score_sum"]), float(total_bucket["eligible_candidates"])),
        "base_weighted_score_mean": weighted_mean(
            float(total_bucket["base_weighted_score_sum"]),
            total_base,
        ),
        "biased_weighted_score_mean": weighted_mean(
            float(total_bucket["biased_weighted_score_sum"]),
            total_biased,
        ),
        "mean_multiplier": weighted_mean(
            float(total_bucket["multiplier_sum"]),
            float(total_bucket["eligible_candidates"]),
        ),
        "max_multiplier": float(total_bucket["multiplier_max"]),
        "largest_coherence_cube26": metrics.get("largest_coherence_cube26", 0),
        "coherence_count_cube26": metrics.get("coherence_count_cube26", 0),
        "component_size_entropy_cube26": metrics.get("component_size_entropy_cube26", 0.0),
        "ledger_error": metrics.get("ledger_error", 0.0),
    }
    return class_rows, tick_row, target_rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def aggregate_class_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = defaultdict(new_bucket)
    total_base = 0.0
    total_biased = 0.0
    for row in rows:
        class_name = str(row["class"])
        bucket = buckets[class_name]
        count = float(row["eligible_candidates"])
        base_sum = float(row["base_probability_sum"])
        biased_sum = float(row["biased_probability_sum"])
        total_base += base_sum
        total_biased += biased_sum
        bucket["eligible_candidates"] += count
        bucket["unique_targets_override"] = float(bucket.get("unique_targets_override") or 0.0) + float(
            row["unique_targets"]
        )
        bucket["base_probability_sum"] += base_sum
        bucket["biased_probability_sum"] += biased_sum
        bucket["score_sum"] += float(row["score_mean"]) * count
        bucket["base_weighted_score_sum"] += float(row["base_weighted_score_mean"]) * base_sum
        bucket["biased_weighted_score_sum"] += float(row["biased_weighted_score_mean"]) * biased_sum
        bucket["multiplier_sum"] += float(row["multiplier_mean"]) * count
        bucket["multiplier_max"] = max(float(bucket["multiplier_max"]), float(row["multiplier_max"]))
        bucket["positive_bias_candidates"] += float(row["positive_bias_candidates"])
        bucket["negative_bias_candidates"] += float(row["negative_bias_candidates"])
        bucket["neutral_bias_candidates"] += float(row["neutral_bias_candidates"])
        bucket["face6_neighbor_sum"] += float(row["face6_neighbor_mean"]) * count
        bucket["face18_neighbor_sum"] += float(row["face18_neighbor_mean"]) * count
        bucket["cube26_neighbor_sum"] += float(row["cube26_neighbor_mean"]) * count
        bucket["face6_component_sum"] += float(row["face6_component_mean"]) * count
        bucket["cube26_component_sum"] += float(row["cube26_component_mean"]) * count
    return [
        bucket_row(-1, class_name, bucket, total_base, total_biased)
        for class_name, bucket in sorted(buckets.items())
    ]


def aggregate_tick_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}

    def mean_field(field: str) -> float:
        return float(np.mean([float(row[field]) for row in rows]))

    def sum_field(field: str) -> float:
        return float(np.sum([float(row[field]) for row in rows]))

    return {
        "sample_count": len(rows),
        "final_tick": int(rows[-1]["tick"]),
        "mean_active_iotas": mean_field("active_iotas"),
        "mean_depleted_cells": mean_field("depleted_cells"),
        "mean_depleted_interface_sites": mean_field("depleted_interface_sites"),
        "total_eligible_candidates": sum_field("eligible_candidates"),
        "mean_eligible_candidates": mean_field("eligible_candidates"),
        "mean_unique_targets": mean_field("unique_targets"),
        "total_base_probability_sum": sum_field("base_probability_sum"),
        "total_biased_probability_sum": sum_field("biased_probability_sum"),
        "total_probability_delta": sum_field("probability_delta"),
        "max_abs_probability_delta": float(max(abs(float(row["probability_delta"])) for row in rows)),
        "mean_score": mean_field("mean_score"),
        "mean_multiplier": mean_field("mean_multiplier"),
        "max_multiplier": float(max(float(row["max_multiplier"]) for row in rows)),
        "mean_component_bridge_cube26_targets": mean_field("component_bridge_cube26_targets"),
        "mean_local_bridge_face6_targets": mean_field("local_bridge_face6_targets"),
        "mean_tip_seed_targets": mean_field("tip_seed_targets"),
        "mean_flat_front_targets": mean_field("flat_front_targets"),
        "mean_concave_fill_targets": mean_field("concave_fill_targets"),
        "final_largest_coherence_cube26": rows[-1]["largest_coherence_cube26"],
        "final_coherence_count_cube26": rows[-1]["coherence_count_cube26"],
        "final_component_size_entropy_cube26": rows[-1]["component_size_entropy_cube26"],
        "final_ledger_error": rows[-1]["ledger_error"],
    }


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    ticks = int(args.ticks if args.ticks is not None else cfg.get("run", {}).get("ticks", 2048))
    sample_ticks = sample_schedule(args, ticks)
    sample_tick_set = set(sample_ticks)
    output_prefix = Path(args.output_prefix)
    class_path = output_prefix.with_name(output_prefix.name + "_classes.csv")
    tick_path = output_prefix.with_name(output_prefix.name + "_ticks.csv")
    target_path = output_prefix.with_name(output_prefix.name + "_targets.csv")
    class_summary_path = output_prefix.with_name(output_prefix.name + "_class_summary.csv")
    summary_path = output_prefix.with_name(output_prefix.name + "_summary.json")

    world = init_world(cfg)
    class_rows: list[dict[str, Any]] = []
    tick_rows: list[dict[str, Any]] = []
    target_rows: list[dict[str, Any]] = []
    sampled_ticks: set[int] = set()
    final_tick = ticks
    early_stop_reason = ""

    for tick in range(0, ticks + 1):
        if tick in sample_tick_set and tick not in sampled_ticks:
            sample_class_rows, sample_tick_row, sample_target_rows = audit_tick(
                world,
                cfg,
                tick,
                args.connectivity,
                int(args.target_limit),
            )
            class_rows.extend(sample_class_rows)
            tick_rows.append(sample_tick_row)
            target_rows.extend(sample_target_rows)
            sampled_ticks.add(tick)
        if tick == ticks:
            break
        step(world, cfg)
        active_count = int(world.active.sum())
        if int(args.stop_active_iotas) > 0 and active_count >= int(args.stop_active_iotas):
            final_tick = tick + 1
            early_stop_reason = f"active_iotas >= {args.stop_active_iotas}"
            if final_tick not in sampled_ticks:
                sample_class_rows, sample_tick_row, sample_target_rows = audit_tick(
                    world,
                    cfg,
                    final_tick,
                    args.connectivity,
                    int(args.target_limit),
                )
                class_rows.extend(sample_class_rows)
                tick_rows.append(sample_tick_row)
                target_rows.extend(sample_target_rows)
                sampled_ticks.add(final_tick)
            break

    class_summary_rows = aggregate_class_rows(class_rows)
    write_csv(class_path, class_rows, CLASS_FIELDNAMES)
    write_csv(tick_path, tick_rows, TICK_FIELDNAMES)
    if target_rows:
        write_csv(target_path, target_rows, TARGET_FIELDNAMES)
    write_csv(class_summary_path, class_summary_rows, CLASS_FIELDNAMES)
    summary = {
        "config": {
            "config_path": args.config,
            "seed": cfg.get("init", {}).get("seed"),
            "ticks": ticks,
            "connectivity": args.connectivity,
            "sample_ticks": sample_ticks,
            "target_limit": args.target_limit,
            "residual_participation_probability": cfg.get("constants", {}).get(
                "residual_participation_probability",
                cfg.get("constants", {}).get("depleted_reactivation_probability", 0.0),
            ),
            "angular_momentum_residual_bias_score_mode": cfg.get("constants", {}).get(
                "angular_momentum_residual_bias_score_mode",
                "",
            ),
            "angular_momentum_residual_bias_strength": cfg.get("constants", {}).get(
                "angular_momentum_residual_bias_strength",
                "",
            ),
        },
        "final_tick": final_tick,
        "early_stop_reason": early_stop_reason,
        "class_path": class_path.as_posix(),
        "tick_path": tick_path.as_posix(),
        "target_path": target_path.as_posix() if target_rows else "",
        "class_summary_path": class_summary_path.as_posix(),
        "aggregate": aggregate_tick_rows(tick_rows),
        "class_summary": class_summary_rows,
    }
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
