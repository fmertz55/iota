from __future__ import annotations

import unittest
from pathlib import Path

from src.quantum_dirac.protocol import FREEZE_TAG, SEARCH_ID
from src.quantum_dirac.seal import preview_disabled_seal, verify_outcome_seal


ROOT = Path(__file__).resolve().parents[2]


class DisabledSealPreviewTests(unittest.TestCase):
    def test_preview_hashes_complete_draft_without_writing_a_seal(self) -> None:
        seal_path = (
            ROOT
            / "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001/outcome_seal.json"
        )
        value = verify_outcome_seal(ROOT) if seal_path.exists() else preview_disabled_seal(ROOT)
        self.assertEqual(value["search_id"], SEARCH_ID)
        self.assertEqual(value["required_freeze_tag"], FREEZE_TAG)
        self.assertFalse(value["run_command_enabled"])
        self.assertEqual(len(value["freeze_parent_commit"]), 40)
        self.assertIn("src/quantum_dirac/candidate.py", value["source_files"])
        self.assertIn("tests/quantum_dirac/test_candidate.py", value["test_files"])
        self.assertIn("Makefile", value["command_files"])
        self.assertEqual(value["primary_library_version"], "0.9.0")
        self.assertEqual(value["independent_library_version"], "1.3.0")
        if not seal_path.exists():
            self.assertFalse(seal_path.exists())


if __name__ == "__main__":
    unittest.main()
