from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import signal
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


PHASE_PATTERNS = (
    "parallel_replay.py",
    "v02_parameter_search.py",
    "queue_supervisor.py",
)


@dataclass(frozen=True)
class Phase:
    name: str
    command: list[str]


def timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temp_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    temp_path.replace(path)


def append_line(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp()} {message}\n")
        handle.flush()
        os.fsync(handle.fileno())


def run_capture(command: list[str], timeout: int = 10) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"{command!r} failed: {exc}"
    output = (result.stdout or "") + (result.stderr or "")
    return output.strip()


def process_table() -> list[tuple[int, int]]:
    output = run_capture(["ps", "-axo", "pid=,ppid="])
    rows: list[tuple[int, int]] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            rows.append((int(parts[0]), int(parts[1])))
        except ValueError:
            continue
    return rows


def descendant_pids(root_pid: int) -> list[int]:
    children_by_parent: dict[int, list[int]] = {}
    for pid, parent_pid in process_table():
        children_by_parent.setdefault(parent_pid, []).append(pid)
    found = [root_pid]
    cursor = 0
    while cursor < len(found):
        current_pid = found[cursor]
        cursor += 1
        found.extend(children_by_parent.get(current_pid, []))
    return found


def ps_snapshot(pids: list[int]) -> str:
    unique_pids = sorted(set(pid for pid in pids if pid > 0))
    if not unique_pids:
        return ""
    return run_capture(
        [
            "ps",
            "-o",
            "pid,ppid,pgid,etime,pcpu,pmem,stat,command",
            "-p",
            ",".join(str(pid) for pid in unique_pids),
        ]
    )


def broader_process_snapshot() -> str:
    output = run_capture(
        [
            "ps",
            "-o",
            "pid,ppid,pgid,etime,pcpu,pmem,stat,command",
            "-ax",
        ],
        timeout=20,
    )
    lines = []
    for line in output.splitlines():
        if any(pattern in line for pattern in PHASE_PATTERNS):
            lines.append(line)
    return "\n".join(lines)


def boot_time() -> str:
    return run_capture(["sysctl", "kern.boottime"])


def build_phases(args: argparse.Namespace) -> list[Phase]:
    phases = {
        "golden": Phase(
            "golden",
            [
                ".venv/bin/python",
                "src/parallel_replay.py",
                "golden",
                "--seeds",
                "42",
                "56",
                "--jobs",
                str(args.golden_jobs),
                "--output",
                "output/findings/parallel_golden_replay.json",
            ],
        ),
        "committor": Phase(
            "committor",
            [
                ".venv/bin/python",
                "src/parallel_replay.py",
                "committor",
                "--jobs",
                str(args.committor_jobs),
                "--targets",
                "output/findings/targeted_seed42_56_replay_targets.csv",
                "--output-dir",
                "output/findings/parallel_committor_seed42_56_targets",
                "--refresh",
            ],
        ),
        "search": Phase(
            "search",
            [
                ".venv/bin/python",
                "src/v02_parameter_search.py",
                "--jobs",
                str(args.search_jobs),
                "--ticks",
                str(args.search_ticks),
                "--stagnation-window",
                str(args.stagnation_window),
                "--output-prefix",
                "output/findings/finding_025_v02_parameter_search",
                "--flush-every",
                str(args.flush_every),
                "--top-n",
                str(args.top_n),
            ],
        ),
        "smoke": Phase(
            "smoke",
            [
                ".venv/bin/python",
                "-c",
                "import os,time; print('smoke pid', os.getpid(), flush=True); time.sleep(2); print('smoke done', flush=True)",
            ],
        ),
    }
    selected = args.phases
    if selected == ["all"]:
        selected = ["golden", "committor", "search"]
    return [phases[name] for name in selected]


