"""EXPLORE-QP-3 probe 1: the filled vacuum alone (fork a, all R full). Exploratory, not a contract.
Rule = frozen QP-002 rule, unchanged (src/quantum_gold/qp002.py layers): node x = slots (R_x, L_x), plain yes/no
switches (no sign rule). Tick = (1) edge exchange on (L_x, R_{x-1}), one-coherence block [[-i mu, n],[n, -i mu]],
both-full untouched; (2) in-node swap R_x <-> L_x, both-full gets e^{i theta}. Ring of N nodes.
Exact: every state with N full slots out of 2N is kept (state vector, no matrices).
Vacuum A = all R full. Changed copy B = A with node 0's full slot moved R -> L (same number of full slots).
Read-outs (nodes' own slots only): return chance of A; per-node trace distance A vs B (cone); far-half and near-half
block trace distance A vs B and far-half entropy of A (where the change's information lives); forward-then-back check.
"""
import numpy as np, sys, os, time, itertools, pandas as pd

def mode(s, x, N): return 2*(x % N)+s          # s=0 R, s=1 L  (same as qp002.mode)

def gate_list(N, mu, theta):
    n = np.sqrt(1-mu**2)
    edge = [('E', mode(1, x, N), mode(0, x-1, N)) for x in range(N)]
    swap = [('X', mode(0, x, N), mode(1, x, N)) for x in range(N)]
    return edge+swap, n

def popcount(a):
    c = np.zeros_like(a)
    while True:
        nz = a != 0
        if not nz.any(): return c
        c += a & 1; a = a >> 1

class Sector:
    def __init__(self, N, k):
        self.N, self.k, self.M = N, k, 2*N
        allb = np.arange(1 << self.M, dtype=np.int64)
        self.st = allb[popcount(allb.copy()) == k]             # sorted
        self.D = len(self.st)
        self.cache = {}
    def idx(self, s): return np.searchsorted(self.st, s).astype(np.int64)
    def pair(self, a, b):
        key = (a, b)
        if key not in self.cache:
            ba = (self.st >> a) & 1; bb = (self.st >> b) & 1
            one = np.nonzero(ba ^ bb)[0]; both = np.nonzero(ba & bb)[0]
            part = self.idx(self.st[one] ^ ((1 << a) | (1 << b)))
            self.cache[key] = (one, part, both)
        return self.cache[key]

def tick(psi, S, gates, mu, n, theta, inverse=False):
    seq = gates[::-1] if inverse else gates
    for g, a, b in seq:
        one, part, both = S.pair(a, b)
        if g == 'E':
            d = (1j if inverse else -1j)*mu
            new = psi.copy(); new[one] = d*psi[one]+n*psi[part]; psi = new
        else:
            new = psi.copy(); new[one] = psi[part]; new[both] *= np.exp((-1j if inverse else 1j)*theta); psi = new
    return psi

def node_rho(psi, S, x):
    """4 numbers + coherence: p00, pR, pL, p11, c = <R|rho|L>."""
    p = np.abs(psi)**2; r = (S.st >> mode(0, x, S.N)) & 1; l = (S.st >> mode(1, x, S.N)) & 1
    one, part, _ = S.pair(mode(0, x, S.N), mode(1, x, S.N))
    sel = r[one] == 1
    c = np.sum(psi[one[sel]]*np.conj(psi[part[sel]]))
    return np.array([p[(r == 0) & (l == 0)].sum(), p[(r == 1) & (l == 0)].sum(), p[(r == 0) & (l == 1)].sum(),
                     p[(r == 1) & (l == 1)].sum()]), c

def node_td(ra, ca, rb, cb):
    d = ra-rb; blk = np.array([[d[1], ca-cb], [np.conj(ca-cb), d[2]]])
    return 0.5*(abs(d[0])+abs(d[3])+np.abs(np.linalg.eigvalsh(blk)).sum())

