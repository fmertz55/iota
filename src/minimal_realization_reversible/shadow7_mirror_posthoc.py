"""Post hoc (not frozen) for SHADOW-007: exact mirror control on mirror-symmetric rules.
For each input, take the erased state s at T. Reader a reads s from the left (as frozen). Reader m runs reader a's
exact procedure on the reflected state M(s): physically, the mirror image of reader a reading s's right edge with
exactly mirrored geometry. chi = footprint_a - footprint_m != 0 means the record itself is handed."""
import json, math, sys, os
os.environ.setdefault('OMP_NUM_THREADS', '1')
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'src'))
import minimal_realization_reversible.shadow7 as S7, minimal_realization_reversible.shadow6 as S6
import minimal_realization_reversible.shadow as S1
from minimal_realization_reversible.vacuum_collide import step
from minimal_realization_reversible import collide2 as C2
H = S7.H; OUT = S7.OUT

def mrule(w):
    t = S7.table(w); return sum(int(t[4 * (i & 1) + (i & 2) + (i >> 2)]) << i for i in range(8))

def run(j):
    S1.N = S7.N
    w, role = j[0], j[4]; tab, Rs, Ls = S7.lists(j)
    close = min(R['v'] - L['v'] for R in Rs for L in Ls); T = math.ceil(552 / close) + 300
    V = C2.vac_seq(tab, T + S7.RUN + C2.PMAX + 4); N, X0, GAP = S7.N, S7.X0, S7.GAP
    st, O, left, right = [], [], [], []
    for ri in range(len(Rs)):
        for li in range(len(Ls)):
            for off in S7.OFFS:
                U = S7.place([(Rs[ri]['seed'], X0), (Ls[li]['seed'], X0 + off)])
                for _ in range(T): U = step(tab, *U)
                objs, resid = S1.objects(tab, *U, V, T); p, c = U[0].copy(), U[1].copy()
                for x in objs:
                    a, b = x['span']; p[a - 2:b + 3] = V[T]; c[a - 2:b + 3] = V[T + 1]
                st.append((p, c)); O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs)))
                L_ = [a for a, _ in resid] + [x['span'][0] for x in objs]; R_ = [b for _, b in resid] + [x['span'][1] for x in objs]
                left.append(min(L_) if L_ else X0); right.append(max(R_) if R_ else X0)
    F, fa, fb = S7.free(tab, Rs[0]['seed'], T, V); wd = fb - fa + 1
    La = min(left) - GAP - wd; Lm = (N - 1 - max(right)) - GAP - wd
    def read(p, c, L0):
        Np, Nc = p, c
        for _ in range(S7.RUN): Np, Nc = step(tab, Np, Nc)
        Pp, Pc = p.copy(), c.copy(); Pp[L0:L0 + wd] = F[0][fa:fb + 1]; Pc[L0:L0 + wd] = F[1][fa:fb + 1]
        for _ in range(S7.RUN): Pp, Pc = step(tab, Pp, Pc)
        y = np.flatnonzero(Pc ^ Nc); return (tuple((y - y.min()).tolist()), int(y.min())) if y.size else ((), 0)
    Ya = [read(p, c, La) for p, c in st]; Ym = [read(p[::-1].copy(), c[::-1].copy(), Lm) for p, c in st]
    HO = H(O); only = math.log2(len(O)) - HO
    f = lambda *Ys: H(list(zip(O, *Ys))) - HO
    return dict(wolfram=w, role=role, only=only, footprint_a=f(Ya), footprint_m=f(Ym), joint_am=f(Ya, Ym),
                chi=f(Ya) - f(Ym), n=len(O))

if __name__ == '__main__':
    res = {(r['wolfram'], r['role']): r for r in json.load(open(OUT / 'results.json'))['rules']}
    jobs = [j for j in S6.pairs() if mrule(j[0]) == j[0]]
    with ProcessPoolExecutor(6) as ex: rows = list(ex.map(run, jobs))
    for r in rows:
        s = res[(r['wolfram'], r['role'])]['C']; r['stored_a'] = s['footprint_a']; r['stored_b'] = s['footprint_b']
        r['stored_joint'] = s['joint']; r['a_reproduced'] = abs(r['footprint_a'] - s['footprint_a']) < 1e-12
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    json.dump(rows, open(OUT / 'posthoc_mirror_control.json', 'w'), indent=1)
