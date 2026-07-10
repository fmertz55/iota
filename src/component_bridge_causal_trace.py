from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from continuation import clone_world, deterministic_continuation_seed, load_checkpoint
from iota_rig import (
    World,
    angular_momentum_residual_score,
    apply_angular_momentum_residual_bias,
    candidate_neighbor_steps,
    clamp_probability,
    clamp_signed,
    classify_residual_target_geometry,
    history_coupled_rotation_offset,
    history_coupled_signed_rotation_offset,
    load_config,
    local_candidates,
    offset_vector_state,
    residual_source_support_score,
    residual_target_support_score,
    secondary_bias_gate_mask,
    signed_round_offset,
    vector_alignment,
    vector_step,
)
from metrics import collect_metrics


EVENT_FIELDNAMES = [
    "case_label",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "tick",
    "offset",
    "event_index",
    "source_x",
    "source_y",
    "source_z",
    "target_x",
    "target_y",
    "target_z",
    "candidate_order",
    "candidate_step",
    "influence",
    "base_probability",
    "transfer_probability",
    "gate_random",
    "residual_bias_multiplier",
    "source_L",
    "target_L",
    "L_contrast",
    "primary_alignment",
    "contrast_score",
    "geometry_score",
    "residual_score",
    "scoring_geometry_class",
    "event_geometry_class",
    "event_face6_neighbors",
    "event_cube26_neighbors",
    "event_cube26_components",
    "global_neighbor_component_count_pre",
    "global_neighbor_component_labels_pre",
    "global_neighbor_component_sizes_pre",
    "global_bridge_pre",
    "component_count_before_event",
    "component_count_after_event",
    "component_count_delta_event",
    "largest_before_event",
    "largest_after_event",
    "largest_delta_event",
    "target_new_vs_checkpoint",
    "target_ever_active_before",
    "target_active_after_1",
    "target_active_after_16",
    "target_active_after_64",
    "target_active_after_128",
    "target_active_after_256",
    "target_active_at_end",
]

DEACTIVATION_FIELDNAMES = [
    "case_label",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "tick",
    "offset",
    "cell_x",
    "cell_y",
    "cell_z",
    "A_before_deactivation",
    "new_vs_checkpoint",
    "ever_active_before",
    "residual_recruited_since_checkpoint",
    "residual_activation_offset",
    "age_since_residual_activation",
    "latest_residual_activation_offset",
    "age_since_latest_residual_activation",
    "component_count_pre_group",
    "component_count_post_group",
    "component_count_delta_group",
    "largest_pre_group",
    "largest_post_group",
    "largest_delta_group",
    "single_removal_component_count_delta",
    "single_removal_largest_delta",
    "single_removal_articulation",
    "neighbor_component_count_after_removal",
    "neighbor_component_labels_after_removal",
    "neighbor_component_sizes_after_removal",
]

TIMELINE_FIELDNAMES = [
    "case_label",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "tick",
    "offset",
    "phase",
    "active_iotas",
    "depleted_cells",
    "active_interface_cells",
    "depleted_interface_cells",
    "interface_union_cells",
    "active_depleted_adjacency",
    "depleted_active_adjacency",
    "coherence_count_cube26",
    "coherence_count_delta_from_checkpoint",
    "coherence_count_delta_from_previous",
    "largest_coherence_cube26",
    "largest_delta_from_checkpoint",
    "largest_delta_from_previous",
    "component_size_entropy_cube26",
    "component_entropy_delta_from_checkpoint",
    "residual_event_count",
    "residual_scoring_component_bridge_count",
    "residual_event_component_bridge_count",
    "residual_global_bridge_count",
    "residual_high_abs_L_contrast_count",
    "residual_mean_abs_L_contrast",
    "residual_max_abs_L_contrast",
    "deactivation_count",
    "deactivation_articulation_count",
    "ledger_error",
]

SUMMARY_FIELDNAMES = [
    "case_label",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "first_component_change_offset",
    "first_component_change_tick",
    "first_component_change_delta_from_checkpoint",
    "first_component_split_offset",
    "first_component_split_tick",
    "component_signal_offsets",
    "component_signal_vanish_offset",
    "component_signal_vanish_tick",
    "pre_signal_residual_events",
    "pre_signal_global_bridge_events",
    "pre_signal_event_component_bridge_events",
    "pre_signal_scoring_component_bridge_events",
    "pre_signal_high_abs_L_contrast_events",
    "pre_signal_deactivations",
    "pre_signal_articulation_deactivations",
    "first_signal_preceded_by_adjacency_delta",
    "active_depleted_adjacency_at_checkpoint",
    "active_depleted_adjacency_before_signal",
    "active_depleted_adjacency_at_signal",
    "residual_event_count",
    "global_bridge_event_count",
    "event_component_bridge_count",
    "scoring_component_bridge_count",
    "high_abs_L_contrast_event_count",
    "deactivation_count",
    "articulation_deactivation_count",
    "component_count_final",
    "component_count_checkpoint",
    "largest_final",
    "largest_checkpoint",
    "ledger_exact",
]

FOLLOWUP_OFFSETS = (1, 16, 64, 128, 256)
HIGH_ABS_L_CONTRAST = 0.5
GEOMETRY_CLASSES = (
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trace residual recruitment events that can convert interface divergence into cube26 component divergence."
    )
    parser.add_argument("--label", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint-state-dir", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--sample-index", type=int, default=6)
    parser.add_argument("--continuation-seed", type=int, default=None)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--horizon", type=int, default=1024)
    parser.add_argument("--phase-length", type=int, default=256)
    parser.add_argument("--connectivity", choices=["cube26"], default="cube26")
    return parser.parse_args()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


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


def interface_metrics(world: World, connectivity: str) -> dict[str, float]:
    depleted = (~world.active) & (world.latent_A == 0)
    active_interface = world.active & adjacent_to_mask(depleted, connectivity, world.wrap)
    depleted_interface = depleted & adjacent_to_mask(world.active, connectivity, world.wrap)
    interface_union = active_interface | depleted_interface
    active_count = int(np.count_nonzero(world.active))
    depleted_count = int(np.count_nonzero(depleted))
    return {
        "active_interface_cells": int(np.count_nonzero(active_interface)),
        "depleted_interface_cells": int(np.count_nonzero(depleted_interface)),
        "interface_union_cells": int(np.count_nonzero(interface_union)),
        "active_depleted_adjacency": (
            float(np.count_nonzero(active_interface) / active_count) if active_count else 0.0
        ),
        "depleted_active_adjacency": (
            float(np.count_nonzero(depleted_interface) / depleted_count) if depleted_count else 0.0
        ),
    }


