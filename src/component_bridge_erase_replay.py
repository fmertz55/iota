from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from component_bridge_causal_trace import (
    DEACTIVATION_FIELDNAMES,
    EVENT_FIELDNAMES,
    HIGH_ABS_L_CONTRAST,
    SUMMARY_FIELDNAMES,
    TIMELINE_FIELDNAMES,
    build_summary,
    csv_bool,
    finalize_event_persistence,
    geometry_from_mask,
    interface_metrics,
    timeline_row,
    traced_hard_step,
    update_event_persistence,
    write_csv,
)
from continuation import clone_world, deterministic_continuation_seed, load_checkpoint
from iota_rig import World, load_config
from metrics import collect_metrics


PIVOTAL_OFFSET = 499
PIVOTAL_SOURCE = (12, 3, 38)
PIVOTAL_TARGET = (13, 3, 38)
SPLIT_OFFSET = 512
SPLIT_SOURCE = (13, 3, 38)
SPLIT_TARGET = (12, 2, 38)
REBRIDGE_OFFSET = 515
REBRIDGE_SOURCE = (12, 2, 38)
REBRIDGE_TARGET = (13, 2, 38)
CAUSAL_CELLS = {
    PIVOTAL_SOURCE,
    PIVOTAL_TARGET,
    SPLIT_TARGET,
    REBRIDGE_TARGET,
}

VARIANTS = (
    "natural",
    "erase_pivotal_transfer",
    "erase_pivotal_L",
    "erase_pivotal_memory",
    "transplant_pivotal_state",
)

WINDOWS = (
    ("before_pivotal", 1, PIVOTAL_OFFSET - 1),
    ("pivotal_to_split", PIVOTAL_OFFSET, SPLIT_OFFSET - 1),
    ("split_tick", SPLIT_OFFSET, SPLIT_OFFSET),
    ("post_split", SPLIT_OFFSET + 1, 1024),
)

INTERVENTION_FIELDNAMES = [
    "case_label",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "variant",
    "offset",
    "intervention",
    "applied",
    "event_found",
    "source_x",
    "source_y",
    "source_z",
    "target_x",
    "target_y",
    "target_z",
    "transplant_x",
    "transplant_y",
    "transplant_z",
    "source_active_pre",
    "source_A_pre",
    "source_active_post_natural",
    "source_A_post_natural",
    "source_active_after",
    "source_A_after",
    "target_active_pre",
    "target_A_pre",
    "target_L_pre",
    "target_V_pre",
    "target_P_pre",
    "target_R_pre",
    "target_active_post_natural",
    "target_A_post_natural",
    "target_L_post_natural",
    "target_V_post_natural",
    "target_P_post_natural",
    "target_R_post_natural",
    "target_active_after",
    "target_A_after",
    "target_L_after",
    "target_V_after",
    "target_P_after",
    "target_R_after",
    "ledger_error_after",
    "notes",
]

WINDOW_FIELDNAMES = [
    "case_label",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "variant",
    "window",
    "start_offset",
    "end_offset",
    "residual_event_count",
    "global_bridge_event_count",
    "event_component_bridge_count",
    "scoring_component_bridge_count",
    "local_bridge_face6_count",
    "high_abs_L_contrast_count",
    "mean_abs_L_contrast",
    "max_abs_L_contrast",
    "touches_causal_cell_count",
    "near_causal_cell_count",
    "source_is_pivotal_target_count",
    "target_is_split_target_count",
    "target_is_rebridge_target_count",
    "deactivation_count",
    "articulation_deactivation_count",
    "causal_cell_deactivation_count",
    "component_signal_tick_count",
    "max_abs_component_delta_from_checkpoint",
    "max_positive_component_delta_from_previous",
    "max_negative_component_delta_from_previous",
]

COUNTERFACTUAL_SUMMARY_FIELDNAMES = SUMMARY_FIELDNAMES + [
    "variant",
    "has_component_signal",
    "split_at_512",
    "rebridge_at_515",
    "pivotal_target_active_499",
    "pivotal_target_active_511",
    "pivotal_target_active_512",
    "split_target_active_512",
    "split_target_active_515",
    "rebridge_target_active_515",
    "causal_path_event_count_499_515",
    "causal_path_articulation_deactivation_count_499_515",
    "ledger_error_final",
]


