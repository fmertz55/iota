import hashlib
import inspect
import unittest

from src.minimal_realization.detector import DetectorResult
from src.minimal_realization.dynamics import state_from_active, translate_state
from src.minimal_realization_orbit.engine import (
    ExactOrbitOutcome,
    LayerAssessment,
    OrbitRunError,
    _update_trace_digest,
    evaluate_candidate_exact_orbit,
    evaluate_detector_layer,
    trace_joint_orbit,
)


def no_pass(_: tuple[int, int], __: int) -> LayerAssessment:
    return LayerAssessment(
        None,
        None,
        None,
        DetectorResult(False, None, None, None, None, None),
    )


class TraceJointOrbitTests(unittest.TestCase):
    def test_pre_saturation_repeats_do_not_close(self) -> None:
        outcome = trace_joint_orbit(
            (0, 0),
            lambda state: state,
            no_pass,
            saturation_layer=3,
            max_layers=10,
            trace_domain=b"synthetic-fixed",
        )
        self.assertEqual(outcome.status, "recurrence_excluded_on_fixed_orbit")
        self.assertEqual(outcome.recurrence[:3], (3, 4, 1))
        self.assertEqual(outcome.last_evaluated_layer, 4)

    def test_joint_not_seeded_only_recurrence_is_required(self) -> None:
        def transition(state: tuple[int, int]) -> tuple[int, int]:
            return state[0], (state[1] + 1) % 4

        outcome = trace_joint_orbit(
            (0, 0),
            transition,
            no_pass,
            saturation_layer=1,
            max_layers=20,
            trace_domain=b"synthetic-joint",
        )
        self.assertEqual(outcome.status, "recurrence_excluded_on_fixed_orbit")
        self.assertEqual(outcome.recurrence[2], 4)
        self.assertGreater(outcome.recurrence[1], 2)

    def test_pass_is_checked_before_same_layer_repeat(self) -> None:
        def assess(_: tuple[int, int], layer: int) -> LayerAssessment:
            if layer == 2:
                return LayerAssessment(
                    0,
                    (0, 0),
                    (0, 0),
                    DetectorResult(True, 2, 0, 0, 0, 1),
                )
            return no_pass((0, 0), layer)

        outcome = trace_joint_orbit(
            (0, 0),
            lambda state: state,
            assess,
            saturation_layer=1,
            max_layers=10,
            trace_domain=b"synthetic-pass-before-repeat",
        )
        self.assertEqual(outcome.status, "exact_pass_on_fixed_orbit")
        self.assertEqual(outcome.t_proto, 2)
        self.assertIsNone(outcome.recurrence)

    def test_resource_cap_is_incomplete(self) -> None:
        outcome = trace_joint_orbit(
            (0, 0),
            lambda state: (state[0], state[1] + 1),
            no_pass,
            saturation_layer=2,
            max_layers=5,
            trace_domain=b"synthetic-cap",
        )
        self.assertEqual(outcome.status, "resource_censored_before_recurrence")
        self.assertEqual(outcome.last_evaluated_layer, 5)
        self.assertIsNone(outcome.recurrence)

    def test_table_repeat_without_checkpoint_match_remains_resource_censored(self) -> None:
        def transition(state: tuple[int, int]) -> tuple[int, int]:
            seeded, baseline = state
            return ({0: 1, 1: 2, 2: 3, 3: 1}[seeded], baseline)

        outcome = trace_joint_orbit(
            (0, 0),
            transition,
            no_pass,
            saturation_layer=1,
            max_layers=5,
            trace_domain=b"synthetic-table-repeat-before-checkpoint",
        )
        self.assertEqual(outcome.status, "resource_censored_before_recurrence")
        self.assertEqual(outcome.last_evaluated_layer, 5)

    def test_first_stage_witnesses_are_retained(self) -> None:
        def assess(_: tuple[int, int], layer: int) -> LayerAssessment:
            if layer == 1:
                return LayerAssessment(
                    3,
                    None,
                    None,
                    DetectorResult(False, None, None, None, None, None),
                )
            if layer == 2:
                return LayerAssessment(
                    4,
                    (4, 5),
                    None,
                    DetectorResult(False, None, None, None, None, None),
                )
            return no_pass((0, 0), layer)

        outcome = trace_joint_orbit(
            (0, 0),
            lambda state: state,
            assess,
            saturation_layer=3,
            max_layers=10,
            trace_domain=b"synthetic-stages",
        )
        self.assertEqual(outcome.first_role, (1, 3))
        self.assertEqual(outcome.first_successor, (2, 4, 5))

    def test_invalid_resource_cap_is_rejected(self) -> None:
        with self.assertRaises(OrbitRunError):
            trace_joint_orbit(
                (0, 0),
                lambda state: state,
                no_pass,
                saturation_layer=3,
                max_layers=2,
                trace_domain=b"synthetic-invalid",
            )

    def test_empty_trace_domain_is_rejected(self) -> None:
        with self.assertRaises(OrbitRunError):
            trace_joint_orbit(
                (0, 0),
                lambda state: state,
                no_pass,
                saturation_layer=1,
                max_layers=2,
                trace_domain=b"",
            )

    def test_transition_state_must_remain_unsigned_64_bit_pair(self) -> None:
        with self.assertRaises(ValueError):
            trace_joint_orbit(
                (0, 0),
                lambda state: (1 << 64, state[1]),
                no_pass,
                saturation_layer=1,
                max_layers=2,
                trace_domain=b"synthetic-invalid-state",
            )


