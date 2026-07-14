from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path

from src.minimal_realization_role_succession_exact import protocol
from src.minimal_realization_role_succession_exact import runner


ROOT = Path(__file__).resolve().parents[2]


class ExactClosureProtocolTests(unittest.TestCase):
    def test_no_second_resource_boundary_is_registered(self) -> None:
        self.assertEqual(protocol.PARENT_RESOURCE_BOUNDARY, 1_000_000)
        self.assertNotIn("MAX_LAYERS", vars(protocol))
        source = inspect.getsource(runner.evaluate_uncapped_continuation)
        self.assertIn("while True", source)
        self.assertNotIn("range(1, max", source)

    def test_only_exact_dynamic_terminals_are_allowed(self) -> None:
        self.assertEqual(
            protocol.DYNAMIC_TERMINAL_STATUSES,
            (
                "exact_pass_on_fixed_orbit",
                "recurrence_excluded_on_fixed_orbit",
            ),
        )
        self.assertNotIn("resource_censored", protocol.TERMINAL_CLASSIFICATIONS)

    def test_freeze_and_registered_paths_are_distinct_from_parent(self) -> None:
        self.assertEqual(protocol.SEARCH_ID, "MIR-ROLE-SUCCESSION-EXACT-001")
        self.assertNotEqual(protocol.RESULT_PATH_REF, protocol.PARENT_RESULT_REF)
        self.assertIn(protocol.FREEZE_TAG, protocol.opening_condition())

    def test_machine_protocol_matches_executable_constants(self) -> None:
        value = json.loads(
            (ROOT / protocol.SPEC_DIR_REF / "protocol.json").read_text(encoding="utf-8")
        )
        self.assertEqual(value["protocol_version"], protocol.PROTOCOL_VERSION)
        self.assertEqual(value["search_id"], protocol.SEARCH_ID)
        self.assertEqual(value["data_class"], protocol.DATA_CLASS)
        self.assertEqual(value["parent"]["result_sha256"], protocol.PARENT_RESULT_SHA256)
        self.assertEqual(value["parent"]["prefix_boundary_layer"], protocol.PARENT_RESOURCE_BOUNDARY)
        self.assertIsNone(value["dynamic_continuation"]["layer_ceiling"])
        self.assertFalse(value["run_command_enabled"])

    def test_result_schema_top_level_is_exactly_the_runner_ledger(self) -> None:
        schema = json.loads(
            (ROOT / protocol.RESULT_SCHEMA_REF).read_text(encoding="utf-8")
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), runner.LEDGER_KEYS)
        self.assertEqual(set(schema["properties"]), runner.LEDGER_KEYS)
        self.assertEqual(schema["properties"]["dynamic_layer_ceiling"]["type"], "null")


if __name__ == "__main__":
    unittest.main()
