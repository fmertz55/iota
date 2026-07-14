from __future__ import annotations

import unittest
from fractions import Fraction

from flint import acb, acb_mat
from mpmath import mp

from src.quantum_dirac.certified import (
    arb_exact,
    ball_precision,
    build_certified_target_hamiltonian,
    certified_fixture_step,
    certified_spectral_norm_upper,
)
from src.quantum_dirac.target import build_spectral_hamiltonian
from src.quantum_dirac.verifier import (
    independent_fixture_step,
    independent_target_propagator,
)


def _acb_from_mpmath(value) -> acb:
    with mp.workdps(100):
        real = mp.nstr(mp.re(value), 95)
        imaginary = mp.nstr(mp.im(value), 95)
    return acb(real, imaginary)


class CertifiedBallFixtureTests(unittest.TestCase):
    def test_repeated_singular_values_have_a_certified_upper_bound(self) -> None:
        with ball_precision():
            identity = acb_mat([[1, 0], [0, 1]])
            bound = certified_spectral_norm_upper(identity)
            self.assertTrue(bound >= 1)
            self.assertTrue(bound.contains(1))

    def test_certified_candidate_step_overlaps_independent_reconstruction(self) -> None:
        with ball_precision():
            state_ball = acb_mat(16, 2)
            state_ball[0, 0] = 1
            state_ball[5, 1] = 1
            certified = certified_fixture_step(
                state_ball,
                n_sites=8,
                delta="1/7",
                mass="1",
            )
        state_mp = mp.matrix(16, 2)
        state_mp[0, 0] = 1
        state_mp[5, 1] = 1
        independent = independent_fixture_step(
            state_mp,
            n_sites=8,
            delta="1/7",
            mass="1",
        )
        with ball_precision():
            for row in range(certified.nrows()):
                for column in range(certified.ncols()):
                    difference = certified[row, column] - _acb_from_mpmath(
                        independent[row, column]
                    )
                    self.assertLess(float(difference.abs_upper()), 1e-70)

    def test_certified_target_exponential_overlaps_independent_taylor(self) -> None:
        with ball_precision():
            hamiltonian_ball = build_certified_target_hamiltonian(
                cutoff=2,
                mass=Fraction(1, 3),
                potential_amplitude=Fraction(1, 7),
                potential_phase_pi=Fraction(1, 3),
            )
            certified = (
                acb(0, -arb_exact("1/5")) * hamiltonian_ball
            ).exp()
        hamiltonian_mp = build_spectral_hamiltonian(
            cutoff=2,
            mass="1/3",
            potential_amplitude="1/7",
            potential_phase_pi="1/3",
        )
        independent = independent_target_propagator(
            hamiltonian_mp,
            duration="1/5",
        )
        with ball_precision():
            for row in range(certified.nrows()):
                for column in range(certified.ncols()):
                    difference = certified[row, column] - _acb_from_mpmath(
                        independent[row, column]
                    )
                    self.assertLess(float(difference.abs_upper()), 1e-70)

    def test_ball_gram_eigenvalue_is_a_certified_spectral_upper_bound(self) -> None:
        with ball_precision():
            matrix = acb_mat([[3, 0], [0, 4], [0, 0]])
            upper = certified_spectral_norm_upper(matrix)
            self.assertTrue(upper.contains(4))
            self.assertLess(float(upper.upper()), 4.000000000001)


if __name__ == "__main__":
    unittest.main()
