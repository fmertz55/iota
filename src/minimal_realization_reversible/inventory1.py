"""MIR-REVERSIBLE-INVENTORY-001: wall/domain species inventory of the shadows; rigid movers separated as carriers.

Inputs, species, T, carrier erasure and age alignment are identical to PHASE-001 (phase1.py). Each aligned residue is
split into components at ambient-vacuum gaps >= GAP cells. Each component is cut into domains (maximal s-periodic
stretches, s <= SMAX, >= MINRUN cells; species = space-time orbit-canonical pattern, plus vacuum phase lag for vacuum
domains) and walls (the gaps between domains and between the component and the ambient vacuum; species = (left domain,
right domain, speed)). Rigid mover = component whose walls all have one speed v != 0 (an unrecognised carrier).
See docs/ICP_MIR_REVERSIBLE_INVENTORY_001_CONTRACT.md.
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
import minimal_realization_reversible.budget1 as B1
TAG = 'mir-reversible-inventory-001-v0.1-frozen'
P = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_INVENTORY_001_CONTRACT.md'] + [P + f for f in (
    'inventory1.py', 'phase1.py', 'budget1.py', 'budget0.py', 'budget0_w3.py', 'shadow7.py', 'shadow6.py', 'shadow3.py',
    'shadow.py', 'collide2.py', 'vacuum_collide.py')] + [
    'output/minimal_realization/MIR-REVERSIBLE-PHASE-001/results.json',
    'output/minimal_realization/MIR-REVERSIBLE-BUDGET-000/results.json']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/inventory1_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-INVENTORY-001'
PREF = OM / 'MIR-REVERSIBLE-PHASE-001/results.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, OFFS, H, SETTLE = S7.N, S7.X0, S7.OFFS, S7.H, PH1.SETTLE
GAP, MINRUN, SMAX = 16, 16, 8          # vacuum gap that separates components; domain min length; max spatial period
L = 4096                               # speed window (ticks)
QDEN = 12                              # speeds are rationals with denominator <= QDEN
TOL_END, TOL_MID = 12 / L, 24 / L      # speed resolution tolerances (full window, half-window consistency)
KB = 120                               # ticks sampled for wall-budget time averages
WMAX = 64                              # a wall wider than this marks a disordered component
S2 = 1024                              # extra settling ticks after the aligned erasure, before the window
OCAP = 20000                           # orbit cap for domain canonicalisation
EXPOSED = [91]
NULLS = ('null',)


def canon(s, pat, tab, cache):
    """Space-time orbit-canonical form of an s-periodic two-layer pattern (q = 2p + c). None if orbit not closed."""
    k = (s, pat)
    if k in cache: return cache[k]
    m = s * math.ceil(12 / s); q0 = np.array(pat * (m // s), np.uint8); p, c = q0 >> 1, q0 & 1
    best = None
    for _ in range(OCAP):
        q = 2 * p + c; row = tuple(int(x) for x in q[:2 * s])
        cand = min(row[r:r + s] for r in range(s)); best = cand if best is None or cand < best else best
        p, c = step(tab, p, c)
        if np.array_equal(2 * p + c, q0): break
    else:
        best = None
    cache[k] = best; return best


def domains(q, a, b):
    """Maximal s-periodic stretches inside [a, b] (smallest s first, no overlap), sorted by start: (start, end, s)."""
    used = np.zeros(b - a + 1, bool); out = []
    for s in range(1, SMAX + 1):
        if b - a + 1 < MINRUN: break
        eq = np.concatenate(([False], q[a:b - s + 1] == q[a + s:b + 1], [False])).astype(np.int8)
        dd = np.diff(eq); st = np.flatnonzero(dd == 1); en = np.flatnonzero(dd == -1)
        for i, j in zip(st, en):
            x, y = int(i), int(j) - 1 + s
            if y - x + 1 >= MINRUN and not used[x:y + 1].any():
                used[x:y + 1] = True; out.append((a + x, a + y, s))
    return sorted(out)


def decomp(p, c, V, t, tab, pv, cache):
    """Components of the residue at tick t. Each: dict(a, b, dom=[(rec, start, end, s, pat)], walls=[(lo, hi)])."""
    d = (p ^ V[t]) | (c ^ V[t + 1]); on = np.flatnonzero(d)
    if not on.size: return []
    br = np.flatnonzero(np.diff(on) > GAP); starts = [on[0]] + list(on[br + 1]); ends = list(on[br]) + [on[-1]]
    q = 2 * p.astype(np.uint8) + c; comps = []
    for a, b in zip(starts, ends):
        a, b = int(a), int(b); dl = []
        for x, y, s in domains(q, a, b):
            m0 = x + ((-x) % s); pat = tuple(int(v) for v in q[m0:m0 + s]); cn = canon(s, pat, tab, cache)
            lag = None
            if s == 1:
                lag = next((k for k in range(pv) if 2 * V[t + k] + V[t + k + 1] == pat[0]), None)
            dl.append(((1, 'vac', lag) if lag is not None else (s, cn, None), x, y, s, pat))
        edges = [a] + [e for _, x, y, _, _ in dl for e in (x, y)] + [b]
        walls = [(edges[2 * i] if i == 0 else edges[2 * i] + 1, edges[2 * i + 1] if i == len(dl) else edges[2 * i + 1] - 1)
                 for i in range(len(dl) + 1)]
        comps.append(dict(a=a, b=b, dom=dl, walls=walls))
    return comps


def wall_pos(w): return (w[0] + w[1]) / 2


def budgets(w, p, c, comps):
    """Window-2 budget per wall (exact; None where a flank domain has nonzero budget per period)."""
    if 'window2_coeffs' not in B1.R2[str(w)]: return [[None] * len(cp['walls']) for cp in comps]
    dd = B1.dens2(w, p, c); cs = np.cumsum(dd, axis=1); nk = len(dd); out = []
    for cp in comps:
        cuts = [tuple(Fr(0) for _ in range(nk))]
        for _, x, y, s, _ in cp['dom']:
            mid = (x + y) // 2 - s // 2
            rho = [int(cs[k][mid + s - 1] - cs[k][mid - 1]) for k in range(nk)]
            cuts.append(None if any(rho) else tuple(Fr(int(sum(cs[k][m - 1] for m in range(mid, mid + s))), s) for k in range(nk)))
        e = min(cp['b'] + 8, N - 1); cuts.append(tuple(Fr(int(cs[k][e])) for k in range(nk)))
        out.append([None if u is None or v is None else tuple(str(y - x) for x, y in zip(u, v)) for u, v in zip(cuts, cuts[1:])])
    return out


def bavg(bseq, sig):
    """Exact time average of each wall budget over its minimal period within the first KB ticks ('aperiodic' if none
    <= KB // 2; None where undefined at some tick)."""
    if any(sg != sig for sg, _ in bseq): return [['aperiodic'] * (len(x) + 1) for x in sig]
    out = []
    for ci in range(len(sig)):
        row = []
        for wi in range(len(sig[ci]) + 1):
            seq = [b[ci][wi] for _, b in bseq]
            if any(x is None for x in seq): row.append(None); continue
            P = next((P for P in range(1, KB // 2 + 1) if all(seq[k] == seq[k + P] for k in range(KB - P))), None)
            row.append('aperiodic' if P is None else tuple(str(sum(Fr(x[i]) for x in seq[:P]) / P) for i in range(len(seq[0]))))
        out.append(row)
    return out


def seqsig(comps): return tuple(tuple(r for r, *_ in cp['dom']) for cp in comps)


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
    V = C2.vac_seq(tab, T + E + SETTLE + S2 + L + 2 * pv + C2.PMAX + 8)
    tc = T + E + SETTLE + S2                               # common absolute tick for exact mover keys
    assert E <= L
    cache = {}
    O, SP, PHs, RES, M, WORD, SHW = [], [], [], [], [], [], []
    runs = []; seen = set(); edge = unsettled = unresolved = opencap = bud_aper = ndis = 0; v1 = defaultdict(set)
    for ri, li, off in [(ri, li, o) for ri in range(len(Rs)) for li in range(len(Ls)) for o in OFFS]:
        U = S6.place([(Rs[ri]['seed'], X0), (Ls[li]['seed'], X0 + off)]); kb = U[0].tobytes() + U[1].tobytes()
        if kb in seen: continue
        seen.add(kb)
        for _ in range(T): U = step(tab, *U)
        objs, _ = S1.objects(tab, *U, V, T)
        O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs)))
        SP.append((ri, li)); PHs.append(off % Delta[(ri, li)])
        e = math.floor((off - OFFS[0]) / cl[(ri, li)]); t = T
        for _ in range(e + SETTLE): U = step(tab, *U); t += 1
        objs, _ = S1.objects(tab, *U, V, t); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[t]; c[a - 2:b + 3] = V[t + 1]
        has = bool(np.flatnonzero((p ^ V[t]) | (c ^ V[t + 1])).size); RES.append(has)
        if not has:
            M.append(()); WORD.append(None); SHW.append(False); v1[(SP[-1], PHs[-1])].add(('none',)); continue
        for _ in range(S2): p, c = step(tab, p, c); t += 1
        t0 = t
        snaps = {}; want = {0, L // 2, L, tc - t0}; bseq = []; inv = 'window2_coeffs' in B1.R2[str(w)]
        for k in range(L + 1):
            if inv and k < KB:
                cps = decomp(p, c, V, t, tab, pv, cache); bseq.append((seqsig(cps), budgets(w, p, c, cps)))
            if k in want:
                cps = decomp(p, c, V, t, tab, pv, cache); snaps[k] = (cps, p.copy(), c.copy(), t)
                edge += any(cp['a'] < 64 or cp['b'] > N - 64 for cp in cps)
            if k < L: p, c = step(tab, p, c); t += 1
        c0, p0, cc0, _ = snaps[0]
        al = (0, L // 2, L)                     # age-aligned snapshots: classification uses only these
        ok = all(len(snaps[k][0]) == len(c0) for k in want)
        dis = [ok and any(max(wl[1] - wl[0] + 1 for wl in snaps[k][0][ci]['walls']) > WMAX for k in al) for ci in range(len(c0))]
        sig = tuple(() if d else x for d, x in zip(dis, seqsig(c0)))
        ok = ok and all(tuple(() if d else x for d, x in zip(dis, seqsig(snaps[k][0]))) == sig for k in al)
        opencap += sum(r[1] is None for cp in c0 for r, *_ in cp['dom'])
        if not ok:
            unsettled += 1; M.append(('open',)); WORD.append(('open',)); SHW.append(True)
            v1[(SP[-1], PHs[-1])].add(('open',)); continue
        b0 = bavg(bseq, seqsig(c0)) if inv and not any(dis) else [[None] * len(cp['walls']) for cp in c0]
        bud_aper += sum(x == 'aperiodic' for u in b0 for x in u); b0 = [[None if x == 'aperiodic' else x for x in u] for u in b0]
        comps = []
        for ci, cp in enumerate(c0):
            sp_ = []
            if dis[ci]:   # disordered: only the two edge speeds
                eg = lambda k, side: snaps[k][0][ci][side] + 0.0
                for side in ('a', 'b'):
                    x0, xm, xe = eg(0, side), eg(L // 2, side), eg(L, side)
                    v = (xe - x0) / L; fr = Fr(v).limit_denominator(QDEN)
                    good = abs(v - fr) <= TOL_END and abs((xm - x0) / (L / 2) - fr) <= TOL_MID
                    unresolved += not good; sp_.append(fr if good else None)
                comps.append(dict(kind='disordered', recs=(), wsp=tuple((None, None, v) for v in sp_), bud=[None, None], ci=ci))
                continue
            for wi, wl in enumerate(cp['walls']):
                x0 = wall_pos(wl); xm = wall_pos(snaps[L // 2][0][ci]['walls'][wi]); xe = wall_pos(snaps[L][0][ci]['walls'][wi])
                v = (xe - x0) / L; fr = Fr(v).limit_denominator(QDEN)
                good = abs(v - fr) <= TOL_END and abs((xm - x0) / (L / 2) - fr) <= TOL_MID
                unresolved += not good; sp_.append(fr if good else None)
            recs = tuple(r for r, *_ in cp['dom']); fl = (((1, 'vac', 0),) + recs + ((1, 'vac', 0),))
            wsp = tuple((fl[i], fl[i + 1], sp_[i]) for i in range(len(sp_)))
            vs = set(sp_); kind = 'mover' if len(vs) == 1 and None not in vs and 0 not in vs else \
                'static' if vs == {Fr(0)} else 'open' if None in vs else 'growing'
            comps.append(dict(kind=kind, recs=recs, wsp=wsp, bud=b0[ci], ci=ci))
        if any(None in [x[2] for x in cm['wsp']] for cm in comps):   # an unresolved speed makes the run open
            unsettled += 1; M.append(('open',)); WORD.append(('open',)); SHW.append(True)
            v1[(SP[-1], PHs[-1])].add(('open',)); continue
        # exact mover keys at the common tick tc (component order is preserved in a settled run)
        ct, pc, ccc, tt = snaps[tc - t0]; mk = []
        for cm in comps:
            if cm['kind'] != 'mover': continue
            cp = ct[cm['ci']]; a, b = cp['a'], cp['b']
            mk.append((a, ((pc[a:b + 1] ^ V[tt]).tobytes(), (ccc[a:b + 1] ^ V[tt + 1]).tobytes())))
        M.append(tuple(mk))
        sh = [cm for cm in comps if cm['kind'] != 'mover']
        word = tuple((cm['kind'], cm['recs'], tuple(x[2] for x in cm['wsp'])) for cm in sh); WORD.append(word); SHW.append(bool(sh))
        mw = tuple(sorted((cm['recs'], cm['wsp'][0][2]) for cm in comps if cm['kind'] == 'mover'))
        v1[(SP[-1], PHs[-1])].add((word, mw))
        runs.append(dict(sp=SP[-1], ph=PHs[-1], comps=comps)); ndis += any(dis)
    n = len(O)
    flags = dict(wolfram=w, role=role, n=n, residue_runs_aligned=sum(RES), unsettled=unsettled, unresolved=unresolved,
                 opencap=opencap, edge_hits=edge, V1_fail=sum(len(x) > 1 for x in v1.values()), bud_aper=bud_aper, disordered_runs=ndis)
    if mode == 'smoke': return flags
    kinds = Counter(cm['kind'] for r in runs for cm in r['comps'])
    if mode == 'calib':
        flags['kinds'] = dict(kinds); flags['inventory'] = sorted(Counter(str((cm['kind'], cm['recs'], cm['wsp'])) for r in runs for cm in r['comps']).items())
        return flags
    out = dict(flags, T=T, E=E, pv=pv, kinds=dict(kinds), Delta={f'{a}{b}': d for (a, b), d in Delta.items()})
    HO = H(O); OM_ = list(zip(O, M)); HOM = H(OM_)
    out['only_phase'] = math.log2(n) - HO                       # = PHASE-001 'only' (aligned convention is the same O)
    out['rec'] = math.log2(n) - HOM                             # H(in | O, movers): record held by the shadow
    out['carried_by_movers'] = out['only_phase'] - out['rec']
    out['rec_word'] = H(list(zip(O, M, WORD))) - HOM            # I(in; word | O, movers)
    out['G_shadow'] = H(list(zip(SP, SHW))) + H(list(zip(SP, PHs))) - H(list(zip(SP, PHs, SHW))) - H(SP)
    allsh = [k for k in range(n) if SHW[k]]; out['open_runs'] = sum(WORD[k] == ('open',) for k in allsh)
    out['open_frac'] = out['open_runs'] / len(allsh) if allsh else 0.0
    out['class_counts'] = dict(settled=len(allsh) - out['open_runs'] - ndis, disordered=ndis, open=out['open_runs'])
    srs = [k for k in allsh if WORD[k] != ('open',)]
    sp = [SP[k] for k in srs]; ph = [PHs[k] for k in srs]; wd = [WORD[k] for k in srs]
    out['shadow_runs'] = len(srs); out['n_contact_shadow'] = len(set(zip(sp, ph)))
    if srs:
        Hsp = H(sp); out['H_C'] = H(list(zip(sp, ph))) - Hsp
        out['I_word'] = H(list(zip(sp, wd))) + H(list(zip(sp, ph))) - H(list(zip(sp, ph, wd))) - Hsp
        out['H_detail'] = out['H_C'] - out['I_word']
        out['I_sp_word'] = H(wd) + Hsp - H(list(zip(sp, wd))); out['n_words'] = len(set(wd))
    else:
        out.update(H_C=0.0, I_word=0.0, H_detail=0.0, I_sp_word=0.0, n_words=0)
    sh = [cm for r in runs for cm in r['comps'] if cm['kind'] not in ('mover', 'disordered')]
    out['disordered_edges'] = sorted({str(cm['wsp']) for r in runs for cm in r['comps'] if cm['kind'] == 'disordered'})
    out['domain_species'] = sorted({str(x) for cm in sh for x in cm['recs']})
    out['wall_species'] = sorted({str(x) for cm in sh for x in cm['wsp']})
    out['mover_species'] = sorted({str((cm['recs'], cm['wsp'][0][2])) for r in runs for cm in r['comps'] if cm['kind'] == 'mover'})
    wb = defaultdict(set)
    for cm in sh:
        for x, b in zip(cm['wsp'], cm['bud']):
            if b is not None: wb[str(x)].add(b)
    occ = Counter(str(x) for cm in sh for x, b in zip(cm['wsp'], cm['bud']) if b is not None)
    out['B_eligible'] = any(m >= 2 for m in occ.values()); out['B_function'] = all(len(v) == 1 for v in wb.values())
    out['wall_budgets'] = {k: sorted(v) for k, v in sorted(wb.items())}
    out['words'] = sorted(Counter(str(x) for x in wd).items(), key=lambda t: -t[1])
    return out


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    jobs = S6.pairs()
    if sys.argv[1:2] in (['smoke'], ['calib']):
        ws = [int(x) for x in sys.argv[2:]] or [j[0] for j in jobs]; sel = [j for j in jobs if j[0] in ws]
        with ProcessPoolExecutor(4) as ex:
            for r in ex.map(job, sel, [sys.argv[1]] * len(sel)): print(json.dumps(r, default=str))
        return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    ref = {r['wolfram']: r for r in json.load(open(PREF))['rules']}
    order = sorted(jobs, key=lambda j: -ref[j[0]]['T'])
    with ProcessPoolExecutor(4) as ex: rows = list(ex.map(job, order))
    for r in rows:
        s = ref[r['wolfram']]
        r['V0'] = (r['n'], r['residue_runs_aligned'], r['T']) == (s['n'], s['residue_runs_aligned'], s['T']) and abs(r['only_phase'] - s['only']) < 1e-12
    lab = lambda r: f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}"
    sh = [r for r in rows if r['role'].startswith('shadow')]; nl = [r for r in rows if r['role'].startswith('null')]
    un = [r for r in sh if r['wolfram'] not in EXPOSED]; el = [r for r in un if r['H_C'] > 1e-9 and r['open_frac'] <= 0.25]
    bl = [r for r in un if r['B_eligible']]
    S = dict(V0_all=all(r['V0'] for r in rows), V1_all=all(r['V1_fail'] == 0 for r in rows),
             V2_nulls=all(r['shadow_runs'] == 0 and r['open_runs'] == 0 for r in nl) and
             all(r['residue_runs_aligned'] == 0 for r in nl if r['wolfram'] in (1, 90)) and
             next(r for r in nl if r['wolfram'] == 5)['kinds'].get('mover', 0) > 0,
             V3_orbits=all(r['opencap'] == 0 for r in rows),
             V4_edges=all(r['edge_hits'] == 0 for r in rows),
             V5_identity=all(abs(r['I_word'] + r['H_detail'] - r['H_C']) < 1e-9 and r['H_detail'] > -1e-9 for r in rows),
             unexposed=len(un), eligible=[lab(r) for r in el], B_eligible=[lab(r) for r in bl],
             H_S_pass=[lab(r) for r in el if r['I_word'] > 1e-9], H_D_pass=[lab(r) for r in el if r['H_detail'] < 1e-9],
             B_function_desc=[lab(r) for r in bl if r['B_function']])
    S['valid'] = all(S[k] for k in ('V0_all', 'V1_all', 'V2_nulls', 'V3_orbits', 'V4_edges', 'V5_identity'))
    v = lambda ok: 'invalid' if not S['valid'] else 'supported' if ok else 'not_supported'
    S['H_S'] = v(len(el) > 0 and len(S['H_S_pass']) >= math.ceil(len(el) / 2))
    S['H_D'] = v(len(el) > 0 and len(S['H_D_pass']) >= math.ceil(len(el) / 2))
    S['table'] = {lab(r): dict(only=round(r['only_phase'], 3), rec=round(r['rec'], 3), movers=round(r['carried_by_movers'], 3),
                  rec_word=round(r['rec_word'], 3), G_sh=round(r['G_shadow'], 3), H_C=round(r['H_C'], 3),
                  I_word=round(r['I_word'], 3), H_detail=round(r['H_detail'], 3), I_sp_word=round(r['I_sp_word'], 3),
                  n_words=r['n_words'], n_shapes_p1=ref[r['wolfram']]['n_shapes'], n_dom=len(r['domain_species']),
                  n_wall=len(r['wall_species']), n_mover=len(r['mover_species']), kinds=r['kinds'], B_fn=r['B_function'],
                  classes=r['class_counts'], open_frac=round(r['open_frac'], 3))
                  for r in rows}
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V0_all', 'V1_all', 'V2_nulls', 'V3_orbits', 'V4_edges', 'V5_identity', 'H_S', 'H_D')}))


if __name__ == '__main__':
    main()
