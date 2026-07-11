from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import csv_bool, write_csv
from continuation import clone_world
from expression_lineage_transport import (
    advance_lineages,
    coords_text,
    lineage_relation,
)
from iota_rig import World, load_config
from phase_free_class_matrix import run_to_checkpoint
from phase_free_constraint_transport import ledger_error
from phase_source_minimization_audit import clamp_stored_phase, discover_config, phase_source_patch
from predecessor_region_lineage import read_events, reconstruct_regions


SOURCE_EVENTS = (
    (46, 7, 61, 65),
    (46, 7, 420, 424),
    (56, 3, 106, 112),
)

CASE_FIELDNAMES = [
    "init_seed",
    "sample_index",
    "event_start_offset",
    "branch_offset",
    "branch_sample",
    "branch_seed",
    "horizon",
    "singleton_original",
    "singleton_lineage_size_at_branch",
    "original_address_loss_offset",
    "address_loss_observed",
    "handoff_success",
    "preexisting_descendant_at_loss",
    "death_tick_child_count",
    "death_tick_children",
    "death_tick_candidate_orders",
    "death_tick_depleted_targets",
    "expression_survival_after_loss",
    "postloss_relation_lifetime",
    "lineage_collision",
    "payload_zero_all_offsets",
    "ledger_exact_all_offsets",
]

AGGREGATE_FIELDNAMES = [
    "init_seed",
    "event_start_offset",
    "branch_offset",
    "branches",
    "address_loss_branches",
    "censored_branches",
    "ambiguous_collision_branches",
    "eligible_address_loss_branches",
    "handoff_successes",
    "handoff_failures",
    "handoff_rate",
    "handoff_wilson_low",
    "handoff_wilson_high",
    "mean_time_to_address_loss",
    "mean_postloss_relation_lifetime",
    "payload_zero_branches",
    "ledger_exact_branches",
]

COMPARISON_FIELDNAMES = [
    "left_source",
    "right_source",
    "left_successes",
    "left_trials",
    "right_successes",
    "right_trials",
    "rate_difference_left_minus_right",
    "odds_ratio",
    "fisher_exact_two_sided_p",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Branch immediately before singleton address loss and measure expression handoff."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument(
        "--event-csv",
        default="output/findings/finding060/phase_free_constraint_transport_events.csv",
    )
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--horizon", type=int, default=128)
    parser.add_argument("--branch-seed-base", type=int, default=2026071100)
    return parser.parse_args()


def select_source_events(path: Path) -> list[tuple[dict[str, str], int]]:
    strict = read_events(path, strict_only=True)
    selected: list[tuple[dict[str, str], int]] = []
    for seed, sample, start, branch_offset in SOURCE_EVENTS:
        matches = [
            row
            for row in strict
            if int(row["init_seed"]) == seed
            and int(row["sample_index"]) == sample
            and int(row["start_offset"]) == start
        ]
        if len(matches) != 1:
            raise RuntimeError(f"expected one source event {(seed, sample, start)}, found {len(matches)}")
        selected.append((matches[0], branch_offset))
    return selected


