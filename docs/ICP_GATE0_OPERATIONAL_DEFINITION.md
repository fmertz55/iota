# Interventional-Divergence Diagnostic

Historical filename: `ICP_GATE0_OPERATIONAL_DEFINITION.md`

Version: `0.1-draft`

Date: 2026-07-13

Status: **draft diagnostic; superseded as the root ICP gate**

The controlling program specification is now the
[ICP Minimal Informational Realization Contract](ICP_MINIMAL_INFORMATIONAL_REALIZATION_CONTRACT.md).
That contract treats mapped causal-role recovery from minimal informational
primitives as the thesis. The JSD and entropy quantities below remain candidate
diagnostics for internal intervention effects or cross-model discrepancies.
They do not define ICP and do not establish informational realization.

This document defines an interventional-divergence diagnostic in
implementation-independent terms. It is intentionally written without using
IOTA transition or detector code as the definition. The IOTA-specific binding
near the end is retained as a historical proposed validation instance.

Data access now follows the development and held-out rules in the controlling
minimal-realization contract. A material change to this diagnostic creates a
new diagnostic version; it does not return the realization thesis to a
JSD-centered gate.

## 1. Ordinary-language name and scope

The operational object defined here is an **interventional divergence between
conditional future-trajectory distributions**. In established terminology it
is a bounded distributional causal-effect measure with an entropy-direction
companion. `ICP` remains the project hypothesis name; it is not a claim that the
underlying divergence is new.

The definition applies initially to a finite or countable, discrete-time
stochastic dynamical system over a finite horizon. Continuous state spaces,
continuous time, thermodynamic limits, quantum systems, and physical ontology
are outside Gate 0.

The definition does not by itself establish:

- transport of information;
- semantic information;
- a new causal-strength measure;
- observer-independent organization;
- material or carrier independence;
- universality across dynamical systems; or
- any physical or pre-quantum interpretation.

Those would require additional operational definitions and evidence.

## 2. System state and stochastic dynamics

Let `(Omega, F, mu)` be a probability space carrying an exogenous process

```text
U = (U_t, U_(t+1), ...).
```

Let `S` be a finite or countable endogenous state space. A state `S_t = s`
must contain every endogenous variable needed to determine the conditional law
of future endogenous states under the fixed law. Hidden simulator variables may
not be omitted merely because the observer does not report them.

For a fixed law `L`, one transition is

```text
S_(t+1) = F_L(S_t, U_t).
```

If one nominal tick contains ordered subevents, `U_t` may be a finite or
countable collection of exogenous variables and `F_L` must state the order in
which subevents are evaluated. A scheduler that affects the transition must be
one of:

1. fixed as part of `L`;
2. represented in `S_t` when its state carries across transitions;
3. represented in `U_t` when randomly redrawn; or
4. explicitly targeted by an intervention.

It may not remain implicit implementation behavior.

The filtration is

```text
F_t = sigma(S_0, U_0, ..., U_(t-1)),
```

or another explicitly declared filtration that makes `S_t` measurable and
future exogenous variables distributed according to the declared conditional
law. Dependence, exchangeability, and stationarity of `U` must be stated; none
is assumed by the symbol `U_t` alone.

### Complete-state convention

The ICP distribution conditions on endogenous state `S_t=s` but marginalizes
over the declared future exogenous process. It does **not** condition on a
realized future PRNG stream. Conditioning on a complete future random stream
would make deterministic code paths point masses and can make the proposed
probability-sensitive quantity scientifically vacuous.

A pseudorandom generator is an implementation of sampling from `mu`, not the
definition of `mu`. Its internal state is implementation metadata unless the
scientific question explicitly treats that state as endogenous.

## 3. Intervention

An intervention is a declared replacement of part of the transition mechanism,
not a retrospective selection of trajectories by their outcome.

Let `q` identify a transition component and let `W = {t, ..., t+d-1}` be an
intervention window. The intervention `do(a)` replaces that component during
`W` by a declared mechanism `F_q^a`, leaving every non-target component fixed:

```text
F_L  ->  F_(L, q <- a, W).
```

The intervention record must state:

- the state or mechanism target;
- the intervention start and duration;
- whether the intervention sets, deletes, randomizes, or replaces a mechanism;
- variables held fixed;
- conservation or other invariants preserved;
- whether an otherwise scheduled exogenous draw is still allocated; and
- how downstream scheduling is defined after the intervention changes state.

