from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from experiment_db import open_database
from experiment_runner import run_experiment
from iota_rig import load_config
from payload_coupling_bracket_4096_sweep import probe_config


OBJECTIVE = "256 payload coupling boundary seed ensemble"
BASE_VARIANT = "A_4774_256_cube26_2_nuclei_medium_payload_4_vs_0"
COUPLINGS = [
    ("0_209375", 0.209375),
    ("0_2109375", 0.2109375),
]
SEEDS = list(range(42, 72))


def variant_name(label: str, seed: int) -> str:
    return f"{BASE_VARIANT}_cross_{label}_seed_{seed}_4096"


def ensemble_config(base_cfg: dict, label: str, coupling: float, seed: int) -> dict:
    cfg = probe_config(base_cfg, label, coupling)
    cfg["experiment"]["objective"] = OBJECTIVE
    cfg["experiment"]["variant"] = variant_name(label, seed)
    cfg["experiment"]["seed_ensemble"] = "42_71"
    cfg["init"]["seed"] = seed
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
        "Seed-ensemble test for the protected/absorber boundary. Same 256^3 "
        "medium-separated P=4 vs P=0 setup; only init.seed and "
        "cross_payload_coupling vary. Classify each run as protected or absorber "
        "from final LCF and hierarchy metrics."
    )

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=config_path.resolve().parent,
        prefix=".iota_payload_coupling_seed_ensemble_4096_",
        suffix=".yaml",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        for seed in SEEDS:
            for label, coupling in COUPLINGS:
                variant = variant_name(label, seed)
                if variant in completed:
                    print(f"Skipping completed variant={variant}")
                    continue
                cfg = ensemble_config(base_cfg, label, coupling, seed)
                temp_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
                run_experiment(
                    str(temp_path),
                    f"256 payload coupling seed ensemble: p={coupling}, seed={seed}",
                    notes,
                    force=True,
                )
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
