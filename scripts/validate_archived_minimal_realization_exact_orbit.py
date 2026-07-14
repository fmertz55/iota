#!/usr/bin/env python3

"""Run the exact-orbit validator from its immutable completed checkpoint."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVAL_TAG = "mir-exact-orbit-001-v0.1-complete"
ARCHIVAL_COMMIT = "43c0013a0de9b3e157b4c8e710e56b3d0f356126"
VALIDATOR = Path("scripts/validate_minimal_realization_exact_orbit.py")


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


def main() -> int:
    try:
        _verify_checkpoint()
    except RuntimeError as error:
        print(f"FAIL archived MIR exact-orbit validation: {error}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="iota-mir-exact-orbit-") as temporary:
        worktree = Path(temporary) / "checkpoint"
        added = _git(
            "worktree",
            "add",
            "--detach",
            str(worktree),
            ARCHIVAL_COMMIT,
            check=False,
        )
        if added.returncode != 0:
            print(added.stderr, end="", file=sys.stderr)
            return 2

        validation_status = 2
        try:
            completed = subprocess.run(
                [sys.executable, str(worktree / VALIDATOR)],
                cwd=worktree,
                check=False,
            )
            validation_status = completed.returncode
        finally:
            removed = _git("worktree", "remove", str(worktree), check=False)
            if removed.returncode != 0:
                print(removed.stderr, end="", file=sys.stderr)
                if validation_status == 0:
                    validation_status = 2
        return validation_status


if __name__ == "__main__":
    raise SystemExit(main())
