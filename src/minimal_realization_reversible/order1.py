"""MIR-REVERSIBLE-ORDER-001: does the background remember the ORDER of two interactions?

A target X (one mover species) is hit by two readers alpha, beta (distinct species from the other side), one after the
other, from the same port. Slot 2 is slot 1 translated exactly by g = (v_X * Delta, Delta), with Delta a multiple of
L = lcm(pv, P_X) and v_X * Delta integer, so a reader alone meets X identically in either slot (checked cell by cell).
AB = alpha in slot 1, beta in slot 2; BA = the swap. Nothing else differs.
Outcome (coarse, translation- and age-invariant): movers = multiset of (species id, direction); background = multiset of
component words after movers are erased (word = sequence of domain records, orbit-canonical, INVENTORY-001 decomp;
compact still oscillators = ('osc', species id); no-domain blobs = ('nodom',)).
Order is recorded in a case iff outcome(AB) != outcome(BA); split into movers-only, background-only, both.
If the two events do not interact, both orders give the same coarse outcome (translation invariance): the built-in null.
See docs/ICP_MIR_REVERSIBLE_ORDER_001_CONTRACT.md.
"""
import hashlib, json, math, os, subprocess, sys, time
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
import minimal_realization_reversible.inventory1 as I1
import minimal_realization_reversible.species1 as SPc
TAG = 'mir-reversible-order-001-v0.1.1-frozen'
P_ = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_ORDER_001_CONTRACT.md'] + [P_ + f for f in (
    'order1.py', 'species1.py', 'inventory1.py', 'shadow4.py', 'shadow7.py', 'shadow6.py', 'shadow3.py', 'shadow.py',
    'collide2.py', 'vacuum_collide.py')] + ['output/minimal_realization/MIR-REVERSIBLE-SPECIES-001/results.json']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/order1_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-ORDER-001'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, K = 32768, 16384, 8
DS = range(24, 88)                  # slot-1 reader start distance from X (SHADOW offsets)
DMIN = (400, 800)                   # Delta = smallest multiple of L >= DMIN[i]
RT = (1600, 2400, 3200)             # readout times after Delta (common to both orders)
NSLOT = 20                          # exact slot-equivalence check on the first NSLOT cases of every job
NCASE = dict(eligible=800, null=400, control=400, calib=None)   # sampled cases per side
SEED = 20261115
ELIGIBLE = ['147', '201', '22s', '26s', '58s', '82s', '114s']
NULLS = ['1', '5', '90s']
CONTROL = 250                       # second-order f = l OR r = Bobenko RCA54 on each sublattice (integrable)
EXPOSED = '91'                      # calibration rule (exposed); V0 slice below
V0_SLICE = dict(X='77faeae98c25bc25', al='7c044ea74008e3ff', be='0d34f6ea613699c3', taus=(0, 3), ds=range(24, 88, 2),
                order=32, valid=64)


def idx(c): return 4 * np.roll(c, 1) + 2 * c + np.roll(c, -1)
def back(tab, p, c): return tab[idx(p)] ^ c, p
def vperiod(V): return next(k for k in range(1, 50) if (V[k], V[k + 1]) == (V[0], V[1]))


