# ICP Quantum-Dirac Role-Recovery Contract

Version: `0.1-draft`

Search ID: `ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001`

Date: `2026-07-14`

Status: **outcome-free design active; production absent and disabled; not frozen**

Base program contract: `ICP Minimal Informational Realization Contract 0.2-draft`

Data class: **prospective constructive-sufficiency development with a single-use confirmatory partition**

## 1. Question and claim boundary

This experiment asks:

> Can a closed, homogeneous, nearest-neighbor quantum-information construction recover the frozen operational role of a bounded sector of the single-particle free Dirac theory in one space and one time dimension, under fixed state, measurement, and intervention maps?

The candidate is a two-directional-mode partitioned quantum cellular automaton whose physical macrostep is a product of local phase, local mass-mixing, and conditional transport operations. The target is the continuum Dirac equation on a finite periodic domain. The comparison is uniform over a finite low-momentum input subspace and includes state witnesses, interventions, symmetries, conservation, a causal-cone certificate, and a three-level refinement ladder.

A complete pass supports only:

```text
Declared quantum-information primitives are constructively sufficient to
realize the frozen 1+1D Dirac operational role within the registered domain
and accuracy.
```

It does not support an ontological claim, a derivation of quantum theory from generic information, continuum equivalence at all scales, a multiparticle or interacting field theory, a finite-classical-bit realization, or minimality.

## 2. Outcome boundary

No registered candidate state, trajectory, propagator distance, measurement distribution, intervention response, or failure-control result may be generated or inspected while this document has status `not frozen`.

This draft resolves the conceptual design choices. It is not an outcome seal. The following must still exist, pass outcome-free review, be committed together, and be tagged before a registered outcome can be opened:

- the complete machine-readable protocol and schemas;
- canonical candidate, state, scenario, and partition manifests;
- the real-space candidate engine and the independent circuit/momentum reconstruction;
- the continuum target solver and an independently expressed verifier;
- certified operator-norm and target-truncation error accounting;
- positive and negative algebraic fixtures that do not use registered scenarios;
- canonical result schemas and ordering;
- a content-hash seal over every causal and evaluative input;
- a production command that is present but disabled; and
- the exact freeze, opening, result, and verification commands.

Pre-freeze testing may use only the disclosed algebraic fixtures in Section 15. A fixture must use a nonregistered lattice, state, or parameter tuple. Any inspected registered result converts this version to development data and requires a new version and confirmation allocation.

## 3. Primary scientific basis

The design uses published work as pre-outcome construction evidence, not as a result of this candidate.

- Arrighi, Forets, and Nesme derive homogeneous causal Dirac quantum walks in product form and prove first-order state-vector convergence, with discrepancy-observation probability quadratic in the discretization step: <https://arxiv.org/abs/1307.3524>.
- Bisio, D'Ariano, and Tosini formulate a distinct one-dimensional Dirac QCA and compare its evolution with Dirac evolution as discrimination between unitary channels: <https://arxiv.org/abs/1212.2839>.
- Bisio, D'Ariano, and Tosini analyze Zitterbewegung and potential scattering in the direct Dirac-QCA family: <https://arxiv.org/abs/1305.0461>.
- D'Ariano and Perinotti derive Dirac behavior in the small-momentum, small-mass regime from a minimal nontrivial QCA subject to declared quantum constraints: <https://arxiv.org/abs/1306.1934>.

The first source controls the active product-form candidate. The second and fourth sources motivate, but do not define, a success-contingent direct-QCA follow-up. These families must not be conflated: their finite-lattice update matrices and symmetry behavior differ.

## 4. Frozen target theory and domain

Use units `hbar = c = 1`. The target spinor is `psi(x,t) in C^2` on the periodic domain `x in [0,L)`, with

```text
L = 16
i d_t psi = H_T(t) psi
H_T(t) = -i sigma_z d_x + m(t) sigma_x + V(x,t) I_2.
```

The Fourier convention is

```text
psi(x) = L^(-1/2) sum_r psi_hat[r] exp(i k_r x)
k_r = 2 pi r / L,  r in Z.
```

The registered input subspace is

```text
K_in = span{|r,s>: -4 <= r <= 4, s in {R,L}}
dim(K_in) = 18
k_max = pi/2.
```

Every registered state has unit norm and lies entirely in `K_in`. The target evolution is exact, piecewise constant within each candidate macrostep, for the registered mass and scalar-potential schedules. The physical horizon and observation times are

