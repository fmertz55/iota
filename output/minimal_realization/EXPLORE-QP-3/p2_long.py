"""Probe 2 long check: does the extra slot's slow leak at mu = 0.8 level off (held part) or reach the even spread?
Occupations only, T = 100 ticks, N = 10, 12, mu = 0.8 (and 0.5 for comparison), theta = 0.5 pi. Writes p2_long.csv."""
import sys, os; sys.path.append(os.getcwd())
import numpy as np, pandas as pd, p1_vacuum as p, p2_extra as p2
th = 0.5*np.pi; rows = []
for N in (10, 12):
    SA = p.Sector(N, N); SB = p.Sector(N, N+1)
    for mu in (0.8, 0.5):
        g, n = p.gate_list(N, mu, th); vac = sum(1 << p.mode(0, x, N) for x in range(N))
        A = np.zeros(SA.D, complex); A[SA.idx(vac)] = 1; B = np.zeros(SB.D, complex); B[SB.idx(vac | 2)] = 1
        for t in range(101):
            if t: A = p.tick(A, SA, g, mu, n, th); B = p.tick(B, SB, g, mu, n, th)
            dn = p2.occ(B, SB)-p2.occ(A, SA); rows.append(dict(N=N, mu=mu, t=t, **p2.shape(dn, N)))
        print(N, mu, flush=True)
    del SA, SB
pd.DataFrame(rows).to_csv('p2_long.csv', index=False); print('done')
