from __future__ import annotations

import argparse
import copy
import csv
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from iota_rig import init_world, load_config, step
from payload_coupling_bracket_4096_sweep import probe_config
from payload_coupling_committor_analysis import (
    MAX_TICKS,
    RAW_FIELDNAMES,
    SEED_EVENTS,
    checkpoint_world,
    run_continuation,
    seed_config,
    summarize,
)
from payload_coupling_divergence_continuation import metric_row as seed42_metric_row
from payload_coupling_divergence_trace import (
    HIGH_COUPLING,
    HIGH_LABEL,
    LOW_COUPLING,
    LOW_LABEL,
    trace_step,
)
from payload_coupling_seed56_divergence_continuation import metric_row as seed56_metric_row
from payload_coupling_seed56_divergence_trace import seed_config as seed56_config


LAW_CONFIGS = {
    "low": (0, LOW_LABEL, LOW_COUPLING),
    "high": (1, HIGH_LABEL, HIGH_COUPLING),
}


@dataclass(frozen=True)
class BranchTask:
    seed: int
    label: str
    law: str
    forced_v: int | None


@dataclass(frozen=True)
class BranchGroupTask:
    seed: int
    law: str
    branches: tuple[BranchTask, ...]


@dataclass(frozen=True)
class CommittorTarget:
    seed: int
    law: str
    condition: str
    sample_index: int
    continuation_seed: int
    forced_v: int
    coupling: float


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temp_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    temp_path.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def branch_config(base_cfg: dict[str, Any], task: BranchTask) -> dict[str, Any]:
    _, coupling_label, coupling = LAW_CONFIGS[task.law]
    if task.seed == 56:
        return seed56_config(base_cfg, coupling_label, coupling)
    cfg = probe_config(base_cfg, coupling_label, coupling)
    cfg["experiment"]["variant"] = (
        "A_4774_256_cube26_2_nuclei_medium_payload_4_vs_0"
        f"_cross_{coupling_label}_seed_{task.seed}_parallel_branch"
    )
    cfg["init"]["seed"] = task.seed
    return cfg


def clone_world_exact(world: Any) -> Any:
    rng = np.random.default_rng()
    rng.bit_generator.state = copy.deepcopy(world.rng.bit_generator.state)
    return type(world)(
        active=world.active.copy(),
        A=world.A.copy(),
        R=world.R.copy(),
        V=world.V.copy(),
        P=world.P.copy(),
        latent_A=world.latent_A.copy(),
        angular_L=world.angular_L.copy() if getattr(world, "angular_L", None) is not None else None,
        initial_total_A=int(world.initial_total_A),
        ledger_enabled=bool(world.ledger_enabled),
        previous_active=world.previous_active.copy(),
        previous_V=world.previous_V.copy(),
        vectors=world.vectors.copy(),
        vector_behaviors=tuple(world.vector_behaviors),
        wrap=world.wrap,
        rng=rng,
    )


def branch_event(task: BranchTask) -> tuple[int, tuple[int, int, int]]:
    event = SEED_EVENTS[task.seed]
    return event.divergence_tick, event.target


def run_branch_task(task: BranchTask) -> dict[str, Any]:
    base_cfg = load_config("config.yaml")
    cfg = branch_config(base_cfg, task)
    world = init_world(cfg)
    divergence_tick, target = branch_event(task)
    for tick in range(1, MAX_TICKS + 1):
        if tick <= divergence_tick:
            trace_step(world, cfg, tick)
        else:
            step(world, cfg)
        if tick == divergence_tick and task.forced_v is not None:
            world.V[target] = np.uint8(task.forced_v)
    _, _, coupling = LAW_CONFIGS[task.law]
    metric_row = seed56_metric_row if task.seed == 56 else seed42_metric_row
    row = metric_row(task.label, coupling, MAX_TICKS, world)
    row["seed"] = task.seed
    row["law"] = task.law
    row["forced_v"] = "" if task.forced_v is None else task.forced_v
    print(
        json.dumps(
            {
                "completed": task.label,
                "seed": task.seed,
                "active_iotas": row["active_iotas"],
                "coherence_ratio": row["coherence_ratio"],
            }
        ),
        flush=True,
    )
    return row


