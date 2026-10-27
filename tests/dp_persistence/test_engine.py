from __future__ import annotations

import unittest

import numpy as np

from src.dp_persistence import calibration_models, l0_engine, l0_replay, l1
from src.dp_persistence.l0_engine import A0, V, L0State, absorbing_certificate, geometry, initial_state, step
from src.dp_persistence.structural_audit import random_synthetic_state


def test_rng(label: int) -> np.random.Generator:
    """Non-registered synthetic stream (plain integer seed, no protocol domain)."""

    return np.random.Generator(np.random.PCG64(900_000 + label))


def idx(x: int, y: int, z: int, L: int) -> int:
    return (x * L + y) * L + z


def coords(i: int, L: int) -> tuple[int, int, int]:
    return (i // (L * L), (i // L) % L, i % L)


def ever_active(initial_fresh: np.ndarray, final: L0State) -> np.ndarray:
    fresh = initial_fresh.copy()
    fresh[final.geometry.seed_index] = False
    reached = (final.a > 0) | (fresh & (final.l == 0))
    reached[final.geometry.seed_index] = True
    return reached


class LedgerAndCertificateTests(unittest.TestCase):
    def test_exact_ledger_on_1000_random_9cubed_media(self) -> None:
        rng = test_rng(1)
        for trial in range(1000):
            fresh = rng.random(9 ** 3) < rng.uniform(0.0, 1.0)
            state = initial_state(fresh, 9)
            total = state.ledger_total()
            dynamics = test_rng(10_000 + trial)
            for _ in range(40):
                state, _ = step(state, dynamics)
                self.assertEqual(state.ledger_total(), total)
                if absorbing_certificate(state):
                    break

    def test_run_reports_zero_residual(self) -> None:
        rng = test_rng(2)
        for trial in range(50):
            fresh = rng.random(9 ** 3) < 0.6
            record = l0_engine.run_medium(fresh, test_rng(20_000 + trial), 200, 9, censor=False)
            self.assertEqual(record["ledger_residual"], 0)

    def test_certificate_is_exact(self) -> None:
        rng = test_rng(3)
        seen = {True: 0, False: 0}
        for i in range(1000):
            state = random_synthetic_state(rng, force_certificate=(i % 3 == 0))
            dynamics = test_rng(30_000 + i)
            before = dynamics.bit_generator.state
            after, record = step(state, dynamics)
            certificate = absorbing_certificate(state)
            seen[certificate] += 1
            if certificate:
                np.testing.assert_array_equal(after.a, state.a)
                np.testing.assert_array_equal(after.l, state.l)
                self.assertEqual(dynamics.bit_generator.state, before)
            else:
                self.assertGreaterEqual(record["sources"].size, 1)
        self.assertGreater(seen[True], 100)
        self.assertGreater(seen[False], 100)

    def test_light_cone(self) -> None:
        rng = test_rng(4)
        L = 15
        geo = geometry(L, l0_engine.default_seed(L))
        for trial in range(30):
            fresh = rng.random(L ** 3) < (1.0 if trial == 0 else rng.uniform(0.3, 1.0))
            state = initial_state(fresh, L)
            touched = state.a > 0
            dynamics = test_rng(40_000 + trial)
            for t in range(1, L // 2 + 1):
                state, record = step(state, dynamics)
                touched[record["touched"]] = True
                self.assertLessEqual(int(geo.chebyshev[touched].max()), t)

    def test_determinism(self) -> None:
        a = l0_engine.run(0.5, 7, 300, L=16)
        b = l0_engine.run(0.5, 7, 300, L=16)
        for key in a:
            if isinstance(a[key], np.ndarray):
                np.testing.assert_array_equal(a[key], b[key])
            else:
                self.assertEqual(a[key], b[key])
        c = l0_engine.run(0.5, 8, 300, L=16)
        self.assertFalse(np.array_equal(a["n_t"], c["n_t"]) and a["S"] == c["S"] and a["C"] == c["C"])


class ReplayAgreementTests(unittest.TestCase):
    FIELDS = ("absorbed_at", "censored_at", "ticks_run", "S", "C", "E", "stranded_amplitude", "ledger_residual")

    def assert_same(self, a: dict, b: dict) -> None:
        self.assertEqual([int(v) for v in a["n_t"]], list(b["n_t"]))
        self.assertEqual([int(v) for v in a["r2_sum_t"]], list(b["r2_sum_t"]))
        for key in self.FIELDS:
            self.assertEqual(a[key], b[key], key)

    def test_bit_identical_on_200_synthetic_cases(self) -> None:
        rng = test_rng(5)
        sizes = (5, 7, 9, 12, 16)
        for case in range(200):
            L = sizes[case % len(sizes)]
            fresh = rng.random(L ** 3) < rng.uniform(0.2, 1.0)
            sites = [coords(int(i), L) for i in np.flatnonzero(fresh)]
            censor = case % 2 == 0
            r_engine = test_rng(50_000 + case)
            r_replay = test_rng(50_000 + case)
            a = l0_engine.run_medium(fresh, r_engine, 400, L, censor=censor)
            b = l0_replay.replay_run(sites, L, r_replay, 400, censor=censor)
            self.assert_same(a, b)
            self.assertEqual(r_engine.bit_generator.state, r_replay.bit_generator.state)
            final_a = {coords(int(i), L): int(a["final_state"].a[i]) for i in np.flatnonzero(a["final_state"].a)}
            self.assertEqual(final_a, b["final_state"].active)
            fresh_after = (a["final_state"].a == 0) & (a["final_state"].l == V)
            self.assertEqual({coords(int(i), L) for i in np.flatnonzero(fresh_after)}, b["final_state"].fresh)

    def test_tracked_run_matches_full_lattice_steps(self) -> None:
        rng = test_rng(11)
        for case in range(60):
            L = (7, 9, 16)[case % 3]
            fresh = rng.random(L ** 3) < rng.uniform(0.2, 1.0)
            tracking = test_rng(90_000 + case)
            tracked = l0_engine.run_medium(fresh, tracking, 300, L, censor=False)
            state = initial_state(fresh, L)
            stepping = test_rng(90_000 + case)
            n_t = []
            for _ in range(tracked["ticks_run"]):
                state, record = step(state, stepping)
                n_t.append(int(record["touched"].size))
            self.assertEqual(list(tracked["n_t"]), n_t)
            np.testing.assert_array_equal(tracked["final_state"].a, state.a)
            np.testing.assert_array_equal(tracked["final_state"].l, state.l)
            self.assertEqual(tracked["S"], int((ever_active(fresh, state)).sum()))
            self.assertEqual(tracking.bit_generator.state, stepping.bit_generator.state)

    def test_run_does_not_mutate_its_input_state(self) -> None:
        fresh = test_rng(12).random(9 ** 3) < 0.7
        state = initial_state(fresh, 9)
        a, l = state.a.copy(), state.l.copy()
        l0_engine.run_from_state(state, test_rng(13), 50, censor=False)
        np.testing.assert_array_equal(state.a, a)
        np.testing.assert_array_equal(state.l, l)

    def test_registered_form_entry_points_agree_on_tiny_lattice(self) -> None:
        for run_seed in (1, 2, 3):
            self.assert_same(l0_engine.run(0.45, run_seed, 200, L=12), l0_replay.replay(0.45, run_seed, 200, size=12))


class BudgetAndStructureTests(unittest.TestCase):
    def test_equivalent_to_bfs_reached_set_when_budget_cannot_bind(self) -> None:
        rng = test_rng(6)
        L = 14
        geo = geometry(L, l0_engine.default_seed(L))
        compared = 0
        for trial in range(40):
            fresh = rng.random(L ** 3) < rng.uniform(0.3, 0.6)
            fresh[geo.seed_index] = False
            while True:
                degree = fresh[geo.neighbours].sum(axis=1)
                crowded = np.flatnonzero(fresh & (degree > V + 1))
                if crowded.size == 0:
                    break
                fresh[rng.choice(crowded)] = False
            self.assertTrue((fresh[geo.neighbours].sum(axis=1)[fresh] <= V + 1).all())
            record = l0_engine.run_medium(fresh, test_rng(60_000 + trial), 10_000, L, censor=False)
            self.assertIsNotNone(record["absorbed_at"])
            bfs = calibration_models.run_site_bfs_on_medium(fresh, 10_000, L, censor=False)
            np.testing.assert_array_equal(ever_active(fresh, record["final_state"]), bfs["reached"])
            self.assertEqual(record["E"] if record["C"] else 1.0, 1.0)
            compared += int(bfs["reached"].sum() > 1)
        self.assertGreater(compared, 10)

    def test_below_threshold_absorption_on_finite_cluster(self) -> None:
        L = 16
        fresh = np.zeros(L ** 3, dtype=bool)
        for site in [(9, 8, 8), (10, 8, 8), (11, 8, 8), (11, 9, 8), (11, 10, 8), (10, 9, 8), (8, 8, 9), (8, 8, 10)]:
            fresh[idx(*site, L)] = True
        fresh[idx(1, 1, 1, L)] = True  # disconnected
        record = l0_engine.run_medium(fresh, test_rng(7), 1000, L)
        self.assertIsNotNone(record["absorbed_at"])
        self.assertIsNone(record["censored_at"])
        self.assertEqual(record["C"], 8)
        self.assertLessEqual(record["S"] - 1, record["C"])
        self.assertEqual(record["ledger_residual"], 0)
        self.assertEqual(record["stranded_amplitude"], int(record["final_state"].a.sum()))

    def test_stranding_example(self) -> None:
        L = 9
        fresh = np.zeros(L ** 3, dtype=bool)
        hub = (5, 4, 4)
        fresh[idx(*hub, L)] = True
        leaves = [(6, 4, 4), (5, 5, 4), (5, 3, 4), (5, 4, 5), (5, 4, 3)]
        for leaf in leaves:
            fresh[idx(*leaf, L)] = True
        for trial in range(20):
            record = l0_engine.run_medium(fresh, test_rng(70_000 + trial), 100, L, censor=False)
            final = record["final_state"]
            self.assertIsNotNone(record["absorbed_at"])
            self.assertEqual(final.a[idx(*hub, L)], 0)  # a = 3 exhausted after serving 3
            served = sum(1 for leaf in leaves if final.l[idx(*leaf, L)] == 0)
            self.assertEqual(served, 3)
            self.assertEqual(record["S"], 5)
            self.assertEqual(record["C"], 6)
            self.assertAlmostEqual(record["E"], 4 / 6)
            self.assertEqual(record["stranded_amplitude"], (A0 - 1) + 3 * (V + 1))

    def test_l1_reactivates_a_configuration_stranded_under_l0(self) -> None:
        L = 9
        fresh = np.zeros(L ** 3, dtype=bool)
        fresh[idx(5, 4, 4, L)] = True
        record = l0_engine.run_medium(fresh, test_rng(8), 50, L, censor=False)
        state = record["final_state"]
        self.assertTrue(absorbing_certificate(state))
        self.assertTrue(l1.l1_absorbing(state, 0.0))
        for r in (0.02, 0.2, 1e-6):
            self.assertFalse(l1.l1_absorbing(state, r))
        total = state.ledger_total()
        rng = test_rng(9)
        transfers = 0
        for _ in range(2000):
            state, tick = l1.step(state, rng, 0.02)
            transfers += int(tick["sources"].size)
            self.assertEqual(state.ledger_total(), total)
            self.assertFalse(l1.l1_absorbing(state, 0.02))
        self.assertGreater(transfers, 0)


if __name__ == "__main__":
    unittest.main()
