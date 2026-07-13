import hashlib
import inspect
import unittest
from pathlib import Path
from unittest import mock

from src.minimal_realization.dynamics import state_from_active
from src.minimal_realization_orbit.engine import (
    _update_trace_digest,
    evaluate_detector_layer,
)
from src.minimal_realization_orbit.runner import (
    CANDIDATE_MANIFEST_REF,
    PARENT_BOUNDED_RESULT_REF,
    candidate_trace_domain,
    expected_candidate_rows,
    load_canonical_json,
    read_candidate_snapshot,
)
from src.minimal_realization_orbit.runner import OrbitLedgerError
from src.minimal_realization_orbit import verifier


ROOT = Path(__file__).resolve().parents[2]


def production_assessment_as_verifier_record(
    seeded_state: int,
    baseline_state: int,
    rows: tuple[str, ...],
    layer: int,
) -> dict[str, object]:
    assessment = evaluate_detector_layer(
        seeded_state,
        baseline_state,
        rows,
        layer=layer,
        origin=0,
    )
    first_role = (
        None
        if assessment.first_role_anchor is None
        else {"layer": layer, "anchor": assessment.first_role_anchor}
    )
    first_successor = (
        None
        if assessment.first_successor is None
        else {
            "layer": layer,
            "anchor": assessment.first_successor[0],
            "successor_anchor": assessment.first_successor[1],
        }
    )
    first_eligible = (
        None
        if assessment.first_intervention_eligible is None
        else {
            "layer": layer,
            "anchor": assessment.first_intervention_eligible[0],
            "successor_anchor": assessment.first_intervention_eligible[1],
        }
    )
    result = assessment.detector_result
    witness = (
        None
        if not result.passed
        else {
            "layer": layer,
            "anchor": result.anchor,
            "successor_anchor": result.successor_anchor,
            "sham_future": result.sham_future,
            "breaking_future": result.breaking_future,
            "seeded_state_hex": f"{seeded_state:016x}",
            "baseline_state_hex": f"{baseline_state:016x}",
        }
    )
    return {
        "first_role": first_role,
        "first_successor": first_successor,
        "first_intervention_eligible": first_eligible,
        "pass_witness": witness,
    }


class IndependentDetectorTests(unittest.TestCase):
    def test_independent_spelling_matches_disclosed_synthetic_states(self) -> None:
        fixtures = (
            (state_from_active([0]), 0, ("01", "11"), 1),
            (state_from_active([0, 1]), 0, ("01", "11"), 1),
            (0xA55A_A55A_A55A_A55A, 0x0123_4567_89AB_CDEF, ("00", "10"), 17),
            (0x8000_0000_0000_0001, 0xFFFF_0000_FFFF_0000, ("00", "01", "11"), 63),
            (0x5555_5555_5555_5555, 0xAAAA_AAAA_AAAA_AAAA, ("10",), 64),
        )
        for seeded, baseline, rows, layer in fixtures:
            with self.subTest(rows=rows, layer=layer):
                self.assertEqual(
                    verifier._assess_layer(seeded, baseline, rows, layer),
                    production_assessment_as_verifier_record(
                        seeded,
                        baseline,
                        rows,
                        layer,
                    ),
                )

    def test_independent_parent_reproduction_matches_committed_H16_rows(self) -> None:
        candidates = read_candidate_snapshot(ROOT / CANDIDATE_MANIFEST_REF)
        parent = load_canonical_json(ROOT / PARENT_BOUNDED_RESULT_REF)
        for index in (1, 5, 15):
            rows = tuple(law["signature"] for law in candidates[index]["laws"])
            self.assertEqual(
                verifier._parent_origin_record(rows),
                parent["candidate_results"][index]["translations"][0],
            )

    def test_trace_domain_and_digest_encoding_match_production(self) -> None:
        candidate = read_candidate_snapshot(ROOT / CANDIDATE_MANIFEST_REF)[1]
        self.assertEqual(verifier.trace_domain(candidate), candidate_trace_domain(candidate))

        domain = candidate_trace_domain(candidate)
        production_digest = hashlib.sha256()
        production_digest.update(b"IOTA-MIR-EXACT-ORBIT-TRACE-V1\x00")
        production_digest.update(len(domain).to_bytes(8, "big"))
        production_digest.update(domain)
        independent_digest = verifier._new_trace_digest(candidate)
        for layer, state in (
            (0, (1, 0)),
            (17, (0x1234, 0x5678)),
            (10**25, (0xFFFF_FFFF_FFFF_FFFF, 1)),
        ):
            _update_trace_digest(production_digest, layer, state)
            verifier._update_digest(independent_digest, layer, state[0], state[1])
        self.assertEqual(production_digest.hexdigest(), independent_digest.hexdigest())

    def test_verifier_does_not_call_production_search_or_layer_assessor(self) -> None:
        source = inspect.getsource(verifier)
        self.assertNotIn("evaluate_candidate_exact_orbit", source)
        self.assertNotIn("evaluate_detector_layer", source)
        self.assertNotIn("run_exact_orbit_search", source)


