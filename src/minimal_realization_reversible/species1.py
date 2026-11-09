"""MIR-REVERSIBLE-SPECIES-001: exhaustive probe-species hunt, widths <= 8, every vacuum phase, catalog definition unchanged.

Seeds: every two-layer pattern of width <= K = 8 (2^16 - 1 seeds, shadow4 bit convention: bit j -> layer t-1 cell j,
bit K + j -> layer t cell j), XORed onto the vacuum at each vacuum phase k = 0 .. pv - 1 (k = 0 is the only phase the
existing catalogs used). Acceptance is the existing one, unchanged (ring NS = 256, horizon TS = 120, layer-t difference
from the vacuum nonzero and <= WS = 8 cells wide at every tick). Mover test per role, unchanged:
  active rules = collide2.catalogue: drift class sub-light (2 < |drift| < 116), exact orbit (C2.orbit, PMAX), v != 0,
                 |v| >= VMIN;
  silent rules = shadow4.catalogue4: exact orbit, v != 0, |v| >= VMIN (light movers allowed).
A species is an exact orbit (C2.orbit species set; same set <=> same cycle up to ring translation). Its width is the
smallest seed extent that produces it. See docs/ICP_MIR_REVERSIBLE_SPECIES_001_CONTRACT.md.
"""
import hashlib, json, os, subprocess, sys
os.environ.setdefault('OMP_NUM_THREADS', '1')
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction as Fr
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import table, step
from minimal_realization_reversible import collide2 as C2
import minimal_realization_reversible.shadow4 as S4
import minimal_realization_reversible.shadow6 as S6
import minimal_realization_reversible.shadow7 as S7
TAG = 'mir-reversible-species-001-v0.1-frozen'
P_ = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_SPECIES_001_CONTRACT.md'] + [P_ + f for f in (
    'species1.py', 'shadow4.py', 'shadow7.py', 'shadow6.py', 'shadow3.py', 'shadow.py', 'collide2.py', 'vacuum_collide.py')] + [
    'output/minimal_realization/MIR-REVERSIBLE-VACUUM-COLLIDE-001/results.json',
    'output/minimal_realization/MIR-REVERSIBLE-SHADOW-004/results.json']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/species1_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-SPECIES-001'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
K, NS, TS, WS, C0 = S4.K, S4.NS, S4.TS, S4.WS, S4.C0          # 8, 256, 120, 8, 128 (asserted in main)
WIDTHS = range(1, K + 1)
WDISC = 6                    # species of width <= WDISC: discovery; width WDISC+1 .. K: confirmation
MINCONF = 2                  # fewer confirmation species than this in a rule -> hash split for that rule


def vac_period(tab):
    V = C2.vac_seq(tab, 64); return next(k for k in range(1, 50) if (V[k], V[k + 1]) == (V[0], V[1]))


def seed_width(s):
    m = (s & ((1 << K) - 1)) | (s >> K); return m.bit_length() - ((m & -m).bit_length() - 1)


def accept(tab, k):
    """Acceptance at vacuum phase k. Returns (seed ids, drift, tick-TS pattern key) for accepted seeds."""
    V = C2.vac_seq(tab, k + TS + 4); s = np.arange(1, 2 ** (2 * K), dtype=np.int64)
    p = np.full((s.size, NS), V[k], np.uint8); c = np.full((s.size, NS), V[k + 1], np.uint8)
    for j in range(K):
        p[:, C0 + j] ^= ((s >> j) & 1).astype(np.uint8); c[:, C0 + j] ^= ((s >> (K + j)) & 1).astype(np.uint8)
    ok = np.ones(s.size, bool); idx = np.arange(NS, dtype=np.int16)
    for t in range(TS + 1):
        d = c ^ V[k + t + 1]
        big = np.where(d, idx, -1).max(1); sm = np.where(d, idx, NS).min(1)
        ok &= d.any(1) & (big - sm + 1 <= WS)
        if t == 0: lo0 = sm.copy()
        if t < TS: p, c = step(tab, p, c)
    out = []
    for i in np.flatnonzero(ok):
        dp, dc = p[i] ^ V[k + TS], c[i] ^ V[k + TS + 1]
        on = np.flatnonzero(dp | dc); a, b = int(on.min()), int(on.max())
        out.append((int(s[i]), int(sm[i] - lo0[i]), (tuple(dp[a:b + 1].tolist()), tuple(dc[a:b + 1].tolist()))))
    return out


def orbit_of(tab, pat, t0):
    V = C2.vac_seq(tab, t0 + C2.PMAX + 8)
    p = np.full(C2.N, V[t0], np.uint8); c = np.full(C2.N, V[t0 + 1], np.uint8)
    p[C2.X0:C2.X0 + len(pat[0])] ^= np.array(pat[0], np.uint8); c[C2.X0:C2.X0 + len(pat[1])] ^= np.array(pat[1], np.uint8)
    return C2.orbit(tab, p, c, t0, V)


def sid(sp): return hashlib.sha256(repr(sorted(sp)).encode()).hexdigest()[:16]


