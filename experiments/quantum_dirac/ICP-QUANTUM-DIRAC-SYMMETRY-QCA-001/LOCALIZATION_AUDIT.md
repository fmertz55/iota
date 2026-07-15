# Full-Hilbert-Space Margolus Localization Audit

Search ID: `ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001`

Status: **existence audit passed; outcome-free; no registered evaluation**

## Audit conclusion

The direct one-excitation law has an exact, homogeneous, strictly local
partitioned realization on the same resource class used by the parent: two
occupation qubits per cell and local Hilbert dimension four.  It requires two
causally ordered layers and no ancilla, global translation gate, Fourier
operation, size-dependent control, or Jordan--Wigner string.

This is an existence result, not a registered Dirac-role outcome.  It also
does not make the full-space extension unique: the displayed `2N`-dimensional
law does not determine phases or scattering in collision sectors.  The
extension used here declares those sectors explicitly below.

## Local state and gates

At each cell `x`, take

```text
H_x = C^2_(R_x) tensor C^2_(L_x),       dim(H_x) = 4.
```

The full Hilbert space is `tensor_x H_x`, of dimension `4^N`.  No restriction
to one excitation is imposed on the construction.

Let `n = sqrt(1 - mu^2)`.  On the edge subcells `(L_x, R_(x-1))`, in basis
`|00>, |01>, |10>, |11>`, define

```text
                 [ 1      0       0     0 ]
b_mu =           [ 0    -i mu     n     0 ]
                 [ 0      n     -i mu   0 ]
                 [ 0      0       0     1 ].
```

Thus vacuum and double occupation on an edge pair are fixed, while the
one-excitation block in mode-amplitude order `(L_x, R_(x-1))` is

```text
C_mu = [[-i mu, n],
        [n, -i mu]].
```

The `x-1` orientation is prospective and candidate-defining. The first draft
used `x+1`; guarded production construction showed that choice has the wrong
massless phase under the contract's fixed `exp(+ikx)` convention. Reversing
the edge orientation before freeze makes this localized layer restrict to the
audited momentum block rather than its sign-reversed partner.

The on-site gate `a_x` is the ordinary qubit SWAP on `(R_x,L_x)`, including
identity action on `|00>` and `|11>`.

The two global partition layers are

```text
B_mu = product_x b_mu[L_x, R_(x-1)]     edge scatter
A    = product_x SWAP[R_x, L_x]         on-site routing

U_full(mu) = A B_mu.                    causal order: B_mu then A
```

Within either product, all gates have disjoint subcell support.  A cell
participates through different tensor factors in the two neighboring edge
gates, so there is no overlap inside the edge layer.

## Exact unitarity

Write `X` for the Pauli exchange matrix on the one-excitation subspace.  Then

```text
C_mu = n X - i mu I,
C_mu^dagger C_mu = (n^2 + mu^2) I = I.
```

The zero- and two-excitation blocks of `b_mu` are one-dimensional identities,
so `b_mu` is unitary on all four local basis states.  Each `a_x` is a unitary
involution.  Products of the disjoint gates are unitary, hence `U_full` is
unitary on all `4^N` states.  Its exact inverse uses the reverse causal order:

```text
U_full(mu)^dagger = B_(-mu) A.
```

This proof does not infer full-space unitarity from the one-excitation Gram
matrix.

## Exact restriction to the declared direct QCA

Before the routing layer, the edge gates give one-excitation amplitudes

```text
(B_mu psi)_R(x) = -i mu R(x) + n L(x+1),
(B_mu psi)_L(x) =  n R(x-1) - i mu L(x).
```

The on-site SWAP exchanges these two output channels.  Therefore

```text
(A B_mu psi)_R(x) = n R(x-1) - i mu L(x),
(A B_mu psi)_L(x) = -i mu R(x) + n L(x+1),
```

which is exactly the candidate law, coefficient by coefficient.  No equality
up to a size-dependent phase is used.  Fixing the edge vacuum block to one is
important here: extending `n SWAP - i mu I` indiscriminately to all four
two-qubit states would add spectator phases and would not give this exact
restriction.