```text
T = 2
t_observe = [1/2, 1, 3/2, 2].
```

The refinement ladder is

| `N` | `delta_x = delta_t = L/N` | macrosteps to `T` |
|---:|---:|---:|
| 256 | 1/16 | 32 |
| 512 | 1/32 | 64 |
| 1024 | 1/64 | 128 |

All intervention boundaries and observation times are exact integer macrostep boundaries at every refinement.

The first tier excludes multiparticle states, particle creation, interacting fields, vector or gauge potentials, curved geometry, nonperiodic boundaries, adaptive interventions, measurement feedback, and any input momentum outside `K_in`.

## 5. Candidate declaration

The candidate is

```text
C = (P, L, G, X_0, U, E, M, Phi).
```

### 5.1 Quantum substrate

There are `N` sites on a directed periodic cycle. Each site has two number-state modes, `R` and `L`. The local Hilbert-space dimension is four, with basis `|00>, |10>, |01>, |11>`. The registered sector contains exactly one excitation globally and has dimension `2N`.

The full local substrate is declared so the walk is not misreported as a free abstract `2N`-component vector. No multiparticle claim follows from using the one-excitation sector.

### 5.2 Exact logical macrostep

Let `x_j = j delta_x`. On a state column vector, one macrostep applies from right to left:

```text
U_C[q] = S C_m[q] V[q].
```

The local scalar-potential phase is

```text
V[q] |j,s> = exp(-i delta_t V_q(x_j)) |j,s>.
```

The local mass mixer is

```text
C_m[q] = exp(-i delta_t m_q sigma_x)
       = [[cos(delta_t m_q), -i sin(delta_t m_q)],
          [-i sin(delta_t m_q), cos(delta_t m_q)]].
```

Conditional transport is

```text
S |j,R> = |j+1 mod N,R>
S |j,L> = |j-1 mod N,L>.
```

For a translation-invariant free step, the momentum block is

```text
U_C(k;m) = exp(-i delta_t k sigma_z)
           exp(-i delta_t m sigma_x).
```

The order is fixed. Reversing it, symmetrizing it, using the direct Dirac-QCA matrix, or combining causal stages creates a new candidate version.

### 5.3 Local circuit realization of transport

The logical transport is not counted as a zero-cost relabeling. It is localized by two layers of disjoint swaps:

1. swap `R_j` with `L_j` at every site;
2. swap `L_j` with `R_(j+1)` on every directed edge.

Tracking the modes gives `R_j -> R_(j+1)` and `L_j -> L_(j-1)`. The production implementation must use the corresponding number-preserving quantum swaps, with the one-excitation restriction explicit.

## 6. Quantum primitive and resource accounting

The classical MIR `N_P` score is inapplicable. This experiment reports the following vector without collapsing it to one number.

| Coordinate | Registered value |
|---|---|
| quantum degree schemas | two occupation-mode schemas, `R` and `L` |
| local Hilbert dimension | 4 |
| registered global sector | one excitation; dimension `2N` |
| initialized systems | `N` four-dimensional cells |
| relation schemas | one oriented nearest-neighbor cycle |
| relation instances | `N` directed edges |
| gate schemas | scalar phase, mass mixer, on-site swap, edge swap |
| fixed free causal depth per macrostep | 3 elementary layers |
| active-potential causal depth per macrostep | 4 elementary layers |
| free gate-work per macrostep | `3N` local/two-mode gates |
| active-potential gate-work per macrostep | `4N` local/two-mode gates |
| quantum storage | `2N` occupation modes; one occupied |
| target-input payload | 18 complex amplitudes subject to normalization |
| measurement postulate | shared Born-rule harness |

`E(x)` is state payload, not a candidate law, but its nonzero coefficient count and numerical representation must be recorded for every fixture. A target state may not contain a future trajectory.

Masses, times, lengths, amplitudes, phases, and mode indices are supplied as the exact integers and rationals listed in the protocol. Transcendental gate entries are computable values defined by those finite descriptions. The production representation must use 256-bit correctly rounded arithmetic and record the library, version, rounding mode, and a certified error bound. No unrecorded binary64 constant may enter candidate or target dynamics.

The potential formula and its time window are exogenous intervention information. Its finite description is charged and recorded. Sitewise phase tables may be generated from the formula; they may not be hand supplied or fitted.

