"""MIR-REVERSIBLE-DESCRIBE-001: is the shadow description D a lossless coordinate system, including time?

Inputs, erasure, settling, aligned snapshots, components, domains, walls, speeds and kinds are WALL-001's (runs() below
is a verbatim copy of wall1.job up to the wall targets), with one change: the walls of rigid-mover components are
tracked too (the whole residue must be described). D of a run:
  global: the absolute tick (vacuum clock);
  per wall: WALL-001 descriptor (sub = orbit of its local window up to rotation, clock, place, speed v, period P),
            measured in the BUILD window [tw, tw + WT);
  per domain: its record (spatial period s, orbit-canonical species or vacuum lag) and its phase = its s-cell pattern
            aligned to x = 0 mod s at the last exact snapshot tL (< tw).
Rebuild at tick t, from D and the two dictionaries (wall orbits by sub, domain orbits by pattern) only:
  ambient vacuum everywhere; each domain's periodic pattern advanced from tL to t by the rule on an s-aligned ring,
  painted between its two walls' predicted edges; each wall's window at orbit phase (t - clock) mod P, at its predicted
  position place + v (t - j) + dx_j, painted on top.
Test: rebuild == both layers (q = 2p + c), every cell of the ring, at every tick of the FUTURE window
[tw + WT, tw + 2 WT), which is not used to build D. See docs/ICP_MIR_REVERSIBLE_DESCRIBE_001_CONTRACT.md.
"""
import hashlib, json, math, os, subprocess, sys
os.environ.setdefault('OMP_NUM_THREADS', '1')
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction as Fr
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import step
from minimal_realization_reversible import collide2 as C2
import minimal_realization_reversible.shadow as S1
import minimal_realization_reversible.shadow6 as S6
import minimal_realization_reversible.shadow7 as S7
import minimal_realization_reversible.phase1 as PH1
import minimal_realization_reversible.inventory1 as I1
import minimal_realization_reversible.wall1 as W1
TAG = 'mir-reversible-describe-001-v0.1-frozen'
P_ = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_DESCRIBE_001_CONTRACT.md'] + [P_ + f for f in (
    'describe1.py', 'wall1.py', 'inventory1.py', 'phase1.py', 'budget1.py', 'budget0.py', 'budget0_w3.py', 'shadow7.py',
    'shadow6.py', 'shadow3.py', 'shadow.py', 'collide2.py', 'vacuum_collide.py')] + [
    'output/minimal_realization/MIR-REVERSIBLE-WALL-001/results.json']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/describe1_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-DESCRIBE-001'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, OFFS, H, SETTLE = W1.N, W1.X0, W1.OFFS, W1.H, W1.SETTLE
L, S2, QDEN, TOL_END, TOL_MID, WMAX = W1.L, W1.S2, W1.QDEN, W1.TOL_END, W1.TOL_MID, W1.WMAX
MW, PWMAX, WT, ANCH = W1.MW, W1.PWMAX, W1.WT, W1.ANCH
EXPOSED = [91]
ELIGIBLE = ['147', '201', '22s', '26s', '58s', '82s', '114s']   # WALL-001 eligible set (stored)
NCTRL = 4                                                      # sensitivity controls per pair


