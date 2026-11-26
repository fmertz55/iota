"""Probe 3, N = 12 part (same runs as p3_theta.py, leaner): int32 index caches, one CSV per run
(p3_theta_N12_mu{mu}_th{thp}.csv), skips runs already written. Results identical in content to p3_theta.py."""
import sys, os, time; sys.path.append(os.getcwd())
import numpy as np, pandas as pd, p1_vacuum as p, p2_extra as p2

class Lean(p.Sector):
    def pair(self, a, b):
        key = (a, b)
        if key not in self.cache:
            ba = (self.st >> a) & 1; bb = (self.st >> b) & 1
            one = np.nonzero(ba ^ bb)[0].astype(np.int32); both = np.nonzero(ba & bb)[0].astype(np.int32)
            part = np.searchsorted(self.st, self.st[one] ^ ((1 << a) | (1 << b))).astype(np.int32)
            self.cache[key] = (one, part, both)
        return self.cache[key]

N = 12; t0 = time.time(); SA = Lean(N, N); SB = Lean(N, N+1); vac = sum(1 << p.mode(0, x, N) for x in range(N))
MUS = [float(sys.argv[1])] if len(sys.argv) > 2 else (0.5, 0.8)
THS = [float(sys.argv[2])] if len(sys.argv) > 2 else (0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0)
for mu in MUS:                     # optional args: mu thp  -> one run per process (fresh memory)
    for thp in THS:
        fn = f'p3_theta_N12_mu{mu}_th{thp}.csv'
        if os.path.exists(fn): continue
        th = thp*np.pi; g, n = p.gate_list(N, mu, th); rows = []
        A = np.zeros(SA.D, complex); A[SA.idx(vac)] = 1; A0 = A.copy(); B = np.zeros(SB.D, complex); B[SB.idx(vac | 2)] = 1
        for t in range(101):
            if t: A = p.tick(A, SA, g, mu, n, th); B = p.tick(B, SB, g, mu, n, th)
            dn = p2.occ(B, SB)-p2.occ(A, SA)
            r = dict(N=N, mu=mu, theta_pi=thp, t=t, ret_A=abs(np.vdot(A0, A))**2, **p2.shape(dn, N))
            r.update({f'dn{x}': dn[x] for x in range(N)}); rows.append(r)
        pd.DataFrame(rows).to_csv(fn, index=False); print(mu, thp, round(time.time()-t0), flush=True)
print('done')
