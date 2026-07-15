"""Canonical prospective manifests without candidate evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .protocol import (
    CANDIDATE_ID,
    CONFIRMATION_SCENARIOS,
    CONFIRMATION_STATES,
    DEVELOPMENT_SCENARIOS,
    DEVELOPMENT_STATES,
    EXPERIMENT_DIR_REF,
    MANIFEST_FILENAMES,
    PROTOCOL_VERSION,
    SEARCH_ID,
    SPEC_DIR_REF,
)
from .spec import audit_design, load_json, repository_root, sha256_file


def _binding(path: Path, root: Path) -> dict[str, str]:
    return {
        "path": path.resolve().relative_to(root.resolve()).as_posix(),
        "sha256": sha256_file(path),
    }


def build_manifests(root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = repository_root() if root is None else root.resolve()
    audit_design(root, allow_lifecycle_artifacts=True)
    spec_dir = root / SPEC_DIR_REF
    candidate = load_json(spec_dir / "candidate.json")
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
            "architecture": {
                "family": "direct_symmetry_derived_Dirac_QCA",
                "gate_order": candidate["gate_order"],
                "full_space_extension": candidate["substrate"]["full_space_extension"],
                "hard_core_double_occupation_phase": candidate[
                    "full_space_claim_boundary"
                ]["hard_core_double_occupation_phase"],
                "canonical_fermionic_substitution_allowed": False,
            },
            "resource_accounting": candidate["resource_accounting"]
            | {
                "local_hilbert_dimension": candidate["substrate"][
                    "local_hilbert_dimension"
                ],
                "modes_per_site": candidate["substrate"]["modes_per_site"],
                "precision_bits": candidate["arithmetic"]["precision_bits"],
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
            "parent_scenario_reuse": False,
            "registered_outcomes_forbidden": True,
        },
        "state_manifest.json": {
            **common,
            "state_spec": _binding(spec_dir / "states.json", root),
            "development_ids": [item["id"] for item in states["development"]],
            "confirmation_ids": [item["id"] for item in states["confirmation"]],
            "serialized_amplitude_tables_allowed": False,
            "parent_state_reuse": False,
            "registered_outcomes_forbidden": True,
        },
        "partition_manifest.json": {
            **common,
            "partition_spec": _binding(spec_dir / "partitions.json", root),
            "development_scenarios": partitions["development_scenarios"],
            "confirmation_scenarios": partitions["confirmation_scenarios"],
            "development_states": list(DEVELOPMENT_STATES),
            "confirmation_states": list(CONFIRMATION_STATES),
            "confirmation_single_use": partitions["confirmation_single_use"],
            "open_confirmation_only_after_verified_development_pass": partitions[
                "open_confirmation_only_after_verified_development_pass"
            ],
            "registered_outcomes_forbidden": True,
        },
    }


def validate_committed_manifests(
    root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    root = repository_root() if root is None else root.resolve()
    expected = build_manifests(root)
    experiment_dir = root / EXPERIMENT_DIR_REF
    if tuple(expected) != MANIFEST_FILENAMES:
        raise ValueError("canonical prospective manifest order is unstable")
    for filename, value in expected.items():
        if load_json(experiment_dir / filename) != value:
            raise ValueError(f"{filename} differs from its canonical prospective manifest")
    return expected
