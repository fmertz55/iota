"""MIR-REVERSIBLE-BREAK-001: does order memory (and its background share) rise as dynamics move away from integrability?
Rules: 250 (RCA54) and all 1-bit and 2-bit table neighbours. Species: SPECIES-001 acceptance (active vacuum: sub-light
drift filter). ORDER-002 machinery unchanged (order2.case/summary). 150 sampled cases per side, seed [20261118, w, side+1].
Elasticity e(w): fraction of single-reader (X + alpha, slot 1) worlds whose movers at Delta + 1600 are exactly {X, alpha}
with no background (pooled over both sides). See docs/ICP_MIR_REVERSIBLE_BREAK_001_CONTRACT.md."""
import hashlib, json, os, subprocess, sys
os.environ.setdefault('OMP_NUM_THREADS', '1')
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction as Fr
from itertools import combinations
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'src'))
import minimal_realization_reversible.order2 as O2
import minimal_realization_reversible.species1 as SPc
from minimal_realization_reversible.vacuum_collide import table
from minimal_realization_reversible import collide2 as C2
TAG = 'mir-reversible-break-001-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_BREAK_001_CONTRACT.md'] + ['src/minimal_realization_reversible/' + f for f in ('break1.py', 'order2.py', 'species1.py', 'inventory1.py', 'collide2.py', 'vacuum_collide.py')]
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/break1_seal.json'; OUT = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-BREAK-001'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
RULES = [250] + [250 ^ (1 << k) for k in range(8)] + [250 ^ (1 << a) ^ (1 << b) for a, b in combinations(range(8), 2)]
N = 150


def species(w):
    tab = table(w); pv = SPc.vac_period(tab); sp = {}
    for k in range(pv):
        orb = {}
        for s, dft, pat in SPc.accept(tab, k):
            if pv > 1 and not (2 < abs(dft) < 116): continue
            if pat not in orb: orb[pat] = SPc.orbit_of(tab, pat, k + SPc.TS)
            r = orb[pat]
            if r is None or r[1] == 0 or abs(Fr(r[1], r[0])) < C2.VMIN: continue
            i = SPc.sid(r[2]); wd = SPc.seed_width(s)
            if i not in sp or (wd, k, s) < (sp[i]['width'], sp[i]['phase'], sp[i]['seed']):
                sp[i] = dict(id=i, v=str(Fr(r[1], r[0])), P=r[0], width=wd, phase=k, seed=s)
    return sorted(sp.values(), key=lambda x: (x['width'], x['phase'], x['seed']))


def job(a):
    w, side = a; sp = species(w); out = dict(w=w, side=side, nsp=len(sp))
    R = O2.Rule(w, sp); G, pairs = O2.grid(R, side)
    if not pairs or len(G) == 0: return dict(out, testable=False)
    by = {o['id']: o for o in R.sp}; rng = np.random.default_rng([20261118, w, side + 1]); rows = []; el = []
    for gi in sorted(rng.choice(len(G), size=min(N, len(G)), replace=False)):
        X, pi, tau, d, De = G[gi]; al, be = pairs[pi]; Xo = by[X]
        x = O2.case(R, Xo, tau, al, be, d, De, side, slot_check=len(rows) < 10); rows.append(x)
        try:
            p, c = O2.run(R, *O2.world(R, [(Xo, tau, O2.X0), (al, al['phase'], O2.X0 - side * d)]), De + O2.RT[0])
            mv, bg, _ = O2.readout(R, p, c, De + O2.RT[0])
            el.append(sorted(mv) == sorted([(X, 1 if Xo['v'] > 0 else -1), (al['id'], 1 if Fr(al['v']) > 0 else -1)]) and not bg)
        except ValueError: pass
    s = O2.summary(rows)
    return dict(out, testable=True, valid=s['valid'], touched=s['touched'], slot_fail=s['slot_fail'], order=s['bits_order'],
                bg=s['bits_bg'], mov=s['bits_mov'], bg_only=s['bits_bg_only'], n_el=len(el), elastic=sum(el))


def main():
    if sys.argv[1:] == ['seal']: SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    CK = OUT / 'jobs'; CK.mkdir(parents=True, exist_ok=True)
    J = [(w, s) for w in RULES for s in (1, -1)]; todo = [j for j in J if not (CK / f'{j[0]}_{j[1]}.json').exists()]
    with ProcessPoolExecutor(4) as ex:
        for j, r in zip(todo, ex.map(job, todo)): (CK / f'{j[0]}_{j[1]}.json').write_text(json.dumps(r))
    res = [json.loads((CK / f'{w}_{s}.json').read_text()) for w, s in J]
    by = {}
    for r in res:
        if r.get('testable') and r['touched']: by.setdefault(r['w'], []).append(r)
    T = {}
    for w, rs in by.items():
        t = sum(r['touched'] for r in rs); ne = sum(r['n_el'] for r in rs)
        T[w] = dict(dist=bin(w ^ 250).count('1'), touched=t, order=sum(r['order'] * r['touched'] for r in rs) / t,
                    bg=sum(r['bg'] * r['touched'] for r in rs) / t, bg_only=sum(r['bg_only'] * r['touched'] for r in rs) / t,
                    elastic=sum(r['elastic'] for r in rs) / ne if ne else None)
    from scipy.stats import spearmanr
    br = [w for w in T if w != 250 and T[w]['elastic'] is not None]
    rho, p = spearmanr([T[w]['elastic'] for w in br], [T[w]['order'] for w in br]) if len(br) >= 5 else (None, None)
    S = dict(V_slot=all(r.get('slot_fail', 0) == 0 for r in res), V_C=250 in T and T[250]['order'] == 0 and T[250]['bg'] == 0,
             n_testable=len(br), rho=rho, p=p, H_B_n=sum(T[w]['bg'] > 0 for w in br))
    S['valid'] = S['V_slot'] and S['V_C'] and len(br) >= 10
    S['H_L'] = 'invalid' if not S['valid'] else 'supported' if rho is not None and rho <= -0.5 and p < 0.01 else 'not_supported'
    S['H_O'] = 'invalid' if not S['valid'] else 'supported' if all(T[w]['order'] > 0 for w in br if T[w]['elastic'] is not None and T[w]['elastic'] < 1) else 'not_supported'
    S['H_B'] = 'invalid' if not S['valid'] else 'supported' if S['H_B_n'] >= 2 * len(br) / 3 else 'not_supported'
    S['table'] = T
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, jobs=res), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V_slot', 'V_C', 'n_testable', 'rho', 'p', 'H_L', 'H_O', 'H_B', 'H_B_n')}, default=str))


if __name__ == '__main__': main()
