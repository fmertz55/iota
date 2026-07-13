from __future__ import annotations

import unittest

from src.minimal_realization.dynamics import (
    STATE_MASK,
    active_loci,
    run_trajectory,
    state_from_active,
    step,
    translate_state,
)


class DynamicsTests(unittest.TestCase):
    def test_no_production_rows_make_fresh_layer_quiescent(self) -> None:
        self.assertEqual(step(state_from_active([0, 1]), ()), 0)

    def test_00_row_emits_on_quiescent_background(self) -> None:
        self.assertEqual(step(0, ("00",)), STATE_MASK)

    def test_copy_predecessor_moves_one_event_one_hop(self) -> None:
        initial = state_from_active([0])
        successor = step(initial, ("01", "11"))
        self.assertEqual(active_loci(successor), (1,))

    def test_update_is_synchronous_without_within_tick_cascade(self) -> None:
        initial = state_from_active([0])
        first = step(initial, ("01", "11"))
        self.assertEqual(active_loci(first), (1,))
        second = step(first, ("01", "11"))
        self.assertEqual(active_loci(second), (2,))

    def test_translation_equivariance(self) -> None:
        state = state_from_active([0, 2, 7])
        rows = ("01", "10")
        for offset in (0, 1, 17, 63):
            self.assertEqual(
                step(translate_state(state, offset), rows),
                translate_state(step(state, rows), offset),
            )

    def test_trajectory_includes_initial_and_last_layer(self) -> None:
        trajectory = run_trajectory(state_from_active([0]), ("01", "11"), 3)
        self.assertEqual(len(trajectory), 4)
        self.assertEqual([active_loci(state) for state in trajectory], [(0,), (1,), (2,), (3,)])

    def test_unknown_signature_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown production signatures"):
            step(0, ("12",))


if __name__ == "__main__":
    unittest.main()
