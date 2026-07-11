from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

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


CASE_FIELDS = [
    "init_seed", "event_start_offset", "branch_offset", "branch_sample", "branch_seed",
    "terminal_offset", "singleton_lineage_size", "preexisting_descendant", "handoff_success",
    "death_tick_child_count", "candidate_events", "singleton_candidate_events",
    "outcome_class", "lineage_collision", "payload_zero_all_offsets", "ledger_exact_all_offsets",
]
CANDIDATE_FIELDS = [
    "init_seed", "event_start_offset", "branch_sample", "branch_seed", "terminal_offset",
    "event_index", "source_in_singleton_lineage", "source", "target", "candidate_order",
    "candidate_step", "available_A_before", "target_active_at_tick_start",
    "target_active_at_evaluation", "target_depleted_at_evaluation",
    "target_latent_at_evaluation", "influence", "residual_bias_multiplier",
    "transfer_probability", "gate_draw", "target_activated", "status",
    "natural_gate_passed", "effective_gate_passed", "gate_overridden",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Account for singleton death-tick continuation from the ordered transfer ledger.")
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--event-csv", default="output/findings/finding060/phase_free_constraint_transport_events.csv")
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--first-sample", type=int, default=64)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--horizon", type=int, default=128)
    parser.add_argument("--branch-seed-base", type=int, default=2026071100)
    return parser.parse_args()


def verify_candidate_hook(world: World, cfg: dict[str, Any], variant: str, seed: int, horizon: int = 32) -> int:
    control = clone_world(world, seed)
    observed = clone_world(world, seed)
    recorded: list[dict[str, Any]] = []
    try:
        with phase_source_patch(variant):
            clamp_stored_phase(control, variant)
            clamp_stored_phase(observed, variant)
            for _ in range(horizon):
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
                iota_rig.step(control, cfg)
                clamp_stored_phase(control, variant)
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = recorded.append
                iota_rig.step(observed, cfg)
                clamp_stored_phase(observed, variant)
                if not world_equal(control, observed):
                    raise RuntimeError("candidate ledger changed simulation state or RNG")
    finally:
        iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
        iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
    return len(recorded)


def classify(preexisting: bool, handoff: bool, collision: bool, rows: list[dict[str, Any]]) -> str:
    if collision:
        return "ambiguous_collision"
    if preexisting:
        return "preexisting_descendant"
    if handoff:
        return "activated_child"
    if any(r.get("target_active_at_tick_start") is False and r.get("target_active_at_evaluation") is True for r in rows):
        return "target_preempted"
    if any(r.get("status") == "gate_failed" for r in rows):
        return "gate_failed"
    if any(r.get("status") == "source_exhausted" for r in rows):
        return "source_exhausted"
    return "no_eligible_successor"


