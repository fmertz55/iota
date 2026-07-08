from __future__ import annotations

import argparse
import copy
import csv
import itertools
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from iota_rig import init_world, initial_conditions, load_config, step
from metrics import collect_metrics


COUNT_KEYS = {
    "exchanges",
    "secondary_exchanges",
    "payload_changes",
    "deactivation_events",
    "amplitude_transfers",
    "failed_transfer_gates",
    "secondary_vector_kicks",
    "residual_participations",
}


FIELDNAMES = [
    "run_id",
    "seed",
    "ticks_requested",
    "final_tick",
    "early_stop_reason",
    "amplitude_coupling",
    "vacuum_amplitude",
    "valence",
    "active_iotas_initial",
    "bond_probability",
    "initial_total_A",
    "peak_active_iotas",
    "final_active_iotas",
    "final_largest_coherence_face6",
    "final_coherence_ratio_face6",
    "final_largest_coherence_cube26",
    "final_coherence_ratio_cube26",
    "final_component_entropy_cube26",
    "final_total_A",
    "final_active_A",
    "final_latent_A",
    "final_depleted_cells",
    "final_ledger_error",
    "max_abs_ledger_error",
    "total_deactivation_events",
    "total_amplitude_transfers",
    "total_failed_transfer_gates",
    "total_secondary_vector_kicks",
    "total_residual_participations",
    "first_growth_tick",
    "first_deactivation_tick",
    "wall_time_seconds",
    "candidate_score",
]


@dataclass(frozen=True)
class SearchTask:
    run_id: str
    config_path: str
    seed: int
    ticks: int
    sample_every: int
    stagnation_window: int
    stop_active_iotas: int
    amplitude_coupling: float
    vacuum_amplitude: int
    valence: int
    active_iotas: int
    bond_probability: float


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temp_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    temp_path.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def stable_float_label(value: float) -> str:
    return str(value).replace(".", "p").replace("-", "m")


def ledger_snapshot(world: Any) -> dict[str, float]:
    active = world.active
    inactive = ~active
    active_a = int(np.sum(world.A[active], dtype=np.int64))
    latent_a = int(np.sum(world.latent_A[inactive], dtype=np.int64))
    depleted_cells = int(np.count_nonzero(inactive & (world.latent_A == 0)))
    total_a = active_a + latent_a
    ledger_error = total_a - int(world.initial_total_A)
    return {
        "total_A": float(total_a),
        "active_A": float(active_a),
        "latent_A": float(latent_a),
        "depleted_cells": float(depleted_cells),
        "ledger_error": float(ledger_error),
    }


def accumulate_counts(total: dict[str, float], extras: dict[str, float]) -> None:
    for key, value in extras.items():
        if key in COUNT_KEYS:
            total[key] = float(total.get(key, 0.0)) + float(value)


def configure_task(task: SearchTask) -> tuple[dict[str, Any], dict[str, float]]:
    cfg = copy.deepcopy(load_config(task.config_path))
    cfg["simulation_version"] = "iota-rig-v0.2.0"
    cfg.setdefault("experiment", {})["objective"] = "v0.2 parameter search"
    cfg.setdefault("init", {})["seed"] = task.seed
    cfg["init"]["active_iotas"] = task.active_iotas
    constants = cfg.setdefault("constants", {})
    constants["conservation"] = "hard"
    constants["deactivation"] = "exhaustion"
    constants["amplitude_coupling"] = task.amplitude_coupling
    constants["vacuum_amplitude"] = task.vacuum_amplitude
    constants["valence"] = task.valence
    constants["bond_probability"] = task.bond_probability
    run = cfg.setdefault("run", {})
    run["ticks"] = task.ticks
    run["metric_every"] = task.sample_every
    return cfg, initial_conditions(cfg)


def candidate_score(row: dict[str, Any]) -> float:
    if float(row["max_abs_ledger_error"]) != 0.0:
        return -1.0e9
    activity = math.log1p(float(row["peak_active_iotas"]))
    transfers = 0.25 * math.log1p(float(row["total_amplitude_transfers"]))
    depletion = 0.75 * math.log1p(float(row["final_depleted_cells"]) + float(row["total_deactivation_events"]))
    fragmentation = 1.0 - float(row["final_coherence_ratio_cube26"])
    return float(activity + transfers + depletion + fragmentation)


