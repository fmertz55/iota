"""Independent replay of the spreading estimator and classifier.

Shares no code with ``estimators`` or ``classifier``: it reads the spec JSON
itself, builds aggregates by direct row selection of resampled runs instead of
weight vectors, fits slopes from explicit normal-equation sums, and computes
percentiles by hand.  It must agree with the primary implementation to 1e-12
on every synthetic ledger.  Only the bootstrap stream (from ``rng``) is shared
by passing an identically seeded generator.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np


_SPEC = Path(__file__).resolve().parents[2] / "specs/icp_directed_percolation_persistence/v0.1-draft"


def _load(name: str) -> dict[str, Any]:
    with (_SPEC / name).open(encoding="utf-8") as handle:
        return json.load(handle)


ESTIMATORS = _load("estimators.json")
REFERENCES = _load("reference_classes.json")
SPREADING = _load("iota_spreading.json")

RATIO_M = ESTIMATORS["local_slopes"]["m"]


def nearest_int(x: float) -> int:
    whole = math.floor(x)
    return whole + 1 if x - whole >= 0.5 else whole


def ladder(start: int, top: float) -> list[int]:
    out: list[int] = []
    k = 0
    while True:
        t = nearest_int(start * 2.0 ** (k / 4.0))
        if t > top:
            break
        if t not in out:
            out.append(t)
        k += 1
    return out


def _inf_if_none(value) -> float:
    return math.inf if value is None else float(value)


def window_top(records, horizon: int) -> int | None:
    total = len(records)
    best = None
    pairs = [(_inf_if_none(r["censored_at"]), _inf_if_none(r["absorbed_at"])) for r in records]
    flagged = sorted(pairs)
    for t in range(1, horizon + 1):
        count = 0
        for c, a in flagged:
            if c > t:
                break
            if a > t:
                count += 1
        if count / total <= 0.01:
            best = t
    return best


def _series_value(series, t: int) -> float:
    return float(series[t - 1]) if 1 <= t <= len(series) else 0.0


def _columns(records, ticks):
    """Per-run columns: uncensored, alive*uncensored, n*unc, r2*alive*unc, n*alive*unc."""

    R, K = len(records), len(ticks)
    cols = {name: np.zeros((R, K)) for name in ("u", "au", "nu", "ra", "na")}
    for i, r in enumerate(records):
        c = _inf_if_none(r["censored_at"])
        a = _inf_if_none(r["absorbed_at"])
        for j, t in enumerate(ticks):
            unc = 1.0 if c > t else 0.0
            alive = 1.0 if a > t else 0.0
            n = _series_value(r["n_t"], t)
            r2 = _series_value(r["r2_sum_t"], t)
            cols["u"][i, j] = unc
            cols["au"][i, j] = alive * unc
            cols["nu"][i, j] = n * unc
            cols["ra"][i, j] = r2 * alive * unc
            cols["na"][i, j] = n * alive * unc
    return cols


def _div(top: float, bottom: float) -> float:
    return top / bottom if bottom > 0 else math.nan


def _aggregates_for_rows(cols, rows):
    sums = {name: cols[name][rows].sum(axis=0) for name in cols}
    K = sums["u"].size
    P = [_div(sums["au"][j], sums["u"][j]) for j in range(K)]
    N = [_div(sums["nu"][j], sums["u"][j]) for j in range(K)]
    R2 = [_div(sums["ra"][j], sums["na"][j]) for j in range(K)]
    return P, N, R2


def _lr(hi: float, lo: float) -> float:
    try:
        value = math.log(hi / lo) / math.log(RATIO_M)
    except (ValueError, ZeroDivisionError):
        return math.nan
    return value if math.isfinite(value) else math.nan


def _slopes(P, N, R2, pairs):
    delta, act, tz, z = [], [], [], []
    for hi, lo in pairs:
        d = _lr(P[hi], P[lo])
        delta.append(-d if math.isfinite(d) else math.nan)
        act.append(_lr(N[hi], N[lo]))
        g = _lr(R2[hi], R2[lo])
        tz.append(g)
        z.append(2.0 / g if math.isfinite(g) and g != 0 else math.nan)
    return {"delta": delta, "theta_or_eta": act, "two_over_z": tz, "z": z}


def _mean_finite(values) -> float:
    kept = [v for v in values if math.isfinite(v)]
    return sum(kept) / len(kept) if kept else math.nan


def _top_half(values):
    return values[len(values) // 2:]


def _fit(x, y, w) -> float:
    sw = sum(w)
    sx = sum(wi * xi for wi, xi in zip(w, x))
    sy = sum(wi * yi for wi, yi in zip(w, y))
    mx, my = sx / sw, sy / sw
    sxy = sum(wi * (xi - mx) * (yi - my) for wi, xi, yi in zip(w, x, y))
    sxx = sum(wi * (xi - mx) ** 2 for wi, xi in zip(w, x))
    return sxy / sxx


def _quantile(values, q: float) -> float:
    ordered = sorted(values)
    position = q * (len(ordered) - 1)
    low = math.floor(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def _sample_sd(values) -> float:
    kept = [v for v in values if math.isfinite(v)]
    if len(kept) < 2:
        return 0.0
    mean = sum(kept) / len(kept)
    return math.sqrt(sum((v - mean) ** 2 for v in kept) / (len(kept) - 1))


def _monotone(values) -> bool:
    kept = [v for v in values if math.isfinite(v)]
    if len(kept) < 3:
        return False
    steps = [b - a for a, b in zip(kept, kept[1:])]
    return all(s > 0 for s in steps) or all(s < 0 for s in steps)


def _clean(value):
    return value if value is not None and math.isfinite(value) else None


def replay_point(records, *, t_min: int, horizon: int, boot_rng, resamples: int = 1000) -> dict[str, Any]:
    R = len(records)
    censored = sum(1 for r in records if r["censored_at"] is not None)
    out: dict[str, Any] = {
        "t_min": t_min,
        "t_max": None,
        "censored_run_fraction": censored / R,
        "criticality": None,
        "slope_s": None,
        "slope_ci95": None,
        "ladder": [],
        "exponents": {},
        "exponent_boot": {},
        "slope_boot": None,
        "crossover_in_window": False,
    }
    top = window_top(records, horizon)
    out["t_max"] = top
    if top is None or top < 4 * t_min:
        out["criticality"] = "window_too_short"
        return out

    rungs = ladder(t_min, top)
    usable = [t for t in rungs if t / RATIO_M >= t_min]
    partner = {t: nearest_int(t / RATIO_M) for t in usable}
    ticks = sorted(set(rungs) | set(partner.values()))
    where = {t: j for j, t in enumerate(ticks)}
    pairs = [(where[t], where[partner[t]]) for t in usable]
    cols = _columns(records, ticks)
    P, N, R2 = _aggregates_for_rows(cols, np.arange(R))
    sl = _slopes(P, N, R2, pairs)
    for t in rungs:
        j = where[t]
        k = usable.index(t) if t in usable else None
        out["ladder"].append(
            {
                "t": t,
                "P": P[j],
                "N": N[j],
                "R2": _clean(R2[j]),
                "delta_eff": None if k is None else _clean(sl["delta"][k]),
                "theta_eff": None if k is None else _clean(sl["theta_or_eta"][k]),
                "two_over_z_eff": None if k is None else _clean(sl["two_over_z"][k]),
            }
        )

    died = sum(1 for r in records if r["absorbed_at"] is not None and r["absorbed_at"] <= top)
    if died < 0.01 * R or died < 50:
        out["criticality"] = "no_absorption_observed"
        return out

    keep = [k for k, v in enumerate(sl["delta"]) if math.isfinite(v)]
    if len(keep) < 2:
        out["criticality"] = "window_too_short"
        return out

    boot_rows = []
    boot_exp = {"delta": [], "theta_or_eta": [], "z": []}
    for _ in range(resamples):
        rows = boot_rng.integers(0, R, size=R)
        bP, bN, bR2 = _aggregates_for_rows(cols, rows)
        bs = _slopes(bP, bN, bR2, pairs)
        boot_rows.append(bs["delta"])
        for name in boot_exp:
            boot_exp[name].append(_mean_finite(_top_half(bs[name])))

    good = [row for row in boot_rows if all(math.isfinite(row[k]) for k in keep)]
    weights = None
    if len(good) > 1:
        variances = []
        for k in keep:
            column = [row[k] for row in good]
            mean = sum(column) / len(column)
            variances.append(sum((v - mean) ** 2 for v in column) / (len(column) - 1))
        if all(math.isfinite(v) and v > 0 for v in variances):
            weights = [1.0 / v for v in variances]
    if weights is None:
        weights = [1.0] * len(keep)
    x = [math.log(usable[k]) for k in keep]
    s = _fit(x, [sl["delta"][k] for k in keep], weights)
    s_boot = [_fit(x, [row[k] for k in keep], weights) for row in good]
    lo, hi = _quantile(s_boot, 0.025), _quantile(s_boot, 0.975)
    if lo <= 0.0 <= hi or s == 0:
        kind = "critical_compatible"
    else:
        kind = "subcritical" if s > 0 else "supercritical"
    out.update(
        criticality=kind,
        slope_s=s,
        slope_ci95=[lo, hi],
        exponents={name: _mean_finite(_top_half(sl[name])) for name in boot_exp},
        exponent_boot={name: np.asarray(v) for name, v in boot_exp.items()},
        slope_boot=np.asarray(s_boot),
        crossover_in_window=_monotone(sl["delta"]) or _monotone(sl["theta_or_eta"]) or _monotone(sl["two_over_z"]),
    )
    return out


def replay_exponents(final, lower=None, upper=None):
    if not final["exponents"]:
        return None
    result = {}
    for name in ("delta", "theta_or_eta", "z"):
        value = final["exponents"][name]
        if not math.isfinite(value):
            return None
        stat = _sample_sd(list(final["exponent_boot"][name]))
        syst = 0.0
        if lower and upper and lower["exponents"] and upper["exponents"]:
            a, b = lower["exponents"][name], upper["exponents"][name]
            if math.isfinite(a) and math.isfinite(b):
                syst = 0.5 * abs(a - b)
        result[name] = {
            "value": value,
            "statistical_se": stat,
            "systematic_se": syst,
            "total_se": math.hypot(stat, syst),
        }
    return result


def replay_static(records, *, boot_rng, resamples: int = 1000) -> dict[str, Any]:
    sizes = [float(r["S"]) for r in records]
    cut_candidates = [
        float(r["S"]) for r in records if r["censored_at"] is not None or r["absorbed_at"] is None
    ]
    s_cut = int(min(cut_candidates)) if cut_candidates else int(max(sizes))
    if s_cut < 256:
        return {"s_cut": s_cut, "status": "range_too_short", "value": None, "boot": None}
    grid = ladder(16, s_cut)
    logs = [math.log(s) for s in grid]
    R = len(sizes)
    S = np.asarray(sizes)
    hits = np.stack([S >= s for s in grid], axis=1).astype(float)

    def tail_slope(rows) -> float:
        F = hits[rows].sum(axis=0) / R
        if (F <= 0).any():
            return math.nan
        return -_fit(logs, [math.log(f) for f in F], [1.0] * len(grid))

    value = tail_slope(np.arange(R))
    boot = [tail_slope(boot_rng.integers(0, R, size=R)) for _ in range(resamples)]
    return {"s_cut": s_cut, "status": "estimated", "value": value, "boot": np.asarray(boot)}


def replay_static_estimate(final, lower=None, upper=None) -> dict[str, Any]:
    out = {"s_cut": final["s_cut"], "status": final["status"]}
    if final["status"] != "estimated":
        return out
    stat = _sample_sd(list(final["boot"]))
    syst = 0.0
    if lower and upper and lower.get("status") == "estimated" and upper.get("status") == "estimated":
        syst = 0.5 * abs(lower["value"] - upper["value"])
    out["tau_minus_2"] = {"value": final["value"], "statistical_se": stat, "systematic_se": syst, "total_se": math.hypot(stat, syst)}
    return out


# ----------------------------------------------------------------------------
# Bracketing
# ----------------------------------------------------------------------------


def _side(kind: str) -> str:
    return "supercritical" if kind == "no_absorption_observed" else kind


def replay_bracket(evaluate, grid, steps: int, kind: str) -> dict[str, Any]:
    """``evaluate(control, role, index)`` -> dict with 'criticality' and 'slope_s'."""

    seen = []
    for i, c in enumerate(grid):
        seen.append((float(c), evaluate(float(c), "coarse", i)))
    ordered = sorted(seen, key=lambda item: item[0])
    found = [
        (ordered[i], ordered[i + 1])
        for i in range(len(ordered) - 1)
        if _side(ordered[i][1]["criticality"]) == "subcritical"
        and _side(ordered[i + 1][1]["criticality"]) == "supercritical"
    ]
    brackets = [[a[0], b[0]] for a, b in found]
    if not found:
        return {"seen": seen, "brackets": brackets, "status": "no_bracket_in_registered_range", "final_bracket": None, "final": None}
    status = "classified" if len(found) == 1 else "multiple_brackets"
    (lo, lo_eval), (hi, hi_eval) = found[0]

    def mid(a, b):
        return 0.5 * (a + b) if kind == "arithmetic" else math.sqrt(a * b)

    for step in range(steps):
        c = mid(lo, hi)
        ev = evaluate(c, "bisection", len(grid) + step)
        seen.append((c, ev))
        side = _side(ev["criticality"])
        if side == "subcritical":
            lo, lo_eval = c, ev
        elif side == "supercritical":
            hi, hi_eval = c, ev
        elif side == "critical_compatible":
            if abs(hi_eval["slope_s"] or 0.0) > abs(lo_eval["slope_s"] or 0.0):
                lo, lo_eval = c, ev
            else:
                hi, hi_eval = c, ev
        else:
            return {"seen": seen, "brackets": brackets, "status": ev["criticality"], "final_bracket": (lo, hi), "final": None}
    best = None
    for c, ev in seen:
        if lo <= c <= hi and ev["criticality"] == "critical_compatible" and ev["slope_s"] is not None:
            key = (abs(ev["slope_s"]), c)
            if best is None or key < best[0]:
                best = (key, c)
    final = best[1] if best is not None else mid(lo, hi)
    return {"seen": seen, "brackets": brackets, "status": status, "final_bracket": (lo, hi), "final": final}


def replay_threshold(lo: float, hi: float, lo_boot, hi_boot) -> dict[str, float]:
    centre = 0.5 * (lo + hi)
    half = 0.5 * abs(hi - lo)
    spread = 0.0
    if lo_boot is not None and hi_boot is not None and len(lo_boot) and len(hi_boot):
        xs = []
        for ya, yb in zip(lo_boot, hi_boot):
            if ya > 0 and yb < 0:
                xs.append(lo + (hi - lo) * ya / (ya - yb))
            else:
                xs.append(lo if ya <= 0 else hi)
        spread = _sample_sd(xs)
    return {"value": centre, "statistical_se": spread, "systematic_se": half, "total_se": math.hypot(spread, half)}


# ----------------------------------------------------------------------------
# Classifier
# ----------------------------------------------------------------------------


def _ref(class_id: str, key: str) -> float:
    table = REFERENCES["classes"][class_id]["exponents"]
    if key == "theta_or_eta":
        key = "theta" if "theta" in table else "eta"
    return table[key]["value"]


def _tol(dim: str, key: str) -> float:
    table = ESTIMATORS["classification"]["absolute_tolerances"][dim]
    return table[key] if key in table else table["theta"]


def _hyper_limit() -> float:
    return float(ESTIMATORS["consistency_checks"]["DyP"].split("<=")[-1])


def replay_classify(estimates, dim: str) -> dict[str, Any]:
    classes = ESTIMATORS["classification"][f"registered_classes_{dim}"]
    per_exponent, per_class, hyper = {}, {}, {}
    for cid in classes:
        marks = {}
        for key in ("delta", "theta_or_eta", "z"):
            gap = abs(estimates[key]["value"] - _ref(cid, key))
            t = _tol(dim, key)
            marks[key] = "agrees" if gap <= t else ("disagrees" if gap > t + 2 * estimates[key]["total_se"] else "indeterminate")
        per_exponent[cid] = marks
        d = REFERENCES["classes"][cid]["spatial_dimension"]
        z = estimates["z"]["value"]
        delta = estimates["delta"]["value"]
        expected = d / z - 2 * delta - (1 if cid.startswith("DyP") else 0)
        residual = estimates["theta_or_eta"]["value"] - expected
        hyper[cid] = {"residual": residual, "passes": abs(residual) <= _hyper_limit()}
        values = list(marks.values())
        if values.count("agrees") == 3:
            status = "match" if hyper[cid]["passes"] else "indeterminate"
        elif "disagrees" in values:
            status = "excluded"
        else:
            status = "indeterminate"
        per_class[cid] = status
    matched = [c for c in classes if per_class[c] == "match"]
    excluded = [c for c in classes if per_class[c] == "excluded"]
    if len(matched) == 1 and len(excluded) == len(classes) - 1:
        verdict = matched[0]
    elif len(excluded) == len(classes):
        verdict = "none_of_registered"
    else:
        verdict = "indeterminate"
    return {"per_exponent": per_exponent, "per_class": per_class, "hyperscaling": hyper, "verdict": verdict}


def replay_h1(rho_c: float, se: float) -> str:
    p_c = REFERENCES["thresholds"]["simple_cubic_site_percolation_z6"]["p_c"]
    tol = float(SPREADING["hypotheses"]["H1_threshold"]["outcomes"]["equal"].split("<=")[-1])
    if abs(rho_c - p_c) <= tol:
        return "equal"
    if rho_c - p_c > tol + 2 * se:
        return "budget_shifted"
    if rho_c - p_c < -(tol + 2 * se):
        return "instrument_failure"
    return "indeterminate"


def replay_h2(h1: str, classification) -> str:
    if h1 != "equal":
        return "not_applicable"
    if classification is None:
        return "indeterminate"
    marks = classification["per_exponent"]["DyP_3"]
    if (marks["delta"], marks["theta_or_eta"], marks["z"]) == ("agrees", "agrees", "disagrees"):
        return "percolation_statics_non_epidemic_dynamics"
    v = classification["verdict"]
    return {"DyP_3": "supported", "DP_3p1": "falsified", "none_of_registered": "falsified"}.get(v, "indeterminate")


def replay_h3(h1: str, static) -> str:
    if h1 != "equal":
        return "not_applicable"
    if not static or static.get("status") != "estimated":
        return "indeterminate"
    reference = REFERENCES["classes"]["DyP_3"]["exponents"]["static_tau"]["value"] - 2
    tol = SPREADING["hypotheses"]["H3_static_cluster_tail"]["tolerance"]
    gap = abs(static["tau_minus_2"]["value"] - reference)
    if gap <= tol:
        return "supported"
    return "falsified" if gap > tol + 2 * static["tau_minus_2"]["total_se"] else "indeterminate"
