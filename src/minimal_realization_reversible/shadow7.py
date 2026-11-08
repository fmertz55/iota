"""MIR-REVERSIBLE-SHADOW-007: alias-free species mixes; does a second reader from the other side complete the read?"""
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
import minimal_realization_reversible.shadow6 as S6
TAG = 'mir-reversible-shadow-007-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_SHADOW_007_CONTRACT.md', 'src/minimal_realization_reversible/shadow7.py',
          'src/minimal_realization_reversible/shadow6.py', 'src/minimal_realization_reversible/shadow3.py',
          'src/minimal_realization_reversible/shadow.py', 'src/minimal_realization_reversible/collide2.py',
          'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/shadow7_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-SHADOW-007'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, GAP, OFFS, RUN, KS = S6.N, S6.X0, 24, range(24, 88), 1500, 2
H = S3.H; place = S6.place


def species(tab, seed):
    V = C2.vac_seq(tab, C2.T + C2.PMAX + 4)
    p = np.zeros(C2.N, np.uint8); c = np.zeros(C2.N, np.uint8); pp, cc = seed
    p[C2.X0:C2.X0 + len(pp)] ^= np.array(pp, np.uint8); c[C2.X0:C2.X0 + len(cc)] ^= np.array(cc, np.uint8)
    r = C2.orbit(tab, p, c, 0, V); return r[2] if r else frozenset()


def dedupe(tab, cands):
    out = []
    for o in cands:
        sp = species(tab, o['seed'])
        if not any(sp & q['sp'] for q in out): out.append(dict(o, sp=sp))
        if len(out) == KS: break
    return out


def free(tab, seed, T, V):
    F = place([(seed, X0)])
    for _ in range(T): F = step(tab, *F)
    fd = np.flatnonzero((F[0] ^ V[T]) | (F[1] ^ V[T + 1])); return F, int(fd.min()) - 2, int(fd.max()) + 2


def core(tab, V, inputs, Rs, Ls, T, readers):
    st, O, left, right, res, seen, dropped = [], [], [], [], [], set(), 0
    for ri, li, off in inputs:
        U = place([(Rs[ri]['seed'], X0), (Ls[li]['seed'], X0 + off)]); key = U[0].tobytes() + U[1].tobytes()
        if key in seen: dropped += 1; continue
        seen.add(key)
        for _ in range(T): U = step(tab, *U)
        objs, resid = S1.objects(tab, *U, V, T); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[T]; c[a - 2:b + 3] = V[T + 1]
        st.append((p, c)); O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs)))
        L_ = [a for a, _ in resid] + [x['span'][0] for x in objs]; R_ = [b for _, b in resid] + [x['span'][1] for x in objs]
        left.append(min(L_) if L_ else X0); right.append(max(R_) if R_ else X0)
        res.append(bool(((p ^ V[T]) | (c ^ V[T + 1])).any()))
    rd = {}
    if 'a' in readers:
        F, fa, fb = free(tab, Rs[0]['seed'], T, V); rd['a'] = (F, fa, fb, min(left) - GAP - (fb - fa + 1))
    if 'b' in readers:
        F, fa, fb = free(tab, Ls[0]['seed'], T, V); rd['b'] = (F, fa, fb, max(right) + GAP)
    Y = {k: [] for k in rd}
    for p, c in st:
        Np, Nc = p, c
        for _ in range(RUN): Np, Nc = step(tab, Np, Nc)
        for k, (F, fa, fb, L0) in rd.items():
            Pp, Pc = p.copy(), c.copy(); Pp[L0:L0 + fb - fa + 1] = F[0][fa:fb + 1]; Pc[L0:L0 + fb - fa + 1] = F[1][fa:fb + 1]
            for _ in range(RUN): Pp, Pc = step(tab, Pp, Pc)
            y = np.flatnonzero(Pc ^ Nc); Y[k].append((tuple((y - y.min()).tolist()), int(y.min())) if y.size else ((), 0))
    return dict(O=O, Y=Y, res=res, dropped=dropped)


def cell(D):
    O = D['O']; n = len(O); HI = math.log2(n); HO = H(O); only = HI - HO
    f = {k: H(list(zip(O, v))) - HO for k, v in D['Y'].items()}
    out = dict(n=n, dropped=D['dropped'], only=only, residue_runs=sum(D['res']), **{f'footprint_{k}': v for k, v in f.items()},
               **{f'unrecovered_{k}': only - v for k, v in f.items()})
    if len(D['Y']) == 2:
        out['joint'] = H(list(zip(O, D['Y']['a'], D['Y']['b']))) - HO; out['unrecovered_joint'] = only - out['joint']
    return out


