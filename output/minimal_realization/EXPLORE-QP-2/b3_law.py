"""Route B item 1: why the theta = pi/2 pair obeys cos eps = n^2 cos K. Helpers on top of b1_pair."""
import numpy as np, pandas as pd, b1_pair as B

def wrapang(a): return (a+np.pi) % (2*np.pi)-np.pi

def continuum(K, mu, nk=4000):
    n = np.sqrt(1-mu**2); k = np.linspace(-np.pi, np.pi, nk, endpoint=False); w = lambda q: np.arccos(np.clip(n*np.cos(q), -1, 1))
    return np.exp(1j*np.concatenate([a*w(k)+b*w(K-k) for a in (1, -1) for b in (1, -1)]))

def held_map(N, mu, theta, hold_gap=6, thr=0.6, vecs=False):
    U2, pairs = B.two_particle(N, mu, theta); bl = B.k_blocks(N, U2, pairs); near = B.node_gap(pairs, N) <= hold_gap; rows = []
    for m in range(N//2+1):
        K, UK, Bm = bl[m]; lam, V = np.linalg.eig(UK); F = Bm@V; P = abs(F)**2; P /= P.sum(0); h = P[near].sum(0); c = continuum(K, mu)
        for j in np.where(h > thr)[0]:
            r = dict(m=m, K=K, eps=-np.angle(lam[j]), held=h[j], dist=np.min(abs(c-lam[j])))
            if vecs: r['vec'] = F[:, j]
            rows.append(r)
    return pd.DataFrame(rows), pairs

def track(hm, eps0):
    out = []; prev = eps0; sl = 0.0; dK = hm.K[hm.m == 1].iloc[0]
    for m in sorted(hm.m.unique()):
        s = hm[hm.m == m]; pred = prev+sl*dK if m > 1 else prev
        j = s.index[np.argmin(abs(wrapang(s.eps.values-pred)))]; r = hm.loc[j]
        if m > 0: sl = wrapang(r.eps-prev)/dK
        prev = r.eps; out.append(r)
    d = pd.DataFrame(out).reset_index(drop=True); d['eps_u'] = np.unwrap(d.eps); return d
