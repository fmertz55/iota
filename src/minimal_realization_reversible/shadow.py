"""MIR-REVERSIBLE-SHADOW-001: (A) ledger re-run with corrected object extraction;
(B) does the collision shadow, with its carriers erased, constrain a later coherence's future?"""
import hashlib, json, math, subprocess, sys
from collections import Counter
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import table, step, SEEDS
from minimal_realization_reversible import collide2 as C2
TAG = 'mir-reversible-shadow-001-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_SHADOW_CONTRACT.md', 'src/minimal_realization_reversible/shadow.py',
          'src/minimal_realization_reversible/collide2.py', 'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/shadow_seal.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, OFFS, T, DP, TF = 2048, 900, range(24, 88), 600, 64, 1400


def ucl(p, c, V, t):
    """Clusters (gap < 3) of the union of both layers' vacuum differences at layer t."""
    on = np.flatnonzero((p ^ V[t]) | (c ^ V[t + 1])); out = []
    for i in on:
        if out and i - out[-1][1] - 1 < 3: out[-1][1] = int(i)
        else: out.append([int(i), int(i)])
    return out


def objects(tab, p, c, V, t):
    objs, resid = [], []
    for a, b in ucl(p, c, V, t):
        if b - a + 1 > 8: resid.append((a, b)); continue
        win = np.zeros(N, bool); win[a - 2:b + 3] = True
        cp = np.where(win, p, V[t]).astype(np.uint8); cc = np.where(win, c, V[t + 1]).astype(np.uint8)
        r = C2.orbit(tab, cp, cc, t, V)
        if r is None: resid.append((a, b)); continue
        st = tuple(sorted([(int(i - a), 0) for i in np.flatnonzero(cp ^ V[t])] + [(int(i - a), 1) for i in np.flatnonzero(cc ^ V[t + 1])]))
        objs.append(dict(species=min(hash(x) for x in r[2]), state=st, pos=a, span=(a, b)))
    return objs, resid


def place(seeds):
    p = np.zeros(N, np.uint8); c = np.zeros(N, np.uint8)
    for s, x in seeds:
        b = SEEDS[s - 1]; p[x:x + 5] ^= b[:5]; c[x:x + 5] ^= b[5:]
    return p, c


def Hc(keys):
    n = len(keys); return sum(m / n * math.log2(m) for m in Counter(keys).values())


def ledger(w, R, L):
    tab = table(w); V = C2.vac_seq(tab, T + C2.PMAX + 4); full, inter, resid = [], [], 0
    for off in OFFS:
        p, c = place([(R['seed'], X0), (L['seed'], X0 + off)])
        for _ in range(T): p, c = step(tab, p, c)
        o, r = objects(tab, p, c, V, T); resid += bool(r)
        full.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in o)))
        inter.append(tuple(sorted((x['species'], x['state']) for x in o)))
    HI = math.log2(len(OFFS))
    return dict(residue_runs=resid, f_objects=(HI - Hc(full)) / HI, f_internal=(HI - Hc(inter)) / HI)


def shadow(w, R, L):
    """Probe = a second copy of R, trailing R by DP sites. After contact + 24 ticks, erase every
    resolved carrier except the probe; keep residue. Y = final difference between the universes
    with and without the probe (the probe's own footprint on the future)."""
    tab = table(w); V = C2.vac_seq(tab, 4000); Ys, valid = [], 0
    for off in OFFS:
        U = {'P': place([(R['seed'], X0 - DP), (R['seed'], X0), (L['seed'], X0 + off)]),
             'N': place([(R['seed'], X0), (L['seed'], X0 + off)])}
        fr = place([(R['seed'], X0)]); fl = place([(L['seed'], X0 + off)]); t = 0; tc = None
        while tc is None and t < 2000:
            r = np.flatnonzero(fr[1] ^ V[t + 1]); l = np.flatnonzero(fl[1] ^ V[t + 1])
            if l.min() - r.max() <= 3: tc = t
            U = {k: step(tab, *v) for k, v in U.items()}; fr = step(tab, *fr); fl = step(tab, *fl); t += 1
        for _ in range(24): U = {k: step(tab, *v) for k, v in U.items()}; t += 1
        oN, _ = objects(tab, *U['N'], V, t); oP, _ = objects(tab, *U['P'], V, t)
        # probe = the leftmost object present in P but not in N
        spansN = {tuple(x['span']) for x in oN}
        cand = [x for x in oP if tuple(x['span']) not in spansN]
        if not cand: Ys.append(None); continue
        probe = min(cand, key=lambda x: x['span'][0])
        ok = all(abs(probe['span'][0] - x['span'][1]) > 3 and abs(x['span'][0] - probe['span'][1]) > 3 for x in oN)
        for k, objs in (('N', oN), ('P', oP)):
            p, c = U[k]; p = p.copy(); c = c.copy()
            for x in objs:
                if k == 'P' and x is probe: continue
                a, b = x['span']; p[a - 2:b + 3] = V[t]; c[a - 2:b + 3] = V[t + 1]
            U[k] = (p, c)
        resid_left = bool(((U['N'][0] ^ V[t]) | (U['N'][1] ^ V[t + 1])).any())
        while t < TF: U = {k: step(tab, *v) for k, v in U.items()}; t += 1
        if not ok: Ys.append(None); continue
        valid += 1
        Y = np.flatnonzero(U['P'][1] ^ U['N'][1]); Ys.append((tuple((Y - Y.min()).tolist()) if Y.size else (), int(Y.min()) if Y.size else 0, resid_left))
    vals = [y for y in Ys if y is not None]
    if len(vals) < 2: return dict(valid=len(vals), I_bits=None)
    I = math.log2(len(vals)) - Hc([y[:2] for y in vals])
    return dict(valid=len(vals), I_bits=I, H_max=math.log2(len(vals)), shadow_present=sum(y[2] for y in vals))


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    out = []
    for rr in json.load(open(C2.CAT))['rules']:
        cat = C2.catalogue(rr); Rs = [o for o in cat if o['v'] > 0]; Ls = [o for o in cat if o['v'] < 0]
        if not (Rs and Ls): continue
        out.append(dict(wolfram=rr['wolfram'], active_vacuum=rr['active_vacuum'],
                        ledger=ledger(rr['wolfram'], Rs[0], Ls[0]), shadow=shadow(rr['wolfram'], Rs[0], Ls[0])))
        print(rr['wolfram'], json.dumps(out[-1]['ledger']), json.dumps(out[-1]['shadow']), flush=True)
    clean = [x for x in out if x['ledger']['residue_runs'] == 0]; dirty = [x for x in out if x['ledger']['residue_runs'] > 0]
    ctrl = [x['shadow']['I_bits'] for x in clean if x['shadow']['I_bits'] is not None]
    test = [x for x in dirty if x['shadow']['I_bits'] is not None]
    S = dict(rules=len(out), clean=len(clean), residue=len(dirty),
             control_clean_I_all_zero=all(abs(i) < 1e-12 for i in ctrl) if ctrl else None,
             shadow_rules_I_positive=sum(x['shadow']['I_bits'] > 1e-12 for x in test), shadow_rules_tested=len(test),
             shadow_I_bits={x['wolfram']: round(x['shadow']['I_bits'], 3) for x in test})
    S['verdict'] = ('invalid_control' if S['control_clean_I_all_zero'] is False else
                    'shadow_constrains_future' if S['shadow_rules_I_positive'] >= 1 else 'no_shadow_effect')
    dst = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-SHADOW-001/results.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(dict(summary=S, rules=out), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)) + '\n')
    print(json.dumps(S, default=str))

if __name__ == '__main__':
    main()
