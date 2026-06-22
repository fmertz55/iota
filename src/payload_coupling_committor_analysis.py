from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from iota_rig import World, init_world, load_config, step
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


def clone_world(world: World, rng_seed: int) -> World:
    return World(
        active=world.active.copy(),
        A=world.A.copy(),
        R=world.R.copy(),
        V=world.V.copy(),
        P=world.P.copy(),
        previous_active=world.previous_active.copy(),
        previous_V=world.previous_V.copy(),
        vectors=world.vectors.copy(),
        vector_behaviors=tuple(world.vector_behaviors),
        wrap=world.wrap,
        rng=np.random.default_rng(rng_seed),
    )


def checkpoint_world(cfg: dict[str, Any], event: SeedEvent) -> World:
    world = init_world(cfg)
    for tick in range(1, event.divergence_tick + 1):
        trace_step(world, cfg, tick)
    return world


def classify(metric: dict[str, Any]) -> str:
    if metric["active_iotas"] >= 1000 and metric["coherence_ratio"] >= 0.95:
        return "absorber"
    if metric["active_iotas"] >= 1000 and metric["coherence_ratio"] >= 0.90:
        return "high_dominant"
    return "protected"


def run_continuation(
    checkpoint: World,
    cfg: dict[str, Any],
    event: SeedEvent,
    forced_v: int,
    continuation_seed: int,
    early_absorber: bool,
    progress_label: str,
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
    return {
        "final_tick": final_tick,
        "early_absorber_stop": final_tick < MAX_TICKS,
        "active_iotas": metric["active_iotas"],
        "largest_coherence": metric["largest_coherence"],
        "coherence_ratio": metric["coherence_ratio"],
        "coherence_count": metric["coherence_count"],
        "component_size_1": metric["component_size_1"],
        "component_size_2": metric["component_size_2"],
        "component_size_3": metric["component_size_3"],
        "top5_component_coverage": metric["top5_component_coverage"],
        "top20_component_coverage": metric["top20_component_coverage"],
        "component_size_entropy": metric["component_size_entropy"],
        "classification": classify(metric),
        "forced_target_V": int(world.V[event.target]),
    }


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, str, int], list[dict[str, Any]]] = {}
    for row in rows:
        key = (int(row["seed"]), str(row["law"]), int(row["forced_v"]))
        groups.setdefault(key, []).append(row)

    summary_rows = []
    for (seed, law, forced_v), group in sorted(groups.items()):
        absorber_count = sum(row["classification"] == "absorber" for row in group)
        high_dominant_count = sum(row["classification"] == "high_dominant" for row in group)
        protected_count = sum(row["classification"] == "protected" for row in group)
        summary_rows.append(
            {
                "seed": seed,
                "law": law,
                "forced_v": forced_v,
                "samples": len(group),
                "absorber_count": absorber_count,
                "absorber_probability": absorber_count / len(group),
                "high_dominant_count": high_dominant_count,
                "high_dominant_probability": high_dominant_count / len(group),
                "protected_count": protected_count,
                "protected_probability": protected_count / len(group),
                "mean_active_iotas": sum(float(row["active_iotas"]) for row in group) / len(group),
                "mean_coherence_ratio": sum(float(row["coherence_ratio"]) for row in group) / len(group),
            }
        )
    return summary_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 56])
    parser.add_argument("--rng-seed-base", type=int, default=20260622)
    parser.add_argument("--early-absorber", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base_cfg = load_config("config.yaml")
    rows: list[dict[str, Any]] = []
    laws = [
        ("low", LOW_LABEL, LOW_COUPLING),
        ("high", HIGH_LABEL, HIGH_COUPLING),
    ]

    for seed in args.seeds:
        event = SEED_EVENTS[seed]
        for law_index, (law, label, coupling) in enumerate(laws):
            cfg = seed_config(base_cfg, seed, label, coupling)
            print(f"building checkpoint seed={seed} law={law}")
            checkpoint = checkpoint_world(cfg, event)
            conditions = [
                ("protected_vector", event.protected_v),
                ("absorber_vector", event.absorber_v),
            ]
            for condition_index, (condition, forced_v) in enumerate(conditions):
                for sample_index in range(args.samples):
                    continuation_seed = (
                        args.rng_seed_base
                        + seed * 1_000_000
                        + law_index * 100_000
                        + condition_index * 10_000
                        + sample_index
                    )
                    progress_label = (
                        f"seed={seed} law={law} condition={condition} "
                        f"sample={sample_index + 1}/{args.samples}"
                    )
                    print(f"starting {progress_label}")
                    result = run_continuation(
                        checkpoint,
                        cfg,
                        event,
                        forced_v,
                        continuation_seed,
                        args.early_absorber,
                        progress_label,
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
                    row.update(result)
                    rows.append(row)
                    print(
                        f"seed={seed} law={law} condition={condition} "
                        f"sample={sample_index + 1}/{args.samples} "
                        f"class={row['classification']} "
                        f"active={row['active_iotas']} lcf={row['coherence_ratio']:.3f}"
                    )

    raw_path = OUTPUT_DIR / "finding_020_committor_raw.csv"
    with raw_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = summarize(rows)
    summary_path = OUTPUT_DIR / "finding_020_committor_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    summary = {
        "samples_per_condition": args.samples,
        "seeds": args.seeds,
        "max_ticks": MAX_TICKS,
        "early_absorber": args.early_absorber,
        "raw_path": str(raw_path),
        "summary_path": str(summary_path),
        "summary_rows": summary_rows,
    }
    json_path = OUTPUT_DIR / "finding_020_committor_summary.json"
    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
