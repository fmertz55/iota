from __future__ import annotations

import unittest
import inspect
from pathlib import Path

from src.quantum_dirac.cli import build_parser
from src.quantum_dirac.manifest import validate_committed_manifests
from src.quantum_dirac.protocol import OUTCOME_SEAL_REF, REGISTERED_SCENARIOS
from src.quantum_dirac.spec import (
    QuantumDiracSpecError,
    audit_design,
    guard_pre_freeze_fixture,
)


ROOT = Path(__file__).resolve().parents[2]


class QuantumDiracSpecTests(unittest.TestCase):
    def test_design_and_prospective_manifests_validate_without_outcomes(self) -> None:
        seal_path = ROOT / OUTCOME_SEAL_REF
        audit = audit_design(ROOT, allow_lifecycle_artifacts=seal_path.exists())
        self.assertTrue(audit["registered_outcomes_forbidden"])
        manifests = validate_committed_manifests(ROOT)
        self.assertEqual(set(manifests), {
            "candidate_manifest.json",
            "scenario_manifest.json",
            "state_manifest.json",
            "partition_manifest.json",
        })
        self.assertTrue(
            all(value["registered_outcomes_forbidden"] for value in manifests.values())
        )

    def test_pre_freeze_guard_allows_only_disclosed_fixture_sizes(self) -> None:
        guard_pre_freeze_fixture(n_sites=8)
        guard_pre_freeze_fixture(n_sites=16)
        for forbidden in (7, 32, 256, 512, 1024):
            with self.subTest(n_sites=forbidden):
                with self.assertRaises(QuantumDiracSpecError):
                    guard_pre_freeze_fixture(n_sites=forbidden)

    def test_registered_scenarios_are_unconditionally_forbidden(self) -> None:
        for scenario_id in REGISTERED_SCENARIOS:
            with self.subTest(scenario_id=scenario_id):
                with self.assertRaises(QuantumDiracSpecError):
                    guard_pre_freeze_fixture(n_sites=8, scenario_id=scenario_id)

    def test_cli_exposes_only_the_gated_lifecycle_surface(self) -> None:
        parser = build_parser()
        commands = set(parser._subparsers._group_actions[0].choices)
        self.assertEqual(
            commands,
            {
                "audit-design",
                "validate-manifests",
                "preview-disabled-seal",
                "seal-outcomes",
                "verify-seal",
                "open-stage",
                "run-stage",
                "verify-result",
            },
        )

    def test_registered_evaluator_import_occurs_after_git_permit(self) -> None:
        from src.quantum_dirac import cli

        source = inspect.getsource(cli._run_command)
        self.assertLess(
            source.index("issue_registered_permit"),
            source.index("from .runner import build_stage_ledger"),
        )


if __name__ == "__main__":
    unittest.main()
