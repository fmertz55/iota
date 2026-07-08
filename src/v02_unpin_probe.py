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

from front_turnover_diagnostic import accumulate_counts, take_snapshot, turnover_row
from iota_rig import init_world, load_config, step


COUNT_KEYS = {
    "exchanges",
    "secondary_exchanges",
    "payload_changes",
    "deactivation_events",
    "amplitude_transfers",
    "failed_transfer_gates",
    "secondary_vector_kicks",
    "depleted_reactivations",
}

FIELDNAMES = [
    "run_id",
    "seed",
    "ticks",
    "sample_every",
    "tail_start_tick",
    "final_tick",
    "early_stop_reason",
    "amplitude_coupling",
    "vacuum_amplitude",
    "valence",
    "active_iotas_initial",
    "bond_probability",
    "secondary_vector_kick_probability",
    "secondary_vector_kick_offset",
    "secondary_vector_kick_preserve_behavior",
    "depleted_reactivation_probability",
    "depleted_reactivation_secondary_only",
    "peak_active_iotas",
    "final_active_iotas",
    "final_depleted_cells",
    "final_active_interface_cells",
    "final_depleted_interface_cells",
    "final_total_A",
    "final_active_A",
    "final_latent_A",
    "final_ledger_error",
    "max_abs_ledger_error",
    "total_amplitude_transfers",
    "total_failed_transfer_gates",
    "total_deactivation_events",
    "total_secondary_vector_kicks",
    "total_depleted_reactivations",
    "tail_rows",
    "tail_mean_active_turnover_fraction",
    "tail_mean_active_interface_turnover_fraction",
    "tail_mean_active_birth_fraction",
    "tail_mean_active_interface_birth_fraction",
    "tail_mean_persistent_active_any_changed_fraction",
    "tail_mean_persistent_active_V_changed_fraction",
    "tail_mean_persistent_interface_any_changed_fraction",
    "tail_mean_persistent_interface_V_changed_fraction",
    "tail_mean_amplitude_transfers_per_tick",
    "tail_mean_secondary_vector_kicks_per_tick",
    "tail_mean_depleted_reactivations_per_tick",
    "wall_time_seconds",
    "unpin_score",
]


@dataclass(frozen=True)
class ProbeTask:
    run_id: str
    config_path: str
    seed: int
    ticks: int
    sample_every: int
    tail_start_tick: int
    stop_active_iotas: int
    connectivity: str
    amplitude_coupling: float
    vacuum_amplitude: int
    valence: int
    active_iotas: int
    bond_probability: float
    secondary_vector_kick_probability: float
    secondary_vector_kick_offset: int
    secondary_vector_kick_preserve_behavior: bool
    depleted_reactivation_probability: float
    depleted_reactivation_secondary_only: bool


def stable_float_label(value: float) -> str:
    return str(value).replace(".", "p").replace("-", "m")


def ledger_metric(world: Any, tick: int, extras: dict[str, float] | None = None) -> dict[str, float]:
    active = world.active
    inactive = ~active
    active_count = int(np.count_nonzero(active))
    active_amplitude = int(np.sum(world.A[active], dtype=np.int64)) if active_count else 0
    latent_amplitude = int(np.sum(world.latent_A[inactive], dtype=np.int64))
    depleted_cells = int(np.count_nonzero(inactive & (world.latent_A == 0)))
    total_amplitude = active_amplitude + latent_amplitude
    metric: dict[str, float] = {
        "tick": float(tick),
        "active_iotas": float(active_count),
        "depleted_cells": float(depleted_cells),
        "total_A": float(total_amplitude),
        "active_A": float(active_amplitude),
        "latent_A": float(latent_amplitude),
        "ledger_error": float(total_amplitude - int(world.initial_total_A)),
    }
    for key in COUNT_KEYS:
        metric[key] = 0.0
    if extras:
        for key, value in extras.items():
            metric[key] = float(value)
    return metric


def configure_task(task: ProbeTask) -> dict[str, Any]:
    config = copy.deepcopy(load_config(task.config_path))
    config["simulation_version"] = "iota-rig-v0.2.1-secondary-kick-probe"
    config.setdefault("experiment", {})["objective"] = "v0.2 secondary kick unpin probe"
    config.setdefault("init", {})["seed"] = int(task.seed)
    config["init"]["active_iotas"] = int(task.active_iotas)
    constants = config.setdefault("constants", {})
    constants["conservation"] = "hard"
    constants["deactivation"] = "exhaustion"
    constants["amplitude_coupling"] = float(task.amplitude_coupling)
    constants["vacuum_amplitude"] = int(task.vacuum_amplitude)
    constants["valence"] = int(task.valence)
    constants["bond_probability"] = float(task.bond_probability)
    constants["secondary_vector_kick_probability"] = float(
        task.secondary_vector_kick_probability
    )
    constants["secondary_vector_kick_offset"] = int(task.secondary_vector_kick_offset)
    constants["secondary_vector_kick_preserve_behavior"] = bool(
        task.secondary_vector_kick_preserve_behavior
    )
    constants["depleted_reactivation_probability"] = float(
        task.depleted_reactivation_probability
    )
    constants["depleted_reactivation_secondary_only"] = bool(
        task.depleted_reactivation_secondary_only
    )
    config.setdefault("run", {})["ticks"] = int(task.ticks)
    return config


