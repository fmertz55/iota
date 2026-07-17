# ICP Quantum-Dirac Symmetry-QCA Contract

Protocol version: `0.1-draft`; implementation-seal retry: `v0.4`

Search ID: `ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001`

Date: `2026-07-17`

Status: **v0.1 execution incomplete with no result; v0.2 and v0.3 development ledgers independently unverified with confirmation unopened; v0.4 certified spectral-norm repair complete, disabled, and not frozen**

Base program contract: `ICP Minimal Informational Realization Contract 0.2-draft`

Data class: **prospective architectural-breadth development with a single-use confirmation partition**

## 1. Question and claim boundary

This experiment asks whether a second, independently designed, strictly local
quantum-information architecture can recover the same bounded single-particle
`1+1D` Dirac operational role as the verified product-walk parent. The active
candidate is the direct two-channel Dirac QCA derived from homogeneity,
locality, unitarity, parity, and time-reversal constraints. It is not a
reordering or retuning of the parent product walk.

A complete pass could support only:

```text
The declared direct symmetry-derived QCA, with its hard-core qubit lift, is
constructively sufficient for the frozen bounded 1+1D Dirac operational role
in the registered single-excitation domain and accuracy.
```

It would not establish ontology, a derivation of quantum theory or the Dirac
equation from no supplied structure, whole-zone Dirac equivalence,
doubler-free behavior, canonical fermionic second quantization, an interacting
QFT, uniqueness, necessity, or global minimality.

## 2. Outcome boundary

No v0.4 registered candidate state, trajectory, propagator, operator distance,
observable, zone-edge probability, or failure-control result may be generated
or inspected before the fresh reviewed freeze/open chain. In particular,
candidate sizes `N=320`, `640`, and `1280`, all registered scenarios, and all
registered state witnesses remain forbidden until that chain exists.

The present v0.4 package contains the prospective design, schemas, guarded
algebraic fixtures, repaired production registered evaluator, and independent
replay. Its seal preview is disabled until the fresh freeze/open lifecycle is
created. The archived v0.1, v0.2, and v0.3 seal/open/result artifacts remain
immutable provenance; a v0.4 opening or result before the new freeze
invalidates the retry. The confirmation partition has not been opened or
inspected.

Before freezing, the package must additionally contain and pass review for:

- production candidate and target implementations using the declared
  arithmetic;
- an algorithmically separate registered verifier;
- canonical prospective manifests and result reducers;
- complete lifecycle authorization and linear-provenance checks; and
- an implementation content seal whose run flag remains disabled.

## 3. Scientific and architectural basis

The active law and its symmetry-derived interpretation follow Bisio, D'Ariano,
and Tosini, <https://arxiv.org/abs/1212.2839>. Potential scattering and
Zitterbewegung in this direct family are informed by
<https://arxiv.org/abs/1305.0461>. The parent target/encoding context is
informed by Arrighi, Forets, and Nesme,
<https://arxiv.org/abs/1307.3524>. The complete source and claim-boundary log is
`specs/icp_quantum_dirac_symmetry_qca/v0.1-draft/literature_basis.md`.

The global-spectrum audit establishes a high-quasienergy opposite-mass
pseudodoubler rather than a traditional zero-energy doubler. The protocol
therefore carries seven mandatory boundaries: low-momentum encoding,
zone-edge leakage accounting, an explicit pseudodoubler failure control,
branch-safe effective-Hamiltonian metrics, a strict mass margin, a
single-excitation claim, and full architecture integrity.

## 4. Target theory and registered domain

Use `hbar=c=1`. The target spinor is periodic on `x in [0,16)` and obeys

```text
i d_t psi = H_T(t) psi
H_T(t) = -i sigma_z d_x + m(t) sigma_x + V(x,t) I_2.
```

The Fourier convention is

```text
psi(x) = 16^(-1/2) sum_r psi_hat[r] exp(i 2 pi r x/16).
```

