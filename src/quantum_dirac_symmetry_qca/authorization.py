"""Git-bound authorization for the direct-QCA registered lifecycle.

The module exposes opaque permits, not a boolean feature flag.  In the current
outcome-free checkout no permit can be issued: the annotated freeze tag,
seal-only freeze commit, and sole-file stage opening do not exist.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .protocol import (
    CONFIRMATION_OPEN_REF,
    CONFIRMATION_RESULT_REF,
    CONFIRMATION_SCENARIOS,
    CONFIRMATION_STATES,
    DEVELOPMENT_OPEN_REF,
    DEVELOPMENT_RESULT_REF,
    DEVELOPMENT_SCENARIOS,
    DEVELOPMENT_STATES,
    FREEZE_TAG,
    OUTCOME_SEAL_REF,
)
from .spec import SymmetryQCASpecError, load_json, repository_root, sha256_file


_EVALUATION_NONCE = object()
_VERIFICATION_NONCE = object()


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
        raise SymmetryQCASpecError(
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
        raise SymmetryQCASpecError("registered evaluation requires a clean worktree")


def _require_committed_bytes(root: Path, relative: str, commit: str = "HEAD") -> None:
    shown = _git(root, "show", f"{commit}:{relative}", check=False)
    path = root / relative
    if shown.returncode or not path.is_file() or path.is_symlink() or path.read_bytes() != shown.stdout:
        raise SymmetryQCASpecError(
            f"registered bytes are absent or uncommitted at {commit}: {relative}"
        )


def _require_freeze(root: Path) -> str:
    ref = f"refs/tags/{FREEZE_TAG}"
    kind = _git(root, "cat-file", "-t", ref, check=False)
    if kind.returncode or kind.stdout.strip() != b"tag":
        raise SymmetryQCASpecError(f"annotated freeze tag is missing: {FREEZE_TAG}")
    freeze = _git(root, "rev-parse", f"{ref}^{{commit}}").stdout.decode("ascii").strip()
    if _changes(root, freeze) != [f"A\t{OUTCOME_SEAL_REF}"]:
        raise SymmetryQCASpecError("freeze commit must add only the outcome seal")
    _require_committed_bytes(root, OUTCOME_SEAL_REF, freeze)
    seal = load_json(root / OUTCOME_SEAL_REF)
    if seal.get("run_command_enabled") is not False:
        raise SymmetryQCASpecError("freeze seal does not disable registered execution")
    if seal.get("required_freeze_tag") != FREEZE_TAG:
        raise SymmetryQCASpecError("freeze seal names a different annotated tag")
    return freeze


def _stage_refs(stage: str) -> tuple[str, str, tuple[str, ...], tuple[str, ...]]:
    if stage == "development":
        return (
            DEVELOPMENT_OPEN_REF,
            DEVELOPMENT_RESULT_REF,
            DEVELOPMENT_SCENARIOS,
            DEVELOPMENT_STATES,
        )
    if stage == "confirmation":
        return (
            CONFIRMATION_OPEN_REF,
            CONFIRMATION_RESULT_REF,
            CONFIRMATION_SCENARIOS,
            CONFIRMATION_STATES,
        )
    raise SymmetryQCASpecError("stage must be development or confirmation")


def _require_open_value(
    root: Path,
    relative: str,
    stage: str,
    freeze: str,
    opening_commit: str,
) -> None:
    _require_committed_bytes(root, relative)
    value = load_json(root / relative)
    expected_keys = {
        "protocol_version",
        "search_id",
        "stage",
        "status",
        "freeze_tag",
        "freeze_commit",
        "stage_parent_commit",
        "outcome_seal",
        "sealed_bindings",
        "scenario_ids",
        "state_ids",
        "run_command_enabled",
        "result_path",
    }
    if type(value) is not dict or set(value) != expected_keys:
        raise SymmetryQCASpecError("stage opening has missing or unexpected fields")
    _, result_ref, scenarios, states = _stage_refs(stage)
    if value["stage"] != stage or value["status"] != "outcomes_opened":
        raise SymmetryQCASpecError("stage opening identity mismatch")
    if value["freeze_tag"] != FREEZE_TAG or value["freeze_commit"] != freeze:
        raise SymmetryQCASpecError("stage opening freeze binding mismatch")
    if value["stage_parent_commit"] != _parent(root, opening_commit):
        raise SymmetryQCASpecError("stage opening parent binding mismatch")
    if value["scenario_ids"] != list(scenarios) or value["state_ids"] != list(states):
        raise SymmetryQCASpecError("stage opening partition mismatch")
    if value["run_command_enabled"] is not True or value["result_path"] != result_ref:
        raise SymmetryQCASpecError("stage opening does not enable exactly its result path")
    if value["outcome_seal"] != {
        "path": OUTCOME_SEAL_REF,
        "sha256": sha256_file(root / OUTCOME_SEAL_REF),
    }:
        raise SymmetryQCASpecError("stage opening outcome-seal binding mismatch")
    from .lifecycle import sealed_bindings

    if value["sealed_bindings"] != sealed_bindings(root):
        raise SymmetryQCASpecError("stage opening sealed bindings mismatch")


@dataclass(frozen=True)
class RegisteredEvaluationPermit:
    stage: str
    root: Path
    freeze_commit: str
    opening_commit: str
    opening_sha256: str
    _nonce: object


@dataclass(frozen=True)
class RegisteredVerificationPermit:
    stage: str
    root: Path
    freeze_commit: str
    opening_commit: str
    result_commit: str
    opening_sha256: str
    result_sha256: str
    _nonce: object


def issue_registered_permit(
    *, stage: str, root: Path | None = None
) -> RegisteredEvaluationPermit:
    root = repository_root() if root is None else root.resolve()
    _require_clean(root)
    freeze = _require_freeze(root)
    head = _head(root)
    open_ref, _, _, _ = _stage_refs(stage)
    if stage == "development":
        if _parent(root, head) != freeze or _changes(root, head) != [f"A\t{open_ref}"]:
            raise SymmetryQCASpecError(
                "development opening must be the sole-file direct child of freeze"
            )
    else:
        development_result = _parent(root, head)
        development_open = _parent(root, development_result)
        if _parent(root, development_open) != freeze:
            raise SymmetryQCASpecError("confirmation ancestry is not rooted at freeze")
        if _changes(root, head) != [f"A\t{open_ref}"]:
            raise SymmetryQCASpecError("confirmation opening commit shape mismatch")
        if _changes(root, development_result) != [f"A\t{DEVELOPMENT_RESULT_REF}"]:
            raise SymmetryQCASpecError("confirmation parent is not the development result")
        if _changes(root, development_open) != [f"A\t{DEVELOPMENT_OPEN_REF}"]:
            raise SymmetryQCASpecError("confirmation ancestry lacks development opening")
        _require_committed_bytes(root, DEVELOPMENT_RESULT_REF, development_result)
        development = load_json(root / DEVELOPMENT_RESULT_REF)
        if (
            development.get("stage") != "development"
            or development.get("status") != "development_passed"
            or development.get("aggregate", {}).get("stage_pass") is not True
        ):
            raise SymmetryQCASpecError(
                "confirmation cannot open without a complete development pass"
            )
    _require_open_value(root, open_ref, stage, freeze, head)
    return RegisteredEvaluationPermit(
        stage=stage,
        root=root,
        freeze_commit=freeze,
        opening_commit=head,
        opening_sha256=sha256_file(root / open_ref),
        _nonce=_EVALUATION_NONCE,
    )


def validate_registered_permit(permit: RegisteredEvaluationPermit) -> None:
    if not isinstance(permit, RegisteredEvaluationPermit) or permit._nonce is not _EVALUATION_NONCE:
        raise SymmetryQCASpecError("registered evaluation permit is invalid")
    _require_clean(permit.root)
    if _head(permit.root) != permit.opening_commit:
        raise SymmetryQCASpecError("registered evaluation moved away from its opening commit")
    open_ref, _, _, _ = _stage_refs(permit.stage)
    if sha256_file(permit.root / open_ref) != permit.opening_sha256:
        raise SymmetryQCASpecError("stage opening bytes changed after permit issuance")


def issue_verification_permit(
    *, stage: str, root: Path | None = None
) -> RegisteredVerificationPermit:
    root = repository_root() if root is None else root.resolve()
    _require_clean(root)
    freeze = _require_freeze(root)
    result_commit = _head(root)
    opening_commit = _parent(root, result_commit)
    open_ref, result_ref, _, _ = _stage_refs(stage)
    if _changes(root, opening_commit) != [f"A\t{open_ref}"]:
        raise SymmetryQCASpecError("result parent is not the sole-file stage opening")
    if _changes(root, result_commit) != [f"A\t{result_ref}"]:
        raise SymmetryQCASpecError("result commit must add only the registered result")
    if stage == "development":
        if _parent(root, opening_commit) != freeze:
            raise SymmetryQCASpecError("development result lineage is not rooted at freeze")
    else:
        development_result = _parent(root, opening_commit)
        development_open = _parent(root, development_result)
        if _parent(root, development_open) != freeze:
            raise SymmetryQCASpecError("confirmation result lineage is not rooted at freeze")
        if _changes(root, development_result) != [f"A\t{DEVELOPMENT_RESULT_REF}"]:
            raise SymmetryQCASpecError("confirmation lineage lacks development result")
    _require_open_value(root, open_ref, stage, freeze, opening_commit)
    _require_committed_bytes(root, result_ref, result_commit)
    return RegisteredVerificationPermit(
        stage=stage,
        root=root,
        freeze_commit=freeze,
        opening_commit=opening_commit,
        result_commit=result_commit,
        opening_sha256=sha256_file(root / open_ref),
        result_sha256=sha256_file(root / result_ref),
        _nonce=_VERIFICATION_NONCE,
    )


def validate_verification_permit(permit: RegisteredVerificationPermit) -> None:
    if not isinstance(permit, RegisteredVerificationPermit) or permit._nonce is not _VERIFICATION_NONCE:
        raise SymmetryQCASpecError("registered verification permit is invalid")
    _require_clean(permit.root)
    if _head(permit.root) != permit.result_commit:
        raise SymmetryQCASpecError("verification moved away from its result checkpoint")
    open_ref, result_ref, _, _ = _stage_refs(permit.stage)
    if sha256_file(permit.root / open_ref) != permit.opening_sha256:
        raise SymmetryQCASpecError("stage opening changed after result commit")
    if sha256_file(permit.root / result_ref) != permit.result_sha256:
        raise SymmetryQCASpecError("registered result changed after its commit")


def validate_registered_access(
    permit: RegisteredEvaluationPermit | RegisteredVerificationPermit,
) -> None:
    if isinstance(permit, RegisteredEvaluationPermit):
        validate_registered_permit(permit)
    elif isinstance(permit, RegisteredVerificationPermit):
        validate_verification_permit(permit)
    else:
        raise SymmetryQCASpecError("registered access permit is invalid")


def authorization_status(root: Path | None = None) -> dict[str, object]:
    """Report the outcome-free state without attempting to issue a permit."""

    root = repository_root() if root is None else root.resolve()
    tag = _git(root, "cat-file", "-t", f"refs/tags/{FREEZE_TAG}", check=False)
    return {
        "registered_outcomes_authorized": False,
        "annotated_freeze_tag_present": tag.returncode == 0 and tag.stdout.strip() == b"tag",
        "evaluation_permit_issued": False,
        "verification_permit_issued": False,
    }
