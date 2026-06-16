from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


def coherence_stats(world: Any) -> tuple[int, int]:
    active_coords = {tuple(int(v) for v in coord) for coord in np.argwhere(world.active)}
    if not active_coords:
        return 0, 0

    size = world.size
    largest = 0
    count = 0
    neighbors = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    while active_coords:
        count += 1
        component_size = 0
        stack = [active_coords.pop()]
        while stack:
            x, y, z = stack.pop()
            component_size += 1
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
    return largest, count


def payload_entropy(world: Any) -> float:
    active_count = int(world.active.sum())
    if active_count == 0:
        return 0.0
    hist = np.bincount(world.P[world.active], minlength=8).astype(np.float64)
    probabilities = hist[hist > 0] / active_count
    return float(-np.sum(probabilities * np.log2(probabilities)))


def collect_metrics(world: Any, tick: int, extras: dict[str, float] | None = None) -> dict[str, float]:
    active_count = int(world.active.sum())
    largest, count = coherence_stats(world)
    metric = {
        "tick": int(tick),
        "active_iotas": active_count,
        "largest_coherence": int(largest),
        "coherence_count": int(count),
        "entropy": payload_entropy(world),
    }
    if extras:
        metric.update(extras)
    return metric


def save_run_metrics(metrics: list[dict[str, float]], out: Path) -> None:
    if not metrics:
        return
    keys = [
        "tick",
        "active_iotas",
        "largest_coherence",
        "coherence_count",
        "entropy",
        "exchanges",
        "payload_changes",
        "mean_A",
        "mean_R",
        "max_payload_fraction",
    ]
    with open(out / "metrics.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
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

    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    series = [
        ("active_iotas", "Active Iotas"),
        ("largest_coherence", "Largest Coherence"),
        ("entropy", "Payload Entropy"),
    ]
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
) -> dict[str, float]:
    init_metadata = init_metadata or {}
    if not metrics:
        summary = {
            "peak_active_iotas": 0,
            "final_active_iotas": 0,
            "largest_coherence": 0,
            "coherence_count": 0,
            "entropy": 0.0,
            "persistence": 0.0,
            "execution_time_seconds": execution_time,
        }
        summary.update(init_metadata)
        return summary
    active = [int(m["active_iotas"]) for m in metrics]
    nonzero_ticks = sum(1 for value in active if value > 0)
    summary = {
        "peak_active_iotas": max(active),
        "final_active_iotas": active[-1],
        "largest_coherence": max(int(m["largest_coherence"]) for m in metrics),
        "coherence_count": int(metrics[-1]["coherence_count"]),
        "entropy": float(metrics[-1]["entropy"]),
        "persistence": float(nonzero_ticks / len(metrics)),
        "execution_time_seconds": execution_time,
    }
    summary.update(init_metadata)
    return summary


def save_experiment_comparison_plots(conn: sqlite3.Connection, output_root: Path) -> None:
    rows = conn.execute(
        """
        SELECT experiment_id, tick, active_iotas, largest_coherence, entropy
        FROM metrics
        ORDER BY experiment_id, tick
        """
    ).fetchall()
    if not rows:
        return

    output_root.mkdir(parents=True, exist_ok=True)
    by_experiment: dict[int, list[tuple[int, int, int, float]]] = {}
    for experiment_id, tick, active_iotas, largest_coherence, entropy in rows:
        by_experiment.setdefault(int(experiment_id), []).append(
            (int(tick), int(active_iotas), int(largest_coherence), float(entropy))
        )

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    for experiment_id, series in by_experiment.items():
        ticks = [row[0] for row in series]
        axes[0].plot(ticks, [row[1] for row in series], label=f"IOTA-{experiment_id:06d}")
        axes[1].plot(ticks, [row[2] for row in series], label=f"IOTA-{experiment_id:06d}")
        axes[2].plot(ticks, [row[3] for row in series], label=f"IOTA-{experiment_id:06d}")
    axes[0].set_ylabel("Active Iotas")
    axes[1].set_ylabel("Largest Coherence")
    axes[2].set_ylabel("Entropy")
    axes[2].set_xlabel("tick")
    axes[0].legend(fontsize="small")
    fig.tight_layout()
    fig.savefig(output_root / "experiments_timeseries.png", dpi=140)
    plt.close(fig)

    scatter_rows = conn.execute(
        """
        SELECT
            p.experiment_id,
            p.parameter_value,
            s.metric_value
        FROM parameters p
        JOIN summary_metrics s ON s.experiment_id = p.experiment_id
        WHERE p.parameter_name = 'init.active_iotas'
          AND s.metric_name = 'largest_coherence'
        ORDER BY p.experiment_id
        """
    ).fetchall()
    if not scatter_rows:
        return

    initial_active = [int(float(parameter_value)) for _, parameter_value, _ in scatter_rows]
    peak_coherence = [float(metric_value) for _, _, metric_value in scatter_rows]
    labels = [f"IOTA-{int(experiment_id):06d}" for experiment_id, _, _ in scatter_rows]

    plt.figure(figsize=(8, 5))
    plt.scatter(initial_active, peak_coherence)
    for x, y, label in zip(initial_active, peak_coherence, labels):
        plt.annotate(label, (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)
    plt.xscale("log", base=2)
    plt.xlabel("Initial Active Iotas")
    plt.ylabel("Peak Largest Coherence")
    plt.title("Initial Active Iotas vs Peak Coherence")
    plt.tight_layout()
    plt.savefig(output_root / "initial_active_vs_peak_coherence.png", dpi=140)
    plt.close()
