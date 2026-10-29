# ICP Directed-Percolation Persistence Contract

Version: `0.1-draft`

Search ID: `ICP-DP-PERSISTENCE-001`

Date: `2026-10-27` (drafted); frozen `2026-10-29` (revision `0.1.1`)

Status: **outcome-free design; frozen; outcomes sealed**

Freeze: seal `experiments/dp_persistence/ICP-DP-PERSISTENCE-001/outcome_seal_v0.1.1.json`,
tag `icp-dp-persistence-001-v0.1.1-frozen`. It supersedes the unopened `v0.1`
freeze to correct the critical-midpoint bisection direction.

Data class: **development with single-use confirmation**

Machine-readable specification:
`specs/icp_directed_percolation_persistence/v0.1-draft/`

## 1. Question

IOTA's organizing question is whether finite local interactions can produce
constraints on reachable futures that persist when their realization is
replaced. Before that question can be asked of organizations, the substrate's
own persistence has to be characterized against physics that IOTA did not
write.

> In the simplest law that keeps IOTA's amplitude ledger, vacuum budget, and
> exhaustion, does single-seed activity persist exactly when the fresh vacuum
> percolates? Is the growth at that threshold in the dynamic-percolation class?

Percolation, directed percolation (DP), and dynamic percolation (DyP) are the
established theories of whether locally propagated activity persists or dies.
Their thresholds and exponents were fixed independently, and DP has been
observed in laboratory turbulence.

## 2. Why the minimal law

A match to external physics is evidence only if the law was not tuned to
produce it. The canonical v0.3.6 law gained mechanisms across versions,
including angular memory, residual recruitment, geometry-weighted bias, and
component-bridge scoring. This protocol therefore registers its test on
`IOTA-MIN-L0`, which keeps only:

- integer amplitude quanta with an exact ledger;
- latent vacuum budget, absorbed on activation; and
- exhaustion into a permanently depleted site.

Every other mechanism is removed. It returns later, one rung of the ablation
ladder at a time, so that any change in threshold or class is attributed to a
named mechanism. Down-gradient redistribution is deliberately the first rung,
not part of the minimal law. A one-quantum transfer between amplitudes 3 and 2
reverses the gradient and can oscillate forever, so the rung needs its own
termination audit.

## 3. The law

Lattice 64³, periodic, face neighbourhood. A site is active (`a ≥ 1`), fresh
(`a = 0`, `l = 2`), or depleted (`a = 0`, `l = 0`). Each non-seed site is fresh
with probability `ρ`. The seed starts with `a = 7`.

Each synchronous tick:

1. every active site with a fresh neighbour sends one quantum to one of them,
   chosen uniformly;
2. a fresh site that receives `k` quanta becomes active with `a = 2 + k`;
3. a source that reaches `a = 0` becomes depleted.

`Σ(a + l)` is exactly conserved. The state is absorbed exactly when no active
site borders a fresh site. The full specification is in `minimal_law.json`.

The control `ρ` is a probability of the medium. Unlike `amplitude_coupling`,
which multiplies every gate, it cannot be absorbed into a rescaling of time.

Two facts hold by construction. Activity can only enter fresh sites, so below
the site-percolation threshold every run dies. Above it, a run can still die by
stranding: an activated site holds about 3 quanta and has up to 5 fresh
neighbours.

## 4. Hypotheses

- **H1 (primary).** `ρ_c` equals the face-neighbour simple-cubic
  site-percolation threshold, 0.31160768. The outcome is "equal" within 0.005,
  or "budget_shifted" above it. No direction is predicted. Every evaluated `ρ`
  reports the exploration completeness `E`, the fraction of the seed's fresh
  cluster actually activated, so the mechanism is measured, not inferred.
  `ρ_c < p_c` is impossible by construction and voids the run.
- **H2 (if H1 is equal).** `δ`, `η`, `z` match `DyP_3`. A match in `δ` and `η`
  with a mismatch in `z` is reported as "percolation statics, non-epidemic
  dynamics", because one-quantum service can slow growth.