def run_branch_group_task(group: BranchGroupTask) -> list[dict[str, Any]]:
    base_cfg = load_config("config.yaml")
    cfg = branch_config(base_cfg, group.branches[0])
    checkpoint = init_world(cfg)
    event = SEED_EVENTS[group.seed]
    for tick in range(1, event.divergence_tick + 1):
        trace_step(checkpoint, cfg, tick)

    rows = []
    for task in group.branches:
        world = clone_world_exact(checkpoint)
        if task.forced_v is not None:
            world.V[event.target] = np.uint8(task.forced_v)
        for _tick in range(event.divergence_tick + 1, MAX_TICKS + 1):
            step(world, cfg)
        _, _, coupling = LAW_CONFIGS[task.law]
        metric_row = seed56_metric_row if task.seed == 56 else seed42_metric_row
        row = metric_row(task.label, coupling, MAX_TICKS, world)
        row["seed"] = task.seed
        row["law"] = task.law
        row["forced_v"] = "" if task.forced_v is None else task.forced_v
        print(
            json.dumps(
                {
                    "completed": task.label,
                    "seed": task.seed,
                    "active_iotas": row["active_iotas"],
                    "coherence_ratio": row["coherence_ratio"],
                }
            ),
            flush=True,
        )
        rows.append(row)
    return rows


def golden_branch_tasks(seeds: list[int]) -> list[BranchTask]:
    tasks: list[BranchTask] = []
    if 42 in seeds:
        tasks.extend(
            [
                BranchTask(42, "seed42_low_natural", "low", None),
                BranchTask(42, "seed42_high_natural", "high", None),
                BranchTask(42, "seed42_low_force_high_vector", "low", 31),
                BranchTask(42, "seed42_high_force_low_vector", "high", 0),
            ]
        )
    if 56 in seeds:
        tasks.extend(
            [
                BranchTask(56, "seed56_low_natural", "low", None),
                BranchTask(56, "seed56_high_natural", "high", None),
                BranchTask(56, "seed56_low_force_high_vector", "low", 27),
                BranchTask(56, "seed56_high_force_low_vector", "high", 0),
            ]
        )
    return tasks


def golden_group_tasks(seeds: list[int]) -> list[BranchGroupTask]:
    tasks = golden_branch_tasks(seeds)
    groups: dict[tuple[int, str], list[BranchTask]] = {}
    for task in tasks:
        groups.setdefault((task.seed, task.law), []).append(task)
    return [
        BranchGroupTask(seed=seed, law=law, branches=tuple(group))
        for (seed, law), group in sorted(groups.items())
    ]


def golden_expected() -> dict[str, tuple[int, int, float, int]]:
    return {
        "seed42_low_natural": (927, 106, 0.11434735706580366, 93),
        "seed42_high_natural": (15713, 15054, 0.9580602049258575, 143),
        "seed42_low_force_high_vector": (15713, 15054, 0.9580602049258575, 143),
        "seed42_high_force_low_vector": (927, 106, 0.11434735706580366, 93),
        "seed56_low_natural": (987, 156, 0.1580547112462006, 85),
        "seed56_high_natural": (26193, 25518, 0.9742297560416905, 123),
        "seed56_low_force_high_vector": (26193, 25518, 0.9742297560416905, 123),
        "seed56_high_force_low_vector": (987, 156, 0.1580547112462006, 85),
    }


def check_golden_rows(rows: list[dict[str, Any]]) -> list[str]:
    expected = golden_expected()
    failures = []
    for row in rows:
        label = str(row["label"])
        active, largest, lcf, count = expected[label]
        checks = [
            (int(row["active_iotas"]) == active, "active_iotas", row["active_iotas"], active),
            (int(row["largest_coherence"]) == largest, "largest_coherence", row["largest_coherence"], largest),
            (float(row["coherence_ratio"]) == lcf, "coherence_ratio", row["coherence_ratio"], lcf),
            (int(row["coherence_count"]) == count, "coherence_count", row["coherence_count"], count),
        ]
        for passed, field, actual, wanted in checks:
            if not passed:
                failures.append(f"{label}.{field}: got {actual}, expected {wanted}")
    return failures