def run_search_task(task_dict: dict[str, Any]) -> dict[str, Any]:
    task = SearchTask(**task_dict)
    start = time.perf_counter()
    cfg, init_metadata = configure_task(task)
    world = init_world(cfg)
    initial_active = int(world.active.sum())
    peak_active = initial_active
    first_growth_tick = ""
    first_deactivation_tick = ""
    early_stop_reason = ""
    final_tick = task.ticks
    max_abs_ledger_error = abs(float(ledger_snapshot(world)["ledger_error"]))
    totals: dict[str, float] = {key: 0.0 for key in COUNT_KEYS}
    last_dynamic_tick = 0
    last_active = initial_active

    for tick in range(1, task.ticks + 1):
        extras = step(world, cfg)
        accumulate_counts(totals, extras)
        active_count = int(world.active.sum())
        peak_active = max(peak_active, active_count)
        ledger = ledger_snapshot(world)
        max_abs_ledger_error = max(max_abs_ledger_error, abs(float(ledger["ledger_error"])))

        state_changed = (
            active_count != last_active
            or int(float(extras.get("amplitude_transfers", 0))) > 0
            or int(float(extras.get("deactivation_events", 0))) > 0
        )
        if state_changed:
            last_dynamic_tick = tick
            last_active = active_count
        if first_growth_tick == "" and active_count > initial_active:
            first_growth_tick = tick
        if first_deactivation_tick == "" and int(float(extras.get("deactivation_events", 0))) > 0:
            first_deactivation_tick = tick
        if active_count == 0:
            final_tick = tick
            early_stop_reason = "extinct"
            break
        if task.stop_active_iotas > 0 and active_count >= task.stop_active_iotas:
            final_tick = tick
            early_stop_reason = f"active_iotas >= {task.stop_active_iotas}"
            break
        if task.stagnation_window > 0 and tick - last_dynamic_tick >= task.stagnation_window:
            final_tick = tick
            early_stop_reason = "stagnant"
            break

    metric = collect_metrics(world, final_tick)
    ledger = ledger_snapshot(world)
    row = {
        "run_id": task.run_id,
        "seed": task.seed,
        "ticks_requested": task.ticks,
        "final_tick": final_tick,
        "early_stop_reason": early_stop_reason,
        "amplitude_coupling": task.amplitude_coupling,
        "vacuum_amplitude": task.vacuum_amplitude,
        "valence": task.valence,
        "active_iotas_initial": task.active_iotas,
        "bond_probability": task.bond_probability,
        "initial_total_A": float(init_metadata["total_iotas"]),
        "peak_active_iotas": peak_active,
        "final_active_iotas": int(metric["active_iotas"]),
        "final_largest_coherence_face6": int(metric["largest_coherence_face6"]),
        "final_coherence_ratio_face6": float(metric["coherence_ratio_face6"]),
        "final_largest_coherence_cube26": int(metric["largest_coherence_cube26"]),
        "final_coherence_ratio_cube26": float(metric["coherence_ratio_cube26"]),
        "final_component_entropy_cube26": float(metric["component_size_entropy_cube26"]),
        "final_total_A": ledger["total_A"],
        "final_active_A": ledger["active_A"],
        "final_latent_A": ledger["latent_A"],
        "final_depleted_cells": ledger["depleted_cells"],
        "final_ledger_error": ledger["ledger_error"],
        "max_abs_ledger_error": max_abs_ledger_error,
        "total_deactivation_events": totals["deactivation_events"],
        "total_amplitude_transfers": totals["amplitude_transfers"],
        "total_failed_transfer_gates": totals["failed_transfer_gates"],
        "total_secondary_vector_kicks": totals["secondary_vector_kicks"],
        "total_residual_participations": totals["residual_participations"],
        "first_growth_tick": first_growth_tick,
        "first_deactivation_tick": first_deactivation_tick,
        "wall_time_seconds": time.perf_counter() - start,
    }
    row["candidate_score"] = candidate_score(row)
    print(
        json.dumps(
            {
                "completed": task.run_id,
                "score": row["candidate_score"],
                "peak_active": peak_active,
                "final_active": row["final_active_iotas"],
                "depleted": row["final_depleted_cells"],
                "ledger_error": row["max_abs_ledger_error"],
            }
        ),
        flush=True,
    )
    return row