@dataclass(frozen=True)
class CellSnapshot:
    active: bool
    A: int
    R: int
    V: int
    P: int
    latent_A: int
    L: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run erase-and-replay interventions against the v0.3.6 seed-46 "
            "component-bridge trajectory."
        )
    )
    parser.add_argument("--label", default="finding_049_seed46_erase_replay")
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint-state-dir", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--sample-index", type=int, default=6)
    parser.add_argument("--continuation-seed", type=int, default=None)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--horizon", type=int, default=1024)
    parser.add_argument("--phase-length", type=int, default=256)
    parser.add_argument(
        "--variants",
        nargs="+",
        choices=VARIANTS,
        default=list(VARIANTS),
        help="Counterfactual variants to run.",
    )
    return parser.parse_args()


def snapshot_cell(world: World, cell: tuple[int, int, int]) -> CellSnapshot:
    return CellSnapshot(
        active=bool(world.active[cell]),
        A=int(world.A[cell]),
        R=int(world.R[cell]),
        V=int(world.V[cell]),
        P=int(world.P[cell]),
        latent_A=int(world.latent_A[cell]),
        L=float(world.angular_L[cell]),
    )


def restore_cell(world: World, cell: tuple[int, int, int], snapshot: CellSnapshot) -> None:
    world.active[cell] = bool(snapshot.active)
    world.A[cell] = int(snapshot.A)
    world.R[cell] = np.uint8(snapshot.R)
    world.V[cell] = np.uint8(snapshot.V)
    world.P[cell] = np.uint8(snapshot.P)
    world.latent_A[cell] = int(snapshot.latent_A)
    world.angular_L[cell] = np.float32(snapshot.L)


def ledger_error(world: World) -> float:
    total = int(np.sum(world.A[world.active], dtype=np.int64))
    total += int(np.sum(world.latent_A[~world.active], dtype=np.int64))
    return float(total - int(world.initial_total_A))


def coord_to_fields(prefix: str, coord: tuple[int, int, int] | None) -> dict[str, Any]:
    if coord is None:
        return {f"{prefix}_x": "", f"{prefix}_y": "", f"{prefix}_z": ""}
    return {f"{prefix}_x": coord[0], f"{prefix}_y": coord[1], f"{prefix}_z": coord[2]}


def cell_after_fields(world: World, prefix: str, cell: tuple[int, int, int]) -> dict[str, Any]:
    snapshot = snapshot_cell(world, cell)
    return {
        f"{prefix}_active_after": csv_bool(snapshot.active),
        f"{prefix}_A_after": snapshot.A,
        f"{prefix}_L_after": snapshot.L,
        f"{prefix}_V_after": snapshot.V,
        f"{prefix}_P_after": snapshot.P,
        f"{prefix}_R_after": snapshot.R,
    }


def snapshot_fields(prefix: str, snapshot: CellSnapshot, suffix: str) -> dict[str, Any]:
    return {
        f"{prefix}_active_{suffix}": csv_bool(snapshot.active),
        f"{prefix}_A_{suffix}": snapshot.A,
        f"{prefix}_L_{suffix}": snapshot.L,
        f"{prefix}_V_{suffix}": snapshot.V,
        f"{prefix}_P_{suffix}": snapshot.P,
        f"{prefix}_R_{suffix}": snapshot.R,
    }


def chebyshev_distance(
    left: tuple[int, int, int],
    right: tuple[int, int, int],
    size: int,
    wrap: bool,
) -> int:
    distances = []
    for left_value, right_value in zip(left, right, strict=True):
        distance = abs(int(left_value) - int(right_value))
        if wrap:
            distance = min(distance, size - distance)
        distances.append(distance)
    return int(max(distances))


def candidate_coords(
    anchor: tuple[int, int, int],
    radius: int,
    size: int,
    wrap: bool,
) -> list[tuple[int, int, int]]:
    ax, ay, az = anchor
    coords: list[tuple[int, int, int]] = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                x, y, z = ax + dx, ay + dy, az + dz
                if wrap:
                    coords.append((x % size, y % size, z % size))
                elif 0 <= x < size and 0 <= y < size and 0 <= z < size:
                    coords.append((x, y, z))
    return sorted(set(coords))


