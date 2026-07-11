from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import write_csv
from continuation import clone_world
from expression_handoff_branch_ensemble import build_branch_state, select_source_events
from expression_lineage_transport import advance_lineages
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG, config_for_seed
from iota_rig import World, load_config
from phase_free_class_matrix import run_to_checkpoint
from phase_free_constraint_transport import ledger_error
from phase_source_minimization_audit import clamp_stored_phase, discover_config, phase_source_patch
from temporal_gate_replication import binomial_interval, event_matches, verify_sham
from terminal_candidate_ledger import CASE_FIELDS, CANDIDATE_FIELDS, run_case


ORIGINAL_SAMPLES = tuple(range(160, 224))
INDEPENDENT_SAMPLES = tuple(range(32, 64))
ORIGINAL_HORIZON = 128
INDEPENDENT_HORIZON = 256
POST_INTERVENTION_HORIZON = 128
ORIGINAL_BRANCH_SEED_BASE = 2_026_071_100
INDEPENDENT_BRANCH_SEED_BASE = 2_026_071_300
FROZEN_MANIFEST_SHA256 = "15ed649a3db93492e1b2cbe4ea72261c10717cf2cdb6a07f6df6eb25b59d717e"

NATURAL_FIELDS = ["cohort", "source_id", *CASE_FIELDS]
CANDIDATE_OUTPUT_FIELDS = ["cohort", "source_id", *CANDIDATE_FIELDS]
SELECTOR_FIELDS = [
    "selection_rule_version", "cohort", "source_id", "init_seed", "event_start_offset",
    "branch_offset", "branch_sample", "branch_seed", "natural_terminal_offset",
    "terminal_relative", "event_index", "gate_ordinal", "source", "target",
    "candidate_order", "candidate_step", "available_A_before",
    "target_active_at_tick_start", "target_active_at_evaluation",
    "target_depleted_at_evaluation", "target_latent_at_evaluation", "influence",
    "residual_bias_multiplier", "transfer_probability", "gate_draw",
    "natural_gate_passed", "target_activated", "natural_child_multiplicity",
    "inheritance_join_verified", "payload_zero", "ledger_exact", "lineage_collision",
]
REPLAY_FIELDS = [
    "cohort", "source_id", "init_seed", "event_start_offset", "branch_sample",
    "branch_seed", "natural_terminal_offset", "selector_event_index", "selector_source",
    "selector_target", "selector_candidate_order", "natural_gate_draw",
    "natural_transfer_probability", "sham_exact", "override_matches",
    "sham_steps_compared", "world_and_rng_exact", "selector_identity_exact",
    "targeted_event_suppressed",
    "source_capacity_retained_after_veto",
    "immediate_alternate_child_count", "immediate_alternate_child_targets",
    "first_alternate_child_delay", "first_alternate_child_target",
    "selected_target_later_inherited", "postveto_address_loss_observed",
    "postveto_terminal_offset", "address_loss_delay", "eventual_handoff",
    "alternate_child_timing", "address_endpoint", "lineage_collision",
    "payload_zero_all_offsets",
    "ledger_exact_all_offsets",
]
AGGREGATE_FIELDS = [
    "cohort", "source_id", "init_seed", "event_start_offset", "natural_branches",
    "eligible_vetoes", "targeted_events_suppressed", "same_tick_redundancy",
    "delayed_redundancy", "no_alternate_child", "lineage_loss_at_address_death",
    "source_survival_censored",
    "eventual_handoffs", "eventual_handoff_rate", "eventual_handoff_ci_low",
    "eventual_handoff_ci_high", "median_address_loss_delay",
    "class_level_replication_eligible",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prospectively veto the first natural child realization.")
    parser.add_argument("--output-prefix", type=Path, default=Path("output/findings/finding068/realization_necessity"))
    parser.add_argument("--event-csv", type=Path, default=Path("output/findings/finding060/phase_free_constraint_transport_events.csv"))
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--source-manifest", type=Path, default=Path("output/findings/finding067/independent_geometry_screen_source_manifest.csv"))
    parser.add_argument("--transport-csv", type=Path, default=Path("output/findings/finding067/independent_geometry_screen_transport_events.csv"))
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def coord(value: str | tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(value, tuple):
        return value
    return tuple(int(part) for part in value.split(":"))  # type: ignore[return-value]


def text_coord(value: tuple[int, int, int] | None) -> str:
    return "" if value is None else ":".join(str(part) for part in value)


def freeze_child_selector(case: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    if case["outcome_class"] != "activated_child" or int(case["singleton_lineage_size"]) != 1:
        raise ValueError("necessity selector requires a natural single-address activated-child case")
    matches = [
        row for row in rows
        if int(row["source_in_singleton_lineage"]) == 1
        and row["status"] == "succeeded"
        and row["target_activated"] is True
        and row["target_active_at_evaluation"] is False
    ]
    if not matches:
        raise RuntimeError(f"natural child case {case['branch_seed']} has no child-producing candidate")
    selected = min(matches, key=lambda row: int(row["event_index"]))
    gated = [row for row in rows if row["status"] in {"succeeded", "gate_failed"}]
    gate_ordinal = next(
        index for index, row in enumerate(gated)
        if int(row["event_index"]) == int(selected["event_index"])
    )
    if len(matches) != int(case["death_tick_child_count"]):
        raise RuntimeError("candidate/inherited child multiplicity mismatch")
    return {
        "relative": int(case["terminal_offset"]) - int(case["branch_offset"]) - 1,
        "event_index": int(selected["event_index"]),
        "gate_ordinal": gate_ordinal,
        "source": coord(selected["source"]),
        "target": coord(selected["target"]),
        "candidate_order": int(selected["candidate_order"]),
        "candidate_step": coord(selected["candidate_step"]),
        "available_A_before": int(selected["available_A_before"]),
        "target_active_at_tick_start": bool(selected["target_active_at_tick_start"]),
        "target_active_at_evaluation": bool(selected["target_active_at_evaluation"]),
        "target_depleted_at_evaluation": bool(selected["target_depleted_at_evaluation"]),
        "target_latent_at_evaluation": bool(selected["target_latent_at_evaluation"]),
        "influence": float(selected["influence"]),
        "residual_bias_multiplier": float(selected["residual_bias_multiplier"]),
        "gate_draw": float(selected["gate_draw"]),
        "transfer_probability": float(selected["transfer_probability"]),
        "natural_gate_passed": True,
        "forced_gate_passed": False,
        "natural_child_multiplicity": len(matches),
        "inheritance_join_verified": True,
    }


def run_veto(
    event: dict[str, str],
    branch_offset: int,
    base: World,
    base_lineages: list[set[tuple[int, int, int]]],
    singleton_index: int,
    original: tuple[int, int, int],
    branch_seed: int,
    selector: dict[str, Any],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    world = clone_world(base, branch_seed)
    lineages = [set(value) for value in base_lineages]
    terminated = [False, False]
    collision = False
    payload_zero = True
    exact = True
    override_matches = 0
    gate_ordinals: dict[int, int] = {}
    selector_identity_exact = False
    intervention: dict[str, Any] | None = None
    first_alternate_delay: int | str = ""
    first_alternate_target: tuple[int, int, int] | None = None
    selected_target_later_inherited = False
    death: dict[str, Any] | None = None
    final_relative = int(selector["relative"]) + POST_INTERVENTION_HORIZON

    def override(relative: int, row: dict[str, Any]) -> bool | None:
        nonlocal override_matches, selector_identity_exact
        gate_ordinal = gate_ordinals.get(relative, 0)
        gate_ordinals[relative] = gate_ordinal + 1
        if relative == int(selector["relative"]) and gate_ordinal == int(selector["gate_ordinal"]):
            if not event_matches(relative, row, selector):
                raise RuntimeError("frozen gate ordinal no longer identifies the selected event")
            checks = {
                "candidate_step": tuple(row["candidate_step"]) == tuple(selector["candidate_step"]),
                "available_A_before": int(row["available_A_before"]) == int(selector["available_A_before"]),
                "target_active_at_tick_start": bool(row["target_active_at_tick_start"]) == bool(selector["target_active_at_tick_start"]),
                "target_active_at_evaluation": bool(row["target_active_at_evaluation"]) == bool(selector["target_active_at_evaluation"]),
                "transfer_probability": float(row["transfer_probability"]) == float(selector["transfer_probability"]),
                "gate_draw": float(row["gate_draw"]) == float(selector["gate_draw"]),
                "natural_gate_passed": bool(row["natural_gate_passed"]) is True,
            }
            if not all(checks.values()):
                raise RuntimeError(f"frozen selector identity changed: {checks}")
            selector_identity_exact = True
            override_matches += 1
            return False
        return None

    try:
        with phase_source_patch(event["variant"]):
            clamp_stored_phase(world, event["variant"])
            for relative in range(final_relative + 1):
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

                alternate_children = [
                    row for row in inherited if int(row["lineage_index"]) == singleton_index
                ]
                if relative >= int(selector["relative"]) and alternate_children and first_alternate_target is None:
                    first = alternate_children[0]
                    first_alternate_delay = relative - int(selector["relative"])
                    first_alternate_target = tuple(first["target"])
                if relative > int(selector["relative"]):
                    selected_target_later_inherited |= any(
                        tuple(row["target"]) == selector["target"] for row in alternate_children
                    )

                if relative == int(selector["relative"]):
                    selected_rows = [row for row in candidates if event_matches(relative, row, selector)]
                    suppressed = (
                        len(selected_rows) == 1
                        and selected_rows[0]["status"] == "gate_failed"
                        and selected_rows[0].get("gate_overridden") is True
                        and selected_rows[0].get("effective_gate_passed") is False
                    )
                    intervention = {
                        "targeted_event_suppressed": suppressed,
                        "source_capacity_retained": (
                            bool(world.active[original]) and int(world.A[original]) > 0
                        ),
                        "immediate_children": alternate_children,
                        "candidate_rows": candidates,
                    }

                if not bool(world.active[original]):
                    handoff = bool(next_lineages[singleton_index]) and not collision
                    death = {
                        "observed": True,
                        "terminal_offset": branch_offset + relative + 1,
                        "handoff": handoff,
                    }
                    break
                lineages = next_lineages
    finally:
        iota_rig.HARD_TRANSFER_TRACE_HOOK = None
        iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
        iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None

    if override_matches != 1 or intervention is None or not selector_identity_exact:
        raise RuntimeError(f"necessity intervention integrity failure matches={override_matches}")
    if death is None:
        death = {"observed": False, "terminal_offset": "", "handoff": False}
    immediate = intervention["immediate_children"]
    if first_alternate_delay == 0:
        alternate_timing = "same_tick"
    elif first_alternate_delay != "":
        alternate_timing = "delayed"
    else:
        alternate_timing = "none"
    if death["observed"] and death["handoff"]:
        address_endpoint = "handoff_at_first_address_loss"
    elif death["observed"]:
        address_endpoint = "lineage_loss_at_first_address_loss"
    else:
        address_endpoint = "source_survival_censored"
    return {
        **intervention,
        **death,
        "override_matches": override_matches,
        "first_alternate_child_delay": first_alternate_delay,
        "first_alternate_child_target": first_alternate_target,
        "selected_target_later_inherited": selected_target_later_inherited,
        "selector_identity_exact": selector_identity_exact,
        "alternate_child_timing": alternate_timing,
        "address_endpoint": address_endpoint,
        "collision": collision,
        "payload_zero": payload_zero,
        "ledger_exact": exact,
    }


def independent_sources(args: argparse.Namespace) -> list[tuple[dict[str, str], dict[str, str]]]:
    if file_sha256(args.source_manifest) != FROZEN_MANIFEST_SHA256:
        raise RuntimeError("Finding 068 independent source manifest changed")
    selected = [
        row for row in read_csv(args.source_manifest) if int(row["frozen_source_selected"]) == 1
    ]
    transports = read_csv(args.transport_csv)
    output: list[tuple[dict[str, str], dict[str, str]]] = []
    for source in selected:
        matches = [
            event for event in transports
            if int(event["init_seed"]) == int(source["init_seed"])
            and int(event["sample_index"]) == int(source["sample_index"])
            and int(event["start_offset"]) == int(source["start_offset"])
            and int(event["rebridge_offset"]) == int(source["rebridge_offset"])
        ]
        if len(matches) != 1:
            raise RuntimeError(f"missing frozen event for {source['source_id']}")
        output.append((source, matches[0]))
    return output


def aggregate_rows(
    natural: list[dict[str, Any]], replays: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    keys = sorted({(row["cohort"], row["source_id"]) for row in natural})
    output: list[dict[str, Any]] = []
    for cohort, source_id in keys:
        source_natural = [row for row in natural if row["cohort"] == cohort and row["source_id"] == source_id]
        selected = [row for row in replays if row["cohort"] == cohort and row["source_id"] == source_id]
        timing = Counter(row["alternate_child_timing"] for row in selected)
        endpoints = Counter(row["address_endpoint"] for row in selected)
        handoffs = sum(int(row["eventual_handoff"]) for row in selected)
        low, high = binomial_interval(handoffs, len(selected))
        delays = [int(row["address_loss_delay"]) for row in selected if row["address_loss_delay"] != ""]
        output.append({
            "cohort": cohort, "source_id": source_id,
            "init_seed": int(source_natural[0]["init_seed"]),
            "event_start_offset": int(source_natural[0]["event_start_offset"]),
            "natural_branches": len(source_natural), "eligible_vetoes": len(selected),
            "targeted_events_suppressed": sum(int(row["targeted_event_suppressed"]) for row in selected),
            "same_tick_redundancy": timing["same_tick"],
            "delayed_redundancy": timing["delayed"],
            "no_alternate_child": timing["none"],
            "lineage_loss_at_address_death": endpoints["lineage_loss_at_first_address_loss"],
            "source_survival_censored": endpoints["source_survival_censored"],
            "eventual_handoffs": handoffs,
            "eventual_handoff_rate": handoffs / len(selected) if selected else "",
            "eventual_handoff_ci_low": low, "eventual_handoff_ci_high": high,
            "median_address_loss_delay": median(delays) if delays else "",
            "class_level_replication_eligible": int(len(selected) >= 5),
        })
    return output


def build_source_specs(args: argparse.Namespace) -> list[dict[str, Any]]:
    original_events = select_source_events(args.event_csv)
    original_seeds = sorted({int(event["init_seed"]) for event, _ in original_events})
    original_configs = {
        seed: load_config(discover_config(args.config_dir, seed)) for seed in original_seeds
    }
    original_checkpoints = {
        seed: run_to_checkpoint(original_configs[seed], "takeover_only_vector_phase", 2048)
        for seed in original_seeds
    }
    source_specs: list[dict[str, Any]] = []
    for source_index, (event, branch_offset) in enumerate(original_events):
        seed = int(event["init_seed"])
        source_specs.append({
            "cohort": "original_states",
            "source_id": f"original-seed{seed}-start{event['start_offset']}",
            "source_index": source_index,
            "event": event,
            "branch_offset": branch_offset,
            "samples": ORIGINAL_SAMPLES,
            "horizon": ORIGINAL_HORIZON,
            "seed_base": ORIGINAL_BRANCH_SEED_BASE + source_index * 10_000,
            "cfg": original_configs[seed],
            "checkpoint": original_checkpoints[seed],
        })

    canonical = load_config(args.canonical_config)
    for source, event in independent_sources(args):
        seed = int(source["init_seed"])
        cfg = config_for_seed(canonical, seed)
        source_specs.append({
            "cohort": "independent_geometries",
            "source_id": source["source_id"],
            "source_index": int(source["source_index"]),
            "event": event,
            "branch_offset": int(event["rebridge_offset"]),
            "samples": INDEPENDENT_SAMPLES,
            "horizon": INDEPENDENT_HORIZON,
            "seed_base": INDEPENDENT_BRANCH_SEED_BASE + int(source["source_index"]) * 10_000,
            "cfg": cfg,
            "checkpoint": run_to_checkpoint(cfg, event["variant"], int(event["checkpoint_tick"])),
        })
    return source_specs


def main() -> None:
    args = parse_args()
    natural_cases: list[dict[str, Any]] = []
    natural_candidates: list[dict[str, Any]] = []
    selectors: list[dict[str, Any]] = []
    source_specs = build_source_specs(args)

    for spec in source_specs:
        event = spec["event"]
        base = build_branch_state(
            event, spec["branch_offset"], spec["checkpoint"], spec["cfg"]
        )
        for sample in spec["samples"]:
            branch_seed = int(spec["seed_base"]) + int(sample)
            case, candidates = run_case(
                event, spec["branch_offset"], *base, sample, branch_seed,
                spec["horizon"], spec["cfg"], allow_censored=True,
            )
            case.update({"cohort": spec["cohort"], "source_id": spec["source_id"]})
            natural_cases.append(case)
            for row in candidates:
                row.update({"cohort": spec["cohort"], "source_id": spec["source_id"]})
            natural_candidates.extend(candidates)
            if case["outcome_class"] != "activated_child":
                continue
            if (
                int(case["preexisting_descendant"]) != 0
                or int(case["lineage_collision"]) != 0
                or int(case["payload_zero_all_offsets"]) != 1
                or int(case["ledger_exact_all_offsets"]) != 1
            ):
                raise RuntimeError("natural necessity selector failed eligibility safety")
            selector = freeze_child_selector(case, candidates)
            selectors.append({
                "selection_rule_version": "f068-first-inherited-child-v1",
                "cohort": spec["cohort"], "source_id": spec["source_id"],
                "init_seed": int(event["init_seed"]),
                "event_start_offset": int(event["start_offset"]),
                "branch_offset": int(spec["branch_offset"]),
                "branch_sample": sample, "branch_seed": branch_seed,
                "natural_terminal_offset": int(case["terminal_offset"]),
                "terminal_relative": selector["relative"],
                "event_index": selector["event_index"],
                "gate_ordinal": selector["gate_ordinal"],
                "source": text_coord(selector["source"]),
                "target": text_coord(selector["target"]),
                "candidate_order": selector["candidate_order"],
                "candidate_step": text_coord(selector["candidate_step"]),
                "available_A_before": selector["available_A_before"],
                "target_active_at_tick_start": int(selector["target_active_at_tick_start"]),
                "target_active_at_evaluation": int(selector["target_active_at_evaluation"]),
                "target_depleted_at_evaluation": int(selector["target_depleted_at_evaluation"]),
                "target_latent_at_evaluation": int(selector["target_latent_at_evaluation"]),
                "influence": selector["influence"],
                "residual_bias_multiplier": selector["residual_bias_multiplier"],
                "transfer_probability": selector["transfer_probability"],
                "gate_draw": selector["gate_draw"],
                "natural_gate_passed": 1, "target_activated": 1,
                "natural_child_multiplicity": selector["natural_child_multiplicity"],
                "inheritance_join_verified": int(selector["inheritance_join_verified"]),
                "payload_zero": int(case["payload_zero_all_offsets"]),
                "ledger_exact": int(case["ledger_exact_all_offsets"]),
                "lineage_collision": int(case["lineage_collision"]),
            })
        print(
            f"necessity cohort={spec['cohort']} source={spec['source_id']} "
            f"branches={len(spec['samples'])}", flush=True,
        )

    prefix = args.output_prefix
    cases_path = prefix.with_name(prefix.name + "_natural_cases.csv")
    candidates_path = prefix.with_name(prefix.name + "_natural_candidates.csv")
    selectors_path = prefix.with_name(prefix.name + "_selectors.csv")
    summary_path = prefix.with_name(prefix.name + "_freeze_summary.json")
    write_csv(cases_path, NATURAL_FIELDS, natural_cases)
    write_csv(candidates_path, CANDIDATE_OUTPUT_FIELDS, natural_candidates)
    write_csv(selectors_path, SELECTOR_FIELDS, selectors)
    summary = {
        "protocol": "factual-only freeze for prospective first-child veto",
        "counterfactual_outcomes_run": False,
        "frozen_independent_manifest_sha256": FROZEN_MANIFEST_SHA256,
        "post_intervention_horizon": POST_INTERVENTION_HORIZON,
        "scheduled_natural_branches": 256,
        "natural_branches": len(natural_cases), "eligible_selectors": len(selectors),
        "natural_outcome_labels": dict(sorted(Counter(row["outcome_class"] for row in natural_cases).items())),
        "natural_child_multiplicity": dict(sorted(Counter(int(row["natural_child_multiplicity"]) for row in selectors).items())),
        "all_inheritance_joins_verified": all(int(row["inheritance_join_verified"]) for row in selectors),
        "all_selector_payload_zero": all(int(row["payload_zero"]) for row in selectors),
        "all_selector_ledgers_exact": all(int(row["ledger_exact"]) for row in selectors),
        "selector_collision_rows": sum(int(row["lineage_collision"]) for row in selectors),
        "natural_cases_csv": str(cases_path), "natural_candidates_csv": str(candidates_path),
        "selectors_csv": str(selectors_path),
    }
    if len(natural_cases) != 256:
        raise RuntimeError(f"incomplete factual matrix: {len(natural_cases)}/256")
    summary["selectors_sha256"] = file_sha256(selectors_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
