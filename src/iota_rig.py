from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import numpy as np
import yaml
import matplotlib.pyplot as plt


# Field layout: four arrays, not one giant object array.
# active: bool/non-dark marker
# A: amplitude 0..7
# R: range 0..7
# V: vector 0..63
# P: payload 0..7

CUBE6 = np.array([
    (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)
], dtype=np.int16)

CUBE26 = np.array([
    (dx, dy, dz)
    for dx in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dz in (-1, 0, 1)
    if not (dx == 0 and dy == 0 and dz == 0)
], dtype=np.int16)

DEFAULT_VECTOR_BANDS = {
    "move": (0, 25),
    "reflect": (26, 51),
    "diffuse": (52, 63),
}


def load_config(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def initial_conditions(cfg: Dict[str, Any]) -> Dict[str, float]:
    size = int(cfg["grid"].get("size", 64))
    total_iotas = size**3
    active_iotas = min(int(cfg["init"].get("active_iotas", 1)), total_iotas)
    density = active_iotas / total_iotas if total_iotas else 0.0
    return {
        "initial_active_iotas": float(active_iotas),
        "total_iotas": float(total_iotas),
        "initial_density": float(density),
        "initial_density_percent": float(density * 100.0),
    }


def _base_vectors(mode: str, count: int, rng: np.random.Generator) -> np.ndarray:
    if mode == "cube6":
        return CUBE6
    if mode == "cube26":
        return CUBE26
    if mode == "random64":
        vals = []
        while len(vals) < count:
            v = rng.integers(-1, 2, size=3)
            if np.any(v != 0):
                vals.append(tuple(int(x) for x in v))
        return np.array(vals, dtype=np.int16)
    raise ValueError(f"Unknown vector mode: {mode}")


def make_vector_states(cfg: Dict[str, Any], rng: np.random.Generator) -> tuple[np.ndarray, tuple[str, ...]]:
    mode = cfg["vectors"].get("mode", "cube26")
    count = int(cfg["vectors"].get("vector_count", 64))
    base = _base_vectors(mode, count, rng)

    reps = math.ceil(count / len(base))
    directions = np.tile(base, (reps, 1))[:count].astype(np.int16)

    behaviors = ["move"] * count
    bands = cfg["vectors"].get("behavior_bands", DEFAULT_VECTOR_BANDS)
    for behavior, span in bands.items():
        start, end = int(span[0]), int(span[1])
        for idx in range(max(0, start), min(count - 1, end) + 1):
            behaviors[idx] = str(behavior)
    return directions, tuple(behaviors)


@dataclass
class World:
    active: np.ndarray
    A: np.ndarray
    R: np.ndarray
    V: np.ndarray
    P: np.ndarray
    vectors: np.ndarray
    vector_behaviors: tuple[str, ...]
    wrap: bool
    rng: np.random.Generator

    @property
    def size(self) -> int:
        return int(self.active.shape[0])


def init_world(cfg: Dict[str, Any]) -> World:
    size = int(cfg["grid"].get("size", 64))
    wrap = bool(cfg["grid"].get("wrap", True))
    seed = int(cfg["init"].get("seed", 42))
    rng = np.random.default_rng(seed)
    vectors, vector_behaviors = make_vector_states(cfg, rng)

    active = np.zeros((size, size, size), dtype=bool)
    A = np.zeros((size, size, size), dtype=np.uint8)
    R = np.zeros((size, size, size), dtype=np.uint8)
    V = np.zeros((size, size, size), dtype=np.uint8)
    P = np.zeros((size, size, size), dtype=np.uint8)

    n = int(cfg["init"].get("active_iotas", 1))
    mode = cfg["init"].get("mode", "random")
    ar = cfg["init"].get("amplitude_range", [1, 7])
    rr = cfg["init"].get("range_range", [1, 7])
    pr = cfg["init"].get("payload_range", [0, 7])

    if mode == "center":
        coords = [(size // 2, size // 2, size // 2)]
        while len(coords) < n:
            offset = rng.integers(-2, 3, size=3)
            c = tuple((np.array([size // 2] * 3) + offset) % size)
            coords.append(c)
    else:
        flat = rng.choice(size**3, size=min(n, size**3), replace=False)
        coords = [np.unravel_index(int(idx), (size, size, size)) for idx in flat]

    for x, y, z in coords:
        active[x, y, z] = True
        A[x, y, z] = rng.integers(ar[0], ar[1] + 1)
        R[x, y, z] = rng.integers(rr[0], rr[1] + 1)
        V[x, y, z] = rng.integers(0, len(vectors))
        P[x, y, z] = rng.integers(pr[0], pr[1] + 1)

    return World(active, A, R, V, P, vectors, vector_behaviors, wrap, rng)


def vector_step(world: World, v_idx: int, a: int, r: int, p: int) -> tuple[int, int, int, str]:
    behavior = world.vector_behaviors[v_idx]
    dx, dy, dz = world.vectors[v_idx]
    if behavior == "reflect":
        return -int(dx), -int(dy), -int(dz), behavior
    if behavior == "diffuse":
        diffuse_idx = (v_idx + a + r + p) % len(world.vectors)
        ddx, ddy, ddz = world.vectors[diffuse_idx]
        return int(ddx), int(ddy), int(ddz), behavior
    return int(dx), int(dy), int(dz), behavior


def rotate_vector_state(world: World, v_idx: int, payload: int) -> int:
    behavior = world.vector_behaviors[v_idx]
    indices = [idx for idx, candidate in enumerate(world.vector_behaviors) if candidate == behavior]
    if not indices:
        return (v_idx + payload) % len(world.vectors)
    offset = indices.index(v_idx)
    return indices[(offset + payload) % len(indices)]


def decay(distance: float, r: int, mode: str) -> float:
    if r <= 0:
        return 0.0
    if mode == "none":
        return 1.0
    if mode == "inverse":
        return 1.0 / max(distance, 1.0)
    if mode == "inverse_square":
        return 1.0 / max(distance * distance, 1.0)
    if mode == "exponential":
        return math.exp(-distance / max(r, 1))
    raise ValueError(f"Unknown decay mode: {mode}")


def local_candidates(
    world: World,
    x: int,
    y: int,
    z: int,
    v_idx: int,
    a: int,
    r: int,
    p: int,
    decay_mode: str,
    valence: int,
    bond_probability: float,
) -> list[dict[str, Any]]:
    if valence <= 0:
        return []

    candidate_steps = []
    seen_steps = set()
    primary = vector_step(world, v_idx, a, r, p)
    candidate_steps.append(primary)
    seen_steps.add(primary[:3])

    if valence > 1:
        behavior = primary[3]
        for dx, dy, dz in world.vectors:
            step_key = (int(dx), int(dy), int(dz))
            if step_key in seen_steps:
                continue
            seen_steps.add(step_key)
            distance = math.sqrt(step_key[0] ** 2 + step_key[1] ** 2 + step_key[2] ** 2)
            if distance <= max(r, 1):
                candidate_steps.append((step_key[0], step_key[1], step_key[2], behavior))

    candidates = []
    seen_targets = set()
    for order, (dx, dy, dz, behavior) in enumerate(candidate_steps):
        tx, ty, tz = int(x + dx), int(y + dy), int(z + dz)
        if world.wrap:
            tx %= world.size
            ty %= world.size
            tz %= world.size
        elif not (0 <= tx < world.size and 0 <= ty < world.size and 0 <= tz < world.size):
            continue
        target = (tx, ty, tz)
        if target in seen_targets:
            continue
        seen_targets.add(target)

        distance = math.sqrt(int(dx) ** 2 + int(dy) ** 2 + int(dz) ** 2)
        influence = (a / 7.0) * decay(distance, r, decay_mode)
        if behavior == "diffuse":
            influence *= 0.5
        if influence <= 0:
            continue
        candidates.append(
            {
                "target": target,
                "step": (int(dx), int(dy), int(dz)),
                "behavior": behavior,
                "influence": influence,
                "order": order,
            }
        )

    candidates.sort(key=lambda row: (-float(row["influence"]), int(row["order"])))

    selected = []
    primary_candidates = [candidate for candidate in candidates if int(candidate["order"]) == 0]
    if primary_candidates:
        selected.append(primary_candidates[0])

    additional_slots = max(0, valence - len(selected))
    additional_candidates = [candidate for candidate in candidates if int(candidate["order"]) != 0]
    for candidate in additional_candidates[:additional_slots]:
        if world.rng.random() < bond_probability:
            selected.append(candidate)

    return selected


def step(world: World, cfg: Dict[str, Any]) -> Dict[str, float]:
    size = world.size
    kA = float(cfg["constants"].get("amplitude_coupling", 0.125))
    kR = float(cfg["constants"].get("range_coupling", 0.125))
    thetaP = float(cfg["constants"].get("payload_takeover", 0.5))
    mu = float(cfg["constants"].get("mutation_rate", 0.0))
    decay_mode = cfg["constants"].get("decay_mode", "inverse_square")
    conservation = cfg["constants"].get("conservation", "soft")
    valence = max(1, int(cfg["constants"].get("valence", 1)))
    bond_probability = float(cfg["constants"].get("bond_probability", 1.0))
    bond_probability = min(1.0, max(0.0, bond_probability))

    next_active = world.active.copy()
    next_A = world.A.astype(np.float32).copy()
    next_R = world.R.astype(np.float32).copy()
    next_V = world.V.copy()
    next_P = world.P.copy()

    coords = np.argwhere(world.active)
    exchanges = 0
    secondary_exchanges = 0
    payload_changes = 0

    # Simple sparse update: iterate only active/non-dark iotas.
    for x, y, z in coords:
        a = int(world.A[x, y, z])
        r = int(world.R[x, y, z])
        if a == 0 or r == 0:
            continue
        v_idx = int(world.V[x, y, z]) % len(world.vectors)
        p = int(world.P[x, y, z])
        candidates = local_candidates(
            world,
            int(x),
            int(y),
            int(z),
            v_idx,
            a,
            r,
            p,
            decay_mode,
            valence,
            bond_probability,
        )

        for candidate in candidates:
            tx, ty, tz = candidate["target"]
            influence = float(candidate["influence"])
            exchanges += 1
            if int(candidate["order"]) != 0:
                secondary_exchanges += 1
            next_active[tx, ty, tz] = True

            # Amplitude/range exchange: octal fields remain clipped to 0..7.
            if conservation == "overwrite":
                next_A[tx, ty, tz] = a
                next_R[tx, ty, tz] = r
            else:
                next_A[tx, ty, tz] = (1 - kA * influence) * next_A[tx, ty, tz] + (kA * influence) * a
                next_R[tx, ty, tz] = (1 - kR * influence) * next_R[tx, ty, tz] + (kR * influence) * r

            # Payload exchange: discrete octal takeover when influence clears threshold.
            if influence >= thetaP:
                new_p = int(world.P[x, y, z])
                if mu > 0 and world.rng.random() < mu:
                    new_p = int((new_p + world.rng.choice([-1, 1])) % 8)
                if int(next_P[tx, ty, tz]) != new_p:
                    payload_changes += 1
                next_P[tx, ty, tz] = new_p
                # Let payload shape propagation by rotating vector slightly.
                next_V[tx, ty, tz] = np.uint8(rotate_vector_state(world, v_idx, new_p))
            else:
                # Below threshold, inherit vector only weakly/stochastically.
                if world.rng.random() < influence * 0.125:
                    next_V[tx, ty, tz] = np.uint8(v_idx)

    world.active = next_active
    world.A = np.clip(np.rint(next_A), 0, 7).astype(np.uint8)
    world.R = np.clip(np.rint(next_R), 0, 7).astype(np.uint8)
    world.V = next_V
    world.P = next_P

    active_count = int(world.active.sum())
    payload_hist = np.bincount(world.P[world.active], minlength=8) if active_count else np.zeros(8)
    max_payload_fraction = float(payload_hist.max() / active_count) if active_count else 0.0
    return {
        "exchanges": exchanges,
        "secondary_exchanges": secondary_exchanges,
        "payload_changes": payload_changes,
        "mean_A": float(world.A[world.active].mean()) if active_count else 0.0,
        "mean_R": float(world.R[world.active].mean()) if active_count else 0.0,
        "max_payload_fraction": max_payload_fraction,
    }


def save_slice(world: World, out: Path, tick: int, cfg: Dict[str, Any]) -> None:
    axis = cfg["visualization"].get("slice_axis", "z")
    idx = int(cfg["visualization"].get("slice_index", world.size // 2))
    idx = max(0, min(world.size - 1, idx))
    data = world.P.copy().astype(float)
    data[~world.active] = np.nan
    if axis == "x":
        img = data[idx, :, :]
    elif axis == "y":
        img = data[:, idx, :]
    else:
        img = data[:, :, idx]
    plt.figure(figsize=(7, 7))
    plt.imshow(img.T, origin="lower", interpolation="nearest")
    plt.title(f"Iota payload slice {axis}={idx}, tick={tick}")
    plt.xlabel("x/y")
    plt.ylabel("y/z")
    plt.colorbar(label="Payload 0..7")
    plt.tight_layout()
    plt.savefig(out / f"slice_{tick:06d}.png", dpi=140)
    plt.close()


def save_scatter(world: World, out: Path, tick: int, cfg: Dict[str, Any]) -> None:
    coords = np.argwhere(world.active)
    max_points = int(cfg["visualization"].get("max_points", 20000))
    if len(coords) == 0:
        return
    if len(coords) > max_points:
        coords = coords[world.rng.choice(len(coords), size=max_points, replace=False)]
    payloads = world.P[coords[:, 0], coords[:, 1], coords[:, 2]]
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2], c=payloads, s=2, alpha=0.7)
    ax.set_title(f"Active iotas, tick={tick}")
    ax.set_xlim(0, world.size); ax.set_ylim(0, world.size); ax.set_zlim(0, world.size)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    plt.tight_layout()
    plt.savefig(out / f"scatter_{tick:06d}.png", dpi=140)
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Octal iota test rig")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--objective", default=None)
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--force",
        action="store_true",
        help="deprecated; the one-parameter protocol is always enforced",
    )
    args = parser.parse_args()
    from experiment_runner import run_experiment

    run_experiment(args.config, args.objective, args.notes, args.force)
