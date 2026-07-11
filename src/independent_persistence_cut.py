from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from component_bridge_causal_trace import write_csv
from expression_handoff_branch_ensemble import build_branch_state
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from independent_persistence_freeze import event_for, selected_sources
from independent_persistence_screen import config_for_seed
from iota_rig import load_config
from phase_free_class_matrix import run_to_checkpoint
from realization_necessity import file_sha256
from sequential_realization_cut import (
    CASE_FIELDS,
    NEXT_SELECTOR_FIELDS,
    branch_key,
    parse_selector,
    run_chain,
)
from temporal_gate_replication import verify_sham


DEFAULT_OUTPUT_DIR = Path("output/findings/finding070")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one committed Finding 070 independent sequential-veto depth."
        )
    )
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument(
        "--selector",
        action="append",
        required=True,
        help="Ordered selector manifest as PATH=SHA256; repeat once per depth.",
    )
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument(
        "--freeze-summary",
        type=Path,
        default=DEFAULT_OUTPUT_DIR
        / "independent_persistence_depth_freeze_summary.json",
    )
    parser.add_argument(
        "--screen-summary",
        type=Path,
        default=DEFAULT_OUTPUT_DIR
        / "independent_persistence_screen_summary.json",
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=DEFAULT_OUTPUT_DIR
        / "independent_persistence_screen_source_manifest.csv",
    )
    parser.add_argument(
        "--transport-csv",
        type=Path,
        default=DEFAULT_OUTPUT_DIR
        / "independent_persistence_screen_transport_events.csv",
    )
    parser.add_argument(
        "--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG
    )
    parser.add_argument("--expected-source-manifest-sha256", required=True)
    return parser.parse_args()


def selector_spec(value: str) -> tuple[Path, str]:
    if "=" not in value:
        raise ValueError("--selector must be PATH=SHA256")
    path, expected = value.rsplit("=", 1)
    return Path(path), expected


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_specs(args: argparse.Namespace) -> dict[tuple[str, str], dict[str, Any]]:
    sources = selected_sources(args)
    transports = read_csv(args.transport_csv)
    canonical = load_config(args.canonical_config)
    specs: dict[tuple[str, str], dict[str, Any]] = {}
    for source in sources:
        seed = int(source["init_seed"])
        event = event_for(source, transports)
        cfg = config_for_seed(canonical, seed)
        checkpoint = run_to_checkpoint(
            cfg, event["variant"], int(event["checkpoint_tick"])
        )
        key = ("independent_depth_replication", source["source_id"])
        specs[key] = {
            "event": event,
            "branch_offset": int(event["rebridge_offset"]),
            "cfg": cfg,
            "checkpoint": checkpoint,
        }
    return specs


def validate_manifest_rows(
    manifests: list[tuple[Path, str, list[dict[str, str]]]]
) -> tuple[
    list[dict[tuple[str, str, int, int, int, int], dict[str, str]]], str
]:
    maps: list[
        dict[tuple[str, str, int, int, int, int], dict[str, str]]
    ] = []
    for rank, (_, _, rows) in enumerate(manifests, start=1):
        keys = [branch_key(row) for row in rows]
        if len(keys) != len(set(keys)):
            raise RuntimeError(
                f"Finding 070 selector manifest has duplicates at depth {rank}"
            )
        if rank == 1:
            if any(
                row["selection_rule_version"]
                != "f070-first-unique-inherited-child-v1"
                or int(row["natural_child_multiplicity"]) != 1
                or int(row["inheritance_join_verified"]) != 1
                or int(row["payload_zero"]) != 1
                or int(row["ledger_exact"]) != 1
                or int(row["lineage_collision"]) != 0
                for row in rows
            ):
                raise RuntimeError("Finding 070 factual selector provenance failed")
        else:
            expected_parent = hashlib.sha256(
                "|".join(item[1] for item in manifests[: rank - 1]).encode(
                    "ascii"
                )
            ).hexdigest()
            if any(
                int(row.get("depth", 0)) != rank
                or row.get("selection_rule_version")
                != "f069-first-next-inherited-child-v1"
                or row.get("parent_chain_sha256") != expected_parent
                or int(row.get("source_in_focal_lineage", 0)) != 1
                or int(row.get("unique_inheritance_join", 0)) != 1
                or int(row.get("inheritance_join_verified", 0)) != 1
                or int(row.get("natural_gate_passed", 0)) != 1
                or int(row.get("target_activated", 0)) != 1
                or int(row.get("payload_zero", 0)) != 1
                or int(row.get("ledger_exact", 0)) != 1
                or int(row.get("lineage_collision", 0)) != 0
                for row in rows
            ):
                raise RuntimeError(
                    f"Finding 070 selector provenance failed at depth {rank}"
                )
        maps.append({key: row for key, row in zip(keys, rows)})
    current_keys = set(maps[-1])
    if any(not current_keys <= set(mapping) for mapping in maps[:-1]):
        raise RuntimeError("Finding 070 selector chain is not nested")
    parent_chain_sha256 = hashlib.sha256(
        "|".join(item[1] for item in manifests).encode("ascii")
    ).hexdigest()
    return maps, parent_chain_sha256


