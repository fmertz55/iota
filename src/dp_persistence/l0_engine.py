"""Vectorized IOTA-MIN-L0 engine (minimal_law.json laws.L0).

Sites are stored in flat arrays indexed lexicographically,
``index = (x * L + y) * L + z``, so ascending index is lexicographic (x, y, z)
source order.  ``a`` is the active amplitude and ``l`` the latent budget.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np

from .rng import iota_streams


V = 2
A0 = 7
REGISTERED_L = 64
# Fixed neighbour order (+x, -x, +y, -y, +z, -z).
NEIGHBOUR_OFFSETS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


@dataclass(frozen=True)
class Geometry:
    L: int
    seed_index: int
    neighbours: np.ndarray  # (L^3, 6) int64
    r2: np.ndarray  # minimum-image squared Euclidean distance from the seed
    chebyshev: np.ndarray  # minimum-image Chebyshev distance from the seed


@lru_cache(maxsize=8)
def geometry(L: int, seed: tuple[int, int, int]) -> Geometry:
    if L < 3:
        raise ValueError("lattice size must be at least 3")
    x, y, z = np.meshgrid(np.arange(L), np.arange(L), np.arange(L), indexing="ij")
    x, y, z = x.ravel(), y.ravel(), z.ravel()
    columns = [
        (((x + dx) % L) * L + (y + dy) % L) * L + (z + dz) % L
        for dx, dy, dz in NEIGHBOUR_OFFSETS
    ]
    neighbours = np.stack(columns, axis=1).astype(np.int64)
    displacement = []
    for coordinate, origin in zip((x, y, z), seed):
        d = (coordinate - origin) % L
        displacement.append(np.minimum(d, L - d))
    dx, dy, dz = displacement
    r2 = (dx * dx + dy * dy + dz * dz).astype(np.int64)
    chebyshev = np.maximum(np.maximum(dx, dy), dz).astype(np.int64)
    seed_index = (seed[0] * L + seed[1]) * L + seed[2]
    for array in (neighbours, r2, chebyshev):
        array.setflags(write=False)
    return Geometry(L, seed_index, neighbours, r2, chebyshev)


def default_seed(L: int) -> tuple[int, int, int]:
    return (L // 2, L // 2, L // 2)


@dataclass
class L0State:
    a: np.ndarray
    l: np.ndarray
    geometry: Geometry

    def copy(self) -> "L0State":
        return L0State(self.a.copy(), self.l.copy(), self.geometry)

    def ledger_total(self) -> int:
        return int(self.a.sum() + self.l.sum())


def draw_medium(rho: float, medium_rng: np.random.Generator, L: int) -> np.ndarray:
    """Fresh mask from L^3 variates drawn in one call, lexicographic order.

    The seed site's variate is part of the draw and is ignored by
    ``initial_state``.
    """

    variates = medium_rng.random(L ** 3)
    return variates < rho


def initial_state(fresh: np.ndarray, L: int, seed: tuple[int, int, int] | None = None) -> L0State:
    geo = geometry(L, default_seed(L) if seed is None else tuple(seed))
    fresh = np.asarray(fresh, dtype=bool).reshape(-1)
    if fresh.size != L ** 3:
        raise ValueError("fresh mask has the wrong size")
    l = np.where(fresh, V, 0).astype(np.int64)
    a = np.zeros(L ** 3, dtype=np.int64)
    a[geo.seed_index] = A0
    l[geo.seed_index] = 0
    return L0State(a, l, geo)


def _fresh_neighbours(a: np.ndarray, l: np.ndarray, neighbours: np.ndarray) -> np.ndarray:
    """Boolean (n, 6): which listed neighbours are fresh (a = 0, l = v)."""

    return (a[neighbours] == 0) & (l[neighbours] == V)


def _certificate(a: np.ndarray, l: np.ndarray, geo: Geometry, active: np.ndarray) -> bool:
    if active.size == 0:
        return True
    return not bool(_fresh_neighbours(a, l, geo.neighbours[active]).any())


def absorbing_certificate(state: L0State) -> bool:
    """True iff no active site has a fresh face neighbour."""

    return _certificate(state.a, state.l, state.geometry, np.flatnonzero(state.a > 0))


_EMPTY = np.zeros(0, dtype=np.int64)
_EMPTY.setflags(write=False)


def _advance(
    a: np.ndarray,
    l: np.ndarray,
    geo: Geometry,
    frontier: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, dict[str, Any]]:
    """One synchronous tick applied in place to ``a`` and ``l``.

    ``frontier`` holds, in ascending (lexicographic) order, every active site
    that has a fresh neighbour; it may also hold other active sites.  An active
    site with no fresh neighbour never sends again in L0 (fresh sites are never
    created), and it draws nothing, so leaving it out changes no draw.  Only the
    frontier and its neighbours are read, and only sources and newly activated
    sites are written.  Returns the new frontier and the tick record, whose
    ``ledger_delta`` is the change of sum(a + l) over the written sites.
    """

    eligible = _fresh_neighbours(a, l, geo.neighbours[frontier])
    counts = eligible.sum(axis=1)
    has_target = counts > 0
    sources = frontier[has_target]
    if sources.size == 0:
        record = {"sources": _EMPTY, "targets": _EMPTY, "activated": _EMPTY, "touched": _EMPTY, "ledger_delta": 0}
        return _EMPTY, record
    eligible = eligible[has_target]
    counts = counts[has_target]

    u = rng.random(sources.size)
    choice = np.floor(u * counts).astype(np.int64)
    running = np.cumsum(eligible, axis=1)
    column = np.argmax(running == (choice + 1)[:, None], axis=1)
    targets = geo.neighbours[sources, column]
    activated, received = np.unique(targets, return_counts=True)

    before = int(a[sources].sum() + l[sources].sum() + a[activated].sum() + l[activated].sum())
    a[sources] -= 1
    a[activated] = V + received
    l[activated] = 0
    # Exhausted sources already have l = 0: they were active.
    after = int(a[sources].sum() + l[sources].sum() + a[activated].sum() + l[activated].sum())

    candidates = np.union1d(sources[a[sources] > 0], activated)
    still_eligible = _fresh_neighbours(a, l, geo.neighbours[candidates]).any(axis=1)
    touched = np.union1d(sources, activated)
    return candidates[still_eligible], {
        "sources": sources,
        "targets": targets,
        "activated": activated,
        "touched": touched,
        "ledger_delta": after - before,
    }


def step(state: L0State, rng: np.random.Generator) -> tuple[L0State, dict[str, Any]]:
    """One synchronous tick; returns a new state and the tick record."""

    new = state.copy()
    _, record = _advance(new.a, new.l, new.geometry, np.flatnonzero(new.a > 0), rng)
    return new, record


def seed_adjacent_fresh_cluster_size(fresh: np.ndarray, L: int, seed: tuple[int, int, int] | None = None) -> int:
    """C: fresh sites in the union of face6 fresh clusters adjacent to the seed."""

    geo = geometry(L, default_seed(L) if seed is None else tuple(seed))
    open_sites = np.asarray(fresh, dtype=bool).reshape(-1).copy()
    open_sites[geo.seed_index] = False
    visited = np.zeros(open_sites.size, dtype=bool)
    visited[geo.seed_index] = True
    frontier = np.array([geo.seed_index], dtype=np.int64)
    count = 0
    while frontier.size:
        candidates = np.unique(geo.neighbours[frontier].ravel())
        candidates = candidates[open_sites[candidates] & ~visited[candidates]]
        visited[candidates] = True
        count += int(candidates.size)
        frontier = candidates
    return count


def run_from_state(
    state: L0State,
    dynamics_rng: np.random.Generator,
    horizon: int,
    *,
    censor: bool = True,
) -> dict[str, Any]:
    """Evolve until absorption, censoring, or the horizon.

    ``n_t[i]`` and ``r2_sum_t[i]`` describe tick ``i + 1``.  The run stops at
    the censoring tick (SPEC_QUESTIONS.md Q-CENS-2).
    """

    geo = state.geometry
    radius = geo.L / 2 - 4
    state = state.copy()
    a, l = state.a, state.l
    total = state.ledger_total()
    active = np.flatnonzero(a > 0)
    reached = int(active.size)
    frontier = active[_fresh_neighbours(a, l, geo.neighbours[active]).any(axis=1)]
    n_t: list[int] = []
    r2_sum_t: list[int] = []
    absorbed_at = 0 if frontier.size == 0 else None
    censored_at = None
    max_residual = 0
    t = 0
    while absorbed_at is None and censored_at is None and t < horizon:
        t += 1
        frontier, record = _advance(a, l, geo, frontier, dynamics_rng)
        max_residual = max(max_residual, abs(record["ledger_delta"]))
        touched = record["touched"]
        activated = record["activated"]
        n_t.append(int(touched.size))
        r2_sum_t.append(int(geo.r2[touched].sum()))
        reached += int(activated.size)
        if censor and activated.size and geo.chebyshev[activated].max() >= radius:
            censored_at = t
        if frontier.size == 0:
            absorbed_at = t
    max_residual = max(max_residual, abs(state.ledger_total() - total))
    stranded = int(a.sum()) if absorbed_at is not None else None
    return {
        "n_t": np.asarray(n_t, dtype=np.int64),
        "r2_sum_t": np.asarray(r2_sum_t, dtype=np.int64),
        "absorbed_at": absorbed_at,
        "censored_at": censored_at,
        "ticks_run": t,
        "S": reached,
        "stranded_amplitude": stranded,
        "ledger_residual": max_residual,
        "final_state": state,
    }


def run_medium(
    fresh: np.ndarray,
    dynamics_rng: np.random.Generator,
    horizon: int,
    L: int,
    *,
    seed: tuple[int, int, int] | None = None,
    censor: bool = True,
) -> dict[str, Any]:
    """Run on a given fresh mask and attach C and E for absorbed runs."""

    state = initial_state(fresh, L, seed)
    record = run_from_state(state, dynamics_rng, horizon, censor=censor)
    if record["absorbed_at"] is not None:
        C = seed_adjacent_fresh_cluster_size(fresh, L, seed)
        record["C"] = C
        record["E"] = (record["S"] - 1) / C if C >= 1 else None
    else:
        record["C"] = None
        record["E"] = None
    return record


def run_with_streams(
    rho: float,
    medium_rng: np.random.Generator,
    dynamics_rng: np.random.Generator,
    horizon: int,
    L: int = REGISTERED_L,
) -> dict[str, Any]:
    fresh = draw_medium(rho, medium_rng, L)
    record = run_medium(fresh, dynamics_rng, horizon, L)
    del record["final_state"]
    return record


def run(rho: float, run_seed: int, horizon: int, L: int = REGISTERED_L) -> dict[str, Any]:
    """One registered-form L0 run: per_run_record of iota_spreading.json."""

    medium_rng, dynamics_rng = iota_streams(run_seed)
    return run_with_streams(rho, medium_rng, dynamics_rng, horizon, L)
