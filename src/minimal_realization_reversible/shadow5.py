"""MIR-REVERSIBLE-SHADOW-005: shadow capacity versus collision diversity."""
import hashlib, json, math, os, subprocess, sys
os.environ.setdefault('OMP_NUM_THREADS', '1')
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import table, step, SEEDS
from minimal_realization_reversible import collide2 as C2
import minimal_realization_reversible.shadow as S1
import minimal_realization_reversible.shadow3 as S3
TAG = 'mir-reversible-shadow-005-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_SHADOW_005_CONTRACT.md', 'src/minimal_realization_reversible/shadow5.py',
          'src/minimal_realization_reversible/shadow3.py', 'src/minimal_realization_reversible/shadow.py',
          'src/minimal_realization_reversible/collide2.py', 'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/shadow5_seal.json'
OUT = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-SHADOW-005'
S3OUT = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-SHADOW-003/results.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, GAP, OFF0, MS, OFFB, JMAX, SPMAX, MARGIN, RUNCAP, BUBW = 8192, 4096, 24, 24, (8, 16, 32, 64, 128, 256), 64, 8, 3, 300, 6000, 64
H = S3.H
u8 = np.uint8


def vac_period(V):
    return next(q for q in range(1, 13) if all(V[k + q] == V[k] for k in range(40)))


def pattern(tab, seed, phi, V):
    """Difference pattern of an isolated seed after phi ticks: (leftmost rel. to x, p-bits, c-bits)."""
    b = SEEDS[seed - 1]; p = np.zeros(N, u8); c = np.zeros(N, u8); p[X0:X0 + 5] = b[:5]; c[X0:X0 + 5] = b[5:]
    for _ in range(phi): p, c = step(tab, p, c)
    dp, dc = p ^ V[phi], c ^ V[phi + 1]; on = np.flatnonzero(dp | dc); a, z = on.min(), on.max()
    return int(a - X0), dp[a:z + 1].copy(), dc[a:z + 1].copy()


def init(inp, pats):
    ri, li, off, j = inp; p = np.zeros(N, u8); c = np.zeros(N, u8)
    for (lo, a, b), x in ((pats['R'][ri][0], X0), (pats['L'][li][j], X0 + off)):
        p[x + lo:x + lo + len(a)] ^= a; c[x + lo:x + lo + len(b)] ^= b
    return p, c


def core(tab, V, inputs, pats, R0seed, T, RUN=None, launch=None):
    """Erase carriers at T, probe from one site. Returns per-input O, Y, Yp, residue, bubble flags."""
    F = S3.place([(R0seed, X0)])
    for _ in range(T): F = step(tab, *F)
    fd = np.flatnonzero((F[0] ^ V[T]) | (F[1] ^ V[T + 1])); fa, fb = int(fd.min()) - 2, int(fd.max()) + 2
    vR = next(o for o in pats['Rcat'] if o['seed'] == R0seed)['v']
    st, O, left, res, bub, right = [], [], [], [], [], []
    for inp in inputs:
        U = init(inp, pats)
        for _ in range(T): U = step(tab, *U)
        objs, resid = S1.objects(tab, *U, V, T); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[T]; c[a - 2:b + 3] = V[T + 1]
        st.append((p, c)); O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs)))
        lst = [a for a, _ in resid] + [x['span'][0] for x in objs]; left.append(min(lst) if lst else X0)
        cl = S1.ucl(p, c, V, T); res.append(bool(cl)); bub.append(any(b - a + 1 > BUBW for a, b in cl))
        right.append(max([b for a, b in cl if b - a + 1 <= BUBW], default=None))
    if launch is None: launch = min(left) - GAP - (fb - fa + 1)
    rr = [r for r in right if r is not None]
    if RUN is None: RUN = min(RUNCAP, math.ceil((max(rr) - launch + 64) / vR)) if rr else 1500
    TF = T + RUN; Y, Yp = [], []
    for p, c in st:
        Pp, Pc = p.copy(), c.copy(); Np, Nc = p, c
        Pp[launch:launch + fb - fa + 1] = F[0][fa:fb + 1]; Pc[launch:launch + fb - fa + 1] = F[1][fa:fb + 1]
        for _ in range(RUN): Pp, Pc = step(tab, Pp, Pc); Np, Nc = step(tab, Np, Nc)
        d = (Pp ^ Np) | (Pc ^ Nc); y = np.flatnonzero(Pc ^ Nc)
        Y.append((tuple((y - y.min()).tolist()), int(y.min())) if y.size else ((), 0))
        objsP, _ = S1.objects(tab, Pp, Pc, V, TF)
        Yp.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objsP if d[x['span'][0]:x['span'][1] + 1].any())))
    return dict(O=O, Y=Y, Yp=Yp, res=res, bub=bub, RUN=RUN, launch=launch, run_capped=RUN == RUNCAP)


def cell(D, idx):
    O = [D['O'][i] for i in idx]; HI = math.log2(len(idx)); HO = H(O)
    only = HI - HO; fp = H(list(zip(O, [D['Y'][i] for i in idx]))) - HO; ps = H(list(zip(O, [D['Yp'][i] for i in idx]))) - HO
    return dict(n=len(idx), H_in=HI, only=only, footprint=fp, probe_state=ps, unrecovered=only - fp,
                residue_runs=sum(D['res'][i] for i in idx), bubble_runs=sum(D['bub'][i] for i in idx))


