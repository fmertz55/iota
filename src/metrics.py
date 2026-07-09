from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from iota_rig import candidate_neighbor_steps


CONNECTIVITY_MODES = ("face6", "face18", "cube26")


def _plot_parameter_metric(
    conn: sqlite3.Connection,
    output_root: Path,
    parameter_name: str,
    x_label: str,
    metric_name: str,
    y_label: str,
    title: str,
    filename: str,
    log2_x: bool = False,
) -> None:
    rows = conn.execute(
        """
        SELECT
            p.experiment_id,
            p.parameter_value,
            s.metric_value
        FROM parameters p
        JOIN summary_metrics s ON s.experiment_id = p.experiment_id
        WHERE p.parameter_name = ?
          AND s.metric_name = ?
        ORDER BY p.experiment_id
        """,
        (parameter_name, metric_name),
    ).fetchall()
    if not rows:
        return

    parameter_values = [float(parameter_value) for _, parameter_value, _ in rows]
    metric_values = [float(metric_value) for _, _, metric_value in rows]
    labels = [f"IOTA-{int(experiment_id):06d}" for experiment_id, _, _ in rows]

    plt.figure(figsize=(8, 5))
    plt.scatter(parameter_values, metric_values)
    for x, y, label in zip(parameter_values, metric_values, labels):
        plt.annotate(label, (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)
    if log2_x:
        plt.xscale("log", base=2)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_root / filename, dpi=140)
    plt.close()


def _plot_initial_active_metric(
    conn: sqlite3.Connection,
    output_root: Path,
    metric_name: str,
    y_label: str,
    title: str,
    filename: str,
) -> None:
    _plot_parameter_metric(
        conn,
        output_root,
        "init.active_iotas",
        "Initial Active Iotas",
        metric_name,
        y_label,
        title,
        filename,
        log2_x=True,
    )


def coherence_stats(
    world: Any,
    connectivity: str = "face6",
) -> tuple[int, int, list[int], list[tuple[float, float, float]]]:
    active_coords = {tuple(int(v) for v in coord) for coord in np.argwhere(world.active)}
    if not active_coords:
        return 0, 0, [], []

    size = world.size
    largest = 0
    count = 0
    components: list[tuple[int, tuple[float, float, float]]] = []
    neighbors = tuple(
        (int(dx), int(dy), int(dz))
        for dx, dy, dz in candidate_neighbor_steps(connectivity)
    )
    while active_coords:
        count += 1
        component_size = 0
        sum_x = 0
        sum_y = 0
        sum_z = 0
        stack = [active_coords.pop()]
        while stack:
            x, y, z = stack.pop()
            component_size += 1
            sum_x += x
            sum_y += y
            sum_z += z
            for dx, dy, dz in neighbors:
                nx, ny, nz = x + dx, y + dy, z + dz
                if world.wrap:
                    nx %= size
                    ny %= size
                    nz %= size
                elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
                    continue
                neighbor = (nx, ny, nz)
                if neighbor in active_coords:
                    active_coords.remove(neighbor)
                    stack.append(neighbor)
        largest = max(largest, component_size)
        components.append(
            (
                component_size,
                (
                    sum_x / component_size,
                    sum_y / component_size,
                    sum_z / component_size,
                ),
            )
        )
    components.sort(key=lambda item: item[0], reverse=True)
    component_sizes = [component[0] for component in components]
    component_centroids = [component[1] for component in components]
    return largest, count, component_sizes, component_centroids


def component_top2_coverage(component_sizes: list[int], active_count: int, fallback: float) -> float:
    if not active_count:
        return 0.0
    if len(component_sizes) >= 2:
        return float(sum(component_sizes[:2]) / active_count)
    return fallback


def component_centroid_distance(component_centroids: list[tuple[float, float, float]]) -> float:
    if len(component_centroids) < 2:
        return 0.0
    first = component_centroids[0]
    second = component_centroids[1]
    return float(np.sqrt(sum((first[index] - second[index]) ** 2 for index in range(3))))


def payload_entropy(world: Any) -> float:
    active_count = int(world.active.sum())
    if active_count == 0:
        return 0.0
    hist = np.bincount(world.P[world.active], minlength=8).astype(np.float64)
    probabilities = hist[hist > 0] / active_count
    return float(-np.sum(probabilities * np.log2(probabilities)))


