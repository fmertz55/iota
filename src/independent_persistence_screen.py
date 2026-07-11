from __future__ import annotations

import argparse
import copy
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from component_bridge_causal_trace import write_csv
from continuation import deterministic_continuation_seed
from experiment_db import artifact_hash, config_hash, flatten_config
from independent_geometry_screen import (
    ALLOWED_CONFIG_CHANGES,
    CASE_FIELDNAMES,
    CONFIG_FIELDNAMES,
    DEFAULT_CANONICAL_CONFIG,
    SEED_AGGREGATE_FIELDNAMES,
    SIGNAL_FIELDNAMES,
    SOURCE_MANIFEST_FIELDNAMES,
    TRANSPORT_FIELDNAMES,
    artifact_paths,
    reconstruct_source_geometry,
    source_manifest_row,
)
from iota_rig import load_config
from phase_free_class_matrix import run_continuation_case, run_to_checkpoint
from phase_free_constraint_transport import replay_event


FINDING = "070A"
INIT_SEEDS = tuple(range(73, 105))
SAMPLE_INDICES = tuple(range(8))
VARIANT = "takeover_only_vector_phase"
CHECKPOINT_TICK = 2048
HORIZON = 600
COORD_LIMIT = 64
CONTINUATION_SEED_BASE = 20_260_711
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding070/independent_persistence_screen"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the frozen Finding 070 independent-initialization screen. "
            "The complete 73..104 by 0..7 matrix is evaluated before sources "
            "are selected."
        )
    )
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument(
        "--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG
    )
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def objective_for_seed(seed: int) -> str:
    return f"finding070_independent_persistence_seed{int(seed)}"


def continuation_seed_for(seed: int, sample_index: int) -> int:
    return deterministic_continuation_seed(
        CONTINUATION_SEED_BASE,
        CHECKPOINT_TICK,
        int(sample_index),
        stream_index=int(seed),
    )


def changed_config_paths(
    canonical: dict[str, Any], effective: dict[str, Any]
) -> set[str]:
    before = flatten_config(canonical)
    after = flatten_config(effective)
    return {
        key
        for key in set(before) | set(after)
        if before.get(key) != after.get(key)
    }


def config_for_seed(canonical: dict[str, Any], seed: int) -> dict[str, Any]:
    cfg = copy.deepcopy(canonical)
    cfg.setdefault("init", {})["seed"] = int(seed)
    cfg.setdefault("experiment", {})["objective"] = objective_for_seed(seed)
    changed = changed_config_paths(canonical, cfg)
    if changed != ALLOWED_CONFIG_CHANGES:
        raise RuntimeError(
            "Finding 070 config mutation escaped the frozen audit: "
            f"expected {sorted(ALLOWED_CONFIG_CHANGES)}, observed {sorted(changed)}"
        )
    return cfg


def classification_args(seed: int) -> SimpleNamespace:
    return SimpleNamespace(
        rng_seed_base=CONTINUATION_SEED_BASE + int(seed) * 100_000,
        checkpoint_tick=CHECKPOINT_TICK,
        horizon=HORIZON,
        coord_limit=COORD_LIMIT,
    )


def transport_args() -> SimpleNamespace:
    return SimpleNamespace(
        checkpoint_tick=CHECKPOINT_TICK,
        coord_limit=COORD_LIMIT,
    )


def candidate_id(row: dict[str, Any]) -> str:
    return (
        f"f070-seed{int(row['init_seed']):03d}-"
        f"sample{int(row['sample_index']):02d}-"
        f"split{int(row['start_offset']):03d}-"
        f"rebridge{int(row['rebridge_offset']):03d}"
    )


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
        row["source_id"] = f"f070-source-{source_index:03d}"


