"""MIR-REVERSIBLE-VACUUM-COLLIDE-001: (V) active-vacuum test by direct object search;
(C) head-on collisions of left/right sub-light objects."""
import hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
TAG = 'mir-reversible-vacuum-collide-001-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_VACUUM_COLLIDE_CONTRACT.md', 'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/vacuum_collide_seal.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
NS, TS, WS, C0 = 256, 120, 8, 128          # search ring, horizon, width bound, seed origin
NC, TC, TAIL = 512, 240, 32                # collision ring, horizon, velocity window
OFFS = range(40, 48)                       # 8 impact phases


def table(w):
    return np.array([(w >> k) & 1 for k in range(8)], dtype=np.uint8)


def step(tab, p, c):
    i = 4 * np.roll(c, 1, -1) + 2 * c + np.roll(c, -1, -1)  # (left, self, right)
    return c, tab[i] ^ p


def vacuum(tab, T):
    p, c, out = np.zeros(1, np.uint8), np.zeros(1, np.uint8), []
    for _ in range(T + 1):
        out.append(int(c[0])); p, c = c, tab[4 * c + 2 * c + c] ^ p
    return out  # homogeneous vacuum value per layer (layer 0 = 0, layer -1 = 0)


SEEDS = np.array([[(s >> k) & 1 for k in range(10)] for s in range(1, 1024)], np.uint8)  # bits0-4: x[-1], 5-9: x[0]


def search(w):
    tab = table(w); vac = vacuum(tab, TS)
    S = len(SEEDS); p = np.zeros((S, NS), np.uint8); c = np.zeros((S, NS), np.uint8)
    p[:, C0:C0 + 5] = SEEDS[:, :5]; c[:, C0:C0 + 5] = SEEDS[:, 5:]   # vacuum at layers -1,0 is 0
    ok = np.ones(S, bool); lo0 = None
    idx = np.arange(NS)
    for t in range(TS + 1):
        d = c ^ vac[t]
        nz = d.any(1); big = np.where(d, idx, -1).max(1); sm = np.where(d, idx, NS).min(1)
        ok &= nz & (big - sm + 1 <= WS)
        if t == 0: lo0 = sm.copy()
        if t < TS: p, c = step(tab, p, c)
    drift = sm - lo0
    objs = [dict(seed=int(s + 1), drift=int(drift[s])) for s in np.flatnonzero(ok)]
    for o in objs:
        a = abs(o['drift']); o['cls'] = 'still' if a <= 2 else ('light' if a >= 116 else 'sub-light')
    return objs


def clusters(row):
    on = np.flatnonzero(row); out = []
    for i in on:
        if out and i - out[-1][1] - 1 < 3: out[-1][1] = i
        else: out.append([i, i])
    return out


def collide(w, sR, sL, off):
    tab = table(w); vac = vacuum(tab, TC)
    def init(placements):
        p = np.zeros(NC, np.uint8); c = np.zeros(NC, np.uint8)
        for s, x in placements:
            b = SEEDS[s - 1]; p[x:x + 5] ^= b[:5]; c[x:x + 5] ^= b[5:]
        return p, c
    runs = {k: init(v) for k, v in dict(both=[(sR, 200), (sL, 200 + off)], R=[(sR, 200)], L=[(sL, 200 + off)]).items()}
    hist = []
    for t in range(TC + 1):
        if t >= TC - TAIL: hist.append({k: v[1] ^ vac[t] for k, v in runs.items()})
        if t < TC: runs = {k: step(tab, *v) for k, v in runs.items()}
    fin = hist[-1]
    if not fin['both'].any(): return dict(outcome='annihilated')
    if np.array_equal(fin['both'], fin['R'] ^ fin['L']): return dict(outcome='transparent')
    vel, rad = [], False
    for cl in clusters(hist[0]['both']):
        if cl[1] - cl[0] + 1 > WS: rad = True; continue
        cur, ok = cl, True
        for h in hist[1:]:
            nx = [e for e in clusters(h['both']) if e[1] - e[0] + 1 <= WS and e[0] <= cur[1] + 1 and e[1] >= cur[0] - 1]
            if not nx: ok = False; break
            cur = nx[0]
        if ok: vel.append((cur[0] - cl[0]) / TAIL)
        else: rad = True
    if len(clusters(fin['both'])) != len(vel): rad = True
    return dict(outcome='interacting', n_out=len(vel), v_out=vel, radiation=rad)


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    rules = []
    for w in range(256):
        objs = search(w)
        rules.append(dict(wolfram=w, active_vacuum=bool(w & 1),
                          n={k: sum(o['cls'] == k for o in objs) for k in ['still', 'sub-light', 'light']}, objects=objs))
    V = {}
    for act in (False, True):
        g = [r for r in rules if r['active_vacuum'] == act]
        V['active' if act else 'silent'] = {k: sum(r['n'][k] > 0 for r in g) for k in ['still', 'sub-light', 'light']}
    V['verdict'] = ('supported' if V['silent']['sub-light'] == 0 and V['active']['sub-light'] >= 1
                    else 'falsified' if V['silent']['sub-light'] >= 1 else 'no_objects')
    cols = []
    for r in rules:
        sub = [o for o in r['objects'] if o['cls'] == 'sub-light']
        R = [o for o in sub if o['drift'] > 0]; L = [o for o in sub if o['drift'] < 0]
        if not (R and L): continue
        vR, vL = R[0]['drift'] / TS, L[0]['drift'] / TS
        for off in OFFS:
            res = collide(r['wolfram'], R[0]['seed'], L[0]['seed'], off)
            if res['outcome'] == 'interacting':
                res['count_conserved'] = res['n_out'] == 2 and not res['radiation']
                res['velocity_sum_conserved'] = (not res['radiation']) and abs(sum(res['v_out']) - (vR + vL)) <= 0.05
            cols.append(dict(wolfram=r['wolfram'], seedR=R[0]['seed'], seedL=L[0]['seed'], vR=vR, vL=vL, offset=off, **res))
    oc = lambda k: sum(c['outcome'] == k for c in cols)
    inter = [c for c in cols if c['outcome'] == 'interacting']
    Cs = dict(rules=len({c['wolfram'] for c in cols}), collisions=len(cols), annihilated=oc('annihilated'),
              transparent=oc('transparent'), interacting=len(inter),
              count_conserved=sum(c['count_conserved'] for c in inter),
              velocity_sum_conserved=sum(c['velocity_sum_conserved'] for c in inter),
              with_radiation=sum(c['radiation'] for c in inter),
              still_products=sum(any(abs(v) < 0.07 for v in c['v_out']) for c in inter))
    dst = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-VACUUM-COLLIDE-001/results.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(dict(V=V, C=Cs, rules=rules, collisions=cols), indent=1) + '\n')
    print(json.dumps(dict(V=V, C=Cs)))

if __name__ == '__main__':
    main()
