from __future__ import annotations

import unittest

from mpmath import mp

from src.quantum_dirac_symmetry_qca.candidate import (
    SymmetryQCAFixtureError,
    basis_state,
    direct_qca_step,
    translate,
    update_matrix,
)


class DirectSymmetryQCAFixtureTests(unittest.TestCase):
    def test_update_matrix_is_unitary(self) -> None:
        with mp.workdps(90):
            update = update_matrix(n_sites=6, mu="1/7")
            gram = update.H * update
            residual = max(
                abs(gram[row, column] - (row == column))
                for row in range(gram.rows)
                for column in range(gram.cols)
            )
            self.assertLess(residual, mp.mpf("1e-80"))

    def test_update_commutes_with_translation(self) -> None:
        with mp.workdps(90):
            state = mp.matrix(12, 2)
            state[0, 0] = mp.sqrt(mp.mpf("1") / 3)
            state[5, 0] = 1j * mp.sqrt(mp.mpf("2") / 3)
            state[3, 1] = 1
            left = direct_qca_step(
                translate(state, n_sites=6), n_sites=6, mu="2/9"
            )
            right = translate(
                direct_qca_step(state, n_sites=6, mu="2/9"), n_sites=6
            )
            residual = max(
                abs(left[row, column] - right[row, column])
                for row in range(left.rows)
                for column in range(left.cols)
            )
            self.assertLess(residual, mp.mpf("1e-80"))

    def test_massless_components_move_in_opposite_directions(self) -> None:
        right = direct_qca_step(
            basis_state(6, 2, "R"), n_sites=6, mu="0"
        )
        left = direct_qca_step(
            basis_state(6, 2, "L"), n_sites=6, mu="0"
        )
        self.assertEqual(right, basis_state(6, 1, "R"))
        self.assertEqual(left, basis_state(6, 3, "L"))

    def test_mass_coupling_and_shift_share_one_direct_update(self) -> None:
        with mp.workdps(90):
            state = basis_state(6, 2, "R")
            result = direct_qca_step(state, n_sites=6, mu="3/5")
            self.assertLess(abs(result[2, 0] - mp.mpf("4") / 5), mp.mpf("1e-80"))
            self.assertLess(
                abs(result[5, 0] + 1j * mp.mpf("3") / 5), mp.mpf("1e-80")
            )

    def test_registered_and_undeclared_sizes_are_rejected(self) -> None:
        for n_sites in (8, 16, 256, 512, 1024):
            with self.subTest(n_sites=n_sites):
                with self.assertRaises(SymmetryQCAFixtureError):
                    basis_state(n_sites, 0, "R")

    def test_low_precision_and_invalid_mass_are_rejected(self) -> None:
        state = basis_state(6, 0, "R")
        with self.assertRaises(SymmetryQCAFixtureError):
            direct_qca_step(state, n_sites=6, mu="1/7", dps=40)
        for mass in ("1", "-1", "nan"):
            with self.subTest(mass=mass):
                with self.assertRaises(SymmetryQCAFixtureError):
                    direct_qca_step(state, n_sites=6, mu=mass)


if __name__ == "__main__":
    unittest.main()
