from __future__ import annotations

import unittest

from src.minimal_realization_role_succession.dynamics import (
    active_loci,
    normalize_rows,
    reflect_state,
    run_trajectory,
    signature_at,
    state_from_active,
    state_mask,
    step,
    translate_state,
)
from src.minimal_realization_role_succession.search import reflected_rows


COPY_PREDECESSOR_ROWS = ("100", "101", "110", "111")
SIGNATURES = tuple(f"{value:03b}" for value in range(8))


def rows_for_rule(rule_number: int) -> tuple[str, ...]:
    return tuple(
        signature
        for index, signature in enumerate(SIGNATURES)
        if rule_number & (1 << index)
    )


def naive_step(state: int, rows: tuple[str, ...], cycle_size: int) -> int:
    selected = set(rows)
    output = 0
    for locus in range(cycle_size):
        signature = "".join(
            str((state >> (neighbor % cycle_size)) & 1)
            for neighbor in (locus - 1, locus, locus + 1)
        )
        if signature in selected:
            output |= 1 << locus
    return output


class DynamicsTests(unittest.TestCase):
    def test_bit_parallel_transition_matches_naive_all_C4_states_and_rules(self) -> None:
        # C4 is not the registered primary topology; exhaustive one-step checks
        # therefore disclose no canonical candidate trajectory.
        for rule_number in range(256):
            rows = rows_for_rule(rule_number)
            for state in range(1 << 4):
                self.assertEqual(
                    step(state, rows, 4),
                    naive_step(state, rows, 4),
                    (rule_number, state),
                )

    def test_bit_parallel_transition_matches_naive_large_synthetic_states(self) -> None:
        for cycle_size in (64, 96, 128):
            state = state_from_active(
                (2, 3, 7, 19, cycle_size // 2, cycle_size - 2),
                cycle_size,
            )
            for rule_number in range(256):
                rows = rows_for_rule(rule_number)
                self.assertEqual(
                    step(state, rows, cycle_size),
                    naive_step(state, rows, cycle_size),
                    (cycle_size, rule_number),
                )

    def test_registered_row_forms_are_interned(self) -> None:
        rows = ("001", "011", "101")
        self.assertIs(normalize_rows(rows), normalize_rows(rows))
        frozen = normalize_rows(rows)
        self.assertIs(frozen, normalize_rows(frozen))

    def test_signature_order_is_predecessor_self_successor(self) -> None:
        state = state_from_active((2, 3), 8)
        self.assertEqual(signature_at(state, 2, 8), "011")
        self.assertEqual(signature_at(state, 3, 8), "110")
        self.assertEqual(active_loci(step(state, ("110",), 8), 8), (3,))

    def test_unselected_rows_write_zero_to_fresh_layer(self) -> None:
        state = state_from_active((4, 9, 17))
        self.assertEqual(step(state, ()), 0)

    def test_all_rows_write_one_everywhere(self) -> None:
        rows = tuple(f"{value:03b}" for value in range(8))
        state = state_from_active((4, 9, 17))
        self.assertEqual(step(state, rows), state_mask())

    def test_copy_predecessor_is_synchronous_without_cascade(self) -> None:
        initial = state_from_active((5, 19))
        first = step(initial, COPY_PREDECESSOR_ROWS)
        second = step(first, COPY_PREDECESSOR_ROWS)
        self.assertEqual(active_loci(first), (6, 20))
        self.assertEqual(active_loci(second), (7, 21))

    def test_synthetic_trajectory_includes_both_endpoints(self) -> None:
        initial = state_from_active((7, 23))
        trajectory = run_trajectory(initial, COPY_PREDECESSOR_ROWS, 2)
        self.assertEqual(len(trajectory), 3)
        self.assertEqual(
            tuple(active_loci(state) for state in trajectory),
            ((7, 23), (8, 24), (9, 25)),
        )

    def test_translation_equivariance_on_registered_cycle_sizes(self) -> None:
        rows = ("001", "011", "100", "110")
        for cycle_size in (64, 96, 128):
            state = state_from_active((5, 19, cycle_size - 2), cycle_size)
            for offset in (1, 17, cycle_size - 1):
                with self.subTest(cycle_size=cycle_size, offset=offset):
                    self.assertEqual(
                        step(translate_state(state, offset, cycle_size), rows, cycle_size),
                        translate_state(step(state, rows, cycle_size), offset, cycle_size),
                    )

    def test_reflection_swaps_relation_incidence_ports(self) -> None:
        rows = ("001", "010", "110")
        state = state_from_active((4, 11, 27))
        self.assertEqual(
            step(reflect_state(state), reflected_rows(rows)),
            reflect_state(step(state, rows)),
        )

    def test_cycle_specific_state_bound_is_enforced(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsigned 64-bit"):
            step(1 << 64, ())
        with self.assertRaisesRegex(ValueError, "at least four"):
            step(0, (), 3)

    def test_unknown_signature_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown production signatures"):
            step(0, ("010", "12"))


if __name__ == "__main__":
    unittest.main()