## 7. Elementary gate clock

One physical macrostep advances target time by `delta_t`. It contains these causally ordered elementary layers:

```text
potential active: phase -> mass mix -> on-site swap -> edge swap
potential absent:          mass mix -> on-site swap -> edge swap
```

Parallel gates within a layer count as one elapsed elementary layer and their gate-work is reported separately. Identity potential layers are omitted and do not count as executed gates. The result reports physical macrosteps, executed elementary layers, gate-work, and storage independently.

No result may call a full macrostep one elementary tick. No gate output may be consumed earlier than the next listed layer.

## 8. Fixed maps `E`, `M`, and `Phi`

### 8.1 Encoding `E_N`

For every target state in `K_in`, `E_N` copies its Fourier coefficient at integer mode `r` and component `s` into the identically labeled normalized DFT mode of the `N`-site construction. Every other construction mode is zero. This is an isometry. It uses no target future, no scenario-specific retuning, and no interpolation selected after outcomes.

### 8.2 Measurement map `M_N`

The same Born-rule evaluation is used for target and construction. `M_N` returns:

- the `N`-outcome Fourier-grid position POVM;
- the momentum-mode distribution;
- the total directional current `<sigma_z>`;
- the signed local directional-current vector on the Fourier grid; and
- the norm and state fidelity used for conservation and witness diagnostics.

The target position distribution is the same grid POVM applied after the target state is embedded into the `N`-mode Fourier representation. It is not an adaptively chosen histogram. Complex state amplitudes are available to the uniform operator certificate but are not treated as directly measured observables.

### 8.3 Intervention map `Phi_N`

`Phi_N` is fixed for the entire tier:

- a target mass schedule `m(t)` becomes the mass-mixer angle `delta_t m_q` at each macrostep;
- a target scalar potential `V(x,t)` becomes the on-site phase `delta_t V(x_j,t_q)` at the same macrostep; and
- a local causal-probe phase on target region `A` becomes the identical local phase on construction sites whose cells intersect `A`.

No intervention may alter `E`, `M`, transport, lattice size, tolerances, or a different parameter not present in the target intervention.

## 9. Registered scenarios

All values below are exact. The notation `cos_1(phi)` means `(1/4) cos(2 pi x/L + phi)` during the stated half-open time window and zero otherwise.

### 9.1 Development scenarios

| ID | Mass schedule | Scalar potential |
|---|---|---|
| `DEV-FREE-LIGHT` | `m=1/4` | zero |
| `DEV-FREE-HEAVY` | `m=1/2` | zero |
| `DEV-QUENCH-UP` | `1/4` for `t<1`; `1/2` for `t>=1` | zero |
| `DEV-POTENTIAL-EVEN` | `m=1/4` | `cos_1(0)` for `1/2 <= t < 3/2` |

### 9.2 Single-use confirmation scenarios

| ID | Mass schedule | Scalar potential |
|---|---|---|
| `HOLDOUT-QUENCH-DOWN` | `1/2` for `t<3/4`; `1/4` for `t>=3/4` | zero |
| `HOLDOUT-POTENTIAL-ODD` | `m=1/2` | `cos_1(pi/2)` for `1/4 <= t < 5/4` |

Every scenario is evaluated at all three refinements. Candidate parameters, maps, code, and gates remain byte-identical between development and confirmation.

## 10. State families and allocation

For scenario initial mass `m_0`, let `u_+(r;m_0)` and `u_-(r;m_0)` be the normalized positive- and negative-energy eigenvectors of `k_r sigma_z + m_0 sigma_x`. Fix their phase by making the first nonzero component real and positive. Let

```text
g(r;r0,w,x0) proportional to
  exp(-(r-r0)^2/(2 w^2)) exp(-i k_r x0),  -4 <= r <= 4.
```

The complete state is normalized after the declared superposition. These formulas, not serialized amplitude tables, define the fixtures.

Development state witnesses are:

- `DEV-STATE-POS`: `g(r;2,1,4) u_+(r;m_0)`;
- `DEV-STATE-NEG`: `g(r;-2,1,12) u_-(r;m_0)`;
- `DEV-STATE-INTERFERENCE`: equal normalized superposition of positive-energy packets `(r0,x0)=(2,4)` and `(-2,12)` with relative phase `i`;
- `DEV-STATE-ZITTER`: `g(r;1,1,8)` multiplying the equal normalized positive/negative-energy superposition with relative phase `exp(i pi/3)`.

