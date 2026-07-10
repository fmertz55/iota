from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import component_labels, csv_bool, write_csv
from continuation import clone_world, deterministic_continuation_seed
from iota_rig import World, load_config


BASE_VECTOR_STEP = iota_rig.vector_step
PIVOTAL_OFFSET = 499
SPLIT_OFFSET = 512
REBRIDGE_OFFSET = 515
PIVOTAL_TARGET = (13, 3, 38)
SPLIT_TARGET = (12, 2, 38)
REBRIDGE_TARGET = (13, 2, 38)
CAUSAL_CELLS = (PIVOTAL_TARGET, SPLIT_TARGET, REBRIDGE_TARGET)

VARIANTS = (
    "natural",
    "no_payload_vector_step",
    "no_payload_rotation_offset",
    "no_payload_rotate_takeover",
    "no_payload_all_action_paths",
    "clamp_payload_each_tick",
)

SUMMARY_FIELDNAMES = [
    "variant",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "component_signal_offsets",
    "first_component_change_offset",
    "component_signal_vanish_offset",
    "split_at_512",
    "rebridge_at_515",
    "pivotal_target_active_499",
    "pivotal_target_active_511",
    "pivotal_target_active_512",
    "split_target_active_512",
    "split_target_active_515",
    "rebridge_target_active_515",
    "checkpoint_active_iotas",
    "checkpoint_component_count",
    "checkpoint_largest_component",
    "checkpoint_nonzero_payload_iotas",
    "checkpoint_payload_unique",
    "checkpoint_payload_entropy",
    "checkpoint_p_sensitive_primary_count",
    "checkpoint_p_sensitive_primary_fraction",
    "final_active_iotas",
    "final_component_count",
    "final_largest_component",
    "final_nonzero_payload_iotas",
    "final_payload_unique",
    "final_payload_entropy",
    "ledger_exact",
    "max_abs_ledger_error",
    "state_hash_without_payload",
]

PAIR_FIELDNAMES = [
    "variant",
    "reference_variant",
    "same_component_signal",
    "same_first_component_change_offset",
    "same_split_at_512",
    "same_rebridge_at_515",
    "same_checkpoint_active_iotas",
    "same_checkpoint_component_count",
    "same_checkpoint_largest_component",
    "same_final_active_iotas",
    "same_final_component_count",
    "same_final_largest_component",
    "same_final_state_without_payload",
    "first_nonpayload_divergence_tick",
    "first_nonpayload_divergence_stage",
    "first_nonpayload_divergence_offset",
    "natural_nonzero_payload_iotas_at_divergence",
    "natural_p_sensitive_primary_count_at_divergence",
    "natural_component_count_at_divergence",
    "variant_component_count_at_divergence",
    "natural_largest_component_at_divergence",
    "variant_largest_component_at_divergence",
    "component_signal_offsets",
    "reference_component_signal_offsets",
]

TIMELINE_FIELDNAMES = [
    "variant",
    "tick",
    "stage",
    "offset",
    "active_iotas",
    "component_count_cube26",
    "component_delta_from_checkpoint",
    "component_delta_from_previous",
    "largest_component_cube26",
    "largest_delta_from_checkpoint",
    "largest_delta_from_previous",
    "ledger_error",
    "nonzero_payload_iotas",
    "payload_unique",
    "payload_entropy",
    "p_sensitive_primary_count",
    "p_sensitive_primary_fraction",
    "pivotal_target_active",
    "split_target_active",
    "rebridge_target_active",
    "state_hash_without_payload",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit early payload as an action-phase selector in v0.3.6 seed46."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--sample-index", type=int, default=6)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--horizon", type=int, default=1024)
    parser.add_argument("--variants", nargs="+", choices=VARIANTS, default=list(VARIANTS))
    return parser.parse_args()


def state_hash_without_payload(world: World) -> str:
    digest = hashlib.sha256()
    for array in (world.active, world.A, world.R, world.V, world.latent_A, world.angular_L):
        digest.update(np.ascontiguousarray(array).view(np.uint8))
    return digest.hexdigest()


def payload_entropy(world: World) -> float:
    active_count = int(np.count_nonzero(world.active))
    if active_count == 0:
        return 0.0
    hist = np.bincount(world.P[world.active], minlength=8).astype(np.float64)
    probabilities = hist[hist > 0] / active_count
    return float(-np.sum(probabilities * np.log2(probabilities)))


def payload_unique(world: World) -> int:
    if not np.any(world.active):
        return 0
    return int(len(np.unique(world.P[world.active])))


