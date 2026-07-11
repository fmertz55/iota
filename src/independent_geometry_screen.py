from __future__ import annotations

import argparse
import copy
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import iota_rig
from component_bridge_causal_trace import csv_bool, write_csv
from continuation import clone_world, deterministic_continuation_seed
from experiment_db import artifact_hash, config_hash, flatten_config
from iota_rig import World, load_config
from phase_free_class_matrix import (
    CASE_FIELDNAMES,
    SIGNAL_FIELDNAMES,
    run_continuation_case,
    run_to_checkpoint,
)
from phase_free_constraint_transport import (
    EVENT_FIELDNAMES as TRANSPORT_FIELDNAMES,
    replay_event,
)
from phase_source_minimization_audit import clamp_stored_phase, phase_source_patch
from predecessor_region_lineage import parse_coords, reconstruct_regions


FINDING = "067B"
INIT_SEEDS = tuple(range(57, 73))
SAMPLE_INDICES = tuple(range(8))
VARIANT = "takeover_only_vector_phase"
CHECKPOINT_TICK = 2048
HORIZON = 600
COORD_LIMIT = 64
CONTINUATION_SEED_BASE = 20_260_708
DEFAULT_CANONICAL_CONFIG = Path(
    "output/findings/configs/"
    "v036_component_bridge_seed42_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_"
    "amc0p5_amr0p5_cap2_amrb2p0_cb0p25_lb0p05_ffn0p05_een0p05.yaml"
)
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding067/independent_geometry_screen"
)
ALLOWED_CONFIG_CHANGES = frozenset({"experiment.objective", "init.seed"})


CONFIG_FIELDNAMES = [
    "init_seed",
    "objective",
    "canonical_config_path",
    "canonical_file_sha256",
    "canonical_config_sha256",
    "effective_config_sha256",
    "changed_paths",
    "only_frozen_paths_changed",
    "in_memory_only",
    "sample_0_continuation_seed",
    "sample_7_continuation_seed",
]

SEED_AGGREGATE_FIELDNAMES = [
    "init_seed",
    "cases",
    "unique_continuation_streams",
    "signal_intervals",
    "class_a_events",
    "class_b_events",
    "non_bridge_events",
    "bridge_unresolved_events",
    "strict_transport_events",
    "singleton_eligible_sources",
    "payload_zero_cases",
    "ledger_exact_cases",
    "payload_zero_transport_events",
    "ledger_exact_transport_events",
]

SOURCE_MANIFEST_FIELDNAMES = [
    "candidate_index",
    "candidate_id",
    "source_index",
    "source_id",
    "frozen_source_selected",
    "selection_uses_intervention_outcomes",
    "init_seed",
    "variant",
    "sample_index",
    "continuation_seed",
    "checkpoint_tick",
    "start_offset",
    "rebridge_offset",
    "source_state_offset",
    "original_bridge_cells",
    "successor_bridge_cells",
    "bridge_path_jaccard",
    "constraint_transport",
    "predecessor_region_count",
    "predecessor_region_sizes",
    "persistent_predecessor_region_sizes",
    "successor_bridge_role_critical",
    "reconstruction_verified",
    "original_bridge_reconstruction_match",
    "strict_region_metrics_match_reconstruction",
    "reconstructed_predecessor_region_sizes",
    "reconstructed_persistent_region_sizes",
    "singleton_region_index",
    "singleton_original_address",
    "singleton_persistent_size_at_rebridge",
    "singleton_original_active_at_rebridge",
    "strict_transport_gate",
    "two_predecessor_regions_gate",
    "exactly_one_singleton_predecessor_gate",
    "persistent_singleton_size_one_gate",
    "successor_role_critical_gate",
    "complete_displacement_gate",
    "singleton_eligible",
    "eligibility_failures",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the frozen Finding 067B independent-initialization geometry screen. "
            "The complete 57..72 by 0..7 matrix is always evaluated before sources "
            "are written."
        )
    )
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    parser.add_argument("--workers", type=int, default=3)
    return parser.parse_args()


def objective_for_seed(seed: int) -> str:
    return f"finding067b_independent_geometry_seed{int(seed)}"


def continuation_seed_for(seed: int, sample_index: int) -> int:
    return deterministic_continuation_seed(
        CONTINUATION_SEED_BASE,
        CHECKPOINT_TICK,
        int(sample_index),
        stream_index=int(seed),
    )