At `mu=0`, `B_0` is the edge SWAP and `A` is the on-site SWAP.  Their opposite
channel shifts cancel the net transport obstruction; the mass-bearing edge
scatter continuously deforms this same two-layer partition without adding a
translation primitive.

## Homogeneity, symmetries, and causal support

Every edge receives the same `b_mu` and every cell receives the same `a_x`.
Cell translation permutes gates inside each layer, so

```text
[U_full, T] = 0.
```

Let `J` reflect cells by `x -> -x`, let `A` exchange `R` and `L` on every
cell, and let `K` be complex conjugation in the occupation basis.  The
full-space parity and time-reversal maps are

```text
P     = A J,
Theta = A K.
```

Because `b_mu` is symmetric under exchange of its two subcells,
`J B_mu J = A B_mu A`, which gives

```text
P U_full P^dagger = U_full.
```

Because `B_mu^* = B_mu^dagger = B_(-mu)` and `A` is real,

```text
Theta U_full Theta^(-1) = B_mu^dagger A = U_full^dagger.
```

The statement is antiunitary time-reversal covariance, not commutation with
`K` alone.

For causal support, conjugating an output-cell observable backward through
`A` keeps it on that cell.  Conjugating through `B_mu` can then touch only the
two edge pairs incident on its `R` and `L` subcells.  One macrostep therefore
has exact cell radius one.  The implementation applies only these gates and
contains no whole-array roll or translation operation.

## Resource clock

One physical macrostep advances the direct-QCA time by `delta_t` and contains
the following elapsed elementary layers:

```text
1. N parallel edge-scatter gates b_mu[L_x, R_(x-1)]
2. N parallel on-site SWAP gates SWAP[R_x, L_x]
```

| Coordinate | Direct localized value | Parent free-step value |
|---|---:|---:|
| local Hilbert dimension | `4` | `4` |
| occupation storage | `2N` qubits | `2N` modes |
| ancilla storage | `0` | `0` |
| causal radius per macrostep | `1` | `1` |
| elapsed elementary layers per macrostep | `2` | `3` |
| local/two-mode gate-work per macrostep | `2N` | `3N` |

The comparison uses the parent's declared granularity, under which an
arbitrary number-preserving two-mode mixer and a SWAP each count as one gate.
If a later protocol compiles gates into a hardware universal basis, it must
prospectively compile and charge both architectures at that new granularity.
A macrostep must not be called one elementary tick: after `M` macrosteps the
direct construction has elapsed `2M` elementary layers and performed `2NM`
two-mode gates.

## Full-space choice and claim boundary

The fixture implementation chooses identity action on the zero- and
two-occupation sectors of each edge gate.  This gives an ordinary qubit
tensor-product QCA with hard-core occupation modes and exact local gates.  It
is not presented as the uniquely induced collision law or as a canonical
fermionic second quantization.  Those alternatives can differ by local
collision phases while sharing the same one-excitation matrix.

The choice is not hidden structure: both qubits per cell, all `4^N` basis
states, the collision action, cyclic edge, gate order, precision, depth,
work, and absence of ancillas are declared.  Requiring a qutrit cell with
double occupation removed, or requiring a particular fermionic Fock lift,
would be a different architectural constraint and would need its own audit.

## Executable evidence and disposition

`src/quantum_dirac_symmetry_qca/localization.py` implements the sparse
full-space gates without allocating a dense `4^N` matrix.  Public access
remains restricted to disclosed `N=6` and `N=10` fixtures.  The tests verify:

- four-state local-gate unitarity and explicit spectator-sector action;
- equality with the direct law on every one-excitation basis state at both
  disclosed sizes;
- vacuum and saturated-state action;
- inverse recovery on a superposition spanning several number sectors;
- full-space translation and parity covariance;
- full-space antiunitary time reversal; and
- storage, elapsed-layer, gate-work, radius, and causal-order accounting.

The localization stop conditions are not triggered.  This closes the
full-space locality obligation only.  No scenario, threshold, partition,
seal, opening manifest, registered size, or result is introduced.  The later
small-`delta` and complete-Brillouin-zone obligations are now resolved in
`CONTINUUM_AUDIT.md` and `GLOBAL_SPECTRUM_AUDIT.md`; the latter preserves this
document's explicit hard-core-versus-fermionic lift boundary.
