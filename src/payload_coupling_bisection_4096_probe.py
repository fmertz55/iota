from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from experiment_db import open_database
from experiment_runner import run_experiment
from iota_rig import load_config
from payload_coupling_bracket_4096_sweep import probe_config, variant_name


LABEL = "0_209375"
COUPLING = 0.209375
OBJECTIVE = "256 payload coupling bisection probe"


def already_completed(database_path: Path) -> bool:
    variant = variant_name(LABEL)
    conn = open_database(database_path)
    try:
        row = conn.execute(
            """
            SELECT 1
            FROM parameters variant
            JOIN summary_metrics final_tick
              ON final_tick.experiment_id = variant.experiment_id
             AND final_tick.metric_name = 'final_tick'
            WHERE variant.parameter_name = 'experiment.variant'
              AND variant.parameter_value = ?
            LIMIT 1
            """,
            (f'"{variant}"',),
        ).fetchone()
    finally:
        conn.close()
    return row is not None


def main() -> None:
    config_path = Path("config.yaml")
    base_cfg = load_config(config_path)
    database_path = Path(base_cfg.get("lab", {}).get("database", "data/iota_lab.db"))
    if already_completed(database_path):
        print(f"Skipping completed variant={variant_name(LABEL)}")
        return

    cfg = probe_config(base_cfg, LABEL, COUPLING)
    cfg["experiment"]["objective"] = OBJECTIVE
    notes = (
        "Single bisection probe between fragmented/protected 0.20 and absorber 0.25. "
        "Judge by hierarchy metrics, not LCF alone."
    )

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=config_path.resolve().parent,
        prefix=".iota_payload_coupling_bisection_4096_",
        suffix=".yaml",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        temp_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        run_experiment(
            str(temp_path),
            f"256 payload coupling bisection: cross_payload_coupling={COUPLING}",
            notes,
            force=True,
        )
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
