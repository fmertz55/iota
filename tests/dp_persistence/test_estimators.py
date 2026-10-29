from __future__ import annotations

import math
import unittest

import numpy as np

from src.dp_persistence import classifier, estimators as est, estimators_replay as rep
from synthetic import (
    cluster_tail_ledger,
    exponential_ledger,
    flat_ledger,
    plateau_ledger,
    power_law_ledger,
)


RESAMPLES = 200
CLASSES = {
    "DP_1p1": (0.159464, 0.313686, 1.580745, "1p1"),
    "DP_3p1": (0.736, 0.11, 1.9, "3d"),
    "DyP_3": (0.34681, 0.48725, 1.3756, "3d"),
}


def boot(seed: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(500_000 + seed))


def evaluate(records, key="3d", horizon=1024, seed=0):
    return est.evaluate_point(records, t_min=est.t_min_for(key), horizon=horizon, boot_rng=boot(seed), resamples=RESAMPLES)


def replay(records, key="3d", horizon=1024, seed=0):
    return rep.replay_point(records, t_min=est.t_min_for(key), horizon=horizon, boot_rng=boot(seed), resamples=RESAMPLES)


def max_difference(a, b, path="") -> float:
    """Largest |a - b| / max(1, |a|) over matching nested structures."""

    if isinstance(a, dict):
        assert set(a) == set(b), (path, set(a) ^ set(b))
        return max([max_difference(a[k], b[k], f"{path}.{k}") for k in a] or [0.0])
    if isinstance(a, (list, tuple, np.ndarray)):
        assert len(a) == len(b), path
        return max([max_difference(x, y, path) for x, y in zip(a, b)] or [0.0])
    if a is None or b is None:
        assert a is None and b is None, (path, a, b)
        return 0.0
    if isinstance(a, (str, bool)):
        assert a == b, (path, a, b)
        return 0.0
    if math.isnan(a):
        assert math.isnan(b), path
        return 0.0
    return abs(a - b) / max(1.0, abs(a))


class ExactPowerLawTests(unittest.TestCase):
    def test_each_registered_class_is_recovered(self) -> None:
        for class_id, (delta, theta, z, key) in CLASSES.items():
            records = power_law_ledger(delta, theta, z, runs=4000, horizon=2048)
            point = evaluate(records, key, horizon=2048)
            self.assertEqual(point.criticality, "critical_compatible", class_id)
            estimates = est.exponent_estimates(point)
            self.assertAlmostEqual(estimates["delta"]["value"], delta, delta=0.01)
            self.assertAlmostEqual(estimates["theta_or_eta"]["value"], theta, delta=0.01)
            self.assertAlmostEqual(estimates["z"]["value"], z, delta=0.01)
            result = classifier.classify(estimates, key)
            self.assertEqual(result["verdict"], class_id)
            self.assertTrue(result["hyperscaling"][class_id]["passes"])

    def test_flat_survival_is_not_critical(self) -> None:
        point = evaluate(flat_ledger())
        self.assertEqual(point.criticality, "no_absorption_observed")
        self.assertEqual(est.bracketing_class(point.criticality), "supercritical")

    def test_too_few_absorbed_runs_is_no_absorption(self) -> None:
        records = flat_ledger(runs=10000)
        for record in records[:60]:  # 0.6% < 1%
            record["absorbed_at"] = 20
            record["n_t"] = record["n_t"][:19]
        self.assertEqual(evaluate(records).criticality, "no_absorption_observed")

    def test_exponential_decay_is_subcritical(self) -> None:
        point = evaluate(exponential_ledger(80.0))
        self.assertEqual(point.criticality, "subcritical")
        self.assertGreater(point.slope_s, 0)

    def test_plateau_is_supercritical(self) -> None:
        point = evaluate(plateau_ledger(0.3))
        self.assertEqual(point.criticality, "supercritical")
        self.assertLess(point.slope_s, 0)

    def test_ladder_and_admissible_points(self) -> None:
        self.assertEqual(est.geometric_ladder(16, 64), [16, 19, 23, 27, 32, 38, 45, 54, 64])
        point = evaluate(power_law_ledger(0.34681, 0.48725, 1.3756, runs=2000, horizon=256), horizon=256)
        ticks = [entry["t"] for entry in point.ladder]
        self.assertEqual(ticks, est.geometric_ladder(16, 256))
        for entry in point.ladder:
            admissible = entry["t"] / est.M >= 16
            self.assertEqual(entry["delta_eff"] is not None, admissible)


