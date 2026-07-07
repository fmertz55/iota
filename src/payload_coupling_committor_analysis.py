from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from continuation import classify_outcome, clone_world
from experiment_db import artifact_hash
from iota_rig import World, init_world, load_config, save_world_state, step
from metrics import collect_metrics
from payload_coupling_bracket_4096_sweep import probe_config
from payload_coupling_divergence_trace import (
    HIGH_COUPLING,
    HIGH_LABEL,
    LOW_COUPLING,
    LOW_LABEL,
    trace_step,
)


MAX_TICKS = 4096
OUTPUT_DIR = Path("output/findings")
RAW_PATH = OUTPUT_DIR / "finding_020_committor_raw.csv"
SUMMARY_PATH = OUTPUT_DIR / "finding_020_committor_summary.csv"
JSON_PATH = OUTPUT_DIR / "finding_020_committor_summary.json"
STATE_DIR = OUTPUT_DIR / "finding_020_committor_states"
RAW_FIELDNAMES = [
    "seed",
    "law",
    "coupling",
    "condition",
    "forced_v",
    "sample_index",
    "continuation_seed",
    "divergence_tick",
    "target",
    "final_tick",
    "early_absorber_stop",
    "active_iotas",
    "largest_coherence",
    "coherence_ratio",
    "coherence_count",
    "largest_coherence_face6",
    "coherence_ratio_face6",
    "coherence_count_face6",
    "largest_coherence_face18",
    "coherence_ratio_face18",
    "coherence_count_face18",
    "largest_coherence_cube26",
    "coherence_ratio_cube26",
    "coherence_count_cube26",
    "component_size_1",
    "component_size_2",
    "component_size_3",
    "component_size_1_face18",
    "component_size_2_face18",
    "component_size_3_face18",
    "component_size_1_cube26",
    "component_size_2_cube26",
    "component_size_3_cube26",
    "top5_component_coverage",
    "top20_component_coverage",
    "component_size_entropy",
    "top5_component_coverage_face18",
    "top20_component_coverage_face18",
    "component_size_entropy_face18",
    "top5_component_coverage_cube26",
    "top20_component_coverage_cube26",
    "component_size_entropy_cube26",
    "classification",
    "classification_face6",
    "classification_face18",
    "classification_cube26",
    "forced_target_V",
    "final_state_path",
    "final_state_sha256",
    "final_state_bytes",
]


@dataclass(frozen=True)
class SeedEvent:
    seed: int
    divergence_tick: int
    target: tuple[int, int, int]
    protected_v: int
    absorber_v: int


SEED_EVENTS = {
    42: SeedEvent(
        seed=42,
        divergence_tick=337,
        target=(41, 43, 23),
        protected_v=0,
        absorber_v=31,
    ),
    56: SeedEvent(
        seed=56,
        divergence_tick=408,
        target=(42, 44, 24),
        protected_v=0,
        absorber_v=27,
    ),
}


def seed_config(base_cfg: dict[str, Any], seed: int, label: str, coupling: float) -> dict[str, Any]:
    cfg = probe_config(base_cfg, label, coupling)
    cfg["experiment"]["objective"] = "Committor analysis for vector-inheritance basin selection"
    cfg["experiment"]["variant"] = (
        "A_4774_256_cube26_2_nuclei_medium_payload_4_vs_0"
        f"_cross_{label}_seed_{seed}_committor"
    )
    cfg["experiment"]["seed_ensemble"] = "42_71"
    cfg["init"]["seed"] = seed
    return cfg


def checkpoint_world(cfg: dict[str, Any], event: SeedEvent) -> World:
    world = init_world(cfg)
    for tick in range(1, event.divergence_tick + 1):
        trace_step(world, cfg, tick)
    return world


def classify(metric: dict[str, Any], connectivity: str = "face6") -> str:
    return classify_outcome(metric, connectivity)


