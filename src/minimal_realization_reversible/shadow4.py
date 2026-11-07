"""MIR-REVERSIBLE-SHADOW-004: can a silent vacuum (f(000)=0) hold a shadow?
Wider seed search among silent rules, then the unchanged SHADOW-003 pair() pipeline."""
import hashlib, json, subprocess, sys
from fractions import Fraction as Fr
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import table, step, vacuum, SEEDS
from minimal_realization_reversible import collide2 as C2
import minimal_realization_reversible.shadow as S1
import minimal_realization_reversible.shadow3 as S3
TAG = 'mir-reversible-shadow-004-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_SHADOW_004_CONTRACT.md', 'src/minimal_realization_reversible/shadow4.py',
          'src/minimal_realization_reversible/shadow3.py', 'src/minimal_realization_reversible/shadow.py',
          'src/minimal_realization_reversible/collide2.py', 'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/shadow4_seal.json'
OUT = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-SHADOW-004'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
K, NS, TS, WS, C0 = 8, 256, 120, 8, 128
KMOV, NSTILL, STAT, NPIC = 2, 64, 300, 16
N = S3.N


def place4(seeds, n=N):
    p = np.zeros(n, np.uint8); c = np.zeros(n, np.uint8)
    for (pp, cc), x in seeds:
        p[x:x + len(pp)] ^= np.array(pp, np.uint8); c[x:x + len(cc)] ^= np.array(cc, np.uint8)
    return p, c


def search(w):
    """Width-K seeds on both layers; same acceptance as VACUUM-COLLIDE-001. Returns per accepted
    seed (in seed order) its drift and its tick-TS pattern (p-layer, c-layer) relative to the union min."""
    tab = table(w); vac = vacuum(tab, TS); s = np.arange(1, 2 ** (2 * K), dtype=np.int64)
    p = np.zeros((s.size, NS), np.uint8); c = np.zeros((s.size, NS), np.uint8)
    for j in range(K):
        p[:, C0 + j] = (s >> j) & 1; c[:, C0 + j] = (s >> (K + j)) & 1
    ok = np.ones(s.size, bool); idx = np.arange(NS, dtype=np.int16)
    for t in range(TS + 1):
        d = c ^ vac[t]
        big = np.where(d, idx, -1).max(1); sm = np.where(d, idx, NS).min(1)
        ok &= d.any(1) & (big - sm + 1 <= WS)
        if t == 0: lo0 = sm.copy()
        if t < TS: p, c = step(tab, p, c)
    out = []
    for i in np.flatnonzero(ok):
        dp, dc = p[i] ^ vac[TS - 1], c[i] ^ vac[TS]
        on = np.flatnonzero(dp | dc); a, b = int(on.min()), int(on.max())
        out.append(dict(drift=int(sm[i] - lo0[i]), pat=(tuple(dp[a:b + 1].tolist()), tuple(dc[a:b + 1].tolist()))))
    return out


def catalogue4(w):
    tab = table(w); V = C2.vac_seq(tab, C2.T + C2.PMAX + 4)
    assert all(v == 0 for v in V), 'not a silent vacuum'
    cand = search(w); seen, movers, still, nstill = set(), [], [], 0
    for o in cand:
        if o['pat'] in seen: continue
        seen.add(o['pat'])
        is_still = abs(o['drift']) <= 2
        if is_still:
            nstill += 1
            if nstill > NSTILL: continue
        r = C2.orbit(tab, *place4([(o['pat'], C2.X0)], C2.N), 0, V)
        if r is None: continue
        v = Fr(r[1], r[0]); rec = dict(seed=o['pat'], v=v, species=r[2])
        if any(r[2] & m['species'] for m in movers + still): continue
        if v == 0 and is_still: still.append(rec)
        elif v != 0 and abs(v) >= C2.VMIN: movers.append(rec)
    pick = lambda f: [m for m in movers if f(m['v'])][:KMOV]
    Rs = pick(lambda v: 0 < v < 1) + pick(lambda v: v == 1)
    Ls = pick(lambda v: -1 < v < 0) + pick(lambda v: v == -1)
    info = dict(accepted=len(cand), distinct_patterns=len(seen),
                movers=sorted(str(m['v']) for m in movers), still_species=len(still))
    return Rs, Ls, still[:2], info


def erased_states(w, R, L):
    """Re-derive pair()'s post-erasure probe-free states (for stationarity and pictures)."""
    tab = table(w); V = C2.vac_seq(tab, S3.T + S3.RUN + C2.PMAX + 4); out = []
    for off in S3.OFFS:
        U = S3.place([(R['seed'], S3.X0), (L['seed'], S3.X0 + off)]); hist = []
        for _ in range(S3.T): hist.append(U[1].copy()); U = step(tab, *U)
        objs, _ = S1.objects(tab, *U, V, S3.T); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[S3.T]; c[a - 2:b + 3] = V[S3.T + 1]
        out.append((off, p, c, hist))
    return tab, V, out


def stationary(w, R, L):
    tab, V, sts = erased_states(w, R, L); ok = True
    for off, p, c, _ in sts:
        d = np.flatnonzero((p ^ V[S3.T]) | (c ^ V[S3.T + 1]))
        if not d.size: continue
        lo, hi = d.min() - 8, d.max() + 8
        for k in range(STAT):
            p, c = step(tab, p, c); e = np.flatnonzero(c ^ V[S3.T + k + 2])
            if e.size and (e.min() < lo or e.max() > hi): ok = False; break
        if not ok: break
    return ok


