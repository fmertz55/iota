"""Canonical prospective manifest construction without candidate evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .protocol import (
    CANDIDATE_ID,
    CONFIRMATION_SCENARIOS,
    DEVELOPMENT_SCENARIOS,
    EXPERIMENT_DIR_REF,
    PROTOCOL_VERSION,
    SEARCH_ID,
    SPEC_DIR_REF,
)
from .spec import audit_design, load_json, repository_root, sha256_file


MANIFEST_FILENAMES = (
    "candidate_manifest.json",
    "scenario_manifest.json",
    "state_manifest.json",
    "partition_manifest.json",
)


def _binding(path: Path, root: Path) -> dict[str, str]:
    return {
        "path": path.resolve().relative_to(root.resolve()).as_posix(),
        "sha256": sha256_file(path),
    }


def build_manifests(root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = repository_root() if root is None else root.resolve()
    # Prospective manifests remain immutable after freezing, so validating them
    # must continue to work while the separately sealed lifecycle files exist.
    audit = audit_design(root, allow_lifecycle_artifacts=True)
    spec_dir = root / SPEC_DIR_REF
    candidate = load_json(spec_dir / "candidate.json")
    scenarios = load_json(spec_dir / "scenarios.json")
    states = load_json(spec_dir / "states.json")
    partitions = load_json(spec_dir / "partitions.json")
    common = {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "prospective_outcomes_forbidden",
        "protocol": _binding(spec_dir / "protocol.json", root),
    }
    return {
        "candidate_manifest.json": {
            **common,
            "candidate_id": CANDIDATE_ID,
            "candidate": _binding(spec_dir / "candidate.json", root),
            "resource_accounting": candidate["arithmetic"] | {
                "local_hilbert_dimension": candidate["substrate"][
                    "local_hilbert_dimension"
                ],
                "modes_per_site": candidate["substrate"]["modes_per_site"],
                "gate_order": candidate["gate_order"],
            },
            "registered_outcomes_forbidden": True,
        },
        "scenario_manifest.json": {
            **common,
            "scenario_spec": _binding(spec_dir / "scenarios.json", root),
            "development_ids": list(DEVELOPMENT_SCENARIOS),
            "confirmation_ids": list(CONFIRMATION_SCENARIOS),
            "development_batch_indivisible": True,
            "confirmation_batch_indivisible": True,
            "registered_outcomes_forbidden": True,
        },
        "state_manifest.json": {
            **common,
            "state_spec": _binding(spec_dir / "states.json", root),
            "development_ids": [value["id"] for value in states["development"]],
            "confirmation_ids": [value["id"] for value in states["confirmation"]],
            "serialized_amplitude_tables_allowed": False,
            "registered_outcomes_forbidden": True,
        },
        "partition_manifest.json": {
            **common,
            "partition_spec": _binding(spec_dir / "partitions.json", root),
            "development_scenarios": partitions["development_scenarios"],
            "confirmation_scenarios": partitions["confirmation_scenarios"],
            "confirmation_single_use": partitions["confirmation_single_use"],
            "registered_outcomes_forbidden": True,
        },
    }


def validate_committed_manifests(root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = repository_root() if root is None else root.resolve()
    expected = build_manifests(root)
    experiment_dir = root / EXPERIMENT_DIR_REF
    for filename, value in expected.items():
        path = experiment_dir / filename
        actual = load_json(path)
        if actual != value:
            raise ValueError(f"{filename} differs from the canonical prospective manifest")
    return expected
