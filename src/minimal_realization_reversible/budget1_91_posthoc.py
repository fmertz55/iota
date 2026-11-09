"""BUDGET-001 post hoc (not frozen): rule 91, the one pair where wall-segment budgets carry record bits beyond species
and flank phases (H_W_bits = 0.125). Per input: species pair, offset, outcome key, flanks, segments, cut sites. Lists the
(O, FL, species) classes with more than one segment-budget value, and saves the erased residue state at T for them."""
import json, math, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import minimal_realization_reversible.budget1 as B
from minimal_realization_reversible.vacuum_collide import step

W = 91


def main():
    B.S1.N = B.N
    j = next(j for j in B.S6.pairs() if j[0] == W and j[4].startswith('shadow')); tab, Rs, Ls = B.S7.lists(j)
    close = min(R['v'] - L['v'] for R in Rs for L in Ls); T = math.ceil(552 / close) + 300
    V = B.C2.vac_seq(tab, T + B.C2.PMAX + 4); rows = []
    for ri, li, off in [(ri, li, o) for ri in range(len(Rs)) for li in range(len(Ls)) for o in B.OFFS]:
        U = B.S6.place([(Rs[ri]['seed'], B.X0), (Ls[li]['seed'], B.X0 + off)])
        for _ in range(T): U = step(tab, *U)
        objs, _ = B.S1.objects(tab, *U, V, T); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[T]; c[a - 2:b + 3] = V[T + 1]
        on = np.flatnonzero((p ^ V[T]) | (c ^ V[T + 1]))
        if not on.size: continue
        lo, hi = int(on.min()), int(on.max()); sg, fl, _ = B.segments(W, p, c, lo, hi)
        O = tuple(sorted((x['species'], x['state'], x['pos']) for x in objs))
        rows.append(dict(ri=ri, li=li, off=off, O=str(O), FL=str(fl), SEG=sg, lo=lo, hi=hi, Bres=B.vec(W, p, c),
                         p=p[lo - 4:hi + 5].tolist(), c=c[lo - 4:hi + 5].tolist()))
    cls = defaultdict(list)
    for r in rows: cls[(r['O'], r['FL'], r['ri'], r['li'])].append(r)
    split = {k: v for k, v in cls.items() if len({str(r['SEG']) for r in v}) > 1}
    out = dict(T=T, residue_runs=len(rows), classes=len(cls), split_classes=len(split),
               split=[dict(ri=k[2], li=k[3], FL=k[1], members=[dict(off=r['off'], SEG=r['SEG'], lo=r['lo'], hi=r['hi'],
                      width=r['hi'] - r['lo'] + 1, Bres=r['Bres']) for r in v]) for k, v in split.items()],
               seg_by_input=[dict(ri=r['ri'], li=r['li'], off=r['off'], SEG=r['SEG'], FL=r['FL'], width=r['hi'] - r['lo'] + 1)
                             for r in rows])
    (B.OUT / 'posthoc_91.json').write_text(json.dumps(out, indent=1, default=str) + '\n')
    np.savez(B.OUT / 'posthoc_91_states.npz', **{f"r{r['ri']}{r['li']}o{r['off']}": np.array([r['p'], r['c']], np.uint8) for r in rows})
    print(json.dumps({k: out[k] for k in ('T', 'residue_runs', 'classes', 'split_classes')}))
    for s in out['split'][:6]: print(s['ri'], s['li'], s['FL'], [(m['off'], m['SEG'], m['width']) for m in s['members']])


if __name__ == '__main__':
    main()
