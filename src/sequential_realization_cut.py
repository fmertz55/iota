from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import write_csv
from continuation import clone_world
from expression_handoff_branch_ensemble import build_branch_state
from expression_lineage_transport import advance_lineages
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from phase_free_constraint_transport import ledger_error
from phase_source_minimization_audit import clamp_stored_phase, phase_source_patch
from realization_necessity import (
    FROZEN_MANIFEST_SHA256,
    POST_INTERVENTION_HORIZON,
    SELECTOR_FIELDS,
    build_source_specs,
    coord,
    file_sha256,
    text_coord,
)


NEXT_SELECTOR_FIELDS = [
    "depth", "parent_chain_sha256", "focal_lineage_size_before",
    "source_in_focal_lineage", "unique_inheritance_join", *SELECTOR_FIELDS,
]
CASE_FIELDS = [
    "depth", "cohort", "source_id", "init_seed", "event_start_offset",
    "branch_sample", "branch_seed", "selectors_expected", "selectors_matched",
    "all_selector_identities_exact", "next_child_observed", "next_child_relative",
    "next_child_offset", "next_child_target", "next_child_multiplicity",
    "next_child_same_as_previous_target", "address_loss_observed", "terminal_offset",
    "address_loss_delay_from_depth1_natural", "handoff", "stage_endpoint",
    "lineage_collision", "payload_zero_all_offsets", "ledger_exact_all_offsets",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one committed sequential realization-veto depth.")
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument(
        "--selector", action="append", required=True,
        help="Ordered selector manifest as PATH=SHA256; repeat once per depth.",
    )
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--expected-replays", type=Path)
    parser.add_argument("--event-csv", type=Path, default=Path("output/findings/finding060/phase_free_constraint_transport_events.csv"))
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--source-manifest", type=Path, default=Path("output/findings/finding067/independent_geometry_screen_source_manifest.csv"))
    parser.add_argument("--transport-csv", type=Path, default=Path("output/findings/finding067/independent_geometry_screen_transport_events.csv"))
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def selector_spec(value: str) -> tuple[Path, str]:
    if "=" not in value:
        raise ValueError("--selector must be PATH=SHA256")
    path, expected = value.rsplit("=", 1)
    return Path(path), expected


def branch_key(row: dict[str, Any]) -> tuple[str, str, int]:
    return str(row["cohort"]), str(row["source_id"]), int(row["branch_seed"])


def parse_selector(row: dict[str, str]) -> dict[str, Any]:
    return {
        "relative": int(row["terminal_relative"]),
        "event_index": int(row["event_index"]),
        "gate_ordinal": int(row["gate_ordinal"]),
        "source": coord(row["source"]), "target": coord(row["target"]),
        "candidate_order": int(row["candidate_order"]),
        "candidate_step": coord(row["candidate_step"]),
        "available_A_before": int(row["available_A_before"]),
        "target_active_at_tick_start": bool(int(row["target_active_at_tick_start"])),
        "target_active_at_evaluation": bool(int(row["target_active_at_evaluation"])),
        "target_depleted_at_evaluation": bool(int(row["target_depleted_at_evaluation"])),
        "target_latent_at_evaluation": bool(int(row["target_latent_at_evaluation"])),
        "influence": float(row["influence"]),
        "residual_bias_multiplier": float(row["residual_bias_multiplier"]),
        "transfer_probability": float(row["transfer_probability"]),
        "gate_draw": float(row["gate_draw"]),
    }


def assert_selector_identity(
    relative: int, gate_ordinal: int, candidate: dict[str, Any], selector: dict[str, Any]
) -> None:
    checks = {
        "relative": relative == selector["relative"],
        "gate_ordinal": gate_ordinal == selector["gate_ordinal"],
        "source": tuple(candidate["source"]) == selector["source"],
        "target": tuple(candidate["target"]) == selector["target"],
        "candidate_order": int(candidate["candidate_order"]) == selector["candidate_order"],
        "candidate_step": tuple(candidate["candidate_step"]) == selector["candidate_step"],
        "available_A_before": int(candidate["available_A_before"]) == selector["available_A_before"],
        "target_active_at_tick_start": bool(candidate["target_active_at_tick_start"]) == selector["target_active_at_tick_start"],
        "target_active_at_evaluation": bool(candidate["target_active_at_evaluation"]) == selector["target_active_at_evaluation"],
        "target_depleted_at_evaluation": bool(candidate["target_depleted_at_evaluation"]) == selector["target_depleted_at_evaluation"],
        "target_latent_at_evaluation": bool(candidate["target_latent_at_evaluation"]) == selector["target_latent_at_evaluation"],
        "influence": float(candidate["influence"]) == selector["influence"],
        "residual_bias_multiplier": float(candidate["residual_bias_multiplier"]) == selector["residual_bias_multiplier"],
        "transfer_probability": float(candidate["transfer_probability"]) == selector["transfer_probability"],
        "gate_draw": float(candidate["gate_draw"]) == selector["gate_draw"],
        "natural_gate_passed": bool(candidate["natural_gate_passed"]) is True,
    }
    if not all(checks.values()):
        raise RuntimeError(f"sequential selector identity mismatch: {checks}")


def child_selector_from_tick(
    depth: int,
    parent_chain_sha256: str,
    source_row: dict[str, str],
    branch_offset: int,
    relative: int,
    terminal_offset: int,
    candidates: list[dict[str, Any]],
    inherited: list[dict[str, Any]],
    lineage_before: set[tuple[int, int, int]],
    singleton_index: int,
    payload_zero: bool,
    exact: bool,
    collision: bool,
) -> dict[str, Any] | None:
    focal_inherited = [
        row for row in inherited if int(row["lineage_index"]) == singleton_index
    ]
    inherited_targets = {tuple(row["target"]) for row in focal_inherited}
    if not inherited_targets:
        return None
    gated_index = -1
    inherited_keys = {
        (tuple(row["source"]), tuple(row["target"]), int(row["candidate_order"]))
        for row in focal_inherited
    }
    matches: list[tuple[int, int, dict[str, Any]]] = []
    for event_index, candidate in enumerate(candidates):
        if candidate["status"] in {"succeeded", "gate_failed"}:
            gated_index += 1
        if (
            candidate["status"] == "succeeded"
            and candidate.get("target_activated") is True
            and (
                tuple(candidate["source"]), tuple(candidate["target"]),
                int(candidate["candidate_order"]),
            ) in inherited_keys
        ):
            matches.append((event_index, gated_index, candidate))
    if not matches:
        raise RuntimeError("inherited child lacks a successful candidate ledger row")
    event_index, gate_ordinal, selected = min(matches, key=lambda item: item[0])
    return {
        "depth": depth,
        "parent_chain_sha256": parent_chain_sha256,
        "focal_lineage_size_before": len(lineage_before),
        "source_in_focal_lineage": int(tuple(selected["source"]) in lineage_before),
        "unique_inheritance_join": int(
            sum(
                key == (
                    tuple(selected["source"]), tuple(selected["target"]),
                    int(selected["candidate_order"]),
                )
                for key in inherited_keys
            ) == 1
        ),
        "selection_rule_version": "f069-first-next-inherited-child-v1",
        "cohort": source_row["cohort"], "source_id": source_row["source_id"],
        "init_seed": int(source_row["init_seed"]),
        "event_start_offset": int(source_row["event_start_offset"]),
        "branch_offset": branch_offset,
        "branch_sample": int(source_row["branch_sample"]),
        "branch_seed": int(source_row["branch_seed"]),
        "natural_terminal_offset": terminal_offset,
        "terminal_relative": relative,
        "event_index": event_index, "gate_ordinal": gate_ordinal,
        "source": text_coord(tuple(selected["source"])),
        "target": text_coord(tuple(selected["target"])),
        "candidate_order": int(selected["candidate_order"]),
        "candidate_step": text_coord(tuple(selected["candidate_step"])),
        "available_A_before": int(selected["available_A_before"]),
        "target_active_at_tick_start": int(bool(selected["target_active_at_tick_start"])),
        "target_active_at_evaluation": int(bool(selected["target_active_at_evaluation"])),
        "target_depleted_at_evaluation": int(bool(selected["target_depleted_at_evaluation"])),
        "target_latent_at_evaluation": int(bool(selected["target_latent_at_evaluation"])),
        "influence": float(selected["influence"]),
        "residual_bias_multiplier": float(selected["residual_bias_multiplier"]),
        "transfer_probability": float(selected["transfer_probability"]),
        "gate_draw": float(selected["gate_draw"]),
        "natural_gate_passed": 1, "target_activated": 1,
        "natural_child_multiplicity": len(inherited_targets),
        "inheritance_join_verified": 1,
        "payload_zero": int(payload_zero), "ledger_exact": int(exact),
        "lineage_collision": int(collision),
    }


def run_chain(
    depth: int,
    source_row: dict[str, str],
    selectors: list[dict[str, Any]],
    parent_chain_sha256: str,
    spec: dict[str, Any],
    base: tuple[Any, ...],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    event = spec["event"]
    branch_offset = int(spec["branch_offset"])
    world = clone_world(base[0], int(source_row["branch_seed"]))
    lineages = [set(value) for value in base[1]]
    singleton_index = int(base[2])
    original = tuple(base[3])
    terminated = [False, False]
    collision = False
    payload_zero = True
    exact = True
    gate_ordinals: dict[int, int] = {}
    selector_map = {
        (selector["relative"], selector["gate_ordinal"]): selector
        for selector in selectors
    }
    matched: set[tuple[int, int]] = set()
    next_selector: dict[str, Any] | None = None
    depth1_relative = selectors[0]["relative"]
    final_relative = depth1_relative + POST_INTERVENTION_HORIZON
    death: dict[str, Any] | None = None

    def override(relative: int, candidate: dict[str, Any]) -> bool | None:
        gate_ordinal = gate_ordinals.get(relative, 0)
        gate_ordinals[relative] = gate_ordinal + 1
        key = (relative, gate_ordinal)
        if key not in selector_map:
            return None
        assert_selector_identity(relative, gate_ordinal, candidate, selector_map[key])
        if key in matched:
            raise RuntimeError("sequential selector matched more than once")
        matched.add(key)
        return False

    try:
        with phase_source_patch(event["variant"]):
            clamp_stored_phase(world, event["variant"])
            for relative in range(final_relative + 1):
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                transfers: list[dict[str, Any]] = []
                candidates: list[dict[str, Any]] = []
                lineage_before = set(lineages[singleton_index])
                iota_rig.HARD_TRANSFER_TRACE_HOOK = transfers.append
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = candidates.append
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = lambda row, r=relative: override(r, row)
                iota_rig.step(world, spec["cfg"])
                iota_rig.HARD_TRANSFER_TRACE_HOOK = None
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
                clamp_stored_phase(world, event["variant"])
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                next_lineages, collided, _, inherited = advance_lineages(lineages, world, transfers)
                collision |= collided
                for selector in selectors:
                    if selector["relative"] != relative:
                        continue
                    ledger_matches = [
                        (index, candidate)
                        for index, candidate in enumerate(candidates)
                        if tuple(candidate["source"]) == selector["source"]
                        and tuple(candidate["target"]) == selector["target"]
                        and int(candidate["candidate_order"]) == selector["candidate_order"]
                        and candidate.get("gate_overridden") is True
                    ]
                    if (
                        len(ledger_matches) != 1
                        or ledger_matches[0][0] != selector["event_index"]
                        or ledger_matches[0][1]["status"] != "gate_failed"
                        or ledger_matches[0][1].get("effective_gate_passed") is not False
                    ):
                        raise RuntimeError("post-step selector ledger identity changed")
                for index in range(2):
                    if terminated[index]:
                        next_lineages[index] = set()
                    elif not next_lineages[index]:
                        terminated[index] = True
                if next_selector is None and len(matched) == depth:
                    next_selector = child_selector_from_tick(
                        depth + 1, parent_chain_sha256, source_row, branch_offset,
                        relative, branch_offset + relative + 1, candidates, inherited,
                        lineage_before, singleton_index, payload_zero, exact, collision,
                    )
                if not bool(world.active[original]):
                    death = {
                        "observed": True,
                        "terminal_offset": branch_offset + relative + 1,
                        "handoff": bool(next_lineages[singleton_index]) and not collision,
                    }
                    break
                lineages = next_lineages
    finally:
        iota_rig.HARD_TRANSFER_TRACE_HOOK = None
        iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
        iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None

    if len(matched) != depth:
        raise RuntimeError(f"matched {len(matched)}/{depth} committed selectors")
    if death is None:
        death = {"observed": False, "terminal_offset": "", "handoff": False}
    if death["handoff"] and next_selector is None:
        raise RuntimeError("handoff survivor lacks a prospective next child selector")
    if not death["handoff"]:
        next_selector = None
    previous_target = selectors[-1]["target"]
    next_target = None if next_selector is None else coord(next_selector["target"])
    natural_terminal = int(source_row["natural_terminal_offset"])
    result = {
        "depth": depth, "cohort": source_row["cohort"],
        "source_id": source_row["source_id"], "init_seed": int(source_row["init_seed"]),
        "event_start_offset": int(source_row["event_start_offset"]),
        "branch_sample": int(source_row["branch_sample"]),
        "branch_seed": int(source_row["branch_seed"]),
        "selectors_expected": depth, "selectors_matched": len(matched),
        "all_selector_identities_exact": 1,
        "next_child_observed": int(next_selector is not None),
        "next_child_relative": "" if next_selector is None else int(next_selector["terminal_relative"]),
        "next_child_offset": "" if next_selector is None else int(next_selector["natural_terminal_offset"]),
        "next_child_target": "" if next_target is None else text_coord(next_target),
        "next_child_multiplicity": "" if next_selector is None else int(next_selector["natural_child_multiplicity"]),
        "next_child_same_as_previous_target": int(next_target == previous_target) if next_target is not None else "",
        "address_loss_observed": int(death["observed"]),
        "terminal_offset": death["terminal_offset"],
        "address_loss_delay_from_depth1_natural": (
            "" if death["terminal_offset"] == "" else int(death["terminal_offset"]) - natural_terminal
        ),
        "handoff": int(death["handoff"]),
        "stage_endpoint": (
            "handoff" if death["handoff"] else
            "lineage_loss" if death["observed"] else "source_survival_censored"
        ),
        "lineage_collision": int(collision),
        "payload_zero_all_offsets": int(payload_zero),
        "ledger_exact_all_offsets": int(exact),
    }
    return result, next_selector


def main() -> None:
    args = parse_args()
    if not 1 <= args.depth <= 8 or len(args.selector) != args.depth:
        raise ValueError("depth must be 1..8 and equal the number of ordered --selector values")
    manifests: list[tuple[Path, str, list[dict[str, str]]]] = []
    for value in args.selector:
        path, expected = selector_spec(value)
        actual = file_sha256(path)
        if actual != expected:
            raise RuntimeError(f"selector hash mismatch for {path}: {actual}")
        manifests.append((path, expected, read_csv(path)))
    if manifests[0][1] != "9e4a70d8d0b829b4a4b288da69b8a740c398b5c161a0e5a26a7605015e8c8cb0":
        raise RuntimeError("depth-1 Finding 068 selector manifest changed")
    parent_chain_sha256 = hashlib.sha256(
        "|".join(item[1] for item in manifests).encode("ascii")
    ).hexdigest()
    maps = [{branch_key(row): row for row in rows} for _, _, rows in manifests]
    for index, (_, _, rows) in enumerate(manifests[1:], start=2):
        if any(int(row.get("depth", 0)) != index for row in rows):
            raise RuntimeError(f"selector manifest rank is not contiguous at depth {index}")
    current_keys = set(maps[-1])
    if any(not current_keys <= set(mapping) for mapping in maps[:-1]):
        raise RuntimeError("selector chain is not nested")

    specs = {(spec["cohort"], spec["source_id"]): spec for spec in build_source_specs(args)}
    base_cache: dict[tuple[str, str], tuple[Any, ...]] = {}
    cases: list[dict[str, Any]] = []
    next_selectors: list[dict[str, Any]] = []
    for key in sorted(current_keys):
        chain_rows = [mapping[key] for mapping in maps]
        source_row = chain_rows[0]
        source_key = (source_row["cohort"], source_row["source_id"])
        spec = specs[source_key]
        if source_key not in base_cache:
            base_cache[source_key] = build_branch_state(
                spec["event"], spec["branch_offset"], spec["checkpoint"], spec["cfg"]
            )
        parsed = [parse_selector(row) for row in chain_rows]
        if any(
            (right["relative"], right["gate_ordinal"])
            <= (left["relative"], left["gate_ordinal"])
            for left, right in zip(parsed, parsed[1:])
        ):
            raise RuntimeError("selector chain order is not strictly increasing")
        case, next_selector = run_chain(
            args.depth, source_row, parsed, parent_chain_sha256, spec,
            base_cache[source_key],
        )
        cases.append(case)
        if next_selector is not None:
            next_selectors.append(next_selector)

    if args.expected_replays is not None:
        expected_replay_hash = "cbba811983592c635a85529ceac467b3fb9d7d27de5fb585d4f56ddaaf728cb1"
        if file_sha256(args.expected_replays) != expected_replay_hash:
            raise RuntimeError("committed Finding 068 replay bytes changed")
        expected = {branch_key(row): row for row in read_csv(args.expected_replays)}
        for case in cases:
            row = expected[branch_key(case)]
            if (
                int(case["handoff"]) != int(row["eventual_handoff"])
                or case["next_child_target"] != row["first_alternate_child_target"]
                or (
                    case["next_child_relative"] != ""
                    and int(case["next_child_relative"]) - int(maps[0][branch_key(case)]["terminal_relative"])
                    != int(row["first_alternate_child_delay"])
                )
            ):
                raise RuntimeError("depth-1 reproduction diverged from committed Finding 068")

    prefix = args.output_prefix
    cases_path = prefix.with_name(prefix.name + "_cases.csv")
    selectors_path = prefix.with_name(prefix.name + "_next_selectors.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(cases_path, CASE_FIELDS, cases)
    write_csv(selectors_path, NEXT_SELECTOR_FIELDS, next_selectors)
    endpoints = Counter(row["stage_endpoint"] for row in cases)
    summary = {
        "protocol": "nested sequential ancestry-realization veto",
        "depth": args.depth,
        "current_depth_veto_run": True,
        "next_depth_veto_run": False,
        "selector_chain": [
            {"path": str(path), "sha256": expected} for path, expected, _ in manifests
        ],
        "parent_chain_sha256": parent_chain_sha256,
        "input_branches": len(cases),
        "stage_endpoints": dict(sorted(endpoints.items())),
        "next_selectors": len(next_selectors),
        "expected_replays": (
            None if args.expected_replays is None else {
                "path": str(args.expected_replays),
                "sha256": file_sha256(args.expected_replays),
            }
        ),
        "all_selectors_matched": all(int(row["selectors_matched"]) == args.depth for row in cases),
        "all_selector_identities_exact": all(int(row["all_selector_identities_exact"]) for row in cases),
        "all_payload_zero": all(int(row["payload_zero_all_offsets"]) for row in cases),
        "all_ledger_exact": all(int(row["ledger_exact_all_offsets"]) for row in cases),
        "collision_cases": sum(int(row["lineage_collision"]) for row in cases),
        "cases_csv": str(cases_path), "next_selectors_csv": str(selectors_path),
    }
    summary["next_selectors_sha256"] = file_sha256(selectors_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
