"""MIR-REVERSIBLE-SHADOW-009: what a single reader misses (reader bank: species x side x launch parity; edges; defect)."""
import hashlib, json, math, os, subprocess, sys
os.environ.setdefault('OMP_NUM_THREADS', '1')
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.vacuum_collide import step
from minimal_realization_reversible import collide2 as C2
import minimal_realization_reversible.shadow as S1
import minimal_realization_reversible.shadow6 as S6
import minimal_realization_reversible.shadow7 as S7
TAG = 'mir-reversible-shadow-009-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_SHADOW_009_CONTRACT.md', 'src/minimal_realization_reversible/shadow9.py',
          'src/minimal_realization_reversible/shadow7.py', 'src/minimal_realization_reversible/shadow6.py',
          'src/minimal_realization_reversible/shadow3.py', 'src/minimal_realization_reversible/shadow.py',
          'src/minimal_realization_reversible/collide2.py', 'src/minimal_realization_reversible/vacuum_collide.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/shadow9_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-SHADOW-009'
S7REF = OM / 'MIR-REVERSIBLE-SHADOW-007/results.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
N, X0, GAP, OFFS, RUN, EW, CW, STAT = S7.N, S7.X0, 24, S7.OFFS, 1500, 16, 64, 300
EXPOSED = {(26, 'shadow_silent'), (82, 'shadow_silent'), (94, 'shadow_silent'), (218, 'shadow_silent')}
H = S7.H


def idx(c):
    return 4 * np.roll(c, 1) + 2 * c + np.roll(c, -1)


def prepare(tab, V, Rs, Ls, T):
    st, O, left, right, EL, ER, typ, dropped, seen = [], [], [], [], [], [], [], 0, set()
    for ri, li, off in [(ri, li, o) for ri in range(len(Rs)) for li in range(len(Ls)) for o in OFFS]:
        U = S6.place([(Rs[ri]['seed'], X0), (Ls[li]['seed'], X0 + off)]); key = U[0].tobytes() + U[1].tobytes()
        if key in seen: dropped += 1; continue
        seen.add(key)
        for _ in range(T): U = step(tab, *U)
        objs, resid = S1.objects(tab, *U, V, T); p, c = U[0].copy(), U[1].copy()
        for x in objs:
            a, b = x['span']; p[a - 2:b + 3] = V[T]; c[a - 2:b + 3] = V[T + 1]
        st.append((p, c)); O.append(tuple(sorted((x['species'], x['state'], x['pos']) for x in objs)))
        L_ = [a for a, _ in resid] + [x['span'][0] for x in objs]; R_ = [b for _, b in resid] + [x['span'][1] for x in objs]
        left.append(min(L_) if L_ else X0); right.append(max(R_) if R_ else X0)
        dp, dc = p ^ V[T], c ^ V[T + 1]; on = np.flatnonzero(dp | dc)
        if not on.size:
            EL.append(None); ER.append(None); typ.append('none'); continue
        lo, hi = int(on.min()), int(on.max())
        EL.append((lo, tuple(dp[lo:lo + EW].tolist()), tuple(dc[lo:lo + EW].tolist())))
        ER.append((hi, tuple(dp[hi - EW + 1:hi + 1].tolist()), tuple(dc[hi - EW + 1:hi + 1].tolist())))
        t = 'extended'
        if hi - lo + 1 <= CW:
            q, r, t = p.copy(), c.copy(), 'compact'
            for k in range(STAT):
                q, r = step(tab, q, r); e = np.flatnonzero((q ^ V[T + k + 1]) | (r ^ V[T + k + 2]))
                if e.min() < lo - 8 or e.max() > hi + 8: t = 'extended'; break
        typ.append(t)
    return dict(st=st, O=O, left=left, right=right, EL=EL, ER=ER, typ=typ, dropped=dropped)


def bank(tab, V, Rs, Ls, T, Lm, Rm):
    out = {}
    for side, sp in (('R', Rs), ('L', Ls)):
        for i, o in enumerate(sp):
            F, fa, fb = S7.free(tab, o['seed'], T, V); W = fb - fa + 1
            for s in (0, 1):
                L0 = Lm - GAP - s - W if side == 'R' else Rm + GAP + s + 1
                out[f'{side}{i}s{s}'] = (F[0][fa:fb + 1].copy(), F[1][fa:fb + 1].copy(), L0)
    return out


def readout(Pc, Nc):
    y = np.flatnonzero(Pc ^ Nc); return (tuple((y - y.min()).tolist()), int(y.min())) if y.size else ((), 0)


def run_input(tab, V, T, p, c, rd):
    """Evolve N once (storing current layers and f-values), then each reader world with defect tracking."""
    Ns, Nf = [], []; Np, Nc = p, c
    for _ in range(RUN):
        f = tab[idx(Nc)]; Ns.append(Nc); Nf.append(f); Np, Nc = Nc, f ^ Np
    NcF = Nc; out = {}
    for k, (fp, fc, L0) in rd.items():
        Pp, Pc = p.copy(), c.copy(); W = len(fp); Pp[L0:L0 + W] = fp; Pc[L0:L0 + W] = fc; touched = False
        for t in range(RUN):
            f = tab[idx(Pc)]
            if not touched:
                v = V[T + t + 1]
                d = f ^ Nf[t] ^ tab[idx(Pc ^ Ns[t] ^ v)] ^ tab[7 * v]
                touched = bool(d.any())
            Pp, Pc = Pc, f ^ Pp
        out[k] = (readout(Pc, NcF), touched)
    return out