def nonzero_payload_iotas(world: World) -> int:
    return int(np.count_nonzero(world.active & (world.P != 0)))


def ledger_error(world: World) -> float:
    active_total = int(np.sum(world.A[world.active], dtype=np.int64))
    latent_total = int(np.sum(world.latent_A[~world.active], dtype=np.int64))
    return float(active_total + latent_total - int(world.initial_total_A))


def component_snapshot(world: World) -> tuple[int, int]:
    _, _, count, largest = component_labels(world.active, bool(world.wrap), "cube26")
    return int(count), int(largest)


def p_sensitive_primary_count(world: World) -> tuple[int, float]:
    active_coords = np.argwhere(world.active)
    if len(active_coords) == 0:
        return 0, 0.0
    count = 0
    for x, y, z in active_coords:
        a = int(world.A[x, y, z])
        r = int(world.R[x, y, z])
        if a == 0 or r == 0:
            continue
        v_idx = int(world.V[x, y, z]) % len(world.vectors)
        p = int(world.P[x, y, z])
        if p == 0:
            continue
        with_p = BASE_VECTOR_STEP(world, v_idx, a, r, p)[:3]
        without_p = BASE_VECTOR_STEP(world, v_idx, a, r, 0)[:3]
        if with_p != without_p:
            count += 1
    active_count = int(len(active_coords))
    return count, float(count / active_count) if active_count else 0.0


@contextmanager
def payload_action_patch(variant: str) -> Iterator[None]:
    original_vector_step = iota_rig.vector_step
    original_rotate_vector_state = iota_rig.rotate_vector_state
    original_rotation_offset = iota_rig.history_coupled_rotation_offset
    original_signed_rotation_offset = iota_rig.history_coupled_signed_rotation_offset

    def vector_step_no_payload(world: World, v_idx: int, a: int, r: int, p: int) -> tuple[int, int, int, str]:
        return original_vector_step(world, v_idx, a, r, 0)

    def rotate_vector_state_no_payload(world: World, v_idx: int, payload: int) -> int:
        return original_rotate_vector_state(world, v_idx, 0)

    def rotation_offset_no_payload(
        source_v: int,
        source_p: int,
        target_v: int,
        target_a: int,
        target_r: int,
        target_p: int,
        candidate_order: int,
        target_depleted: bool,
        influence: float,
        max_offset: int,
    ) -> int:
        return original_rotation_offset(
            source_v=source_v,
            source_p=0,
            target_v=target_v,
            target_a=target_a,
            target_r=target_r,
            target_p=0,
            candidate_order=candidate_order,
            target_depleted=target_depleted,
            influence=influence,
            max_offset=max_offset,
        )

    def signed_rotation_offset_no_payload(
        source_v: int,
        source_p: int,
        target_v: int,
        target_a: int,
        target_r: int,
        target_p: int,
        candidate_order: int,
        target_depleted: bool,
        influence: float,
        max_offset: int,
    ) -> int:
        return original_signed_rotation_offset(
            source_v=source_v,
            source_p=0,
            target_v=target_v,
            target_a=target_a,
            target_r=target_r,
            target_p=0,
            candidate_order=candidate_order,
            target_depleted=target_depleted,
            influence=influence,
            max_offset=max_offset,
        )

    try:
        if variant in {"no_payload_vector_step", "no_payload_all_action_paths"}:
            iota_rig.vector_step = vector_step_no_payload
        if variant in {"no_payload_rotate_takeover", "no_payload_all_action_paths"}:
            iota_rig.rotate_vector_state = rotate_vector_state_no_payload
        if variant in {"no_payload_rotation_offset", "no_payload_all_action_paths"}:
            iota_rig.history_coupled_rotation_offset = rotation_offset_no_payload
            iota_rig.history_coupled_signed_rotation_offset = signed_rotation_offset_no_payload
        yield
    finally:
        iota_rig.vector_step = original_vector_step
        iota_rig.rotate_vector_state = original_rotate_vector_state
        iota_rig.history_coupled_rotation_offset = original_rotation_offset
        iota_rig.history_coupled_signed_rotation_offset = original_signed_rotation_offset


def apply_payload_clamp(world: World, variant: str) -> None:
    if variant == "clamp_payload_each_tick":
        world.P.fill(0)


