from __future__ import annotations

import copy
import inspect
import unittest
from unittest import mock

from src.minimal_realization_role_succession.manifest import compile_candidates
from src.minimal_realization_role_succession.detector import assess_layer
from src.minimal_realization_role_succession.dynamics import state_from_active, step
from src.minimal_realization_role_succession.protocol import (
    EMBEDDING_CYCLE_SIZES,
    FORMATION_HORIZON,
    MAX_LAYERS_PER_CANDIDATE,
    PARENT_EXACT_RESULT_REF,
    PARENT_EXACT_RESULT_SHA256,
)
from src.minimal_realization_role_succession.runner import (
    ExactOrbitOutcome,
    build_result_ledger,
    synthetic_candidate_evaluation,
)
from src.minimal_realization_role_succession import verifier


SIGNATURES = tuple(f"{value:03b}" for value in range(8))


def rows_for_rule(rule_number: int) -> tuple[str, ...]:
    return tuple(
        signature
        for index, signature in enumerate(SIGNATURES)
        if rule_number & (1 << index)
    )


def production_assessment_tuple(
    seeded: int,
    baseline: int,
    rows: tuple[str, ...],
    cycle_size: int,
) -> tuple[object, ...]:
    assessment = assess_layer(
        seeded,
        baseline,
        rows,
        layer=cycle_size // 2,
        origin=0,
        cycle_size=cycle_size,
    )
    result = assessment.detector_result
    return (
        assessment.first_role_anchor,
        assessment.first_successor,
        assessment.first_intervention_eligible,
        result.passed,
        result.t_proto,
        result.anchor,
        result.successor_anchor,
        result.sham_future,
        result.breaking_future,
    )


def independent_assessment_tuple(
    seeded: int,
    baseline: int,
    rows: tuple[str, ...],
    cycle_size: int,
) -> tuple[object, ...]:
    assessment = verifier._independent_assessment(
        seeded,
        baseline,
        rows,
        cycle_size // 2,
        origin=0,
        cycle_size=cycle_size,
    )
    role = assessment["first_role"]
    successor = assessment["first_successor"]
    eligible = assessment["first_intervention_eligible"]
    passed = assessment["first_complete_pass"]
    return (
        None if role is None else role["anchor"],
        None
        if successor is None
        else (successor["anchor"], successor["successor_anchor"]),
        None
        if eligible is None
        else (eligible["anchor"], eligible["successor_anchor"]),
        passed is not None,
        None if passed is None else passed["layer"],
        None if passed is None else passed["anchor"],
        None if passed is None else passed["successor_anchor"],
        None if passed is None else passed["sham_future"],
        None if passed is None else passed["breaking_future"],
    )


def recurrence(rows: tuple[str, ...]):
    return synthetic_candidate_evaluation(
        rows,
        ExactOrbitOutcome(
            "recurrence_excluded_on_fixed_orbit",
            None,
            33,
            None,
            None,
            None,
            None,
            (32, 33, 1, 0, 0),
            "a" * 64,
        ),
    )


def bindings() -> dict[str, dict[str, str]]:
    names = (
        "open_manifest_binding",
        "outcome_seal_binding",
        "candidate_manifest_binding",
        "result_schema_binding",
    )
    result = {
        name: {"path": f"synthetic/{name}.json", "sha256": f"{index:x}" * 64}
        for index, name in enumerate(names, start=1)
    }
    result["parent_exact_result_binding"] = {
        "path": PARENT_EXACT_RESULT_REF,
        "sha256": PARENT_EXACT_RESULT_SHA256,
    }
    return result


