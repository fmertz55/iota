"""MIR-REVERSIBLE-LEDGER-001: where does collision information go?"""
import hashlib, json, math, subprocess, sys
from collections import Counter
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import table, step, SEEDS, clusters
from minimal_realization_reversible import collide2 as C2
TAG = 'mir-reversible-ledger-001-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_LEDGER_CONTRACT.md', 'src/minimal_realization_reversible/ledger.py',
          'src/minimal_realization_reversible/collide2.py', 'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/ledger_seal.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, T, X0, OFFS = 2048, 600, 600, range(24, 88)   # 64 inputs per rule


def run(w, R, L, off):
    tab = table(w); V = C2.vac_seq(tab, T + C2.PMAX + 4)
    p = np.zeros(N, np.uint8); c = np.zeros(N, np.uint8)
    for s, x in [(R['seed'], X0), (L['seed'], X0 + off)]:
        b = SEEDS[s - 1]; p[x:x + 5] ^= b[:5]; c[x:x + 5] ^= b[5:]
    for _ in range(T): p, c = step(tab, p, c)
    d = c ^ V[T + 1]; objs, residue = [], 0
    for a, b in clusters(d):
        if b - a + 1 > 8: residue += b - a + 1; continue
        win = np.zeros(N, bool); win[a - 2:b + 3] = True
        cp = np.where(win, p, V[T]).astype(np.uint8); cc = np.where(win, c, V[T + 1]).astype(np.uint8)
        r = C2.orbit(tab, cp, cc, T, V)
        if r is None: residue += b - a + 1; continue
        dp, dc = cp ^ V[T], cc ^ V[T + 1]
        state = tuple(sorted([(int(i - a), 0) for i in np.flatnonzero(dp)] + [(int(i - a), 1) for i in np.flatnonzero(dc)]))
        sid = min(hash(x) for x in r[2])            # species id: orbit-invariant
        objs.append(dict(species=sid, state=state, pos=int(a)))
    return objs, residue, bool(d.any())


def H_cond(keys):
    n = len(keys); cnt = Counter(keys)
    return sum(m / n * math.log2(m) for m in cnt.values())


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    rules = json.load(open(C2.CAT))['rules']; out = []
    for rr in rules:
        cat = C2.catalogue(rr); Rs = [o for o in cat if o['v'] > 0]; Ls = [o for o in cat if o['v'] < 0]
        if not (Rs and Ls): continue
        res = [run(rr['wolfram'], Rs[0], Ls[0], off) for off in OFFS]
        full = [tuple(sorted((o['species'], o['state'], o['pos']) for o in objs)) for objs, _, _ in res]
        internal = [tuple(sorted((o['species'], o['state']) for o in objs)) for objs, _, _ in res]
        species = [tuple(sorted(o['species'] for o in objs)) for objs, _, _ in res]
        HI = math.log2(len(OFFS))
        f = lambda keys: (HI - H_cond(keys)) / HI
        out.append(dict(wolfram=rr['wolfram'], active_vacuum=rr['active_vacuum'],
                        any_residue=sum(r > 0 for _, r, _ in res), annihilated=sum(not a for _, _, a in res),
                        f_objects=f(full), f_internal=f(internal), f_species=f(species)))
    clean = [x for x in out if x['any_residue'] == 0]; dirty = [x for x in out if x['any_residue'] > 0]
    S = dict(rules=len(out), clean_rules=len(clean), residue_rules=len(dirty),
             annihilated=sum(x['annihilated'] for x in out),
             H_I1_complete_carriers=('supported' if clean and all(x['f_objects'] == 1 for x in clean) else 'falsified' if clean else 'no_clean_rules'),
             H_I2_residue_holds_information=('supported' if dirty and all(x['f_objects'] < 1 for x in dirty) else 'falsified' if dirty else 'no_residue_rules'),
             clean_f_internal=[round(x['f_internal'], 3) for x in clean],
             clean_f_species=[round(x['f_species'], 3) for x in clean],
             residue_f_objects=[round(x['f_objects'], 3) for x in dirty])
    dst = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-LEDGER-001/results.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(dict(summary=S, rules=out), indent=1) + '\n')
    print(json.dumps(S))

if __name__ == '__main__':
    main()