def build_branch_state(
    event: dict[str, str],
    branch_offset: int,
    checkpoint: World,
    cfg: dict[str, Any],
) -> tuple[World, list[set[tuple[int, int, int]]], int, tuple[int, int, int]]:
    continuation_seed = int(event["continuation_seed"])
    start_offset = int(event["start_offset"])
    rebridge_offset = int(event["rebridge_offset"])
    world = clone_world(checkpoint, continuation_seed)
    snapshots: dict[int, World] = {}
    regions: list[set[tuple[int, int, int]]] = []
    lineages: list[set[tuple[int, int, int]]] = []
    terminated = [False, False]
    singleton_index = -1
    singleton_original: tuple[int, int, int] | None = None
    try:
        with phase_source_patch(event["variant"]):
            clamp_stored_phase(world, event["variant"])
            for offset in range(branch_offset + 1):
                if offset in {start_offset - 1, start_offset}:
                    snapshots[offset] = clone_world(world, continuation_seed)
                if offset == start_offset:
                    regions, _ = reconstruct_regions(
                        snapshots[start_offset - 1], snapshots[start_offset]
                    )
                if offset == rebridge_offset:
                    lineages = [
                        {coord for coord in region if bool(world.active[coord])}
                        for region in regions
                    ]
                    singleton_index = min(range(2), key=lambda index: len(regions[index]))
                    singleton_original = next(iter(regions[singleton_index]))
                if offset < branch_offset:
                    events: list[dict[str, Any]] = []
                    iota_rig.HARD_TRANSFER_TRACE_HOOK = events.append
                    iota_rig.step(world, cfg)
                    iota_rig.HARD_TRANSFER_TRACE_HOOK = None
                    clamp_stored_phase(world, event["variant"])
                    if lineages and offset >= rebridge_offset:
                        next_lineages, collision, _, _ = advance_lineages(
                            lineages, world, events
                        )
                        if collision:
                            raise RuntimeError("natural source trajectory has lineage collision")
                        for index in range(2):
                            if terminated[index]:
                                next_lineages[index] = set()
                            elif not next_lineages[index]:
                                terminated[index] = True
                        lineages = next_lineages
    finally:
        iota_rig.HARD_TRANSFER_TRACE_HOOK = None
    if singleton_original is None or singleton_index < 0:
        raise RuntimeError("failed to construct singleton source lineage")
    if not bool(world.active[singleton_original]):
        raise RuntimeError("singleton original is not active at preregistered branch state")
    if not lineages[singleton_index]:
        raise RuntimeError("singleton expression lineage is empty at branch state")
    return world, lineages, singleton_index, singleton_original