def run_case(event: dict[str, str], branch_offset: int, base_world: World,
             base_lineages: list[set[tuple[int, int, int]]], singleton_index: int,
             original: tuple[int, int, int], sample: int, branch_seed: int,
             horizon: int, cfg: dict[str, Any], gate_override: Any = None,
             allow_censored: bool = False) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    world = clone_world(base_world, branch_seed)
    lineages = [set(x) for x in base_lineages]
    terminated = [False, False]
    collision = False
    payload_zero = True
    exact = True
    terminal_rows: list[dict[str, Any]] = []
    case: dict[str, Any] | None = None
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
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = (
                    None if gate_override is None else lambda row: gate_override(relative, row)
                )
                iota_rig.step(world, cfg)
                iota_rig.HARD_TRANSFER_TRACE_HOOK = None
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
                clamp_stored_phase(world, event["variant"])
                payload_zero = payload_zero and int(np.count_nonzero(world.P)) == 0
                exact = exact and ledger_error(world) == 0.0
                next_lineages, collided, _, inherited = advance_lineages(lineages, world, transfers)
                collision |= collided
                for index in range(2):
                    if terminated[index]:
                        next_lineages[index] = set()
                    elif not next_lineages[index]:
                        terminated[index] = True
                if not bool(world.active[original]):
                    children = [x for x in inherited if int(x["lineage_index"]) == singleton_index]
                    preexisting = any(x != original for x in before)
                    handoff = bool(next_lineages[singleton_index]) and not collision
                    for index, row in enumerate(candidates):
                        normalized = {key: row.get(key, "") for key in CANDIDATE_FIELDS}
                        normalized.update({
                            "init_seed": int(event["init_seed"]), "event_start_offset": int(event["start_offset"]),
                            "branch_sample": sample, "branch_seed": branch_seed,
                            "terminal_offset": branch_offset + relative + 1, "event_index": index,
                            "source_in_singleton_lineage": csv_bool(tuple(row["source"]) in before),
                            "source": ":".join(map(str, row["source"])),
                            "target": ":".join(map(str, row["target"])),
                            "candidate_step": ":".join(map(str, row.get("candidate_step", ()))),
                        })
                        terminal_rows.append(normalized)
                    singleton_rows = [r for r in candidates if tuple(r["source"]) in before]
                    case = {
                        "init_seed": int(event["init_seed"]), "event_start_offset": int(event["start_offset"]),
                        "branch_offset": branch_offset, "branch_sample": sample, "branch_seed": branch_seed,
                        "terminal_offset": branch_offset + relative + 1, "singleton_lineage_size": len(before),
                        "preexisting_descendant": csv_bool(preexisting), "handoff_success": csv_bool(handoff),
                        "death_tick_child_count": len(children), "candidate_events": len(candidates),
                        "singleton_candidate_events": len(singleton_rows),
                        "outcome_class": classify(preexisting, handoff, collision, singleton_rows),
                        "lineage_collision": csv_bool(collision), "payload_zero_all_offsets": csv_bool(payload_zero),
                        "ledger_exact_all_offsets": csv_bool(exact),
                    }
                    break
                lineages = next_lineages
    finally:
        iota_rig.HARD_TRANSFER_TRACE_HOOK = None
        iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
        iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
    if case is None and allow_censored:
        case = {
            "init_seed": int(event["init_seed"]), "event_start_offset": int(event["start_offset"]),
            "branch_offset": branch_offset, "branch_sample": sample, "branch_seed": branch_seed,
            "terminal_offset": "", "singleton_lineage_size": len(lineages[singleton_index]),
            "preexisting_descendant": "", "handoff_success": 0, "death_tick_child_count": 0,
            "candidate_events": 0, "singleton_candidate_events": 0,
            "outcome_class": "censored", "lineage_collision": csv_bool(collision),
            "payload_zero_all_offsets": csv_bool(payload_zero),
            "ledger_exact_all_offsets": csv_bool(exact),
        }
    if case is None:
        raise RuntimeError(f"terminal address loss not observed for branch {branch_seed}")
    return case, terminal_rows


def main() -> None:
    args = parse_args()
    if (args.first_sample, args.samples) != (64, 32):
        raise ValueError("Finding 066 preregistration requires fresh samples 64..95")
    sources = select_source_events(Path(args.event_csv))
    seeds = sorted({int(e["init_seed"]) for e, _ in sources})
    configs = {s: load_config(discover_config(args.config_dir, s)) for s in seeds}
    checkpoints = {s: run_to_checkpoint(configs[s], "takeover_only_vector_phase", args.checkpoint_tick) for s in seeds}
    cases: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    equivalence_events = 0
    for source_index, (event, branch_offset) in enumerate(sources):
        seed = int(event["init_seed"])
        base = build_branch_state(event, branch_offset, checkpoints[seed], configs[seed])
        equivalence_events += verify_candidate_hook(base[0], configs[seed], event["variant"], 990000 + source_index)
        for sample in range(args.first_sample, args.first_sample + args.samples):
            branch_seed = args.branch_seed_base + source_index * 10_000 + sample
            case, rows = run_case(event, branch_offset, *base, sample, branch_seed, args.horizon, configs[seed])
            cases.append(case)
            ledger.extend(rows)
        print(f"ledger seed={seed} event={event['start_offset']} rows={args.samples}", flush=True)
    prefix = Path(args.output_prefix)
    cases_path = prefix.with_name(prefix.name + "_cases.csv")
    ledger_path = prefix.with_name(prefix.name + "_candidates.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(cases_path, CASE_FIELDS, cases)
    write_csv(ledger_path, CANDIDATE_FIELDS, ledger)
    classes = Counter(row["outcome_class"] for row in cases)
    summary = {
        "branches": len(cases), "candidate_events": len(ledger), "equivalence_gate_events_observed": equivalence_events,
        "equivalence_gate_passed": True, "outcome_classes": dict(sorted(classes.items())),
        "handoff_successes": sum(int(r["handoff_success"]) for r in cases),
        "all_cases_accounted": sum(classes.values()) == len(cases),
        "all_payload_zero": all(int(r["payload_zero_all_offsets"]) for r in cases),
        "all_ledger_exact": all(int(r["ledger_exact_all_offsets"]) for r in cases),
        "collision_cases": sum(int(r["lineage_collision"]) for r in cases),
        "cases_csv": str(cases_path), "candidates_csv": str(ledger_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