def run_continuation(
    checkpoint: World,
    cfg: dict[str, Any],
    event: SeedEvent,
    forced_v: int,
    continuation_seed: int,
    early_absorber: bool,
    progress_label: str,
    final_state_path: Path | None = None,
    final_state_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    world = clone_world(checkpoint, continuation_seed)
    world.V[event.target] = np.uint8(forced_v)

    metric: dict[str, Any] | None = None
    final_tick = MAX_TICKS
    for tick in range(event.divergence_tick + 1, MAX_TICKS + 1):
        step(world, cfg)
        if tick % 256 == 0:
            active_count = int(world.active.sum())
            print(f"{progress_label} tick={tick} active={active_count}")
            if early_absorber and active_count >= 1000:
                metric = collect_metrics(world, tick)
                if metric["coherence_ratio"] >= 0.95:
                    final_tick = tick
                    break

    if metric is None:
        metric = collect_metrics(world, final_tick)
    state_sha256 = ""
    state_bytes = ""
    state_path = ""
    if final_state_path is not None:
        save_world_state(
            world,
            final_state_path,
            {
                **(final_state_metadata or {}),
                "final_tick": final_tick,
                "early_absorber_stop": final_tick < MAX_TICKS,
            },
        )
        state_sha256 = artifact_hash(final_state_path)
        state_bytes = str(final_state_path.stat().st_size)
        state_path = final_state_path.as_posix()
    return {
        "final_tick": final_tick,
        "early_absorber_stop": final_tick < MAX_TICKS,
        "active_iotas": metric["active_iotas"],
        "largest_coherence": metric["largest_coherence"],
        "coherence_ratio": metric["coherence_ratio"],
        "coherence_count": metric["coherence_count"],
        "largest_coherence_face6": metric["largest_coherence_face6"],
        "coherence_ratio_face6": metric["coherence_ratio_face6"],
        "coherence_count_face6": metric["coherence_count_face6"],
        "largest_coherence_face18": metric["largest_coherence_face18"],
        "coherence_ratio_face18": metric["coherence_ratio_face18"],
        "coherence_count_face18": metric["coherence_count_face18"],
        "largest_coherence_cube26": metric["largest_coherence_cube26"],
        "coherence_ratio_cube26": metric["coherence_ratio_cube26"],
        "coherence_count_cube26": metric["coherence_count_cube26"],
        "component_size_1": metric["component_size_1"],
        "component_size_2": metric["component_size_2"],
        "component_size_3": metric["component_size_3"],
        "component_size_1_face18": metric["component_size_1_face18"],
        "component_size_2_face18": metric["component_size_2_face18"],
        "component_size_3_face18": metric["component_size_3_face18"],
        "component_size_1_cube26": metric["component_size_1_cube26"],
        "component_size_2_cube26": metric["component_size_2_cube26"],
        "component_size_3_cube26": metric["component_size_3_cube26"],
        "top5_component_coverage": metric["top5_component_coverage"],
        "top20_component_coverage": metric["top20_component_coverage"],
        "component_size_entropy": metric["component_size_entropy"],
        "top5_component_coverage_face18": metric["top5_component_coverage_face18"],
        "top20_component_coverage_face18": metric["top20_component_coverage_face18"],
        "component_size_entropy_face18": metric["component_size_entropy_face18"],
        "top5_component_coverage_cube26": metric["top5_component_coverage_cube26"],
        "top20_component_coverage_cube26": metric["top20_component_coverage_cube26"],
        "component_size_entropy_cube26": metric["component_size_entropy_cube26"],
        "classification": classify(metric),
        "classification_face6": classify(metric, "face6"),
        "classification_face18": classify(metric, "face18"),
        "classification_cube26": classify(metric, "cube26"),
        "forced_target_V": int(world.V[event.target]),
        "final_state_path": state_path,
        "final_state_sha256": state_sha256,
        "final_state_bytes": state_bytes,
    }


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, str, int], list[dict[str, Any]]] = {}
    for row in rows:
        key = (int(row["seed"]), str(row["law"]), int(row["forced_v"]))
        groups.setdefault(key, []).append(row)

    def numeric_values(group: list[dict[str, Any]], key: str) -> list[float]:
        values = []
        for row in group:
            value = row.get(key)
            if value in (None, ""):
                continue
            values.append(float(value))
        return values

    def mean_or_blank(group: list[dict[str, Any]], key: str) -> float | str:
        values = numeric_values(group, key)
        return sum(values) / len(values) if values else ""

    def classification_counts(group: list[dict[str, Any]], key: str) -> tuple[int, int, int, int]:
        classified = [str(row[key]) for row in group if row.get(key) not in (None, "")]
        return (
            len(classified),
            sum(value == "absorber" for value in classified),
            sum(value == "high_dominant" for value in classified),
            sum(value == "protected" for value in classified),
        )

    summary_rows = []
    for (seed, law, forced_v), group in sorted(groups.items()):
        samples = len(group)
        _, absorber_count, high_dominant_count, protected_count = classification_counts(
            group,
            "classification",
        )
        row = {
            "seed": seed,
            "law": law,
            "forced_v": forced_v,
            "samples": samples,
            "absorber_count": absorber_count,
            "absorber_probability": absorber_count / samples,
            "high_dominant_count": high_dominant_count,
            "high_dominant_probability": high_dominant_count / samples,
            "protected_count": protected_count,
            "protected_probability": protected_count / samples,
            "mean_active_iotas": sum(float(row["active_iotas"]) for row in group) / samples,
            "mean_coherence_ratio": sum(float(row["coherence_ratio"]) for row in group) / samples,
            "rows_with_final_state": sum(bool(row.get("final_state_path")) for row in group),
        }
        for connectivity in ("face6", "face18", "cube26"):
            key = f"classification_{connectivity}"
            classified, absorbers, high_dominant, protected = classification_counts(group, key)
            row.update(
                {
                    f"samples_{connectivity}": classified,
                    f"absorber_count_{connectivity}": absorbers,
                    f"absorber_probability_{connectivity}": absorbers / classified if classified else "",
                    f"high_dominant_count_{connectivity}": high_dominant,
                    f"high_dominant_probability_{connectivity}": (
                        high_dominant / classified if classified else ""
                    ),
                    f"protected_count_{connectivity}": protected,
                    f"protected_probability_{connectivity}": protected / classified if classified else "",
                    f"mean_coherence_ratio_{connectivity}": mean_or_blank(
                        group,
                        f"coherence_ratio_{connectivity}",
                    ),
                }
            )
        summary_rows.append(row)
    return summary_rows


