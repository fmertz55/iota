from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import csv_bool, write_csv
from iota_rig import World, load_config


SEED_SET = (42, 43, 44, 45, 46, 56)

SUMMARY_FIELDNAMES = [
    "seed",
    "ticks_run",
    "first_nonzero_phase_tick",
    "last_nonzero_phase_tick",
    "phase_collapse_tick",
    "max_nonzero_phase_iotas",
    "initial_nonzero_phase_iotas",
    "initial_phase_unique",
    "final_nonzero_phase_iotas",
    "vector_step_events",
    "vector_step_result_collision_signatures",
    "vector_step_phase_collision_signatures",
    "rotate_takeover_events",
    "rotate_takeover_result_collision_signatures",
    "rotate_takeover_phase_collision_signatures",
    "rotation_offset_events",
    "rotation_offset_result_collision_signatures",
    "rotation_offset_phase_collision_signatures",
    "signed_rotation_offset_events",
    "signed_rotation_offset_result_collision_signatures",
    "signed_rotation_offset_phase_collision_signatures",
    "local_cell_signature_records",
    "local_cell_phase_collision_signatures",
    "mode_only_local_derivable",
    "numeric_phase_storage_eliminable",
]

PATH_FIELDNAMES = [
    "seed",
    "path",
    "events",
    "unique_signatures",
    "phase_collision_signatures",
    "phase_collision_events",
    "result_collision_signatures",
    "result_collision_events",
]

COLLISION_FIELDNAMES = [
    "seed",
    "path",
    "collision_type",
    "signature",
    "events",
    "first_tick",
    "last_tick",
    "phase_keys",
    "result_keys",
]

TIMELINE_FIELDNAMES = [
    "seed",
    "tick",
    "active_iotas",
    "nonzero_phase_iotas",
    "phase_unique",
    "phase_created_iotas",
    "phase_changed_iotas",
    "phase_cleared_iotas",
    "vector_step_events",
    "rotate_takeover_events",
    "rotation_offset_events",
    "signed_rotation_offset_events",
]

LOCAL_FIELDNAMES = [
    "seed",
    "tick",
    "signature",
    "phase_keys",
    "records",
]

