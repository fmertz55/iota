# Implementation prompt: ICP-DP-PERSISTENCE-001 (pre-freeze code)

Paste everything below the line into a coding agent opened at the root of the
`iota` repository.

---

You are implementing the pre-freeze code for the preregistered protocol
`ICP-DP-PERSISTENCE-001` in this repository. The protocol is specified, not yet
frozen. Your job is to build everything the freeze requires and to generate
**no registered outcomes**.

## Read first, in this order

1. `specs/icp_directed_percolation_persistence/v0.1-draft/README.md`
2. `docs/ICP_DIRECTED_PERCOLATION_PERSISTENCE_CONTRACT.md`
3. Every JSON file in `specs/icp_directed_percolation_persistence/v0.1-draft/`.
   `minimal_law.json`, `estimators.json`, `calibration.json`,
   `partitions.json`, and `result.schema.json` are normative.
4. For repository conventions only: `src/minimal_realization_role_succession/`
   (`cli.py`, `seal.py`, `manifest.py`, `runner.py`, `verifier.py`), its tests
   in `tests/minimal_realization_role_succession/`, the `Makefile`, and
   `specs/icp_minimal_realization_role_succession/v0.1-draft/README.md`. Match
   their style for CLI shape, seal format, manifest gating, atomic result
   writes, and tests.

The sister project `/Users/douglasclark/ICP` (Information-Constraint Principle)
is context only. Do not modify it.

## Hard rules

1. **No outcomes.** Do not draw a registered random medium. Do not run any
   calibration model at its registered lattice size, grid, or run count. Do not
   sweep `rho`. Do not write any path listed under `registered_paths` in
   `protocol.json`. Tests may use only hand-built synthetic media, tiny lattices
   (at most 16³ in 3D, at most 256 sites in 1D), and synthetic ledgers with
   known exact power laws.
2. **Do not modify** `src/iota_rig.py`, any existing spec, or any existing test.
3. **Do not commit, tag, or freeze.** The owner does that. Leave the work
   uncommitted.
4. **Do not resolve spec ambiguity silently.** If any field is ambiguous,
   contradictory, or underspecified, implement the most literal reading. Then
   record it in
   `specs/icp_directed_percolation_persistence/v0.1-draft/SPEC_QUESTIONS.md`
   with the file, the field, the reading you chose, and the alternatives.
5. **Dependencies:** numpy, pyyaml, the standard library, and `jsonschema` for
   schema validation. Add `jsonschema` to `requirements.txt` only if it is
   missing.

## Deliverables

Create the package `src/dp_persistence/` with:

### 1. `rng.py`
Seed derivation exactly as specified. Calibration streams use
`calibration.json` → `rng.seed_derivation`. IOTA streams use `partitions.json`
→ `iota_development.streams`: numpy `PCG64` seeded with the integer formed by
the first 8 big-endian bytes of SHA-256 over the ASCII-plus-NUL domain string.
Use separate `medium` and `dynamics` streams, and a domain-separated bootstrap
stream.

### 2. `l0_engine.py` (vectorized numpy)
Implement `IOTA-MIN-L0` exactly as `minimal_law.json` → `laws.L0` specifies:
- 64³ periodic lattice, face6 neighbours.
- Fixed neighbour order `(+x, -x, +y, -y, +z, -z)`.
- `v = 2`, `a0 = 7`, seed at `(32, 32, 32)`.
- Medium: draw `L³` variates in one call, in lexicographic order. A site is
  fresh iff its variate `< rho`. The seed site's variate is drawn and
  discarded.
- Synchronous tick. Every active source with fresh neighbours consumes one
  `u = rng.random()`, in lexicographic source order, and sends to
  `E_x[floor(u * |E_x|)]`.
- A fresh site receiving `k` quanta becomes active with `a = v + k`. A source
  that reaches `a = 0` becomes depleted.

