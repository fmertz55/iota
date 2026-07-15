from __future__ import annotations

import unittest

from mpmath import mp

from src.quantum_dirac_symmetry_qca.candidate import SymmetryQCAFixtureError
from src.quantum_dirac_symmetry_qca.spec import SymmetryQCASpecError
from src.quantum_dirac_symmetry_qca.target import (
    build_harmonic_two_hamiltonian,
    eigensystem_propagator,
    independent_taylor_propagator,
)


class DirectSymmetryQCATargetFixtureTests(unittest.TestCase):
    def test_cutoff_three_harmonic_two_hamiltonian_is_hermitian(self) -> None:
        with mp.workdps(90):
            hamiltonian = build_harmonic_two_hamiltonian(
                mass="1/7",
                potential_amplitude="1/9",
                potential_phase_pi="1/5",
            )
            residual = max(
                abs(hamiltonian[row, column] - mp.conj(hamiltonian[column, row]))
                for row in range(14)
                for column in range(14)
            )
            self.assertLess(residual, mp.mpf("1e-80"))

    def test_independent_exponential_agrees_on_disclosed_fixture(self) -> None:
        with mp.workdps(100):
            hamiltonian = build_harmonic_two_hamiltonian(
                mass="1/7",
                potential_amplitude="1/9",
                potential_phase_pi="1/5",
                dps=100,
            )
            primary = eigensystem_propagator(
                hamiltonian, duration="1/7", dps=100
            )
            independent = independent_taylor_propagator(
                hamiltonian, duration="1/7", dps=100
            )
            residual = max(
                abs(primary[row, column] - independent[row, column])
                for row in range(14)
                for column in range(14)
            )
            self.assertLess(residual, mp.mpf("1e-85"))

    def test_registered_cutoff_and_low_precision_are_rejected(self) -> None:
        with self.assertRaises(SymmetryQCASpecError):
            build_harmonic_two_hamiltonian(cutoff=72, mass="1/7")
        hamiltonian = build_harmonic_two_hamiltonian(mass="1/7")
        with self.assertRaises(SymmetryQCAFixtureError):
            independent_taylor_propagator(
                hamiltonian, duration="1/7", terms=20
            )


if __name__ == "__main__":
    unittest.main()

