"""Shared spreading instrument (estimators.json), primary implementation.

Applied without modification to every calibration model and to IOTA-MIN-L0.
Readings of underspecified fields are listed in SPEC_QUESTIONS.md (Q-EST-*).

Run records use the engine convention: ``n_t[i]`` and ``r2_sum_t[i]`` are tick
``i + 1``; values after a run stopped are zero.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

import numpy as np

from .protocol import spec


M = 4
LADDER_STEPS_PER_OCTAVE = 4
BOOTSTRAP_RESAMPLES = 1000
CENSOR_FRACTION = 0.01
MIN_ABSORBED_FRACTION = 0.01
MIN_ABSORBED_RUNS = 50
STATIC_S_MIN = 16
STATIC_MIN_S_CUT = 256
EXPONENTS = ("delta", "theta_or_eta", "z")


def t_min_for(dimension_key: str) -> int:
    return int(spec("estimators.json")["censoring"]["fit_window_lower"][dimension_key])


def round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def geometric_ladder(start: int, upper: float) -> list[int]:
    """``round(start * 2^(k/4))`` for k = 0, 1, ... while the value <= upper."""

    ladder: list[int] = []
    k = 0
    while True:
        value = round_half_up(start * 2.0 ** (k / LADDER_STEPS_PER_OCTAVE))
        if value > upper:
            return ladder
        if not ladder or value != ladder[-1]:
            ladder.append(value)
        k += 1


def partner_tick(t: int) -> int:
    """Integer tick standing for t/m (Q-EST-1)."""

    return round_half_up(t / M)


# ----------------------------------------------------------------------------
# Run table
# ----------------------------------------------------------------------------


@dataclass
class RunTable:
    absorbed: np.ndarray  # float, inf when never absorbed
    censored: np.ndarray  # float, inf when never censored
    runs: list[dict[str, Any]]

    @classmethod
    def from_records(cls, records: Sequence[dict[str, Any]]) -> "RunTable":
        def column(key: str) -> np.ndarray:
            return np.array(
                [math.inf if r[key] is None else float(r[key]) for r in records], dtype=float
            )

        return cls(column("absorbed_at"), column("censored_at"), list(records))

    @property
    def size(self) -> int:
        return int(self.absorbed.size)

    def values_at(self, key: str, ticks: Sequence[int]) -> np.ndarray:
        out = np.zeros((self.size, len(ticks)), dtype=float)
        for i, record in enumerate(self.runs):
            series = record[key]
            length = len(series)
            for j, t in enumerate(ticks):
                if 1 <= t <= length:
                    out[i, j] = float(series[t - 1])
        return out


def fit_window_upper(table: RunTable, horizon: int) -> int | None:
    """Largest t <= horizon with (alive and censored_at <= t) / runs <= 0.01."""

    # A run counts on the ticks c <= t < a (censored at c, absorbed at a).
    counts = np.zeros(horizon + 2, dtype=np.int64)
    for c, a in zip(table.censored, table.absorbed):
        if not math.isfinite(c):
            continue
        start = max(int(c), 1)
        stop = horizon + 1 if not math.isfinite(a) else min(int(a), horizon + 1)
        if start < stop:
            counts[start] += 1
            counts[stop] -= 1
    fraction = np.cumsum(counts)[1 : horizon + 1] / table.size
    allowed = np.flatnonzero(fraction <= CENSOR_FRACTION)
    if allowed.size == 0:
        return None
    return int(allowed[-1] + 1)


# ----------------------------------------------------------------------------
# Aggregates and local slopes
# ----------------------------------------------------------------------------


@dataclass
class _Matrices:
    ticks: list[int]
    uncensored: np.ndarray
    alive_uncensored: np.ndarray
    n_uncensored: np.ndarray
    r2_alive: np.ndarray
    n_alive: np.ndarray


def _matrices(table: RunTable, ticks: list[int]) -> _Matrices:
    t = np.asarray(ticks, dtype=float)[None, :]
    uncensored = (table.censored[:, None] > t).astype(float)
    alive = (table.absorbed[:, None] > t).astype(float)
    n = table.values_at("n_t", ticks)
    r2 = table.values_at("r2_sum_t", ticks)
    alive_uncensored = alive * uncensored
    return _Matrices(
        ticks,
        uncensored,
        alive_uncensored,
        n * uncensored,
        r2 * alive_uncensored,
        n * alive_uncensored,
    )


def _ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denominator > 0, numerator / np.where(denominator > 0, denominator, 1), np.nan)


def _aggregates(mats: _Matrices, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    u = weights @ mats.uncensored
    P = _ratio(weights @ mats.alive_uncensored, u)
    N = _ratio(weights @ mats.n_uncensored, u)
    R2 = _ratio(weights @ mats.r2_alive, weights @ mats.n_alive)
    return P, N, R2


def _log_ratio(values: np.ndarray, upper: np.ndarray, lower: np.ndarray) -> np.ndarray:
    a = values[upper]
    b = values[lower]
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.log(a / b) / math.log(M)
    result[~np.isfinite(result)] = np.nan
    return result


def _local_slopes(P, N, R2, upper_idx, lower_idx) -> dict[str, np.ndarray]:
    two_over_z = _log_ratio(R2, upper_idx, lower_idx)
    with np.errstate(divide="ignore", invalid="ignore"):
        z_eff = 2.0 / two_over_z
    z_eff[~np.isfinite(z_eff)] = np.nan
    return {
        "delta": -_log_ratio(P, upper_idx, lower_idx),
        "theta_or_eta": _log_ratio(N, upper_idx, lower_idx),
        "two_over_z": two_over_z,
        "z": z_eff,
    }


def _weighted_slope(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    W = w.sum()
    xm = (w * x).sum() / W
    ym = (w * y).sum() / W
    return float((w * (x - xm) * (y - ym)).sum() / (w * (x - xm) ** 2).sum())


def _upper_half(values: np.ndarray) -> np.ndarray:
    return values[len(values) // 2:]


def _nanmean_or_nan(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    return float(finite.mean()) if finite.size else math.nan


def _none(value: float) -> float | None:
    return None if value is None or not math.isfinite(value) else float(value)


def _strictly_monotone(series: np.ndarray) -> bool:
    finite = series[np.isfinite(series)]
    if finite.size < 3:
        return False
    d = np.diff(finite)
    return bool((d > 0).all() or (d < 0).all())


@dataclass
class PointEvaluation:
    t_min: int
    t_max: int | None
    criticality: str
    slope_s: float | None
    slope_ci95: list[float] | None
    ladder: list[dict[str, Any]]
    censored_run_fraction: float
    runs: int
    exponents: dict[str, float] = field(default_factory=dict)
    exponent_boot: dict[str, np.ndarray] = field(default_factory=dict)
    slope_boot: np.ndarray | None = None
    crossover_in_window: bool = False

    def summary(self) -> dict[str, Any]:
        return {
            "t_min": self.t_min,
            "t_max": self.t_max,
            "censored_run_fraction": self.censored_run_fraction,
            "criticality": self.criticality,
            "slope_s": self.slope_s,
            "slope_ci95": self.slope_ci95,
            "ladder": self.ladder,
        }


def evaluate_point(
    records: Sequence[dict[str, Any]],
    *,
    t_min: int,
    horizon: int,
    boot_rng: np.random.Generator,
    resamples: int = BOOTSTRAP_RESAMPLES,
) -> PointEvaluation:
    """Window, ladder, local slopes, precheck, and the criticality test."""

    table = RunTable.from_records(records)
    R = table.size
    censored_fraction = float(np.isfinite(table.censored).sum() / R)
    t_max = fit_window_upper(table, horizon)
    base = dict(t_min=t_min, t_max=t_max, censored_run_fraction=censored_fraction, runs=R)
    if t_max is None or t_max < 4 * t_min:
        return PointEvaluation(criticality="window_too_short", slope_s=None, slope_ci95=None, ladder=[], **base)

    ladder_ticks = geometric_ladder(t_min, t_max)
    admissible = [t for t in ladder_ticks if t / M >= t_min]
    partners = [partner_tick(t) for t in admissible]
    ticks = sorted(set(ladder_ticks) | set(partners))
    position = {t: j for j, t in enumerate(ticks)}
    upper_idx = np.array([position[t] for t in admissible], dtype=np.int64)
    lower_idx = np.array([position[t] for t in partners], dtype=np.int64)
    ladder_idx = np.array([position[t] for t in ladder_ticks], dtype=np.int64)

    mats = _matrices(table, ticks)
    P, N, R2 = _aggregates(mats, np.ones(R))
    slopes = _local_slopes(P, N, R2, upper_idx, lower_idx)
    by_tick = {t: k for k, t in enumerate(admissible)}
    ladder = []
    for t, j in zip(ladder_ticks, ladder_idx):
        k = by_tick.get(t)
        ladder.append(
            {
                "t": int(t),
                "P": float(P[j]),
                "N": float(N[j]),
                "R2": _none(R2[j]),
                "delta_eff": None if k is None else _none(slopes["delta"][k]),
                "theta_eff": None if k is None else _none(slopes["theta_or_eta"][k]),
                "two_over_z_eff": None if k is None else _none(slopes["two_over_z"][k]),
            }
        )

    absorbed_by_t_max = int((table.absorbed <= t_max).sum())
    if absorbed_by_t_max < MIN_ABSORBED_FRACTION * R or absorbed_by_t_max < MIN_ABSORBED_RUNS:
        return PointEvaluation(criticality="no_absorption_observed", slope_s=None, slope_ci95=None, ladder=ladder, **base)

    log_t = np.log(np.asarray(admissible, dtype=float))
    fit = np.isfinite(slopes["delta"])
    if fit.sum() < 2:
        return PointEvaluation(criticality="window_too_short", slope_s=None, slope_ci95=None, ladder=ladder, **base)

    boot_delta = np.empty((resamples, len(admissible)))
    boot_exp = {name: np.empty(resamples) for name in EXPONENTS}
    for b in range(resamples):
        index = boot_rng.integers(0, R, size=R)
        weights = np.bincount(index, minlength=R).astype(float)
        bP, bN, bR2 = _aggregates(mats, weights)
        b_slopes = _local_slopes(bP, bN, bR2, upper_idx, lower_idx)
        boot_delta[b] = b_slopes["delta"]
        for name in EXPONENTS:
            boot_exp[name][b] = _nanmean_or_nan(_upper_half(b_slopes[name]))

    usable = np.isfinite(boot_delta[:, fit]).all(axis=1)
    variances = boot_delta[usable][:, fit].var(axis=0, ddof=1) if usable.sum() > 1 else None
    if variances is None or not np.isfinite(variances).all() or (variances <= 0).any():
        weights = np.ones(int(fit.sum()))
    else:
        weights = 1.0 / variances
    x = log_t[fit]
    s = _weighted_slope(x, slopes["delta"][fit], weights)
    slope_boot = np.array([_weighted_slope(x, row[fit], weights) for row in boot_delta[usable]])
    lo, hi = (float(v) for v in np.percentile(slope_boot, [2.5, 97.5]))
    if lo <= 0.0 <= hi:
        criticality = "critical_compatible"
    elif s > 0:
        criticality = "subcritical"
    elif s < 0:
        criticality = "supercritical"
    else:
        criticality = "critical_compatible"

    exponents = {name: _nanmean_or_nan(_upper_half(slopes[name])) for name in EXPONENTS}
    crossover = any(
        _strictly_monotone(slopes[name]) for name in ("delta", "theta_or_eta", "two_over_z")
    )
    return PointEvaluation(
        criticality=criticality,
        slope_s=s,
        slope_ci95=[lo, hi],
        ladder=ladder,
        exponents=exponents,
        exponent_boot=boot_exp,
        slope_boot=slope_boot,
        crossover_in_window=crossover,
        **base,
    )


def bracketing_class(criticality: str) -> str:
    """no_absorption_observed is supercritical for bracketing."""

    return "supercritical" if criticality == "no_absorption_observed" else criticality


# ----------------------------------------------------------------------------
# Exponent estimates
# ----------------------------------------------------------------------------


def _bootstrap_se(samples: np.ndarray) -> float:
    finite = samples[np.isfinite(samples)]
    return float(finite.std(ddof=1)) if finite.size > 1 else 0.0


def exponent_estimates(
    final: PointEvaluation,
    lower: PointEvaluation | None = None,
    upper: PointEvaluation | None = None,
) -> dict[str, dict[str, float]] | None:
    if not final.exponents:
        return None
    estimates = {}
    for name in EXPONENTS:
        value = final.exponents[name]
        if not math.isfinite(value):
            return None
        statistical = _bootstrap_se(final.exponent_boot[name])
        systematic = 0.0
        if lower is not None and upper is not None and lower.exponents and upper.exponents:
            a, b = lower.exponents[name], upper.exponents[name]
            if math.isfinite(a) and math.isfinite(b):
                systematic = abs(a - b) / 2.0
        estimates[name] = {
            "value": value,
            "statistical_se": statistical,
            "systematic_se": systematic,
            "total_se": math.sqrt(statistical ** 2 + systematic ** 2),
        }
    return estimates


# ----------------------------------------------------------------------------
# Bracketing and bisection
# ----------------------------------------------------------------------------


@dataclass
class EvaluatedPoint:
    control: float
    role: str
    evaluation: PointEvaluation
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class BracketSearch:
    points: list[EvaluatedPoint]
    brackets: list[list[float]]
    terminal_status: str
    final_bracket: tuple[EvaluatedPoint, EvaluatedPoint] | None
    final_control: float | None


def midpoint(lo: float, hi: float, kind: str) -> float:
    if kind == "arithmetic":
        return (lo + hi) / 2.0
    if kind == "geometric":
        return math.sqrt(lo * hi)
    raise ValueError(f"unknown midpoint kind {kind!r}")


def adjacent_brackets(points: Sequence[EvaluatedPoint]) -> list[tuple[EvaluatedPoint, EvaluatedPoint]]:
    ordered = sorted(points, key=lambda p: p.control)
    pairs = []
    for left, right in zip(ordered, ordered[1:]):
        if (
            bracketing_class(left.evaluation.criticality) == "subcritical"
            and bracketing_class(right.evaluation.criticality) == "supercritical"
        ):
            pairs.append((left, right))
    return pairs


def bracket_search(
    evaluate: Callable[[float, str, int], EvaluatedPoint],
    coarse_grid: Sequence[float],
    bisection_steps: int,
    midpoint_kind: str,
) -> BracketSearch:
    """Coarse grid, then bisection of the lowest bracket (no final re-run).

    ``evaluate(control, role, index)`` returns an EvaluatedPoint; ``index`` is
    the coarse index (0..) or ``len(coarse_grid) + step`` for bisection.
    """

    points = [evaluate(float(c), "coarse", i) for i, c in enumerate(coarse_grid)]
    pairs = adjacent_brackets(points)
    brackets = [[left.control, right.control] for left, right in pairs]
    if not pairs:
        return BracketSearch(points, brackets, "no_bracket_in_registered_range", None, None)
    status = "multiple_brackets" if len(pairs) > 1 else "classified"
    lo, hi = pairs[0]
    for step in range(bisection_steps):
        control = midpoint(lo.control, hi.control, midpoint_kind)
        point = evaluate(control, "bisection", len(coarse_grid) + step)
        points.append(point)
        kind = bracketing_class(point.evaluation.criticality)
        if kind == "subcritical":
            lo = point
        elif kind == "supercritical":
            hi = point
        elif kind == "critical_compatible":
            if abs(hi.evaluation.slope_s or 0.0) > abs(lo.evaluation.slope_s or 0.0):
                lo = point
            else:
                hi = point
        else:
            return BracketSearch(points, brackets, point.evaluation.criticality, (lo, hi), None)
    inside = [
        p
        for p in points
        if lo.control <= p.control <= hi.control
        and p.evaluation.criticality == "critical_compatible"
        and p.evaluation.slope_s is not None
    ]
    if inside:
        final = min(inside, key=lambda p: (abs(p.evaluation.slope_s), p.control)).control
    else:
        final = midpoint(lo.control, hi.control, midpoint_kind)
    return BracketSearch(points, brackets, status, (lo, hi), final)


def threshold_estimate(lo: EvaluatedPoint, hi: EvaluatedPoint) -> dict[str, float]:
    """Final bracket midpoint; SE = half-width (+) bootstrap spread (Q-EST-9)."""

    a, b = lo.control, hi.control
    value = (a + b) / 2.0
    half_width = abs(b - a) / 2.0
    spread = 0.0
    sa, sb = lo.evaluation.slope_boot, hi.evaluation.slope_boot
    if sa is not None and sb is not None and sa.size and sb.size:
        n = min(sa.size, sb.size)
        crossings = np.empty(n)
        for i in range(n):
            ya, yb = sa[i], sb[i]
            if ya > 0 and yb < 0:
                crossings[i] = a + (b - a) * ya / (ya - yb)
            elif ya <= 0:
                crossings[i] = a
            else:
                crossings[i] = b
        spread = float(crossings.std(ddof=1)) if n > 1 else 0.0
    return {
        "value": value,
        "statistical_se": spread,
        "systematic_se": half_width,
        "total_se": math.sqrt(spread ** 2 + half_width ** 2),
    }


# ----------------------------------------------------------------------------
# Static cluster-size tail
# ----------------------------------------------------------------------------


def _ls_slope(x: np.ndarray, y: np.ndarray) -> float:
    xm = x.mean()
    return float(((x - xm) * (y - y.mean())).sum() / ((x - xm) ** 2).sum())


def static_tail_point(
    records: Sequence[dict[str, Any]],
    *,
    boot_rng: np.random.Generator,
    resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict[str, Any]:
    """tau - 2 from the CCDF of S on the exact range [16, s_cut].

    A run that is censored or still alive at the horizon is right-censored at
    its recorded S (Q-EST-11).  Returns the value and bootstrap samples.
    """

    S = np.array([float(r["S"]) for r in records])
    right_censored = np.array(
        [r["censored_at"] is not None or r["absorbed_at"] is None for r in records]
    )
    s_cut = int(S[right_censored].min()) if right_censored.any() else int(S.max())
    if s_cut < STATIC_MIN_S_CUT:
        return {"s_cut": s_cut, "status": "range_too_short", "value": None, "boot": None}
    s_values = np.asarray(geometric_ladder(STATIC_S_MIN, s_cut), dtype=float)
    above = (S[:, None] >= s_values[None, :]).astype(float)
    log_s = np.log(s_values)
    R = S.size
    value = -_ls_slope(log_s, np.log(above.mean(axis=0)))
    boot = np.empty(resamples)
    for b in range(resamples):
        index = boot_rng.integers(0, R, size=R)
        weights = np.bincount(index, minlength=R).astype(float)
        F = (weights @ above) / R
        with np.errstate(divide="ignore"):
            boot[b] = -_ls_slope(log_s, np.log(F)) if (F > 0).all() else math.nan
    return {"s_cut": s_cut, "status": "estimated", "value": value, "boot": boot}


def static_tail_estimate(
    final: dict[str, Any],
    lower: dict[str, Any] | None = None,
    upper: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {"s_cut": final["s_cut"], "status": final["status"]}
    if final["status"] != "estimated":
        return result
    statistical = _bootstrap_se(final["boot"])
    systematic = 0.0
    if (
        lower is not None
        and upper is not None
        and lower.get("status") == "estimated"
        and upper.get("status") == "estimated"
    ):
        systematic = abs(lower["value"] - upper["value"]) / 2.0
    result["tau_minus_2"] = {
        "value": final["value"],
        "statistical_se": statistical,
        "systematic_se": systematic,
        "total_se": math.sqrt(statistical ** 2 + systematic ** 2),
    }
    return result
