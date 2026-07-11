from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import independent_persistence_screen as reusable
from component_bridge_causal_trace import write_csv
from experiment_db import artifact_hash
from independent_geometry_screen import (
    CASE_FIELDNAMES,
    CONFIG_FIELDNAMES,
    DEFAULT_CANONICAL_CONFIG,
    SEED_AGGREGATE_FIELDNAMES,
    SIGNAL_FIELDNAMES,
    SOURCE_MANIFEST_FIELDNAMES,
    TRANSPORT_FIELDNAMES,
    artifact_paths,
)
from iota_rig import load_config


FINDING = "071A"
INIT_SEEDS = tuple(range(105, 233))
DISCOVERY_SEEDS = tuple(range(105, 169))
CONFIRMATION_SEEDS = tuple(range(169, 233))
SAMPLE_INDICES = tuple(range(8))
CONTINUATION_SEED_BASE = 20_260_716
DEFAULT_OUTPUT_PREFIX = Path("output/findings/finding071/local_affordance_screen")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the frozen Finding 071 independent source screen over seeds "
            "105..232 before any affordance response branches."
        )
    )
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument(
        "--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG
    )
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def objective_for_seed(seed: int) -> str:
    return f"finding071_local_affordance_seed{int(seed)}"


def candidate_id(row: dict[str, Any]) -> str:
    return (
        f"f071-seed{int(row['init_seed']):03d}-"
        f"sample{int(row['sample_index']):02d}-"
        f"split{int(row['start_offset']):03d}-"
        f"rebridge{int(row['rebridge_offset']):03d}"
    )


def configure_reusable() -> None:
    reusable.FINDING = FINDING
    reusable.INIT_SEEDS = INIT_SEEDS
    reusable.SAMPLE_INDICES = SAMPLE_INDICES
    reusable.CONTINUATION_SEED_BASE = CONTINUATION_SEED_BASE
    reusable.objective_for_seed = objective_for_seed
    reusable.candidate_id = candidate_id


def freeze_source_ids(rows: list[dict[str, Any]]) -> None:
    eligible_by_seed: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        if int(row["singleton_eligible"]) == 1:
            eligible_by_seed.setdefault(int(row["init_seed"]), []).append(row)
    selected = [
        min(
            candidates,
            key=lambda row: (
                int(row["sample_index"]),
                int(row["start_offset"]),
                int(row["rebridge_offset"]),
            ),
        )
        for _, candidates in sorted(eligible_by_seed.items())
    ]
    for source_index, row in enumerate(selected, start=1):
        row["frozen_source_selected"] = 1
        row["source_index"] = source_index
        row["source_id"] = f"f071-source-{source_index:03d}"


def run_seed_job(job: tuple[str, int]) -> dict[str, Any]:
    configure_reusable()
    return reusable.run_seed_job(job)


