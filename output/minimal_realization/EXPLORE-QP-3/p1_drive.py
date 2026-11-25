"""Probe 1 grid: N = 8, 10, 12; mu = 0.5, 0.8; theta = 0.5 pi, 0; T = 3N ticks. Writes p1_vacuum_N{N}.csv."""
import sys, os, time; sys.path.append(os.getcwd())
import numpy as np, pandas as pd, p1_vacuum as p
for N in (8, 10, 12):
    t0 = time.time(); S = p.Sector(N, N); B = p.Block(S); rows = []
    for mu in (0.5, 0.8):
        for th in (0.5*np.pi, 0.0):
            rows += p.run(N, mu, th, 3*N, S, B); print(N, mu, th, round(time.time()-t0), flush=True)
    pd.DataFrame(rows).to_csv(f'p1_vacuum_N{N}.csv', index=False); del S, B
print('done')
