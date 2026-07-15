#!/usr/bin/env python3

"""Validate the completed quantum-Dirac experiment at its immutable tag."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVAL_TAG = "icp-quantum-dirac-role-recovery-001-v0.4-complete"
ARCHIVAL_COMMIT = "490dab6b2ce683f397ad37ecbe40d133f063188d"


def _git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _verify_checkpoint() -> None:
    tag_type = _git("cat-file", "-t", ARCHIVAL_TAG, check=False)
    if tag_type.returncode != 0 or tag_type.stdout.strip() != "tag":
        raise RuntimeError(f"annotated archival tag is unavailable: {ARCHIVAL_TAG}")
    resolved = _git("rev-parse", f"{ARCHIVAL_TAG}^{{commit}}", check=False)
    if resolved.returncode != 0 or resolved.stdout.strip() != ARCHIVAL_COMMIT:
        raise RuntimeError(
            f"archival tag {ARCHIVAL_TAG} does not identify {ARCHIVAL_COMMIT}"
        )


def _run_checkpoint_checks(worktree: Path) -> int:
    commands = (
        [sys.executable, "-m", "src.quantum_dirac.cli", "validate-manifests"],
        [sys.executable, "-m", "src.quantum_dirac.cli", "verify-seal"],
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests/quantum_dirac",
            "-p",
            "test_*.py",
        ],
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "from src.quantum_dirac.ledger import validate_result_ledger; "
                "from src.quantum_dirac.lifecycle import verify_ledger_bindings; "
                "from src.quantum_dirac.spec import load_json; "
                "root=Path.cwd(); "
                "base=root/'output/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001'; "
                "[(validate_result_ledger(value:=load_json(base/f'{stage}_results_v0.4.json'), expected_stage=stage), "
                "verify_ledger_bindings(value, stage=stage, root=root)) "
                "for stage in ('development','confirmation')]"
            ),
        ],
    )
    for command in commands:
        completed = subprocess.run(command, cwd=worktree, check=False)
        if completed.returncode:
            return completed.returncode
    print(
        "PASS archived quantum-Dirac v0.4: seal, manifests, ledgers, bindings, and tests verified"
    )
    return 0


def main() -> int:
    try:
        _verify_checkpoint()
    except RuntimeError as error:
        print(f"FAIL archived quantum-Dirac validation: {error}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="iota-quantum-dirac-") as temporary:
        worktree = Path(temporary) / "checkpoint"
        added = _git(
            "worktree",
            "add",
            "--detach",
            str(worktree),
            ARCHIVAL_COMMIT,
            check=False,
        )
        if added.returncode:
            print(added.stderr, end="", file=sys.stderr)
            return 2

        status = 2
        try:
            status = _run_checkpoint_checks(worktree)
        finally:
            removed = _git("worktree", "remove", str(worktree), check=False)
            if removed.returncode:
                print(removed.stderr, end="", file=sys.stderr)
                if status == 0:
                    status = 2
        return status


if __name__ == "__main__":
    raise SystemExit(main())
