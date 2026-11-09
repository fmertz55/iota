"""MIR-REVERSIBLE-WALL-002: what do the walls' bits name: which species collided, the contact phase, or the age?

Inputs, carriers, erasure, tracking and wall descriptors are WALL-001's (wall1.py, imported; runs() below is a verbatim
copy of wall1.job up to the per-run lists, plus the offset). Each input is relabelled by its collision channels:
species pair sp, contact phase phi = off mod Delta_sp, translate index k = (off - off0(sp, phi)) / Delta_sp (offsets in
one contact class (sp, phi) give exact space-time translates; contact later by k*tau, placed v_R*k*tau to the right).
Exact conditional-entropy ledger of the record H(in | O, M) and of the edge-only part I(in; walls | O, M, static wall)
split into these channels. Lemma control V_L: within each class every tracked wall obeys the translate law
sub_k = sub_0, clock_k = clock_0 + k*tau (mod P), place_k = place_0 + k*tau*(v_R - u). See
docs/ICP_MIR_REVERSIBLE_WALL_002_CONTRACT.md.
"""
import hashlib, json, math, os, subprocess, sys
os.environ.setdefault('OMP_NUM_THREADS', '1')
from collections import Counter, defaultdict
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
import minimal_realization_reversible.wall1 as W1
TAG = 'mir-reversible-wall-002-v0.1-frozen'
P_ = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_WALL_002_CONTRACT.md'] + [P_ + f for f in (
    'wall2.py', 'wall1.py', 'inventory1.py', 'phase1.py', 'budget1.py', 'budget0.py', 'budget0_w3.py', 'shadow7.py',
    'shadow6.py', 'shadow3.py', 'shadow.py', 'collide2.py', 'vacuum_collide.py')] + [
    'output/minimal_realization/MIR-REVERSIBLE-WALL-001/results.json']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/wall2_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-WALL-002'
WREF = OM / 'MIR-REVERSIBLE-WALL-001/results.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, OFFS, H, SETTLE = W1.N, W1.X0, W1.OFFS, W1.H, W1.SETTLE
L, S2, QDEN, TOL_END, TOL_MID, WMAX, WT = W1.L, W1.S2, W1.QDEN, W1.TOL_END, W1.TOL_MID, W1.WMAX, W1.WT
EXPOSED = [91]
ELIG = ['147', '201', '22s', '26s', '58s', '82s', '114s']   # WALL-001 eligible set (recomputed and checked, V1)
TOL = 1e-9


