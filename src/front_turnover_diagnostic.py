from __future__ import annotations

import argparse
import copy
import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from iota_rig import World, candidate_neighbor_steps, init_world, load_config, save_world_state, step
from metrics import collect_metrics


COUNT_KEYS = {
    "exchanges",
    "secondary_exchanges",
    "payload_changes",
    "deactivation_events",
    "amplitude_transfers",
    "failed_transfer_gates",
    "secondary_vector_kicks",
    "residual_participations",
    "depleted_reactivations",
    "rotation_events",
    "rotation_events_on_residual_entry",
    "rotation_events_on_secondary_exchange",
    "angular_momentum_updates",
    "angular_momentum_biased_rotation_events",
    "angular_momentum_bias_abs_sum",
    "angular_momentum_observed_turn_abs_sum",
}

MASK_PREFIXES = (
    "active",
    "depleted",
    "active_interface",
    "depleted_interface",
    "interface_union",
)

MASK_DELTA_SUFFIXES = (
    "previous_cells",
    "current_cells",
    "retained_cells",
    "new_cells",
    "lost_cells",
    "retention_fraction",
    "current_from_previous_fraction",
    "birth_fraction",
    "loss_fraction",
    "jaccard",
    "turnover_fraction",
)

CONTENT_PREFIXES = (
    "persistent_active",
    "persistent_active_interface",
)

CONTENT_DELTA_SUFFIXES = (
    "cells",
    "any_changed",
    "any_changed_fraction",
    "A_changed",
    "A_changed_fraction",
    "R_changed",
    "R_changed_fraction",
    "V_changed",
    "V_changed_fraction",
    "P_changed",
    "P_changed_fraction",
    "mean_abs_A_delta",
)

FIELDNAMES = [
    "tick",
    "previous_tick",
    "window_ticks",
    "connectivity",
    "active_iotas",
    "depleted_cells",
    "active_interface_cells",
    "depleted_interface_cells",
    "interface_union_cells",
    "total_A",
    "active_A",
    "latent_A",
    "ledger_error",
    "amplitude_transfers",
    "failed_transfer_gates",
    "deactivation_events",
    "secondary_vector_kicks",
    "residual_participations",
    "rotation_events",
    "rotation_events_on_residual_entry",
    "rotation_events_on_secondary_exchange",
    "angular_momentum_updates",
    "angular_momentum_biased_rotation_events",
    "angular_momentum_bias_abs_sum",
    "angular_momentum_observed_turn_abs_sum",
    "angular_momentum_nonzero_cells",
    "angular_momentum_mean_abs_active",
    "angular_momentum_mean_signed_active",
    "angular_momentum_max_abs",
    "amplitude_transfers_per_tick",
    "failed_transfer_gates_per_tick",
    "deactivation_events_per_tick",
    "secondary_vector_kicks_per_tick",
    "residual_participations_per_tick",
    "rotation_events_per_tick",
    "rotation_events_on_residual_entry_per_tick",
    "rotation_events_on_secondary_exchange_per_tick",
    "angular_momentum_updates_per_tick",
    "angular_momentum_biased_rotation_events_per_tick",
    *[
        f"{prefix}_{suffix}"
        for prefix in MASK_PREFIXES
        for suffix in MASK_DELTA_SUFFIXES
    ],
    *[
        f"{prefix}_{suffix}"
        for prefix in CONTENT_PREFIXES
        for suffix in CONTENT_DELTA_SUFFIXES
    ],
]


