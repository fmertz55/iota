from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, deque
from pathlib import Path
from typing import Any

import numpy as np

from iota_rig import load_config
from payload_coupling_committor_analysis import (
    HIGH_COUPLING,
    HIGH_LABEL,
    LOW_COUPLING,
    LOW_LABEL,
    MAX_TICKS,
    SEED_EVENTS,
    checkpoint_world,
    clone_world,
    seed_config,
)
from payload_coupling_divergence_trace import trace_step


OUTPUT_DIR = Path("output/findings")
NEIGHBORS_6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def entropy_from_counts(counts: np.ndarray) -> float:
    total = float(np.sum(counts))
    if total <= 0:
        return 0.0
    probabilities = counts[counts > 0].astype(np.float64) / total
    return float(-np.sum(probabilities * np.log2(probabilities)))


def component_records(world: Any, top_components: int, min_size: int) -> list[dict[str, Any]]:
    active_coords = {tuple(int(value) for value in coord) for coord in np.argwhere(world.active)}
    components: list[dict[str, Any]] = []

    while active_coords:
        start = active_coords.pop()
        coords = [start]
        queue: deque[tuple[int, int, int]] = deque([start])
        while queue:
            x, y, z = queue.popleft()
            for dx, dy, dz in NEIGHBORS_6:
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

        if len(coords) < min_size:
            continue

        coord_array = np.array(coords, dtype=np.int32)
        xs = coord_array[:, 0]
        ys = coord_array[:, 1]
        zs = coord_array[:, 2]
        payloads = world.P[xs, ys, zs].astype(np.int64)
        vectors = world.V[xs, ys, zs].astype(np.int64) % len(world.vectors)
        vector_steps = world.vectors[vectors].astype(np.float64)
        mean_vector = vector_steps.mean(axis=0)
        mean_vector_norm = float(np.linalg.norm(mean_vector))
        payload_counts = np.bincount(payloads, minlength=8)
        vector_counts = np.bincount(vectors, minlength=len(world.vectors))
        dominant_payload = int(np.argmax(payload_counts))
        bbox_volume = (
            int(xs.max() - xs.min() + 1)
            * int(ys.max() - ys.min() + 1)
            * int(zs.max() - zs.min() + 1)
        )
        components.append(
            {
                "coords": frozenset(coords),
                "size": len(coords),
                "centroid_x": float(xs.mean()),
                "centroid_y": float(ys.mean()),
                "centroid_z": float(zs.mean()),
                "mean_A": float(world.A[xs, ys, zs].mean()),
                "mean_R": float(world.R[xs, ys, zs].mean()),
                "dominant_payload": dominant_payload,
                "dominant_payload_fraction": float(payload_counts[dominant_payload] / len(coords)),
                "payload_entropy": entropy_from_counts(payload_counts),
                "vector_entropy": entropy_from_counts(vector_counts),
                "mean_vector_x": float(mean_vector[0]),
                "mean_vector_y": float(mean_vector[1]),
                "mean_vector_z": float(mean_vector[2]),
                "mean_vector_norm": mean_vector_norm,
                "bbox_volume": bbox_volume,
                "bbox_density": float(len(coords) / bbox_volume) if bbox_volume else 0.0,
            }
        )

    components.sort(key=lambda row: int(row["size"]), reverse=True)
    return components[:top_components]


def vector_turn_degrees(previous: dict[str, Any] | None, current: dict[str, Any]) -> float:
    if previous is None:
        return 0.0
    first = np.array(
        [previous["mean_vector_x"], previous["mean_vector_y"], previous["mean_vector_z"]],
        dtype=np.float64,
    )
    second = np.array(
        [current["mean_vector_x"], current["mean_vector_y"], current["mean_vector_z"]],
        dtype=np.float64,
    )
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    if denominator <= 0:
        return 0.0
    alignment = float(np.clip(np.dot(first, second) / denominator, -1.0, 1.0))
    return float(math.degrees(math.acos(alignment)))