def component_labels(
    active: np.ndarray,
    wrap: bool,
    connectivity: str,
) -> tuple[np.ndarray, dict[int, int], int, int]:
    labels = np.full(active.shape, -1, dtype=np.int32)
    coords = {tuple(int(value) for value in coord) for coord in np.argwhere(active)}
    if not coords:
        return labels, {}, 0, 0

    size = int(active.shape[0])
    steps = tuple(
        (int(dx), int(dy), int(dz))
        for dx, dy, dz in candidate_neighbor_steps(connectivity)
    )
    component_sizes: dict[int, int] = {}
    label = 0
    largest = 0
    while coords:
        stack = [coords.pop()]
        component_size = 0
        while stack:
            x, y, z = stack.pop()
            labels[x, y, z] = label
            component_size += 1
            for dx, dy, dz in steps:
                nx, ny, nz = x + dx, y + dy, z + dz
                if wrap:
                    nx %= size
                    ny %= size
                    nz %= size
                elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
                    continue
                neighbor = (nx, ny, nz)
                if neighbor in coords:
                    coords.remove(neighbor)
                    stack.append(neighbor)
        component_sizes[label] = component_size
        largest = max(largest, component_size)
        label += 1
    return labels, component_sizes, label, largest


def active_neighbor_coords(
    active: np.ndarray,
    target: tuple[int, int, int],
    connectivity: str,
    wrap: bool,
) -> list[tuple[int, int, int]]:
    size = int(active.shape[0])
    tx, ty, tz = target
    coords: list[tuple[int, int, int]] = []
    for raw_delta in candidate_neighbor_steps(connectivity):
        dx, dy, dz = (int(value) for value in raw_delta)
        nx, ny, nz = tx + dx, ty + dy, tz + dz
        if wrap:
            nx %= size
            ny %= size
            nz %= size
        elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
            continue
        if bool(active[nx, ny, nz]):
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
    steps = tuple(
        (int(dx), int(dy), int(dz))
        for dx, dy, dz in candidate_neighbor_steps(connectivity)
    )
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            x, y, z = stack.pop()
            for dx, dy, dz in steps:
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


def geometry_from_mask(
    active: np.ndarray,
    target: tuple[int, int, int],
    wrap: bool,
) -> dict[str, Any]:
    face6_coords = active_neighbor_coords(active, target, "face6", wrap)
    face18_coords = active_neighbor_coords(active, target, "face18", wrap)
    cube26_coords = active_neighbor_coords(active, target, "cube26", wrap)
    face6_count = len(face6_coords)
    face18_count = len(face18_coords)
    cube26_count = len(cube26_coords)
    face6_components = local_component_count(face6_coords, "face6", int(active.shape[0]), wrap)
    cube26_components = local_component_count(cube26_coords, "cube26", int(active.shape[0]), wrap)

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


def neighbor_component_summary(
    active: np.ndarray,
    labels: np.ndarray,
    component_sizes: dict[int, int],
    target: tuple[int, int, int],
    wrap: bool,
    connectivity: str,
) -> dict[str, Any]:
    label_values: set[int] = set()
    for coord in active_neighbor_coords(active, target, connectivity, wrap):
        label = int(labels[coord])
        if label >= 0:
            label_values.add(label)
    sorted_labels = sorted(label_values)
    return {
        "neighbor_component_count": len(sorted_labels),
        "neighbor_component_labels": ";".join(str(value) for value in sorted_labels),
        "neighbor_component_sizes": ";".join(str(int(component_sizes.get(value, 0))) for value in sorted_labels),
    }


def csv_bool(value: bool) -> int:
    return 1 if bool(value) else 0


