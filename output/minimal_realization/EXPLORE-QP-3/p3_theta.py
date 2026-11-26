"""EXPLORE-QP-3 probe 3: theta scan for one extra full slot (L_0) in the all-R vacuum. Exploratory, not a contract.
theta/pi = 0, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0; mu = 0.5, 0.8; N = 8, 10, 12; T = 100 ticks. Occupations only.
Per tick: dn shape (p2_extra.shape: peak, spread, near, neg, total) and return chance of the plain vacuum A.
Writes p3_theta.csv."""
import sys, os, time; sys.path.append(os.getcwd())
import numpy as np, pandas as pd, p1_vacuum as p, p2_extra as p2
rows = []; t0 = time.time()
for N in (8, 10, 12):
    SA = p.Sector(N, N); SB = p.Sector(N, N+1); vac = sum(1 << p.mode(0, x, N) for x in range(N))
    for mu in (0.5, 0.8):
        for thp in (0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0):
            th = thp*np.pi; g, n = p.gate_list(N, mu, th)
            A = np.zeros(SA.D, complex); A[SA.idx(vac)] = 1; A0 = A.copy()
            B = np.zeros(SB.D, complex); B[SB.idx(vac | 2)] = 1
            for t in range(101):
                if t: A = p.tick(A, SA, g, mu, n, th); B = p.tick(B, SB, g, mu, n, th)
                dn = p2.occ(B, SB)-p2.occ(A, SA)
                r = dict(N=N, mu=mu, theta_pi=thp, t=t, ret_A=abs(np.vdot(A0, A))**2, **p2.shape(dn, N))
                r.update({f'dn{x}': dn[x] for x in range(N)}); rows.append(r)
            print(N, mu, thp, round(time.time()-t0), flush=True)
    del SA, SB
    pd.DataFrame(rows).to_csv('p3_theta.csv', index=False)
print('done')
