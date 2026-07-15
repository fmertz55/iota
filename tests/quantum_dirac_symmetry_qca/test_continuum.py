from __future__ import annotations

import unittest

from mpmath import mp

from src.quantum_dirac_symmetry_qca.candidate import SymmetryQCAFixtureError
from src.quantum_dirac_symmetry_qca.continuum import (
    corrected_generator,
    dirac_generator,
    effective_generator,
    first_correction_coefficient,
    independent_log_generator,
    momentum_update,
)


class DirectSymmetryQCAContinuumTests(unittest.TestCase):
    tolerance = mp.mpf("1e-80")

    @staticmethod
    def _matrix_residual(left: mp.matrix, right: mp.matrix):
        return max(
            abs(left[row, column] - right[row, column])
            for row in range(left.rows)
            for column in range(left.cols)
        )

    def test_momentum_block_is_exactly_unitary(self) -> None:
        with mp.workdps(90):
            for n_sites in (6, 10):
                update = momentum_update(
                    n_sites=n_sites,
                    k="3/5",
                    mass="2/5",
                    delta="1/20",
                )
                self.assertLess(
                    self._matrix_residual(update.H * update, mp.eye(2)),
                    self.tolerance,
                )

    def test_closed_form_generator_matches_independent_matrix_log(self) -> None:
        with mp.workdps(90):
            for n_sites in (6, 10):
                closed_form = effective_generator(
                    n_sites=n_sites,
                    k="3/5",
                    mass="2/5",
                    delta="1/20",
                )
                independent = independent_log_generator(
                    n_sites=n_sites,
                    k="3/5",
                    mass="2/5",
                    delta="1/20",
                )
                self.assertLess(
                    self._matrix_residual(closed_form, independent),
                    self.tolerance,
                )

    def test_effective_generator_has_derived_quadratic_correction(self) -> None:
        with mp.workdps(90):
            residuals = []
            for delta in ("1/20", "1/40", "1/80"):
                exact = effective_generator(
                    n_sites=6,
                    k="3/5",
                    mass="2/5",
                    delta=delta,
                )
                corrected = corrected_generator(
                    n_sites=6,
                    k="3/5",
                    mass="2/5",
                    delta=delta,
                )
                residuals.append(self._matrix_residual(exact, corrected))
            for coarse, fine in zip(residuals, residuals[1:]):
                ratio = fine / coarse
                self.assertGreater(ratio, mp.mpf("0.0624"))
                self.assertLess(ratio, mp.mpf("0.0626"))

    def test_extracted_first_correction_converges_to_formula(self) -> None:
        with mp.workdps(90):
            delta = mp.mpf(1) / 160
            effective = effective_generator(
                n_sites=10,
                k="3/5",
                mass="2/5",
                delta=delta,
            )
            leading = dirac_generator(n_sites=10, k="3/5", mass="2/5")
            extracted = (effective - leading) / delta**2
            predicted = first_correction_coefficient(
                n_sites=10, k="3/5", mass="2/5"
            )
            self.assertLess(
                self._matrix_residual(extracted, predicted),
                mp.mpf("2e-7"),
            )

    def test_one_step_differs_from_dirac_propagator_at_cubic_order(self) -> None:
        with mp.workdps(90):
            generator = dirac_generator(n_sites=6, k="3/5", mass="2/5")
            residuals = []
            for delta_text in ("1/20", "1/40", "1/80"):
                delta = mp.mpf(delta_text)
                direct = momentum_update(
                    n_sites=6,
                    k="3/5",
                    mass="2/5",
                    delta=delta,
                )
                continuum = mp.expm(-1j * delta * generator)
                residuals.append(self._matrix_residual(direct, continuum))
            for coarse, fine in zip(residuals, residuals[1:]):
                ratio = fine / coarse
                self.assertGreater(ratio, mp.mpf("0.124"))
                self.assertLess(ratio, mp.mpf("0.126"))

    def test_signed_step_reverses_update_and_leaves_generator_even(self) -> None:
        with mp.workdps(90):
            forward = momentum_update(
                n_sites=6, k="3/5", mass="2/5", delta="1/20"
            )
            backward = momentum_update(
                n_sites=6, k="3/5", mass="2/5", delta="-1/20"
            )
            self.assertLess(
                self._matrix_residual(backward, forward.H), self.tolerance
            )

            forward_generator = effective_generator(
                n_sites=6, k="3/5", mass="2/5", delta="1/20"
            )
            backward_generator = effective_generator(
                n_sites=6, k="3/5", mass="2/5", delta="-1/20"
            )
            self.assertLess(
                self._matrix_residual(
                    backward_generator, forward_generator
                ),
                self.tolerance,
            )

    def test_continuum_fixture_guards_remain_outcome_free(self) -> None:
        with self.assertRaises(SymmetryQCAFixtureError):
            momentum_update(
                n_sites=8, k="3/5", mass="2/5", delta="1/20"
            )
        with self.assertRaises(SymmetryQCAFixtureError):
            momentum_update(
                n_sites=6, k="3/5", mass="2/5", delta="0"
            )
        with self.assertRaises(SymmetryQCAFixtureError):
            momentum_update(
                n_sites=6, k="1", mass="0", delta="1/4"
            )
        with self.assertRaises(SymmetryQCAFixtureError):
            independent_log_generator(
                n_sites=6,
                k="3/5",
                mass="2/5",
                delta="1/20",
                terms=100,
            )


if __name__ == "__main__":
    unittest.main()
