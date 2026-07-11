from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import independent_persistence_screen as reusable
from component_bridge_causal_trace import write_csv
from expression_handoff_branch_ensemble import build_branch_state
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from independent_persistence_freeze import selector_row
from iota_rig import load_config
from local_affordance_features import event_for, read_csv, selected_sources
from local_affordance_screen import (
    CONFIRMATION_SEEDS,
    DISCOVERY_SEEDS,
    configure_reusable,
)
from phase_free_class_matrix import run_to_checkpoint
from realization_necessity import (
    CANDIDATE_OUTPUT_FIELDS,
    NATURAL_FIELDS,
    SELECTOR_FIELDS,
    file_sha256,
    freeze_child_selector,
)
from terminal_candidate_ledger import run_case


BRANCH_SAMPLES = tuple(range(48))
NATURAL_HORIZON = 256
POST_INTERVENTION_HORIZON = 128
BRANCH_SEED_BASES = {
    "discovery": 2_026_071_700,
    "confirmation": 2_026_071_800,
}
DEFAULT_OUTPUT_DIR = Path("output/findings/finding071")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one frozen Finding 071 factual response split."
    )
    parser.add_argument("--split", choices=("discovery", "confirmation"), required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument(
        "--screen-summary",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "local_affordance_screen_summary.json",
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "local_affordance_screen_source_manifest.csv",
    )
    parser.add_argument(
        "--transport-csv",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "local_affordance_screen_transport_events.csv",
    )
    parser.add_argument(
        "--feature-schema",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "local_affordance_feature_schema.json",
    )
    parser.add_argument(
        "--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG
    )
    parser.add_argument("--expected-source-manifest-sha256", required=True)
    parser.add_argument("--expected-feature-schema-sha256", required=True)
    return parser.parse_args()


def validate_feature_freeze(args: argparse.Namespace) -> dict[str, Any]:
    actual = file_sha256(args.feature_schema)
    schema = json.loads(args.feature_schema.read_text(encoding="utf-8"))
    checks = {
        "hash": actual == args.expected_feature_schema_sha256,
        "pre_outcome": schema.get("features_extracted_before_affordance_responses")
        is True,
        "responses_unrun": schema.get("affordance_response_outcomes_run") is False,
        "source_hash": schema.get("source_manifest_sha256")
        == args.expected_source_manifest_sha256,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Finding 071 feature freeze failed: {checks}")
    return schema


def main() -> None:
    args = parse_args()
    configure_reusable()
    feature_schema = validate_feature_freeze(args)
    all_sources = selected_sources(args)
    allowed = DISCOVERY_SEEDS if args.split == "discovery" else CONFIRMATION_SEEDS
    sources = [row for row in all_sources if int(row["init_seed"]) in allowed]
    if len(sources) < 6:
        raise RuntimeError(f"Finding 071 {args.split} source support gate failed")
    transports = read_csv(args.transport_csv)
    canonical = load_config(args.canonical_config)
    natural_cases: list[dict[str, Any]] = []
    natural_candidates: list[dict[str, Any]] = []
    selectors: list[dict[str, Any]] = []
    cohort = f"local_affordance_{args.split}"
    branch_seed_base = BRANCH_SEED_BASES[args.split]

    for source in sources:
        source_index = int(source["source_index"])
        seed = int(source["init_seed"])
        event = event_for(source, transports)
        cfg = reusable.config_for_seed(canonical, seed)
        checkpoint = run_to_checkpoint(
            cfg, event["variant"], int(event["checkpoint_tick"])
        )
        branch_offset = int(event["rebridge_offset"])
        base = build_branch_state(event, branch_offset, checkpoint, cfg)
        for sample in BRANCH_SAMPLES:
            branch_seed = branch_seed_base + source_index * 10_000 + sample
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
            case.update({"cohort": cohort, "source_id": source["source_id"]})
            natural_cases.append(case)
            for row in candidates:
                row.update({"cohort": cohort, "source_id": source["source_id"]})
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
                raise RuntimeError("Finding 071 factual selector failed safety")
            selector = freeze_child_selector(case, candidates)
            if int(selector["natural_child_multiplicity"]) != 1:
                continue
            frozen = selector_row(
                source, event, case, selector, sample, branch_seed
            )
            frozen.update(
                {
                    "selection_rule_version": "f071-first-unique-inherited-child-v1",
                    "cohort": cohort,
                }
            )
            selectors.append(frozen)
        print(
            f"f071 factual split={args.split} source={source['source_id']} "
            f"seed={seed} branches={len(BRANCH_SAMPLES)}",
            flush=True,
        )

    expected_branches = len(sources) * len(BRANCH_SAMPLES)
    if len(natural_cases) != expected_branches:
        raise RuntimeError("Finding 071 factual matrix is incomplete")
    branch_keys = [
        (row["source_id"], int(row["branch_seed"])) for row in natural_cases
    ]
    if len(branch_keys) != len(set(branch_keys)):
        raise RuntimeError("Finding 071 factual branch keys are not unique")

    prefix = args.output_prefix
    cases_path = prefix.with_name(prefix.name + "_natural_cases.csv")
    candidates_path = prefix.with_name(prefix.name + "_natural_candidates.csv")
    selectors_path = prefix.with_name(prefix.name + "_selectors.csv")
    summary_path = prefix.with_name(prefix.name + "_freeze_summary.json")
    write_csv(cases_path, NATURAL_FIELDS, natural_cases)
    write_csv(candidates_path, CANDIDATE_OUTPUT_FIELDS, natural_candidates)
    write_csv(selectors_path, SELECTOR_FIELDS, selectors)

    address_losses = Counter(
        row["source_id"]
        for row in natural_cases
        if row["outcome_class"] != "censored"
    )
    selectors_by_source = Counter(row["source_id"] for row in selectors)
    measurement_eligible = [
        source["source_id"]
        for source in sources
        if address_losses[source["source_id"]] >= 16
        and selectors_by_source[source["source_id"]] >= 8
    ]
    summary = {
        "finding": "071C",
        "split": args.split,
        "protocol": "factual-only local affordance response and selector freeze",
        "counterfactual_outcomes_run": False,
        "confirmation_outcomes_run": args.split == "confirmation",
        "source_manifest_sha256": file_sha256(args.source_manifest),
        "feature_schema_sha256": file_sha256(args.feature_schema),
        "feature_rows": int(feature_schema["sources"]),
        "selected_sources": len(sources),
        "branches_per_source": len(BRANCH_SAMPLES),
        "natural_horizon_from_rebridge": NATURAL_HORIZON,
        "post_intervention_horizon": POST_INTERVENTION_HORIZON,
        "branch_seed_base": branch_seed_base,
        "scheduled_natural_branches": expected_branches,
        "natural_branches": len(natural_cases),
        "natural_outcome_labels": dict(
            sorted(Counter(row["outcome_class"] for row in natural_cases).items())
        ),
        "eligible_selectors": len(selectors),
        "address_losses_by_source": {
            source["source_id"]: address_losses[source["source_id"]]
            for source in sources
        },
        "eligible_selectors_by_source": {
            source["source_id"]: selectors_by_source[source["source_id"]]
            for source in sources
        },
        "measurement_eligible_sources": measurement_eligible,
        "measurement_support_gate_met": len(measurement_eligible) >= 6,
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
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
