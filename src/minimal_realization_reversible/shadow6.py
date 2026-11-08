"""MIR-REVERSIBLE-SHADOW-006: shadow scaling, outline vs content, regimes and type (active + silent)."""
import ast, hashlib, json, math, os, subprocess, sys
os.environ.setdefault('OMP_NUM_THREADS', '1')
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction as Fr
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import table, step, SEEDS
from minimal_realization_reversible import collide2 as C2
import minimal_realization_reversible.shadow as S1
import minimal_realization_reversible.shadow3 as S3
TAG = 'mir-reversible-shadow-006-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_SHADOW_006_CONTRACT.md', 'src/minimal_realization_reversible/shadow6.py',
          'src/minimal_realization_reversible/shadow3.py', 'src/minimal_realization_reversible/shadow.py',
          'src/minimal_realization_reversible/collide2.py', 'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/shadow6_seal.json'
OM = ROOT / 'output/minimal_realization'
OUT = OM / 'MIR-REVERSIBLE-SHADOW-006'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, GAP, OFF0, MS, OFFC, MARGIN, RUNCAP, CW, STAT = 16384, 8192, 24, 24, (8, 16, 32, 64, 128, 256, 512), 64, 300, 6000, 64, 300
H = S3.H
u8 = np.uint8


def place(seeds):
    p = np.zeros(N, u8); c = np.zeros(N, u8)
    for (pp, cc), x in seeds:
        p[x:x + len(pp)] ^= np.array(pp, u8); c[x:x + len(cc)] ^= np.array(cc, u8)
    return p, c


def core(tab, V, inputs, Rs, Ls, R0, T, RUN=None):
    F = place([(R0['seed'], X0)])
    for _ in range(T): F = step(tab, *F)
    fd = np.flatnonzero((F[0] ^ V[T]) | (F[1] ^ V[T + 1])); fa, fb = int(fd.min()) - 2, int(fd.max()) + 2
    st, O, G, typ, left, right = [], [], [], [], [], []
    for ri, li, off in inputs:
        U = place([(Rs[ri]['seed'], X0), (Ls[li]['seed'], X0 + off)])
        for _ in range(T): U = step(tab, *U)
        objs, resid = S1.objects(tab, *U, V, T); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[T]; c[a - 2:b + 3] = V[T + 1]
        st.append((p, c)); O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs)))
        lst = [a for a, _ in resid] + [x['span'][0] for x in objs]; left.append(min(lst) if lst else X0)
        on = np.flatnonzero((p ^ V[T]) | (c ^ V[T + 1]))
        if not on.size: G.append(None); typ.append('none'); continue
        lo, hi = int(on.min()), int(on.max()); G.append((lo, hi))
        t = 'extended'
        if hi - lo + 1 <= CW:
            q, r, t = p.copy(), c.copy(), 'compact'
            for k in range(STAT):
                q, r = step(tab, q, r); e = np.flatnonzero((q ^ V[T + k + 1]) | (r ^ V[T + k + 2]))
                if e.min() < lo - 8 or e.max() > hi + 8: t = 'extended'; break
            right.append(hi)
        typ.append(t)
    launch = min(left) - GAP - (fb - fa + 1)
    if RUN is None: RUN = min(RUNCAP, math.ceil((max(right) - launch + 64) / R0['v'])) if right else 1500
    TF = T + RUN; Y, Yp = [], []
    for p, c in st:
        Pp, Pc = p.copy(), c.copy(); Np, Nc = p, c
        Pp[launch:launch + fb - fa + 1] = F[0][fa:fb + 1]; Pc[launch:launch + fb - fa + 1] = F[1][fa:fb + 1]
        for _ in range(RUN): Pp, Pc = step(tab, Pp, Pc); Np, Nc = step(tab, Np, Nc)
        d = (Pp ^ Np) | (Pc ^ Nc); y = np.flatnonzero(Pc ^ Nc)
        Y.append((tuple((y - y.min()).tolist()), int(y.min())) if y.size else ((), 0))
        objsP, _ = S1.objects(tab, Pp, Pc, V, TF)
        Yp.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objsP if d[x['span'][0]:x['span'][1] + 1].any())))
    return dict(O=O, G=G, typ=typ, Y=Y, Yp=Yp, RUN=RUN, run_capped=RUN == RUNCAP)


