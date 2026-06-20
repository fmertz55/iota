from __future__ import annotations

import csv
import json
import math
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np

from iota_rig import (
    candidate_neighbor_steps,
    decay,
    init_world,
    load_config,
    rotate_vector_state,
    vector_step,
)
from payload_coupling_bracket_4096_sweep import probe_config


LOW_LABEL = "0_209375"
LOW_COUPLING = 0.209375
HIGH_LABEL = "0_2109375"
HIGH_COUPLING = 0.2109375
MAX_TICKS = 4096
OUTPUT_DIR = Path("output/findings")


def component_labels(world: Any) -> tuple[dict[tuple[int, int, int], int], dict[int, int]]:
    active_coords = {tuple(int(value) for value in coord) for coord in np.argwhere(world.active)}
    labels: dict[tuple[int, int, int], int] = {}
    sizes: dict[int, int] = {}
    neighbors = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    component_id = 0
    while active_coords:
        component_id += 1
        size = 0
        start = active_coords.pop()
        labels[start] = component_id
        queue: deque[tuple[int, int, int]] = deque([start])
        while queue:
            x, y, z = queue.popleft()
            size += 1
            for dx, dy, dz in neighbors:
                nx, ny, nz = x + dx, y + dy, z + dz
                if world.wrap:
                    nx %= world.size
                    ny %= world.size
                    nz %= world.size
                elif not (0 <= nx < world.size and 0 <= ny < world.size and 0 <= nz < world.size):
                    continue
                neighbor = (nx, ny, nz)
                if neighbor not in active_coords:
                    continue
                active_coords.remove(neighbor)
                labels[neighbor] = component_id
                queue.append(neighbor)
        sizes[component_id] = size
    return labels, sizes