def mean_metric(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row.get(key, 0.0) or 0.0) for row in rows]
    return float(np.mean(values)) if values else 0.0


def score_probe(row: dict[str, Any]) -> float:
    if float(row["max_abs_ledger_error"]) != 0.0:
        return -1.0e9
    burst_penalty = 20.0 if row["early_stop_reason"] else 0.0
    activity = math.log1p(float(row["final_active_iotas"]))
    depletion = math.log1p(float(row["final_depleted_cells"]))
    interface_turnover = 100.0 * float(row["tail_mean_active_interface_turnover_fraction"])
    active_turnover = 50.0 * float(row["tail_mean_active_turnover_fraction"])
    vector_change = 25.0 * float(row["tail_mean_persistent_interface_V_changed_fraction"])
    kick_rate_penalty = 0.05 * float(row["tail_mean_secondary_vector_kicks_per_tick"])
    reactivation_rate_penalty = 0.05 * float(row["tail_mean_depleted_reactivations_per_tick"])
    return float(
        interface_turnover
        + active_turnover
        + vector_change
        + 0.25 * activity
        + 0.25 * depletion
        - kick_rate_penalty
        - reactivation_rate_penalty
        - burst_penalty
    )


def run_probe_task(task_dict: dict[str, Any]) -> dict[str, Any]:
    task = ProbeTask(**task_dict)
    start_time = time.perf_counter()
    config = configure_task(task)
    world = init_world(config)
    sample_ticks = set(range(0, task.ticks + 1, int(task.sample_every)))
    sample_ticks.add(int(task.ticks))
    sample_ticks.add(0)
    pending_extras: dict[str, float] = {}
    previous_snapshot = None
    turnover_rows: list[dict[str, Any]] = []
    totals = {key: 0.0 for key in COUNT_KEYS}
    initial_metric = ledger_metric(world, 0)
    max_abs_ledger_error = abs(float(initial_metric["ledger_error"]))
    peak_active_iotas = int(initial_metric["active_iotas"])
    final_tick = int(task.ticks)
    early_stop_reason = ""

    def add_sample(tick: int) -> None:
        nonlocal previous_snapshot, pending_extras
        metric = ledger_metric(world, tick, pending_extras)
        current_snapshot = take_snapshot(world, tick, task.connectivity)
        turnover_rows.append(
            turnover_row(previous_snapshot, current_snapshot, metric, task.connectivity)
        )
        previous_snapshot = current_snapshot
        pending_extras = {}

    add_sample(0)
    sampled_ticks = {0}

    for tick in range(1, int(task.ticks) + 1):
        extras = step(world, config)
        accumulate_counts(pending_extras, extras)
        accumulate_counts(totals, extras)
        metric = ledger_metric(world, tick)
        active_count = int(metric["active_iotas"])
        peak_active_iotas = max(peak_active_iotas, active_count)
        max_abs_ledger_error = max(max_abs_ledger_error, abs(float(metric["ledger_error"])))
        if tick in sample_ticks and tick not in sampled_ticks:
            add_sample(tick)
            sampled_ticks.add(tick)
        if active_count == 0:
            final_tick = tick
            early_stop_reason = "extinct"
            break
        if int(task.stop_active_iotas) > 0 and active_count >= int(task.stop_active_iotas):
            final_tick = tick
            early_stop_reason = f"active_iotas >= {task.stop_active_iotas}"
            if tick not in sampled_ticks:
                add_sample(tick)
                sampled_ticks.add(tick)
            break

    if final_tick not in sampled_ticks:
        add_sample(final_tick)

    final_metric = ledger_metric(world, final_tick)
    final_snapshot = take_snapshot(world, final_tick, task.connectivity)
    tail_rows = [
        row
        for row in turnover_rows
        if row.get("previous_tick") != "" and int(row["tick"]) >= int(task.tail_start_tick)
    ]
    row = {
        "run_id": task.run_id,
        "seed": task.seed,
        "ticks": task.ticks,
        "sample_every": task.sample_every,
        "tail_start_tick": task.tail_start_tick,
        "final_tick": final_tick,
        "early_stop_reason": early_stop_reason,
        "amplitude_coupling": task.amplitude_coupling,
        "vacuum_amplitude": task.vacuum_amplitude,
        "valence": task.valence,
        "active_iotas_initial": task.active_iotas,
        "bond_probability": task.bond_probability,
        "secondary_vector_kick_probability": task.secondary_vector_kick_probability,
        "secondary_vector_kick_offset": task.secondary_vector_kick_offset,
        "secondary_vector_kick_preserve_behavior": task.secondary_vector_kick_preserve_behavior,
        "depleted_reactivation_probability": task.depleted_reactivation_probability,
        "depleted_reactivation_secondary_only": task.depleted_reactivation_secondary_only,
        "peak_active_iotas": peak_active_iotas,
        "final_active_iotas": int(final_metric["active_iotas"]),
        "final_depleted_cells": int(final_metric["depleted_cells"]),
        "final_active_interface_cells": int(np.count_nonzero(final_snapshot.active_interface)),
        "final_depleted_interface_cells": int(np.count_nonzero(final_snapshot.depleted_interface)),
        "final_total_A": float(final_metric["total_A"]),
        "final_active_A": float(final_metric["active_A"]),
        "final_latent_A": float(final_metric["latent_A"]),
        "final_ledger_error": float(final_metric["ledger_error"]),
        "max_abs_ledger_error": max_abs_ledger_error,
        "total_amplitude_transfers": totals["amplitude_transfers"],
        "total_failed_transfer_gates": totals["failed_transfer_gates"],
        "total_deactivation_events": totals["deactivation_events"],
        "total_secondary_vector_kicks": totals["secondary_vector_kicks"],
        "total_depleted_reactivations": totals["depleted_reactivations"],
        "tail_rows": len(tail_rows),
        "tail_mean_active_turnover_fraction": mean_metric(tail_rows, "active_turnover_fraction"),
        "tail_mean_active_interface_turnover_fraction": mean_metric(
            tail_rows,
            "active_interface_turnover_fraction",
        ),
        "tail_mean_active_birth_fraction": mean_metric(tail_rows, "active_birth_fraction"),
        "tail_mean_active_interface_birth_fraction": mean_metric(
            tail_rows,
            "active_interface_birth_fraction",
        ),
        "tail_mean_persistent_active_any_changed_fraction": mean_metric(
            tail_rows,
            "persistent_active_any_changed_fraction",
        ),
        "tail_mean_persistent_active_V_changed_fraction": mean_metric(
            tail_rows,
            "persistent_active_V_changed_fraction",
        ),
        "tail_mean_persistent_interface_any_changed_fraction": mean_metric(
            tail_rows,
            "persistent_active_interface_any_changed_fraction",
        ),
        "tail_mean_persistent_interface_V_changed_fraction": mean_metric(
            tail_rows,
            "persistent_active_interface_V_changed_fraction",
        ),
        "tail_mean_amplitude_transfers_per_tick": mean_metric(
            tail_rows,
            "amplitude_transfers_per_tick",
        ),
        "tail_mean_secondary_vector_kicks_per_tick": mean_metric(
            tail_rows,
            "secondary_vector_kicks_per_tick",
        ),
        "tail_mean_depleted_reactivations_per_tick": mean_metric(
            tail_rows,
            "depleted_reactivations_per_tick",
        ),
        "wall_time_seconds": time.perf_counter() - start_time,
    }
    row["unpin_score"] = score_probe(row)
    print(
        json.dumps(
            {
                "completed": task.run_id,
                "score": row["unpin_score"],
                "final_active": row["final_active_iotas"],
                "tail_interface_turnover": row["tail_mean_active_interface_turnover_fraction"],
                "tail_vector_change": row["tail_mean_persistent_interface_V_changed_fraction"],
                "early_stop": early_stop_reason,
            }
        ),
        flush=True,
    )
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})
        handle.flush()
        os.fsync(handle.fileno())


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temp_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    temp_path.replace(path)


