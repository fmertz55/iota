"""Content sealing for the outcome-free role-succession protocol.

The functions here hash and validate preregistered artifacts.  They never
import the production evaluator and never inspect a role-succession result.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .manifest import (
    canonical_json,
    read_jsonl,
    sha256_file,
    validate_candidate_manifest,
)
from .protocol import (
    BASE_CONTRACT_VERSION,
    CANDIDATE_MANIFEST_REF,
    DATA_CLASS,
    DYNAMIC_CANDIDATE_COUNT,
    FREEZE_TAG,
    FORMATION_HORIZON,
    MAX_LAYERS_PER_CANDIDATE,
    OPEN_MANIFEST_REF,
    OUTCOME_SEAL_REF,
    PARENT_EXACT_RESULT_REF,
    PARENT_EXACT_RESULT_SHA256,
    PRIMARY_CYCLE_SIZE,
    PROTOCOL_VERSION,
    REGISTERED_WORKER_PROCESSES,
    RESULT_PATH_REF,
    SEARCH_ID,
)


SPEC_DIR_REF = "specs/icp_minimal_realization_role_succession/v0.1-draft"
CONTRACT_REF = "docs/ICP_MINIMAL_INFORMATIONAL_REALIZATION_ROLE_SUCCESSION_CONTRACT.md"
LITERATURE_REF = (
    "docs/literature/minimal_realization_role_succession_preoutcome_2026-07-13.md"
)
SOURCE_DIR_REF = "src/minimal_realization_role_succession"
TEST_DIR_REF = "tests/minimal_realization_role_succession"

OPENING_CONDITION = (
    f"add the complete outcome-free protocol seal in a commit whose parent lacks it, "
    f"tag that exact seal-introduction commit "
    f"with annotated {FREEZE_TAG}, then add only the open manifest in its "
    "direct child"
)


class SealError(ValueError):
    pass


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


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
        data = path.read_bytes()
    except OSError as exc:
        raise SealError(f"{path}: {exc}") from exc
    try:
        text = data.decode("ascii")
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SealError(f"{path}: {exc}") from exc
    if type(value) is not dict:
        raise SealError(f"{path}: root must be an object")
    if text != canonical_json(value) + "\n":
        raise SealError(f"{path}: file is not canonical JSON plus LF")
    return value


def _repo_path(root: Path, relative: str) -> Path:
    root = root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise SealError(f"registered path escapes repository: {relative}") from exc
    return path


def require_registered_path(root: Path, path: Path, relative: str) -> Path:
    expected = _repo_path(root, relative)
    if path.resolve() != expected:
        raise SealError(f"path must be the registered location {relative}")
    cursor = root.resolve()
    for part in Path(relative).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise SealError(f"symlink is forbidden in registered path {relative}")
    return expected


def _binding(root: Path, relative: str) -> dict[str, str]:
    path = require_registered_path(root, _repo_path(root, relative), relative)
    if not path.is_file():
        raise SealError(f"registered file is missing: {relative}")
    return {"path": relative, "sha256": sha256_file(path)}


def _discover_files(root: Path, directory_ref: str) -> tuple[str, ...]:
    directory = _repo_path(root, directory_ref)
    if not directory.is_dir():
        raise SealError(f"registered directory is missing: {directory_ref}")
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
        raise SealError(f"registered directory is empty: {directory_ref}")
    for relative in files:
        require_registered_path(root, _repo_path(root, relative), relative)
    return files


def _hash_map(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    return {relative: sha256_file(_repo_path(root, relative)) for relative in paths}


def build_outcome_seal(root: Path) -> dict[str, Any]:
    """Build seal data without writing it or evaluating any candidate."""

    root = root.resolve()
    for forbidden in (OUTCOME_SEAL_REF, OPEN_MANIFEST_REF, RESULT_PATH_REF):
        if _repo_path(root, forbidden).exists():
            raise SealError(f"cannot build seal while registered artifact exists: {forbidden}")

    candidates_path = _repo_path(root, CANDIDATE_MANIFEST_REF)
    candidates = read_jsonl(candidates_path)
    validate_candidate_manifest(candidates)

    parent = _binding(root, PARENT_EXACT_RESULT_REF)
    if parent["sha256"] != PARENT_EXACT_RESULT_SHA256:
        raise SealError("parent exact-orbit result hash differs from registered provenance")

    source_files = _discover_files(root, SOURCE_DIR_REF)
    test_files = _discover_files(root, TEST_DIR_REF)
    spec_files = _discover_files(root, SPEC_DIR_REF)
    contract = _binding(root, CONTRACT_REF)
    literature = _binding(root, LITERATURE_REF)

    return {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "data_class": DATA_CLASS,
        "parent_exact_result": parent,
        "candidate_manifest": _binding(root, CANDIDATE_MANIFEST_REF),
        "contract": contract,
        "literature_record": literature,
        "spec_files": _hash_map(root, spec_files),
        "source_files": _hash_map(root, source_files),
        "test_files": _hash_map(root, test_files),
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "pre_wrap_formation_horizon": FORMATION_HORIZON,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "dynamic_candidate_count": DYNAMIC_CANDIDATE_COUNT,
        "registered_worker_processes": REGISTERED_WORKER_PROCESSES,
        "required_freeze_tag": FREEZE_TAG,
        "run_command_enabled": False,
        "result_path": RESULT_PATH_REF,
        "opening_condition": OPENING_CONDITION,
    }


def _require_binding(value: Any, label: str) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"path", "sha256"}:
        raise SealError(f"{label} binding shape mismatch")
    if type(value["path"]) is not str or not value["path"]:
        raise SealError(f"{label} path is invalid")
    digest = value["sha256"]
    if (
        type(digest) is not str
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise SealError(f"{label} digest is invalid")
    return value


def verify_outcome_seal(path: Path, *, root: Path | None = None) -> dict[str, Any]:
    """Verify every current byte against the recorded outcome-free seal."""

    root = repository_root() if root is None else root.resolve()
    path = require_registered_path(root, path, OUTCOME_SEAL_REF)
    seal = load_canonical_json(path)
    expected_keys = {
        "base_contract_version",
        "protocol_version",
        "search_id",
        "status",
        "data_class",
        "parent_exact_result",
        "candidate_manifest",
        "contract",
        "literature_record",
        "spec_files",
        "source_files",
        "test_files",
        "primary_cycle_size",
        "pre_wrap_formation_horizon",
        "max_layers_per_candidate",
        "dynamic_candidate_count",
        "registered_worker_processes",
        "required_freeze_tag",
        "run_command_enabled",
        "result_path",
        "opening_condition",
    }
    if set(seal) != expected_keys:
        raise SealError("outcome seal has missing or unexpected fields")
    fixed = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "data_class": DATA_CLASS,
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "pre_wrap_formation_horizon": FORMATION_HORIZON,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "dynamic_candidate_count": DYNAMIC_CANDIDATE_COUNT,
        "registered_worker_processes": REGISTERED_WORKER_PROCESSES,
        "required_freeze_tag": FREEZE_TAG,
        "run_command_enabled": False,
        "result_path": RESULT_PATH_REF,
        "opening_condition": OPENING_CONDITION,
    }
    for key, expected in fixed.items():
        if seal[key] != expected:
            raise SealError(f"outcome seal {key} mismatch")

    registered = {
        "parent_exact_result": PARENT_EXACT_RESULT_REF,
        "candidate_manifest": CANDIDATE_MANIFEST_REF,
        "contract": CONTRACT_REF,
        "literature_record": LITERATURE_REF,
    }
    for name, relative in registered.items():
        binding = _require_binding(seal[name], name)
        if binding["path"] != relative:
            raise SealError(f"outcome seal {name} path mismatch")
        if _binding(root, relative) != binding:
            raise SealError(f"outcome seal {name} hash mismatch")
    if seal["parent_exact_result"]["sha256"] != PARENT_EXACT_RESULT_SHA256:
        raise SealError("parent exact-orbit result provenance mismatch")

    candidates = read_jsonl(_repo_path(root, CANDIDATE_MANIFEST_REF))
    validate_candidate_manifest(candidates)
    expected_groups = {
        "source_files": _discover_files(root, SOURCE_DIR_REF),
        "test_files": _discover_files(root, TEST_DIR_REF),
        "spec_files": _discover_files(root, SPEC_DIR_REF),
    }
    for name, paths in expected_groups.items():
        hashes = seal[name]
        if type(hashes) is not dict or set(hashes) != set(paths):
            raise SealError(f"outcome seal {name} allocation mismatch")
        if hashes != _hash_map(root, paths):
            raise SealError(f"outcome seal {name} hash mismatch")
    return seal


def write_canonical_json_once(path: Path, value: dict[str, Any]) -> None:
    """Atomically publish canonical JSON without overwrite."""

    if path.exists():
        raise SealError(f"refusing to overwrite registered artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise SealError(f"refusing to overwrite stale temporary file: {temporary}")
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