The registered input subspace is `r=-4..4` with both spinor components, so its
dimension is `18` and `|k|<=pi/2`. The target solver retains `|r|<=72` and
adds a scenario-specific outward tail bound. The horizon is `T=2`; observation
times are `[2/5,4/5,6/5,8/5,2]`.

| `N` | `delta_x=delta_t` | macrosteps to `T` |
|---:|---:|---:|
| 320 | `1/20` | 40 |
| 640 | `1/40` | 80 |
| 1280 | `1/80` | 160 |

All intervention and observation boundaries are exact macrostep boundaries at
all three refinements. The tier excludes multiparticle inputs, particle
creation, interacting fields, vector or gauge potentials, curved geometry,
nonperiodic boundaries, feedback, and input modes outside `r=-4..4`.

## 5. Candidate declaration

Each site has occupation qubits `R` and `L`, local basis
`|00>,|10>,|01>,|11>`, and local Hilbert dimension four. The registered
sector has exactly one excitation globally and dimension `2N`.

For `mu_q=delta m_q` and `n_q=sqrt(1-mu_q^2)`, the free one-excitation law is

```text
R'(x) = n_q R(x-1) - i mu_q L(x)
L'(x) = -i mu_q R(x) + n_q L(x+1),
```

with momentum block

```text
U_mu(q) = [[n exp(-i q), -i mu],
           [-i mu,       n exp(+i q)]].
```

The physical full-space macrostep is, from right to left,

```text
U[q] = A B_mu[q] P_V[q],
```

where `P_V` is omitted when the scalar potential is inactive. `P_V` is the
on-site number phase `exp(-i delta V(x_j,t_q)(n_Rj+n_Lj))`; `B_mu` applies the
same edge-scatter gate to all disjoint pairs `(L_j,R_(j-1))`; and `A` applies
ordinary on-site qubit SWAPs `(R_j,L_j)`. The order is candidate-defining.

The edge gate fixes `|00>` and `|11>` with phase `+1` and has one-excitation
block `n X-i mu I` in edge-mode order. The on-site SWAP also fixes double
occupation with phase `+1`. Canonical fermionic lifts instead carry
determinant phase `-1` on `|11>`. Substituting either fermionic phase changes
the architecture.

The edge orientation above is fixed by the declared positive-sign target
Fourier convention. During guarded production construction, the earlier draft
pairing `(L_j,R_(j+1))` was found to yield the opposite massless Fourier phase.
Before any freeze or registered evaluation it was corrected to
`(L_j,R_(j-1))`. A disclosed fixture now requires the real-space recurrence,
localized layers, and momentum block to agree on the same sign.

The registered largest physical mass is `3/5`. At the coarsest refinement,
`|mu|<=3/100`, leaving margin `97/100` from the localization endpoint
`|mu|=1`.

## 6. Resource accounting and clock

The classical MIR `N_P` score is inapplicable. The declared quantum resources
are:

| Coordinate | Value |
|---|---|
| degree schemas | two occupation-mode schemas, `R` and `L` |
| local Hilbert dimension | 4 |
| registered sector | one excitation; dimension `2N` |
| storage | `2N` occupation qubits; one occupied |
| relation schema/instances | one oriented cycle / `N` edges |
| free causal depth | 2 layers |
| active-potential causal depth | 3 layers |
| free gate-work | `2N` gates per macrostep |
| active-potential gate-work | `3N` gates per macrostep |
| ancillas | 0 |
| causal radius | one cell per macrostep |

Potential formulas are charged finite intervention descriptions. Generated
sitewise phases are allowed; fitted or hand-supplied sitewise tables are not.
Registered dynamics must use 256-bit outward-rounded Arb/Acb arithmetic via
`python-flint 0.9.0` or the later sealed exact dependency, with an independent
`mpmath 1.3.0` replay at 110 decimal digits. Binary64 registered dynamics are
forbidden.

