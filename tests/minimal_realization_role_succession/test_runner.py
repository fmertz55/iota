from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from src.minimal_realization_role_succession.detector import (
    DetectorResult,
    LayerAssessment,
)
from src.minimal_realization_role_succession.manifest import (
    build_candidate,
    compile_candidates,
)
from src.minimal_realization_role_succession.protocol import (
    EMBEDDING_CYCLE_SIZES,
    FORMATION_HORIZON,
    MAX_LAYERS_PER_CANDIDATE,
    PARENT_EXACT_RESULT_REF,
    PARENT_EXACT_RESULT_SHA256,
)
from src.minimal_realization_role_succession.runner import (
    CandidateEvaluation,
    ExactOrbitOutcome,
    RoleSuccessionRunError,
    SizeControlOutcome,
    build_result_ledger,
    run_development_search,
    synthetic_candidate_evaluation,
    trace_joint_orbit,
    validate_result_ledger,
    write_result_ledger,
    _excluded_candidate_record,
    _signed_offset,
    _validate_size_controls,
)


def no_pass_assessment() -> LayerAssessment:
    return LayerAssessment(
        None,
        None,
        None,
        DetectorResult(False, None, None, None, None, None),
    )


def recurrence(rows: tuple[str, ...]) -> CandidateEvaluation:
    outcome = ExactOrbitOutcome(
        "recurrence_excluded_on_fixed_orbit",
        None,
        33,
        None,
        None,
        None,
        None,
        (32, 33, 1, 0, 0),
        "a" * 64,
    )
    return synthetic_candidate_evaluation(rows, outcome)


def resource(rows: tuple[str, ...]) -> CandidateEvaluation:
    outcome = ExactOrbitOutcome(
        "resource_censored_before_recurrence",
        None,
        MAX_LAYERS_PER_CANDIDATE,
        None,
        None,
        None,
        None,
        None,
        "b" * 64,
    )
    return synthetic_candidate_evaluation(rows, outcome)


def exact_pass(rows: tuple[str, ...], layer: int) -> CandidateEvaluation:
    witness = (layer, 0, 1, 0, 1, 3, 0)
    outcome = ExactOrbitOutcome(
        "exact_pass_on_fixed_orbit",
        layer,
        layer,
        (1, 0),
        (layer, 0, 1),
        (layer, 0, 1),
        witness,
        None,
        "c" * 64,
    )
    required = layer <= FORMATION_HORIZON
    controls = tuple(
        SizeControlOutcome(
            cycle_size,
            layer,
            (layer, 0, 1, 0, 1),
            True,
            required,
            True if required else None,
        )
        for cycle_size in EMBEDDING_CYCLE_SIZES
    )
    return synthetic_candidate_evaluation(rows, outcome, size_controls=controls)


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


class OutcomeBlindRecordContractTests(unittest.TestCase):
    def test_signed_offset_boundaries_use_positive_even_antipode(self) -> None:
        for cycle_size in (64, 96, 128):
            origin = 7
            half = cycle_size // 2
            with self.subTest(cycle_size=cycle_size):
                self.assertEqual(_signed_offset(origin, origin, cycle_size), 0)
                self.assertEqual(
                    _signed_offset((origin + half) % cycle_size, origin, cycle_size),
                    half,
                )
                self.assertEqual(
                    _signed_offset((origin + half + 1) % cycle_size, origin, cycle_size),
                    -(half - 1),
                )
                self.assertEqual(
                    _signed_offset((origin - 1) % cycle_size, origin, cycle_size),
                    -1,
                )

    def test_zero_law_record_is_analytic_and_has_no_dynamic_classification(self) -> None:
        record = _excluded_candidate_record(build_candidate(()))
        self.assertEqual(record["candidate_id"], "MIR-RS-P2-L0-NONE")
        self.assertEqual(record["evaluation_status"], "analytically_excluded")
        self.assertEqual(record["bounded_status"], "not_applicable")
        self.assertFalse(record["pass_by_H29"])
        self.assertIsNone(record["pre_wrap_classification"])
        self.assertEqual(record["cross_size_controls"], [])
        self.assertFalse(record["localized_interpretation"])
        for key in (
            "t_proto_exact",
            "last_assessed_layer",
            "first_role",
            "first_successor",
            "first_intervention_eligible",
            "first_complete_pass",
            "recurrence",
            "resource_limit",
            "trace_sha256",
            "transition_symmetry_audit",
        ):
            with self.subTest(key=key):
                self.assertIsNone(record[key])