def assign_tracks(
    components: list[dict[str, Any]],
    previous_tracks: dict[int, dict[str, Any]],
    next_track_id: int,
    min_overlap_fraction: float,
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]], int]:
    assigned_previous: set[int] = set()
    rows: list[dict[str, Any]] = []
    current_tracks: dict[int, dict[str, Any]] = {}

    for rank, component in enumerate(components, start=1):
        best_track_id = None
        best_overlap_fraction = 0.0
        best_jaccard = 0.0
        current_coords = component["coords"]
        for track_id, previous in previous_tracks.items():
            if track_id in assigned_previous:
                continue
            previous_coords = previous["coords"]
            overlap = len(current_coords & previous_coords)
            if overlap <= 0:
                continue
            overlap_fraction = overlap / min(len(current_coords), len(previous_coords))
            jaccard = overlap / len(current_coords | previous_coords)
            if overlap_fraction > best_overlap_fraction:
                best_track_id = track_id
                best_overlap_fraction = overlap_fraction
                best_jaccard = jaccard

        previous = None
        if best_track_id is not None and best_overlap_fraction >= min_overlap_fraction:
            track_id = best_track_id
            assigned_previous.add(track_id)
            previous = previous_tracks[track_id]
        else:
            track_id = next_track_id
            next_track_id += 1

        row = dict(component)
        row.update(
            {
                "track_id": track_id,
                "rank": rank,
                "overlap_fraction": best_overlap_fraction,
                "jaccard": best_jaccard,
                "size_delta": int(component["size"] - previous["size"]) if previous else 0,
                "vector_turn_degrees": vector_turn_degrees(previous, component),
            }
        )
        rows.append(row)
        current_tracks[track_id] = component

    return rows, current_tracks, next_track_id


def update_interval_counters(counters: Counter[str], events: list[dict[str, Any]]) -> None:
    counters["ticks"] += 1
    counters["productive_exchanges"] += len(events)
    for event in events:
        if event["subtype"] == "secondary":
            counters["secondary_exchanges"] += 1
        if event["inter_component_bridge"]:
            counters["inter_component_bridges"] += 1
        if event["creates_new_active"]:
            counters["new_active_events"] += 1
        if event["payload_takeover"]:
            counters["payload_takeovers"] += 1
        if event["vector_inherit"]:
            counters["vector_inheritances"] += 1
        if event["payload_multiplier_class"] == "cross_payload":
            counters["cross_payload_exchanges"] += 1
        if event["payload_multiplier_class"] == "same_payload":
            counters["same_payload_exchanges"] += 1
        counters["influence_sum"] += float(event["influence"])
        counters["base_influence_sum"] += float(event["base_influence"])


def interval_row(tick: int, counters: Counter[str], components: list[dict[str, Any]]) -> dict[str, Any]:
    active_top = sum(int(component["size"]) for component in components)
    top_sizes = [int(component["size"]) for component in components]
    total_exchanges = counters["productive_exchanges"]
    return {
        "tick": tick,
        "interval_ticks": counters["ticks"],
        "tracked_component_count": len(components),
        "tracked_active_sites": active_top,
        "top1_size": top_sizes[0] if top_sizes else 0,
        "top2_coverage_within_tracked": (
            sum(top_sizes[:2]) / active_top if active_top and len(top_sizes) >= 2 else 1.0 if active_top else 0.0
        ),
        "component_size_entropy_within_tracked": entropy_from_counts(np.array(top_sizes, dtype=np.int64)),
        "productive_exchanges": total_exchanges,
        "secondary_exchanges": counters["secondary_exchanges"],
        "inter_component_bridges": counters["inter_component_bridges"],
        "bridge_fraction": counters["inter_component_bridges"] / total_exchanges if total_exchanges else 0.0,
        "new_active_events": counters["new_active_events"],
        "payload_takeovers": counters["payload_takeovers"],
        "vector_inheritances": counters["vector_inheritances"],
        "cross_payload_exchanges": counters["cross_payload_exchanges"],
        "same_payload_exchanges": counters["same_payload_exchanges"],
        "mean_influence": counters["influence_sum"] / total_exchanges if total_exchanges else 0.0,
        "mean_base_influence": counters["base_influence_sum"] / total_exchanges if total_exchanges else 0.0,
    }