## 7. Fixed maps `E`, `M`, and `Phi`

`E_N` is the isometry that copies the target coefficients at `r=-4..4` into
the identically labelled normalized construction DFT modes and zeros every
other construction mode. Aliasing, interpolation, and target-future payloads
are forbidden.

`M_N` returns the Fourier-grid position POVM, momentum distribution, total
`sigma_z` current, signed local current, π-sector probability, norm, and
fidelity. The π sector is the fixed set `|q|>=3pi/4`.

`Phi_N` maps `m_q` to `mu_q=delta m_q` and `n_q=sqrt(1-mu_q^2)`, maps the
scalar potential to the leading on-site number phase, and samples schedules at
the left endpoint of each macrostep. A disclosed local phase probe is allowed
only in the algebraic causal-support fixture.

## 8. Registered scenarios

All values are exact. The scalar-potential tuple is
`(start,end,harmonic,amplitude,phase)` and denotes
`amplitude*cos(2pi*harmonic*x/16+phase)` on the half-open active window.

Development scenarios are:

| ID | Class | Mass | Scalar potential |
|---|---|---|---|
| `DEV-DIRECT-FREE-POS` | direct-only | `1/3` | zero |
| `DEV-DIRECT-FREE-NEG` | direct-only | `-2/5` | zero |
| `DEV-DIRECT-SIGN-QUENCH` | direct-only | `1/4` to `t=4/5`, then `-1/3` | zero |
| `DEV-DIRECT-POTENTIAL-H2` | potential split | `2/5` | harmonic 2, amplitude `1/8`, phase 0 on `[3/10,13/10)` |

Single-use confirmation scenarios are:

| ID | Class | Mass | Scalar potential |
|---|---|---|---|
| `HOLDOUT-DIRECT-MASS-PULSE` | direct-only | `-1/5` on `[0,7/20)`, `3/5` on `[7/20,27/20)`, then `1/5` | zero |
| `HOLDOUT-DIRECT-POTENTIAL-H3` | potential split | `-1/3` | harmonic 3, amplitude `1/10`, phase `pi/2` on `[1/4,29/20)` |

These allocations, the refinement ladder, and the thresholds are fresh. No
parent holdout, parent threshold, or parent result counts as candidate data.

## 9. State witnesses and allocation

Every witness is a normalized Gaussian Fourier envelope on `r=-4..4`,

```text
exp(-(r-r0)^2/(2w^2)) exp(-i k_r x0),
```

times fixed-phase positive- or negative-energy spinors of
`k_r sigma_z+m_0 sigma_x`. Interference states use the two frozen packets and
relative phase; Zitterbewegung states use an equal positive/negative-energy
mixture with the frozen relative phase. Exact parameters and canonical order
are in `states.json`. Serialized amplitude tables are forbidden.

The four development states are evaluated only with development scenarios.
The four confirmation states are evaluated only after a verified development
pass and only with the two confirmation scenarios. The primary gate is uniform
over the entire input subspace; state holdouts are interpretable observable
witnesses, not statistically independent proof of the uniform norm bound.

## 10. Primary operational metric

For scenario `a`, time `t`, and refinement `N`, define

```text
D_N(a,t) = U_direct,N[a](t) E_N
           - J_N U_target,72[a](t) P_in.
```

The raw norm is the spectral operator `2`-norm. The certified distance adds an
outward target-tail bound and numerical enclosure. A scenario distance is the
maximum over the five registered observation times.

The proposed direct-only gates are:

| `N` | absolute gate |
|---:|---:|
| 320 | `0.0040` |
| 640 | `0.0012` |
| 1280 | `0.0004` |

with successive gate `d_fine <= 0.35 d_coarse + 1e-10`.

The proposed potential-split gates are:

| `N` | absolute gate |
|---:|---:|
| 320 | `0.020` |
| 640 | `0.011` |
| 1280 | `0.006` |