def changed_config_paths(
    canonical: dict[str, Any],
    effective: dict[str, Any],
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
    cfg.setdefault("experiment", {})["objective"] = objective_for_seed(int(seed))
    changed = changed_config_paths(canonical, cfg)
    if changed != ALLOWED_CONFIG_CHANGES:
        raise RuntimeError(
            "Finding 067B config mutation escaped the frozen audit: "
            f"expected {sorted(ALLOWED_CONFIG_CHANGES)}, observed {sorted(changed)}"
        )
    return cfg


def classification_args(seed: int) -> SimpleNamespace:
    # run_continuation_case adds the checkpoint and sample terms. Moving the
    # initialization seed into its documented stream slot makes all 128 streams
    # distinct while retaining the frozen Finding 059 continuation generator.
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


def integer_series(value: Any) -> list[int]:
    return [int(item) for item in str(value).split(";") if str(item).strip()]


def coords_text(coords: set[tuple[int, int, int]]) -> str:
    return ";".join(":".join(str(value) for value in coord) for coord in sorted(coords))


def reconstruct_source_geometry(
    signal: dict[str, Any],
    checkpoint: World,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Independently reconstruct predecessor regions and rebridge descendants."""

    start_offset = int(signal["start_offset"])
    rebridge_offset = int(signal["rebridge_offset"])
    if start_offset < 1 or rebridge_offset <= start_offset:
        raise RuntimeError(
            "Class B source lacks a replayable split/rebridge interval: "
            f"start={start_offset}, rebridge={rebridge_offset}"
        )

    continuation_seed = int(signal["continuation_seed"])
    world = clone_world(checkpoint, continuation_seed)
    before_split: World | None = None
    split: World | None = None
    rebridge: World | None = None
    with phase_source_patch(VARIANT):
        clamp_stored_phase(world, VARIANT)
        for offset in range(rebridge_offset + 1):
            if offset == start_offset - 1:
                before_split = clone_world(world, continuation_seed)
            if offset == start_offset:
                split = clone_world(world, continuation_seed)
            if offset == rebridge_offset:
                rebridge = clone_world(world, continuation_seed)
            if offset < rebridge_offset:
                iota_rig.step(world, cfg)
                clamp_stored_phase(world, VARIANT)

    if before_split is None or split is None or rebridge is None:
        raise RuntimeError("failed to capture all source reconstruction states")

    regions, original_bridge = reconstruct_regions(before_split, split)
    persistent_regions = [
        {coord for coord in region if bool(rebridge.active[coord])}
        for region in regions
    ]
    region_sizes = [len(region) for region in regions]
    persistent_sizes = [len(region) for region in persistent_regions]
    singleton_indices = [index for index, size in enumerate(region_sizes) if size == 1]
    singleton_index: int | None = (
        singleton_indices[0] if len(singleton_indices) == 1 else None
    )
    singleton_original: tuple[int, int, int] | None = None
    singleton_persistent_size = 0
    singleton_original_active = False
    if singleton_index is not None:
        singleton_original = next(iter(regions[singleton_index]))
        singleton_persistent_size = persistent_sizes[singleton_index]
        singleton_original_active = bool(rebridge.active[singleton_original])

    return {
        "original_bridge": original_bridge,
        "region_sizes": region_sizes,
        "persistent_sizes": persistent_sizes,
        "singleton_index": singleton_index,
        "singleton_original": singleton_original,
        "singleton_persistent_size": singleton_persistent_size,
        "singleton_original_active": singleton_original_active,
    }


def candidate_id(transport: dict[str, Any]) -> str:
    return (
        f"f067b-seed{int(transport['init_seed']):02d}-"
        f"sample{int(transport['sample_index']):02d}-"
        f"split{int(transport['start_offset']):03d}-"
        f"rebridge{int(transport['rebridge_offset']):03d}"
    )


def source_manifest_row(
    candidate_index: int,
    signal: dict[str, Any],
    transport: dict[str, Any],
    reconstruction: dict[str, Any],
) -> dict[str, Any]:
    strict_region_sizes = integer_series(transport["predecessor_region_sizes"])
    strict_persistent_sizes = integer_series(
        transport["persistent_predecessor_region_sizes"]
    )
    reconstructed_sizes = list(reconstruction["region_sizes"])
    reconstructed_persistent = list(reconstruction["persistent_sizes"])
    original_bridge = set(reconstruction["original_bridge"])
    original_bridge_match = (
        original_bridge == parse_coords(str(transport["original_bridge_cells"]))
        and original_bridge == parse_coords(str(signal["start_lost_bridge_coords"]))
    )
    region_metrics_match = (
        strict_region_sizes == reconstructed_sizes
        and strict_persistent_sizes == reconstructed_persistent
    )

    singleton_index = reconstruction["singleton_index"]
    gates = {
        "strict_transport": int(transport["constraint_transport"]) == 1,
        "two_predecessor_regions": (
            int(transport["predecessor_region_count"]) == 2
            and len(reconstructed_sizes) == 2
        ),
        "exactly_one_singleton_predecessor": (
            strict_region_sizes.count(1) == 1
            and reconstructed_sizes.count(1) == 1
        ),
        "persistent_singleton_size_one": (
            singleton_index is not None
            and int(reconstruction["singleton_persistent_size"]) == 1
            and bool(reconstruction["singleton_original_active"])
        ),
        "successor_role_critical": (
            int(transport["successor_bridge_role_critical"]) == 1
        ),
        "complete_displacement": float(transport["bridge_path_jaccard"]) == 0.0,
        "original_bridge_reconstruction": original_bridge_match,
        "strict_region_metrics_match_reconstruction": region_metrics_match,
    }
    eligible = all(gates.values())
    singleton_original = reconstruction["singleton_original"]
    failures = [name for name, passed in gates.items() if not passed]
    return {
        "candidate_index": int(candidate_index),
        "candidate_id": candidate_id(transport),
        "source_index": "",
        "source_id": "",
        "frozen_source_selected": 0,
        "selection_uses_intervention_outcomes": 0,
        "init_seed": int(transport["init_seed"]),
        "variant": str(transport["variant"]),
        "sample_index": int(transport["sample_index"]),
        "continuation_seed": int(transport["continuation_seed"]),
        "checkpoint_tick": CHECKPOINT_TICK,
        "start_offset": int(transport["start_offset"]),
        "rebridge_offset": int(transport["rebridge_offset"]),
        "source_state_offset": int(transport["rebridge_offset"]),
        "original_bridge_cells": str(transport["original_bridge_cells"]),
        "successor_bridge_cells": str(transport["successor_bridge_cells"]),
        "bridge_path_jaccard": float(transport["bridge_path_jaccard"]),
        "constraint_transport": int(transport["constraint_transport"]),
        "predecessor_region_count": int(transport["predecessor_region_count"]),
        "predecessor_region_sizes": str(transport["predecessor_region_sizes"]),
        "persistent_predecessor_region_sizes": str(
            transport["persistent_predecessor_region_sizes"]
        ),
        "successor_bridge_role_critical": int(
            transport["successor_bridge_role_critical"]
        ),
        "reconstruction_verified": 1,
        "original_bridge_reconstruction_match": csv_bool(original_bridge_match),
        "strict_region_metrics_match_reconstruction": csv_bool(region_metrics_match),
        "reconstructed_predecessor_region_sizes": ";".join(
            str(value) for value in reconstructed_sizes
        ),
        "reconstructed_persistent_region_sizes": ";".join(
            str(value) for value in reconstructed_persistent
        ),
        "singleton_region_index": "" if singleton_index is None else singleton_index,
        "singleton_original_address": (
            "" if singleton_original is None else coords_text({singleton_original})
        ),
        "singleton_persistent_size_at_rebridge": int(
            reconstruction["singleton_persistent_size"]
        ),
        "singleton_original_active_at_rebridge": csv_bool(
            bool(reconstruction["singleton_original_active"])
        ),
        "strict_transport_gate": csv_bool(gates["strict_transport"]),
        "two_predecessor_regions_gate": csv_bool(gates["two_predecessor_regions"]),
        "exactly_one_singleton_predecessor_gate": csv_bool(
            gates["exactly_one_singleton_predecessor"]
        ),
        "persistent_singleton_size_one_gate": csv_bool(
            gates["persistent_singleton_size_one"]
        ),
        "successor_role_critical_gate": csv_bool(gates["successor_role_critical"]),
        "complete_displacement_gate": csv_bool(gates["complete_displacement"]),
        "singleton_eligible": csv_bool(eligible),
        "eligibility_failures": ";".join(failures),
    }


def freeze_source_ids(rows: list[dict[str, Any]]) -> None:
    source_index = 0
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
    for row in selected:
        source_index += 1
        row["frozen_source_selected"] = 1
        row["source_index"] = source_index
        row["source_id"] = f"f067b-source-{source_index:03d}"


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
        "only_frozen_paths_changed": csv_bool(changed == ALLOWED_CONFIG_CHANGES),
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
        transports = [row for row in transport_rows if int(row["init_seed"]) == seed]
        sources = [row for row in source_rows if int(row["init_seed"]) == seed]
        output.append(
            {
                "init_seed": seed,
                "cases": len(cases),
                "unique_continuation_streams": len(
                    {int(row["continuation_seed"]) for row in cases}
                ),
                "signal_intervals": len(signals),
                "class_a_events": sum(row["event_class"] == "class_a" for row in signals),
                "class_b_events": sum(row["event_class"] == "class_b" for row in signals),
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
                    int(row["payload_zero_all_observed_offsets"]) for row in transports
                ),
                "ledger_exact_transport_events": sum(
                    int(row["ledger_exact_all_observed_offsets"]) for row in transports
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
    expected_cases = {(seed, sample) for seed in INIT_SEEDS for sample in SAMPLE_INDICES}
    observed_cases = {
        (int(row["init_seed"]), int(row["sample_index"])) for row in case_rows
    }
    if observed_cases != expected_cases or len(case_rows) != len(expected_cases):
        raise RuntimeError(
            f"incomplete Finding 067B case matrix: {len(observed_cases)}/{len(expected_cases)}"
        )
    continuation_seeds = [int(row["continuation_seed"]) for row in case_rows]
    if len(set(continuation_seeds)) != len(expected_cases):
        raise RuntimeError("Finding 067B continuation RNG streams are not globally unique")
    if {int(row["init_seed"]) for row in config_rows} != set(INIT_SEEDS):
        raise RuntimeError("Finding 067B config manifest does not cover every initialization seed")
    if not all(int(row["only_frozen_paths_changed"]) for row in config_rows):
        raise RuntimeError("a Finding 067B effective config changed a non-frozen path")
    class_b_signals = [row for row in signal_rows if row["event_class"] == "class_b"]
    if len(transport_rows) != len(class_b_signals):
        raise RuntimeError(
            "not every frozen Finding 059 Class B event received a Finding 060 audit"
        )
    if len(source_rows) != len(transport_rows):
        raise RuntimeError("source manifest is not complete over Finding 060 candidate audits")
    if not all(int(row["reconstruction_verified"]) for row in source_rows):
        raise RuntimeError("a source-manifest candidate lacks reconstruction verification")


def artifact_paths(prefix: Path) -> dict[str, Path]:
    return {
        "case_csv": prefix.with_name(prefix.name + "_cases.csv"),
        "signal_csv": prefix.with_name(prefix.name + "_signals.csv"),
        "transport_csv": prefix.with_name(prefix.name + "_transport_events.csv"),
        "source_manifest_csv": prefix.with_name(prefix.name + "_source_manifest.csv"),
        "seed_aggregate_csv": prefix.with_name(prefix.name + "_seed_aggregate.csv"),
        "config_manifest_csv": prefix.with_name(prefix.name + "_config_manifest.csv"),
        "summary_json": prefix.with_name(prefix.name + "_summary.json"),
    }


def run_seed_job(job: tuple[str, int]) -> dict[str, Any]:
    canonical_path = Path(job[0])
    seed = int(job[1])
    canonical = load_config(canonical_path)
    cfg = config_for_seed(canonical, seed)
    case_rows: list[dict[str, Any]] = []
    signal_rows: list[dict[str, Any]] = []
    transport_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    print(f"checkpoint seed={seed} variant={VARIANT} tick={CHECKPOINT_TICK}", flush=True)
    checkpoint = run_to_checkpoint(cfg, VARIANT, CHECKPOINT_TICK)
    for sample_index in SAMPLE_INDICES:
        case, signals = run_continuation_case(
            classification_args(seed), cfg, seed, VARIANT, checkpoint, sample_index
        )
        expected_seed = continuation_seed_for(seed, sample_index)
        if int(case["continuation_seed"]) != expected_seed:
            raise RuntimeError(
                f"continuation stream-key mismatch seed={seed} sample={sample_index}"
            )
        case_rows.append(case)
        signal_rows.extend(signals)
        print(
            f"screen seed={seed} sample={sample_index} "
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
        transport_rows.append(transport)
        source_rows.append(source_manifest_row(0, signal, transport, reconstruction))
        print(
            f"audit seed={seed} sample={signal['sample_index']} "
            f"split={signal['start_offset']} strict={transport['constraint_transport']} "
            f"singleton={source_rows[-1]['singleton_eligible']}",
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
        raise FileNotFoundError(f"canonical v036 config not found: {canonical_path}")
    canonical = load_config(canonical_path)
    if not str(canonical.get("simulation_version", "")).startswith("iota-rig-v0.3.6"):
        raise RuntimeError("Finding 067B requires the canonical v036 configuration")
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
        case_rows,
        signal_rows,
        transport_rows,
        source_rows,
        config_rows,
    )
    aggregates = seed_aggregate_rows(
        case_rows,
        signal_rows,
        transport_rows,
        source_rows,
    )
    paths = artifact_paths(Path(args.output_prefix))
    write_csv(paths["case_csv"], CASE_FIELDNAMES, case_rows)
    write_csv(paths["signal_csv"], SIGNAL_FIELDNAMES, signal_rows)
    write_csv(paths["transport_csv"], TRANSPORT_FIELDNAMES, transport_rows)
    write_csv(paths["source_manifest_csv"], SOURCE_MANIFEST_FIELDNAMES, source_rows)
    write_csv(paths["seed_aggregate_csv"], SEED_AGGREGATE_FIELDNAMES, aggregates)
    write_csv(paths["config_manifest_csv"], CONFIG_FIELDNAMES, config_rows)

    class_b_count = sum(row["event_class"] == "class_b" for row in signal_rows)
    strict_count = sum(int(row["constraint_transport"]) for row in transport_rows)
    eligible_count = sum(int(row["singleton_eligible"]) for row in source_rows)
    summary = {
        "finding": FINDING,
        "screen_complete": True,
        "protocol_frozen_before_intervention_outcomes": True,
        "intervention_outcomes_inspected_for_selection": False,
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
        "continuation_seed_formula": (
            "base + checkpoint_tick*1000000 + init_seed*100000 + sample_index"
        ),
        "classification": "frozen Finding 059 Class A/B signal classification",
        "transport_audit": "frozen Finding 060 strict constraint-transport analysis",
        "singleton_eligibility_rule": {
            "constraint_transport": True,
            "predecessor_region_count": 2,
            "exactly_one_predecessor_region_size": 1,
            "persistent_singleton_size_at_rebridge": 1,
            "successor_bridge_role_critical": True,
            "bridge_path_jaccard": 0.0,
            "reconstruction_match_required": True,
        },
        "cases": len(case_rows),
        "expected_cases": len(INIT_SEEDS) * len(SAMPLE_INDICES),
        "unique_continuation_streams": len(
            {int(row["continuation_seed"]) for row in case_rows}
        ),
        "signal_intervals": len(signal_rows),
        "class_b_candidates": class_b_count,
        "strict_transport_events": strict_count,
        "singleton_eligible_sources": eligible_count,
        "frozen_primary_sources": sum(
            int(row["frozen_source_selected"]) for row in source_rows
        ),
        "all_classification_payload_zero": all(
            int(row["payload_zero_all_offsets"]) for row in case_rows
        ),
        "all_classification_ledgers_exact": all(
            int(row["ledger_exact_all_offsets"]) for row in case_rows
        ),
        "all_transport_payload_zero": all(
            int(row["payload_zero_all_observed_offsets"]) for row in transport_rows
        ),
        "all_transport_ledgers_exact": all(
            int(row["ledger_exact_all_observed_offsets"]) for row in transport_rows
        ),
        "artifacts": {
            name: {
                "path": str(path),
                "sha256": artifact_hash(path),
            }
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
    return summary


def main() -> None:
    run_screen(parse_args())


if __name__ == "__main__":
    main()
