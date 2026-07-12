from __future__ import annotations

import argparse
import json
import os
import queue
import shlex
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def reader(stream: Any, messages: queue.Queue[str | None]) -> None:
    try:
        for line in iter(stream.readline, ""):
            messages.put(line)
    finally:
        messages.put(None)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a command with a durable local log and atomically updated "
            "heartbeat state."
        )
    )
    parser.add_argument("--name", required=True)
    parser.add_argument("--state-dir", type=Path, default=Path(".run_state"))
    parser.add_argument("--heartbeat-seconds", type=float, default=30.0)
    parser.add_argument("--tail-lines", type=int, default=40)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required after --")
    if args.heartbeat_seconds <= 0 or args.tail_lines <= 0:
        parser.error("heartbeat and tail-lines must be positive")
    return args


def main() -> None:
    args = parse_args()
    safe_name = "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in args.name
    ).strip("-")
    if not safe_name:
        raise SystemExit("--name must contain a letter or number")
    state_dir = args.state_dir.resolve()
    run_stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    run_id = f"{safe_name}-{run_stamp}"
    state_path = state_dir / f"{run_id}.json"
    latest_path = state_dir / f"latest-{safe_name}.json"
    log_path = state_dir / f"{run_id}.log"
    state_dir.mkdir(parents=True, exist_ok=True)

    started_wall = time.time()
    started_monotonic = time.monotonic()
    tail: deque[str] = deque(maxlen=int(args.tail_lines))
    state: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "name": safe_name,
        "status": "starting",
        "command": args.command,
        "command_text": shlex.join(args.command),
        "cwd": str(ROOT),
        "git_head_at_start": git_head(),
        "started_at": timestamp(),
        "updated_at": timestamp(),
        "heartbeat_seconds": float(args.heartbeat_seconds),
        "log_path": str(log_path),
        "state_path": str(state_path),
        "output_lines": 0,
        "output_bytes": 0,
        "last_output_at": None,
        "output_tail": [],
    }

    def write_state() -> None:
        state["updated_at"] = timestamp()
        state["elapsed_seconds"] = round(time.monotonic() - started_monotonic, 3)
        state["output_tail"] = list(tail)
        atomic_json(state_path, state)
        atomic_json(latest_path, state)

    write_state()
    environment = os.environ.copy()
    environment.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    process = subprocess.Popen(
        args.command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=environment,
        start_new_session=True,
    )
    state.update({"status": "running", "pid": process.pid, "process_group": process.pid})
    write_state()

    def forward_signal(signum: int, _frame: Any) -> None:
        state["status"] = "terminating"
        state["received_signal"] = signum
        write_state()
        try:
            os.killpg(process.pid, signum)
        except ProcessLookupError:
            pass

    signal.signal(signal.SIGINT, forward_signal)
    signal.signal(signal.SIGTERM, forward_signal)
    messages: queue.Queue[str | None] = queue.Queue()
    thread = threading.Thread(target=reader, args=(process.stdout, messages), daemon=True)
    thread.start()
    next_heartbeat = time.monotonic() + float(args.heartbeat_seconds)
    reader_finished = False

    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"{timestamp()} START {state['command_text']}\n")
        log.flush()
        os.fsync(log.fileno())
        while not reader_finished or process.poll() is None:
            try:
                message = messages.get(timeout=0.25)
            except queue.Empty:
                message = ""
            if message is None:
                reader_finished = True
            elif message:
                sys.stdout.write(message)
                sys.stdout.flush()
                log.write(message)
                state["output_lines"] += 1
                state["output_bytes"] += len(message.encode("utf-8"))
                state["last_output_at"] = timestamp()
                tail.append(message.rstrip("\r\n"))
            if time.monotonic() >= next_heartbeat:
                log.write(
                    f"{timestamp()} HEARTBEAT elapsed_seconds="
                    f"{time.monotonic() - started_monotonic:.1f} "
                    f"output_lines={state['output_lines']}\n"
                )
                log.flush()
                os.fsync(log.fileno())
                write_state()
                next_heartbeat = time.monotonic() + float(args.heartbeat_seconds)
        exit_code = process.wait()
        log.write(f"{timestamp()} EXIT {exit_code}\n")
        log.flush()
        os.fsync(log.fileno())

    state.update(
        {
            "status": "completed" if exit_code == 0 else "failed",
            "exit_code": int(exit_code),
            "finished_at": timestamp(),
            "duration_seconds": round(time.time() - started_wall, 3),
            "git_head_at_finish": git_head(),
        }
    )
    write_state()
    print(f"heartbeat state: {latest_path}", flush=True)
    print(f"durable log: {log_path}", flush=True)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
