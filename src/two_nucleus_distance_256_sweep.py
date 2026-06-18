from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any

import yaml

from experiment_db import open_database
from experiment_runner import run_experiment
from iota_rig import load_config


BASE_COORDS = [
    [7, 54, 1],
    [16, 33, 14],
    [42, 43, 24],
    [52, 26, 55],
]

DISTANCE_OFFSETS = {
    "medium": [64, 0, 0],
    "near": [24, 0, 0],
}

AMPLITUDES = [4, 7, 7, 4]
UNIFORM_P = [4, 4, 4, 4]
UNIFORM_V = [49, 49, 49, 49]
SEED = 42
OBJECTIVE = "256 two-nucleus distance interaction probe"


def translated_coord(coord: list[int], offset: list[int]) -> list[int]:
    return [coord[index] + offset[index] for index in range(3)]


def fixed_iotas(distance_label: str) -> list[dict[str, int | list[int]]]:
    iotas: list[dict[str, int | list[int]]] = []
    for offset in ([0, 0, 0], DISTANCE_OFFSETS[distance_label]):
        for index, coord in enumerate(BASE_COORDS):
            iotas.append(
                {
                    "coord": translated_coord(coord, offset),
                    "A": AMPLITUDES[index],
                    "R": 7,
                    "V": UNIFORM_V[index],
                    "P": UNIFORM_P[index],
                }
            )
    return iotas


def variant_config(base_cfg: dict[str, Any], distance_label: str) -> dict[str, Any]:
    cfg = copy.deepcopy(base_cfg)
    cfg.get("experiment", {}).pop("id", None)
    cfg.setdefault("experiment", {})["variant"] = f"A_4774_256_cube26_2_nuclei_{distance_label}"
    cfg["experiment"]["nucleus_count"] = 2
    cfg["experiment"]["nucleus_separation"] = distance_label
    cfg["experiment"]["objective"] = OBJECTIVE

    cfg.setdefault("grid", {})
    cfg["grid"].update(
        {
            "size": 256,
            "wrap": True,
        }
    )

    cfg.setdefault("init", {})
    cfg["init"].update(
        {
            "seed": SEED,
            "active_iotas": 8,
            "mode": "fixed",
            "fixed_iotas": fixed_iotas(distance_label),
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
            "metric_every": 256,
            "snapshot_every": 4096,
            "stop_active_iotas": 100000,
            "stop_coherence_ratio": None,
            "stop_coherence_min_active": 1000,
            "dashboard": False,
        }
    )
    return cfg


def completed_variants(database_path: Path) -> set[str]:
    conn = open_database(database_path)
    try:
        rows = conn.execute(
            """
            SELECT variant.parameter_value
            FROM experiments experiment
            JOIN parameters variant
              ON variant.experiment_id = experiment.experiment_id
             AND variant.parameter_name = 'experiment.variant'
            JOIN summary_metrics final_tick
              ON final_tick.experiment_id = experiment.experiment_id
             AND final_tick.metric_name = 'final_tick'
            WHERE experiment.objective = ?
            """,
            (OBJECTIVE,),
        ).fetchall()
    finally:
        conn.close()
    return {str(variant).strip('"') for (variant,) in rows}


def main() -> None:
    config_path = Path("config.yaml")
    base_cfg = load_config(config_path)
    database_path = Path(base_cfg.get("lab", {}).get("database", "data/iota_lab.db"))
    completed = completed_variants(database_path)
    notes = (
        "Two-nucleus distance interaction probe at 256^3: same A_4774 composition, seed=42, "
        "uniform P=4, uniform V=49, R=7, p=0.005, valence=2, neighbor_mode=cube26. "
        "Far baseline is existing IOTA-000269; this run adds medium and near separations. "
        "Global LCF early stop disabled."
    )

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=config_path.resolve().parent,
        prefix=".iota_two_nucleus_distance_256_",
        suffix=".yaml",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        for distance_label in ("medium", "near"):
            variant = f"A_4774_256_cube26_2_nuclei_{distance_label}"
            if variant in completed:
                print(f"Skipping completed variant={variant}")
                continue
            cfg = variant_config(base_cfg, distance_label)
            temp_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            run_experiment(
                str(temp_path),
                f"256 two-nucleus distance probe: {distance_label}",
                notes,
                force=True,
            )
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
