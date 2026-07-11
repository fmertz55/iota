from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from component_bridge_causal_trace import write_csv
from expression_handoff_branch_ensemble import build_branch_state
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from independent_persistence_screen import config_for_seed
from iota_rig import load_config
from phase_free_class_matrix import run_to_checkpoint
from realization_necessity import (
    CANDIDATE_OUTPUT_FIELDS,
    NATURAL_FIELDS,
    SELECTOR_FIELDS,
    file_sha256,
    freeze_child_selector,
    text_coord,
)
from terminal_candidate_ledger import run_case


BRANCH_SAMPLES = tuple(range(32))
NATURAL_HORIZON = 256
POST_INTERVENTION_HORIZON = 128
BRANCH_SEED_BASE = 2_026_071_500
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding070/independent_persistence_depth"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the factual-only Finding 070 branch screen and freeze the "
            "first unique inherited child before any veto outcome."
        )
    )
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument(
        "--screen-summary",
        type=Path,
        default=Path(
            "output/findings/finding070/"
            "independent_persistence_screen_summary.json"
        ),
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=Path(
            "output/findings/finding070/"
            "independent_persistence_screen_source_manifest.csv"
        ),
    )
    parser.add_argument(
        "--transport-csv",
        type=Path,
        default=Path(
            "output/findings/finding070/"
            "independent_persistence_screen_transport_events.csv"
        ),
    )
    parser.add_argument(
        "--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG
    )
    parser.add_argument("--expected-source-manifest-sha256", required=True)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def selected_sources(args: argparse.Namespace) -> list[dict[str, str]]:
    summary = json.loads(args.screen_summary.read_text(encoding="utf-8"))
    if (
        summary.get("screen_complete") is not True
        or summary.get("protocol_frozen_before_branch_outcomes") is not True
        or summary.get("branch_or_cut_outcomes_inspected_for_selection") is not False
    ):
        raise RuntimeError("Finding 070 source screen is incomplete or contaminated")
    actual_hash = file_sha256(args.source_manifest)
    if actual_hash != args.expected_source_manifest_sha256:
        raise RuntimeError(
            f"Finding 070 source-manifest hash mismatch: {actual_hash}"
        )
    recorded = summary["artifacts"]["source_manifest_csv"]["sha256"]
    if actual_hash != recorded:
        raise RuntimeError("Finding 070 screen summary and source manifest disagree")
    sources = [
        row
        for row in read_csv(args.source_manifest)
        if int(row["frozen_source_selected"]) == 1
    ]
    keys = [(int(row["init_seed"]), row["source_id"]) for row in sources]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Finding 070 selected-source identities are not unique")
    if len({seed for seed, _ in keys}) != len(keys):
        raise RuntimeError("Finding 070 selected more than one source per seed")
    if len(sources) != int(summary["frozen_primary_sources"]):
        raise RuntimeError("Finding 070 selected-source count changed")
    return sources


def event_for(
    source: dict[str, str], transports: list[dict[str, str]]
) -> dict[str, str]:
    matches = [
        row
        for row in transports
        if int(row["init_seed"]) == int(source["init_seed"])
        and int(row["sample_index"]) == int(source["sample_index"])
        and int(row["start_offset"]) == int(source["start_offset"])
        and int(row["rebridge_offset"]) == int(source["rebridge_offset"])
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one Finding 070 event for {source['source_id']}, "
            f"observed {len(matches)}"
        )
    return matches[0]


def selector_row(
    source: dict[str, str],
    event: dict[str, str],
    case: dict[str, Any],
    selector: dict[str, Any],
    sample: int,
    branch_seed: int,
) -> dict[str, Any]:
    return {
        "selection_rule_version": "f070-first-unique-inherited-child-v1",
        "cohort": "independent_depth_replication",
        "source_id": source["source_id"],
        "init_seed": int(event["init_seed"]),
        "event_start_offset": int(event["start_offset"]),
        "branch_offset": int(event["rebridge_offset"]),
        "branch_sample": sample,
        "branch_seed": branch_seed,
        "natural_terminal_offset": int(case["terminal_offset"]),
        "terminal_relative": selector["relative"],
        "event_index": selector["event_index"],
        "gate_ordinal": selector["gate_ordinal"],
        "source": text_coord(selector["source"]),
        "target": text_coord(selector["target"]),
        "candidate_order": selector["candidate_order"],
        "candidate_step": text_coord(selector["candidate_step"]),
        "available_A_before": selector["available_A_before"],
        "target_active_at_tick_start": int(
            selector["target_active_at_tick_start"]
        ),
        "target_active_at_evaluation": int(
            selector["target_active_at_evaluation"]
        ),
        "target_depleted_at_evaluation": int(
            selector["target_depleted_at_evaluation"]
        ),
        "target_latent_at_evaluation": int(
            selector["target_latent_at_evaluation"]
        ),
        "influence": selector["influence"],
        "residual_bias_multiplier": selector["residual_bias_multiplier"],
        "transfer_probability": selector["transfer_probability"],
        "gate_draw": selector["gate_draw"],
        "natural_gate_passed": 1,
        "target_activated": 1,
        "natural_child_multiplicity": selector["natural_child_multiplicity"],
        "inheritance_join_verified": int(selector["inheritance_join_verified"]),
        "payload_zero": int(case["payload_zero_all_offsets"]),
        "ledger_exact": int(case["ledger_exact_all_offsets"]),
        "lineage_collision": int(case["lineage_collision"]),
    }


