from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np

from component_bridge_causal_trace import component_labels, csv_bool, write_csv
from continuation import clone_world, deterministic_continuation_seed, load_checkpoint
from iota_rig import World, init_world, load_config, step


PIVOTAL_OFFSET = 499
SPLIT_OFFSET = 512
REBRIDGE_OFFSET = 515
PIVOTAL_TARGET = (13, 3, 38)
SPLIT_TARGET = (12, 2, 38)
REBRIDGE_TARGET = (13, 2, 38)
CAUSAL_CELLS = (PIVOTAL_TARGET, SPLIT_TARGET, REBRIDGE_TARGET)

VARIANTS = (
    "natural",
    "neutral_payload_coupling",
    "uniform_payload_initial",
    "clamp_payload_each_tick",
)

SUMMARY_FIELDNAMES = [
    "case_label",
    "start_mode",
    "variant",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "same_payload_coupling",
    "cross_payload_coupling",
    "payload_takeover",
    "payload_mutation_rate",
    "checkpoint_component_count",
    "checkpoint_largest_component",
    "checkpoint_payload_entropy",
    "checkpoint_payload_unique",
    "final_component_count",
    "final_largest_component",
    "first_component_change_offset",
    "component_signal_offsets",
    "component_signal_vanish_offset",
    "split_at_512",
    "rebridge_at_515",
    "pivotal_target_active_499",
    "pivotal_target_active_511",
    "pivotal_target_active_512",
    "split_target_active_512",
    "split_target_active_515",
    "rebridge_target_active_515",
    "active_iotas_final",
    "ledger_exact",
    "max_abs_ledger_error",
    "payload_entropy_final",
    "payload_unique_final",
    "state_hash_full",
    "state_hash_without_payload",
]

TIMELINE_FIELDNAMES = [
    "case_label",
    "start_mode",
    "variant",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "offset",
    "tick",
    "active_iotas",
    "component_count_cube26",
    "component_delta_from_checkpoint",
    "component_delta_from_previous",
    "largest_component_cube26",
    "largest_delta_from_checkpoint",
    "largest_delta_from_previous",
    "ledger_error",
    "payload_entropy",
    "payload_unique",
    "pivotal_target_active",
    "split_target_active",
    "rebridge_target_active",
]

PAIR_FIELDNAMES = [
    "case_label",
    "start_mode",
    "init_seed",
    "checkpoint_tick",
    "sample_index",
    "variant",
    "reference_variant",
    "same_component_signal",
    "same_first_component_change_offset",
    "same_split_at_512",
    "same_rebridge_at_515",
    "same_final_component_count",
    "same_final_largest_component",
    "same_state_without_payload",
    "component_signal_offsets",
    "reference_component_signal_offsets",
    "state_hash_without_payload",
    "reference_state_hash_without_payload",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay v0.3.6 continuations with payload influence/state ablated."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[46])
    parser.add_argument("--sample-indices", nargs="+", type=int, default=[6])
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--horizon", type=int, default=1024)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--finding-dir", default="output/findings")
    parser.add_argument("--variants", nargs="+", choices=VARIANTS, default=list(VARIANTS))
    parser.add_argument(
        "--start-mode",
        choices=["checkpoint", "init"],
        default="checkpoint",
        help="Start from saved checkpoint or regenerate the checkpoint from init first.",
    )
    parser.add_argument(
        "--timeline-seed",
        type=int,
        default=46,
        help="Write per-tick timeline rows only for this seed/sample pair.",
    )
    parser.add_argument("--timeline-sample-index", type=int, default=6)
    return parser.parse_args()


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


def ledger_error(world: World) -> float:
    active_total = int(np.sum(world.A[world.active], dtype=np.int64))
    latent_total = int(np.sum(world.latent_A[~world.active], dtype=np.int64))
    return float(active_total + latent_total - int(world.initial_total_A))


def state_hash(world: World, include_payload: bool) -> str:
    digest = hashlib.sha256()
    for array in (world.active, world.A, world.R, world.V, world.latent_A, world.angular_L):
        digest.update(np.ascontiguousarray(array).view(np.uint8))
    if include_payload:
        digest.update(np.ascontiguousarray(world.P).view(np.uint8))
    return digest.hexdigest()


def discover_case_paths(args: argparse.Namespace, seed: int) -> tuple[Path, Path]:
    config_matches = sorted(
        Path(args.config_dir).glob(f"v036_component_bridge_seed{int(seed)}_*.yaml")
    )
    if len(config_matches) != 1:
        raise SystemExit(f"expected one v0.3.6 config for seed {seed}, found {len(config_matches)}")
    state_matches = sorted(
        Path(args.finding_dir).glob(
            f"finding_046_v036_component_bridge_seed{int(seed)}_*_rotation_aware_openness_states"
        )
    )
    if len(state_matches) != 1:
        raise SystemExit(f"expected one v0.3.6 state dir for seed {seed}, found {len(state_matches)}")
    return config_matches[0], state_matches[0]