def cell(D, idx):
    O = [D['O'][i] for i in idx]; HI = math.log2(len(idx)); HO = H(O)
    only = HI - HO; fp = H(list(zip(O, [D['Y'][i] for i in idx]))) - HO
    ps = H(list(zip(O, [D['Yp'][i] for i in idx]))) - HO
    content = HI - H(list(zip(O, [D['G'][i] for i in idx])))
    ty = [D['typ'][i] for i in idx]
    reg = 'clean' if only < 1e-9 else 'full' if only - fp < 1e-9 else 'partial'
    return dict(n=len(idx), H_in=HI, only=only, footprint=fp, probe_state=ps, unrecovered=only - fp, content=content,
                content_share=content / only if only > 1e-9 else None, regime=reg,
                types={k: ty.count(k) for k in ('none', 'compact', 'extended')})


def job(a):
    S1.N = N
    w, Rs, Ls, ref, role = a; tab = table(w); R0, L0 = Rs[0], Ls[0]
    out = dict(wolfram=w, role=role, vR0=str(R0['v']), vL0=str(L0['v']))
    Vs = C2.vac_seq(tab, 600 + 1500 + C2.PMAX + 4)
    if ref is not None:
        D0 = core(tab, Vs, [(0, 0, off) for off in range(OFF0, OFF0 + 64)], Rs, Ls, R0, 600, RUN=1500); c0 = cell(D0, range(64))
        out['V0'] = bool(abs(c0['only'] - ref['only_shadow']) < 1e-12 and abs(c0['footprint'] - ref['footprint_beyond']) < 1e-12)
    else: out['V0'] = True
    if role == 'smoke': return out
    close = min(R['v'] - L['v'] for R in Rs for L in Ls); T = math.ceil(552 / close) + MARGIN
    A = [(0, 0, off) for off in range(OFF0, OFF0 + max(MS))]
    Cs = [(ri, li, off) for ri in range(len(Rs)) for li in range(len(Ls)) for off in range(OFF0, OFF0 + OFFC)]
    U = list(dict.fromkeys(A + Cs)); ix = {u: i for i, u in enumerate(U)}
    V = C2.vac_seq(tab, T + RUNCAP + C2.PMAX + STAT + 4); D = core(tab, V, U, Rs, Ls, R0, T)
    out.update(T=T, RUN=D['RUN'], run_capped=D['run_capped'], A={M: cell(D, [ix[u] for u in A[:M]]) for M in MS},
               C=cell(D, [ix[u] for u in Cs]))
    return out