def traced_local_candidates(
    world: Any,
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
    neighbor_mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if valence <= 0:
        return [], []

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
        candidates.append(
            {
                "target": target,
                "step": (int(dx), int(dy), int(dz)),
                "behavior": behavior,
                "base_influence": influence,
                "order": order,
            }
        )

    candidates.sort(key=lambda row: (-float(row["base_influence"]), int(row["order"])))

    selected = []
    decision_log: list[dict[str, Any]] = []
    primary_candidates = [candidate for candidate in candidates if int(candidate["order"]) == 0]
    if primary_candidates:
        candidate = primary_candidates[0]
        selected.append(candidate)
        decision_log.append(
            {
                "event_class": "candidate_selection",
                "subtype": "primary",
                "target": candidate["target"],
                "order": int(candidate["order"]),
                "base_influence": float(candidate["base_influence"]),
                "accepted": True,
                "random_draw": None,
                "threshold": None,
            }
        )

    additional_slots = max(0, valence - len(selected))
    additional_candidates = [candidate for candidate in candidates if int(candidate["order"]) != 0]
    for candidate in additional_candidates[:additional_slots]:
        draw = float(world.rng.random())
        accepted = draw < bond_probability
        decision_log.append(
            {
                "event_class": "candidate_selection",
                "subtype": "secondary",
                "target": candidate["target"],
                "order": int(candidate["order"]),
                "base_influence": float(candidate["base_influence"]),
                "accepted": accepted,
                "random_draw": draw,
                "threshold": bond_probability,
            }
        )
        if accepted:
            selected.append(candidate)

    return selected, decision_log


def trace_step(world: Any, cfg: dict[str, Any], tick: int) -> list[dict[str, Any]]:
    kA = float(cfg["constants"].get("amplitude_coupling", 0.125))
    kR = float(cfg["constants"].get("range_coupling", 0.125))
    thetaP = float(cfg["constants"].get("payload_takeover", 0.5))
    mu = float(cfg["constants"].get("mutation_rate", 0.0))
    decay_mode = cfg["constants"].get("decay_mode", "inverse_square")
    conservation = cfg["constants"].get("conservation", "soft")
    valence = max(1, int(cfg["constants"].get("valence", 1)))
    bond_probability = min(1.0, max(0.0, float(cfg["constants"].get("bond_probability", 1.0))))
    neighbor_mode = str(cfg["constants"].get("neighbor_mode", "cube26"))
    cross_payload_coupling = float(cfg["constants"].get("cross_payload_coupling", 1.0))
    same_payload_coupling = float(cfg["constants"].get("same_payload_coupling", 1.0))

    labels, sizes = component_labels(world)
    old_active = world.active.copy()
    old_V = world.V.copy()
    next_active = world.active.copy()
    next_A = world.A.astype(np.float32).copy()
    next_R = world.R.astype(np.float32).copy()
    next_V = world.V.copy()
    next_P = world.P.copy()

    events: list[dict[str, Any]] = []
    sequence = 0
    for x, y, z in np.argwhere(world.active):
        actor = (int(x), int(y), int(z))
        a = int(world.A[actor])
        r = int(world.R[actor])
        if a == 0 or r == 0:
            continue
        v_idx = int(world.V[actor]) % len(world.vectors)
        p = int(world.P[actor])
        selected, selection_log = traced_local_candidates(
            world,
            actor[0],
            actor[1],
            actor[2],
            v_idx,
            a,
            r,
            p,
            decay_mode,
            valence,
            bond_probability,
            neighbor_mode,
        )

        for candidate in selected:
            sequence += 1
            target = tuple(int(value) for value in candidate["target"])
            target_pre_active = bool(world.active[target])
            target_pre_payload = int(world.P[target])
            same_payload_target = target_pre_active and target_pre_payload == p
            cross_payload_target = target_pre_active and target_pre_payload != p
            payload_multiplier = 1.0
            payload_multiplier_class = "inactive_target"
            if target_pre_active:
                if same_payload_target:
                    payload_multiplier = same_payload_coupling
                    payload_multiplier_class = "same_payload"
                else:
                    payload_multiplier = cross_payload_coupling
                    payload_multiplier_class = "cross_payload"
            base_influence = float(candidate["base_influence"])
            influence = base_influence * payload_multiplier
            if influence <= 0:
                continue

            actor_component = labels.get(actor)
            target_component = labels.get(target)
            inter_component_bridge = (
                target_pre_active
                and actor_component is not None
                and target_component is not None
                and actor_component != target_component
            )
            if conservation == "overwrite":
                next_a_float = float(a)
                next_r_float = float(r)
            else:
                next_a_float = float((1 - kA * influence) * next_A[target] + (kA * influence) * a)
                next_r_float = float((1 - kR * influence) * next_R[target] + (kR * influence) * r)
            next_a_round = int(np.clip(np.rint(next_a_float), 0, 7))
            next_r_round = int(np.clip(np.rint(next_r_float), 0, 7))

            payload_takeover = influence >= thetaP
            vector_inherit_draw = None
            vector_inherit_threshold = None
            vector_inherit = False
            next_p = int(next_P[target])
            next_v = int(next_V[target])
            mutation_draw = None
            if payload_takeover:
                next_p = p
                if mu > 0:
                    mutation_draw = float(world.rng.random())
                    if mutation_draw < mu:
                        next_p = int((next_p + world.rng.choice([-1, 1])) % 8)
                next_v = int(rotate_vector_state(world, v_idx, next_p))
            else:
                vector_inherit_threshold = influence * 0.125
                vector_inherit_draw = float(world.rng.random())
                vector_inherit = vector_inherit_draw < vector_inherit_threshold
                if vector_inherit:
                    next_v = v_idx

            next_active[target] = True
            next_A[target] = next_a_float
            next_R[target] = next_r_float
            next_P[target] = np.uint8(next_p)
            next_V[target] = np.uint8(next_v)

            event = {
                "tick": tick,
                "sequence": sequence,
                "actor": actor,
                "target": target,
                "event_class": "productive_exchange",
                "subtype": "secondary" if int(candidate["order"]) != 0 else "primary",
                "actor_A": a,
                "actor_R": r,
                "actor_V": v_idx,
                "actor_P": p,
                "target_pre_active": target_pre_active,
                "target_pre_A": int(world.A[target]),
                "target_pre_R": int(world.R[target]),
                "target_pre_V": int(world.V[target]),
                "target_pre_P": target_pre_payload,
                "target_pre_component": target_component,
                "target_pre_component_size": sizes.get(target_component, 0),
                "actor_component": actor_component,
                "actor_component_size": sizes.get(actor_component, 0),
                "inter_component_bridge": inter_component_bridge,
                "creates_new_active": not target_pre_active,
                "order": int(candidate["order"]),
                "step": candidate["step"],
                "base_influence": base_influence,
                "payload_multiplier_class": payload_multiplier_class,
                "payload_multiplier": payload_multiplier,
                "influence": influence,
                "payload_takeover_threshold": thetaP,
                "payload_takeover": payload_takeover,
                "vector_inherit_draw": vector_inherit_draw,
                "vector_inherit_threshold": vector_inherit_threshold,
                "vector_inherit": vector_inherit,
                "mutation_draw": mutation_draw,
                "next_A_float": next_a_float,
                "next_R_float": next_r_float,
                "next_A_round": next_a_round,
                "next_R_round": next_r_round,
                "next_P": next_p,
                "next_V": next_v,
                "candidate_decisions": selection_log,
            }
            events.append(event)

    world.previous_active = old_active
    world.previous_V = old_V
    world.active = next_active
    world.A = np.clip(np.rint(next_A), 0, 7).astype(np.uint8)
    world.R = np.clip(np.rint(next_R), 0, 7).astype(np.uint8)
    world.V = next_V
    world.P = next_P
    return events


def semantic_signature(event: dict[str, Any]) -> tuple[Any, ...]:
    return (
        event["actor"],
        event["target"],
        event["subtype"],
        event["target_pre_active"],
        event["payload_multiplier_class"],
        event["payload_takeover"],
        event["vector_inherit"],
        event["inter_component_bridge"],
        event["creates_new_active"],
        event["next_A_round"],
        event["next_R_round"],
        event["next_P"],
        event["next_V"],
    )


def compact_event(event: dict[str, Any] | None) -> dict[str, Any] | None:
    if event is None:
        return None
    keys = [
        "tick",
        "sequence",
        "actor",
        "target",
        "subtype",
        "actor_A",
        "actor_R",
        "actor_V",
        "actor_P",
        "target_pre_active",
        "target_pre_A",
        "target_pre_R",
        "target_pre_V",
        "target_pre_P",
        "actor_component",
        "actor_component_size",
        "target_pre_component",
        "target_pre_component_size",
        "inter_component_bridge",
        "creates_new_active",
        "base_influence",
        "payload_multiplier_class",
        "payload_multiplier",
        "influence",
        "payload_takeover",
        "vector_inherit_draw",
        "vector_inherit_threshold",
        "vector_inherit",
        "next_A_float",
        "next_R_float",
        "next_A_round",
        "next_R_round",
        "next_P",
        "next_V",
    ]
    return {key: event[key] for key in keys}


def write_event_pair(path: Path, low_event: dict[str, Any] | None, high_event: dict[str, Any] | None) -> None:
    fields = sorted(set(compact_event(low_event) or {}) | set(compact_event(high_event) or {}))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["side", *fields])
        writer.writeheader()
        for side, event in (("low", compact_event(low_event)), ("high", compact_event(high_event))):
            if event is None:
                writer.writerow({"side": side})
            else:
                row = {"side": side}
                row.update(event)
                writer.writerow(row)