def choose_transplant_target(
    world: World,
    source: tuple[int, int, int],
    target: tuple[int, int, int],
    event_row: dict[str, Any] | None,
) -> tuple[int, int, int] | None:
    desired_class = "" if event_row is None else str(event_row["event_geometry_class"])
    desired_face6 = 0 if event_row is None else int(event_row["event_face6_neighbors"])
    desired_cube26 = 0 if event_row is None else int(event_row["event_cube26_neighbors"])
    size = int(world.active.shape[0])
    best: tuple[Any, tuple[int, int, int]] | None = None
    for radius in (1, 2, 3):
        for coord in candidate_coords(target, radius, size, bool(world.wrap)):
            if coord in CAUSAL_CELLS or coord == source:
                continue
            if bool(world.active[coord]) or int(world.latent_A[coord]) != 0:
                continue
            geometry = geometry_from_mask(world.active, coord, bool(world.wrap))
            class_penalty = 0 if str(geometry["class"]) == desired_class else 1
            support_delta = abs(int(geometry["face6_neighbors"]) - desired_face6)
            support_delta += abs(int(geometry["cube26_neighbors"]) - desired_cube26)
            source_distance = chebyshev_distance(coord, source, size, bool(world.wrap))
            target_distance = chebyshev_distance(coord, target, size, bool(world.wrap))
            score = (
                class_penalty,
                target_distance,
                support_delta,
                source_distance,
                coord,
            )
            if best is None or score < best[0]:
                best = (score, coord)
        if best is not None and best[0][0] == 0:
            return best[1]
    return None if best is None else best[1]


def event_matches(row: dict[str, Any], source: tuple[int, int, int], target: tuple[int, int, int]) -> bool:
    return (
        (int(row["source_x"]), int(row["source_y"]), int(row["source_z"])) == source
        and (int(row["target_x"]), int(row["target_y"]), int(row["target_z"])) == target
    )


