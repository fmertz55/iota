from __future__ import annotations

import unittest

import numpy as np

from src.dp_persistence import calibration_models as cm
from src.dp_persistence.l0_engine import default_seed, geometry, seed_adjacent_fresh_cluster_size


def test_rng(label: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(700_000 + label))


def manhattan_ball(t: int) -> int:
    """Lattice points with |x| + |y| + |z| <= t."""

    return sum(
        1
        for x in range(-t, t + 1)
        for y in range(-t, t + 1)
        for z in range(-t, t + 1)
        if abs(x) + abs(y) + abs(z) <= t
    )


class ZeroControlTests(unittest.TestCase):
    def test_p_zero_dies_immediately(self) -> None:
        cases = [
            cm.run_domany_kinzel(0.0, 0.0, test_rng(1), 100, 64),
            cm.run_bond_dp_3(0.0, test_rng(2), 100, 16),
            cm.run_sir_3(0.0, test_rng(3), 100, 16),
            cm.run_site_bfs_3(0.0, test_rng(4), 100, 16),
        ]
        for record in cases:
            self.assertEqual(record["absorbed_at"], 1)
            self.assertEqual(list(record["n_t"]), [0])
            self.assertEqual(record["S"], 1)

    def test_dk_probabilities(self) -> None:
        self.assertEqual(cm.dk_probabilities(cm.DK_BOND, 0.5), (0.5, 0.75))
        self.assertEqual(cm.dk_probabilities(cm.DK_SITE, 0.5), (0.5, 0.5))


class LightConeTests(unittest.TestCase):
    def test_dk_full_occupation_fills_the_light_cone(self) -> None:
        L = 256
        record = cm.run_domany_kinzel(1.0, 1.0, test_rng(5), 60, L, censor=False)
        for t in range(1, 61):
            self.assertEqual(record["n_t"][t - 1], t + 1)
            expected_r2 = sum(d * d for d in range(-t, t + 1, 2))
            self.assertEqual(record["r2_sum_t"][t - 1], expected_r2)
        self.assertIsNone(record["absorbed_at"])

    def test_bond_dp_full_occupation_is_the_manhattan_ball(self) -> None:
        record = cm.run_bond_dp_3(1.0, test_rng(6), 5, 16, censor=False)
        self.assertEqual(list(record["n_t"]), [manhattan_ball(t) for t in range(1, 6)])

    def test_sir_and_bfs_full_occupation_are_the_manhattan_shell(self) -> None:
        shells = [manhattan_ball(t) - manhattan_ball(t - 1) for t in range(1, 6)]
        self.assertEqual(list(cm.run_sir_3(1.0, test_rng(7), 5, 16, censor=False)["n_t"]), shells)
        self.assertEqual(list(cm.run_site_bfs_3(1.0, test_rng(8), 5, 16, censor=False)["n_t"]), shells)

    def test_censoring_radius(self) -> None:
        L = 16
        record = cm.run_site_bfs_3(1.0, test_rng(9), 100, L)
        self.assertEqual(record["censored_at"], L // 2 - 4)  # Chebyshev reach of the shell
        dk = cm.run_domany_kinzel(1.0, 1.0, test_rng(10), 100, 32)
        self.assertEqual(dk["censored_at"], 32 // 2 - 4)


class BreadthFirstClusterTests(unittest.TestCase):
    def test_reached_set_equals_the_connected_cluster(self) -> None:
        rng = test_rng(11)
        L = 16
        geo = geometry(L, default_seed(L))
        for trial in range(25):
            open_sites = rng.random(L ** 3) < rng.uniform(0.2, 0.5)
            record = cm.run_site_bfs_on_medium(open_sites, 10_000, L, censor=False)
            # Independent flood fill from the seed through open sites.
            mask = open_sites.copy()
            mask[geo.seed_index] = True
            seen = {geo.seed_index}
            stack = [geo.seed_index]
            while stack:
                site = stack.pop()
                for neighbour in geo.neighbours[site]:
                    neighbour = int(neighbour)
                    if mask[neighbour] and neighbour not in seen:
                        seen.add(neighbour)
                        stack.append(neighbour)
            self.assertEqual(set(np.flatnonzero(record["reached"]).tolist()), seen)
            self.assertEqual(record["S"] - 1, seed_adjacent_fresh_cluster_size(open_sites, L))
            self.assertIsNotNone(record["absorbed_at"])

    def test_generation_order_is_chemical_distance(self) -> None:
        L = 16
        open_sites = np.zeros(L ** 3, dtype=bool)
        path = [(9, 8, 8), (10, 8, 8), (10, 9, 8), (10, 10, 8)]
        for x, y, z in path:
            open_sites[(x * L + y) * L + z] = True
        record = cm.run_site_bfs_on_medium(open_sites, 100, L, censor=False)
        self.assertEqual(list(record["n_t"]), [1, 1, 1, 1, 0])
        self.assertEqual(record["absorbed_at"], 5)


class DeterminismTests(unittest.TestCase):
    def test_same_stream_same_run(self) -> None:
        for runner in (
            lambda r: cm.run_domany_kinzel(0.7, 0.9, r, 200, 128),
            lambda r: cm.run_bond_dp_3(0.2, r, 50, 16),
            lambda r: cm.run_sir_3(0.3, r, 50, 16),
        ):
            a, b = runner(test_rng(12)), runner(test_rng(12))
            np.testing.assert_array_equal(a["n_t"], b["n_t"])
            self.assertEqual(a["S"], b["S"])


if __name__ == "__main__":
    unittest.main()
