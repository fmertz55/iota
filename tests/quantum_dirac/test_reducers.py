from __future__ import annotations

import unittest

from flint import acb_mat, arb
from mpmath import mp

from src.quantum_dirac.certified import ball_precision
from src.quantum_dirac.reducers import (
    arb_lower_text,
    arb_upper_text,
    momentum_probabilities_ball,
    parity_ball,
    theta_ball,
    witness_metrics_ball,
)


class CertifiedReducerTests(unittest.TestCase):
    def test_decimal_interval_serialization_contains_ball(self) -> None:
        with ball_precision():
            value = arb(1) / 7
            lower = mp.mpf(arb_lower_text(value))
            upper = mp.mpf(arb_upper_text(value))
            self.assertLessEqual(lower, mp.mpf("1") / 7)
            self.assertGreaterEqual(upper, mp.mpf("1") / 7)

    def test_arbitrary_precision_fft_normalizes_site_basis(self) -> None:
        with ball_precision():
            state = acb_mat(16, 1)
            state[0, 0] = 1
            probabilities = momentum_probabilities_ball(state, n_sites=8)
            total = sum(probabilities, arb(0))
            self.assertTrue(total.contains(1))
            for probability in probabilities:
                self.assertTrue(probability.contains(arb(1) / 8))

    def test_parity_and_time_reversal_are_involutions(self) -> None:
        with ball_precision():
            state = acb_mat(16, 1)
            state[2, 0] = 1 + 2j
            state[9, 0] = 3 - 4j
            parity_twice = parity_ball(parity_ball(state, n_sites=8), n_sites=8)
            theta_twice = theta_ball(theta_ball(state, n_sites=8), n_sites=8)
            for row in range(state.nrows()):
                self.assertEqual(parity_twice[row, 0], state[row, 0])
                self.assertEqual(theta_twice[row, 0], state[row, 0])

    def test_identical_states_have_zero_witness_discrepancy(self) -> None:
        with ball_precision():
            state = acb_mat(16, 1)
            state[0, 0] = 1
            metrics = witness_metrics_ball(state, state, n_sites=8)
            for value in metrics.values():
                self.assertLess(float(value.upper()), 1e-70)


if __name__ == "__main__":
    unittest.main()