def row_key(row: dict[str, Any]) -> tuple[int, str, str, int, int]:
    return (
        int(row["seed"]),
        str(row["law"]),
        str(row["condition"]),
        int(row["sample_index"]),
        int(row["continuation_seed"]),
    )


def state_path_for(
    seed: int,
    law: str,
    condition: str,
    sample_index: int,
    continuation_seed: int,
) -> Path:
    filename = (
        f"seed_{seed}_{law}_{condition}_"
        f"sample_{sample_index:03d}_rng_{continuation_seed}.npz"
    )
    return STATE_DIR / filename


def row_has_durable_outputs(row: dict[str, Any]) -> bool:
    return all(
        row.get(key) not in (None, "")
        for key in (
            "coherence_ratio_face6",
            "coherence_ratio_face18",
            "coherence_ratio_cube26",
            "classification_face6",
            "classification_face18",
            "classification_cube26",
            "final_state_path",
            "final_state_sha256",
            "final_state_bytes",
        )
    )


def load_existing_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row.setdefault("largest_coherence_face6", row.get("largest_coherence", ""))
        row.setdefault("coherence_ratio_face6", row.get("coherence_ratio", ""))
        row.setdefault("coherence_count_face6", row.get("coherence_count", ""))
        row.setdefault("classification_face6", row.get("classification", ""))
    return rows


def write_raw_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=RAW_FIELDNAMES,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in RAW_FIELDNAMES})
        handle.flush()
        os.fsync(handle.fileno())


def append_raw_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=RAW_FIELDNAMES,
            extrasaction="ignore",
            lineterminator="\n",
        )
        if needs_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in RAW_FIELDNAMES})
        handle.flush()
        os.fsync(handle.fileno())


