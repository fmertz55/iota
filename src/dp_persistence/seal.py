"""Content sealing for the outcome-free ICP-DP-PERSISTENCE-001 protocol.

The functions here hash preregistered artifacts.  They never import a runner
and never inspect a result.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ledger import canonical_json, sha256_file, write_canonical_json_once
from .protocol import (
    ALL_PROTECTED_PATHS,
    CONTRACT_REF,
    DATA_CLASS,
    FREEZE_REVISION,
    FREEZE_TAG,
    OUTCOME_SEAL_REF,
    PROTOCOL_VERSION,
    REGISTERED_PATHS,
    REGISTERED_WORKER_PROCESSES,
    SEARCH_ID,
    SOURCE_DIR_REF,
    SPEC_DIR_REF,
    SUPERSEDED_FREEZE_TAG,
    SUPERSEDED_SEAL_REF,
    SUPERSESSION_REASON,
    TEST_DIR_REF,
    repository_root,
)


OPENING_CONDITION = (
    f"add the complete outcome-free protocol seal in a commit whose parent lacks it, "
    f"tag that exact seal-introduction commit with annotated {FREEZE_TAG}, then add "
    "each stage open manifest alone in its own commit and each result alone in the "
    "direct child of its opening"
)

SUPERSEDES = {
    "freeze_tag": SUPERSEDED_FREEZE_TAG,
    "seal_path": SUPERSEDED_SEAL_REF,
    "reason": SUPERSESSION_REASON,
}

SEAL_KEYS = {
    "protocol_version",
    "freeze_revision",
    "supersedes",
    "search_id",
    "status",
    "data_class",
    "contract",
    "spec_files",
    "source_files",
    "test_files",
    "registered_paths",
    "registered_worker_processes",
    "required_freeze_tag",
    "run_command_enabled",
    "opening_condition",
}


class SealError(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SealError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise SealError(f"non-finite JSON number {value!r} is forbidden")


def load_canonical_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_bytes().decode("ascii")
        value = json.loads(text, object_pairs_hook=_strict_object, parse_constant=_reject_constant)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SealError(f"{path}: {exc}") from exc
    if type(value) is not dict:
        raise SealError(f"{path}: root must be an object")
    if text != canonical_json(value) + "\n":
        raise SealError(f"{path}: file is not canonical JSON plus LF")
    return value


def repo_path(root: Path, relative: str) -> Path:
    root = root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise SealError(f"registered path escapes repository: {relative}") from exc
    cursor = root
    for part in Path(relative).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise SealError(f"symlink is forbidden in registered path {relative}")
    return path


def binding(root: Path, relative: str) -> dict[str, str]:
    path = repo_path(root, relative)
    if not path.is_file():
        raise SealError(f"registered file is missing: {relative}")
    return {"path": relative, "sha256": sha256_file(path)}


def discover_files(root: Path, directory_ref: str) -> tuple[str, ...]:
    directory = repo_path(root, directory_ref)
    if not directory.is_dir():
        raise SealError(f"registered directory is missing: {directory_ref}")
    files = tuple(
        sorted(
            path.resolve().relative_to(root.resolve()).as_posix()
            for path in directory.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and not path.name.startswith(".")
        )
    )
    if not files:
        raise SealError(f"registered directory is empty: {directory_ref}")
    return files


def _hash_map(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    return {relative: sha256_file(repo_path(root, relative)) for relative in paths}


def build_outcome_seal(root: Path) -> dict[str, Any]:
    """Build seal data without writing it or running anything."""

    root = root.resolve()
    for forbidden in ALL_PROTECTED_PATHS:
        if repo_path(root, forbidden).exists():
            raise SealError(f"cannot build seal while registered artifact exists: {forbidden}")
    return {
        "protocol_version": PROTOCOL_VERSION,
        "freeze_revision": FREEZE_REVISION,
        "supersedes": dict(SUPERSEDES),
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "data_class": DATA_CLASS,
        "contract": binding(root, CONTRACT_REF),
        "spec_files": _hash_map(root, discover_files(root, SPEC_DIR_REF)),
        "source_files": _hash_map(root, discover_files(root, SOURCE_DIR_REF)),
        "test_files": _hash_map(root, discover_files(root, TEST_DIR_REF)),
        "registered_paths": dict(REGISTERED_PATHS),
        "registered_worker_processes": REGISTERED_WORKER_PROCESSES,
        "required_freeze_tag": FREEZE_TAG,
        "run_command_enabled": False,
        "opening_condition": OPENING_CONDITION,
    }


def write_outcome_seal(root: Path, path: Path) -> dict[str, Any]:
    seal = build_outcome_seal(root)
    write_canonical_json_once(path, seal)
    return seal


def verify_outcome_seal(path: Path, *, root: Path | None = None) -> dict[str, Any]:
    """Verify every current byte against the recorded outcome-free seal."""

    root = repository_root() if root is None else root.resolve()
    if path.resolve() != repo_path(root, OUTCOME_SEAL_REF):
        raise SealError(f"seal must be at the registered location {OUTCOME_SEAL_REF}")
    seal = load_canonical_json(path)
    if set(seal) != SEAL_KEYS:
        raise SealError("outcome seal has missing or unexpected fields")
    fixed = {
        "protocol_version": PROTOCOL_VERSION,
        "freeze_revision": FREEZE_REVISION,
        "supersedes": dict(SUPERSEDES),
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "data_class": DATA_CLASS,
        "registered_paths": dict(REGISTERED_PATHS),
        "registered_worker_processes": REGISTERED_WORKER_PROCESSES,
        "required_freeze_tag": FREEZE_TAG,
        "run_command_enabled": False,
        "opening_condition": OPENING_CONDITION,
    }
    for key, expected in fixed.items():
        if seal[key] != expected:
            raise SealError(f"outcome seal {key} mismatch")
    if seal["contract"] != binding(root, CONTRACT_REF):
        raise SealError("outcome seal contract hash mismatch")
    groups = {
        "spec_files": SPEC_DIR_REF,
        "source_files": SOURCE_DIR_REF,
        "test_files": TEST_DIR_REF,
    }
    for name, directory in groups.items():
        paths = discover_files(root, directory)
        hashes = seal[name]
        if type(hashes) is not dict or set(hashes) != set(paths):
            raise SealError(f"outcome seal {name} allocation mismatch")
        if hashes != _hash_map(root, paths):
            raise SealError(f"outcome seal {name} hash mismatch")
    return seal