Confirmation state witnesses are:

- `HOLDOUT-STATE-POS`: `g(r;-1,3/4,6) u_+(r;m_0)`;
- `HOLDOUT-STATE-NEG`: `g(r;3,3/4,10) u_-(r;m_0)`;
- `HOLDOUT-STATE-INTERFERENCE`: equal normalized superposition of positive-energy packets `(r0,x0)=(1,2)` and `(-3,9)` with relative phase `exp(i pi/5)`;
- `HOLDOUT-STATE-ZITTER`: `g(r;-2,3/4,3)` multiplying the equal normalized positive/negative-energy superposition with relative phase `exp(-i pi/4)`.

Development witnesses are evaluated only with development scenarios. Confirmation witnesses are evaluated with both confirmation scenarios and, after the holdout is opened, with `DEV-FREE-LIGHT`. Because the primary certificate is uniform over `K_in`, state holdouts are interpretable witnesses rather than statistically independent confirmation. The single-use new intervention schedules provide the non-algebraically-implied confirmation.

## 11. Primary operational metric and tolerance

For scenario `a`, observation time `t`, and refinement `N`, define the common-space discrepancy from the entire input subspace:

```text
D_N(a,t) = U_C,N[a](t) E_N
           - J_N U_T,R[a](t) P_in.
```

`P_in` includes the 18 input basis columns. `U_T,R` is the independently computed target evolution on Fourier modes `|r| <= R_ref=64`. `J_N` embeds those output modes into the construction DFT space. Candidate amplitude in all other construction modes remains in the first term and therefore counts as error.

The certified distance is

```text
d_N(a,t) = upper_bound(||D_N(a,t)||_2)
           + beta_target_tail(a,t)
           + beta_numeric(a,t,N).
```

For the registered one-Fourier-mode scalar potential, each Dyson insertion changes `r` by at most one. Starting from `|r|<=4`, leaving `|r|<=64` requires at least 61 insertions. The conservative tail certificate is

```text
lambda = ||V||_infinity T = 1/2
beta_target_tail = 2 exp(lambda) lambda^61 / 61!.
```

Zero-potential scenarios have zero target-truncation tail. The implementation may prove a tighter bound but may not use it to loosen another gate.

For each scenario, let `d_N(a)` be the maximum over the four observation times. The prospectively frozen gates are

```text
d_256(a)  <= 0.20
d_512(a)  <= 0.10
d_1024(a) <= 0.05

d_512(a)  <= 0.60 d_256(a) + 1e-8
d_1024(a) <= 0.60 d_512(a) + 1e-8.
```

The tolerance scale is outcome-free. For a constant-mass momentum block, the
unitary first-order product estimate gives a one-step error no larger than
`delta_t^2 |k m|`; telescoping through `T/delta_t` steps gives
`T delta_t |k m|`. At the registered worst-case `|k|=pi/2`, `m=1/2`, and
`T=2`, this bound is `pi/32`, `pi/64`, and `pi/128` across the refinement
ladder. The absolute gates are approximately twice those bounds, leaving
room for the frozen potential intervention and certified numerical error.
This rationale does not presuppose that the potential scenarios pass; their
full operator distances remain registered outcomes.

The two ratio inequalities are waived only when the coarse error is at most `1e-10`, in which case both finer errors must also be at most `1e-10`. These are first-order refinement gates, not a post-outcome fit.

The development stage passes this section only if all four development scenarios pass. Confirmation passes only if both held-out scenarios pass without changing any sealed input.

## 12. Observable, interference, and Zitterbewegung witnesses

For every registered state/scenario pair and observation time at `N=1024`, require

```text
position total-variation distance <= 0.05
momentum total-variation distance <= 0.05
absolute total-current error      <= 0.10
local-current vector L1 error     <= 0.10
state infidelity                  <= 0.0025.
```

The interference fixtures must use their frozen relative phases. Replacing a coherent superposition by the corresponding mixture is a preregistered negative fixture and must change at least one position-POVM entry in the target; the construction-to-target comparison still uses the coherent state.

For each Zitterbewegung fixture, record the total-current series at every macrostep through `T`, not only selected peaks. Its construction-to-target supremum error must be at most `0.10`. No frequency, amplitude, or phase may be estimated and refit before comparison.

## 13. Conservation, causality, parity, and time reversal

