"""MIR-REVERSIBLE-COLLIDE-002: exact-species collision test and vacuum-bubble test."""
import hashlib, json, subprocess, sys
from fractions import Fraction as Fr
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import table, step, SEEDS, clusters
TAG = 'mir-reversible-collide-002-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_COLLIDE_002_CONTRACT.md', 'src/minimal_realization_reversible/collide2.py',
          'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/collide2_seal.json'
CAT = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-VACUUM-COLLIDE-001/results.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, T, PMAX, X0, OFFS, VMIN, BUB = 1024, 400, 240, 400, range(24, 32), Fr(1, 8), 32


def vac_seq(tab, n):  # vac[k] = homogeneous vacuum value at layer k-1 (vac[0] = layer -1)
    v = [0, 0]
    while len(v) < n + 2:
        a, b = v[-2], v[-1]; v.append(int(tab[7 * b]) ^ a)
    return v


def orbit(tab, p, c, t0, V):
    """Exact period/shift of an isolated pattern (both layers) starting at layer t0.
    Returns (period, shift, species set) or None."""
    def key(p, c, t):
        dp, dc = p ^ V[t], c ^ V[t + 1]
        on = [(i, 0) for i in np.flatnonzero(dp)] + [(i, 1) for i in np.flatnonzero(dc)]
        if not on: return None, None
        m = min(i for i, _ in on)
        return (V[t], V[t + 1], tuple(sorted((i - m, l) for i, l in on))), m
    k0, m0 = key(p, c, t0); seen = {k0}
    if k0 is None: return None
    for k in range(1, PMAX + 1):
        p, c = step(tab, p, c)
        kk, m = key(p, c, t0 + k)
        if kk is None: return None
        if kk == k0: return k, int(m - m0), frozenset(seen)
        seen.add(kk)
    return None


def place(seeds):
    p = np.zeros(N, np.uint8); c = np.zeros(N, np.uint8)
    for s, x in seeds:
        b = SEEDS[s - 1]; p[x:x + 5] ^= b[:5]; c[x:x + 5] ^= b[5:]
    return p, c


def catalogue(rule_rec):
    w = rule_rec['wolfram']; tab = table(w); V = vac_seq(tab, T + PMAX + 4)
    out = []
    for o in rule_rec['objects']:
        if o['cls'] != 'sub-light': continue
        r = orbit(tab, *place([(o['seed'], X0)]), 0, V)
        if r and r[1] != 0 and abs(Fr(r[1], r[0])) >= VMIN:
            out.append(dict(seed=o['seed'], v=Fr(r[1], r[0]), species=r[2]))
    return out


def collide(w, R, L, off):
    tab = table(w); V = vac_seq(tab, T + PMAX + 4)
    st = {'B': place([(R['seed'], X0), (L['seed'], X0 + off)]), 'R': place([(R['seed'], X0)]), 'L': place([(L['seed'], X0 + off)])}
    contact = False
    for t in range(T):
        r = np.flatnonzero(st['R'][1] ^ V[t + 1]); l = np.flatnonzero(st['L'][1] ^ V[t + 1])
        if l.min() - r.max() <= 3: contact = True
        st = {k: step(tab, *v) for k, v in st.items()}
    p, c = st['B']; d = c ^ V[T + 1]
    res = dict(wolfram=w, offset=off, vR=str(R['v']), vL=str(L['v']), contact=contact)
    if not d.any(): return res | dict(outcome='annihilated')
    if np.array_equal(d, (st['R'][1] ^ V[T + 1]) ^ (st['L'][1] ^ V[T + 1])): return res | dict(outcome='superposition')
    runs = np.diff(np.flatnonzero(np.diff(np.r_[0, d, 0])))[::2]
    if runs.size and runs.max() >= BUB:
        # bubble wall speeds: track bubble edges from T-40 to T in a parallel copy
        return res | dict(outcome='bubble', bubble_width=int(runs.max()))
    outs, ok = [], True
    for a, b in clusters(d):
        if b - a + 1 > 8: ok = False; break
        win = np.zeros(N, bool); win[max(a - 2, 0):b + 3] = True
        cp = np.where(win, p, V[T]).astype(np.uint8); cc = np.where(win, c, V[T + 1]).astype(np.uint8)
        r = orbit(tab, cp, cc, T, V)
        if r is None: ok = False; break
        sp = 'R' if r[2] & R['species'] else 'L' if r[2] & L['species'] else 'new'
        outs.append(dict(v=str(Fr(r[1], r[0])), species=sp))
    if not ok: return res | dict(outcome='unresolved')
    vin = sorted([R['v'], L['v']]); vout = sorted(Fr(o['v']) for o in outs)
    elastic = len(outs) == 2 and vout == vin and sorted(o['species'] for o in outs) == ['L', 'R']
    return res | dict(outcome='elastic' if elastic else 'transmuted', outs=outs,
                      count_conserved=len(outs) == 2, momentum_conserved=sum(vout) == sum(vin))


