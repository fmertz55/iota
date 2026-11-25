"""Validity: the probe-1 engine reproduces frozen QP-002 one- and two-coherence ticks exactly (N = 4, 5)."""
import numpy as np, sys
sys.path.insert(0, '/Users/douglasclark/iota/src')
from quantum_gold import qp002 as q
import os; sys.path.append(os.getcwd())
from p1_vacuum import Sector, gate_list, tick
worst = 0.0
for N in (4, 5):
    for mu, th in ((0.5, 0.5*np.pi), (0.8, 0.0), (0.3, 0.9*np.pi)):
        gates, n = gate_list(N, mu, th)
        for k in (1, 2):
            S = Sector(N, k)
            U = np.column_stack([tick(np.eye(S.D, dtype=complex)[:, j], S, gates, mu, n, th) for j in range(S.D)])
            if k == 1:
                ref = q.one_coherence(N, mu); order = [int(np.log2(s)) for s in S.st]
            else:
                ref, pairs = q.two_coherence(N, mu, th); ref = ref.toarray()
                order = [pairs.index(tuple(sorted(int(i) for i in range(2*N) if (s >> i) & 1))) for s in S.st]
            ref = ref[np.ix_(order, order)]; worst = max(worst, np.abs(U-ref).max())
            Ui = np.column_stack([tick(U[:, j], S, gates, mu, n, th, inverse=True) for j in range(S.D)])
            worst = max(worst, np.abs(Ui-np.eye(S.D)).max())
print('max |engine - QP-002|, max |back*fwd - 1| =', worst)