def find_pivotal_event(tick_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in tick_events:
        if event_matches(row, PIVOTAL_SOURCE, PIVOTAL_TARGET):
            return row
    return None


def set_lineage_dicts(
    first_offsets: dict[tuple[int, int, int], int],
    latest_offsets: dict[tuple[int, int, int], int],
    first_before: dict[tuple[int, int, int], int],
    latest_before: dict[tuple[int, int, int], int],
) -> None:
    first_offsets.clear()
    first_offsets.update(first_before)
    latest_offsets.clear()
    latest_offsets.update(latest_before)


def apply_intervention(
    variant: str,
    world: World,
    case: dict[str, Any],
    offset: int,
    event_rows: list[dict[str, Any]],
    deactivation_rows: list[dict[str, Any]],
    tick_events: list[dict[str, Any]],
    tick_deactivations: list[dict[str, Any]],
    pre_snapshots: dict[tuple[int, int, int], CellSnapshot],
    first_offsets: dict[tuple[int, int, int], int],
    latest_offsets: dict[tuple[int, int, int], int],
    first_offsets_before: dict[tuple[int, int, int], int],
    latest_offsets_before: dict[tuple[int, int, int], int],
    ever_active: np.ndarray,
) -> dict[str, Any] | None:
    if variant == "natural" or offset != PIVOTAL_OFFSET:
        return None

    event_row = find_pivotal_event(tick_events)
    source_pre = pre_snapshots[PIVOTAL_SOURCE]
    target_pre = pre_snapshots[PIVOTAL_TARGET]
    source_post = snapshot_cell(world, PIVOTAL_SOURCE)
    target_post = snapshot_cell(world, PIVOTAL_TARGET)
    transplant_target: tuple[int, int, int] | None = None
    notes = ""
    applied = event_row is not None

    if event_row is None:
        notes = "pivotal event not present"
    elif variant == "erase_pivotal_transfer":
        restore_cell(world, PIVOTAL_SOURCE, source_pre)
        restore_cell(world, PIVOTAL_TARGET, target_pre)
        set_lineage_dicts(first_offsets, latest_offsets, first_offsets_before, latest_offsets_before)
        event_rows[:] = [
            row
            for row in event_rows
            if not (int(row["offset"]) == offset and event_matches(row, PIVOTAL_SOURCE, PIVOTAL_TARGET))
        ]
        tick_events[:] = [
            row
            for row in tick_events
            if not event_matches(row, PIVOTAL_SOURCE, PIVOTAL_TARGET)
        ]
        deactivation_rows[:] = [
            row
            for row in deactivation_rows
            if not (
                int(row["offset"]) == offset
                and (int(row["cell_x"]), int(row["cell_y"]), int(row["cell_z"])) == PIVOTAL_SOURCE
            )
        ]
        tick_deactivations[:] = [
            row
            for row in tick_deactivations
            if (int(row["cell_x"]), int(row["cell_y"]), int(row["cell_z"])) != PIVOTAL_SOURCE
        ]
        notes = "restored pivotal source and target to pre-kick state"
    elif variant == "erase_pivotal_L":
        world.angular_L[PIVOTAL_TARGET] = np.float32(target_pre.L)
        set_lineage_dicts(first_offsets, latest_offsets, first_offsets_before, latest_offsets_before)
        notes = "preserved activation and vector state; restored target angular_L"
    elif variant == "erase_pivotal_memory":
        world.R[PIVOTAL_TARGET] = np.uint8(target_pre.R)
        world.V[PIVOTAL_TARGET] = np.uint8(target_pre.V)
        world.P[PIVOTAL_TARGET] = np.uint8(target_pre.P)
        world.angular_L[PIVOTAL_TARGET] = np.float32(target_pre.L)
        set_lineage_dicts(first_offsets, latest_offsets, first_offsets_before, latest_offsets_before)
        notes = "preserved activation/A; restored target R/V/P/angular_L"
    elif variant == "transplant_pivotal_state":
        transplant_target = choose_transplant_target(world, PIVOTAL_SOURCE, PIVOTAL_TARGET, event_row)
        if transplant_target is None:
            applied = False
            notes = "no depleted nearby transplant target found"
        else:
            restore_cell(world, PIVOTAL_TARGET, target_pre)
            world.active[transplant_target] = bool(target_post.active)
            world.A[transplant_target] = int(target_post.A)
            world.R[transplant_target] = np.uint8(target_post.R)
            world.V[transplant_target] = np.uint8(target_post.V)
            world.P[transplant_target] = np.uint8(target_post.P)
            world.latent_A[transplant_target] = int(target_post.latent_A)
            world.angular_L[transplant_target] = np.float32(target_post.L)
            set_lineage_dicts(first_offsets, latest_offsets, first_offsets_before, latest_offsets_before)
            first_offsets.setdefault(transplant_target, offset)
            latest_offsets[transplant_target] = offset
            ever_active[transplant_target] = True
            notes = "moved post-kick target state to matched nearby depleted site"
    else:
        raise ValueError(f"unknown variant: {variant}")

    ever_active |= world.active
    return {
        **case["ids"],
        "variant": variant,
        "offset": offset,
        "intervention": variant,
        "applied": csv_bool(applied),
        "event_found": csv_bool(event_row is not None),
        **coord_to_fields("source", PIVOTAL_SOURCE),
        **coord_to_fields("target", PIVOTAL_TARGET),
        **coord_to_fields("transplant", transplant_target),
        **snapshot_fields("source", source_pre, "pre"),
        "source_active_post_natural": csv_bool(source_post.active),
        "source_A_post_natural": source_post.A,
        "source_active_after": csv_bool(bool(world.active[PIVOTAL_SOURCE])),
        "source_A_after": int(world.A[PIVOTAL_SOURCE]),
        **snapshot_fields("target", target_pre, "pre"),
        "target_active_post_natural": csv_bool(target_post.active),
        "target_A_post_natural": target_post.A,
        "target_L_post_natural": target_post.L,
        "target_V_post_natural": target_post.V,
        "target_P_post_natural": target_post.P,
        "target_R_post_natural": target_post.R,
        **cell_after_fields(world, "target", PIVOTAL_TARGET),
        "ledger_error_after": ledger_error(world),
        "notes": notes,
    }


def row_coord(row: dict[str, Any], prefix: str) -> tuple[int, int, int]:
    return (
        int(row[f"{prefix}_x"]),
        int(row[f"{prefix}_y"]),
        int(row[f"{prefix}_z"]),
    )


def touches_causal_cell(row: dict[str, Any]) -> bool:
    return row_coord(row, "source") in CAUSAL_CELLS or row_coord(row, "target") in CAUSAL_CELLS


def near_causal_cell(row: dict[str, Any], size: int, wrap: bool) -> bool:
    source = row_coord(row, "source")
    target = row_coord(row, "target")
    for cell in CAUSAL_CELLS:
        if chebyshev_distance(source, cell, size, wrap) <= 1:
            return True
        if chebyshev_distance(target, cell, size, wrap) <= 1:
            return True
    return False


def causal_cell_deactivation(row: dict[str, Any]) -> bool:
    return (int(row["cell_x"]), int(row["cell_y"]), int(row["cell_z"])) in CAUSAL_CELLS


def summarize_window(
    case: dict[str, Any],
    variant: str,
    window_name: str,
    start_offset: int,
    end_offset: int,
    event_rows: list[dict[str, Any]],
    deactivation_rows: list[dict[str, Any]],
    timeline_rows: list[dict[str, Any]],
    size: int,
    wrap: bool,
) -> dict[str, Any]:
    events = [
        row
        for row in event_rows
        if start_offset <= int(row["offset"]) <= min(end_offset, int(timeline_rows[-1]["offset"]))
    ]
    deactivations = [
        row
        for row in deactivation_rows
        if start_offset <= int(row["offset"]) <= min(end_offset, int(timeline_rows[-1]["offset"]))
    ]
    timeline = [
        row
        for row in timeline_rows
        if start_offset <= int(row["offset"]) <= min(end_offset, int(timeline_rows[-1]["offset"]))
    ]
    abs_contrasts = [abs(float(row["L_contrast"])) for row in events]
    deltas_from_checkpoint = [abs(int(row["coherence_count_delta_from_checkpoint"])) for row in timeline]
    deltas_from_previous = [int(row["coherence_count_delta_from_previous"]) for row in timeline]
    return {
        **case["ids"],
        "variant": variant,
        "window": window_name,
        "start_offset": start_offset,
        "end_offset": min(end_offset, int(timeline_rows[-1]["offset"])),
        "residual_event_count": len(events),
        "global_bridge_event_count": sum(1 for row in events if int(row["global_bridge_pre"]) == 1),
        "event_component_bridge_count": sum(
            1 for row in events if row["event_geometry_class"] == "component_bridge_cube26"
        ),
        "scoring_component_bridge_count": sum(
            1 for row in events if row["scoring_geometry_class"] == "component_bridge_cube26"
        ),
        "local_bridge_face6_count": sum(
            1 for row in events if row["event_geometry_class"] == "local_bridge_face6"
        ),
        "high_abs_L_contrast_count": sum(
            1 for value in abs_contrasts if value >= HIGH_ABS_L_CONTRAST
        ),
        "mean_abs_L_contrast": float(np.mean(abs_contrasts)) if abs_contrasts else 0.0,
        "max_abs_L_contrast": float(max(abs_contrasts)) if abs_contrasts else 0.0,
        "touches_causal_cell_count": sum(1 for row in events if touches_causal_cell(row)),
        "near_causal_cell_count": sum(1 for row in events if near_causal_cell(row, size, wrap)),
        "source_is_pivotal_target_count": sum(
            1 for row in events if row_coord(row, "source") == PIVOTAL_TARGET
        ),
        "target_is_split_target_count": sum(
            1 for row in events if row_coord(row, "target") == SPLIT_TARGET
        ),
        "target_is_rebridge_target_count": sum(
            1 for row in events if row_coord(row, "target") == REBRIDGE_TARGET
        ),
        "deactivation_count": len(deactivations),
        "articulation_deactivation_count": sum(
            1 for row in deactivations if int(row["single_removal_articulation"]) == 1
        ),
        "causal_cell_deactivation_count": sum(1 for row in deactivations if causal_cell_deactivation(row)),
        "component_signal_tick_count": sum(
            1 for row in timeline if int(row["coherence_count_delta_from_checkpoint"]) != 0
        ),
        "max_abs_component_delta_from_checkpoint": max(deltas_from_checkpoint) if deltas_from_checkpoint else 0,
        "max_positive_component_delta_from_previous": (
            max([value for value in deltas_from_previous if value > 0], default=0)
        ),
        "max_negative_component_delta_from_previous": (
            min([value for value in deltas_from_previous if value < 0], default=0)
        ),
    }


def active_at_offset(
    timeline_cells: dict[tuple[int, int, int], dict[int, int]],
    cell: tuple[int, int, int],
    offset: int,
) -> str:
    return str(timeline_cells.get(cell, {}).get(offset, ""))


def extend_summary(
    variant: str,
    summary: dict[str, Any],
    event_rows: list[dict[str, Any]],
    deactivation_rows: list[dict[str, Any]],
    timeline_rows: list[dict[str, Any]],
    timeline_cells: dict[tuple[int, int, int], dict[int, int]],
) -> dict[str, Any]:
    signal_offsets = str(summary["component_signal_offsets"])
    events_499_515 = [
        row
        for row in event_rows
        if PIVOTAL_OFFSET <= int(row["offset"]) <= REBRIDGE_OFFSET and touches_causal_cell(row)
    ]
    deactivations_499_515 = [
        row
        for row in deactivation_rows
        if PIVOTAL_OFFSET <= int(row["offset"]) <= REBRIDGE_OFFSET
        and causal_cell_deactivation(row)
        and int(row["single_removal_articulation"]) == 1
    ]
    final_row = timeline_rows[-1]
    return {
        **summary,
        "variant": variant,
        "has_component_signal": csv_bool(bool(signal_offsets)),
        "split_at_512": csv_bool(
            any(
                int(row["offset"]) == SPLIT_OFFSET
                and int(row["coherence_count_delta_from_previous"]) > 0
                for row in timeline_rows
            )
        ),
        "rebridge_at_515": csv_bool(
            any(
                int(row["offset"]) == REBRIDGE_OFFSET
                and int(row["coherence_count_delta_from_previous"]) < 0
                for row in timeline_rows
            )
        ),
        "pivotal_target_active_499": active_at_offset(timeline_cells, PIVOTAL_TARGET, PIVOTAL_OFFSET),
        "pivotal_target_active_511": active_at_offset(timeline_cells, PIVOTAL_TARGET, SPLIT_OFFSET - 1),
        "pivotal_target_active_512": active_at_offset(timeline_cells, PIVOTAL_TARGET, SPLIT_OFFSET),
        "split_target_active_512": active_at_offset(timeline_cells, SPLIT_TARGET, SPLIT_OFFSET),
        "split_target_active_515": active_at_offset(timeline_cells, SPLIT_TARGET, REBRIDGE_OFFSET),
        "rebridge_target_active_515": active_at_offset(timeline_cells, REBRIDGE_TARGET, REBRIDGE_OFFSET),
        "causal_path_event_count_499_515": len(events_499_515),
        "causal_path_articulation_deactivation_count_499_515": len(deactivations_499_515),
        "ledger_error_final": float(final_row["ledger_error"]),
    }


def run_variant(
    args: argparse.Namespace,
    cfg: dict[str, Any],
    checkpoint: World,
    variant: str,
    continuation_seed: int,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    checkpoint_tick = int(args.checkpoint_tick)
    world = clone_world(checkpoint, continuation_seed)
    init_seed = int(cfg.get("init", {}).get("seed", -1))
    case = {
        "ids": {
            "case_label": variant,
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
    intervention_rows: list[dict[str, Any]] = []
    timeline_cells = {cell: {0: csv_bool(bool(world.active[cell]))} for cell in CAUSAL_CELLS}

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
        pre_snapshots = {
            PIVOTAL_SOURCE: snapshot_cell(world, PIVOTAL_SOURCE),
            PIVOTAL_TARGET: snapshot_cell(world, PIVOTAL_TARGET),
        }
        first_offsets_before = dict(first_residual_activation_offsets)
        latest_offsets_before = dict(latest_residual_activation_offsets)
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
        tick_events = event_rows[event_start:]
        tick_deactivations = deactivation_rows[deactivation_start:]
        intervention_row = apply_intervention(
            variant,
            world,
            case,
            offset,
            event_rows,
            deactivation_rows,
            tick_events,
            tick_deactivations,
            pre_snapshots,
            first_residual_activation_offsets,
            latest_residual_activation_offsets,
            first_offsets_before,
            latest_offsets_before,
            ever_active,
        )
        if intervention_row is not None:
            intervention_rows.append(intervention_row)
        update_event_persistence(event_rows, world, offset)
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
        for cell in CAUSAL_CELLS:
            timeline_cells[cell][offset] = csv_bool(bool(world.active[cell]))

    finalize_event_persistence(event_rows, world)
    summary_row = build_summary(case, timeline_rows, event_rows, deactivation_rows)
    extended_summary = extend_summary(
        variant,
        summary_row,
        event_rows,
        deactivation_rows,
        timeline_rows,
        timeline_cells,
    )
    window_rows = [
        summarize_window(
            case,
            variant,
            window_name,
            start_offset,
            end_offset,
            event_rows,
            deactivation_rows,
            timeline_rows,
            int(world.active.shape[0]),
            bool(world.wrap),
        )
        for window_name, start_offset, end_offset in WINDOWS
    ]
    return event_rows, deactivation_rows, timeline_rows, extended_summary, intervention_rows, window_rows


def run_all(args: argparse.Namespace) -> dict[str, Any]:
    cfg = load_config(args.config)
    constants = cfg.get("constants", {})
    if str(constants.get("conservation", "soft")) != "hard":
        raise SystemExit("component bridge erase replay currently supports hard conservation configs only")
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

    all_events: list[dict[str, Any]] = []
    all_deactivations: list[dict[str, Any]] = []
    all_timeline: list[dict[str, Any]] = []
    all_summaries: list[dict[str, Any]] = []
    all_interventions: list[dict[str, Any]] = []
    all_windows: list[dict[str, Any]] = []

    for variant in args.variants:
        events, deactivations, timeline, summary, interventions, windows = run_variant(
            args,
            cfg,
            checkpoint,
            variant,
            continuation_seed,
        )
        all_events.extend(events)
        all_deactivations.extend(deactivations)
        all_timeline.extend(timeline)
        all_summaries.append(summary)
        all_interventions.extend(interventions)
        all_windows.extend(windows)
        print(
            f"{variant}: residual_events={len(events)} deactivations={len(deactivations)} "
            f"first_component_change_offset={summary['first_component_change_offset']} "
            f"split_at_512={summary['split_at_512']} rebridge_at_515={summary['rebridge_at_515']}"
        )

    return {
        "events": all_events,
        "deactivations": all_deactivations,
        "timeline": all_timeline,
        "summaries": all_summaries,
        "interventions": all_interventions,
        "windows": all_windows,
    }


def main() -> None:
    args = parse_args()
    payload = run_all(args)
    output_prefix = Path(args.output_prefix)
    write_csv(output_prefix.with_name(output_prefix.name + "_events.csv"), EVENT_FIELDNAMES, payload["events"])
    write_csv(
        output_prefix.with_name(output_prefix.name + "_deactivations.csv"),
        DEACTIVATION_FIELDNAMES,
        payload["deactivations"],
    )
    write_csv(output_prefix.with_name(output_prefix.name + "_timeline.csv"), TIMELINE_FIELDNAMES, payload["timeline"])
    write_csv(
        output_prefix.with_name(output_prefix.name + "_summary.csv"),
        COUNTERFACTUAL_SUMMARY_FIELDNAMES,
        payload["summaries"],
    )
    write_csv(
        output_prefix.with_name(output_prefix.name + "_interventions.csv"),
        INTERVENTION_FIELDNAMES,
        payload["interventions"],
    )
    write_csv(
        output_prefix.with_name(output_prefix.name + "_windows.csv"),
        WINDOW_FIELDNAMES,
        payload["windows"],
    )

    summary_by_variant = {str(row["variant"]): row for row in payload["summaries"]}
    event_counts = Counter(str(row["case_label"]) for row in payload["events"])
    deactivation_counts = Counter(str(row["case_label"]) for row in payload["deactivations"])
    json_payload = {
        "label": args.label,
        "summary_by_variant": summary_by_variant,
        "event_counts": dict(sorted(event_counts.items())),
        "deactivation_counts": dict(sorted(deactivation_counts.items())),
        "events_csv": str(output_prefix.with_name(output_prefix.name + "_events.csv")),
        "deactivations_csv": str(output_prefix.with_name(output_prefix.name + "_deactivations.csv")),
        "timeline_csv": str(output_prefix.with_name(output_prefix.name + "_timeline.csv")),
        "summary_csv": str(output_prefix.with_name(output_prefix.name + "_summary.csv")),
        "interventions_csv": str(output_prefix.with_name(output_prefix.name + "_interventions.csv")),
        "windows_csv": str(output_prefix.with_name(output_prefix.name + "_windows.csv")),
    }
    json_path = output_prefix.with_name(output_prefix.name + "_summary.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(json_payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


if __name__ == "__main__":
    main()
