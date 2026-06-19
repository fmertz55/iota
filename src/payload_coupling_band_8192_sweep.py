from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any

import yaml

from experiment_db import open_database
from experiment_runner import run_experiment
from iota_rig import load_config
from two_nucleus_payload_contrast_8192_probe import fixed_iotas


SEED = 42
OBJECTIVE = "256 medium two-nucleus payload coupling band"
BASE_VARIANT = "A_4774_256_cube26_2_nuclei_medium_payload_4_vs_0"
COUPLINGS = [
    ("0_25", 0.25),
    ("0_5", 0.50),
    ("0_75", 0.75),
    ("1_0", 1.00),
]


def variant_name(label: str) -> str:
    return f"{BASE_VARIANT}_cross_{label}_8192"


def probe_config(base_cfg: dict[str, Any], label: str, coupling: float) -> dict[str, Any]:
    cfg = copy.deepcopy(base_cfg)
    cfg.get("experiment", {}).pop("id", None)
    cfg.setdefault("experiment", {})["variant"] = variant_name(label)
    cfg["experiment"]["nucleus_count"] = 2
    cfg["experiment"]["nucleus_separation"] = "medium"
    cfg["experiment"]["nucleus_payloads"] = "4_vs_0"
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
            "same_payload_coupling": 1.0,
            "cross_payload_coupling": coupling,
        }
    )

    cfg.setdefault("run", {})
    cfg["run"].update(
        {
            "ticks": 8192,
            "metric_every": 256,
            "heartbeat_every": 256,
            "commit_metrics": True,
            "snapshot_every": 8192,
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
            FROM parameters variant
            JOIN summary_metrics final_tick
              ON final_tick.experiment_id = variant.experiment_id
             AND final_tick.metric_name = 'final_tick'
            WHERE variant.parameter_name = 'experiment.variant'
            """
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
        "Payload-coupling compatibility band at 256^3. Medium-separated A_4774 nuclei "
        "with P=4 vs P=0. same_payload_coupling=1.0; cross_payload_coupling varies. "
        "Attenuation applies only to already-active targets."
    )

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=config_path.resolve().parent,
        prefix=".iota_payload_coupling_band_8192_",
        suffix=".yaml",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        for label, coupling in COUPLINGS:
            variant = variant_name(label)
            if variant in completed:
                print(f"Skipping completed variant={variant}")
                continue
            cfg = probe_config(base_cfg, label, coupling)
            temp_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            run_experiment(
                str(temp_path),
                f"256 payload coupling band: cross_payload_coupling={coupling}",
                notes,
                force=True,
            )
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
