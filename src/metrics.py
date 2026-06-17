from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


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
    coherence_ratio = float(largest / active_count) if active_count else 0.0
    metric = {
        "tick": int(tick),
        "active_iotas": active_count,
        "largest_coherence": int(largest),
        "coherence_count": int(count),
        "coherence_ratio": coherence_ratio,
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
        "coherence_ratio",
        "entropy",
        "exchanges",
        "secondary_exchanges",
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
            "execution_time_seconds": execution_time,
        }
        summary.update(init_metadata)
        return summary
    active = [int(m["active_iotas"]) for m in metrics]
    nonzero_ticks = sum(1 for value in active if value > 0)
    secondary_ticks = [
        int(m["tick"])
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
        "execution_time_seconds": execution_time,
    }
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