def run_golden(args: argparse.Namespace) -> None:
    output_path = Path(args.output)
    tasks = golden_branch_tasks(args.seeds)
    grouped_tasks = golden_group_tasks(args.seeds)
    row_groups = run_tasks(grouped_tasks, args.jobs, run_branch_group_task)
    rows = [row for group in row_groups for row in group]
    label_order = [task.label for task in tasks]
    rows.sort(key=lambda row: label_order.index(str(row["label"])))
    failures = check_golden_rows(rows)
    payload = {
        "mode": "golden",
        "seeds": args.seeds,
        "jobs": args.jobs,
        "passed": not failures,
        "failures": failures,
        "rows": rows,
    }
    atomic_write_json(output_path, payload)
    write_csv(output_path.with_suffix(".csv"), rows, list(rows[0].keys()))
    print(json.dumps(payload, indent=2, default=str))
    if failures:
        raise SystemExit(1)


def target_key(target: CommittorTarget) -> str:
    return (
        f"seed_{target.seed}_{target.law}_{target.condition}_"
        f"sample_{target.sample_index:03d}_rng_{target.continuation_seed}"
    )


def row_json_path(output_dir: Path, target: CommittorTarget) -> Path:
    return output_dir / "rows" / f"{target_key(target)}.json"


def final_state_path(output_dir: Path, target: CommittorTarget) -> Path:
    return output_dir / "states" / f"{target_key(target)}.npz"


def run_committor_group(payload: tuple[tuple[int, str], list[dict[str, Any]], dict[str, Any]]) -> list[dict[str, Any]]:
    (seed, law), target_dicts, options = payload
    output_dir = Path(str(options["output_dir"]))
    early_absorber = bool(options["early_absorber"])
    save_final_states = bool(options["save_final_states"])
    _, coupling_label, _ = LAW_CONFIGS[law]
    event = SEED_EVENTS[seed]
    cfg = seed_config(load_config("config.yaml"), seed, coupling_label, LAW_CONFIGS[law][2])
    checkpoint = checkpoint_world(cfg, event)
    rows = []
    for target_dict in target_dicts:
        target = CommittorTarget(**target_dict)
        existing_path = row_json_path(output_dir, target)
        if existing_path.exists() and not bool(options["refresh"]):
            rows.append(json.loads(existing_path.read_text(encoding="utf-8")))
            continue
        state_path = final_state_path(output_dir, target) if save_final_states else None
        row = {
            "seed": target.seed,
            "law": target.law,
            "coupling": target.coupling,
            "condition": target.condition,
            "forced_v": target.forced_v,
            "sample_index": target.sample_index,
            "continuation_seed": target.continuation_seed,
            "divergence_tick": event.divergence_tick,
            "target": event.target,
        }
        result = run_continuation(
            checkpoint,
            cfg,
            event,
            target.forced_v,
            target.continuation_seed,
            early_absorber,
            f"seed={target.seed} law={target.law} condition={target.condition} sample={target.sample_index}",
            state_path,
            row,
        )
        row.update(result)
        atomic_write_json(existing_path, row)
        rows.append(row)
    return rows


def parse_target_file(path: Path) -> list[CommittorTarget]:
    targets = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row in reader:
            seed = int(row["seed"])
            law = str(row["law"])
            condition = str(row["condition"])
            sample_index = int(row["sample_index"])
            targets.append(make_committor_target(seed, law, condition, sample_index, int(row.get("rng_seed_base", 20260622))))
    return targets


def make_committor_target(
    seed: int,
    law: str,
    condition: str,
    sample_index: int,
    rng_seed_base: int,
) -> CommittorTarget:
    law_index, _, coupling = LAW_CONFIGS[law]
    condition_index = 0 if condition == "protected_vector" else 1
    event = SEED_EVENTS[seed]
    forced_v = event.protected_v if condition == "protected_vector" else event.absorber_v
    continuation_seed = (
        rng_seed_base
        + seed * 1_000_000
        + law_index * 100_000
        + condition_index * 10_000
        + sample_index
    )
    return CommittorTarget(seed, law, condition, sample_index, continuation_seed, forced_v, coupling)


