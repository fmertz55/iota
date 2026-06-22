from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from experiment_db import open_database
from experiment_runner import run_experiment
from iota_rig import load_config
from payload_coupling_bracket_4096_sweep import probe_config


OBJECTIVE = "Payload coupling boundary scale probe"
BASE_VARIANT = "A_4774_cube26_2_nuclei_medium_payload_4_vs_0"
SEED = 42
COUPLINGS = [
    ("0_209375", 0.209375),
    ("0_2109375", 0.2109375),
]
GRID_SIZES = [128, 256, 512]


def variant_name(size: int, label: str) -> str:
    return f"{BASE_VARIANT}_grid_{size}_cross_{label}_seed_{SEED}_4096"


def scale_config(base_cfg: dict, size: int, label: str, coupling: float) -> dict:
    cfg = probe_config(base_cfg, label, coupling)
    cfg["experiment"]["objective"] = OBJECTIVE
    cfg["experiment"]["variant"] = variant_name(size, label)
    cfg["experiment"]["scale_probe"] = f"grid_{size}"
    cfg["grid"]["size"] = size
    cfg["init"]["seed"] = SEED
    cfg["run"]["snapshot_every"] = 4096
    cfg["run"]["dashboard"] = False
    cfg["run"]["stop_active_iotas"] = 500000 if size >= 512 else 100000
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
        "Scale probe for the protected/absorber boundary. Uses the same absolute "
        "medium-separated A_4774 coordinates where valid; grid sizes are 128, 256, "
        "and 512. The 64^3 grid is intentionally excluded because the 64-cell "
        "medium offset would wrap and overlap nuclei."
    )

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=config_path.resolve().parent,
        prefix=".iota_payload_coupling_scale_boundary_",
        suffix=".yaml",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        for size in GRID_SIZES:
            for label, coupling in COUPLINGS:
                variant = variant_name(size, label)
                if variant in completed:
                    print(f"Skipping completed variant={variant}")
                    continue
                cfg = scale_config(base_cfg, size, label, coupling)
                temp_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
                run_experiment(
                    str(temp_path),
                    f"payload coupling scale boundary: grid={size}, p={coupling}",
                    notes,
                    force=True,
                )
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
