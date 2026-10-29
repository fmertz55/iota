# Spec questions found during implementation

Status: **frozen (revision 0.1.1).** Q-EST-7 was resolved before the v0.1 freeze
by changing the bracketing rule in `estimators.json`. Q-EST-8 was resolved by
revision 0.1.1, which supersedes the unopened v0.1 freeze. Every other entry is
frozen as the reading implemented in `src/dp_persistence/` and described below. Entries marked
**consequential** could change a registered outcome.

## Contradictions

### Q-EST-6. Bisection midpoint for IOTA (consequential)
- **Files:** `estimators.json` → `bracketing.bisection` says "geometric midpoint for IOTA". `iota_spreading.json` → `control_grid.bisection` says "arithmetic midpoints, 6 steps".
- **Reading:** arithmetic, from the IOTA-specific file (`runner.iota_plan`). Both kinds are implemented in `estimators.midpoint`.
- **Alternative:** geometric. The estimators file justifies it with "control spans decades", which ρ in [0.25, 0.70] does not.

### Q-EQ-1. Condition for the BFS-equivalence test
- **Files:** `protocol.json` → `required_before_freeze` says "every *activated* site has at most v + 1 fresh neighbours". The implementation prompt says "every *fresh* site".
- **Reading:** the test prunes the medium so that every fresh site has at most 3 fresh neighbours. This is the stronger condition, and it implies the other. The seed has `a0 = 7 ≥ 6`, so it is never a constraint.

## Bracketing and the criticality test

### Q-EST-7. A critical-compatible coarse point between the bracket ends (resolved)
- **File:** `estimators.json` → `bracketing.coarse`.
- **Original issue:** the draft required an *adjacent* (subcritical, supercritical) pair. A critical-compatible coarse point right at the threshold would have left no bracket, failing a calibration gate and ending the version.
- **Resolution before the freeze:** a bracket is a subcritical point followed by a supercritical point with only critical-compatible points between them. Those points are retained as final-point candidates. Any other classification between them still breaks the pair. Implemented in `estimators.adjacent_brackets` and the replay, and tested.

### Q-EST-8. Direction of bisection after a critical midpoint (resolved in revision 0.1.1)
- **File:** `estimators.json` → `bracketing.bisection`.
- **Original issue:** the v0.1 text said "continues toward the side whose endpoint has the larger |s|". The endpoint with the smaller |s| is nearer the threshold, so whenever a midpoint was critical-compatible, that rule moved the bracket away from the threshold. H1's tolerance is ±0.005, so this could matter.
- **Resolution (0.1.1):** bisection continues toward the endpoint with the smaller |s|. The critical midpoint replaces the endpoint with the larger |s|, and on a tie it replaces the upper endpoint. This is implemented in `estimators.bracket_search` and the replay. A test checks that the final bracket contains the threshold for several thresholds.

### Q-EST-8b. A bisection midpoint that neither brackets nor is critical
- **File:** `estimators.json` → `bracketing`. The spec does not say what happens when a midpoint is `window_too_short` or `resource_censored`.
- **Reading:** bisection stops, and the model's terminal status becomes that criticality.
- **Alternative:** skip the point, or bisect away from it.

### Q-EST-12. Multiple brackets
- **File:** `estimators.json` → `bracketing.multiple_brackets`. The spec says the lowest bracket is primary.
- **Reading:** bisection and classification continue on the primary bracket, and `terminal_status` is `multiple_brackets` instead of `classified`. Under Q-CAL-7, this fails a calibration gate.
- **Alternative:** stop after the coarse grid.

