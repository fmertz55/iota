from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import numpy as np

import iota_rig
from component_bridge_causal_trace import csv_bool, write_csv
from continuation import clone_world
from expression_handoff_branch_ensemble import build_branch_state, select_source_events
from expression_lineage_transport import advance_lineages, world_equal
from iota_rig import World, load_config
from phase_free_class_matrix import run_to_checkpoint
from phase_free_constraint_transport import ledger_error
from phase_source_minimization_audit import clamp_stored_phase, discover_config, phase_source_patch
from terminal_candidate_ledger import CASE_FIELDS, CANDIDATE_FIELDS, run_case


FAILURE_LABELS = {"gate_failed", "source_exhausted", "target_preempted"}
REPLAY_FIELDS = [
    "init_seed", "event_start_offset", "branch_sample", "branch_seed",
    "finding066_outcome_label", "natural_label",
    "natural_terminal_offset", "selector_event_index", "selector_source", "selector_target",
    "selector_candidate_order", "natural_gate_draw", "natural_transfer_probability",
    "natural_gate_passed", "forced_gate_passed", "sham_exact", "override_matches",
    "capacity_retained_after_intervention", "later_singleton_candidate_evaluated",
    "preempted_target_available_at_singleton_evaluation", "immediate_child_count",
    "route_reopened", "postintervention_address_loss_observed",
    "postintervention_terminal_offset", "address_loss_delay", "eventual_handoff",
    "eventual_death_tick_child_count", "lineage_collision", "payload_zero_all_offsets",
    "ledger_exact_all_offsets",
]
AGGREGATE_FIELDS = [
    "natural_label", "eligible_replays", "route_reopened", "route_rate", "route_ci_low",
    "route_ci_high", "immediate_child", "immediate_child_rate", "immediate_child_ci_low",
    "immediate_child_ci_high", "eventual_handoff", "eventual_handoff_rate",
    "eventual_handoff_ci_low", "eventual_handoff_ci_high", "median_address_loss_delay",
    "class_level_replication_eligible",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prospectively replicate one-decision temporal interventions.")
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--event-csv", default="output/findings/finding060/phase_free_constraint_transport_events.csv")
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--first-sample", type=int, default=96)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--natural-horizon", type=int, default=128)
    parser.add_argument("--replay-horizon", type=int, default=256)
    parser.add_argument("--branch-seed-base", type=int, default=2026071100)
    return parser.parse_args()


