"""MIR-REVERSIBLE-BUDGET-001: where the conserved budget goes in a shadow collision (carriers vs shadow).

Inputs, species, T and erasure are identical to SHADOW-009 (shadow9.prepare conventions). Budgets: BUDGET-000 window-2
normal-form basis (primary, 'w2') and window-2 + window-3 extension (window3.json, 'full'). All budgets are ring totals
(vacuum density 0 in every phase, so they are gauge-free). See docs/ICP_MIR_REVERSIBLE_BUDGET_001_CONTRACT.md.
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
from minimal_realization_reversible.vacuum_collide import table, step
from minimal_realization_reversible import collide2 as C2
import minimal_realization_reversible.shadow as S1
import minimal_realization_reversible.shadow6 as S6
import minimal_realization_reversible.shadow7 as S7
import minimal_realization_reversible.budget0 as B0
import minimal_realization_reversible.budget0_w3 as B3
TAG = 'mir-reversible-budget-001-v0.1-frozen'
P = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_BUDGET_001_CONTRACT.md'] + [P + f for f in (
    'budget1.py', 'budget0.py', 'budget0_w3.py', 'shadow7.py', 'shadow6.py', 'shadow3.py', 'shadow.py', 'collide2.py',
    'vacuum_collide.py')] + ['output/minimal_realization/MIR-REVERSIBLE-BUDGET-000/results.json',
                             'output/minimal_realization/MIR-REVERSIBLE-BUDGET-000/window3.json']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/budget1_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-BUDGET-001'
S9REF = OM / 'MIR-REVERSIBLE-SHADOW-009/results.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, OFFS = S7.N, S7.X0, S7.OFFS
SMAX, MINRUN = 8, 16
INV = [22, 26, 33, 37, 54, 82, 91, 94, 123, 139, 147, 201, 209, 218]
FREE = [58, 114, 143, 151, 154, 171, 182, 186, 213, 233, 241]
H = S7.H
R2 = json.loads((OM / 'MIR-REVERSIBLE-BUDGET-000/results.json').read_text())['rules']
R3 = json.loads((OM / 'MIR-REVERSIBLE-BUDGET-000/window3.json').read_text())['rules']


def basis(w):
    return R2[str(w)]['window2_coeffs'], R3[str(w)]['tables']


def vec(w, p, c):
    """Full budget vector: window-2 components first, then the new window-3 components (python ints)."""
    b2, b3 = basis(w)
    return tuple(int(B0.total(k, p, c)) for k in b2) + tuple(int(B3.total3(t, p, c)) for t in b3)


def dens2(w, p, c):
    """Window-2 local densities d_i = phi(cell i, cell i+1), one row per basis element."""
    cell = 2 * p.astype(np.int64) + c; ix = 4 * cell + np.roll(cell, -1)
    return [(B0.MNF @ np.array(k))[ix] for k in basis(w)[0]]


def segments(w, p, c, lo, hi):
    """Cut the residue [lo, hi] at background stretches: maximal runs (>= MINRUN cells) that are spatially periodic with
    the smallest period s <= SMAX. A stretch is a valid cut only if its window-2 budget per period is exactly 0; the cut
    value is the left sum L(m) = sum_{i<m} d_i averaged over one period at the stretch middle. Returns (segment budget
    sequence, flank descriptors, number of drifting stretches). Flank = (s, the period pattern read from the first
    site m with m % s == 0 inside the stretch), i.e. pattern and spatial phase."""
    q = 2 * p.astype(np.int64) + c; d = dens2(w, p, c); cs = np.cumsum(d, axis=1); used = np.zeros(N, bool)
    cuts, drift = [], 0
    for s in range(1, SMAX + 1):
        eq = np.zeros(N, bool); eq[lo:hi - s + 1] = q[lo:hi - s + 1] == q[lo + s:hi + 1]
        i = lo
        while i <= hi:
            if not eq[i]: i += 1; continue
            j = i
            while j <= hi and eq[j]: j += 1
            a, b = i, j - 1 + s  # cells a..b are s-periodic
            if b - a + 1 >= MINRUN and not used[a:b + 1].any():
                used[a:b + 1] = True; mid = (a + b) // 2 - s // 2
                rho = [int(cs[k][mid + s - 1] - cs[k][mid - 1]) for k in range(len(d))]
                if any(rho): drift += 1
                else:
                    val = tuple(Fr(int(sum(cs[k][m - 1] for m in range(mid, mid + s))), s) for k in range(len(d)))
                    m0 = next(m for m in range(a, b + 1) if m % s == 0)
                    cuts.append((a, val, (s, tuple(q[m0:m0 + s].tolist()))))
            i = j
    cuts.sort(); tot = tuple(Fr(int(cs[k][-1])) for k in range(len(d))); vals = [v for _, v, _ in cuts] + [tot]
    seg, prev = [], tuple(Fr(0) for _ in d)
    for v in vals: seg.append(tuple(str(x - y) for x, y in zip(v, prev))); prev = v
    return tuple(seg), tuple(f for _, _, f in cuts), drift


def sid(tab, seed):
    sp = S7.species(tab, seed); return min(hash(x) for x in sp) if sp else None


def job(j, smoke=False):
    S1.N = N
    w, _, _, _, role = j; tab, Rs, Ls = S7.lists(j); n2 = len(basis(w)[0])
    close = min(R['v'] - L['v'] for R in Rs for L in Ls); T = math.ceil(552 / close) + 300
    V = C2.vac_seq(tab, T + C2.PMAX + 4); orb = {(int(V[t]), int(V[t + 1])) for t in range(C2.PMAX)}
    vac = lambda: (np.full(N, V[T], np.uint8), np.full(N, V[T + 1], np.uint8))
    # V1b: free species budgets at 0 and T
    spb, v1b = {}, True
    for side, sp in (('R', Rs), ('L', Ls)):
        for i, o in enumerate(sp):
            b0 = vec(w, *S6.place([(o['seed'], X0)])); F, _, _ = S7.free(tab, o['seed'], T, V)
            v1b &= vec(w, *F) == b0; spb[(side, i)] = b0
    sidR = [sid(tab, o['seed']) for o in Rs]; sidL = [sid(tab, o['seed']) for o in Ls]
    O, BR, SP, SEG, FL, ND, elastic, res, seen = [], [], [], [], [], [], [], [], set()
    dropped = v1a_fail = v2_fail = v4_fail = 0
    for ri, li, off in [(ri, li, o) for ri in range(len(Rs)) for li in range(len(Ls)) for o in OFFS]:
        U = S6.place([(Rs[ri]['seed'], X0), (Ls[li]['seed'], X0 + off)]); key = U[0].tobytes() + U[1].tobytes()
        if key in seen: dropped += 1; continue
        seen.add(key)
        Bin = vec(w, *U); v1a_fail += Bin != tuple(a + b for a, b in zip(spb[('R', ri)], spb[('L', li)]))
        for _ in range(T): U = step(tab, *U)
        objs, _ = S1.objects(tab, *U, V, T); p, c = U[0].copy(), U[1].copy(); Bout = [0] * len(Bin)
        for x in objs:
            a, b = x['span']; q, r = vac(); q[a - 2:b + 3] = U[0][a - 2:b + 3]; r[a - 2:b + 3] = U[1][a - 2:b + 3]
            Bout = [s + t for s, t in zip(Bout, vec(w, q, r))]
            p[a - 2:b + 3] = V[T]; c[a - 2:b + 3] = V[T + 1]
        Bres = vec(w, p, c); v2_fail += Bin != tuple(s + t for s, t in zip(Bout, Bres))
        O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs))); BR.append(Bres); SP.append((ri, li))
        on = np.flatnonzero((p ^ V[T]) | (c ^ V[T + 1])); has = bool(on.size); res.append(has)
        if not has:
            v4_fail += any(Bres); SEG.append(None); FL.append(None); ND.append(0); elastic.append(None); continue
        sg, fl, dr = segments(w, p, c, int(on.min()), int(on.max())); SEG.append(sg); FL.append(fl); ND.append(dr)
        elastic.append(Counter([sidR[ri], sidL[li]]) == Counter(x['species'] for x in objs))
    n = len(O); HO = H(O); only = math.log2(n) - HO
    I = lambda *cols: H(list(zip(O, *cols))) - HO
    w2 = [b[:n2] for b in BR]
    def stats(Bv):
        I_B = I(Bv); cls = Counter(zip(O, Bv))
        onlyZ = sum(m / n * math.log2(m) for (o, b), m in cls.items() if not any(b))
        rr = [b for b, h in zip(Bv, res) if h]
        return dict(I_B=I_B, I_free=only - I_B, only_Z=onlyZ, f_bear=sum(map(any, rr)) / len(rr) if rr else None,
                    distinct=sorted({str(b) for b in rr}), elastic_Bres=sorted({str(b) for b, e in zip(Bv, elastic) if e}))
    rr = [k for k, h in enumerate(res) if h]
    out = dict(wolfram=w, role=role, n=n, dropped=dropped, T=T, residue_runs=sum(res), only=only, n_w2=n2,
               n_full=len(BR[0]) if BR else 0, bound=I(SP), V1=(v1a_fail == 0 and v1b), V1a_fail=v1a_fail, V1b=v1b,
               V2_fail=v2_fail, V4_fail=v4_fail, w2=stats(w2), full=stats(BR),
               I_seg=I(SEG), I_seg_flank=I(SEG, FL) - I(FL), H_W_bits=I(SEG, FL, SP) - I(FL, SP),
               I_flank=I(FL), I_segL=I([x and x[0] for x in SEG]), I_segR=I([x and x[-1] for x in SEG]),
               runs_with_cut=sum(len(SEG[k]) > 1 for k in rr), drifting_stretches=sum(ND),
               nseg=sorted(Counter(len(SEG[k]) for k in rr).items()), flank_periods=sorted({f[0] for k in rr for f in FL[k]}),
               elastic_frac=sum(elastic[k] for k in rr) / len(rr) if rr else None,
               seg_values=sorted(Counter(str(SEG[k]) for k in rr).items(), key=lambda t: -t[1])[:12],
               species_budget={f'{s}{i}': list(b) for (s, i), b in spb.items()})
    if smoke:
        return {k: out[k] for k in ('wolfram', 'n', 'dropped', 'residue_runs', 'V1', 'V2_fail', 'V4_fail', 'runs_with_cut', 'drifting_stretches', 'nseg', 'flank_periods')}
    return out


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    jobs = [j for j in S6.pairs() if j[0] in INV and j[4].startswith('shadow')]
    assert sorted(j[0] for j in jobs) == sorted(INV), [j[0] for j in jobs]
    if sys.argv[1:2] == ['smoke']:
        print(json.dumps(job(next(j for j in jobs if j[0] == int(sys.argv[2])), smoke=True))); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    ref = {r['wolfram']: r for r in json.load(open(S9REF))['rules'] if r['role'].startswith('shadow')}
    order = sorted(jobs, key=lambda j: -ref[j[0]]['T'])
    with ProcessPoolExecutor(4) as ex: rows = list(ex.map(job, order))
    for r in rows:
        s = ref[r['wolfram']]
        r['V0'] = (r['n'], r['dropped'], r['residue_runs']) == (s['n'], s['dropped'], s['residue_runs']) and abs(r['only'] - s['only']) < 1e-12
        r['V3'] = r['w2']['I_B'] <= r['bound'] + 1e-9 and r['full']['I_B'] <= r['bound'] + 1e-9
        r['I_L_s9'], r['I_R_s9'] = s['I_L'], s['I_R']
    lab = lambda r: f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}"
    inc = [r for r in rows if r['V2_fail'] == 0]; ni = len(inc)
    bear = lambda key: [lab(r) for r in inc if r[key]['f_bear'] is not None and r[key]['f_bear'] > 0.5]
    zero = lambda key: [lab(r) for r in inc if r[key]['only_Z'] > 1e-9]
    hw = [lab(r) for r in inc if r['H_W_bits'] > 1e-9]
    r54 = next(r for r in rows if r['wolfram'] == 54)
    S = dict(V0_all=all(r['V0'] for r in rows), V1_all=all(r['V1'] for r in rows), V2_excluded=[lab(r) for r in rows if r['V2_fail']],
             V3_all=all(r['V3'] for r in inc) and r54['w2']['I_B'] < 1e-12 and r54['full']['I_B'] < 1e-12,
             V4_all=all(r['V4_fail'] == 0 for r in rows), included=ni,
             H_A_pass=bear('w2'), H_A3_pass=bear('full'), H_Z_pass=zero('w2'), H_Z3_pass=zero('full'), H_W_pass=hw)
    S['valid'] = S['V0_all'] and S['V1_all'] and len(S['V2_excluded']) <= 2 and S['V3_all'] and S['V4_all']
    v = lambda ok: 'invalid' if not S['valid'] else 'supported' if ok else 'not_supported'
    S['H_A'] = v(len(S['H_A_pass']) >= math.ceil(ni / 2)); S['H_A3'] = v(len(S['H_A3_pass']) >= math.ceil(ni / 2))
    S['H_Z'] = v(len(S['H_Z_pass']) >= 1); S['H_Z3'] = v(len(S['H_Z3_pass']) >= 1); S['H_W'] = v(len(hw) >= 1)
    S['table'] = {lab(r): dict(only=round(r['only'], 3), bound=round(r['bound'], 3),
                  IB2=round(r['w2']['I_B'], 3), IB=round(r['full']['I_B'], 3), Z2=round(r['w2']['only_Z'], 3),
                  Z=round(r['full']['only_Z'], 3), bear2=r['w2']['f_bear'], bear=r['full']['f_bear'],
                  Iseg=round(r['I_seg'], 3), Isegfl=round(r['I_seg_flank'], 3), HW=round(r['H_W_bits'], 3),
                  Ifl=round(r['I_flank'], 3), IsL=round(r['I_segL'], 3), IsR=round(r['I_segR'], 3),
                  IL9=round(r['I_L_s9'], 3), IR9=round(r['I_R_s9'], 3), elastic=r['elastic_frac'],
                  cut=r['runs_with_cut'], drift=r['drifting_stretches'], nseg=r['nseg']) for r in rows}
    S['invariant_free_pairs'] = {w: 'B identically 0 (no additive invariant up to window 4)' for w in FREE}
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V0_all', 'V1_all', 'V2_excluded', 'V3_all', 'V4_all', 'H_A', 'H_A3', 'H_Z', 'H_Z3', 'H_W')}))


if __name__ == '__main__':
    main()