- **H3 (if H1 is equal).** `P(S ≥ s) ~ s^−(τ−2)` with `τ − 2 = 0.18906`, a test
  that does not depend on how time is counted.
- **L1 (analytic).** With any reactivation `r > 0` of depleted sites, activity
  is immortal under the exact ledger.

The L1 argument: the active amplitude never falls below the seed's, so an
active set always exists. Every finite active set has a boundary site with an
inactive neighbour, which is eligible with probability 1 if fresh or `r` if
depleted. So the absorbing certificate can never hold.

Consequence: in IOTA's canonical laws (residual recruitment > 0), lattice
activity cannot die. Persistence there is meaningful only for specific
organizations, which is deferred stage R.

If H1 is "budget_shifted", the transition is spreading on a supercritical random
medium. Quenched disorder is then relevant for DP in 3D (Harris criterion:
`dν⊥ = 1.75 < 2`), so no clean class is registered and H2 and H3 are reported as
exploratory.

## 5. Why this is a fair test

- **External numbers.** No threshold, exponent, or tolerance is chosen after an
  outcome.
- **The instrument is proven first.** Stage C must recover the Domany–Kinzel
  thresholds and DP in 1+1D, DP in 3+1D, DyP for one-tick SIR, and the site
  threshold and `τ` for breadth-first growth on the diluted lattice. That last
  model is `L0` with an unlimited budget.
- **Structure is certified first.** Stage A tests the implemented engine on
  synthetic media (exact ledger, exact certificate, light cone, determinism) and
  commits the prediction record before Stage S.
- **Every outcome means something.** "Equal" and "budget_shifted" are both
  substantive results.

## 6. Outcome boundary

No registered random medium may be drawn, and no `ρ` sweep run, before all of
the following are committed together:

- this contract and the specification;
- verified literature values;
- the `L0` engine as a new module (`src/iota_rig.py` unchanged), the calibration
  models, and the estimator and classifier;
- independent replays of the engine, estimator, and classifier;
- the engine and classifier tests; and
- a disabled content-hash seal, tagged `icp-dp-persistence-001-v0.1.1-frozen`.

A failing calibration ends this version.

## 7. Stages

| Stage | Name | Gate |
|---|---|---|
| C | Instrument calibration | classes, thresholds, and `τ` recovered within tolerance |
| A | L0 implementation and structure audit; L1 analytic check | answers, synthetic tests, prediction record committed |
| S | L0 single-seed sweep over `ρ` | development result committed |
| K | Single-use confirmation | confirmation result committed |

## 8. Ablation ladder (planned; separate freezes)

| Rung | Change from the previous rung |
|---|---|
| 0 | `IOTA-MIN-L0` (this version) |
| 1 | down-gradient redistribution, non-reversing rule `a_y ≤ a_x − 2`, with a termination audit |
| 1b | cube26 neighbourhood (reference threshold 0.0976) |
| 2 | probabilistic gates, `min(1, k × influence)` |
| 3 | sequential lexicographic scheduler |
| 4 | vectors and vector-directed targets |
| 5 | payload labels (expected to have no effect on activity) |
| 6 | angular memory, rotation, and residual bias, with residual probability 0 |
| 7 | residual recruitment > 0 (activity immortal by L1; the question moves to roles) |

## 9. Deferred stage R

Two hypotheses are recorded here but not registered. Each needs an
already-frozen role detector:

1. Role-continuing successors of a tracked organization, treated as the active
   unit, show an absorbing transition.
2. The fraction of partial carrier replacements that a role survives falls
   toward zero as the critical point is approached. This is the
   noise-sensitivity prediction.

## 10. Claim limits

- A result for `IOTA-MIN-L0`. It transfers to richer laws only through the
  ladder.
- Lattice-activity persistence only. This is not organization or role
  persistence.
- Not physical percolation in any material system, and not substrate
  validation.
- Effective exponents at `L = 64` over the registered window.
- No novelty claim for percolation, DP, DyP, or the instrument.