def variant_config(cfg: dict[str, Any], variant: str) -> dict[str, Any]:
    next_cfg = deepcopy(cfg)
    if variant != "natural":
        constants = next_cfg.setdefault("constants", {})
        constants["same_payload_coupling"] = 1.0
        constants["cross_payload_coupling"] = 1.0
        constants["mutation_rate"] = 0.0
    return next_cfg


def apply_payload_ablation(world: World, variant: str) -> None:
    if variant in {"uniform_payload_initial", "clamp_payload_each_tick"}:
        world.P.fill(0)


def component_snapshot(world: World) -> tuple[int, int]:
    _, _, count, largest = component_labels(world.active, bool(world.wrap), "cube26")
    return int(count), int(largest)


def timeline_row(
    case_ids: dict[str, Any],
    world: World,
    offset: int,
    checkpoint_count: int,
    checkpoint_largest: int,
    previous_count: int | None,
    previous_largest: int | None,
) -> dict[str, Any]:
    count, largest = component_snapshot(world)
    return {
        **case_ids,
        "offset": int(offset),
        "tick": int(case_ids["checkpoint_tick"] + offset),
        "active_iotas": int(np.count_nonzero(world.active)),
        "component_count_cube26": count,
        "component_delta_from_checkpoint": int(count - checkpoint_count),
        "component_delta_from_previous": 0 if previous_count is None else int(count - previous_count),
        "largest_component_cube26": largest,
        "largest_delta_from_checkpoint": int(largest - checkpoint_largest),
        "largest_delta_from_previous": 0 if previous_largest is None else int(largest - previous_largest),
        "ledger_error": ledger_error(world),
        "payload_entropy": payload_entropy(world),
        "payload_unique": payload_unique(world),
        "pivotal_target_active": csv_bool(bool(world.active[PIVOTAL_TARGET])),
        "split_target_active": csv_bool(bool(world.active[SPLIT_TARGET])),
        "rebridge_target_active": csv_bool(bool(world.active[REBRIDGE_TARGET])),
    }


def active_at_offset(
    active_cells: dict[tuple[int, int, int], dict[int, int]],
    cell: tuple[int, int, int],
    offset: int,
) -> str:
    return str(active_cells.get(cell, {}).get(offset, ""))


def build_summary(
    case_ids: dict[str, Any],
    cfg: dict[str, Any],
    variant: str,
    timeline_rows: list[dict[str, Any]],
    active_cells: dict[tuple[int, int, int], dict[int, int]],
    world: World,
) -> dict[str, Any]:
    checkpoint_row = timeline_rows[0]
    final_row = timeline_rows[-1]
    signal_rows = [
        row for row in timeline_rows if int(row["component_delta_from_checkpoint"]) != 0
    ]
    first_signal = signal_rows[0] if signal_rows else None
    vanish_row = None
    if first_signal is not None:
        first_index = timeline_rows.index(first_signal)
        for row in timeline_rows[first_index + 1 :]:
            if int(row["component_delta_from_checkpoint"]) == 0:
                vanish_row = row
                break
    constants = cfg.get("constants", {})
    return {
        **case_ids,
        "variant": variant,
        "same_payload_coupling": float(constants.get("same_payload_coupling", 1.0)),
        "cross_payload_coupling": float(constants.get("cross_payload_coupling", 1.0)),
        "payload_takeover": float(constants.get("payload_takeover", 0.5)),
        "payload_mutation_rate": float(constants.get("mutation_rate", 0.0)),
        "checkpoint_component_count": int(checkpoint_row["component_count_cube26"]),
        "checkpoint_largest_component": int(checkpoint_row["largest_component_cube26"]),
        "checkpoint_payload_entropy": float(checkpoint_row["payload_entropy"]),
        "checkpoint_payload_unique": int(checkpoint_row["payload_unique"]),
        "final_component_count": int(final_row["component_count_cube26"]),
        "final_largest_component": int(final_row["largest_component_cube26"]),
        "first_component_change_offset": "" if first_signal is None else int(first_signal["offset"]),
        "component_signal_offsets": ";".join(str(int(row["offset"])) for row in signal_rows),
        "component_signal_vanish_offset": "" if vanish_row is None else int(vanish_row["offset"]),
        "split_at_512": csv_bool(
            any(
                int(row["offset"]) == SPLIT_OFFSET and int(row["component_delta_from_previous"]) > 0
                for row in timeline_rows
            )
        ),
        "rebridge_at_515": csv_bool(
            any(
                int(row["offset"]) == REBRIDGE_OFFSET and int(row["component_delta_from_previous"]) < 0
                for row in timeline_rows
            )
        ),
        "pivotal_target_active_499": active_at_offset(active_cells, PIVOTAL_TARGET, PIVOTAL_OFFSET),
        "pivotal_target_active_511": active_at_offset(active_cells, PIVOTAL_TARGET, SPLIT_OFFSET - 1),
        "pivotal_target_active_512": active_at_offset(active_cells, PIVOTAL_TARGET, SPLIT_OFFSET),
        "split_target_active_512": active_at_offset(active_cells, SPLIT_TARGET, SPLIT_OFFSET),
        "split_target_active_515": active_at_offset(active_cells, SPLIT_TARGET, REBRIDGE_OFFSET),
        "rebridge_target_active_515": active_at_offset(active_cells, REBRIDGE_TARGET, REBRIDGE_OFFSET),
        "active_iotas_final": int(final_row["active_iotas"]),
        "ledger_exact": csv_bool(all(abs(float(row["ledger_error"])) == 0.0 for row in timeline_rows)),
        "max_abs_ledger_error": max(abs(float(row["ledger_error"])) for row in timeline_rows),
        "payload_entropy_final": float(final_row["payload_entropy"]),
        "payload_unique_final": int(final_row["payload_unique"]),
        "state_hash_full": state_hash(world, include_payload=True),
        "state_hash_without_payload": state_hash(world, include_payload=False),
    }