### Q-EST-5. Details of the weighted slope
- **File:** `estimators.json` → `criticality_test`.
- **Readings:**
  - **Weights:** `1/var` of `delta_eff` at each admissible ladder point, over the bootstrap resamples (ddof = 1).
  - **Equal-weights fallback:** if any variance is zero or undefined, all points get equal weights.
  - **Undefined points:** a point whose full-sample `delta_eff` is undefined (for example `P = 0`) is excluded from the fit. A resample is dropped if it is undefined at any retained point.
  - **Confidence interval:** percentile CI, with numpy linear interpolation.
  - **Too few points:** fewer than 2 fittable points is `window_too_short`.
  - **Check order:** `window_too_short` (from `t_max`) is checked before the `no_absorption_observed` precheck.
  - **Odd interval:** if `s > 0` and the CI lies entirely below 0, the point is classified `subcritical`. That is the literal reading of "s > 0 and its 95% bootstrap interval excludes 0".

### Q-EST-1 and Q-EST-2. Non-integer `t/m` and rounding
- **File:** `estimators.json` → `local_slopes`. `t_k / 4` is usually not an integer.
- **Readings:**
  - `P(t/m)` is read at tick `round_half_up(t_k / m)`, and the exponent divides by `ln m`.
  - `round` in the ladder means round half up.
- **Alternatives:**
  - Use the ladder point `t_{k-8}`, which can differ by one tick, for example 22 versus 23 at `t_k = 90`.
  - Divide by `ln(t / t')` instead of `ln m`.
  - Interpolate.

### Q-EST-9. "Bootstrap spread of the bracket decision" in SE(ρ_c)
- **File:** `iota_spreading.json` → `H1_threshold.rho_c_estimate`.
- **Reading:** for each bootstrap resample `b`, take the linear zero crossing of `s_b` between the two final bracket endpoints, clipped to the bracket. The spread is the standard deviation of those crossings. `SE = sqrt(spread² + (half width)²)`. `statistical_se` carries the spread and `systematic_se` carries the half width.
- **Alternative:** the fraction of resamples in which either endpoint's classification flips, converted to ρ units.

### Q-EST-10. Exponent estimate
- **File:** `estimators.json` → `exponent_estimate`.
- **Readings:**
  - **z:** the mean of `2 / two_over_z_eff`, not `2 / mean(two_over_z_eff)`.
  - **Upper half:** of K admissible points, the last `ceil(K/2)`.
  - **SEs:** the statistical SE is the bootstrap SD (ddof = 1). The systematic SE uses the final bracket endpoints.
  - **`crossover_in_window`:** true if any of the three local-slope series at the final point is strictly monotone over at least 3 admissible points. With noisy data this flag will often be true.
- **Alternative:** a trend test.

### Q-EST-3 and Q-EST-4. Aggregates with censoring and the L0 absorbing tick
- **File:** `estimators.json` → `aggregates` and `censoring.rule`.
- **Readings:**
  - Denominators of `P` and `N` count only runs not censored by `t`.
  - `N(t)` uses the recorded `n_t`, which is zero after a run stops. For L0, a run with `absorbed_at = T` still has `n_T > 0`, because tick T moved the last quantum (see Q-L0-1).
- **Alternative:** multiply `n_t` by `alive(t)`.

### Q-EST-11. Static tail
- **File:** `estimators.json` → `static_cluster_size`.
- **Readings:**
  - A run neither absorbed nor censored at the horizon is right-censored at its recorded S.
  - With no right-censored run, `s_cut` = max S.
  - The ladder is `round_half_up(16 · 2^(j/4)) ≤ s_cut`.
  - The fit is an unweighted least-squares fit.
  - A bootstrap resample with `F = 0` at some ladder point is dropped.
  - `range_too_short` reports no estimate.

### Q-EST-13 and Q-EST-14. Fresh seeds at the final point
- **Files:** `estimators.json` → `bracketing.final_point` ("re-run with runs_at_final_point fresh seeds") and `calibration.json` → `rng.seed_derivation`. The calibration seed depends on (model, control, run index), so re-running at an already-evaluated control with indices 0..N reuses the same runs.
- **Readings:**
  - **Calibration:** run indices continue after those already used at the same control value.
  - **IOTA:** the final point uses grid index 16.
  - **Bootstrap:** the bootstrap stream domain includes the point's role, so a final re-run gets an independent stream.

## Engine and records

