from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from src.minimal_realization.detector import (
    detect_proto_object,
    matched_intervention_states,
    outward_future_values,
    role_at,
    successor_anchor,
)
from src.minimal_realization.dynamics import active_loci, run_trajectory, state_from_active


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "specs/icp_minimal_realization/v0.2-draft/detector_fixtures.json"


def load_fixtures() -> dict:
    with FIXTURES.open(encoding="utf-8") as handle:
        return json.load(handle)


class DetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = load_fixtures()

    def test_role_fixtures(self) -> None:
        for case in self.fixtures["role_cases"]:
            with self.subTest(case=case["id"]):
                state = state_from_active(case["active_offsets"])
                baseline = state_from_active(case["baseline_active_offsets"])
                self.assertEqual(role_at(state, baseline, case["anchor"]), case["expected"])

    def test_successor_fixtures(self) -> None:
        for case in self.fixtures["succession_cases"]:
            with self.subTest(case=case["id"]):
                active = []
                expected = case["expected_successor_anchor"]
                if expected is not None:
                    active = [expected, expected + 1]
                elif case["eligible_next_anchors"]:
                    ineligible = case["eligible_next_anchors"][0]
                    active = [ineligible, ineligible + 1]
                result = successor_anchor(
                    state_from_active(active),
                    0,
                    case["formation_anchor"],
                    origin=0,
                    next_layer=4,
                )
                self.assertEqual(result, expected)

    def test_matched_intervention_invariants(self) -> None:
        case = next(
            item for item in self.fixtures["intervention_cases"] if item["id"] == "matched_arm_invariants"
        )
        natural = state_from_active([0, 1])
        sham, breaking = matched_intervention_states(natural, 0)
        natural_bits = set(active_loci(natural))
        for arm in (sham, breaking):
            arm_bits = set(active_loci(arm))
            self.assertEqual(len(natural_bits ^ arm_bits), case["expected_hamming_distance_each"])
            self.assertEqual(len(arm_bits), case["expected_active_count_each"])

    def test_nonquiescent_external_guard_rejects_intervention(self) -> None:
        case = next(
            item
            for item in self.fixtures["intervention_cases"]
            if item["id"] == "nonquiescent_external_guard_is_ineligible"
        )
        state = state_from_active(case["natural_active_offsets"])
        with self.assertRaisesRegex(ValueError, "external guard"):
            matched_intervention_states(state, 0)

    def test_detector_skips_guarded_role_instead_of_aborting(self) -> None:
        seed = state_from_active([0])
        guarded_role = state_from_active([0, 1, 3])
        seeded = (seed,) + (guarded_role,) * 18
        baseline = (0,) * 19

        def synthetic_exact_step(state: int, rows: object) -> int:
            del rows
            if state == seed:
                return guarded_role
            if state == guarded_role:
                return guarded_role
            return 0

        with (
            patch("src.minimal_realization.detector.step", side_effect=synthetic_exact_step),
            patch(
                "src.minimal_realization.detector.outward_future_values",
                side_effect=AssertionError("guarded role must not reach intervention"),
            ),
        ):
            result = detect_proto_object(seeded, baseline, ())
        self.assertFalse(result.passed)

    def test_copy_predecessor_fixture_has_outward_effect(self) -> None:
        case = next(
            item for item in self.fixtures["intervention_cases"] if item["id"] == "copy_predecessor_outward_effect"
        )
        state = state_from_active(case["natural_active_offsets"])
        sham, breaking = outward_future_values(state, case["production_rows"], 0)
        self.assertEqual(sham, case["expected_sham_external_future"])
        self.assertEqual(breaking, case["expected_breaking_external_future"])
        self.assertEqual(sham != breaking, case["expected"])

    def test_endpoint_comparison_fixtures(self) -> None:
        for case in self.fixtures["intervention_cases"]:
            if "sham_external_future" not in case:
                continue
            with self.subTest(case=case["id"]):
                observed = case["sham_external_future"] != case["breaking_external_future"]
                self.assertEqual(observed, case["expected"])

    def test_selection_fixture(self) -> None:
        case = self.fixtures["selection_cases"][0]
        selected = min(case["qualifying_time_anchor_pairs"], key=lambda pair: (pair[0], pair[1]))
        self.assertEqual(selected, case["expected"])

    def test_excluded_zero_law_trajectory_fails_exact_detector(self) -> None:
        seeded = run_trajectory(state_from_active([0]), (), 18)
        baseline = run_trajectory(0, (), 18)
        result = detect_proto_object(seeded, baseline, ())
        self.assertFalse(result.passed)
        self.assertIsNone(result.t_proto)

    def test_detector_rejects_nonlawful_trajectory(self) -> None:
        seeded = list(run_trajectory(state_from_active([0]), (), 18))
        baseline = run_trajectory(0, (), 18)
        seeded[2] = state_from_active([1])
        with self.assertRaisesRegex(ValueError, "not law-exact"):
            detect_proto_object(tuple(seeded), baseline, ())


if __name__ == "__main__":
    unittest.main()