class CensoringTests(unittest.TestCase):
    def censored_ledger(self, censor_tick: int, fraction: float, runs: int = 4000):
        records = power_law_ledger(0.34681, 0.48725, 1.3756, runs=runs, horizon=1024)
        alive_at_end = [r for r in records if r["absorbed_at"] is None]
        for record in alive_at_end[: int(fraction * runs)]:
            record["censored_at"] = censor_tick
            record["absorbed_at"] = None
            record["n_t"] = record["n_t"][:censor_tick]
            record["r2_sum_t"] = record["r2_sum_t"][:censor_tick]
        return records

    def test_fit_window_upper(self) -> None:
        records = self.censored_ledger(300, 0.02)
        self.assertEqual(est.fit_window_upper(est.RunTable.from_records(records), 1024), 299)
        self.assertEqual(evaluate(records).t_max, 299)
        records = self.censored_ledger(300, 0.005)
        self.assertEqual(est.fit_window_upper(est.RunTable.from_records(records), 1024), 1024)

    def test_window_too_short(self) -> None:
        point = evaluate(self.censored_ledger(40, 0.02))
        self.assertEqual(point.t_max, 39)
        self.assertEqual(point.criticality, "window_too_short")

    def test_censored_runs_leave_the_aggregates(self) -> None:
        records = self.censored_ledger(300, 0.02)
        point = evaluate(records)
        table = est.RunTable.from_records(records)
        for entry in point.ladder:
            t = entry["t"]
            uncensored = table.censored > t
            alive = table.absorbed > t
            self.assertAlmostEqual(entry["P"], (alive & uncensored).sum() / uncensored.sum(), places=14)
        self.assertAlmostEqual(point.censored_run_fraction, 0.02)


class ExponentAndClassifierTests(unittest.TestCase):
    def estimate(self, value, se=0.0):
        return {"value": value, "statistical_se": se, "systematic_se": 0.0, "total_se": se}

    def test_systematic_se_from_bracket_endpoints(self) -> None:
        final = evaluate(power_law_ledger(0.34681, 0.48725, 1.3756))
        lower = evaluate(power_law_ledger(0.40, 0.45, 1.40))
        upper = evaluate(power_law_ledger(0.30, 0.52, 1.35))
        estimates = est.exponent_estimates(final, lower, upper)
        self.assertAlmostEqual(
            estimates["delta"]["systematic_se"],
            abs(lower.exponents["delta"] - upper.exponents["delta"]) / 2,
        )
        for value in estimates.values():
            self.assertAlmostEqual(value["total_se"], math.hypot(value["statistical_se"], value["systematic_se"]))

    def test_per_exponent_rules(self) -> None:
        self.assertEqual(classifier.per_exponent(self.estimate(1.07), 1.0, 0.08), "agrees")
        self.assertEqual(classifier.per_exponent(self.estimate(1.20, 0.01), 1.0, 0.08), "disagrees")
        self.assertEqual(classifier.per_exponent(self.estimate(1.09, 0.01), 1.0, 0.08), "indeterminate")

    def test_hyperscaling_downgrade(self) -> None:
        estimates = {
            "delta": self.estimate(0.666),
            "theta_or_eta": self.estimate(0.18),
            "z": self.estimate(1.76),
        }
        result = classifier.classify(estimates, "3d")
        self.assertEqual(set(result["per_exponent"]["DP_3p1"].values()), {"agrees"})
        self.assertFalse(result["hyperscaling"]["DP_3p1"]["passes"])
        self.assertEqual(result["per_class"]["DP_3p1"], "indeterminate")
        self.assertEqual(result["per_class"]["DyP_3"], "excluded")
        self.assertEqual(result["verdict"], "indeterminate")

    def test_none_of_registered(self) -> None:
        estimates = {"delta": self.estimate(1.5), "theta_or_eta": self.estimate(-1.0), "z": self.estimate(3.0)}
        self.assertEqual(classifier.classify(estimates, "3d")["verdict"], "none_of_registered")

    def test_reference_values_come_from_the_spec(self) -> None:
        self.assertEqual(classifier.reference_exponent("DyP_3", "theta_or_eta"), 0.48725)
        self.assertEqual(classifier.reference_exponent("DP_3p1", "theta_or_eta"), 0.11)
        self.assertEqual(classifier.tolerance("1p1", "theta_or_eta"), 0.03)

    def test_hypothesis_outcomes(self) -> None:
        self.assertEqual(classifier.h1_outcome(0.3136, 0.001), "equal")
        self.assertEqual(classifier.h1_outcome(0.33, 0.001), "budget_shifted")
        self.assertEqual(classifier.h1_outcome(0.318, 0.01), "indeterminate")
        self.assertEqual(classifier.h1_outcome(0.29, 0.001), "instrument_failure")
        dyp_like = {
            "per_exponent": {"DyP_3": {"delta": "agrees", "theta_or_eta": "agrees", "z": "disagrees"}},
            "verdict": "none_of_registered",
        }
        self.assertEqual(classifier.h2_outcome("equal", dyp_like), "percolation_statics_non_epidemic_dynamics")
        self.assertEqual(classifier.h2_outcome("budget_shifted", dyp_like), "not_applicable")
        self.assertEqual(classifier.h3_outcome("indeterminate", None), "not_applicable")
        tail = {"status": "estimated", "tau_minus_2": self.estimate(0.20, 0.01)}
        self.assertEqual(classifier.h3_outcome("equal", tail), "supported")
        tail = {"status": "estimated", "tau_minus_2": self.estimate(0.30, 0.01)}
        self.assertEqual(classifier.h3_outcome("equal", tail), "falsified")
        self.assertEqual(classifier.h3_outcome("equal", {"status": "range_too_short", "s_cut": 100}), "indeterminate")


