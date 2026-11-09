"""MIR-REVERSIBLE-WALL-001: where in the static wall does the record live? Clock (internal orbit phase) vs placement.

Inputs, species, T, carrier erasure, age alignment, components, domains, walls, speeds, kinds, run classes, words and
mover keys are identical to INVENTORY-001 (inventory1.py, imported). New: from the common absolute tick
tw = T + E + SETTLE + S2 + L every wall of every settled non-mover, non-disordered component is followed for WT ticks.
Walls are tracked locally from the last aligned snapshot (where the frozen decomposition is exact): each boundary is
where the flank's known periodicity (domain period s, or the ambient vacuum) breaks, walking from an anchor ANCH cells
inside the flank. (Re-decomposing every tick fails in 22s: domains() drops a whole s = 4 stretch when a shorter-period
run overlaps it, at some tick parities.) Its local state (window: wall cells plus MW flank cells each side, and the
wall's step) forms a time orbit of minimal
period P <= PWMAX. Descriptor per wall: sub = the orbit up to rotation (canonical rotation); clock = t* mod P where t*
is the absolute tick of the canonical phase; place = space-time intercept x(t*) - v t*. Capture-tick invariant by
construction; covariance under ring translation and capture delay checked (V2). See
docs/ICP_MIR_REVERSIBLE_WALL_001_CONTRACT.md.
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
TAG = 'mir-reversible-wall-001-v0.1-frozen'
P_ = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_WALL_001_CONTRACT.md'] + [P_ + f for f in (
    'wall1.py', 'inventory1.py', 'phase1.py', 'budget1.py', 'budget0.py', 'budget0_w3.py', 'shadow7.py', 'shadow6.py',
    'shadow3.py', 'shadow.py', 'collide2.py', 'vacuum_collide.py')] + [
    'output/minimal_realization/MIR-REVERSIBLE-INVENTORY-001/results.json']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/wall1_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-WALL-001'
PREF = OM / 'MIR-REVERSIBLE-INVENTORY-001/results.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, OFFS, H, SETTLE = S7.N, S7.X0, S7.OFFS, S7.H, PH1.SETTLE
L, S2, QDEN, TOL_END, TOL_MID, WMAX = I1.L, I1.S2, I1.QDEN, I1.TOL_END, I1.TOL_MID, I1.WMAX
MW = 8              # flank cells included in a wall's window on each side
PWMAX = 96          # maximal wall orbit period
WT = 2 * PWMAX      # ticks followed from tw
EXPOSED = [91]
ANCH = 40          # anchor distance from a wall edge into its flank (cells)


def bounds(q, amb, lo, hi, fl):
    """Local wall boundaries from the previous (lo, hi): walk from an anchor inside each flank toward the wall while the
    flank's periodicity holds. fl = (sL, sR); s = 0 means the ambient vacuum (cell == amb)."""
    sL, sR = fl; aL = lo - ANCH; aR = hi + ANCH
    y = aL
    if sL: 
        while q[y] == q[y + sL]: y += 1
        nlo = y + sL
    else:
        while q[y] == amb: y += 1
        nlo = y
    y = aR
    if sR:
        while q[y] == q[y - sR]: y -= 1
        nhi = y - sR
    else:
        while q[y] == amb: y -= 1
        nhi = y
    return nlo, nhi


