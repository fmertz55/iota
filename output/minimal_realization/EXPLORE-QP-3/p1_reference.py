"""Probe 1 read-out: (a) conserved linear slot counts of the rule (one tick and two ticks), (b) random references
(plain random pair; colour-matched random pair), (c) per-run summary of p1_vacuum_N*.csv. Writes p1_reference.csv,
p1_summary.csv. Colour P = {R at even nodes, L at odd nodes}; Q = the rest (even N)."""
import sys, os; sys.path.append(os.getcwd()); sys.path.insert(0, '/Users/douglasclark/iota/src')
import numpy as np, pandas as pd, p1_vacuum as p
from quantum_gold import qp002 as q

for N in (6, 8, 10):                                   # (a) linear counts w.n with U diag(w) = diag(w) U
    for mu in (0.5, 0.8):
        U = q.one_coherence(N, mu); out = []
        for UU in (U, U@U):
            conn = (np.abs(UU) > 1e-12); np.fill_diagonal(conn, False)
            import scipy.sparse.csgraph as cg
            out.append(cg.connected_components(conn, directed=False)[0])
        print(f'N={N} mu={mu}: conserved linear counts per 1 tick = {out[0]}, per 2 ticks = {out[1]}')
P = lambda N: sum(1 << p.mode(x % 2, x, N) for x in range(N))
print('colour P: edge (L_x, R_{x-1}) same colour:', all(((x % 2 == 1) == ((x-1) % 2 == 0)) for x in range(8)))

rng = np.random.default_rng(7); ref = []
def rand_in(mask, D):
    v = np.zeros(D, complex); v[mask] = rng.normal(size=mask.sum())+1j*rng.normal(size=mask.sum()); return v/np.linalg.norm(v)
for N, ns in ((8, 20), (10, 10), (12, 3)):            # (b)
    S = p.Sector(N, N); B = p.Block(S); cP = p.popcount(S.st & P(N)); allm = np.ones(S.D, bool)
    for kind in ('plain', 'colour'):
        for s in range(ns):
            if kind == 'plain':
                a = rand_in(allm, S.D); b = rand_in(allm, S.D); b -= np.vdot(a, b)*a; b /= np.linalg.norm(b)
            else:
                a = rand_in(cP == N//2, S.D); b = rand_in(cP == N//2-1, S.D)
            tdf, tdn, ent = p.td_and_entropy(B.rhos(a), B.rhos(b))
            nt = np.mean([p.node_td(*p.node_rho(a, S, x), *p.node_rho(b, S, x)) for x in range(N)])
            both = np.mean([p.node_rho(a, S, x)[0][3] for x in range(N)])
            ref.append(dict(N=N, kind=kind, td_far=tdf, td_near=tdn, S_far_bits=ent, node_td=nt, both=both))
    vac = sum(1 << p.mode(0, x, N) for x in range(N)); print(N, 'P count vacuum, changed:', cP[S.idx(vac)], cP[S.idx(vac ^ 3)])
    del S, B, cP
R = pd.DataFrame(ref).groupby(['N', 'kind']).agg(['mean', 'std']); R.columns = ['_'.join(c) for c in R.columns]
R.reset_index().to_csv('p1_reference.csv', index=False)

df = pd.concat([pd.read_csv(f'p1_vacuum_N{N}.csv') for N in (8, 10, 12)]); rows = []   # (c)
for (N, mu, th), g in df.groupby(['N', 'mu', 'theta_pi']):
    late = g[g.t >= N]; tdn = [f'td_n{x}' for x in range(N)]
    front = [int(g[g[f'td_n{d}'] > 1e-12].t.min()) for d in range(1, N//2+1)]
    outside = max(g.loc[g.t == t, [f'td_n{x}' for x in range(N) if min(x, N-x) > t]].values.max(initial=0) for t in range(N//2))
    rows.append(dict(N=N, mu=mu, theta_pi=th, ret_max_t1on=g[g.t > 0].ret_A.max(), ret_late=late.ret_A.mean(),
        meanR_late=late.mean_R.mean(), both_late=late.mean_both.mean(), S_far_late=late.S_far_bits.mean(),
        cone_1_per_tick=front == list(range(1, N//2+1)), outside_cone_max=outside, td_far_late=late.td_far.mean(),
        td_near_late=late.td_near.mean(), node_td_late=late[tdn].values.mean(), back_fid=g.back_fid_B.iloc[0],
        norm_err=max(abs(g.normA-1).max(), abs(g.normB-1).max())))
pd.DataFrame(rows).to_csv('p1_summary.csv', index=False); print('written')
