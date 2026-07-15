from __future__ import annotations

import unittest

from mpmath import mp

from src.quantum_dirac_symmetry_qca.candidate import (
    basis_state,
    direct_qca_step,
)
from src.quantum_dirac_symmetry_qca.localization import (
    edge_scatter_gate,
    full_basis_state,
    margolus_inverse,
    margolus_step,
    one_excitation_vector,
    parity_full,
    resource_clock,
    time_reverse_full,
    translate_full,
)


class DirectSymmetryQCAMargolusTests(unittest.TestCase):
    tolerance = mp.mpf("1e-80")

    def assertSparseClose(self, left, right) -> None:
        residual = max(
            (
                abs(left.get(key, 0) - right.get(key, 0))
                for key in left.keys() | right.keys()
            ),
            default=mp.mpf(0),
        )
        self.assertLess(residual, self.tolerance)

    @staticmethod
    def _basis_index(n_sites: int, occupied_modes) -> int:
        return next(iter(full_basis_state(n_sites, occupied_modes)))

    def _multisector_state(self, n_sites: int):
        with mp.workdps(90):
            return {
                self._basis_index(n_sites, ()): mp.sqrt(mp.mpf(1) / 7),
                self._basis_index(n_sites, ((1, "R"), (2, "L"))): (
                    1j * mp.sqrt(mp.mpf(2) / 7)
                ),
                self._basis_index(
                    n_sites, ((0, "L"), (3, "R"), (4, "L"))
                ): mp.sqrt(mp.mpf(4) / 7),
            }

    def test_edge_scatter_is_unitary_on_all_four_local_states(self) -> None:
        with mp.workdps(90):
            gate = edge_scatter_gate(mu="3/5")
            gram = gate.H * gate
            residual = max(
                abs(gram[row, column] - (row == column))
                for row in range(4)
                for column in range(4)
            )
            self.assertLess(residual, self.tolerance)
            self.assertEqual(gate[0, 0], 1)
            self.assertEqual(gate[3, 3], 1)

    def test_full_step_restricts_exactly_to_direct_law_on_every_basis(self) -> None:
        with mp.workdps(90):
            for n_sites in (6, 10):
                for site in range(n_sites):
                    for component in ("R", "L"):
                        with self.subTest(
                            n_sites=n_sites, site=site, component=component
                        ):
                            localized = one_excitation_vector(
                                margolus_step(
                                    full_basis_state(
                                        n_sites, ((site, component),)
                                    ),
                                    n_sites=n_sites,
                                    mu="3/5",
                                ),
                                n_sites=n_sites,
                            )
                            direct = direct_qca_step(
                                basis_state(n_sites, site, component),
                                n_sites=n_sites,
                                mu="3/5",
                            )
                            residual = max(
                                abs(localized[row, 0] - direct[row, 0])
                                for row in range(2 * n_sites)
                            )
                            self.assertLess(residual, self.tolerance)

    def test_vacuum_and_saturated_full_space_states_are_fixed(self) -> None:
        for n_sites in (6, 10):
            vacuum = full_basis_state(n_sites)
            saturated = {(1 << (2 * n_sites)) - 1: mp.mpf(1)}
            self.assertEqual(
                margolus_step(vacuum, n_sites=n_sites, mu="2/9"), vacuum
            )
            self.assertEqual(
                margolus_step(saturated, n_sites=n_sites, mu="2/9"), saturated
            )

    def test_reverse_causal_order_inverts_a_multisector_state(self) -> None:
        with mp.workdps(90):
            for n_sites in (6, 10):
                state = self._multisector_state(n_sites)
                evolved = margolus_step(state, n_sites=n_sites, mu="3/5")
                recovered = margolus_inverse(
                    evolved, n_sites=n_sites, mu="3/5"
                )
                self.assertSparseClose(recovered, state)

    def test_full_space_update_commutes_with_cell_translation(self) -> None:
        with mp.workdps(90):
            state = self._multisector_state(6)
            left = margolus_step(
                translate_full(state, n_sites=6), n_sites=6, mu="2/9"
            )
            right = translate_full(
                margolus_step(state, n_sites=6, mu="2/9"), n_sites=6
            )
            self.assertSparseClose(left, right)

    def test_full_space_parity_commutes_with_update(self) -> None:
        with mp.workdps(90):
            state = self._multisector_state(6)
            left = margolus_step(
                parity_full(state, n_sites=6), n_sites=6, mu="2/9"
            )
            right = parity_full(
                margolus_step(state, n_sites=6, mu="2/9"), n_sites=6
            )
            self.assertSparseClose(left, right)

    def test_full_space_time_reversal_gives_inverse_update(self) -> None:
        with mp.workdps(90):
            state = self._multisector_state(6)
            transformed = time_reverse_full(state, n_sites=6)
            left = time_reverse_full(
                margolus_step(transformed, n_sites=6, mu="2/9"),
                n_sites=6,
            )
            right = margolus_inverse(state, n_sites=6, mu="2/9")
            self.assertSparseClose(left, right)

    def test_resource_clock_counts_both_explicit_layers(self) -> None:
        self.assertEqual(
            resource_clock(n_sites=10, macrosteps=7),
            {
                "local_hilbert_dimension": 4,
                "occupation_modes": 20,
                "ancilla_modes": 0,
                "macrosteps": 7,
                "elementary_layers": 14,
                "two_mode_gate_work": 140,
                "causal_radius_per_macrostep": 1,
                "gate_order": "edge_scatter_then_on_site_swap",
            },
        )


if __name__ == "__main__":
    unittest.main()
