from __future__ import annotations

import inspect
import unittest

from src.minimal_realization_role_succession.detector import (
    DetectorResult,
    LayerAssessment,
)
from src.minimal_realization_role_succession_exact.local_impossibility import (
    analyze_local_impossibility,
)
from src.minimal_realization_role_succession_exact.runner import (
    ExactClosureError,
    _capture_stages,
    _dynamic_record,
    _static_record,
    evaluate_uncapped_continuation,
)


COPY_SELF_ROWS = ("010", "011", "110", "111")
COPY_PREDECESSOR_ROWS = ("100", "101", "110", "111")


def synthetic_candidate(rows: tuple[str, ...]) -> dict[str, object]:
    rule = sum(1 << int(row, 2) for row in rows)
    return {
        "candidate_id": f"SYNTHETIC-{rule}",
        "wolfram_rule_number": rule,
        "atomic_n_l": len(rows),
        "parent_candidate_index": 1,
        "parent_record_sha256": "0" * 64,
        "production_rows": list(rows),
    }


class RunnerHelperTests(unittest.TestCase):
    def test_registered_continuation_has_no_resource_ceiling_parameter(self) -> None:
        self.assertNotIn("max_layers", inspect.signature(evaluate_uncapped_continuation).parameters)
        self.assertNotIn("resource_limit", inspect.signature(evaluate_uncapped_continuation).parameters)

    def test_static_record_requires_an_actual_impossibility_proof(self) -> None:
        excluded = analyze_local_impossibility(COPY_SELF_ROWS)
        record = _static_record(synthetic_candidate(COPY_SELF_ROWS), excluded)
        self.assertEqual(record["classification"], "symbolically_unreachable")
        self.assertTrue(record["future_unreachable"])
        self.assertIsNone(record["dynamic_continuation"])

        survivor = analyze_local_impossibility(COPY_PREDECESSOR_ROWS)
        with self.assertRaisesRegex(ExactClosureError, "impossibility certificate"):
            _static_record(synthetic_candidate(COPY_PREDECESSOR_ROWS), survivor)

    def test_dynamic_record_requires_an_exact_terminal(self) -> None:
        survivor = analyze_local_impossibility(COPY_PREDECESSOR_ROWS)
        candidate = synthetic_candidate(COPY_PREDECESSOR_ROWS)
        with self.assertRaisesRegex(ExactClosureError, "exact terminal"):
            _dynamic_record(candidate, survivor, {"classification": "resource_censored"})

    def test_stage_capture_keeps_first_witness(self) -> None:
        assessment = LayerAssessment(
            first_role_anchor=4,
            first_successor=(4, 5),
            first_intervention_eligible=(4, 5),
            detector_result=DetectorResult(False, None, None, None, None, None),
        )
        values = _capture_stages(assessment, 7, None, None, None)
        self.assertEqual(values, ((7, 4), (7, 4, 5), (7, 4, 5)))
        later = _capture_stages(assessment, 8, *values)
        self.assertEqual(later, values)


if __name__ == "__main__":
    unittest.main()