def build_tasks(args: argparse.Namespace) -> list[SearchTask]:
    tasks = []
    for index, (seed, k_a, vacuum, valence, active_iotas, bond_probability) in enumerate(
        itertools.product(
            args.seeds,
            args.amplitude_couplings,
            args.vacuum_amplitudes,
            args.valences,
            args.active_iotas,
            args.bond_probabilities,
        ),
        start=1,
    ):
        run_id = (
            f"v02_{index:04d}_s{seed}_ka{stable_float_label(k_a)}_"
            f"vac{vacuum}_val{valence}_n{active_iotas}_bp{stable_float_label(bond_probability)}"
        )
        tasks.append(
            SearchTask(
                run_id=run_id,
                config_path=args.config,
                seed=seed,
                ticks=args.ticks,
                sample_every=args.sample_every,
                stagnation_window=args.stagnation_window,
                stop_active_iotas=args.stop_active_iotas,
                amplitude_coupling=float(k_a),
                vacuum_amplitude=int(vacuum),
                valence=int(valence),
                active_iotas=int(active_iotas),
                bond_probability=float(bond_probability),
            )
        )
    return tasks


def sorted_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(row["run_id"]))


def top_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: float(row["candidate_score"]), reverse=True)[:limit]


def write_outputs(output_prefix: Path, rows: list[dict[str, Any]], tasks: list[SearchTask], complete: bool, top_n: int) -> None:
    ordered = sorted_rows(rows)
    write_csv(output_prefix.with_suffix(".csv"), ordered)
    atomic_write_json(
        output_prefix.with_suffix(".json"),
        {
            "mode": "v02_parameter_search",
            "complete": complete,
            "task_count": len(tasks),
            "completed_count": len(rows),
            "top_rows": top_rows(rows, top_n),
        },
    )


def run_tasks(tasks: list[SearchTask], args: argparse.Namespace) -> list[dict[str, Any]]:
    output_prefix = Path(args.output_prefix)
    if args.jobs <= 1:
        rows = []
        for task in tasks:
            rows.append(run_search_task(asdict(task)))
            if args.flush_every > 0 and len(rows) % args.flush_every == 0:
                write_outputs(output_prefix, rows, tasks, False, args.top_n)
        return rows

    rows = []
    with ProcessPoolExecutor(max_workers=args.jobs) as executor:
        futures = [executor.submit(run_search_task, asdict(task)) for task in tasks]
        for future in as_completed(futures):
            rows.append(future.result())
            if args.flush_every > 0 and len(rows) % args.flush_every == 0:
                write_outputs(output_prefix, rows, tasks, False, args.top_n)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parallel v0.2 hard-conservation parameter search.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--ticks", type=int, default=1024)
    parser.add_argument("--sample-every", type=int, default=128)
    parser.add_argument("--stagnation-window", type=int, default=256)
    parser.add_argument("--stop-active-iotas", type=int, default=0)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 56])
    parser.add_argument("--amplitude-couplings", type=float, nargs="+", default=[1.0, 2.0, 4.0, 8.0])
    parser.add_argument("--vacuum-amplitudes", type=int, nargs="+", default=[1, 2])
    parser.add_argument("--valences", type=int, nargs="+", default=[2, 4])
    parser.add_argument("--active-iotas", type=int, nargs="+", default=[1, 4])
    parser.add_argument("--bond-probabilities", type=float, nargs="+", default=[0.0, 1.0])
    parser.add_argument("--output-prefix", default="output/findings/finding_025_v02_parameter_search")
    parser.add_argument("--flush-every", type=int, default=8)
    parser.add_argument("--top-n", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = build_tasks(args)
    rows = run_tasks(tasks, args)
    write_outputs(Path(args.output_prefix), rows, tasks, True, args.top_n)


if __name__ == "__main__":
    main()
