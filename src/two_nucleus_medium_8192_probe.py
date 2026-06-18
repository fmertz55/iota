from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any

import yaml

from experiment_db import open_database
from experiment_runner import run_experiment
from iota_rig import load_config
from two_nucleus_distance_256_sweep import fixed_iotas


SEED = 42
OBJECTIVE = "256 medium two-nucleus long-time probe"
VARIANT = "A_4774_256_cube26_2_nuclei_medium_8192"


def probe_config(base_cfg: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(base_cfg)
    cfg.get("experiment", {}).pop("id", None)
    cfg.setdefault("experiment", {})["variant"] = VARIANT
    cfg["experiment"]["nucleus_count"] = 2
    cfg["experiment"]["nucleus_separation"] = "medium"
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
            "fixed_iotas": fixed_iotas("medium"),
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
            "ticks": 8192,
            "metric_every": 256,
            "snapshot_every": 8192,
            "stop_active_iotas": 100000,
            "stop_coherence_ratio": None,
            "stop_coherence_min_active": 1000,
            "dashboard": False,
        }
    )
    return cfg


def already_completed(database_path: Path) -> bool:
    conn = open_database(database_path)
    try:
        row = conn.execute(
            """
            SELECT 1
            FROM experiments experiment
            JOIN parameters variant
              ON variant.experiment_id = experiment.experiment_id
             AND variant.parameter_name = 'experiment.variant'
             AND variant.parameter_value = ?
            JOIN summary_metrics final_tick
              ON final_tick.experiment_id = experiment.experiment_id
             AND final_tick.metric_name = 'final_tick'
            WHERE experiment.objective = ?
            LIMIT 1
            """,
            (f'"{VARIANT}"', OBJECTIVE),
        ).fetchone()
    finally:
        conn.close()
    return row is not None


def main() -> None:
    config_path = Path("config.yaml")
    base_cfg = load_config(config_path)
    database_path = Path(base_cfg.get("lab", {}).get("database", "data/iota_lab.db"))
    if already_completed(database_path):
        print("Skipping completed medium 8192 probe")
        return

    notes = (
        "Long-time medium-separation two-nucleus probe at 256^3. This extends the "
        "IOTA-000271 medium interaction case from 4096 to 8192 ticks to test whether "
        "two-domain coexistence persists or eventually integrates."
    )

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=config_path.resolve().parent,
        prefix=".iota_two_nucleus_medium_8192_",
        suffix=".yaml",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        cfg = probe_config(base_cfg)
        temp_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        run_experiment(
            str(temp_path),
            "256 medium two-nucleus long-time probe",
            notes,
            force=True,
        )
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
