"""BUDGET-000 extension: exact window-3 invariants of the 14 invariant rules (rules only; no shadow outcomes).

For each rule: exact null space of the k=3 coboundary system (budget0.system). From its phi-projection keep only the
vectors that are independent modulo constants, window-3 coboundaries and lifts of the window-2 basis; their count
must equal n3 - n2 from BUDGET-000. Each new density is a table over the 64 three-cell words (cell code 2p+c, word
index 16 w0 + 4 w1 + w2), shifted by a constant so that the homogeneous vacuum has density 0 in every phase (the
shift must be phase-independent), then scaled to coprime integers. Ring totals of these tables are gauge-free.
Checked by simulation (exact conservation on L = 37, 64, 101; 50 random states, 400 steps).
"""
import json, sys
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from math import gcd
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible import budget0 as B
OUT = B.OUT / 'window3.json'
W3 = B.words(3)


def lift2(coef):
    """Window-2 normal-form density as a 64-table on (w0, w1, w2): phi2(w0, w1)."""
    t = B.MNF @ np.array(coef); return [Fraction(int(t[4 * a + b])) for a, b, _ in W3]


def trivial3():
    rows = [[Fraction(1)] * 64]
    for g in range(16):
        rows.append([Fraction(int(4 * b + c == g) - int(4 * a + b == g)) for a, b, c in W3])
    return rows


def rank(rows):
    return len(B.rref(rows)[0]) if rows else 0


def total3(tab, p, c):
    cell = 2 * p + c; return np.asarray(tab)[16 * cell + 4 * np.roll(cell, -1, -1) + np.roll(cell, -2, -1)].sum(-1)


def extract(w):
    r0 = json.loads((B.OUT / 'results.json').read_text())['rules'][str(w)]
    n2, n3 = r0['nontrivial_by_window']['2'], r0['nontrivial_by_window']['3']
    A, nphi = B.system(w, 3); span = trivial3() + [lift2(c) for c in r0['window2_coeffs']]; rk = rank(span); new = []
    for v in B.nullspace(A.tolist()):
        phi = v[:nphi]
        if rank(span + [phi]) > rk:
            span.append(phi); rk += 1; new.append(phi)
    assert len(new) == n3 - n2, (w, len(new), n3 - n2)
    out = []
    for phi in new:
        orb = r0['vacuum_orbit']; vals = {phi[21 * (2 * q + r)] for q, r in orb}  # 21 = 16+4+1: homogeneous word
        assert len(vals) == 1, (w, 'vacuum density phase-dependent', vals)
        s = vals.pop(); phi = [x - s for x in phi]
        L = int(np.lcm.reduce([x.denominator for x in phi])); z = [int(x * L) for x in phi]
        g = 0
        for x in z: g = gcd(g, abs(x))
        out.append([x // g for x in z])
    rng = np.random.default_rng(w); ok = True
    for Lr in (37, 64, 101):
        p, c = rng.integers(0, 2, (50, Lr)), rng.integers(0, 2, (50, Lr)); E0 = [total3(t, p, c) for t in out]
        for _ in range(400): p, c = B.stepv(w, p, c)
        ok &= all((total3(t, p, c) == e).all() for t, e in zip(out, E0))
    vac = [[int(t[21 * (2 * q + r)]) for q, r in r0['vacuum_orbit']] for t in out]
    return w, dict(n2=n2, n3=n3, new_window3=len(out), tables=out, simulation_conserved=bool(ok), vacuum_density=vac)


def main():
    rules = [w for w, _ in B.RULES if json.loads((B.OUT / 'results.json').read_text())['rules'][str(w)]['nontrivial_by_window']['2'] > 0]
    with ProcessPoolExecutor(4) as ex: res = dict(ex.map(extract, rules))
    for w, e in res.items(): print(w, e['n2'], e['n3'], e['new_window3'], e['simulation_conserved'], flush=True)
    OUT.write_text(json.dumps(dict(id='MIR-REVERSIBLE-BUDGET-000 window-3 extension', word_index='16*w0+4*w1+w2, w=2p+c',
                                   rules=res), indent=1) + '\n')


if __name__ == '__main__':
    main()