def sorted_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(row["run_id"]))


def top_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: float(row["unpin_score"]), reverse=True)[:limit]


def write_outputs(output_prefix: Path, rows: list[dict[str, Any]], task_count: int, complete: bool, top_n: int) -> None:
    ordered = sorted_rows(rows)
    write_csv(output_prefix.with_suffix(".csv"), ordered)
    atomic_write_json(
        output_prefix.with_suffix(".json"),
        {
            "mode": "v02_secondary_kick_unpin_probe",
            "complete": complete,
            "task_count": task_count,
            "completed_count": len(rows),
            "top_rows": top_rows(rows, top_n),
        },
    )


def build_tasks(args: argparse.Namespace) -> list[ProbeTask]:
    tasks: list[ProbeTask] = []
    for index, values in enumerate(
        itertools.product(
            args.seeds,
            args.amplitude_couplings,
            args.vacuum_amplitudes,
            args.valences,
            args.active_iotas,
            args.bond_probabilities,
            args.secondary_vector_kick_probabilities,
            args.secondary_vector_kick_offsets,
            args.depleted_reactivation_probabilities,
        ),
        start=1,
    ):
        (
            seed,
            amplitude_coupling,
            vacuum_amplitude,
            valence,
            active_iotas,
            bond_probability,
            kick_probability,
            kick_offset,
            depleted_reactivation_probability,
        ) = values
        run_id = (
            f"unpin_{index:04d}_s{seed}_ka{stable_float_label(amplitude_coupling)}_"
            f"vac{vacuum_amplitude}_val{valence}_n{active_iotas}_"
            f"bp{stable_float_label(bond_probability)}_"
            f"skp{stable_float_label(kick_probability)}_sko{kick_offset}_"
            f"drp{stable_float_label(depleted_reactivation_probability)}"
        )
        tasks.append(
            ProbeTask(
                run_id=run_id,
                config_path=args.config,
                seed=int(seed),
                ticks=int(args.ticks),
                sample_every=int(args.sample_every),
                tail_start_tick=int(args.tail_start_tick),
                stop_active_iotas=int(args.stop_active_iotas),
                connectivity=str(args.connectivity),
                amplitude_coupling=float(amplitude_coupling),
                vacuum_amplitude=int(vacuum_amplitude),
                valence=int(valence),
                active_iotas=int(active_iotas),
                bond_probability=float(bond_probability),
                secondary_vector_kick_probability=float(kick_probability),
                secondary_vector_kick_offset=int(kick_offset),
                secondary_vector_kick_preserve_behavior=bool(
                    args.secondary_vector_kick_preserve_behavior
                ),
                depleted_reactivation_probability=float(depleted_reactivation_probability),
                depleted_reactivation_secondary_only=bool(
                    args.depleted_reactivation_secondary_only
                ),
            )
        )
    return tasks