The primary contrast has two arms:

```text
a     = the natural or interaction-present mechanism;
a_0   = a scientifically meaningful matched reference mechanism.
```

`a_0` may be a mechanism deletion, randomized replacement, sign reversal, or
other declared null. It is not automatically meaningful merely because it is
easy to code. The contrast must be justified in terms of the causal question.

Selection of `(s, q, W, a, a_0)` must use information available before the
future outcomes included in the analysis. Outcome-selected interventions do not
identify a prospective effect without a separate selection correction.

## 4. Future probability law and reachable support

Fix a positive integer horizon `H`. Let

```text
g : S^H -> Y
```

be a measurable, frozen observation map from the endogenous trajectory
`S_(t+1:t+H)` to an outcome `Y`. The outcome space `Y`, label serialization,
graph convention, tie handling, censoring, and every coarse-graining threshold
must be declared before outcomes.

The arm-specific conditional future distribution is

```text
P_(a,H)^g(y | s)
  = Pr_mu[g(S_(t+1:t+H)) = y | do(a), S_t=s].
```

The matched reference distribution is `P_(a_0,H)^g(. | s)`.

The reachable support is

```text
R_(a,H)^g(s) = {y in Y : P_(a,H)^g(y | s) > 0}.
```

For the finite/countable Gate 0 domain, support means strictly positive
probability under the mathematical law. A sampled-but-unseen outcome is not
proved to have zero probability. Empirical support estimates therefore require
an explicit estimator and cannot substitute silently for mathematical support.

The two arm distributions must be represented on the union outcome space

```text
Y_* = R_(a,H)^g(s) union R_(a_0,H)^g(s),
```

with zero mass assigned where an arm does not support a label.

## 5. Information and direction quantities

All logarithms in Gate 0 use base 2. Entropies and divergences are measured in
bits.

For a discrete distribution `P`, define Shannon entropy

```text
H(P) = - sum_y P(y) log2 P(y),
```

using `0 log2 0 = 0`.

Let

```text
P = P_(a,H)^g(. | s)
Q = P_(a_0,H)^g(. | s)
M = (P + Q) / 2.
```

The primary operational ICP magnitude is

```text
I_ICP(s; a, a_0, H, g)
  = JSD(P || Q)
  = H(M) - [H(P) + H(Q)] / 2.
```

For equal arm weights and base-2 logarithms,

```text
0 <= I_ICP <= 1 bit.
```

`I_ICP = 0` if and only if the two declared outcome distributions are equal.
Jensen-Shannon divergence is symmetric: it measures distinguishability of the
two future distributions but does not say which arm is more constrained.

The signed entropy companion is

```text
Delta H_ICP(s; a, a_0, H, g) = H(Q) - H(P).
```

Under the arm orientation above:

- `Delta H_ICP > 0`: the natural/interaction-present arm is more concentrated
  in the declared observable than the reference arm;
- `Delta H_ICP = 0`: equal entropy, including possible deterministic
  redirection or equal-support reshaping; and
- `Delta H_ICP < 0`: the natural/interaction-present arm is more dispersed in
  the declared observable than the reference arm.

When exact finite supports are available, the optional Hartley companion is

```text
Delta H_0 = log2 |R_(a_0,H)^g(s)| - log2 |R_(a,H)^g(s)|.
```

`Delta H_0` is never the primary endpoint. It is undefined for an empty support,
which cannot occur for a valid probability distribution, and may be infinite
for countably infinite support. Gate 0 makes no continuous-space extension of
this quantity.

### Interpretation boundary

`I_ICP` is a distributional causal-effect magnitude under the declared
intervention and observation map. `Delta H_ICP` supplies a constraint direction
only relative to that map. Neither quantity alone distinguishes an organized
relation from any other intervention with the same distributional effect.

Consequently, an empirical claim must name the mechanism intervention and the
observable. The phrase `information itself caused` is not licensed by a
nonzero divergence.

## 6. Predicted observable

There are three nested claims, which must not be collapsed:

### 6.1 Distributional-effect claim

For prospectively selected states and a declared mechanism contrast, the
natural and matched-reference future distributions differ by more than a frozen
equivalence region:

```text
I_ICP > epsilon_JSD.
```

Failure means the intervention has no resolved effect on the declared future
observable at the selected horizon and precision.

### 6.2 Constraint-direction claim

When the scientific claim uses the word `constraint`, it additionally predicts

