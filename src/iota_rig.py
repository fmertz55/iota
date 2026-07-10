from __future__ import annotations

import argparse
import json
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
# latent_A: v0.2 inactive-cell conserved budget ledger

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

EDGE12 = np.array([
    (dx, dy, dz)
    for dx, dy, dz in CUBE26
    if abs(int(dx)) + abs(int(dy)) + abs(int(dz)) == 2
], dtype=np.int16)

CORNER8 = np.array([
    (dx, dy, dz)
    for dx, dy, dz in CUBE26
    if abs(int(dx)) + abs(int(dy)) + abs(int(dz)) == 3
], dtype=np.int16)

FACE18 = np.array([
    (dx, dy, dz)
    for dx, dy, dz in CUBE26
    if abs(int(dx)) + abs(int(dy)) + abs(int(dz)) <= 2
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


def candidate_neighbor_steps(mode: str) -> np.ndarray:
    if mode == "cube26":
        return CUBE26
    if mode == "face18" or mode == "face6_plus_edge12":
        return FACE18
    if mode == "face6" or mode == "cube6":
        return CUBE6
    if mode == "edge12":
        return EDGE12
    if mode == "corner8":
        return CORNER8
    raise ValueError(f"Unknown neighbor mode: {mode}")


def active_neighbor_coords(
    world: World,
    target: tuple[int, int, int],
    connectivity: str,
) -> list[tuple[int, int, int]]:
    size = world.size
    tx, ty, tz = target
    coords: list[tuple[int, int, int]] = []
    for raw_delta in candidate_neighbor_steps(connectivity):
        dx, dy, dz = (int(value) for value in raw_delta)
        nx, ny, nz = tx + dx, ty + dy, tz + dz
        if world.wrap:
            nx %= size
            ny %= size
            nz %= size
        elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
            continue
        if bool(world.active[nx, ny, nz]):
            coords.append((nx, ny, nz))
    return coords


def local_component_count(
    coords: list[tuple[int, int, int]],
    connectivity: str,
    size: int,
    wrap: bool,
) -> int:
    remaining = set(coords)
    if not remaining:
        return 0
    neighbors = tuple(
        (int(dx), int(dy), int(dz))
        for dx, dy, dz in candidate_neighbor_steps(connectivity)
    )
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            x, y, z = stack.pop()
            for dx, dy, dz in neighbors:
                nx, ny, nz = x + dx, y + dy, z + dz
                if wrap:
                    nx %= size
                    ny %= size
                    nz %= size
                elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
                    continue
                neighbor = (nx, ny, nz)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def classify_residual_target_geometry(
    world: World,
    target: tuple[int, int, int],
) -> dict[str, Any]:
    face6_coords = active_neighbor_coords(world, target, "face6")
    face18_coords = active_neighbor_coords(world, target, "face18")
    cube26_coords = active_neighbor_coords(world, target, "cube26")
    face6_count = len(face6_coords)
    face18_count = len(face18_coords)
    cube26_count = len(cube26_coords)
    face6_components = local_component_count(face6_coords, "face6", world.size, world.wrap)
    cube26_components = local_component_count(cube26_coords, "cube26", world.size, world.wrap)

    is_component_bridge_cube26 = cube26_components >= 2
    is_local_bridge_face6 = face6_components >= 2
    is_tip_seed = cube26_count <= 2
    is_flat_front = face6_count == 1 and cube26_count >= 9
    is_concave_fill = face6_count >= 4 or cube26_count >= 18

    if is_component_bridge_cube26:
        class_name = "component_bridge_cube26"
    elif is_local_bridge_face6:
        class_name = "local_bridge_face6"
    elif is_concave_fill:
        class_name = "concave_fill"
    elif is_tip_seed:
        class_name = "tip_seed"
    elif face6_count == 0:
        class_name = "diagonal_shear"
    elif is_flat_front:
        class_name = "flat_front"
    elif face6_count == 1:
        class_name = "edge_extension"
    elif face6_count in {2, 3}:
        class_name = "ridge_or_corner_fill"
    else:
        class_name = "interface_fill"

    return {
        "class": class_name,
        "face6_neighbors": face6_count,
        "face18_neighbors": face18_count,
        "cube26_neighbors": cube26_count,
        "face6_components": face6_components,
        "cube26_components": cube26_components,
        "is_component_bridge_cube26": is_component_bridge_cube26,
        "is_local_bridge_face6": is_local_bridge_face6,
        "is_tip_seed": is_tip_seed,
        "is_flat_front": is_flat_front,
        "is_concave_fill": is_concave_fill,
    }


def residual_target_support_features(
    world: World,
    target: tuple[int, int, int],
) -> dict[str, float]:
    geometry = classify_residual_target_geometry(world, target)
    face6_neighbors = float(geometry["face6_neighbors"])
    cube26_neighbors = float(geometry["cube26_neighbors"])
    cube26_components = float(geometry["cube26_components"])

    cube26_neighbor_support = max(0.0, min(1.0, (cube26_neighbors - 1.0) / 5.0))
    face6_neighbor_support = max(0.0, min(1.0, (face6_neighbors - 1.0) / 3.0))
    multi_component_support = 1.0 if cube26_components >= 2.0 else 0.0
    supported_bridge = (
        max(0.0, min(1.0, (cube26_neighbors - cube26_components) / 4.0))
        if cube26_components >= 2.0
        else 0.0
    )
    non_articulation_support = (
        max(0.0, min(1.0, (cube26_neighbors - 1.0) / 4.0))
        if cube26_components <= 1.0
        else 0.0
    )
    dangling_articulation_risk = 0.0
    if cube26_neighbors <= 2.0:
        dangling_articulation_risk = 1.0
    elif cube26_components >= 2.0 and cube26_neighbors <= 3.0:
        dangling_articulation_risk = 0.5

    return {
        "cube26_neighbor_support": cube26_neighbor_support,
        "face6_neighbor_support": face6_neighbor_support,
        "multi_component_support": multi_component_support,
        "supported_bridge": supported_bridge,
        "non_articulation_support": non_articulation_support,
        "dangling_articulation_risk": dangling_articulation_risk,
    }


def residual_target_support_score(
    world: World,
    target: tuple[int, int, int],
    weights: dict[str, float] | None = None,
) -> float:
    feature_weights = weights or {}
    features = residual_target_support_features(world, target)
    return float(
        feature_weights.get("cube26_neighbor_support", 0.0) * features["cube26_neighbor_support"]
        + feature_weights.get("face6_neighbor_support", 0.0) * features["face6_neighbor_support"]
        + feature_weights.get("multi_component_support", 0.0) * features["multi_component_support"]
        + feature_weights.get("supported_bridge", 0.0) * features["supported_bridge"]
        + feature_weights.get("non_articulation_support", 0.0) * features["non_articulation_support"]
        - feature_weights.get("dangling_articulation_risk", 0.0) * features["dangling_articulation_risk"]
    )


def residual_source_support_features(
    world: World,
    source: tuple[int, int, int],
    source_a: int,
) -> dict[str, float]:
    cube26_coords = active_neighbor_coords(world, source, "cube26")
    cube26_neighbors = float(len(cube26_coords))
    cube26_components_after_removal = float(
        local_component_count(cube26_coords, "cube26", world.size, world.wrap)
    )
    source_neighbor_support = max(0.0, min(1.0, (cube26_neighbors - 1.0) / 5.0))
    source_amplitude_support = max(0.0, min(1.0, (float(source_a) - 1.0) / 4.0))
    if int(source_a) <= 1:
        source_exhaustion_risk = 1.0
    elif int(source_a) == 2:
        source_exhaustion_risk = 0.5
    else:
        source_exhaustion_risk = 0.0
    source_articulation_risk = 1.0 if cube26_components_after_removal >= 2.0 else 0.0
    return {
        "source_neighbor_support": source_neighbor_support,
        "source_amplitude_support": source_amplitude_support,
        "source_exhaustion_risk": source_exhaustion_risk,
        "source_articulation_risk": source_articulation_risk,
    }


def residual_source_support_score(
    world: World,
    source: tuple[int, int, int],
    source_a: int,
    weights: dict[str, float] | None = None,
) -> float:
    feature_weights = weights or {}
    features = residual_source_support_features(world, source, source_a)
    return float(
        feature_weights.get("source_neighbor_support", 0.0) * features["source_neighbor_support"]
        + feature_weights.get("source_amplitude_support", 0.0) * features["source_amplitude_support"]
        - feature_weights.get("source_exhaustion_risk", 0.0) * features["source_exhaustion_risk"]
        - feature_weights.get("source_articulation_risk", 0.0) * features["source_articulation_risk"]
    )


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
    latent_A: np.ndarray
    initial_total_A: int
    ledger_enabled: bool
    previous_active: np.ndarray
    previous_V: np.ndarray
    vectors: np.ndarray
    vector_behaviors: tuple[str, ...]
    wrap: bool
    rng: np.random.Generator
    angular_L: np.ndarray | None = None

    def __post_init__(self) -> None:
        if self.angular_L is None:
            self.angular_L = np.zeros(self.active.shape, dtype=np.float32)
        else:
            self.angular_L = self.angular_L.astype(np.float32, copy=False)

    @property
    def size(self) -> int:
        return int(self.active.shape[0])


def save_world_state(world: World, path: Path, metadata: dict[str, Any] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        active=world.active,
        A=world.A,
        R=world.R,
        V=world.V,
        P=world.P,
        latent_A=world.latent_A,
        angular_L=world.angular_L,
        initial_total_A=np.array(int(world.initial_total_A), dtype=np.int64),
        ledger_enabled=np.array(bool(world.ledger_enabled)),
        previous_active=world.previous_active,
        previous_V=world.previous_V,
        vectors=world.vectors,
        vector_behaviors=np.array(world.vector_behaviors, dtype=str),
        wrap=np.array(world.wrap),
        rng_state_json=np.array(json.dumps(world.rng.bit_generator.state, sort_keys=True)),
        metadata_json=np.array(json.dumps(metadata or {}, sort_keys=True, default=str)),
    )


def load_world_state(path: Path) -> World:
    with np.load(path, allow_pickle=False) as data:
        rng = np.random.default_rng()
        rng_state_json = str(data["rng_state_json"].item())
        rng.bit_generator.state = json.loads(rng_state_json)
        active = data["active"].astype(bool)
        latent_A = (
            data["latent_A"].copy()
            if "latent_A" in data.files
            else np.zeros(active.shape, dtype=np.int64)
        )
        angular_L = (
            data["angular_L"].astype(np.float32)
            if "angular_L" in data.files
            else np.zeros(active.shape, dtype=np.float32)
        )
        ledger_enabled = bool(data["ledger_enabled"].item()) if "ledger_enabled" in data.files else False
        initial_total_A = (
            int(data["initial_total_A"].item())
            if "initial_total_A" in data.files
            else int(np.sum(data["A"][active], dtype=np.int64) + np.sum(latent_A[~active], dtype=np.int64))
        )
        return World(
            active=active,
            A=data["A"].copy(),
            R=data["R"].astype(np.uint8),
            V=data["V"].astype(np.uint8),
            P=data["P"].astype(np.uint8),
            latent_A=latent_A,
            angular_L=angular_L,
            initial_total_A=initial_total_A,
            ledger_enabled=ledger_enabled,
            previous_active=data["previous_active"].astype(bool),
            previous_V=data["previous_V"].astype(np.uint8),
            vectors=data["vectors"].astype(np.int16),
            vector_behaviors=tuple(str(value) for value in data["vector_behaviors"].tolist()),
            wrap=bool(data["wrap"].item()),
            rng=rng,
        )


def init_world(cfg: Dict[str, Any]) -> World:
    size = int(cfg["grid"].get("size", 64))
    wrap = bool(cfg["grid"].get("wrap", True))
    seed = int(cfg["init"].get("seed", 42))
    rng = np.random.default_rng(seed)
    vectors, vector_behaviors = make_vector_states(cfg, rng)
    ledger_enabled = str(cfg.get("constants", {}).get("conservation", "soft")) == "hard"
    amplitude_dtype = np.int64 if ledger_enabled else np.uint8

    active = np.zeros((size, size, size), dtype=bool)
    A = np.zeros((size, size, size), dtype=amplitude_dtype)
    R = np.zeros((size, size, size), dtype=np.uint8)
    V = np.zeros((size, size, size), dtype=np.uint8)
    P = np.zeros((size, size, size), dtype=np.uint8)
    latent_A = np.zeros((size, size, size), dtype=amplitude_dtype)

    n = int(cfg["init"].get("active_iotas", 1))
    mode = cfg["init"].get("mode", "random")
    ar = cfg["init"].get("amplitude_range", [1, 7])
    rr = cfg["init"].get("range_range", [1, 7])
    pr = cfg["init"].get("payload_range", [0, 7])

    if mode == "fixed":
        fixed_iotas = cfg["init"].get("fixed_iotas", [])
        if not fixed_iotas:
            raise ValueError("init.mode=fixed requires init.fixed_iotas")
        coords = []
        for iota in fixed_iotas:
            x, y, z = (int(value) for value in iota["coord"])
            if wrap:
                x %= size
                y %= size
                z %= size
            elif not (0 <= x < size and 0 <= y < size and 0 <= z < size):
                raise ValueError(f"Fixed iota coordinate out of bounds: {(x, y, z)}")
            coords.append((x, y, z))
    elif mode == "center":
        coords = [(size // 2, size // 2, size // 2)]
        while len(coords) < n:
            offset = rng.integers(-2, 3, size=3)
            c = tuple((np.array([size // 2] * 3) + offset) % size)
            coords.append(c)
    else:
        flat = rng.choice(size**3, size=min(n, size**3), replace=False)
        coords = [np.unravel_index(int(idx), (size, size, size)) for idx in flat]

    if mode == "fixed":
        for coord, iota in zip(coords, fixed_iotas):
            x, y, z = coord
            active[x, y, z] = True
            A[x, y, z] = max(0, min(7, int(iota["A"])))
            R[x, y, z] = np.uint8(max(0, min(7, int(iota["R"]))))
            V[x, y, z] = np.uint8(int(iota["V"]) % len(vectors))
            P[x, y, z] = np.uint8(max(0, min(7, int(iota["P"]))))
    else:
        for x, y, z in coords:
            active[x, y, z] = True
            A[x, y, z] = rng.integers(ar[0], ar[1] + 1)
            R[x, y, z] = rng.integers(rr[0], rr[1] + 1)
            V[x, y, z] = rng.integers(0, len(vectors))
            P[x, y, z] = rng.integers(pr[0], pr[1] + 1)

    if ledger_enabled:
        vacuum_amplitude = max(0, int(cfg.get("constants", {}).get("vacuum_amplitude", 1)))
        latent_A.fill(vacuum_amplitude)
        latent_A[active] = 0
    initial_total_A = int(np.sum(A[active], dtype=np.int64) + np.sum(latent_A[~active], dtype=np.int64))

    return World(
        active,
        A,
        R,
        V,
        P,
        latent_A,
        initial_total_A,
        ledger_enabled,
        active.copy(),
        V.copy(),
        vectors,
        vector_behaviors,
        wrap,
        rng,
    )


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
    return offset_vector_state(world, v_idx, payload, preserve_behavior=True)


def history_coupled_rotation_offset(
    source_v: int,
    source_p: int,
    target_v: int,
    target_a: int,
    target_r: int,
    target_p: int,
    candidate_order: int,
    target_depleted: bool,
    influence: float,
    max_offset: int,
) -> int:
    bounded_max = max(1, int(max_offset))
    source_phase = int(source_v) % 8
    payload_delta = (int(source_p) - int(target_p)) % 8
    target_phase = (int(target_v) + int(target_a) + int(target_r) + int(target_p)) % 8
    influence_phase = max(1, min(7, int(round(float(influence) * 7.0))))
    residual_phase = 1 if target_depleted else 0
    order_phase = int(candidate_order) % 8
    return 1 + (
        source_phase
        + payload_delta
        + target_phase
        + influence_phase
        + residual_phase
        + order_phase
    ) % bounded_max


def history_coupled_signed_rotation_offset(
    source_v: int,
    source_p: int,
    target_v: int,
    target_a: int,
    target_r: int,
    target_p: int,
    candidate_order: int,
    target_depleted: bool,
    influence: float,
    max_offset: int,
) -> int:
    magnitude = history_coupled_rotation_offset(
        source_v=source_v,
        source_p=source_p,
        target_v=target_v,
        target_a=target_a,
        target_r=target_r,
        target_p=target_p,
        candidate_order=candidate_order,
        target_depleted=target_depleted,
        influence=influence,
        max_offset=max_offset,
    )
    influence_phase = max(1, min(7, int(round(float(influence) * 7.0))))
    turn_parity = (
        int(source_v)
        - int(target_v)
        + int(source_p)
        - int(target_p)
        + int(target_a)
        - int(target_r)
        + int(candidate_order)
        + influence_phase
        + (1 if target_depleted else 0)
    ) % 2
    return int(magnitude if turn_parity == 0 else -magnitude)


def signed_round_offset(value: float) -> int:
    if value == 0.0:
        return 0
    return int(math.copysign(math.floor(abs(float(value)) + 0.5), float(value)))


def clamp_signed(value: float, cap: float) -> float:
    if cap <= 0:
        return 0.0
    return max(-float(cap), min(float(cap), float(value)))


def offset_vector_state(
    world: World,
    v_idx: int,
    offset: int,
    preserve_behavior: bool = True,
) -> int:
    if int(offset) == 0:
        return int(v_idx) % len(world.vectors)
    if not preserve_behavior:
        return int(v_idx + offset) % len(world.vectors)
    behavior = world.vector_behaviors[v_idx]
    indices = [idx for idx, candidate in enumerate(world.vector_behaviors) if candidate == behavior]
    if not indices:
        return int(v_idx + offset) % len(world.vectors)
    index_offset = indices.index(v_idx)
    return indices[(index_offset + int(offset)) % len(indices)]


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


def vector_alignment(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))
    if first_norm == 0.0 or second_norm == 0.0:
        return 0.0
    dot = sum(a * b for a, b in zip(first, second))
    return max(-1.0, min(1.0, dot / (first_norm * second_norm)))


def _shifted_mask(mask: np.ndarray, delta: tuple[int, int, int], wrap: bool) -> np.ndarray:
    if wrap:
        return np.roll(mask, shift=tuple(-value for value in delta), axis=(0, 1, 2))

    size = int(mask.shape[0])
    output = np.zeros_like(mask, dtype=bool)
    source_slices: list[slice] = []
    target_slices: list[slice] = []
    for offset in delta:
        if offset > 0:
            source_slices.append(slice(0, size - offset))
            target_slices.append(slice(offset, size))
        elif offset < 0:
            source_slices.append(slice(-offset, size))
            target_slices.append(slice(0, size + offset))
        else:
            source_slices.append(slice(None))
            target_slices.append(slice(None))
    output[tuple(source_slices)] = mask[tuple(target_slices)]
    return output


def _adjacent_to_mask(mask: np.ndarray, neighbor_mode: str, wrap: bool) -> np.ndarray:
    adjacent = np.zeros_like(mask, dtype=bool)
    for raw_delta in candidate_neighbor_steps(neighbor_mode):
        delta = tuple(int(value) for value in raw_delta)
        adjacent |= _shifted_mask(mask, delta, wrap)
    return adjacent


def secondary_bias_gate_mask(world: World, neighbor_mode: str) -> np.ndarray:
    depleted = (~world.active) & (world.latent_A == 0)
    active_interface = world.active & _adjacent_to_mask(depleted, neighbor_mode, world.wrap)
    depleted_interface = depleted & _adjacent_to_mask(world.active, neighbor_mode, world.wrap)
    recruitable_boundary = (
        (~world.active)
        & (world.latent_A > 0)
        & _adjacent_to_mask(world.active, neighbor_mode, world.wrap)
    )
    previous_active = (
        world.previous_active
        if world.previous_active.shape == world.active.shape
        else world.active
    )
    active_turnover = previous_active != world.active
    turnover_neighborhood = active_turnover | _adjacent_to_mask(
        active_turnover,
        neighbor_mode,
        world.wrap,
    )
    return (
        active_interface
        | depleted_interface
        | recruitable_boundary
        | turnover_neighborhood
    )


def angular_momentum_residual_score(
    world: World,
    old_L: np.ndarray,
    x: int,
    y: int,
    z: int,
    v_idx: int,
    a: int,
    r: int,
    p: int,
    candidate: dict[str, Any],
    angular_momentum_cap: float,
    preserve_behavior: bool,
    score_mode: str,
    geometry_weights: dict[str, float] | None = None,
) -> float:
    if angular_momentum_cap <= 0.0:
        return 0.0

    def alignment_score(
        l_value: float,
        local_v: int,
        local_a: int,
        local_r: int,
        local_p: int,
    ) -> float:
        if abs(l_value) <= 1e-6:
            return 0.0
        bias_offset = 1 if l_value > 0.0 else -1
        bias_v = offset_vector_state(
            world,
            local_v,
            bias_offset,
            preserve_behavior=preserve_behavior,
        )
        bias_dx, bias_dy, bias_dz, _ = vector_step(
            world,
            bias_v,
            local_a,
            local_r,
            local_p,
        )
        return min(1.0, abs(l_value) / angular_momentum_cap) * vector_alignment(
            (bias_dx, bias_dy, bias_dz),
            candidate["step"],
        )

    tx, ty, tz = candidate["target"]
    source_l = float(old_L[x, y, z])
    target_l = float(old_L[tx, ty, tz])
    if score_mode == "source_L_alignment":
        return alignment_score(source_l, v_idx, a, r, p)
    if score_mode == "target_L_alignment":
        target_v = int(world.V[tx, ty, tz]) % len(world.vectors)
        target_a = int(world.A[tx, ty, tz])
        target_r = int(world.R[tx, ty, tz])
        target_p = int(world.P[tx, ty, tz])
        return alignment_score(target_l, target_v, target_a, target_r, target_p)
    if score_mode == "source_target_L_contrast":
        contrast = clamp_signed(
            (source_l - target_l) / angular_momentum_cap,
            1.0,
        )
        primary_dx, primary_dy, primary_dz, _ = vector_step(world, v_idx, a, r, p)
        return float(contrast) * vector_alignment(
            (primary_dx, primary_dy, primary_dz),
            candidate["step"],
        )
    if score_mode == "source_target_L_contrast_component_bridge":
        contrast = clamp_signed(
            (source_l - target_l) / angular_momentum_cap,
            1.0,
        )
        primary_dx, primary_dy, primary_dz, _ = vector_step(world, v_idx, a, r, p)
        contrast_score = float(contrast) * vector_alignment(
            (primary_dx, primary_dy, primary_dz),
            candidate["step"],
        )
        weights = geometry_weights or {}
        geometry = classify_residual_target_geometry(world, tuple(int(value) for value in candidate["target"]))
        geometry_score = float(weights.get(str(geometry["class"]), 0.0))
        return clamp_signed(contrast_score + geometry_score, 1.0)
    if score_mode == "source_target_L_contrast_support_weighted":
        contrast = clamp_signed(
            (source_l - target_l) / angular_momentum_cap,
            1.0,
        )
        primary_dx, primary_dy, primary_dz, _ = vector_step(world, v_idx, a, r, p)
        contrast_score = float(contrast) * vector_alignment(
            (primary_dx, primary_dy, primary_dz),
            candidate["step"],
        )
        weights = geometry_weights or {}
        target = tuple(int(value) for value in candidate["target"])
        geometry = classify_residual_target_geometry(world, target)
        geometry_score = float(weights.get(str(geometry["class"]), 0.0))
        support_score = residual_target_support_score(world, target, weights)
        support_score += residual_source_support_score(world, (int(x), int(y), int(z)), int(a), weights)
        return clamp_signed(contrast_score + geometry_score + support_score, 1.0)
    raise ValueError(f"Unknown angular_momentum_residual_bias_score_mode: {score_mode}")


def apply_angular_momentum_residual_bias(
    world: World,
    old_L: np.ndarray,
    candidates: list[dict[str, Any]],
    x: int,
    y: int,
    z: int,
    v_idx: int,
    a: int,
    r: int,
    p: int,
    next_active: np.ndarray,
    next_latent_A: np.ndarray,
    kA: float,
    residual_participation_probability: float,
    residual_participation_secondary_only: bool,
    angular_momentum_cap: float,
    strength: float,
    preserve_behavior: bool,
    mean_preserving: bool,
    score_mode: str,
    geometry_weights: dict[str, float] | None = None,
) -> dict[str, float]:
    entries: list[tuple[dict[str, Any], float, float]] = []
    for candidate in candidates:
        tx, ty, tz = candidate["target"]
        target_depleted = (not bool(next_active[tx, ty, tz])) and int(next_latent_A[tx, ty, tz]) <= 0
        if not target_depleted:
            continue
        if residual_participation_probability <= 0.0:
            continue
        if residual_participation_secondary_only and int(candidate["order"]) == 0:
            continue
        influence = float(candidate["influence"])
        if influence <= 0.0:
            continue
        base_probability = clamp_probability(kA * influence) * residual_participation_probability
        if base_probability <= 0.0:
            continue
        score = angular_momentum_residual_score(
            world,
            old_L,
            x,
            y,
            z,
            v_idx,
            a,
            r,
            p,
            candidate,
            angular_momentum_cap,
            preserve_behavior,
            score_mode,
            geometry_weights,
        )
        raw_multiplier = max(0.0, 1.0 + float(strength) * score)
        entries.append((candidate, base_probability, raw_multiplier))

    base_sum = sum(base_probability for _, base_probability, _ in entries)
    raw_biased_sum = sum(
        base_probability * raw_multiplier
        for _, base_probability, raw_multiplier in entries
    )
    normalizer = raw_biased_sum / base_sum if mean_preserving and base_sum > 0.0 else 1.0
    force_unbiased = False
    if normalizer <= 1e-12:
        normalizer = 1.0
        force_unbiased = True

    biased_sum = 0.0
    for candidate, base_probability, raw_multiplier in entries:
        multiplier = 1.0 if force_unbiased else raw_multiplier / normalizer
        candidate["residual_bias_multiplier"] = multiplier
        biased_sum += base_probability * multiplier

    return {
        "eligible_candidates": float(len(entries)),
        "base_probability_sum": float(base_sum),
        "biased_probability_sum": float(biased_sum),
    }


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
    neighbor_mode: str = "cube26",
    secondary_bias_step: tuple[int, int, int] | None = None,
    secondary_bias_strength: float = 0.0,
    secondary_bias_gate: np.ndarray | None = None,
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
        for dx, dy, dz in candidate_neighbor_steps(neighbor_mode):
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
        secondary_bias_score = 0.0
        secondary_bias_allowed = (
            secondary_bias_gate is None
            or bool(secondary_bias_gate[tx, ty, tz])
        )
        if (
            secondary_bias_allowed
            and secondary_bias_step is not None
            and order != 0
            and secondary_bias_strength != 0.0
        ):
            secondary_bias_score = float(secondary_bias_strength) * vector_alignment(
                secondary_bias_step,
                (int(dx), int(dy), int(dz)),
            )
        candidates.append(
            {
                "target": target,
                "step": (int(dx), int(dy), int(dz)),
                "behavior": behavior,
                "influence": influence,
                "order": order,
                "secondary_bias_score": secondary_bias_score,
            }
        )

    candidates.sort(
        key=lambda row: (
            -float(row["influence"]) - float(row.get("secondary_bias_score", 0.0)),
            int(row["order"]),
        )
    )

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


def clamp_probability(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _step_hard_transfer(world: World, cfg: Dict[str, Any]) -> Dict[str, float]:
    kA = float(cfg["constants"].get("amplitude_coupling", 0.125))
    kR = float(cfg["constants"].get("range_coupling", 0.125))
    thetaP = float(cfg["constants"].get("payload_takeover", 0.5))
    mu = float(cfg["constants"].get("mutation_rate", 0.0))
    decay_mode = cfg["constants"].get("decay_mode", "inverse_square")
    deactivation = str(cfg["constants"].get("deactivation", "none"))
    valence = max(1, int(cfg["constants"].get("valence", 1)))
    bond_probability = clamp_probability(float(cfg["constants"].get("bond_probability", 1.0)))
    neighbor_mode = str(cfg["constants"].get("neighbor_mode", "cube26"))
    cross_payload_coupling = float(cfg["constants"].get("cross_payload_coupling", 1.0))
    same_payload_coupling = float(cfg["constants"].get("same_payload_coupling", 1.0))
    secondary_vector_kick_probability = clamp_probability(
        float(cfg["constants"].get("secondary_vector_kick_probability", 0.0))
    )
    secondary_vector_kick_offset = int(cfg["constants"].get("secondary_vector_kick_offset", 1))
    secondary_vector_kick_preserve_behavior = bool(
        cfg["constants"].get("secondary_vector_kick_preserve_behavior", True)
    )
    received_rotation_probability = clamp_probability(
        float(
            cfg["constants"].get(
                "received_rotation_probability",
                cfg["constants"].get("history_coupled_rotation_probability", 0.0),
            )
        )
    )
    received_rotation_max_offset = max(
        1,
        int(
            cfg["constants"].get(
                "received_rotation_max_offset",
                cfg["constants"].get("history_coupled_rotation_max_offset", 3),
            )
        ),
    )
    received_rotation_preserve_behavior = bool(
        cfg["constants"].get(
            "received_rotation_preserve_behavior",
            cfg["constants"].get("history_coupled_rotation_preserve_behavior", True),
        )
    )
    received_rotation_residual_multiplier = float(
        cfg["constants"].get(
            "received_rotation_residual_multiplier",
            cfg["constants"].get("history_coupled_rotation_residual_multiplier", 1.0),
        )
    )
    received_rotation_secondary_multiplier = float(
        cfg["constants"].get(
            "received_rotation_secondary_multiplier",
            cfg["constants"].get("history_coupled_rotation_secondary_multiplier", 1.0),
        )
    )
    angular_momentum_enabled = bool(cfg["constants"].get("angular_momentum_enabled", False))
    angular_momentum_decay = max(0.0, min(1.0, float(cfg["constants"].get("angular_momentum_decay", 1.0))))
    angular_momentum_coupling = float(cfg["constants"].get("angular_momentum_coupling", 0.0))
    angular_momentum_retention = float(cfg["constants"].get("angular_momentum_retention", 1.0))
    angular_momentum_cap = max(0.0, float(cfg["constants"].get("angular_momentum_cap", received_rotation_max_offset)))
    angular_momentum_enabled = angular_momentum_enabled and angular_momentum_cap > 0.0
    angular_momentum_secondary_bias_enabled = bool(
        cfg["constants"].get("angular_momentum_secondary_bias_enabled", False)
    )
    angular_momentum_secondary_bias_strength = max(
        0.0,
        float(cfg["constants"].get("angular_momentum_secondary_bias_strength", 0.0)),
    )
    angular_momentum_secondary_bias_preserve_behavior = bool(
        cfg["constants"].get("angular_momentum_secondary_bias_preserve_behavior", True)
    )
    angular_momentum_secondary_bias_gate = str(
        cfg["constants"].get("angular_momentum_secondary_bias_gate", "none")
    )
    if angular_momentum_secondary_bias_gate not in {"none", "interface_recruitment"}:
        raise ValueError(
            "Unknown angular_momentum_secondary_bias_gate: "
            f"{angular_momentum_secondary_bias_gate}"
        )
    angular_momentum_secondary_bias_enabled = (
        angular_momentum_enabled
        and angular_momentum_secondary_bias_enabled
        and angular_momentum_secondary_bias_strength > 0.0
    )
    angular_momentum_residual_bias_enabled = bool(
        cfg["constants"].get("angular_momentum_residual_bias_enabled", False)
    )
    angular_momentum_residual_bias_strength = max(
        0.0,
        float(cfg["constants"].get("angular_momentum_residual_bias_strength", 0.0)),
    )
    angular_momentum_residual_bias_gate = str(
        cfg["constants"].get("angular_momentum_residual_bias_gate", "depleted_interface")
    )
    if angular_momentum_residual_bias_gate not in {"depleted_interface"}:
        raise ValueError(
            "Unknown angular_momentum_residual_bias_gate: "
            f"{angular_momentum_residual_bias_gate}"
        )
    angular_momentum_residual_bias_mean_preserving = bool(
        cfg["constants"].get("angular_momentum_residual_bias_mean_preserving", True)
    )
    angular_momentum_residual_bias_preserve_behavior = bool(
        cfg["constants"].get("angular_momentum_residual_bias_preserve_behavior", True)
    )
    angular_momentum_residual_bias_score_mode = str(
        cfg["constants"].get(
            "angular_momentum_residual_bias_score_mode",
            "source_L_alignment",
        )
    )
    if angular_momentum_residual_bias_score_mode not in {
        "source_L_alignment",
        "target_L_alignment",
        "source_target_L_contrast",
        "source_target_L_contrast_component_bridge",
        "source_target_L_contrast_support_weighted",
    }:
        raise ValueError(
            "Unknown angular_momentum_residual_bias_score_mode: "
            f"{angular_momentum_residual_bias_score_mode}"
        )
    raw_residual_geometry_weights = cfg["constants"].get(
        "angular_momentum_residual_geometry_weights",
        {},
    )
    if raw_residual_geometry_weights is None:
        raw_residual_geometry_weights = {}
    if not isinstance(raw_residual_geometry_weights, dict):
        raise ValueError("angular_momentum_residual_geometry_weights must be a mapping")
    residual_geometry_classes = (
        "component_bridge_cube26",
        "local_bridge_face6",
        "flat_front",
        "edge_extension",
        "tip_seed",
        "diagonal_shear",
        "concave_fill",
        "ridge_or_corner_fill",
        "interface_fill",
    )
    angular_momentum_residual_geometry_weights = {
        class_name: float(
            cfg["constants"].get(
                f"angular_momentum_residual_geometry_{class_name}_weight",
                raw_residual_geometry_weights.get(class_name, 0.0),
            )
        )
        for class_name in residual_geometry_classes
    }
    residual_support_terms = (
        "cube26_neighbor_support",
        "face6_neighbor_support",
        "multi_component_support",
        "supported_bridge",
        "non_articulation_support",
        "dangling_articulation_risk",
        "source_neighbor_support",
        "source_amplitude_support",
        "source_exhaustion_risk",
        "source_articulation_risk",
    )
    for term in residual_support_terms:
        angular_momentum_residual_geometry_weights[term] = float(
            cfg["constants"].get(
                f"angular_momentum_residual_{term}_weight",
                raw_residual_geometry_weights.get(term, 0.0),
            )
        )
    angular_momentum_residual_bias_enabled = (
        angular_momentum_enabled
        and angular_momentum_residual_bias_enabled
        and angular_momentum_residual_bias_strength > 0.0
    )
    residual_participation_probability = clamp_probability(
        float(
            cfg["constants"].get(
                "residual_participation_probability",
                cfg["constants"].get("depleted_reactivation_probability", 0.0),
            )
        )
    )
    residual_participation_secondary_only = bool(
        cfg["constants"].get(
            "residual_participation_secondary_only",
            cfg["constants"].get("depleted_reactivation_secondary_only", True),
        )
    )

    if deactivation not in {"none", "exhaustion"}:
        raise ValueError(f"Unknown deactivation mode: {deactivation}")

    old_active = world.active.copy()
    old_V = world.V.copy()
    next_active = world.active.copy()
    next_A = world.A.astype(np.int64, copy=True)
    available_A = world.A.astype(np.int64, copy=True)
    next_latent_A = world.latent_A.astype(np.int64, copy=True)
    next_R = world.R.astype(np.float32).copy()
    next_V = world.V.copy()
    next_P = world.P.copy()
    old_L = (
        world.angular_L.astype(np.float32, copy=True)
        if world.angular_L is not None
        else np.zeros(world.active.shape, dtype=np.float32)
    )
    next_L = old_L * angular_momentum_decay if angular_momentum_enabled else old_L.copy()

    coords = np.argwhere(world.active)
    exchanges = 0
    secondary_exchanges = 0
    payload_changes = 0
    amplitude_transfers = 0
    failed_transfer_gates = 0
    secondary_vector_kicks = 0
    residual_participations = 0
    rotation_events = 0
    rotation_events_on_residual_entry = 0
    rotation_events_on_secondary_exchange = 0
    angular_momentum_updates = 0
    angular_momentum_biased_rotation_events = 0
    angular_momentum_bias_abs_sum = 0.0
    angular_momentum_observed_turn_abs_sum = 0.0
    angular_momentum_secondary_bias_sources = 0
    angular_momentum_secondary_bias_selected_candidates = 0
    angular_momentum_residual_bias_eligible_candidates = 0.0
    angular_momentum_residual_bias_base_probability_sum = 0.0
    angular_momentum_residual_bias_biased_probability_sum = 0.0
    exchange_alignments: list[float] = []
    secondary_exchange_alignments: list[float] = []
    gated_secondary_bias_mask = (
        secondary_bias_gate_mask(world, neighbor_mode)
        if (
            angular_momentum_secondary_bias_enabled
            and angular_momentum_secondary_bias_gate == "interface_recruitment"
        )
        else None
    )

    for x, y, z in coords:
        a = int(world.A[x, y, z])
        r = int(world.R[x, y, z])
        if a <= 0 or r == 0:
            continue
        v_idx = int(world.V[x, y, z]) % len(world.vectors)
        p = int(world.P[x, y, z])
        primary_dx, primary_dy, primary_dz, _ = vector_step(world, v_idx, a, r, p)
        primary_step = (primary_dx, primary_dy, primary_dz)
        secondary_bias_step = None
        secondary_bias_strength = 0.0
        if angular_momentum_secondary_bias_enabled:
            source_l = float(old_L[x, y, z])
            if abs(source_l) > 1e-6:
                bias_offset = 1 if source_l > 0.0 else -1
                bias_v = offset_vector_state(
                    world,
                    v_idx,
                    bias_offset,
                    preserve_behavior=angular_momentum_secondary_bias_preserve_behavior,
                )
                secondary_bias_dx, secondary_bias_dy, secondary_bias_dz, _ = vector_step(
                    world,
                    bias_v,
                    a,
                    r,
                    p,
                )
                secondary_bias_step = (
                    secondary_bias_dx,
                    secondary_bias_dy,
                    secondary_bias_dz,
                )
                secondary_bias_strength = angular_momentum_secondary_bias_strength * min(
                    1.0,
                    abs(source_l) / angular_momentum_cap,
                )
                angular_momentum_secondary_bias_sources += 1
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
            neighbor_mode,
            secondary_bias_step=secondary_bias_step,
            secondary_bias_strength=secondary_bias_strength,
            secondary_bias_gate=gated_secondary_bias_mask,
        )
        angular_momentum_secondary_bias_selected_candidates += sum(
            1
            for candidate in candidates
            if int(candidate["order"]) != 0 and abs(float(candidate.get("secondary_bias_score", 0.0))) > 0.0
        )
        if angular_momentum_residual_bias_enabled:
            residual_bias_metric = apply_angular_momentum_residual_bias(
                world,
                old_L,
                candidates,
                int(x),
                int(y),
                int(z),
                v_idx,
                a,
                r,
                p,
                next_active,
                next_latent_A,
                kA,
                residual_participation_probability,
                residual_participation_secondary_only,
                angular_momentum_cap,
                angular_momentum_residual_bias_strength,
                angular_momentum_residual_bias_preserve_behavior,
                angular_momentum_residual_bias_mean_preserving,
                angular_momentum_residual_bias_score_mode,
                angular_momentum_residual_geometry_weights,
            )
            angular_momentum_residual_bias_eligible_candidates += residual_bias_metric[
                "eligible_candidates"
            ]
            angular_momentum_residual_bias_base_probability_sum += residual_bias_metric[
                "base_probability_sum"
            ]
            angular_momentum_residual_bias_biased_probability_sum += residual_bias_metric[
                "biased_probability_sum"
            ]

        for candidate in candidates:
            if int(available_A[x, y, z]) <= 0:
                break
            tx, ty, tz = candidate["target"]
            target_previous_a = int(world.A[tx, ty, tz])
            target_previous_r = int(world.R[tx, ty, tz])
            target_previous_v = int(world.V[tx, ty, tz]) % len(world.vectors)
            target_previous_p = int(world.P[tx, ty, tz])
            target_active = bool(next_active[tx, ty, tz])
            target_depleted = (not target_active) and int(next_latent_A[tx, ty, tz]) <= 0
            if target_active:
                if int(next_A[tx, ty, tz]) >= int(available_A[x, y, z]):
                    continue
            elif target_depleted and (
                residual_participation_probability <= 0.0
                or (
                    residual_participation_secondary_only
                    and int(candidate["order"]) == 0
                )
            ):
                continue

            influence = float(candidate["influence"])
            if bool(world.active[tx, ty, tz]):
                influence *= (
                    same_payload_coupling
                    if int(world.P[tx, ty, tz]) == p
                    else cross_payload_coupling
                )
            if influence <= 0:
                continue

            transfer_probability = clamp_probability(kA * influence)
            if target_depleted:
                transfer_probability *= residual_participation_probability
                if angular_momentum_residual_bias_enabled:
                    transfer_probability *= float(candidate.get("residual_bias_multiplier", 1.0))
                    transfer_probability = clamp_probability(transfer_probability)
            if world.rng.random() >= transfer_probability:
                failed_transfer_gates += 1
                continue

            available_A[x, y, z] -= 1
            next_A[x, y, z] -= 1
            if target_active:
                next_A[tx, ty, tz] += 1
            elif target_depleted:
                next_A[tx, ty, tz] += 1
                next_latent_A[tx, ty, tz] = 0
                next_active[tx, ty, tz] = True
                residual_participations += 1
            else:
                next_A[tx, ty, tz] += int(next_latent_A[tx, ty, tz]) + 1
                next_latent_A[tx, ty, tz] = 0
                next_active[tx, ty, tz] = True
            next_latent_A[tx, ty, tz] = 0

            exchanges += 1
            amplitude_transfers += 1
            if int(candidate["order"]) != 0:
                secondary_exchanges += 1
            alignment = vector_alignment(primary_step, candidate["step"])
            exchange_alignments.append(alignment)
            if int(candidate["order"]) != 0:
                secondary_exchange_alignments.append(alignment)

            next_R[tx, ty, tz] = (1 - kR * influence) * next_R[tx, ty, tz] + (kR * influence) * r

            if influence >= thetaP:
                new_p = int(world.P[x, y, z])
                if mu > 0 and world.rng.random() < mu:
                    new_p = int((new_p + world.rng.choice([-1, 1])) % 8)
                if int(next_P[tx, ty, tz]) != new_p:
                    payload_changes += 1
                next_P[tx, ty, tz] = new_p
                next_V[tx, ty, tz] = np.uint8(rotate_vector_state(world, v_idx, new_p))
            elif world.rng.random() < influence * 0.125:
                next_V[tx, ty, tz] = np.uint8(v_idx)

            if received_rotation_probability > 0.0:
                rotation_probability = received_rotation_probability
                if target_depleted:
                    rotation_probability *= received_rotation_residual_multiplier
                if int(candidate["order"]) != 0:
                    rotation_probability *= received_rotation_secondary_multiplier
                rotation_probability = clamp_probability(rotation_probability)
                if rotation_probability > 0.0 and world.rng.random() < rotation_probability:
                    rotation_offset = history_coupled_rotation_offset(
                        source_v=v_idx,
                        source_p=p,
                        target_v=target_previous_v,
                        target_a=target_previous_a,
                        target_r=target_previous_r,
                        target_p=target_previous_p,
                        candidate_order=int(candidate["order"]),
                        target_depleted=target_depleted,
                        influence=influence,
                        max_offset=received_rotation_max_offset,
                    )
                    if angular_momentum_enabled:
                        exchange_rotation_offset = history_coupled_signed_rotation_offset(
                            source_v=v_idx,
                            source_p=p,
                            target_v=target_previous_v,
                            target_a=target_previous_a,
                            target_r=target_previous_r,
                            target_p=target_previous_p,
                            candidate_order=int(candidate["order"]),
                            target_depleted=target_depleted,
                            influence=influence,
                            max_offset=received_rotation_max_offset,
                        )
                        turn_bias = float(old_L[tx, ty, tz]) * angular_momentum_coupling
                        angular_momentum_bias_abs_sum += abs(turn_bias)
                        unbiased_turn = clamp_signed(float(exchange_rotation_offset), angular_momentum_cap)
                        unbiased_rotation_offset = signed_round_offset(unbiased_turn)
                        total_turn = clamp_signed(
                            float(exchange_rotation_offset) + turn_bias,
                            angular_momentum_cap,
                        )
                        rotation_offset = signed_round_offset(total_turn)
                        if rotation_offset != unbiased_rotation_offset:
                            angular_momentum_biased_rotation_events += 1
                    rotated_v = offset_vector_state(
                        world,
                        int(next_V[tx, ty, tz]) % len(world.vectors),
                        rotation_offset,
                        preserve_behavior=received_rotation_preserve_behavior,
                    )
                    if int(next_V[tx, ty, tz]) != rotated_v:
                        next_V[tx, ty, tz] = np.uint8(rotated_v)
                        rotation_events += 1
                        if angular_momentum_enabled:
                            next_L[tx, ty, tz] = clamp_signed(
                                float(next_L[tx, ty, tz]) + angular_momentum_retention * float(rotation_offset),
                                angular_momentum_cap,
                            )
                            angular_momentum_updates += 1
                            angular_momentum_observed_turn_abs_sum += abs(float(rotation_offset))
                        if target_depleted:
                            rotation_events_on_residual_entry += 1
                        if int(candidate["order"]) != 0:
                            rotation_events_on_secondary_exchange += 1

            if (
                int(candidate["order"]) != 0
                and secondary_vector_kick_probability > 0.0
                and world.rng.random() < secondary_vector_kick_probability
            ):
                kicked_v = offset_vector_state(
                    world,
                    int(next_V[tx, ty, tz]) % len(world.vectors),
                    secondary_vector_kick_offset,
                    preserve_behavior=secondary_vector_kick_preserve_behavior,
                )
                if int(next_V[tx, ty, tz]) != kicked_v:
                    next_V[tx, ty, tz] = np.uint8(kicked_v)
                    secondary_vector_kicks += 1

    deactivation_events = 0
    if deactivation == "exhaustion":
        exhausted = next_active & (next_A <= 0)
        deactivation_events = int(np.count_nonzero(exhausted))
        if deactivation_events:
            next_active[exhausted] = False
            next_A[exhausted] = 0
            next_V[exhausted] = 0
            next_P[exhausted] = 0
            next_latent_A[exhausted] = 0

    next_A[~next_active] = 0
    next_latent_A[next_active] = 0

    world.previous_active = old_active
    world.previous_V = old_V
    world.active = next_active
    world.A = next_A
    world.R = np.clip(np.rint(next_R), 0, 7).astype(np.uint8)
    world.V = next_V
    world.P = next_P
    world.latent_A = next_latent_A
    world.angular_L = np.clip(next_L, -angular_momentum_cap, angular_momentum_cap).astype(np.float32)
    world.ledger_enabled = True

    active_count = int(world.active.sum())
    payload_hist = np.bincount(world.P[world.active], minlength=8) if active_count else np.zeros(8)
    max_payload_fraction = float(payload_hist.max() / active_count) if active_count else 0.0
    exchange_turn_degrees = [
        math.degrees(math.acos(max(-1.0, min(1.0, alignment))))
        for alignment in exchange_alignments
    ]
    secondary_turn_degrees = [
        math.degrees(math.acos(max(-1.0, min(1.0, alignment))))
        for alignment in secondary_exchange_alignments
    ]
    return {
        "exchanges": exchanges,
        "secondary_exchanges": secondary_exchanges,
        "payload_changes": payload_changes,
        "amplitude_transfers": amplitude_transfers,
        "failed_transfer_gates": failed_transfer_gates,
        "deactivation_events": deactivation_events,
        "secondary_vector_kicks": secondary_vector_kicks,
        "residual_participations": residual_participations,
        "depleted_reactivations": residual_participations,
        "rotation_events": rotation_events,
        "rotation_events_on_residual_entry": rotation_events_on_residual_entry,
        "rotation_events_on_secondary_exchange": rotation_events_on_secondary_exchange,
        "angular_momentum_updates": angular_momentum_updates,
        "angular_momentum_biased_rotation_events": angular_momentum_biased_rotation_events,
        "angular_momentum_bias_abs_sum": angular_momentum_bias_abs_sum,
        "angular_momentum_observed_turn_abs_sum": angular_momentum_observed_turn_abs_sum,
        "angular_momentum_secondary_bias_sources": angular_momentum_secondary_bias_sources,
        "angular_momentum_secondary_bias_selected_candidates": angular_momentum_secondary_bias_selected_candidates,
        "angular_momentum_residual_bias_eligible_candidates": angular_momentum_residual_bias_eligible_candidates,
        "angular_momentum_residual_bias_base_probability_sum": angular_momentum_residual_bias_base_probability_sum,
        "angular_momentum_residual_bias_biased_probability_sum": angular_momentum_residual_bias_biased_probability_sum,
        "angular_momentum_residual_bias_probability_delta": (
            angular_momentum_residual_bias_biased_probability_sum
            - angular_momentum_residual_bias_base_probability_sum
        ),
        "mean_A": float(world.A[world.active].mean()) if active_count else 0.0,
        "mean_R": float(world.R[world.active].mean()) if active_count else 0.0,
        "max_payload_fraction": max_payload_fraction,
        "mean_exchange_alignment": (
            float(sum(exchange_alignments) / len(exchange_alignments))
            if exchange_alignments
            else 0.0
        ),
        "mean_exchange_turn_degrees": (
            float(sum(exchange_turn_degrees) / len(exchange_turn_degrees))
            if exchange_turn_degrees
            else 0.0
        ),
        "mean_secondary_exchange_alignment": (
            float(sum(secondary_exchange_alignments) / len(secondary_exchange_alignments))
            if secondary_exchange_alignments
            else 0.0
        ),
        "mean_secondary_exchange_turn_degrees": (
            float(sum(secondary_turn_degrees) / len(secondary_turn_degrees))
            if secondary_turn_degrees
            else 0.0
        ),
    }


def step(world: World, cfg: Dict[str, Any]) -> Dict[str, float]:
    size = world.size
    kA = float(cfg["constants"].get("amplitude_coupling", 0.125))
    kR = float(cfg["constants"].get("range_coupling", 0.125))
    thetaP = float(cfg["constants"].get("payload_takeover", 0.5))
    mu = float(cfg["constants"].get("mutation_rate", 0.0))
    decay_mode = cfg["constants"].get("decay_mode", "inverse_square")
    conservation = cfg["constants"].get("conservation", "soft")
    if conservation == "hard":
        return _step_hard_transfer(world, cfg)
    valence = max(1, int(cfg["constants"].get("valence", 1)))
    bond_probability = float(cfg["constants"].get("bond_probability", 1.0))
    bond_probability = min(1.0, max(0.0, bond_probability))
    neighbor_mode = str(cfg["constants"].get("neighbor_mode", "cube26"))
    cross_payload_coupling = float(cfg["constants"].get("cross_payload_coupling", 1.0))
    same_payload_coupling = float(cfg["constants"].get("same_payload_coupling", 1.0))

    old_active = world.active.copy()
    old_V = world.V.copy()
    next_active = world.active.copy()
    next_A = world.A.astype(np.float32).copy()
    next_R = world.R.astype(np.float32).copy()
    next_V = world.V.copy()
    next_P = world.P.copy()

    coords = np.argwhere(world.active)
    exchanges = 0
    secondary_exchanges = 0
    payload_changes = 0
    exchange_alignments: list[float] = []
    secondary_exchange_alignments: list[float] = []

    # Simple sparse update: iterate only active/non-dark iotas.
    for x, y, z in coords:
        a = int(world.A[x, y, z])
        r = int(world.R[x, y, z])
        if a == 0 or r == 0:
            continue
        v_idx = int(world.V[x, y, z]) % len(world.vectors)
        p = int(world.P[x, y, z])
        primary_dx, primary_dy, primary_dz, _ = vector_step(world, v_idx, a, r, p)
        primary_step = (primary_dx, primary_dy, primary_dz)
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
            neighbor_mode,
        )

        for candidate in candidates:
            tx, ty, tz = candidate["target"]
            influence = float(candidate["influence"])
            payload_multiplier = 1.0
            if bool(world.active[tx, ty, tz]):
                payload_multiplier = (
                    same_payload_coupling
                    if int(world.P[tx, ty, tz]) == p
                    else cross_payload_coupling
                )
            influence *= payload_multiplier
            if influence <= 0:
                continue
            exchanges += 1
            if int(candidate["order"]) != 0:
                secondary_exchanges += 1
            alignment = vector_alignment(primary_step, candidate["step"])
            exchange_alignments.append(alignment)
            if int(candidate["order"]) != 0:
                secondary_exchange_alignments.append(alignment)
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

    world.previous_active = old_active
    world.previous_V = old_V
    world.active = next_active
    world.A = np.clip(np.rint(next_A), 0, 7).astype(np.uint8)
    world.R = np.clip(np.rint(next_R), 0, 7).astype(np.uint8)
    world.V = next_V
    world.P = next_P

    active_count = int(world.active.sum())
    payload_hist = np.bincount(world.P[world.active], minlength=8) if active_count else np.zeros(8)
    max_payload_fraction = float(payload_hist.max() / active_count) if active_count else 0.0
    exchange_turn_degrees = [
        math.degrees(math.acos(max(-1.0, min(1.0, alignment))))
        for alignment in exchange_alignments
    ]
    secondary_turn_degrees = [
        math.degrees(math.acos(max(-1.0, min(1.0, alignment))))
        for alignment in secondary_exchange_alignments
    ]
    return {
        "exchanges": exchanges,
        "secondary_exchanges": secondary_exchanges,
        "payload_changes": payload_changes,
        "mean_A": float(world.A[world.active].mean()) if active_count else 0.0,
        "mean_R": float(world.R[world.active].mean()) if active_count else 0.0,
        "max_payload_fraction": max_payload_fraction,
        "mean_exchange_alignment": (
            float(sum(exchange_alignments) / len(exchange_alignments))
            if exchange_alignments
            else 0.0
        ),
        "mean_exchange_turn_degrees": (
            float(sum(exchange_turn_degrees) / len(exchange_turn_degrees))
            if exchange_turn_degrees
            else 0.0
        ),
        "mean_secondary_exchange_alignment": (
            float(sum(secondary_exchange_alignments) / len(secondary_exchange_alignments))
            if secondary_exchange_alignments
            else 0.0
        ),
        "mean_secondary_exchange_turn_degrees": (
            float(sum(secondary_turn_degrees) / len(secondary_turn_degrees))
            if secondary_turn_degrees
            else 0.0
        ),
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
