from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
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

DIFF_IGNORES = {"lab.database", "lab.experiments_dir", "run.output_dir"}


def load_config(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def canonical_config(cfg: Dict[str, Any]) -> str:
    return json.dumps(cfg, sort_keys=True, separators=(",", ":"), default=str)


def config_hash(cfg: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_config(cfg).encode("utf-8")).hexdigest()


def parameter_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def flatten_config(cfg: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
    flat = {}
    for key, value in sorted(cfg.items()):
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            flat.update(flatten_config(value, name))
        else:
            flat[name] = parameter_value(value)
    return flat


def display_value(value: str | None) -> str:
    if value is None:
        return "<missing>"
    try:
        return str(json.loads(value))
    except json.JSONDecodeError:
        return value


def open_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS experiments (
            experiment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            objective TEXT NOT NULL,
            notes TEXT NOT NULL,
            config_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS parameters (
            experiment_id INTEGER NOT NULL,
            parameter_name TEXT NOT NULL,
            parameter_value TEXT NOT NULL,
            PRIMARY KEY (experiment_id, parameter_name),
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        );

        CREATE TABLE IF NOT EXISTS metrics (
            experiment_id INTEGER NOT NULL,
            tick INTEGER NOT NULL,
            active_iotas INTEGER NOT NULL,
            largest_coherence INTEGER NOT NULL,
            coherence_count INTEGER NOT NULL,
            entropy REAL NOT NULL,
            PRIMARY KEY (experiment_id, tick),
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        );

        CREATE TABLE IF NOT EXISTS observations (
            experiment_id INTEGER PRIMARY KEY,
            result TEXT NOT NULL,
            summary TEXT NOT NULL,
            next_experiment TEXT NOT NULL,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        );

        CREATE TABLE IF NOT EXISTS parameter_diffs (
            experiment_id INTEGER NOT NULL,
            parameter_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        );

        CREATE TABLE IF NOT EXISTS summary_metrics (
            experiment_id INTEGER NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            PRIMARY KEY (experiment_id, metric_name),
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        );
        """
    )
    conn.commit()
    return conn


def latest_experiment_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute("SELECT MAX(experiment_id) FROM experiments").fetchone()
    return int(row[0]) if row and row[0] is not None else None


def load_parameters(conn: sqlite3.Connection, experiment_id: int) -> Dict[str, str]:
    rows = conn.execute(
        """
        SELECT parameter_name, parameter_value
        FROM parameters
        WHERE experiment_id = ?
        """,
        (experiment_id,),
    ).fetchall()
    return {str(name): str(value) for name, value in rows}


def detect_parameter_diffs(previous: Dict[str, str], current: Dict[str, str]) -> list[tuple[str, str | None, str | None]]:
    diffs = []
    for name in sorted(set(previous) | set(current)):
        if name in DIFF_IGNORES:
            continue
        old_value = previous.get(name)
        new_value = current.get(name)
        if old_value != new_value:
            diffs.append((name, old_value, new_value))
    return diffs


def create_experiment(
    conn: sqlite3.Connection,
    cfg: Dict[str, Any],
    objective: str,
    notes: str,
    force: bool,
) -> tuple[int, str, list[tuple[str, str | None, str | None]]]:
    current_params = flatten_config(cfg)
    previous_id = latest_experiment_id(conn)
    diffs: list[tuple[str, str | None, str | None]] = []
    if previous_id is not None:
        diffs = detect_parameter_diffs(load_parameters(conn, previous_id), current_params)
        if len(diffs) > 1 and not force:
            lines = [
                "Refusing to run: more than one parameter changed from the previous experiment.",
                "Use --force to intentionally allow this run.",
                "",
            ]
            lines.extend(
                f"- {name}: {display_value(old)} -> {display_value(new)}"
                for name, old, new in diffs
            )
            raise SystemExit("\n".join(lines))

    timestamp = datetime.now(timezone.utc).isoformat()
    cfg_hash = config_hash(cfg)
    cursor = conn.execute(
        """
        INSERT INTO experiments (timestamp, objective, notes, config_hash)
        VALUES (?, ?, ?, ?)
        """,
        (timestamp, objective, notes, cfg_hash),
    )
    experiment_id = int(cursor.lastrowid)
    conn.executemany(
        """
        INSERT INTO parameters (experiment_id, parameter_name, parameter_value)
        VALUES (?, ?, ?)
        """,
        [(experiment_id, name, value) for name, value in current_params.items()],
    )
    conn.executemany(
        """
        INSERT INTO parameter_diffs (experiment_id, parameter_name, old_value, new_value)
        VALUES (?, ?, ?, ?)
        """,
        [(experiment_id, name, old, new) for name, old, new in diffs],
    )
    conn.execute(
        """
        INSERT INTO observations (experiment_id, result, summary, next_experiment)
        VALUES (?, ?, ?, ?)
        """,
        (experiment_id, "pending", "Pending human interpretation.", ""),
    )
    conn.commit()
    return experiment_id, timestamp, diffs


def insert_metric(conn: sqlite3.Connection, experiment_id: int, metric: Dict[str, float]) -> None:
    conn.execute(
        """
        INSERT INTO metrics (
            experiment_id,
            tick,
            active_iotas,
            largest_coherence,
            coherence_count,
            entropy
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            experiment_id,
            int(metric["tick"]),
            int(metric["active_iotas"]),
            int(metric["largest_coherence"]),
            int(metric["coherence_count"]),
            float(metric["entropy"]),
        ),
    )
    conn.commit()


def insert_summary_metrics(conn: sqlite3.Connection, experiment_id: int, summary: Dict[str, float]) -> None:
    conn.executemany(
        """
        INSERT INTO summary_metrics (experiment_id, metric_name, metric_value)
        VALUES (?, ?, ?)
        """,
        [(experiment_id, name, float(value)) for name, value in summary.items()],
    )
    conn.commit()


def make_vectors(cfg: Dict[str, Any], rng: np.random.Generator) -> np.ndarray:
    mode = cfg["vectors"].get("mode", "cube26")
    count = int(cfg["vectors"].get("vector_count", 64))
    if mode == "cube6":
        base = CUBE6
    elif mode == "cube26":
        base = CUBE26
    elif mode == "random64":
        # Random local-ish vectors in [-1,1]^3 excluding zero.
        vals = []
        while len(vals) < count:
            v = rng.integers(-1, 2, size=3)
            if np.any(v != 0):
                vals.append(tuple(int(x) for x in v))
        return np.array(vals, dtype=np.int16)
    else:
        raise ValueError(f"Unknown vector mode: {mode}")

    # Map 64 vector states onto repeated physical neighbor vectors.
    reps = math.ceil(count / len(base))
    return np.tile(base, (reps, 1))[:count].astype(np.int16)


@dataclass
class World:
    active: np.ndarray
    A: np.ndarray
    R: np.ndarray
    V: np.ndarray
    P: np.ndarray
    vectors: np.ndarray
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
    vectors = make_vectors(cfg, rng)

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

    return World(active, A, R, V, P, vectors, wrap, rng)


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


def step(world: World, cfg: Dict[str, Any]) -> Dict[str, float]:
    size = world.size
    kA = float(cfg["constants"].get("amplitude_coupling", 0.125))
    kR = float(cfg["constants"].get("range_coupling", 0.125))
    thetaP = float(cfg["constants"].get("payload_takeover", 0.5))
    mu = float(cfg["constants"].get("mutation_rate", 0.0))
    decay_mode = cfg["constants"].get("decay_mode", "inverse_square")
    conservation = cfg["constants"].get("conservation", "soft")

    next_active = world.active.copy()
    next_A = world.A.astype(np.float32).copy()
    next_R = world.R.astype(np.float32).copy()
    next_V = world.V.copy()
    next_P = world.P.copy()

    coords = np.argwhere(world.active)
    exchanges = 0
    payload_changes = 0

    # Simple sparse update: iterate only active/non-dark iotas.
    for x, y, z in coords:
        a = int(world.A[x, y, z])
        r = int(world.R[x, y, z])
        if a == 0 or r == 0:
            continue
        v_idx = int(world.V[x, y, z]) % len(world.vectors)
        dx, dy, dz = world.vectors[v_idx]

        # One direct vector pass per tick. Range controls influence magnitude, not multi-hop fanout yet.
        tx, ty, tz = int(x + dx), int(y + dy), int(z + dz)
        if world.wrap:
            tx %= size; ty %= size; tz %= size
        elif not (0 <= tx < size and 0 <= ty < size and 0 <= tz < size):
            continue

        d = math.sqrt(int(dx)**2 + int(dy)**2 + int(dz)**2)
        influence = (a / 7.0) * decay(d, r, decay_mode)
        if influence <= 0:
            continue

        exchanges += 1
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
            next_V[tx, ty, tz] = np.uint8((v_idx + new_p) % len(world.vectors))
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
        "payload_changes": payload_changes,
        "mean_A": float(world.A[world.active].mean()) if active_count else 0.0,
        "mean_R": float(world.R[world.active].mean()) if active_count else 0.0,
        "max_payload_fraction": max_payload_fraction,
    }


def coherence_stats(world: World) -> tuple[int, int]:
    active_coords = {tuple(int(v) for v in coord) for coord in np.argwhere(world.active)}
    if not active_coords:
        return 0, 0

    size = world.size
    largest = 0
    count = 0
    neighbors = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    while active_coords:
        count += 1
        component_size = 0
        stack = [active_coords.pop()]
        while stack:
            x, y, z = stack.pop()
            component_size += 1
            for dx, dy, dz in neighbors:
                nx, ny, nz = x + dx, y + dy, z + dz
                if world.wrap:
                    nx %= size
                    ny %= size
                    nz %= size
                elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
                    continue
                neighbor = (nx, ny, nz)
                if neighbor in active_coords:
                    active_coords.remove(neighbor)
                    stack.append(neighbor)
        largest = max(largest, component_size)
    return largest, count


def payload_entropy(world: World) -> float:
    active_count = int(world.active.sum())
    if active_count == 0:
        return 0.0
    hist = np.bincount(world.P[world.active], minlength=8).astype(np.float64)
    probabilities = hist[hist > 0] / active_count
    return float(-np.sum(probabilities * np.log2(probabilities)))


def collect_metrics(world: World, tick: int, extras: Dict[str, float] | None = None) -> Dict[str, float]:
    active_count = int(world.active.sum())
    largest, count = coherence_stats(world)
    metric = {
        "tick": int(tick),
        "active_iotas": active_count,
        "largest_coherence": int(largest),
        "coherence_count": int(count),
        "entropy": payload_entropy(world),
    }
    if extras:
        metric.update(extras)
    return metric


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


def save_metrics(metrics: list[Dict[str, float]], out: Path) -> None:
    if not metrics:
        return
    keys = [
        "tick",
        "active_iotas",
        "largest_coherence",
        "coherence_count",
        "entropy",
        "exchanges",
        "payload_changes",
        "mean_A",
        "mean_R",
        "max_payload_fraction",
    ]
    with open(out / "metrics.csv", "w", encoding="utf-8") as f:
        f.write(",".join(keys) + "\n")
        for row in metrics:
            f.write(",".join(str(row.get(k, "")) for k in keys) + "\n")

    ticks = [m["tick"] for m in metrics]
    active = [m["active_iotas"] for m in metrics]
    plt.figure(figsize=(8, 5))
    plt.plot(ticks, active)
    plt.title("Active / non-dark iotas over time")
    plt.xlabel("tick")
    plt.ylabel("active iotas")
    plt.tight_layout()
    plt.savefig(out / "active_over_time.png", dpi=140)
    plt.close()

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    series = [
        ("active_iotas", "Active Iotas"),
        ("largest_coherence", "Largest Coherence"),
        ("coherence_count", "Number of Coherences"),
        ("entropy", "Payload Entropy"),
    ]
    for ax, (key, label) in zip(axes.flat, series):
        ax.plot(ticks, [m[key] for m in metrics])
        ax.set_title(label)
        ax.set_xlabel("tick")
    fig.tight_layout()
    fig.savefig(out / "metrics_timeseries.png", dpi=140)
    plt.close(fig)


def metrics_summary(metrics: list[Dict[str, float]], execution_time: float) -> Dict[str, float]:
    if not metrics:
        return {
            "peak_active_iotas": 0,
            "final_active_iotas": 0,
            "largest_coherence": 0,
            "coherence_count": 0,
            "entropy": 0.0,
            "persistence": 0.0,
            "execution_time_seconds": execution_time,
        }
    active = [int(m["active_iotas"]) for m in metrics]
    nonzero_ticks = sum(1 for value in active if value > 0)
    return {
        "peak_active_iotas": max(active),
        "final_active_iotas": active[-1],
        "largest_coherence": max(int(m["largest_coherence"]) for m in metrics),
        "coherence_count": int(metrics[-1]["coherence_count"]),
        "entropy": float(metrics[-1]["entropy"]),
        "persistence": float(nonzero_ticks / len(metrics)),
        "execution_time_seconds": execution_time,
    }


def ensure_experiment_template(experiments_dir: Path) -> None:
    experiments_dir.mkdir(parents=True, exist_ok=True)
    template = experiments_dir / "IOTA_EXPERIMENT_TEMPLATE.md"
    if template.exists():
        return
    template.write_text(
        """# IOTA-000000

## Objective

## Changed Parameter

- Parameter:
- Old Value:
- New Value:

## Configuration Hash

## Notes

## Metrics Summary

## Result

## Next Experiment
""",
        encoding="utf-8",
    )


def write_experiment_notebook(
    experiments_dir: Path,
    experiment_id: int,
    timestamp: str,
    objective: str,
    notes: str,
    cfg_hash: str,
    diffs: list[tuple[str, str | None, str | None]],
    summary: Dict[str, float],
    output_dir: Path,
) -> None:
    ensure_experiment_template(experiments_dir)
    label = f"IOTA-{experiment_id:06d}"
    if not diffs:
        diff_text = "- Changed Parameter: none\n- Old Value: n/a\n- New Value: n/a"
    elif len(diffs) == 1:
        name, old, new = diffs[0]
        diff_text = (
            f"- Changed Parameter: {name}\n"
            f"- Old Value: {display_value(old)}\n"
            f"- New Value: {display_value(new)}"
        )
    else:
        diff_text = "\n".join(
            f"- {name}: {display_value(old)} -> {display_value(new)}"
            for name, old, new in diffs
        )

    metrics_text = "\n".join(
        f"- {name}: {value}"
        for name, value in summary.items()
    )
    (experiments_dir / f"{label}.md").write_text(
        f"""# {label}

## Timestamp

{timestamp}

## Objective

{objective}

## Changed Parameter

{diff_text}

## Configuration Hash

{cfg_hash}

## Notes

{notes or "None"}

## Output

{output_dir}

## Metrics Summary

{metrics_text}

## Result

Pending human interpretation.

## Next Experiment

""",
        encoding="utf-8",
    )

def run(config_path: str, objective: str, notes: str, force: bool) -> None:
    cfg = load_config(config_path)
    base_dir = Path(config_path).resolve().parent
    lab_cfg = cfg.get("lab", {})
    db_path = base_dir / lab_cfg.get("database", "data/iota_lab.db")
    experiments_dir = base_dir / lab_cfg.get("experiments_dir", "experiments")
    conn = open_database(db_path)
    experiment_id, timestamp, diffs = create_experiment(conn, cfg, objective, notes, force)
    label = f"IOTA-{experiment_id:06d}"

    world = init_world(cfg)
    out = base_dir / cfg["run"].get("output_dir", "output") / label
    out.mkdir(parents=True, exist_ok=True)

    ticks = int(cfg["run"].get("ticks", 256))
    snapshot_every = int(cfg["run"].get("snapshot_every", 8))
    metrics: list[Dict[str, float]] = []
    start = time.perf_counter()

    # initial snapshot
    save_slice(world, out, 0, cfg)
    save_scatter(world, out, 0, cfg)
    initial_metric = collect_metrics(world, 0)
    metrics.append(initial_metric)
    insert_metric(conn, experiment_id, initial_metric)

    for t in range(1, ticks + 1):
        extras = step(world, cfg)
        metric = collect_metrics(world, t, extras)
        metrics.append(metric)
        insert_metric(conn, experiment_id, metric)
        if t % snapshot_every == 0 or t == ticks:
            save_slice(world, out, t, cfg)
            save_scatter(world, out, t, cfg)
            save_metrics(metrics, out)
            print(
                f"tick={t} active={metric['active_iotas']} "
                f"largest_coherence={metric['largest_coherence']} "
                f"coherences={metric['coherence_count']} "
                f"entropy={metric['entropy']:.3f}"
            )

    save_metrics(metrics, out)
    elapsed = time.perf_counter() - start
    summary = metrics_summary(metrics, elapsed)
    insert_summary_metrics(conn, experiment_id, summary)
    write_experiment_notebook(
        experiments_dir,
        experiment_id,
        timestamp,
        objective,
        notes,
        config_hash(cfg),
        diffs,
        summary,
        out,
    )
    conn.close()

    if not diffs:
        print("Changed parameter: none")
    elif len(diffs) == 1:
        name, old, new = diffs[0]
        print(f"Changed parameter: {name} {display_value(old)} -> {display_value(new)}")
    else:
        print(f"Forced run with {len(diffs)} changed parameters")
    print(f"Experiment: {label}")
    print(f"Database: {db_path}")
    print(f"Notebook: {experiments_dir / f'{label}.md'}")
    print(f"Output: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Octal iota test rig")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--objective", default="Unspecified")
    parser.add_argument("--notes", default="")
    parser.add_argument("--force", action="store_true", help="allow more than one changed parameter")
    args = parser.parse_args()
    run(args.config, args.objective, args.notes, args.force)