def make_timeline_row(
    variant: str,
    world: World,
    tick: int,
    checkpoint_tick: int,
    checkpoint_count: int | None,
    checkpoint_largest: int | None,
    previous_count: int | None,
    previous_largest: int | None,
) -> dict[str, Any]:
    count, largest = component_snapshot(world)
    sensitive_count, sensitive_fraction = p_sensitive_primary_count(world)
    offset = int(tick - checkpoint_tick)
    stage = "precheckpoint" if tick < checkpoint_tick else ("checkpoint" if tick == checkpoint_tick else "continuation")
    return {
        "variant": variant,
        "tick": int(tick),
        "stage": stage,
        "offset": offset,
        "active_iotas": int(np.count_nonzero(world.active)),
        "component_count_cube26": count,
        "component_delta_from_checkpoint": (
            0 if checkpoint_count is None else int(count - checkpoint_count)
        ),
        "component_delta_from_previous": (
            0 if previous_count is None else int(count - previous_count)
        ),
        "largest_component_cube26": largest,
        "largest_delta_from_checkpoint": (
            0 if checkpoint_largest is None else int(largest - checkpoint_largest)
        ),
        "largest_delta_from_previous": (
            0 if previous_largest is None else int(largest - previous_largest)
        ),
        "ledger_error": ledger_error(world),
        "nonzero_payload_iotas": nonzero_payload_iotas(world),
        "payload_unique": payload_unique(world),
        "payload_entropy": payload_entropy(world),
        "p_sensitive_primary_count": sensitive_count,
        "p_sensitive_primary_fraction": sensitive_fraction,
        "pivotal_target_active": csv_bool(bool(world.active[PIVOTAL_TARGET])),
        "split_target_active": csv_bool(bool(world.active[SPLIT_TARGET])),
        "rebridge_target_active": csv_bool(bool(world.active[REBRIDGE_TARGET])),
        "state_hash_without_payload": state_hash_without_payload(world),
    }


def build_summary(variant: str, args: argparse.Namespace, rows: list[dict[str, Any]]) -> dict[str, Any]:
    checkpoint_row = next(row for row in rows if int(row["tick"]) == int(args.checkpoint_tick))
    final_row = rows[-1]
    continuation_rows = [row for row in rows if str(row["stage"]) == "continuation"]
    signal_rows = [row for row in continuation_rows if int(row["component_delta_from_checkpoint"]) != 0]
    first_signal = signal_rows[0] if signal_rows else None
    vanish_row = None
    if first_signal is not None:
        first_index = rows.index(first_signal)
        for row in rows[first_index + 1 :]:
            if int(row["tick"]) > int(args.checkpoint_tick) and int(row["component_delta_from_checkpoint"]) == 0:
                vanish_row = row
                break
    return {
        "variant": variant,
        "init_seed": "",
        "checkpoint_tick": int(args.checkpoint_tick),
        "sample_index": int(args.sample_index),
        "continuation_seed": deterministic_continuation_seed(
            int(args.rng_seed_base),
            int(args.checkpoint_tick),
            int(args.sample_index),
        ),
        "component_signal_offsets": ";".join(str(int(row["offset"])) for row in signal_rows),
        "first_component_change_offset": "" if first_signal is None else int(first_signal["offset"]),
        "component_signal_vanish_offset": "" if vanish_row is None else int(vanish_row["offset"]),
        "split_at_512": csv_bool(
            any(
                int(row["offset"]) == SPLIT_OFFSET and int(row["component_delta_from_previous"]) > 0
                for row in continuation_rows
            )
        ),
        "rebridge_at_515": csv_bool(
            any(
                int(row["offset"]) == REBRIDGE_OFFSET and int(row["component_delta_from_previous"]) < 0
                for row in continuation_rows
            )
        ),
        "pivotal_target_active_499": row_value_at_offset(rows, "pivotal_target_active", PIVOTAL_OFFSET),
        "pivotal_target_active_511": row_value_at_offset(rows, "pivotal_target_active", SPLIT_OFFSET - 1),
        "pivotal_target_active_512": row_value_at_offset(rows, "pivotal_target_active", SPLIT_OFFSET),
        "split_target_active_512": row_value_at_offset(rows, "split_target_active", SPLIT_OFFSET),
        "split_target_active_515": row_value_at_offset(rows, "split_target_active", REBRIDGE_OFFSET),
        "rebridge_target_active_515": row_value_at_offset(rows, "rebridge_target_active", REBRIDGE_OFFSET),
        "checkpoint_active_iotas": int(checkpoint_row["active_iotas"]),
        "checkpoint_component_count": int(checkpoint_row["component_count_cube26"]),
        "checkpoint_largest_component": int(checkpoint_row["largest_component_cube26"]),
        "checkpoint_nonzero_payload_iotas": int(checkpoint_row["nonzero_payload_iotas"]),
        "checkpoint_payload_unique": int(checkpoint_row["payload_unique"]),
        "checkpoint_payload_entropy": float(checkpoint_row["payload_entropy"]),
        "checkpoint_p_sensitive_primary_count": int(checkpoint_row["p_sensitive_primary_count"]),
        "checkpoint_p_sensitive_primary_fraction": float(checkpoint_row["p_sensitive_primary_fraction"]),
        "final_active_iotas": int(final_row["active_iotas"]),
        "final_component_count": int(final_row["component_count_cube26"]),
        "final_largest_component": int(final_row["largest_component_cube26"]),
        "final_nonzero_payload_iotas": int(final_row["nonzero_payload_iotas"]),
        "final_payload_unique": int(final_row["payload_unique"]),
        "final_payload_entropy": float(final_row["payload_entropy"]),
        "ledger_exact": csv_bool(all(abs(float(row["ledger_error"])) == 0.0 for row in rows)),
        "max_abs_ledger_error": max(abs(float(row["ledger_error"])) for row in rows),
        "state_hash_without_payload": str(final_row["state_hash_without_payload"]),
    }