def main() -> None:
    base_cfg = load_config("config.yaml")
    low_cfg = probe_config(base_cfg, LOW_LABEL, LOW_COUPLING)
    high_cfg = probe_config(base_cfg, HIGH_LABEL, HIGH_COUPLING)
    low_world = init_world(low_cfg)
    high_world = init_world(high_cfg)
    first_numeric_cross_event: dict[str, Any] | None = None
    first_divergence: dict[str, Any] | None = None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for tick in range(1, MAX_TICKS + 1):
        low_events = trace_step(low_world, low_cfg, tick)
        high_events = trace_step(high_world, high_cfg, tick)
        for index in range(max(len(low_events), len(high_events))):
            low_event = low_events[index] if index < len(low_events) else None
            high_event = high_events[index] if index < len(high_events) else None
            if (
                first_numeric_cross_event is None
                and low_event is not None
                and high_event is not None
                and low_event["payload_multiplier_class"] == "cross_payload"
                and high_event["payload_multiplier_class"] == "cross_payload"
                and abs(float(low_event["influence"]) - float(high_event["influence"])) > 0.0
            ):
                first_numeric_cross_event = {
                    "tick": tick,
                    "event_index": index,
                    "low": compact_event(low_event),
                    "high": compact_event(high_event),
                }
            if low_event is None or high_event is None or semantic_signature(low_event) != semantic_signature(high_event):
                first_divergence = {
                    "tick": tick,
                    "event_index": index,
                    "low": compact_event(low_event),
                    "high": compact_event(high_event),
                    "low_signature": semantic_signature(low_event) if low_event is not None else None,
                    "high_signature": semantic_signature(high_event) if high_event is not None else None,
                }
                write_event_pair(
                    OUTPUT_DIR / "finding_018_payload_coupling_first_semantic_divergence.csv",
                    low_event,
                    high_event,
                )
                break
        if first_divergence is not None:
            break
        if tick % 256 == 0:
            print(
                f"tick={tick} active_low={int(low_world.active.sum())} "
                f"active_high={int(high_world.active.sum())}"
            )

    result = {
        "low_coupling": LOW_COUPLING,
        "high_coupling": HIGH_COUPLING,
        "first_numeric_cross_event": first_numeric_cross_event,
        "first_semantic_divergence": first_divergence,
        "final_tick_checked": tick,
        "low_active_at_stop": int(low_world.active.sum()),
        "high_active_at_stop": int(high_world.active.sum()),
    }
    (OUTPUT_DIR / "finding_018_payload_coupling_divergence_trace.json").write_text(
        json.dumps(result, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