def follow_d(p, c, t, V, tab, targets, tw):
    """wall1.follow extended: track to tw + 2 WT; windows recorded in the build window [tw, tw + WT) exactly as
    wall1.follow; q stored at every tick of the future window. Returns (desc, dicts, qfut, lost_future, edge)."""
    cur = {k: (lo, hi) for k, (lo, hi, _) in targets.items()}; seqs = {k: [] for k in targets}; lost = set(); edge = False
    lostf = set(); qf = []
    while t < tw + 2 * WT:
        q = 2 * p.astype(np.uint8) + c; amb = 2 * V[t] + V[t + 1]
        if t >= tw + WT: qf.append(q.copy())
        for k, (_, _, fl) in targets.items():
            if k in lost: continue
            lo, hi = cur[k]
            if lo - ANCH - 8 < 64 or hi + ANCH + 8 > N - 64: edge = True; lost.add(k); continue
            nlo, nhi = W1.bounds(q, amb, lo, hi, fl)
            if nhi - nlo + 1 > WMAX or nlo > nhi + 1 + I1.SMAX or abs(nlo - lo) > 2 * ANCH or abs(nhi - hi) > 2 * ANCH:
                lost.add(k); (lostf.add(k) if t >= tw + WT else None); continue
            cur[k] = (nlo, nhi)
            if tw <= t < tw + WT:
                seqs[k].append((nlo, nhi - nlo, q[min(nlo, nhi + 1) - MW:max(nhi, nlo - 1) + MW + 1].tobytes()))
        p, c = step(tab, p, c); t += 1
    out, orb = {}, {}
    for key, s in seqs.items():
        if key in lost and key not in lostf: out[key] = 'lost'; continue
        Pw = None
        for P in range(1, PWMAX + 1):
            d = s[P][0] - s[0][0]
            if all(s[j + P][1:] == s[j][1:] and s[j + P][0] - s[j][0] == d for j in range(WT - P)): Pw = P; break
        if Pw is None: out[key] = 'noclose'; continue
        sub, r = min((tuple((s[r + j][0] - s[r][0], s[r + j][1], s[r + j][2]) for j in range(Pw)), r) for r in range(Pw))
        d = s[Pw][0] - s[0][0]; vw = Fr(d, Pw); ts = tw + r
        h = hashlib.sha1(repr((Pw, d, sub)).encode()).hexdigest()[:12]
        out[key] = (h, ts % Pw, str(s[r][0] - vw * ts), str(vw), Pw); orb[h] = sub   # orb: the wall dictionary
    return out, orb, qf, lostf, edge


def wall_at(desc, orb, t):
    """Predicted (lo, width, window bytes, window start) of a wall at tick t from its descriptor alone."""
    h, clock, place, v, P = desc; v = Fr(v); j = (t - clock) % P; dx, wd, win = orb[h][j]
    lo = Fr(place) + v * (t - j) + dx; assert lo.denominator == 1; lo = int(lo)
    return lo, wd, win, min(lo, lo + wd + 1) - MW


