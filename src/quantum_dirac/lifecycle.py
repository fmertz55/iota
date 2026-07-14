"""Linear freeze, opening, and result provenance for quantum-Dirac stages."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .ledger import validate_result_ledger
from .protocol import (
    CONFIRMATION_OPEN_REF,
    CONFIRMATION_RESULT_REF,
    DEVELOPMENT_OPEN_REF,
    DEVELOPMENT_RESULT_REF,
    EXPERIMENT_DIR_REF,
    FREEZE_TAG,
    OUTCOME_SEAL_REF,
    PROTOCOL_VERSION,
    SEARCH_ID,
    SPEC_DIR_REF,
)
from .seal import load_canonical_json, verify_outcome_seal
from .spec import (
    QuantumDiracSpecError,
    load_json,
    repository_root,
    sha256_file,
    write_canonical_json_once,
)


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise QuantumDiracSpecError(f"git {' '.join(arguments)} failed: {message}")
    return result


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD").stdout.decode("ascii").strip()


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


def require_clean(root: Path) -> None:
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise QuantumDiracSpecError("lifecycle command requires a clean worktree")


def _binding(root: Path, relative: str) -> dict[str, str]:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise QuantumDiracSpecError(f"registered binding path is missing: {relative}")
    return {"path": relative, "sha256": sha256_file(path)}


def _committed(root: Path, relative: str, commit: str = "HEAD") -> None:
    shown = _git(root, "show", f"{commit}:{relative}", check=False)
    path = root / relative
    if shown.returncode or not path.is_file() or shown.stdout != path.read_bytes():
        raise QuantumDiracSpecError(f"registered bytes are uncommitted: {relative}")


def freeze_commit(root: Path | None = None) -> str:
    root = repository_root() if root is None else root.resolve()
    ref = f"refs/tags/{FREEZE_TAG}"
    kind = _git(root, "cat-file", "-t", ref, check=False)
    if kind.returncode or kind.stdout.strip() != b"tag":
        raise QuantumDiracSpecError(f"required annotated freeze tag is missing: {FREEZE_TAG}")
    freeze = _git(root, "rev-parse", f"{ref}^{{commit}}").stdout.decode("ascii").strip()
    if _changes(root, freeze) != [f"A\t{OUTCOME_SEAL_REF}"]:
        raise QuantumDiracSpecError("freeze commit must add only the outcome seal")
    seal = verify_outcome_seal(root)
    if _parent(root, freeze) != seal["freeze_parent_commit"]:
        raise QuantumDiracSpecError("freeze parent differs from the sealed implementation commit")
    _committed(root, OUTCOME_SEAL_REF, freeze)
    return freeze


def _open_ref(stage: str) -> str:
    if stage == "development":
        return DEVELOPMENT_OPEN_REF
    if stage == "confirmation":
        return CONFIRMATION_OPEN_REF
    raise QuantumDiracSpecError("stage must be development or confirmation")


def _result_ref(stage: str) -> str:
    return DEVELOPMENT_RESULT_REF if stage == "development" else CONFIRMATION_RESULT_REF


def expected_open_manifest(root: Path, *, stage: str, freeze: str) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "stage": stage,
        "status": "outcomes_opened",
        "freeze_tag": FREEZE_TAG,
        "freeze_commit": freeze,
        "outcome_seal": _binding(root, OUTCOME_SEAL_REF),
        "run_command_enabled": True,
        "result_path": _result_ref(stage),
    }


def _require_development_result_parent(root: Path, freeze: str) -> str:
    development_result = _head(root)
    development_open = _parent(root, development_result)
    if _parent(root, development_open) != freeze:
        raise QuantumDiracSpecError("development result lineage is not rooted at freeze")
    if _changes(root, development_open) != [f"A\t{DEVELOPMENT_OPEN_REF}"]:
        raise QuantumDiracSpecError("development opening commit shape mismatch")
    if _changes(root, development_result) != [f"A\t{DEVELOPMENT_RESULT_REF}"]:
        raise QuantumDiracSpecError("development result commit shape mismatch")
    _committed(root, DEVELOPMENT_RESULT_REF)
    ledger = load_json(root / DEVELOPMENT_RESULT_REF)
    validate_result_ledger(ledger, expected_stage="development")
    if ledger["status"] != "development_passed" or ledger["aggregate"]["stage_pass"] is not True:
        raise QuantumDiracSpecError("confirmation cannot open after a failed development stage")
    return development_result


def write_open_manifest(*, stage: str, root: Path | None = None) -> Path:
    root = repository_root() if root is None else root.resolve()
    require_clean(root)
    freeze = freeze_commit(root)
    head = _head(root)
    if stage == "development":
        if head != freeze:
            raise QuantumDiracSpecError("development may open only at the tagged freeze commit")
    elif stage == "confirmation":
        _require_development_result_parent(root, freeze)
    else:
        raise QuantumDiracSpecError("stage must be development or confirmation")
    for relative in (_open_ref(stage), _result_ref(stage)):
        if (root / relative).exists():
            raise QuantumDiracSpecError(f"registered stage artifact already exists: {relative}")
    path = root / _open_ref(stage)
    write_canonical_json_once(
        path,
        expected_open_manifest(root, stage=stage, freeze=freeze),
    )
    return path


def verify_open_manifest(
    *, stage: str, root: Path | None = None, require_head: bool = True
) -> dict[str, Any]:
    root = repository_root() if root is None else root.resolve()
    freeze = freeze_commit(root)
    relative = _open_ref(stage)
    value = load_canonical_json(root / relative)
    if value != expected_open_manifest(root, stage=stage, freeze=freeze):
        raise QuantumDiracSpecError("stage opening differs from frozen provenance")
    if require_head:
        opening = _head(root)
        if _changes(root, opening) != [f"A\t{relative}"]:
            raise QuantumDiracSpecError("stage opening commit must add only its manifest")
        if stage == "development":
            if _parent(root, opening) != freeze:
                raise QuantumDiracSpecError("development opening is not a direct child of freeze")
        else:
            development_result = _parent(root, opening)
            development_open = _parent(root, development_result)
            if _parent(root, development_open) != freeze:
                raise QuantumDiracSpecError("confirmation opening lineage is invalid")
    _committed(root, relative)
    return value


def result_bindings(
    *, stage: str, root: Path | None = None, require_open_at_head: bool = True
) -> dict[str, dict[str, str]]:
    root = repository_root() if root is None else root.resolve()
    verify_open_manifest(stage=stage, root=root, require_head=require_open_at_head)
    paths = {
        "open_manifest": _open_ref(stage),
        "outcome_seal": OUTCOME_SEAL_REF,
        "result_schema": f"{SPEC_DIR_REF}/result.schema.json",
        "candidate_manifest": f"{EXPERIMENT_DIR_REF}/candidate_manifest.json",
        "scenario_manifest": f"{EXPERIMENT_DIR_REF}/scenario_manifest.json",
        "state_manifest": f"{EXPERIMENT_DIR_REF}/state_manifest.json",
        "partition_manifest": f"{EXPERIMENT_DIR_REF}/partition_manifest.json",
    }
    return {label: _binding(root, relative) for label, relative in paths.items()}


def verify_ledger_bindings(
    ledger: dict[str, Any], *, stage: str, root: Path | None = None
) -> None:
    root = repository_root() if root is None else root.resolve()
    expected = result_bindings(stage=stage, root=root, require_open_at_head=False)
    if ledger.get("bindings") != expected:
        raise QuantumDiracSpecError("result ledger bindings differ from registered bytes")
