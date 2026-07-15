"""Linear freeze, stage-opening, and binding helpers for direct-QCA runs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .protocol import (
    CONFIRMATION_OPEN_REF,
    CONFIRMATION_RESULT_REF,
    CONFIRMATION_SCENARIOS,
    CONFIRMATION_STATES,
    CONTRACT_REF,
    DEVELOPMENT_OPEN_REF,
    DEVELOPMENT_RESULT_REF,
    DEVELOPMENT_SCENARIOS,
    DEVELOPMENT_STATES,
    FREEZE_TAG,
    OUTCOME_SEAL_REF,
    PROTOCOL_VERSION,
    SEARCH_ID,
    SPEC_DIR_REF,
)
from .spec import (
    SymmetryQCASpecError,
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
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise SymmetryQCASpecError(f"git {' '.join(arguments)} failed: {detail}")
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
        raise SymmetryQCASpecError("lifecycle command requires a clean worktree")


def _binding(root: Path, relative: str) -> dict[str, str]:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise SymmetryQCASpecError(f"binding path is missing: {relative}")
    return {"path": relative, "sha256": sha256_file(path)}


def _committed(root: Path, relative: str, commit: str = "HEAD") -> None:
    shown = _git(root, "show", f"{commit}:{relative}", check=False)
    path = root / relative
    if shown.returncode or not path.is_file() or path.is_symlink() or shown.stdout != path.read_bytes():
        raise SymmetryQCASpecError(f"lifecycle bytes are uncommitted: {relative}")


def freeze_commit(root: Path | None = None) -> str:
    root = repository_root() if root is None else root.resolve()
    ref = f"refs/tags/{FREEZE_TAG}"
    kind = _git(root, "cat-file", "-t", ref, check=False)
    if kind.returncode or kind.stdout.strip() != b"tag":
        raise SymmetryQCASpecError(f"required annotated freeze tag is missing: {FREEZE_TAG}")
    freeze = _git(root, "rev-parse", f"{ref}^{{commit}}").stdout.decode("ascii").strip()
    if _changes(root, freeze) != [f"A\t{OUTCOME_SEAL_REF}"]:
        raise SymmetryQCASpecError("freeze commit must add only the outcome seal")
    from .seal import verify_outcome_seal

    seal = verify_outcome_seal(root)
    if _parent(root, freeze) != seal["freeze_parent_commit"]:
        raise SymmetryQCASpecError("freeze parent differs from the sealed implementation")
    _committed(root, OUTCOME_SEAL_REF, freeze)
    return freeze


def _stage_values(stage: str) -> tuple[str, str, tuple[str, ...], tuple[str, ...]]:
    if stage == "development":
        return DEVELOPMENT_OPEN_REF, DEVELOPMENT_RESULT_REF, DEVELOPMENT_SCENARIOS, DEVELOPMENT_STATES
    if stage == "confirmation":
        return CONFIRMATION_OPEN_REF, CONFIRMATION_RESULT_REF, CONFIRMATION_SCENARIOS, CONFIRMATION_STATES
    raise SymmetryQCASpecError("stage must be development or confirmation")


def sealed_bindings(root: Path) -> dict[str, dict[str, str]]:
    references = {
        "contract": CONTRACT_REF,
        "protocol": f"{SPEC_DIR_REF}/protocol.json",
        "candidate": f"{SPEC_DIR_REF}/candidate.json",
        "target": f"{SPEC_DIR_REF}/target.json",
        "maps": f"{SPEC_DIR_REF}/maps.json",
        "scenarios": f"{SPEC_DIR_REF}/scenarios.json",
        "states": f"{SPEC_DIR_REF}/states.json",
        "partitions": f"{SPEC_DIR_REF}/partitions.json",
        "result_schema": f"{SPEC_DIR_REF}/result.schema.json",
    }
    return {name: _binding(root, relative) for name, relative in references.items()}


def expected_open_manifest(
    root: Path, *, stage: str, freeze: str, stage_parent: str
) -> dict[str, Any]:
    _, result_ref, scenarios, states = _stage_values(stage)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "stage": stage,
        "status": "outcomes_opened",
        "freeze_tag": FREEZE_TAG,
        "freeze_commit": freeze,
        "stage_parent_commit": stage_parent,
        "outcome_seal": _binding(root, OUTCOME_SEAL_REF),
        "sealed_bindings": sealed_bindings(root),
        "scenario_ids": list(scenarios),
        "state_ids": list(states),
        "run_command_enabled": True,
        "result_path": result_ref,
    }


def _require_confirmation_parent(root: Path, freeze: str) -> str:
    development_result = _head(root)
    development_open = _parent(root, development_result)
    if _parent(root, development_open) != freeze:
        raise SymmetryQCASpecError("confirmation parent lineage is not rooted at freeze")
    if _changes(root, development_open) != [f"A\t{DEVELOPMENT_OPEN_REF}"]:
        raise SymmetryQCASpecError("confirmation lineage lacks development opening")
    if _changes(root, development_result) != [f"A\t{DEVELOPMENT_RESULT_REF}"]:
        raise SymmetryQCASpecError("confirmation must directly follow the development result")
    _committed(root, DEVELOPMENT_RESULT_REF, development_result)
    value = load_json(root / DEVELOPMENT_RESULT_REF)
    if (
        value.get("stage") != "development"
        or value.get("status") != "development_passed"
        or value.get("aggregate", {}).get("stage_pass") is not True
    ):
        raise SymmetryQCASpecError("confirmation requires a complete development pass")
    # Confirmation opening itself performs the clean-checkpoint independent
    # replay.  This makes the "verified development pass" prerequisite causal,
    # without inserting an extra commit into the fixed linear history.
    from .authorization import issue_verification_permit
    from .independent_verifier import verify_ledger_independently
    from .ledger import validate_result_ledger

    permit = issue_verification_permit(stage="development", root=root)
    validate_result_ledger(value, expected_stage="development")
    verify_ledger_bindings(value, stage="development", root=root)
    verify_ledger_independently(permit, value)
    return development_result


def write_open_manifest(*, stage: str, root: Path | None = None) -> Path:
    root = repository_root() if root is None else root.resolve()
    require_clean(root)
    freeze = freeze_commit(root)
    open_ref, _, _, _ = _stage_values(stage)
    if stage == "development":
        stage_parent = _head(root)
        if stage_parent != freeze:
            raise SymmetryQCASpecError("development must open directly from the freeze commit")
    else:
        stage_parent = _require_confirmation_parent(root, freeze)
    path = root / open_ref
    write_canonical_json_once(
        path,
        expected_open_manifest(
            root, stage=stage, freeze=freeze, stage_parent=stage_parent
        ),
    )
    return path


def result_bindings(*, stage: str, root: Path | None = None) -> dict[str, dict[str, str]]:
    root = repository_root() if root is None else root.resolve()
    open_ref, _, _, _ = _stage_values(stage)
    return {
        "open_manifest": _binding(root, open_ref),
        "outcome_seal": _binding(root, OUTCOME_SEAL_REF),
        "result_schema": _binding(root, f"{SPEC_DIR_REF}/result.schema.json"),
        **sealed_bindings(root),
    }


def verify_ledger_bindings(
    ledger: dict[str, Any], *, stage: str, root: Path | None = None
) -> None:
    root = repository_root() if root is None else root.resolve()
    expected = result_bindings(stage=stage, root=root)
    if ledger.get("bindings") != expected:
        raise SymmetryQCASpecError(
            "result ledger bindings differ from the registered bytes"
        )
