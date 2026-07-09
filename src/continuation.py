from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from iota_rig import World, load_world_state, save_world_state


OUTCOME_CLASSES = ("absorber", "high_dominant", "protected")


def clone_world(world: World, rng_seed: int) -> World:
    return World(
        active=world.active.copy(),
        A=world.A.copy(),
        R=world.R.copy(),
        V=world.V.copy(),
        P=world.P.copy(),
        latent_A=world.latent_A.copy(),
        angular_L=world.angular_L.copy() if world.angular_L is not None else None,
        initial_total_A=int(world.initial_total_A),
        ledger_enabled=bool(world.ledger_enabled),
        previous_active=world.previous_active.copy(),
        previous_V=world.previous_V.copy(),
        vectors=world.vectors.copy(),
        vector_behaviors=tuple(world.vector_behaviors),
        wrap=world.wrap,
        rng=np.random.default_rng(rng_seed),
    )


def deterministic_continuation_seed(
    base_seed: int,
    checkpoint_tick: int,
    sample_index: int,
    stream_index: int = 0,
) -> int:
    return int(
        base_seed
        + int(checkpoint_tick) * 1_000_000
        + int(stream_index) * 100_000
        + int(sample_index)
    )


def save_checkpoint(
    world: World,
    path: str | Path,
    metadata: dict[str, Any] | None = None,
) -> None:
    save_world_state(world, Path(path), metadata)


def load_checkpoint(path: str | Path) -> World:
    return load_world_state(Path(path))


def connectivity_metric(metric: Mapping[str, Any], name: str, connectivity: str) -> float:
    if connectivity == "face6":
        key = f"{name}_face6"
        if key in metric:
            return float(metric[key])
        return float(metric[name])
    return float(metric[f"{name}_{connectivity}"])


def classify_outcome(
    metric: Mapping[str, Any],
    connectivity: str = "cube26",
    min_active: int = 1000,
    absorber_lcf: float = 0.95,
    high_dominant_lcf: float = 0.90,
) -> str:
    active_iotas = int(float(metric["active_iotas"]))
    lcf = connectivity_metric(metric, "coherence_ratio", connectivity)
    if active_iotas >= min_active and lcf >= absorber_lcf:
        return "absorber"
    if active_iotas >= min_active and lcf >= high_dominant_lcf:
        return "high_dominant"
    return "protected"


def entropy_from_counts(counts: Mapping[str, int]) -> float:
    total = sum(int(value) for value in counts.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in counts.values():
        count = int(value)
        if count <= 0:
            continue
        probability = count / total
        entropy -= probability * math.log(probability)
    return float(entropy)


def normalized_outcome_entropy(counts: Mapping[str, int]) -> float:
    if len(OUTCOME_CLASSES) <= 1:
        return 0.0
    return float(entropy_from_counts(counts) / math.log(len(OUTCOME_CLASSES)))


def outcome_counts(rows: list[Mapping[str, Any]], key: str = "classification") -> dict[str, int]:
    counts = {name: 0 for name in OUTCOME_CLASSES}
    for row in rows:
        value = str(row.get(key, ""))
        if value not in counts:
            continue
        counts[value] += 1
    return counts
