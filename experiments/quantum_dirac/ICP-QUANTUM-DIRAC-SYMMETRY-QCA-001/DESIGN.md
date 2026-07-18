# Direct Symmetry-Derived Dirac QCA — Outcome-Free Prospective Design

Search ID: `ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001`

Status: **historical outcome-free design snapshot; v0.4 subsequently passed development, confirmation, and independent replay**

> Post-result note (`2026-07-18`): the v0.4 lineage froze, passed its
> independently reconstructed development batch, opened the single-use
> confirmation partition, and passed confirmation plus independent replay.
> A later semantic audit withdrew the empirical pi-sector reducer because both
> implementations selected an empty sector; the correctly derived analytic
> tail remains valid. The authoritative qualified outcome is in `RESULTS.md`
> and `POST_RESULT_AUDIT.md`. The remainder of this
> document preserves the prospective design state and should be read in that
> historical tense.

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
R'(x) = n R(x - 1) - i mu L(x)
L'(x) = -i mu R(x) + n L(x + 1).
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
4. **Global spectrum and lift stage (complete).** Audit the complete
   Brillouin zone, quasienergy branches, group velocity, doubling or
   pseudodoubling, mass endpoints, and the dependence on hard-core versus
   canonical fermionic collision sectors. The result and mandatory protocol
   boundaries are in `GLOBAL_SPECTRUM_AUDIT.md`.
5. **Protocol stage (outcome-free draft complete).** After stages 1–4, fix target maps,
   interventions, states, scenario partitions, refinement sizes, metrics,
   proposed thresholds, failure controls, and the required independent-verifier
   architecture. Do not freeze until production and independent code pass and
   all draft inputs receive hostile review.
6. **Implementation and lifecycle stage.** Build disabled production and
   independent code, prospective manifests, and authorization; then seal all causal inputs,
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

The full-zone audit is complete. It finds no traditional zero-energy doubler
in `1+1D`, but it does find the exact pi-mode relation
`U_mu(-pi+p)=-U_-mu(p)`. This is a high-quasienergy opposite-mass
pseudodoubler and a mandatory low-momentum/leakage boundary. The audit also
shows that the chosen hard-core qubit collision phases are not the canonical
fermionic lift. See `GLOBAL_SPECTRUM_AUDIT.md` and the dated literature log.

The outcome-free prospective protocol is now explicit in
`specs/icp_quantum_dirac_symmetry_qca/v0.1-draft/` and the controlling human
contract. It uses fresh sizes `N=320,640,1280`, fresh development and
single-use confirmation allocations, a fixed low-mode encoding, explicit
pi-sector probability and tail gates, a strict `|mu|<=3/100` registered
margin, and a single-excitation hard-core claim boundary. The potential is a
separately charged leading number phase, so direct-only scenarios carry
second-order global convergence gates while potential-split scenarios carry
first-order gates.

The absolute-gate scale has a 256-bit outward-rounded analytic certificate.
The certificate bounds the complete direct one-step unitary discrepancy,
telescopes it through `T=2`, charges the scalar-potential commutator, target
tail, and numerical budget, and uses refinement-specific intermediate mode
bands `|r|<=13,17,20`. This last term prevents an invalid assumption that a
potential-driven state remains in the input band. The worst potential
envelopes are `0.019662`, `0.007805`, and `0.002914`, below the prospective
absolute gates. Refinement ratios, witnesses, implementation agreement,
symmetry-role residuals, and all classifications remain uncomputed outcomes.

The outcome-free production tranche is complete. It includes a 256-bit
Arb/Acb real-space candidate and spectral target, an independent 110-digit
momentum/sparse-circuit/Taylor reconstruction, canonical reducers, prospective
manifests, and a Git-linear seal/authorization surface. Building it exposed an
opposite Fourier sign in the earlier edge orientation; the pairing was
prospectively reversed before the v0.1 freeze so the real-space, localized,
momentum, and target conventions now agree. The v0.1 development run later
stopped before ledger construction on an independent complex-Gram eigensolver
error; no partial artifact was written or inspected.

The v0.2 pipeline completed its indivisible development batch and committed a
ledger classified `development_passed`. Mandatory independent replay then
rejected the first operator enclosure as insufficiently tight. The primary
Fourier basis had been constructed under ambient 53-bit python-flint precision
before the registered 256-bit context; the exact midpoint and all scientific
gates remained on the passing side, but conservative slack of about `4.299e-14`
violated the frozen `1e-65` replay-tightness allowance. Confirmation was not
opened.

The outcome-free v0.3 repair gave basis construction an explicit precision
budget, enclosed basis transformations and the entire registered reduction
batch at 256 bits, and added a disclosed `N=6` regression. Candidate, target,
maps, scenarios, states, partitions, thresholds, metrics, controls, and
stopping rules were unchanged. Its primary development batch passed, and
mandatory replay confirmed every potential-free scenario tightly, but the
potential case exposed a second infrastructure defect: a maximum-Gram-row-sum
spectral-norm enclosure was rigorous but too loose when the potential coupled
registered momentum columns. Confirmation remained unopened.

The outcome-free v0.4 repair chooses a finite-precision similarity basis from
approximate Gram eigenvectors, rigorously inverts and applies that basis using
ball arithmetic, and bounds the largest Gram eigenvalue with certified
Gershgorin discs. The approximate basis is not proof-carrying; only the
certified inverse, transform, and discs determine the enclosure. On the first
affected potential comparison this reduces the certified bound from about
`3.27664e-4` to `2.83580008164455e-4` and agrees with independent replay to
`2.38e-73`. Scientific definitions and stopping rules remain unchanged. No
v0.4 development or confirmation partition may be opened before these
repaired bytes are committed, explicitly sealed in a sole-file freeze commit,
and bound by the declared v0.4 annotated tag.