class StaticTailTests(unittest.TestCase):
    def test_exact_tail_recovers_tau_minus_two(self) -> None:
        point = est.static_tail_point(cluster_tail_ledger(0.18906), boot_rng=boot(1), resamples=RESAMPLES)
        self.assertEqual(point["status"], "estimated")
        self.assertAlmostEqual(point["value"], 0.18906, delta=0.002)

    def test_censoring_sets_s_cut(self) -> None:
        point = est.static_tail_point(cluster_tail_ledger(0.18906, censor_above=5000), boot_rng=boot(2), resamples=RESAMPLES)
        self.assertEqual(point["s_cut"], 5000)
        self.assertAlmostEqual(point["value"], 0.18906, delta=0.005)

    def test_range_too_short(self) -> None:
        point = est.static_tail_point(cluster_tail_ledger(0.18906, censor_above=200), boot_rng=boot(3), resamples=RESAMPLES)
        self.assertEqual(point["status"], "range_too_short")
        self.assertNotIn("tau_minus_2", est.static_tail_estimate(point))


class BracketingTests(unittest.TestCase):
    @staticmethod
    def fake(threshold_classes):
        """evaluate() whose class depends only on the control value."""

        def evaluate_fn(control, role, index):
            kind, slope = threshold_classes(control)
            evaluation = est.PointEvaluation(
                t_min=16, t_max=1000, criticality=kind, slope_s=slope,
                slope_ci95=[slope - 0.1, slope + 0.1] if slope is not None else None,
                ladder=[], censored_run_fraction=0.0, runs=10,
            )
            return est.EvaluatedPoint(control, role, evaluation)

        return evaluate_fn

    @staticmethod
    def sharp(pc):
        return lambda c: ("subcritical", 1.0) if c < pc else ("no_absorption_observed", None) if c > 0.5 else ("supercritical", -1.0)

    def test_single_bracket_and_arithmetic_bisection(self) -> None:
        search = est.bracket_search(self.fake(self.sharp(0.3116)), [0.25, 0.30, 0.32, 0.40, 0.70], 6, "arithmetic")
        self.assertEqual(search.terminal_status, "classified")
        self.assertEqual(search.brackets, [[0.30, 0.32]])
        lo, hi = search.final_bracket
        self.assertLess(lo.control, 0.3116)
        self.assertGreater(hi.control, 0.3116)
        self.assertAlmostEqual(hi.control - lo.control, 0.02 / 2 ** 6)
        self.assertAlmostEqual(search.final_control, (lo.control + hi.control) / 2)

    def test_geometric_bisection(self) -> None:
        search = est.bracket_search(self.fake(self.sharp(0.05)), [0.01, 0.1], 1, "geometric")
        self.assertAlmostEqual(search.points[-1].control, math.sqrt(0.001))

    def test_multiple_brackets(self) -> None:
        def classes(c):
            if c < 0.3 or 0.4 < c < 0.5:
                return "subcritical", 1.0
            return "supercritical", -1.0

        search = est.bracket_search(self.fake(classes), [0.2, 0.35, 0.45, 0.6], 2, "arithmetic")
        self.assertEqual(search.terminal_status, "multiple_brackets")
        self.assertEqual(search.brackets, [[0.2, 0.35], [0.45, 0.6]])
        self.assertLessEqual(search.final_bracket[1].control, 0.35)

    def test_no_bracket(self) -> None:
        search = est.bracket_search(self.fake(lambda c: ("supercritical", -1.0)), [0.2, 0.3], 6, "arithmetic")
        self.assertEqual(search.terminal_status, "no_bracket_in_registered_range")
        self.assertIsNone(search.final_control)

    def test_critical_midpoint_is_retained_and_selected(self) -> None:
        def classes(c):
            if abs(c - 0.3) < 0.011:
                return "critical_compatible", (c - 0.3) * 0.1
            return ("subcritical", 2.0) if c < 0.3 else ("supercritical", -1.0)

        search = est.bracket_search(self.fake(classes), [0.28, 0.32], 3, "arithmetic")
        roles = [(p.role, round(p.control, 4), p.evaluation.criticality) for p in search.points]
        self.assertEqual(roles[2], ("bisection", 0.3, "critical_compatible"))
        # |s| at 0.32 (1.0) < |s| at 0.28 (2.0): the upper end is nearer the
        # threshold, so the critical midpoint replaces the lower end.
        self.assertAlmostEqual(search.points[3].control, 0.31)
        # Then 0.30 (|s| ~ 0) is the nearer end, and the midpoints replace the upper end.
        self.assertAlmostEqual(search.points[4].control, 0.305)
        lo, hi = search.final_bracket
        self.assertAlmostEqual(lo.control, 0.30)
        self.assertAlmostEqual(hi.control, 0.305)
        # The critical point with the smallest |s| inside the final bracket.
        self.assertAlmostEqual(search.final_control, 0.30)

    def test_critical_midpoint_bracket_keeps_the_threshold(self) -> None:
        for threshold in (0.302, 0.309, 0.311, 0.318):
            def classes(c, pc=threshold):
                s = 5.0 * (pc - c)
                return ("critical_compatible", s) if abs(s) < 0.06 else (("subcritical", s) if s > 0 else ("supercritical", s))

            search = est.bracket_search(self.fake(classes), [0.29, 0.33], 6, "arithmetic")
            lo, hi = search.final_bracket
            self.assertLessEqual(lo.control, threshold)
            self.assertGreaterEqual(hi.control, threshold)

    def test_critical_coarse_points_lie_inside_the_bracket(self) -> None:
        def classes(c):
            if 0.305 < c < 0.325:
                return "critical_compatible", 0.01 * (c - 0.31)
            return ("subcritical", 1.0) if c < 0.31 else ("supercritical", -1.0)

        search = est.bracket_search(self.fake(classes), [0.29, 0.30, 0.31, 0.32, 0.33, 0.35], 0, "arithmetic")
        self.assertEqual(search.terminal_status, "classified")
        self.assertEqual(search.brackets, [[0.30, 0.33]])
        # With no bisection, the critical coarse point with the smallest |s| is final.
        self.assertAlmostEqual(search.final_control, 0.31)

    def test_other_classes_break_a_bracket(self) -> None:
        def classes(c):
            if abs(c - 0.31) < 0.001:
                return "window_too_short", None
            return ("subcritical", 1.0) if c < 0.31 else ("supercritical", -1.0)

        search = est.bracket_search(self.fake(classes), [0.30, 0.31, 0.32], 6, "arithmetic")
        self.assertEqual(search.terminal_status, "no_bracket_in_registered_range")

    def test_only_the_last_subcritical_point_starts_a_bracket(self) -> None:
        def classes(c):
            if c in (0.31, 0.32):
                return "critical_compatible", 0.0
            return ("subcritical", 1.0) if c < 0.31 else ("supercritical", -1.0)

        pairs = est.adjacent_brackets(
            [self.fake(classes)(c, "coarse", i) for i, c in enumerate([0.33, 0.29, 0.31, 0.30, 0.32])]
        )
        self.assertEqual([[a.control, b.control] for a, b in pairs], [[0.30, 0.33]])

    def test_threshold_estimate(self) -> None:
        lo = self.fake(lambda c: ("subcritical", 1.0))(0.31, "x", 0)
        hi = self.fake(lambda c: ("supercritical", -1.0))(0.33, "x", 0)
        lo.evaluation.slope_boot = np.array([1.0, 0.5, -0.1])
        hi.evaluation.slope_boot = np.array([-1.0, -0.5, -0.2])
        value = est.threshold_estimate(lo, hi)
        self.assertAlmostEqual(value["value"], 0.32)
        self.assertAlmostEqual(value["systematic_se"], 0.01)
        crossings = [0.32, 0.32, 0.31]
        self.assertAlmostEqual(value["statistical_se"], float(np.std(crossings, ddof=1)))


