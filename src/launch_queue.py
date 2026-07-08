from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def timestamp_run_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def build_supervisor_args(args: argparse.Namespace, run_id: str) -> list[str]:
    supervisor_args = [
        ".venv/bin/python",
        "src/queue_supervisor.py",
        "--run-id",
        run_id,
        "--phases",
        *args.phases,
        "--golden-jobs",
        str(args.golden_jobs),
        "--committor-jobs",
        str(args.committor_jobs),
        "--search-jobs",
        str(args.search_jobs),
        "--search-ticks",
        str(args.search_ticks),
        "--stagnation-window",
        str(args.stagnation_window),
        "--heartbeat-seconds",
        str(args.heartbeat_seconds),
        "--poll-seconds",
        str(args.poll_seconds),
    ]
    if args.continue_on_error:
        supervisor_args.append("--continue-on-error")
    return supervisor_args


def launch_screen(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path.cwd()
    output_dir = repo / "output/findings"
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or timestamp_run_id(args.run_prefix)
    session_name = args.session_name or f"iota_{run_id}"
    supervisor_args = build_supervisor_args(args, run_id)
    inner_command = (
        f"cd {shlex.quote(str(repo))} && "
        f"exec /usr/bin/caffeinate -dimsu {shlex.join(supervisor_args)}"
    )
    screen_command = [
        "/usr/bin/screen",
        "-dmS",
        session_name,
        "/bin/zsh",
        "-lc",
        inner_command,
    ]
    metadata = {
        "run_id": run_id,
        "session_name": session_name,
        "repo": str(repo),
        "screen_command": screen_command,
        "inner_command": inner_command,
        "state_path": str(output_dir / f"{run_id}_state.json"),
        "supervisor_log": str(output_dir / f"{run_id}_supervisor.log"),
    }
    if args.dry_run:
        return {**metadata, "launched": False}
    result = subprocess.run(screen_command, check=False, capture_output=True, text=True)
    metadata.update(
        {
            "launched": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    )
    if result.returncode != 0:
        raise SystemExit(json.dumps(metadata, indent=2))
    atomic_write_json(output_dir / f"{run_id}_launch.json", metadata)
    (output_dir / "run_seed42_56_v02_queue.latest_run_id").write_text(f"{run_id}\n", encoding="utf-8")
    (output_dir / "run_seed42_56_v02_queue.latest_session").write_text(f"{session_name}\n", encoding="utf-8")
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the instrumented Iota queue in a screen session.")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--run-prefix", default="queue")
    parser.add_argument("--session-name", default="")
    parser.add_argument(
        "--phases",
        nargs="+",
        choices=["all", "golden", "committor", "search", "smoke"],
        default=["all"],
    )
    parser.add_argument("--golden-jobs", type=int, default=4)
    parser.add_argument("--committor-jobs", type=int, default=3)
    parser.add_argument("--search-jobs", type=int, default=6)
    parser.add_argument("--search-ticks", type=int, default=1024)
    parser.add_argument("--stagnation-window", type=int, default=256)
    parser.add_argument("--heartbeat-seconds", type=float, default=60.0)
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    metadata = launch_screen(parse_args())
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
