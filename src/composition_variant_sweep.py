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

UNIFORM_A = [4, 4, 4, 4]
DIVERSE_A = [2, 7, 7, 3]

UNIFORM_P = [4, 4, 4, 4]
DIVERSE_P = [2, 1, 0, 5]

UNIFORM_V = [49, 49, 49, 49]
DIVERSE_V = [6, 34, 54, 43]

VARIANTS = [
    ("A_diversity_only", DIVERSE_A, UNIFORM_P, UNIFORM_V),
    ("P_diversity_only", UNIFORM_A, DIVERSE_P, UNIFORM_V),
    ("V_diversity_only", UNIFORM_A, UNIFORM_P, DIVERSE_V),
    ("A_P_diversity", DIVERSE_A, DIVERSE_P, UNIFORM_V),
    ("A_V_diversity", DIVERSE_A, UNIFORM_P, DIVERSE_V),
    ("P_V_diversity", UNIFORM_A, DIVERSE_P, DIVERSE_V),
    ("A_P_V_diversity", DIVERSE_A, DIVERSE_P, DIVERSE_V),
]


def fixed_iotas(amplitudes: list[int], payloads: list[int], vectors: list[int]) -> list[dict[str, int | list[int]]]:
    return [
        {
            "coord": coord,
            "A": amplitudes[index],
            "R": 7,
            "V": vectors[index],
            "P": payloads[index],
        }
        for index, coord in enumerate(COORDS)
    ]


def variant_config(base_cfg: dict[str, Any], name: str, amplitudes: list[int], payloads: list[int], vectors: list[int]) -> dict[str, Any]:
    cfg = copy.deepcopy(base_cfg)
    cfg.get("experiment", {}).pop("id", None)
    cfg.setdefault("experiment", {})["variant"] = name
    cfg["experiment"]["objective"] = "Fixed initial composition variant sweep"

    cfg.setdefault("init", {})
    cfg["init"].update(
        {
            "seed": 44,
            "active_iotas": 4,
            "mode": "fixed",
            "fixed_iotas": fixed_iotas(amplitudes, payloads, vectors),
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
        "Fixed composition diagnostic: same four seed-44 coordinates, p=0.005, "
        "N0=4, valence=2, R=7. Variants isolate A, P, and V/behavior diversity."
    )

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=config_path.resolve().parent,
        prefix=".iota_fixed_composition_",
        suffix=".yaml",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        for name, amplitudes, payloads, vectors in VARIANTS:
            cfg = variant_config(base_cfg, name, amplitudes, payloads, vectors)
            temp_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            run_experiment(
                str(temp_path),
                f"Fixed composition variant: {name}",
                notes,
                force=True,
            )
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