def vector_persistence_stats(world: Any) -> dict[str, float]:
    if not hasattr(world, "previous_active") or not hasattr(world, "previous_V"):
        return {
            "vector_continuing_iotas": 0.0,
            "vector_changed_iotas": 0.0,
            "vector_persistence_ratio": 0.0,
            "mean_vector_alignment": 0.0,
            "mean_vector_turn_degrees": 0.0,
        }

    continuing = world.active & world.previous_active
    continuing_count = int(continuing.sum())
    if continuing_count == 0:
        return {
            "vector_continuing_iotas": 0.0,
            "vector_changed_iotas": 0.0,
            "vector_persistence_ratio": 0.0,
            "mean_vector_alignment": 0.0,
            "mean_vector_turn_degrees": 0.0,
        }

    previous_indices = world.previous_V[continuing].astype(np.int64) % len(world.vectors)
    current_indices = world.V[continuing].astype(np.int64) % len(world.vectors)
    changed_count = int(np.count_nonzero(previous_indices != current_indices))
    previous_vectors = world.vectors[previous_indices].astype(np.float64)
    current_vectors = world.vectors[current_indices].astype(np.float64)
    dot = np.sum(previous_vectors * current_vectors, axis=1)
    previous_norm = np.linalg.norm(previous_vectors, axis=1)
    current_norm = np.linalg.norm(current_vectors, axis=1)
    denominator = previous_norm * current_norm
    valid = denominator > 0
    if not np.any(valid):
        mean_alignment = 0.0
        mean_turn_degrees = 0.0
    else:
        alignments = np.clip(dot[valid] / denominator[valid], -1.0, 1.0)
        mean_alignment = float(np.mean(alignments))
        mean_turn_degrees = float(np.degrees(np.mean(np.arccos(alignments))))

    return {
        "vector_continuing_iotas": float(continuing_count),
        "vector_changed_iotas": float(changed_count),
        "vector_persistence_ratio": float(1.0 - (changed_count / continuing_count)),
        "mean_vector_alignment": mean_alignment,
        "mean_vector_turn_degrees": mean_turn_degrees,
    }


def component_hierarchy_stats(component_sizes: list[int], active_count: int) -> dict[str, float]:
    if active_count <= 0 or not component_sizes:
        return {
            "top1_component_fraction": 0.0,
            "top5_component_coverage": 0.0,
            "top20_component_coverage": 0.0,
            "component_size_entropy": 0.0,
            "component_size_slope": 0.0,
        }

    sizes = np.array(component_sizes, dtype=np.float64)
    probabilities = sizes / float(active_count)
    nonzero_probabilities = probabilities[probabilities > 0]
    entropy = float(-np.sum(nonzero_probabilities * np.log2(nonzero_probabilities)))

    slope = 0.0
    ranked_sizes = sizes[:20]
    positive = ranked_sizes > 0
    if int(np.count_nonzero(positive)) >= 2:
        ranks = np.arange(1, len(ranked_sizes) + 1, dtype=np.float64)[positive]
        slope = float(np.polyfit(np.log(ranks), np.log(ranked_sizes[positive]), 1)[0])

    return {
        "top1_component_fraction": float(sizes[0] / active_count),
        "top5_component_coverage": float(np.sum(sizes[:5]) / active_count),
        "top20_component_coverage": float(np.sum(sizes[:20]) / active_count),
        "component_size_entropy": entropy,
        "component_size_slope": slope,
    }


def ledger_stats(world: Any) -> dict[str, float]:
    active_count = int(world.active.sum())
    active_A = int(np.sum(world.A[world.active], dtype=np.int64)) if active_count else 0
    ledger_enabled = bool(getattr(world, "ledger_enabled", False))
    if not ledger_enabled:
        return {
            "total_A": float(active_A),
            "active_A": float(active_A),
            "latent_A": 0.0,
            "depleted_cells": 0.0,
            "ledger_error": 0.0,
            "deactivation_events": 0.0,
            "amplitude_transfers": 0.0,
            "failed_transfer_gates": 0.0,
        }
    latent_A_array = getattr(world, "latent_A", None)
    if latent_A_array is None:
        latent_A = 0
        depleted_cells = 0
    else:
        inactive = ~world.active
        latent_A = int(np.sum(latent_A_array[inactive], dtype=np.int64))
        depleted_cells = int(np.count_nonzero(inactive & (latent_A_array == 0)))
    total_A = active_A + latent_A
    initial_total_A = int(getattr(world, "initial_total_A", total_A))
    return {
        "total_A": float(total_A),
        "active_A": float(active_A),
        "latent_A": float(latent_A),
        "depleted_cells": float(depleted_cells),
        "ledger_error": float(total_A - initial_total_A),
        "deactivation_events": 0.0,
        "amplitude_transfers": 0.0,
        "failed_transfer_gates": 0.0,
    }