with successive gate `d_fine <= 0.62 d_coarse + 1e-10`. Either ratio gate is
waived only if all three certified distances are at most `1e-12`.

These gates are not yet frozen. Their absolute scale now has an
outward-rounded analytic certificate. The derived free effective generator has
`H_eff=H_D+delta^2 K_2+O(delta^4)`; the norm of `K_2` is monotone in `k^2` and
`m^2` on the registered box and is approximately `0.339813` at
`|k|=pi/2, |m|=3/5`. The certificate separately bounds the complete
finite-`delta` one-step unitary remainder and telescopes it without norm
growth. For potential cases it does not assume that all later states remain in
the input band: it uses intermediate cutoffs `|r|<=13,17,20` across the three
refinements and charges the outward Dyson amplitude beyond each band at every
remaining step. It also adds the Lie-product commutator bound controlled by
`||V'||`, the target-cutoff tail, and a `1e-10` numerical-enclosure budget.
The resulting worst potential envelopes are `0.019662`, `0.007805`, and
`0.002914`, below the three proposed absolute gates. This certificate fixes
the threshold rationale only; refinement ratios, observables, implementation
agreement, and all pass/fail classifications remain uncomputed outcomes.

## 11. Target-tail and zone-edge leakage accounting

Each harmonic interaction changes mode number by at most its harmonic `h`.
Starting from `|r|<=4`, leaving `|r|<=72` first occurs at order 35 for `h=2`
and order 23 for `h=3`. At the coarsest lattice, `|q|>=3pi/4` begins at
`|r|=120`; it first becomes reachable at orders 58 and 39 respectively.

For first reachable order `s`, amplitude `A`, and active duration `tau`, use

```text
beta(A,tau,s) = 2 exp(z) z^s/s!,  z=|A| tau.
```

Zero-potential scenarios have exactly zero candidate π-sector probability.
Every potential scenario must include the analytic leakage enclosure and also
pass measured candidate π-sector probability `<=1e-24`; the bound may not be
discarded merely because the measured value is small.

## 12. Observable gates at `N=1280`

For every registered state/scenario pair and observation time, require:

```text
position total-variation distance <= 0.010
momentum total-variation distance <= 0.010
absolute total-current error      <= 0.020
local-current vector L1 error     <= 0.020
state infidelity                  <= 0.0001
candidate pi-sector probability  <= 1e-24.
```

For each Zitterbewegung witness, record total current at every macrostep and
require construction-to-target supremum error `<=0.020`. No frequency,
amplitude, or phase may be estimated and refit before comparison.

## 13. Structure, causality, and symmetries

Abstract full-space unitarity is exact. Numerical norm residual must be at
most `1e-12`; independent state-vector disagreement must be at most `1e-11`.

Before wrap, support is exactly zero beyond one cell per completed macrostep.
At `m=V=0`, the two directional modes must attain opposite cone boundaries.
Translation covariance is exact for homogeneous mass and inactive or
spatially constant potential.

Parity is ordinary qubit `R/L` SWAP together with `x -> -x`. Its free
full-space residual is symbolic zero; an even-potential numerical residual
must be at most `1e-12`.

Time reversal is ordinary qubit `R/L` SWAP followed by complex conjugation.
The free full-space relation `Theta U Theta^-1=U^dagger` is exact. The leading
potential split is judged as a target-role approximation at `N=1280` with
residual `<=0.020` and the same `0.62` refinement gate as the potential primary
metric. Exact signed-step reversal is claimed only for the direct free law.

## 14. Independent implementation requirement

The planned production candidate must apply the leading real-space phase and
then the direct recurrence with certified ball arithmetic. Its free verifier
must instead construct independent `2x2` momentum blocks. Its potential
verifier must explicitly build sparse phase, edge-scatter, and routing
operators. The production target is a certified spectral solver on
`r=-72..72`; the verifier independently rebuilds the sparse harmonic generator
and its exponential. The verifier norm comes from a higher-precision
Gram-matrix largest eigenvalue.