```text
Delta H_ICP > epsilon_H.
```

A nonzero `I_ICP` with `Delta H_ICP <= epsilon_H` supports redirection or
reshaping, not the stated entropy-concentration claim.

### 6.3 Relational re-instantiation claim

For a relational-persistence study, `g` must contain a prospectively declared,
identity-independent relational-role observable. The candidate observable is a
first-passage outcome:

```text
Y_role = (T_reinst, W_reinst, C_H),
```

where:

- `T_reinst` is the first transition in `1..H` at which the declared relation
  is realized after its declared loss, or `none` if absent by `H`;
- `W_reinst` is a canonical, material-identity-independent witness class for
  that realization, including whether it is disjoint from the predecessor
  witness; and
- `C_H` is a declared censoring/status label at the horizon.

The role prediction must include both the distributional quantities above and
the directly interpretable risk difference

```text
Delta p_role
  = Pr_a(T_reinst != none and W_reinst is disjoint)
    - Pr_(a_0)(T_reinst != none and W_reinst is disjoint).
```

The sign, minimum effect, unit of replication, horizon, and graph/relation
definition remain **unfrozen blockers** in version `0.1-draft`. They must be
fixed before Gate 0 can pass. Existing IOTA outcomes may inform transparent
development but cannot be relabeled as confirmatory evidence for the frozen
version.

## 7. Exogenous-noise allocation and estimation target

The estimand is the pair of marginal distributions `(P, Q)`. A coupling between
the two arms is an estimator design choice, not part of `I_ICP`.

Valid implementations may use:

1. exact enumeration of the exogenous variables;
2. independent continuation samples in the two arms; or
3. common random numbers keyed to semantic event identities rather than to
   mutable execution order.

Sequential PRNG consumption indexed only by call order is permitted as a fully
specified sampler for each marginal distribution. It is not a valid basis for
interpreting pointwise paired descendant differences after an intervention
changes control flow, because later draws may be reassigned to different events.

Every estimator must declare whether it targets exact probabilities or a
finite-sample approximation, and must specify uncertainty, convergence, unseen
outcome handling, smoothing, and stopping rules. These are Formal-Gate matters;
Gate 0 fixes the exact target they must estimate.

## 8. Invariance and representation tests

The operational quantity must satisfy the following Gate 0 agreement checks:

1. **Common bijective relabeling:** applying the same bijection to outcome
   labels in both arms leaves `I_ICP` and `Delta H_ICP` unchanged.
2. **Arm exchange:** exchanging `a` and `a_0` leaves `I_ICP` unchanged and
   reverses the sign of `Delta H_ICP`.
3. **Zero-probability padding:** adding the same unused labels with zero mass
   leaves both quantities unchanged.
4. **Non-bijective coarse-graining:** merging outcome labels may change both
   quantities. This sensitivity must be reported, not called a violation of
   label invariance.
5. **Mixture weights:** Gate 0 uses equal arm weights. Changing weights defines
   a different quantity and requires a new version.

## 9. Canonical semantic fixtures

Each fixture uses the ordered outcome alphabet `['y0', 'y1']`, with `P` for the
natural arm and `Q` for the matched reference arm. Required agreement tolerance
is absolute error at most `1e-12` for the analytic values below.

| Fixture | `P` | `Q` | `I_ICP` bits | `Delta H_ICP` bits | Purpose |
|---|---:|---:|---:|---:|---|
| no interaction | `[0.5, 0.5]` | `[0.5, 0.5]` | `0` | `0` | equality |
| same deterministic future | `[1, 0]` | `[1, 0]` | `0` | `0` | deterministic null |
| deterministic redirection | `[1, 0]` | `[0, 1]` | `1` | `0` | causal difference without entropy constraint |
| strict support reduction | `[1, 0]` | `[0.5, 0.5]` | `0.311278124459133` | `1` | concentration and support loss |
| equal-support reshaping | `[0.9, 0.1]` | `[0.5, 0.5]` | `0.146793102436052` | `0.531004406410719` | probability reshaping without support loss |
| support expansion | `[0.5, 0.5]` | `[1, 0]` | `0.311278124459133` | `-1` | signed direction |

For the common-relabeling fixture, both arms of `equal-support reshaping` are
serialized under the bijection `y0 -> alpha`, `y1 -> beta`; all numeric outputs
must remain identical.