def pairs():
    s3 = json.load(open(OM / 'MIR-REVERSIBLE-SHADOW-003/results.json'))['pairs']
    s4 = json.load(open(OM / 'MIR-REVERSIBLE-SHADOW-004/results.json'))['pairs']
    ph = json.load(open(OM / 'MIR-REVERSIBLE-SHADOW-004/posthoc_bubble_widths.json'))
    rules = {r['wolfram']: r for r in json.load(open(C2.CAT))['rules']}
    pat = lambda s: (tuple(SEEDS[s - 1][:5].tolist()), tuple(SEEDS[s - 1][5:].tolist()))
    def act(x, role):
        cat = C2.catalogue(rules[x['wolfram']]); R = [o for o in cat if o['v'] > 0][:2]; L = [o for o in cat if o['v'] < 0][:2]
        R = [o for o in R if o['seed'] == x['seedR']] + [o for o in R if o['seed'] != x['seedR']]
        L = [o for o in L if o['seed'] == x['seedL']] + [o for o in L if o['seed'] != x['seedL']]
        cv = lambda o: dict(seed=pat(o['seed']), v=o['v'])
        return (x['wolfram'], [cv(o) for o in R], [cv(o) for o in L], x if role == 'shadow' else None, role + '_active')
    def sil(x, role):
        rows = [y for y in s4 if y['wolfram'] == x['wolfram']]
        uniq = lambda k, vk, first: list(dict.fromkeys([first] + [y[k] for y in rows]))[:2]
        vmap = {y['seedR']: y['vR'] for y in rows} | {y['seedL']: y['vL'] for y in rows}
        cv = lambda s: dict(seed=ast.literal_eval(s), v=Fr(vmap[s]))
        return (x['wolfram'], [cv(s) for s in uniq('seedR', 'vR', x['seedR'])], [cv(s) for s in uniq('seedL', 'vL', x['seedL'])],
                x if role == 'shadow' else None, role + '_silent')
    jobs, seen = [], set()
    for x in s3:
        if x['shadow_runs'] > 0 and x['only_shadow'] > 1e-12 and x['wolfram'] not in seen:
            seen.add(x['wolfram']); jobs.append(act(x, 'shadow'))
    dirty4 = [x for x in s4 if x['shadow_runs'] > 0]; seen = set()
    for x, p in zip(dirty4, ph):
        if x['only_shadow'] > 1e-12 and p['minw'] >= 1000 and x['wolfram'] not in seen:
            seen.add(x['wolfram']); jobs.append(sil(x, 'shadow'))
    for w in (1, 5): jobs.append(act(next(x for x in s3 if x['wolfram'] == w and x['shadow_runs'] == 0), 'null'))
    n90 = [x for x in s4 if x['wolfram'] == 90 and x['shadow_runs'] == 0]
    if n90: jobs.append(sil(n90[0], 'null'))
    return jobs


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    jobs = pairs()
    if sys.argv[1:] == ['smoke']:
        for j in jobs:
            if j[0] == 37 or j[4] == 'shadow_silent':
                print('smoke', j[0], j[4], job(j[:4] + ('smoke',))['V0'], flush=True)
                if j[4] == 'shadow_silent': break
        print('pairs', [(j[0], j[4]) for j in jobs]); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(6) as ex: rows = list(ex.map(job, jobs))
    sh = [r for r in rows if r['role'].startswith('shadow') and r['A'][256]['only'] > 1e-9]
    gain = {f"{r['wolfram']}{r['role'][6]}": r['A'][512]['only'] - r['A'][256]['only'] for r in sh}
    share = {f"{r['wolfram']}{r['role'][6]}": r['A'][512]['content_share'] for r in sh}
    cells = [c for r in rows for c in list(r['A'].values()) + [r['C']]]
    k = math.ceil(2 * len(sh) / 3) if sh else None
    S = dict(V0_all=all(r['V0'] for r in rows),
             V1=all(c['footprint'] < 1e-9 and c['content'] < 1e-9 for c in cells if c['types']['none'] == c['n']),
             pairs=len(rows), shadow_pairs_eligible=len(sh), gain_512_vs_256=gain, content_share_512=share,
             n_log=sum(0.25 <= g <= 0.75 for g in gain.values()), n_sat=sum(g < 0.25 for g in gain.values()),
             n_full=sum(g > 0.75 for g in gain.values()),
             n_outline=sum(s < 0.05 for s in share.values()), n_content=sum(s >= 0.5 for s in share.values()),
             regimes={'A512': {g: sum(r['A'][512]['regime'] == g for r in rows if r['role'].startswith('shadow')) for g in ('clean', 'partial', 'full')},
                      'C': {g: sum(r['C']['regime'] == g for r in rows if r['role'].startswith('shadow')) for g in ('clean', 'partial', 'full')}},
             types_A512={t: sum(r['A'][512]['types'][t] for r in rows if r['role'].startswith('shadow')) for t in ('none', 'compact', 'extended')},
             all_compact_pairs=[f"{r['wolfram']}{r['role'][6]}" for r in rows if r['role'].startswith('shadow')
                                and r['A'][512]['types']['extended'] == 0 and r['A'][512]['types']['compact'] > 0],
             run_capped=[r['wolfram'] for r in rows if r['run_capped']])
    S['valid'] = S['V0_all'] and S['V1']
    v = lambda a, b, c, names: 'invalid' if not S['valid'] else 'n/a' if not sh else next((n for n, x in zip(names, (a, b, c)) if x >= k), 'mixed')
    S['H1'] = v(S['n_log'], S['n_sat'], S['n_full'], ('log', 'saturating', 'full_transfer'))
    S['H2'] = v(S['n_outline'], S['n_content'], -1, ('outline', 'content', '-'))
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps(S, default=str))


if __name__ == '__main__':
    main()
