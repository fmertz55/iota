from __future__ import annotations

import unittest

from mpmath import mp

from src.quantum_dirac.states import (
    decode_fourier,
    encode_fixture_fourier,
    energy_spinor,
    momentum_probabilities,
    position_probabilities,
    state_norm_squared,
    total_directional_current,
)


class MapFixtureTests(unittest.TestCase):
    def test_disclosed_fourier_encoding_is_isometric_and_povms_normalize(self) -> None:
        with mp.workdps(90):
            normalization = mp.sqrt(3)
            coefficients = {
                (-1, "R"): 1 / normalization,
                (0, "L"): mp.j / normalization,
                (1, "R"): 1 / normalization,
            }
            state = encode_fixture_fourier(
                n_sites=16,
                coefficients=coefficients,
            )
            self.assertLess(abs(state_norm_squared(state) - 1), mp.mpf("1e-75"))
            self.assertLess(
                abs(mp.fsum(position_probabilities(state, n_sites=16)) - 1),
                mp.mpf("1e-75"),
            )
            momentum = momentum_probabilities(
                state,
                n_sites=16,
                modes=(-1, 0, 1),
            )
            self.assertLess(abs(mp.fsum(momentum.values()) - 1), mp.mpf("1e-75"))
            decoded = decode_fourier(
                state,
                n_sites=16,
                modes=(-1, 0, 1),
            )
            for key, value in coefficients.items():
                self.assertLess(abs(decoded[key] - value), mp.mpf("1e-75"))

    def test_energy_spinors_have_frozen_sign_and_unit_norm(self) -> None:
        with mp.workdps(90):
            plus = energy_spinor(r=1, mass="1/3", energy_sign=1)
            minus = energy_spinor(r=1, mass="1/3", energy_sign=-1)
            self.assertLess(abs(sum(abs(v) ** 2 for v in plus) - 1), mp.mpf("1e-75"))
            self.assertLess(abs(sum(abs(v) ** 2 for v in minus) - 1), mp.mpf("1e-75"))
            overlap = mp.conj(plus[0]) * minus[0] + mp.conj(plus[1]) * minus[1]
            self.assertLess(abs(overlap), mp.mpf("1e-75"))

    def test_directional_current_of_basis_modes(self) -> None:
        right = encode_fixture_fourier(
            n_sites=16,
            coefficients={(0, "R"): 1},
        )
        left = encode_fixture_fourier(
            n_sites=16,
            coefficients={(0, "L"): 1},
        )
        self.assertLess(abs(total_directional_current(right, n_sites=16) - 1), mp.mpf("1e-70"))
        self.assertLess(abs(total_directional_current(left, n_sites=16) + 1), mp.mpf("1e-70"))


if __name__ == "__main__":
    unittest.main()
