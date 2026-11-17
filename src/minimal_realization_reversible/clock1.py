"""MIR-REVERSIBLE-CLOCK-001: does a shadow domain change every coherence's clock by one common factor (metric-like),
or does each coherence feel it differently (medium-like)? See docs/ICP_MIR_REVERSIBLE_CLOCK_001_CONTRACT.md.

Shadow: for each rule, the first (target L species, reader R species, tau phase index m, d in 24..39) in SPECIES-001
order whose collision at T = 600 leaves no movers and a background (order2 readout). Its leftmost / rightmost domain is
the medium for probes from the left / right.
Probe: every species of that side, seeded at tau_P = first phase-aligned tick >= TL, placed gapx + j cells outside
the shadow edge (TL in {1000, 1600}; j in 0..7). Leading edge = outer end of the leading cluster of P XOR N (gap 8).
Inside: the N-world window around the leading edge (WB behind, M ahead) is spatially periodic with the medium's period
and is not the current vacuum. On the longest contiguous inside segment (>= 180 ticks), the exact orbit of the P-world
window around the leading edge (period P', shift D', confirmed twice) gives the in-medium clock.
Types: localized (the difference cluster stays <= 16 wide over the segment), front (it grows: the traveller rewrites the
medium), no_entry, short, *_noorbit.
kappa_f = P_vac / P', kappa_v = (D' / P') / v_vac.
"""
import hashlib, json, math, os, subprocess, sys, time
os.environ.setdefault('OMP_NUM_THREADS', '1')
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction as Fr
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import minimal_realization_reversible.order2 as O2
from minimal_realization_reversible.vacuum_collide import step
TAG = 'mir-reversible-clock-001-v0.1-frozen'
P_ = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_CLOCK_001_CONTRACT.md'] + [P_ + f for f in ('clock1.py', 'order2.py', 'species1.py',
          'inventory1.py', 'collide2.py', 'vacuum_collide.py')] + ['output/minimal_realization/MIR-REVERSIBLE-SPECIES-001/results.json']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/clock1_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-CLOCK-001'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
X0 = O2.X0
TLS, JS, GAPX, RUN, PMAX, WB, M, WLOC, G = (1000, 1600), range(8), 40, 1600, 240, 24, 8, 16, 8
CONTROL_LAG = ['147', '201']


def periodic(q, a, b, s):
    w = q[a:b + 1]; return bool(np.all(w[s:] == w[:-s]))


def clusters(d, gap):
    on = np.flatnonzero(d)
    if not on.size: return []
    br = np.flatnonzero(np.diff(on) > gap); st = [on[0]] + list(on[br + 1]); en = list(on[br]) + [on[-1]]
    return [(int(a), int(b)) for a, b in zip(st, en)]