Canonical machine-readable fixtures and schemas are committed under
`specs/icp_gate0/v0.1-draft/`. They remain draft artifacts until specification
version `1.0` is frozen.

## 10. Independent implementation agreement

Gate 0 requires two isolated implementations.

Each implementer receives only:

- the frozen version of this specification;
- canonical serialized fixtures;
- the input/output schema; and
- a blank ambiguity-report template.

An implementation may not import IOTA transition code, detector code, or the
other implementation. Before code freeze, implementers may submit written
ambiguity reports. Any answer becomes a dated specification amendment visible
to both implementers; private explanatory guidance is prohibited.

After both implementations and environment manifests are frozen, a neutral
comparison checks:

- identical outcome alphabets and arm orientation;
- normalized probability distributions;
- all canonical values within tolerance;
- invariance-test results;
- identical treatment of zero mass; and
- identical error classification for malformed fixtures.

Disagreement fails Gate 0 and returns the specification for repair. Agreement
passes only semantic implementation of the small fixtures. Full independent
reimplementation of the experimental system remains an Artifact-Gate test.

## 11. Proposed IOTA binding for later Formal-Gate validation

This section records what the current simulator audit implies. It is a draft
binding and may not be used to generate a held-out result.

### 11.1 Candidate endogenous state

For the current hard-transfer law, the candidate `S_t` contains the complete
lattice arrays

```text
active, A, R, V, P, latent_A, angular_L, previous_active.
```

The fixed law parameter `L` contains lattice dimensions, boundary condition,
vector-state table and behavior table, all transition constants, neighborhood
ordering, source scheduler, and candidate scheduler. `previous_V` appears to be
retained output bookkeeping rather than an input to the current hard-transfer
transition; this must be confirmed by a dependency test before freeze.
`initial_total_A` and `ledger_enabled` are safety/accounting metadata unless a
transition dependency is demonstrated.

The candidate state explicitly excludes the NumPy PRNG internal state. Future
randomness is marginalized under a declared product measure or another frozen
exogenous law.

### 11.2 Scheduler semantics discovered in the audit

The current law is not simply synchronous. Tick-start active sources are
enumerated in lexicographic array order. Source fields are read from tick-start
arrays, while target eligibility and available amplitude can depend on earlier
events in the same tick. Candidates have a deterministic primary/neighborhood
ordering plus stochastic secondary selection, and random draws are consumed
sequentially as execution proceeds.

Those semantics must be written into the IOTA law binding or deliberately
replaced by a new validation implementation. They cannot be treated as harmless
coding details.

### 11.3 Current noise limitation

Existing paired branch interventions preserve the selected gate draw and can
verify a sham arm exactly. Once an effective intervention changes control flow,
later sequential PRNG draws can attach to different candidate events. Therefore
existing same-seed descendant pairs do not supply event-keyed common noise.

The Formal Gate must choose and preregister either:

- independent continuation ensembles for estimating each arm marginal; or
- a counter/key-based event noise scheme and a validation showing that keys are
  stable under the declared intervention.

No choice has been frozen.

### 11.4 Unfrozen IOTA intervention and observable

The scientifically strongest candidate is a prospective predecessor-mechanism
intervention followed by the role first-passage observable in Section 6.3. A
successor-bridge deletion alone establishes endpoint necessity but does not test
whether an earlier relation preferentially changes later re-instantiation.

The following remain blockers:

- the exact predecessor mechanism and matched reference;
- prospective state/event selection;
- tracked-region definition;
- relation and witness definition;
- horizon and censoring;
- `epsilon_JSD`, `epsilon_H`, and minimum `Delta p_role`;
- analysis and replication units; and
- multiplicity and uncertainty rules.

## 12. Gate 0 pass/fail state

Version `0.1-draft` **does not pass Gate 0**.

Completed:

- core state/probability/intervention semantics drafted;
- primary and signed companion quantities defined;
- analytic fixture values specified;
- ordinary terminology and novelty boundary stated;
- initial pre-validation literature search committed; and
- current IOTA state, scheduler, and noise issues audited.

Still required:

1. freeze the IOTA intervention and relational observable;
2. freeze effect/equivalence thresholds and replication unit;
3. validate and freeze the machine-readable fixture and result schemas;
4. complete the literature coverage gaps and closest-work comparison;
5. obtain independent ambiguity review;
6. freeze specification version `1.0`; and
7. obtain agreement from two isolated implementations.