def picture(w, R, L, tag):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    tab, V, sts = erased_states(w, R, L)
    k = next((i for i, (_, p, c, _) in enumerate(sts) if ((p ^ V[S3.T]) | (c ^ V[S3.T + 1])).any()), 0)
    off, p, c, hist = sts[k]; rows = list(hist)
    for j in range(STAT): rows.append(c ^ V[S3.T + j + 1]); p, c = step(tab, p, c)
    A = np.array(rows)[:, S3.X0 - 200:S3.X0 + 300]
    fig, ax = plt.subplots(figsize=(5, 7)); ax.imshow(A, cmap='Greys', aspect='auto', interpolation='nearest')
    ax.axhline(S3.T, color='r', lw=0.6); ax.set_title(f'rule {w} {tag} offset {off} (red: carriers erased)', fontsize=8)
    ax.set_xlabel('site - (X0-200)'); ax.set_ylabel('tick'); fig.savefig(OUT / f'st_{w}_{tag}.png', dpi=110); plt.close(fig)


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    rules = {r['wolfram']: r for r in json.load(open(C2.CAT))['rules']}
    # V0 positive control through the patched placement path
    old = json.load(open(ROOT / 'output/minimal_realization/MIR-REVERSIBLE-SHADOW-003/results.json'))['pairs']
    cat = C2.catalogue(rules[37]); R0 = [o for o in cat if o['v'] > 0][0]; L0 = [o for o in cat if o['v'] < 0][0]
    ref = next(x for x in old if x['wolfram'] == 37 and x['seedR'] == R0['seed'] and x['seedL'] == L0['seed'])
    S3.place = place4
    cv = lambda o: dict(o, seed=(tuple(SEEDS[o['seed'] - 1][:5].tolist()), tuple(SEEDS[o['seed'] - 1][5:].tolist())))
    r0 = S3.pair(37, cv(R0), cv(L0)); keys = ['shadow_runs', 'only_shadow', 'footprint_beyond', 'probe_state_beyond']
    V0 = all(abs(r0[k] - ref[k]) < 1e-12 for k in keys); print('V0', V0, {k: (r0[k], ref[k]) for k in keys}, flush=True)
    cats, out = {}, []
    for w in range(0, 256, 2):
        Rs, Ls, St, info = catalogue4(w); cats[w] = info
        print(json.dumps(dict(wolfram=w, **info, R=[str(m['v']) for m in Rs], L=[str(m['v']) for m in Ls])), flush=True)
        jobs = [(R, L, 'light' if abs(R['v']) == 1 and abs(L['v']) == 1 else 'finite' if abs(R['v']) < 1 and abs(L['v']) < 1 else 'mixed')
                for R in Rs for L in Ls]
        jobs += [(R, St[0], 'still-target') for R in Rs if St and R['v'] >= Fr(1, 4)]
        for R, L, stratum in jobs:
            r = S3.pair(w, R, L)
            r.update(wolfram=w, stratum=stratum, vR=str(R['v']), vL=str(L['v']), seedR=str(R['seed']), seedL=str(L['seed']))
            out.append((r, R, L)); print(json.dumps(r, default=str), flush=True)
    rows = [r for r, _, _ in out]
    clean = [r for r in rows if r['shadow_runs'] == 0]
    dirty = [(r, R, L) for r, R, L in out if r['shadow_runs'] > 0 and r['only_shadow'] > 1e-12]
    for r, R, L in dirty: r['stationary'] = stationary(r['wolfram'], R, L)
    for i, (r, R, L) in enumerate(dirty[:NPIC]): picture(r['wolfram'], R, L, f'shadow{i}')
    for i, (r, R, L) in enumerate([x for x in out if x[0]['shadow_runs'] == 0][:4]): picture(r['wolfram'], R, L, f'clean{i}')
    D = [r for r, _, _ in dirty]
    S = dict(V0_positive_control=V0, silent_rules=128,
             rules_with_movers=sum(bool(v['movers']) for v in cats.values()),
             rules_with_finite_movers=sum(any(abs(Fr(m)) < 1 for m in v['movers']) for v in cats.values()),
             pairs=len(rows), pairs_by_stratum={s: sum(r['stratum'] == s for r in rows) for s in ['finite', 'light', 'mixed', 'still-target']},
             rules_paired=len({r['wolfram'] for r in rows}), clean_pairs=len(clean),
             residue_no_unique_info=sum(r['shadow_runs'] > 0 and r['only_shadow'] <= 1e-12 for r in rows),
             S_silent_shadow_pairs=len(D), shadow_rules=sorted({r['wolfram'] for r in D}),
             shadow_by_stratum={s: sum(r['stratum'] == s for r in D) for s in ['finite', 'light', 'mixed', 'still-target']},
             stationary=sum(r['stationary'] for r in D),
             V1_clean_all_zero=all(r['footprint_beyond'] < 1e-12 and r['probe_state_beyond'] < 1e-12 for r in clean),
             footprint_ratio_1=sum(abs(r['footprint_ratio'] - 1) < 1e-9 for r in D),
             probe_state_positive=sum(r['probe_state_ratio'] > 1e-12 for r in D),
             probe_state_ratio_median=float(np.median([r['probe_state_ratio'] for r in D])) if D else None)
    S['valid'] = V0 and S['V1_clean_all_zero']
    S['Q1'] = 'invalid' if not S['valid'] else ('silent_shadow_found_pending_picture_check' if D else 'none_at_this_depth')
    S['P_prior_S_eq_0'] = 'held' if not D else 'failed'
    S['H_R'] = 'n/a' if not D else ('supported' if S['footprint_ratio_1'] >= 0.9 * len(D) else 'not_supported')
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, catalogue=cats, pairs=rows), indent=1,
                                                 default=lambda o: o.item() if hasattr(o, 'item') else str(o)) + '\n')
    print(json.dumps(S, default=str))


if __name__ == '__main__':
    main()
