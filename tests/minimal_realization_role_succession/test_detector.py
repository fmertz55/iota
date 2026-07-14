from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

import src.minimal_realization_role_succession.detector as detector_module

from src.minimal_realization_role_succession.detector import (
    FORMATION_HORIZON,
    LAST_REQUIRED_LAYER,
    assess_layer,
    in_bidirectional_cone,
    matched_intervention_states,
    ordered_anchors,
    outward_future_values,
    role_anchor_mask,
    role_at,
    successor_anchor,
)
from src.minimal_realization_role_succession.dynamics import (
    active_loci,
    state_from_active,
    step,
)


COPY_PREDECESSOR_ROWS = ("100", "101", "110", "111")
COPY_SELF_ROWS = ("010", "011", "110", "111")
ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    ROOT
    / "specs"
    / "icp_minimal_realization_role_succession"
    / "v0.1-draft"
    / "development_fixtures.json"
)


def disclosed_fixtures() -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="ascii"))
    return payload, {fixture["id"]: fixture for fixture in payload["fixtures"]}


class DisclosedFixtureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload, cls.fixtures = disclosed_fixtures()

    def test_fixture_file_forbids_canonical_seed_trajectories(self) -> None:
        self.assertIs(self.payload["canonical_seed_trajectories_forbidden"], True)

    def test_supplied_dyad_fixtures_execute_exactly_as_disclosed(self) -> None:
        for fixture_id in (
            "copy_predecessor_supplied_dyad_complete_pass",
            "copy_self_supplied_dyad_successor_no_outward_effect",
        ):
            fixture = self.fixtures[fixture_id]
            size = int(fixture["cycle_size"])
            rows = tuple(fixture["rows"])
            seeded = state_from_active(fixture["formation_active_loci"], size)
            baseline = state_from_active(fixture["comparator_active_loci"], size)
            anchor = int(fixture["formation_anchor"])
            with self.subTest(fixture=fixture_id):
                self.assertEqual(
                    outward_future_values(seeded, rows, anchor, size),
                    (
                        fixture["expected_sham_endpoint"],
                        fixture["expected_breaking_endpoint"],
                    ),
                )
                assessment = assess_layer(
                    seeded,
                    baseline,
                    rows,
                    layer=int(fixture["formation_layer"]),
                    origin=int(fixture["origin"]),
                    cycle_size=size,
                )
                self.assertEqual(assessment.first_role_anchor, anchor)
                self.assertEqual(
                    assessment.first_successor,
                    (anchor, fixture["expected_successor_anchor"]),
                )
                expected_pass = (
                    fixture["expected_sham_endpoint"]
                    != fixture["expected_breaking_endpoint"]
                )
                self.assertIs(assessment.detector_result.passed, expected_pass)

    def test_formation_comparator_fixture_blocks_attribution(self) -> None:
        fixture = self.fixtures["comparator_attribution_failure"]
        size = int(fixture["cycle_size"])
        seeded = state_from_active(fixture["formation_active_loci"], size)
        baseline = state_from_active(fixture["comparator_active_loci"], size)
        self.assertIs(
            role_at(seeded, baseline, int(fixture["formation_anchor"]), size),
            fixture["expected_role_attributed"],
        )

    def test_successor_comparator_contamination_blocks_attribution(self) -> None:
        fixture = self.fixtures["successor_comparator_attribution_failure"]
        size = int(fixture["cycle_size"])
        rows = tuple(fixture["rows"])
        seeded = state_from_active(fixture["formation_active_loci"], size)
        baseline = state_from_active(fixture["comparator_active_loci"], size)
        raw_successor = int(fixture["raw_successor_anchor"])

        next_seeded = step(seeded, rows, size)
        next_baseline = step(baseline, rows, size)
        self.assertTrue(role_at(next_seeded, 0, raw_successor, size))
        self.assertFalse(role_at(next_seeded, next_baseline, raw_successor, size))

        assessment = assess_layer(
            seeded,
            baseline,
            rows,
            layer=int(fixture["formation_layer"]),
            origin=int(fixture["origin"]),
            cycle_size=size,
        )
        self.assertEqual(
            assessment.first_role_anchor,
            fixture["expected_first_role_anchor"],
        )
        self.assertIs(assessment.first_successor, fixture["expected_first_successor"])
        self.assertIs(
            assessment.detector_result.passed,
            fixture["expected_complete_pass"],
        )

    def test_ordered_scan_continues_after_earlier_guard_failure(self) -> None:
        fixture = self.fixtures["ordered_scan_continues_after_guard_failure"]
        size = int(fixture["cycle_size"])
        rows = tuple(fixture["rows"])
        assessment = assess_layer(
            state_from_active(fixture["formation_active_loci"], size),
            state_from_active(fixture["comparator_active_loci"], size),
            rows,
            layer=int(fixture["formation_layer"]),
            origin=int(fixture["origin"]),
            cycle_size=size,
        )
        self.assertEqual(
            assessment.first_role_anchor,
            fixture["expected_first_role_anchor"],
        )
        self.assertEqual(
            assessment.first_successor,
            tuple(fixture["expected_first_successor"]),
        )
        self.assertEqual(
            assessment.first_intervention_eligible,
            tuple(fixture["expected_first_intervention_eligible"]),
        )
        self.assertTrue(assessment.detector_result.passed)
        self.assertEqual(
            assessment.detector_result.anchor,
            fixture["expected_complete_pass_anchor"],
        )
        self.assertEqual(
            assessment.detector_result.successor_anchor,
            fixture["expected_complete_pass_successor_anchor"],
        )
        self.assertEqual(
            (
                assessment.detector_result.sham_future,
                assessment.detector_result.breaking_future,
            ),
            (
                fixture["expected_sham_endpoint"],
                fixture["expected_breaking_endpoint"],
            ),
        )