class Rule:
    def __init__(s, w, species):
        s.w = w; s.tab = table(w); s.V = C2.vac_seq(s.tab, C2.PMAX + 64); s.pv = vperiod(s.V); s.cache = {}; s.orb = {}
        s.sp = [dict(x, v=Fr(x['v'])) for x in species]

    def dev(s, o, tau, t, M=8192):
        """Deviation from vacuum at time t of species o seeded (SPECIES-001 convention) at time tau at ring centre."""
        assert (tau - o['phase']) % s.pv == 0
        V, k = s.V, o['phase']; p = np.full(M, V[k], np.uint8); c = np.full(M, V[k + 1], np.uint8); sd = o['seed']
        for j in range(K):
            p[M // 2 + j] ^= (sd >> j) & 1; c[M // 2 + j] ^= (sd >> (K + j)) & 1
        n = t - tau
        for _ in range(abs(n)): p, c = step(s.tab, p, c) if n > 0 else back(s.tab, p, c)
        ph = (k + n) % s.pv; dp = p ^ V[ph]; dc = c ^ V[ph + 1]
        on = np.flatnonzero(dp | dc); a, b = int(on.min()), int(on.max())
        if a < 50 or b > M - 50: raise ValueError('dev edge')
        return dp[a:b + 1].copy(), dc[a:b + 1].copy(), a - M // 2


def world(R, objs):
    V = R.V; p = np.full(N, V[0], np.uint8); c = np.full(N, V[1], np.uint8); occ = np.zeros(N, bool)
    for o, tau, x in objs:
        dp, dc, off = R.dev(o, tau, 0); a = x + off
        if a < 64 or a + len(dp) > N - 64 or occ[a - 4:a + len(dp) + 4].any(): raise ValueError('placement')
        occ[a:a + len(dp)] = True; p[a:a + len(dp)] ^= dp; c[a:a + len(dc)] ^= dc
    return p, c


def run(R, p, c, n):
    for _ in range(n): p, c = step(R.tab, p, c)
    return p, c


def clusters(d, gap=3):
    on = np.flatnonzero(d); out = []
    for i in on:
        if out and i - out[-1][1] - 1 < gap: out[-1][1] = int(i)
        else: out.append([int(i), int(i)])
    return out


def orbit_id(R, p, c, t, a, b):
    V = R.V; W = 1024; m = W // 2; ph = t % R.pv
    pp = np.full(W, V[ph], np.uint8); cc = np.full(W, V[ph + 1], np.uint8)
    pp[m - 2:m + b - a + 3] = p[a - 2:b + 3]; cc[m - 2:m + b - a + 3] = c[a - 2:b + 3]
    key = (ph, pp[m - 2:m + b - a + 3].tobytes(), cc[m - 2:m + b - a + 3].tobytes())
    if key not in R.orb:
        r = C2.orbit(R.tab, pp, cc, ph, V); R.orb[key] = (SPc.sid(r[2]), Fr(r[1], r[0])) if r else None
    return R.orb[key]


def readout(R, p, c, t):
    """(movers, background, target-direction mover positions)."""
    V = R.V; ph = t % R.pv; d = (p ^ V[ph]) | (c ^ V[ph + 1]); p = p.copy(); c = c.copy(); mv, osc, pos = [], [], []
    for a, b in clusters(d):
        if b - a + 1 > 8: continue
        r = orbit_id(R, p, c, t, a, b)
        if r is None: continue
        if r[1] == 0: osc.append(('osc', r[0]))
        else: mv.append((r[0], 1 if r[1] > 0 else -1)); pos.append((r[0], 1 if r[1] > 0 else -1, a))
        p[a - 2:b + 3] = V[ph]; c[a - 2:b + 3] = V[ph + 1]
    words = [tuple(rec for rec, *_ in cp['dom']) if cp['dom'] else ('nodom',) for cp in I1.decomp(p, c, V, ph, R.tab, R.pv, R.cache)]
    return tuple(sorted(mv)), tuple(sorted(repr(x) for x in words + osc)), tuple(sorted(pos))


def L_of(R, X):
    L0 = math.lcm(R.pv, X['P']); L = L0
    while (X['v'] * L).denominator != 1: L += L0
    return L


def case(R, X, tauX, al, be, d, Delta, side, slot_check=True):
    """side = +1: X moves left, readers start to its left; side = -1: mirror. Readouts at Delta + RT."""
    sh = int(X['v'] * Delta); TT = [Delta + r for r in RT]
    s1 = lambda o: (o, o['phase'], X0 - side * d); s2 = lambda o: (o, o['phase'] + Delta, X0 - side * d + sh); tg = (X, tauX, X0)
    try:
        out = dict(d=d, Delta=Delta, tauX=tauX, AB=[], BA=[], AB_pos=[], BA_pos=[])
        fin = {}
        for nm, objs in (('AB', [tg, s1(al), s2(be)]), ('BA', [tg, s1(be), s2(al)])):
            p, c = world(R, objs); t = 0
            for T in TT:
                p, c = run(R, p, c, T - t); t = T; r1 = readout(R, p, c, T); out[nm].append(r1[:2]); out[nm + '_pos'].append(r1[2])
                if T == TT[0]: fin[nm] = (p, c)
        ok = True
        if slot_check:            # exact slot equivalence: slot 2 = slot 1 translated by g
            for o in (al, be):
                pa, ca = run(R, *world(R, [tg, s1(o)]), TT[0] - Delta); pb, cb = run(R, *world(R, [tg, s2(o)]), TT[0])
                ok &= bool(np.array_equal(np.roll(pa, sh), pb) and np.array_equal(np.roll(ca, sh), cb))
        tch = {}
        for nm, (f, s) in (('AB', (al, be)), ('BA', (be, al))):   # did the slot-2 reader interact at all (by TT[0])?
            ps, cs = run(R, *world(R, [tg, s1(f)]), TT[0]); dp, dc, off = R.dev(s, s['phase'] + Delta, TT[0]); a = X0 - side * d + sh + off
            ps = ps.copy(); cs = cs.copy(); ps[a:a + len(dp)] ^= dp; cs[a:a + len(dc)] ^= dc
            P, C = fin[nm]; tch[nm] = not (np.array_equal(ps, P) and np.array_equal(cs, C))
        out.update(slot_ok=ok, slot_checked=slot_check, touched=tch, valid=ok)
    except ValueError as e:
        out = dict(d=d, Delta=Delta, tauX=tauX, valid=False, slot_ok=True, slot_checked=False, err=str(e))
    return out


def classify1(A, B):
    mv = A[0] != B[0]; bg = A[1] != B[1]; pa, pb = bool(A[1]), bool(B[1])
    return dict(order=mv or bg, mov_only=mv and not bg, bg_only=bg and not mv, both=mv and bg,
                gate=bg and pa != pb, written=bg and pa and pb, bg_any=pa or pb)


def classify(x):
    """Persistent classes: the class holds at every readout time. touched = second reader interacted in both orders."""
    per = [classify1(A, B) for A, B in zip(x['AB'], x['BA'])]
    out = {k: all(p[k] for p in per) for k in per[0]}
    out['order_any'] = any(p['order'] for p in per); out['bg_ever'] = any(p['bg_any'] for p in per)
    out['touched'] = all(x['touched'].values())
    return out


class Grid:
    """The case grid, indexed lazily in the v0.1 enumeration order (X sorted by id; pair; tau; d; Delta), so that
    rng.choice(len(G)) picks exactly the cases v0.1 would have picked (v0.1.1: memory fix only)."""
    def __init__(s, R, side, pairs):
        s.blocks = []; off = 0
        for X in sorted([o for o in R.sp if o['v'] * side < 0], key=lambda o: o['id']):
            L = L_of(R, X); Ds = [L * math.ceil(m / L) for m in DMIN]; taus = [X['phase'] + m * R.pv for m in range(X['P'] // R.pv)]
            n = len(pairs) * len(taus) * len(DS) * len(Ds); s.blocks.append((off, n, X['id'], taus, Ds)); off += n
        s.n = off
    def __len__(s): return s.n
    def __getitem__(s, g):
        for off, n, Xid, taus, Ds in s.blocks:
            if g < off + n:
                r = g - off; De = Ds[r % len(Ds)]; r //= len(Ds); d = DS[r % len(DS)]; r //= len(DS)
                tau = taus[r % len(taus)]; pi = r // len(taus); return (Xid, pi, tau, d, De)
        raise IndexError(g)


def grid(R, side):
    Rd = sorted([o for o in R.sp if o['v'] * side > 0], key=lambda o: o['id'])
    pairs = [(Rd[i], Rd[j]) for i in range(len(Rd)) for j in range(i + 1, len(Rd))]
    return Grid(R, side, pairs), pairs


def job(a):
    lab, w, species, n, side, mode = a
    R = Rule(w, species); byid = {o['id']: o for o in R.sp}; t0 = time.time()
    if mode == 'v0':
        S = V0_SLICE; X = byid[S['X']]; L = L_of(R, X); De = L * math.ceil(240 / L)
        rows = [case(R, X, tau, byid[S['al']], byid[S['be']], d, De, 1) for tau in S['taus'] for d in S['ds']]
        return dict(lab=lab, mode=mode, valid=sum(x['valid'] for x in rows), order=sum(x['valid'] and classify1(x['AB'][0], x['BA'][0])['order'] for x in rows))
    G, pairs = grid(R, side)
    if not pairs: return dict(lab=lab, side=side, n_grid=0, rows=[])
    rng = np.random.default_rng([SEED, int(w), side + 1]); pick = sorted(rng.choice(len(G), size=min(n, len(G)), replace=False)) if n else range(len(G))
    if mode == 'smoke': pick = list(pick)[:8]
    rows = []
    for gi in pick:
        Xid, pi, tau, d, De = G[gi]; al, be = pairs[pi]
        x = case(R, byid[Xid], tau, al, be, d, De, side, slot_check=len(rows) < NSLOT); x.update(X=Xid, al=al['id'], be=be['id'], side=side); rows.append(x)
    return dict(lab=lab, side=side, n_grid=len(G), n_pairs=len(pairs), rows=rows, secs=time.time() - t0)


def summary(rows):
    V = [x for x in rows if x['valid']]; Tt = [x for x in V if classify(x)['touched']]; C = Counter(); Ca = Counter()
    for x in Tt:
        for k, v in classify(x).items(): C[k] += v
    for x in V:
        for k, v in classify(x).items(): Ca[k] += v
    n = len(Tt); f = lambda k: C[k] / n if n else None
    return dict(n=len(rows), valid=len(V), touched=n, slot_checked=sum(x.get('slot_checked', False) for x in rows),
                slot_fail=sum(not x['slot_ok'] for x in rows), placement_err=sum('err' in x for x in rows),
                counts=dict(C), counts_all_valid=dict(Ca), bits_order=f('order'), bits_bg=(C['bg_only'] + C['both']) / n if n else None,
                bits_mov=(C['mov_only'] + C['both']) / n if n else None, bits_bg_only=f('bg_only'))


def jobs_list(sel=None):
    S = {f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}": r for r in json.load(open(OM / 'MIR-REVERSIBLE-SPECIES-001/results.json'))['rules']}
    J = []
    for lab in ELIGIBLE + NULLS:
        grp = 'eligible' if lab in ELIGIBLE else 'null'
        for side in (1, -1): J.append((lab, S[lab]['wolfram'], S[lab]['species'], NCASE[grp], side, 'full'))
    sp250 = control_species()
    for side in (1, -1): J.append(('250c', CONTROL, sp250, NCASE['control'], side, 'full'))
    J.append((EXPOSED, 91, S[EXPOSED]['species'], None, 1, 'v0'))
    return [j for j in J if sel is None or j[0] in sel]


def control_species():
    """SPECIES-001 acceptance and silent mover test, unchanged, applied to rule 250."""
    tab = table(CONTROL); pv = SPc.vac_period(tab); sp = {}
    for k in range(pv):
        orb = {}
        for s, dft, pat in SPc.accept(tab, k):
            if pat not in orb: orb[pat] = SPc.orbit_of(tab, pat, k + SPc.TS)
            r = orb[pat]
            if r is None or r[1] == 0 or abs(Fr(r[1], r[0])) < C2.VMIN: continue
            i = SPc.sid(r[2]); wd = SPc.seed_width(s)
            if i not in sp or (wd, k, s) < (sp[i]['width'], sp[i]['phase'], sp[i]['seed']):
                sp[i] = dict(id=i, v=str(Fr(r[1], r[0])), P=r[0], width=wd, phase=k, seed=s)
    return sorted(sp.values(), key=lambda x: (x['width'], x['phase'], x['seed']))


def tpos(x, nm):
    """Target-direction movers (species, position) at T_F: the exact Yang-Baxter check for the control."""
    return [sorted(p for p in P if p[1] == -x['side']) for P in x[nm + '_pos']]


def verdicts(res):
    by = {}
    for r in res:
        if r.get('mode') == 'v0': continue
        by.setdefault(r['lab'], []).extend(r['rows'])
    T = {lab: summary(rows) for lab, rows in by.items()}
    v0 = next(r for r in res if r.get('mode') == 'v0')
    c = [x for x in by.get('250c', []) if x['valid'] and classify(x)['touched']]
    S = dict(V0=v0['valid'] == V0_SLICE['valid'] and v0['order'] == V0_SLICE['order'],
             V_slot=all(x['slot_ok'] for rows in by.values() for x in rows) and all(sum(x.get('slot_checked', False) for x in rows) >= 10 for rows in by.values()),
             V_C54=len(c) >= 100 and all(not classify(x)['order_any'] and not classify(x)['bg_ever'] for x in c) and
                   all(tpos(x, 'AB') == tpos(x, 'BA') for x in c),
             V_valid=all(T[l]['valid'] >= 0.9 * T[l]['n'] and T[l]['touched'] >= 50 for l in ELIGIBLE))
    S['valid'] = all(S[k] for k in ('V0', 'V_slot', 'V_C54', 'V_valid'))
    S['H_O_pass'] = [l for l in ELIGIBLE if T[l]['counts'].get('order', 0) > 0]
    S['H_B_pass'] = [l for l in ELIGIBLE if T[l]['counts'].get('bg_only', 0) > 0]
    S['H_W_pass'] = [l for l in ELIGIBLE if T[l]['counts'].get('written', 0) > 0]
    v = lambda ps, k: 'invalid' if not S['valid'] else 'supported' if len(ps) >= k else 'not_supported'
    S['H_O'] = v(S['H_O_pass'], 5); S['H_B'] = v(S['H_B_pass'], 4); S['H_W'] = v(S['H_W_pass'], 4)
    S['table'] = T
    return S


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    if sys.argv[1:2] in (['smoke'], ['time']):
        sel = sys.argv[2:] or None; J = [j[:5] + (('smoke' if sys.argv[1] == 'smoke' else 'full') if j[5] != 'v0' else 'v0',) for j in jobs_list(sel)]
        with ProcessPoolExecutor(6) as ex:
            for r in ex.map(job, J):
                if r.get('mode') == 'v0': print(r); continue
                s = summary(r['rows']); print(r['lab'], r['side'], 'grid', r['n_grid'], 'secs', round(r.get('secs', 0), 1),
                                              {k: s[k] for k in ('n', 'valid', 'touched', 'slot_checked', 'slot_fail', 'placement_err')})
        return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    J = sorted(jobs_list(), key=lambda j: -(j[3] or 0))
    CK = OUT / 'jobs'; CK.mkdir(exist_ok=True)
    ck = lambda j: CK / f"{j[0]}_{j[4]}_{j[5]}.json"
    todo = [j for j in J if not ck(j).exists()]
    with ProcessPoolExecutor(5) as ex:
        for j, r in zip(todo, ex.map(job, todo)): ck(j).write_text(json.dumps(r, default=str))   # v0.1.1: per-job checkpoint
    res = [json.loads(ck(j).read_text()) for j in J]
    S = verdicts(res)
    rows = [dict(lab=r['lab'], side=r.get('side'), n_grid=r.get('n_grid'), rows=r.get('rows'), v0=r if r.get('mode') == 'v0' else None) for r in res]
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, jobs=rows), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V0', 'V_slot', 'V_C54', 'V_valid', 'H_O', 'H_B', 'H_W')}),
          'pass O/B/W:', S['H_O_pass'], S['H_B_pass'], S['H_W_pass'])


if __name__ == '__main__':
    main()