def run_branch(
    event: dict[str, str],
    branch_offset: int,
    branch_world: World,
    branch_lineages: list[set[tuple[int, int, int]]],
    singleton_index: int,
    singleton_original: tuple[int, int, int],
    branch_sample: int,
    branch_seed: int,
    horizon: int,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    world = clone_world(branch_world, branch_seed)
    lineages = [set(lineage) for lineage in branch_lineages]
    terminated = [False, False]
    collision = False
    payload_zero = True
    ledger_exact = True
    address_loss_relative: int | str = ""
    handoff_success = False
    preexisting_descendant = False
    death_children: list[dict[str, Any]] = []
    expression_survival = 0
    postloss_relation_lifetime = 0
    postloss_relation_terminated = False
    try:
        with phase_source_patch(event["variant"]):
            clamp_stored_phase(world, event["variant"])
            for relative in range(horizon + 1):
                payload_zero = payload_zero and int(np.count_nonzero(world.P)) == 0
                ledger_exact = ledger_exact and ledger_error(world) == 0.0
                if address_loss_relative != "":
                    alive, reachability, _ = lineage_relation(world, lineages)
                    if lineages[singleton_index]:
                        expression_survival += 1
                    if (
                        not postloss_relation_terminated
                        and alive
                        and reachability == 1.0
                        and not collision
                    ):
                        postloss_relation_lifetime += 1
                    else:
                        postloss_relation_terminated = True
                if relative >= horizon:
                    break

                singleton_before = set(lineages[singleton_index])
                events: list[dict[str, Any]] = []
                iota_rig.HARD_TRANSFER_TRACE_HOOK = events.append
                iota_rig.step(world, cfg)
                iota_rig.HARD_TRANSFER_TRACE_HOOK = None
                clamp_stored_phase(world, event["variant"])
                next_lineages, collided, _, inherited = advance_lineages(
                    lineages, world, events
                )
                collision = collision or collided
                for index in range(2):
                    if terminated[index]:
                        next_lineages[index] = set()
                    elif not next_lineages[index]:
                        terminated[index] = True

                if address_loss_relative == "" and not bool(world.active[singleton_original]):
                    address_loss_relative = relative + 1
                    preexisting_descendant = any(
                        coord != singleton_original for coord in singleton_before
                    )
                    death_children = [
                        row
                        for row in inherited
                        if int(row["lineage_index"]) == singleton_index
                    ]
                    handoff_success = bool(next_lineages[singleton_index]) and not collision
                lineages = next_lineages
    finally:
        iota_rig.HARD_TRANSFER_TRACE_HOOK = None

    orders = sorted({int(row["candidate_order"]) for row in death_children})
    depleted = sum(bool(row["target_depleted_before"]) for row in death_children)
    absolute_loss = (
        "" if address_loss_relative == "" else branch_offset + int(address_loss_relative)
    )
    return {
        "init_seed": int(event["init_seed"]),
        "sample_index": int(event["sample_index"]),
        "event_start_offset": int(event["start_offset"]),
        "branch_offset": branch_offset,
        "branch_sample": branch_sample,
        "branch_seed": branch_seed,
        "horizon": horizon,
        "singleton_original": coords_text({singleton_original}),
        "singleton_lineage_size_at_branch": len(branch_lineages[singleton_index]),
        "original_address_loss_offset": absolute_loss,
        "address_loss_observed": csv_bool(address_loss_relative != ""),
        "handoff_success": csv_bool(handoff_success),
        "preexisting_descendant_at_loss": csv_bool(preexisting_descendant),
        "death_tick_child_count": len(death_children),
        "death_tick_children": coords_text({tuple(row["target"]) for row in death_children}),
        "death_tick_candidate_orders": ";".join(str(value) for value in orders),
        "death_tick_depleted_targets": depleted,
        "expression_survival_after_loss": expression_survival,
        "postloss_relation_lifetime": postloss_relation_lifetime,
        "lineage_collision": csv_bool(collision),
        "payload_zero_all_offsets": csv_bool(payload_zero),
        "ledger_exact_all_offsets": csv_bool(ledger_exact),
    }


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    keys = sorted({(int(row["init_seed"]), int(row["event_start_offset"])) for row in rows})
    for seed, start in keys:
        selected = [
            row
            for row in rows
            if int(row["init_seed"]) == seed and int(row["event_start_offset"]) == start
        ]
        deaths = [row for row in selected if int(row["address_loss_observed"]) == 1]
        eligible = [row for row in deaths if int(row["lineage_collision"]) == 0]
        successes = sum(int(row["handoff_success"]) for row in eligible)
        wilson_low, wilson_high = wilson_interval(successes, len(eligible))
        output.append(
            {
                "init_seed": seed,
                "event_start_offset": start,
                "branch_offset": int(selected[0]["branch_offset"]),
                "branches": len(selected),
                "address_loss_branches": len(deaths),
                "censored_branches": len(selected) - len(deaths),
                "ambiguous_collision_branches": sum(
                    int(row["lineage_collision"]) for row in deaths
                ),
                "eligible_address_loss_branches": len(eligible),
                "handoff_successes": successes,
                "handoff_failures": len(eligible) - successes,
                "handoff_rate": successes / len(eligible) if eligible else "",
                "handoff_wilson_low": wilson_low,
                "handoff_wilson_high": wilson_high,
                "mean_time_to_address_loss": (
                    mean(
                        int(row["original_address_loss_offset"])
                        - int(row["branch_offset"])
                        for row in deaths
                    )
                    if deaths
                    else ""
                ),
                "mean_postloss_relation_lifetime": (
                    mean(int(row["postloss_relation_lifetime"]) for row in eligible)
                    if eligible
                    else ""
                ),
                "payload_zero_branches": sum(
                    int(row["payload_zero_all_offsets"]) for row in selected
                ),
                "ledger_exact_branches": sum(
                    int(row["ledger_exact_all_offsets"]) for row in selected
                ),
            }
        )
    return output


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float | str, float | str]:
    if trials <= 0:
        return "", ""
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    center = (proportion + z * z / (2.0 * trials)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1.0 - proportion) / trials
            + z * z / (4.0 * trials * trials)
        )
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    row_one = a + b
    row_two = c + d
    successes = a + c
    total = row_one + row_two

    def probability(value: int) -> float:
        if value < 0 or value > row_one or successes - value < 0 or successes - value > row_two:
            return 0.0
        return (
            math.comb(row_one, value)
            * math.comb(row_two, successes - value)
            / math.comb(total, successes)
        )

    observed = probability(a)
    lower = max(0, successes - row_two)
    upper = min(row_one, successes)
    return min(
        1.0,
        sum(
            probability(value)
            for value in range(lower, upper + 1)
            if probability(value) <= observed + 1e-15
        ),
    )


