from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import component_labels, csv_bool, write_csv
from continuation import clone_world, deterministic_continuation_seed
from iota_rig import World, load_config


PIVOTAL_OFFSET = 499
SPLIT_OFFSET = 512
REBRIDGE_OFFSET = 515
PIVOTAL_TARGET = (13, 3, 38)
SPLIT_TARGET = (12, 2, 38)
REBRIDGE_TARGET = (13, 2, 38)

SUMMARY_FIELDNAMES = [
    "case_label",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "ticks_compared",
    "nonpayload_equal_ticks",
    "phase_equal_ticks",
    "replacement_payload_zero_ticks",
    "rng_equal_ticks",
    "first_nonpayload_divergence_tick",
    "first_phase_divergence_tick",
    "first_replacement_payload_nonzero_tick",
    "first_rng_divergence_tick",
    "phase_collapse_tick",
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
    "checkpoint_phase_nonzero_iotas",
    "checkpoint_phase_unique",
    "checkpoint_p_sensitive_primary_count",
    "final_active_iotas",
    "final_component_count",
    "final_largest_component",
    "final_phase_nonzero_iotas",
    "final_phase_unique",
    "ledger_exact",
    "max_abs_ledger_error",
    "final_nonpayload_hash",
    "final_phase_hash",
]

TIMELINE_FIELDNAMES = [
    "case_label",
    "tick",
    "stage",
    "offset",
    "nonpayload_equal",
    "phase_equal",
    "replacement_payload_zero",
    "rng_equal",
    "active_iotas",
    "component_count_cube26",
    "component_delta_from_checkpoint",
    "component_delta_from_previous",
    "largest_component_cube26",
    "largest_delta_from_checkpoint",
    "largest_delta_from_previous",
    "phase_nonzero_iotas",
    "phase_unique",
    "p_sensitive_primary_count",
    "legacy_payload_nonzero_iotas",
    "replacement_payload_nonzero_iotas",
    "legacy_ledger_error",
    "replacement_ledger_error",
    "pivotal_target_active",
    "split_target_active",
    "rebridge_target_active",
    "nonpayload_hash_legacy",
    "nonpayload_hash_replacement",
    "phase_hash_legacy",
    "phase_hash_replacement",
    "rng_hash_legacy",
    "rng_hash_replacement",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test exact equivalence between legacy payload and transient action-phase side state."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[46])
    parser.add_argument("--sample-indices", nargs="+", type=int, default=[6])
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--horizon", type=int, default=1024)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--timeline-seed", type=int, default=46)
    parser.add_argument("--timeline-sample-index", type=int, default=6)
    return parser.parse_args()


def discover_config(config_dir: str, seed: int) -> Path:
    matches = sorted(Path(config_dir).glob(f"v036_component_bridge_seed{int(seed)}_*.yaml"))
    if len(matches) != 1:
        raise SystemExit(f"expected one v0.3.6 config for seed {seed}, found {len(matches)}")
    return matches[0]


def array_hash(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).view(np.uint8)).hexdigest()


def nonpayload_hash(world: World) -> str:
    digest = hashlib.sha256()
    for array in (
        world.active,
        world.A,
        world.R,
        world.V,
        world.latent_A,
        world.angular_L,
        world.previous_active,
        world.previous_V,
    ):
        digest.update(np.ascontiguousarray(array).view(np.uint8))
    return digest.hexdigest()