EVENT_PATHS = (
    "vector_step",
    "rotate_takeover",
    "rotation_offset",
    "signed_rotation_offset",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit whether transient action phase can be derived from local non-payload state."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(SEED_SET))
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--max-ticks", type=int, default=160)
    parser.add_argument("--post-collapse-confirm", type=int, default=8)
    parser.add_argument("--collision-example-limit", type=int, default=80)
    return parser.parse_args()


def discover_config(config_dir: str, seed: int) -> Path:
    matches = sorted(Path(config_dir).glob(f"v036_component_bridge_seed{int(seed)}_*.yaml"))
    if len(matches) != 1:
        raise SystemExit(f"expected one v0.3.6 config for seed {seed}, found {len(matches)}")
    return matches[0]


def key_payload(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def result_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def rounded_influence(value: float) -> float:
    return round(float(value), 12)


def phase_unique(world: World) -> int:
    if not np.any(world.active):
        return 0
    return int(len(np.unique(world.P[world.active])))


def active_nonzero_phase(world: World) -> int:
    return int(np.count_nonzero(world.active & (world.P != 0)))


def neighbor_mask_and_count(world: World, coord: tuple[int, int, int]) -> tuple[int, int, int]:
    x, y, z = coord
    size = world.active.shape[0]
    cube_mask = 0
    cube_count = 0
    face_count = 0
    bit = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                nx, ny, nz = x + dx, y + dy, z + dz
                if world.wrap:
                    nx %= size
                    ny %= size
                    nz %= size
                elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
                    bit += 1
                    continue
                if bool(world.active[nx, ny, nz]):
                    cube_mask |= 1 << bit
                    cube_count += 1
                    if abs(dx) + abs(dy) + abs(dz) == 1:
                        face_count += 1
                bit += 1
    return cube_mask, cube_count, face_count


def local_cell_signature(world: World, coord: tuple[int, int, int]) -> str:
    x, y, z = coord
    v_idx = int(world.V[x, y, z]) % len(world.vectors)
    cube_mask, cube_count, face_count = neighbor_mask_and_count(world, coord)
    angular_l = 0.0 if world.angular_L is None else round(float(world.angular_L[x, y, z]), 6)
    signature = {
        "active": bool(world.active[x, y, z]),
        "A": int(world.A[x, y, z]),
        "R": int(world.R[x, y, z]),
        "V": v_idx,
        "behavior": world.vector_behaviors[v_idx],
        "latent_A": int(world.latent_A[x, y, z]),
        "angular_L": angular_l,
        "cube26_mask": cube_mask,
        "cube26_count": cube_count,
        "face6_count": face_count,
    }
    return key_payload(signature)


class PhaseRecorder:
    def __init__(self, seed: int) -> None:
        self.seed = int(seed)
        self.tick = 0
        self.call_index = 0
        self.events: list[dict[str, Any]] = []
        self.tick_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def set_tick(self, tick: int) -> None:
        self.tick = int(tick)
        self.call_index = 0

    def record(self, path: str, signature: dict[str, Any], phase: Any, result: Any) -> None:
        self.call_index += 1
        row = {
            "seed": self.seed,
            "tick": self.tick,
            "call_index": self.call_index,
            "path": path,
            "signature": key_payload(signature),
            "phase_key": key_payload(phase),
            "result_key": result_key(result),
        }
        self.events.append(row)
        self.tick_counts[self.tick][path] += 1


@contextmanager
def instrument_phase_paths(recorder: PhaseRecorder) -> Iterator[None]:
    original_vector_step = iota_rig.vector_step
    original_rotate_vector_state = iota_rig.rotate_vector_state
    original_rotation_offset = iota_rig.history_coupled_rotation_offset
    original_signed_rotation_offset = iota_rig.history_coupled_signed_rotation_offset

    def vector_step_wrapper(world: World, v_idx: int, a: int, r: int, p: int) -> tuple[int, int, int, str]:
        result = original_vector_step(world, v_idx, a, r, p)
        if int(p) != 0:
            zero_result = original_vector_step(world, v_idx, a, r, 0)
            if result[:3] != zero_result[:3]:
                behavior = world.vector_behaviors[int(v_idx) % len(world.vectors)]
                recorder.record(
                    "vector_step",
                    {
                        "v_idx": int(v_idx) % len(world.vectors),
                        "A": int(a),
                        "R": int(r),
                        "behavior": behavior,
                    },
                    {"p": int(p)},
                    {"step": [int(result[0]), int(result[1]), int(result[2])]},
                )
        return result

    def rotate_vector_state_wrapper(world: World, v_idx: int, payload: int) -> int:
        result = original_rotate_vector_state(world, v_idx, payload)
        if int(payload) != 0:
            behavior = world.vector_behaviors[int(v_idx) % len(world.vectors)]
            recorder.record(
                "rotate_takeover",
                {"v_idx": int(v_idx) % len(world.vectors), "behavior": behavior},
                {"p": int(payload)},
                {"rotated_v": int(result)},
            )
        return result

    def rotation_offset_wrapper(
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
        result = original_rotation_offset(
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
        if int(source_p) != 0 or int(target_p) != 0:
            recorder.record(
                "rotation_offset",
                {
                    "source_v": int(source_v),
                    "target_v": int(target_v),
                    "target_a": int(target_a),
                    "target_r": int(target_r),
                    "candidate_order": int(candidate_order),
                    "target_depleted": bool(target_depleted),
                    "influence": rounded_influence(float(influence)),
                    "max_offset": int(max_offset),
                },
                {"source_p": int(source_p), "target_p": int(target_p)},
                {"offset": int(result)},
            )
        return result

    def signed_rotation_offset_wrapper(
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
        saved_rotation_offset = iota_rig.history_coupled_rotation_offset
        iota_rig.history_coupled_rotation_offset = original_rotation_offset
        try:
            result = original_signed_rotation_offset(
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
        finally:
            iota_rig.history_coupled_rotation_offset = saved_rotation_offset
        if int(source_p) != 0 or int(target_p) != 0:
            recorder.record(
                "signed_rotation_offset",
                {
                    "source_v": int(source_v),
                    "target_v": int(target_v),
                    "target_a": int(target_a),
                    "target_r": int(target_r),
                    "candidate_order": int(candidate_order),
                    "target_depleted": bool(target_depleted),
                    "influence": rounded_influence(float(influence)),
                    "max_offset": int(max_offset),
                },
                {"source_p": int(source_p), "target_p": int(target_p)},
                {"signed_offset": int(result)},
            )
        return result

    iota_rig.vector_step = vector_step_wrapper
    iota_rig.rotate_vector_state = rotate_vector_state_wrapper
    iota_rig.history_coupled_rotation_offset = rotation_offset_wrapper
    iota_rig.history_coupled_signed_rotation_offset = signed_rotation_offset_wrapper
    try:
        yield
    finally:
        iota_rig.vector_step = original_vector_step
        iota_rig.rotate_vector_state = original_rotate_vector_state
        iota_rig.history_coupled_rotation_offset = original_rotation_offset
        iota_rig.history_coupled_signed_rotation_offset = original_signed_rotation_offset


def summarize_path(seed: int, path: str, events: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path_events = [event for event in events if event["path"] == path]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in path_events:
        grouped[event["signature"]].append(event)

    phase_collision_signatures = 0
    phase_collision_events = 0
    result_collision_signatures = 0
    result_collision_events = 0
    collisions: list[dict[str, Any]] = []
    for signature, signature_events in grouped.items():
        phase_keys = sorted({event["phase_key"] for event in signature_events})
        result_keys = sorted({event["result_key"] for event in signature_events})
        first_tick = min(int(event["tick"]) for event in signature_events)
        last_tick = max(int(event["tick"]) for event in signature_events)
        if len(phase_keys) > 1:
            phase_collision_signatures += 1
            phase_collision_events += len(signature_events)
            collisions.append(
                {
                    "seed": seed,
                    "path": path,
                    "collision_type": "phase",
                    "signature": signature,
                    "events": len(signature_events),
                    "first_tick": first_tick,
                    "last_tick": last_tick,
                    "phase_keys": ";".join(phase_keys),
                    "result_keys": ";".join(result_keys),
                }
            )
        if len(result_keys) > 1:
            result_collision_signatures += 1
            result_collision_events += len(signature_events)
            collisions.append(
                {
                    "seed": seed,
                    "path": path,
                    "collision_type": "result",
                    "signature": signature,
                    "events": len(signature_events),
                    "first_tick": first_tick,
                    "last_tick": last_tick,
                    "phase_keys": ";".join(phase_keys),
                    "result_keys": ";".join(result_keys),
                }
            )

    row = {
        "seed": seed,
        "path": path,
        "events": len(path_events),
        "unique_signatures": len(grouped),
        "phase_collision_signatures": phase_collision_signatures,
        "phase_collision_events": phase_collision_events,
        "result_collision_signatures": result_collision_signatures,
        "result_collision_events": result_collision_events,
    }
    return row, collisions


def summarize_local_signatures(
    seed: int, local_records: list[dict[str, Any]]
) -> tuple[int, list[dict[str, Any]]]:
    grouped: dict[tuple[int, str], list[int]] = defaultdict(list)
    for record in local_records:
        grouped[(int(record["tick"]), str(record["signature"]))].append(int(record["phase"]))
    collision_rows: list[dict[str, Any]] = []
    for (tick, signature), phases in grouped.items():
        phase_keys = sorted({str(phase) for phase in phases})
        if len(phase_keys) > 1:
            collision_rows.append(
                {
                    "seed": seed,
                    "tick": tick,
                    "signature": signature,
                    "phase_keys": ";".join(phase_keys),
                    "records": len(phases),
                }
            )
    return len(collision_rows), collision_rows


def run_seed(
    args: argparse.Namespace,
    seed: int,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    cfg = load_config(discover_config(args.config_dir, seed))
    world = iota_rig.init_world(cfg)
    recorder = PhaseRecorder(seed)
    timeline_rows: list[dict[str, Any]] = []
    local_records: list[dict[str, Any]] = []

    first_nonzero_tick: int | None = None
    last_nonzero_tick: int | None = None
    phase_collapse_tick: int | None = None
    max_nonzero = 0
    collapse_confirm = 0
    previous_observed_p: np.ndarray | None = None
    initial_nonzero = active_nonzero_phase(world)
    initial_unique = phase_unique(world)

    with instrument_phase_paths(recorder):
        for tick in range(int(args.max_ticks) + 1):
            recorder.set_tick(tick)
            nonzero = active_nonzero_phase(world)
            active_count = int(np.count_nonzero(world.active))
            phase_unique_count = phase_unique(world)
            max_nonzero = max(max_nonzero, nonzero)
            if nonzero:
                if first_nonzero_tick is None:
                    first_nonzero_tick = tick
                last_nonzero_tick = tick
                collapse_confirm = 0
            elif first_nonzero_tick is not None:
                if phase_collapse_tick is None:
                    phase_collapse_tick = tick
                collapse_confirm += 1

            for coord_array in np.argwhere(world.active & (world.P != 0)):
                coord = tuple(int(value) for value in coord_array)
                local_records.append(
                    {
                        "tick": tick,
                        "signature": local_cell_signature(world, coord),
                        "phase": int(world.P[coord]),
                    }
                )

            if previous_observed_p is not None:
                created = int(np.count_nonzero(world.active & (previous_observed_p == 0) & (world.P != 0)))
                changed = int(
                    np.count_nonzero(
                        world.active
                        & (previous_observed_p != 0)
                        & (world.P != 0)
                        & (previous_observed_p != world.P)
                    )
                )
                cleared = int(np.count_nonzero((previous_observed_p != 0) & ((~world.active) | (world.P == 0))))
            else:
                created = nonzero
                changed = 0
                cleared = 0
            should_stop = (
                first_nonzero_tick is not None and collapse_confirm >= int(args.post_collapse_confirm)
            ) or tick >= int(args.max_ticks)
            observed_p = world.P.copy()
            if not should_stop:
                iota_rig.step(world, cfg)
            tick_counts = recorder.tick_counts[tick]
            timeline_rows.append(
                {
                    "seed": seed,
                    "tick": tick,
                    "active_iotas": active_count,
                    "nonzero_phase_iotas": nonzero,
                    "phase_unique": phase_unique_count,
                    "phase_created_iotas": created,
                    "phase_changed_iotas": changed,
                    "phase_cleared_iotas": cleared,
                    "vector_step_events": int(tick_counts.get("vector_step", 0)),
                    "rotate_takeover_events": int(tick_counts.get("rotate_takeover", 0)),
                    "rotation_offset_events": int(tick_counts.get("rotation_offset", 0)),
                    "signed_rotation_offset_events": int(tick_counts.get("signed_rotation_offset", 0)),
                }
            )
            previous_observed_p = observed_p
            if should_stop:
                break

    path_rows: list[dict[str, Any]] = []
    collision_rows: list[dict[str, Any]] = []
    path_summaries: dict[str, dict[str, Any]] = {}
    for path in EVENT_PATHS:
        path_row, path_collisions = summarize_path(seed, path, recorder.events)
        path_rows.append(path_row)
        collision_rows.extend(path_collisions)
        path_summaries[path] = path_row

    local_collision_count, local_collision_rows = summarize_local_signatures(seed, local_records)
    result_collision_total = sum(int(path_summaries[path]["result_collision_signatures"]) for path in EVENT_PATHS)
    mode_only_local_derivable = result_collision_total == 0 and local_collision_count == 0
    numeric_phase_storage_eliminable = result_collision_total == 0

    summary_row = {
        "seed": seed,
        "ticks_run": int(timeline_rows[-1]["tick"]) if timeline_rows else 0,
        "first_nonzero_phase_tick": -1 if first_nonzero_tick is None else first_nonzero_tick,
        "last_nonzero_phase_tick": -1 if last_nonzero_tick is None else last_nonzero_tick,
        "phase_collapse_tick": -1 if phase_collapse_tick is None else phase_collapse_tick,
        "max_nonzero_phase_iotas": max_nonzero,
        "initial_nonzero_phase_iotas": initial_nonzero,
        "initial_phase_unique": initial_unique,
        "final_nonzero_phase_iotas": active_nonzero_phase(world),
        "vector_step_events": path_summaries["vector_step"]["events"],
        "vector_step_result_collision_signatures": path_summaries["vector_step"]["result_collision_signatures"],
        "vector_step_phase_collision_signatures": path_summaries["vector_step"]["phase_collision_signatures"],
        "rotate_takeover_events": path_summaries["rotate_takeover"]["events"],
        "rotate_takeover_result_collision_signatures": path_summaries["rotate_takeover"][
            "result_collision_signatures"
        ],
        "rotate_takeover_phase_collision_signatures": path_summaries["rotate_takeover"][
            "phase_collision_signatures"
        ],
        "rotation_offset_events": path_summaries["rotation_offset"]["events"],
        "rotation_offset_result_collision_signatures": path_summaries["rotation_offset"][
            "result_collision_signatures"
        ],
        "rotation_offset_phase_collision_signatures": path_summaries["rotation_offset"][
            "phase_collision_signatures"
        ],
        "signed_rotation_offset_events": path_summaries["signed_rotation_offset"]["events"],
        "signed_rotation_offset_result_collision_signatures": path_summaries["signed_rotation_offset"][
            "result_collision_signatures"
        ],
        "signed_rotation_offset_phase_collision_signatures": path_summaries["signed_rotation_offset"][
            "phase_collision_signatures"
        ],
        "local_cell_signature_records": len(local_records),
        "local_cell_phase_collision_signatures": local_collision_count,
        "mode_only_local_derivable": csv_bool(mode_only_local_derivable),
        "numeric_phase_storage_eliminable": csv_bool(numeric_phase_storage_eliminable),
    }
    return summary_row, path_rows, collision_rows, timeline_rows, local_collision_rows


def write_limited_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]], limit: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output_rows = rows if limit is None else rows[:limit]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    output_prefix = Path(args.output_prefix)

    summary_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    collision_rows: list[dict[str, Any]] = []
    timeline_rows: list[dict[str, Any]] = []
    local_collision_rows: list[dict[str, Any]] = []

    for seed in args.seeds:
        summary, paths, collisions, timeline, local_collisions = run_seed(args, int(seed))
        summary_rows.append(summary)
        path_rows.extend(paths)
        collision_rows.extend(collisions)
        timeline_rows.extend(timeline)
        local_collision_rows.extend(local_collisions)

    write_csv(output_prefix.with_name(output_prefix.name + "_summary.csv"), SUMMARY_FIELDNAMES, summary_rows)
    write_csv(output_prefix.with_name(output_prefix.name + "_paths.csv"), PATH_FIELDNAMES, path_rows)
    write_limited_csv(
        output_prefix.with_name(output_prefix.name + "_collisions.csv"),
        COLLISION_FIELDNAMES,
        collision_rows,
        int(args.collision_example_limit),
    )
    write_csv(output_prefix.with_name(output_prefix.name + "_timeline.csv"), TIMELINE_FIELDNAMES, timeline_rows)
    write_limited_csv(
        output_prefix.with_name(output_prefix.name + "_local_collisions.csv"),
        LOCAL_FIELDNAMES,
        local_collision_rows,
        int(args.collision_example_limit),
    )

    print(json.dumps(summary_rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
