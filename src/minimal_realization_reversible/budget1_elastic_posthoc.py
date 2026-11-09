"""BUDGET-001 post hoc (not frozen): check of the elastic readout. Do residue-free runs (pass-throughs) register as
elastic under the same species-id convention? If not, the frozen elastic_frac = 0 is a convention artifact."""
import json, math, sys
from collections import Counter
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import minimal_realization_reversible.budget1 as B
from minimal_realization_reversible.vacuum_collide import step


def check(j):
    B.S1.N = B.N
    w, _, _, _, role = j; tab, Rs, Ls = B.S7.lists(j)
    close = min(R['v'] - L['v'] for R in Rs for L in Ls); T = math.ceil(552 / close) + 300
    V = B.C2.vac_seq(tab, T + B.C2.PMAX + 4)
    sR = [B.sid(tab, o['seed']) for o in Rs]; sL = [B.sid(tab, o['seed']) for o in Ls]
    c = Counter()
    for ri, li, off in [(ri, li, o) for ri in range(len(Rs)) for li in range(len(Ls)) for o in B.OFFS]:
        U = B.S6.place([(Rs[ri]['seed'], B.X0), (Ls[li]['seed'], B.X0 + off)])
        for _ in range(T): U = step(tab, *U)
        objs, resid = B.S1.objects(tab, *U, V, T); p, q = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[T]; q[a - 2:b + 3] = V[T + 1]
        has = bool(((p ^ V[T]) | (q ^ V[T + 1])).any())
        el = Counter([sR[ri], sL[li]]) == Counter(x['species'] for x in objs)
        c[(has, el, len(objs))] += 1
    return w, {f'residue={h} elastic={e} n_out={k}': m for (h, e, k), m in sorted(c.items())}


if __name__ == '__main__':
    from concurrent.futures import ProcessPoolExecutor
    jobs = [j for j in B.S6.pairs() if j[0] in B.INV and j[4].startswith('shadow')]
    with ProcessPoolExecutor(4) as ex: res = dict(ex.map(check, jobs))
    out = B.OUT / 'posthoc_elastic_check.json'; out.write_text(json.dumps(res, indent=1) + '\n')
    for w, r in res.items(): print(w, r)