Candidate and verifier may not share a candidate constructor. Target and
verifier may not share a target constructor. Agreement of two wrappers around
the same matrix is not independent verification.

## 15. Allowed pre-freeze fixtures

Only these disclosed outcome-free fixtures may run:

- `N=6` direct one-excitation update, continuum generator, and spectrum;
- `N=10` full-space localization, collision phases, symmetries, and resource
  clock;
- the analytic π-partner identity `U_mu(-pi+p)=-U_-mu(p)` on `N=6`;
- a target-only cutoff-3, harmonic-2 solver fixture; and
- a one-macrostep local-phase causal-support fixture on `N=10`.

Analytic tail and threshold design calculations are allowed only when they do
not propagate a registered candidate or registered state. The completed
disabled-seal preview hashes the reviewed implementation, reports
`seal_ready=true` and `run_command_enabled=false`, and creates no file. Seal
creation remains a separate explicit clean-worktree action; the resulting seal
must itself remain execution-disabled.

## 16. Required negative fixtures

Tests must reject registered sizes, parent sizes, registered scenarios before
freeze, parent product-walk substitution, Gupta--Short walk-family
substitution, canonical fermionic-lift substitution, reversed gate order,
wrong Fourier sign, omitted edge-scatter or SWAP layers, an uncharged potential
phase, and any enabled draft production path.

## 17. Partitions and stopping rule

Development is an indivisible four-scenario batch. If any development gate
fails, stop with confirmation unopened. After a verified development pass,
confirmation is an indivisible, single-use two-scenario batch. Partial results
are not scientific results. An interrupted or provenance-invalid execution is
classified as no result.

## 18. Failure controls after the confirmation primary

Only after the registered confirmation primary has been evaluated, run in
fixed order:

1. the analytic opposite-mass π-partner identity;
2. high-`q` `N=320`, `r=120`, `m=1/3` through `T=2`;
3. the `|mu|=1` flat-band mass endpoint;
4. a low-band `N=320`, `r=-4..4`, `m=1/3` run through `T=12`;
5. a rough spatial-step leakage control at `N=320`, initialized in the
   normalized right-moving `r=0` mode, with `m=1/3` and the site potential
   `V=1/8` on sites `0..159`, `V=-1/8` on sites `160..319`, active for all 40
   macrosteps through `T=2`; and
6. the disclosed hard-core versus fermionic two-excitation collision contrast.

The π-partner is evaluated at `p=1/7`, `mu=1/5`. The collision contrast is the
distance between the declared hard-core double-occupation phase `+1` and the
canonical fermionic determinant phase `-1`. These exact control definitions
and their canonical metrics are serialized in `protocol.json`.

These controls characterize known boundaries. They cannot repair a failed
primary or broaden a pass claim.

## 19. Linear provenance

The future history is: complete implementation; seal-only freeze commit and
annotated tag `icp-quantum-dirac-symmetry-qca-001-v0.4-frozen`;
development-open-only child; development-result-only child; conditional
confirmation-open-only child; confirmation-result-only child. Each child must
bind its exact parent and every causal input. Reopening, overwriting, or
side-branch substitution invalidates the result.

The first implementation seal, `v0.1`, opened development but wrote no result.
Its independent replay passed a complex Hermitian Gram matrix to mpmath's
real-symmetric eigensolver, which raised `TypeError` before ledger construction
completed. No partial artifact was written or inspected. Under the registered
`execution_incomplete_no_result` rule, `v0.1` remains immutable and closed.
The `v0.2` retry changes only that independent spectral-norm implementation to
the Hermitian eigensolver, adds a public complex-Gram regression fixture, and
uses fresh lifecycle paths. Scientific definitions, scenarios, partitions,
states, thresholds, maps, and stopping rules are unchanged.