def dominant_period_ticks(values: list[float], sample_every: int) -> float:
    if len(values) < 4:
        return 0.0
    series = np.array(values, dtype=np.float64)
    series = series - np.mean(series)
    if float(np.max(np.abs(series))) == 0.0:
        return 0.0
    spectrum = np.fft.rfft(series)
    power = np.abs(spectrum) ** 2
    if len(power) <= 1:
        return 0.0
    power[0] = 0.0
    index = int(np.argmax(power))
    if index <= 0 or power[index] <= 0:
        return 0.0
    frequency_per_sample = index / len(series)
    return float(sample_every / frequency_per_sample)


def track_summary_rows(component_rows: list[dict[str, Any]], sample_every: int) -> list[dict[str, Any]]:
    by_track: dict[int, list[dict[str, Any]]] = {}
    for row in component_rows:
        by_track.setdefault(int(row["track_id"]), []).append(row)

    summaries = []
    for track_id, rows in sorted(by_track.items()):
        rows.sort(key=lambda row: int(row["tick"]))
        sizes = [float(row["size"]) for row in rows]
        turns = [float(row["vector_turn_degrees"]) for row in rows[1:]]
        growth = [float(row["size_delta"]) for row in rows[1:]]
        positive_pulses = sum(1 for value in growth if value > 0)
        summaries.append(
            {
                "track_id": track_id,
                "observations": len(rows),
                "first_tick": rows[0]["tick"],
                "last_tick": rows[-1]["tick"],
                "mean_size": float(np.mean(sizes)),
                "max_size": int(max(sizes)),
                "size_cv": float(np.std(sizes) / np.mean(sizes)) if np.mean(sizes) else 0.0,
                "positive_growth_pulses": positive_pulses,
                "growth_pulse_fraction": positive_pulses / len(growth) if growth else 0.0,
                "mean_abs_growth": float(np.mean(np.abs(growth))) if growth else 0.0,
                "mean_vector_turn_degrees": float(np.mean(turns)) if turns else 0.0,
                "cumulative_vector_turn_degrees": float(np.sum(turns)) if turns else 0.0,
                "dominant_size_period_ticks": dominant_period_ticks(sizes, sample_every),
                "mean_payload_entropy": float(np.mean([float(row["payload_entropy"]) for row in rows])),
                "mean_vector_entropy": float(np.mean([float(row["vector_entropy"]) for row in rows])),
            }
        )
    return summaries


