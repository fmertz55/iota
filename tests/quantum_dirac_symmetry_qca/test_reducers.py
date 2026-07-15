from __future__ import annotations

import unittest

from flint import acb_mat

from src.quantum_dirac_symmetry_qca.production import ball_precision
from src.quantum_dirac_symmetry_qca.reducers import (
    canonical_refinement_reduction,
    momentum_probabilities_ball,
    pi_sector_probability_ball,
)


class CanonicalReducerTests(unittest.TestCase):
    def test_arbitrary_size_dft_recovers_a_disclosed_mode(self) -> None:
        with ball_precision():
            state = acb_mat(12, 1)
            for site in range(6):
                from flint import acb, arb

                state[2 * site, 0] = acb(
                    0, 2 * arb.pi() * arb(site) / 6
                ).exp() / arb(6).sqrt()
            probabilities = momentum_probabilities_ball(state, n_sites=6)
            self.assertTrue(probabilities[1].contains(1))
            self.assertLess(float(pi_sector_probability_ball(state, n_sites=6)), 1e-70)

    def test_refinement_reducer_applies_class_specific_gates(self) -> None:
        direct = canonical_refinement_reduction(
            ["0.003", "0.001", "0.0003"], scenario_class="direct_only"
        )
        potential = canonical_refinement_reduction(
            ["0.019", "0.010", "0.0059"], scenario_class="potential_split"
        )
        self.assertTrue(direct["pass"])
        self.assertTrue(potential["pass"])
        self.assertFalse(
            canonical_refinement_reduction(
                ["0.003", "0.0011", "0.0003"], scenario_class="direct_only"
            )["pass"]
        )


if __name__ == "__main__":
    unittest.main()