def dom_rows(tab, s, pat, n):
    """Rows of an s-periodic domain: n ticks from its aligned pattern (q values) at tL; ring of m = s * ceil(12/s)."""
    m = s * math.ceil(12 / s); q0 = np.array(pat * (m // s), np.uint8); p, c = q0 >> 1, q0 & 1; rows = []
    for _ in range(n):
        rows.append((2 * p + c)[:s].copy()); p, c = step(tab, p, c)
    return rows


def rebuild(D, orb, tab, V, t, rows):
    """qhat at tick t from D. D = list of components: dict(walls=[desc], doms=[(s, pat)]); rows = cached domain rows."""
    qh = np.full(N, 2 * V[t] + V[t + 1], np.uint8); masks = dict(wall=np.zeros(N, bool), dom=np.zeros(N, bool))
    for ci, cm in enumerate(D):
        W = [wall_at(x, orb, t) for x in cm['walls']]
        for di, (s, pat) in enumerate(cm['doms']):
            a = W[di][0] + W[di][1] + 1; b = W[di + 1][0] - 1
            if b < a: continue
            row = rows[(ci, di)][t]
            xs = np.arange(a, b + 1); qh[a:b + 1] = row[xs % s]; masks['dom'][a:b + 1] = True
        for lo, wd, win, st in W:
            arr = np.frombuffer(win, np.uint8); qh[st:st + arr.size] = arr; masks['wall'][st:st + arr.size] = True
    return qh, masks


def runs(j):
    """Verbatim copy of wall1.job up to the wall targets; mover components' walls also targeted; returns per run the
    run class and, for describable runs, (targets, doms, tracking state)."""
    S1.N = N
    w, _, _, _, role = j; tab, Rs, Ls = S7.lists(j)
    close = min(R['v'] - L_['v'] for R in Rs for L_ in Ls); T = math.ceil(552 / close) + 300
    V0 = C2.vac_seq(tab, 64); pv = next(k for k in range(1, 50) if (V0[k], V0[k + 1]) == (V0[0], V0[1]))
    pR = [PH1.period(tab, o['seed'], C2.vac_seq(tab, C2.PMAX + 8)) for o in Rs]
    pL = [PH1.period(tab, o['seed'], C2.vac_seq(tab, C2.PMAX + 8)) for o in Ls]
    tau = {(ri, li): math.lcm(pR[ri][0], pL[li][0], pv) for ri in range(len(Rs)) for li in range(len(Ls))}
    cl = {k: Rs[k[0]]['v'] - Ls[k[1]]['v'] for k in tau}
    E = max(math.floor((OFFS[-1] - OFFS[0]) / v) for v in cl.values())
    tw = T + E + SETTLE + S2 + L
    V = C2.vac_seq(tab, tw + 2 * WT + 2 * pv + C2.PMAX + 16)
    tc = T + E + SETTLE + S2
    cache = {}
    seen = set(); out = []
    for ri, li, off in [(ri, li, o) for ri in range(len(Rs)) for li in range(len(Ls)) for o in OFFS]:
        U = S6.place([(Rs[ri]['seed'], X0), (Ls[li]['seed'], X0 + off)]); kb = U[0].tobytes() + U[1].tobytes()
        if kb in seen: continue
        seen.add(kb)
        for _ in range(T): U = step(tab, *U)
        e = math.floor((off - OFFS[0]) / cl[(ri, li)]); t = T
        for _ in range(e + SETTLE): U = step(tab, *U); t += 1
        objs, _ = S1.objects(tab, *U, V, t); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[t]; c[a - 2:b + 3] = V[t + 1]
        if not np.flatnonzero((p ^ V[t]) | (c ^ V[t + 1])).size:
            out.append(dict(cls='none', p=p, c=c, t=t)); continue
        for _ in range(S2): p, c = step(tab, p, c); t += 1
        t0 = t; snaps = {}; want = {0, L // 2, L, tc - t0}
        for k in range(L + 1):
            if k in want: snaps[k] = (I1.decomp(p, c, V, t, tab, pv, cache), p.copy(), c.copy(), t)
            if k < L: p, c = step(tab, p, c); t += 1
        c0 = snaps[0][0]; al = (0, L // 2, L)
        ok = all(len(snaps[k][0]) == len(c0) for k in want)
        dis = [ok and any(max(wl[1] - wl[0] + 1 for wl in snaps[k][0][ci]['walls']) > WMAX for k in al) for ci in range(len(c0))]
        sig = tuple(() if d else x for d, x in zip(dis, I1.seqsig(c0)))
        ok = ok and all(tuple(() if d else x for d, x in zip(dis, I1.seqsig(snaps[k][0]))) == sig for k in al)
        if not ok: out.append(dict(cls='open')); continue
        comps = []
        for ci, cp in enumerate(c0):
            if dis[ci]:
                sp_ = []
                for side in ('a', 'b'):
                    x0, xm, xe = (snaps[k][0][ci][side] + 0.0 for k in (0, L // 2, L))
                    v = (xe - x0) / L; fr = Fr(v).limit_denominator(QDEN)
                    sp_.append(fr if abs(v - fr) <= TOL_END and abs((xm - x0) / (L / 2) - fr) <= TOL_MID else None)
                comps.append(dict(kind='disordered', recs=(), wsp=tuple((None, None, v) for v in sp_), ci=ci)); continue
            sp_ = []
            for wi, wl in enumerate(cp['walls']):
                x0 = I1.wall_pos(wl); xm = I1.wall_pos(snaps[L // 2][0][ci]['walls'][wi]); xe = I1.wall_pos(snaps[L][0][ci]['walls'][wi])
                v = (xe - x0) / L; fr = Fr(v).limit_denominator(QDEN)
                sp_.append(fr if abs(v - fr) <= TOL_END and abs((xm - x0) / (L / 2) - fr) <= TOL_MID else None)
            recs = tuple(r for r, *_ in cp['dom']); fl_ = (((1, 'vac', 0),) + recs + ((1, 'vac', 0),))
            wsp = tuple((fl_[i], fl_[i + 1], sp_[i]) for i in range(len(sp_)))
            vs = set(sp_); kind = 'mover' if len(vs) == 1 and None not in vs and 0 not in vs else \
                'static' if vs == {Fr(0)} else 'open' if None in vs else 'growing'
            comps.append(dict(kind=kind, recs=recs, wsp=wsp, ci=ci))
        if any(None in [x[2] for x in cm['wsp']] for cm in comps): out.append(dict(cls='open')); continue
        sh = [cm for cm in comps if cm['kind'] != 'mover']
        if any(cm['kind'] == 'disordered' for cm in sh): out.append(dict(cls='dis')); continue
        wcls = 'movers' if not sh else 'followed'                                       # WALL-001's class
        cL, pL_, cL_, tL = snaps[L]
        targets, doms = {}, []
        for cm in comps:                                  # all components, movers included (the one change)
            dl = cL[cm['ci']]['dom']; ss = [0] + [x[3] for x in dl] + [0]
            for wi, x in enumerate(cm['wsp']):
                lo, hi = cL[cm['ci']]['walls'][wi]; targets[(cm['ci'], wi, x[2])] = (lo, hi, (ss[wi], ss[wi + 1]))
            doms.append([(s, pat) for _, _, _, s, pat in dl])
        out.append(dict(cls=wcls, targets=targets, doms=doms, p=pL_.copy(), c=cL_.copy(), t=tL))
    return dict(w=w, role=role, tab=tab, V=V, tw=tw, pv=pv, runs=out)


def check(R, tab, V, tw, perturb=None):
    """Build D from the build window, rebuild every future tick. Returns a result dict."""
    st, orb, qf, lostf, edge = follow_d(R['p'].copy(), R['c'].copy(), R['t'], V, tab, R['targets'], tw)
    bad = [k for k, x in st.items() if isinstance(x, str)]
    if edge: return dict(res='edge')
    if bad or lostf: return dict(res='wall_untracked', n=len(bad) + len(lostf))
    keys = sorted(R['targets'], key=lambda k: (k[0], k[1])); comps = sorted({k[0] for k in keys})
    D = [dict(walls=[st[k] for k in keys if k[0] == ci], doms=R['doms'][i]) for i, ci in enumerate(comps)]
    if perturb is not None:
        ci, wi, fld = perturb; h, clock, place, v, P = D[ci]['walls'][wi]
        # clock control: orbit phase advanced by 1 with place - v, so the wall keeps an integer path (wrong phase only)
        D[ci]['walls'][wi] = (h, (clock + 1) % P, str(Fr(place) - Fr(v)), v, P) if fld == 'clock' else \
                             (h, clock, str(Fr(place) + 1), v, P)
    t1 = tw + WT; n = WT
    rows = {}
    for ci, cm in enumerate(D):
        for di, (s, pat) in enumerate(cm['doms']):
            rr = dom_rows(tab, s, pat, t1 + n - R['t']); rows[(ci, di)] = {R['t'] + k: rr[k] for k in range(len(rr))}
    first, cls = None, Counter()
    for k in range(n):
        t = t1 + k; qh, m = rebuild(D, orb, tab, V, t, rows); diff = qh != qf[k]
        if diff.any():
            first = t if first is None else first
            cls['wall'] += int((diff & m['wall']).sum()); cls['interior'] += int((diff & m['dom'] & ~m['wall']).sum())
            cls['outside'] += int((diff & ~m['dom'] & ~m['wall']).sum())
    nw = sum(len(cm['walls']) for cm in D); cells = int(np.count_nonzero(qf[0] != 2 * V[t1] + V[t1 + 1]))
    return dict(res='exact' if first is None else 'mismatch', first=first, cls_cells=dict(cls), n_walls=nw,
                subs=sorted({x[0] for cm in D for x in cm['walls']}), P=[x[4] for cm in D for x in cm['walls']],
                doms=sorted({(s, pat) for cm in D for s, pat in cm['doms']}), cells=cells)


def job(j, mode='full'):
    G = runs(j); tab, V, tw = G['tab'], G['V'], G['tw']
    res, ctrl = [], []
    for R in G['runs']:
        if R['cls'] in ('none', 'open', 'dis'): res.append(dict(cls=R['cls'], res=R['cls'])); continue
        r = check(R, tab, V, tw); r['cls'] = R['cls']; res.append(r)
        if r['res'] == 'exact' and len(ctrl) < NCTRL:          # sensitivity: the claim must fail for a wrong D
            Pw = r['P'][0]                                     # first wall of the first component
            ctrl.append(dict(place=check(R, tab, V, tw, (0, 0, 'place'))['res'],
                             clock=check(R, tab, V, tw, (0, 0, 'clock'))['res'] if Pw > 1 else 'P=1'))
    cnt = Counter(r['res'] for r in res); cc = Counter(r['cls'] for r in res)
    desc = [r for r in res if r['cls'] in ('followed', 'movers')]
    out = dict(wolfram=G['w'], role=G['role'], n=len(res), tw=tw, run_classes=dict(cc), results=dict(cnt), ctrl=ctrl,
               n_described=len(desc), n_exact=sum(r['res'] == 'exact' for r in desc))
    mm = [r for r in desc if r['res'] == 'mismatch']
    fc = Counter()
    for r in mm: fc.update(r['cls_cells'])
    out['fail_cells'] = dict(fc)
    if mode == 'smoke':
        return dict(wolfram=G['w'], run_classes=out['run_classes'], ctrl=ctrl, edge=cnt.get('edge', 0),
                    untracked=cnt.get('wall_untracked', 0))
    ex = [r for r in desc if r['res'] == 'exact']
    out['n_walls'] = sum(r['n_walls'] for r in ex); out['n_subs'] = len({s for r in ex for s in r['subs']})
    out['n_dom_states'] = len({d for r in ex for d in r['doms']}); out['cells_mean'] = (
        sum(r['cells'] for r in ex) / len(ex) if ex else None)
    out['first_fail'] = min((r['first'] for r in mm), default=None)
    return out


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    jobs = S6.pairs()
    if sys.argv[1:2] in (['smoke'], ['calib']):
        ws = [int(x) for x in sys.argv[2:]]; sel = [j for j in jobs if j[0] in ws]
        with ProcessPoolExecutor(4) as ex:
            for r in ex.map(job, sel, ['smoke' if sys.argv[1] == 'smoke' else 'full'] * len(sel)): print(json.dumps(r, default=str))
        return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    ref = {r['wolfram']: r for r in json.load(open(OM / 'MIR-REVERSIBLE-WALL-001/results.json'))['rules']}
    order = sorted(jobs, key=lambda j: -ref[j[0]]['T'])
    with ProcessPoolExecutor(4) as ex: rows = list(ex.map(job, order))
    lab = lambda r: f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}"
    for r in rows:
        s = ref[r['wolfram']]; r['V0'] = r['n'] == s['n'] and r['run_classes'] == s['run_classes']
    el = [r for r in rows if lab(r) in ELIGIBLE]
    S = dict(V0_all=all(r['V0'] for r in rows),
             V1_tracked=all(r['results'].get('edge', 0) == 0 and r['results'].get('wall_untracked', 0) == 0 for r in el),
             V_S=all(c['place'] != 'exact' and c['clock'] != 'exact' for r in rows for c in r['ctrl']) and
             all(len(r['ctrl']) > 0 for r in el))
    S['valid'] = S['V0_all'] and S['V1_tracked'] and S['V_S']
    S['H_D_pass'] = [lab(r) for r in el if r['n_described'] > 0 and r['n_exact'] == r['n_described']]
    S['H_D'] = 'invalid' if not S['valid'] else 'supported' if len(S['H_D_pass']) == len(el) else 'not_supported'
    S['table'] = {lab(r): dict(described=r['n_described'], exact=r['n_exact'], classes=r['run_classes'],
                               results=r['results'], fail_cells=r['fail_cells'], walls=r.get('n_walls'),
                               subs=r.get('n_subs'), dom_states=r.get('n_dom_states')) for r in rows}
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V0_all', 'V1_tracked', 'V_S', 'H_D')}), 'pass:', S['H_D_pass'])


if __name__ == '__main__':
    main()