def follow(p, c, t, V, tab, targets, tw):
    """Track walls targets = {key: (lo, hi, (sL, sR))} from tick t (where (lo, hi) are exact) to tw + WT; record windows
    during [tw, tw + WT). Returns ({key: (sub, clock, place, v, P) | 'noclose' | 'lost'}, edge_hit)."""
    cur = {k: (lo, hi) for k, (lo, hi, _) in targets.items()}; seqs = {k: [] for k in targets}; lost = set(); edge = False
    while t < tw + WT:
        q = 2 * p.astype(np.uint8) + c; amb = 2 * V[t] + V[t + 1]
        for k, (_, _, fl) in targets.items():
            if k in lost: continue
            lo, hi = cur[k]
            if lo - ANCH - 8 < 64 or hi + ANCH + 8 > N - 64: edge = True; lost.add(k); continue
            nlo, nhi = bounds(q, amb, lo, hi, fl)
            if nhi - nlo + 1 > WMAX or nlo > nhi + 1 + I1.SMAX or abs(nlo - lo) > 2 * ANCH or abs(nhi - hi) > 2 * ANCH: lost.add(k); continue
            cur[k] = (nlo, nhi)
            if t >= tw:   # overlapping flank extents (phase-slip walls, width < 0) allowed; window over the union
                seqs[k].append((nlo, nhi - nlo, q[min(nlo, nhi + 1) - MW:max(nhi, nlo - 1) + MW + 1].tobytes()))
        p, c = step(tab, p, c); t += 1
    out = {}
    for key, s in seqs.items():
        if key in lost: out[key] = 'lost'; continue
        Pw = None
        for P in range(1, PWMAX + 1):
            d = s[P][0] - s[0][0]
            if all(s[j + P][1:] == s[j][1:] and s[j + P][0] - s[j][0] == d for j in range(WT - P)): Pw = P; break
        if Pw is None: out[key] = 'noclose'; continue
        sub, r = min((tuple((s[r + j][0] - s[r][0], s[r + j][1], s[r + j][2]) for j in range(Pw)), r) for r in range(Pw))
        d = s[Pw][0] - s[0][0]; vw = Fr(d, Pw); ts = tw + r
        out[key] = (hashlib.sha1(repr((Pw, d, sub)).encode()).hexdigest()[:12], ts % Pw, str(s[r][0] - vw * ts), str(vw), Pw)
    return out, edge