def angular_momentum_stats(world: Any) -> dict[str, float]:
    angular_L = getattr(world, "angular_L", None)
    if angular_L is None:
        return {
            "angular_momentum_nonzero_cells": 0.0,
            "angular_momentum_mean_abs_active": 0.0,
            "angular_momentum_mean_signed_active": 0.0,
            "angular_momentum_max_abs": 0.0,
        }
    abs_L = np.abs(angular_L)
    active = getattr(world, "active", None)
    if active is None:
        active_abs_L = np.array([], dtype=np.float32)
        active_L = np.array([], dtype=np.float32)
    else:
        active_abs_L = abs_L[active]
        active_L = angular_L[active]
    return {
        "angular_momentum_nonzero_cells": float(np.count_nonzero(abs_L > 1e-6)),
        "angular_momentum_mean_abs_active": float(active_abs_L.mean()) if active_abs_L.size else 0.0,
        "angular_momentum_mean_signed_active": float(active_L.mean()) if active_L.size else 0.0,
        "angular_momentum_max_abs": float(abs_L.max()) if abs_L.size else 0.0,
    }


def collect_metrics(world: Any, tick: int, extras: dict[str, float] | None = None) -> dict[str, float]:
    active_count = int(world.active.sum())
    component_stats = {
        connectivity: coherence_stats(world, connectivity)
        for connectivity in CONNECTIVITY_MODES
    }
    largest, count, component_sizes, component_centroids = component_stats["face6"]
    coherence_ratio = float(largest / active_count) if active_count else 0.0
    top2_coverage = component_top2_coverage(component_sizes, active_count, coherence_ratio)
    centroid_distance_1_2 = component_centroid_distance(component_centroids)
    metric = {
        "tick": int(tick),
        "active_iotas": active_count,
        "largest_coherence": int(largest),
        "coherence_count": int(count),
        "coherence_ratio": coherence_ratio,
        "entropy": payload_entropy(world),
        "top2_component_coverage": top2_coverage,
        "component_centroid_distance_1_2": centroid_distance_1_2,
    }
    metric.update(ledger_stats(world))
    metric.update(angular_momentum_stats(world))
    for index in range(20):
        metric[f"component_size_{index + 1}"] = int(component_sizes[index]) if index < len(component_sizes) else 0
    metric.update(component_hierarchy_stats(component_sizes, active_count))
    for connectivity, (mode_largest, mode_count, mode_sizes, mode_centroids) in component_stats.items():
        mode_ratio = float(mode_largest / active_count) if active_count else 0.0
        metric[f"largest_coherence_{connectivity}"] = int(mode_largest)
        metric[f"coherence_count_{connectivity}"] = int(mode_count)
        metric[f"coherence_ratio_{connectivity}"] = mode_ratio
        metric[f"top2_component_coverage_{connectivity}"] = component_top2_coverage(
            mode_sizes,
            active_count,
            mode_ratio,
        )
        metric[f"component_centroid_distance_1_2_{connectivity}"] = component_centroid_distance(
            mode_centroids
        )
        for index in range(20):
            metric[f"component_size_{index + 1}_{connectivity}"] = (
                int(mode_sizes[index]) if index < len(mode_sizes) else 0
            )
        for key, value in component_hierarchy_stats(mode_sizes, active_count).items():
            metric[f"{key}_{connectivity}"] = value
    metric.update(vector_persistence_stats(world))
    if extras:
        metric.update(extras)
    return metric


def connectivity_metric_keys() -> list[str]:
    keys: list[str] = []
    for connectivity in CONNECTIVITY_MODES:
        keys.extend(
            [
                f"largest_coherence_{connectivity}",
                f"coherence_count_{connectivity}",
                f"coherence_ratio_{connectivity}",
            ]
        )
        keys.extend(
            f"component_size_{index + 1}_{connectivity}"
            for index in range(20)
        )
        keys.extend(
            [
                f"top2_component_coverage_{connectivity}",
                f"top1_component_fraction_{connectivity}",
                f"top5_component_coverage_{connectivity}",
                f"top20_component_coverage_{connectivity}",
                f"component_size_entropy_{connectivity}",
                f"component_size_slope_{connectivity}",
                f"component_centroid_distance_1_2_{connectivity}",
            ]
        )
    return keys


