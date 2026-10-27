"""Stage C calibration models (calibration.json models).

Every model returns the same per-run record shape as IOTA-MIN-L0:
``n_t``/``r2_sum_t`` for ticks 1, 2, ... (index ``t - 1``), ``absorbed_at``,
``censored_at``, ``ticks_run``, and ``S`` (distinct sites ever active,
including the seed).  Each model uses its own active unit and absorbing test
from calibration.json.  Draw orders not fixed by the spec are recorded in
SPEC_QUESTIONS.md (Q-CAL-*).
"""

from __future__ import annotations

from typing import Any, Callable

import numpy as np

from .l0_engine import default_seed, draw_medium, geometry
from .protocol import calibration_model
from .rng import calibration_stream


DK_BOND = "CAL-DK-BOND-1P1"
DK_SITE = "CAL-DK-SITE-1P1"
BOND_DP_3 = "CAL-BOND-DP-3P1"
SIR_3 = "CAL-SIR-SC-3"
SITE_BFS_3 = "CAL-SITE-BFS-SC-3"
MODEL_IDS = (DK_BOND, DK_SITE, BOND_DP_3, SIR_3, SITE_BFS_3)


def _record(n_t, r2_sum_t, absorbed_at, censored_at, ticks_run, S, **extra) -> dict[str, Any]:
    record = {
        "n_t": np.asarray(n_t, dtype=np.int64),
        "r2_sum_t": np.asarray(r2_sum_t, dtype=np.int64),
        "absorbed_at": absorbed_at,
        "censored_at": censored_at,
        "ticks_run": ticks_run,
        "S": int(S),
    }
    record.update(extra)
    return record


# ----------------------------------------------------------------------------
# Domany-Kinzel, 1 + 1 dimensions
# ----------------------------------------------------------------------------


def dk_probabilities(model_id: str, p: float) -> tuple[float, float]:
    if model_id == DK_BOND:
        return p, p * (2.0 - p)
    if model_id == DK_SITE:
        return p, p
    raise ValueError(f"not a Domany-Kinzel model: {model_id}")


def run_domany_kinzel(
    p1: float,
    p2: float,
    rng: np.random.Generator,
    horizon: int,
    L: int,
    *,
    censor: bool = True,
) -> dict[str, Any]:
    """Seed at site 0; site i at layer t+1 reads sites i-1 and i+1 at layer t.

    One uniform is drawn per candidate site (at least one active input), in
    increasing site index; the site activates iff u < p1 (one active input)
    or u < p2 (two).
    """

    radius = L / 2 - 4
    active = np.array([0], dtype=np.int64)
    ever = np.zeros(L, dtype=bool)
    ever[0] = True
    n_t: list[int] = []
    r2_sum_t: list[int] = []
    absorbed_at = None
    censored_at = None
    t = 0
    while absorbed_at is None and censored_at is None and t < horizon:
        t += 1
        inputs = np.concatenate(((active - 1) % L, (active + 1) % L))
        candidates, counts = np.unique(inputs, return_counts=True)
        probability = np.where(counts == 1, p1, p2)
        u = rng.random(candidates.size)
        active = candidates[u < probability]
        distance = np.minimum(active, L - active)
        n_t.append(int(active.size))
        r2_sum_t.append(int((distance * distance).sum()))
        ever[active] = True
        if censor and active.size and distance.max() >= radius:
            censored_at = t
        if active.size == 0:
            absorbed_at = t
    return _record(n_t, r2_sum_t, absorbed_at, censored_at, t, ever.sum())


# ----------------------------------------------------------------------------
# Three-dimensional models on the simple cubic lattice
# ----------------------------------------------------------------------------


def run_bond_dp_3(
    p: float,
    rng: np.random.Generator,
    horizon: int,
    L: int,
    *,
    censor: bool = True,
) -> dict[str, Any]:
    """Each active site draws 7 bonds (+x, -x, +y, -y, +z, -z, self) in order."""

    geo = geometry(L, default_seed(L))
    radius = L / 2 - 4
    active = np.array([geo.seed_index], dtype=np.int64)
    ever = np.zeros(L ** 3, dtype=bool)
    ever[active] = True
    n_t: list[int] = []
    r2_sum_t: list[int] = []
    absorbed_at = None
    censored_at = None
    t = 0
    while absorbed_at is None and censored_at is None and t < horizon:
        t += 1
        bonds = np.concatenate((geo.neighbours[active], active[:, None]), axis=1)
        u = rng.random(bonds.shape)
        active = np.unique(bonds[u < p])
        n_t.append(int(active.size))
        r2_sum_t.append(int(geo.r2[active].sum()))
        ever[active] = True
        if censor and active.size and geo.chebyshev[active].max() >= radius:
            censored_at = t
        if active.size == 0:
            absorbed_at = t
    return _record(n_t, r2_sum_t, absorbed_at, censored_at, t, ever.sum())