### 13.1 Unitarity and norm

The abstract scalar phase, mass mixer, and swaps are unitary. Their algebraic proof is mandatory. The finite-precision implementation must preserve norm to `1e-12` at every registered observation and agree with the independent implementation to `1e-11` in state-vector norm.

### 13.2 Causal support

Local phase and mass layers do not change position. One completed transport moves amplitude by exactly one site. Before periodic wrap, the candidate block propagator must be exactly zero when graph distance exceeds the number of completed macrosteps. A local intervention difference must obey the same cone. For `m=V=0`, both directional modes must attain the two cone boundaries, so the maximum speed is exactly one rather than merely bounded above by one.

The target Dirac equation has the corresponding unit-speed domain of dependence. The registered support claim is equality of the outer causal speed and absence of superluminal intervention effect. It does not claim pointwise equality of lattice-parity support inside the cone.

The production certificate is structural and exact; it may not infer zeros from a floating threshold.

### 13.3 Parity

Use

```text
(Pi psi)(x) = sigma_x psi(-x mod L).
```

The target and candidate must satisfy parity covariance under `V(x,t) -> V(-x,t)`. The abstract candidate residual must be symbolically zero. The numerical residual must be at most `1e-12`.

### 13.4 Time reversal

Use the antiunitary

```text
Theta = sigma_x K,
```

where `K` is complex conjugation in the position/directional basis. For a schedule `a`, `a^R` reverses its macrostep order. The target obeys the frozen time-reversal relation exactly. The ordered first-order candidate is not assumed to obey it exactly. Require

```text
r_TR,N(a) = ||Theta U_C,N[a] Theta^-1 - U_C,N[a^R]^dagger||_2
r_TR,1024(a) <= 0.10
r_TR,512(a)  <= 0.60 r_TR,256(a) + 1e-8
r_TR,1024(a) <= 0.60 r_TR,512(a) + 1e-8.
```

The same near-zero waiver as Section 11 applies. A pass supports convergent recovery of the target time-reversal role, not exact microscopic time-reversal invariance of this gate ordering.

## 14. Target solver, candidate engine, and independent verification

The production candidate engine must update the `2N` amplitudes in real space by separately applying phase, mass mixing, and the two swap layers. It may not call the target Hamiltonian or an exact target propagator.

The production target solver must build the spectral Dirac generator on `|r|<=64`, including the exact `r -> r+/-1` potential couplings, and evaluate each piecewise-constant exponential with at least 256-bit arithmetic. It may not call candidate update code.

The independent verifier must differ algorithmically:

- reconstruct free and quench candidate blocks from `2x2` momentum matrices;
- reconstruct potential candidate evolution from explicit sparse circuit matrices rather than the real-space update routine;
- rebuild target generators and exponentials without importing production matrix constructors;
- recompute the largest singular value from the Gram matrix at higher precision;
- recompute the Dyson tail certificate from exact rationals; and
- compare canonical scenario, state, map, and result hashes before accepting a ledger.

Agreement between two calls to the same linear-algebra routine is not independence. The final verifier must run from the clean committed result checkpoint and reject later scientific changes.

## 15. Allowed pre-freeze algebraic fixtures

Only these outcome-free implementation fixtures may be run before the freeze:

1. `N=8`, zero mass and zero potential: each directional basis state moves to its exact neighboring site after the declared swap layers.
2. `N=8`, zero transport duration: the identity is recovered.
3. `N=8`, a disclosed rational coin angle unrelated to every registered `delta_t m`: the real-space mixer equals its explicit `2x2` matrix.
4. A symbolic one-macrostep proof that the two swap layers equal `S` in the one-excitation sector.
5. A synthetic Fourier input with support `|r|<=1` on `N=16`: `E` is an isometry and the position and momentum POVMs each sum to one.
6. A target-only synthetic tridiagonal generator: production and independent exponential implementations agree within their certified numerical bound.
7. Negative fixtures with reversed gate order, a wrong Fourier sign, a missing swap layer, a nonunitary coin, an uncharged phase table, an out-of-partition scenario, and an enabled production seal must all be rejected.

The registered lattice sizes, masses, potential windows, state formulas, and full scenario combinations are forbidden in pre-freeze fixtures.

## 16. Known failure boundaries and negative controls

The claim is confined to `K_in`, masses at most `1/2`, `T<=2`, the registered potential amplitude, and the refinement ladder. After and only after a confirmation ledger is complete, the same sealed code reports these non-gating controls:

