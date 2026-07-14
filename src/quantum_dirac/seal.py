"""Content seal for the frozen quantum-Dirac experiment."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .manifest import MANIFEST_FILENAMES, validate_committed_manifests
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
    OUTCOME_SEAL_REF,
    PRECISION_BITS,
    PRIMARY_LIBRARY_VERSION,
    PROTOCOL_VERSION,
    REGISTERED_SIZES,
    SEARCH_ID,
    SPEC_DIR_REF,
)
from .spec import (
    QuantumDiracSpecError,
    audit_design,
    canonical_json,
    repository_root,
    sha256_file,
    write_canonical_json_once,
)


class QuantumDiracSealError(ValueError):
    pass


def _discover(root: Path, directory: str) -> tuple[str, ...]:
    base = root / directory
    if not base.is_dir() or base.is_symlink():
        raise QuantumDiracSealError(f"registered directory is missing: {directory}")
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
        raise QuantumDiracSealError("cannot resolve the seal parent commit")
    return result.stdout.strip()


def _registered_paths(root: Path) -> tuple[dict[str, str], ...]:
    experiment_dir = root / EXPERIMENT_DIR_REF
    return tuple(
        {
            "path": (experiment_dir / filename).relative_to(root).as_posix(),
            "sha256": sha256_file(experiment_dir / filename),
        }
        for filename in MANIFEST_FILENAMES
    )


COMMAND_FILES = (
    "Makefile",
    "requirements.txt",
    ".github/workflows/research-compendium.yml",
)


def build_disabled_seal(root: Path | None = None) -> dict[str, Any]:
    root = repository_root() if root is None else root.resolve()
    audit_design(root)
    validate_committed_manifests(root)
    forbidden = (
        root / OUTCOME_SEAL_REF,
        root / DEVELOPMENT_OPEN_REF,
        root / CONFIRMATION_OPEN_REF,
        root / DEVELOPMENT_RESULT_REF,
        root / CONFIRMATION_RESULT_REF,
    )
    for path in forbidden:
        if path.exists():
            raise QuantumDiracSealError(
                f"registered artifact already exists: {path.relative_to(root)}"
            )
    source_files = _discover(root, "src/quantum_dirac")
    test_files = _discover(root, "tests/quantum_dirac")
    spec_files = _discover(root, SPEC_DIR_REF)
    manifests = _registered_paths(root)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "freeze_parent_commit": _head(root),
        "contract": {"path": CONTRACT_REF, "sha256": sha256_file(root / CONTRACT_REF)},
        "source_files": _hash_map(root, source_files),
        "test_files": _hash_map(root, test_files),
        "spec_files": _hash_map(root, spec_files),
        "manifest_files": {item["path"]: item["sha256"] for item in manifests},
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
        "run_command_enabled": False,
        "development_result_path": DEVELOPMENT_RESULT_REF,
        "confirmation_result_path": CONFIRMATION_RESULT_REF,
    }


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise QuantumDiracSealError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def load_canonical_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="ascii")
        value = json.loads(text, object_pairs_hook=_strict_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QuantumDiracSealError(f"{path}: {exc}") from exc
    if type(value) is not dict or text != canonical_json(value) + "\n":
        raise QuantumDiracSealError(f"{path}: expected canonical JSON plus LF")
    return value


def _expected_from_existing(root: Path, existing: dict[str, Any]) -> dict[str, Any]:
    expected_keys = set(build_disabled_seal_from_current(root, existing))
    if set(existing) != expected_keys:
        raise QuantumDiracSealError("outcome seal has missing or unexpected fields")
    return build_disabled_seal_from_current(root, existing)


def build_disabled_seal_from_current(
    root: Path, existing: dict[str, Any]
) -> dict[str, Any]:
    """Rebuild the seal while allowing lifecycle artifacts to exist."""

    validate_committed_manifests(root)
    source_files = _discover(root, "src/quantum_dirac")
    test_files = _discover(root, "tests/quantum_dirac")
    spec_files = _discover(root, SPEC_DIR_REF)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "freeze_parent_commit": existing.get("freeze_parent_commit"),
        "contract": {"path": CONTRACT_REF, "sha256": sha256_file(root / CONTRACT_REF)},
        "source_files": _hash_map(root, source_files),
        "test_files": _hash_map(root, test_files),
        "spec_files": _hash_map(root, spec_files),
        "manifest_files": {
            item["path"]: item["sha256"] for item in _registered_paths(root)
        },
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
        "run_command_enabled": False,
        "development_result_path": DEVELOPMENT_RESULT_REF,
        "confirmation_result_path": CONFIRMATION_RESULT_REF,
    }


def preview_disabled_seal(root: Path | None = None) -> dict[str, Any]:
    return build_disabled_seal(root)


def write_disabled_seal(root: Path | None = None) -> Path:
    root = repository_root() if root is None else root.resolve()
    path = root / OUTCOME_SEAL_REF
    write_canonical_json_once(path, build_disabled_seal(root))
    return path


def verify_outcome_seal(root: Path | None = None) -> dict[str, Any]:
    root = repository_root() if root is None else root.resolve()
    path = root / OUTCOME_SEAL_REF
    if not path.is_file() or path.is_symlink():
        raise QuantumDiracSealError("registered outcome seal is missing")
    existing = load_canonical_json(path)
    expected = _expected_from_existing(root, existing)
    if existing != expected:
        raise QuantumDiracSealError("outcome seal differs from registered bytes")
    return existing
