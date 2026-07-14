from __future__ import annotations

import unittest
from pathlib import Path

from src.quantum_dirac.protocol import FREEZE_TAG, SEARCH_ID
from src.quantum_dirac.seal import preview_disabled_seal


ROOT = Path(__file__).resolve().parents[2]


class DisabledSealPreviewTests(unittest.TestCase):
    def test_preview_hashes_complete_draft_without_writing_a_seal(self) -> None:
        value = preview_disabled_seal(ROOT)
        self.assertEqual(value["search_id"], SEARCH_ID)
        self.assertEqual(value["required_freeze_tag"], FREEZE_TAG)
        self.assertFalse(value["run_command_enabled"])
        self.assertTrue(value["preview_only_not_writable"])
        self.assertIn("src/quantum_dirac/candidate.py", value["source_files"])
        self.assertIn("tests/quantum_dirac/test_candidate.py", value["test_files"])
        self.assertFalse(
            (
                ROOT
                / "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001/outcome_seal.json"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
