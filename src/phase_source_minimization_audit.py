from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import iota_rig
from component_bridge_causal_trace import write_csv
from continuation import clone_world, deterministic_continuation_seed
from iota_rig import World, load_config
from payload_action_phase_audit import (
    PAIR_FIELDNAMES,
    SUMMARY_FIELDNAMES,
    TIMELINE_FIELDNAMES,
    build_summary,
    component_snapshot,
    divergence_pair,
    make_timeline_row,
)


VARIANTS = (
    "natural",
    "zero_phase",
    "vector_state_phase",
    "interaction_phase",
    "rotation_only_interaction_phase",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test phase-source minimization laws with no stored payload/action phase."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46, 56])
    parser.add_argument(
        "--variants",
        nargs="+",
        choices=VARIANTS,
        default=[
            "natural",
            "zero_phase",
            "interaction_phase",
            "rotation_only_interaction_phase",
        ],
    )
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--horizon", type=int, default=1024)
    parser.add_argument("--sample-index", type=int, default=6)
    parser.add_argument("--rng-seed-base", type=int, default=20260708)
    parser.add_argument("--timeline-seed", type=int, default=46)
    return parser.parse_args()


def discover_config(config_dir: str, seed: int) -> Path:
    matches = sorted(Path(config_dir).glob(f"v036_component_bridge_seed{int(seed)}_*.yaml"))
    if len(matches) != 1:
        raise SystemExit(f"expected one v0.3.6 config for seed {seed}, found {len(matches)}")
    return matches[0]


def influence_phase(influence: float) -> int:
    return max(1, min(7, int(round(float(influence) * 7.0))))


def vector_state_phase(v_idx: int) -> int:
    return int(v_idx) % 8


def vector_step_phase(v_idx: int, a: int, r: int, variant: str) -> int:
    if variant == "vector_state_phase":
        return vector_state_phase(v_idx)
    if variant == "interaction_phase":
        return (int(v_idx) + int(a) + int(r)) % 8
    return 0


def takeover_phase(v_idx: int, variant: str) -> int:
    if variant in {"vector_state_phase", "interaction_phase"}:
        return vector_state_phase(v_idx)
    return 0


def rotation_phases(
    source_v: int,
    target_v: int,
    target_a: int,
    target_r: int,
    candidate_order: int,
    target_depleted: bool,
    influence: float,
    variant: str,
) -> tuple[int, int]:
    if variant == "vector_state_phase":
        return vector_state_phase(source_v), vector_state_phase(target_v)
    if variant in {"interaction_phase", "rotation_only_interaction_phase"}:
        residual_phase = 1 if target_depleted else 0
        source_phase = (
            int(source_v)
            + int(candidate_order)
            + influence_phase(influence)
            + residual_phase
        ) % 8
        target_phase = (
            int(target_v)
            + int(target_a)
            + int(target_r)
            + int(candidate_order)
        ) % 8
        return source_phase, target_phase
    return 0, 0


@contextmanager
def phase_source_patch(variant: str) -> Iterator[None]:
    original_vector_step = iota_rig.vector_step
    original_rotate_vector_state = iota_rig.rotate_vector_state
    original_rotation_offset = iota_rig.history_coupled_rotation_offset
    original_signed_rotation_offset = iota_rig.history_coupled_signed_rotation_offset

    def vector_step_wrapper(world: World, v_idx: int, a: int, r: int, p: int) -> tuple[int, int, int, str]:
        return original_vector_step(
            world,
            v_idx,
            a,
            r,
            vector_step_phase(v_idx, a, r, variant),
        )

    def rotate_vector_state_wrapper(world: World, v_idx: int, payload: int) -> int:
        return original_rotate_vector_state(world, v_idx, takeover_phase(v_idx, variant))

    def rotation_offset_wrapper(
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
        derived_source_p, derived_target_p = rotation_phases(
            source_v,
            target_v,
            target_a,
            target_r,
            candidate_order,
            target_depleted,
            influence,
            variant,
        )
        return original_rotation_offset(
            source_v=source_v,
            source_p=derived_source_p,
            target_v=target_v,
            target_a=target_a,
            target_r=target_r,
            target_p=derived_target_p,
            candidate_order=candidate_order,
            target_depleted=target_depleted,
            influence=influence,
            max_offset=max_offset,
        )

    def signed_rotation_offset_wrapper(
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
        derived_source_p, derived_target_p = rotation_phases(
            source_v,
            target_v,
            target_a,
            target_r,
            candidate_order,
            target_depleted,
            influence,
            variant,
        )
        saved_rotation_offset = iota_rig.history_coupled_rotation_offset
        iota_rig.history_coupled_rotation_offset = original_rotation_offset
        try:
            return original_signed_rotation_offset(
                source_v=source_v,
                source_p=derived_source_p,
                target_v=target_v,
                target_a=target_a,
                target_r=target_r,
                target_p=derived_target_p,
                candidate_order=candidate_order,
                target_depleted=target_depleted,
                influence=influence,
                max_offset=max_offset,
            )
        finally:
            iota_rig.history_coupled_rotation_offset = saved_rotation_offset

    if variant != "natural":
        iota_rig.vector_step = vector_step_wrapper
        iota_rig.rotate_vector_state = rotate_vector_state_wrapper
        iota_rig.history_coupled_rotation_offset = rotation_offset_wrapper
        iota_rig.history_coupled_signed_rotation_offset = signed_rotation_offset_wrapper
    try:
        yield
    finally:
        iota_rig.vector_step = original_vector_step
        iota_rig.rotate_vector_state = original_rotate_vector_state
        iota_rig.history_coupled_rotation_offset = original_rotation_offset
        iota_rig.history_coupled_signed_rotation_offset = original_signed_rotation_offset


def clamp_stored_phase(world: World, variant: str) -> None:
    if variant != "natural":
        world.P.fill(0)


def run_variant(
    args: argparse.Namespace,
    cfg: dict[str, Any],
    seed: int,
    variant: str,
) -> list[dict[str, Any]]:
    continuation_seed = deterministic_continuation_seed(
        int(args.rng_seed_base),
        int(args.checkpoint_tick),
        int(args.sample_index),
    )
    rows: list[dict[str, Any]] = []
    with phase_source_patch(variant):
        world = iota_rig.init_world(cfg)
        clamp_stored_phase(world, variant)
        previous_count: int | None = None
        previous_largest: int | None = None
        checkpoint_count: int | None = None
        checkpoint_largest: int | None = None
        end_tick = int(args.checkpoint_tick) + int(args.horizon)
        for tick in range(0, end_tick + 1):
            if tick == int(args.checkpoint_tick):
                checkpoint_count, checkpoint_largest = component_snapshot(world)
                world = clone_world(world, continuation_seed)
                clamp_stored_phase(world, variant)
                previous_count = checkpoint_count
                previous_largest = checkpoint_largest
            if tick >= int(args.checkpoint_tick):
                rows.append(
                    make_timeline_row(
                        variant,
                        world,
                        tick,
                        int(args.checkpoint_tick),
                        checkpoint_count,
                        checkpoint_largest,
                        previous_count,
                        previous_largest,
                    )
                )
                previous_count = int(rows[-1]["component_count_cube26"])
                previous_largest = int(rows[-1]["largest_component_cube26"])
            if tick >= end_tick:
                break
            clamp_stored_phase(world, variant)
            iota_rig.step(world, cfg)
            clamp_stored_phase(world, variant)
    for row in rows:
        row["init_seed"] = int(seed)
    return rows


def main() -> None:
    args = parse_args()
    output_prefix = Path(args.output_prefix)
    summaries: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    timeline_rows: list[dict[str, Any]] = []

    for seed in args.seeds:
        cfg = load_config(discover_config(args.config_dir, int(seed)))
        rows_by_variant: dict[str, list[dict[str, Any]]] = {}
        summaries_by_variant: dict[str, dict[str, Any]] = {}
        for variant in args.variants:
            rows = run_variant(args, cfg, int(seed), variant)
            rows_by_variant[variant] = rows
            summary = build_summary(variant, args, rows)
            summary["init_seed"] = int(seed)
            summaries_by_variant[variant] = summary
            summaries.append(summary)
            if int(seed) == int(args.timeline_seed):
                timeline_rows.extend(rows)
            print(
                f"seed={seed} variant={variant} "
                f"signal={summary['component_signal_offsets'] or 'none'} "
                f"checkpoint_active={summary['checkpoint_active_iotas']} "
                f"checkpoint_payload={summary['checkpoint_nonzero_payload_iotas']} "
                f"ledger={summary['ledger_exact']}"
            )
        if "natural" in summaries_by_variant:
            natural_summary = summaries_by_variant["natural"]
            natural_rows = rows_by_variant["natural"]
            for variant, summary in summaries_by_variant.items():
                if variant == "natural":
                    continue
                pair = divergence_pair(summary, natural_summary, rows_by_variant[variant], natural_rows)
                pair["init_seed"] = int(seed)
                pairs.append(pair)

    summary_path = output_prefix.with_name(output_prefix.name + "_summary.csv")
    pair_path = output_prefix.with_name(output_prefix.name + "_pairs.csv")
    timeline_path = output_prefix.with_name(output_prefix.name + "_timeline.csv")
    write_csv(summary_path, SUMMARY_FIELDNAMES, summaries)
    write_csv(pair_path, ["init_seed", *PAIR_FIELDNAMES], pairs)
    write_csv(timeline_path, ["init_seed", *TIMELINE_FIELDNAMES], timeline_rows)
    payload = {
        "summary_csv": str(summary_path),
        "pairs_csv": str(pair_path),
        "timeline_csv": str(timeline_path),
        "summary_by_seed_variant": {
            f"{row['init_seed']}:{row['variant']}": row for row in summaries
        },
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
