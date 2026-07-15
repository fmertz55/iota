from __future__ import annotations

import inspect
import unittest
from fractions import Fraction

from flint import acb, acb_mat
from mpmath import mp

from src.quantum_dirac_symmetry_qca import independent_registered
from src.quantum_dirac_symmetry_qca import independent_states
from src.quantum_dirac_symmetry_qca.independent_registered import (
    independent_candidate_fixture,
    independent_target_fixture,
)
from src.quantum_dirac_symmetry_qca.production import (
    ball_precision,
    production_candidate_fixture,
    production_target_fixture,
)
from src.quantum_dirac_symmetry_qca.spec import SymmetryQCASpecError


class GuardedProductionTests(unittest.TestCase):
    def test_primary_recurrence_matches_explicit_independent_layers(self) -> None:
        with ball_precision(), mp.workdps(120):
            primary_input = acb_mat(12, 3)
            independent_input = mp.matrix(12, 3)
            values = ((0, 0, 1), (5, 1, 2j / 7), (11, 2, -3 / 11))
            for row, column, value in values:
                primary_input[row, column] = value
                independent_input[row, column] = value
            primary = production_candidate_fixture(
                primary_input, n_sites=6, mu=Fraction(2, 9)
            )
            independent = independent_candidate_fixture(
                independent_input, n_sites=6, mu=Fraction(2, 9)
            )
            maximum = 0
            for row in range(12):
                for column in range(3):
                    reference = independent[row, column]
                    difference = primary[row, column] - acb(
                        mp.nstr(mp.re(reference), 110), mp.nstr(mp.im(reference), 110)
                    )
                    maximum = max(maximum, float(difference.abs_upper()))
            self.assertLess(maximum, 1e-70)

    def test_positive_fourier_mode_has_the_audited_free_phase(self) -> None:
        with ball_precision(), mp.workdps(120):
            state = acb_mat(12, 1)
            for site in range(6):
                state[2 * site, 0] = acb(0, 2 * mp.pi * site / 6).exp() / mp.sqrt(6)
            result = production_candidate_fixture(state, n_sites=6, mu=0)
            expected = mp.exp(-2j * mp.pi / 6)
            difference = result[0, 0] - acb(
                mp.nstr(mp.re(expected / mp.sqrt(6)), 110),
                mp.nstr(mp.im(expected / mp.sqrt(6)), 110),
            )
            self.assertLess(float(difference.abs_upper()), 1e-70)

    def test_target_fixture_is_independently_reconstructed(self) -> None:
        with ball_precision(), mp.workdps(120):
            primary = production_target_fixture(
                cutoff=3,
                mass=Fraction(-1, 3),
                potential_amplitude=Fraction(1, 10),
                potential_phase_pi=Fraction(1, 2),
            )
            independent = independent_target_fixture(
                cutoff=3,
                mass=Fraction(-1, 3),
                potential_amplitude=Fraction(1, 10),
                potential_phase_pi=Fraction(1, 2),
            )
            maximum = 0
            for row in range(14):
                for column in range(14):
                    reference = independent[row, column]
                    difference = primary[row, column] - acb(
                        mp.nstr(mp.re(reference), 110), mp.nstr(mp.im(reference), 110)
                    )
                    maximum = max(maximum, float(difference.abs_upper()))
            self.assertLess(maximum, 1e-70)

    def test_fixture_entry_points_reject_registered_domains(self) -> None:
        with self.assertRaises(SymmetryQCASpecError):
            production_candidate_fixture(acb_mat(640, 1), n_sites=320, mu=0)
        with self.assertRaises(SymmetryQCASpecError):
            independent_candidate_fixture(mp.matrix(640, 1), n_sites=320, mu=0)
        with self.assertRaises(SymmetryQCASpecError):
            production_target_fixture(
                cutoff=72, mass=0, potential_amplitude=0
            )

    def test_independent_module_imports_no_primary_constructor(self) -> None:
        source = inspect.getsource(independent_registered)
        self.assertNotIn("from .production", source)
        self.assertNotIn("from .candidate", source)
        self.assertNotIn("from .target", source)
        self.assertNotIn("from .localization", source)
        state_source = inspect.getsource(independent_states)
        self.assertNotIn("from .states", state_source)
        self.assertNotIn("from .production", state_source)


if __name__ == "__main__":
    unittest.main()