def job(j, mode='full'):
    S1.N = N
    w, _, _, _, role = j; tab, Rs, Ls = S7.lists(j)
    close = min(R['v'] - L_['v'] for R in Rs for L_ in Ls); T = math.ceil(552 / close) + 300
    V0 = C2.vac_seq(tab, 64); pv = next(k for k in range(1, 50) if (V0[k], V0[k + 1]) == (V0[0], V0[1]))
    pR = [PH1.period(tab, o['seed'], C2.vac_seq(tab, C2.PMAX + 8)) for o in Rs]
    pL = [PH1.period(tab, o['seed'], C2.vac_seq(tab, C2.PMAX + 8)) for o in Ls]
    tau = {(ri, li): math.lcm(pR[ri][0], pL[li][0], pv) for ri in range(len(Rs)) for li in range(len(Ls))}
    Delta = {k: int((Rs[k[0]]['v'] - Ls[k[1]]['v']) * t) for k, t in tau.items()}
    cl = {k: Rs[k[0]]['v'] - Ls[k[1]]['v'] for k in tau}
    E = max(math.floor((OFFS[-1] - OFFS[0]) / v) for v in cl.values())
    tw = T + E + SETTLE + S2 + L
    V = C2.vac_seq(tab, tw + WT + 2 * pv + C2.PMAX + 16)
    tc = T + E + SETTLE + S2
    cache = {}
    O, M, WORD, WS, SP = [], [], [], [], []
    seen = set(); fl = Counter(); ctrl = None
    for ri, li, off in [(ri, li, o) for ri in range(len(Rs)) for li in range(len(Ls)) for o in OFFS]:
        U = S6.place([(Rs[ri]['seed'], X0), (Ls[li]['seed'], X0 + off)]); kb = U[0].tobytes() + U[1].tobytes()
        if kb in seen: continue
        seen.add(kb)
        for _ in range(T): U = step(tab, *U)
        objs, _ = S1.objects(tab, *U, V, T)
        O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs))); SP.append((ri, li))
        e = math.floor((off - OFFS[0]) / cl[(ri, li)]); t = T
        for _ in range(e + SETTLE): U = step(tab, *U); t += 1
        objs, _ = S1.objects(tab, *U, V, t); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[t]; c[a - 2:b + 3] = V[t + 1]
        if not np.flatnonzero((p ^ V[t]) | (c ^ V[t + 1])).size:
            M.append(()); WORD.append(None); WS.append('none'); continue
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
        if not ok: M.append(('open',)); WORD.append(('open',)); WS.append('open'); continue
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
        if any(None in [x[2] for x in cm['wsp']] for cm in comps):
            M.append(('open',)); WORD.append(('open',)); WS.append('open'); continue
        ct, pc, ccc, tt = snaps[tc - t0]; mk = []
        for cm in comps:
            if cm['kind'] != 'mover': continue
            cp = ct[cm['ci']]; a, b = cp['a'], cp['b']
            mk.append((a, ((pc[a:b + 1] ^ V[tt]).tobytes(), (ccc[a:b + 1] ^ V[tt + 1]).tobytes())))
        M.append(tuple(mk))
        sh = [cm for cm in comps if cm['kind'] != 'mover']
        WORD.append(tuple((cm['kind'], cm['recs'], tuple(x[2] for x in cm['wsp'])) for cm in sh))
        if any(cm['kind'] == 'disordered' for cm in sh) or not sh:
            WS.append('dis' if sh else 'movers'); continue
        # track every wall of every shadow component from the last aligned snapshot (exact walls) to tw + WT
        cL, pL_, cL_, tL = snaps[L]
        targets = {}
        for cm in sh:
            dl = cL[cm['ci']]['dom']; ss = [0] + [x[3] for x in dl] + [0]
            for wi, x in enumerate(cm['wsp']):
                lo, hi = cL[cm['ci']]['walls'][wi]; targets[(cm['ci'], wi, x[2])] = (lo, hi, (ss[wi], ss[wi + 1]))
        st, eh = follow(pL_.copy(), cL_.copy(), tL, V, tab, targets, tw)
        fl['edge_hits'] += eh; fl['lost'] += sum(x == 'lost' for x in st.values())
        fl['noclose'] += sum(x == 'noclose' for x in st.values())
        fl['speed_mismatch'] += sum(not isinstance(x, str) and Fr(x[3]) != k[2] for k, x in st.items())
        WS.append(tuple((ci, wi, str(v), st[(ci, wi, v)]) for (ci, wi, v) in targets))
        if ctrl is None and all(not isinstance(x, str) for x in st.values()):   # V2 covariance controls
            sh1 = {k: (lo + 1, hi + 1, f_) for k, (lo, hi, f_) in targets.items()}
            s1, _ = follow(np.roll(pL_, 1), np.roll(cL_, 1), tL, V, tab, sh1, tw)
            s2, _ = follow(pL_.copy(), cL_.copy(), tL, V, tab, targets, tw + 1)
            okT = all(not isinstance(s1[k], str) and s1[k][:2] == st[k][:2] and Fr(s1[k][2]) == Fr(st[k][2]) + 1 for k in targets)
            okD = all(s2[k] == st[k] for k in targets)
            # agreement with the frozen decomposition at the aligned snapshot L + 1 tick is not required; at L it is exact
            ctrl = dict(translate=okT, delay=okD)
    n = len(O)
    flags = dict(wolfram=w, role=role, n=n, ctrl=ctrl, **{k: fl[k] for k in ('lost', 'edge_hits', 'noclose', 'speed_mismatch')})
    if mode == 'smoke': return flags
    lg = math.log2(n); OMk = list(zip(O, M))
    r_ = lambda *ks: lg - H(list(zip(O, M, *ks)))      # H(in | O, M, keys); inputs uniform and distinct
    static = lambda ws, f: (ws if isinstance(ws, str) else tuple(f(x[3]) for x in ws if x[2] == '0'))
    outer = lambda ws, f: (ws if isinstance(ws, str) else tuple(f(x[3]) for x in ws if x[2] != '0'))
    side = lambda ws, i: (ws if isinstance(ws, str) else ws[i][3])
    Wst = [static(ws, lambda s: s) for ws in WS]
    out = dict(flags, T=T, E=E, pv=pv, tw=tw)
    out['rec'] = lg - H(OMk)
    out['r_W'] = r_(Wst)                                               # one stationary wall, full state
    out['r_clock'] = r_([static(ws, lambda s: s if isinstance(s, str) else s[:2]) for ws in WS])   # sub + clock
    out['r_place'] = r_([static(ws, lambda s: s if isinstance(s, str) else s[2]) for ws in WS])   # placement only
    out['r_subplace'] = r_([static(ws, lambda s: s if isinstance(s, str) else (s[0], s[2])) for ws in WS])
    out['r_sub'] = r_([static(ws, lambda s: s if isinstance(s, str) else s[0]) for ws in WS])
    out['clock_beyond_place'] = out['r_subplace'] - out['r_W']          # I(in; clock | O, M, sub, place)
    out['r_outer'] = r_([outer(ws, lambda s: s) for ws in WS])
    out['r_allwalls'] = r_([ws for ws in WS])
    out['r_left_edge'] = r_([side(ws, 0) for ws in WS]); out['r_right_edge'] = r_([side(ws, -1) for ws in WS])
    fol = [ws for ws in WS if ws not in ('none', 'movers')]
    out['shadow_runs'] = len(fol); out['run_classes'] = dict(Counter(ws if isinstance(ws, str) else 'followed' for ws in WS))
    out['lost_or_open_walls'] = fl['lost'] + fl['noclose']
    out['one_static_all'] = bool(fol) and all(not isinstance(ws, str) and sum(x[2] == '0' for x in ws) == 1 for ws in fol)
    stp = [x[3] for ws in WS if not isinstance(ws, str) for x in ws if x[2] == '0' and not isinstance(x[3], str)]
    out['static_periods'] = sorted(Counter(s[4] for s in stp).items())
    out['n_static_sub'] = len({s[0] for s in stp}); out['n_static_clock'] = len({s[:2] for s in stp})
    out['n_static_place'] = len({s[2] for s in stp}); out['n_static_state'] = len(set(stp))
    out['word_counts'] = sorted(Counter(str(x) for x in WORD if x not in (None, ('open',), ())).items(), key=lambda t: -t[1])
    return out


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    jobs = S6.pairs()
    if sys.argv[1:2] in (['smoke'], ['calib']):
        ws = [int(x) for x in sys.argv[2:]] or [j[0] for j in jobs]; sel = [j for j in jobs if j[0] in ws]
        with ProcessPoolExecutor(4) as ex:
            for r in ex.map(job, sel, ['smoke' if sys.argv[1] == 'smoke' else 'full'] * len(sel)): print(json.dumps(r, default=str))
        return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    ref = {r['wolfram']: r for r in json.load(open(PREF))['rules']}
    order = sorted(jobs, key=lambda j: -ref[j[0]]['T'])
    with ProcessPoolExecutor(4) as ex: rows = list(ex.map(job, order))
    lab = lambda r: f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}"
    for r in rows:
        s = ref[r['wolfram']]
        r['V0'] = r['n'] == s['n'] and abs(r['rec'] - s['rec']) < 1e-12 and dict(r['word_counts']) == dict(s['words'])
        r['V4'] = r['r_W'] >= -1e-9 and r['r_W'] <= r['r_subplace'] + 1e-9 and r['r_W'] <= r['r_clock'] + 1e-9 and r['r_allwalls'] <= r['r_W'] + 1e-9
    sh = [r for r in rows if r['role'].startswith('shadow')]; nl = [r for r in rows if r['role'].startswith('null')]
    un = [r for r in sh if r['wolfram'] not in EXPOSED]
    el = [r for r in un if r['rec'] > 1e-9 and r['one_static_all']]
    S = dict(V0_all=all(r['V0'] for r in rows),
             V1_closed=all(r['noclose'] == 0 and r['lost'] == 0 and r['speed_mismatch'] == 0 for r in rows if r in el),
             V2_covariance=all(r['ctrl'] is None or (r['ctrl']['translate'] and r['ctrl']['delay']) for r in rows) and
             all(r['ctrl'] is not None for r in el),
             V3_edges=all(r['edge_hits'] == 0 for r in rows), V4_order=all(r['V4'] for r in rows),
             V5_nulls=all(r['ctrl'] is None for r in nl),
             eligible=[lab(r) for r in el],
             H_1_pass=[lab(r) for r in el if r['r_W'] < 1e-9],
             H_T_pass=[lab(r) for r in el if r['clock_beyond_place'] > 1e-9],
             H_I_pass=[lab(r) for r in el if r['r_clock'] < 1e-9])
    S['valid'] = all(S[k] for k in ('V0_all', 'V1_closed', 'V2_covariance', 'V3_edges', 'V4_order', 'V5_nulls'))
    need = math.ceil(len(el) / 2)
    v = lambda ok: 'invalid' if not S['valid'] else 'supported' if ok else 'not_supported'
    for h in ('H_1', 'H_T', 'H_I'): S[h] = v(len(el) > 0 and len(S[h + '_pass']) >= need)
    keys = ('rec', 'r_W', 'r_clock', 'r_place', 'r_subplace', 'r_sub', 'clock_beyond_place', 'r_outer', 'r_allwalls',
            'r_left_edge', 'r_right_edge')
    S['table'] = {lab(r): dict({k: round(r[k], 3) for k in keys}, one_static=r['one_static_all'],
                  n_sub=r['n_static_sub'], n_clock=r['n_static_clock'], n_place=r['n_static_place'], n_state=r['n_static_state'])
                  for r in rows}
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V0_all', 'V1_closed', 'V2_covariance', 'V3_edges', 'V4_order', 'V5_nulls', 'H_1', 'H_T', 'H_I')}))


if __name__ == '__main__':
    main()
