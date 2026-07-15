"""Content seal builder for the not-yet-frozen direct-QCA experiment."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .manifest import validate_committed_manifests
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
    EXPERIMENT_DIR_REF,
    FREEZE_TAG,
    INDEPENDENT_DPS,
    INDEPENDENT_LIBRARY_VERSION,
    MANIFEST_FILENAMES,
    OUTCOME_SEAL_REF,
    PRECISION_BITS,
    PRIMARY_LIBRARY_VERSION,
    PROTOCOL_VERSION,
    REGISTERED_SIZES,
    SEARCH_ID,
    SPEC_DIR_REF,
)
from .spec import (
    SymmetryQCASpecError,
    audit_design,
    canonical_json,
    repository_root,
    sha256_file,
)


class SymmetryQCASealError(ValueError):
    pass


COMMAND_FILES = (
    "Makefile",
    "requirements.txt",
    ".github/workflows/research-compendium.yml",
)


def _discover(root: Path, directory: str) -> tuple[str, ...]:
    base = root / directory
    if not base.is_dir() or base.is_symlink():
        raise SymmetryQCASealError(f"seal directory is missing: {directory}")
    return tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in base.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and "__pycache__" not in path.parts
            and not path.name.startswith(".")
        )
    )


def _hash_map(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    return {path: sha256_file(root / path) for path in paths}


def _head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode:
        raise SymmetryQCASealError("cannot resolve seal parent commit")
    return result.stdout.strip()


def _manifest_hashes(root: Path) -> dict[str, str]:
    base = root / EXPERIMENT_DIR_REF
    return {
        (base / filename).relative_to(root).as_posix(): sha256_file(base / filename)
        for filename in MANIFEST_FILENAMES
    }


def _payload(root: Path, *, freeze_parent_commit: str) -> dict[str, Any]:
    source_files = _discover(root, "src/quantum_dirac_symmetry_qca")
    test_files = _discover(root, "tests/quantum_dirac_symmetry_qca")
    spec_files = _discover(root, SPEC_DIR_REF)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "freeze_parent_commit": freeze_parent_commit,
        "contract": {"path": CONTRACT_REF, "sha256": sha256_file(root / CONTRACT_REF)},
        "source_files": _hash_map(root, source_files),
        "test_files": _hash_map(root, test_files),
        "spec_files": _hash_map(root, spec_files),
        "manifest_files": _manifest_hashes(root),
        "command_files": _hash_map(root, COMMAND_FILES),
        "registered_sizes": list(REGISTERED_SIZES),
        "development_scenarios": list(DEVELOPMENT_SCENARIOS),
        "confirmation_scenarios": list(CONFIRMATION_SCENARIOS),
        "development_states": list(DEVELOPMENT_STATES),
        "confirmation_states": list(CONFIRMATION_STATES),
        "primary_backend": "python-flint Arb/Acb",
        "primary_library_version": PRIMARY_LIBRARY_VERSION,
        "primary_precision_bits": PRECISION_BITS,
        "independent_backend": "mpmath",
        "independent_library_version": INDEPENDENT_LIBRARY_VERSION,
        "independent_decimal_digits": INDEPENDENT_DPS,
        "required_freeze_tag": FREEZE_TAG,
        "seal_ready": False,
        "run_command_enabled": False,
        "registered_outcomes_forbidden_until_stage_open": True,
        "missing_prerequisites": [
            "registered stage runner",
            "canonical result-ledger builder validator and atomic writer",
            "full-ledger independent verifier",
            "hostile review of the complete outcome-free execution path",
        ],
        "development_result_path": DEVELOPMENT_RESULT_REF,
        "confirmation_result_path": CONFIRMATION_RESULT_REF,
    }


def build_disabled_seal(root: Path | None = None) -> dict[str, Any]:
    root = repository_root() if root is None else root.resolve()
    audit_design(root)
    validate_committed_manifests(root)
    for relative in (
        OUTCOME_SEAL_REF,
        DEVELOPMENT_OPEN_REF,
        CONFIRMATION_OPEN_REF,
        DEVELOPMENT_RESULT_REF,
        CONFIRMATION_RESULT_REF,
    ):
        if (root / relative).exists():
            raise SymmetryQCASealError(f"lifecycle artifact already exists: {relative}")
    return _payload(root, freeze_parent_commit=_head(root))


def preview_disabled_seal(root: Path | None = None) -> dict[str, Any]:
    """Return freeze payload bytes without creating or authorizing a run."""

    return build_disabled_seal(root)


def write_disabled_seal(root: Path | None = None) -> Path:
    raise SymmetryQCASealError(
        "outcome seal is disabled until the registered runner, canonical ledger "
        "pipeline, full-ledger independent verifier, and hostile review are complete"
    )


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SymmetryQCASealError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load_canonical(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="ascii")
        value = json.loads(text, object_pairs_hook=_strict_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SymmetryQCASealError(f"{path}: {exc}") from exc
    if type(value) is not dict or text != canonical_json(value) + "\n":
        raise SymmetryQCASealError("outcome seal is not canonical JSON plus LF")
    return value


def verify_outcome_seal(root: Path | None = None) -> dict[str, Any]:
    root = repository_root() if root is None else root.resolve()
    path = root / OUTCOME_SEAL_REF
    if not path.is_file() or path.is_symlink():
        raise SymmetryQCASealError("registered outcome seal is missing")
    existing = _load_canonical(path)
    audit_design(root, allow_lifecycle_artifacts=True)
    validate_committed_manifests(root)
    expected = _payload(
        root, freeze_parent_commit=existing.get("freeze_parent_commit", "")
    )
    if existing != expected:
        raise SymmetryQCASealError("outcome seal differs from the sealed bytes")
    return existing