class IndependentPrimitiveTests(unittest.TestCase):
    def test_anf_transition_matches_production_all_C4_states_and_rules(self) -> None:
        for rule_number in range(256):
            rows = rows_for_rule(rule_number)
            for state in range(1 << 4):
                self.assertEqual(
                    verifier._transition(state, rows, 4),
                    step(state, rows, 4),
                    (rule_number, state),
                )

    def test_anf_transition_matches_large_synthetic_registered_sizes(self) -> None:
        for cycle_size in (64, 96, 128):
            state = state_from_active(
                (2, 3, 7, 19, cycle_size // 2, cycle_size - 2),
                cycle_size,
            )
            for rule_number in range(256):
                rows = rows_for_rule(rule_number)
                self.assertEqual(
                    verifier._transition(state, rows, cycle_size),
                    step(state, rows, cycle_size),
                    (cycle_size, rule_number),
                )

    def test_independent_detector_matches_production_exhaustively_on_C4(self) -> None:
        for rule_number in range(256):
            rows = rows_for_rule(rule_number)
            for seeded in range(1 << 4):
                for baseline in range(1 << 4):
                    self.assertEqual(
                        independent_assessment_tuple(seeded, baseline, rows, 4),
                        production_assessment_tuple(seeded, baseline, rows, 4),
                        (rule_number, seeded, baseline),
                    )

    def test_transition_is_bit_parallel_and_compilation_is_cached(self) -> None:
        source = inspect.getsource(verifier._transition)
        self.assertNotIn("range(cycle_size)", source)
        self.assertIn("_anf_terms", source)
        rows = ("001", "011", "101")
        self.assertIs(verifier._anf_terms(rows), verifier._anf_terms(rows))

    def test_no_role_fast_path_avoids_natural_successor_evolution(self) -> None:
        with mock.patch.object(
            verifier,
            "_transition",
            side_effect=AssertionError("no successor evolution expected"),
        ):
            assessment = verifier._independent_assessment(
                0,
                0,
                ("000",),
                100,
                origin=0,
                cycle_size=64,
            )
        self.assertIsNone(assessment["first_role"])

    def test_signed_offset_boundaries_match_canonical_positive_antipode(self) -> None:
        for cycle_size in (64, 96, 128):
            half = cycle_size // 2
            with self.subTest(cycle_size=cycle_size):
                self.assertEqual(verifier._signed_offset(0, 0, cycle_size), 0)
                self.assertEqual(
                    verifier._signed_offset(half, 0, cycle_size),
                    half,
                )
                self.assertEqual(
                    verifier._signed_offset(half + 1, 0, cycle_size),
                    -(half - 1),
                )
                self.assertEqual(
                    verifier._signed_offset(cycle_size - 1, 0, cycle_size),
                    -1,
                )

    def test_transition_uses_predecessor_self_successor_order(self) -> None:
        state = (1 << 0) | (1 << 2)
        # At locus 1 the neighborhood is 101, and no other locus has 101.
        self.assertEqual(verifier._transition(state, ("101",), 8), 1 << 1)

    def test_disclosed_supplied_dyad_reaches_all_detector_stages(self) -> None:
        seeded = (1 << 0) | (1 << 1)
        rows = ("100", "101", "110", "111")
        assessment = verifier._independent_assessment(
            seeded,
            0,
            rows,
            1,
            origin=0,
            cycle_size=64,
        )
        self.assertIsNotNone(assessment["first_role"])
        self.assertIsNotNone(assessment["first_successor"])
        self.assertIsNotNone(assessment["first_intervention_eligible"])
        self.assertIsNotNone(assessment["first_complete_pass"])

    def test_comparator_attribution_failure_blocks_role(self) -> None:
        seeded = (1 << 0) | (1 << 1)
        assessment = verifier._independent_assessment(
            seeded,
            1 << 0,
            ("100", "101", "110", "111"),
            1,
            origin=0,
            cycle_size=64,
        )
        self.assertIsNone(assessment["first_role"])

    def test_verifier_has_no_production_transition_detector_or_runner_import(self) -> None:
        source = inspect.getsource(verifier)
        self.assertNotIn("from .runner", source)
        self.assertNotIn("from .dynamics", source)
        self.assertNotIn("from .detector", source)
        self.assertNotIn("evaluate_candidate_exact_orbit", source)
        self.assertNotIn("run_development_search", source)


class IndependentReplayTests(unittest.TestCase):
    candidate = {"candidate_id": "SYNTHETIC", "laws": ["synthetic"]}
    rows = ("000",)

    @staticmethod
    def fake_transition(state: int, _rows: tuple[str, ...], _size: int) -> int:
        if state == 0:
            return 0
        return {1: 2, 2: 3, 3: 4, 4: 5, 5: 4}[state]

    @staticmethod
    def no_stages(*_args, **_kwargs):
        return {
            "first_role": None,
            "first_successor": None,
            "first_intervention_eligible": None,
            "first_complete_pass": None,
        }

    def digest(self, last_layer: int) -> str:
        seeded = 1
        baseline = 0
        digest = verifier._new_digest(self.candidate)
        verifier._update_digest(digest, 0, seeded, baseline)
        for layer in range(1, last_layer + 1):
            seeded = self.fake_transition(seeded, self.rows, 64)
            baseline = self.fake_transition(baseline, self.rows, 64)
            verifier._update_digest(digest, layer, seeded, baseline)
        return digest.hexdigest()

    def record(self) -> dict[str, object]:
        state = {
            "seeded_state_hex": "0000000000000004",
            "baseline_state_hex": "0000000000000000",
        }
        return {
            "evaluation_status": "recurrence_excluded_on_fixed_orbit",
            "bounded_status": "right_censored_T_proto_gt_29",
            "pass_by_H29": False,
            "t_proto_exact": None,
            "last_assessed_layer": 35,
            "first_role": None,
            "first_successor": None,
            "first_intervention_eligible": None,
            "first_complete_pass": None,
            "pre_wrap_classification": {
                "formation_horizon": FORMATION_HORIZON,
                "role_by_H29": False,
                "successor_by_H29": False,
                "intervention_eligible_by_H29": False,
                "pass_by_H29": False,
                "first_role": None,
                "first_successor": None,
                "first_intervention_eligible": None,
                "first_complete_pass": None,
            },
            "recurrence": {
                "cone_saturation_layer": 32,
                "checkpoint_layer": 33,
                "repeat_layer": 35,
                "period": 2,
                "checkpoint_state": dict(state),
                "repeat_state": dict(state),
                "exact_full_state_equality": True,
            },
            "resource_limit": None,
            "trace_sha256": self.digest(35),
            "transition_symmetry_audit": {
                "translation_offsets": list(range(64)),
                "last_audited_layer": 31,
                "translation_covariance_exact": True,
                "reflection_covariance_exact": True,
                "reflected_production_rows": ["000"],
            },
            "cross_size_controls": [],
            "localized_interpretation": False,
        }

    def test_registered_checkpoint_recurrence_replays(self) -> None:
        record = self.record()
        with mock.patch.object(verifier, "_transition", side_effect=self.fake_transition), mock.patch.object(
            verifier, "_independent_assessment", side_effect=self.no_stages
        ), mock.patch.object(verifier, "_verify_covariance", return_value=None):
            verifier._verify_dynamic_candidate(record, self.candidate, self.rows)

    def test_trace_tamper_is_rejected(self) -> None:
        record = self.record()
        record["trace_sha256"] = "0" * 64
        with mock.patch.object(verifier, "_transition", side_effect=self.fake_transition), mock.patch.object(
            verifier, "_independent_assessment", side_effect=self.no_stages
        ), mock.patch.object(verifier, "_verify_covariance", return_value=None):
            with self.assertRaisesRegex(
                verifier.IndependentVerificationError,
                "trace digest",
            ):
                verifier._verify_dynamic_candidate(record, self.candidate, self.rows)


class IndependentLedgerOrchestrationTests(unittest.TestCase):
    def test_every_dynamic_candidate_is_replayed(self) -> None:
        candidates = compile_candidates()
        ledger = build_result_ledger(
            candidates=candidates,
            evaluator=lambda _candidate, rows: recurrence(rows),
            **bindings(),
        )
        calls: list[str] = []

        def replay(record, candidate, rows):
            del record, rows
            calls.append(candidate["candidate_id"])

        with mock.patch.object(verifier, "_verify_dynamic_candidate", side_effect=replay):
            verifier.verify_ledger_independently(ledger, candidates)
        self.assertEqual(len(calls), 255)
        self.assertNotIn(candidates[0]["candidate_id"], calls)

    def test_aggregate_tamper_is_rejected_without_real_replay(self) -> None:
        candidates = compile_candidates()
        ledger = build_result_ledger(
            candidates=candidates,
            evaluator=lambda _candidate, rows: recurrence(rows),
            **bindings(),
        )
        mutated = copy.deepcopy(ledger)
        mutated["exact_family_conclusion"] = "one_or_more_exact_passes"
        with mock.patch.object(verifier, "_verify_dynamic_candidate", return_value=None):
            with self.assertRaisesRegex(
                verifier.IndependentVerificationError,
                "aggregate",
            ):
                verifier.verify_ledger_independently(mutated, candidates)


if __name__ == "__main__":
    unittest.main()
