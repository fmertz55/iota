from __future__ import annotations

import json
import unittest

from src.minimal_realization_role_succession.detector import (
    outward_future_values,
    role_at,
)
from src.minimal_realization_role_succession.dynamics import state_from_active, step
from src.minimal_realization_role_succession_exact.local_impossibility import (
    EMPTY_LOCAL_PASS_CONTEXT_SET,
    HOMOGENEOUS_COMPARATOR_OBSTRUCTION,
    analyze_local_impossibility,
    evaluate_truth_table_bit,
)


SIGNATURES = tuple(f"{value:03b}" for value in range(8))
COPY_PREDECESSOR_ROWS = ("100", "101", "110", "111")
COPY_SELF_ROWS = ("010", "011", "110", "111")
COPY_PREDECESSOR_WITH_000_ROWS = (
    "000",
    "100",
    "101",
    "110",
    "111",
)


def rows_for_rule(rule_number: int) -> tuple[str, ...]:
    return tuple(
        signature
        for signature in SIGNATURES
        if rule_number & (1 << int(signature, 2))
    )


def context_state(bitstring: str, *, anchor: int, cycle_size: int) -> int:
    offsets = (-2, -1, 0, 1, 2, 3, 4, 5)
    return state_from_active(
        (
            anchor + offset
            for offset, bit in zip(offsets, bitstring)
            if bit == "1"
        ),
        cycle_size,
    )


class DirectTruthTableTests(unittest.TestCase):
    def test_copy_predecessor_reads_the_declared_first_port(self) -> None:
        for predecessor in (0, 1):
            for self_value in (0, 1):
                for successor in (0, 1):
                    self.assertEqual(
                        evaluate_truth_table_bit(
                            COPY_PREDECESSOR_ROWS,
                            predecessor,
                            self_value,
                            successor,
                        ),
                        predecessor,
                    )

    def test_direct_evaluator_rejects_nonbits_and_unknown_rows(self) -> None:
        with self.assertRaisesRegex(ValueError, "integer bit"):
            evaluate_truth_table_bit((), True, 0, 0)
        with self.assertRaisesRegex(ValueError, "unknown production signatures"):
            evaluate_truth_table_bit(("012",), 0, 0, 0)
        with self.assertRaisesRegex(TypeError, "iterable of signatures"):
            evaluate_truth_table_bit("010", 0, 1, 0)


