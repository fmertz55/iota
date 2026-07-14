from __future__ import annotations

import unittest

from mpmath import mp

from src.quantum_dirac.metrics import (
    certified_spectral_distance,
    refinement_gate,
    spectral_norm_from_gram,
    total_variation,
)
from src.quantum_dirac.target import (
    FixtureTargetSolver,
    build_spectral_hamiltonian,
    dyson_tail_bound,
)
from src.quantum_dirac.verifier import independent_target_propagator


class TargetAndMetricFixtureTests(unittest.TestCase):
    def test_synthetic_target_hamiltonian_is_hermitian(self) -> None:
        hamiltonian = build_spectral_hamiltonian(
            cutoff=2,
            mass="1/3",
            potential_amplitude="1/7",
            potential_phase_pi="1/3",
        )
        with mp.workdps(90):
            residual = max(
                abs(hamiltonian[row, column] - mp.conj(hamiltonian[column, row]))
                for row in range(hamiltonian.rows)
                for column in range(hamiltonian.cols)
            )
            self.assertLess(residual, mp.mpf("1e-80"))

    def test_eigendecomposition_and_independent_taylor_propagators_agree(self) -> None:
        hamiltonian = build_spectral_hamiltonian(
            cutoff=2,
            mass="1/3",
            potential_amplitude="1/7",
            potential_phase_pi="1/3",
        )
        primary = FixtureTargetSolver().propagator(
            mass="1/3",
            duration="1/5",
            potential_amplitude="1/7",
            potential_phase_pi="1/3",
        )
        independent = independent_target_propagator(
            hamiltonian,
            duration="1/5",
        )
        with mp.workdps(90):
            discrepancy = max(
                abs(primary[row, column] - independent[row, column])
                for row in range(primary.rows)
                for column in range(primary.cols)
            )
            self.assertLess(discrepancy, mp.mpf("1e-70"))

    def test_gram_spectral_norm_and_certified_addends(self) -> None:
        matrix = mp.matrix([[3, 0], [0, 4], [0, 0]])
        self.assertLess(abs(spectral_norm_from_gram(matrix) - 4), mp.mpf("1e-70"))
        zero = mp.matrix(3, 2)
        value = certified_spectral_distance(
            matrix,
            zero,
            target_tail="1/10",
            numerical_bound="1/100",
        )
        with mp.workdps(90):
            self.assertLess(abs(value - mp.mpf("4.11")), mp.mpf("1e-70"))

    def test_tail_bound_and_refinement_rules_are_deterministic(self) -> None:
        bound = dyson_tail_bound(
            amplitude="1/4",
            duration="2",
            first_omitted_order=61,
        )
        self.assertGreater(bound, 0)
        self.assertLess(bound, mp.mpf("1e-90"))
        self.assertTrue(refinement_gate("0.16", "0.08", "0.04"))
        self.assertFalse(refinement_gate("0.16", "0.12", "0.04"))
        self.assertAlmostEqual(float(total_variation((0.5, 0.5), (0.25, 0.75))), 0.25)


if __name__ == "__main__":
    unittest.main()
