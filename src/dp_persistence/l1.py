"""IOTA-MIN-L1 reactivation rule, for the synthetic analytic check only.

L1 is L0 plus reactivation (minimal_law.json laws.L1).  This module exposes a
single tick and the L1 absorbing test.  It has no sweep entry point.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .l0_engine import V, L0State


REGISTERED_R = 0.02


def l1_absorbing(state: L0State, r: float) -> bool:
    """True iff no active site can send a quantum under L1.

    A transfer is possible iff some active site borders a fresh site, or
    ``r > 0`` and some active site borders a depleted site.
    """

    geo = state.geometry
    active = np.flatnonzero(state.a > 0)
    if active.size == 0:
        return True
    fresh = (state.a == 0) & (state.l == V)
    depleted = (state.a == 0) & (state.l == 0)
    neighbours = geo.neighbours[active]
    if fresh[neighbours].any():
        return False
    return not (r > 0 and bool(depleted[neighbours].any()))


def step(state: L0State, rng: np.random.Generator, r: float = REGISTERED_R) -> tuple[L0State, dict[str, Any]]:
    """One synchronous L1 tick, using the registered draw rule.

    For each active source in lexicographic order: one draw per depleted
    neighbour in the fixed neighbour order (included iff u < r), then, if the
    eligible set is non-empty, one target draw as in L0, all from ``rng``.
    """

    geo = state.geometry
    fresh = (state.a == 0) & (state.l == V)
    depleted = (state.a == 0) & (state.l == 0)
    sources: list[int] = []
    targets: list[int] = []
    for source in np.flatnonzero(state.a > 0):
        eligible = []
        for neighbour in geo.neighbours[source]:
            if fresh[neighbour]:
                eligible.append(int(neighbour))
            elif depleted[neighbour]:
                if rng.random() < r:
                    eligible.append(int(neighbour))
        if eligible:
            u = rng.random()
            sources.append(int(source))
            targets.append(eligible[math.floor(u * len(eligible))])

    new = state.copy()
    received: dict[int, int] = {}
    for source, target in zip(sources, targets):
        new.a[source] -= 1
        received[target] = received.get(target, 0) + 1
    for target, k in received.items():
        if fresh[target]:
            new.a[target] = V + k
        else:
            new.a[target] = k
        new.l[target] = 0
    return new, {
        "sources": np.asarray(sources, dtype=np.int64),
        "targets": np.asarray(targets, dtype=np.int64),
    }
