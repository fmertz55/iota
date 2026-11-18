"""Elasticity v2: a single collision is elastic iff it leaves no background and, in each direction, the movers' total
deviation-cell count (both layers) equals that of the free incoming object moving that way, at the same tick."""
import numpy as np
import minimal_realization_reversible.order2 as O2


def mass(R, p, c, t, pos):
    V = R.V; ph = t % R.pv; d = (p ^ V[ph]).astype(int) + (c ^ V[ph + 1]).astype(int); out = {1: 0, -1: 0}
    for a, b in O2.clusters((p ^ V[ph]) | (c ^ V[ph + 1])):
        k = [q for q in pos if q[2] == a]
        if k: out[k[0][1]] += int(d[a:b + 1].sum())
    return out


def elastic(R, X, tau, al, d, side, T):
    p, c = O2.run(R, *O2.world(R, [(X, tau, O2.X0), (al, al['phase'], O2.X0 - side * d)]), T)
    mv, bg, pos = O2.readout(R, p, c, T)
    if bg: return False
    m = mass(R, p, c, T, pos); ref = {1: 0, -1: 0}
    for o, x in ((X, O2.X0), (al, O2.X0 - side * d)):
        pf, cf = O2.run(R, *O2.world(R, [(o, tau if o is X else o['phase'], x)]), T)
        _, _, pp = O2.readout(R, pf, cf, T); mm = mass(R, pf, cf, T, pp); ref[1] += mm[1]; ref[-1] += mm[-1]
    return m == ref
