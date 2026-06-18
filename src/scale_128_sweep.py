from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any

import yaml

from experiment_db import open_database
from experiment_runner import run_experiment
from iota_rig import load_config


COORDS = [
    [7, 54, 1],
    [16, 33, 14],
    [42, 43, 24],
    [52, 26, 55],
]

AMPLITUDES = [4, 7, 7, 4]
UNIFORM_P = [4, 4, 4, 4]
UNIFORM_V = [49, 49, 49, 49]
SEEDS = [42, 43, 44, 45, 46]
OBJECTIVE = "128 grid scale test"


def fixed_iotas() -> list[dict[str, int | list[int]]]:
    return [
        {
            "coord": coord,
            "A": AMPLITUDES[index],
            "R": 7,
            "V": UNIFORM_V[index],
            "P": UNIFORM_P[index],
        }
        for index, coord in enumerate(COORDS)
    ]


def variant_config(base_cfg: dict[str, Any], seed: int) -> dict[str, Any]:
    cfg = copy.deepcopy(base_cfg)
    cfg.get("experiment", {}).pop("id", None)
    cfg.setdefault("experiment", {})["variant"] = "A_4774_128_cube26"
    cfg["experiment"]["objective"] = OBJECTIVE

    cfg.setdefault("grid", {})
    cfg["grid"].update(
        {
            "size": 128,
            "wrap": True,
        }
    )

    cfg.setdefault("init", {})
    cfg["init"].update(
        {
            "seed": seed,
            "active_iotas": 4,
            "mode": "fixed",
            "fixed_iotas": fixed_iotas(),
            "range_range": [7, 7],
        }
    )

    cfg.setdefault("vectors", {})
    cfg["vectors"].update(
        {
            "mode": "cube26",
            "vector_count": 64,
        }
    )

    cfg.setdefault("constants", {})
    cfg["constants"].update(
        {
            "amplitude_coupling": 1.0,
            "range_coupling": 1.0,
            "payload_takeover": 0.5,
            "mutation_rate": 0.0,
            "decay_mode": "inverse_square",
            "conservation": "soft",
            "valence": 2,
            "bond_probability": 0.005,
            "neighbor_mode": "cube26",
        }
    )

    cfg.setdefault("run", {})
    cfg["run"].update(
        {
            "ticks": 4096,
            "metric_every": 128,
            "snapshot_every": 4096,
            "stop_active_iotas": 100000,
            "stop_coherence_ratio": 0.97,
            "stop_coherence_min_active": 1000,
            "dashboard": False,
        }
    )
    return cfg


def completed_seeds(database_path: Path) -> set[int]:
    conn = open_database(database_path)
    try:
        rows = conn.execute(
            """
            SELECT seed.parameter_value
            FROM experiments experiment
            JOIN parameters variant
              ON variant.experiment_id = experiment.experiment_id
             AND variant.parameter_name = 'experiment.variant'
             AND variant.parameter_value = '"A_4774_128_cube26"'
            JOIN parameters seed
              ON seed.experiment_id = experiment.experiment_id
             AND seed.parameter_name = 'init.seed'
            JOIN summary_metrics final_tick
              ON final_tick.experiment_id = experiment.experiment_id
             AND final_tick.metric_name = 'final_tick'
            WHERE experiment.objective = ?
            """,
            (OBJECTIVE,),
        ).fetchall()
    finally:
        conn.close()
    return {int(seed) for (seed,) in rows}


def main() -> None:
    config_path = Path("config.yaml")
    base_cfg = load_config(config_path)
    database_path = Path(base_cfg.get("lab", {}).get("database", "data/iota_lab.db"))
    completed = completed_seeds(database_path)
    notes = (
        "Scale diagnostic: A_4774 winner on grid.size=128 with same absolute fixed "
        "coordinates, uniform P=4, uniform V=49, R=7, p=0.005, valence=2, "
        "neighbor_mode=cube26. Coordinates are intentionally not scaled, so only "
        "available dark volume and boundary distance change."
    )

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=config_path.resolve().parent,
        prefix=".iota_scale_128_",
        suffix=".yaml",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        for seed in SEEDS:
            if seed in completed:
                print(f"Skipping completed seed={seed}")
                continue
            cfg = variant_config(base_cfg, seed)
            temp_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            run_experiment(
                str(temp_path),
                f"128 scale test: A_4774 cube26 seed={seed}",
                notes,
                force=True,
            )
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