def get_geometry_weights(constants: dict[str, Any]) -> dict[str, float]:
    raw = constants.get("angular_momentum_residual_geometry_weights", {})
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("angular_momentum_residual_geometry_weights must be a mapping")
    weights = {
        class_name: float(
            constants.get(
                f"angular_momentum_residual_geometry_{class_name}_weight",
                raw.get(class_name, 0.0),
            )
        )
        for class_name in GEOMETRY_CLASSES
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
        weights[term] = float(
            constants.get(
                f"angular_momentum_residual_{term}_weight",
                raw.get(term, 0.0),
            )
        )
    return weights


def residual_score_parts(
    world: World,
    old_L: np.ndarray,
    x: int,
    y: int,
    z: int,
    v_idx: int,
    a: int,
    r: int,
    p: int,
    candidate: dict[str, Any],
    angular_momentum_cap: float,
    score_mode: str,
    geometry_weights: dict[str, float],
) -> dict[str, float | str]:
    tx, ty, tz = candidate["target"]
    source_l = float(old_L[x, y, z])
    target_l = float(old_L[tx, ty, tz])
    l_contrast = clamp_signed(
        (source_l - target_l) / angular_momentum_cap if angular_momentum_cap > 0.0 else 0.0,
        1.0,
    )
    primary_dx, primary_dy, primary_dz, _ = vector_step(world, v_idx, a, r, p)
    primary_alignment = vector_alignment((primary_dx, primary_dy, primary_dz), candidate["step"])
    contrast_score = float(l_contrast) * primary_alignment
    scoring_geometry = classify_residual_target_geometry(world, tuple(int(value) for value in candidate["target"]))
    geometry_score = (
        float(geometry_weights.get(str(scoring_geometry["class"]), 0.0))
        if score_mode in {
            "source_target_L_contrast_component_bridge",
            "source_target_L_contrast_support_weighted",
        }
        else 0.0
    )
    residual_score = angular_momentum_residual_score(
        world,
        old_L,
        x,
        y,
        z,
        v_idx,
        a,
        r,
        p,
        candidate,
        angular_momentum_cap,
        True,
        score_mode,
        geometry_weights,
    )
    support_score = (
        residual_target_support_score(world, tuple(int(value) for value in candidate["target"]), geometry_weights)
        + residual_source_support_score(world, (int(x), int(y), int(z)), int(a), geometry_weights)
        if score_mode == "source_target_L_contrast_support_weighted"
        else 0.0
    )
    return {
        "source_L": source_l,
        "target_L": target_l,
        "L_contrast": float(l_contrast),
        "primary_alignment": float(primary_alignment),
        "contrast_score": float(contrast_score),
        "geometry_score": float(geometry_score + support_score),
        "residual_score": float(residual_score),
        "scoring_geometry_class": str(scoring_geometry["class"]),
    }


def append_deactivation_rows(
    rows: list[dict[str, Any]],
    case: dict[str, Any],
    offset: int,
    exhausted_coords: np.ndarray,
    pre_active: np.ndarray,
    post_active: np.ndarray,
    pre_deactivation_A: np.ndarray,
    checkpoint_active: np.ndarray,
    ever_active: np.ndarray,
    first_residual_activation_offsets: dict[tuple[int, int, int], int],
    latest_residual_activation_offsets: dict[tuple[int, int, int], int],
) -> None:
    if len(exhausted_coords) == 0:
        return
    pre_labels, pre_sizes, pre_count, pre_largest = component_labels(pre_active, case["wrap"], "cube26")
    post_labels, post_sizes, post_count, post_largest = component_labels(post_active, case["wrap"], "cube26")
    group_delta = int(post_count - pre_count)
    group_largest_delta = int(post_largest - pre_largest)
    ever_active_before_deactivation = ever_active | pre_active
    for coord in exhausted_coords:
        cell = tuple(int(value) for value in coord)
        single_removed = pre_active.copy()
        single_removed[cell] = False
        single_labels, single_sizes, single_count, single_largest = component_labels(
            single_removed,
            case["wrap"],
            "cube26",
        )
        neighbor_summary = neighbor_component_summary(
            single_removed,
            single_labels,
            single_sizes,
            cell,
            case["wrap"],
            "cube26",
        )
        activation_offset = first_residual_activation_offsets.get(cell)
        latest_activation_offset = latest_residual_activation_offsets.get(cell)
        rows.append(
            {
                **case["ids"],
                "tick": int(case["checkpoint_tick"] + offset),
                "offset": int(offset),
                "cell_x": cell[0],
                "cell_y": cell[1],
                "cell_z": cell[2],
                "A_before_deactivation": int(pre_deactivation_A[cell]),
                "new_vs_checkpoint": csv_bool(not bool(checkpoint_active[cell])),
                "ever_active_before": csv_bool(bool(ever_active_before_deactivation[cell])),
                "residual_recruited_since_checkpoint": csv_bool(activation_offset is not None),
                "residual_activation_offset": "" if activation_offset is None else int(activation_offset),
                "age_since_residual_activation": "" if activation_offset is None else int(offset - activation_offset),
                "latest_residual_activation_offset": (
                    "" if latest_activation_offset is None else int(latest_activation_offset)
                ),
                "age_since_latest_residual_activation": (
                    "" if latest_activation_offset is None else int(offset - latest_activation_offset)
                ),
                "component_count_pre_group": int(pre_count),
                "component_count_post_group": int(post_count),
                "component_count_delta_group": group_delta,
                "largest_pre_group": int(pre_largest),
                "largest_post_group": int(post_largest),
                "largest_delta_group": group_largest_delta,
                "single_removal_component_count_delta": int(single_count - pre_count),
                "single_removal_largest_delta": int(single_largest - pre_largest),
                "single_removal_articulation": csv_bool(single_count > pre_count),
                "neighbor_component_count_after_removal": int(neighbor_summary["neighbor_component_count"]),
                "neighbor_component_labels_after_removal": neighbor_summary["neighbor_component_labels"],
                "neighbor_component_sizes_after_removal": neighbor_summary["neighbor_component_sizes"],
            }
        )


def traced_hard_step(
    world: World,
    cfg: dict[str, Any],
    case: dict[str, Any],
    offset: int,
    event_rows: list[dict[str, Any]],
    deactivation_rows: list[dict[str, Any]],
    checkpoint_active: np.ndarray,
    ever_active: np.ndarray,
    first_residual_activation_offsets: dict[tuple[int, int, int], int],
    latest_residual_activation_offsets: dict[tuple[int, int, int], int],
) -> dict[str, float]:
    constants = cfg["constants"]
    kA = float(constants.get("amplitude_coupling", 0.125))
    kR = float(constants.get("range_coupling", 0.125))
    thetaP = float(constants.get("payload_takeover", 0.5))
    mu = float(constants.get("mutation_rate", 0.0))
    decay_mode = constants.get("decay_mode", "inverse_square")
    deactivation = str(constants.get("deactivation", "none"))
    valence = max(1, int(constants.get("valence", 1)))
    bond_probability = clamp_probability(float(constants.get("bond_probability", 1.0)))
    neighbor_mode = str(constants.get("neighbor_mode", "cube26"))
    cross_payload_coupling = float(constants.get("cross_payload_coupling", 1.0))
    same_payload_coupling = float(constants.get("same_payload_coupling", 1.0))
    secondary_vector_kick_probability = clamp_probability(
        float(constants.get("secondary_vector_kick_probability", 0.0))
    )
    secondary_vector_kick_offset = int(constants.get("secondary_vector_kick_offset", 1))
    secondary_vector_kick_preserve_behavior = bool(
        constants.get("secondary_vector_kick_preserve_behavior", True)
    )
    received_rotation_probability = clamp_probability(
        float(
            constants.get(
                "received_rotation_probability",
                constants.get("history_coupled_rotation_probability", 0.0),
            )
        )
    )
    received_rotation_max_offset = max(
        1,
        int(
            constants.get(
                "received_rotation_max_offset",
                constants.get("history_coupled_rotation_max_offset", 3),
            )
        ),
    )
    received_rotation_preserve_behavior = bool(
        constants.get(
            "received_rotation_preserve_behavior",
            constants.get("history_coupled_rotation_preserve_behavior", True),
        )
    )
    received_rotation_residual_multiplier = float(
        constants.get(
            "received_rotation_residual_multiplier",
            constants.get("history_coupled_rotation_residual_multiplier", 1.0),
        )
    )
    received_rotation_secondary_multiplier = float(
        constants.get(
            "received_rotation_secondary_multiplier",
            constants.get("history_coupled_rotation_secondary_multiplier", 1.0),
        )
    )
    angular_momentum_enabled = bool(constants.get("angular_momentum_enabled", False))
    angular_momentum_decay = max(0.0, min(1.0, float(constants.get("angular_momentum_decay", 1.0))))
    angular_momentum_coupling = float(constants.get("angular_momentum_coupling", 0.0))
    angular_momentum_retention = float(constants.get("angular_momentum_retention", 1.0))
    angular_momentum_cap = max(0.0, float(constants.get("angular_momentum_cap", received_rotation_max_offset)))
    angular_momentum_enabled = angular_momentum_enabled and angular_momentum_cap > 0.0
    angular_momentum_secondary_bias_enabled = bool(
        constants.get("angular_momentum_secondary_bias_enabled", False)
    )
    angular_momentum_secondary_bias_strength = max(
        0.0,
        float(constants.get("angular_momentum_secondary_bias_strength", 0.0)),
    )
    angular_momentum_secondary_bias_preserve_behavior = bool(
        constants.get("angular_momentum_secondary_bias_preserve_behavior", True)
    )
    angular_momentum_secondary_bias_gate = str(
        constants.get("angular_momentum_secondary_bias_gate", "none")
    )
    angular_momentum_secondary_bias_enabled = (
        angular_momentum_enabled
        and angular_momentum_secondary_bias_enabled
        and angular_momentum_secondary_bias_strength > 0.0
    )
    angular_momentum_residual_bias_enabled = bool(
        constants.get("angular_momentum_residual_bias_enabled", False)
    )
    angular_momentum_residual_bias_strength = max(
        0.0,
        float(constants.get("angular_momentum_residual_bias_strength", 0.0)),
    )
    angular_momentum_residual_bias_mean_preserving = bool(
        constants.get("angular_momentum_residual_bias_mean_preserving", True)
    )
    angular_momentum_residual_bias_preserve_behavior = bool(
        constants.get("angular_momentum_residual_bias_preserve_behavior", True)
    )
    angular_momentum_residual_bias_score_mode = str(
        constants.get("angular_momentum_residual_bias_score_mode", "source_L_alignment")
    )
    angular_momentum_residual_geometry_weights = get_geometry_weights(constants)
    angular_momentum_residual_bias_enabled = (
        angular_momentum_enabled
        and angular_momentum_residual_bias_enabled
        and angular_momentum_residual_bias_strength > 0.0
    )
    residual_participation_probability = clamp_probability(
        float(
            constants.get(
                "residual_participation_probability",
                constants.get("depleted_reactivation_probability", 0.0),
            )
        )
    )
    residual_participation_secondary_only = bool(
        constants.get(
            "residual_participation_secondary_only",
            constants.get("depleted_reactivation_secondary_only", True),
        )
    )

    if deactivation not in {"none", "exhaustion"}:
        raise ValueError(f"Unknown deactivation mode: {deactivation}")

    old_active = world.active.copy()
    old_V = world.V.copy()
    next_active = world.active.copy()
    next_A = world.A.astype(np.int64, copy=True)
    available_A = world.A.astype(np.int64, copy=True)
    next_latent_A = world.latent_A.astype(np.int64, copy=True)
    next_R = world.R.astype(np.float32).copy()
    next_V = world.V.copy()
    next_P = world.P.copy()
    old_L = (
        world.angular_L.astype(np.float32, copy=True)
        if world.angular_L is not None
        else np.zeros(world.active.shape, dtype=np.float32)
    )
    next_L = old_L * angular_momentum_decay if angular_momentum_enabled else old_L.copy()

    coords = np.argwhere(world.active)
    exchanges = 0
    secondary_exchanges = 0
    payload_changes = 0
    amplitude_transfers = 0
    failed_transfer_gates = 0
    secondary_vector_kicks = 0
    residual_participations = 0
    rotation_events = 0
    rotation_events_on_residual_entry = 0
    rotation_events_on_secondary_exchange = 0
    angular_momentum_updates = 0
    angular_momentum_biased_rotation_events = 0
    angular_momentum_bias_abs_sum = 0.0
    angular_momentum_observed_turn_abs_sum = 0.0
    angular_momentum_secondary_bias_sources = 0
    angular_momentum_secondary_bias_selected_candidates = 0
    angular_momentum_residual_bias_eligible_candidates = 0.0
    angular_momentum_residual_bias_base_probability_sum = 0.0
    angular_momentum_residual_bias_biased_probability_sum = 0.0
    exchange_alignments: list[float] = []
    secondary_exchange_alignments: list[float] = []
    gated_secondary_bias_mask = (
        secondary_bias_gate_mask(world, neighbor_mode)
        if (
            angular_momentum_secondary_bias_enabled
            and angular_momentum_secondary_bias_gate == "interface_recruitment"
        )
        else None
    )

    for x, y, z in coords:
        a = int(world.A[x, y, z])
        r = int(world.R[x, y, z])
        if a <= 0 or r == 0:
            continue
        v_idx = int(world.V[x, y, z]) % len(world.vectors)
        p = int(world.P[x, y, z])
        primary_dx, primary_dy, primary_dz, _ = vector_step(world, v_idx, a, r, p)
        primary_step = (primary_dx, primary_dy, primary_dz)
        secondary_bias_step = None
        secondary_bias_strength = 0.0
        if angular_momentum_secondary_bias_enabled:
            source_l = float(old_L[x, y, z])
            if abs(source_l) > 1e-6:
                bias_offset = 1 if source_l > 0.0 else -1
                bias_v = offset_vector_state(
                    world,
                    v_idx,
                    bias_offset,
                    preserve_behavior=angular_momentum_secondary_bias_preserve_behavior,
                )
                secondary_bias_dx, secondary_bias_dy, secondary_bias_dz, _ = vector_step(
                    world,
                    bias_v,
                    a,
                    r,
                    p,
                )
                secondary_bias_step = (
                    secondary_bias_dx,
                    secondary_bias_dy,
                    secondary_bias_dz,
                )
                secondary_bias_strength = angular_momentum_secondary_bias_strength * min(
                    1.0,
                    abs(source_l) / angular_momentum_cap,
                )
                angular_momentum_secondary_bias_sources += 1
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
            secondary_bias_step=secondary_bias_step,
            secondary_bias_strength=secondary_bias_strength,
            secondary_bias_gate=gated_secondary_bias_mask,
        )
        angular_momentum_secondary_bias_selected_candidates += sum(
            1
            for candidate in candidates
            if int(candidate["order"]) != 0 and abs(float(candidate.get("secondary_bias_score", 0.0))) > 0.0
        )
        if angular_momentum_residual_bias_enabled:
            residual_bias_metric = apply_angular_momentum_residual_bias(
                world,
                old_L,
                candidates,
                int(x),
                int(y),
                int(z),
                v_idx,
                a,
                r,
                p,
                next_active,
                next_latent_A,
                kA,
                residual_participation_probability,
                residual_participation_secondary_only,
                angular_momentum_cap,
                angular_momentum_residual_bias_strength,
                angular_momentum_residual_bias_preserve_behavior,
                angular_momentum_residual_bias_mean_preserving,
                angular_momentum_residual_bias_score_mode,
                angular_momentum_residual_geometry_weights,
            )
            angular_momentum_residual_bias_eligible_candidates += residual_bias_metric[
                "eligible_candidates"
            ]
            angular_momentum_residual_bias_base_probability_sum += residual_bias_metric[
                "base_probability_sum"
            ]
            angular_momentum_residual_bias_biased_probability_sum += residual_bias_metric[
                "biased_probability_sum"
            ]

        for candidate in candidates:
            if int(available_A[x, y, z]) <= 0:
                break
            tx, ty, tz = candidate["target"]
            target_previous_a = int(world.A[tx, ty, tz])
            target_previous_r = int(world.R[tx, ty, tz])
            target_previous_v = int(world.V[tx, ty, tz]) % len(world.vectors)
            target_previous_p = int(world.P[tx, ty, tz])
            target_active = bool(next_active[tx, ty, tz])
            target_depleted = (not target_active) and int(next_latent_A[tx, ty, tz]) <= 0
            if target_active:
                if int(next_A[tx, ty, tz]) >= int(available_A[x, y, z]):
                    continue
            elif target_depleted and (
                residual_participation_probability <= 0.0
                or (
                    residual_participation_secondary_only
                    and int(candidate["order"]) == 0
                )
            ):
                continue

            influence = float(candidate["influence"])
            if bool(world.active[tx, ty, tz]):
                influence *= (
                    same_payload_coupling
                    if int(world.P[tx, ty, tz]) == p
                    else cross_payload_coupling
                )
            if influence <= 0:
                continue

            transfer_probability = clamp_probability(kA * influence)
            if target_depleted:
                transfer_probability *= residual_participation_probability
                if angular_momentum_residual_bias_enabled:
                    transfer_probability *= float(candidate.get("residual_bias_multiplier", 1.0))
                    transfer_probability = clamp_probability(transfer_probability)
            gate_draw = float(world.rng.random())
            if gate_draw >= transfer_probability:
                failed_transfer_gates += 1
                continue

            event_row: dict[str, Any] | None = None
            target = (int(tx), int(ty), int(tz))
            if target_depleted:
                pre_labels, pre_sizes, pre_count, pre_largest = component_labels(
                    next_active,
                    world.wrap,
                    "cube26",
                )
                neighbor_summary = neighbor_component_summary(
                    next_active,
                    pre_labels,
                    pre_sizes,
                    target,
                    world.wrap,
                    "cube26",
                )
                event_geometry = geometry_from_mask(next_active, target, world.wrap)
                score_parts = residual_score_parts(
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
                    angular_momentum_cap,
                    angular_momentum_residual_bias_score_mode,
                    angular_momentum_residual_geometry_weights,
                )
                base_probability = clamp_probability(kA * float(candidate["influence"])) * residual_participation_probability
                after_active = next_active.copy()
                after_active[target] = True
                _, _, after_count, after_largest = component_labels(after_active, world.wrap, "cube26")
                event_row = {
                    **case["ids"],
                    "tick": int(case["checkpoint_tick"] + offset),
                    "offset": int(offset),
                    "event_index": len(event_rows),
                    "source_x": int(x),
                    "source_y": int(y),
                    "source_z": int(z),
                    "target_x": target[0],
                    "target_y": target[1],
                    "target_z": target[2],
                    "candidate_order": int(candidate["order"]),
                    "candidate_step": ",".join(str(int(value)) for value in candidate["step"]),
                    "influence": float(influence),
                    "base_probability": float(base_probability),
                    "transfer_probability": float(transfer_probability),
                    "gate_random": gate_draw,
                    "residual_bias_multiplier": float(candidate.get("residual_bias_multiplier", 1.0)),
                    **score_parts,
                    "event_geometry_class": str(event_geometry["class"]),
                    "event_face6_neighbors": int(event_geometry["face6_neighbors"]),
                    "event_cube26_neighbors": int(event_geometry["cube26_neighbors"]),
                    "event_cube26_components": int(event_geometry["cube26_components"]),
                    "global_neighbor_component_count_pre": int(neighbor_summary["neighbor_component_count"]),
                    "global_neighbor_component_labels_pre": neighbor_summary["neighbor_component_labels"],
                    "global_neighbor_component_sizes_pre": neighbor_summary["neighbor_component_sizes"],
                    "global_bridge_pre": csv_bool(int(neighbor_summary["neighbor_component_count"]) >= 2),
                    "component_count_before_event": int(pre_count),
                    "component_count_after_event": int(after_count),
                    "component_count_delta_event": int(after_count - pre_count),
                    "largest_before_event": int(pre_largest),
                    "largest_after_event": int(after_largest),
                    "largest_delta_event": int(after_largest - pre_largest),
                    "target_new_vs_checkpoint": csv_bool(not bool(checkpoint_active[target])),
                    "target_ever_active_before": csv_bool(bool(ever_active[target])),
                    "target_active_after_1": "",
                    "target_active_after_16": "",
                    "target_active_after_64": "",
                    "target_active_after_128": "",
                    "target_active_after_256": "",
                    "target_active_at_end": "",
                }

            available_A[x, y, z] -= 1
            next_A[x, y, z] -= 1
            if target_active:
                next_A[tx, ty, tz] += 1
            elif target_depleted:
                next_A[tx, ty, tz] += 1
                next_latent_A[tx, ty, tz] = 0
                next_active[tx, ty, tz] = True
                residual_participations += 1
                first_residual_activation_offsets.setdefault(target, int(offset))
                latest_residual_activation_offsets[target] = int(offset)
                if event_row is not None:
                    event_rows.append(event_row)
            else:
                next_A[tx, ty, tz] += int(next_latent_A[tx, ty, tz]) + 1
                next_latent_A[tx, ty, tz] = 0
                next_active[tx, ty, tz] = True
            next_latent_A[tx, ty, tz] = 0

            exchanges += 1
            amplitude_transfers += 1
            if int(candidate["order"]) != 0:
                secondary_exchanges += 1
            alignment = vector_alignment(primary_step, candidate["step"])
            exchange_alignments.append(alignment)
            if int(candidate["order"]) != 0:
                secondary_exchange_alignments.append(alignment)

            next_R[tx, ty, tz] = (1 - kR * influence) * next_R[tx, ty, tz] + (kR * influence) * r

            if influence >= thetaP:
                new_p = int(world.P[x, y, z])
                if mu > 0 and world.rng.random() < mu:
                    new_p = int((new_p + world.rng.choice([-1, 1])) % 8)
                if int(next_P[tx, ty, tz]) != new_p:
                    payload_changes += 1
                next_P[tx, ty, tz] = new_p
                next_V[tx, ty, tz] = np.uint8(offset_vector_state(world, v_idx, new_p, preserve_behavior=True))
            elif world.rng.random() < influence * 0.125:
                next_V[tx, ty, tz] = np.uint8(v_idx)

            if received_rotation_probability > 0.0:
                rotation_probability = received_rotation_probability
                if target_depleted:
                    rotation_probability *= received_rotation_residual_multiplier
                if int(candidate["order"]) != 0:
                    rotation_probability *= received_rotation_secondary_multiplier
                rotation_probability = clamp_probability(rotation_probability)
                if rotation_probability > 0.0 and world.rng.random() < rotation_probability:
                    rotation_offset = history_coupled_rotation_offset(
                        source_v=v_idx,
                        source_p=p,
                        target_v=target_previous_v,
                        target_a=target_previous_a,
                        target_r=target_previous_r,
                        target_p=target_previous_p,
                        candidate_order=int(candidate["order"]),
                        target_depleted=target_depleted,
                        influence=influence,
                        max_offset=received_rotation_max_offset,
                    )
                    if angular_momentum_enabled:
                        exchange_rotation_offset = history_coupled_signed_rotation_offset(
                            source_v=v_idx,
                            source_p=p,
                            target_v=target_previous_v,
                            target_a=target_previous_a,
                            target_r=target_previous_r,
                            target_p=target_previous_p,
                            candidate_order=int(candidate["order"]),
                            target_depleted=target_depleted,
                            influence=influence,
                            max_offset=received_rotation_max_offset,
                        )
                        turn_bias = float(old_L[tx, ty, tz]) * angular_momentum_coupling
                        angular_momentum_bias_abs_sum += abs(turn_bias)
                        unbiased_turn = clamp_signed(float(exchange_rotation_offset), angular_momentum_cap)
                        unbiased_rotation_offset = signed_round_offset(unbiased_turn)
                        total_turn = clamp_signed(
                            float(exchange_rotation_offset) + turn_bias,
                            angular_momentum_cap,
                        )
                        rotation_offset = signed_round_offset(total_turn)
                        if rotation_offset != unbiased_rotation_offset:
                            angular_momentum_biased_rotation_events += 1
                    rotated_v = offset_vector_state(
                        world,
                        int(next_V[tx, ty, tz]) % len(world.vectors),
                        rotation_offset,
                        preserve_behavior=received_rotation_preserve_behavior,
                    )
                    if int(next_V[tx, ty, tz]) != rotated_v:
                        next_V[tx, ty, tz] = np.uint8(rotated_v)
                        rotation_events += 1
                        if angular_momentum_enabled:
                            next_L[tx, ty, tz] = clamp_signed(
                                float(next_L[tx, ty, tz]) + angular_momentum_retention * float(rotation_offset),
                                angular_momentum_cap,
                            )
                            angular_momentum_updates += 1
                            angular_momentum_observed_turn_abs_sum += abs(float(rotation_offset))
                        if target_depleted:
                            rotation_events_on_residual_entry += 1
                        if int(candidate["order"]) != 0:
                            rotation_events_on_secondary_exchange += 1

            if (
                int(candidate["order"]) != 0
                and secondary_vector_kick_probability > 0.0
                and world.rng.random() < secondary_vector_kick_probability
            ):
                kicked_v = offset_vector_state(
                    world,
                    int(next_V[tx, ty, tz]) % len(world.vectors),
                    secondary_vector_kick_offset,
                    preserve_behavior=secondary_vector_kick_preserve_behavior,
                )
                if int(next_V[tx, ty, tz]) != kicked_v:
                    next_V[tx, ty, tz] = np.uint8(kicked_v)
                    secondary_vector_kicks += 1

    deactivation_events = 0
    if deactivation == "exhaustion":
        exhausted = next_active & (next_A <= 0)
        deactivation_events = int(np.count_nonzero(exhausted))
        if deactivation_events:
            pre_deactivation_active = next_active.copy()
            pre_deactivation_A = next_A.copy()
            exhausted_coords = np.argwhere(exhausted)
            next_active[exhausted] = False
            next_A[exhausted] = 0
            next_V[exhausted] = 0
            next_P[exhausted] = 0
            next_latent_A[exhausted] = 0
            append_deactivation_rows(
                deactivation_rows,
                case,
                offset,
                exhausted_coords,
                pre_deactivation_active,
                next_active,
                pre_deactivation_A,
                checkpoint_active,
                ever_active,
                first_residual_activation_offsets,
                latest_residual_activation_offsets,
            )

    next_A[~next_active] = 0
    next_latent_A[next_active] = 0

    world.previous_active = old_active
    world.previous_V = old_V
    world.active = next_active
    world.A = next_A
    world.R = np.clip(np.rint(next_R), 0, 7).astype(np.uint8)
    world.V = next_V
    world.P = next_P
    world.latent_A = next_latent_A
    world.angular_L = np.clip(next_L, -angular_momentum_cap, angular_momentum_cap).astype(np.float32)
    world.ledger_enabled = True
    ever_active |= world.active

    active_count = int(world.active.sum())
    payload_hist = np.bincount(world.P[world.active], minlength=8) if active_count else np.zeros(8)
    max_payload_fraction = float(payload_hist.max() / active_count) if active_count else 0.0
    exchange_turn_degrees = [
        float(np.degrees(np.arccos(max(-1.0, min(1.0, alignment)))))
        for alignment in exchange_alignments
    ]
    secondary_turn_degrees = [
        float(np.degrees(np.arccos(max(-1.0, min(1.0, alignment)))))
        for alignment in secondary_exchange_alignments
    ]
    return {
        "exchanges": exchanges,
        "secondary_exchanges": secondary_exchanges,
        "payload_changes": payload_changes,
        "amplitude_transfers": amplitude_transfers,
        "failed_transfer_gates": failed_transfer_gates,
        "deactivation_events": deactivation_events,
        "secondary_vector_kicks": secondary_vector_kicks,
        "residual_participations": residual_participations,
        "depleted_reactivations": residual_participations,
        "rotation_events": rotation_events,
        "rotation_events_on_residual_entry": rotation_events_on_residual_entry,
        "rotation_events_on_secondary_exchange": rotation_events_on_secondary_exchange,
        "angular_momentum_updates": angular_momentum_updates,
        "angular_momentum_biased_rotation_events": angular_momentum_biased_rotation_events,
        "angular_momentum_bias_abs_sum": angular_momentum_bias_abs_sum,
        "angular_momentum_observed_turn_abs_sum": angular_momentum_observed_turn_abs_sum,
        "angular_momentum_secondary_bias_sources": angular_momentum_secondary_bias_sources,
        "angular_momentum_secondary_bias_selected_candidates": angular_momentum_secondary_bias_selected_candidates,
        "angular_momentum_residual_bias_eligible_candidates": angular_momentum_residual_bias_eligible_candidates,
        "angular_momentum_residual_bias_base_probability_sum": angular_momentum_residual_bias_base_probability_sum,
        "angular_momentum_residual_bias_biased_probability_sum": angular_momentum_residual_bias_biased_probability_sum,
        "angular_momentum_residual_bias_probability_delta": (
            angular_momentum_residual_bias_biased_probability_sum
            - angular_momentum_residual_bias_base_probability_sum
        ),
        "mean_A": float(world.A[world.active].mean()) if active_count else 0.0,
        "mean_R": float(world.R[world.active].mean()) if active_count else 0.0,
        "max_payload_fraction": max_payload_fraction,
        "mean_exchange_alignment": (
            float(sum(exchange_alignments) / len(exchange_alignments))
            if exchange_alignments
            else 0.0
        ),
        "mean_exchange_turn_degrees": (
            float(sum(exchange_turn_degrees) / len(exchange_turn_degrees))
            if exchange_turn_degrees
            else 0.0
        ),
        "mean_secondary_exchange_alignment": (
            float(sum(secondary_exchange_alignments) / len(secondary_exchange_alignments))
            if secondary_exchange_alignments
            else 0.0
        ),
        "mean_secondary_exchange_turn_degrees": (
            float(sum(secondary_turn_degrees) / len(secondary_turn_degrees))
            if secondary_turn_degrees
            else 0.0
        ),
    }


