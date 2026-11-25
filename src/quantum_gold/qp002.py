"""QP-002: node-only held pairs. Exact two-coherence sector of the direct Dirac QCA with one both-full phase.
Vocabulary: clock = turns per tick; pair speed K = total phase-wind per node; gap = nodes between the two parts.
Rule (zero bags): node x = two yes/no slots (R_x, L_x). One tick = (1) edge exchange on (L_x, R_{x-1}) with the
one-coherence block [[-i mu, n],[n, -i mu]], n = sqrt(1-mu^2), both-full untouched; (2) in-node swap R_x <-> L_x,
both-full gets e^{i theta}. Ring of N nodes. `check` = validity only; `run` = all outcomes."""
import numpy as np, scipy.sparse as sp, itertools, pandas as pd, sys, os

def mode(s, x, N): return 2*(x % N)+s          # s=0 R, s=1 L

def layers(N, mu, theta):
    n = np.sqrt(1-mu**2); E = np.array([[-1j*mu, n], [n, -1j*mu]]); X = np.array([[0, 1], [1, 0]], complex)
    return [[((mode(1, x, N), mode(0, x-1, N)), E, 1.0) for x in range(N)],
            [((mode(0, x, N), mode(1, x, N)), X, np.exp(1j*theta)) for x in range(N)]]

def one_coherence(N, mu):
    W = np.eye(2*N, dtype=complex)
    for lay in layers(N, mu, 0.0):
        M = np.zeros((2*N, 2*N), complex)
        for (a, b), U, _ in lay: M[np.ix_([a, b], [a, b])] = U
        W = M@W
    return W

def two_coherence(N, mu, theta):
    pairs = list(itertools.combinations(range(2*N), 2)); idx = {p: i for i, p in enumerate(pairs)}; D = len(pairs)
    U2 = sp.identity(D, complex, format='csr')
    for lay in layers(N, mu, theta):
        g = {}
        for (a, b), U, ph in lay: g[a] = (a, b, U, ph, 0); g[b] = (a, b, U, ph, 1)
        r, c, v = [], [], []
        for j, (p, q) in enumerate(pairs):
            ap, bp, Up, php, ip = g[p]; aq, bq, Uq, phq, iq = g[q]
            if ap == aq: r.append(j); c.append(j); v.append(php); continue
            for op, mp_ in ((0, ap), (1, bp)):
                for oq, mq in ((0, aq), (1, bq)):
                    amp = Up[op, ip]*Uq[oq, iq]
                    if amp != 0: r.append(idx[tuple(sorted((mp_, mq)))]); c.append(j); v.append(amp)
        U2 = sp.csr_matrix((v, (r, c)), shape=(D, D))@U2
    return U2, pairs

def full_circuit_two(N, mu, theta):
    """Independent check: the full 2N-qubit circuit (gates on qubit pairs), restricted to two full slots."""
    nq = 2*N; dim = 2**nq; T = np.eye(dim, dtype=complex)
    for lay in layers(N, mu, theta):
        for (a, b), U, ph in lay:
            G4 = np.zeros((4, 4), complex); G4[0, 0] = 1; G4[1:3, 1:3] = U[::-1, ::-1]; G4[3, 3] = ph  # basis |ab>: 00,01,10,11
            T = apply2(T, G4, a, b, nq)
    _, pairs = two_coherence(N, mu, theta)
    bits = [sum(1 << (nq-1-m) for m in p) for p in pairs]
    return T[np.ix_(bits, bits)]

def apply2(T, G4, a, b, nq):
    T = T.reshape([2]*nq+[-1]); T = np.moveaxis(T, [a, b], [0, 1]); sh = T.shape
    T = (G4@T.reshape(4, -1)).reshape(sh); return np.moveaxis(T, [0, 1], [a, b]).reshape(2**nq, -1)

def k_block(N, U2, pairs, m):
    M2 = 2*N; idx = {p: i for i, p in enumerate(pairs)}; K = 2*np.pi*m/N
    tr = lambda p: tuple(sorted(((p[0]+2) % M2, (p[1]+2) % M2)))
    seen = set(); r, c, v = [], [], []; col = 0
    for p in pairs:
        if p in seen: continue
        orb = [p]; q = tr(p)
        while q != p: orb.append(q); q = tr(q)
        seen.update(orb)
        if (m*len(orb)) % N: continue
        for j, s in enumerate(orb): r.append(idx[s]); c.append(col); v.append(np.exp(-1j*K*j)/np.sqrt(len(orb)))
        col += 1
    Bm = sp.csr_matrix((v, (r, c)), shape=(len(pairs), col)); return K, (Bm.conj().T@(U2@Bm)).toarray(), Bm

def node_gap(pairs, N):
    a = np.array(pairs)//2; d = np.abs(a[:, 0]-a[:, 1]); return np.minimum(d, N-d)