class StaticCertificateTests(unittest.TestCase):
    def test_context_universe_has_canonical_fixed_eight_bit_identities(self) -> None:
        certificate = analyze_local_impossibility(COPY_SELF_ROWS)
        expected = (
            "00110000",
            "00110001",
            "00110010",
            "00110011",
            "10110000",
            "10110001",
            "10110010",
            "10110011",
        )
        self.assertEqual(
            tuple(context.bitstring for context in certificate.context_universe),
            expected,
        )
        self.assertEqual(
            tuple(context.context_id for context in certificate.context_universe),
            tuple(int(bitstring, 2) for bitstring in expected),
        )

    def test_copy_predecessor_is_a_synthetic_nonexclusion_certificate(self) -> None:
        certificate = analyze_local_impossibility(COPY_PREDECESSOR_ROWS)
        self.assertFalse(certificate.comparator_obstruction)
        self.assertFalse(certificate.symbolically_unreachable)
        self.assertIsNone(certificate.proof_route)
        self.assertEqual(len(certificate.joint_pass_capable_contexts), 8)
        for context in certificate.context_universe:
            self.assertEqual(context.raw_seeded_successor_displacements, (1,))
            self.assertEqual(context.attributed_successor_displacements, (1,))
            self.assertEqual(
                (context.sham_endpoint_bit, context.breaking_endpoint_bit),
                (1, 0),
            )
            self.assertEqual(context.joint_pass_capable_displacements, (1,))

    def test_copy_self_is_excluded_by_empty_local_joint_set(self) -> None:
        certificate = analyze_local_impossibility(COPY_SELF_ROWS)
        self.assertFalse(certificate.comparator_obstruction)
        self.assertTrue(certificate.symbolically_unreachable)
        self.assertEqual(certificate.proof_route, EMPTY_LOCAL_PASS_CONTEXT_SET)
        self.assertEqual(len(certificate.succession_capable_contexts), 8)
        self.assertEqual(certificate.causal_capable_contexts, ())
        self.assertEqual(certificate.joint_pass_capable_contexts, ())

    def test_000_obstruction_distinguishes_raw_from_attributed_successors(self) -> None:
        certificate = analyze_local_impossibility(COPY_PREDECESSOR_WITH_000_ROWS)
        self.assertEqual(certificate.formation_comparator_bit, 0)
        self.assertEqual(certificate.next_comparator_bit, 1)
        self.assertTrue(certificate.comparator_obstruction)
        self.assertTrue(certificate.raw_seeded_succession_capable_contexts)
        self.assertEqual(certificate.succession_capable_contexts, ())
        self.assertEqual(certificate.joint_pass_capable_contexts, ())
        self.assertTrue(certificate.symbolically_unreachable)
        self.assertEqual(
            certificate.proof_route,
            HOMOGENEOUS_COMPARATOR_OBSTRUCTION,
        )

    def test_certificate_is_json_transparent_and_validates_itself(self) -> None:
        certificate = analyze_local_impossibility(COPY_PREDECESSOR_ROWS)
        certificate.validate()
        payload = certificate.to_dict()
        self.assertEqual(len(payload["context_universe"]), 8)
        self.assertEqual(payload["context_offsets"], [-2, -1, 0, 1, 2, 3, 4, 5])
        self.assertEqual(
            payload["symbolically_unreachable"],
            len(payload["joint_pass_capable_contexts"]) == 0,
        )
        json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def test_all_rules_and_contexts_match_registered_detector_primitives(self) -> None:
        # This is a generic family audit: it enumerates all 256 truth tables and
        # all eight abstract contexts.  It does not read a registered candidate
        # manifest, result record, or canonical trajectory.
        cycle_size = 16
        anchor = 4
        for rule_number in range(256):
            rows = rows_for_rule(rule_number)
            certificate = analyze_local_impossibility(rows)
            next_baseline = step(0, rows, cycle_size)
            for context in certificate.context_universe:
                state = context_state(
                    context.bitstring,
                    anchor=anchor,
                    cycle_size=cycle_size,
                )
                next_state = step(state, rows, cycle_size)
                raw_displacements = tuple(
                    displacement
                    for displacement in (0, 1)
                    if role_at(
                        next_state,
                        0,
                        anchor + displacement,
                        cycle_size,
                    )
                )
                attributed_displacements = tuple(
                    displacement
                    for displacement in (0, 1)
                    if role_at(
                        next_state,
                        next_baseline,
                        anchor + displacement,
                        cycle_size,
                    )
                )
                sham_endpoint, breaking_endpoint = outward_future_values(
                    state,
                    rows,
                    anchor,
                    cycle_size,
                )
                with self.subTest(
                    rule_number=rule_number,
                    context_id=context.context_id,
                ):
                    self.assertEqual(
                        context.raw_seeded_successor_displacements,
                        raw_displacements,
                    )
                    self.assertEqual(
                        context.attributed_successor_displacements,
                        attributed_displacements,
                    )
                    self.assertEqual(
                        (context.sham_endpoint_bit, context.breaking_endpoint_bit),
                        (sham_endpoint, breaking_endpoint),
                    )
                    self.assertEqual(
                        context.joint_pass_capable,
                        bool(attributed_displacements)
                        and sham_endpoint != breaking_endpoint,
                    )
            self.assertEqual(
                certificate.symbolically_unreachable,
                not certificate.joint_pass_capable_contexts,
            )


if __name__ == "__main__":
    unittest.main()
