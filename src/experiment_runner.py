from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from dashboard import save_dashboard
from experiment_db import (
    config_hash,
    create_experiment,
    display_value,
    insert_metric,
    insert_summary_metrics,
    open_database,
)
from iota_rig import initial_conditions, init_world, load_config, save_scatter, save_slice, step
from metrics import (
    collect_metrics,
    metrics_summary,
    save_experiment_comparison_plots,
    save_run_metrics,
)


def ensure_experiment_template(experiments_dir: Path) -> None:
    experiments_dir.mkdir(parents=True, exist_ok=True)
    template = experiments_dir / "IOTA_EXPERIMENT_TEMPLATE.md"
    if template.exists():
        return
    template.write_text(
        """# IOTA-000000

## Timestamp

## Objective

## Changed Parameter

- Parameter:
- Old Value:
- New Value:

## Configuration Hash

## Notes

## Initial Conditions

## Metrics Summary

## Result

## Next Experiment
""",
        encoding="utf-8",
    )


def write_experiment_notebook(
    experiments_dir: Path,
    experiment_id: int,
    timestamp: str,
    objective: str,
    notes: str,
    cfg_hash: str,
    diffs: list[tuple[str, str | None, str | None]],
    summary: dict[str, float],
    output_dir: Path,
    init_metadata: dict[str, float],
) -> None:
    ensure_experiment_template(experiments_dir)
    label = f"IOTA-{experiment_id:06d}"
    if not diffs:
        diff_text = "- Changed Parameter: none\n- Old Value: n/a\n- New Value: n/a"
    elif len(diffs) == 1:
        name, old, new = diffs[0]
        diff_text = (
            f"- Changed Parameter: {name}\n"
            f"- Old Value: {display_value(old)}\n"
            f"- New Value: {display_value(new)}"
        )
    else:
        diff_text = "\n".join(
            f"- {name}: {display_value(old)} -> {display_value(new)}"
            for name, old, new in diffs
        )

    metrics_text = "\n".join(
        f"- {name}: {value}"
        for name, value in summary.items()
    )
    density_text = (
        f"- Initial Active Iotas: {int(init_metadata['initial_active_iotas'])}\n"
        f"- Total Iotas: {int(init_metadata['total_iotas'])}\n"
        f"- Initial Density: {init_metadata['initial_density']:.12f}\n"
        f"- Initial Density Percent: {init_metadata['initial_density_percent']:.6f}%"
    )
    (experiments_dir / f"{label}.md").write_text(
        f"""# {label}

## Timestamp

{timestamp}

## Objective

{objective}

## Changed Parameter

{diff_text}

## Configuration Hash

{cfg_hash}

## Notes

{notes or "None"}

## Initial Conditions

{density_text}

## Output

{output_dir}

## Metrics Summary

{metrics_text}

## Result

Pending human interpretation.

## Next Experiment

""",
        encoding="utf-8",
    )


def lab_paths(config_path: str | Path, cfg: dict[str, Any]) -> tuple[Path, Path, Path, Path]:
    base_dir = Path(config_path).resolve().parent
    lab_cfg = cfg.get("lab", {})
    db_path = base_dir / lab_cfg.get("database", "data/iota_lab.db")
    experiments_dir = base_dir / lab_cfg.get("experiments_dir", "experiments")
    output_root = base_dir / cfg["run"].get("output_dir", "output")
    comparison_dir = output_root / "experiments"
    return db_path, experiments_dir, output_root, comparison_dir


def run_experiment(config_path: str, objective: str | None, notes: str, force: bool) -> None:
    cfg = load_config(config_path)
    experiment_cfg = cfg.get("experiment", {})
    resolved_objective = objective or experiment_cfg.get("objective", "Unspecified")
    init_metadata = initial_conditions(cfg)
    db_path, experiments_dir, output_root, comparison_dir = lab_paths(config_path, cfg)
    conn = open_database(db_path)
    experiment_id, timestamp, diffs = create_experiment(conn, cfg, resolved_objective, notes, force)
    label = f"IOTA-{experiment_id:06d}"

    world = init_world(cfg)
    out = output_root / label
    out.mkdir(parents=True, exist_ok=True)

    ticks = int(cfg["run"].get("ticks", 256))
    snapshot_every = int(cfg["run"].get("snapshot_every", 8))
    run_metrics: list[dict[str, float]] = []
    start = time.perf_counter()

    print(
        f"initial_density={int(init_metadata['initial_active_iotas'])}/"
        f"{int(init_metadata['total_iotas'])} "
        f"({init_metadata['initial_density_percent']:.6f}%)"
    )

    save_slice(world, out, 0, cfg)
    save_scatter(world, out, 0, cfg)
    initial_metric = collect_metrics(world, 0)
    run_metrics.append(initial_metric)
    insert_metric(conn, experiment_id, initial_metric)
    dashboard_path = save_dashboard(conn, output_root)

    for tick in range(1, ticks + 1):
        extras = step(world, cfg)
        metric = collect_metrics(world, tick, extras)
        run_metrics.append(metric)
        insert_metric(conn, experiment_id, metric)
        if tick % snapshot_every == 0 or tick == ticks:
            save_slice(world, out, tick, cfg)
            save_scatter(world, out, tick, cfg)
            save_run_metrics(run_metrics, out)
            dashboard_path = save_dashboard(conn, output_root)
            print(
                f"tick={tick} active={metric['active_iotas']} "
                f"largest_coherence={metric['largest_coherence']} "
                f"coherences={metric['coherence_count']} "
                f"entropy={metric['entropy']:.3f}"
            )

    save_run_metrics(run_metrics, out)
    elapsed = time.perf_counter() - start
    summary = metrics_summary(run_metrics, elapsed, init_metadata)
    insert_summary_metrics(conn, experiment_id, summary)
    write_experiment_notebook(
        experiments_dir,
        experiment_id,
        timestamp,
        resolved_objective,
        notes,
        config_hash(cfg),
        diffs,
        summary,
        out,
        init_metadata,
    )
    save_experiment_comparison_plots(conn, comparison_dir)
    dashboard_path = save_dashboard(conn, output_root)
    conn.close()

    if not diffs:
        print("Changed parameter: none")
    elif len(diffs) == 1:
        name, old, new = diffs[0]
        print(f"Changed parameter: {name} {display_value(old)} -> {display_value(new)}")
    else:
        print(f"Forced run with {len(diffs)} changed parameters")
    print(f"Experiment: {label}")
    print(f"Database: {db_path}")
    print(f"Notebook: {experiments_dir / f'{label}.md'}")
    print(f"Output: {out}")
    print(f"Experiment plots: {comparison_dir}")
    print(f"Dashboard: {dashboard_path}")