### Q-L0-1. Tick indexing and `absorbed_at` (consequential for comparing models)
- **Files:** `estimators.json` → `observables_per_run.absorbed_at` and `minimal_law.json` → `absorbing_certificate`.
- **L0 reading:** `absorbed_at` is the first `t` whose state `S_t` satisfies the certificate, so it is 0 if the initial state does. `n_t[i]` is tick `i + 1`.
- **Calibration reading:** the calibration absorbing tests ("no active site") hold at the first layer with zero activity.
- **Consequence:** L0's `absorbed_at` is the tick of the last transfer, while a calibration model's is one layer after its last activity. The two conventions are offset by one tick.
- **Alternative:** L0 `absorbed_at` = T + 1.

### Q-CENS-1 and Q-CENS-2. Censoring
- **File:** `estimators.json` → `observables_per_run.censored_at`.
- **Readings:**
  - Censoring is tested on newly activated sites. This is equivalent, because the active set is a subset of the ever-active set.
  - **A run stops at its censoring tick.** `absorbed_at` is recorded only if the certificate also holds at that tick. A censored run counts as "alive" in the `t_max` rule.
- **Alternative:** continue to the horizon. This needs more compute and adds wrap risk.

### Q-CENS-3. Small test lattices
- The censoring radius `L/2 − 4` is below 1 for L ≤ 9, so the tests run with `censor=False`.
- The Stage A command uses 9³ states (`structural_audit.json` → `outcome_boundary`). The tests use up to 16³.

### Q-S-3. Per-run record fields for non-absorbed runs
- **File:** `iota_spreading.json` → `per_run_record`.
- **Reading:** `C`, `E`, and the stranded amplitude are null unless the run is absorbed. `E` is also null when `C = 0`.

### Q-L1-1. L1 draw rule
- **File:** `minimal_law.json` → `laws.L1.draw_rule`.
- **Reading:** an inclusion draw is made for every depleted neighbour of every active source, even a source with no fresh neighbour. The target draw follows only if the eligible set is non-empty. `E_x` keeps the fixed neighbour order across fresh and included depleted sites.

### Q-A-1. Stage A synthetic states
- **File:** `structural_audit.json` → `A2.required_check`.
- **Reading:** the 1000 states are arbitrary synthetic states on 9³: random fresh densities, random active sites with `a` in 1..8, and half of them forced to satisfy the certificate. They are drawn from a domain-separated synthetic stream. They need not be reachable.

## Calibration models

### Q-RNG-1. "Control value as decimal string"
- **File:** `calibration.json` → `rng.seed_derivation`.
- **Reading:** Python `repr(float(value))`, the shortest round-trip form. For example 0.60 becomes "0.6", and a bisection midpoint becomes e.g. "0.645".
- **Alternatives:** the JSON source text ("0.60"), or a fixed number of decimals.

### Q-RNG-2. Number of calibration streams
- **File:** `calibration.json` → `rng`.
- **Reading:** one PCG64 stream per run. For `CAL-SITE-BFS-SC-3`, the medium is the first `L³` variates of that stream (Q-CAL-4).
- **Alternative:** separate medium and dynamics streams, as for IOTA.

### Q-RNG-3. Bootstrap domain
- **File:** `estimators.json` → `criticality_test.bootstrap.rng` ("domain-separated").
- **Reading:** the domain is `SEARCH_ID NUL 'bootstrap' NUL model_id NUL control NUL '<role>:<purpose>'`.

### Q-CAL-1. Domany–Kinzel geometry and draws
- **Readings:**
  - Site `i` at layer `t+1` reads sites `i−1` and `i+1`.
  - The seed is site 0.
  - One uniform is drawn per candidate site (at least one active input), in increasing index order. The site activates iff `u < p1` (one input) or `u < p2` (two inputs).

### Q-CAL-2. Bond DP 3+1 draws
- **Reading:** 7 draws per active source in lexicographic order, with bonds in the order `+x, −x, +y, −y, +z, −z, self`.