def main() -> None:
    args = parse_args()
    if not 1 <= args.depth <= 8 or len(args.selector) != args.depth:
        raise ValueError(
            "depth must be 1..8 and equal the number of --selector values"
        )
    actual_source_hash = file_sha256(args.source_manifest)
    if actual_source_hash != args.expected_source_manifest_sha256:
        raise RuntimeError("Finding 070 source-manifest hash changed")
    freeze = json.loads(args.freeze_summary.read_text(encoding="utf-8"))
    if (
        freeze.get("counterfactual_outcomes_run") is not False
        or freeze.get("source_manifest_sha256") != actual_source_hash
    ):
        raise RuntimeError("Finding 070 factual freeze is invalid")

    manifests: list[tuple[Path, str, list[dict[str, str]]]] = []
    for value in args.selector:
        path, expected = selector_spec(value)
        actual = file_sha256(path)
        if actual != expected:
            raise RuntimeError(f"Finding 070 selector hash mismatch: {path}")
        manifests.append((path, expected, read_csv(path)))
    if manifests[0][1] != freeze["selectors_sha256"]:
        raise RuntimeError("Finding 070 factual selector freeze changed")

    maps, parent_chain_sha256 = validate_manifest_rows(manifests)
    specs = build_specs(args)
    base_cache: dict[tuple[str, str], tuple[Any, ...]] = {}
    cases: list[dict[str, Any]] = []
    next_selectors: list[dict[str, Any]] = []
    sham_matches: list[int] = []
    for key in sorted(maps[-1]):
        chain_rows = [mapping[key] for mapping in maps]
        source_row = chain_rows[0]
        source_key = (source_row["cohort"], source_row["source_id"])
        if source_key not in specs:
            raise RuntimeError(f"Finding 070 source specification missing: {source_key}")
        spec = specs[source_key]
        if source_key not in base_cache:
            base_cache[source_key] = build_branch_state(
                spec["event"],
                spec["branch_offset"],
                spec["checkpoint"],
                spec["cfg"],
            )
        parsed = [parse_selector(row) for row in chain_rows]
        if any(
            (right["relative"], right["gate_ordinal"])
            <= (left["relative"], left["gate_ordinal"])
            for left, right in zip(parsed, parsed[1:])
        ):
            raise RuntimeError("Finding 070 selector order is not increasing")
        if args.depth == 1:
            sham_matches.append(
                verify_sham(
                    base_cache[source_key][0],
                    spec["event"],
                    spec["cfg"],
                    int(source_row["branch_seed"]),
                    parsed[0],
                )
            )
        case, next_selector = run_chain(
            args.depth,
            source_row,
            parsed,
            parent_chain_sha256,
            spec,
            base_cache[source_key],
        )
        cases.append(case)
        if next_selector is not None:
            next_selectors.append(next_selector)

    if args.depth == 1 and (
        len(sham_matches) != len(cases) or any(value != 1 for value in sham_matches)
    ):
        raise RuntimeError("Finding 070 matched sham failed")

    prefix = args.output_prefix
    cases_path = prefix.with_name(prefix.name + "_cases.csv")
    selectors_path = prefix.with_name(prefix.name + "_next_selectors.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(cases_path, CASE_FIELDS, cases)
    write_csv(selectors_path, NEXT_SELECTOR_FIELDS, next_selectors)
    endpoints = Counter(row["stage_endpoint"] for row in cases)
    summary = {
        "protocol": (
            "independent replication of nested sequential ancestry vetoes"
        ),
        "depth": args.depth,
        "current_depth_veto_run": True,
        "next_depth_veto_run": False,
        "source_manifest_path": str(args.source_manifest),
        "source_manifest_sha256": actual_source_hash,
        "freeze_summary_path": str(args.freeze_summary),
        "freeze_summary_sha256": file_sha256(args.freeze_summary),
        "factual_selector_sha256": manifests[0][1],
        "depth1_matched_sham_run": args.depth == 1,
        "all_depth1_shams_exact": (
            all(value == 1 for value in sham_matches)
            if args.depth == 1
            else None
        ),
        "selector_chain": [
            {"path": str(path), "sha256": expected}
            for path, expected, _ in manifests
        ],
        "parent_chain_sha256": parent_chain_sha256,
        "input_branches": len(cases),
        "stage_endpoints": dict(sorted(endpoints.items())),
        "next_selectors": len(next_selectors),
        "transient_child_lineage_losses": sum(
            int(row["next_child_observed"]) == 1
            and row["stage_endpoint"] == "lineage_loss"
            for row in cases
        ),
        "child_bearing_source_censoring": sum(
            int(row["next_child_observed"]) == 1
            and row["stage_endpoint"] == "source_survival_censored"
            for row in cases
        ),
        "all_selectors_matched": all(
            int(row["selectors_matched"]) == args.depth for row in cases
        ),
        "all_selector_identities_exact": all(
            int(row["all_selector_identities_exact"]) for row in cases
        ),
        "all_payload_zero": all(
            int(row["payload_zero_all_offsets"]) for row in cases
        ),
        "all_ledger_exact": all(
            int(row["ledger_exact_all_offsets"]) for row in cases
        ),
        "collision_cases": sum(int(row["lineage_collision"]) for row in cases),
        "cases_csv": str(cases_path),
        "next_selectors_csv": str(selectors_path),
    }
    summary["next_selectors_sha256"] = file_sha256(selectors_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
