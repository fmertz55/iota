from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any

import yaml

from experiment_runner import run_experiment
from iota_rig import load_config


COORDS = [
    [7, 54, 1],
    [16, 33, 14],
    [42, 43, 24],
    [52, 26, 55],
]

UNIFORM_P = [4, 4, 4, 4]
UNIFORM_V = [49, 49, 49, 49]

VARIANTS = [
    ("A_4444", [4, 4, 4, 4]),
    ("A_5444", [5, 4, 4, 4]),
    ("A_6444", [6, 4, 4, 4]),
    ("A_7444", [7, 4, 4, 4]),
    ("A_7744", [7, 7, 4, 4]),
    ("A_7774", [7, 7, 7, 4]),
    ("A_7777", [7, 7, 7, 7]),
]


def fixed_iotas(amplitudes: list[int]) -> list[dict[str, int | list[int]]]:
    return [
        {
            "coord": coord,
            "A": amplitudes[index],
            "R": 7,
            "V": UNIFORM_V[index],
            "P": UNIFORM_P[index],
        }
        for index, coord in enumerate(COORDS)
    ]


def variant_config(base_cfg: dict[str, Any], name: str, amplitudes: list[int]) -> dict[str, Any]:
    cfg = copy.deepcopy(base_cfg)
    cfg.get("experiment", {}).pop("id", None)
    cfg.setdefault("experiment", {})["variant"] = name
    cfg["experiment"]["objective"] = "Fixed amplitude spread sweep"

    cfg.setdefault("init", {})
    cfg["init"].update(
        {
            "seed": 44,
            "active_iotas": 4,
            "mode": "fixed",
            "fixed_iotas": fixed_iotas(amplitudes),
            "range_range": [7, 7],
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
        }
    )

    cfg.setdefault("run", {})
    cfg["run"].update(
        {
            "ticks": 4096,
            "snapshot_every": 256,
            "stop_active_iotas": 30000,
            "stop_coherence_ratio": 0.97,
            "stop_coherence_min_active": 1000,
        }
    )
    return cfg


def main() -> None:
    config_path = Path("config.yaml")
    base_cfg = load_config(config_path)
    notes = (
        "Fixed amplitude spread diagnostic: same four seed-44 coordinates, uniform P=4, "
        "uniform V=49, p=0.005, N0=4, valence=2, R=7. Variants isolate A spread."
    )

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=config_path.resolve().parent,
        prefix=".iota_amplitude_spread_",
        suffix=".yaml",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        for name, amplitudes in VARIANTS:
            cfg = variant_config(base_cfg, name, amplitudes)
            temp_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            run_experiment(
                str(temp_path),
                f"Fixed amplitude spread variant: {name}",
                notes,
                force=True,
            )
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
