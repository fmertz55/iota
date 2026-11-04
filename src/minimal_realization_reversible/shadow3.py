"""MIR-REVERSIBLE-SHADOW-003: does the probe coherence itself carry the shadow's record out?
And is the SHADOW-002 result robust across collision pairs?"""
import hashlib, json, math, subprocess, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import table, step, SEEDS
from minimal_realization_reversible import collide2 as C2
import minimal_realization_reversible.shadow as S1
TAG = 'mir-reversible-shadow-003-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_SHADOW_003_CONTRACT.md', 'src/minimal_realization_reversible/shadow3.py',
          'src/minimal_realization_reversible/shadow.py', 'src/minimal_realization_reversible/collide2.py',
          'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/shadow3_seal.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, OFFS, T, RUN, GAP, KMAX = 8192, 4096, range(24, 88), 600, 1500, 24, 2
S1.N = N
from collections import Counter
H = lambda keys: -sum(m / len(keys) * math.log2(m / len(keys)) for m in Counter(keys).values())


def place(seeds):
    p = np.zeros(N, np.uint8); c = np.zeros(N, np.uint8)
    for s, x in seeds:
        b = SEEDS[s - 1]; p[x:x + 5] ^= b[:5]; c[x:x + 5] ^= b[5:]
    return p, c


def pair(w, R, L):
    tab = table(w); V = C2.vac_seq(tab, T + RUN + C2.PMAX + 4)
    F = place([(R['seed'], X0)])
    for _ in range(T): F = step(tab, *F)
    fd = np.flatnonzero((F[0] ^ V[T]) | (F[1] ^ V[T + 1])); fa, fb = int(fd.min()) - 2, int(fd.max()) + 2
    states, O, left = [], [], []
    for off in OFFS:
        U = place([(R['seed'], X0), (L['seed'], X0 + off)])
        for _ in range(T): U = step(tab, *U)
        objs, resid = S1.objects(tab, *U, V, T)
        p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[T]; c[a - 2:b + 3] = V[T + 1]
        states.append((p, c)); O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs)))
        left.append(min([a for a, _ in resid] + [x['span'][0] for x in objs]))
    launch = min(left) - GAP - (fb - fa + 1)
    Rsp = min(hash(x) for x in R['species'])
    Y, Yp, surv, shadow_runs = [], [], 0, 0
    TF = T + RUN
    for (p, c) in states:
        shadow_runs += bool(((p ^ V[T]) | (c ^ V[T + 1])).any())
        Pp, Pc = p.copy(), c.copy(); Np, Nc = p, c
        Pp[launch:launch + fb - fa + 1] = F[0][fa:fb + 1]; Pc[launch:launch + fb - fa + 1] = F[1][fa:fb + 1]
        for _ in range(RUN): Pp, Pc = step(tab, Pp, Pc); Np, Nc = step(tab, Np, Nc)
        d = (Pp ^ Np) | (Pc ^ Nc); y = np.flatnonzero(Pc ^ Nc)
        Y.append((tuple((y - y.min()).tolist()), int(y.min())) if y.size else ((), 0))
        objsP, _ = S1.objects(tab, Pp, Pc, V, TF)
        mine = [x for x in objsP if d[x['span'][0]:x['span'][1] + 1].any()]   # coherences the probe's passage created or altered
        Yp.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in mine)))
        surv += any(x['species'] == Rsp for x in mine)
    HI = math.log2(len(OFFS)); only = HI - H(O)
    cond = lambda Z: H(list(zip(O, Z))) - H(O)
    return dict(shadow_runs=shadow_runs, only_shadow=only, footprint_beyond=cond(Y), probe_state_beyond=cond(Yp),
                footprint_ratio=cond(Y) / only if only > 1e-12 else None,
                probe_state_ratio=cond(Yp) / only if only > 1e-12 else None,
                probe_R_species_survives=surv)


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    out = []
    for rr in json.load(open(C2.CAT))['rules']:
        cat = C2.catalogue(rr); Rs = [o for o in cat if o['v'] > 0][:KMAX]; Ls = [o for o in cat if o['v'] < 0][:KMAX]
        for R in Rs:
            for L in Ls:
                r = pair(rr['wolfram'], R, L); r.update(wolfram=rr['wolfram'], seedR=R['seed'], seedL=L['seed'], vR=str(R['v']), vL=str(L['v']))
                out.append(r); print(json.dumps(r), flush=True)
    clean = [x for x in out if x['shadow_runs'] == 0]; dirty = [x for x in out if x['shadow_runs'] > 0 and x['only_shadow'] > 1e-12]
    S = dict(pairs=len(out), rules=len({x['wolfram'] for x in out}), clean_pairs=len(clean), shadow_pairs=len(dirty),
             shadow_rules=len({x['wolfram'] for x in dirty}),
             control_clean_all_zero=all(x['footprint_beyond'] < 1e-12 and x['probe_state_beyond'] < 1e-12 for x in clean),
             footprint_ratio_1=sum(abs(x['footprint_ratio'] - 1) < 1e-9 for x in dirty),
             footprint_positive=sum(x['footprint_ratio'] > 1e-12 for x in dirty),
             probe_state_positive=sum(x['probe_state_ratio'] > 1e-12 for x in dirty),
             probe_state_ratio_1=sum(abs(x['probe_state_ratio'] - 1) < 1e-9 for x in dirty),
             probe_state_ratio_median=float(np.median([x['probe_state_ratio'] for x in dirty])) if dirty else None)
    S['H_R_robust'] = 'invalid_control' if not S['control_clean_all_zero'] else ('supported' if S['footprint_ratio_1'] >= 0.9 * len(dirty) else 'not_supported')
    S['H_P_probe_carries'] = 'supported' if S['probe_state_positive'] >= math.ceil(len(dirty) / 2) else 'not_supported'
    dst = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-SHADOW-003/results.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(dict(summary=S, pairs=out), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)) + '\n')
    print(json.dumps(S, default=str))

if __name__ == '__main__':
    main()