def vacuum_readout(tab, V, T, rd):
    p = np.full(N, V[T], np.uint8); c = np.full(N, V[T + 1], np.uint8); Np, Nc = p, c
    for _ in range(RUN): Np, Nc = step(tab, Np, Nc)
    out = {}
    for k, (fp, fc, L0) in rd.items():
        Pp, Pc = p.copy(), c.copy(); W = len(fp); Pp[L0:L0 + W] = fp; Pc[L0:L0 + W] = fc
        for _ in range(RUN): Pp, Pc = step(tab, Pp, Pc)
        out[k] = readout(Pc, Nc)
    return out


def job(j):
    S1.N = N
    w, _, _, _, role = j; tab, Rs, Ls = S7.lists(j)
    close = min(R['v'] - L['v'] for R in Rs for L in Ls); T = math.ceil(552 / close) + 300
    V = C2.vac_seq(tab, T + RUN + STAT + C2.PMAX + 4)
    D = prepare(tab, V, Rs, Ls, T); rd = bank(tab, V, Rs, Ls, T, min(D['left']), max(D['right']))
    res = [run_input(tab, V, T, p, c, rd) for p, c in D['st']]
    vac = vacuum_readout(tab, V, T, rd)
    O = D['O']; n = len(O); HO = H(O); only = math.log2(n) - HO
    I = lambda *cols: H(list(zip(O, *cols))) - HO
    Y = {k: [r[k][0] for r in res] for k in rd}; TT = {k: [r[k][1] for r in res] for k in rd}
    fp = {k: I(Y[k]) for k in rd}
    jl = I(*[Y[k] for k in rd if k[0] == 'R']); jr = I(*[Y[k] for k in rd if k[0] == 'L']); ja = I(*Y.values())
    IL, IR, ILR = I(D['EL']), I(D['ER']), I(D['EL'], D['ER'])
    V2 = all(Y[k][m] == vac[k] for k in rd for m in range(n) if not TT[k][m])
    a = 'R0s0'
    return dict(wolfram=w, role=role, exposed=(w, role) in EXPOSED, n=n, dropped=D['dropped'], T=T,
                residue_runs=sum(e is not None for e in D['EL']), only=only, footprint=fp,
                transparent_frac={k: 1 - sum(TT[k]) / n for k in rd}, joint_left=jl, joint_right=jr, joint_all=ja,
                I_L=IL, I_R=IR, I_LR=ILR, V2=V2, type={t: D['typ'].count(t) for t in ('none', 'compact', 'extended')},
                a_far_edge=math.log2(n) - H(list(zip(O, D['EL']))), a_near_unread=IL - fp[a],
                seeds=dict(R=[str(o['seed']) for o in Rs], L=[str(o['seed']) for o in Ls]))


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    jobs = S6.pairs()
    if sys.argv[1:2] == ['smoke']:
        r = job(next(j for j in jobs if j[0] == int(sys.argv[2])))
        print(json.dumps(r, default=str)); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    ref = {(r['wolfram'], r['role']): r['C'] for r in json.load(open(S7REF))['rules']}
    order = sorted(jobs, key=lambda j: (j[0], j[4]) not in {(94, 'shadow_silent')})  # longest first
    with ProcessPoolExecutor(4) as ex: rows = list(ex.map(job, order))
    for r in rows: r['V0'] = abs(r['footprint']['R0s0'] - ref[(r['wolfram'], r['role'])]['footprint_a']) < 1e-12
    lab = lambda r: f"{r['wolfram']}{r['role'][7]}"
    sh = [r for r in rows if r['role'].startswith('shadow') and r['only'] > 1e-9]; un = [r for r in sh if not r['exposed']]
    hb = [lab(r) for r in un if r['only'] - r['joint_all'] < 1e-9]
    def phase(r):
        ks = {k[:2] for k in r['footprint']}
        return any(abs(r['footprint'][k + 's0'] - r['footprint'][k + 's1']) > 0.01 for k in ks)
    hp = [lab(r) for r in un if phase(r)]
    he = [lab(r) for r in un if abs(r['joint_left'] - r['I_L']) <= 0.05 and abs(r['joint_right'] - r['I_R']) <= 0.05]
    S = dict(V0_all=all(r['V0'] for r in rows), V1=all(r['only'] < 1e-9 and max(r['footprint'].values()) < 1e-9
             for r in rows if r['residue_runs'] == 0), V2_all=all(r['V2'] for r in rows),
             shadow_pairs=len(sh), unexposed=len(un), dropped_total=sum(r['dropped'] for r in rows),
             H_B_pass=hb, H_Phi_pass=hp, H_E_pass=he)
    S['valid'] = S['V0_all'] and S['V1'] and S['V2_all']
    v = lambda ok: 'invalid' if not S['valid'] else 'supported' if ok else 'not_supported'
    S['H_B'] = v(len(hb) >= math.ceil(0.9 * len(un))); S['H_Phi'] = v(len(hp) >= math.ceil(len(un) / 3))
    S['H_E'] = v(len(he) >= math.ceil(2 * len(un) / 3))
    S['table'] = {lab(r): dict(exp=r['exposed'], only=round(r['only'], 3), a=round(r['footprint']['R0s0'], 3),
                  best=max(r['footprint'], key=r['footprint'].get), best_v=round(max(r['footprint'].values()), 3),
                  jl=round(r['joint_left'], 3), jr=round(r['joint_right'], 3), ja=round(r['joint_all'], 3),
                  IL=round(r['I_L'], 3), IR=round(r['I_R'], 3), ILR=round(r['I_LR'], 3),
                  a_far=round(r['a_far_edge'], 3), a_near=round(r['a_near_unread'], 3), type=r['type']) for r in rows}
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S, rules=rows), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V0_all', 'V2_all', 'H_B', 'H_Phi', 'H_E', 'unexposed')}))


if __name__ == '__main__':
    main()
