"""Route B step 2 (exploratory): smooth limit. Does the theta-held pair stay tight as mu gets small, or spread?
Exact two-coherence sector, pair at rest (K = 0 block only). Pick the eigenstate whose clock matches the law
cos(clock) = n^2 cos K - mu^2 cos(theta); measure the node-gap profile P(d) of its two parts."""
import numpy as np, pandas as pd, sys, b1_pair as B

def k0_block(N, U2, pairs):
    M2 = 2*N; idx = {p: i for i, p in enumerate(pairs)}
    tr = lambda p: tuple(sorted(((p[0]+2) % M2, (p[1]+2) % M2)))
    seen = set(); r, c, v = [], [], []; col = 0
    for p in pairs:
        if p in seen: continue
        orb = [p]; q = tr(p)
        while q != p: orb.append(q); q = tr(q)
        seen.update(orb)
        for s in orb: r.append(idx[s]); c.append(col); v.append(1/np.sqrt(len(orb)))
        col += 1
    import scipy.sparse as sp
    Bm = sp.csr_matrix((v, (r, c)), shape=(len(pairs), col)); return (Bm.conj().T@(U2@Bm)).toarray(), Bm

def probe(N, mu, theta):
    U2, pairs = B.two_particle(N, mu, theta); UK, Bm = k0_block(N, U2, pairs)
    lam, V = np.linalg.eig(UK); n2 = 1-mu**2
    eps_law = np.arccos(np.clip(n2 - mu**2*np.cos(theta), -1, 1))
    j = np.argmin(abs(lam - np.exp(-1j*eps_law)))          # one of the +/- pair; both are mirror images
    F = np.asarray(Bm@V[:, j]).ravel(); P = abs(F)**2; P /= P.sum()
    d = B.node_gap(pairs, N); Pd = np.bincount(d, weights=P, minlength=N//2+1)
    mean = (d*P).sum(); rms = np.sqrt((d**2*P).sum()); within1 = Pd[:2].sum()
    # tail decay length from log P(d) over the window where P(d) falls from 1e-2 to 1e-10 of its peak
    pk = Pd.max(); w = np.where((Pd < 1e-2*pk) & (Pd > 1e-10*pk))[0]
    ell = -1/np.polyfit(w, np.log(Pd[w]), 1)[0] if len(w) > 4 else np.nan   # decay length of probability
    return dict(N=N, mu=mu, theta_pi=theta/np.pi, clock=-np.angle(lam[j]), clock_law=eps_law,
                law_err=abs(abs(np.angle(lam[j]))-eps_law), mean_gap=mean, rms_gap=rms, P_gap_le1=within1,
                decay_len=ell, edge_P=Pd[-3:].sum()), Pd

if __name__ == '__main__':
    rows, prof = [], []
    for N in (240, 360):
        for mu in (0.8, 0.5, 0.3, 0.2, 0.1, 0.05):
            if N == 360 and mu > 0.1: continue
            for th in (0.25, 0.5, 0.75):
                r, Pd = probe(N, mu, th*np.pi); rows.append(r)
                prof += [dict(N=N, mu=mu, theta_pi=th, d=k, P=p) for k, p in enumerate(Pd)]
                print({k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    pd.DataFrame(rows).to_csv('c1_smooth_limit.csv', index=False); pd.DataFrame(prof).to_csv('c1_gap_profiles.csv', index=False)
