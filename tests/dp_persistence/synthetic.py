"""Synthetic run ledgers with exact power laws, for estimator tests only."""

from __future__ import annotations

import math

import numpy as np


def power_law_ledger(
    delta: float,
    theta: float,
    z: float,
    *,
    runs: int = 4000,
    horizon: int = 1024,
    amplitude: float = 1000.0,
) -> list[dict]:
    """P(t) = t^-delta, N(t) = amplitude t^theta, R2(t) = t^(2/z), exactly up
    to the 1/runs quantile discretization of P."""

    records = []
    for i in range(runs):
        u = (i + 0.5) / runs
        absorbed = math.floor(u ** (-1.0 / delta)) + 1 if delta > 0 else None
        if absorbed is not None and absorbed > horizon:
            absorbed = None
        length = horizon if absorbed is None else absorbed - 1
        t = np.arange(1, length + 1, dtype=float)
        n = amplitude * t ** (theta + delta)
        records.append(
            {
                "n_t": n,
                "r2_sum_t": n * t ** (2.0 / z),
                "absorbed_at": absorbed,
                "censored_at": None,
                "S": 1,
            }
        )
    return records


def exponential_ledger(xi: float, *, runs: int = 4000, horizon: int = 1024) -> list[dict]:
    """P(t) = exp(-t/xi): subcritical."""

    records = []
    for i in range(runs):
        u = (i + 0.5) / runs
        absorbed = math.floor(-xi * math.log(u)) + 1
        absorbed = None if absorbed > horizon else absorbed
        length = horizon if absorbed is None else absorbed - 1
        t = np.arange(1, length + 1, dtype=float)
        records.append(
            {
                "n_t": 10.0 * np.ones(length),
                "r2_sum_t": 10.0 * t,
                "absorbed_at": absorbed,
                "censored_at": None,
                "S": 1,
            }
        )
    return records


def plateau_ledger(p_inf: float, *, runs: int = 4000, horizon: int = 1024, delta: float = 0.5) -> list[dict]:
    """P(t) -> p_inf > 0: supercritical."""

    records = []
    for i in range(runs):
        u = (i + 0.5) / runs
        if u <= p_inf:
            absorbed = None
        else:
            q = (u - p_inf) / (1 - p_inf)
            absorbed = math.floor(q ** (-1.0 / delta)) + 1
            absorbed = None if absorbed > horizon else absorbed
        length = horizon if absorbed is None else absorbed - 1
        t = np.arange(1, length + 1, dtype=float)
        records.append(
            {
                "n_t": 10.0 * t,
                "r2_sum_t": 10.0 * t * t,
                "absorbed_at": absorbed,
                "censored_at": None,
                "S": 1,
            }
        )
    return records


def flat_ledger(*, runs: int = 200, horizon: int = 1024) -> list[dict]:
    """P(t) = 1: no run is ever absorbed."""

    t = np.arange(1, horizon + 1, dtype=float)
    return [
        {"n_t": 5.0 * t, "r2_sum_t": 5.0 * t * t, "absorbed_at": None, "censored_at": None, "S": 1}
        for _ in range(runs)
    ]


def cluster_tail_ledger(tau_minus_2: float, *, runs: int = 20000, censor_above: int | None = None) -> list[dict]:
    """P(S >= s) = s^-(tau - 2) up to quantile discretization."""

    records = []
    for i in range(runs):
        u = (i + 0.5) / runs
        S = int(min(math.floor(u ** (-1.0 / tau_minus_2)), 10 ** 12))
        censored = None
        absorbed = 10
        if censor_above is not None and S >= censor_above:
            S = censor_above + (i % 7)
            censored, absorbed = 5, None
        records.append(
            {"n_t": np.zeros(0), "r2_sum_t": np.zeros(0), "absorbed_at": absorbed, "censored_at": censored, "S": S}
        )
    return records