def size_control_record(*, pre_wrap: bool = True) -> dict[str, object]:
    layer = 4 if pre_wrap else FORMATION_HORIZON + 1
    compact = {
        "layer": layer,
        "signed_anchor": -1,
        "successor_displacement": 1,
        "sham_future": 0,
        "breaking_future": 1,
    }
    return {
        "evaluation_status": "exact_pass_on_fixed_orbit",
        "pass_by_H29": pre_wrap,
        "t_proto_exact": layer,
        "first_complete_pass": dict(compact),
        "cross_size_controls": [
            {
                "cycle_size": cycle_size,
                "evaluated_through_layer": layer,
                "first_complete_pass": dict(compact),
                "matches_primary_witness": True,
                "pre_wrap_agreement_required": pre_wrap,
                "exact_pre_wrap_agreement": True if pre_wrap else None,
            }
            for cycle_size in EMBEDDING_CYCLE_SIZES
        ],
    }


class CrossSizeControlValidatorTests(unittest.TestCase):
    def assert_size_control_rejected(self, record: dict[str, object]) -> None:
        with self.assertRaises(RoleSuccessionRunError):
            _validate_size_controls(record)

    def test_exact_pre_wrap_control_tamper_matrix_is_rejected_for_both_sizes(self) -> None:
        witness_mutations = {
            "layer": lambda witness: witness.__setitem__("layer", 3),
            "signed_anchor": lambda witness: witness.__setitem__("signed_anchor", 0),
            "successor_displacement": lambda witness: witness.__setitem__(
                "successor_displacement", 0
            ),
            "endpoint_pair": lambda witness: witness.update(
                {"sham_future": 1, "breaking_future": 0}
            ),
        }
        for control_index, cycle_size in enumerate(EMBEDDING_CYCLE_SIZES):
            for field, mutate in witness_mutations.items():
                record = size_control_record()
                witness = record["cross_size_controls"][control_index][
                    "first_complete_pass"
                ]
                mutate(witness)
                with self.subTest(cycle_size=cycle_size, field=field):
                    self.assert_size_control_rejected(record)

    def test_control_allocation_and_flags_tamper_matrix_is_rejected(self) -> None:
        mutations = {
            "missing_C128": lambda record: record["cross_size_controls"].pop(),
            "duplicate_C96": lambda record: record["cross_size_controls"][1].update(
                {"cycle_size": 96}
            ),
            "wrong_horizon": lambda record: record["cross_size_controls"][0].update(
                {"evaluated_through_layer": 3}
            ),
            "wrong_match_flag": lambda record: record["cross_size_controls"][0].update(
                {"matches_primary_witness": False}
            ),
            "wrong_required_flag": lambda record: record["cross_size_controls"][0].update(
                {"pre_wrap_agreement_required": False}
            ),
            "wrong_exact_flag": lambda record: record["cross_size_controls"][0].update(
                {"exact_pre_wrap_agreement": False}
            ),
            "missing_witness": lambda record: record["cross_size_controls"][0].update(
                {"first_complete_pass": None}
            ),
        }
        for label, mutate in mutations.items():
            record = size_control_record()
            mutate(record)
            with self.subTest(tamper=label):
                self.assert_size_control_rejected(record)

    def test_post_wrap_passer_still_requires_both_diagnostic_controls(self) -> None:
        record = size_control_record(pre_wrap=False)
        _validate_size_controls(record)
        record["cross_size_controls"].pop()
        self.assert_size_control_rejected(record)

    def test_post_wrap_mismatch_is_diagnostic_and_cannot_claim_exact_agreement(self) -> None:
        record = size_control_record(pre_wrap=False)
        control = record["cross_size_controls"][0]
        control["first_complete_pass"] = None
        control["matches_primary_witness"] = False
        _validate_size_controls(record)
        control["exact_pre_wrap_agreement"] = False
        self.assert_size_control_rejected(record)

    def test_nonpass_cannot_carry_conditional_controls(self) -> None:
        record = size_control_record()
        record["evaluation_status"] = "recurrence_excluded_on_fixed_orbit"
        self.assert_size_control_rejected(record)