class IndependentReplayTests(unittest.TestCase):
    candidate = {"candidate_id": "SYNTHETIC-CHECKPOINT", "laws": ["synthetic"]}

    @staticmethod
    def fake_step(state: int, _rows: tuple[str, ...]) -> int:
        if state == 0:
            return 0
        if state < 64:
            return state + 1
        return {64: 65, 65: 66, 66: 64}[state]

    @staticmethod
    def no_pass(_seeded: int, _baseline: int, _rows: tuple[str, ...], _layer: int):
        return {
            "first_role": None,
            "first_successor": None,
            "first_intervention_eligible": None,
            "pass_witness": None,
        }

    def trace_digest(self, last_layer: int) -> str:
        seeded = verifier.canonical_initial_state(0)
        baseline = 0
        digest = verifier._new_trace_digest(self.candidate)
        verifier._update_digest(digest, 0, seeded, baseline)
        for layer in range(1, last_layer + 1):
            seeded = self.fake_step(seeded, ())
            baseline = self.fake_step(baseline, ())
            verifier._update_digest(digest, layer, seeded, baseline)
        return digest.hexdigest()

    def base_record(self, status: str, last_layer: int) -> dict[str, object]:
        return {
            "evaluation_status": status,
            "last_evaluated_layer": last_layer,
            "trace_sha256": self.trace_digest(last_layer),
            "first_role": None,
            "first_successor": None,
            "first_intervention_eligible": None,
            "pass_witness": None,
            "t_proto_exact": None,
            "recurrence": None,
        }

    def test_table_repeat_without_checkpoint_match_is_valid_resource_prefix(self) -> None:
        record = self.base_record("resource_censored_before_recurrence", 67)
        with mock.patch.object(verifier, "step", side_effect=self.fake_step), mock.patch.object(
            verifier, "_assess_layer", side_effect=self.no_pass
        ):
            verifier._verify_dynamic_candidate(record, self.candidate, ("synthetic",))

    def test_registered_checkpoint_recurrence_and_tamper_detection(self) -> None:
        record = self.base_record("recurrence_excluded_on_fixed_orbit", 69)
        state = {"seeded_state_hex": "0000000000000040", "baseline_state_hex": "0000000000000000"}
        record["recurrence"] = {
            "cone_saturation_layer": 63,
            "checkpoint_layer": 66,
            "repeat_layer": 69,
            "period": 3,
            "checkpoint_state": dict(state),
            "repeat_state": dict(state),
            "exact_full_state_equality": True,
        }
        with mock.patch.object(verifier, "step", side_effect=self.fake_step), mock.patch.object(
            verifier, "_assess_layer", side_effect=self.no_pass
        ):
            verifier._verify_dynamic_candidate(record, self.candidate, ("synthetic",))

        record["recurrence"]["checkpoint_layer"] = 63
        with mock.patch.object(verifier, "step", side_effect=self.fake_step), mock.patch.object(
            verifier, "_assess_layer", side_effect=self.no_pass
        ):
            with self.assertRaises(OrbitLedgerError):
                verifier._verify_dynamic_candidate(record, self.candidate, ("synthetic",))

    def test_trace_tamper_is_rejected(self) -> None:
        record = self.base_record("resource_censored_before_recurrence", 67)
        record["trace_sha256"] = "0" * 64
        with mock.patch.object(verifier, "step", side_effect=self.fake_step), mock.patch.object(
            verifier, "_assess_layer", side_effect=self.no_pass
        ):
            with self.assertRaises(OrbitLedgerError):
                verifier._verify_dynamic_candidate(record, self.candidate, ("synthetic",))

    def test_exact_pass_branch_and_pass_witness_tamper(self) -> None:
        def pass_at_67(
            seeded: int,
            baseline: int,
            _rows: tuple[str, ...],
            layer: int,
        ) -> dict[str, object]:
            if layer != 67:
                return self.no_pass(seeded, baseline, (), layer)
            return {
                "first_role": {"layer": layer, "anchor": 0},
                "first_successor": {
                    "layer": layer,
                    "anchor": 0,
                    "successor_anchor": 1,
                },
                "first_intervention_eligible": {
                    "layer": layer,
                    "anchor": 0,
                    "successor_anchor": 1,
                },
                "pass_witness": {
                    "layer": layer,
                    "anchor": 0,
                    "successor_anchor": 1,
                    "sham_future": 0,
                    "breaking_future": 1,
                    "seeded_state_hex": f"{seeded:016x}",
                    "baseline_state_hex": f"{baseline:016x}",
                },
            }

        record = self.base_record("exact_pass_on_fixed_orbit", 67)
        witness = pass_at_67(65, 0, (), 67)
        record["first_role"] = witness["first_role"]
        record["first_successor"] = witness["first_successor"]
        record["first_intervention_eligible"] = witness[
            "first_intervention_eligible"
        ]
        record["pass_witness"] = witness["pass_witness"]
        record["t_proto_exact"] = 67
        with mock.patch.object(verifier, "step", side_effect=self.fake_step), mock.patch.object(
            verifier, "_assess_layer", side_effect=pass_at_67
        ):
            verifier._verify_dynamic_candidate(record, self.candidate, ("synthetic",))

        record["pass_witness"] = dict(record["pass_witness"])
        record["pass_witness"]["anchor"] = 2
        with mock.patch.object(verifier, "step", side_effect=self.fake_step), mock.patch.object(
            verifier, "_assess_layer", side_effect=pass_at_67
        ):
            with self.assertRaises(OrbitLedgerError):
                verifier._verify_dynamic_candidate(record, self.candidate, ("synthetic",))

        continued = self.base_record("exact_pass_on_fixed_orbit", 68)
        continued.update(
            {
                "first_role": witness["first_role"],
                "first_successor": witness["first_successor"],
                "first_intervention_eligible": witness[
                    "first_intervention_eligible"
                ],
                "pass_witness": witness["pass_witness"],
                "t_proto_exact": 67,
            }
        )
        with mock.patch.object(verifier, "step", side_effect=self.fake_step), mock.patch.object(
            verifier, "_assess_layer", side_effect=pass_at_67
        ):
            with self.assertRaises(OrbitLedgerError):
                verifier._verify_dynamic_candidate(
                    continued,
                    self.candidate,
                    ("synthetic",),
                )

    def test_all_parent_reproductions_precede_any_dynamic_replay(self) -> None:
        rows = expected_candidate_rows()
        events: list[str] = []
        candidates = tuple({"candidate_id": f"C{index}"} for index in range(16))
        parent_results = [
            {"translations": [{"rows": list(candidate_rows)}]}
            for candidate_rows in rows
        ]
        ledger = {"candidate_results": [{} for _ in range(16)]}
        parent = {"candidate_results": parent_results}

        def reproduce(candidate_rows: tuple[str, ...]) -> dict[str, object]:
            events.append("parent")
            return {"rows": list(candidate_rows)}

        def replay(*_args) -> None:
            events.append("dynamic")

        with mock.patch.object(verifier, "_parent_origin_record", side_effect=reproduce), mock.patch.object(
            verifier, "_verify_dynamic_candidate", side_effect=replay
        ):
            verifier.verify_ledger_independently(ledger, candidates, parent)

        self.assertEqual(events[:15], ["parent"] * 15)
        self.assertEqual(events[15:], ["dynamic"] * 15)


if __name__ == "__main__":
    unittest.main()
