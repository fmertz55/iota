"""EXPLORE-QP-3 probe 2: one extra full slot in the all-R vacuum. Exploratory, not a contract.
A = all R (N full). B = all R plus L_0 full (N+1 full; node 0 both-full). Same frozen QP-002 rule (p1_vacuum engine).
Where the extra slot sits: dn(x,t) = <n_x>_B - <n_x>_A (node occupation; sums to 1 exactly).
  peak = max_x dn; spread = (sum|dn|)^2 / sum dn^2 (effective nodes); near = dn summed over nodes 0, +-1;
  neg = total of negative dn (vacuum pushed away = a dip).
Baselines: (free) one slot L_0 in an EMPTY ring, same rule (QP-002 one-coherence); (random) random states with the same
total and colour counts. Also per-node and half-ring trace distance A vs B, far-half entropy of B, forward-then-back.
Writes p2_extra_N{N}.csv, p2_free.csv, p2_reference.csv."""
import sys, os, time; sys.path.append(os.getcwd()); sys.path.insert(0, '/Users/douglasclark/iota/src')
import numpy as np, pandas as pd, p1_vacuum as p
from quantum_gold import qp002 as q

def far_near(Bk, psi, N):
    """dicts keyed by number of full slots in the far half / near half."""
    far, near = {}, {}
    for sel, fr, nr, cf, cn in Bk.blocks:
        Mx = np.zeros((cf, cn), complex); Mx[fr, nr] = psi[sel]
        kf = Bk.kfar[id(sel)]; far[kf] = Mx@Mx.conj().T; near[Bk.k-kf] = Mx.T@Mx.conj()
    return far, near

def tdict(a, b):
    td = 0.0
    for k in set(a) | set(b):
        if k in a and k in b: td += np.abs(np.linalg.eigvalsh(a[k]-b[k])).sum()
        else: td += np.real(np.trace(a[k] if k in a else b[k]))
    return 0.5*td

def ent(d):
    s = 0.0
    for m in d.values():
        w = np.linalg.eigvalsh(m); w = w[w > 1e-15]; s -= np.sum(w*np.log2(w))
    return s

def make_block(S):
    Bk = p.Block(S); Bk.k = S.k; Bk.kfar = {}
    fm = [p.mode(s, x, S.N) for x in Bk.far for s in (0, 1)]
    for sel, fr, nr, cf, cn in Bk.blocks:
        st = S.st[sel[0]]; Bk.kfar[id(sel)] = sum((st >> m) & 1 for m in fm)
    return Bk

def occ(psi, S):
    pr = np.abs(psi)**2
    return np.array([pr[((S.st >> p.mode(0, x, S.N)) & 1) == 1].sum()+pr[((S.st >> p.mode(1, x, S.N)) & 1) == 1].sum()
                     for x in range(S.N)])

def shape(dn, N):
    near = sum(dn[x % N] for x in (-1, 0, 1))
    return dict(peak=dn.max(), spread=np.abs(dn).sum()**2/np.sum(dn**2), near=near, neg=dn[dn < 0].sum(),
                total=dn.sum())

def run(N, mu, th, T, SA, SB, BA, BB):
    gates, n = p.gate_list(N, mu, th)
    vac = sum(1 << p.mode(0, x, N) for x in range(N)); ext = vac | (1 << p.mode(1, 0, N))
    A = np.zeros(SA.D, complex); A[SA.idx(vac)] = 1; B = np.zeros(SB.D, complex); B[SB.idx(ext)] = 1; B0 = B.copy()
    rows = []
    for t in range(T+1):
        if t: A = p.tick(A, SA, gates, mu, n, th); B = p.tick(B, SB, gates, mu, n, th)
        dn = occ(B, SB)-occ(A, SA); fa, na = far_near(BA, A, N); fb, nb = far_near(BB, B, N)
        row = dict(N=N, mu=mu, theta_pi=th/np.pi, t=t, **shape(dn, N), td_far=tdict(fa, fb), td_near=tdict(na, nb),
                   S_far_B=ent(fb), S_far_A=ent(fa))
        for x in range(N):
            row[f'dn{x}'] = dn[x]
            row[f'td_n{x}'] = p.node_td(*p.node_rho(A, SA, x), *p.node_rho(B, SB, x))
        rows.append(row)
    Bb = B.copy()
    for t in range(T): Bb = p.tick(Bb, SB, gates, mu, n, th, inverse=True)
    for r in rows: r['back_fid_B'] = abs(np.vdot(B0, Bb))**2
    return rows

def free(N, mu, th, T):
    U = q.one_coherence(N, mu); v = np.zeros(2*N, complex); v[p.mode(1, 0, N)] = 1; rows = []
    for t in range(T+1):
        if t: v = U@v
        dn = np.abs(v[0::2])**2+np.abs(v[1::2])**2
        row = dict(N=N, mu=mu, t=t, **shape(dn, N)); row.update({f'dn{x}': dn[x] for x in range(N)}); rows.append(row)
    return rows

if __name__ == '__main__':
    th = 0.5*np.pi; P = lambda N: sum(1 << p.mode(x % 2, x, N) for x in range(N)); rng = np.random.default_rng(11)
    fr, ref = [], []
    for N in (8, 10, 12):
        t0 = time.time(); SA = p.Sector(N, N); SB = p.Sector(N, N+1); BA = make_block(SA); BB = make_block(SB); rows = []
        for mu in (0.5, 0.8):
            rows += run(N, mu, th, 3*N, SA, SB, BA, BB); fr += free(N, mu, th, 3*N); print(N, mu, round(time.time()-t0), flush=True)
        pd.DataFrame(rows).to_csv(f'p2_extra_N{N}.csv', index=False)
        cA = p.popcount(SA.st & P(N)); cB = p.popcount(SB.st & P(N))
        vac = sum(1 << p.mode(0, x, N) for x in range(N)); print(N, 'P count A, B:', cA[SA.idx(vac)], cB[SB.idx(vac | 2)])
        for s in range((20, 10, 3)[(N-8)//2]):
            a = np.zeros(SA.D, complex); m = cA == N//2; a[m] = rng.normal(size=m.sum())+1j*rng.normal(size=m.sum()); a /= np.linalg.norm(a)
            b = np.zeros(SB.D, complex); m = cB == N//2; b[m] = rng.normal(size=m.sum())+1j*rng.normal(size=m.sum()); b /= np.linalg.norm(b)
            dn = occ(b, SB)-occ(a, SA); fa, na = far_near(BA, a, N); fb, nb = far_near(BB, b, N)
            ref.append(dict(N=N, **shape(dn, N), td_far=tdict(fa, fb), td_near=tdict(na, nb), S_far_B=ent(fb),
                            node_td=np.mean([p.node_td(*p.node_rho(a, SA, x), *p.node_rho(b, SB, x)) for x in range(N)])))
        del SA, SB, BA, BB
    pd.DataFrame(fr).to_csv('p2_free.csv', index=False); pd.DataFrame(ref).to_csv('p2_reference.csv', index=False)
    print('done')
