from __future__ import annotations

import unittest

from mpmath import mp

from src.quantum_dirac_symmetry_qca.candidate import SymmetryQCAFixtureError
from src.quantum_dirac_symmetry_qca.localization import (
    edge_scatter_gate,
    on_site_swap_gate,
)
from src.quantum_dirac_symmetry_qca.spectrum import (
    canonical_fermionic_two_mode_lift,
    finite_cycle_momenta,
    full_space_extension_summary,
    global_band_summary,
    global_momentum_update,
    group_velocity,
    principal_band_angle,
    principal_eigenvalues,
    zone_edge_partner_residual,
)


class DirectSymmetryQCAGlobalSpectrumTests(unittest.TestCase):
    tolerance = mp.mpf("1e-80")

    @staticmethod
    def _matrix_residual(left: mp.matrix, right: mp.matrix):
        return max(
            abs(left[row, column] - right[row, column])
            for row in range(left.rows)
            for column in range(left.cols)
        )

    def test_exact_eigenvalues_cover_each_disclosed_brillouin_grid(self) -> None:
        with mp.workdps(90):
            for n_sites in (6, 10):
                for momentum in finite_cycle_momenta(n_sites=n_sites):
                    update = global_momentum_update(
                        n_sites=n_sites, q=momentum, mu="3/5"
                    )
                    self.assertLess(abs(mp.det(update) - 1), self.tolerance)
                    for eigenvalue in principal_eigenvalues(
                        n_sites=n_sites, q=momentum, mu="3/5"
                    ):
                        characteristic = mp.det(
                            update - eigenvalue * mp.eye(2)
                        )
                        self.assertLess(abs(characteristic), self.tolerance)

    def test_band_edges_and_both_circular_gaps_are_exact(self) -> None:
        with mp.workdps(90):
            summary = global_band_summary(n_sites=6, mu="3/5")
            edge = mp.asin(mp.mpf(3) / 5)
            self.assertLess(
                abs(summary["principal_angle_minimum"] - edge), self.tolerance
            )
            self.assertLess(
                abs(summary["principal_angle_maximum"] - (mp.pi - edge)),
                self.tolerance,
            )
            self.assertLess(
                abs(summary["zero_quasienergy_gap"] - 2 * edge),
                self.tolerance,
            )
            self.assertLess(
                abs(summary["pi_quasienergy_gap"] - 2 * edge),
                self.tolerance,
            )
            self.assertLess(
                abs(
                    principal_band_angle(n_sites=6, q=0, mu="3/5")
                    - edge
                ),
                self.tolerance,
            )
            self.assertLess(
                abs(
                    principal_band_angle(n_sites=6, q=-mp.pi, mu="3/5")
                    - (mp.pi - edge)
                ),
                self.tolerance,
            )

    def test_group_velocity_matches_derivative_and_speed_bound(self) -> None:
        with mp.workdps(90):
            momentum = mp.mpf(7) / 10
            step = mp.mpf("1e-20")
            analytic = group_velocity(
                n_sites=10, q=momentum, mu="3/5", band=1
            )
            finite_difference = (
                principal_band_angle(
                    n_sites=10, q=momentum + step, mu="3/5"
                )
                - principal_band_angle(
                    n_sites=10, q=momentum - step, mu="3/5"
                )
            ) / (2 * step)
            self.assertLess(abs(analytic - finite_difference), mp.mpf("1e-38"))

            summary = global_band_summary(n_sites=10, mu="3/5")
            maximum = group_velocity(
                n_sites=10, q=mp.pi / 2, mu="3/5", band=1
            )
            self.assertLess(
                abs(maximum - summary["maximum_group_speed"]), self.tolerance
            )

    def test_zone_edge_is_exact_opposite_mass_pi_partner(self) -> None:
        with mp.workdps(90):
            for n_sites in (6, 10):
                self.assertLess(
                    zone_edge_partner_residual(
                        n_sites=n_sites, offset="3/10", mu="2/5"
                    ),
                    self.tolerance,
                )

            offset = mp.mpf(3) / 10
            low = principal_band_angle(n_sites=6, q=offset, mu=0)
            zone_edge = principal_band_angle(
                n_sites=6, q=-mp.pi + offset, mu=0
            )
            self.assertLess(abs(low - offset), self.tolerance)
            self.assertLess(abs((mp.pi - zone_edge) - offset), self.tolerance)

    def test_mass_endpoints_are_unitary_flat_local_bands(self) -> None:
        with mp.workdps(90):
            for mass in (-1, 1):
                first = global_momentum_update(
                    n_sites=6, q=0, mu=mass
                )
                second = global_momentum_update(
                    n_sites=6, q="4/5", mu=mass
                )
                self.assertLess(
                    self._matrix_residual(first, second), self.tolerance
                )
                self.assertLess(
                    self._matrix_residual(first.H * first, mp.eye(2)),
                    self.tolerance,
                )
                self.assertEqual(
                    global_band_summary(n_sites=6, mu=mass)[
                        "maximum_group_speed"
                    ],
                    0,
                )

    def test_hard_core_and_fermionic_lifts_share_only_low_sectors(self) -> None:
        with mp.workdps(90):
            hard_edge = edge_scatter_gate(mu="3/5")
            fermion_edge = canonical_fermionic_two_mode_lift(
                hard_edge[1:3, 1:3]
            )
            hard_onsite = on_site_swap_gate()
            fermion_onsite = canonical_fermionic_two_mode_lift(
                hard_onsite[1:3, 1:3]
            )
            for row in range(3):
                for column in range(3):
                    self.assertEqual(
                        hard_edge[row, column], fermion_edge[row, column]
                    )
                    self.assertEqual(
                        hard_onsite[row, column], fermion_onsite[row, column]
                    )
            self.assertEqual(hard_edge[3, 3], 1)
            self.assertEqual(fermion_edge[3, 3], -1)
            self.assertEqual(hard_onsite[3, 3], 1)
            self.assertEqual(fermion_onsite[3, 3], -1)

            summary = full_space_extension_summary(n_sites=10, mu="3/5")
            self.assertEqual(
                summary["fermionic_edge_double_occupation_phase"], -1
            )
            self.assertEqual(
                summary["fermionic_onsite_double_occupation_phase"], -1
            )

    def test_global_fixture_guards_remain_outcome_free(self) -> None:
        with self.assertRaises(SymmetryQCAFixtureError):
            global_momentum_update(n_sites=8, q=0, mu="1/5")
        with self.assertRaises(SymmetryQCAFixtureError):
            global_momentum_update(n_sites=6, q=mp.pi + 1, mu="1/5")
        with self.assertRaises(SymmetryQCAFixtureError):
            global_momentum_update(n_sites=6, q=0, mu="6/5")
        with self.assertRaises(SymmetryQCAFixtureError):
            global_momentum_update(n_sites=6, q=0, mu="1/5", dps=40)
        with self.assertRaises(SymmetryQCAFixtureError):
            group_velocity(n_sites=6, q=0, mu=0, band=1)


if __name__ == "__main__":
    unittest.main()
