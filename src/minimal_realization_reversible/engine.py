"""MIR-REVERSIBLE-001 engine: second-order (Fredkin) reversible radius-1 rules
on an oriented cycle, evaluated with the inherited centered isolated-dyad
outward-effect detector (MIR-ISOLATED-DYAD-OUTWARD-EFFECT-CENTERED-V0.1).

Dynamics (order=2):  x[t+1][i] = f(x[t][i-1], x[t][i], x[t][i+1]) XOR x[t-1][i]
Dynamics (order=1):  x[t+1][i] = f(...)  (parent family; used only for the
                     cross-check against the already-opened parent result).
f is given by its Wolfram code w: f(abc) = (w >> (4a+2b+c)) & 1.
Seed: x[-1] = 0, x[0] = e_0.  Comparator: x[-1] = x[0] = 0, same rule.
Interventions act on layer t only; layer t-1 (memory) is left unchanged.
"""
from __future__ import annotations

ROLE = ((-1, 0), (0, 1), (1, 1), (2, 0))
SHAM, BREAK = (0, 1, 1), (1, 0, 1)


def step(w, prev, cur, order):
    n = len(cur)
    nxt = [(w >> (4 * cur[i - 1] + 2 * cur[i] + cur[(i + 1) % n])) & 1 for i in range(n)]
    if order == 2:
        nxt = [a ^ b for a, b in zip(nxt, prev)]
    return cur, nxt


def orbit(w, n, layers, order, seed=True):
    prev, cur = [0] * n, [0] * n
    if seed:
        cur[0] = 1
    out = [(prev, cur)]
    for _ in range(layers):
        prev, cur = step(w, prev, cur, order)
        out.append((prev, cur))
    return out  # out[t] = (x[t-1], x[t])


def in_cone(locus, t, n):
    d = locus % n
    return min(d, n - d) <= t


def is_role(x, a):
    n = len(x)
    return all(x[(a + o) % n] == v for o, v in ROLE)


def attributed(x, cx, a):
    n = len(x)
    return is_role(x, a) and cx[a % n] == 0 and cx[(a + 1) % n] == 0


def endpoint(w, prev, cur, a, window, order):
    n = len(cur)
    cur = list(cur)
    for k, v in enumerate(window):
        cur[(a + k) % n] = v
    for _ in range(2):
        prev, cur = step(w, prev, cur, order)
    return cur[(a + 3) % n]


def evaluate(w, n=64, order=2, horizon=None):
    """Return first_role, first_successor, first_intervention_eligible,
    first_complete_pass as (layer, anchor) or None, for formation t <= horizon."""
    if horizon is None:
        horizon = max(t for t in range(n) if 2 * (t + 2) < n)
    ob = orbit(w, n, horizon + 2, order, True)
    oc = orbit(w, n, horizon + 2, order, False)
    first = dict(first_role=None, first_successor=None,
                 first_intervention_eligible=None, first_complete_pass=None)
    for t in range(1, horizon + 1):  # initial state must fail
        prev, x = ob[t]
        cx = oc[t][1]
        x1, cx1 = ob[t + 1][1], oc[t + 1][1]
        for a in range(n):
            if not (attributed(x, cx, a) and in_cone(a, t, n) and in_cone(a + 1, t, n)):
                continue
            if first['first_role'] is None:
                first['first_role'] = (t, a)
            succ = None
            for s in (0, 1):
                b = a + s
                if attributed(x1, cx1, b) and in_cone(b, t + 1, n) and in_cone(b + 1, t + 1, n):
                    succ = b % n
                    break
            if succ is None:
                continue
            if first['first_successor'] is None:
                first['first_successor'] = (t, a)
            if not (in_cone(a + 3, t + 2, n) and x[(a + 3) % n] == 0):
                continue
            if first['first_intervention_eligible'] is None:
                first['first_intervention_eligible'] = (t, a)
            if endpoint(w, prev, x, a, SHAM, order) != endpoint(w, prev, x, a, BREAK, order):
                first['first_complete_pass'] = (t, a)
                return first
    return first