class Supervisor:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.output_dir = Path(args.output_dir)
        self.run_id = args.run_id or datetime.now().strftime("queue_%Y%m%d_%H%M%S")
        self.supervisor_log = self.output_dir / f"{self.run_id}_supervisor.log"
        self.state_path = self.output_dir / f"{self.run_id}_state.json"
        self.current_process: subprocess.Popen[str] | None = None
        self.state: dict[str, Any] = {
            "run_id": self.run_id,
            "status": "starting",
            "started_at": timestamp(),
            "repo": str(Path.cwd()),
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "python": sys.version,
            "supervisor_pid": os.getpid(),
            "boot_time": boot_time(),
            "phases": [],
        }

    def write_state(self) -> None:
        atomic_write_json(self.state_path, self.state)

    def log(self, message: str) -> None:
        append_line(self.supervisor_log, message)

    def install_signal_handlers(self) -> None:
        for signal_name in ("SIGTERM", "SIGINT", "SIGHUP", "SIGQUIT"):
            signal_value = getattr(signal, signal_name, None)
            if signal_value is None:
                continue
            signal.signal(signal_value, self.handle_signal)

    def handle_signal(self, signal_number: int, _frame: Any) -> None:
        signal_name = signal.Signals(signal_number).name
        self.log(f"received {signal_name}; terminating current child")
        self.state["status"] = "interrupted"
        self.state["interrupted_at"] = timestamp()
        self.state["signal"] = signal_name
        self.write_state()
        if self.current_process is not None and self.current_process.poll() is None:
            try:
                os.killpg(self.current_process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except Exception as exc:
                self.log(f"failed to terminate process group {self.current_process.pid}: {exc}")
        raise SystemExit(128 + signal_number)

    def preflight(self) -> None:
        self.log("preflight start")
        self.log(f"cwd={Path.cwd()}")
        self.log(f"boot_time={self.state['boot_time']}")
        self.log(f"uptime={run_capture(['uptime'])}")
        self.log(f"python={run_capture(['.venv/bin/python', '--version'])}")
        self.log(f"git_status={run_capture(['git', 'status', '--short', '--branch'])}")
        self.log(f"process_snapshot=\n{broader_process_snapshot()}")
        self.log("preflight complete")

    def run_phase(self, phase: Phase) -> int:
        phase_log = self.output_dir / f"{self.run_id}_{phase.name}.log"
        phase_record: dict[str, Any] = {
            "name": phase.name,
            "command": phase.command,
            "command_text": shlex.join(phase.command),
            "phase_log": str(phase_log),
            "started_at": timestamp(),
            "status": "running",
        }
        self.state["current_phase"] = phase_record
        self.state["phases"].append(phase_record)
        self.write_state()
        self.log(f"phase {phase.name} start: {phase_record['command_text']}")

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        with phase_log.open("a", encoding="utf-8") as phase_handle:
            phase_handle.write(f"{timestamp()} START {phase_record['command_text']}\n")
            phase_handle.flush()
            os.fsync(phase_handle.fileno())
            self.current_process = subprocess.Popen(
                phase.command,
                stdout=phase_handle,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                start_new_session=True,
            )
            phase_record["pid"] = self.current_process.pid
            phase_record["process_group"] = self.current_process.pid
            self.write_state()
            self.log(f"phase {phase.name} child_pid={self.current_process.pid}")

            last_heartbeat = 0.0
            while True:
                exit_code = self.current_process.poll()
                now = time.monotonic()
                if now - last_heartbeat >= self.args.heartbeat_seconds:
                    pids = descendant_pids(self.current_process.pid)
                    snapshot = ps_snapshot(pids)
                    self.log(
                        f"heartbeat phase={phase.name} child_pid={self.current_process.pid} "
                        f"exit_code={exit_code} descendants={pids}\n{snapshot}"
                    )
                    phase_record["last_heartbeat_at"] = timestamp()
                    phase_record["last_descendant_pids"] = pids
                    self.write_state()
                    last_heartbeat = now
                if exit_code is not None:
                    phase_record["exit_code"] = exit_code
                    phase_record["finished_at"] = timestamp()
                    phase_record["status"] = "completed" if exit_code == 0 else "failed"
                    phase_handle.write(f"{timestamp()} EXIT {exit_code}\n")
                    phase_handle.flush()
                    os.fsync(phase_handle.fileno())
                    self.write_state()
                    self.log(f"phase {phase.name} exit_code={exit_code}")
                    self.current_process = None
                    return int(exit_code)
                time.sleep(self.args.poll_seconds)

    def run(self) -> int:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.install_signal_handlers()
        self.state["status"] = "running"
        self.write_state()
        self.preflight()
        phases = build_phases(self.args)
        self.state["planned_phases"] = [asdict(phase) for phase in phases]
        self.write_state()

        final_exit_code = 0
        for phase in phases:
            exit_code = self.run_phase(phase)
            if exit_code != 0:
                final_exit_code = exit_code
                if not self.args.continue_on_error:
                    self.log(f"stopping after failed phase {phase.name}")
                    break
        self.state["status"] = "completed" if final_exit_code == 0 else "failed"
        self.state["finished_at"] = timestamp()
        self.state["exit_code"] = final_exit_code
        self.write_state()
        self.log(f"supervisor exit_code={final_exit_code}")
        return final_exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Instrumented Iota long-run queue supervisor.")
    parser.add_argument("--output-dir", default="output/findings")
    parser.add_argument("--run-id", default="")
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
    parser.add_argument("--flush-every", type=int, default=8)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--heartbeat-seconds", type=float, default=60.0)
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    parser.add_argument("--continue-on-error", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    supervisor = Supervisor(args)
    raise SystemExit(supervisor.run())


if __name__ == "__main__":
    main()