def generated_targets(args: argparse.Namespace) -> list[CommittorTarget]:
    if args.targets:
        return parse_target_file(Path(args.targets))
    targets = []
    for seed in args.seeds:
        for law in args.laws:
            for condition in args.conditions:
                for sample_index in args.sample_indexes:
                    targets.append(make_committor_target(seed, law, condition, sample_index, args.rng_seed_base))
    return targets


def run_committor(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    targets = generated_targets(args)
    groups: dict[tuple[int, str], list[CommittorTarget]] = {}
    for target in targets:
        groups.setdefault((target.seed, target.law), []).append(target)
    options = {
        "output_dir": output_dir.as_posix(),
        "early_absorber": args.early_absorber,
        "save_final_states": not args.no_save_final_states,
        "refresh": args.refresh,
    }
    jobs = [
        (key, [asdict(target) for target in sorted(group, key=lambda item: (item.condition, item.sample_index))], options)
        for key, group in sorted(groups.items())
    ]
    row_groups = run_tasks(jobs, args.jobs, run_committor_group)
    rows = [row for group in row_groups for row in group]
    rows.sort(key=lambda row: (int(row["seed"]), str(row["law"]), str(row["condition"]), int(row["sample_index"])))
    write_csv(output_dir / "committor_rows.csv", rows, RAW_FIELDNAMES)
    summary_rows = summarize(rows)
    if summary_rows:
        write_csv(output_dir / "committor_summary.csv", summary_rows, list(summary_rows[0].keys()))
    atomic_write_json(
        output_dir / "committor_summary.json",
        {
            "mode": "committor",
            "jobs": args.jobs,
            "target_count": len(targets),
            "row_count": len(rows),
            "output_dir": output_dir.as_posix(),
            "summary_rows": summary_rows,
        },
    )


def run_tasks(tasks: list[Any], jobs: int, fn: Any) -> list[Any]:
    if jobs <= 1:
        return [fn(task) for task in tasks]
    results = []
    with ProcessPoolExecutor(max_workers=jobs) as executor:
        futures = [executor.submit(fn, task) for task in tasks]
        for future in as_completed(futures):
            results.append(future.result())
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parallel replay utilities for golden and targeted Iota checks.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    golden = subparsers.add_parser("golden", help="Run branch-sensitive golden replays in parallel.")
    golden.add_argument("--seeds", type=int, nargs="+", default=[42, 56], choices=[42, 56])
    golden.add_argument("--jobs", type=int, default=4)
    golden.add_argument("--output", default="output/findings/parallel_golden_replay.json")

    committor = subparsers.add_parser("committor", help="Run targeted committor continuations in parallel groups.")
    committor.add_argument("--jobs", type=int, default=4)
    committor.add_argument("--output-dir", default="output/findings/parallel_committor")
    committor.add_argument("--targets", default=None, help="CSV/TSV with seed, law, condition, sample_index columns.")
    committor.add_argument("--seeds", type=int, nargs="+", default=[42, 56], choices=[42, 56])
    committor.add_argument("--laws", choices=["low", "high"], nargs="+", default=["low", "high"])
    committor.add_argument(
        "--conditions",
        choices=["protected_vector", "absorber_vector"],
        nargs="+",
        default=["protected_vector", "absorber_vector"],
    )
    committor.add_argument("--sample-indexes", type=int, nargs="+", required=False, default=[0])
    committor.add_argument("--rng-seed-base", type=int, default=20260622)
    committor.add_argument("--early-absorber", action="store_true")
    committor.add_argument("--no-save-final-states", action="store_true")
    committor.add_argument("--refresh", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "golden":
        run_golden(args)
    elif args.mode == "committor":
        run_committor(args)
    else:
        raise SystemExit(f"unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
