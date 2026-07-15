from __future__ import annotations

import unittest

from mpmath import mp

from src.quantum_dirac_symmetry_qca.candidate import SymmetryQCAFixtureError
from src.quantum_dirac_symmetry_qca.thresholds import (
    amplitude_tail_bound,
    draft_threshold_evidence,
    first_interaction_order,
    leading_correction_endpoint_norm,
)


class OutcomeFreeThresholdDesignTests(unittest.TestCase):
    def test_declared_interaction_orders_follow_mode_arithmetic(self) -> None:
        self.assertEqual(
            first_interaction_order(
                initial_abs_mode=4, boundary_abs_mode=73, harmonic=2
            ),
            35,
        )
        self.assertEqual(
            first_interaction_order(
                initial_abs_mode=4, boundary_abs_mode=120, harmonic=2
            ),
            58,
        )
        self.assertEqual(
            first_interaction_order(
                initial_abs_mode=4, boundary_abs_mode=73, harmonic=3
            ),
            23,
        )
        self.assertEqual(
            first_interaction_order(
                initial_abs_mode=4, boundary_abs_mode=120, harmonic=3
            ),
            39,
        )

    def test_tail_bounds_are_below_declared_design_scales(self) -> None:
        evidence = draft_threshold_evidence()
        self.assertEqual(
            evidence["status"],
            "design_evidence_only_interval_certificate_required",
        )
        self.assertLess(evidence["h2_target_tail"], mp.mpf("6e-72"))
        self.assertLess(evidence["h2_pi_tail"], mp.mpf("5e-131"))
        self.assertLess(evidence["h3_target_tail"], mp.mpf("6e-44"))
        self.assertLess(evidence["h3_pi_tail"], mp.mpf("2e-82"))

    def test_leading_correction_value_is_not_mislabeled_a_certificate(self) -> None:
        with mp.workdps(90):
            value = leading_correction_endpoint_norm()
            self.assertGreater(value, mp.mpf("0.3398"))
            self.assertLess(value, mp.mpf("0.3399"))
        self.assertIn("interval_certificate_required", draft_threshold_evidence()["status"])

    def test_invalid_tail_arguments_are_rejected(self) -> None:
        with self.assertRaises(SymmetryQCAFixtureError):
            amplitude_tail_bound(amplitude="1/8", duration="1", first_order=0)
        with self.assertRaises(SymmetryQCAFixtureError):
            first_interaction_order(
                initial_abs_mode=4, boundary_abs_mode=4, harmonic=2
            )


if __name__ == "__main__":
    unittest.main()

