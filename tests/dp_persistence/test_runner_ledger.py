from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from src.dp_persistence import ledger, runner
from src.dp_persistence.ledger import LedgerError, validate_result, write_canonical_json_once
from src.dp_persistence.protocol import LAW_ID, PROTOCOL_VERSION, SEARCH_ID
from tiny_tasks import echo, slow, synthetic_iota_run


DEV_FIRST = 10_000_000


def tiny_runner(workers: int = 2) -> runner.PointRunner:
    plan = runner.ModelPlan(
        model_id=LAW_ID,
        dimension_key="3d",
        coarse_grid=[0.2, 0.4],
        bisection_steps=2,
        runs_coarse=400,
        runs_bisection=400,
        runs_final=600,
        horizon=512,
        midpoint_kind="arithmetic",
        expected_class=None,
        static=True,
    )
    return runner.PointRunner(
        plan,
        seed_block=lambda index, control, runs: list(range(DEV_FIRST + 25000 * index, DEV_FIRST + 25000 * index + runs)),
        task_for=lambda control, seed: (control, seed, 512),
        task_function=synthetic_iota_run,
        workers=workers,
        ceiling_seconds=600,
    )


def development_ledger(model: dict) -> dict:
    return {
        "search_id": SEARCH_ID,
        "protocol_version": PROTOCOL_VERSION,
        "result_kind": "development",
        "seal_sha256": "0" * 64,
        "parent_commit": "1" * 40,
        "predicted_classes": {"IOTA-MIN-L0": "DyP_3", "IOTA-MIN-L1": "no_absorbing_transition"},
        "models": [model],
    }


class WorkerPoolTests(unittest.TestCase):
    def test_results_are_collected_in_canonical_order(self) -> None:
        values = [record["value"] for record in runner.run_tasks(echo, list(range(40)), workers=4, ceiling_seconds=60)]
        self.assertEqual(values, list(range(40)))

    def test_wall_clock_ceiling_discards_the_point(self) -> None:
        with self.assertRaises(runner.ResourceCeiling):
            runner.run_tasks(slow, list(range(20)), workers=2, ceiling_seconds=0.1)


class EndToEndPlumbingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = runner.iota_search_result(tiny_runner())

    def test_result_validates(self) -> None:
        model = self.model
        self.assertEqual(model["terminal_status"], "classified")
        self.assertEqual(model["brackets"], [[0.2, 0.4]])
        self.assertEqual([p["role"] for p in model["points"]], ["coarse", "coarse", "bisection", "bisection", "final"])
        self.assertEqual(model["points"][-1]["seed_first"], DEV_FIRST + 25000 * 16)
        self.assertEqual(model["ledger_max_abs_residual"], 0)
        self.assertEqual(len(model["exploration"]), 5)
        validate_result(development_ledger(model))

    def test_cross_field_checks(self) -> None:
        bad = copy.deepcopy(self.model)
        bad["ledger_max_abs_residual"] = 1
        with self.assertRaises(LedgerError):
            validate_result(development_ledger(bad))

        bad = copy.deepcopy(self.model)
        bad["per_class"] = {"DP_3p1": "excluded", "DyP_3": "match"}
        bad["verdict"] = "DP_3p1"
        with self.assertRaises(LedgerError):
            validate_result(development_ledger(bad))

        bad = copy.deepcopy(self.model)
        bad["hypotheses"] = {"H1_threshold": "budget_shifted", "H2_dynamic_class": "supported", "H3_static_tail": "not_applicable"}
        with self.assertRaises(LedgerError):
            validate_result(development_ledger(bad))

        bad = copy.deepcopy(self.model)
        bad["points"][0]["seed_first"] = 30_000_000
        bad["points"][0]["seed_last"] = 30_000_000 + bad["points"][0]["runs"] - 1
        with self.assertRaises(LedgerError):
            validate_result(development_ledger(bad))

        bad = development_ledger(copy.deepcopy(self.model))
        bad["models"][0]["unexpected"] = 1
        with self.assertRaises(LedgerError):
            validate_result(bad)

    def test_trace_hash_is_order_sensitive(self) -> None:
        records = [(s, synthetic_iota_run((0.2, s, 64))) for s in (5, 6, 7)]
        digest = ledger.point_trace_sha256("domain", records)
        self.assertEqual(digest, ledger.point_trace_sha256("domain", records))
        self.assertNotEqual(digest, ledger.point_trace_sha256("other", records))
        with self.assertRaises(LedgerError):
            ledger.point_trace_sha256("domain", list(reversed(records)))


class AtomicWriteTests(unittest.TestCase):
    def test_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "result.json"
            write_canonical_json_once(path, {"b": 1, "a": [1, 2]})
            self.assertEqual(path.read_text(), '{"a":[1,2],"b":1}\n')
            with self.assertRaises(LedgerError):
                write_canonical_json_once(path, {"a": 2})
            self.assertFalse(path.with_name("result.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
