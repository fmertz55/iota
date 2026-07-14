"""Content seal for the exact closure protocol.

This module hashes preregistered artifacts and the already committed parent
ledger.  It never invokes the symbolic analyzer or trajectory evaluator.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.minimal_realization_role_succession.manifest import canonical_json, sha256_file

from .manifest import (
    load_and_validate_parent,
    read_jsonl,
    validate_continuation_manifest,
)
from .protocol import (
    CANDIDATE_MANIFEST_REF,
    CONTRACT_REF,
    DATA_CLASS,
    FREEZE_TAG,
    OPEN_MANIFEST_REF,
    OUTCOME_SEAL_REF,
    PARENT_RESOURCE_CENSORED_COUNT,
    PARENT_RESULT_REF,
    PARENT_RESULT_SHA256,
    PROTOCOL_VERSION,
    REGISTERED_WORKER_PROCESSES,
    RESULT_PATH_REF,
    SEARCH_ID,
    SOURCE_DIR_REF,
    SPEC_DIR_REF,
    TEST_DIR_REF,
    opening_condition,
)


class ExactSealError(ValueError):
    pass


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_path(root: Path, relative: str) -> Path:
    base = root.resolve()
    path = (base / relative).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ExactSealError(f"registered path escapes repository: {relative}") from exc
    cursor = base
    for part in Path(relative).parts:
        cursor /= part
        if cursor.is_symlink():
            raise ExactSealError(f"symlink is forbidden in registered path: {relative}")
    return path


def _binding(root: Path, relative: str) -> dict[str, str]:
    path = _repo_path(root, relative)
    if not path.is_file():
        raise ExactSealError(f"registered file is missing: {relative}")
    return {"path": relative, "sha256": sha256_file(path)}


def _discover(root: Path, directory_ref: str) -> tuple[str, ...]:
    directory = _repo_path(root, directory_ref)
    if not directory.is_dir():
        raise ExactSealError(f"registered directory is missing: {directory_ref}")
    files = tuple(
        sorted(
            path.resolve().relative_to(root.resolve()).as_posix()
            for path in directory.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and not path.name.startswith(".")
        )
    )
    if not files:
        raise ExactSealError(f"registered directory is empty: {directory_ref}")
    return files


def _hash_map(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    return {relative: sha256_file(_repo_path(root, relative)) for relative in paths}


def build_outcome_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    for forbidden in (OUTCOME_SEAL_REF, OPEN_MANIFEST_REF, RESULT_PATH_REF):
        if _repo_path(root, forbidden).exists():
            raise ExactSealError(f"registered artifact already exists: {forbidden}")
    parent = load_and_validate_parent(root)
    candidates = read_jsonl(_repo_path(root, CANDIDATE_MANIFEST_REF))
    validate_continuation_manifest(candidates, parent)
    parent_binding = _binding(root, PARENT_RESULT_REF)
    if parent_binding["sha256"] != PARENT_RESULT_SHA256:
        raise ExactSealError("parent result provenance mismatch")
    groups = {
        "source_files": _discover(root, SOURCE_DIR_REF),
        "test_files": _discover(root, TEST_DIR_REF),
        "spec_files": _discover(root, SPEC_DIR_REF),
    }
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "data_class": DATA_CLASS,
        "parent_result": parent_binding,
        "candidate_manifest": _binding(root, CANDIDATE_MANIFEST_REF),
        "contract": _binding(root, CONTRACT_REF),
        "source_files": _hash_map(root, groups["source_files"]),
        "test_files": _hash_map(root, groups["test_files"]),
        "spec_files": _hash_map(root, groups["spec_files"]),
        "continuation_candidate_count": PARENT_RESOURCE_CENSORED_COUNT,
        "symbolic_analysis_first": True,
        "dynamic_layer_ceiling": None,
        "registered_worker_processes": REGISTERED_WORKER_PROCESSES,
        "required_freeze_tag": FREEZE_TAG,
        "run_command_enabled": False,
        "result_path": RESULT_PATH_REF,
        "opening_condition": opening_condition(),
    }


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ExactSealError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ExactSealError(f"non-finite number {value!r} is forbidden")


def load_canonical_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="ascii")
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExactSealError(f"{path}: {exc}") from exc
    if type(value) is not dict or text != canonical_json(value) + "\n":
        raise ExactSealError(f"{path}: file is not canonical JSON plus LF")
    return value


def verify_outcome_seal(path: Path, *, root: Path | None = None) -> dict[str, Any]:
    root = repository_root() if root is None else root.resolve()
    if path.resolve() != _repo_path(root, OUTCOME_SEAL_REF):
        raise ExactSealError("outcome seal is not at its registered path")
    seal = load_canonical_json(path)
    expected = build_expected_seal_from_current_files(root, seal)
    if seal != expected:
        raise ExactSealError("outcome seal differs from current registered bytes")
    return seal


def build_expected_seal_from_current_files(
    root: Path,
    existing_seal: dict[str, Any],
) -> dict[str, Any]:
    """Rebuild expected seal while permitting the seal file itself to exist."""

    parent = load_and_validate_parent(root)
    candidates = read_jsonl(_repo_path(root, CANDIDATE_MANIFEST_REF))
    validate_continuation_manifest(candidates, parent)
    parent_binding = _binding(root, PARENT_RESULT_REF)
    groups = {
        "source_files": _discover(root, SOURCE_DIR_REF),
        "test_files": _discover(root, TEST_DIR_REF),
        "spec_files": _discover(root, SPEC_DIR_REF),
    }
    expected = {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "data_class": DATA_CLASS,
        "parent_result": parent_binding,
        "candidate_manifest": _binding(root, CANDIDATE_MANIFEST_REF),
        "contract": _binding(root, CONTRACT_REF),
        "source_files": _hash_map(root, groups["source_files"]),
        "test_files": _hash_map(root, groups["test_files"]),
        "spec_files": _hash_map(root, groups["spec_files"]),
        "continuation_candidate_count": PARENT_RESOURCE_CENSORED_COUNT,
        "symbolic_analysis_first": True,
        "dynamic_layer_ceiling": None,
        "registered_worker_processes": REGISTERED_WORKER_PROCESSES,
        "required_freeze_tag": FREEZE_TAG,
        "run_command_enabled": False,
        "result_path": RESULT_PATH_REF,
        "opening_condition": opening_condition(),
    }
    if parent_binding["sha256"] != PARENT_RESULT_SHA256:
        raise ExactSealError("parent result provenance mismatch")
    if set(existing_seal) != set(expected):
        raise ExactSealError("outcome seal has missing or unexpected fields")
    return expected


def write_canonical_json_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise ExactSealError(f"refusing to overwrite registered artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise ExactSealError(f"stale temporary file exists: {temporary}")
    data = (canonical_json(value) + "\n").encode("ascii")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        temporary.unlink()
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