class StreamingOrbitTests(unittest.TestCase):
    def test_repeat_before_saturation_does_not_close_detector_state(self) -> None:
        outcome = trace_joint_orbit(
            (5, 7),
            lambda state: state,
            lambda _state, _layer: no_pass_assessment(),
            saturation_layer=3,
            max_layers=8,
            trace_domain=b"synthetic-pre-saturation",
            cycle_size=8,
        )
        self.assertEqual(outcome.status, "recurrence_excluded_on_fixed_orbit")
        self.assertEqual(outcome.recurrence[:3], (3, 4, 1))

    def test_joint_state_not_seeded_state_alone_controls_recurrence(self) -> None:
        def transition(state: tuple[int, int]) -> tuple[int, int]:
            return state[0], (state[1] + 1) % 4

        outcome = trace_joint_orbit(
            (2, 0),
            transition,
            lambda _state, _layer: no_pass_assessment(),
            saturation_layer=1,
            max_layers=20,
            trace_domain=b"synthetic-joint-recurrence",
            cycle_size=8,
        )
        self.assertEqual(outcome.status, "recurrence_excluded_on_fixed_orbit")
        self.assertEqual(outcome.recurrence[2], 4)

    def test_detector_pass_precedes_same_layer_recurrence(self) -> None:
        def assessor(_state: tuple[int, int], layer: int) -> LayerAssessment:
            if layer == 2:
                return LayerAssessment(
                    0,
                    (0, 1),
                    (0, 1),
                    DetectorResult(True, 2, 0, 1, 0, 1),
                )
            return no_pass_assessment()

        outcome = trace_joint_orbit(
            (3, 0),
            lambda state: state,
            assessor,
            saturation_layer=1,
            max_layers=5,
            trace_domain=b"synthetic-pass-before-repeat",
            cycle_size=8,
        )
        self.assertEqual(outcome.status, "exact_pass_on_fixed_orbit")
        self.assertEqual(outcome.t_proto, 2)
        self.assertIsNone(outcome.recurrence)


class FamilyOrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidates = compile_candidates()

    def test_all_255_nonempty_candidates_run_without_shell_stop(self) -> None:
        calls: list[tuple[str, ...]] = []

        def evaluator(_candidate, rows):
            calls.append(rows)
            return recurrence(rows)

        search = run_development_search(self.candidates, evaluator)
        self.assertEqual(len(calls), 255)
        self.assertEqual(len(search["candidate_results"]), 256)
        self.assertTrue(search["all_nonempty_candidates_processed"])
        self.assertFalse(search["shell_stopping_used"])
        self.assertEqual(
            search["exact_family_conclusion"],
            "all_dynamic_candidates_recurrence_excluded",
        )

    def test_pre_wrap_and_post_wrap_passes_are_distinguished(self) -> None:
        first_dynamic = self.candidates[1]["candidate_id"]
        second_dynamic = self.candidates[2]["candidate_id"]

        def evaluator(candidate, rows):
            if candidate["candidate_id"] == first_dynamic:
                return exact_pass(rows, FORMATION_HORIZON)
            if candidate["candidate_id"] == second_dynamic:
                return exact_pass(rows, FORMATION_HORIZON + 1)
            return recurrence(rows)

        search = run_development_search(self.candidates, evaluator)
        by_id = {row["candidate_id"]: row for row in search["candidate_results"]}
        self.assertEqual(by_id[first_dynamic]["bounded_status"], "pass_by_H29")
        self.assertTrue(by_id[first_dynamic]["localized_interpretation"])
        self.assertEqual(
            by_id[second_dynamic]["bounded_status"],
            "right_censored_T_proto_gt_29",
        )
        self.assertIn(second_dynamic, search["finite_ring_exposed_candidate_ids"])

    def test_lower_shell_resource_censor_blocks_minimum_law_ranking(self) -> None:
        lower = self.candidates[1]["candidate_id"]
        passer = next(
            candidate
            for candidate in self.candidates
            if len(candidate["laws"]) == 2
        )["candidate_id"]

        def evaluator(candidate, rows):
            if candidate["candidate_id"] == lower:
                return resource(rows)
            if candidate["candidate_id"] == passer:
                return exact_pass(rows, 12)
            return recurrence(rows)

        search = run_development_search(self.candidates, evaluator)
        self.assertEqual(
            search["minimum_law_ranking_status"],
            "blocked_by_lower_shell_resource_censoring",
        )
        self.assertEqual(search["minimum_law_winner_candidate_ids"], [])
        self.assertEqual(search["exact_family_conclusion"], "one_or_more_exact_passes")

    def test_pre_wrap_passer_requires_both_exact_size_controls(self) -> None:
        rows = ("000",)
        evaluation = exact_pass(rows, 4)
        broken = copy.deepcopy(evaluation)
        controls = list(broken.size_controls)
        controls[0] = SizeControlOutcome(96, 4, None, False, True, False)
        broken = CandidateEvaluation(broken.orbit, broken.symmetry_audit, tuple(controls))
        with self.assertRaisesRegex(RoleSuccessionRunError, "size agreement"):
            run_development_search(
                self.candidates,
                lambda candidate, candidate_rows: broken
                if candidate["candidate_id"] == self.candidates[1]["candidate_id"]
                else recurrence(candidate_rows),
            )

    def test_high_level_search_requires_explicit_evaluator(self) -> None:
        with self.assertRaises(TypeError):
            run_development_search(self.candidates)  # type: ignore[call-arg]


class LedgerWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidates = compile_candidates()
        self.ledger = build_result_ledger(
            candidates=self.candidates,
            evaluator=lambda _candidate, rows: recurrence(rows),
            **bindings(),
        )

    def test_synthetic_full_ledger_validates(self) -> None:
        validate_result_ledger(self.ledger, self.candidates)

    def test_summary_tamper_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["pre_wrap_stage_counts"]["successor"] = 1
        with self.assertRaises(RoleSuccessionRunError):
            validate_result_ledger(mutated, self.candidates)

    def test_nested_pass_and_size_control_records_validate(self) -> None:
        passer_id = self.candidates[1]["candidate_id"]
        ledger = build_result_ledger(
            candidates=self.candidates,
            evaluator=lambda candidate, rows: exact_pass(rows, 7)
            if candidate["candidate_id"] == passer_id
            else recurrence(rows),
            **bindings(),
        )
        validate_result_ledger(ledger, self.candidates)

        malformed = copy.deepcopy(ledger)
        malformed["candidate_results"][1]["cross_size_controls"][0][
            "evaluated_through_layer"
        ] = 6
        with self.assertRaisesRegex(RoleSuccessionRunError, "cross-size"):
            validate_result_ledger(malformed, self.candidates)

    def test_nested_state_chronology_and_strict_integer_tamper_are_rejected(self) -> None:
        malformed = copy.deepcopy(self.ledger)
        malformed["candidate_results"][1]["atomic_n_l"] = True
        with self.assertRaises(RoleSuccessionRunError):
            validate_result_ledger(malformed, self.candidates)

        malformed = copy.deepcopy(self.ledger)
        malformed["candidate_results"][1]["recurrence"]["checkpoint_state"][
            "seeded_state_hex"
        ] = "g" * 16
        malformed["candidate_results"][1]["recurrence"]["repeat_state"][
            "seeded_state_hex"
        ] = "g" * 16
        with self.assertRaisesRegex(RoleSuccessionRunError, "state encoding"):
            validate_result_ledger(malformed, self.candidates)

    def test_top_level_resource_metadata_is_exact(self) -> None:
        malformed = copy.deepcopy(self.ledger)
        malformed["primitive_capacity"]["relation_incidence_reads_per_site"] = 1
        with self.assertRaisesRegex(RoleSuccessionRunError, "primitive capacity"):
            validate_result_ledger(malformed, self.candidates)

    def test_writer_requires_verified_open_manifest_and_never_clobbers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-result.json"
            with self.assertRaisesRegex(RoleSuccessionRunError, "verified open"):
                write_result_ledger(
                    path,
                    self.ledger,
                    open_manifest_verified=False,
                )
            self.assertFalse(path.exists())
            write_result_ledger(path, self.ledger, open_manifest_verified=True)
            self.assertTrue(path.exists())
            with self.assertRaisesRegex(RoleSuccessionRunError, "overwrite"):
                write_result_ledger(path, self.ledger, open_manifest_verified=True)

    def test_writer_rejects_stale_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-result.json"
            path.with_name(path.name + ".tmp").write_text("stale", encoding="ascii")
            with self.assertRaisesRegex(RoleSuccessionRunError, "stale temporary"):
                write_result_ledger(path, self.ledger, open_manifest_verified=True)


if __name__ == "__main__":
    unittest.main()