### Q-CAL-3. One-tick SIR draws
- **Reading:** one draw per (infected source, susceptible neighbour) pair. Sources are taken in lexicographic order and neighbours in the fixed order. Susceptibility is read at the start of the generation.

### Q-CAL-4. Site-BFS medium
- **Reading:** drawn exactly like the L0 medium: `L³` variates in one call, with the seed's variate discarded.

### Q-CAL-5. S for calibration models
- **Reading:** the number of distinct sites ever active, including the seed. Only `CAL-SITE-BFS-SC-3` feeds the static estimator.

### Q-CAL-6. Wall-clock ceiling for calibration
- **Reading:** `calibration.json` gives no ceiling, so the IOTA value of 12 h per point is used.

### Q-CAL-7. Calibration gate
- **Readings:**
  - A model passes only if its `terminal_status` is `classified`, its verdict equals `expected_class`, its threshold gate passes, and its static gate passes (BFS only).
  - The threshold estimate is the final bracket midpoint.
  - The calibration `prediction_outcome` is `supported` iff the verdict equals the expected class, and `indeterminate` when the verdict is indeterminate.

## Results, paths, and stages

### Q-PATH-1. Calibration open manifest path
- **File:** `protocol.json` → `registered_paths`. It has development and confirmation open manifests but none for calibration.
- **Reading:** the calibration manifest is at `experiments/dp_persistence/ICP-DP-PERSISTENCE-001/calibration_open_manifest.json`. It is protected like the registered paths. Stage A has no open manifest: its answers are committed directly.

### Q-GIT-1. Multi-stage lineage
- **File:** `protocol.json` → `opening_rule`.
- **Implemented:**
  - The annotated tag selects the commit that adds the seal.
  - That commit is an ancestor of HEAD.
  - The worktree is clean.
  - `run-<stage>` requires HEAD to add only that stage's open manifest.
- **Not implemented:**
  - A check that a committed result is the direct child of its opening. No `verify-results` command was requested.
  - Exact ordering between stages C and A.

### Q-S-1. `predicted_classes`
- **File:** `result.schema.json` → `predicted_classes`.
- **Reading:** `{"IOTA-MIN-L0": "DyP_3", "IOTA-MIN-L1": "no_absorbing_transition"}`, copied from the committed Stage A answers.

### Q-S-2. `prediction_outcome` for development
- **Reading:** the H2 outcome. `percolation_statics_non_epidemic_dynamics` is not in the schema's `prediction_outcome` enum, so it maps to `indeterminate`. An H1 of `instrument_failure` sets `terminal_status` to `instrument_failure`.

### Q-K-1. Confirmation H1 to H3
- **File:** `partitions.json` → `iota_confirmation.registered_endpoint`.
- **Readings:**
  - Confirmation ρ_c is the midpoint of the frozen [lower, upper] pair, with a bootstrap spread computed from the confirmation data.
  - H2 and H3 are evaluated at the confirmation final point.
  - `prediction_outcome` is `supported` iff the lower endpoint is subcritical, the upper is supercritical (or `no_absorption_observed`), H1 equals the development H1, and, if H1 is equal, H2 and H3 equal their development values.

### Q-K-2. Where the three frozen ρ values come from
- **Issue:** the final bracket is not a field in `result.schema.json`.
- **Reading:** `open-confirmation` reconstructs it by replaying the registered bracketing rule over the recorded coarse and bisection points. It refuses if the replay does not reproduce `final_control_value`.
- **Alternative:** add a `final_bracket` field to the schema.

### Q-REP-1. The 1e-12 replay tolerance
- **Reading:** applied as `|a − b| / max(1, |a|)`, because `N(t)` and `R²(t)` reach about 1e4–1e6 on the synthetic ledgers. Observed agreement is about 1e-15 relative.

### Q-LIT-1. Literature values
See `VERIFICATION_LOG.md`. That log proposes changes to registered values: DK site p_c, the z = 26 p_c, DP_3p1 β's SE and ν⊥, and the τ spread. `reference_classes.json` was not edited.