def timeline_row(
    world: World,
    case: dict[str, Any],
    offset: int,
    phase_length: int,
    checkpoint_metrics: dict[str, Any],
    previous_metrics: dict[str, Any] | None,
    tick_event_rows: list[dict[str, Any]],
    tick_deactivation_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics = collect_metrics(world, case["checkpoint_tick"] + offset)
    metrics.update(interface_metrics(world, "cube26"))
    abs_contrasts = [abs(float(row["L_contrast"])) for row in tick_event_rows]
    deactivation_articulations = [
        row for row in tick_deactivation_rows if int(row["single_removal_articulation"]) == 1
    ]
    return {
        **case["ids"],
        "tick": int(case["checkpoint_tick"] + offset),
        "offset": int(offset),
        "phase": int(((offset - 1) // phase_length) + 1) if offset > 0 else 0,
        "active_iotas": int(metrics.get("active_iotas", 0)),
        "depleted_cells": int(metrics.get("depleted_cells", 0)),
        "active_interface_cells": int(metrics["active_interface_cells"]),
        "depleted_interface_cells": int(metrics["depleted_interface_cells"]),
        "interface_union_cells": int(metrics["interface_union_cells"]),
        "active_depleted_adjacency": float(metrics["active_depleted_adjacency"]),
        "depleted_active_adjacency": float(metrics["depleted_active_adjacency"]),
        "coherence_count_cube26": int(metrics.get("coherence_count_cube26", 0)),
        "coherence_count_delta_from_checkpoint": int(
            int(metrics.get("coherence_count_cube26", 0))
            - int(checkpoint_metrics.get("coherence_count_cube26", 0))
        ),
        "coherence_count_delta_from_previous": (
            0
            if previous_metrics is None
            else int(metrics.get("coherence_count_cube26", 0))
            - int(previous_metrics.get("coherence_count_cube26", 0))
        ),
        "largest_coherence_cube26": int(metrics.get("largest_coherence_cube26", 0)),
        "largest_delta_from_checkpoint": int(
            int(metrics.get("largest_coherence_cube26", 0))
            - int(checkpoint_metrics.get("largest_coherence_cube26", 0))
        ),
        "largest_delta_from_previous": (
            0
            if previous_metrics is None
            else int(metrics.get("largest_coherence_cube26", 0))
            - int(previous_metrics.get("largest_coherence_cube26", 0))
        ),
        "component_size_entropy_cube26": float(metrics.get("component_size_entropy_cube26", 0.0)),
        "component_entropy_delta_from_checkpoint": float(
            float(metrics.get("component_size_entropy_cube26", 0.0))
            - float(checkpoint_metrics.get("component_size_entropy_cube26", 0.0))
        ),
        "residual_event_count": len(tick_event_rows),
        "residual_scoring_component_bridge_count": sum(
            1 for row in tick_event_rows if row["scoring_geometry_class"] == "component_bridge_cube26"
        ),
        "residual_event_component_bridge_count": sum(
            1 for row in tick_event_rows if row["event_geometry_class"] == "component_bridge_cube26"
        ),
        "residual_global_bridge_count": sum(
            1 for row in tick_event_rows if int(row["global_bridge_pre"]) == 1
        ),
        "residual_high_abs_L_contrast_count": sum(
            1 for value in abs_contrasts if value >= HIGH_ABS_L_CONTRAST
        ),
        "residual_mean_abs_L_contrast": float(np.mean(abs_contrasts)) if abs_contrasts else 0.0,
        "residual_max_abs_L_contrast": float(max(abs_contrasts)) if abs_contrasts else 0.0,
        "deactivation_count": len(tick_deactivation_rows),
        "deactivation_articulation_count": len(deactivation_articulations),
        "ledger_error": float(metrics.get("ledger_error", 0.0)),
        "_metrics": metrics,
    }


def update_event_persistence(event_rows: list[dict[str, Any]], world: World, offset: int) -> None:
    for row in event_rows:
        age = int(offset - int(row["offset"]))
        if age in FOLLOWUP_OFFSETS:
            target = (int(row["target_x"]), int(row["target_y"]), int(row["target_z"]))
            row[f"target_active_after_{age}"] = csv_bool(bool(world.active[target]))


def finalize_event_persistence(event_rows: list[dict[str, Any]], world: World) -> None:
    for row in event_rows:
        target = (int(row["target_x"]), int(row["target_y"]), int(row["target_z"]))
        row["target_active_at_end"] = csv_bool(bool(world.active[target]))


def build_summary(
    case: dict[str, Any],
    timeline_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
    deactivation_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    checkpoint_row = timeline_rows[0]
    signal_rows = [
        row for row in timeline_rows if int(row["coherence_count_delta_from_checkpoint"]) != 0
    ]
    first_signal = signal_rows[0] if signal_rows else None
    first_split = next(
        (
            row
            for row in timeline_rows
            if int(row["coherence_count_delta_from_previous"]) > 0
        ),
        None,
    )
    vanish_row = None
    if signal_rows:
        for row in timeline_rows[timeline_rows.index(signal_rows[0]) + 1 :]:
            if int(row["coherence_count_delta_from_checkpoint"]) == 0:
                vanish_row = row
                break
    signal_offset = int(first_signal["offset"]) if first_signal else None
    pre_signal_events = [
        row for row in event_rows if signal_offset is None or int(row["offset"]) <= signal_offset
    ]
    pre_signal_deactivations = [
        row for row in deactivation_rows if signal_offset is None or int(row["offset"]) <= signal_offset
    ]
    before_signal_row = None
    if first_signal:
        previous = [row for row in timeline_rows if int(row["offset"]) < int(first_signal["offset"])]
        before_signal_row = previous[-1] if previous else checkpoint_row
    final_row = timeline_rows[-1]
    return {
        **case["ids"],
        "first_component_change_offset": "" if first_signal is None else int(first_signal["offset"]),
        "first_component_change_tick": "" if first_signal is None else int(first_signal["tick"]),
        "first_component_change_delta_from_checkpoint": (
            "" if first_signal is None else int(first_signal["coherence_count_delta_from_checkpoint"])
        ),
        "first_component_split_offset": "" if first_split is None else int(first_split["offset"]),
        "first_component_split_tick": "" if first_split is None else int(first_split["tick"]),
        "component_signal_offsets": ";".join(str(int(row["offset"])) for row in signal_rows),
        "component_signal_vanish_offset": "" if vanish_row is None else int(vanish_row["offset"]),
        "component_signal_vanish_tick": "" if vanish_row is None else int(vanish_row["tick"]),
        "pre_signal_residual_events": len(pre_signal_events),
        "pre_signal_global_bridge_events": sum(
            1 for row in pre_signal_events if int(row["global_bridge_pre"]) == 1
        ),
        "pre_signal_event_component_bridge_events": sum(
            1 for row in pre_signal_events if row["event_geometry_class"] == "component_bridge_cube26"
        ),
        "pre_signal_scoring_component_bridge_events": sum(
            1 for row in pre_signal_events if row["scoring_geometry_class"] == "component_bridge_cube26"
        ),
        "pre_signal_high_abs_L_contrast_events": sum(
            1 for row in pre_signal_events if abs(float(row["L_contrast"])) >= HIGH_ABS_L_CONTRAST
        ),
        "pre_signal_deactivations": len(pre_signal_deactivations),
        "pre_signal_articulation_deactivations": sum(
            1 for row in pre_signal_deactivations if int(row["single_removal_articulation"]) == 1
        ),
        "first_signal_preceded_by_adjacency_delta": (
            ""
            if first_signal is None or before_signal_row is None
            else float(before_signal_row["active_depleted_adjacency"])
            - float(checkpoint_row["active_depleted_adjacency"])
        ),
        "active_depleted_adjacency_at_checkpoint": float(checkpoint_row["active_depleted_adjacency"]),
        "active_depleted_adjacency_before_signal": (
            "" if before_signal_row is None else float(before_signal_row["active_depleted_adjacency"])
        ),
        "active_depleted_adjacency_at_signal": (
            "" if first_signal is None else float(first_signal["active_depleted_adjacency"])
        ),
        "residual_event_count": len(event_rows),
        "global_bridge_event_count": sum(1 for row in event_rows if int(row["global_bridge_pre"]) == 1),
        "event_component_bridge_count": sum(
            1 for row in event_rows if row["event_geometry_class"] == "component_bridge_cube26"
        ),
        "scoring_component_bridge_count": sum(
            1 for row in event_rows if row["scoring_geometry_class"] == "component_bridge_cube26"
        ),
        "high_abs_L_contrast_event_count": sum(
            1 for row in event_rows if abs(float(row["L_contrast"])) >= HIGH_ABS_L_CONTRAST
        ),
        "deactivation_count": len(deactivation_rows),
        "articulation_deactivation_count": sum(
            1 for row in deactivation_rows if int(row["single_removal_articulation"]) == 1
        ),
        "component_count_final": int(final_row["coherence_count_cube26"]),
        "component_count_checkpoint": int(checkpoint_row["coherence_count_cube26"]),
        "largest_final": int(final_row["largest_coherence_cube26"]),
        "largest_checkpoint": int(checkpoint_row["largest_coherence_cube26"]),
        "ledger_exact": csv_bool(all(abs(float(row["ledger_error"])) == 0.0 for row in timeline_rows)),
    }


def run_trace(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    cfg = load_config(args.config)
    constants = cfg.get("constants", {})
    if str(constants.get("conservation", "soft")) != "hard":
        raise SystemExit("component bridge causal trace currently supports hard conservation configs only")
    checkpoint_tick = int(args.checkpoint_tick)
    checkpoint_path = Path(args.checkpoint_state_dir) / f"checkpoint_tick_{checkpoint_tick:06d}.npz"
    checkpoint = load_checkpoint(checkpoint_path)
    continuation_seed = (
        int(args.continuation_seed)
        if args.continuation_seed is not None
        else deterministic_continuation_seed(
            int(args.rng_seed_base),
            checkpoint_tick,
            int(args.sample_index),
        )
    )
    world = clone_world(checkpoint, continuation_seed)
    init_seed = int(cfg.get("init", {}).get("seed", -1))
    case = {
        "ids": {
            "case_label": str(args.label),
            "init_seed": init_seed,
            "checkpoint_tick": checkpoint_tick,
            "sample_index": int(args.sample_index),
            "continuation_seed": continuation_seed,
        },
        "checkpoint_tick": checkpoint_tick,
        "wrap": bool(world.wrap),
    }
    checkpoint_active = world.active.copy()
    ever_active = world.active.copy()
    first_residual_activation_offsets: dict[tuple[int, int, int], int] = {}
    latest_residual_activation_offsets: dict[tuple[int, int, int], int] = {}
    event_rows: list[dict[str, Any]] = []
    deactivation_rows: list[dict[str, Any]] = []
    timeline_rows: list[dict[str, Any]] = []

    checkpoint_metrics = collect_metrics(world, checkpoint_tick)
    checkpoint_metrics.update(interface_metrics(world, "cube26"))
    initial_row = timeline_row(
        world,
        case,
        0,
        int(args.phase_length),
        checkpoint_metrics,
        None,
        [],
        [],
    )
    timeline_rows.append({key: value for key, value in initial_row.items() if key != "_metrics"})
    previous_metrics = initial_row["_metrics"]

    for offset in range(1, int(args.horizon) + 1):
        event_start = len(event_rows)
        deactivation_start = len(deactivation_rows)
        traced_hard_step(
            world,
            cfg,
            case,
            offset,
            event_rows,
            deactivation_rows,
            checkpoint_active,
            ever_active,
            first_residual_activation_offsets,
            latest_residual_activation_offsets,
        )
        update_event_persistence(event_rows, world, offset)
        tick_events = event_rows[event_start:]
        tick_deactivations = deactivation_rows[deactivation_start:]
        row = timeline_row(
            world,
            case,
            offset,
            int(args.phase_length),
            checkpoint_metrics,
            previous_metrics,
            tick_events,
            tick_deactivations,
        )
        previous_metrics = row["_metrics"]
        timeline_rows.append({key: value for key, value in row.items() if key != "_metrics"})

    finalize_event_persistence(event_rows, world)
    summary_row = build_summary(case, timeline_rows, event_rows, deactivation_rows)
    return event_rows, deactivation_rows, timeline_rows, summary_row


def main() -> None:
    args = parse_args()
    event_rows, deactivation_rows, timeline_rows, summary_row = run_trace(args)
    output_prefix = Path(args.output_prefix)
    write_csv(output_prefix.with_name(output_prefix.name + "_events.csv"), EVENT_FIELDNAMES, event_rows)
    write_csv(
        output_prefix.with_name(output_prefix.name + "_deactivations.csv"),
        DEACTIVATION_FIELDNAMES,
        deactivation_rows,
    )
    write_csv(output_prefix.with_name(output_prefix.name + "_timeline.csv"), TIMELINE_FIELDNAMES, timeline_rows)
    write_csv(output_prefix.with_name(output_prefix.name + "_summary.csv"), SUMMARY_FIELDNAMES, [summary_row])
    class_counts = Counter(str(row["event_geometry_class"]) for row in event_rows)
    scoring_class_counts = Counter(str(row["scoring_geometry_class"]) for row in event_rows)
    payload = {
        "summary": summary_row,
        "event_geometry_counts": dict(sorted(class_counts.items())),
        "scoring_geometry_counts": dict(sorted(scoring_class_counts.items())),
        "event_csv": str(output_prefix.with_name(output_prefix.name + "_events.csv")),
        "deactivation_csv": str(output_prefix.with_name(output_prefix.name + "_deactivations.csv")),
        "timeline_csv": str(output_prefix.with_name(output_prefix.name + "_timeline.csv")),
        "summary_csv": str(output_prefix.with_name(output_prefix.name + "_summary.csv")),
    }
    json_path = output_prefix.with_name(output_prefix.name + "_summary.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(
        f"{args.label}: residual_events={len(event_rows)} deactivations={len(deactivation_rows)} "
        f"first_component_change_offset={summary_row['first_component_change_offset']}"
    )


if __name__ == "__main__":
    main()