def row_value_at_offset(rows: list[dict[str, Any]], key: str, offset: int) -> str:
    for row in rows:
        if int(row["offset"]) == int(offset):
            return str(row[key])
    return ""


def run_variant(args: argparse.Namespace, cfg: dict[str, Any], variant: str) -> list[dict[str, Any]]:
    continuation_seed = deterministic_continuation_seed(
        int(args.rng_seed_base),
        int(args.checkpoint_tick),
        int(args.sample_index),
    )
    rows: list[dict[str, Any]] = []
    with payload_action_patch(variant):
        world = iota_rig.init_world(cfg)
        apply_payload_clamp(world, variant)
        previous_count: int | None = None
        previous_largest: int | None = None
        checkpoint_count: int | None = None
        checkpoint_largest: int | None = None
        for tick in range(0, int(args.checkpoint_tick) + int(args.horizon) + 1):
            if tick == int(args.checkpoint_tick):
                checkpoint_count, checkpoint_largest = component_snapshot(world)
                world = clone_world(world, continuation_seed)
                apply_payload_clamp(world, variant)
                previous_count = checkpoint_count
                previous_largest = checkpoint_largest
            row = make_timeline_row(
                variant,
                world,
                tick,
                int(args.checkpoint_tick),
                checkpoint_count,
                checkpoint_largest,
                previous_count,
                previous_largest,
            )
            rows.append(row)
            previous_count = int(row["component_count_cube26"])
            previous_largest = int(row["largest_component_cube26"])
            if tick >= int(args.checkpoint_tick) + int(args.horizon):
                break
            apply_payload_clamp(world, variant)
            iota_rig.step(world, cfg)
            apply_payload_clamp(world, variant)
    return rows


