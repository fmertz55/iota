from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DIFF_IGNORES = {
    "experiment.id",
    "experiment.objective",
    "lab.database",
    "lab.experiments_dir",
    "run.output_dir",
    "simulation_version",
}
DIFF_IGNORE_PREFIXES = ("artifacts.",)


def canonical_config(cfg: dict[str, Any]) -> str:
    return json.dumps(cfg, sort_keys=True, separators=(",", ":"), default=str)


def config_hash(cfg: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_config(cfg).encode("utf-8")).hexdigest()


def simulation_version(cfg: dict[str, Any]) -> str:
    return str(cfg.get("simulation_version", "unknown"))


def parameter_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def flatten_config(cfg: dict[str, Any], prefix: str = "") -> dict[str, str]:
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
            config_hash TEXT NOT NULL,
            simulation_version TEXT NOT NULL DEFAULT 'unknown'
        );

        CREATE TABLE IF NOT EXISTS config_snapshots (
            experiment_id INTEGER PRIMARY KEY,
            config_json TEXT NOT NULL,
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
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

        CREATE TABLE IF NOT EXISTS artifacts (
            experiment_id INTEGER NOT NULL,
            artifact_type TEXT NOT NULL,
            tick INTEGER,
            path TEXT NOT NULL,
            sha256 TEXT,
            bytes INTEGER NOT NULL,
            retained INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (experiment_id, path),
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
        );
        """
    )
    columns = {
        str(row[1])
        for row in conn.execute("PRAGMA table_info(experiments)").fetchall()
    }
    if "simulation_version" not in columns:
        conn.execute(
            "ALTER TABLE experiments "
            "ADD COLUMN simulation_version TEXT NOT NULL DEFAULT 'unknown'"
        )
    metric_columns = {
        str(row[1])
        for row in conn.execute("PRAGMA table_info(metrics)").fetchall()
    }
    if "coherence_ratio" not in metric_columns:
        conn.execute(
            "ALTER TABLE metrics "
            "ADD COLUMN coherence_ratio REAL NOT NULL DEFAULT 0.0"
        )
        conn.execute(
            """
            UPDATE metrics
            SET coherence_ratio = CASE
                WHEN active_iotas > 0 THEN CAST(largest_coherence AS REAL) / active_iotas
                ELSE 0.0
            END
            """
        )
    conn.commit()
    return conn


def latest_experiment_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute("SELECT MAX(experiment_id) FROM experiments").fetchone()
    return int(row[0]) if row and row[0] is not None else None


def configured_experiment_id(cfg: dict[str, Any]) -> int | None:
    experiment_id = cfg.get("experiment", {}).get("id")
    if experiment_id is None:
        return None
    match = re.fullmatch(r"IOTA-(\d{6})", str(experiment_id).strip().upper())
    if not match:
        raise SystemExit(f"experiment.id must look like IOTA-000001, got {experiment_id!r}")
    return int(match.group(1))


def load_parameters(conn: sqlite3.Connection, experiment_id: int) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT parameter_name, parameter_value
        FROM parameters
        WHERE experiment_id = ?
        """,
        (experiment_id,),
    ).fetchall()
    return {str(name): str(value) for name, value in rows}


def detect_parameter_diffs(
    previous: dict[str, str],
    current: dict[str, str],
) -> list[tuple[str, str | None, str | None]]:
    diffs = []
    for name in sorted(set(previous) | set(current)):
        if name in DIFF_IGNORES or name.startswith(DIFF_IGNORE_PREFIXES):
            continue
        old_value = previous.get(name)
        new_value = current.get(name)
        if old_value != new_value:
            diffs.append((name, old_value, new_value))
    return diffs