class Block:
    """Split the ring into a far half (N/2 nodes farthest from node 0) and the near half."""
    def __init__(self, S):
        N = S.N; h = N//2; s0 = -(-N//4); self.far = [(s0+j) % N for j in range(h)]
        self.near = [x for x in range(N) if x not in self.far]
        fm = [mode(s, x, N) for x in self.far for s in (0, 1)]; nm = [mode(s, x, N) for x in self.near for s in (0, 1)]
        fc = np.zeros(S.D, np.int64); nc = np.zeros(S.D, np.int64)
        for j, m in enumerate(fm): fc |= ((S.st >> m) & 1) << j
        for j, m in enumerate(nm): nc |= ((S.st >> m) & 1) << j
        fk = popcount(fc.copy()); self.blocks = []
        for k in np.unique(fk):
            sel = np.nonzero(fk == k)[0]
            fu, fr = np.unique(fc[sel], return_inverse=True); nu, nr = np.unique(nc[sel], return_inverse=True)
            self.blocks.append((sel, fr, nr, len(fu), len(nu)))
    def rhos(self, psi):
        out = []
        for sel, fr, nr, cf, cn in self.blocks:
            Mx = np.zeros((cf, cn), complex); Mx[fr, nr] = psi[sel]; out.append((Mx@Mx.conj().T, Mx.T@Mx.conj()))
        return out   # (far rho, near rho) per block

def td_and_entropy(ra, rb):
    tdf = tdn = 0.0; ent = 0.0
    for (fa, na), (fb, nb) in zip(ra, rb):
        tdf += 0.5*np.abs(np.linalg.eigvalsh(fa-fb)).sum(); tdn += 0.5*np.abs(np.linalg.eigvalsh(na-nb)).sum()
        w = np.linalg.eigvalsh(fa); w = w[w > 1e-15]; ent -= np.sum(w*np.log2(w))
    return tdf, tdn, ent

def run(N, mu, theta, T, S=None, B=None):
    S = S or Sector(N, N); B = B or Block(S); gates, n = gate_list(N, mu, theta)
    vac = sum(1 << mode(0, x, N) for x in range(N)); chg = vac ^ (1 << mode(0, 0, N)) ^ (1 << mode(1, 0, N))
    A = np.zeros(S.D, complex); A[S.idx(vac)] = 1; Bv = np.zeros(S.D, complex); Bv[S.idx(chg)] = 1
    A0, B0 = A.copy(), Bv.copy(); rows = []
    for t in range(T+1):
        if t > 0: A = tick(A, S, gates, mu, n, theta); Bv = tick(Bv, S, gates, mu, n, theta)
        rows_n = []
        for x in range(N):
            ra, ca = node_rho(A, S, x); rb, cb = node_rho(Bv, S, x); rows_n.append((x, ra, ca, node_td(ra, ca, rb, cb)))
        tdf, tdn, ent = td_and_entropy(B.rhos(A), B.rhos(Bv))
        p = np.abs(A)**2
        row = dict(N=N, mu=mu, theta_pi=theta/np.pi, t=t, ret_A=abs(np.vdot(A0, A))**2, pr_A=1/np.sum(p**2),
                   td_far=tdf, td_near=tdn, S_far_bits=ent, normA=np.linalg.norm(A), normB=np.linalg.norm(Bv))
        for x, ra, ca, td in rows_n:
            d = min(x, N-x); row[f'td_n{x}'] = td
            if x == 0: row.update(R0=ra[1]+ra[3], L0=ra[2]+ra[3], both0=ra[3], none0=ra[0])
        row['mean_R'] = np.mean([ra[1]+ra[3] for _, ra, _, _ in rows_n]); row['mean_both'] = np.mean([ra[3] for _, ra, _, _ in rows_n])
        rows.append(row)
    Bb = Bv.copy()
    for t in range(T): Bb = tick(Bb, S, gates, mu, n, theta, inverse=True)
    back = abs(np.vdot(B0, Bb))**2
    for r in rows: r['back_fid_B'] = back
    return rows