def divergence_pair(row: dict[str, Any], reference: dict[str, Any], rows: list[dict[str, Any]], reference_rows: list[dict[str, Any]]) -> dict[str, Any]:
    first_divergence: tuple[dict[str, Any], dict[str, Any]] | None = None
    for variant_row, natural_row in zip(rows, reference_rows, strict=True):
        if str(variant_row["state_hash_without_payload"]) != str(natural_row["state_hash_without_payload"]):
            first_divergence = (variant_row, natural_row)
            break
    if first_divergence is None:
        divergence_tick: Any = ""
        divergence_stage: Any = ""
        divergence_offset: Any = ""
        natural_nonzero_payload: Any = ""
        natural_sensitive_count: Any = ""
        natural_component_count: Any = ""
        variant_component_count: Any = ""
        natural_largest: Any = ""
        variant_largest: Any = ""
    else:
        variant_row, natural_row = first_divergence
        divergence_tick = int(variant_row["tick"])
        divergence_stage = str(variant_row["stage"])
        divergence_offset = int(variant_row["offset"])
        natural_nonzero_payload = int(natural_row["nonzero_payload_iotas"])
        natural_sensitive_count = int(natural_row["p_sensitive_primary_count"])
        natural_component_count = int(natural_row["component_count_cube26"])
        variant_component_count = int(variant_row["component_count_cube26"])
        natural_largest = int(natural_row["largest_component_cube26"])
        variant_largest = int(variant_row["largest_component_cube26"])

    return {
        "variant": row["variant"],
        "reference_variant": reference["variant"],
        "same_component_signal": csv_bool(
            str(row["component_signal_offsets"]) == str(reference["component_signal_offsets"])
        ),
        "same_first_component_change_offset": csv_bool(
            str(row["first_component_change_offset"]) == str(reference["first_component_change_offset"])
        ),
        "same_split_at_512": csv_bool(int(row["split_at_512"]) == int(reference["split_at_512"])),
        "same_rebridge_at_515": csv_bool(int(row["rebridge_at_515"]) == int(reference["rebridge_at_515"])),
        "same_checkpoint_active_iotas": csv_bool(
            int(row["checkpoint_active_iotas"]) == int(reference["checkpoint_active_iotas"])
        ),
        "same_checkpoint_component_count": csv_bool(
            int(row["checkpoint_component_count"]) == int(reference["checkpoint_component_count"])
        ),
        "same_checkpoint_largest_component": csv_bool(
            int(row["checkpoint_largest_component"]) == int(reference["checkpoint_largest_component"])
        ),
        "same_final_active_iotas": csv_bool(int(row["final_active_iotas"]) == int(reference["final_active_iotas"])),
        "same_final_component_count": csv_bool(
            int(row["final_component_count"]) == int(reference["final_component_count"])
        ),
        "same_final_largest_component": csv_bool(
            int(row["final_largest_component"]) == int(reference["final_largest_component"])
        ),
        "same_final_state_without_payload": csv_bool(
            str(row["state_hash_without_payload"]) == str(reference["state_hash_without_payload"])
        ),
        "first_nonpayload_divergence_tick": divergence_tick,
        "first_nonpayload_divergence_stage": divergence_stage,
        "first_nonpayload_divergence_offset": divergence_offset,
        "natural_nonzero_payload_iotas_at_divergence": natural_nonzero_payload,
        "natural_p_sensitive_primary_count_at_divergence": natural_sensitive_count,
        "natural_component_count_at_divergence": natural_component_count,
        "variant_component_count_at_divergence": variant_component_count,
        "natural_largest_component_at_divergence": natural_largest,
        "variant_largest_component_at_divergence": variant_largest,
        "component_signal_offsets": row["component_signal_offsets"],
        "reference_component_signal_offsets": reference["component_signal_offsets"],
    }


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    summaries: list[dict[str, Any]] = []
    timeline_by_variant: dict[str, list[dict[str, Any]]] = {}
    for variant in args.variants:
        rows = run_variant(args, cfg, variant)
        timeline_by_variant[variant] = rows
        summary = build_summary(variant, args, rows)
        summary["init_seed"] = int(cfg.get("init", {}).get("seed", -1))
        summaries.append(summary)
        print(
            f"{variant}: signal={summary['component_signal_offsets'] or 'none'} "
            f"checkpoint_active={summary['checkpoint_active_iotas']} "
            f"checkpoint_largest={summary['checkpoint_largest_component']} "
            f"divergence_baseline=pending"
        )

    natural_summary = next(row for row in summaries if row["variant"] == "natural")
    natural_rows = timeline_by_variant["natural"]
    pairs = [
        divergence_pair(summary, natural_summary, timeline_by_variant[str(summary["variant"])], natural_rows)
        for summary in summaries
        if summary["variant"] != "natural"
    ]

    all_timeline = [row for variant in args.variants for row in timeline_by_variant[variant]]
    output_prefix = Path(args.output_prefix)
    write_csv(output_prefix.with_name(output_prefix.name + "_summary.csv"), SUMMARY_FIELDNAMES, summaries)
    write_csv(output_prefix.with_name(output_prefix.name + "_pairs.csv"), PAIR_FIELDNAMES, pairs)
    write_csv(output_prefix.with_name(output_prefix.name + "_timeline.csv"), TIMELINE_FIELDNAMES, all_timeline)
    payload = {
        "summary_csv": str(output_prefix.with_name(output_prefix.name + "_summary.csv")),
        "pairs_csv": str(output_prefix.with_name(output_prefix.name + "_pairs.csv")),
        "timeline_csv": str(output_prefix.with_name(output_prefix.name + "_timeline.csv")),
        "summary_by_variant": {str(row["variant"]): row for row in summaries},
        "pairs_by_variant": {str(row["variant"]): row for row in pairs},
    }
    json_path = output_prefix.with_name(output_prefix.name + "_summary.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


if __name__ == "__main__":
    main()
