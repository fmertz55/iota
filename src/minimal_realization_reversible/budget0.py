"""MIR-REVERSIBLE-BUDGET-000: exact additive invariants of the 25 shadow rules (rules only; no shadow outcomes).

State: cells (p_i, c_i) = (x[t-1]_i, x[t]_i), cell code 2p+c. Step: (p, c) -> (c, f(c_{i-1}, c_i, c_{i+1}) XOR p).
A window-k density phi is conserved on every ring (and on the line, for finite perturbations of a homogeneous
background) iff its one-step change Delta(w) on (k+2)-cell words is a coboundary h(w[1:]) - h(w[:-1])
(Livsic-type criterion on the full shift; cf. Hattori & Takesue 1991). Joint linear system in (phi, h);
nontrivial count = dim(phi-projection of the null space) - dim(constants + coboundaries) = ... - 4^(k-1).
Ranks: float SVD and two prime moduli must agree (k <= 3); float only at k = 4.
Densities at k = 2 are extracted with exact rational elimination and written in a normal form: monomials in
p0, c0, p1, c1 (cell i, cell i+1), with the constant and cell-(i+1)-only terms folded away. In this form the
homogeneous vacuum has density 0 in every phase, so the budget of a finite disturbance is sum_i phi.
"""
import itertools, json, sys
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-BUDGET-000'
RULES = [(22, 1), (26, 1), (33, 0), (37, 0), (54, 1), (82, 1), (91, 0), (94, 1), (123, 0), (139, 0), (147, 0),
         (201, 0), (209, 0), (218, 1), (58, 1), (114, 1), (143, 0), (151, 0), (154, 1), (171, 0), (182, 1),
         (186, 1), (213, 0), (233, 0), (241, 0)]  # (Wolfram code, silent vacuum f(000)=0)
NULLS = [1, 5, 90]
PRIMES = (2147483647, 1000000007)


def words(n):
    return np.array(list(itertools.product(range(4), repeat=n)), dtype=np.int64)


def enc(W):
    v = np.zeros(len(W), dtype=np.int64)
    for j in range(W.shape[1]):
        v = v * 4 + W[:, j]
    return v


def image(w, W):
    p, c = W // 2, W % 2
    f = (w >> (4 * c[:, :-2] + 2 * c[:, 1:-1] + c[:, 2:])) & 1
    return 2 * c[:, 1:-1] + (f ^ p[:, 1:-1])


def system(w, k):
    m = k + 2; W = words(m); nphi, nh = 4 ** k, 4 ** (m - 1); R = np.arange(len(W))
    A = np.zeros((len(W), nphi + nh), dtype=np.int64)
    np.add.at(A, (R, enc(image(w, W))), 1); np.add.at(A, (R, enc(W[:, 1:-1])), -1)
    np.add.at(A, (R, nphi + enc(W[:, 1:])), -1); np.add.at(A, (R, nphi + enc(W[:, :-1])), 1)
    return A, nphi


def rank_mod(A, p):
    A = (A % p).astype(np.int64); r = 0
    for c in range(A.shape[1]):
        piv = np.nonzero(A[r:, c])[0]
        if not len(piv):
            continue
        i = r + piv[0]; A[[r, i]] = A[[i, r]]; A[r] = (A[r] * pow(int(A[r, c]), p - 2, p)) % p
        for j in np.nonzero(A[:, c])[0]:
            if j != r:
                A[j] = (A[j] - A[j, c] * A[r]) % p
        r += 1
        if r == A.shape[0]:
            break
    return r


def n_nontrivial(w, k):
    A, nphi = system(w, k)
    rk = [lambda M: int(np.linalg.matrix_rank(M.astype(float)))]
    if k <= 3:
        rk += [lambda M, p=p: rank_mod(M, p) for p in PRIMES]
    vals = {(A.shape[1] - r(A)) - (A.shape[1] - nphi - r(A[:, nphi:])) - 4 ** (k - 1) for r in rk}
    assert len(vals) == 1, (w, k, vals)
    return vals.pop()


def rref(M):
    M = [[x if isinstance(x, Fraction) else Fraction(int(x)) for x in row] for row in M]; piv, r = [], 0
    for c in range(len(M[0])):
        i = next((i for i in range(r, len(M)) if M[i][c]), None)
        if i is None:
            continue
        M[r], M[i] = M[i], M[r]; M[r] = [x / M[r][c] for x in M[r]]
        for j in range(len(M)):
            if j != r and M[j][c]:
                M[j] = [a - M[j][c] * b for a, b in zip(M[j], M[r])]
        piv.append(c); r += 1
    return M[:r], piv