def write_current_summary(
    rows: list[dict[str, Any]],
    args: argparse.Namespace,
    raw_path: Path,
    summary_path: Path,
    json_path: Path,
) -> None:
    if not rows:
        return
    summary_rows = summarize(rows)
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(summary_rows[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(summary_rows)
        handle.flush()
        os.fsync(handle.fileno())

    law_order = {"low": 0, "high": 1}
    condition_order = {"protected_vector": 0, "absorber_vector": 1}
    summary = {
        "summary_scope": "all_loaded_rows",
        "samples_per_condition_requested": args.samples,
        "samples_completed": len(rows),
        "seeds": sorted({int(row["seed"]) for row in rows}),
        "laws": sorted({str(row["law"]) for row in rows}, key=lambda value: law_order.get(value, 99)),
        "conditions": sorted(
            {str(row["condition"]) for row in rows},
            key=lambda value: condition_order.get(value, 99),
        ),
        "sample_indexes": sorted({int(row["sample_index"]) for row in rows}),
        "last_run_filter": {
            "seeds": args.seeds,
            "laws": args.laws,
            "conditions": args.conditions,
            "sample_indexes": args.sample_indexes,
        },
        "max_ticks": MAX_TICKS,
        "early_absorber": args.early_absorber,
        "raw_path": str(raw_path),
        "summary_path": str(summary_path),
        "summary_rows": summary_rows,
    }
    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 56])
    parser.add_argument("--laws", choices=["low", "high"], nargs="+", default=["low", "high"])
    parser.add_argument(
        "--conditions",
        choices=["protected_vector", "absorber_vector"],
        nargs="+",
        default=["protected_vector", "absorber_vector"],
    )
    parser.add_argument(
        "--sample-indexes",
        type=int,
        nargs="+",
        default=None,
        help="Specific zero-based sample indexes to run or refresh. Defaults to range(samples).",
    )
    parser.add_argument("--rng-seed-base", type=int, default=20260622)
    parser.add_argument("--early-absorber", action="store_true")
    parser.add_argument(
        "--refresh-missing",
        action="store_true",
        help="Rerun existing rows that lack multi-connectivity metrics or final-state artifacts.",
    )
    parser.add_argument(
        "--no-save-final-states",
        action="store_true",
        help="Do not write final-state .npz artifacts. Not recommended for finding runs.",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Ignore existing committor CSV rows and start a fresh output file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base_cfg = load_config("config.yaml")
    if args.restart:
        RAW_PATH.unlink(missing_ok=True)
        SUMMARY_PATH.unlink(missing_ok=True)
        JSON_PATH.unlink(missing_ok=True)
        if STATE_DIR.exists():
            shutil.rmtree(STATE_DIR)
        rows: list[dict[str, Any]] = []
    else:
        rows = load_existing_rows(RAW_PATH)
        if rows:
            print(f"resuming from {RAW_PATH}: completed_rows={len(rows)}")
            write_raw_rows(RAW_PATH, rows)
            write_current_summary(rows, args, RAW_PATH, SUMMARY_PATH, JSON_PATH)
    completed = {row_key(row) for row in rows}
    row_indexes = {row_key(row): index for index, row in enumerate(rows)}
    laws = [
        (0, "low", LOW_LABEL, LOW_COUPLING),
        (1, "high", HIGH_LABEL, HIGH_COUPLING),
    ]
    laws = [entry for entry in laws if entry[1] in set(args.laws)]
    sample_indexes = args.sample_indexes if args.sample_indexes is not None else list(range(args.samples))
    invalid_sample_indexes = [index for index in sample_indexes if index < 0 or index >= args.samples]
    if invalid_sample_indexes:
        raise SystemExit(
            f"sample indexes must be within [0, {args.samples - 1}], got {invalid_sample_indexes}"
        )

    for seed in args.seeds:
        event = SEED_EVENTS[seed]
        for law_index, law, label, coupling in laws:
            cfg = seed_config(base_cfg, seed, label, coupling)
            print(f"building checkpoint seed={seed} law={law}")
            checkpoint = checkpoint_world(cfg, event)
            conditions = [
                ("protected_vector", event.protected_v),
                ("absorber_vector", event.absorber_v),
            ]
            conditions = [
                entry
                for entry in conditions
                if entry[0] in set(args.conditions)
            ]
            for condition, forced_v in conditions:
                condition_index = 0 if condition == "protected_vector" else 1
                for sample_index in sample_indexes:
                    continuation_seed = (
                        args.rng_seed_base
                        + seed * 1_000_000
                        + law_index * 100_000
                        + condition_index * 10_000
                        + sample_index
                    )
                    key = (seed, law, condition, sample_index, continuation_seed)
                    existing_row = rows[row_indexes[key]] if key in row_indexes else None
                    should_refresh = (
                        args.refresh_missing
                        and existing_row is not None
                        and not row_has_durable_outputs(existing_row)
                    )
                    if key in completed and not should_refresh:
                        print(
                            f"skipping completed seed={seed} law={law} "
                            f"condition={condition} sample={sample_index + 1}/{args.samples}"
                        )
                        continue
                    progress_label = (
                        f"seed={seed} law={law} condition={condition} "
                        f"sample={sample_index + 1}/{args.samples}"
                    )
                    print(f"{'refreshing' if should_refresh else 'starting'} {progress_label}")
                    final_state_path = None
                    if not args.no_save_final_states:
                        final_state_path = state_path_for(
                            seed,
                            law,
                            condition,
                            sample_index,
                            continuation_seed,
                        )
                    row = {
                        "seed": seed,
                        "law": law,
                        "coupling": coupling,
                        "condition": condition,
                        "forced_v": forced_v,
                        "sample_index": sample_index,
                        "continuation_seed": continuation_seed,
                        "divergence_tick": event.divergence_tick,
                        "target": event.target,
                    }
                    result = run_continuation(
                        checkpoint,
                        cfg,
                        event,
                        forced_v,
                        continuation_seed,
                        args.early_absorber,
                        progress_label,
                        final_state_path,
                        row,
                    )
                    row.update(result)
                    if key in row_indexes:
                        rows[row_indexes[key]] = row
                        write_raw_rows(RAW_PATH, rows)
                    else:
                        rows.append(row)
                        row_indexes[key] = len(rows) - 1
                        completed.add(key)
                        append_raw_row(RAW_PATH, row)
                    write_current_summary(rows, args, RAW_PATH, SUMMARY_PATH, JSON_PATH)
                    print(
                        f"seed={seed} law={law} condition={condition} "
                        f"sample={sample_index + 1}/{args.samples} "
                        f"class_face6={row['classification_face6']} "
                        f"class_cube26={row['classification_cube26']} "
                        f"active={row['active_iotas']} "
                        f"lcf6={float(row['coherence_ratio_face6']):.3f} "
                        f"lcf26={float(row['coherence_ratio_cube26']):.3f}"
                    )

    write_current_summary(rows, args, RAW_PATH, SUMMARY_PATH, JSON_PATH)
    print(JSON_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