def save_run_metrics(metrics: list[dict[str, float]], out: Path) -> None:
    if not metrics:
        return
    keys = [
        "tick",
        "active_iotas",
        "largest_coherence",
        "coherence_count",
        "coherence_ratio",
        "entropy",
        *connectivity_metric_keys(),
        "component_size_1",
        "component_size_2",
        "component_size_3",
        "component_size_4",
        "component_size_5",
        "component_size_6",
        "component_size_7",
        "component_size_8",
        "component_size_9",
        "component_size_10",
        "component_size_11",
        "component_size_12",
        "component_size_13",
        "component_size_14",
        "component_size_15",
        "component_size_16",
        "component_size_17",
        "component_size_18",
        "component_size_19",
        "component_size_20",
        "top2_component_coverage",
        "top1_component_fraction",
        "top5_component_coverage",
        "top20_component_coverage",
        "component_size_entropy",
        "component_size_slope",
        "component_centroid_distance_1_2",
        "exchanges",
        "secondary_exchanges",
        "payload_changes",
        "mean_A",
        "mean_R",
        "max_payload_fraction",
        "total_A",
        "active_A",
        "latent_A",
        "depleted_cells",
        "deactivation_events",
        "amplitude_transfers",
        "failed_transfer_gates",
        "ledger_error",
        "vector_continuing_iotas",
        "vector_changed_iotas",
        "vector_persistence_ratio",
        "mean_vector_alignment",
        "mean_vector_turn_degrees",
        "mean_exchange_alignment",
        "mean_exchange_turn_degrees",
        "mean_secondary_exchange_alignment",
        "mean_secondary_exchange_turn_degrees",
    ]
    with open(out / "metrics.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in metrics:
            writer.writerow(row)

    ticks = [m["tick"] for m in metrics]
    active = [m["active_iotas"] for m in metrics]
    plt.figure(figsize=(8, 5))
    plt.plot(ticks, active)
    plt.title("Active / non-dark iotas over time")
    plt.xlabel("tick")
    plt.ylabel("active iotas")
    plt.tight_layout()
    plt.savefig(out / "active_over_time.png", dpi=140)
    plt.close()

    series = [
        ("active_iotas", "Active Iotas"),
        ("largest_coherence", "Largest Coherence"),
        ("coherence_ratio", "Coherence Ratio"),
        ("entropy", "Payload Entropy"),
    ]
    fig, axes = plt.subplots(4, 1, figsize=(9, 11), sharex=True)
    for ax, (key, label) in zip(axes, series):
        ax.plot(ticks, [m[key] for m in metrics])
        ax.set_ylabel(label)
    axes[-1].set_xlabel("tick")
    fig.tight_layout()
    fig.savefig(out / "metrics_timeseries.png", dpi=140)
    plt.close(fig)


def metrics_summary(
    metrics: list[dict[str, float]],
    execution_time: float,
    init_metadata: dict[str, float] | None = None,
    early_stopped: bool = False,
) -> dict[str, float]:
    init_metadata = init_metadata or {}
    if not metrics:
        summary = {
            "peak_active_iotas": 0,
            "final_active_iotas": 0,
            "largest_coherence": 0,
            "coherence_count": 0,
            "peak_coherence_ratio": 0.0,
            "final_coherence_ratio": 0.0,
            "final_tick": 0,
            "early_stopped": float(early_stopped),
            "entropy": 0.0,
            "persistence": 0.0,
            "final_vector_persistence_ratio": 0.0,
            "final_mean_vector_alignment": 0.0,
            "final_mean_vector_turn_degrees": 0.0,
            "mean_exchange_turn_degrees": 0.0,
            "mean_secondary_exchange_turn_degrees": 0.0,
            "final_total_A": 0.0,
            "final_active_A": 0.0,
            "final_latent_A": 0.0,
            "final_depleted_cells": 0.0,
            "total_deactivation_events": 0.0,
            "total_amplitude_transfers": 0.0,
            "total_failed_transfer_gates": 0.0,
            "max_abs_ledger_error": 0.0,
            "final_top1_component_fraction": 0.0,
            "final_top5_component_coverage": 0.0,
            "final_top20_component_coverage": 0.0,
            "final_component_size_entropy": 0.0,
            "final_component_size_slope": 0.0,
            "execution_time_seconds": execution_time,
        }
        for connectivity in CONNECTIVITY_MODES:
            summary.update(
                {
                    f"largest_coherence_{connectivity}": 0,
                    f"coherence_count_{connectivity}": 0,
                    f"peak_coherence_ratio_{connectivity}": 0.0,
                    f"final_coherence_ratio_{connectivity}": 0.0,
                    f"final_top1_component_fraction_{connectivity}": 0.0,
                    f"final_top5_component_coverage_{connectivity}": 0.0,
                    f"final_top20_component_coverage_{connectivity}": 0.0,
                    f"final_component_size_entropy_{connectivity}": 0.0,
                    f"final_component_size_slope_{connectivity}": 0.0,
                }
            )
        summary.update(init_metadata)
        return summary
    active = [int(m["active_iotas"]) for m in metrics]
    nonzero_ticks = sum(1 for value in active if value > 0)
    secondary_ticks = [
        int(m["tick"])
        for m in metrics
        if int(float(m.get("secondary_exchanges", 0))) > 0
    ]
    exchange_turn_rows = [
        float(m.get("mean_exchange_turn_degrees", 0.0))
        for m in metrics
        if int(float(m.get("exchanges", 0))) > 0
    ]
    secondary_turn_rows = [
        float(m.get("mean_secondary_exchange_turn_degrees", 0.0))
        for m in metrics
        if int(float(m.get("secondary_exchanges", 0))) > 0
    ]
    summary = {
        "peak_active_iotas": max(active),
        "final_active_iotas": active[-1],
        "largest_coherence": max(int(m["largest_coherence"]) for m in metrics),
        "coherence_count": int(metrics[-1]["coherence_count"]),
        "peak_coherence_ratio": max(float(m["coherence_ratio"]) for m in metrics),
        "final_coherence_ratio": float(metrics[-1]["coherence_ratio"]),
        "final_tick": int(metrics[-1]["tick"]),
        "early_stopped": float(early_stopped),
        "entropy": float(metrics[-1]["entropy"]),
        "persistence": float(nonzero_ticks / len(metrics)),
        "total_secondary_exchanges": float(
            sum(int(float(m.get("secondary_exchanges", 0))) for m in metrics)
        ),
        "first_secondary_exchange_tick": float(secondary_ticks[0] if secondary_ticks else -1),
        "final_vector_persistence_ratio": float(metrics[-1].get("vector_persistence_ratio", 0.0)),
        "final_mean_vector_alignment": float(metrics[-1].get("mean_vector_alignment", 0.0)),
        "final_mean_vector_turn_degrees": float(metrics[-1].get("mean_vector_turn_degrees", 0.0)),
        "mean_exchange_turn_degrees": float(
            np.mean(exchange_turn_rows) if exchange_turn_rows else 0.0
        ),
        "mean_secondary_exchange_turn_degrees": float(
            np.mean(secondary_turn_rows) if secondary_turn_rows else 0.0
        ),
        "final_total_A": float(metrics[-1].get("total_A", 0.0)),
        "final_active_A": float(metrics[-1].get("active_A", 0.0)),
        "final_latent_A": float(metrics[-1].get("latent_A", 0.0)),
        "final_depleted_cells": float(metrics[-1].get("depleted_cells", 0.0)),
        "total_deactivation_events": float(
            sum(int(float(m.get("deactivation_events", 0))) for m in metrics)
        ),
        "total_amplitude_transfers": float(
            sum(int(float(m.get("amplitude_transfers", 0))) for m in metrics)
        ),
        "total_failed_transfer_gates": float(
            sum(int(float(m.get("failed_transfer_gates", 0))) for m in metrics)
        ),
        "max_abs_ledger_error": float(
            max(abs(float(m.get("ledger_error", 0.0))) for m in metrics)
        ),
        "final_top1_component_fraction": float(metrics[-1].get("top1_component_fraction", 0.0)),
        "final_top5_component_coverage": float(metrics[-1].get("top5_component_coverage", 0.0)),
        "final_top20_component_coverage": float(metrics[-1].get("top20_component_coverage", 0.0)),
        "final_component_size_entropy": float(metrics[-1].get("component_size_entropy", 0.0)),
        "final_component_size_slope": float(metrics[-1].get("component_size_slope", 0.0)),
        "execution_time_seconds": execution_time,
    }
    for connectivity in CONNECTIVITY_MODES:
        summary.update(
            {
                f"largest_coherence_{connectivity}": max(
                    int(m.get(f"largest_coherence_{connectivity}", 0)) for m in metrics
                ),
                f"coherence_count_{connectivity}": int(
                    metrics[-1].get(f"coherence_count_{connectivity}", 0)
                ),
                f"peak_coherence_ratio_{connectivity}": max(
                    float(m.get(f"coherence_ratio_{connectivity}", 0.0)) for m in metrics
                ),
                f"final_coherence_ratio_{connectivity}": float(
                    metrics[-1].get(f"coherence_ratio_{connectivity}", 0.0)
                ),
                f"final_top1_component_fraction_{connectivity}": float(
                    metrics[-1].get(f"top1_component_fraction_{connectivity}", 0.0)
                ),
                f"final_top5_component_coverage_{connectivity}": float(
                    metrics[-1].get(f"top5_component_coverage_{connectivity}", 0.0)
                ),
                f"final_top20_component_coverage_{connectivity}": float(
                    metrics[-1].get(f"top20_component_coverage_{connectivity}", 0.0)
                ),
                f"final_component_size_entropy_{connectivity}": float(
                    metrics[-1].get(f"component_size_entropy_{connectivity}", 0.0)
                ),
                f"final_component_size_slope_{connectivity}": float(
                    metrics[-1].get(f"component_size_slope_{connectivity}", 0.0)
                ),
            }
        )
    summary.update(init_metadata)
    return summary


def save_experiment_comparison_plots(conn: sqlite3.Connection, output_root: Path) -> None:
    rows = conn.execute(
        """
        SELECT
            experiment_id,
            tick,
            active_iotas,
            largest_coherence,
            entropy,
            CASE
                WHEN active_iotas > 0 THEN CAST(largest_coherence AS REAL) / active_iotas
                ELSE 0.0
            END AS coherence_ratio
        FROM metrics
        ORDER BY experiment_id, tick
        """
    ).fetchall()
    if not rows:
        return

    output_root.mkdir(parents=True, exist_ok=True)
    by_experiment: dict[int, list[tuple[int, int, int, float, float]]] = {}
    for experiment_id, tick, active_iotas, largest_coherence, entropy, coherence_ratio in rows:
        by_experiment.setdefault(int(experiment_id), []).append(
            (
                int(tick),
                int(active_iotas),
                int(largest_coherence),
                float(entropy),
                float(coherence_ratio),
            )
        )

    fig, axes = plt.subplots(4, 1, figsize=(10, 12), sharex=True)
    for experiment_id, series in by_experiment.items():
        ticks = [row[0] for row in series]
        axes[0].plot(ticks, [row[1] for row in series], label=f"IOTA-{experiment_id:06d}")
        axes[1].plot(ticks, [row[2] for row in series], label=f"IOTA-{experiment_id:06d}")
        axes[2].plot(ticks, [row[3] for row in series], label=f"IOTA-{experiment_id:06d}")
        axes[3].plot(ticks, [row[4] for row in series], label=f"IOTA-{experiment_id:06d}")
    axes[0].set_ylabel("Active Iotas")
    axes[1].set_ylabel("Largest Coherence")
    axes[2].set_ylabel("Entropy")
    axes[3].set_ylabel("Coherence Ratio")
    axes[3].set_xlabel("tick")
    axes[0].legend(fontsize="small")
    fig.tight_layout()
    fig.savefig(output_root / "experiments_timeseries.png", dpi=140)
    plt.close(fig)

    _plot_initial_active_metric(
        conn,
        output_root,
        "largest_coherence",
        "Peak Largest Coherence",
        "Initial Active Iotas vs Peak Coherence",
        "initial_active_vs_peak_coherence.png",
    )
    _plot_initial_active_metric(
        conn,
        output_root,
        "persistence",
        "Persistence",
        "Initial Active Iotas vs Persistence",
        "initial_active_vs_persistence.png",
    )
    _plot_initial_active_metric(
        conn,
        output_root,
        "entropy",
        "Final Entropy",
        "Initial Active Iotas vs Entropy",
        "initial_active_vs_entropy.png",
    )
    _plot_parameter_metric(
        conn,
        output_root,
        "constants.amplitude_coupling",
        "Amplitude Coupling",
        "largest_coherence",
        "Peak Largest Coherence",
        "Amplitude Coupling vs Peak Coherence",
        "amplitude_coupling_vs_peak_coherence.png",
    )
    _plot_parameter_metric(
        conn,
        output_root,
        "constants.amplitude_coupling",
        "Amplitude Coupling",
        "final_coherence_ratio",
        "Final Coherence Ratio",
        "Amplitude Coupling vs Final Coherence Ratio",
        "amplitude_coupling_vs_final_coherence_ratio.png",
    )