def shadow_maker(R, T=600):
    Ls = [o for o in R.sp if o['v'] < 0]; Rs = [o for o in R.sp if o['v'] > 0]
    for X in Ls[:3]:
        for a in Rs[:3]:
            for m in range(X['P'] // R.pv):
                for d in range(24, 40):
                    objs = [(X, X['phase'] + m * R.pv, X0), (a, a['phase'], X0 - d)]
                    p, c = O2.run(R, *O2.world(R, objs), T); mv, bg, _ = O2.readout(R, p, c, T)
                    if bg and not mv: return objs, (X['id'], a['id'], m, d), bg
    return None, None, None


def edge(R, objs, T, side):
    p, c = O2.run(R, *O2.world(R, objs), T); d = np.flatnonzero((p ^ R.V[T % R.pv]) | (c ^ R.V[T % R.pv + 1]))
    return int(d[0]) if side == 1 else int(d[-1])


def transit(R, objs, probe, side, dom_s, TL, j):
    tau = probe['phase'] + R.pv * math.ceil((TL - probe['phase']) / R.pv)
    e = edge(R, objs, tau, side); xP = e - GAPX - j if side == 1 else e + GAPX + j
    try:
        pN, cN = O2.world(R, objs); pP, cP = O2.world(R, objs + [(probe, tau, xP)])
    except ValueError:
        return dict(type='placement')
    rec = {}
    for t in range(tau + RUN):
        if t >= tau:
            cl = clusters((pN ^ pP) | (cN ^ cP), G)
            if cl:
                a, b = cl[-1] if side == 1 else cl[0]; x = b if side == 1 else a
                lo, hi = (x - WB, x + M) if side == 1 else (x - M, x + WB)
                qN = 2 * pN + cN; ph = t % R.pv; vac = 2 * R.V[ph] + R.V[ph + 1]
                if periodic(qN, lo, hi, dom_s) and not np.all(qN[lo:hi + 1] == vac):
                    qP = 2 * pP + cP; rec[t] = (x, qP[lo:hi + 1].tobytes(), (b - a + 1) <= WLOC)
        pN, cN = step(R.tab, pN, cN); pP, cP = step(R.tab, pP, cP)
    if not rec: return dict(type='no_entry')
    ts = sorted(rec); segs = []; cur = [ts[0]]
    for x in ts[1:]:
        if x == cur[-1] + 1: cur.append(x)
        else: segs.append(cur); cur = [x]
    segs.append(cur); seg = max(segs, key=len)
    if len(seg) < 3 * PMAX // 4: return dict(type='short')
    t0 = seg[16]; A = rec[t0]; typ = 'localized' if all(rec[t][2] for t in seg[16:]) else 'front'
    for P in range(1, PMAX + 1):
        B = rec.get(t0 + P); C = rec.get(t0 + 2 * P)
        if B is None or C is None: break
        if B[1] == A[1] and C[1] == A[1] and C[0] - B[0] == B[0] - A[0]:
            kf = Fr(probe['P'], P); kv = (Fr(B[0] - A[0], P) / probe['v'])
            return dict(type=typ, P=P, D=B[0] - A[0], kf=str(kf), kv=str(kv))
    return dict(type=typ + '_noorbit')


def job(a):
    lab, w, species, side, mode = a
    R = O2.Rule(w, species); objs, key, bg = shadow_maker(R)
    if objs is None: return dict(lab=lab, side=side, err='no shadow')
    doms = eval(bg[0]); ds = doms[0][0] if side == 1 else doms[-1][0]; med = repr(doms[0] if side == 1 else doms[-1])
    sp = sorted([o for o in R.sp if o['v'] * side > 0], key=lambda o: o['id'])
    rows = []
    for o in sp:
        for TL in TLS:
            for j in (JS if mode == 'full' else range(1)):
                r = transit(R, objs, o, side, ds, TL, j); r.update(sp=o['id'], TL=TL, j=j); rows.append(r)
    return dict(lab=lab, side=side, shadow=key, medium=med, n_species=len(sp), rows=rows)


def analyse(res):
    T = {}
    for r in res:
        k = f"{r['lab']}{'L' if r['side'] == 1 else 'R'}"; rows = r['rows']
        loc = [x for x in rows if x['type'] == 'localized']; fr = [x for x in rows if x['type'] == 'front']
        T[k] = dict(medium=r['medium'], types=dict(Counter(x['type'] for x in rows)),
                    loc_species=len({x['sp'] for x in loc}), loc_kf=sorted({x['kf'] for x in loc}), loc_kv=sorted({x['kv'] for x in loc}),
                    loc_metric=all(x['kf'] == x['kv'] for x in loc), front_species=len({x['sp'] for x in fr}),
                    front_speeds=sorted({str(Fr(x['D'], x['P'])) for x in fr}))
    return T


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    S = {f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}": r for r in json.load(open(OM / 'MIR-REVERSIBLE-SPECIES-001/results.json'))['rules']}
    J = [(lab, S[lab]['wolfram'], S[lab]['species'], side, 'full') for lab in O2.ELIGIBLE for side in (1, -1)]
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(5) as ex: res = list(ex.map(job, J))
    T = analyse(res)
    ctrl = [T[k] for k in T if k[:-1] in CONTROL_LAG]
    Sm = dict(V_lag=all(t['loc_species'] >= 2 and t['loc_kf'] == ['1'] and t['loc_kv'] == ['1'] for t in ctrl))
    med = {k: t for k, t in T.items() if k[:-1] not in CONTROL_LAG}
    elig_u = {k: t for k, t in med.items() if t['loc_species'] >= 2}
    elig_f = {k: t for k, t in med.items() if t['front_species'] >= 2}
    Sm['U_eligible'] = sorted(elig_u); Sm['F_eligible'] = sorted(elig_f)
    Sm['H_U_pass'] = sorted(k for k, t in elig_u.items() if len(t['loc_kf']) == 1 and len(t['loc_kv']) == 1)
    Sm['H_M_pass'] = sorted(k for k, t in elig_u.items() if t['loc_metric'] and len(t['loc_kf']) == 1)
    Sm['H_F_pass'] = sorted(k for k, t in elig_f.items() if len(t['front_speeds']) == 1)
    Sm['valid'] = Sm['V_lag'] and len(elig_u) >= 1
    v = lambda ps, el, need: 'invalid' if not Sm['valid'] else 'n/a' if not el else 'supported' if len(ps) >= need(len(el)) else 'not_supported'
    Sm['H_U'] = v(Sm['H_U_pass'], elig_u, lambda n: n); Sm['H_M'] = v(Sm['H_M_pass'], elig_u, lambda n: n)
    Sm['H_F'] = v(Sm['H_F_pass'], elig_f, lambda n: math.ceil(2 * n / 3))
    Sm['table'] = T
    (OUT / 'results.json').write_text(json.dumps(dict(summary=Sm, jobs=res), indent=1, default=str) + '\n')
    print(json.dumps({k: Sm[k] for k in ('valid', 'V_lag', 'H_U', 'H_M', 'H_F', 'U_eligible', 'F_eligible', 'H_U_pass', 'H_F_pass')}))


if __name__ == '__main__':
    main()