def config_manifest_row(
    canonical_path: Path,
    canonical: dict[str, Any],
    cfg: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    changed = changed_config_paths(canonical, cfg)
    return {
        "init_seed": int(seed),
        "objective": objective_for_seed(seed),
        "canonical_config_path": str(canonical_path),
        "canonical_file_sha256": artifact_hash(canonical_path),
        "canonical_config_sha256": config_hash(canonical),
        "effective_config_sha256": config_hash(cfg),
        "changed_paths": ";".join(sorted(changed)),
        "only_frozen_paths_changed": int(changed == ALLOWED_CONFIG_CHANGES),
        "in_memory_only": 1,
        "sample_0_continuation_seed": continuation_seed_for(seed, 0),
        "sample_7_continuation_seed": continuation_seed_for(seed, 7),
    }


def seed_aggregate_rows(
    case_rows: list[dict[str, Any]],
    signal_rows: list[dict[str, Any]],
    transport_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for seed in INIT_SEEDS:
        cases = [row for row in case_rows if int(row["init_seed"]) == seed]
        signals = [row for row in signal_rows if int(row["init_seed"]) == seed]
        transports = [
            row for row in transport_rows if int(row["init_seed"]) == seed
        ]
        sources = [row for row in source_rows if int(row["init_seed"]) == seed]
        output.append(
            {
                "init_seed": seed,
                "cases": len(cases),
                "unique_continuation_streams": len(
                    {int(row["continuation_seed"]) for row in cases}
                ),
                "signal_intervals": len(signals),
                "class_a_events": sum(
                    row["event_class"] == "class_a" for row in signals
                ),
                "class_b_events": sum(
                    row["event_class"] == "class_b" for row in signals
                ),
                "non_bridge_events": sum(
                    row["event_class"] == "non_bridge" for row in signals
                ),
                "bridge_unresolved_events": sum(
                    row["event_class"] == "bridge_unresolved" for row in signals
                ),
                "strict_transport_events": sum(
                    int(row["constraint_transport"]) for row in transports
                ),
                "singleton_eligible_sources": sum(
                    int(row["singleton_eligible"]) for row in sources
                ),
                "payload_zero_cases": sum(
                    int(row["payload_zero_all_offsets"]) for row in cases
                ),
                "ledger_exact_cases": sum(
                    int(row["ledger_exact_all_offsets"]) for row in cases
                ),
                "payload_zero_transport_events": sum(
                    int(row["payload_zero_all_observed_offsets"])
                    for row in transports
                ),
                "ledger_exact_transport_events": sum(
                    int(row["ledger_exact_all_observed_offsets"])
                    for row in transports
                ),
            }
        )
    return output


def assert_complete_screen(
    case_rows: list[dict[str, Any]],
    signal_rows: list[dict[str, Any]],
    transport_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    config_rows: list[dict[str, Any]],
) -> None:
    expected_cases = {
        (seed, sample) for seed in INIT_SEEDS for sample in SAMPLE_INDICES
    }
    observed_cases = {
        (int(row["init_seed"]), int(row["sample_index"])) for row in case_rows
    }
    if observed_cases != expected_cases or len(case_rows) != len(expected_cases):
        raise RuntimeError(
            f"incomplete Finding 070 case matrix: {len(observed_cases)}/"
            f"{len(expected_cases)}"
        )
    continuation_seeds = [int(row["continuation_seed"]) for row in case_rows]
    if len(set(continuation_seeds)) != len(expected_cases):
        raise RuntimeError("Finding 070 continuation streams are not globally unique")
    if {int(row["init_seed"]) for row in config_rows} != set(INIT_SEEDS):
        raise RuntimeError("Finding 070 config manifest does not cover every seed")
    if not all(int(row["only_frozen_paths_changed"]) for row in config_rows):
        raise RuntimeError("a Finding 070 config changed a non-frozen path")
    class_b = [row for row in signal_rows if row["event_class"] == "class_b"]
    if len(transport_rows) != len(class_b):
        raise RuntimeError("not every Finding 070 Class B event was audited")
    if len(source_rows) != len(transport_rows):
        raise RuntimeError("Finding 070 source manifest is incomplete")
    if not all(int(row["reconstruction_verified"]) for row in source_rows):
        raise RuntimeError("a Finding 070 source candidate lacks reconstruction")
    selected = [
        row for row in source_rows if int(row["frozen_source_selected"]) == 1
    ]
    if len({int(row["init_seed"]) for row in selected}) != len(selected):
        raise RuntimeError("Finding 070 selected more than one source per seed")


def run_seed_job(job: tuple[str, int]) -> dict[str, Any]:
    canonical_path = Path(job[0])
    seed = int(job[1])
    canonical = load_config(canonical_path)
    cfg = config_for_seed(canonical, seed)
    case_rows: list[dict[str, Any]] = []
    signal_rows: list[dict[str, Any]] = []
    transport_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    print(f"f070 checkpoint seed={seed} tick={CHECKPOINT_TICK}", flush=True)
    checkpoint = run_to_checkpoint(cfg, VARIANT, CHECKPOINT_TICK)
    for sample_index in SAMPLE_INDICES:
        case, signals = run_continuation_case(
            classification_args(seed),
            cfg,
            seed,
            VARIANT,
            checkpoint,
            sample_index,
        )
        if int(case["continuation_seed"]) != continuation_seed_for(
            seed, sample_index
        ):
            raise RuntimeError(
                f"Finding 070 stream mismatch seed={seed} sample={sample_index}"
            )
        case_rows.append(case)
        signal_rows.extend(signals)
        print(
            f"f070 screen seed={seed} sample={sample_index} "
            f"case={case['case_class']} signals={case['signal_interval_count']}",
            flush=True,
        )
    class_b = sorted(
        (row for row in signal_rows if row["event_class"] == "class_b"),
        key=lambda row: (int(row["sample_index"]), int(row["start_offset"])),
    )
    for signal in class_b:
        transport = replay_event(transport_args(), signal, checkpoint, cfg)
        reconstruction = reconstruct_source_geometry(signal, checkpoint, cfg)
        source = source_manifest_row(0, signal, transport, reconstruction)
        source["candidate_id"] = candidate_id(transport)
        transport_rows.append(transport)
        source_rows.append(source)
        print(
            f"f070 audit seed={seed} sample={signal['sample_index']} "
            f"split={signal['start_offset']} strict={transport['constraint_transport']} "
            f"singleton={source['singleton_eligible']}",
            flush=True,
        )
    return {
        "cases": case_rows,
        "signals": signal_rows,
        "transports": transport_rows,
        "sources": source_rows,
        "config": config_manifest_row(canonical_path, canonical, cfg, seed),
    }


def run_screen(args: argparse.Namespace) -> dict[str, Any]:
    canonical_path = Path(args.canonical_config)
    if not canonical_path.is_file():
        raise FileNotFoundError(canonical_path)
    canonical = load_config(canonical_path)
    if not str(canonical.get("simulation_version", "")).startswith(
        "iota-rig-v0.3.6"
    ):
        raise RuntimeError("Finding 070 requires the canonical v0.3.6 config")
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
    assert_complete_screen(
        case_rows, signal_rows, transport_rows, source_rows, config_rows
    )
    aggregates = seed_aggregate_rows(
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
    summary = {
        "finding": FINDING,
        "screen_complete": True,
        "protocol_frozen_before_branch_outcomes": True,
        "branch_or_cut_outcomes_inspected_for_selection": False,
        "canonical_config_path": str(canonical_path),
        "canonical_file_sha256": artifact_hash(canonical_path),
        "effective_config_changes": sorted(ALLOWED_CONFIG_CHANGES),
        "effective_configs_written_to_disk": False,
        "init_seeds": list(INIT_SEEDS),
        "sample_indices": list(SAMPLE_INDICES),
        "variant": VARIANT,
        "checkpoint_tick": CHECKPOINT_TICK,
        "horizon": HORIZON,
        "continuation_seed_base": CONTINUATION_SEED_BASE,
        "worker_processes": int(args.workers),
        "selection_rule": (
            "one lexicographically first eligible source per initialization seed"
        ),
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
