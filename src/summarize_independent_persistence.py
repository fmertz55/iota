from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from summarize_sequential_cut import (
    as_bool,
    branch_key,
    display_path,
    file_sha256,
    fraction,
    read_csv,
    selector_offset,
    source_key,
    write_csv,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST_SHA256 = (
    "c2749807dbbd06d8ec6ff52762ca9e1154c5c56be8d037c86e692c66d2114618"
)
FACTUAL_SELECTOR_SHA256 = (
    "01ad7968c7bdd2795c5d7029b481a4420982f3e4c940e99dcf5fd71297bc17e7"
)
FREEZE_SUMMARY_SHA256 = (
    "d072f4d772e444701fcf2309192561df72cd192e945e8ca2378a88fe190e1721"
)
FIXED_FOLLOWUP = 128
MAX_DEPTH = 8

DEPTH_FIELDS = [
    "depth",
    "risk_set",
    "cuts",
    "handoffs",
    "source_survival_censored",
    "conditional_cut_fraction_of_risk",
    "conditional_cut_fraction_of_resolved",
    "cumulative_cuts",
    "cumulative_source_survival_censored",
    "cumulative_confirmed_handoffs",
    "next_selectors",
]
SOURCE_FIELDS = [
    "depth",
    "source_id",
    "init_seed",
    "event_start_offset",
    "initial_selectors",
    "risk_set",
    "cuts",
    "handoffs",
    "source_survival_censored",
    "cumulative_cuts",
    "cumulative_source_survival_censored",
    "cumulative_confirmed_handoffs",
]
HASH_FIELDS = [
    "depth",
    "summary_path",
    "summary_sha256",
    "cases_path",
    "cases_sha256",
    "current_selector_path",
    "current_selector_sha256",
    "parent_chain_sha256",
    "next_selector_path",
    "next_selector_sha256",
    "next_selector_rows",
]
ASSIGNMENT_FIELDS = [
    "source_id",
    "init_seed",
    "event_start_offset",
    "branch_sample",
    "branch_seed",
    "last_observed_depth",
    "selectors_vetoed",
    "selector_target_sequence",
    "unique_selector_targets",
    "repeated_selector_targets",
    "selector_offset_sequence",
    "selector_offset_span",
    "maximum_interselector_delay",
    "cut_depth",
    "cut_depth_label",
    "assignment_status",
    "right_censored",
    "source_survival_censored_depth",
    "terminal_offset_at_assignment",
    "address_loss_delay_at_assignment",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and summarize the complete Finding 070 depth chain."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("output/findings/finding070"),
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=Path(
            "output/findings/finding070/independent_persistence_replication"
        ),
    )
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def resolve(path_text: str, input_dir: Path) -> Path:
    path = Path(path_text)
    candidates = [path] if path.is_absolute() else [ROOT / path, input_dir / path.name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(path_text)


def validate_case(row: dict[str, str], depth: int) -> None:
    checks = {
        "depth": int(row["depth"]) == depth,
        "expected": int(row["selectors_expected"]) == depth,
        "matched": int(row["selectors_matched"]) == depth,
        "identity": as_bool(
            row["all_selector_identities_exact"],
            "all_selector_identities_exact",
        ),
        "collision_free": not as_bool(row["lineage_collision"], "lineage_collision"),
        "payload_zero": as_bool(
            row["payload_zero_all_offsets"], "payload_zero_all_offsets"
        ),
        "ledger_exact": as_bool(
            row["ledger_exact_all_offsets"], "ledger_exact_all_offsets"
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(
            f"Finding 070 depth {depth} branch {branch_key(row)} failed: {checks}"
        )
    endpoint = row["stage_endpoint"]
    if endpoint not in {"handoff", "lineage_loss", "source_survival_censored"}:
        raise RuntimeError(f"Finding 070 depth {depth} unknown endpoint {endpoint}")
    observed = as_bool(row["address_loss_observed"], "address_loss_observed")
    if endpoint in {"handoff", "lineage_loss"} and not observed:
        raise RuntimeError("resolved Finding 070 endpoint lacks address loss")
    if endpoint == "source_survival_censored" and observed:
        raise RuntimeError("Finding 070 source censor reports address loss")
    delay = row["address_loss_delay_from_depth1_natural"]
    if observed and (delay == "" or not 0 <= int(delay) <= FIXED_FOLLOWUP):
        raise RuntimeError("Finding 070 address loss escaped the fixed endpoint")


def load_stage(depth: int, input_dir: Path) -> dict[str, Any]:
    summary_path = input_dir / f"depth{depth:03d}_summary.json"
    cases_path = input_dir / f"depth{depth:03d}_cases.csv"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    cases = read_csv(cases_path)
    if int(summary["depth"]) != depth or len(cases) != int(summary["input_branches"]):
        raise RuntimeError(f"Finding 070 depth {depth} summary/case mismatch")
    case_keys = [branch_key(row) for row in cases]
    if len(case_keys) != len(set(case_keys)):
        raise RuntimeError(f"Finding 070 depth {depth} duplicate cases")
    for row in cases:
        validate_case(row, depth)
    case_by_key = {branch_key(row): row for row in cases}
    endpoints = Counter(row["stage_endpoint"] for row in cases)
    if dict(sorted(endpoints.items())) != summary["stage_endpoints"]:
        raise RuntimeError(f"Finding 070 depth {depth} endpoint mismatch")

    chain = summary["selector_chain"]
    if len(chain) != depth:
        raise RuntimeError(f"Finding 070 depth {depth} chain length changed")
    chain_hashes: list[str] = []
    for item in chain:
        path = resolve(str(item["path"]), input_dir)
        actual = file_sha256(path)
        if actual != item["sha256"]:
            raise RuntimeError(f"Finding 070 selector hash changed: {path}")
        chain_hashes.append(actual)
    parent_hash = hashlib.sha256("|".join(chain_hashes).encode("ascii")).hexdigest()
    if parent_hash != summary["parent_chain_sha256"]:
        raise RuntimeError(f"Finding 070 depth {depth} parent hash changed")
    if chain_hashes[0] != FACTUAL_SELECTOR_SHA256:
        raise RuntimeError("Finding 070 factual selector hash changed")

    current_path = resolve(str(chain[-1]["path"]), input_dir)
    current_rows = read_csv(current_path)
    current_keys = [branch_key(row) for row in current_rows]
    if len(current_keys) != len(set(current_keys)) or set(current_keys) != set(case_keys):
        raise RuntimeError(f"Finding 070 depth {depth} current risk set changed")
    current_by_key = {branch_key(row): row for row in current_rows}

    next_path = resolve(str(summary["next_selectors_csv"]), input_dir)
    next_hash = file_sha256(next_path)
    if next_hash != summary["next_selectors_sha256"]:
        raise RuntimeError(f"Finding 070 depth {depth} next-selector hash changed")
    next_rows = read_csv(next_path)
    next_keys = [branch_key(row) for row in next_rows]
    handoff_keys = {
        branch_key(row) for row in cases if row["stage_endpoint"] == "handoff"
    }
    if (
        len(next_keys) != len(set(next_keys))
        or set(next_keys) != handoff_keys
        or len(next_rows) != int(summary["next_selectors"])
    ):
        raise RuntimeError(f"Finding 070 depth {depth} next risk set changed")
    for selector in next_rows:
        key = branch_key(selector)
        case = case_by_key[key]
        offset = selector_offset(selector)
        checks = {
            "depth": int(selector["depth"]) == depth + 1,
            "rule": selector["selection_rule_version"]
            == "f069-first-next-inherited-child-v1",
            "parent": selector["parent_chain_sha256"] == parent_hash,
            "offset_equation": offset
            == int(selector["branch_offset"])
            + int(selector["terminal_relative"])
            + 1,
            "target": selector["target"] == case["next_child_target"],
            "relative": int(selector["terminal_relative"])
            == int(case["next_child_relative"]),
            "offset": offset == int(case["next_child_offset"]),
            "multiplicity": int(selector["natural_child_multiplicity"])
            == int(case["next_child_multiplicity"]),
        }
        if not all(checks.values()):
            raise RuntimeError(
                f"Finding 070 depth {depth} selector/case join failed: {checks}"
            )
    summary_checks = {
        "source_manifest": summary["source_manifest_sha256"]
        == SOURCE_MANIFEST_SHA256,
        "freeze": summary["freeze_summary_sha256"] == FREEZE_SUMMARY_SHA256,
        "factual": summary["factual_selector_sha256"]
        == FACTUAL_SELECTOR_SHA256,
        "matched": summary["all_selectors_matched"] is True,
        "identity": summary["all_selector_identities_exact"] is True,
        "payload": summary["all_payload_zero"] is True,
        "ledger": summary["all_ledger_exact"] is True,
        "collision": int(summary["collision_cases"]) == 0,
        "current_run": summary["current_depth_veto_run"] is True,
        "next_not_run": summary["next_depth_veto_run"] is False,
    }
    if depth == 1:
        summary_checks.update(
            {
                "sham_run": summary["depth1_matched_sham_run"] is True,
                "shams_exact": summary["all_depth1_shams_exact"] is True,
            }
        )
    if not all(summary_checks.values()):
        raise RuntimeError(
            f"Finding 070 depth {depth} summary failed: {summary_checks}"
        )
    return {
        "depth": depth,
        "summary": summary,
        "summary_path": summary_path,
        "cases_path": cases_path,
        "cases": cases,
        "keys": set(case_keys),
        "handoff_keys": handoff_keys,
        "chain_hashes": chain_hashes,
        "parent_hash": parent_hash,
        "current_path": current_path,
        "current_by_key": current_by_key,
        "next_path": next_path,
        "next_hash": next_hash,
        "next_rows": next_rows,
    }


def validate_chain(stages: list[dict[str, Any]]) -> None:
    for previous, current in zip(stages, stages[1:]):
        if current["keys"] != previous["handoff_keys"]:
            raise RuntimeError("Finding 070 risk-set nesting changed")
        if current["chain_hashes"] != previous["chain_hashes"] + [
            previous["next_hash"]
        ]:
            raise RuntimeError("Finding 070 selector-chain extension changed")
        for key in current["keys"]:
            before = previous["current_by_key"][key]
            after = current["current_by_key"][key]
            if (
                selector_offset(after),
                int(after["gate_ordinal"]),
            ) <= (
                selector_offset(before),
                int(before["gate_ordinal"]),
            ):
                raise RuntimeError("Finding 070 selector order did not advance")


def depth_rows(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cumulative_cuts = 0
    cumulative_censored = 0
    output: list[dict[str, Any]] = []
    for stage in stages:
        endpoints = Counter(row["stage_endpoint"] for row in stage["cases"])
        risk = len(stage["cases"])
        cuts = endpoints["lineage_loss"]
        handoffs = endpoints["handoff"]
        censored = endpoints["source_survival_censored"]
        cumulative_cuts += cuts
        cumulative_censored += censored
        output.append(
            {
                "depth": stage["depth"],
                "risk_set": risk,
                "cuts": cuts,
                "handoffs": handoffs,
                "source_survival_censored": censored,
                "conditional_cut_fraction_of_risk": fraction(cuts, risk),
                "conditional_cut_fraction_of_resolved": fraction(
                    cuts, cuts + handoffs
                ),
                "cumulative_cuts": cumulative_cuts,
                "cumulative_source_survival_censored": cumulative_censored,
                "cumulative_confirmed_handoffs": handoffs,
                "next_selectors": len(stage["next_rows"]),
            }
        )
    return output


def source_rows(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    initial = Counter(source_key(row) for row in stages[0]["cases"])
    cuts: Counter[tuple[str, str, int, int]] = Counter()
    censored: Counter[tuple[str, str, int, int]] = Counter()
    output: list[dict[str, Any]] = []
    for stage in stages:
        grouped: dict[tuple[str, str, int, int], list[dict[str, str]]] = {}
        for row in stage["cases"]:
            grouped.setdefault(source_key(row), []).append(row)
        for key in sorted(initial):
            rows = grouped.get(key, [])
            endpoints = Counter(row["stage_endpoint"] for row in rows)
            cuts[key] += endpoints["lineage_loss"]
            censored[key] += endpoints["source_survival_censored"]
            output.append(
                {
                    "depth": stage["depth"],
                    "source_id": key[1],
                    "init_seed": key[2],
                    "event_start_offset": key[3],
                    "initial_selectors": initial[key],
                    "risk_set": len(rows),
                    "cuts": endpoints["lineage_loss"],
                    "handoffs": endpoints["handoff"],
                    "source_survival_censored": endpoints[
                        "source_survival_censored"
                    ],
                    "cumulative_cuts": cuts[key],
                    "cumulative_source_survival_censored": censored[key],
                    "cumulative_confirmed_handoffs": endpoints["handoff"],
                }
            )
    return output


def assignments(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    histories = {branch_key(row): [] for row in stages[0]["cases"]}
    selector_histories = {key: [] for key in histories}
    for stage in stages:
        for row in stage["cases"]:
            histories[branch_key(row)].append(row)
        for key, row in stage["current_by_key"].items():
            selector_histories[key].append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(histories):
        rows = histories[key]
        selectors = selector_histories[key]
        first, last = rows[0], rows[-1]
        targets = [row["target"] for row in selectors]
        offsets = [selector_offset(row) for row in selectors]
        gaps = [right - left for left, right in zip(offsets, offsets[1:])]
        endpoint = last["stage_endpoint"]
        if endpoint == "lineage_loss":
            cut_depth: int | str = int(last["depth"])
            label = str(cut_depth)
            status = "observed_cut"
            right_censored = 0
            source_censor_depth: int | str = ""
        elif endpoint == "source_survival_censored":
            cut_depth = ""
            source_censor_depth = int(last["depth"])
            label = f"source-censored@{source_censor_depth}"
            status = "source_survival_censored"
            right_censored = 1
        elif endpoint == "handoff" and int(last["depth"]) == MAX_DEPTH:
            cut_depth = ""
            source_censor_depth = ""
            label = ">8"
            status = "right_censored_above_protocol_max"
            right_censored = 1
        else:
            raise RuntimeError(f"Finding 070 incomplete assignment: {key}")
        output.append(
            {
                "source_id": first["source_id"],
                "init_seed": int(first["init_seed"]),
                "event_start_offset": int(first["event_start_offset"]),
                "branch_sample": int(first["branch_sample"]),
                "branch_seed": int(first["branch_seed"]),
                "last_observed_depth": int(last["depth"]),
                "selectors_vetoed": len(selectors),
                "selector_target_sequence": "|".join(targets),
                "unique_selector_targets": len(set(targets)),
                "repeated_selector_targets": len(targets) - len(set(targets)),
                "selector_offset_sequence": "|".join(str(value) for value in offsets),
                "selector_offset_span": offsets[-1] - offsets[0],
                "maximum_interselector_delay": max(gaps, default=0),
                "cut_depth": cut_depth,
                "cut_depth_label": label,
                "assignment_status": status,
                "right_censored": right_censored,
                "source_survival_censored_depth": source_censor_depth,
                "terminal_offset_at_assignment": last["terminal_offset"],
                "address_loss_delay_at_assignment": last[
                    "address_loss_delay_from_depth1_natural"
                ],
            }
        )
    return output


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    source_manifest = input_dir / "independent_persistence_screen_source_manifest.csv"
    freeze_summary = input_dir / "independent_persistence_depth_freeze_summary.json"
    factual_selectors = input_dir / "independent_persistence_depth_selectors.csv"
    if file_sha256(source_manifest) != SOURCE_MANIFEST_SHA256:
        raise RuntimeError("Finding 070 source freeze changed")
    if file_sha256(freeze_summary) != FREEZE_SUMMARY_SHA256:
        raise RuntimeError("Finding 070 factual freeze summary changed")
    if file_sha256(factual_selectors) != FACTUAL_SELECTOR_SHA256:
        raise RuntimeError("Finding 070 factual selectors changed")
    stages = [load_stage(depth, input_dir) for depth in range(1, MAX_DEPTH + 1)]
    validate_chain(stages)

    depths = depth_rows(stages)
    sources = source_rows(stages)
    branch_assignments = assignments(stages)
    hash_rows = [
        {
            "depth": stage["depth"],
            "summary_path": display_path(stage["summary_path"], ROOT),
            "summary_sha256": file_sha256(stage["summary_path"]),
            "cases_path": display_path(stage["cases_path"], ROOT),
            "cases_sha256": file_sha256(stage["cases_path"]),
            "current_selector_path": display_path(stage["current_path"], ROOT),
            "current_selector_sha256": stage["chain_hashes"][-1],
            "parent_chain_sha256": stage["parent_hash"],
            "next_selector_path": display_path(stage["next_path"], ROOT),
            "next_selector_sha256": stage["next_hash"],
            "next_selector_rows": len(stage["next_rows"]),
        }
        for stage in stages
    ]

    prefix = args.output_prefix
    depths_path = prefix.with_name(prefix.name + "_depths.csv")
    sources_path = prefix.with_name(prefix.name + "_sources.csv")
    hashes_path = prefix.with_name(prefix.name + "_selector_hashes.csv")
    assignments_path = prefix.with_name(prefix.name + "_assignments.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(depths_path, DEPTH_FIELDS, depths)
    write_csv(sources_path, SOURCE_FIELDS, sources)
    write_csv(hashes_path, HASH_FIELDS, hash_rows)
    write_csv(assignments_path, ASSIGNMENT_FIELDS, branch_assignments)

    labels = Counter(row["cut_depth_label"] for row in branch_assignments)
    statuses = Counter(row["assignment_status"] for row in branch_assignments)
    observed_delays = [
        int(row["address_loss_delay_from_depth1_natural"])
        for stage in stages
        for row in stage["cases"]
        if row["address_loss_delay_from_depth1_natural"] != ""
    ]
    original_summary = json.loads(
        (
            ROOT
            / "output/findings/finding069/"
            "sequential_realization_cut_summary.json"
        ).read_text(encoding="utf-8")
    )
    summary = {
        "protocol": "independent replication of ordered realization cut depth",
        "estimand": (
            "prefix-minimal retained-amplitude veto depth under the frozen "
            "first-next-child policy"
        ),
        "protocol_complete": True,
        "initial_selectors": len(branch_assignments),
        "independent_initialization_seeds": len(
            {int(row["init_seed"]) for row in branch_assignments}
        ),
        "fixed_followup_offsets": FIXED_FOLLOWUP,
        "protocol_max_depth": MAX_DEPTH,
        "observed_cut_depth_counts": {
            str(depth): labels[str(depth)] for depth in range(1, MAX_DEPTH + 1)
        },
        "observed_cuts": statuses["observed_cut"],
        "right_censored_above_protocol_max": statuses[
            "right_censored_above_protocol_max"
        ],
        "source_survival_censored": statuses["source_survival_censored"],
        "distinct_selector_events_vetoed": sum(
            int(row["selectors_vetoed"]) for row in branch_assignments
        ),
        "selector_override_executions": sum(
            int(row["depth"]) * int(row["risk_set"]) for row in depths
        ),
        "branches_with_reused_selector_targets": sum(
            int(row["repeated_selector_targets"]) > 0
            for row in branch_assignments
        ),
        "transient_child_lineage_losses": sum(
            int(stage["summary"]["transient_child_lineage_losses"])
            for stage in stages
        ),
        "child_bearing_source_censoring": sum(
            int(stage["summary"]["child_bearing_source_censoring"])
            for stage in stages
        ),
        "collision_cases": sum(
            int(stage["summary"]["collision_cases"]) for stage in stages
        ),
        "maximum_observed_address_loss_delay": max(observed_delays),
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "factual_selector_sha256": FACTUAL_SELECTOR_SHA256,
        "freeze_summary_sha256": FREEZE_SUMMARY_SHA256,
        "all_depth1_shams_exact": stages[0]["summary"][
            "all_depth1_shams_exact"
        ],
        "all_risk_sets_nested": True,
        "all_selector_hashes_verified": True,
        "all_selector_case_joins_verified": True,
        "all_safety_checks_passed": True,
        "depth1_handoff_sources": len(
            {
                row["source_id"]
                for row in stages[0]["cases"]
                if row["stage_endpoint"] == "handoff"
            }
        ),
        "preregistered_nontrivial_support_replication_met": len(
            {
                row["source_id"]
                for row in stages[0]["cases"]
                if row["stage_endpoint"] == "handoff"
            }
        )
        >= 2,
        "finding069_descriptive_comparison": {
            "finding069_initial_selectors": original_summary["initial_branches"],
            "finding069_depth1_handoff_fraction": original_summary[
                "depth_aggregate"
            ][0]["conditional_handoff_fraction_of_risk"],
            "finding070_depth1_handoff_fraction": fraction(
                depths[0]["handoffs"], depths[0]["risk_set"]
            ),
            "finding069_above_depth8_fraction": fraction(
                original_summary["right_censored_above_protocol_max"],
                original_summary["initial_branches"],
            ),
            "finding070_above_depth8_fraction": fraction(
                statuses["right_censored_above_protocol_max"],
                len(branch_assignments),
            ),
        },
        "cut_depth_distribution": dict(sorted(labels.items())),
        "depth_aggregate": depths,
        "depths_csv": display_path(depths_path, ROOT),
        "sources_csv": display_path(sources_path, ROOT),
        "selector_hashes_csv": display_path(hashes_path, ROOT),
        "assignments_csv": display_path(assignments_path, ROOT),
    }
    write_json(summary_path, summary)
    if not args.quiet:
        print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