def create_experiment(
    conn: sqlite3.Connection,
    cfg: dict[str, Any],
    objective: str,
    notes: str,
    force: bool,
) -> tuple[int, str, list[tuple[str, str | None, str | None]]]:
    current_params = flatten_config(cfg)
    previous_id = latest_experiment_id(conn)
    diffs: list[tuple[str, str | None, str | None]] = []
    if previous_id is not None:
        diffs = detect_parameter_diffs(load_parameters(conn, previous_id), current_params)
        if len(diffs) != 1:
            lines = [
                "Experiment rejected.",
                f"{len(diffs)} controlled parameters changed.",
                "Exactly one controlled parameter must change after the baseline.",
                "",
            ]
            lines.extend(name for name, _, _ in diffs)
            raise SystemExit("\n".join(lines))
    if force:
        print("--force is ignored; the one-parameter protocol is always enforced.")

    timestamp = datetime.now(timezone.utc).isoformat()
    cfg_hash = config_hash(cfg)
    sim_version = simulation_version(cfg)
    configured_id = configured_experiment_id(cfg)
    if configured_id is None:
        cursor = conn.execute(
            """
            INSERT INTO experiments (timestamp, objective, notes, config_hash, simulation_version)
            VALUES (?, ?, ?, ?, ?)
            """,
            (timestamp, objective, notes, cfg_hash, sim_version),
        )
    else:
        cursor = conn.execute(
            """
            INSERT INTO experiments (
                experiment_id,
                timestamp,
                objective,
                notes,
                config_hash,
                simulation_version
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (configured_id, timestamp, objective, notes, cfg_hash, sim_version),
        )
    experiment_id = int(cursor.lastrowid)
    conn.execute(
        """
        INSERT INTO config_snapshots (experiment_id, config_json)
        VALUES (?, ?)
        """,
        (experiment_id, canonical_config(cfg)),
    )
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


def artifact_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_path(path: Path, base_dir: Path) -> str:
    return path.resolve().relative_to(base_dir.resolve()).as_posix()


def register_artifact(
    conn: sqlite3.Connection,
    experiment_id: int,
    artifact_type: str,
    path: Path,
    base_dir: Path,
    tick: int | None = None,
    retained: bool = True,
) -> None:
    if not path.exists():
        return
    relative_path = artifact_path(path, base_dir)
    conn.execute(
        """
        INSERT INTO artifacts (
            experiment_id,
            artifact_type,
            tick,
            path,
            sha256,
            bytes,
            retained,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(experiment_id, path) DO UPDATE SET
            artifact_type = excluded.artifact_type,
            tick = excluded.tick,
            sha256 = excluded.sha256,
            bytes = excluded.bytes,
            retained = excluded.retained,
            created_at = excluded.created_at
        """,
        (
            experiment_id,
            artifact_type,
            tick,
            relative_path,
            artifact_hash(path),
            path.stat().st_size,
            1 if retained else 0,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()


def mark_artifact_pruned(
    conn: sqlite3.Connection,
    experiment_id: int,
    path: Path,
    base_dir: Path,
) -> None:
    conn.execute(
        """
        UPDATE artifacts
        SET retained = 0
        WHERE experiment_id = ?
          AND path = ?
        """,
        (experiment_id, artifact_path(path, base_dir)),
    )
    conn.commit()


def insert_metric(conn: sqlite3.Connection, experiment_id: int, metric: dict[str, float]) -> None:
    conn.execute(
        """
        INSERT INTO metrics (
            experiment_id,
            tick,
            active_iotas,
            largest_coherence,
            coherence_count,
            coherence_ratio,
            entropy
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            experiment_id,
            int(metric["tick"]),
            int(metric["active_iotas"]),
            int(metric["largest_coherence"]),
            int(metric["coherence_count"]),
            float(metric["coherence_ratio"]),
            float(metric["entropy"]),
        ),
    )
    conn.commit()


def insert_summary_metrics(
    conn: sqlite3.Connection,
    experiment_id: int,
    summary: dict[str, float],
) -> None:
    conn.executemany(
        """
        INSERT INTO summary_metrics (experiment_id, metric_name, metric_value)
        VALUES (?, ?, ?)
        """,
        [(experiment_id, name, float(value)) for name, value in summary.items()],
    )
    conn.commit()
