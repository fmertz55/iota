from __future__ import annotations

import unittest
from pathlib import Path

from src.quantum_dirac_symmetry_qca.protocol import (
    FORBIDDEN_PRE_FREEZE_PATHS,
    REGISTERED_SCENARIOS,
    REGISTERED_SIZES,
    SEARCH_ID,
)
from src.quantum_dirac_symmetry_qca.seal import (
    SymmetryQCASealError,
    preview_disabled_seal,
    write_disabled_seal,
)
from src.quantum_dirac_symmetry_qca.manifest import validate_committed_manifests
from src.quantum_dirac_symmetry_qca.spec import (
    SymmetryQCASpecError,
    audit_design,
    guard_pre_freeze_candidate,
    guard_pre_freeze_target,
)


ROOT = Path(__file__).resolve().parents[2]


class SymmetryQCAProtocolDraftTests(unittest.TestCase):
    def test_design_audits_without_authorizing_outcomes(self) -> None:
        audit = audit_design(ROOT)
        self.assertEqual(audit["search_id"], SEARCH_ID)
        self.assertTrue(audit["registered_outcomes_forbidden"])
        self.assertTrue(audit["production_implementation_present"])
        self.assertIn("production.py", audit["implementation_files"])
        self.assertIn("independent_registered.py", audit["implementation_files"])
        self.assertTrue(audit["threshold_interval_certificate_present"])

    def test_candidate_guard_allows_only_disclosed_sizes(self) -> None:
        guard_pre_freeze_candidate(n_sites=6)
        guard_pre_freeze_candidate(n_sites=10)
        for n_sites in (8, 256, 320, 512, 640, 1024, 1280):
            with self.subTest(n_sites=n_sites):
                with self.assertRaises(SymmetryQCASpecError):
                    guard_pre_freeze_candidate(n_sites=n_sites)

    def test_registered_scenarios_are_forbidden_even_on_fixture_sizes(self) -> None:
        for scenario_id in REGISTERED_SCENARIOS:
            with self.subTest(scenario_id=scenario_id):
                with self.assertRaises(SymmetryQCASpecError):
                    guard_pre_freeze_candidate(n_sites=6, scenario_id=scenario_id)
                with self.assertRaises(SymmetryQCASpecError):
                    guard_pre_freeze_target(cutoff=3, scenario_id=scenario_id)

    def test_target_guard_allows_only_cutoff_three(self) -> None:
        guard_pre_freeze_target(cutoff=3)
        for cutoff in (2, 4, 72):
            with self.subTest(cutoff=cutoff):
                with self.assertRaises(SymmetryQCASpecError):
                    guard_pre_freeze_target(cutoff=cutoff)

    def test_disabled_preview_reports_remaining_preseal_pipeline(self) -> None:
        preview = preview_disabled_seal(ROOT)
        self.assertFalse(preview["seal_ready"])
        self.assertFalse(preview["run_command_enabled"])
        self.assertTrue(preview["registered_outcomes_forbidden_until_stage_open"])
        self.assertIn("registered stage runner", preview["missing_prerequisites"])
        self.assertIn("full-ledger independent verifier", preview["missing_prerequisites"])
        with self.assertRaises(SymmetryQCASealError):
            write_disabled_seal(ROOT)
        for relative in FORBIDDEN_PRE_FREEZE_PATHS:
            self.assertFalse((ROOT / relative).exists())

    def test_prospective_manifests_are_canonical_and_outcome_free(self) -> None:
        manifests = validate_committed_manifests(ROOT)
        self.assertEqual(len(manifests), 4)
        self.assertTrue(
            all(value["registered_outcomes_forbidden"] for value in manifests.values())
        )

    def test_registered_size_constants_are_not_fixture_sizes(self) -> None:
        self.assertEqual(REGISTERED_SIZES, (320, 640, 1280))


if __name__ == "__main__":
    unittest.main()