Expose:
- `absorbing_certificate(state)`: true iff no active site borders a fresh site.
- `step(state, rng) -> (state, tick_record)`.
- `run(rho, run_seed, horizon, L=64)`. It returns the per-run record listed in
  `iota_spreading.json` → `per_run_record`: `n_t` and `r2_sum_t` per tick,
  `absorbed_at`, `censored_at`, `S`, and the stranded amplitude. For absorbed
  runs it also returns `C`, computed by breadth-first search over the fresh
  face6 clusters adjacent to the seed in the initial medium, and `E`. It must
  also return the ledger residual, which must be exactly 0.

Censoring is per `estimators.json` → `observables_per_run.censored_at`: any
active or ever-active site at minimum-image Chebyshev distance `>= L/2 - 4`
from the seed. The active unit for `n_t` is a site that sends or receives a
quantum in that tick. `r2_sum_t` uses the minimum-image Euclidean distance.

### 3. `l0_replay.py` (independent implementation)
A deliberately different code path: pure Python, per-site loops, dictionaries
instead of arrays, no code shared with `l0_engine.py` except `rng.py`. It must
agree with `l0_engine.py` bit for bit, including every RNG draw, on every test
case.

### 4. `l1.py`
The L1 reactivation rule (`minimal_law.json` → `laws.L1`, including
`draw_rule`), for the synthetic analytic check only. Add no sweep entry point.

### 5. `calibration_models.py`
- `CAL-DK-BOND-1P1` and `CAL-DK-SITE-1P1` (Domany–Kinzel).
- `CAL-BOND-DP-3P1`: bond DP, 6 face neighbours plus self.
- `CAL-SIR-SC-3`: one-tick SIR on the simple cubic lattice.
- `CAL-SITE-BFS-SC-3`: breadth-first growth on the site-diluted simple cubic
  lattice.

Each exposes the same per-run record interface as L0, with its own active unit
and absorbing test from `calibration.json`. Each must also expose `S` and the
cluster quantities where the static estimator needs them.

### 6. `estimators.py`
Implement every section of `estimators.json` exactly:
- aggregates `P(t)`, `N(t)`, `R²(t)`, with censoring;
- the fit window (`t_min`, `t_max`, and the 1% censoring rule);
- the geometric ladder `t_k = round(t_min * 2^(k/4))` with `m = 4` local slopes;
- the `no_absorption_observed` precheck;
- the weighted slope `s` of `delta_eff` against `ln t`, with a 1000-resample
  whole-run bootstrap and its 95% interval;
- bracketing: coarse grid, multiple brackets, arithmetic or geometric bisection,
  and the final-point rule;
- exponent estimates with statistical, systematic, and total SE;
- the `crossover_in_window` flag;
- the `static_cluster_size` estimator: CCDF with right censoring, exact range
  `[16, s_cut]`, ladder ratio `2^(1/4)`, and `range_too_short` when
  `s_cut < 256`.

### 7. `classifier.py`
Per-exponent, per-class, and verdict rules. Absolute tolerances for 1+1D and
3D. Hyperscaling downgrade, using `theta = d/z - 2δ` for DP and
`eta = d/z - 2δ - 1` for DyP. The H1, H2, and H3 outcome logic from
`iota_spreading.json` → `hypotheses`, including `instrument_failure` for
`rho_c < p_c - 0.005 - 2·SE` and the
`percolation_statics_non_epidemic_dynamics` label. All reference values are
read from `reference_classes.json` at runtime; hard-code none.

### 8. `estimators_replay.py`
An independent implementation of items 6 and 7 that shares no estimator code.
It must agree with them to `1e-12` on every synthetic ledger.

### 9. `ledger.py`
- Atomic, exactly-once result writing.
- Result validation against `result.schema.json` plus cross-field checks: the
  ledger residual is 0; a verdict is consistent with `per_class`; H2 and H3 are
  `not_applicable` unless H1 is `equal`; every seed lies in its partition range.
- Trace hashing in the style of the role-succession protocol.

### 10. `seal.py` and `cli.py`
Commands, following the existing conventions:

