"""Probe 3 read-out. Joins p3_theta.csv (N = 8, 10) and the per-run N = 12 files into p3_theta_N12.csv, then
summarises each (N, mu, theta) run in 20-tick windows -> p3_summary.csv.
near = share of the extra slot within 1 node of node 0 (even spread = 3/N); peak = largest node share (even = 1/N);
spread = effective number of nodes; stag = (-1)^t sum_x (-1)^x dn_x (node-alternating wave; 0 when mixed);
min_dn = lowest node value over the run (negative = node below the plain vacuum); retA = return chance of plain vacuum."""
import glob, numpy as np, pandas as pd
n12 = sorted(glob.glob('p3_theta_N12_mu*_th*.csv'))
if n12: pd.concat([pd.read_csv(f) for f in n12]).to_csv('p3_theta_N12.csv', index=False)
d = pd.concat([pd.read_csv('p3_theta.csv'), pd.read_csv('p3_theta_N12.csv')]); rows = []
for (N, mu, th), g in d.groupby(['N', 'mu', 'theta_pi']):
    sg = np.array([(-1)**x for x in range(N)]); dn = g[[f'dn{x}' for x in range(N)]].values
    g = g.assign(stag=(dn@sg)*((-1)**g.t.values)); r = dict(N=N, mu=mu, theta_pi=th, even_near=3/N, even_peak=1/N,
        min_dn=dn.min(), retA_max_t1on=g[g.t > 0].ret_A.max(), total_err=abs(g.total-1).max())
    for a in (20, 40, 60, 80):
        w = g[(g.t >= a) & (g.t < a+20)] if a < 80 else g[g.t >= 80]
        r.update({f'near_{a}': w.near.mean(), f'peak_{a}': w.peak.mean(), f'spread_{a}': w.spread.mean(),
                  f'stag_{a}': w.stag.mean(), f'absstag_{a}': w.stag.abs().mean(), f'retA_{a}': w.ret_A.mean()})
    rows.append(r)
pd.DataFrame(rows).to_csv('p3_summary.csv', index=False)
print(pd.DataFrame(rows)[['N', 'mu', 'theta_pi', 'near_80', 'even_near', 'peak_80', 'even_peak', 'spread_80',
      'absstag_20', 'absstag_80', 'min_dn', 'retA_80', 'total_err']].round(3).to_string(index=False))
