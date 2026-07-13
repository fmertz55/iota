import json
import tempfile
import unittest
from pathlib import Path

from src.minimal_realization_orbit.engine import ExactOrbitOutcome
from src.minimal_realization_orbit.runner import (
    BASE_OUTCOME_SEAL_REF,
    CANDIDATE_MANIFEST_REF,
    PARENT_BOUNDED_RESULT_REF,
    RESULT_SCHEMA_REF,
    OrbitLedgerError,
    build_result_ledger,
    candidate_trace_domain,
    canonical_json,
    load_canonical_json,
    load_canonical_json_bytes,
    read_candidate_snapshot,
    read_candidate_snapshot_bytes,
    run_exact_orbit_search,
    sha256_file,
    validate_parent_bounded_result,
    validate_result_ledger,
    write_result_ledger,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_PATH = ROOT / CANDIDATE_MANIFEST_REF
PARENT_PATH = ROOT / PARENT_BOUNDED_RESULT_REF


def recurrence_outcome(period: int = 1) -> ExactOrbitOutcome:
    return ExactOrbitOutcome(
        status="recurrence_excluded_on_fixed_orbit",
        t_proto=None,
        last_evaluated_layer=63 + period,
        first_role=None,
        first_successor=None,
        first_intervention_eligible=None,
        pass_witness=None,
        recurrence=(63, 63 + period, period, 0, 0),
        trace_sha256="1" * 64,
    )


def pass_outcome(layer: int) -> ExactOrbitOutcome:
    return ExactOrbitOutcome(
        status="exact_pass_on_fixed_orbit",
        t_proto=layer,
        last_evaluated_layer=layer,
        first_role=(layer, 0),
        first_successor=(layer, 0, 1),
        first_intervention_eligible=(layer, 0, 1),
        pass_witness=(layer, 0, 1, 0, 1, 3, 0),
        recurrence=None,
        trace_sha256="2" * 64,
    )


def resource_outcome() -> ExactOrbitOutcome:
    return ExactOrbitOutcome(
        status="resource_censored_before_recurrence",
        t_proto=None,
        last_evaluated_layer=1_000_000,
        first_role=None,
        first_successor=None,
        first_intervention_eligible=None,
        pass_witness=None,
        recurrence=None,
        trace_sha256="3" * 64,
    )


class SnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidates = read_candidate_snapshot(CANDIDATES_PATH)
        self.parent = load_canonical_json(PARENT_PATH)

    def test_snapshot_has_canonical_shell_order(self) -> None:
        self.assertEqual(len(self.candidates), 16)
        self.assertEqual([len(row["laws"]) for row in self.candidates], [0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4])

    def test_candidate_reordering_is_rejected(self) -> None:
        lines = CANDIDATES_PATH.read_bytes().splitlines(keepends=True)
        lines[1], lines[2] = lines[2], lines[1]
        with self.assertRaises(OrbitLedgerError):
            read_candidate_snapshot_bytes(b"".join(lines), "mutated")

    def test_duplicate_json_key_is_rejected(self) -> None:
        with self.assertRaises(OrbitLedgerError):
            load_canonical_json_bytes(b'{"a":1,"a":2}\n', "duplicate")

    def test_nonfinite_json_is_rejected(self) -> None:
        with self.assertRaises(OrbitLedgerError):
            load_canonical_json_bytes(b'{"a":NaN}\n', "nan")

    def test_noncanonical_json_is_rejected(self) -> None:
        with self.assertRaises(OrbitLedgerError):
            load_canonical_json_bytes(b'{ "a": 1 }\n', "spaced")

    def test_parent_ledger_is_bound_to_all_candidates(self) -> None:
        validate_parent_bounded_result(self.parent, self.candidates)
        mutated = json.loads(json.dumps(self.parent))
        mutated["candidate_results"][1]["candidate_id"] = "wrong"
        with self.assertRaises(OrbitLedgerError):
            validate_parent_bounded_result(mutated, self.candidates)

    def test_trace_domain_binds_candidate_identity(self) -> None:
        self.assertNotEqual(
            candidate_trace_domain(self.candidates[1]),
            candidate_trace_domain(self.candidates[2]),
        )


class SearchAggregationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidates = read_candidate_snapshot(CANDIDATES_PATH)
        self.parent = load_canonical_json(PARENT_PATH)

    def test_all_candidates_are_processed_without_shell_stop(self) -> None:
        calls = []

        def evaluator(candidate, rows, parent_origin):
            calls.append((candidate["candidate_id"], rows, parent_origin["translation_offset"]))
            return recurrence_outcome()

        search = run_exact_orbit_search(self.candidates, self.parent, evaluator)
        self.assertEqual(len(calls), 15)
        self.assertEqual(search["search_conclusion"], "all_dynamic_candidates_recurrence_excluded")
        self.assertTrue(search["all_dynamic_candidates_resolved"])
        self.assertEqual(search["candidate_results"][0]["evaluation_status"], "analytically_excluded")

    def test_lexicographic_winner_prefers_lower_law_count(self) -> None:
        def evaluator(candidate, rows, parent_origin):
            if rows == ("11",):
                return pass_outcome(30)
            if rows == ("00", "01"):
                return pass_outcome(17)
            return recurrence_outcome()

        search = run_exact_orbit_search(self.candidates, self.parent, evaluator)
        self.assertEqual(search["search_conclusion"], "one_or_more_exact_passes")
        self.assertEqual(search["exact_orbit_winner_candidate_ids"], ["MIR-P2-L1-11"])

    def test_every_cobest_winner_is_retained(self) -> None:
        def evaluator(candidate, rows, parent_origin):
            if rows in (("00",), ("01",)):
                return pass_outcome(19)
            return recurrence_outcome()

        search = run_exact_orbit_search(self.candidates, self.parent, evaluator)
        self.assertEqual(
            search["exact_orbit_winner_candidate_ids"],
            ["MIR-P2-L1-00", "MIR-P2-L1-01"],
        )

    def test_any_resource_censoring_blocks_family_claim(self) -> None:
        def evaluator(candidate, rows, parent_origin):
            return resource_outcome() if rows == ("00",) else recurrence_outcome()

        search = run_exact_orbit_search(self.candidates, self.parent, evaluator)
        self.assertEqual(search["completion_status"], "incomplete_resource_censored")
        self.assertEqual(search["search_conclusion"], "resource_censored_incomplete")
        self.assertFalse(search["all_dynamic_candidates_resolved"])
        self.assertEqual(search["exact_orbit_winner_candidate_ids"], [])


class LedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidates = read_candidate_snapshot(CANDIDATES_PATH)
        self.parent = load_canonical_json(PARENT_PATH)
        protocol_path = ROOT / "specs/icp_minimal_realization_exact_orbit/v0.1-draft/protocol.json"
        self.open_seal = {
            "parent_outcome_seal": {"path": "new-seal", "sha256": "a" * 64},
            "base_outcome_seal": {"path": BASE_OUTCOME_SEAL_REF, "sha256": "b" * 64},
            "candidate_manifest": {"path": CANDIDATE_MANIFEST_REF, "sha256": sha256_file(CANDIDATES_PATH)},
            "parent_bounded_result": {"path": PARENT_BOUNDED_RESULT_REF, "sha256": sha256_file(PARENT_PATH)},
            "result_schema": {"path": RESULT_SCHEMA_REF, "sha256": sha256_file(ROOT / RESULT_SCHEMA_REF)},
        }
        self.ledger = build_result_ledger(
            root=ROOT,
            open_seal_path=protocol_path,
            open_seal=self.open_seal,
            candidates=self.candidates,
            parent_result=self.parent,
            evaluator=lambda candidate, rows, parent_origin: recurrence_outcome(),
        )

    def test_synthetic_ledger_validates(self) -> None:
        validate_result_ledger(self.ledger, self.candidates)

    def test_recurrence_state_mutation_is_rejected(self) -> None:
        mutated = json.loads(canonical_json(self.ledger))
        mutated["candidate_results"][1]["recurrence"]["repeat_state"]["seeded_state_hex"] = "1" * 16
        with self.assertRaises(OrbitLedgerError):
            validate_result_ledger(mutated, self.candidates)

    def test_boolean_recurrence_period_is_rejected(self) -> None:
        mutated = json.loads(canonical_json(self.ledger))
        mutated["candidate_results"][1]["recurrence"]["period"] = True
        with self.assertRaises(OrbitLedgerError):
            validate_result_ledger(mutated, self.candidates)

    def test_summary_mutation_is_rejected(self) -> None:
        mutated = json.loads(canonical_json(self.ledger))
        mutated["search_conclusion"] = "one_or_more_exact_passes"
        with self.assertRaises(OrbitLedgerError):
            validate_result_ledger(mutated, self.candidates)

    def test_boolean_substitution_for_integer_metadata_is_rejected(self) -> None:
        mutations = (
            ("canonical_origin", False),
            ("translation_offsets_evaluated", [False]),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                mutated = json.loads(canonical_json(self.ledger))
                mutated[key] = value
                with self.assertRaises(OrbitLedgerError):
                    validate_result_ledger(mutated, self.candidates)

        mutated = json.loads(canonical_json(self.ledger))
        mutated["candidate_results"][0]["atomic_n_l"] = False
        with self.assertRaises(OrbitLedgerError):
            validate_result_ledger(mutated, self.candidates)

    def test_no_clobber_writer_is_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            write_result_ledger(path, self.ledger, self.candidates)
            self.assertEqual(path.read_text(encoding="utf-8"), canonical_json(self.ledger) + "\n")
            with self.assertRaises(OrbitLedgerError):
                write_result_ledger(path, self.ledger, self.candidates)

    def test_stale_temporary_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.with_name("result.json.tmp").write_text("stale", encoding="utf-8")
            with self.assertRaises(OrbitLedgerError):
                write_result_ledger(path, self.ledger, self.candidates)


if __name__ == "__main__":
    unittest.main()