def job(j):
    w, role = j[0], j[4]; tab = table(w); pv = vac_period(tab); active = role.endswith('active')
    sp = {}                                                   # species id -> record
    acc = {}; v0 = None
    for k in range(pv):
        A = acc[k] = accept(tab, k); orb = {}
        if k == 0:   # VC-001 seeds: cells 0-4 of both layers (cells 5-7 empty)
            hi3 = (0b111 << 5) | (0b111 << (K + 5))
            v0 = dict(n5=sorted((s, d) for s, d, _ in A if not s & hi3),
                      accepted=len(A), distinct=len({x for _, _, x in A}))
        for s, d, pat in A:
            if active and not (2 < abs(d) < 116): continue
            if pat not in orb: orb[pat] = orbit_of(tab, pat, k + TS)
            r = orb[pat]
            if r is None or r[1] == 0: continue
            v = Fr(r[1], r[0])
            if abs(v) < C2.VMIN: continue
            i = sid(r[2]); wd = seed_width(s)
            if i not in sp:
                shape = frozenset(x[2] for x in r[2])
                sp[i] = dict(id=i, v=str(v), P=r[0], width=wd, phase=k, seed=s, shape=sid(shape), set=r[2])
            elif wd < sp[i]['width'] or (wd == sp[i]['width'] and (k, s) < (sp[i]['phase'], sp[i]['seed'])):
                sp[i].update(width=wd, phase=k, seed=s)
    # V1: every current probe species is in the catalog
    _, Rs, Ls = S7.lists(j)
    cur = [sid(o['sp']) for o in Rs + Ls]
    rec = dict(wolfram=w, role=role, pv=pv, V1_missing=[i for i in cur if i not in sp], current=cur)
    # V0 inputs (phase 0, catalog-equivalent subsets)
    rec['n5_phase0'] = v0['n5']; rec['accepted_phase0'] = v0['accepted']; rec['distinct_phase0'] = v0['distinct']
    # silent V0 input: distinct movers reachable at phase 0 (catalogue4's mover list, one entry per species)
    m0 = {}
    if not active:
        for s, d, pat in acc[0]:
            r = orbit_of(tab, pat, TS)
            if r is None or r[1] == 0 or abs(Fr(r[1], r[0])) < C2.VMIN: continue
            m0[sid(r[2])] = str(Fr(r[1], r[0]))
    rec['silent_movers_phase0'] = sorted(m0.values())
    # split
    L = sorted(sp.values(), key=lambda x: (x['width'], x['phase'], x['seed']))
    conf = [x for x in L if x['width'] > WDISC]
    mode = 'width' if len(conf) >= MINCONF else 'hash'
    for x in L:
        x['split'] = ('conf' if x['width'] > WDISC else 'disc') if mode == 'width' else \
                     ('conf' if int(x['id'][:8], 16) % 2 else 'disc')
        x['current'] = x['id'] in cur; del x['set']
    rec.update(split_mode=mode, n_species=len(L), species=L,
               yield_all={wd: sum(x['width'] <= wd for x in L) for wd in WIDTHS},
               yield_phase0={wd: sum(x['width'] <= wd and x['phase'] == 0 for x in L) for wd in WIDTHS},
               n_shapes=len({x['shape'] for x in L}),
               n_disc=sum(x['split'] == 'disc' for x in L), n_conf=sum(x['split'] == 'conf' for x in L),
               n_right=sum(Fr(x['v']) > 0 for x in L), n_left=sum(Fr(x['v']) < 0 for x in L))
    return rec


def main():
    assert (K, NS, TS, WS, C0) == (8, 256, 120, 8, 128) and C2.VMIN == Fr(1, 8)
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    jobs = S6.pairs()
    if sys.argv[1:2] == ['smoke']:
        ws = [int(x) for x in sys.argv[2:]]; sel = [j for j in jobs if j[0] in ws]
        with ProcessPoolExecutor(4) as ex:
            for r in ex.map(job, sel):
                print(json.dumps(dict(wolfram=r['wolfram'], V1_missing=r['V1_missing'])))
        return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(4) as ex: rows = list(ex.map(job, jobs))
    vc = {r['wolfram']: r for r in json.load(open(OM / 'MIR-REVERSIBLE-VACUUM-COLLIDE-001/results.json'))['rules']}
    s4 = json.load(open(OM / 'MIR-REVERSIBLE-SHADOW-004/results.json'))['catalogue']
    for r in rows:
        w = r['wolfram']
        if r['role'].endswith('active'):
            # VC-001 seed index s5 (bits 0-4 layer t-1, 5-9 layer t) -> K-bit convention
            conv = lambda s5: (s5 & 0b11111) | (((s5 >> 5) & 0b11111) << K)
            ref = sorted((conv(o['seed']), o['drift']) for o in vc[w]['objects'])
            r['V0'] = ref == r['n5_phase0']
        else:
            ref = s4[str(w)]
            r['V0'] = (ref['accepted'] == r['accepted_phase0'] and ref['distinct_patterns'] == r['distinct_phase0']
                       and sorted(ref['movers']) == r['silent_movers_phase0'])
        for k in ('n5_phase0', 'silent_movers_phase0'): del r[k]
    S = dict(V0_all=all(r['V0'] for r in rows), V1_all=all(not r['V1_missing'] for r in rows))
    S['valid'] = S['V0_all'] and S['V1_all']
    lab = lambda r: f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}"
    S['table'] = {lab(r): dict(n=r['n_species'], right=r['n_right'], left=r['n_left'], shapes=r['n_shapes'],
                               disc=r['n_disc'], conf=r['n_conf'], split=r['split_mode'],
                               yield_all=r['yield_all'], yield_phase0=r['yield_phase0']) for r in rows}
    S['rising_at_8'] = [lab(r) for r in rows if r['yield_all'][8] > r['yield_all'][7]]
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V0_all', 'V1_all')}), 'rising_at_8:', S['rising_at_8'])


if __name__ == '__main__':
    main()
