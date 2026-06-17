from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from experiment_db import open_database
from iota_rig import init_world, vector_step


def load_experiment_config(db_path: Path, experiment_id: int) -> dict[str, Any]:
    conn = open_database(db_path)
    try:
        row = conn.execute(
            """
            SELECT config_json
            FROM config_snapshots
            WHERE experiment_id = ?
            """,
            (experiment_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise SystemExit(f"No config snapshot found for IOTA-{experiment_id:06d}")
    return json.loads(str(row[0]))


def load_metrics(output_root: Path, experiment_id: int) -> list[dict[str, Any]]:
    path = output_root / f"IOTA-{experiment_id:06d}" / "metrics.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            parsed: dict[str, Any] = {"experiment_id": experiment_id}
            for key, value in row.items():
                if key == "tick":
                    parsed[key] = int(value)
                elif value == "":
                    parsed[key] = 0.0
                else:
                    parsed[key] = float(value)
            rows.append(parsed)
    return rows


def toroidal_distance(a: np.ndarray, b: np.ndarray, size: int, wrap: bool) -> float:
    delta = np.abs(a - b)
    if wrap:
        delta = np.minimum(delta, size - delta)
    return float(np.sqrt(np.sum(delta * delta)))


def initial_rows(experiment_id: int, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    world = init_world(cfg)
    coords = np.argwhere(world.active)
    rows: list[dict[str, Any]] = []
    for index, coord in enumerate(coords):
        x, y, z = (int(v) for v in coord)
        nearest = 0.0
        if len(coords) > 1:
            nearest = min(
                toroidal_distance(coord, other, world.size, world.wrap)
                for other_index, other in enumerate(coords)
                if other_index != index
            )
        a = int(world.A[x, y, z])
        r = int(world.R[x, y, z])
        v_idx = int(world.V[x, y, z]) % len(world.vectors)
        payload = int(world.P[x, y, z])
        dx, dy, dz, behavior = vector_step(world, v_idx, a, r, payload)
        rows.append(
            {
                "experiment_id": experiment_id,
                "seed": int(cfg["init"].get("seed", 0)),
                "initial_active_iotas": int(cfg["init"].get("active_iotas", 0)),
                "bond_probability": float(cfg["constants"].get("bond_probability", 0.0)),
                "cell_index": index,
                "x": x,
                "y": y,
                "z": z,
                "A": a,
                "R": r,
                "V": v_idx,
                "P": payload,
                "behavior": behavior,
                "primary_dx": dx,
                "primary_dy": dy,
                "primary_dz": dz,
                "nearest_initial_neighbor_distance": nearest,
            }
        )
    return rows


def threshold_tick(rows: list[dict[str, Any]], key: str, threshold: float) -> int | str:
    for row in rows:
        if float(row[key]) >= threshold:
            return int(row["tick"])
    return ""


def summarize_run(rows: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, Any]:
    final = rows[-1]
    peak_lcf = max(rows, key=lambda row: float(row["coherence_ratio"]))
    cumulative_secondary = sum(float(row.get("secondary_exchanges", 0.0)) for row in rows)
    first_secondary = threshold_tick(rows, "secondary_exchanges", 1.0)
    largest_growth_rates = []
    previous = rows[0]
    for row in rows[1:]:
        dt = max(1, int(row["tick"]) - int(previous["tick"]))
        largest_growth_rates.append(
            (float(row["largest_coherence"]) - float(previous["largest_coherence"])) / dt
        )
        previous = row
    final_tick = int(final["tick"])
    last_quarter_start = final_tick * 0.75
    last_quarter = [row for row in rows if int(row["tick"]) >= last_quarter_start]
    return {
        "experiment_id": int(final["experiment_id"]),
        "seed": int(cfg["init"].get("seed", 0)),
        "initial_active_iotas": int(cfg["init"].get("active_iotas", 0)),
        "bond_probability": float(cfg["constants"].get("bond_probability", 0.0)),
        "final_tick": final_tick,
        "final_active_iotas": int(final["active_iotas"]),
        "final_largest_coherence": int(final["largest_coherence"]),
        "final_lcf": float(final["coherence_ratio"]),
        "final_component_count": int(final["coherence_count"]),
        "final_entropy": float(final["entropy"]),
        "final_max_payload_fraction": float(final.get("max_payload_fraction", 0.0)),
        "cumulative_secondary_exchanges": int(cumulative_secondary),
        "first_secondary_exchange_tick": first_secondary,
        "first_lcf_0_8_tick": threshold_tick(rows, "coherence_ratio", 0.8),
        "first_lcf_0_9_tick": threshold_tick(rows, "coherence_ratio", 0.9),
        "first_lcf_0_95_tick": threshold_tick(rows, "coherence_ratio", 0.95),
        "first_lcf_0_97_tick": threshold_tick(rows, "coherence_ratio", 0.97),
        "peak_lcf": float(peak_lcf["coherence_ratio"]),
        "peak_lcf_tick": int(peak_lcf["tick"]),
        "max_largest_growth_per_tick": max(largest_growth_rates) if largest_growth_rates else 0.0,
        "mean_lcf_last_quarter": float(np.mean([row["coherence_ratio"] for row in last_quarter])),
        "mean_component_count_last_quarter": float(np.mean([row["coherence_count"] for row in last_quarter])),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def sampled_timeseries(
    experiment_rows: list[tuple[dict[str, Any], list[dict[str, Any]]]],
    interval: int,
) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for cfg, rows in experiment_rows:
        cumulative_secondary = 0.0
        previous_sample_tick = 0
        previous_sample_largest = float(rows[0]["largest_coherence"])
        for row in rows:
            cumulative_secondary += float(row.get("secondary_exchanges", 0.0))
            tick = int(row["tick"])
            final_tick = int(rows[-1]["tick"])
            if tick % interval != 0 and tick != final_tick:
                continue
            dt = max(1, tick - previous_sample_tick)
            growth = (float(row["largest_coherence"]) - previous_sample_largest) / dt
            previous_sample_tick = tick
            previous_sample_largest = float(row["largest_coherence"])
            output_rows.append(
                {
                    "experiment_id": int(row["experiment_id"]),
                    "seed": int(cfg["init"].get("seed", 0)),
                    "initial_active_iotas": int(cfg["init"].get("active_iotas", 0)),
                    "bond_probability": float(cfg["constants"].get("bond_probability", 0.0)),
                    "tick": tick,
                    "active_iotas": int(row["active_iotas"]),
                    "largest_coherence": int(row["largest_coherence"]),
                    "lcf": float(row["coherence_ratio"]),
                    "component_count": int(row["coherence_count"]),
                    "largest_growth_per_tick_since_sample": growth,
                    "secondary_exchanges": int(row.get("secondary_exchanges", 0.0)),
                    "cumulative_secondary_exchanges": int(cumulative_secondary),
                    "exchanges": int(row.get("exchanges", 0.0)),
                    "payload_changes": int(row.get("payload_changes", 0.0)),
                    "payload_entropy": float(row["entropy"]),
                    "max_payload_fraction": float(row.get("max_payload_fraction", 0.0)),
                    "mean_A": float(row.get("mean_A", 0.0)),
                    "mean_R": float(row.get("mean_R", 0.0)),
                }
            )
    return output_rows


def plot_series(rows: list[dict[str, Any]], output_path: Path, y_key: str, ylabel: str, title: str) -> None:
    groups: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault((int(row["initial_active_iotas"]), int(row["seed"])), []).append(row)

    plt.figure(figsize=(9, 5))
    for (initial_active, seed), group_rows in sorted(groups.items()):
        group_rows.sort(key=lambda row: int(row["tick"]))
        plt.plot(
            [row["tick"] for row in group_rows],
            [row[y_key] for row in group_rows],
            label=f"N0={initial_active}, seed={seed}",
        )
    plt.xlabel("Tick")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=140)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create seed-geometry diagnostics from completed metrics.")
    parser.add_argument("experiment_ids", nargs="+", type=int)
    parser.add_argument("--database", default="data/iota_lab.db")
    parser.add_argument("--output-root", default="output")
    parser.add_argument("--findings-dir", default="output/findings")
    parser.add_argument("--interval", type=int, default=256)
    parser.add_argument("--prefix", default="seed_metrics_diagnostic")
    args = parser.parse_args()

    db_path = Path(args.database)
    output_root = Path(args.output_root)
    findings_dir = Path(args.findings_dir)
    findings_dir.mkdir(parents=True, exist_ok=True)

    experiment_rows: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    initial_condition_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for experiment_id in args.experiment_ids:
        cfg = load_experiment_config(db_path, experiment_id)
        rows = load_metrics(output_root, experiment_id)
        experiment_rows.append((cfg, rows))
        initial_condition_rows.extend(initial_rows(experiment_id, cfg))
        summary_rows.append(summarize_run(rows, cfg))

    timeseries_rows = sampled_timeseries(experiment_rows, args.interval)
    write_csv(findings_dir / f"{args.prefix}_timeseries.csv", timeseries_rows)
    write_csv(findings_dir / f"{args.prefix}_summary.csv", summary_rows)
    write_csv(findings_dir / f"{args.prefix}_initial_conditions.csv", initial_condition_rows)

    plot_series(timeseries_rows, findings_dir / f"{args.prefix}_lcf.png", "lcf", "LCF", "LCF by Seed Geometry")
    plot_series(
        timeseries_rows,
        findings_dir / f"{args.prefix}_active.png",
        "active_iotas",
        "Active Iotas",
        "Active Iotas by Seed Geometry",
    )
    plot_series(
        timeseries_rows,
        findings_dir / f"{args.prefix}_components.png",
        "component_count",
        "Component Count",
        "Component Count by Seed Geometry",
    )
    plot_series(
        timeseries_rows,
        findings_dir / f"{args.prefix}_cumulative_secondary.png",
        "cumulative_secondary_exchanges",
        "Cumulative Secondary Exchanges",
        "Secondary Exchanges by Seed Geometry",
    )
    plot_series(
        timeseries_rows,
        findings_dir / f"{args.prefix}_payload_fraction.png",
        "max_payload_fraction",
        "Max Payload Fraction",
        "Payload Concentration by Seed Geometry",
    )

    print(findings_dir / f"{args.prefix}_summary.csv")
    print(findings_dir / f"{args.prefix}_timeseries.csv")
    print(findings_dir / f"{args.prefix}_initial_conditions.csv")


if __name__ == "__main__":
    main()