class DetectorTests(unittest.TestCase):
    def test_role_anchor_mask_matches_direct_predicate_exhaustively_on_C4(self) -> None:
        def direct_role(state: int, baseline: int, anchor: int) -> bool:
            values = tuple(
                (state >> ((anchor + offset) % 4)) & 1
                for offset in (-1, 0, 1, 2)
            )
            return (
                values == (0, 1, 1, 0)
                and not (baseline >> anchor) & 1
                and not (baseline >> ((anchor + 1) % 4)) & 1
            )

        for state in range(1 << 4):
            for baseline in range(1 << 4):
                anchors = role_anchor_mask(state, baseline, 4)
                expected = sum(
                    1 << anchor
                    for anchor in range(4)
                    if direct_role(state, baseline, anchor)
                )
                self.assertEqual(anchors, expected, (state, baseline))

    def test_anchor_schedule_is_cached(self) -> None:
        self.assertIs(ordered_anchors(0, 64), ordered_anchors(0, 64))
        self.assertIs(ordered_anchors(17, 96), ordered_anchors(17, 96))

    def test_no_role_fast_path_does_not_evolve_successor_states(self) -> None:
        with mock.patch.object(
            detector_module,
            "step",
            side_effect=AssertionError("no successor evolution expected"),
        ):
            assessment = assess_layer(
                0,
                0,
                ("000",),
                layer=100,
                origin=0,
                cycle_size=64,
            )
        self.assertIsNone(assessment.first_role_anchor)
        self.assertFalse(assessment.detector_result.passed)

    def test_frozen_pre_wrap_horizon_leaves_two_layer_endpoint_pre_saturation(self) -> None:
        self.assertEqual(FORMATION_HORIZON, 29)
        self.assertEqual(LAST_REQUIRED_LAYER, 31)

    def test_centered_cone_and_anchor_order_are_bidirectional(self) -> None:
        self.assertEqual(ordered_anchors()[:9], (0, 1, 63, 2, 62, 3, 61, 4, 60))
        self.assertTrue(in_bidirectional_cone(63, 0, 1))
        self.assertTrue(in_bidirectional_cone(1, 0, 1))
        self.assertFalse(in_bidirectional_cone(2, 0, 1))
        self.assertEqual(ordered_anchors()[-1], 32)

    def test_role_is_isolated_dyad_with_active_witness_attribution(self) -> None:
        state = state_from_active((10, 11, 30))
        self.assertTrue(role_at(state, 0, 10))
        self.assertFalse(role_at(state, state_from_active((10,)), 10))
        self.assertFalse(role_at(state_from_active((9, 10, 11)), 0, 10))
        self.assertFalse(role_at(state_from_active((10, 11, 12)), 0, 10))

    def test_successor_selection_allows_only_same_then_forward_anchor(self) -> None:
        same = state_from_active((10, 11))
        forward = state_from_active((11, 12))
        predecessor = state_from_active((9, 10))
        self.assertEqual(
            successor_anchor(same, 0, 10, origin=10, next_layer=2),
            10,
        )
        self.assertEqual(
            successor_anchor(forward, 0, 10, origin=10, next_layer=2),
            11,
        )
        self.assertIsNone(
            successor_anchor(predecessor, 0, 10, origin=10, next_layer=2)
        )

    def test_matched_interventions_preserve_count_and_external_state(self) -> None:
        natural = state_from_active((10, 11, 30))
        sham, breaking = matched_intervention_states(natural, 10)
        self.assertEqual(active_loci(sham), (11, 12, 30))
        self.assertEqual(active_loci(breaking), (10, 12, 30))
        natural_bits = set(active_loci(natural))
        for arm in (sham, breaking):
            arm_bits = set(active_loci(arm))
            self.assertEqual(len(natural_bits ^ arm_bits), 2)
            self.assertEqual(len(arm_bits), len(natural_bits))

    def test_nonquiescent_external_guard_is_ineligible(self) -> None:
        state = state_from_active((10, 11, 13))
        with self.assertRaisesRegex(ValueError, "external guard"):
            matched_intervention_states(state, 10)

    def test_supplied_dyad_copy_predecessor_positive_is_detector_development_only(self) -> None:
        supplied_role = state_from_active((10, 11))
        self.assertEqual(
            outward_future_values(supplied_role, COPY_PREDECESSOR_ROWS, 10),
            (1, 0),
        )
        assessment = assess_layer(
            supplied_role,
            0,
            COPY_PREDECESSOR_ROWS,
            layer=1,
            origin=10,
        )
        self.assertEqual(assessment.first_role_anchor, 10)
        self.assertEqual(assessment.first_successor, (10, 11))
        self.assertEqual(assessment.first_intervention_eligible, (10, 11))
        self.assertTrue(assessment.detector_result.passed)
        self.assertEqual(assessment.detector_result.t_proto, 1)
        self.assertEqual(assessment.detector_result.anchor, 10)
        self.assertEqual(assessment.detector_result.successor_anchor, 11)
        self.assertEqual(
            (
                assessment.detector_result.sham_future,
                assessment.detector_result.breaking_future,
            ),
            (1, 0),
        )

    def test_diagnostics_stop_at_first_role_without_succession(self) -> None:
        assessment = assess_layer(
            state_from_active((10, 11)),
            0,
            (),
            layer=1,
            origin=10,
        )
        self.assertEqual(assessment.first_role_anchor, 10)
        self.assertIsNone(assessment.first_successor)
        self.assertIsNone(assessment.first_intervention_eligible)
        self.assertFalse(assessment.detector_result.passed)

    def test_succession_without_outward_difference_is_not_complete_pass(self) -> None:
        assessment = assess_layer(
            state_from_active((10, 11)),
            0,
            COPY_SELF_ROWS,
            layer=1,
            origin=10,
        )
        self.assertEqual(assessment.first_successor, (10, 10))
        self.assertEqual(assessment.first_intervention_eligible, (10, 10))
        self.assertFalse(assessment.detector_result.passed)

    def test_guard_failure_is_diagnostic_successor_but_not_eligibility(self) -> None:
        assessment = assess_layer(
            state_from_active((10, 11, 13)),
            0,
            COPY_PREDECESSOR_ROWS,
            layer=1,
            origin=10,
        )
        self.assertEqual(assessment.first_role_anchor, 10)
        self.assertEqual(assessment.first_successor, (10, 11))
        self.assertIsNone(assessment.first_intervention_eligible)
        self.assertFalse(assessment.detector_result.passed)

    def test_comparator_active_witness_blocks_all_stages(self) -> None:
        assessment = assess_layer(
            state_from_active((10, 11)),
            state_from_active((10,)),
            COPY_PREDECESSOR_ROWS,
            layer=1,
            origin=10,
        )
        self.assertIsNone(assessment.first_role_anchor)
        self.assertIsNone(assessment.first_successor)
        self.assertFalse(assessment.detector_result.passed)

    def test_role_active_witnesses_must_both_be_in_centered_cone(self) -> None:
        role = state_from_active((62, 63))
        outside = assess_layer(role, 0, (), layer=1, origin=0)
        boundary = assess_layer(role, 0, (), layer=2, origin=0)
        self.assertIsNone(outside.first_role_anchor)
        self.assertEqual(boundary.first_role_anchor, 62)

    def test_supplied_positive_embeds_on_all_registered_cycle_sizes(self) -> None:
        for cycle_size in (64, 96, 128):
            anchor = cycle_size - 1
            supplied_role = state_from_active((anchor, anchor + 1), cycle_size)
            with self.subTest(cycle_size=cycle_size):
                assessment = assess_layer(
                    supplied_role,
                    0,
                    COPY_PREDECESSOR_ROWS,
                    layer=1,
                    origin=anchor,
                    cycle_size=cycle_size,
                )
                self.assertTrue(assessment.detector_result.passed)
                self.assertEqual(assessment.detector_result.anchor, anchor)
                self.assertEqual(assessment.detector_result.successor_anchor, 0)
                self.assertEqual(
                    (
                        assessment.detector_result.sham_future,
                        assessment.detector_result.breaking_future,
                    ),
                    (1, 0),
                )


if __name__ == "__main__":
    unittest.main()
