from __future__ import annotations

import unittest
from pathlib import Path

from src.minimal_realization_role_succession_exact.cli import build_parser
from src.minimal_realization_role_succession_exact.protocol import (
    OUTCOME_SEAL_REF,
    PARENT_RESULT_SHA256,
    RESULT_PATH_REF,
    SEARCH_ID,
)
from src.minimal_realization_role_succession_exact.seal import (
    build_outcome_seal,
    verify_outcome_seal,
)


ROOT = Path(__file__).resolve().parents[2]


class SealAndCommandSurfaceTests(unittest.TestCase):
    def test_disabled_seal_is_buildable_or_verifiable_without_outcome_work(self) -> None:
        path = ROOT / OUTCOME_SEAL_REF
        value = (
            verify_outcome_seal(path, root=ROOT)
            if path.exists()
            else build_outcome_seal(ROOT)
        )
        self.assertEqual(value["search_id"], SEARCH_ID)
        self.assertEqual(value["parent_result"]["sha256"], PARENT_RESULT_SHA256)
        self.assertFalse(value["run_command_enabled"])
        self.assertIsNone(value["dynamic_layer_ceiling"])
        self.assertEqual(value["result_path"], RESULT_PATH_REF)
        self.assertIn("runner.py", "\n".join(value["source_files"]))
        self.assertIn("test_local_impossibility.py", "\n".join(value["test_files"]))

    def test_cli_exposes_no_pre_freeze_run_bypass(self) -> None:
        parser = build_parser()
        commands = set(parser._subparsers._group_actions[0].choices)
        self.assertEqual(
            commands,
            {
                "compile-candidates",
                "seal-outcomes",
                "verify-seal",
                "open-outcomes",
                "run",
                "verify-results",
            },
        )


if __name__ == "__main__":
    unittest.main()