def continuation_seed_for(seed: int, law: str, condition: str, sample_index: int, rng_seed_base: int) -> int:
    law_index = 0 if law == "low" else 1
    condition_index = 0 if condition == "protected_vector" else 1
    return rng_seed_base + seed * 1_000_000 + law_index * 100_000 + condition_index * 10_000 + sample_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42, choices=sorted(SEED_EVENTS))
    parser.add_argument("--law", choices=["low", "high"], default="low")
    parser.add_argument("--condition", choices=["protected_vector", "absorber_vector"], default="protected_vector")
    parser.add_argument("--sample-index", type=int, default=1)
    parser.add_argument("--rng-seed-base", type=int, default=20260622)
    parser.add_argument("--sample-every", type=int, default=128)
    parser.add_argument("--max-ticks", type=int, default=MAX_TICKS)
    parser.add_argument("--top-components", type=int, default=20)
    parser.add_argument("--min-component-size", type=int, default=10)
    parser.add_argument("--min-overlap-fraction", type=float, default=0.25)
    parser.add_argument("--output-prefix", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base_cfg = load_config("config.yaml")
    label = LOW_LABEL if args.law == "low" else HIGH_LABEL
    coupling = LOW_COUPLING if args.law == "low" else HIGH_COUPLING
    event = SEED_EVENTS[args.seed]
    cfg = seed_config(base_cfg, args.seed, label, coupling)
    checkpoint = checkpoint_world(cfg, event)
    continuation_seed = continuation_seed_for(
        args.seed,
        args.law,
        args.condition,
        args.sample_index,
        args.rng_seed_base,
    )
    world = clone_world(checkpoint, continuation_seed)
    forced_v = event.protected_v if args.condition == "protected_vector" else event.absorber_v
    world.V[event.target] = np.uint8(forced_v)

    prefix = args.output_prefix or (
        "finding_021_second_order"
        f"_seed{args.seed}_{args.law}_{args.condition}_sample{args.sample_index}"
    )
    component_rows: list[dict[str, Any]] = []
    interval_rows: list[dict[str, Any]] = []
    previous_tracks: dict[int, dict[str, Any]] = {}
    next_track_id = 1
    counters: Counter[str] = Counter()

    for tick in range(event.divergence_tick + 1, args.max_ticks + 1):
        events = trace_step(world, cfg, tick)
        update_interval_counters(counters, events)
        if tick % args.sample_every != 0 and tick != args.max_ticks:
            continue

        components = component_records(world, args.top_components, args.min_component_size)
        tracked_rows, previous_tracks, next_track_id = assign_tracks(
            components,
            previous_tracks,
            next_track_id,
            args.min_overlap_fraction,
        )
        for row in tracked_rows:
            serializable = {key: value for key, value in row.items() if key != "coords"}
            serializable["tick"] = tick
            component_rows.append(serializable)
        interval_rows.append(interval_row(tick, counters, components))
        counters = Counter()
        print(
            f"tick={tick} tracks={len(tracked_rows)} "
            f"top1={tracked_rows[0]['size'] if tracked_rows else 0} "
            f"bridges={interval_rows[-1]['inter_component_bridges']}"
        )

    summary_rows = track_summary_rows(component_rows, args.sample_every)
    paths = {
        "component_timeseries": OUTPUT_DIR / f"{prefix}_component_timeseries.csv",
        "interval_graph": OUTPUT_DIR / f"{prefix}_interval_graph.csv",
        "track_summary": OUTPUT_DIR / f"{prefix}_track_summary.csv",
        "summary_json": OUTPUT_DIR / f"{prefix}_summary.json",
    }

    if component_rows:
        with paths["component_timeseries"].open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(component_rows[0].keys()))
            writer.writeheader()
            writer.writerows(component_rows)
    if interval_rows:
        with paths["interval_graph"].open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(interval_rows[0].keys()))
            writer.writeheader()
            writer.writerows(interval_rows)
    if summary_rows:
        with paths["track_summary"].open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)

    summary = {
        "seed": args.seed,
        "law": args.law,
        "condition": args.condition,
        "sample_index": args.sample_index,
        "continuation_seed": continuation_seed,
        "forced_v": forced_v,
        "divergence_tick": event.divergence_tick,
        "target": event.target,
        "sample_every": args.sample_every,
        "max_ticks": args.max_ticks,
        "paths": {key: str(path) for key, path in paths.items()},
        "track_count": len(summary_rows),
        "persistent_track_count": sum(row["observations"] >= 4 for row in summary_rows),
        "mean_bridge_fraction": (
            float(np.mean([row["bridge_fraction"] for row in interval_rows]))
            if interval_rows
            else 0.0
        ),
        "mean_component_entropy": (
            float(np.mean([row["component_size_entropy_within_tracked"] for row in interval_rows]))
            if interval_rows
            else 0.0
        ),
    }
    paths["summary_json"].write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
