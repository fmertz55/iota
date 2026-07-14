from __future__ import annotations

import unittest

from mpmath import mp

from src.quantum_dirac.candidate import (
    FixtureCandidateEngine,
    FixturePermit,
    basis_state,
    direct_logical_transport,
    mass_mix_layer,
    norm_squared,
    transport_via_swaps,
)
from src.quantum_dirac.spec import QuantumDiracSpecError
from src.quantum_dirac.verifier import independent_fixture_step


class CandidateFixtureTests(unittest.TestCase):
    def test_two_swap_layers_equal_directional_transport_on_every_basis(self) -> None:
        for component in ("R", "L"):
            for site in range(8):
                with self.subTest(component=component, site=site):
                    state = basis_state(8, site, component)
                    actual = transport_via_swaps(state, n_sites=8)
                    expected = direct_logical_transport(state, n_sites=8)
                    self.assertEqual(
                        max(abs(actual[row] - expected[row]) for row in range(actual.rows)),
                        0,
                    )

    def test_disclosed_coin_fixture_matches_independent_matrix_reconstruction(self) -> None:
        engine = FixtureCandidateEngine(FixturePermit.issue(8))
        state = mp.matrix(16, 2)
        state[0, 0] = 1
        state[5, 1] = 1
        actual = engine.macrostep(state, delta="1/7", mass="1")
        expected = independent_fixture_step(
            state,
            n_sites=8,
            delta="1/7",
            mass="1",
        )
        with mp.workdps(90):
            discrepancy = max(
                abs(actual[row, column] - expected[row, column])
                for row in range(actual.rows)
                for column in range(actual.cols)
            )
            self.assertLess(discrepancy, mp.mpf("1e-80"))

    def test_mass_layer_and_transport_preserve_norm(self) -> None:
        with mp.workdps(80):
            state = mp.matrix(16, 1)
            state[0] = mp.sqrt(mp.mpf("1") / 3)
            state[3] = mp.sqrt(mp.mpf("2") / 3)
            mixed = mass_mix_layer(state, n_sites=8, angle="1/7")
            transported = transport_via_swaps(mixed, n_sites=8)
            self.assertLess(abs(norm_squared(transported) - 1), mp.mpf("1e-70"))

    def test_registered_engine_permit_cannot_be_issued(self) -> None:
        with self.assertRaises(QuantumDiracSpecError):
            FixturePermit.issue(256)

    def test_low_precision_fixture_engine_is_rejected(self) -> None:
        with self.assertRaises(QuantumDiracSpecError):
            FixtureCandidateEngine(FixturePermit.issue(8), dps=40)


if __name__ == "__main__":
    unittest.main()