def bubble_walls(w, R, L, off):
    tab = table(w); V = vac_seq(tab, T + PMAX + 4)
    p, c = place([(R['seed'], X0), (L['seed'], X0 + off)]); E = {}
    for t in range(T):
        p, c = step(tab, p, c)
        if t + 1 in (T - 40, T):
            d = c ^ V[t + 2]; idx = np.flatnonzero(np.diff(np.r_[0, d, 0]))
            s, e = idx[::2], idx[1::2]; k = int(np.argmax(e - s)); E[t + 1] = (int(s[k]), int(e[k]))
    return [(E[T - 40][0] - E[T][0]) / 40, (E[T][1] - E[T - 40][1]) / 40]


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    rules = json.load(open(CAT))['rules']; rows = []
    for rr in rules:
        cat = catalogue(rr); Rs = [o for o in cat if o['v'] > 0]; Ls = [o for o in cat if o['v'] < 0]
        if not (Rs and Ls): continue
        for off in OFFS:
            x = collide(rr['wolfram'], Rs[0], Ls[0], off); x['active_vacuum'] = rr['active_vacuum']
            if x['outcome'] == 'bubble': x['wall_speeds'] = bubble_walls(rr['wolfram'], Rs[0], Ls[0], off)
            rows.append(x)
    met = [x for x in rows if x['contact']]
    oc = lambda k: sum(x['outcome'] == k for x in met)
    bnd = [x for x in met if x['outcome'] in ('elastic', 'transmuted')]
    bub = [x for x in met if x['outcome'] == 'bubble']
    S = dict(rules=len({x['wolfram'] for x in rows}), collisions=len(rows), met=len(met),
             outcomes={k: oc(k) for k in ['annihilated', 'superposition', 'elastic', 'transmuted', 'bubble', 'unresolved']},
             bounded_count_conserved=sum(x['count_conserved'] for x in bnd),
             bounded_momentum_conserved=sum(x['momentum_conserved'] for x in bnd),
             fusion_2to1=sum(len(x['outs']) == 1 for x in bnd),
             new_species=sum(any(o['species'] == 'new' for o in x['outs']) for x in bnd),
             bubbles_silent_vacuum=sum(not x['active_vacuum'] for x in bub),
             bubbles_light_walls=sum(all(abs(abs(s) - 1) <= 0.05 for s in x['wall_speeds']) for x in bub))
    S['H_B1_bubbles_need_active_vacuum'] = 'no_bubbles' if not bub else ('supported' if S['bubbles_silent_vacuum'] == 0 else 'falsified')
    S['H_B2_light_speed_walls'] = 'no_bubbles' if not bub else ('supported' if S['bubbles_light_walls'] >= 0.9 * len(bub) else 'falsified')
    S['H_M_momentum'] = 'no_bounded' if not bnd else f"{S['bounded_momentum_conserved']}/{len(bnd)}"
    dst = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-COLLIDE-002/results.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(dict(summary=S, rows=rows), indent=1, default=str) + '\n')
    print(json.dumps(S, default=str))

if __name__ == '__main__':
    main()