def run_sir_3(
    p: float,
    rng: np.random.Generator,
    horizon: int,
    L: int,
    *,
    censor: bool = True,
) -> dict[str, Any]:
    """One-tick SIR; one draw per (infected source, susceptible neighbour) pair.

    Sources in lexicographic order, neighbours in the fixed order; a site's
    susceptibility is read at the start of the generation.
    """

    geo = geometry(L, default_seed(L))
    radius = L / 2 - 4
    susceptible = np.ones(L ** 3, dtype=bool)
    infected = np.array([geo.seed_index], dtype=np.int64)
    susceptible[infected] = False
    n_t: list[int] = []
    r2_sum_t: list[int] = []
    absorbed_at = None
    censored_at = None
    t = 0
    while absorbed_at is None and censored_at is None and t < horizon:
        t += 1
        neighbours = geo.neighbours[infected]
        exposed = susceptible[neighbours]
        u = rng.random(int(exposed.sum()))
        infected = np.unique(neighbours[exposed][u < p])
        susceptible[infected] = False
        n_t.append(int(infected.size))
        r2_sum_t.append(int(geo.r2[infected].sum()))
        if censor and infected.size and geo.chebyshev[infected].max() >= radius:
            censored_at = t
        if infected.size == 0:
            absorbed_at = t
    return _record(n_t, r2_sum_t, absorbed_at, censored_at, t, (~susceptible).sum())


def run_site_bfs_on_medium(
    open_sites: np.ndarray,
    horizon: int,
    L: int,
    *,
    censor: bool = True,
    seed: tuple[int, int, int] | None = None,
) -> dict[str, Any]:
    """Breadth-first growth through open sites; the seed's own entry is ignored."""

    geo = geometry(L, default_seed(L) if seed is None else tuple(seed))
    radius = L / 2 - 4
    open_sites = np.asarray(open_sites, dtype=bool).reshape(-1)
    reached = np.zeros(L ** 3, dtype=bool)
    reached[geo.seed_index] = True
    frontier = np.array([geo.seed_index], dtype=np.int64)
    n_t: list[int] = []
    r2_sum_t: list[int] = []
    absorbed_at = None
    censored_at = None
    t = 0
    while absorbed_at is None and censored_at is None and t < horizon:
        t += 1
        candidates = np.unique(geo.neighbours[frontier].ravel())
        frontier = candidates[open_sites[candidates] & ~reached[candidates]]
        reached[frontier] = True
        n_t.append(int(frontier.size))
        r2_sum_t.append(int(geo.r2[frontier].sum()))
        if censor and frontier.size and geo.chebyshev[frontier].max() >= radius:
            censored_at = t
        if frontier.size == 0:
            absorbed_at = t
    return _record(n_t, r2_sum_t, absorbed_at, censored_at, t, reached.sum(), reached=reached)


def run_site_bfs_3(
    rho: float,
    rng: np.random.Generator,
    horizon: int,
    L: int,
    *,
    censor: bool = True,
) -> dict[str, Any]:
    """Medium drawn exactly as the L0 medium (L^3 variates, one call)."""

    record = run_site_bfs_on_medium(draw_medium(rho, rng, L), horizon, L, censor=censor)
    del record["reached"]
    return record


# ----------------------------------------------------------------------------
# Registered dispatch
# ----------------------------------------------------------------------------


def model_runner(model_id: str) -> Callable[..., dict[str, Any]]:
    """``f(control, rng, horizon, L, censor=True)`` for a calibration model."""

    if model_id in (DK_BOND, DK_SITE):
        def run_dk(control, rng, horizon, L, *, censor=True):
            p1, p2 = dk_probabilities(model_id, control)
            return run_domany_kinzel(p1, p2, rng, horizon, L, censor=censor)

        return run_dk
    if model_id == BOND_DP_3:
        return run_bond_dp_3
    if model_id == SIR_3:
        return run_sir_3
    if model_id == SITE_BFS_3:
        return run_site_bfs_3
    raise KeyError(f"unknown calibration model {model_id!r}")


def run_registered(model_id: str, control: float, run_index: int) -> dict[str, Any]:
    """One calibration run at its registered lattice size and horizon."""

    model = calibration_model(model_id)
    L = model["lattice"]["length"]
    horizon = model["horizon_layers"]
    rng = calibration_stream(model_id, control, run_index)
    return model_runner(model_id)(control, rng, horizon, L)