- `HIGH-K`: `N=256`, single modes `r=+/-48`, `m=1/2`, `T=2`;
- `HIGH-MASS`: `N=256`, `|r|<=4`, `m=8`, `T=2`;
- `LONG-HORIZON`: `N=256`, `|r|<=4`, `m=1/2`, `T=16`;
- `FINITE-RING`: `N=256`, zero-mass directional site basis through 256 macrosteps, exposing exact wrap and recurrence; and
- `DEPHASED`: the Zitterbewegung and interference witnesses with their positive/negative-energy coherence removed.

These controls cannot rescue or enlarge a pass. Unexpectedly good behavior outside the domain is only a reason to preregister another experiment. Unexpectedly bad behavior is reported as part of the failure anatomy.

## 17. Partitions and stopping rule

The experiment has two irreversible openings.

1. After the freeze, open all four development scenarios as one indivisible batch. Serialize one development result only after every scenario, refinement, operator certificate, symmetry check, and development witness finishes.
2. If any development gate fails, stop. Do not open confirmation.
3. If every development gate passes and both implementations verify, add the confirmation opening manifest in the next direct child and evaluate both confirmation scenarios as one indivisible batch.
4. Confirmation passes only if every primary, observable, conservation, causal, parity, and time-reversal gate passes. Then run and append all non-gating failure controls before the single confirmation result is written.

Interruptions, exceptions, worker failures, or unfinished certificates write no scientific result. Worker scratch data are not inspectable outcomes. No threshold, map, candidate gate, solver, state, scenario, or partition changes after freeze.

## 18. Linear provenance

The future freeze tag is

```text
icp-quantum-dirac-role-recovery-001-v0.1-frozen
```

The required history is:

1. one outcome-free commit that introduces the complete disabled seal, tagged with the annotated freeze tag;
2. a direct child changing only the development open manifest;
3. a direct child changing only the canonical development result;
4. if development passes, a direct child changing only the confirmation open manifest;
5. a direct child changing only the canonical confirmation result; and
6. only after independent verification, a documentation commit and completion tag.

The freeze commit must descend from the completed MIR closure and the pre-switch CI provenance repair. Opening code must verify clean worktree, exact parent, annotated tag target, seal hashes, disabled-to-enabled boundary, and sole changed path. Result verification must enforce the same lineage and reject a later worktree.

At this draft stage, no freeze tag, open manifest, result path, production command, or result artifact may exist.

## 19. Result taxonomy

The only scientific terminal classifications are

```text
development_gate_failed_confirmation_unopened
development_passed_confirmation_failed
constructive_sufficiency_passed_frozen_dirac_sector
execution_incomplete_no_result
provenance_invalid_no_result
```

A pass is not a minimum and does not establish necessity of phase, reversibility, two directional modes, the selected gate order, or any resource coordinate. Those require prospective ablations against the identical gate.

## 20. Success-contingent breadth program

The following are noncontrolling ideas, not registered candidates. They may be designed only after this experiment produces an independently verified pass.

1. **Direct symmetry-derived Dirac QCA.** Use the non-product update `[[n S_-,-i m],[-i m,n S_+]]`, with `n^2+m^2=1`, and an explicit Margolus localization. This tests a different finite-lattice dynamics with exact parity/time-reversal structure rather than Lie-Trotter gate ordering.
2. **Time-symmetric split construction.** Use a Strang-ordered half-mass, transport, half-mass circuit. This tests whether a different causal order improves symmetry and changes the convergence class while increasing elementary gate depth.
3. **Reversible classical lattice-gas role recovery.** On a separate branch, target a frozen hydrodynamic/telegraph sector with finite classical bits and reversible collision/streaming. This tests breadth across primitive class; it is not evidence for the quantum Dirac claim and must use a new resource normalization.

Running small parameter variations of the present product walk would measure robustness. It would not provide the breadth supplied by these different architectures.

## 21. Current draft state

The conceptual choices required by the handoff are now explicit: quantum resource normalization, exact candidate update, elementary gate clock, target subspace, metric and tolerances, interventions, causal-support semantics, refinement gate, partitions, failure controls, independent verification, and linear provenance.

The next outcome-free work is implementation and schema construction. This document must remain `not frozen` until that work and its independent audit are complete. No registered QCA outcome is authorized by this draft.
