# ICP Directed-Percolation Persistence `0.1-draft`

This directory is the frozen, outcome-free specification for search ID
`ICP-DP-PERSISTENCE-001`. The freeze commit adds the disabled content-hash seal
`experiments/dp_persistence/ICP-DP-PERSISTENCE-001/outcome_seal.json` and is
tagged `icp-dp-persistence-001-v0.1-frozen`. Every literature value entering a
gate was checked against a primary source (`VERIFICATION_LOG.md`). No outcome
existed when it was sealed.

## Question

> In the simplest law that keeps IOTA's amplitude ledger, vacuum budget, and
> exhaustion (`IOTA-MIN-L0`), does single-seed activity persist exactly when the
> fresh vacuum percolates? Is the growth at that threshold in the
> dynamic-percolation class?

## Why the minimal law

A threshold or universality-class match only counts as evidence if the law
wasn't tuned to produce it. The canonical v0.3.6 law gained a mechanism in most
versions, so the registered test runs on the minimal law instead. Each richer
mechanism comes back one rung at a time (`minimal_law.json`,
`ablation_ladder`), so any change in persistence is attributed to a named
mechanism.

## The minimal law, `IOTA-MIN-L0`

- **Lattice.** 64³ periodic, 6 face neighbours.
- **Sites.** A site is *active* (`a ≥ 1`), *fresh* (`a = 0`, latent budget
  `l = v = 2`), or *depleted* (`a = 0`, `l = 0`).
- **Medium.** Every non-seed site is fresh with probability `ρ`, otherwise
  depleted. The seed starts active with `a = 7`.
- **Tick (synchronous).** Each active site with at least one fresh neighbour
  sends one quantum to a uniformly chosen fresh neighbour. A fresh site that
  receives `k` quanta becomes active with `a = 2 + k`. A source that reaches
  `a = 0` becomes depleted.
- **Ledger.** `Σ(a + l)` is exactly constant.
- **Absorption.** Exact: no active site has a fresh neighbour.

Everything else is removed: vectors, payloads, range and decay, coupling gates,
valence, angular memory, rotation, residual bias, the sequential scheduler, and
down-gradient redistribution. Redistribution is deferred because a one-quantum
swap can reverse a gradient and oscillate forever. It returns as ladder rung 1,
with a termination audit.

The control is `ρ`, a probability of the medium. It cannot be absorbed into a
rescaling of time, which was the flaw in using `amplitude_coupling`. Below the
site-percolation threshold, every run must die.

## What is tested

- **H1, primary.** Is the persistence threshold `ρ_c` equal to the
  simple-cubic site-percolation threshold, 0.3116? The alternative is that it is
  pushed higher because an activated site holds only about 3 quanta and can
  strand parts of a thin cluster. No direction is predicted. The mechanism is
  measured directly as the fraction `E` of the seed's fresh cluster that a run
  actually explores.
- **H2, if H1 holds.** Spreading exponents `δ`, `η`, `z` match dynamic
  percolation in 3D. One-quantum-per-tick service can slow growth, so a match in
  `δ` and `η` with a different `z` is reported as "percolation statics,
  non-epidemic dynamics".
- **H3, if H1 holds.** The total explored mass has the percolation tail
  `P(S ≥ s) ~ s^−0.189`. This test doesn't depend on how time is counted.
- **L1, analytic.** Adding any reactivation of depleted sites (`r > 0`) makes
  activity immortal under an exact ledger. No sweep is needed, and the
  consequence for IOTA is that persistence questions about the canonical law
  must be asked of roles, not of activity.

## Stages

- **C, calibration.** Domany–Kinzel bond and site (1+1D), bond directed
  percolation (3+1D), one-tick SIR on the simple cubic lattice, and
  breadth-first growth on the site-diluted lattice. The last one is `L0` with an
  unlimited budget, and it is the exact reference for H1–H3.
- **A, audit.** Synthetic-state certification that the implemented `L0` is the
  specified law with the assumed structure.
- **S, sweep.** `ρ` from 0.25 to 0.70, then 6 bisection steps, with up to 20,000
  runs at the final point.
- **K, confirmation.** One use of held-out seeds at the three
  development-frozen `ρ` values.

## Files

- `minimal_law.json`: `L0`, the analytic `L1`, and the ablation ladder.
- `protocol.json`: stages, gates, outcome boundary, registered paths, deferred
  stage R.
- `reference_classes.json`: exponents, thresholds, and their checked citations.
- `calibration.json`: Stage C models and gates.
- `structural_audit.json`: Stage A questions, design answers, required checks,
  and the prediction record.
- `iota_spreading.json`: the Stage S grid, per-run record, H1–H3, and
  falsification.
- `estimators.json`: observables, censoring, local slopes, bracketing,
  classifier, and the static cluster-tail estimator.
- `partitions.json`: seeds and RNG streams.
- `result.schema.json`: result transport schema.
- `literature_basis.md`: sources and verification status.

The contract is `docs/ICP_DIRECTED_PERCOLATION_PERSISTENCE_CONTRACT.md`.

## Freeze

Each step below was completed before the freeze commit.

1. Verify every literature value against its primary source.
2. Implement `L0` as a new module (`src/iota_rig.py` is untouched), along with
   the calibration models, the estimator and classifier, and an independent
   replay.
3. Pass the engine tests (exact ledger, exact certificate, light cone,
   determinism, and an identical explored set to breadth-first growth wherever
   the budget cannot bind) and the classifier tests on exact synthetic power
   laws.
4. Write a disabled content-hash seal, commit, and tag
   `icp-dp-persistence-001-v0.1-frozen`.

## Not claimed

The result applies to `IOTA-MIN-L0` only. It reaches richer laws only through
the ladder. It measures lattice-activity persistence, not role persistence,
which is deferred stage R. Effective exponents at `L = 64` are window
estimates. There is no novelty claim for percolation, DP, or DyP physics.

## Implementation

The pre-freeze code is in `src/dp_persistence/`, and its tests are in
`tests/dp_persistence/`. `make validate-dp-persistence` runs the audit, then
`verify-seal` if a seal exists, then the test suite. Commands are run as
`python -m src.dp_persistence.cli <command>`:

| Command | Behaviour |
|---|---|
| `audit` | Outcome-free consistency checks between the spec and the package. |
| `structural-audit --output PATH` | Runs every Stage A required check on synthetic 9³ states. Writes only to `PATH`, and refuses registered paths. |
| `freeze-seal` | Writes the disabled content-hash seal. |
| `verify-seal` | Verifies the seal against current bytes. |
| `open-calibration`, `run-calibration` | Stage C. |
| `open-development`, `run-development` | Stage S. Requires the calibration result committed with every gate passing, and the Stage A answers committed. |
| `open-confirmation`, `run-confirmation` | Stage K. Single use at the three development-frozen ρ values. |

Each `open-*` and `run-*` command refuses unless all of these hold:

- the committed seal verifies;
- the annotated tag `icp-dp-persistence-001-v0.1-frozen` selects the
  seal-introduction commit and is an ancestor of HEAD;
- the worktree is clean;
- for `run-*`, HEAD adds only the stage's committed open manifest.

Open readings of the spec are listed in `SPEC_QUESTIONS.md`. Literature checks
are in `VERIFICATION_LOG.md`.