| Command | Behaviour |
|---|---|
| `audit` | Outcome-free spec and implementation consistency checks. |
| `structural-audit` | Runs every Stage A `required_check` on synthetic states. Writes its answers only to a temporary path given on the command line, never to the registered path. |
| `freeze-seal` | Writes a content-hash seal over the spec directory, the contract, the package, and its tests, with `run_command_enabled: false`. |
| `verify-seal` | Verifies the seal. |
| `open-calibration`, `run-calibration`, `open-development`, `run-development`, `open-confirmation`, `run-confirmation` | Implemented, but each refuses unless a committed seal, the annotated tag `icp-dp-persistence-001-v0.1-frozen` on the seal-introduction commit, a clean worktree, and the stage's committed open manifest all exist. `run-development` must also refuse unless the calibration result and the Stage A answers are committed and every calibration gate passed. |

Runners use 4 spawn workers with one complete run as the parallel unit. They
collect results in canonical order, write no partial artifacts, enforce the
per-point wall-clock ceiling, and offer no worker-count or grid override flags.

### 11. Tests in `tests/dp_persistence/`
At minimum:

**Engine**
- exact ledger on 1000 random synthetic 9³ media;
- the certificate is exact: if true, the next tick is bit-identical; if false,
  at least one transfer occurs;
- light cone: no site beyond Chebyshev distance `t` is touched by tick `t`;
- determinism under fixed seeds;
- `l0_engine` and `l0_replay` are bit-identical on 200 synthetic cases;
- equivalence to `CAL-SITE-BFS-SC-3`'s final reached set on synthetic media
  where every fresh site has at most `v + 1` fresh neighbours (timing may
  differ);
- below-threshold absorption on a hand-built finite fresh cluster;
- the stranding example (a site with `a = 3` and 5 fresh neighbours serves at
  most 3 of them);
- the L1 synthetic test: a configuration stranded under L0 is non-absorbing
  under L1 for `r > 0`.

**Estimators and classifier**
- synthetic ledgers with exact DP 1+1, DP 3+1, and DyP 3 power laws are each
  classified correctly;
- a flat `P(t) = 1` ledger yields `no_absorption_observed`, not
  `critical_compatible`;
- an exponential-decay ledger yields `subcritical`;
- an exact `s^-(tau-2)` tail recovers `tau - 2`;
- censoring handling, bracketing, multiple-bracket reporting, and the
  hyperscaling downgrade;
- agreement between the replay and primary estimators.

**Calibration models**
Tiny-lattice behaviour tests only: `p = 0` dies immediately, `p = 1`
deterministic growth matches the light cone, and the BFS model's reached set
equals the connected cluster.

**Seal and CLI**
- every gated command refuses without seal, tag, clean tree, and manifest;
- no command writes a registered path in tests (use temporary directories).

### 12. Makefile and docs
- Add a target `validate-dp-persistence` that runs `audit`, `verify-seal` if a
  seal exists, and the test suite. Do not add it to `verify` yet.
- Update `specs/icp_directed_percolation_persistence/v0.1-draft/README.md` only
  to list the implemented commands, under a new "Implementation" heading.

### 13. Literature verification (if you have web access)
For every entry in `reference_classes.json` → `pre_freeze_verification.values_pending`:
1. Check the value against the cited primary source.
2. Write the checked citation into a new file
   `specs/icp_directed_percolation_persistence/v0.1-draft/VERIFICATION_LOG.md`.
3. Do not edit `reference_classes.json`; list the proposed edits in the log for
   the owner to apply.

If you cannot reach a source, say so in the log. Never substitute a value.

### 14. Compute estimate
Without running registered workloads, time the engine on synthetic 64³ media at
`rho` in `{0.30, 0.32, 0.40}` for at most 5 runs each, using a disposable seed
domain such as `'TIMING-ONLY'` that cannot collide with registered seeds.
Report the projected wall-clock time for the full Stage C and Stage S plans
under 4 workers. Delete the timing outputs. This is a resource estimate, not an
outcome.

## Final report

When done, report:
- every file created or changed;
- the test count and the pass/fail summary;
- the compute projection;
- the contents of `SPEC_QUESTIONS.md` and `VERIFICATION_LOG.md`;
- explicit confirmation that no registered path was written, no registered
  medium was drawn, nothing was committed, and `src/iota_rig.py` is unchanged.
