"""MIR-REVERSIBLE-SHADOW-002: launched-probe shadow test for all residue rules + capacity."""
import hashlib, json, math, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import table, step, SEEDS
from minimal_realization_reversible import collide2 as C2
import minimal_realization_reversible.shadow as S1
TAG = 'mir-reversible-shadow-002-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_SHADOW_002_CONTRACT.md', 'src/minimal_realization_reversible/shadow2.py',
          'src/minimal_realization_reversible/shadow.py', 'src/minimal_realization_reversible/collide2.py',
          'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/shadow2_seal.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, OFFS, T, RUN, GAP = 16384, 8192, range(24, 88), 600, 1500, 24
S1.N = N  # shared helpers use the module ring size


def place(seeds):
    p = np.zeros(N, np.uint8); c = np.zeros(N, np.uint8)
    for s, x in seeds:
        b = SEEDS[s - 1]; p[x:x + 5] ^= b[:5]; c[x:x + 5] ^= b[5:]
    return p, c


def H(keys):  # exact entropy of the uniform input ensemble pushed through `keys`
    n = len(keys); return -sum(m / n * math.log2(m / n) for m in Counter(keys).values())


def rule(w, R, L):
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
    launch = min(left) - GAP - (fb - fa + 1)       # fixed launch site, outside every shadow
    Y = []; shadow_runs = 0
    for (p, c) in states:
        shadow_runs += bool(((p ^ V[T]) | (c ^ V[T + 1])).any())
        Pp, Pc = p.copy(), c.copy(); Np, Nc = p, c
        Pp[launch:launch + fb - fa + 1] = F[0][fa:fb + 1]; Pc[launch:launch + fb - fa + 1] = F[1][fa:fb + 1]
        for _ in range(RUN): Pp, Pc = step(tab, Pp, Pc); Np, Nc = step(tab, Np, Nc)
        y = np.flatnonzero(Pc ^ Nc); Y.append((tuple((y - y.min()).tolist()), int(y.min())) if y.size else ((), 0))
    HI = math.log2(len(OFFS))  # I(I;X) = H(X) for a deterministic map of a uniform input
    I_O = H(O); I_Y = H(Y); H_I_given_O = HI - I_O
    I_Y_given_O = H(list(zip(O, Y))) - H(O)        # I(I;Y|O) = H(O,Y) - H(O) (deterministic)
    return dict(shadow_runs=shadow_runs, launch_dist=int(X0 - launch), I_objects=I_O, shadow_only_bits=H_I_given_O,
                I_probe=I_Y, I_probe_given_objects=I_Y_given_O,
                capacity_ratio=(I_Y_given_O / H_I_given_O) if H_I_given_O > 1e-12 else None)


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    out = []
    for rr in json.load(open(C2.CAT))['rules']:
        cat = C2.catalogue(rr); Rs = [o for o in cat if o['v'] > 0]; Ls = [o for o in cat if o['v'] < 0]
        if not (Rs and Ls): continue
        r = rule(rr['wolfram'], Rs[0], Ls[0]); r['wolfram'] = rr['wolfram']; out.append(r)
        print(json.dumps(r), flush=True)
    clean = [x for x in out if x['shadow_runs'] == 0]; dirty = [x for x in out if x['shadow_runs'] > 0]
    S = dict(rules=len(out), clean=len(clean), shadow_rules=len(dirty),
             control_clean_all_zero=all(abs(x['I_probe']) < 1e-12 for x in clean),
             shadow_effect_rules=sum(x['I_probe'] > 1e-12 for x in dirty),
             capacity_positive_rules=sum((x['capacity_ratio'] or 0) > 1e-12 for x in dirty),
             per_rule={x['wolfram']: dict(only_shadow=round(x['shadow_only_bits'], 3), probe=round(x['I_probe'], 3),
                                          probe_beyond_objects=round(x['I_probe_given_objects'], 3),
                                          ratio=None if x['capacity_ratio'] is None else round(x['capacity_ratio'], 3)) for x in dirty})
    S['H_S_typical'] = ('invalid_control' if not S['control_clean_all_zero'] else
                        'typical' if S['shadow_effect_rules'] >= math.ceil(len(dirty) / 2) else 'exception')
    S['H_C_capacity'] = ('supported' if S['capacity_positive_rules'] >= math.ceil(len(dirty) / 2) else 'not_supported')
    dst = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-SHADOW-002/results.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(dict(summary=S, rules=out), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)) + '\n')
    print(json.dumps(S, default=str))

if __name__ == '__main__':
    main()
