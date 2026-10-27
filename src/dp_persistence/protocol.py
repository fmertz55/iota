"""Registered constants and spec loading for ICP-DP-PERSISTENCE-001.

Every reference value used by the classifier is read from the spec directory
at runtime.  The constants below are repository paths and identities that the
audit command cross-checks against ``protocol.json``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


SEARCH_ID = "ICP-DP-PERSISTENCE-001"
PROTOCOL_VERSION = "0.1-draft"
FREEZE_TAG = "icp-dp-persistence-001-v0.1-frozen"
DATA_CLASS = "development with single-use confirmation"
LAW_ID = "IOTA-MIN-L0"

SPEC_DIR_REF = "specs/icp_directed_percolation_persistence/v0.1-draft"
CONTRACT_REF = "docs/ICP_DIRECTED_PERCOLATION_PERSISTENCE_CONTRACT.md"
SOURCE_DIR_REF = "src/dp_persistence"
TEST_DIR_REF = "tests/dp_persistence"
RESULT_SCHEMA_REF = f"{SPEC_DIR_REF}/result.schema.json"

EXPERIMENT_DIR_REF = "experiments/dp_persistence/ICP-DP-PERSISTENCE-001"
OUTPUT_DIR_REF = "output/dp_persistence/ICP-DP-PERSISTENCE-001"

OUTCOME_SEAL_REF = f"{EXPERIMENT_DIR_REF}/outcome_seal.json"
CALIBRATION_RESULT_REF = f"{OUTPUT_DIR_REF}/calibration_results.json"
STRUCTURAL_AUDIT_ANSWERS_REF = f"{EXPERIMENT_DIR_REF}/structural_audit_answers.json"
DEVELOPMENT_OPEN_MANIFEST_REF = f"{EXPERIMENT_DIR_REF}/development_open_manifest.json"
DEVELOPMENT_RESULT_REF = f"{OUTPUT_DIR_REF}/development_results.json"
CONFIRMATION_OPEN_MANIFEST_REF = f"{EXPERIMENT_DIR_REF}/confirmation_open_manifest.json"
CONFIRMATION_RESULT_REF = f"{OUTPUT_DIR_REF}/confirmation_results.json"
# Not listed in protocol.json registered_paths; see SPEC_QUESTIONS.md Q-PATH-1.
CALIBRATION_OPEN_MANIFEST_REF = f"{EXPERIMENT_DIR_REF}/calibration_open_manifest.json"

REGISTERED_PATHS = {
    "seal": OUTCOME_SEAL_REF,
    "calibration_result": CALIBRATION_RESULT_REF,
    "structural_audit_answers": STRUCTURAL_AUDIT_ANSWERS_REF,
    "development_open_manifest": DEVELOPMENT_OPEN_MANIFEST_REF,
    "development_result": DEVELOPMENT_RESULT_REF,
    "confirmation_open_manifest": CONFIRMATION_OPEN_MANIFEST_REF,
    "confirmation_result": CONFIRMATION_RESULT_REF,
}

ALL_PROTECTED_PATHS = tuple(REGISTERED_PATHS.values()) + (CALIBRATION_OPEN_MANIFEST_REF,)

REGISTERED_WORKER_PROCESSES = 4

SPEC_FILES = (
    "protocol.json",
    "minimal_law.json",
    "estimators.json",
    "calibration.json",
    "partitions.json",
    "iota_spreading.json",
    "reference_classes.json",
    "structural_audit.json",
)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def spec_dir(root: Path | None = None) -> Path:
    return (repository_root() if root is None else root) / SPEC_DIR_REF


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_spec_file(name: str, root: Path | None = None) -> dict[str, Any]:
    path = spec_dir(root) / name
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    if type(value) is not dict:
        raise ValueError(f"{path}: root must be an object")
    return value


@lru_cache(maxsize=None)
def spec(name: str) -> dict[str, Any]:
    """Cached spec file from the repository's own spec directory."""

    return load_spec_file(name)


def calibration_model(model_id: str) -> dict[str, Any]:
    for model in spec("calibration.json")["models"]:
        if model["model_id"] == model_id:
            return model
    raise KeyError(f"unknown calibration model {model_id!r}")