The v0.2 development batch then completed and wrote the immutable ledger at
commit `1228249f545fa05c914bc1b2484bc6cd37f5c0d8`. The ledger classified the
development gates as passed, but mandatory post-commit independent replay
stopped at the first operator-distance comparison because the certified upper
enclosure was not replay-tight. At `N=320`, time `2/5`, the ledger stored
`0.0001446347782483140844...` while the 110-digit independent replay gave
`0.0001446347782053239702...`, leaving conservative slack of about
`4.2990e-14`, far above the registered `1e-65` tightness allowance.
Confirmation was never opened.

The cause is implementation precision ownership, not a scientific threshold
failure: the primary Fourier input basis was constructed at python-flint's
ambient 53-bit precision before the evaluator entered its declared 256-bit
context, and stage-level certified reductions lacked one enclosing precision
context. Reconstructing the same basis at 256 bits makes the certified upper
agree with the independent replay to about `1e-77`. The v0.3 retry moves basis
construction and basis transformations inside the declared bit budget, wraps
the full registered construction/reduction/serialization batch at 256 bits,
adds a disclosed `N=6` precision regression, and uses fresh lifecycle paths.
It does not change the candidate, target, scenarios, states, partitions,
thresholds, maps, metrics, gates, controls, or stopping rule.

The v0.3 retry then froze at `9da2d87`, opened development at `ae64d7a`, and
wrote its immutable development ledger at
`712552b9d5f171a8a133b06c13ef6760bbfeb7f1`. Its primary gates classified the
batch `development_passed`. Mandatory independent replay confirmed all three
potential-free scenarios with certified slack below `7e-73`, but rejected the
potential scenario because the primary certified spectral norm used the
maximum Gram row sum. That bound is rigorous, yet coupling between registered
momentum columns made it too loose for the `1e-65` replay-tightness rule.
Confirmation was never opened.

The v0.4 retry replaces only that norm reducer. Approximate Gram eigenvectors
choose a finite-precision basis; a rigorous ball-arithmetic inverse and
similarity transform then carry the proof, followed by certified Gershgorin
upper discs for the largest Gram eigenvalue. On the first affected potential
comparison, the old row-sum bound was about `3.27664e-4`; the repaired bound
and the independently replayed norm both give `2.83580008164455e-4`, with
certified slack `2.38e-73`. This changes no scientific definition, threshold,
partition, scenario, state, map, metric, gate, control, or stopping rule.

## 20. Terminal classifications

The only terminal labels are:

- `development_gate_failed_confirmation_unopened`;
- `development_passed`;
- `development_passed_confirmation_failed`;
- `constructive_sufficiency_passed_direct_symmetry_qca_sector`;
- `execution_incomplete_no_result`; and
- `provenance_invalid_no_result`.

## 21. Current draft disposition

Localization, continuum, and global-spectrum audits are complete. The
prospective target, maps, interventions, state formulas, partitions, metrics,
proposed gates, their outward-rounded absolute-gate certificate, schemas, and
lifecycle paths are explicit. The certified real-space candidate and spectral
target, algorithmically separate momentum/sparse-circuit/Taylor replay,
canonical reducers, four prospective manifests, content-seal builder, and
Git-linear authorization surface now pass disclosed-fixture validation. The
Fourier-orientation defect found during implementation was corrected before
the v0.1 freeze. That development run was authorized but stopped before any
result ledger was generated. The v0.2 retry completed its development ledger,
but its mandatory independent verification exposed the 53-bit Fourier-basis
enclosure described above. The v0.3 repair corrected that defect and completed
another primary-passing development ledger, but mandatory replay exposed the
potential-coupled row-sum looseness described above. Both classified passes
are therefore independently unverified, and confirmation remains unopened.
The v0.4 spectral-norm repair and disclosed regressions are complete. Its fresh
lifecycle paths point only to v0.4 artifacts, and no v0.4 seal, opening,
permit, or result exists. The repaired bytes must pass the full repository
verification gate before a seal-only freeze commit and annotated v0.4 tag are
created.