def law_clock(mu, theta, K): return np.arccos(np.clip((1-mu**2)*np.cos(K)-mu**2*np.cos(theta), -1, 1))

def held_pair(N, mu, theta, ms, U2=None, pairs=None):
    """For each pair speed m: the eigenstate whose clock is nearest the law (either sign), its law error and gap profile."""
    if U2 is None: U2, pairs = two_coherence(N, mu, theta)
    d = node_gap(pairs, N); rows = []
    for m in ms:
        K, UK, Bm = k_block(N, U2, pairs, m); lam, V = np.linalg.eig(UK); e = law_clock(mu, theta, K)
        err = np.minimum(abs(lam-np.exp(-1j*e)), abs(lam-np.exp(1j*e))); j = np.argmin(err)
        F = np.asarray(Bm@V[:, j]).ravel(); P = abs(F)**2; P /= P.sum(); Pd = np.bincount(d, weights=P, minlength=N//2+1)
        rows.append(dict(N=N, mu=mu, theta_pi=theta/np.pi, m=m, K=K, clock=abs(np.angle(lam[j])), clock_law=e,
                         law_err=err[j], mean_gap=(d*P).sum(), P_far=Pd[N//4:].sum(), P_edge=Pd[-3:].sum()))
    return rows

def validity():
    out = {}
    mu, th, N = 0.37, 0.41*np.pi, 4
    A = full_circuit_two(N, mu, th); Bq, _ = two_coherence(N, mu, th); out['V1_circuit_err'] = np.max(abs(A-Bq.toarray()))
    N = 12; U2, pairs = two_coherence(N, mu, th); D = U2.shape[0]
    out['V2_unitary_err'] = np.max(abs((U2.conj().T@U2).toarray()-np.eye(D)))
    ev = np.concatenate([np.linalg.eigvals(k_block(N, U2, pairs, m)[1]) for m in range(N)])
    full = np.linalg.eigvals(U2.toarray())
    out['V3_blocks_count_ok'] = int(len(ev) == D)
    out['V3_blocks_err'] = max(np.min(abs(full[:, None]-ev[None, :]), 1).max(), np.min(abs(ev[:, None]-full[None, :]), 1).max())
    N = 40; W = one_coherence(N, mu); lam = np.linalg.eigvals(W); k = 2*np.pi*np.arange(N)/N
    pred = np.concatenate([np.exp(-1j*s*np.arccos(np.sqrt(1-mu**2)*np.cos(k))) for s in (1, -1)])
    out['V4_one_coherence_err'] = max(np.min(abs(lam[:, None]-pred[None, :]), 1).max(), np.min(abs(pred[:, None]-lam[None, :]), 1).max())
    return out

# ---------------- QP-002 frozen grids ----------------
LAW_N = 160; LAW_MU = [0.35, 0.65]; LAW_TH = [0.3, 0.6, 0.8]                     # all pair speeds m = 0..N/2
SIZE_MU = [0.24, 0.12, 0.06]; SIZE_TH = [0.4, 0.6, 0.8]; SIZE_N = {0.24: 160, 0.12: 240, 0.06: 432}   # K = 0

if __name__ == '__main__':
    mode_ = sys.argv[1] if len(sys.argv) > 1 else 'check'; od = 'qp002_out'; os.makedirs(od, exist_ok=True)
    v = validity(); print('VALIDITY', v, flush=True)
    if mode_ == 'check': sys.exit()
    law = []
    for mu in LAW_MU:
        for th in LAW_TH:
            law += held_pair(LAW_N, mu, th*np.pi, range(LAW_N//2+1)); print('law', mu, th, flush=True)
    law = pd.DataFrame(law); law.to_csv(f'{od}/qp002_law.csv', index=False)
    size = []
    for mu in SIZE_MU:
        for th in SIZE_TH:
            r = held_pair(SIZE_N[mu], mu, th*np.pi, [0])[0]; r['s'] = r['mean_gap']*mu*np.sin(th*np.pi/2); size.append(r)
            print('size', {k: r[k] for k in ('mu', 'theta_pi', 'N', 'mean_gap', 's', 'law_err', 'P_far')}, flush=True)
    size = pd.DataFrame(size); size.to_csv(f'{od}/qp002_size.csv', index=False)
    pd.DataFrame([v]).to_csv(f'{od}/qp002_validity.csv', index=False)
    with open(f'{od}/summary.txt', 'w') as f:
        f.write(f'VALIDITY {v}\n\nLAW per (mu, theta): max law_err, max P_far, min/max mean_gap\n')
        f.write(law.groupby(['mu', 'theta_pi']).agg(max_err=('law_err', 'max'), max_Pfar=('P_far', 'max'),
                min_gap=('mean_gap', 'min'), max_gap=('mean_gap', 'max')).to_string())
        f.write(f'\nLAW overall median err {law.law_err.median():.3e}\n\nSIZE\n' + size.to_string())
    print(open(f'{od}/summary.txt').read())
