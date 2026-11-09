"""MIR-REVERSIBLE-PHASE-001: does a shadow keep the carriers' contact phase as internal state, or only as placement?

Inputs, species, T and carrier erasure are identical to SHADOW-009 / BUDGET-001 (shadow7.lists conventions; N = 16384,
X0 = 8192, offsets 24..87; duplicate starting states dropped). Contact phase class phi = off mod Delta, with
Delta = (v_R - v_L) * lcm(p_R, p_L, p_vac): offsets in one class give exact space-time translates of one history.
Shape type S = erased residue modulo space-time translation (union of exact matches of the cropped two-layer vacuum
difference, vacuum phase included, inside a tick window). See docs/ICP_MIR_REVERSIBLE_PHASE_001_CONTRACT.md.
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
TAG = 'mir-reversible-phase-001-v0.1-frozen'
P = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_PHASE_001_CONTRACT.md'] + [P + f for f in (
    'phase1.py', 'shadow7.py', 'shadow6.py', 'shadow3.py', 'shadow.py', 'collide2.py', 'vacuum_collide.py')]
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/phase1_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-PHASE-001'
S9REF = OM / 'MIR-REVERSIBLE-SHADOW-009/results.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, OFFS = S7.N, S7.X0, S7.OFFS
H = S7.H
EXPOSED = [91]
SETTLE = 300


def period(tab, seed, V):
    p = np.zeros(C2.N, np.uint8); c = np.zeros(C2.N, np.uint8); pp, cc = seed
    p[C2.X0:C2.X0 + len(pp)] ^= np.array(pp, np.uint8); c[C2.X0:C2.X0 + len(cc)] ^= np.array(cc, np.uint8)
    r = C2.orbit(tab, p, c, 0, V); return r[0], r[1]


def key(p, c, V, t):
    dp, dc = p ^ V[t], c ^ V[t + 1]; on = np.flatnonzero(dp | dc)
    if not on.size: return None, None, None
    lo, hi = int(on.min()), int(on.max())
    h = hashlib.blake2b(bytes([V[t], V[t + 1]]) + dp[lo:hi + 1].tobytes() + b'|' + dc[lo:hi + 1].tobytes(), digest_size=16).digest()
    return h, lo, hi


class UF:
    def __init__(s, n): s.p = list(range(n))
    def f(s, a):
        while s.p[a] != a: s.p[a] = s.p[s.p[a]]; a = s.p[a]
        return a
    def u(s, a, b):
        a, b = s.f(a), s.f(b)
        if a != b: s.p[max(a, b)] = min(a, b)


def partition(runs, half):
    """Shape types: run a ~ run b if b's centre key occurs in a's window within +-half ticks of a's centre."""
    uf = UF(len(runs)); idx = defaultdict(list)
    for a, r in enumerate(runs):
        D = len(r['keys']) // 2
        for k in range(D - half, D + half + 1): idx[r['keys'][k]].append((a, k - D))
    dmax = 0
    for b, r in enumerate(runs):
        for a, d in idx.get(r['keys'][len(r['keys']) // 2], []):
            uf.u(a, b); dmax = max(dmax, abs(d)) if a != b else dmax
    return [uf.f(a) for a in range(len(runs))], dmax


def job(j, smoke=False):
    S1.N = N
    w, _, _, _, role = j; tab, Rs, Ls = S7.lists(j)
    close = min(R['v'] - L['v'] for R in Rs for L in Ls); T = math.ceil(552 / close) + 300
    V0 = C2.vac_seq(tab, 64); pv = next(k for k in range(1, 50) if (V0[k], V0[k + 1]) == (V0[0], V0[1]))
    pR = [period(tab, o['seed'], C2.vac_seq(tab, C2.PMAX + 8)) for o in Rs]
    pL = [period(tab, o['seed'], C2.vac_seq(tab, C2.PMAX + 8)) for o in Ls]
    tau = {(ri, li): math.lcm(pR[ri][0], pL[li][0], pv) for ri in range(len(Rs)) for li in range(len(Ls))}
    Delta = {k: int((Rs[k[0]]['v'] - Ls[k[1]]['v']) * t) for k, t in tau.items()}
    D = 3 * max(tau.values()) + 32
    cl = {k: Rs[k[0]]['v'] - Ls[k[1]]['v'] for k in tau}
    E = max(math.floor((OFFS[-1] - OFFS[0]) / v) for v in cl.values())
    V = C2.vac_seq(tab, T + E + SETTLE + 2 * D + C2.PMAX + 8)
    O, SP, PH, RES, RES9, runs, seen = [], [], [], [], [], [], set(); dropped = edge = 0
    for ri, li, off in [(ri, li, o) for ri in range(len(Rs)) for li in range(len(Ls)) for o in OFFS]:
        U = S6.place([(Rs[ri]['seed'], X0), (Ls[li]['seed'], X0 + off)]); kb = U[0].tobytes() + U[1].tobytes()
        if kb in seen: dropped += 1; continue
        seen.add(kb)
        for _ in range(T): U = step(tab, *U)
        objs, _ = S1.objects(tab, *U, V, T); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[T]; c[a - 2:b + 3] = V[T + 1]
        O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs)))
        RES9.append(bool(np.flatnonzero((p ^ V[T]) | (c ^ V[T + 1])).size))
        SP.append((ri, li)); PH.append(off % Delta[(ri, li)])
        # age-aligned erasure: equal collision age for all inputs (exact translates within a contact class)
        e = math.floor((off - OFFS[0]) / cl[(ri, li)]); t = T
        for _ in range(e + SETTLE): U = step(tab, *U); t += 1
        objs, _ = S1.objects(tab, *U, V, t); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[t]; c[a - 2:b + 3] = V[t + 1]
        has = bool(np.flatnonzero((p ^ V[t]) | (c ^ V[t + 1])).size); RES.append(has)
        if not has: continue
        keys, ext = [], []
        for k in range(2 * D + 1):
            h, lo, hi = key(p, c, V, t); keys.append(h); ext.append((lo, hi))
            edge += lo < 64 or hi > N - 64
            if k < 2 * D: p, c = step(tab, p, c); t += 1
        runs.append(dict(i=len(O) - 1, sp=(ri, li), off=off, ph=PH[-1], keys=keys, ext=(ext[0], ext[-1])))
    n = len(O)
    lab, dmax = partition(runs, D); lab2, _ = partition(runs, D // 2)
    # V1: one shape type and one residue status per contact class; members of a class match at delta = 0
    v1 = 0; byC = defaultdict(set); resC = defaultdict(set); cen = defaultdict(set)
    for r, s in zip(runs, lab): byC[(r['sp'], r['ph'])].add(s); cen[(r['sp'], r['ph'])].add(r['keys'][D])
    for i in range(n): resC[(SP[i], PH[i])].add(RES[i])
    v1 = sum(len(x) > 1 for x in byC.values()) + sum(len(x) > 1 for x in resC.values()) + sum(len(x) > 1 for x in cen.values())
    out = dict(wolfram=w, role=role, n=n, dropped=dropped, T=T, residue_runs=sum(RES9), residue_runs_aligned=sum(RES), pv=pv, D=D,
               periods=dict(R=[list(x) for x in pR], L=[list(x) for x in pL]), Delta={f'{a}{b}': d for (a, b), d in Delta.items()},
               V1_fail=v1, V3=sorted(Counter(lab).values()) == sorted(Counter(lab2).values()) and len(set(lab)) == len(set(lab2)),
               edge_hits=edge, dmax=dmax)
    if smoke:
        return {k: out[k] for k in ('wolfram', 'n', 'dropped', 'residue_runs', 'V1_fail', 'edge_hits')}
    HO = H(O); out['only'] = math.log2(n) - HO if n else 0.0
    out['G'] = H(list(zip(SP, RES))) + H(list(zip(SP, PH))) - H(list(zip(SP, PH, RES))) - H(SP)  # I(res; phi | sp)
    if runs:
        sp = [r['sp'] for r in runs]; ph = [r['ph'] for r in runs]
        Hsp = H(sp); out['H_C'] = H(list(zip(sp, ph))) - Hsp                       # H(phi | sp, res)
        out['I_int'] = H(list(zip(sp, lab))) - Hsp                                   # I(S; phi | sp, res)
        out['H_place'] = out['H_C'] - out['I_int']                                   # H(phi | sp, S, res)
        out['I_int_check'] = H(list(zip(sp, lab))) + H(list(zip(sp, ph))) - H(list(zip(sp, ph, lab))) - Hsp
        out['I_sp_int'] = H(lab) + Hsp - H(list(zip(sp, lab)))                       # I(S; sp | res)
        out['H_S'] = H(lab); out['n_shapes'] = len(set(lab)); out['n_contact'] = len(set(zip(sp, ph)))
        Sfull = [None] * n
        for r, s in zip(runs, lab): Sfull[r['i']] = s
        out['I_rec_S'] = H(list(zip(O, Sfull))) - HO                                 # I(in; S | O)
        types = defaultdict(list)
        for r, s in zip(runs, lab): types[s].append(r)
        out['shape_types'] = []
        for s, rs in sorted(types.items(), key=lambda t: -len(t[1])):
            (l1, h1), (l2, h2) = rs[0]['ext']
            out['shape_types'].append(dict(runs=len(rs), contacts=sorted({f"{r['sp'][0]}{r['sp'][1]}:{r['ph']}" for r in rs}),
                                           v_left=round((l2 - l1) / (2 * D), 4), v_right=round((h2 - h1) / (2 * D), 4)))
    else:
        out.update(H_C=0.0, I_int=0.0, H_place=0.0, I_int_check=0.0, I_sp_int=0.0, H_S=0.0, n_shapes=0, n_contact=0,
                   I_rec_S=0.0, shape_types=[])
    return out


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    jobs = S6.pairs()
    if sys.argv[1:2] == ['smoke']:
        print(json.dumps(job(next(j for j in jobs if j[0] == int(sys.argv[2])), smoke=True))); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    ref = {r['wolfram']: r for r in json.load(open(S9REF))['rules']}
    order = sorted(jobs, key=lambda j: -ref[j[0]]['T'])
    with ProcessPoolExecutor(4) as ex: rows = list(ex.map(job, order))
    for r in rows:
        s = ref[r['wolfram']]
        r['V0'] = (r['n'], r['dropped'], r['residue_runs'], r['T']) == (s['n'], s['dropped'], s['residue_runs'], s['T']) and abs(r['only'] - s['only']) < 1e-12
    lab = lambda r: f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}"
    sh = [r for r in rows if r['role'].startswith('shadow')]; nl = [r for r in rows if r['role'].startswith('null')]
    un = [r for r in sh if r['wolfram'] not in EXPOSED]; el = [r for r in un if r['H_C'] > 1e-9]
    S = dict(V0_all=all(r['V0'] for r in rows), V1_all=all(r['V1_fail'] == 0 for r in rows),
             V2_nulls=all(r['residue_runs'] == 0 and r['n_shapes'] == 0 for r in nl),
             V3_all=all(r['V3'] for r in rows), V4_edges=all(r['edge_hits'] == 0 for r in rows),
             V5_identity=all(abs(r['I_int'] - r['I_int_check']) < 1e-9 for r in rows),
             unexposed=len(un), eligible=[lab(r) for r in el],
             H_G_pass=[lab(r) for r in un if r['G'] > 1e-9], H_I_pass=[lab(r) for r in el if r['I_int'] > 1e-9],
             H_F_pass=[lab(r) for r in el if r['H_place'] < 1e-9])
    S['valid'] = all(S[k] for k in ('V0_all', 'V1_all', 'V2_nulls', 'V3_all', 'V4_edges', 'V5_identity'))
    v = lambda ok: 'invalid' if not S['valid'] else 'supported' if ok else 'not_supported'
    S['H_G'] = v(len(S['H_G_pass']) >= math.ceil(len(un) / 2))
    S['H_I'] = v(len(el) > 0 and len(S['H_I_pass']) >= math.ceil(len(el) / 2))
    S['H_F'] = v(len(el) > 0 and len(S['H_F_pass']) >= math.ceil(len(el) / 2))
    S['table'] = {lab(r): dict(only=round(r['only'], 3), G=round(r['G'], 3), H_C=round(r['H_C'], 3), I_int=round(r['I_int'], 3),
                  H_place=round(r['H_place'], 3), I_sp_int=round(r['I_sp_int'], 3), I_rec_S=round(r['I_rec_S'], 3),
                  n_shapes=r['n_shapes'], n_contact=r['n_contact'], res=r['residue_runs'], Delta=r['Delta'], dmax=r['dmax'])
                  for r in rows}
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V0_all', 'V1_all', 'V2_nulls', 'V3_all', 'V4_edges', 'V5_identity', 'H_G', 'H_I', 'H_F')}))


if __name__ == '__main__':
    main()