def job(a):
    w, seedR, seedL, ref, role = a
    S1.N = N; tab = table(w); rr = next(r for r in json.load(open(C2.CAT))['rules'] if r['wolfram'] == w)
    cat = C2.catalogue(rr); Rs = [o for o in cat if o['v'] > 0][:SPMAX]; Ls = [o for o in cat if o['v'] < 0][:SPMAX]
    ri0 = [o['seed'] for o in Rs].index(seedR); li0 = [o['seed'] for o in Ls].index(seedL)
    V0seq = C2.vac_seq(tab, 40 + 4 * JMAX * 12); q = vac_period(V0seq)
    pats = dict(Rcat=Rs, R=[[pattern(tab, o['seed'], 0, V0seq)] for o in Rs], L=[])
    for o in Ls:
        base = pattern(tab, o['seed'], 0, V0seq); seq = [base]
        for j in range(1, JMAX):
            assert V0seq[q * j] == V0seq[0] and V0seq[q * j + 1] == V0seq[1]
            pj = pattern(tab, o['seed'], q * j, V0seq)
            if len(pj[1]) == len(base[1]) and np.array_equal(pj[1], base[1]) and np.array_equal(pj[2], base[2]): break
            seq.append((base[0], pj[1], pj[2]))
        pats['L'].append(seq)
    J = len(pats['L'][li0])
    A = [(ri0, li0, off, 0) for off in range(OFF0, OFF0 + max(MS))]
    B = [(ri0, li0, off, j) for off in range(OFF0, OFF0 + OFFB) for j in range(J)]
    Cs = [(ri, li, off, 0) for ri in range(len(Rs)) for li in range(len(Ls)) for off in range(OFF0, OFF0 + OFFB)]
    out = dict(wolfram=w, role=role, seedR=seedR, seedL=seedL, q=q, J=J, nR=len(Rs), nL=len(Ls))
    # V0: SHADOW-003 settings
    Vs = C2.vac_seq(tab, 600 + 1500 + C2.PMAX + 4)
    D0 = core(tab, Vs, A[:64], pats, seedR, 600, RUN=1500); c0 = cell(D0, range(64))
    out['V0'] = bool(ref is None or all(abs(c0[k] - ref[r]) < 1e-12 for k, r in
                                        [('only', 'only_shadow'), ('footprint', 'footprint_beyond'), ('probe_state', 'probe_state_beyond')]))
    if role == 'smoke': return out
    close = min(R['v'] - L['v'] for R in Rs for L in Ls); T = math.ceil(296 / close) + MARGIN
    U = list(dict.fromkeys(A + B + Cs)); ix = {u: i for i, u in enumerate(U)}
    V = C2.vac_seq(tab, T + RUNCAP + C2.PMAX + 4); D = core(tab, V, U, pats, seedR, T)
    out.update(T=T, RUN=D['RUN'], run_capped=D['run_capped'],
               A={M: cell(D, [ix[u] for u in A[:M]]) for M in MS},
               B=cell(D, [ix[u] for u in B]), C=cell(D, [ix[u] for u in Cs]))
    return out


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    if sys.argv[1:] != ['smoke']:
        subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
        assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    old = json.load(open(S3OUT))['pairs']; jobs, seen = [], set()
    for x in old:
        if x['shadow_runs'] > 0 and x['only_shadow'] > 1e-12 and x['wolfram'] not in seen:
            seen.add(x['wolfram']); jobs.append((x['wolfram'], x['seedR'], x['seedL'], x, 'shadow'))
    for w in (1, 5):
        x = next(x for x in old if x['wolfram'] == w and x['shadow_runs'] == 0); jobs.append((w, x['seedR'], x['seedL'], x, 'null'))
    if sys.argv[1:] == ['smoke']:
        j = jobs[[a[0] for a in jobs].index(37)]; r = job(j[:4] + ('smoke',)); print('smoke V0', r['V0']); return
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(6) as ex: rows = list(ex.map(job, jobs))
    cells = [(r, c) for r in rows for c in list(r['A'].values()) + [r['B'], r['C']]]
    sh = [r for r in rows if r['role'] == 'shadow']
    elig = [r for r in sh if r['A'][64]['only'] > 1e-12 and r['A'][256]['bubble_runs'] == 0]
    gain = {r['wolfram']: r['A'][256]['only'] - r['A'][64]['only'] for r in elig}
    bf = [c for r, c in cells if c['bubble_runs'] == 0 and c['only'] > 1e-9]
    S = dict(V0_all=all(r['V0'] for r in rows), V1=all(c['footprint'] < 1e-9 and c['probe_state'] < 1e-9 for _, c in cells if c['residue_runs'] == 0),
             shadow_rules=len(sh), eligible_H_sat=len(elig), gain_256_vs_64=gain,
             sat=sum(g <= 0.5 for g in gain.values()), grow=sum(g >= 1 for g in gain.values()),
             bubble_free_cells_with_only=len(bf), unrecovered_zero=sum(c['unrecovered'] < 1e-9 for c in bf),
             cells_with_bubbles=sum(c['bubble_runs'] > 0 for _, c in cells), run_capped=[r['wolfram'] for r in rows if r['run_capped']])
    S['valid'] = S['V0_all'] and S['V1']
    k = math.ceil(2 * len(elig) / 3) if elig else None
    S['H_sat'] = 'invalid' if not S['valid'] else 'n/a' if not elig else 'supported' if S['sat'] >= k else 'H_grow' if S['grow'] >= k else 'mixed'
    S['H_R'] = 'invalid' if not S['valid'] else 'n/a' if not bf else 'supported' if S['unrecovered_zero'] >= 0.9 * len(bf) else 'not_supported'
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps(S, default=str))


if __name__ == '__main__':
    main()
