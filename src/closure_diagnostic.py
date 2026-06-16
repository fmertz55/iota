from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from experiment_db import open_database
from iota_rig import decay, init_world, local_candidates, step, vector_step


def load_experiment_config(db_path: Path, experiment_id: int) -> dict[str, Any]:
    conn = open_database(db_path)
    try:
        row = conn.execute(
            """
            SELECT config_json
            FROM config_snapshots
            WHERE experiment_id = ?
            """,
            (experiment_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise SystemExit(f"No config snapshot found for IOTA-{experiment_id:06d}")
    return json.loads(str(row[0]))


def replay_world(cfg: dict[str, Any], tick_override: int | None = None) -> Any:
    world = init_world(cfg)
    ticks = int(tick_override if tick_override is not None else cfg["run"].get("ticks", 0))
    for _ in range(ticks):
        step(world, cfg)
    return world


def target_for_cell(world: Any, cfg: dict[str, Any], coord: tuple[int, int, int]) -> dict[str, Any]:
    x, y, z = coord
    a = int(world.A[x, y, z])
    r = int(world.R[x, y, z])
    v_idx = int(world.V[x, y, z]) % len(world.vectors)
    p = int(world.P[x, y, z])
    dx, dy, dz, behavior = vector_step(world, v_idx, a, r, p)

    tx, ty, tz = x + dx, y + dy, z + dz
    if world.wrap:
        tx %= world.size
        ty %= world.size
        tz %= world.size
    distance = math.sqrt(dx**2 + dy**2 + dz**2)
    influence = (a / 7.0) * decay(distance, r, cfg["constants"].get("decay_mode", "inverse_square"))
    if behavior == "diffuse":
        influence *= 0.5

    return {
        "coord": coord,
        "state": {"A": a, "R": r, "V": v_idx, "P": p, "behavior": behavior},
        "step": (dx, dy, dz),
        "target": (int(tx), int(ty), int(tz)),
        "target_active": bool(world.active[tx, ty, tz]),
        "target_state": {
            "A": int(world.A[tx, ty, tz]),
            "R": int(world.R[tx, ty, tz]),
            "V": int(world.V[tx, ty, tz]),
            "P": int(world.P[tx, ty, tz]),
        },
        "influence": influence,
    }


def candidate_rows_for_cell(world: Any, cfg: dict[str, Any], coord: tuple[int, int, int]) -> list[dict[str, Any]]:
    x, y, z = coord
    a = int(world.A[x, y, z])
    r = int(world.R[x, y, z])
    v_idx = int(world.V[x, y, z]) % len(world.vectors)
    p = int(world.P[x, y, z])
    valence = max(1, int(cfg["constants"].get("valence", 1)))
    decay_mode = cfg["constants"].get("decay_mode", "inverse_square")
    return local_candidates(world, x, y, z, v_idx, a, r, p, decay_mode, valence)


def limited_values(values: set[tuple[int, int, int]], limit: int) -> list[tuple[int, int, int] | str]:
    ordered = sorted(values)
    if len(ordered) <= limit:
        return ordered
    return [*ordered[:limit], f"... {len(ordered) - limit} more"]


def print_diagnostic(db_path: Path, experiment_id: int, limit: int, tick_override: int | None) -> None:
    cfg = load_experiment_config(db_path, experiment_id)
    world = replay_world(cfg, tick_override)
    active_coords = sorted(
        tuple(int(value) for value in coord)
        for coord in zip(*world.active.nonzero())
    )
    active_set = set(active_coords)

    print(f"IOTA-{experiment_id:06d}")
    print(
        f"ticks={tick_override if tick_override is not None else cfg['run'].get('ticks')} "
        f"range_range={cfg['init'].get('range_range')} "
        f"valence={cfg['constants'].get('valence', 1)}"
    )
    print(f"active_count={len(active_coords)}")
    print("active_cells:")
    outgoing_targets = set()
    productive_targets = set()
    productive_edges = 0
    productive_external_edges = 0
    for coord in active_coords:
        rows = candidate_rows_for_cell(world, cfg, coord)
        productive_edges += len(rows)
        for candidate in rows:
            productive_targets.add(candidate["target"])
            if candidate["target"] not in active_set:
                productive_external_edges += 1

        row = target_for_cell(world, cfg, coord)
        outgoing_targets.add(row["target"])
        if len(outgoing_targets) > limit:
            continue
        state = row["state"]
        target = row["target"]
        target_state = row["target_state"]
        print(
            "  "
            f"{coord} "
            f"A={state['A']} R={state['R']} V={state['V']} P={state['P']} "
            f"behavior={state['behavior']} step={row['step']} "
            f"target={target} active={row['target_active']} "
            f"influence={row['influence']:.6f} "
            f"target_state=A{target_state['A']}/R{target_state['R']}/V{target_state['V']}/P{target_state['P']}"
        )
    print(f"closed_under_outgoing_targets={outgoing_targets <= active_set}")
    print(f"external_targets={limited_values(outgoing_targets - active_set, limit)}")
    print(f"closed_under_productive_targets={productive_targets <= active_set}")
    print(f"productive_external_targets={limited_values(productive_targets - active_set, limit)}")
    print(f"productive_edges={productive_edges}")
    print(f"productive_external_edges={productive_external_edges}")
    if len(active_coords) > limit:
        print(f"printed_cell_limit={limit}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay an experiment and inspect active-cell closure.")
    parser.add_argument("experiment_ids", nargs="+", type=int)
    parser.add_argument("--database", default="data/iota_lab.db")
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--ticks", type=int, default=None)
    args = parser.parse_args()

    for experiment_id in args.experiment_ids:
        print_diagnostic(Path(args.database), experiment_id, args.limit, args.ticks)


if __name__ == "__main__":
    main()