def compare_sources(aggregate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for left_index in range(len(aggregate_rows)):
        for right_index in range(left_index + 1, len(aggregate_rows)):
            left = aggregate_rows[left_index]
            right = aggregate_rows[right_index]
            left_success = int(left["handoff_successes"])
            left_trials = int(left["eligible_address_loss_branches"])
            right_success = int(right["handoff_successes"])
            right_trials = int(right["eligible_address_loss_branches"])
            left_failure = left_trials - left_success
            right_failure = right_trials - right_success
            odds_ratio: float | str
            if left_failure == 0 or right_success == 0:
                odds_ratio = ""
            elif right_failure == 0 or left_success == 0:
                odds_ratio = 0.0
            else:
                odds_ratio = (left_success * right_failure) / (left_failure * right_success)
            output.append(
                {
                    "left_source": f"seed{left['init_seed']}_event{left['event_start_offset']}",
                    "right_source": f"seed{right['init_seed']}_event{right['event_start_offset']}",
                    "left_successes": left_success,
                    "left_trials": left_trials,
                    "right_successes": right_success,
                    "right_trials": right_trials,
                    "rate_difference_left_minus_right": (
                        left_success / left_trials - right_success / right_trials
                    ),
                    "odds_ratio": odds_ratio,
                    "fisher_exact_two_sided_p": fisher_exact_two_sided(
                        left_success,
                        left_failure,
                        right_success,
                        right_failure,
                    ),
                }
            )
    return output


def main() -> None:
    args = parse_args()
    sources = select_source_events(Path(args.event_csv))
    seeds = sorted({int(event["init_seed"]) for event, _ in sources})
    configs = {
        seed: load_config(discover_config(args.config_dir, seed)) for seed in seeds
    }
    checkpoints: dict[int, World] = {}
    for seed in seeds:
        print(f"checkpoint seed={seed} variant=takeover_only_vector_phase", flush=True)
        checkpoints[seed] = run_to_checkpoint(
            configs[seed], "takeover_only_vector_phase", int(args.checkpoint_tick)
        )

    rows: list[dict[str, Any]] = []
    for source_index, (event, branch_offset) in enumerate(sources):
        seed = int(event["init_seed"])
        branch_world, lineages, singleton_index, singleton_original = build_branch_state(
            event, branch_offset, checkpoints[seed], configs[seed]
        )
        print(
            f"source seed={seed} event={event['start_offset']} branch={branch_offset} "
            f"singleton_lineage={len(lineages[singleton_index])}",
            flush=True,
        )
        for branch_sample in range(int(args.samples)):
            branch_seed = int(args.branch_seed_base) + source_index * 10_000 + branch_sample
            row = run_branch(
                event,
                branch_offset,
                branch_world,
                lineages,
                singleton_index,
                singleton_original,
                branch_sample,
                branch_seed,
                int(args.horizon),
                configs[seed],
            )
            rows.append(row)
        selected = rows[-int(args.samples) :]
        deaths = sum(int(row["address_loss_observed"]) for row in selected)
        successes = sum(int(row["handoff_success"]) for row in selected)
        print(
            f"ensemble seed={seed} event={event['start_offset']} "
            f"deaths={deaths}/{args.samples} handoffs={successes}",
            flush=True,
        )

    aggregate_rows = aggregate(rows)
    comparison_rows = compare_sources(aggregate_rows)
    prefix = Path(args.output_prefix)
    case_path = prefix.with_name(prefix.name + "_cases.csv")
    aggregate_path = prefix.with_name(prefix.name + "_aggregate.csv")
    comparison_path = prefix.with_name(prefix.name + "_comparisons.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(case_path, CASE_FIELDNAMES, rows)
    write_csv(aggregate_path, AGGREGATE_FIELDNAMES, aggregate_rows)
    write_csv(comparison_path, COMPARISON_FIELDNAMES, comparison_rows)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "cases": len(rows),
        "sources": len(sources),
        "samples_per_source": int(args.samples),
        "horizon": int(args.horizon),
        "aggregate": aggregate_rows,
        "comparisons": comparison_rows,
        "all_payload_zero": all(int(row["payload_zero_all_offsets"]) for row in rows),
        "all_ledger_exact": all(int(row["ledger_exact_all_offsets"]) for row in rows),
        "case_csv": str(case_path),
        "aggregate_csv": str(aggregate_path),
        "comparison_csv": str(comparison_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
