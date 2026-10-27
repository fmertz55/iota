"""Independent pure-Python replay of IOTA-MIN-L0.

This module deliberately shares no code with ``l0_engine``: it uses
coordinate tuples, dictionaries, and per-site loops, and draws one scalar
``rng.random()`` per eligible source.  Only the seed derivation in ``rng`` is
shared.  It must agree with the vectorized engine bit for bit.
"""

from __future__ import annotations

import math
from typing import Any

from .rng import iota_streams


LATENT = 2
SEED_AMPLITUDE = 7
ORDER = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


class ReplayState:
    """Active amplitudes by coordinate, plus the set of fresh coordinates."""

    def __init__(self, size: int, seed: tuple[int, int, int], active: dict, fresh: set) -> None:
        self.size = size
        self.seed = seed
        self.active = active
        self.fresh = fresh

    def clone(self) -> "ReplayState":
        return ReplayState(self.size, self.seed, dict(self.active), set(self.fresh))

    def ledger(self) -> int:
        return sum(self.active.values()) + LATENT * len(self.fresh)

    def neighbours(self, site: tuple[int, int, int]) -> list[tuple[int, int, int]]:
        n = self.size
        x, y, z = site
        return [((x + dx) % n, (y + dy) % n, (z + dz) % n) for dx, dy, dz in ORDER]

    def separation(self, site: tuple[int, int, int]) -> tuple[int, int]:
        """(squared Euclidean, Chebyshev) minimum-image distance from the seed."""

        squares = 0
        largest = 0
        for c, s in zip(site, self.seed):
            d = abs(c - s)
            d = min(d, self.size - d)
            squares += d * d
            largest = max(largest, d)
        return squares, largest


def lexicographic_sites(size: int):
    for x in range(size):
        for y in range(size):
            for z in range(size):
                yield (x, y, z)


def build_state(fresh_sites, size: int, seed: tuple[int, int, int] | None = None) -> ReplayState:
    if seed is None:
        seed = (size // 2, size // 2, size // 2)
    seed = tuple(seed)
    fresh = set(tuple(site) for site in fresh_sites)
    fresh.discard(seed)
    return ReplayState(size, seed, {seed: SEED_AMPLITUDE}, fresh)


def replay_medium(rho: float, medium_rng, size: int) -> set:
    variates = medium_rng.random(size ** 3)
    fresh = set()
    position = 0
    for site in lexicographic_sites(size):
        if variates[position] < rho:
            fresh.add(site)
        position += 1
    return fresh


def certificate(state: ReplayState) -> bool:
    for site in state.active:
        for neighbour in state.neighbours(site):
            if neighbour in state.fresh:
                return False
    return True


def tick(state: ReplayState, rng) -> tuple[ReplayState, list[tuple[tuple, tuple]]]:
    transfers = []
    for source in sorted(state.active):
        options = [nb for nb in state.neighbours(source) if nb in state.fresh]
        if not options:
            continue
        u = rng.random()
        transfers.append((source, options[math.floor(u * len(options))]))

    after = state.clone()
    incoming: dict[tuple, int] = {}
    for source, target in transfers:
        after.active[source] -= 1
        incoming[target] = incoming.get(target, 0) + 1
    for source, _ in transfers:
        if after.active.get(source) == 0:
            del after.active[source]
    for target, k in incoming.items():
        after.fresh.remove(target)
        after.active[target] = LATENT + k
    return after, transfers


def cluster_next_to_seed(fresh: set, size: int, seed: tuple[int, int, int]) -> int:
    probe = ReplayState(size, seed, {}, set())
    seen = {seed}
    queue = [seed]
    found = 0
    while queue:
        site = queue.pop()
        for neighbour in probe.neighbours(site):
            if neighbour in fresh and neighbour not in seen:
                seen.add(neighbour)
                found += 1
                queue.append(neighbour)
    return found


def replay_run(
    fresh_sites,
    size: int,
    rng,
    horizon: int,
    *,
    seed: tuple[int, int, int] | None = None,
    censor: bool = True,
) -> dict[str, Any]:
    state = build_state(fresh_sites, size, seed)
    initial_fresh = set(state.fresh)
    start_total = state.ledger()
    reached = {state.seed}
    threshold = size / 2 - 4
    n_t: list[int] = []
    r2_sum_t: list[int] = []
    absorbed_at = 0 if certificate(state) else None
    censored_at = None
    worst = 0
    t = 0
    while absorbed_at is None and censored_at is None and t < horizon:
        t += 1
        state, transfers = tick(state, rng)
        units = set()
        newly = set()
        for source, target in transfers:
            units.add(source)
            units.add(target)
            newly.add(target)
        n_t.append(len(units))
        r2_sum_t.append(sum(state.separation(site)[0] for site in units))
        reached |= newly
        worst = max(worst, abs(state.ledger() - start_total))
        if censor and any(state.separation(site)[1] >= threshold for site in newly):
            censored_at = t
        if certificate(state):
            absorbed_at = t
    record: dict[str, Any] = {
        "n_t": n_t,
        "r2_sum_t": r2_sum_t,
        "absorbed_at": absorbed_at,
        "censored_at": censored_at,
        "ticks_run": t,
        "S": len(reached),
        "stranded_amplitude": sum(state.active.values()) if absorbed_at is not None else None,
        "ledger_residual": worst,
        "C": None,
        "E": None,
        "final_state": state,
    }
    if absorbed_at is not None:
        C = cluster_next_to_seed(initial_fresh, size, state.seed)
        record["C"] = C
        record["E"] = (record["S"] - 1) / C if C >= 1 else None
    return record


def replay(rho: float, run_seed: int, horizon: int, size: int = 64) -> dict[str, Any]:
    medium_rng, dynamics_rng = iota_streams(run_seed)
    fresh = replay_medium(rho, medium_rng, size)
    record = replay_run(fresh, size, dynamics_rng, horizon)
    del record["final_state"]
    return record
