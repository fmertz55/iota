"""Linear Git provenance gate for future registered evaluation.

No permit can be issued in the current draft because the required annotated
freeze tag, committed disabled seal, and stage-opening commit do not exist.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .protocol import (
    CONFIRMATION_OPEN_REF,
    CONFIRMATION_RESULT_REF,
    DEVELOPMENT_OPEN_REF,
    DEVELOPMENT_RESULT_REF,
    FREEZE_TAG,
    OUTCOME_SEAL_REF,
)
from .spec import QuantumDiracSpecError, load_json, repository_root, sha256_file


_PERMIT_NONCE = object()


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise QuantumDiracSpecError(
            f"git {' '.join(arguments)} failed: {detail or 'unknown error'}"
        )
    return result


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "--verify", "HEAD").stdout.decode("ascii").strip()


def _parent(root: Path, commit: str) -> str:
    return _git(root, "rev-parse", f"{commit}^").stdout.decode("ascii").strip()


def _changes(root: Path, commit: str) -> list[str]:
    return _git(
        root,
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "--no-renames",
        "-r",
        commit,
    ).stdout.decode("utf-8").splitlines()


def _require_clean(root: Path) -> None:
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise QuantumDiracSpecError("registered evaluation requires a clean worktree")


def _require_annotated_freeze(root: Path) -> str:
    ref = f"refs/tags/{FREEZE_TAG}"
    kind = _git(root, "cat-file", "-t", ref, check=False)
    if kind.returncode or kind.stdout.strip() != b"tag":
        raise QuantumDiracSpecError(f"annotated freeze tag is missing: {FREEZE_TAG}")
    return _git(root, "rev-parse", f"{ref}^{{commit}}").stdout.decode("ascii").strip()


def _require_committed_bytes(root: Path, relative: str, commit: str = "HEAD") -> None:
    path = root / relative
    shown = _git(root, "show", f"{commit}:{relative}", check=False)
    if shown.returncode or not path.is_file() or path.read_bytes() != shown.stdout:
        raise QuantumDiracSpecError(
            f"registered bytes are absent or uncommitted at {commit}: {relative}"
        )


def _require_freeze(root: Path) -> str:
    freeze = _require_annotated_freeze(root)
    if _changes(root, freeze).count(f"A\t{OUTCOME_SEAL_REF}") != 1:
        raise QuantumDiracSpecError("freeze commit did not introduce exactly one outcome seal")
    _require_committed_bytes(root, OUTCOME_SEAL_REF, freeze)
    seal = load_json(root / OUTCOME_SEAL_REF)
    if seal.get("run_command_enabled") is not False:
        raise QuantumDiracSpecError("freeze seal does not disable registered execution")
    if seal.get("required_freeze_tag") != FREEZE_TAG:
        raise QuantumDiracSpecError("freeze seal names a different tag")
    return freeze


def _require_open_value(root: Path, relative: str, stage: str, freeze: str) -> None:
    _require_committed_bytes(root, relative)
    value = load_json(root / relative)
    expected = {
        "protocol_version",
        "search_id",
        "stage",
        "status",
        "freeze_tag",
        "freeze_commit",
        "outcome_seal",
        "run_command_enabled",
        "result_path",
    }
    if set(value) != expected:
        raise QuantumDiracSpecError("stage opening has missing or unexpected fields")
    if value["stage"] != stage or value["status"] != "outcomes_opened":
        raise QuantumDiracSpecError("stage opening identity mismatch")
    if value["freeze_tag"] != FREEZE_TAG or value["freeze_commit"] != freeze:
        raise QuantumDiracSpecError("stage opening freeze binding mismatch")
    if value["run_command_enabled"] is not True:
        raise QuantumDiracSpecError("stage opening does not enable its registered run")
    binding = value["outcome_seal"]
    if binding != {
        "path": OUTCOME_SEAL_REF,
        "sha256": sha256_file(root / OUTCOME_SEAL_REF),
    }:
        raise QuantumDiracSpecError("stage opening outcome-seal binding mismatch")


@dataclass(frozen=True)
class RegisteredEvaluationPermit:
    stage: str
    root: Path
    freeze_commit: str
    opening_commit: str
    opening_sha256: str
    _nonce: object


def issue_registered_permit(
    *,
    stage: str,
    root: Path | None = None,
) -> RegisteredEvaluationPermit:
    root = repository_root() if root is None else root.resolve()
    _require_clean(root)
    freeze = _require_freeze(root)
    head = _head(root)
    if stage == "development":
        open_ref = DEVELOPMENT_OPEN_REF
        if _parent(root, head) != freeze or _changes(root, head) != [f"A\t{open_ref}"]:
            raise QuantumDiracSpecError(
                "development opening must be the sole-file direct child of freeze"
            )
    elif stage == "confirmation":
        open_ref = CONFIRMATION_OPEN_REF
        parent = _parent(root, head)
        grandparent = _parent(root, parent)
        great_grandparent = _parent(root, grandparent)
        if _changes(root, head) != [f"A\t{open_ref}"]:
            raise QuantumDiracSpecError("confirmation opening commit shape mismatch")
        if _changes(root, parent) != [f"A\t{DEVELOPMENT_RESULT_REF}"]:
            raise QuantumDiracSpecError("confirmation parent is not the development result")
        if _changes(root, grandparent) != [f"A\t{DEVELOPMENT_OPEN_REF}"]:
            raise QuantumDiracSpecError("confirmation ancestry lacks development opening")
        if great_grandparent != freeze:
            raise QuantumDiracSpecError("confirmation ancestry is not rooted at freeze")
    else:
        raise QuantumDiracSpecError("stage must be development or confirmation")
    _require_open_value(root, open_ref, stage, freeze)
    return RegisteredEvaluationPermit(
        stage=stage,
        root=root,
        freeze_commit=freeze,
        opening_commit=head,
        opening_sha256=sha256_file(root / open_ref),
        _nonce=_PERMIT_NONCE,
    )


def validate_registered_permit(permit: RegisteredEvaluationPermit) -> None:
    if (
        not isinstance(permit, RegisteredEvaluationPermit)
        or permit._nonce is not _PERMIT_NONCE
    ):
        raise QuantumDiracSpecError("registered evaluation permit is invalid")
    _require_clean(permit.root)
    if _head(permit.root) != permit.opening_commit:
        raise QuantumDiracSpecError("registered evaluation moved away from its opening commit")
    open_ref = (
        DEVELOPMENT_OPEN_REF
        if permit.stage == "development"
        else CONFIRMATION_OPEN_REF
    )
    if sha256_file(permit.root / open_ref) != permit.opening_sha256:
        raise QuantumDiracSpecError("stage opening bytes changed after permit issuance")