def main() -> None:
    args = parse_args()
    sources = selected_sources(args)
    transports = read_csv(args.transport_csv)
    canonical = load_config(args.canonical_config)
    natural_cases: list[dict[str, Any]] = []
    natural_candidates: list[dict[str, Any]] = []
    selectors: list[dict[str, Any]] = []

    for source in sources:
        source_index = int(source["source_index"])
        seed = int(source["init_seed"])
        event = event_for(source, transports)
        cfg = config_for_seed(canonical, seed)
        checkpoint = run_to_checkpoint(
            cfg, event["variant"], int(event["checkpoint_tick"])
        )
        branch_offset = int(event["rebridge_offset"])
        base = build_branch_state(event, branch_offset, checkpoint, cfg)
        for sample in BRANCH_SAMPLES:
            branch_seed = BRANCH_SEED_BASE + source_index * 10_000 + sample
            case, candidates = run_case(
                event,
                branch_offset,
                *base,
                sample,
                branch_seed,
                NATURAL_HORIZON,
                cfg,
                allow_censored=True,
            )
            case.update(
                {
                    "cohort": "independent_depth_replication",
                    "source_id": source["source_id"],
                }
            )
            natural_cases.append(case)
            for row in candidates:
                row.update(
                    {
                        "cohort": "independent_depth_replication",
                        "source_id": source["source_id"],
                    }
                )
            natural_candidates.extend(candidates)
            if (
                case["outcome_class"] != "activated_child"
                or int(case["singleton_lineage_size"]) != 1
                or int(case["preexisting_descendant"]) != 0
            ):
                continue
            if (
                int(case["lineage_collision"]) != 0
                or int(case["payload_zero_all_offsets"]) != 1
                or int(case["ledger_exact_all_offsets"]) != 1
            ):
                raise RuntimeError("Finding 070 factual selector failed safety")
            selector = freeze_child_selector(case, candidates)
            if int(selector["natural_child_multiplicity"]) != 1:
                continue
            selectors.append(
                selector_row(
                    source, event, case, selector, sample, branch_seed
                )
            )
        print(
            f"f070 factual source={source['source_id']} seed={seed} "
            f"branches={len(BRANCH_SAMPLES)}",
            flush=True,
        )

    expected_branches = len(sources) * len(BRANCH_SAMPLES)
    if len(natural_cases) != expected_branches:
        raise RuntimeError(
            f"incomplete Finding 070 factual matrix: {len(natural_cases)}/"
            f"{expected_branches}"
        )
    branch_keys = [
        (row["source_id"], int(row["branch_seed"])) for row in natural_cases
    ]
    if len(branch_keys) != len(set(branch_keys)):
        raise RuntimeError("Finding 070 factual branch keys are not unique")

    prefix = args.output_prefix
    cases_path = prefix.with_name(prefix.name + "_natural_cases.csv")
    candidates_path = prefix.with_name(prefix.name + "_natural_candidates.csv")
    selectors_path = prefix.with_name(prefix.name + "_selectors.csv")
    summary_path = prefix.with_name(prefix.name + "_freeze_summary.json")
    write_csv(cases_path, NATURAL_FIELDS, natural_cases)
    write_csv(candidates_path, CANDIDATE_OUTPUT_FIELDS, natural_candidates)
    write_csv(selectors_path, SELECTOR_FIELDS, selectors)

    eligible_by_source = Counter(row["source_id"] for row in selectors)
    source_seed = {row["source_id"]: int(row["init_seed"]) for row in sources}
    geometry_replication_eligible = [
        source_id
        for source_id, count in sorted(eligible_by_source.items())
        if count >= 5
    ]
    summary = {
        "protocol": (
            "factual-only freeze for independent ordered-depth replication"
        ),
        "counterfactual_outcomes_run": False,
        "screen_summary_path": str(args.screen_summary),
        "source_manifest_path": str(args.source_manifest),
        "source_manifest_sha256": file_sha256(args.source_manifest),
        "transport_csv_sha256": file_sha256(args.transport_csv),
        "selected_sources": len(sources),
        "selected_initialization_seeds": sorted(source_seed.values()),
        "branches_per_source": len(BRANCH_SAMPLES),
        "natural_horizon_from_rebridge": NATURAL_HORIZON,
        "post_intervention_horizon": POST_INTERVENTION_HORIZON,
        "branch_seed_base": BRANCH_SEED_BASE,
        "scheduled_natural_branches": expected_branches,
        "natural_branches": len(natural_cases),
        "eligible_selectors": len(selectors),
        "eligible_selectors_by_source": {
            source_id: eligible_by_source[source_id]
            for source_id in sorted(source_seed)
        },
        "geometry_replication_eligible_sources": geometry_replication_eligible,
        "geometry_replication_eligible_seed_count": len(
            {source_seed[source_id] for source_id in geometry_replication_eligible}
        ),
        "natural_outcome_labels": dict(
            sorted(Counter(row["outcome_class"] for row in natural_cases).items())
        ),
        "natural_child_multiplicity": dict(
            sorted(
                Counter(
                    int(row["natural_child_multiplicity"]) for row in selectors
                ).items()
            )
        ),
        "all_inheritance_joins_verified": all(
            int(row["inheritance_join_verified"]) for row in selectors
        ),
        "all_selector_payload_zero": all(
            int(row["payload_zero"]) for row in selectors
        ),
        "all_selector_ledgers_exact": all(
            int(row["ledger_exact"]) for row in selectors
        ),
        "selector_collision_rows": sum(
            int(row["lineage_collision"]) for row in selectors
        ),
        "natural_cases_csv": str(cases_path),
        "natural_candidates_csv": str(candidates_path),
        "selectors_csv": str(selectors_path),
    }
    summary["selectors_sha256"] = file_sha256(selectors_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