def run_screen(args: argparse.Namespace) -> dict[str, Any]:
    configure_reusable()
    canonical_path = Path(args.canonical_config)
    if not canonical_path.is_file():
        raise FileNotFoundError(canonical_path)
    canonical = load_config(canonical_path)
    if not str(canonical.get("simulation_version", "")).startswith(
        "iota-rig-v0.3.6"
    ):
        raise RuntimeError("Finding 071 requires the canonical v0.3.6 config")
    if not 1 <= int(args.workers) <= 4:
        raise ValueError("--workers must be between 1 and 4")

    case_rows: list[dict[str, Any]] = []
    signal_rows: list[dict[str, Any]] = []
    transport_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    config_rows: list[dict[str, Any]] = []
    jobs = [(str(canonical_path), seed) for seed in INIT_SEEDS]
    with ProcessPoolExecutor(max_workers=int(args.workers)) as executor:
        for result in executor.map(run_seed_job, jobs):
            case_rows.extend(result["cases"])
            signal_rows.extend(result["signals"])
            transport_rows.extend(result["transports"])
            source_rows.extend(result["sources"])
            config_rows.append(result["config"])
    for index, row in enumerate(source_rows, start=1):
        row["candidate_index"] = index

    freeze_source_ids(source_rows)
    reusable.assert_complete_screen(
        case_rows, signal_rows, transport_rows, source_rows, config_rows
    )
    aggregates = reusable.seed_aggregate_rows(
        case_rows, signal_rows, transport_rows, source_rows
    )
    paths = artifact_paths(Path(args.output_prefix))
    write_csv(paths["case_csv"], CASE_FIELDNAMES, case_rows)
    write_csv(paths["signal_csv"], SIGNAL_FIELDNAMES, signal_rows)
    write_csv(paths["transport_csv"], TRANSPORT_FIELDNAMES, transport_rows)
    write_csv(
        paths["source_manifest_csv"], SOURCE_MANIFEST_FIELDNAMES, source_rows
    )
    write_csv(paths["seed_aggregate_csv"], SEED_AGGREGATE_FIELDNAMES, aggregates)
    write_csv(paths["config_manifest_csv"], CONFIG_FIELDNAMES, config_rows)

    selected = [
        row for row in source_rows if int(row["frozen_source_selected"]) == 1
    ]
    discovery = [
        row for row in selected if int(row["init_seed"]) in DISCOVERY_SEEDS
    ]
    confirmation = [
        row for row in selected if int(row["init_seed"]) in CONFIRMATION_SEEDS
    ]
    support_gate = len(discovery) >= 6 and len(confirmation) >= 6
    summary = {
        "finding": FINDING,
        "screen_complete": True,
        "protocol_frozen_before_affordance_responses": True,
        "affordance_branch_or_veto_outcomes_inspected_for_selection": False,
        "canonical_config_path": str(canonical_path),
        "canonical_file_sha256": artifact_hash(canonical_path),
        "effective_config_changes": sorted(reusable.ALLOWED_CONFIG_CHANGES),
        "effective_configs_written_to_disk": False,
        "init_seeds": list(INIT_SEEDS),
        "discovery_seeds": list(DISCOVERY_SEEDS),
        "confirmation_seeds": list(CONFIRMATION_SEEDS),
        "sample_indices": list(SAMPLE_INDICES),
        "variant": reusable.VARIANT,
        "checkpoint_tick": reusable.CHECKPOINT_TICK,
        "horizon": reusable.HORIZON,
        "continuation_seed_base": CONTINUATION_SEED_BASE,
        "worker_processes": int(args.workers),
        "selection_rule": (
            "one lexicographically first eligible source per initialization seed"
        ),
        "minimum_sources_per_split": 6,
        "source_support_gate_met": support_gate,
        "cases": len(case_rows),
        "expected_cases": len(INIT_SEEDS) * len(SAMPLE_INDICES),
        "unique_continuation_streams": len(
            {int(row["continuation_seed"]) for row in case_rows}
        ),
        "signal_intervals": len(signal_rows),
        "class_b_candidates": sum(
            row["event_class"] == "class_b" for row in signal_rows
        ),
        "strict_transport_events": sum(
            int(row["constraint_transport"]) for row in transport_rows
        ),
        "singleton_eligible_sources": sum(
            int(row["singleton_eligible"]) for row in source_rows
        ),
        "frozen_primary_sources": len(selected),
        "discovery_sources": len(discovery),
        "confirmation_sources": len(confirmation),
        "selected_initialization_seeds": sorted(
            int(row["init_seed"]) for row in selected
        ),
        "all_classification_payload_zero": all(
            int(row["payload_zero_all_offsets"]) for row in case_rows
        ),
        "all_classification_ledgers_exact": all(
            int(row["ledger_exact_all_offsets"]) for row in case_rows
        ),
        "all_transport_payload_zero": all(
            int(row["payload_zero_all_observed_offsets"])
            for row in transport_rows
        ),
        "all_transport_ledgers_exact": all(
            int(row["ledger_exact_all_observed_offsets"])
            for row in transport_rows
        ),
        "artifacts": {
            name: {"path": str(path), "sha256": artifact_hash(path)}
            for name, path in paths.items()
            if name != "summary_json"
        },
        "seed_aggregate": aggregates,
    }
    paths["summary_json"].parent.mkdir(parents=True, exist_ok=True)
    paths["summary_json"].write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True), flush=True)
    return summary


def main() -> None:
    run_screen(parse_args())


if __name__ == "__main__":
    main()