def rng_hash(world: World) -> str:
    payload = json.dumps(world.rng.bit_generator.state, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ledger_error(world: World) -> float:
    active_total = int(np.sum(world.A[world.active], dtype=np.int64))
    latent_total = int(np.sum(world.latent_A[~world.active], dtype=np.int64))
    return float(active_total + latent_total - int(world.initial_total_A))


def component_snapshot(world: World) -> tuple[int, int]:
    _, _, count, largest = component_labels(world.active, bool(world.wrap), "cube26")
    return int(count), int(largest)


def p_sensitive_primary_count(world: World, phase: np.ndarray) -> int:
    active_coords = np.argwhere(world.active)
    count = 0
    for x, y, z in active_coords:
        a = int(world.A[x, y, z])
        r = int(world.R[x, y, z])
        if a == 0 or r == 0:
            continue
        p = int(phase[x, y, z])
        if p == 0:
            continue
        v_idx = int(world.V[x, y, z]) % len(world.vectors)
        with_phase = iota_rig.vector_step(world, v_idx, a, r, p)[:3]
        without_phase = iota_rig.vector_step(world, v_idx, a, r, 0)[:3]
        if with_phase != without_phase:
            count += 1
    return count


def phase_unique(world: World, phase: np.ndarray) -> int:
    if not np.any(world.active):
        return 0
    return int(len(np.unique(phase[world.active])))


def stage_for_tick(tick: int, checkpoint_tick: int) -> str:
    if tick < checkpoint_tick:
        return "precheckpoint"
    if tick == checkpoint_tick:
        return "checkpoint"
    return "continuation"


def offset_for_tick(tick: int, checkpoint_tick: int) -> int:
    return int(tick - checkpoint_tick)


def make_timeline_row(
    case_label: str,
    legacy: World,
    replacement: World,
    action_phase: np.ndarray,
    tick: int,
    checkpoint_tick: int,
    checkpoint_count: int | None,
    checkpoint_largest: int | None,
    previous_count: int | None,
    previous_largest: int | None,
) -> dict[str, Any]:
    count, largest = component_snapshot(legacy)
    offset = offset_for_tick(tick, checkpoint_tick)
    nonpayload_hash_legacy = nonpayload_hash(legacy)
    nonpayload_hash_replacement = nonpayload_hash(replacement)
    phase_hash_legacy = array_hash(legacy.P)
    phase_hash_replacement = array_hash(action_phase)
    rng_hash_legacy = rng_hash(legacy)
    rng_hash_replacement = rng_hash(replacement)
    return {
        "case_label": case_label,
        "tick": int(tick),
        "stage": stage_for_tick(tick, checkpoint_tick),
        "offset": offset,
        "nonpayload_equal": csv_bool(nonpayload_hash_legacy == nonpayload_hash_replacement),
        "phase_equal": csv_bool(phase_hash_legacy == phase_hash_replacement),
        "replacement_payload_zero": csv_bool(not np.any(replacement.P != 0)),
        "rng_equal": csv_bool(rng_hash_legacy == rng_hash_replacement),
        "active_iotas": int(np.count_nonzero(legacy.active)),
        "component_count_cube26": count,
        "component_delta_from_checkpoint": (
            0 if checkpoint_count is None else int(count - checkpoint_count)
        ),
        "component_delta_from_previous": 0 if previous_count is None else int(count - previous_count),
        "largest_component_cube26": largest,
        "largest_delta_from_checkpoint": (
            0 if checkpoint_largest is None else int(largest - checkpoint_largest)
        ),
        "largest_delta_from_previous": 0 if previous_largest is None else int(largest - previous_largest),
        "phase_nonzero_iotas": int(np.count_nonzero(legacy.active & (action_phase != 0))),
        "phase_unique": phase_unique(legacy, action_phase),
        "p_sensitive_primary_count": p_sensitive_primary_count(legacy, action_phase),
        "legacy_payload_nonzero_iotas": int(np.count_nonzero(legacy.active & (legacy.P != 0))),
        "replacement_payload_nonzero_iotas": int(np.count_nonzero(replacement.active & (replacement.P != 0))),
        "legacy_ledger_error": ledger_error(legacy),
        "replacement_ledger_error": ledger_error(replacement),
        "pivotal_target_active": csv_bool(bool(legacy.active[PIVOTAL_TARGET])),
        "split_target_active": csv_bool(bool(legacy.active[SPLIT_TARGET])),
        "rebridge_target_active": csv_bool(bool(legacy.active[REBRIDGE_TARGET])),
        "nonpayload_hash_legacy": nonpayload_hash_legacy,
        "nonpayload_hash_replacement": nonpayload_hash_replacement,
        "phase_hash_legacy": phase_hash_legacy,
        "phase_hash_replacement": phase_hash_replacement,
        "rng_hash_legacy": rng_hash_legacy,
        "rng_hash_replacement": rng_hash_replacement,
    }


def step_replacement(world: World, cfg: dict[str, Any], action_phase: np.ndarray) -> np.ndarray:
    world.P = action_phase.copy()
    iota_rig.step(world, cfg)
    next_phase = world.P.copy()
    world.P.fill(0)
    return next_phase


def row_at_offset(rows: list[dict[str, Any]], key: str, offset: int) -> str:
    for row in rows:
        if int(row["offset"]) == int(offset):
            return str(row[key])
    return ""


def build_summary(
    case_label: str,
    cfg: dict[str, Any],
    args: argparse.Namespace,
    sample_index: int,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
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
        "case_label": case_label,
        "init_seed": int(cfg.get("init", {}).get("seed", -1)),
        "checkpoint_tick": int(args.checkpoint_tick),
        "sample_index": int(sample_index),
        "continuation_seed": deterministic_continuation_seed(
            int(args.rng_seed_base),
            int(args.checkpoint_tick),
            int(sample_index),
        ),
        "ticks_compared": len(rows),
        "nonpayload_equal_ticks": sum(1 for row in rows if int(row["nonpayload_equal"]) == 1),
        "phase_equal_ticks": sum(1 for row in rows if int(row["phase_equal"]) == 1),
        "replacement_payload_zero_ticks": sum(1 for row in rows if int(row["replacement_payload_zero"]) == 1),
        "rng_equal_ticks": sum(1 for row in rows if int(row["rng_equal"]) == 1),
        "first_nonpayload_divergence_tick": first_tick(rows, "nonpayload_equal", 0),
        "first_phase_divergence_tick": first_tick(rows, "phase_equal", 0),
        "first_replacement_payload_nonzero_tick": first_tick(rows, "replacement_payload_zero", 0),
        "first_rng_divergence_tick": first_tick(rows, "rng_equal", 0),
        "phase_collapse_tick": first_phase_collapse_tick(rows),
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
        "pivotal_target_active_499": row_at_offset(rows, "pivotal_target_active", PIVOTAL_OFFSET),
        "pivotal_target_active_511": row_at_offset(rows, "pivotal_target_active", SPLIT_OFFSET - 1),
        "pivotal_target_active_512": row_at_offset(rows, "pivotal_target_active", SPLIT_OFFSET),
        "split_target_active_512": row_at_offset(rows, "split_target_active", SPLIT_OFFSET),
        "split_target_active_515": row_at_offset(rows, "split_target_active", REBRIDGE_OFFSET),
        "rebridge_target_active_515": row_at_offset(rows, "rebridge_target_active", REBRIDGE_OFFSET),
        "checkpoint_active_iotas": int(checkpoint_row["active_iotas"]),
        "checkpoint_component_count": int(checkpoint_row["component_count_cube26"]),
        "checkpoint_largest_component": int(checkpoint_row["largest_component_cube26"]),
        "checkpoint_phase_nonzero_iotas": int(checkpoint_row["phase_nonzero_iotas"]),
        "checkpoint_phase_unique": int(checkpoint_row["phase_unique"]),
        "checkpoint_p_sensitive_primary_count": int(checkpoint_row["p_sensitive_primary_count"]),
        "final_active_iotas": int(final_row["active_iotas"]),
        "final_component_count": int(final_row["component_count_cube26"]),
        "final_largest_component": int(final_row["largest_component_cube26"]),
        "final_phase_nonzero_iotas": int(final_row["phase_nonzero_iotas"]),
        "final_phase_unique": int(final_row["phase_unique"]),
        "ledger_exact": csv_bool(
            all(
                abs(float(row["legacy_ledger_error"])) == 0.0
                and abs(float(row["replacement_ledger_error"])) == 0.0
                for row in rows
            )
        ),
        "max_abs_ledger_error": max(
            max(abs(float(row["legacy_ledger_error"])), abs(float(row["replacement_ledger_error"])))
            for row in rows
        ),
        "final_nonpayload_hash": str(final_row["nonpayload_hash_legacy"]),
        "final_phase_hash": str(final_row["phase_hash_legacy"]),
    }


def first_tick(rows: list[dict[str, Any]], key: str, target_value: int) -> str:
    for row in rows:
        if int(row[key]) == int(target_value):
            return str(int(row["tick"]))
    return ""


def first_phase_collapse_tick(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if int(row["phase_nonzero_iotas"]) == 0:
            return str(int(row["tick"]))
    return ""


def run_case(args: argparse.Namespace, config_path: Path, sample_index: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cfg = load_config(config_path)
    legacy = iota_rig.init_world(cfg)
    replacement = iota_rig.init_world(cfg)
    action_phase = replacement.P.copy()
    replacement.P.fill(0)
    case_label = f"seed{int(cfg.get('init', {}).get('seed', -1))}_sample{int(sample_index)}"
    continuation_seed = deterministic_continuation_seed(
        int(args.rng_seed_base),
        int(args.checkpoint_tick),
        int(sample_index),
    )
    rows: list[dict[str, Any]] = []
    checkpoint_count: int | None = None
    checkpoint_largest: int | None = None
    previous_count: int | None = None
    previous_largest: int | None = None
    end_tick = int(args.checkpoint_tick) + int(args.horizon)
    for tick in range(0, end_tick + 1):
        if tick == int(args.checkpoint_tick):
            checkpoint_count, checkpoint_largest = component_snapshot(legacy)
            legacy = clone_world(legacy, continuation_seed)
            replacement = clone_world(replacement, continuation_seed)
            replacement.P.fill(0)
            action_phase = action_phase.copy()
            previous_count = checkpoint_count
            previous_largest = checkpoint_largest
        row = make_timeline_row(
            case_label,
            legacy,
            replacement,
            action_phase,
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
        if tick >= end_tick:
            break
        iota_rig.step(legacy, cfg)
        action_phase = step_replacement(replacement, cfg, action_phase)
    return build_summary(case_label, cfg, args, sample_index, rows), rows


def aggregate_payload(summary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cases": len(summary_rows),
        "exact_nonpayload_cases": sum(
            1 for row in summary_rows if int(row["nonpayload_equal_ticks"]) == int(row["ticks_compared"])
        ),
        "exact_phase_cases": sum(
            1 for row in summary_rows if int(row["phase_equal_ticks"]) == int(row["ticks_compared"])
        ),
        "payload_zero_cases": sum(
            1 for row in summary_rows if int(row["replacement_payload_zero_ticks"]) == int(row["ticks_compared"])
        ),
        "rng_equal_cases": sum(
            1 for row in summary_rows if int(row["rng_equal_ticks"]) == int(row["ticks_compared"])
        ),
        "component_signal_cases": sum(1 for row in summary_rows if str(row["component_signal_offsets"]) != ""),
        "split_at_512_cases": sum(1 for row in summary_rows if int(row["split_at_512"]) == 1),
        "rebridge_at_515_cases": sum(1 for row in summary_rows if int(row["rebridge_at_515"]) == 1),
        "ledger_exact_cases": sum(1 for row in summary_rows if int(row["ledger_exact"]) == 1),
    }


def main() -> None:
    args = parse_args()
    summary_rows: list[dict[str, Any]] = []
    timeline_rows: list[dict[str, Any]] = []
    for seed in args.seeds:
        config_path = discover_config(args.config_dir, seed)
        for sample_index in args.sample_indices:
            summary, rows = run_case(args, config_path, int(sample_index))
            summary_rows.append(summary)
            if int(seed) == int(args.timeline_seed) and int(sample_index) == int(args.timeline_sample_index):
                timeline_rows.extend(rows)
            print(
                f"seed={seed} sample={sample_index} exact_nonpayload="
                f"{summary['nonpayload_equal_ticks']}/{summary['ticks_compared']} "
                f"signal={summary['component_signal_offsets'] or 'none'}"
            )

    output_prefix = Path(args.output_prefix)
    write_csv(output_prefix.with_name(output_prefix.name + "_summary.csv"), SUMMARY_FIELDNAMES, summary_rows)
    write_csv(output_prefix.with_name(output_prefix.name + "_timeline.csv"), TIMELINE_FIELDNAMES, timeline_rows)
    payload = {
        "summary_csv": str(output_prefix.with_name(output_prefix.name + "_summary.csv")),
        "timeline_csv": str(output_prefix.with_name(output_prefix.name + "_timeline.csv")),
        "aggregate": aggregate_payload(summary_rows),
        "summary_by_case": {str(row["case_label"]): row for row in summary_rows},
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