def lists(j):
    w, Rs6, Ls6, ref, role = j; tab = table(w)
    if role.endswith('active'):
        rr = next(r for r in json.load(open(C2.CAT))['rules'] if r['wolfram'] == w); cat = C2.catalogue(rr)
        pat = lambda s: (tuple(SEEDS[s - 1][:5].tolist()), tuple(SEEDS[s - 1][5:].tolist()))
        Rc = [dict(seed=pat(o['seed']), v=o['v']) for o in cat if o['v'] > 0]; Lc = [dict(seed=pat(o['seed']), v=o['v']) for o in cat if o['v'] < 0]
    else:
        rows = [y for y in json.load(open(OM / 'MIR-REVERSIBLE-SHADOW-004/results.json'))['pairs'] if y['wolfram'] == w]
        Rc = [dict(seed=ast.literal_eval(s), v=Fr(v)) for s, v in dict.fromkeys((y['seedR'], y['vR']) for y in rows)]
        Lc = [dict(seed=ast.literal_eval(s), v=Fr(v)) for s, v in dict.fromkeys((y['seedL'], y['vL']) for y in rows)]
    first = lambda c, s: [o for o in c if o['seed'] == s] + [o for o in c if o['seed'] != s]
    return tab, dedupe(tab, first(Rc, Rs6[0]['seed'])), dedupe(tab, first(Lc, Ls6[0]['seed']))


def job(j, smoke=False):
    S1.N = N
    w, Rs6, Ls6, ref, role = j; tab, Rs, Ls = lists(j)
    out = dict(wolfram=w, role=role, nR=len(Rs), nL=len(Ls))
    if ref is not None:
        Vs = C2.vac_seq(tab, 600 + RUN + C2.PMAX + 4)
        c0 = cell(core(tab, Vs, [(0, 0, o) for o in OFFS], Rs, Ls, 600, ('a',)))
        out['V0'] = bool(abs(c0['only'] - ref['only_shadow']) < 1e-12 and abs(c0['footprint_a'] - ref['footprint_beyond']) < 1e-12)
    else: out['V0'] = True
    if smoke: return out
    close = min(R['v'] - L['v'] for R in Rs for L in Ls); T = math.ceil(552 / close) + 300
    V = C2.vac_seq(tab, T + RUN + C2.PMAX + 4)
    out.update(T=T, C=cell(core(tab, V, [(ri, li, o) for ri in range(len(Rs)) for li in range(len(Ls)) for o in OFFS], Rs, Ls, T, ('a', 'b'))))
    return out


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    jobs = S6.pairs()
    if sys.argv[1:] == ['smoke']:
        for j in jobs:
            if j[0] in (37, 22): print('smoke', j[0], job(j, smoke=True)['V0'], flush=True)
        return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(6) as ex: rows = list(ex.map(job, jobs))
    sh = [r for r in rows if r['role'].startswith('shadow') and r['C']['only'] > 1e-9]
    pa = [r for r in sh if r['C']['unrecovered_a'] > 1e-9]
    S = dict(V0_all=all(r['V0'] for r in rows),
             V1=all(r['C']['only'] < 1e-9 and r['C']['footprint_a'] < 1e-9 and r['C']['footprint_b'] < 1e-9 for r in rows if r['C']['residue_runs'] == 0),
             pairs=len(rows), shadow_pairs=len(sh), dropped_total=sum(r['C']['dropped'] for r in rows),
             species_counts={f"{r['wolfram']}{r['role'][7]}": (r['nR'], r['nL']) for r in rows},
             partial_a=[f"{r['wolfram']}{r['role'][7]}" for r in pa],
             partial_b=[f"{r['wolfram']}{r['role'][7]}" for r in sh if r['C']['unrecovered_b'] > 1e-9],
             joint_complete_among_partial_a=[f"{r['wolfram']}{r['role'][7]}" for r in pa if r['C']['unrecovered_joint'] < 1e-9],
             partial_both_full_joint=[f"{r['wolfram']}{r['role'][7]}" for r in sh if r['C']['unrecovered_a'] > 1e-9
                                      and r['C']['unrecovered_b'] > 1e-9 and r['C']['unrecovered_joint'] < 1e-9],
             unrecovered={f"{r['wolfram']}{r['role'][7]}": [round(r['C'][k], 3) for k in ('only', 'unrecovered_a', 'unrecovered_b', 'unrecovered_joint')] for r in sh})
    S['valid'] = S['V0_all'] and S['V1']
    S['H_P'] = 'invalid' if not S['valid'] else 'supported' if len(pa) >= math.ceil(len(sh) / 3) else 'not_supported'
    S['H_J'] = 'invalid' if not S['valid'] else 'n/a' if not pa else ('supported' if len(S['joint_complete_among_partial_a']) >= math.ceil(2 * len(pa) / 3) else 'not_supported')
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'H_P', 'H_J', 'shadow_pairs', 'dropped_total')}))


if __name__ == '__main__':
    main()
