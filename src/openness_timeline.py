from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, deque
from pathlib import Path
from typing import Any

import numpy as np

from continuation import (
    OUTCOME_CLASSES,
    classify_outcome,
    clone_world,
    connectivity_metric,
    entropy_from_counts,
    normalized_outcome_entropy,
    outcome_counts,
)
from experiment_db import artifact_hash, config_hash
from iota_rig import (
    World,
    candidate_neighbor_steps,
    init_world,
    load_config,
    save_world_state,
    step,
)
from metrics import collect_metrics


DEFAULT_PREFIX = "finding_022_openness_timeline"
RAW_FIELDNAMES = [
    "checkpoint_tick",
    "sample_index",
    "continuation_seed",
    "horizon",
    "final_tick",
    "final_offset",
    "early_absorber_stop",
    "active_iotas",
    "largest_coherence_face6",
    "coherence_ratio_face6",
    "coherence_count_face6",
    "largest_coherence_face18",
    "coherence_ratio_face18",
    "coherence_count_face18",
    "largest_coherence_cube26",
    "coherence_ratio_cube26",
    "coherence_count_cube26",
    "component_size_entropy_face6",
    "component_size_entropy_face18",
    "component_size_entropy_cube26",
    "classification_face6",
    "classification_face18",
    "classification_cube26",
    "classification",
]
SUMMARY_FIELDNAMES = [
    "checkpoint_tick",
    "samples",
    "classification_connectivity",
    "absorber_count",
    "high_dominant_count",
    "protected_count",
    "outcome_entropy",
    "openness",
    "effective_classes",
    "constraint_accumulation_rate",
    "committed",
    "base_active_iotas",
    "base_lcf",
    "base_classification",
    "mean_active_iotas",
    "std_active_iotas",
    "mean_lcf",
    "std_lcf",
    "persistence_tick",
    "component_persistence",
    "complexity_score",
    "checkpoint_state_path",
    "checkpoint_state_sha256",
    "checkpoint_state_bytes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate openness O(t) from resampled continuations of scheduled checkpoints."
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output-dir", default="output/findings")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    parser.add_argument("--ticks", type=int, default=None)
    parser.add_argument("--checkpoint-every", type=int, default=256)
    parser.add_argument("--checkpoint-ticks", type=int, nargs="+", default=None)
    parser.add_argument("--horizon", type=int, default=1024)
    parser.add_argument("--samples", type=int, default=24)
    parser.add_argument("--rng-seed-base", type=int, default=20260707)
    parser.add_argument("--connectivity", choices=["face6", "face18", "cube26"], default="cube26")
    parser.add_argument("--metric-every", type=int, default=256)
    parser.add_argument("--early-absorber", action="store_true")
    parser.add_argument("--min-active", type=int, default=1000)
    parser.add_argument("--absorber-lcf", type=float, default=0.95)
    parser.add_argument("--high-dominant-lcf", type=float, default=0.90)
    parser.add_argument("--commitment-epsilon", type=float, default=0.05)
    parser.add_argument("--persistence-top-k", type=int, default=5)
    parser.add_argument("--persistence-min-size", type=int, default=1)
    parser.add_argument("--persistence-window", type=int, default=None)
    parser.add_argument("--persistence-overlap", type=float, default=0.5)
    parser.add_argument("--no-save-checkpoints", action="store_true")
    return parser.parse_args()


def checkpoint_schedule(args: argparse.Namespace, cfg: dict[str, Any]) -> list[int]:
    ticks = int(args.ticks if args.ticks is not None else cfg["run"].get("ticks", 4096))
    if args.checkpoint_ticks is not None:
        values = sorted({int(value) for value in args.checkpoint_ticks})
        invalid = [value for value in values if value < 0 or value > ticks]
        if invalid:
            raise SystemExit(f"checkpoint ticks must be within [0, {ticks}], got {invalid}")
        return values
    if args.checkpoint_every <= 0:
        raise SystemExit("--checkpoint-every must be positive")
    values = list(range(0, ticks + 1, int(args.checkpoint_every)))
    if values[-1] != ticks:
        values.append(ticks)
    return values


def component_sets(
    world: World,
    connectivity: str,
    top_k: int | None = None,
    min_size: int = 1,
) -> list[frozenset[tuple[int, int, int]]]:
    active_coords = {tuple(int(value) for value in coord) for coord in np.argwhere(world.active)}
    neighbors = tuple(
        (int(dx), int(dy), int(dz))
        for dx, dy, dz in candidate_neighbor_steps(connectivity)
    )
    components: list[frozenset[tuple[int, int, int]]] = []
    while active_coords:
        start = active_coords.pop()
        coords = [start]
        queue: deque[tuple[int, int, int]] = deque([start])
        while queue:
            x, y, z = queue.popleft()
            for dx, dy, dz in neighbors:
                nx, ny, nz = x + dx, y + dy, z + dz
                if world.wrap:
                    nx %= world.size
                    ny %= world.size
                    nz %= world.size
                elif not (0 <= nx < world.size and 0 <= ny < world.size and 0 <= nz < world.size):
                    continue
                neighbor = (nx, ny, nz)
                if neighbor not in active_coords:
                    continue
                active_coords.remove(neighbor)
                coords.append(neighbor)
                queue.append(neighbor)
        if len(coords) >= min_size:
            components.append(frozenset(coords))
    components.sort(key=len, reverse=True)
    return components if top_k is None else components[:top_k]


def persistence_fraction(
    current_components: list[frozenset[tuple[int, int, int]]],
    future_components: list[frozenset[tuple[int, int, int]]],
    min_overlap_fraction: float,
) -> float | str:
    if not current_components:
        return 0.0
    future_labels: dict[tuple[int, int, int], int] = {}
    for index, component in enumerate(future_components):
        for coord in component:
            future_labels[coord] = index
    surviving = 0
    for component in current_components:
        label_counts: Counter[int] = Counter()
        for coord in component:
            label = future_labels.get(coord)
            if label is not None:
                label_counts[label] += 1
        best_overlap = max(label_counts.values(), default=0) / len(component)
        if best_overlap >= min_overlap_fraction:
            surviving += 1
    return float(surviving / len(current_components))


def continuation_seed(args: argparse.Namespace, checkpoint_tick: int, sample_index: int) -> int:
    return int(args.rng_seed_base + checkpoint_tick * 1_000_000 + sample_index)


def run_continuation(
    checkpoint: World,
    cfg: dict[str, Any],
    checkpoint_tick: int,
    sample_index: int,
    seed: int,
    args: argparse.Namespace,
) -> dict[str, Any]:
    world = clone_world(checkpoint, seed)
    metric: dict[str, Any] = collect_metrics(world, checkpoint_tick)
    final_tick = checkpoint_tick
    early_stop = False
    metric_every = max(1, int(args.metric_every))

    for offset in range(1, int(args.horizon) + 1):
        step(world, cfg)
        tick = checkpoint_tick + offset
        should_measure = offset % metric_every == 0 or offset == int(args.horizon)
        if not should_measure:
            continue
        metric = collect_metrics(world, tick)
        final_tick = tick
        if args.early_absorber:
            outcome = classify_outcome(
                metric,
                args.connectivity,
                args.min_active,
                args.absorber_lcf,
                args.high_dominant_lcf,
            )
            if outcome == "absorber":
                early_stop = True
                break

    classification_by_connectivity = {
        connectivity: classify_outcome(
            metric,
            connectivity,
            args.min_active,
            args.absorber_lcf,
            args.high_dominant_lcf,
        )
        for connectivity in ("face6", "face18", "cube26")
    }
    return {
        "checkpoint_tick": checkpoint_tick,
        "sample_index": sample_index,
        "continuation_seed": seed,
        "horizon": int(args.horizon),
        "final_tick": final_tick,
        "final_offset": final_tick - checkpoint_tick,
        "early_absorber_stop": early_stop,
        "active_iotas": int(metric["active_iotas"]),
        "largest_coherence_face6": int(metric["largest_coherence_face6"]),
        "coherence_ratio_face6": float(metric["coherence_ratio_face6"]),
        "coherence_count_face6": int(metric["coherence_count_face6"]),
        "largest_coherence_face18": int(metric["largest_coherence_face18"]),
        "coherence_ratio_face18": float(metric["coherence_ratio_face18"]),
        "coherence_count_face18": int(metric["coherence_count_face18"]),
        "largest_coherence_cube26": int(metric["largest_coherence_cube26"]),
        "coherence_ratio_cube26": float(metric["coherence_ratio_cube26"]),
        "coherence_count_cube26": int(metric["coherence_count_cube26"]),
        "component_size_entropy_face6": float(metric["component_size_entropy_face6"]),
        "component_size_entropy_face18": float(metric["component_size_entropy_face18"]),
        "component_size_entropy_cube26": float(metric["component_size_entropy_cube26"]),
        "classification_face6": classification_by_connectivity["face6"],
        "classification_face18": classification_by_connectivity["face18"],
        "classification_cube26": classification_by_connectivity["cube26"],
        "classification": classification_by_connectivity[args.connectivity],
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def summarize_checkpoint(
    checkpoint_tick: int,
    base_metric: dict[str, Any],
    rows: list[dict[str, Any]],
    state_artifact: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    counts = outcome_counts(rows, "classification")
    entropy = entropy_from_counts(counts)
    openness = normalized_outcome_entropy(counts)
    active_values = np.array([float(row["active_iotas"]) for row in rows], dtype=np.float64)
    lcf_key = f"coherence_ratio_{args.connectivity}"
    lcf_values = np.array([float(row[lcf_key]) for row in rows], dtype=np.float64)
    return {
        "checkpoint_tick": checkpoint_tick,
        "samples": len(rows),
        "classification_connectivity": args.connectivity,
        "absorber_count": counts["absorber"],
        "high_dominant_count": counts["high_dominant"],
        "protected_count": counts["protected"],
        "outcome_entropy": entropy,
        "openness": openness,
        "effective_classes": float(np.exp(entropy)) if rows else 0.0,
        "constraint_accumulation_rate": "",
        "committed": openness < float(args.commitment_epsilon),
        "base_active_iotas": int(base_metric["active_iotas"]),
        "base_lcf": connectivity_metric(base_metric, "coherence_ratio", args.connectivity),
        "base_classification": classify_outcome(
            base_metric,
            args.connectivity,
            args.min_active,
            args.absorber_lcf,
            args.high_dominant_lcf,
        ),
        "mean_active_iotas": float(np.mean(active_values)) if len(active_values) else 0.0,
        "std_active_iotas": float(np.std(active_values)) if len(active_values) else 0.0,
        "mean_lcf": float(np.mean(lcf_values)) if len(lcf_values) else 0.0,
        "std_lcf": float(np.std(lcf_values)) if len(lcf_values) else 0.0,
        "persistence_tick": "",
        "component_persistence": "",
        "complexity_score": "",
        **state_artifact,
    }


def checkpoint_artifact(
    world: World,
    path: Path | None,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    if path is None:
        return {
            "checkpoint_state_path": "",
            "checkpoint_state_sha256": "",
            "checkpoint_state_bytes": "",
        }
    save_world_state(world, path, metadata)
    return {
        "checkpoint_state_path": path.as_posix(),
        "checkpoint_state_sha256": artifact_hash(path),
        "checkpoint_state_bytes": str(path.stat().st_size),
    }


def apply_persistence(
    summary_rows: list[dict[str, Any]],
    top_components_by_tick: dict[int, list[frozenset[tuple[int, int, int]]]],
    all_components_by_tick: dict[int, list[frozenset[tuple[int, int, int]]]],
    checkpoint_ticks: list[int],
    args: argparse.Namespace,
) -> None:
    window = int(args.persistence_window or args.checkpoint_every)
    for row in summary_rows:
        tick = int(row["checkpoint_tick"])
        future_tick = next((value for value in checkpoint_ticks if value >= tick + window), None)
        if future_tick is None:
            continue
        persistence = persistence_fraction(
            top_components_by_tick.get(tick, []),
            all_components_by_tick.get(future_tick, []),
            float(args.persistence_overlap),
        )
        row["persistence_tick"] = future_tick
        row["component_persistence"] = persistence
        row["complexity_score"] = float(persistence) * float(row["openness"])


def apply_constraint_rates(summary_rows: list[dict[str, Any]]) -> None:
    previous: dict[str, Any] | None = None
    for row in summary_rows:
        if previous is not None:
            dt = int(row["checkpoint_tick"]) - int(previous["checkpoint_tick"])
            if dt > 0:
                row["constraint_accumulation_rate"] = (
                    float(previous["openness"]) - float(row["openness"])
                ) / dt
        previous = row


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    checkpoint_ticks = checkpoint_schedule(args, cfg)
    max_tick = max(checkpoint_ticks)
    output_dir = Path(args.output_dir)
    raw_path = output_dir / f"{args.prefix}_raw.csv"
    summary_path = output_dir / f"{args.prefix}_summary.csv"
    json_path = output_dir / f"{args.prefix}_summary.json"
    state_dir = output_dir / f"{args.prefix}_states"

    world = init_world(cfg)
    raw_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    top_components_by_tick: dict[int, list[frozenset[tuple[int, int, int]]]] = {}
    all_components_by_tick: dict[int, list[frozenset[tuple[int, int, int]]]] = {}

    checkpoint_set = set(checkpoint_ticks)
    for tick in range(0, max_tick + 1):
        if tick in checkpoint_set:
            print(f"checkpoint tick={tick} active={int(world.active.sum())}")
            base_metric = collect_metrics(world, tick)
            top_components_by_tick[tick] = component_sets(
                world,
                args.connectivity,
                top_k=int(args.persistence_top_k),
                min_size=int(args.persistence_min_size),
            )
            all_components_by_tick[tick] = component_sets(
                world,
                args.connectivity,
                top_k=None,
                min_size=1,
            )
            state_path = None
            if not args.no_save_checkpoints:
                state_path = state_dir / f"checkpoint_tick_{tick:06d}.npz"
            state_artifact = checkpoint_artifact(
                world,
                state_path,
                {
                    "checkpoint_tick": tick,
                    "config_hash": config_hash(cfg),
                    "samples": args.samples,
                    "horizon": args.horizon,
                    "connectivity": args.connectivity,
                },
            )
            checkpoint_rows = []
            for sample_index in range(int(args.samples)):
                seed = continuation_seed(args, tick, sample_index)
                row = run_continuation(world, cfg, tick, sample_index, seed, args)
                raw_rows.append(row)
                checkpoint_rows.append(row)
                print(
                    f"checkpoint={tick} sample={sample_index + 1}/{args.samples} "
                    f"class={row['classification']} active={row['active_iotas']} "
                    f"lcf={float(row[f'coherence_ratio_{args.connectivity}']):.3f}"
                )
            summary_rows.append(
                summarize_checkpoint(tick, base_metric, checkpoint_rows, state_artifact, args)
            )
            apply_constraint_rates(summary_rows)
            write_csv(raw_path, RAW_FIELDNAMES, raw_rows)
            write_csv(summary_path, SUMMARY_FIELDNAMES, summary_rows)
            json_path.write_text(
                json.dumps(
                    {
                        "config_path": args.config,
                        "config_hash": config_hash(cfg),
                        "raw_path": raw_path.as_posix(),
                        "summary_path": summary_path.as_posix(),
                        "checkpoint_ticks": checkpoint_ticks,
                        "samples": args.samples,
                        "horizon": args.horizon,
                        "connectivity": args.connectivity,
                        "commitment_epsilon": args.commitment_epsilon,
                        "outcome_classes": OUTCOME_CLASSES,
                        "summary_rows": summary_rows,
                    },
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
        if tick < max_tick:
            step(world, cfg)

    apply_persistence(
        summary_rows,
        top_components_by_tick,
        all_components_by_tick,
        checkpoint_ticks,
        args,
    )
    apply_constraint_rates(summary_rows)
    first_commitment_tick = next(
        (
            int(row["checkpoint_tick"])
            for row in summary_rows
            if float(row["openness"]) < float(args.commitment_epsilon)
        ),
        None,
    )
    write_csv(raw_path, RAW_FIELDNAMES, raw_rows)
    write_csv(summary_path, SUMMARY_FIELDNAMES, summary_rows)
    json_path.write_text(
        json.dumps(
            {
                "config_path": args.config,
                "config_hash": config_hash(cfg),
                "raw_path": raw_path.as_posix(),
                "summary_path": summary_path.as_posix(),
                "checkpoint_ticks": checkpoint_ticks,
                "samples": args.samples,
                "horizon": args.horizon,
                "connectivity": args.connectivity,
                "commitment_epsilon": args.commitment_epsilon,
                "first_commitment_tick": first_commitment_tick,
                "outcome_classes": OUTCOME_CLASSES,
                "summary_rows": summary_rows,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(json_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