def runs(j):
    """Verbatim copy of wall1.job up to the per-run lists (plus OFF); returns the lists instead of readouts."""
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
    O, M, WORD, WS, SP, OFF = [], [], [], [], [], []
    seen = set(); fl = Counter(); ctrl = None
    for ri, li, off in [(ri, li, o) for ri in range(len(Rs)) for li in range(len(Ls)) for o in OFFS]:
        U = S6.place([(Rs[ri]['seed'], X0), (Ls[li]['seed'], X0 + off)]); kb = U[0].tobytes() + U[1].tobytes()
        if kb in seen: continue
        seen.add(kb)
        for _ in range(T): U = step(tab, *U)
        objs, _ = S1.objects(tab, *U, V, T)
        O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs))); SP.append((ri, li)); OFF.append(off)
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
            if k in want: snaps[k] = (W1.I1.decomp(p, c, V, t, tab, pv, cache), p.copy(), c.copy(), t)
            if k < L: p, c = step(tab, p, c); t += 1
        c0 = snaps[0][0]; al = (0, L // 2, L)
        ok = all(len(snaps[k][0]) == len(c0) for k in want)
        dis = [ok and any(max(wl[1] - wl[0] + 1 for wl in snaps[k][0][ci]['walls']) > WMAX for k in al) for ci in range(len(c0))]
        sig = tuple(() if d else x for d, x in zip(dis, W1.I1.seqsig(c0)))
        ok = ok and all(tuple(() if d else x for d, x in zip(dis, W1.I1.seqsig(snaps[k][0]))) == sig for k in al)
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
                x0 = W1.I1.wall_pos(wl); xm = W1.I1.wall_pos(snaps[L // 2][0][ci]['walls'][wi]); xe = W1.I1.wall_pos(snaps[L][0][ci]['walls'][wi])
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
        st, eh = W1.follow(pL_.copy(), cL_.copy(), tL, V, tab, targets, tw)
        fl['edge_hits'] += eh; fl['lost'] += sum(x == 'lost' for x in st.values())
        fl['noclose'] += sum(x == 'noclose' for x in st.values())
        fl['speed_mismatch'] += sum(not isinstance(x, str) and Fr(x[3]) != k[2] for k, x in st.items())
        WS.append(tuple((ci, wi, str(v), st[(ci, wi, v)]) for (ci, wi, v) in targets))
        if ctrl is None and all(not isinstance(x, str) for x in st.values()):   # V2 covariance controls
            sh1 = {k: (lo + 1, hi + 1, f_) for k, (lo, hi, f_) in targets.items()}
            s1, _ = W1.follow(np.roll(pL_, 1), np.roll(cL_, 1), tL, V, tab, sh1, tw)
            s2, _ = W1.follow(pL_.copy(), cL_.copy(), tL, V, tab, targets, tw + 1)
            okT = all(not isinstance(s1[k], str) and s1[k][:2] == st[k][:2] and Fr(s1[k][2]) == Fr(st[k][2]) + 1 for k in targets)
            okD = all(s2[k] == st[k] for k in targets)
            # agreement with the frozen decomposition at the aligned snapshot L + 1 tick is not required; at L it is exact
            ctrl = dict(translate=okT, delay=okD)
    return dict(w=w, role=role, O=O, M=M, WS=WS, SP=SP, OFF=OFF, tau=tau, Delta=Delta,
                vR={ri: Rs[ri]['v'] for ri in range(len(Rs))}, flags=dict(lost=fl['lost'], noclose=fl['noclose'],
                speed_mismatch=fl['speed_mismatch'], edge_hits=fl['edge_hits']), ctrl=ctrl)


def lemma(R):
    """V_L: translate law inside every contact class. Returns (n_checked_runs, n_fail)."""
    by = defaultdict(list)
    for i, (sp, off) in enumerate(zip(R['SP'], R['OFF'])):
        D = R['Delta'][sp]; by[(sp, off % D)].append((off, R['WS'][i]))
    chk = bad = 0
    for (sp, ph), rs in by.items():
        rs.sort(); tau = R['tau'][sp]; vR = R['vR'][sp[0]]; D = R['Delta'][sp]; off0, w0 = rs[0]
        for off, ws in rs[1:]:
            chk += 1; dk = (off - off0) // D; dt = dk * tau
            if isinstance(w0, str) or isinstance(ws, str):
                bad += ws != w0; continue
            if [x[:3] for x in ws] != [x[:3] for x in w0]: bad += 1; continue
            ok = True
            for x, y in zip(w0, ws):
                if isinstance(x[3], str) or isinstance(y[3], str): ok &= x[3] == y[3]; continue
                s0, c0, p0, u, P = x[3]; s1, c1, p1, u1, P1 = y[3]; u = Fr(u)
                ok &= s1 == s0 and P1 == P and u1 == x[3][3] and c1 == (c0 + dt) % P and Fr(p1) == Fr(p0) + dt * (vR - u)
            bad += not ok
    return chk, bad


def ledger(R):
    O, M, WS, SP, OFF = R['O'], R['M'], R['WS'], R['SP'], R['OFF']; n = len(O); lg = math.log2(n)
    PHI = [off % R['Delta'][sp] for sp, off in zip(SP, OFF)]
    K = []
    for sp, off, ph in zip(SP, OFF, PHI):
        D = R['Delta'][sp]; off0 = OFFS[0] + (ph - OFFS[0]) % D; K.append((off - off0) // D)
    st = lambda ws, f: ws if isinstance(ws, str) else tuple(f(x[3]) for x in ws if x[2] == '0')
    W = [st(ws, lambda s: s) for ws in WS]; PL = [st(ws, lambda s: s if isinstance(s, str) else s[2]) for ws in WS]
    A = list(WS); CL = list(zip(SP, PHI))
    Hj = lambda *cs: H(list(zip(*cs)))
    Hc = lambda X, *Y: Hj(X, *Y) - Hj(*Y)                       # H(X | Y)
    Ic = lambda X, Z, *Y: Hc(X, *Y) - Hc(X, Z, *Y)              # I(X; Z | Y)
    r = dict(n=n, rec=lg - Hj(O, M), r_W=lg - Hj(O, M, W), r_place=lg - Hj(O, M, PL), r_allwalls=lg - Hj(O, M, A))
    # channels of the record
    r['c_sp'] = Hc(SP, O, M); r['c_off'] = Hc(OFF, O, M, SP); r['c_phi'] = Hc(PHI, O, M, SP); r['c_k'] = Hc(K, O, M, CL)
    r['c_off_first'] = Hc(OFF, O, M); r['c_sp_given_off'] = Hc(SP, O, M, OFF)
    # what the static wall's placement names
    r['pl'] = r['rec'] - r['r_place']
    r['pl_off'] = Ic(OFF, PL, O, M); r['pl_sp_given_off'] = Ic(SP, PL, O, M, OFF)
    r['pl_sp'] = Ic(SP, PL, O, M); r['pl_off_given_sp'] = Ic(OFF, PL, O, M, SP)
    # what only the walls beyond the static wall hold
    r['R_E'] = r['r_W'] - r['r_allwalls']
    r['J_sp'] = Ic(SP, A, O, M, W); r['J_phi'] = Ic(PHI, A, O, M, W, SP); r['J_k'] = Ic(K, A, O, M, W, CL)
    r['Q_off'] = Ic(OFF, A, O, M, W, SP); r['Q_sp'] = Ic(SP, A, O, M, W, OFF); r['E_off_first'] = Ic(OFF, A, O, M, W)
    # age held by the static wall inside a class (lemma: place pins k when v_R*tau != 0)
    r['W_age'] = Ic(K, W, O, M, CL)
    r['id_err'] = max(abs(r['c_sp'] + r['c_off'] - r['rec']), abs(r['c_phi'] + r['c_k'] - r['c_off']),
                      abs(r['c_off_first'] + r['c_sp_given_off'] - r['rec']),
                      abs(r['pl_off'] + r['pl_sp_given_off'] - r['pl']), abs(r['pl_sp'] + r['pl_off_given_sp'] - r['pl']),
                      abs(r['J_sp'] + r['J_phi'] + r['J_k'] - r['R_E']), abs(r['J_phi'] + r['J_k'] - r['Q_off']),
                      abs(r['E_off_first'] + r['Q_sp'] - r['R_E']))
    return r


def job(j, mode='full'):
    R = runs(j); chk, bad = lemma(R); out = dict(wolfram=R['w'], role=R['role'], L_checked=chk, L_fail=bad, ctrl=R['ctrl'],
                                                 **R['flags'])
    lr = ledger(R); out['V0_keys'] = {k: lr[k] for k in ('n', 'rec', 'r_W', 'r_place', 'r_allwalls')}
    if mode == 'smoke': out.pop('V0_keys'); out['id_err_ok'] = lr['id_err'] < TOL; return out
    out.update(lr); return out


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
    ref = {r['wolfram']: r for r in json.load(open(WREF))['rules']}
    order = sorted(jobs, key=lambda j: -ref[j[0]]['T'])
    with ProcessPoolExecutor(4) as ex: rows = list(ex.map(job, order))
    lab = lambda r: f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}"
    for r in rows:
        s = ref[r['wolfram']]
        r['V0'] = r['n'] == s['n'] and all(abs(r[k] - s[k]) < 1e-12 for k in ('rec', 'r_W', 'r_place', 'r_allwalls'))
    el = [r for r in rows if lab(r) in ELIG]
    ws1 = json.load(open(WREF))['summary']['eligible']
    S = dict(V0_all=all(r['V0'] for r in rows), V1_eligible=sorted(ws1) == sorted(ELIG) and len(el) == len(ELIG),
             V_L=all(r['L_fail'] == 0 for r in el), V_L_checked=sum(r['L_checked'] for r in el),
             V_id=all(r['id_err'] < TOL for r in rows), V_track=all(r['lost'] == 0 and r['noclose'] == 0 and
             r['speed_mismatch'] == 0 and r['edge_hits'] == 0 for r in el))
    S['valid'] = all(S[k] for k in ('V0_all', 'V1_eligible', 'V_L', 'V_id', 'V_track'))
    v = lambda ok: 'invalid' if not S['valid'] else 'supported' if ok else 'not_supported'
    S['H_C0_pass'] = [lab(r) for r in el if r['c_off'] < TOL]
    S['H_C0'] = v(len(S['H_C0_pass']) >= math.ceil(len(el) / 2))
    te = [r for r in el if lab(r) in ('58s', '114s')]
    S['H_S_pass'] = [lab(r) for r in te if r['Q_off'] < TOL]; S['H_S'] = v(len(S['H_S_pass']) == len(te))
    S['P_age0_pass'] = [lab(r) for r in el if r['J_k'] < TOL]                 # lemma prediction (all 7)
    S['P_gate_pass'] = [lab(r) for r in el if lab(r) in ('26s', '82s') and r['Q_off'] < TOL]   # predicted: both
    keys = ('rec', 'c_sp', 'c_off', 'c_phi', 'c_k', 'c_off_first', 'c_sp_given_off', 'pl', 'pl_off', 'pl_sp_given_off',
            'pl_sp', 'pl_off_given_sp', 'R_E', 'J_sp', 'J_phi', 'J_k', 'Q_off', 'Q_sp', 'E_off_first', 'W_age')
    S['table'] = {lab(r): {k: round(r[k], 3) for k in keys} for r in el}
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V0_all', 'V1_eligible', 'V_L', 'V_L_checked', 'V_id', 'V_track',
                                        'H_C0', 'H_S', 'P_age0_pass', 'P_gate_pass')}))


if __name__ == '__main__':
    main()