def run_case_variant(
    args: argparse.Namespace,
    seed: int,
    sample_index: int,
    config_path: Path,
    state_dir: Path,
    variant: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cfg = variant_config(load_config(config_path), variant)
    continuation_seed = deterministic_continuation_seed(
        int(args.rng_seed_base),
        int(args.checkpoint_tick),
        int(sample_index),
    )
    if args.start_mode == "checkpoint":
        checkpoint_path = state_dir / f"checkpoint_tick_{int(args.checkpoint_tick):06d}.npz"
        checkpoint = load_checkpoint(checkpoint_path)
    else:
        checkpoint = init_world(cfg)
        apply_payload_ablation(checkpoint, variant)
        for _tick in range(1, int(args.checkpoint_tick) + 1):
            if variant == "clamp_payload_each_tick":
                checkpoint.P.fill(0)
            step(checkpoint, cfg)
            if variant == "clamp_payload_each_tick":
                checkpoint.P.fill(0)
    world = clone_world(checkpoint, continuation_seed)
    apply_payload_ablation(world, variant)

    case_label = f"{args.start_mode}_seed{int(seed)}_sample{int(sample_index)}"
    case_ids = {
        "case_label": case_label,
        "start_mode": str(args.start_mode),
        "variant": variant,
        "init_seed": int(seed),
        "checkpoint_tick": int(args.checkpoint_tick),
        "sample_index": int(sample_index),
        "continuation_seed": continuation_seed,
    }
    checkpoint_count, checkpoint_largest = component_snapshot(world)
    active_cells = {
        cell: {0: csv_bool(bool(world.active[cell]))}
        for cell in CAUSAL_CELLS
    }
    timeline_rows = [
        timeline_row(
            case_ids,
            world,
            0,
            checkpoint_count,
            checkpoint_largest,
            None,
            None,
        )
    ]
    previous_count = checkpoint_count
    previous_largest = checkpoint_largest
    for offset in range(1, int(args.horizon) + 1):
        if variant == "clamp_payload_each_tick":
            world.P.fill(0)
        step(world, cfg)
        if variant == "clamp_payload_each_tick":
            world.P.fill(0)
        row = timeline_row(
            case_ids,
            world,
            offset,
            checkpoint_count,
            checkpoint_largest,
            previous_count,
            previous_largest,
        )
        timeline_rows.append(row)
        previous_count = int(row["component_count_cube26"])
        previous_largest = int(row["largest_component_cube26"])
        for cell in CAUSAL_CELLS:
            active_cells[cell][offset] = csv_bool(bool(world.active[cell]))

    summary = build_summary(case_ids, cfg, variant, timeline_rows, active_cells, world)
    should_keep_timeline = (
        int(seed) == int(args.timeline_seed)
        and int(sample_index) == int(args.timeline_sample_index)
    )
    return summary, timeline_rows if should_keep_timeline else []


def build_pair_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    natural_by_case = {
        (
            str(row["start_mode"]),
            int(row["init_seed"]),
            int(row["checkpoint_tick"]),
            int(row["sample_index"]),
        ): row
        for row in summary_rows
        if row["variant"] == "natural"
    }
    pair_rows: list[dict[str, Any]] = []
    for row in summary_rows:
        if row["variant"] == "natural":
            continue
        key = (
            str(row["start_mode"]),
            int(row["init_seed"]),
            int(row["checkpoint_tick"]),
            int(row["sample_index"]),
        )
        reference = natural_by_case.get(key)
        if reference is None:
            continue
        pair_rows.append(
            {
                "case_label": row["case_label"],
                "start_mode": row["start_mode"],
                "init_seed": row["init_seed"],
                "checkpoint_tick": row["checkpoint_tick"],
                "sample_index": row["sample_index"],
                "variant": row["variant"],
                "reference_variant": "natural",
                "same_component_signal": csv_bool(
                    str(row["component_signal_offsets"]) == str(reference["component_signal_offsets"])
                ),
                "same_first_component_change_offset": csv_bool(
                    str(row["first_component_change_offset"])
                    == str(reference["first_component_change_offset"])
                ),
                "same_split_at_512": csv_bool(int(row["split_at_512"]) == int(reference["split_at_512"])),
                "same_rebridge_at_515": csv_bool(
                    int(row["rebridge_at_515"]) == int(reference["rebridge_at_515"])
                ),
                "same_final_component_count": csv_bool(
                    int(row["final_component_count"]) == int(reference["final_component_count"])
                ),
                "same_final_largest_component": csv_bool(
                    int(row["final_largest_component"]) == int(reference["final_largest_component"])
                ),
                "same_state_without_payload": csv_bool(
                    str(row["state_hash_without_payload"])
                    == str(reference["state_hash_without_payload"])
                ),
                "component_signal_offsets": row["component_signal_offsets"],
                "reference_component_signal_offsets": reference["component_signal_offsets"],
                "state_hash_without_payload": row["state_hash_without_payload"],
                "reference_state_hash_without_payload": reference["state_hash_without_payload"],
            }
        )
    return pair_rows


def aggregate_payload(summary_rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    variants = sorted({str(row["variant"]) for row in summary_rows})
    aggregate: dict[str, Any] = {}
    for variant in variants:
        rows = [row for row in summary_rows if row["variant"] == variant]
        aggregate[variant] = {
            "cases": len(rows),
            "component_signal_cases": sum(1 for row in rows if str(row["component_signal_offsets"]) != ""),
            "split_at_512_cases": sum(1 for row in rows if int(row["split_at_512"]) == 1),
            "rebridge_at_515_cases": sum(1 for row in rows if int(row["rebridge_at_515"]) == 1),
            "ledger_exact_cases": sum(1 for row in rows if int(row["ledger_exact"]) == 1),
            "payload_unique_final_values": sorted({int(row["payload_unique_final"]) for row in rows}),
        }
    for variant in variants:
        if variant == "natural":
            continue
        pairs = [row for row in pair_rows if row["variant"] == variant]
        aggregate[variant]["same_component_signal_vs_natural"] = sum(
            1 for row in pairs if int(row["same_component_signal"]) == 1
        )
        aggregate[variant]["same_state_without_payload_vs_natural"] = sum(
            1 for row in pairs if int(row["same_state_without_payload"]) == 1
        )
    return aggregate


def main() -> None:
    args = parse_args()
    summary_rows: list[dict[str, Any]] = []
    timeline_rows: list[dict[str, Any]] = []
    for seed in args.seeds:
        config_path, state_dir = discover_case_paths(args, seed)
        for sample_index in args.sample_indices:
            for variant in args.variants:
                summary, timeline = run_case_variant(
                    args,
                    int(seed),
                    int(sample_index),
                    config_path,
                    state_dir,
                    variant,
                )
                summary_rows.append(summary)
                timeline_rows.extend(timeline)
                print(
                    f"seed={seed} sample={sample_index} variant={variant} "
                    f"signal={summary['component_signal_offsets'] or 'none'} "
                    f"payload_unique_final={summary['payload_unique_final']}"
                )

    pair_rows = build_pair_rows(summary_rows)
    output_prefix = Path(args.output_prefix)
    write_csv(output_prefix.with_name(output_prefix.name + "_summary.csv"), SUMMARY_FIELDNAMES, summary_rows)
    write_csv(output_prefix.with_name(output_prefix.name + "_pairs.csv"), PAIR_FIELDNAMES, pair_rows)
    write_csv(output_prefix.with_name(output_prefix.name + "_timeline.csv"), TIMELINE_FIELDNAMES, timeline_rows)
    payload = {
        "summary_csv": str(output_prefix.with_name(output_prefix.name + "_summary.csv")),
        "pairs_csv": str(output_prefix.with_name(output_prefix.name + "_pairs.csv")),
        "timeline_csv": str(output_prefix.with_name(output_prefix.name + "_timeline.csv")),
        "aggregate": aggregate_payload(summary_rows, pair_rows),
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
