# Direct Symmetry-Derived Dirac QCA — Outcome-Free Design Kickoff

Search ID: `ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001`

Status: **localization and continuum audits passed; protocol design next; registered outcomes forbidden**

## Question

Can a direct homogeneous causal Dirac QCA, derived from unitarity and discrete
symmetries rather than Lie-Trotter gate ordering, recover a frozen bounded
1+1D Dirac operational role under an explicit local-circuit resource model?

This is an architectural breadth test. It is not a robustness sweep of the
successful product walk and must not inherit that experiment's positive
classification, thresholds, or confirmation allocation by default.

## Parent evidence and claim boundary

The parent experiment established bounded constructive sufficiency for one
product-walk architecture. Its verified result motivates this design but does
not count as data for this candidate. The immutable parent bindings are in
`parent_binding.json`.

A future pass could support only that a second, symmetry-derived architecture
is constructively sufficient in its own frozen domain. It would not establish
minimality, uniqueness, generic emergence of quantum theory, or equivalence
between the two architectures outside their shared registered observables.

## Candidate law

For lattice spacing and time step `delta`, define the dimensionless mass
`mu = m delta` and `n = sqrt(1 - mu^2)`. On the one-excitation sector, the
translation-invariant update has momentum block

```text
U_delta(k) = [[n exp(-i k delta), -i mu],
              [-i mu,              n exp(+i k delta)]].
```

Equivalently in real space,

```text
R'(x) = n R(x + 1) - i mu L(x)
L'(x) = -i mu R(x) + n L(x - 1).
```

The update is exactly unitary when `n^2 + mu^2 = 1`. Unlike the successful
parent, its mass coupling and directional propagation are entries of one
direct QCA update rather than a sequential coin/transport product.

## Required architectural contrast

| Coordinate | Verified parent | This experiment |
|---|---|---|
| Finite-lattice law | Product phase, mass mix, swaps | Direct symmetry-derived block |
| Mass/transport relation | Ordered sublayers | One exact QCA update |
| Leading discretization mechanism | Lie-Trotter ordering | Nonlinear `n=sqrt(1-mu^2)` normalization |
| Localization | Two declared swap layers | Edge scatter then on-site SWAP; full-space audit passed |
| Symmetry status | Numerically certified on input sector | Full-space parity and time reversal derived |

## Outcome-free work stages

1. **Algebraic fixture stage (complete).** On nonregistered sizes only, verify
   exact update construction, high-precision unitarity, translation
   covariance, massless directional motion, and rejection of registered sizes.
2. **Localization stage (complete).** Give an explicit finite-depth Margolus
   or equivalent local-unitary realization on the full local Hilbert space,
   including vacuum and multi-excitation action. Count elementary gates
   without borrowing the parent's resource normalization. The proof and
   accounting are in `LOCALIZATION_AUDIT.md`.
3. **Symmetry and continuum stage (complete).**
   Derive parity and time-reversal maps for the localized update; derive the
   small-`delta` effective generator and identify the first nonzero correction
   independently. The derivation and independent matrix-log check are in
   `CONTINUUM_AUDIT.md`.
4. **Protocol stage.** Only after stages 1–3 pass, freeze target maps,
   interventions, states, scenario partitions, refinement sizes, metrics,
   thresholds, failure controls, and a separately implemented verifier.
5. **Lifecycle stage.** Build disabled production code, seal all causal inputs,
   and use a fresh linear freeze/open/result/verification history. No parent
   holdout case may be silently reused as a new holdout.

## Pre-registration stop conditions

Stop before any registered outcome if:

- no explicit local-unitary realization preserves the declared direct update
  with auditable finite depth;
- the proposed full-space update is unitary only in the one-excitation sector;
- parity or time reversal requires an outcome-dependent convention;
- resource accounting cannot be compared without hiding ancillas or substeps;
- the independent fixture implementation is not algorithmically separate; or
- any registered size, state, scenario, or threshold is evaluated before a
  new outcome seal and opening manifest exist.

## Current disposition and next concrete task

The full-space Margolus localization succeeds with a mass-bearing edge
scatter followed by an on-site routing SWAP. It has depth `2`, gate-work
`2N`, storage `2N` qubits, local dimension `4`, causal radius `1`, and no
ancillas. Its one-excitation restriction is exactly the declared law, while
vacuum and collision-sector actions are explicitly declared rather than
inferred. See `LOCALIZATION_AUDIT.md` and the guarded fixture implementation.

The small-`delta` audit also succeeds. The exact principal effective generator
is `H_D + delta^2 K_2 + O(delta^4)`, with the independently checked correction
given in `CONTINUUM_AUDIT.md`. Signed-step reversal is exact and the effective
generator is even in `delta`.

Next begin outcome-free prospective protocol design without evaluating a
registered size or opening development/confirmation partitions.
