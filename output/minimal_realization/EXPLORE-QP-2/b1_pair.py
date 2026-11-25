"""EXPLORE-QP-2 route B step 1 (exploratory). Node-only rule, zero bags.
Node x = two yes/no slots (R_x, L_x). One tick = edge exchange on (L_x, R_{x-1}) [one-coherence block
[[-i mu, n],[n, -i mu]], both-full untouched as frozen] then in-node swap R_x<->L_x [both-full gets e^{i theta}].
This is the frozen direct Dirac QCA (LOCALIZATION_AUDIT) with ONE added phase. Two coherences, ring of N nodes,
exact: the number of full slots is conserved, translation by one node commutes with the tick -> blocks of fixed
total phase-wind K. Held pair = eigenstate whose two coherences stay within a few nodes of each other."""
import numpy as np, scipy.sparse as sp, itertools

def mode(s, x, N): return 2*(x % N)+s          # s=0 R, s=1 L

def layers(N, mu, theta, edge_phase=1.0):
    n = np.sqrt(1-mu**2); E = np.array([[-1j*mu, n], [n, -1j*mu]]); X = np.array([[0, 1], [1, 0]], complex)
    edge = [((mode(1, x, N), mode(0, x-1, N)), E, edge_phase) for x in range(N)]
    swap = [((mode(0, x, N), mode(1, x, N)), X, np.exp(1j*theta)) for x in range(N)]
    return [edge, swap]

def one_particle(N, mu):
    W = np.eye(2*N, dtype=complex)
    for lay in layers(N, mu, 0.0):
        M = np.zeros((2*N, 2*N), complex)
        for (a, b), U, _ in lay: M[np.ix_([a, b], [a, b])] = U
        W = M@W
    return W

def two_particle(N, mu, theta, edge_phase=1.0):
    M2 = 2*N; pairs = list(itertools.combinations(range(M2), 2)); idx = {p: i for i, p in enumerate(pairs)}; D = len(pairs)
    U2 = sp.identity(D, complex, format='csr')
    for lay in layers(N, mu, theta, edge_phase):
        g = {}; 
        for (a, b), U, ph in lay: g[a] = (a, b, U, ph, 0); g[b] = (a, b, U, ph, 1)
        r, c, v = [], [], []
        for j, (p, q) in enumerate(pairs):
            ap, bp, Up, php, ip = g[p]; aq, bq, Uq, phq, iq = g[q]
            if ap == aq:                                  # both slots of one gate full
                r.append(j); c.append(j); v.append(php); continue
            for op, mp_ in ((0, ap), (1, bp)):
                for oq, mq in ((0, aq), (1, bq)):
                    amp = Up[op, ip]*Uq[oq, iq]
                    if amp != 0: r.append(idx[tuple(sorted((mp_, mq)))]); c.append(j); v.append(amp)
        U2 = sp.csr_matrix((v, (r, c)), shape=(D, D))@U2
    return U2, pairs

def k_blocks(N, U2, pairs):
    """Project onto total phase-wind K = 2 pi m / N via translation orbits."""
    M2 = 2*N; idx = {p: i for i, p in enumerate(pairs)}
    tr = lambda p: tuple(sorted(((p[0]+2) % M2, (p[1]+2) % M2)))
    seen = set(); orbits = []
    for p in pairs:
        if p in seen: continue
        orb = [p]; q = tr(p)
        while q != p: orb.append(q); q = tr(q)
        seen.update(orb); orbits.append(orb)
    out = {}
    for m in range(N):
        K = 2*np.pi*m/N; r, c, v = [], [], []; col = 0; reps = []
        for orb in orbits:
            L = len(orb)
            if (m*L) % N: continue                        # short orbit incompatible with this K
            for j, p in enumerate(orb): r.append(idx[p]); c.append(col); v.append(np.exp(-1j*K*j)/np.sqrt(L))
            reps.append(orb[0]); col += 1
        B = sp.csr_matrix((v, (r, c)), shape=(len(pairs), col))
        out[m] = (K, (B.conj().T@(U2@B)).toarray(), B)
    return out

def node_gap(pairs, N):
    a = np.array(pairs)//2; d = np.abs(a[:, 0]-a[:, 1]); return np.minimum(d, N-d)
