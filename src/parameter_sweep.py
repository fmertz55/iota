from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path
from typing import Any

import yaml

from experiment_db import latest_experiment_id, open_database
from experiment_runner import lab_paths, run_experiment
from iota_rig import load_config


def latest_config(conn) -> dict[str, Any] | None:
    experiment_id = latest_experiment_id(conn)
    if experiment_id is None:
        return None
    row = conn.execute(
        """
        SELECT config_json
        FROM config_snapshots
        WHERE experiment_id = ?
        """,
        (experiment_id,),
    ).fetchone()
    if row is None:
        return None
    return json.loads(str(row[0]))


def get_nested(cfg: dict[str, Any], dotted_path: str) -> Any:
    current: Any = cfg
    for part in dotted_path.split("."):
        current = current[part]
    return current


def set_nested(cfg: dict[str, Any], dotted_path: str, value: Any) -> None:
    current: Any = cfg
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def rotate_to_start(values: list[int], start: int) -> list[int]:
    if start not in values:
        raise SystemExit(
            f"Current seed is {start}, but --seeds is {values}. "
            "Include the current seed so each run changes only one parameter."
        )
    index = values.index(start)
    return values[index:] + values[:index]


def parse_value(raw_value: str) -> Any:
    try:
        return yaml.safe_load(raw_value)
    except yaml.YAMLError as exc:
        raise SystemExit(f"Could not parse sweep value {raw_value!r}: {exc}") from exc


def display_sweep_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def sweep_configs(
    base_cfg: dict[str, Any],
    parameter_path: str,
    parameter_values: list[Any],
    seeds: list[int],
) -> list[tuple[dict[str, Any], Any, int]]:
    current_seed = int(get_nested(base_cfg, "init.seed"))
    seed_order = rotate_to_start(seeds, current_seed)
    configs = []
    for value_index, parameter_value in enumerate(parameter_values):
        ordered_seeds = seed_order if value_index % 2 == 0 else list(reversed(seed_order))
        for seed in ordered_seeds:
            cfg = copy.deepcopy(base_cfg)
            cfg.get("experiment", {}).pop("id", None)
            set_nested(cfg, parameter_path, parameter_value)
            set_nested(cfg, "init.seed", seed)
            configs.append((cfg, parameter_value, seed))
    return configs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a controlled one-parameter sweep.")
    parser.add_argument("parameter", help="Dotted config path, e.g. constants.amplitude_coupling")
    parser.add_argument("values", nargs="+", help="YAML values to sweep, e.g. 0.5 or '[3,3]'")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--objective", default="Amplitude coupling sweep")
    parser.add_argument("--notes", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config)
    file_cfg = load_config(config_path)
    db_path, _, _, _ = lab_paths(config_path, file_cfg)
    conn = open_database(db_path)
    base_cfg = latest_config(conn) or file_cfg
    conn.close()

    parameter_values = [parse_value(value) for value in args.values]
    configs = sweep_configs(base_cfg, args.parameter, parameter_values, args.seeds)
    if args.dry_run:
        for _, parameter_value, seed in configs:
            print(f"{args.parameter}={display_sweep_value(parameter_value)} init.seed={seed}")
        return

    base_dir = config_path.resolve().parent
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=base_dir,
        prefix=".iota_sweep_",
        suffix=".yaml",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    try:
        for cfg, parameter_value, seed in configs:
            temp_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            value_text = display_sweep_value(parameter_value)
            objective = f"{args.objective}: {args.parameter}={value_text}, seed={seed}"
            run_experiment(str(temp_path), objective, args.notes, force=False)
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