class DetectorLayerTests(unittest.TestCase):
    def test_disclosed_copy_predecessor_fixture_passes(self) -> None:
        assessment = evaluate_detector_layer(
            state_from_active([0, 1]),
            0,
            ("01", "11"),
            layer=1,
            origin=0,
        )
        self.assertTrue(assessment.detector_result.passed)
        self.assertEqual(assessment.detector_result.anchor, 0)
        self.assertEqual(assessment.detector_result.successor_anchor, 1)

    def test_singleton_has_no_role(self) -> None:
        assessment = evaluate_detector_layer(
            state_from_active([0]),
            0,
            ("01", "11"),
            layer=1,
            origin=0,
        )
        self.assertFalse(assessment.detector_result.passed)
        self.assertIsNone(assessment.first_role_anchor)

    def test_exact_layer_assessment_commutes_with_cycle_translation(self) -> None:
        seeded = state_from_active([0, 1])
        baseline = 0
        rows = ("01", "11")
        reference = evaluate_detector_layer(
            seeded,
            baseline,
            rows,
            layer=63,
            origin=0,
        )
        for offset in (1, 17, 47):
            shifted = evaluate_detector_layer(
                translate_state(seeded, offset),
                translate_state(baseline, offset),
                rows,
                layer=63,
                origin=offset,
            )
            self.assertEqual(
                shifted.first_role_anchor,
                (reference.first_role_anchor + offset) % 64,
            )
            self.assertEqual(
                shifted.first_successor,
                tuple((value + offset) % 64 for value in reference.first_successor),
            )
            self.assertEqual(
                shifted.first_intervention_eligible,
                tuple(
                    (value + offset) % 64
                    for value in reference.first_intervention_eligible
                ),
            )
            self.assertEqual(
                shifted.detector_result.anchor,
                (reference.detector_result.anchor + offset) % 64,
            )
            self.assertEqual(
                shifted.detector_result.successor_anchor,
                (reference.detector_result.successor_anchor + offset) % 64,
            )
            self.assertEqual(
                (
                    shifted.detector_result.passed,
                    shifted.detector_result.t_proto,
                    shifted.detector_result.sham_future,
                    shifted.detector_result.breaking_future,
                ),
                (
                    reference.detector_result.passed,
                    reference.detector_result.t_proto,
                    reference.detector_result.sham_future,
                    reference.detector_result.breaking_future,
                ),
            )

    def test_large_decimal_layer_digest_is_supported(self) -> None:
        left = hashlib.sha256()
        right = hashlib.sha256()
        _update_trace_digest(left, 10**30, (1, 2))
        _update_trace_digest(right, 10**30 + 1, (1, 2))
        self.assertNotEqual(left.hexdigest(), right.hexdigest())

    def test_production_evaluator_has_no_resource_override(self) -> None:
        parameters = inspect.signature(evaluate_candidate_exact_orbit).parameters
        self.assertEqual(set(parameters), {"rows", "trace_domain"})


if __name__ == "__main__":
    unittest.main()