class ReplayAgreementTests(unittest.TestCase):
    TOLERANCE = 1e-12

    def compare_point(self, records, key="3d", horizon=1024):
        primary = evaluate(records, key, horizon)
        independent = replay(records, key, horizon)
        summary = primary.summary()
        self.assertLessEqual(max_difference(summary, {k: independent[k] for k in summary}), self.TOLERANCE)
        self.assertEqual(primary.crossover_in_window, independent["crossover_in_window"])
        if primary.exponents:
            a = est.exponent_estimates(primary)
            b = rep.replay_exponents(independent)
            self.assertLessEqual(max_difference(a, b), self.TOLERANCE)
            self.assertLessEqual(max_difference(classifier.classify(a, key), rep.replay_classify(b, key)), self.TOLERANCE)
            self.assertLessEqual(max_difference(primary.slope_boot, independent["slope_boot"]), self.TOLERANCE)
        return primary, independent

    def test_agreement_on_every_synthetic_ledger(self) -> None:
        for class_id, (delta, theta, z, key) in CLASSES.items():
            self.compare_point(power_law_ledger(delta, theta, z, runs=2000, horizon=1024), key)
        self.compare_point(exponential_ledger(80.0))
        self.compare_point(plateau_ledger(0.3))
        self.compare_point(flat_ledger())
        self.compare_point(CensoringTests().censored_ledger(300, 0.02))
        self.compare_point(CensoringTests().censored_ledger(40, 0.02))

    def test_static_tail_agreement(self) -> None:
        for censor in (None, 5000, 200):
            records = cluster_tail_ledger(0.18906, runs=5000, censor_above=censor)
            a = est.static_tail_point(records, boot_rng=boot(4), resamples=50)
            b = rep.replay_static(records, boot_rng=boot(4), resamples=50)
            self.assertEqual(a["status"], b["status"])
            self.assertEqual(a["s_cut"], b["s_cut"])
            self.assertLessEqual(
                max_difference(est.static_tail_estimate(a), rep.replay_static_estimate(b)), self.TOLERANCE
            )

    def test_bracketing_and_hypotheses_agreement(self) -> None:
        def classes(c):
            if abs(c - 0.312) < 0.004:
                return "critical_compatible", (c - 0.312) * 3
            return ("subcritical", 0.5) if c < 0.312 else ("supercritical", -0.5)

        grid = [0.25, 0.28, 0.30, 0.31, 0.32, 0.33, 0.35, 0.40, 0.50, 0.70]
        for kind in ("arithmetic", "geometric"):
            a = est.bracket_search(BracketingTests.fake(classes), grid, 6, kind)
            b = rep.replay_bracket(
                lambda c, r, i: {
                    "criticality": classes(c)[0],
                    "slope_s": classes(c)[1],
                },
                grid,
                6,
                kind,
            )
            self.assertEqual(a.terminal_status, b["status"])
            self.assertEqual(a.brackets, b["brackets"])
            self.assertEqual([p.control for p in a.points], [c for c, _ in b["seen"]])
            self.assertLessEqual(abs(a.final_control - b["final"]), self.TOLERANCE)
        lo = BracketingTests.fake(lambda c: ("subcritical", 1.0))(0.31, "x", 0)
        hi = BracketingTests.fake(lambda c: ("supercritical", -1.0))(0.33, "x", 0)
        lo.evaluation.slope_boot = boot(5).normal(0.3, 0.2, 100)
        hi.evaluation.slope_boot = boot(6).normal(-0.3, 0.2, 100)
        t1 = est.threshold_estimate(lo, hi)
        t2 = rep.replay_threshold(0.31, 0.33, lo.evaluation.slope_boot, hi.evaluation.slope_boot)
        self.assertLessEqual(max_difference(t1, t2), self.TOLERANCE)
        for rho_c, se in ((0.3136, 0.001), (0.33, 0.001), (0.318, 0.01), (0.29, 0.001)):
            self.assertEqual(classifier.h1_outcome(rho_c, se), rep.replay_h1(rho_c, se))


if __name__ == "__main__":
    unittest.main()