@dataclass
class Snapshot:
    tick: int
    active: np.ndarray
    depleted: np.ndarray
    active_interface: np.ndarray
    depleted_interface: np.ndarray
    interface_union: np.ndarray
    A: np.ndarray
    R: np.ndarray
    V: np.ndarray
    P: np.ndarray


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure active/depleted front turnover across sampled windows."
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--ticks", type=int, default=None)
    parser.add_argument("--sample-every", type=int, default=16)
    parser.add_argument("--sample-ticks", type=int, nargs="+", default=None)
    parser.add_argument("--connectivity", choices=["face6", "face18", "cube26"], default="cube26")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--amplitude-coupling", type=float, default=None)
    parser.add_argument("--vacuum-amplitude", type=int, default=None)
    parser.add_argument("--valence", type=int, default=None)
    parser.add_argument("--active-iotas", type=int, default=None)
    parser.add_argument("--bond-probability", type=float, default=None)
    parser.add_argument("--secondary-vector-kick-probability", type=float, default=None)
    parser.add_argument("--secondary-vector-kick-offset", type=int, default=None)
    parser.add_argument("--secondary-vector-kick-preserve-behavior", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--residual-participation-probability", type=float, default=None)
    parser.add_argument("--residual-participation-secondary-only", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--depleted-reactivation-probability", type=float, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--depleted-reactivation-secondary-only", action=argparse.BooleanOptionalAction, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--stop-active-iotas", type=int, default=0)
    parser.add_argument("--save-final-state", action="store_true")
    return parser.parse_args()


def apply_overrides(cfg: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    updated = copy.deepcopy(cfg)
    if args.seed is not None:
        updated.setdefault("init", {})["seed"] = int(args.seed)
    if args.active_iotas is not None:
        updated.setdefault("init", {})["active_iotas"] = int(args.active_iotas)
    constants = updated.setdefault("constants", {})
    if args.amplitude_coupling is not None:
        constants["amplitude_coupling"] = float(args.amplitude_coupling)
    if args.vacuum_amplitude is not None:
        constants["vacuum_amplitude"] = int(args.vacuum_amplitude)
    if args.valence is not None:
        constants["valence"] = int(args.valence)
    if args.bond_probability is not None:
        constants["bond_probability"] = float(args.bond_probability)
    if args.secondary_vector_kick_probability is not None:
        constants["secondary_vector_kick_probability"] = float(args.secondary_vector_kick_probability)
    if args.secondary_vector_kick_offset is not None:
        constants["secondary_vector_kick_offset"] = int(args.secondary_vector_kick_offset)
    if args.secondary_vector_kick_preserve_behavior is not None:
        constants["secondary_vector_kick_preserve_behavior"] = bool(args.secondary_vector_kick_preserve_behavior)
    residual_participation_probability = (
        args.residual_participation_probability
        if args.residual_participation_probability is not None
        else args.depleted_reactivation_probability
    )
    residual_participation_secondary_only = (
        args.residual_participation_secondary_only
        if args.residual_participation_secondary_only is not None
        else args.depleted_reactivation_secondary_only
    )
    if residual_participation_probability is not None:
        constants["residual_participation_probability"] = float(residual_participation_probability)
    if residual_participation_secondary_only is not None:
        constants["residual_participation_secondary_only"] = bool(residual_participation_secondary_only)
    return updated


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


def accumulate_counts(pending: dict[str, float], extras: dict[str, float]) -> None:
    for key, value in extras.items():
        numeric = float(value)
        if key in COUNT_KEYS:
            pending[key] = float(pending.get(key, 0.0)) + numeric
        else:
            pending[key] = numeric


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


def take_snapshot(world: World, tick: int, connectivity: str) -> Snapshot:
    active = world.active.copy()
    depleted = (~world.active) & (world.latent_A == 0)
    active_interface = active & adjacent_to_mask(depleted, connectivity, world.wrap)
    depleted_interface = depleted & adjacent_to_mask(active, connectivity, world.wrap)
    return Snapshot(
        tick=int(tick),
        active=active,
        depleted=depleted.copy(),
        active_interface=active_interface,
        depleted_interface=depleted_interface,
        interface_union=active_interface | depleted_interface,
        A=world.A.copy(),
        R=world.R.copy(),
        V=world.V.copy(),
        P=world.P.copy(),
    )


def fraction(numerator: int | float, denominator: int | float) -> float:
    return float(numerator / denominator) if float(denominator) else 0.0


def mask_delta(prefix: str, previous: np.ndarray, current: np.ndarray) -> dict[str, float]:
    previous_count = int(np.count_nonzero(previous))
    current_count = int(np.count_nonzero(current))
    retained = int(np.count_nonzero(previous & current))
    new_cells = int(np.count_nonzero(current & ~previous))
    lost_cells = int(np.count_nonzero(previous & ~current))
    union_count = previous_count + current_count - retained
    jaccard = fraction(retained, union_count) if union_count else 1.0
    return {
        f"{prefix}_previous_cells": float(previous_count),
        f"{prefix}_current_cells": float(current_count),
        f"{prefix}_retained_cells": float(retained),
        f"{prefix}_new_cells": float(new_cells),
        f"{prefix}_lost_cells": float(lost_cells),
        f"{prefix}_retention_fraction": fraction(retained, previous_count),
        f"{prefix}_current_from_previous_fraction": fraction(retained, current_count),
        f"{prefix}_birth_fraction": fraction(new_cells, current_count),
        f"{prefix}_loss_fraction": fraction(lost_cells, previous_count),
        f"{prefix}_jaccard": jaccard,
        f"{prefix}_turnover_fraction": float(1.0 - jaccard),
    }


def content_delta(
    prefix: str,
    previous: Snapshot,
    current: Snapshot,
    mask: np.ndarray,
) -> dict[str, float]:
    cells = int(np.count_nonzero(mask))
    if cells <= 0:
        return {
            f"{prefix}_cells": 0.0,
            f"{prefix}_any_changed": 0.0,
            f"{prefix}_any_changed_fraction": 0.0,
            f"{prefix}_A_changed": 0.0,
            f"{prefix}_A_changed_fraction": 0.0,
            f"{prefix}_R_changed": 0.0,
            f"{prefix}_R_changed_fraction": 0.0,
            f"{prefix}_V_changed": 0.0,
            f"{prefix}_V_changed_fraction": 0.0,
            f"{prefix}_P_changed": 0.0,
            f"{prefix}_P_changed_fraction": 0.0,
            f"{prefix}_mean_abs_A_delta": 0.0,
        }

    changed_A = previous.A[mask] != current.A[mask]
    changed_R = previous.R[mask] != current.R[mask]
    changed_V = previous.V[mask] != current.V[mask]
    changed_P = previous.P[mask] != current.P[mask]
    any_changed = changed_A | changed_R | changed_V | changed_P
    mean_abs_A_delta = float(
        np.mean(
            np.abs(
                current.A[mask].astype(np.int64)
                - previous.A[mask].astype(np.int64)
            )
        )
    )
    return {
        f"{prefix}_cells": float(cells),
        f"{prefix}_any_changed": float(np.count_nonzero(any_changed)),
        f"{prefix}_any_changed_fraction": fraction(np.count_nonzero(any_changed), cells),
        f"{prefix}_A_changed": float(np.count_nonzero(changed_A)),
        f"{prefix}_A_changed_fraction": fraction(np.count_nonzero(changed_A), cells),
        f"{prefix}_R_changed": float(np.count_nonzero(changed_R)),
        f"{prefix}_R_changed_fraction": fraction(np.count_nonzero(changed_R), cells),
        f"{prefix}_V_changed": float(np.count_nonzero(changed_V)),
        f"{prefix}_V_changed_fraction": fraction(np.count_nonzero(changed_V), cells),
        f"{prefix}_P_changed": float(np.count_nonzero(changed_P)),
        f"{prefix}_P_changed_fraction": fraction(np.count_nonzero(changed_P), cells),
        f"{prefix}_mean_abs_A_delta": mean_abs_A_delta,
    }


def turnover_row(
    previous: Snapshot | None,
    current: Snapshot,
    metric: dict[str, float],
    connectivity: str,
) -> dict[str, Any]:
    active_interface_count = int(np.count_nonzero(current.active_interface))
    depleted_interface_count = int(np.count_nonzero(current.depleted_interface))
    interface_union_count = int(np.count_nonzero(current.interface_union))
    row: dict[str, Any] = {
        "tick": current.tick,
        "previous_tick": "" if previous is None else previous.tick,
        "window_ticks": 0 if previous is None else current.tick - previous.tick,
        "connectivity": connectivity,
        "active_iotas": int(metric["active_iotas"]),
        "depleted_cells": int(float(metric.get("depleted_cells", 0.0))),
        "active_interface_cells": active_interface_count,
        "depleted_interface_cells": depleted_interface_count,
        "interface_union_cells": interface_union_count,
        "total_A": float(metric.get("total_A", 0.0)),
        "active_A": float(metric.get("active_A", 0.0)),
        "latent_A": float(metric.get("latent_A", 0.0)),
        "ledger_error": float(metric.get("ledger_error", 0.0)),
        "amplitude_transfers": float(metric.get("amplitude_transfers", 0.0)),
        "failed_transfer_gates": float(metric.get("failed_transfer_gates", 0.0)),
        "deactivation_events": float(metric.get("deactivation_events", 0.0)),
        "secondary_vector_kicks": float(metric.get("secondary_vector_kicks", 0.0)),
        "residual_participations": float(
            metric.get(
                "residual_participations",
                metric.get("depleted_reactivations", 0.0),
            )
        ),
        "rotation_events": float(metric.get("rotation_events", 0.0)),
        "rotation_events_on_residual_entry": float(
            metric.get("rotation_events_on_residual_entry", 0.0)
        ),
        "rotation_events_on_secondary_exchange": float(
            metric.get("rotation_events_on_secondary_exchange", 0.0)
        ),
        "angular_momentum_updates": float(metric.get("angular_momentum_updates", 0.0)),
        "angular_momentum_biased_rotation_events": float(
            metric.get("angular_momentum_biased_rotation_events", 0.0)
        ),
        "angular_momentum_bias_abs_sum": float(metric.get("angular_momentum_bias_abs_sum", 0.0)),
        "angular_momentum_observed_turn_abs_sum": float(
            metric.get("angular_momentum_observed_turn_abs_sum", 0.0)
        ),
        "angular_momentum_nonzero_cells": float(metric.get("angular_momentum_nonzero_cells", 0.0)),
        "angular_momentum_mean_abs_active": float(metric.get("angular_momentum_mean_abs_active", 0.0)),
        "angular_momentum_mean_signed_active": float(
            metric.get("angular_momentum_mean_signed_active", 0.0)
        ),
        "angular_momentum_max_abs": float(metric.get("angular_momentum_max_abs", 0.0)),
    }
    window = int(row["window_ticks"])
    row["amplitude_transfers_per_tick"] = fraction(row["amplitude_transfers"], window)
    row["failed_transfer_gates_per_tick"] = fraction(row["failed_transfer_gates"], window)
    row["deactivation_events_per_tick"] = fraction(row["deactivation_events"], window)
    row["secondary_vector_kicks_per_tick"] = fraction(row["secondary_vector_kicks"], window)
    row["residual_participations_per_tick"] = fraction(row["residual_participations"], window)
    row["rotation_events_per_tick"] = fraction(row["rotation_events"], window)
    row["rotation_events_on_residual_entry_per_tick"] = fraction(
        row["rotation_events_on_residual_entry"],
        window,
    )
    row["rotation_events_on_secondary_exchange_per_tick"] = fraction(
        row["rotation_events_on_secondary_exchange"],
        window,
    )
    row["angular_momentum_updates_per_tick"] = fraction(row["angular_momentum_updates"], window)
    row["angular_momentum_biased_rotation_events_per_tick"] = fraction(
        row["angular_momentum_biased_rotation_events"],
        window,
    )

    if previous is None:
        return row

    masks = {
        "active": (previous.active, current.active),
        "depleted": (previous.depleted, current.depleted),
        "active_interface": (previous.active_interface, current.active_interface),
        "depleted_interface": (previous.depleted_interface, current.depleted_interface),
        "interface_union": (previous.interface_union, current.interface_union),
    }
    for prefix, (previous_mask, current_mask) in masks.items():
        row.update(mask_delta(prefix, previous_mask, current_mask))

    persistent_active = previous.active & current.active
    persistent_active_interface = previous.active_interface & current.active_interface
    row.update(content_delta("persistent_active", previous, current, persistent_active))
    row.update(
        content_delta(
            "persistent_active_interface",
            previous,
            current,
            persistent_active_interface,
        )
    )
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})
        handle.flush()
        os.fsync(handle.fileno())


def numeric_row_value(row: dict[str, Any], key: str) -> float:
    value = row.get(key, "")
    if value == "":
        return 0.0
    return float(value)


def first_tail_tick(rows: list[dict[str, Any]], keys: tuple[str, ...], target: float = 1.0) -> int | None:
    eligible = [row for row in rows if row.get("previous_tick") != ""]
    for index, row in enumerate(eligible):
        tail = eligible[index:]
        if all(all(numeric_row_value(tail_row, key) == target for key in keys) for tail_row in tail):
            return int(row["tick"])
    return None


def mean_for(rows: list[dict[str, Any]], key: str) -> float:
    values = [numeric_row_value(row, key) for row in rows if row.get("previous_tick") != ""]
    return float(np.mean(values)) if values else 0.0


def max_for(rows: list[dict[str, Any]], key: str) -> float:
    values = [numeric_row_value(row, key) for row in rows if row.get("previous_tick") != ""]
    return float(np.max(values)) if values else 0.0


def sum_for(rows: list[dict[str, Any]], key: str) -> float:
    return float(sum(numeric_row_value(row, key) for row in rows if row.get("previous_tick") != ""))


def tail_rows_from(rows: list[dict[str, Any]], tick: int | None) -> list[dict[str, Any]]:
    if tick is None:
        return []
    return [row for row in rows if row.get("previous_tick") != "" and int(row["tick"]) >= tick]


def aggregate_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    active_freeze_tick = first_tail_tick(rows, ("active_jaccard",))
    depleted_freeze_tick = first_tail_tick(rows, ("depleted_jaccard",))
    active_interface_freeze_tick = first_tail_tick(rows, ("active_interface_jaccard",))
    interface_union_freeze_tick = first_tail_tick(rows, ("interface_union_jaccard",))
    full_front_freeze_tick = first_tail_tick(
        rows,
        ("active_jaccard", "depleted_jaccard", "active_interface_jaccard", "interface_union_jaccard"),
    )
    tail_rows = tail_rows_from(rows, full_front_freeze_tick)
    final_row = rows[-1] if rows else {}
    return {
        "sample_count": len(rows),
        "active_mask_freeze_tick": active_freeze_tick,
        "depleted_mask_freeze_tick": depleted_freeze_tick,
        "active_interface_freeze_tick": active_interface_freeze_tick,
        "interface_union_freeze_tick": interface_union_freeze_tick,
        "full_front_freeze_tick": full_front_freeze_tick,
        "cumulative_new_active_cells": sum_for(rows, "active_new_cells"),
        "cumulative_lost_active_cells": sum_for(rows, "active_lost_cells"),
        "cumulative_new_active_interface_cells": sum_for(rows, "active_interface_new_cells"),
        "cumulative_lost_active_interface_cells": sum_for(rows, "active_interface_lost_cells"),
        "max_active_turnover_fraction": max_for(rows, "active_turnover_fraction"),
        "max_active_interface_turnover_fraction": max_for(rows, "active_interface_turnover_fraction"),
        "mean_active_turnover_fraction": mean_for(rows, "active_turnover_fraction"),
        "mean_active_interface_turnover_fraction": mean_for(rows, "active_interface_turnover_fraction"),
        "tail_mean_amplitude_transfers_per_tick_after_full_freeze": mean_for(
            tail_rows,
            "amplitude_transfers_per_tick",
        ),
        "tail_mean_failed_transfer_gates_per_tick_after_full_freeze": mean_for(
            tail_rows,
            "failed_transfer_gates_per_tick",
        ),
        "tail_mean_secondary_vector_kicks_per_tick_after_full_freeze": mean_for(
            tail_rows,
            "secondary_vector_kicks_per_tick",
        ),
        "tail_mean_residual_participations_per_tick_after_full_freeze": mean_for(
            tail_rows,
            "residual_participations_per_tick",
        ),
        "tail_mean_rotation_events_per_tick_after_full_freeze": mean_for(
            tail_rows,
            "rotation_events_per_tick",
        ),
        "tail_mean_rotation_events_on_residual_entry_per_tick_after_full_freeze": mean_for(
            tail_rows,
            "rotation_events_on_residual_entry_per_tick",
        ),
        "tail_mean_rotation_events_on_secondary_exchange_per_tick_after_full_freeze": mean_for(
            tail_rows,
            "rotation_events_on_secondary_exchange_per_tick",
        ),
        "tail_mean_persistent_active_changed_fraction_after_full_freeze": mean_for(
            tail_rows,
            "persistent_active_any_changed_fraction",
        ),
        "tail_mean_persistent_interface_changed_fraction_after_full_freeze": mean_for(
            tail_rows,
            "persistent_active_interface_any_changed_fraction",
        ),
        "final_active_iotas": final_row.get("active_iotas", 0),
        "final_depleted_cells": final_row.get("depleted_cells", 0),
        "final_active_interface_cells": final_row.get("active_interface_cells", 0),
        "final_depleted_interface_cells": final_row.get("depleted_interface_cells", 0),
        "final_ledger_error": final_row.get("ledger_error", 0.0),
    }


def main() -> None:
    args = parse_args()
    cfg = apply_overrides(load_config(args.config), args)
    ticks = int(args.ticks if args.ticks is not None else cfg.get("run", {}).get("ticks", 2048))
    sample_ticks = sample_schedule(args, ticks)
    sample_tick_set = set(sample_ticks)
    output_prefix = Path(args.output_prefix)
    turnover_path = output_prefix.with_name(output_prefix.name + "_turnover.csv")
    summary_path = output_prefix.with_name(output_prefix.name + "_turnover_summary.json")
    final_state_path = output_prefix.with_suffix(".npz")

    world = init_world(cfg)
    previous_snapshot: Snapshot | None = None
    rows: list[dict[str, Any]] = []
    pending_extras: dict[str, float] = {}
    final_tick = ticks
    early_stop_reason = ""

    def add_sample(tick: int) -> None:
        nonlocal previous_snapshot, pending_extras
        metric = collect_metrics(world, tick, pending_extras)
        current_snapshot = take_snapshot(world, tick, args.connectivity)
        rows.append(turnover_row(previous_snapshot, current_snapshot, metric, args.connectivity))
        previous_snapshot = current_snapshot
        pending_extras = {}

    sampled_ticks: set[int] = set()
    for tick in range(0, ticks + 1):
        if tick in sample_tick_set and tick not in sampled_ticks:
            add_sample(tick)
            sampled_ticks.add(tick)
        if tick == ticks:
            break
        extras = step(world, cfg)
        accumulate_counts(pending_extras, extras)
        active_count = int(world.active.sum())
        if int(args.stop_active_iotas) > 0 and active_count >= int(args.stop_active_iotas):
            final_tick = tick + 1
            early_stop_reason = f"active_iotas >= {args.stop_active_iotas}"
            if final_tick not in sampled_ticks:
                add_sample(final_tick)
                sampled_ticks.add(final_tick)
            break

    if args.save_final_state:
        save_world_state(
            world,
            final_state_path,
            {
                "final_tick": final_tick,
                "early_stop_reason": early_stop_reason,
                "config": args.config,
                "connectivity": args.connectivity,
            },
        )

    write_csv(turnover_path, rows)
    summary = {
        "config": {
            "config_path": args.config,
            "seed": cfg.get("init", {}).get("seed"),
            "active_iotas": cfg.get("init", {}).get("active_iotas"),
            "amplitude_coupling": cfg.get("constants", {}).get("amplitude_coupling"),
            "vacuum_amplitude": cfg.get("constants", {}).get("vacuum_amplitude"),
            "valence": cfg.get("constants", {}).get("valence"),
            "bond_probability": cfg.get("constants", {}).get("bond_probability"),
            "secondary_vector_kick_probability": cfg.get("constants", {}).get(
                "secondary_vector_kick_probability",
                0.0,
            ),
            "secondary_vector_kick_offset": cfg.get("constants", {}).get(
                "secondary_vector_kick_offset",
                1,
            ),
            "secondary_vector_kick_preserve_behavior": cfg.get("constants", {}).get(
                "secondary_vector_kick_preserve_behavior",
                True,
            ),
            "residual_participation_probability": cfg.get("constants", {}).get(
                "residual_participation_probability",
                cfg.get("constants", {}).get("depleted_reactivation_probability", 0.0),
            ),
            "residual_participation_secondary_only": cfg.get("constants", {}).get(
                "residual_participation_secondary_only",
                cfg.get("constants", {}).get("depleted_reactivation_secondary_only", True),
            ),
            "received_rotation_probability": cfg.get("constants", {}).get(
                "received_rotation_probability",
                cfg.get("constants", {}).get("history_coupled_rotation_probability", 0.0),
            ),
            "received_rotation_max_offset": cfg.get("constants", {}).get(
                "received_rotation_max_offset",
                cfg.get("constants", {}).get("history_coupled_rotation_max_offset", 3),
            ),
            "received_rotation_preserve_behavior": cfg.get("constants", {}).get(
                "received_rotation_preserve_behavior",
                cfg.get("constants", {}).get("history_coupled_rotation_preserve_behavior", True),
            ),
            "ticks": ticks,
            "connectivity": args.connectivity,
            "sample_ticks": sample_ticks,
            "stop_active_iotas": args.stop_active_iotas,
        },
        "final_tick": final_tick,
        "early_stop_reason": early_stop_reason,
        "turnover_path": turnover_path.as_posix(),
        "summary_path": summary_path.as_posix(),
        "final_state_path": final_state_path.as_posix() if args.save_final_state else "",
        "aggregate": aggregate_summary(rows),
        "final_row": rows[-1] if rows else {},
    }
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