def run_tasks(tasks: list[ProbeTask], args: argparse.Namespace) -> list[dict[str, Any]]:
    output_prefix = Path(args.output_prefix)
    if args.jobs <= 1:
        rows = []
        for task in tasks:
            rows.append(run_probe_task(asdict(task)))
            if args.flush_every > 0 and len(rows) % args.flush_every == 0:
                write_outputs(output_prefix, rows, len(tasks), False, args.top_n)
        return rows

    rows = []
    with ProcessPoolExecutor(max_workers=int(args.jobs)) as executor:
        futures = [executor.submit(run_probe_task, asdict(task)) for task in tasks]
        for future in as_completed(futures):
            rows.append(future.result())
            if args.flush_every > 0 and len(rows) % args.flush_every == 0:
                write_outputs(output_prefix, rows, len(tasks), False, args.top_n)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search for v0.2 secondary-kick settings that unpin front geometry.")
    parser.add_argument("--config", default="output/findings/configs/v02_front_seed56_ka5_vac2_val8_n16.yaml")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--ticks", type=int, default=768)
    parser.add_argument("--sample-every", type=int, default=8)
    parser.add_argument("--tail-start-tick", type=int, default=416)
    parser.add_argument("--stop-active-iotas", type=int, default=2500)
    parser.add_argument("--connectivity", choices=["face6", "face18", "cube26"], default="cube26")
    parser.add_argument("--seeds", type=int, nargs="+", default=[56])
    parser.add_argument("--amplitude-couplings", type=float, nargs="+", default=[5.0])
    parser.add_argument("--vacuum-amplitudes", type=int, nargs="+", default=[2])
    parser.add_argument("--valences", type=int, nargs="+", default=[8])
    parser.add_argument("--active-iotas", type=int, nargs="+", default=[16])
    parser.add_argument("--bond-probabilities", type=float, nargs="+", default=[1.0])
    parser.add_argument(
        "--secondary-vector-kick-probabilities",
        type=float,
        nargs="+",
        default=[0.0, 0.001, 0.005, 0.01, 0.02, 0.05],
    )
    parser.add_argument("--secondary-vector-kick-offsets", type=int, nargs="+", default=[1, 3])
    parser.add_argument("--secondary-vector-kick-preserve-behavior", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--depleted-reactivation-probabilities",
        type=float,
        nargs="+",
        default=[0.0],
    )
    parser.add_argument("--depleted-reactivation-secondary-only", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--output-prefix", default="output/findings/finding_031_v02_secondary_kick_unpin_probe")
    parser.add_argument("--flush-every", type=int, default=4)
    parser.add_argument("--top-n", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = build_tasks(args)
    rows = run_tasks(tasks, args)
    write_outputs(Path(args.output_prefix), rows, len(tasks), True, args.top_n)


if __name__ == "__main__":
    main()