def coord(value: str | tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(value, tuple):
        return value
    return tuple(int(part) for part in value.split(":"))  # type: ignore[return-value]


def event_matches(relative: int, row: dict[str, Any], selector: dict[str, Any]) -> bool:
    return (
        relative == int(selector["relative"])
        and tuple(row["source"]) == selector["source"]
        and tuple(row["target"]) == selector["target"]
        and int(row["candidate_order"]) == int(selector["candidate_order"])
    )


def freeze_selector(label: str, case: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    terminal_relative = int(case["terminal_offset"]) - int(case["branch_offset"]) - 1
    singleton = [row for row in rows if int(row["source_in_singleton_lineage"]) == 1]
    selected: dict[str, Any] | None = None
    preempted_target: tuple[int, int, int] | None = None
    if label == "gate_failed":
        matches = [
            row for row in singleton
            if row["status"] == "gate_failed" and row["target_active_at_evaluation"] is False
        ]
        selected = min(matches, key=lambda row: int(row["event_index"])) if matches else None
        forced = True
    elif label == "source_exhausted":
        exhausted_sources = {
            coord(row["source"]) for row in singleton if row["status"] == "source_exhausted"
        }
        matches = [
            row for row in singleton
            if row["status"] == "succeeded"
            and row["target_active_at_evaluation"] is True
            and int(row["available_A_before"]) == 1
            and coord(row["source"]) in exhausted_sources
        ]
        selected = max(matches, key=lambda row: int(row["event_index"])) if matches else None
        forced = False
    elif label == "target_preempted":
        preempted = [
            row for row in singleton
            if row["target_active_at_tick_start"] is False
            and row["target_active_at_evaluation"] is True
        ]
        if preempted:
            first = min(preempted, key=lambda row: int(row["event_index"]))
            preempted_target = coord(first["target"])
            activators = [
                row for row in rows
                if int(row["event_index"]) < int(first["event_index"])
                and coord(row["target"]) == preempted_target
                and row["status"] == "succeeded"
                and row["target_activated"] is True
            ]
            selected = max(activators, key=lambda row: int(row["event_index"])) if activators else None
        forced = False
    else:
        raise ValueError(f"no intervention for {label}")
    if selected is None:
        raise RuntimeError(f"frozen selector could not identify one event for {label} branch {case['branch_seed']}")
    return {
        "label": label,
        "relative": terminal_relative,
        "event_index": int(selected["event_index"]),
        "source": coord(selected["source"]),
        "target": coord(selected["target"]),
        "candidate_order": int(selected["candidate_order"]),
        "gate_draw": float(selected["gate_draw"]),
        "transfer_probability": float(selected["transfer_probability"]),
        "natural_gate_passed": selected["status"] == "succeeded",
        "forced_gate_passed": forced,
        "preempted_target": preempted_target,
    }


def causal_label(rows: list[dict[str, Any]]) -> str | None:
    singleton = [row for row in rows if int(row["source_in_singleton_lineage"]) == 1]
    if any(
        row["target_active_at_tick_start"] is False
        and row["target_active_at_evaluation"] is True
        for row in singleton
    ):
        return "target_preempted"
    if any(
        row["status"] == "gate_failed" and row["target_active_at_evaluation"] is False
        for row in singleton
    ):
        return "gate_failed"
    exhausted_sources = {
        coord(row["source"]) for row in singleton if row["status"] == "source_exhausted"
    }
    if any(
        row["status"] == "succeeded"
        and row["target_active_at_evaluation"] is True
        and int(row["available_A_before"]) == 1
        and coord(row["source"]) in exhausted_sources
        for row in singleton
    ):
        return "source_exhausted"
    return None


def verify_sham(base: World, event: dict[str, str], cfg: dict[str, Any], branch_seed: int,
                selector: dict[str, Any]) -> int:
    control = clone_world(base, branch_seed)
    sham = clone_world(base, branch_seed)
    matches = 0

    def callback(relative: int, row: dict[str, Any]) -> bool | None:
        nonlocal matches
        if event_matches(relative, row, selector):
            matches += 1
            return bool(row["natural_gate_passed"])
        return None

    try:
        with phase_source_patch(event["variant"]):
            clamp_stored_phase(control, event["variant"])
            clamp_stored_phase(sham, event["variant"])
            for relative in range(int(selector["relative"]) + 1):
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
                iota_rig.step(control, cfg)
                clamp_stored_phase(control, event["variant"])
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = lambda row, r=relative: callback(r, row)
                iota_rig.step(sham, cfg)
                clamp_stored_phase(sham, event["variant"])
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
                if not world_equal(control, sham):
                    raise RuntimeError("matched sham changed world state or RNG")
    finally:
        iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
    if matches != 1:
        raise RuntimeError(f"matched sham expected one selector match, observed {matches}")
    return matches


def run_intervention(event: dict[str, str], branch_offset: int, base: World,
                     base_lineages: list[set[tuple[int, int, int]]], singleton_index: int,
                     original: tuple[int, int, int], branch_seed: int, selector: dict[str, Any],
                     horizon: int, cfg: dict[str, Any]) -> dict[str, Any]:
    world = clone_world(base, branch_seed)
    lineages = [set(value) for value in base_lineages]
    terminated = [False, False]
    collision = False
    payload_zero = True
    exact = True
    override_matches = 0
    mediator: dict[str, Any] | None = None
    death: dict[str, Any] | None = None

    def override(relative: int, row: dict[str, Any]) -> bool | None:
        nonlocal override_matches
        if event_matches(relative, row, selector):
            override_matches += 1
            return bool(selector["forced_gate_passed"])
        return None

    try:
        with phase_source_patch(event["variant"]):
            clamp_stored_phase(world, event["variant"])
            for relative in range(horizon):
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                before = set(lineages[singleton_index])
                transfers: list[dict[str, Any]] = []
                candidates: list[dict[str, Any]] = []
                iota_rig.HARD_TRANSFER_TRACE_HOOK = transfers.append
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = candidates.append
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = lambda row, r=relative: override(r, row)
                iota_rig.step(world, cfg)
                iota_rig.HARD_TRANSFER_TRACE_HOOK = None
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
                clamp_stored_phase(world, event["variant"])
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                next_lineages, collided, _, inherited = advance_lineages(lineages, world, transfers)
                collision |= collided
                for index in range(2):
                    if terminated[index]:
                        next_lineages[index] = set()
                    elif not next_lineages[index]:
                        terminated[index] = True

                if relative == int(selector["relative"]):
                    singleton_rows = [row for row in candidates if tuple(row["source"]) in before]
                    selector_positions = [
                        index for index, row in enumerate(candidates)
                        if event_matches(relative, row, selector)
                    ]
                    position = selector_positions[0] if selector_positions else -1
                    later_evaluated = any(
                        index > position and tuple(row["source"]) in before
                        and row["status"] != "source_exhausted"
                        for index, row in enumerate(candidates)
                    )
                    preempted_available = False
                    if selector["preempted_target"] is not None:
                        target_rows = [
                            row for row in singleton_rows
                            if tuple(row["target"]) == selector["preempted_target"]
                        ]
                        preempted_available = bool(target_rows) and not bool(
                            target_rows[0]["target_active_at_evaluation"]
                        )
                    child_count = sum(
                        int(row["lineage_index"]) == singleton_index for row in inherited
                    )
                    capacity = bool(world.active[original]) and int(world.A[original]) > 0
                    if selector["label"] == "gate_failed":
                        route = child_count > 0
                    elif selector["label"] == "source_exhausted":
                        route = child_count > 0 or (capacity and later_evaluated)
                    else:
                        route = preempted_available
                    mediator = {
                        "capacity_retained": capacity,
                        "later_candidate_evaluated": later_evaluated,
                        "preempted_target_available": preempted_available,
                        "immediate_child_count": child_count,
                        "route_reopened": route,
                    }

                if not bool(world.active[original]):
                    death_children = [
                        row for row in inherited if int(row["lineage_index"]) == singleton_index
                    ]
                    death = {
                        "observed": True,
                        "terminal_offset": branch_offset + relative + 1,
                        "handoff": bool(next_lineages[singleton_index]) and not collision,
                        "death_tick_child_count": len(death_children),
                    }
                    break
                lineages = next_lineages
    finally:
        iota_rig.HARD_TRANSFER_TRACE_HOOK = None
        iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
        iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
    if override_matches != 1 or mediator is None:
        raise RuntimeError(f"intervention integrity failure: matches={override_matches} mediator={mediator}")
    if death is None:
        death = {"observed": False, "terminal_offset": "", "handoff": False, "death_tick_child_count": 0}
    return {
        **mediator, **death, "override_matches": override_matches, "collision": collision,
        "payload_zero": payload_zero, "ledger_exact": exact,
    }


def binomial_interval(successes: int, trials: int, alpha: float = 0.05) -> tuple[float | str, float | str]:
    if trials <= 0:
        return "", ""
    if successes == 0:
        low = 0.0
    else:
        def upper_tail(p: float) -> float:
            return sum(math.comb(trials, k) * p**k * (1-p)**(trials-k) for k in range(successes, trials+1))
        lo, hi = 0.0, successes / trials
        for _ in range(80):
            mid = (lo + hi) / 2
            if upper_tail(mid) < alpha / 2:
                lo = mid
            else:
                hi = mid
        low = hi
    if successes == trials:
        high = 1.0
    else:
        def lower_tail(p: float) -> float:
            return sum(math.comb(trials, k) * p**k * (1-p)**(trials-k) for k in range(0, successes+1))
        lo, hi = successes / trials, 1.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if lower_tail(mid) > alpha / 2:
                lo = mid
            else:
                hi = mid
        high = lo
    return low, high


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for label in sorted(FAILURE_LABELS):
        selected = [row for row in rows if row["natural_label"] == label]
        n = len(selected)
        values = {}
        for key in ("route_reopened", "immediate_child_count", "eventual_handoff"):
            count = sum((int(row[key]) > 0) for row in selected)
            low, high = binomial_interval(count, n)
            values[key] = (count, count / n if n else "", low, high)
        delays = sorted(int(row["address_loss_delay"]) for row in selected if row["address_loss_delay"] != "")
        median = "" if not delays else (delays[len(delays)//2] if len(delays)%2 else (delays[len(delays)//2-1]+delays[len(delays)//2])/2)
        output.append({
            "natural_label": label, "eligible_replays": n,
            "route_reopened": values["route_reopened"][0], "route_rate": values["route_reopened"][1],
            "route_ci_low": values["route_reopened"][2], "route_ci_high": values["route_reopened"][3],
            "immediate_child": values["immediate_child_count"][0],
            "immediate_child_rate": values["immediate_child_count"][1],
            "immediate_child_ci_low": values["immediate_child_count"][2],
            "immediate_child_ci_high": values["immediate_child_count"][3],
            "eventual_handoff": values["eventual_handoff"][0],
            "eventual_handoff_rate": values["eventual_handoff"][1],
            "eventual_handoff_ci_low": values["eventual_handoff"][2],
            "eventual_handoff_ci_high": values["eventual_handoff"][3],
            "median_address_loss_delay": median,
            "class_level_replication_eligible": csv_bool(n >= 5),
        })
    return output


def main() -> None:
    args = parse_args()
    if (args.first_sample, args.samples) != (96, 64):
        raise ValueError("Finding 067 preregistration requires samples 96..159")
    sources = select_source_events(Path(args.event_csv))
    seeds = sorted({int(event["init_seed"]) for event, _ in sources})
    configs = {seed: load_config(discover_config(args.config_dir, seed)) for seed in seeds}
    checkpoints = {
        seed: run_to_checkpoint(configs[seed], "takeover_only_vector_phase", args.checkpoint_tick)
        for seed in seeds
    }
    natural_cases: list[dict[str, Any]] = []
    natural_candidates: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    for source_index, (event, branch_offset) in enumerate(sources):
        seed = int(event["init_seed"])
        base = build_branch_state(event, branch_offset, checkpoints[seed], configs[seed])
        for sample in range(args.first_sample, args.first_sample + args.samples):
            branch_seed = args.branch_seed_base + source_index * 10_000 + sample
            case, candidates = run_case(
                event, branch_offset, *base, sample, branch_seed, args.natural_horizon, configs[seed]
            )
            natural_cases.append(case)
            natural_candidates.extend(candidates)
            finding066_label = str(case["outcome_class"])
            if finding066_label not in FAILURE_LABELS:
                continue
            label = causal_label(candidates)
            if label is None:
                raise RuntimeError(
                    f"no frozen causal cohort for death branch {case['branch_seed']} "
                    f"with Finding 066 label {finding066_label}"
                )
            selector = freeze_selector(label, case, candidates)
            verify_sham(base[0], event, configs[seed], branch_seed, selector)
            replay = run_intervention(
                event, branch_offset, *base, branch_seed, selector, args.replay_horizon, configs[seed]
            )
            terminal = replay["terminal_offset"]
            delay = "" if terminal == "" else int(terminal) - int(case["terminal_offset"])
            replay_rows.append({
                "init_seed": seed, "event_start_offset": int(event["start_offset"]),
                "branch_sample": sample, "branch_seed": branch_seed,
                "finding066_outcome_label": finding066_label, "natural_label": label,
                "natural_terminal_offset": int(case["terminal_offset"]),
                "selector_event_index": selector["event_index"],
                "selector_source": ":".join(map(str, selector["source"])),
                "selector_target": ":".join(map(str, selector["target"])),
                "selector_candidate_order": selector["candidate_order"],
                "natural_gate_draw": selector["gate_draw"],
                "natural_transfer_probability": selector["transfer_probability"],
                "natural_gate_passed": csv_bool(selector["natural_gate_passed"]),
                "forced_gate_passed": csv_bool(selector["forced_gate_passed"]),
                "sham_exact": 1, "override_matches": replay["override_matches"],
                "capacity_retained_after_intervention": csv_bool(replay["capacity_retained"]),
                "later_singleton_candidate_evaluated": csv_bool(replay["later_candidate_evaluated"]),
                "preempted_target_available_at_singleton_evaluation": csv_bool(replay["preempted_target_available"]),
                "immediate_child_count": replay["immediate_child_count"],
                "route_reopened": csv_bool(replay["route_reopened"]),
                "postintervention_address_loss_observed": csv_bool(replay["observed"]),
                "postintervention_terminal_offset": terminal, "address_loss_delay": delay,
                "eventual_handoff": csv_bool(replay["handoff"]),
                "eventual_death_tick_child_count": replay["death_tick_child_count"],
                "lineage_collision": csv_bool(replay["collision"]),
                "payload_zero_all_offsets": csv_bool(replay["payload_zero"]),
                "ledger_exact_all_offsets": csv_bool(replay["ledger_exact"]),
            })
        print(f"replication seed={seed} event={event['start_offset']} baselines={args.samples}", flush=True)

    aggregate_rows = aggregate(replay_rows)
    prefix = Path(args.output_prefix)
    cases_path = prefix.with_name(prefix.name + "_natural_cases.csv")
    candidates_path = prefix.with_name(prefix.name + "_natural_candidates.csv")
    replay_path = prefix.with_name(prefix.name + "_replays.csv")
    aggregate_path = prefix.with_name(prefix.name + "_aggregate.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(cases_path, CASE_FIELDS, natural_cases)
    write_csv(candidates_path, CANDIDATE_FIELDS, natural_candidates)
    write_csv(replay_path, REPLAY_FIELDS, replay_rows)
    write_csv(aggregate_path, AGGREGATE_FIELDS, aggregate_rows)
    summary = {
        "natural_branches": len(natural_cases),
        "natural_outcome_labels": dict(sorted(Counter(row["outcome_class"] for row in natural_cases).items())),
        "eligible_replays": len(replay_rows), "aggregate": aggregate_rows,
        "all_shams_exact": all(int(row["sham_exact"]) for row in replay_rows),
        "all_natural_payload_zero": all(int(row["payload_zero_all_offsets"]) for row in natural_cases),
        "all_natural_ledger_exact": all(int(row["ledger_exact_all_offsets"]) for row in natural_cases),
        "natural_collision_cases": sum(int(row["lineage_collision"]) for row in natural_cases),
        "all_exactly_one_override": all(int(row["override_matches"]) == 1 for row in replay_rows),
        "all_payload_zero": all(int(row["payload_zero_all_offsets"]) for row in replay_rows),
        "all_ledger_exact": all(int(row["ledger_exact_all_offsets"]) for row in replay_rows),
        "collision_replays": sum(int(row["lineage_collision"]) for row in replay_rows),
        "natural_cases_csv": str(cases_path), "natural_candidates_csv": str(candidates_path),
        "replays_csv": str(replay_path), "aggregate_csv": str(aggregate_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