def nullspace(A):
    R, piv = rref(A); n = len(A[0]); free = [c for c in range(n) if c not in piv]; out = []
    for f in free:
        v = [Fraction(0)] * n; v[f] = Fraction(1)
        for row, pc in zip(R, piv):
            v[pc] = -row[f]
        out.append(v)
    return out


B2 = words(2); P0, C0, P1, C1 = B2[:, 0] // 2, B2[:, 0] % 2, B2[:, 1] // 2, B2[:, 1] % 2
NF = [('p0', P0), ('c0', C0), ('p0c0', P0 * C0), ('p0p1', P0 * P1), ('p0c1', P0 * C1), ('c0p1', C0 * P1),
      ('c0c1', C0 * C1), ('p0c0p1', P0 * C0 * P1), ('p0c0c1', P0 * C0 * C1), ('p0p1c1', P0 * P1 * C1),
      ('c0p1c1', C0 * P1 * C1), ('p0c0p1c1', P0 * C0 * P1 * C1)]
MNF = np.column_stack([v for _, v in NF])
TRIV = np.column_stack([np.ones(16, int), P1 - P0, C1 - C0, P1 * C1 - P0 * C0])
FULL = np.column_stack([MNF, TRIV])  # 16 x 16, invertible


def densities(w):
    A, nphi = system(w, 2); coords = []
    for v in nullspace(A.tolist()):
        aug, piv = rref([list(FULL[i]) + [v[i]] for i in range(16)])  # exact solve FULL x = phi
        assert piv == list(range(16))
        coords.append([row[16] for row in aug[:12]])
    R, _ = rref(coords) if coords else ([], [])
    out = []
    for r in R:
        if not any(r):
            continue
        L = np.lcm.reduce([q.denominator for q in r]); out.append([int(q * L) for q in r])
    return out


def fmt(r):
    s = ' '.join(f"{'+' if q > 0 else '-'} {'' if abs(q) == 1 else abs(q)}{NF[j][0]}" for j, q in enumerate(r) if q)
    return s[2:] if s.startswith('+ ') else s


def total(coef, p, c):
    cell = 2 * p + c; return (MNF @ np.array(coef))[4 * cell + np.roll(cell, -1, axis=-1)].sum(-1)


def stepv(w, p, c):
    return c, ((w >> (4 * np.roll(c, 1, -1) + 2 * c + np.roll(c, -1, -1))) & 1) ^ p


def check(w, basis, rng):
    for L in (37, 64, 101):
        p, c = rng.integers(0, 2, (50, L)), rng.integers(0, 2, (50, L)); E0 = [total(b, p, c) for b in basis]
        for _ in range(400):
            p, c = stepv(w, p, c)
        if not all((total(b, p, c) == e).all() for b, e in zip(basis, E0)):
            return False
    return True


def vacuum(w, basis):
    p, c, orb = np.zeros(5, int), np.zeros(5, int), []
    while (int(p[0]), int(c[0])) not in orb:
        orb.append((int(p[0]), int(c[0]))); p, c = stepv(w, p, c)
    return orb, [[int(total(b, np.full(5, q), np.full(5, r))) / 5 for q, r in orb] for b in basis]


def main():
    OUT.mkdir(parents=True, exist_ok=True); rng = np.random.default_rng(0)
    TRIVD = {k: int(np.linalg.matrix_rank(np.column_stack([np.ones(4 ** k)] + ([] if k == 1 else [
        np.eye(4 ** (k - 1))[enc(words(k)[:, 1:])] - np.eye(4 ** (k - 1))[enc(words(k)[:, :-1])]])))) for k in (1, 2, 3)}
    assert TRIVD == {1: 1, 2: 4, 3: 16}, TRIVD
    res = {}
    for w, s in RULES + [(x, None) for x in NULLS]:
        n = {k: n_nontrivial(w, k) for k in (1, 2, 3, 4)}
        e = dict(silent=s, nontrivial_by_window=n)
        if s is not None and n[2] > 0:
            b = densities(w); assert len(b) == n[2], (w, len(b), n)
            orb, vd = vacuum(w, b)
            e.update(window2_basis=[fmt(r) for r in b], window2_coeffs=b, simulation_conserved=check(w, b, rng),
                     vacuum_orbit=orb, vacuum_density=vd)
        res[w] = e; print(w, e.get('silent'), n, e.get('window2_basis', ''), e.get('simulation_conserved', ''), flush=True)
    (OUT / 'results.json').write_text(json.dumps(dict(id='MIR-REVERSIBLE-BUDGET-000', monomials=[m for m, _ in NF],
                                                      rules=res), indent=1))


if __name__ == '__main__':
    main()
