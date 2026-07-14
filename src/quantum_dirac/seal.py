"""Read-only preview of the future disabled quantum-Dirac outcome seal."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest import MANIFEST_FILENAMES, validate_committed_manifests
from .protocol import (
    CONTRACT_REF,
    DEVELOPMENT_RESULT_REF,
    EXPERIMENT_DIR_REF,
    FREEZE_TAG,
    PROTOCOL_VERSION,
    SEARCH_ID,
    SPEC_DIR_REF,
)
from .spec import audit_design, repository_root, sha256_file


class QuantumDiracSealError(ValueError):
    pass


def _discover(root: Path, directory: str) -> tuple[str, ...]:
    base = root / directory
    if not base.is_dir():
        raise QuantumDiracSealError(f"registered directory is missing: {directory}")
    return tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in base.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    )


def _hash_map(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    return {path: sha256_file(root / path) for path in paths}


def preview_disabled_seal(root: Path | None = None) -> dict[str, Any]:
    root = repository_root() if root is None else root.resolve()
    audit_design(root)
    validate_committed_manifests(root)
    source_files = _discover(root, "src/quantum_dirac")
    test_files = _discover(root, "tests/quantum_dirac")
    spec_files = _discover(root, SPEC_DIR_REF)
    experiment_dir = root / EXPERIMENT_DIR_REF
    manifest_paths = tuple(
        (experiment_dir / filename).relative_to(root).as_posix()
        for filename in MANIFEST_FILENAMES
    )
    for forbidden in (
        experiment_dir / "outcome_seal.json",
        experiment_dir / "development_open_manifest.json",
        experiment_dir / "confirmation_open_manifest.json",
        root / DEVELOPMENT_RESULT_REF,
    ):
        if forbidden.exists():
            raise QuantumDiracSealError(
                f"draft seal preview found forbidden artifact: {forbidden.relative_to(root)}"
            )
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "contract": {
            "path": CONTRACT_REF,
            "sha256": sha256_file(root / CONTRACT_REF),
        },
        "source_files": _hash_map(root, source_files),
        "test_files": _hash_map(root, test_files),
        "spec_files": _hash_map(root, spec_files),
        "manifest_files": _hash_map(root, manifest_paths),
        "required_freeze_tag": FREEZE_TAG,
        "run_command_enabled": False,
        "registered_result_path": DEVELOPMENT_RESULT_REF,
        "preview_only_not_writable": True,
    }
