# Direct Symmetry-Derived Dirac QCA — Outcome-Free Design Kickoff

Search ID: `ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001`

Status: **conceptual and algebraic fixtures only; registered outcomes forbidden**

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
| Localization obligation | Two declared swap layers | Explicit Margolus or equivalent construction still required |
| Symmetry question | Numerically certified on input sector | Must be derived for the localized update before registration |

## Outcome-free work stages

1. **Algebraic fixture stage (started).** On nonregistered sizes only, verify
   exact update construction, high-precision unitarity, translation
   covariance, massless directional motion, and rejection of registered sizes.
2. **Localization stage.** Give an explicit finite-depth Margolus or equivalent
   local-unitary realization on the full local Hilbert space, including vacuum
   and multi-excitation action. Count elementary gates without borrowing the
   parent's resource normalization.
3. **Symmetry and continuum stage.** Derive parity and time-reversal maps for
   the localized update; derive the small-`delta` effective generator and
   identify the first nonzero correction independently.
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

## Next concrete task

Construct and test the full-space Margolus localization. The output should be
a gate-level identity proof or a precise no-go result, plus resource counts.
Do not define development/confirmation partitions until that task is closed.
