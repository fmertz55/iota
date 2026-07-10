# Findings

## Field Terminology Alignment

The working rig vocabulary is retained for reproducibility, but paper-facing interpretation should use standard terms from percolation theory, network science, cellular automata, and nonlinear dynamics where possible.

| Rig Term | Field-Aligned Term | Use |
|---|---|---|
| active iotas | active sites / occupied sites | Count of non-dark lattice cells. |
| largest coherence | largest connected component / giant component | Size of the largest active connected component. |
| coherence ratio / LCF | largest-component fraction / order parameter | `largest_connected_component / active_sites`, always relative to a stated connectivity graph. |
| coherence count | connected-component count / cluster count | Number of active connected components under a stated connectivity graph. |
| valence | coordination capacity / maximum productive degree | Maximum simultaneous productive relationships an active site can express. |
| bond_probability | ranked secondary-edge occupation probability / modified stochastic bond occupation | Probability that a non-primary productive relationship is admitted after candidate scoring; not ordinary independent bond percolation. |
| neighbor_mode | interaction neighborhood / lattice connectivity | Candidate geometry: `face6` is a 3D von Neumann neighborhood, `face18` is face+edge connectivity, and `cube26` is a 3D Moore neighborhood. |
| A_4774 nucleus | heterogeneous nucleation seed / amplitude-gradient seed | Fixed local initial condition with amplitude contrast and placement. |
| protected regime | fragmented / subcritical / non-percolating regime | Low-LCF regime where no absorbing giant component forms. |
| absorber regime | absorbing-state-like giant-component takeover | High-LCF regime where one component captures most active sites. |
| payload coupling | state-dependent interaction strength / compatibility coupling | Payload-dependent attenuation or compatibility gate. |
| vector inheritance event | directional-state inheritance / state-transition gate | Event where one site inherits the directional state of another. |
| first semantic divergence | critical event / basin-selection event | First state-changing event that sends matched runs to different attractors. |
| openness `O(t)` | outcome-distribution entropy / committor entropy | Normalized entropy of independently resampled future outcome classes from state `s_t`. |
| commitment time `t_c` | first passage to low committor entropy | First checkpoint where sampled future outcomes collapse below a declared openness threshold. |
| durable form without closed future | persistent structure with non-degenerate future | Candidate complexity definition: component-lineage persistence times openness. |
| constraint-accumulation rate | committor-entropy decay rate | `-dO/dt`, estimated between scheduled checkpoints. |
| scale test | finite-size scaling / scaling robustness probe | Check whether morphology survives larger lattice volumes. |
| seed | stochastic realization / disorder realization | Fixed random initialization and event schedule realization. |

Terminology discipline:

- Use `giant connected component`, `largest-component fraction`, and `cluster count` in paper-facing plots and captions.
- Report connectivity explicitly for component metrics: `LCF_face6`, `LCF_face18`, and `LCF_cube26` are distinct measurements, not interchangeable aliases.
- Describe `bond_probability` as a ranked, directed, state-dependent edge-occupation rule when contrasting with standard bond percolation.
- Use `discontinuous`, `threshold-like`, or `first-order-like` only with the qualifier `like` until seed ensembles and finite-size scaling support a stronger claim.
- Use `nucleation-like` for single-seed or single-event mechanisms until robustness across stochastic realizations is established.
- Use `absorbing component` or `single-cluster takeover` instead of `complexity` when the result is one dominant high-LCF component.
- Use `state-dependent compatibility coupling` instead of bare `payload protection` when describing the mechanism in Findings 016-018.
- Treat `metastable` cautiously: in the current irreversible activation model, `finite-time coexistence` and `time-to-merger` are often more precise.
- When using `durable form without closed future`, explicitly connect it to open-ended evolution, absorbing states, edge-of-chaos language, and assembly-theory-adjacent durable-form vocabulary. The phrase is a sharpening of those themes, not a replacement for related work.

## Reference Marker: Pre-Vectorization Baseline

Current reference implementation marker:

- Date: `2026-06-20`
- Branch: `main`
- Reference remote: `origin/main`
- Reference commit: `7e2f45b`
- Reference meaning: pre-vectorization baseline for Findings 001-018 and the active seed-ensemble boundary test.

Before any vectorized engine replaces the current implementation, it must satisfy trajectory-level equivalence against this reference. Finding 018 is especially sensitive: one exact directional-state inheritance event at tick `337`, sequence `15`, changes the system from the protected regime to the absorbing-component regime. Any change to update ordering, random-number consumption, candidate ordering, or component labeling can silently alter that result.

Minimum equivalence requirements:

- Reproduce the protected/absorber split for `cross_payload_coupling=0.209375` versus `0.2109375`.
- Reproduce the first semantic divergence at tick `337`, sequence `15`.
- Reproduce the vector inheritance draw `0.01315728279463102` and pass/fail thresholds.
- Reproduce final active-site count, largest connected component, LCF, and cluster count for the paired runs.
- Preserve within-tick event ordering or explicitly prove order-independent accumulation gives the same trajectory on golden cases.

## Engineering Roadmap

All roadmap items reference the baseline marker above.

1. Repair component measurement before new second-order claims. Historical LCF values are valid as face-connectivity measurements, but the current `coherence_stats` graph does not match the `cube26` interaction graph used by Findings 017-020. Add explicit `face6`, `face18`, and `cube26` component metrics before interpreting edge-coherent cases.
2. Recompute key regime classifications under all component graphs. Re-score the seed-42 and seed-56 natural/counterfactual rows, the high-dominant controls `45`, `50`, `61`, representative protected/dust seeds, and the largest Finding 020 protected exceptions.
3. Separate discovery and comparison protocols. Early stopping is acceptable for cheap classification, but fixed-horizon runs with early stopping disabled are required for time-series comparisons and paper-grade morphology tables.
4. Run openness timelines before changing the law. Use `src/openness_timeline.py` to estimate `O(t)` and commitment time under v0.1 before using the same instrument on v0.2. Add component persistence only as a second-pass diagnostic.
5. Vectorize only behind golden trajectory tests. The current engine uses a pure-Python per-active-site update loop and full component analysis at each metric snapshot. Vectorization should target update candidate generation, contribution accumulation, and component labeling, but it must first pass the Finding 018 equivalence suite.
6. Add deactivation or decay only as a new controlled law. Current active sites are effectively irreversible. A death/subthreshold rule would change the model class and should be introduced as a versioned experiment, not as a silent fix.
7. Make within-tick updates order-independent. Multiple sources currently update targets through sequential blending. A scatter/accumulate phase followed by one target update per tick would make the dynamics easier to reason about and vectorize.
8. Guard against silent no-op sweeps. Swept dotted keys should be validated against known-consumed config paths so a tidy parameter table cannot be produced for a parameter the engine never reads.
9. Keep local refs synchronized before major experiments. This checkout currently resolves `HEAD...origin/main` as `0 0`; if that changes, sync before interpreting new runs.

## Paper-Critical Validation Gate

Findings 017-020 should not be treated as a general law without the validation gates below.

The important correction is that bisection guarantees a first divergence, but it does not guarantee that the first divergence is outcome-pivotal. Finding 018 is nontrivial because the bidirectional counterfactual intervention swapped both final outcomes exactly. Finding 019 replicated that replay-pivotal event class in seed `56`. Finding 020 then showed that the same vector state is not a robust deterministic committor under independent future random streams.

### 0. Measurement Connectivity Repair

Before running second-order coherence diagnostics, repair the component measurement layer.

The current key experiments use `vectors.mode = cube26` and `constants.neighbor_mode = cube26`, while the historical largest-component fraction is measured with face-only connectivity. That means a structure can be dynamically connected through the interaction graph but counted as fragmented by the measurement graph.

Protocol:

- retain historical LCF values as `LCF_face6`;
- add `LCF_face18`, `LCF_cube26`, `component_count_face18`, and `component_count_cube26`;
- update diagnostics to accept an explicit component-connectivity mode;
- rerun the key rows from Findings 017-020 under all three graphs;
- only then classify protected, high-dominant, absorber, and edge-coherent cases.

Interpretation:

- If `LCF_face6` is low but `LCF_cube26` is high, the run is not simply fragmented. It is interaction-neighborhood coherent but face-fragmented.
- If all LCF variants remain low, the protected/dust label is stronger.
- If all LCF variants remain high, the absorber/high-dominant label is robust.
- If labels change by graph, the result should be reported as connectivity-relative rather than silently collapsed into one regime.

### 1. Boundary Seed Ensemble

Run the protected/absorber boundary across a seed ensemble, using the same medium-separated `P=4` versus `P=0` two-nucleus setup.

Question:

- Does the transition point cluster tightly across stochastic realizations?
- Or does each seed have its own knife-edge, producing a smooth ensemble-level sigmoid?
- Is the outcome distribution genuinely bimodal, or does the LCF gap fill in across seeds?

Interpretation:

- Tight clustering plus bimodality supports a sharp, characterizable transition.
- Wide scatter weakens Finding 017 as a general claim and reframes Finding 018 as a single-realization basin-selection mechanism.

Current run:

- Script: `src/payload_coupling_seed_ensemble_4096_sweep.py`
- Couplings: `0.209375`, `0.2109375`
- Seeds: `42-71`
- Status: completed in Finding 019.

### 2. Finite-Size Scaling

Run the same boundary comparison across lattice sizes after the seed ensemble is summarized.

Question:

- Does the protected-to-absorber jump sharpen as `L` grows?
- Or does it round off with scale?

Interpretation:

- Sharpening with size supports a first-order-like discontinuous transition in this substrate.
- Rounding with size suggests a finite-size artifact or seed-specific basin split.

The existing `64^3 -> 128^3 -> 256^3` scale probes are boundary-artifact tests because they keep the local initial coordinates unchanged while increasing available dark volume. They are not yet a conventional finite-size scaling study. A proper finite-size protocol needs consistent geometry, observation time, density, and order-parameter definitions as `L` changes.

### 3. Mechanism Replication

The make-or-break test for Finding 018 is not only whether `p*` clusters across seeds. It is whether the same event class repeatedly selects the basin.

For each seed near its boundary:

- repeat the paired divergence trace;
- identify the first consequential divergence;
- classify whether the divergence is directional-state inheritance, payload takeover, rounded A/R transfer, target selection, or another event class;
- intervene on the divergent state variable;
- test whether the one-state intervention reproduces the opposite fate;
- test whether the swap works in both parameter directions.

Interpretation:

- If vector inheritance repeatedly acts as the basin selector, Finding 018 generalizes as a mechanism even if each seed has a different `p*`.
- If `p*` clusters tightly but different event classes cause the fate split, then the transition may be robust while the Finding 018 mechanism is seed-specific.

### 4. Committor Analysis

A stronger causal test is a committor-style experiment. Save the state immediately before each traced vector-inheritance event, then launch many independent future random continuations after setting the target state to each alternative:

- seed `42`: `do(V=0)` versus `do(V=31)`
- seed `56`: `do(V=0)` versus `do(V=27)`

Estimate:

- `Pr(absorber | protected-side vector)`
- `Pr(absorber | absorber-side vector)`

If those probabilities are near `0` and `1`, respectively, the vector state is a robust basin selector rather than an accident of one downstream RNG stream. This is the cleanest way to test whether the identified variable lies on the transition boundary.

Current result:

- Finding 020 did not produce near-`0` versus near-`1` committor probabilities.
- The vector state is replay-pivotal under the recorded future random stream, but not sufficient by itself under independent continuation streams.

### Interpretive Boundary

The PSA/identity interpretation should be framed carefully:

`a single microscopic directional-state inheritance event can tip identity-preserving fragmentation into dissolution`

That is a legitimate interpretive angle if labeled as interpretation. The empirical claim remains the measured transition, ensemble robustness, finite-size behavior, and counterfactual causal test.

Current scope:

- Established: for seeds `42` and `56`, under the recorded future random stream, the traced directional-state inheritance event is necessary and sufficient for absorber versus protected fate.
- Not established: that the vector state is a robust committor-pivotal state under independent future random streams, or that the compatibility-coupling response is a thermodynamic first-order transition.
- Provisional: morphology labels based on LCF remain connectivity-relative until Finding 021's measurement pass is completed.

Paper framing should therefore treat Findings 018-020 as trajectory-level causal discoveries plus a committor correction. The bidirectional interventions are substantive replay results; the broader transition claim depends on connectivity-aware morphology measurement, mechanism replication, committor analysis, and finite-size behavior.

## Finding 001: Valence-2 Coherent Percolation

Under soft conservation, one active iota with `range_range=[7,7]`, `amplitude_coupling=1.0`, and `range_coupling=1.0` transitions from trace-limited propagation to single-component coherent growth when `constants.valence` increases from `1` to `2`.

This finding does not claim stable chemistry-like structure. It establishes a phase change from capped traces to connected percolation.

### Conditions

- `init.active_iotas`: 1
- `init.range_range`: `[7,7]`
- `constants.amplitude_coupling`: 1.0
- `constants.range_coupling`: 1.0
- `constants.conservation`: `soft`
- `run.stop_active_iotas`: 30000

### Evidence

| Experiment | Valence | Requested Ticks | Final Tick | Final Active | Largest Coherence | Coherence Count |
|---:|---:|---:|---:|---:|---:|---:|
| 67 | 1 | 8 | 8 | 5 | 3 | 3 |
| 68 | 1 | 16 | 16 | 8 | 3 | 6 |
| 69 | 1 | 32 | 32 | 10 | 3 | 8 |
| 70 | 1 | 64 | 64 | 10 | 3 | 8 |
| 71 | 1 | 128 | 128 | 12 | 3 | 10 |
| 72 | 1 | 256 | 256 | 13 | 3 | 11 |
| 60 | 2 | 8 | 8 | 36 | 36 | 1 |
| 61 | 2 | 16 | 16 | 160 | 160 | 1 |
| 62 | 2 | 32 | 32 | 621 | 621 | 1 |
| 63 | 2 | 64 | 64 | 3695 | 3695 | 1 |
| 64 | 2 | 128 | 128 | 19766 | 19766 | 1 |
| 65 | 2 | 256 | 160 | 30232 | 30232 | 1 |

### Artifacts

- `output/findings/finding_001_valence_percolation.png`
- `output/findings/finding_001_valence_percolation.csv`

### Interpretation

`valence=1` remains trace-limited: active count grows slightly and largest coherence stays capped at 3.

`valence=2` enters coherent percolation: every recorded active iota belongs to one connected component, and active count rises rapidly until the early-stop threshold is reached.

### Next Question

Determine whether valence-2 percolation is merely connected expansion or whether it contains stable morphology. Candidate metrics:

- surface-area-to-volume proxy
- bounding box dimensions
- cycle or loop count
- payload/vector diversity inside the giant component
- growth-rate fit across early ticks

## Finding 002: Nonzero Secondary Bond Probability

Under the corrected slot-level bond rule, one deterministic primary relationship plus any tested nonzero probability of a secondary relationship produces a giant coherent component by tick 256.

This finding tests effective relational capacity, not candidate fanout. `constants.bond_probability` gates the non-primary valence slot after candidate scoring; if admitted, the next highest-scored candidate receives the existing exchange rule. Conservation, decay, payload, and rounding are unchanged.

### Conditions

- `simulation_version`: `iota-rig-v0.1.1` for `p > 0`
- `init.active_iotas`: 1
- `init.range_range`: `[7,7]`
- `constants.valence`: 2
- `constants.amplitude_coupling`: 1.0
- `constants.range_coupling`: 1.0
- `constants.conservation`: `soft`
- `run.ticks`: 256
- `run.stop_active_iotas`: 30000

### Evidence

| Experiment | Bond Probability | Final Tick | Final Active | Largest Coherence | Coherence Count | Coherence Ratio |
|---:|---:|---:|---:|---:|---:|---:|
| 84 | 0.0 | 256 | 13 | 3 | 11 | 0.230769 |
| 88 | 0.1 | 256 | 2351 | 2323 | 19 | 0.988090 |
| 89 | 0.2 | 256 | 8631 | 8553 | 33 | 0.990963 |
| 90 | 0.3 | 256 | 11543 | 11438 | 44 | 0.990904 |
| 91 | 0.4 | 256 | 13570 | 13395 | 59 | 0.987104 |
| 92 | 0.5 | 256 | 15020 | 14720 | 62 | 0.980027 |
| 93 | 0.6 | 256 | 19031 | 18887 | 41 | 0.992433 |
| 94 | 0.7 | 256 | 20453 | 20365 | 53 | 0.995697 |
| 95 | 0.8 | 256 | 18503 | 18246 | 69 | 0.986110 |
| 96 | 0.9 | 256 | 26125 | 26086 | 33 | 0.998507 |
| 97 | 1.0 | 256 | 12452 | 12361 | 30 | 0.992692 |

### Artifacts

- `output/findings/finding_002_bond_probability.png`
- `output/findings/finding_002_bond_probability.csv`

### Interpretation

`bond_probability=0.0` reproduces trace-limited behavior because the secondary relationship never exists.

Every tested nonzero value enters coherent percolation, with the largest component containing at least 98% of active iotas by tick 256. The transition appears sharp at `p > 0` for this seed and configuration.

The growth magnitude is not monotonic across probability. That suggests `bond_probability` changes timing and geometry of growth, not only final capacity. Replicate seeds are needed before interpreting the curve shape.

### Method Note

Experiments 75-83 used an earlier candidate-level probability gate and are superseded for this question. Experiments 85-87 used the corrected slot-level gate but inherited stale `simulation_version` metadata. Finding 002 uses experiments 88-97 for `p > 0`.

## Finding 003: Tiny Secondary Bond Probability Boundary

With a longer horizon and secondary-exchange diagnostics, tiny nonzero secondary coupling does not automatically create large-scale coherent structure within 4096 ticks. The tested boundary lies between `bond_probability=0.001` and `bond_probability=0.005` for seed 42 under the current stopping criterion.

The stopping criterion for positive percolation was `coherence_ratio >= 0.97` after at least `1000` active iotas, with `run.stop_active_iotas=30000` still enabled.

### Conditions

- `simulation_version`: `iota-rig-v0.1.1`
- `init.active_iotas`: 1
- `init.range_range`: `[7,7]`
- `constants.valence`: 2
- `constants.amplitude_coupling`: 1.0
- `constants.range_coupling`: 1.0
- `constants.conservation`: `soft`
- `run.ticks`: 4096
- `run.stop_coherence_ratio`: 0.97
- `run.stop_coherence_min_active`: 1000
- `run.stop_active_iotas`: 30000

### Evidence

| Experiment | Bond Probability | Final Tick | Final Active | Largest Coherence | First Secondary Tick | Total Secondary Exchanges | Early Stopped |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 108 | 0.0 | 4096 | 13 | 3 | -1 | 0 | 0 |
| 107 | 0.000001 | 4096 | 13 | 3 | -1 | 0 | 0 |
| 106 | 0.00001 | 4096 | 13 | 3 | -1 | 0 | 0 |
| 105 | 0.0001 | 4096 | 28 | 8 | 1098 | 4 | 0 |
| 104 | 0.001 | 4096 | 155 | 142 | 210 | 166 | 0 |
| 103 | 0.005 | 1942 | 1001 | 995 | 67 | 1692 | 1 |
| 102 | 0.01 | 1210 | 1001 | 994 | 10 | 3410 | 1 |
| 101 | 0.025 | 899 | 1936 | 1879 | 10 | 9531 | 1 |
| 100 | 0.05 | 259 | 1013 | 1002 | 6 | 2699 | 1 |
| 99 | 0.1 | 175 | 1005 | 986 | 6 | 4509 | 1 |

### Artifacts

- `output/findings/finding_003_tiny_bond_probability.png`
- `output/findings/finding_003_tiny_bond_probability.csv`

### Interpretation

This falsifies the broad version of the hypothesis for the tested horizon: any nonzero coupling is not sufficient within 4096 ticks.

The sharper statement is: rare secondary bonds can seed coherent visible structure only after enough secondary exchanges accumulate. In this run, `p=0.0001` produced 4 secondary exchanges and no large structure, `p=0.001` produced 166 and still did not reach the criterion, while `p=0.005` produced 1692 and crossed the giant-component threshold.

The immediate next question is seed robustness near the boundary: repeat `p=0.001`, `0.0025`, and `0.005` across multiple seeds.

## Finding 004: Low-Coupling Morphology Is Not Binary

At `constants.bond_probability=0.003`, increasing `init.active_iotas` does not monotonically increase coherent percolation. Instead, it changes morphology: some runs form a dominant component, while others generate broad fragmented activity.

The key quantity is largest component fraction:

`LCF = largest_coherence / active_iotas`

This is already recorded as `coherence_ratio`.

### Conditions

- `simulation_version`: `iota-rig-v0.1.1`
- `constants.bond_probability`: 0.003
- `constants.valence`: 2
- `init.range_range`: `[7,7]`
- `constants.amplitude_coupling`: 1.0
- `constants.range_coupling`: 1.0
- `constants.conservation`: `soft`
- `run.ticks`: 4096
- `run.stop_coherence_ratio`: 0.97
- `run.stop_coherence_min_active`: 1000
- `run.stop_active_iotas`: 30000

### Evidence

| Initial Active | Seed | Final Active | Largest Coherence | LCF |
|---:|---:|---:|---:|---:|
| 1 | 42 | 1054 | 1004 | 0.953 |
| 2 | 42 | 67 | 56 | 0.836 |
| 2 | 43 | 6 | 3 | 0.500 |
| 2 | 44 | 8 | 3 | 0.375 |
| 2 | 45 | 188 | 138 | 0.734 |
| 2 | 46 | 11 | 6 | 0.545 |
| 4 | 42 | 3048 | 2650 | 0.869 |
| 4 | 43 | 1960 | 656 | 0.335 |
| 4 | 44 | 1956 | 1818 | 0.929 |
| 4 | 45 | 2061 | 1268 | 0.615 |
| 4 | 46 | 794 | 570 | 0.718 |
| 8 | 42 | 2899 | 1220 | 0.421 |
| 8 | 43 | 1439 | 967 | 0.672 |
| 8 | 44 | 3622 | 1751 | 0.483 |
| 8 | 45 | 2611 | 1999 | 0.766 |
| 8 | 46 | 3102 | 1560 | 0.503 |
| 16 | 42 | 4519 | 2552 | 0.565 |
| 16 | 43 | 2992 | 1956 | 0.654 |
| 16 | 44 | 7585 | 3045 | 0.401 |
| 16 | 45 | 650 | 122 | 0.188 |
| 16 | 46 | 6060 | 2601 | 0.429 |

### Artifacts

- `output/findings/finding_004_lcf_geometry_summary.csv`
- `output/findings/finding_004_lcf_geometry_timeseries.csv`
- `output/findings/finding_004_lcf_geometry_timeseries.png`
- `output/findings/finding_004_lcf_geometry_scatter.png`
- `output/findings/finding_004_grouped_metrics_timeseries.csv`
- `output/findings/finding_004_lcf_vs_tick.png`
- `output/findings/finding_004_active_vs_tick.png`
- `output/findings/finding_004_secondary_exchanges_vs_tick.png`
- `output/findings/finding_004_cumulative_secondary_exchanges_vs_tick.png`
- `output/findings/finding_004_morphology_classification.csv`
- `output/findings/finding_004_morphology_by_initial_active.csv`
- `output/findings/finding_004_morphology_regimes.png`
- `output/findings/finding_004_morphology_by_initial_active.png`

### Interpretation

The result does not support a simple rule that more initial active iotas make coherent percolation more likely.

The strongest dominant-component cases occurred at `init.active_iotas=4`, especially seeds 42 and 44. Higher initial counts often produced more active iotas but lower LCF, consistent with competing growth domains rather than one coherent collapse.

This suggests the low-coupling regime is better described as morphology-sensitive critical growth:

`trace -> dominant component -> fragmented expansion`

The relevant phase quantity appears to be connectedness, not activity alone.

### Derived Morphology Metrics

Each run was classified from existing metrics only. No simulation parameters were changed.

Derived quantities:

- `peak_lcf`: maximum observed largest component fraction
- `time_to_peak_lcf`: tick where `peak_lcf` occurs
- `final_lcf`: final `coherence_ratio`
- `fragmentation_index`: `coherence_count / active_iotas`
- `regime`: morphology label derived from final active count and final LCF

Regime counts:

| Regime | Count |
|---|---:|
| trace | 4 |
| dominant_coherent | 3 |
| intermediate_dominant | 6 |
| intermediate_fragmented | 1 |
| fragmented_active | 7 |

Aggregate morphology by initial active count:

| Initial Active | Runs | Avg Final Active | Avg Final LCF | Max Final LCF | Fragmented Active Runs | Dominant Coherent Runs |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1054.0 | 0.953 | 0.953 | 0 | 1 |
| 2 | 5 | 56.0 | 0.598 | 0.836 | 0 | 0 |
| 4 | 5 | 1963.8 | 0.693 | 0.929 | 1 | 2 |
| 8 | 5 | 2734.6 | 0.569 | 0.766 | 3 | 0 |
| 16 | 5 | 4361.2 | 0.447 | 0.654 | 3 | 0 |

The morphology classifier makes the central result explicit: `init.active_iotas=4` produced the best coherence balance, while `init.active_iotas=8` and `16` produced more activity but more fragmented growth.

## Finding 005: Seed Geometry Controls Low-Coupling Morphology

### Status

Confirmed diagnostic from existing completed metrics. No new simulation parameters were introduced.

### Setup

Reference diagnostic:

- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `init.active_iotas = 4`
- Seeds compared: `44` and `45`
- Control comparison: same `p` and seeds with `init.active_iotas = 1`

### Result

| Initial Active | Seed | Experiment | Final Tick | Final Active | Largest Coherence | Final LCF | Components | Cumulative Secondary Exchanges |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 4 | 44 | IOTA-000168 | 3033 | 4122 | 4001 | 0.971 | 18 | 15845 |
| 4 | 45 | IOTA-000167 | 4096 | 4565 | 3410 | 0.747 | 61 | 16003 |
| 1 | 44 | IOTA-000136 | 4096 | 3 | 3 | 1.000 | 1 | 20 |
| 1 | 45 | IOTA-000135 | 4096 | 428 | 413 | 0.965 | 10 | 1849 |

The seed-44 advantage is not a scalar property of seed `44`. It appears only in the `init.active_iotas=4` geometry. With one initial active iota, seed `44` remains trace-limited while seed `45` grows a coherent small component.

### Initial Geometry Contrast

At `init.active_iotas=4`:

- Seed `44` starts with mixed payloads `2,1,0,5`, mixed behaviors `move,reflect,diffuse,reflect`, and two max-amplitude cells with `A=7`.
- Seed `45` starts with homogeneous payload `P=4` across all four cells, all `reflect` behavior, and lower state diversity.
- Seed `44` initial cells are farther apart, with nearest-neighbor distances around `26–35`.
- Seed `45` has three closer initial cells, with nearest-neighbor distances around `13–15`, plus one farther cell.

### Interpretation

The diagnostic supports a geometry-sensitive nucleation mechanism rather than a simple coupling threshold.

Secondary exchange count alone does not explain the result: seeds `44` and `45` have nearly equal cumulative secondary exchanges in the `init.active_iotas=4` comparison. The difference is how those exchanges attach to an already coherent reachable region.

Working interpretation:

`low coupling + favorable initial state diversity + favorable local attachment geometry -> coherent collapse`

while:

`low coupling + homogeneous or poorly attached local geometry -> fragmented expansion`

### Artifacts

- `output/findings/finding_005_seed_44_45_metrics_summary.csv`
- `output/findings/finding_005_seed_44_45_metrics_timeseries.csv`
- `output/findings/finding_005_seed_44_45_metrics_initial_conditions.csv`
- `output/findings/finding_005_seed_44_45_metrics_lcf.png`
- `output/findings/finding_005_seed_44_45_metrics_active.png`
- `output/findings/finding_005_seed_44_45_metrics_components.png`
- `output/findings/finding_005_seed_44_45_metrics_cumulative_secondary.png`
- `output/findings/finding_005_seed_44_45_metrics_payload_fraction.png`

## Finding 006: Amplitude Diversity Is Sufficient for Fixed-Geometry Nucleation

### Status

Controlled fixed-initial-state diagnostic. This experiment intentionally bypassed the one-parameter guard because the setup required switching from random initialization to explicit fixed iotas.

### Setup

All variants used:

- Same four seed-44 coordinates from the favorable `init.active_iotas=4` geometry
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `init.active_iotas = 4`
- `R = 7` for every initial iota
- `run.ticks = 4096`

Only initial `A`, `P`, and `V` composition varied.

Uniform baseline values:

- `A = [4,4,4,4]`
- `P = [4,4,4,4]`
- `V = [49,49,49,49]`

Diverse values:

- `A = [2,7,7,3]`
- `P = [2,1,0,5]`
- `V = [6,34,54,43]`

### Result

| Variant | Final Tick | Final Active | Largest Coherence | Final LCF | Components | Time to LCF 0.95 | Time to LCF 0.97 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A diversity only | 3279 | 6442 | 6327 | 0.982 | 51 | 3279 | 3279 |
| P diversity only | 4096 | 260 | 83 | 0.319 | 31 | — | — |
| V diversity only | 4096 | 518 | 243 | 0.469 | 36 | — | — |
| A + P diversity | 4096 | 2447 | 2023 | 0.827 | 67 | — | — |
| A + V diversity | 4096 | 2876 | 2722 | 0.946 | 30 | — | — |
| P + V diversity | 4096 | 601 | 285 | 0.474 | 30 | — | — |
| A + P + V diversity | 4096 | 5837 | 5537 | 0.949 | 66 | — | — |

### Interpretation

Amplitude diversity alone was sufficient to trigger coherent collapse in this fixed geometry.

Payload diversity alone and vector/behavior diversity alone did not nucleate large-scale coherence. Adding payload diversity to amplitude diversity reduced coherence relative to amplitude diversity alone. Adding vector/behavior diversity to amplitude diversity produced a strong near-threshold morphology, but still did not cross the guarded `0.97` stop.

This falsifies the working bet that payload diversity plus amplitude spread would be strongest. In this fixed geometry and coupling regime, initial amplitude heterogeneity is the primary driver.

Working interpretation:

`low coupling + favorable geometry + amplitude heterogeneity -> coherent nucleation`

Payload and vector diversity are not automatically beneficial. They can add fragmentation unless amplitude heterogeneity already produces a coherent growth front.

### Artifacts

- `output/findings/finding_006_composition_variants_summary.csv`
- `output/findings/finding_006_composition_variants_timeseries.csv`
- `output/findings/finding_006_composition_variants_final_lcf.png`
- `output/findings/finding_006_composition_variants_lcf_timeseries.png`
- `output/findings/finding_006_composition_variants_active_timeseries.png`

## Finding 007: Coherence Is Gradient-Selected, Not Amplitude-Maximized

### Status

Controlled fixed-geometry amplitude-spread diagnostic.

### Setup

All variants used:

- Same four fixed coordinates as Finding 006
- Uniform payload: `P = [4,4,4,4]`
- Uniform vector state: `V = [49,49,49,49]`
- `R = 7` for every initial iota
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `run.ticks = 4096`

Only initial amplitude pattern varied.

### Result

| Variant | Final Tick | Final Active | Largest Coherence | Active Outside Largest | Final LCF | Components | Time to LCF 0.97 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `A_4444` | 4096 | 432 | 121 | 311 | 0.280 | 38 | — |
| `A_5444` | 4096 | 953 | 460 | 493 | 0.483 | 52 | — |
| `A_6444` | 4096 | 1967 | 1611 | 356 | 0.819 | 48 | — |
| `A_7444` | 4096 | 6212 | 5850 | 362 | 0.942 | 64 | — |
| `A_7744` | 3693 | 10244 | 9938 | 306 | 0.970 | 78 | 3693 |
| `A_7774` | 4096 | 14726 | 10002 | 4724 | 0.679 | 95 | — |
| `A_7777` | 4096 | 24383 | 14028 | 10355 | 0.575 | 143 | — |

### Interpretation

The result is not amplitude monotonicity.

Increasing amplitude from `A_4444` through `A_7744` improves coherent growth, but additional high-amplitude seeds after `A_7744` increase total activity while reducing single-component dominance.

This supports a gradient-selection mechanism:

`too little A contrast -> weak growth`

`one high-A anchor -> coherent growth`

`two high-A anchors -> strongest coherent growth`

`three or four high-A anchors -> competing fronts / fragmentation`

The best current interpretation is:

`coherent nucleation requires amplitude asymmetry, but too much high-amplitude uniformity destroys the dominant gradient`

This refines Finding 006: amplitude heterogeneity matters, but the useful quantity is not simply spread or total amplitude. The useful condition appears to be a limited high-amplitude anchor set embedded in lower-amplitude context.

### Instrumentation Gap

The current persisted metrics include component count and largest component size, but not full component-size distribution or per-component state statistics.

The desired next diagnostics are:

- `top_5_component_sizes`
- `mean_A_by_component`
- `frontier_count`
- component-level payload/vector composition

Those require either replaying final worlds or adding runtime component diagnostics/state snapshots. For this finding, `coherence_count`, `active_outside_largest`, and `final_lcf` already show the fragmentation pattern clearly:

- `A_7744`: only `306` active iotas outside the largest component
- `A_7774`: `4724` outside the largest component
- `A_7777`: `10355` outside the largest component

### Artifacts

- `output/findings/finding_007_amplitude_spread_summary.csv`
- `output/findings/finding_007_amplitude_spread_timeseries.csv`
- `output/findings/finding_007_amplitude_spread_final_lcf.png`
- `output/findings/finding_007_amplitude_spread_active_vs_largest.png`
- `output/findings/finding_007_amplitude_spread_fragmentation.png`
- `output/findings/finding_007_amplitude_spread_lcf_timeseries.png`

## Finding 008: Amplitude Placement Controls Coherence Morphology

### Status

Controlled amplitude-position permutation sweep.

### Setup

All variants used:

- Same four fixed coordinates as Findings 006 and 007
- Uniform payload: `P = [4,4,4,4]`
- Uniform vector state: `V = [49,49,49,49]`
- `R = 7` for every initial iota
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `run.ticks = 4096`
- Seeds `42-46`

Only the positions of high-amplitude initial iotas varied.

### Result

| Variant | Mean LCF | Std LCF | Min LCF | Max LCF | Mean Active | Success LCF >= 0.95 |
|---|---:|---:|---:|---:|---:|---:|
| `A_4447` | 0.922 | 0.011 | 0.904 | 0.933 | 5819 | 0/5 |
| `A_4474` | 0.933 | 0.019 | 0.901 | 0.956 | 6349 | 1/5 |
| `A_4477` | 0.613 | 0.178 | 0.480 | 0.964 | 8943 | 1/5 |
| `A_4744` | 0.905 | 0.044 | 0.823 | 0.956 | 5429 | 1/5 |
| `A_4747` | 0.710 | 0.211 | 0.490 | 0.971 | 9103 | 2/5 |
| `A_4774` | 0.970 | 0.001 | 0.968 | 0.972 | 9873 | 5/5 |
| `A_7444` | 0.914 | 0.022 | 0.879 | 0.942 | 4490 | 0/5 |
| `A_7447` | 0.636 | 0.165 | 0.497 | 0.960 | 10274 | 1/5 |
| `A_7474` | 0.654 | 0.154 | 0.543 | 0.958 | 9819 | 1/5 |
| `A_7744` | 0.792 | 0.212 | 0.500 | 0.967 | 9131 | 3/5 |

### Interpretation

Amplitude contrast is not enough by itself. The specific placement of high-amplitude anchors strongly controls whether growth becomes one dominant coherent component or fragments into competing fronts.

The strongest result is `A_4774`: all five seeds converged to a stable high-LCF morphology near `0.97`, with extremely low variance. Other two-anchor placements often produced similar or higher activity but lower LCF, implying fragmented growth rather than coherent takeover.

This revises Finding 007:

`coherent nucleation is gradient-selected and geometry-sensitive`

The high-amplitude anchors need to occupy a favorable relation to the fixed local update geometry. More high-amplitude sources, or poorly placed high-amplitude pairs, can increase activity while reducing coherent dominance.

### Next Test

Run a geometry-thinning diagnostic using the robust winner:

- `A_4774`
- `N0 = 4`
- `R = 7`
- `constants.valence = 2`
- `constants.bond_probability = 0.005`
- `conservation = soft`
- Same fixed coordinates, payloads, vector states, and seeds

Add a new `constants.neighbor_mode` that only changes the secondary candidate-neighbor set. Do not change `vectors.mode`, because that would confound candidate geometry with primary vector behavior.

First pass:

- `cube26`
- `face18`
- `face6`

### Artifacts

- `output/findings/finding_008_amplitude_position_permutation_raw.csv`
- `output/findings/finding_008_amplitude_position_permutation_summary.csv`

## Finding 009: Face-Only Geometry Breaks A_4774 Coherent Nucleation

### Status

Controlled geometry-thinning diagnostic.

### Setup

All variants used the robust Finding 008 winner:

- `A = [4,7,7,4]`
- Same four fixed coordinates
- Uniform payload: `P = [4,4,4,4]`
- Uniform vector state: `V = [49,49,49,49]`
- `R = 7` for every initial iota
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `run.ticks = 4096`
- Seeds `42-46`

Only `constants.neighbor_mode` changed. `vectors.mode` remained `cube26`, so primary vector behavior was not changed.

### Result

| Neighbor Mode | Mean LCF | Std LCF | Min LCF | Max LCF | Mean Active | Mean Largest | Success LCF >= 0.95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cube26` | 0.970 | 0.001 | 0.968 | 0.972 | 9873 | 9578 | 5/5 |
| `face18` | 0.970 | 0.001 | 0.968 | 0.972 | 9873 | 9578 | 5/5 |
| `face6` | 0.549 | 0.092 | 0.482 | 0.730 | 5248 | 2871 | 0/5 |

### Interpretation

The result cleanly separates dense-neighbor availability from minimum connectivity.

`face18` exactly reproduced `cube26` across all five seeds, so corner-neighbor candidates are not required for the `A_4774` coherent morphology.

`face6` failed across all five seeds. Activity still grew, but it fragmented:

- lower total active count
- much smaller largest component
- no LCF >= 0.95 successes

This supports a minimum local-connectivity condition:

`face + edge candidate reachability is sufficient`

`face-only candidate reachability is insufficient`

The mechanism is therefore not simply amplitude placement or stochastic seed luck. It requires the favorable `A_4774` gradient plus enough local geometric connectivity to form a single dominant component.

### Artifacts

- `output/findings/finding_009_geometry_thinning_raw.csv`
- `output/findings/finding_009_geometry_thinning_summary.csv`

## Finding 010: A_4774 Coherent Morphology Survives 128³ Scale

### Status

Controlled scale diagnostic.

### Setup

All runs used:

- `grid.size = 128`
- `A = [4,7,7,4]`
- Same four fixed coordinates as Findings 006-009
- Uniform payload: `P = [4,4,4,4]`
- Uniform vector state: `V = [49,49,49,49]`
- `R = 7` for every initial iota
- `vectors.mode = cube26`
- `constants.neighbor_mode = cube26`
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `run.ticks = 4096`
- Seeds `42-46`

Coordinates were intentionally not scaled. This isolates increased dark volume and boundary distance from changes in initial geometry.

### Result

| Seed | Final Active | Largest Coherence | Final LCF |
|---:|---:|---:|---:|
| 42 | 11664 | 11335 | 0.972 |
| 43 | 9654 | 9349 | 0.968 |
| 44 | 10870 | 10551 | 0.971 |
| 45 | 22144 | 21610 | 0.976 |
| 46 | 12962 | 12499 | 0.964 |

Summary:

- Mean LCF: `0.970`
- Std LCF: `0.004`
- Success LCF >= 0.95: `5/5`
- Success LCF >= 0.97: `3/5`

### Interpretation

The `A_4774` coherent morphology survives an 8x volume increase from `64³` to `128³`.

This weakens the boundary-artifact objection. With the same local initial geometry but much more dark volume, the system still forms one dominant coherent component across all five seeds.

The active counts remain local-scale rather than volume-filling:

`mean active / total iotas = 13458.8 / 2097152 ≈ 0.64%`

This supports the current interpretation:

`coherent nucleation is local, geometry-sensitive, and scale-stable at 128³`

The next scale test should be exactly one guarded `256³` probe using the same setup and seed `42`.

### Artifacts

- `output/findings/finding_010_scale_128_raw.csv`
- `output/findings/finding_010_scale_128_summary.csv`

## Finding 011: A_4774 Coherent Morphology Survives 256³ Single-Seed Probe

### Status

Single guarded scale probe.

### Setup

The run used:

- `grid.size = 256`
- `A = [4,7,7,4]`
- Same four fixed coordinates as Findings 006-010
- Uniform payload: `P = [4,4,4,4]`
- Uniform vector state: `V = [49,49,49,49]`
- `R = 7` for every initial iota
- `vectors.mode = cube26`
- `constants.neighbor_mode = cube26`
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `run.ticks = 4096`
- Seed `42`

Dashboard generation was disabled and metrics were sampled every 256 ticks for scale safety.

### Result

| Grid Size | Seed | Final Tick | Final Active | Largest Coherence | Final LCF | Coherence Count |
|---:|---:|---:|---:|---:|---:|---:|
| 256 | 42 | 4096 | 12328 | 11992 | 0.973 | 90 |

The final active density was:

`12328 / 16777216 ≈ 0.073%`

### Scale Comparison

Direct seed-42 comparison across grid sizes:

| Grid Size | Experiment | Seed | Final Tick | Final Active | Largest Coherence | Final LCF | Tick LCF >= 0.95 | Tick LCF >= 0.97 | Runtime |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 64 | IOTA-000247 | 42 | 3648 | 8585 | 8328 | 0.970 | 3072 | 3648 | 410s |
| 128 | IOTA-000263 | 42 | 4096 | 11664 | 11335 | 0.972 | 3072 | 4096 | 633s |
| 256 | IOTA-000268 | 42 | 4096 | 12328 | 11992 | 0.973 | 3072 | 4096 | 1020s |

The key scale result is not that active count grows with volume. It mostly does not. The key result is that the dominant coherent morphology persists as available dark volume increases by 64x from `64³` to `256³`.

The tick of nucleation/collapse is also stable at the available metric resolution:

`LCF >= 0.95` first appears at tick `3072` for all three comparable seed-42 runs.

### Timeseries Read

The run remained fragmented through mid-run, then collapsed into a dominant coherent component:

| Tick | Active | Largest | LCF |
|---:|---:|---:|---:|
| 2048 | 2806 | 1316 | 0.469 |
| 2560 | 4326 | 2150 | 0.497 |
| 2816 | 5209 | 2686 | 0.516 |
| 3072 | 6258 | 6049 | 0.967 |
| 3584 | 8322 | 8053 | 0.968 |
| 4096 | 12328 | 11992 | 0.973 |

### Interpretation

The `A_4774` coherent morphology survived the 64x volume increase from `64³` to `256³` in the seed-42 probe.

This strongly weakens the scale-artifact objection. The system forms a high-LCF coherent component in a substrate that is overwhelmingly dark:

`99.927%` of the 256³ grid remains inactive at final tick.

The transition timing is also important. Coherence did not start dominant. It emerged abruptly between ticks `2816` and `3072`, consistent with a nucleation/collapse phase rather than simple monotonic aggregation.

The current scale read is:

`local amplitude-gradient geometry + sufficient candidate connectivity -> scale-stable coherent nucleation`

### Paper Planning Bridge

This finding changes the project status from exploratory rig-building to paper-candidate evidence.

The minimum defensible paper claim is not that the model explains any physical universe. The defensible claim is:

`A minimal octal iota substrate exhibits a reproducible transition from fragmented activity to scale-stable coherent nucleation when relational capacity, amplitude-gradient placement, and face+edge local connectivity are present.`

The core result chain is now:

1. `valence = 1` produces trace-limited propagation.
2. `valence = 2` enables coherent percolation.
3. Low coupling produces seed-sensitive/nucleation-limited growth.
4. Amplitude heterogeneity alone is sufficient in fixed geometry.
5. Amplitude placement controls morphology.
6. Face+edge candidate connectivity is sufficient; face-only connectivity fails.
7. The `A_4774` morphology survives `64³ -> 128³ -> 256³` scaling.

Before drafting, the remaining paper-critical work is:

- Freeze a versioned experiment manifest for the main figures.
- Produce publication-grade plots from Findings 001, 008, 009, 010, and 011.
- Add exact reproducibility instructions: config hashes, scripts, seeds, and database/artifact paths.
- Decide whether the paper frames this as artificial life, cellular automata, graph/percolation dynamics, or computational physics.

### Artifacts

- `output/findings/finding_011_scale_256_timeseries.csv`
- `output/findings/finding_011_scale_256_summary.csv`
- `output/findings/finding_011_scale_comparison.csv`

## Finding 012: Multiple Coherent Nuclei Can Coexist in 256³

### Status

Controlled multi-nucleus coexistence probe.

### Setup

All runs used:

- `grid.size = 256`
- Translated copies of the `A_4774` nucleus
- Uniform payload: `P = [4,4,4,4]` per nucleus
- Uniform vector state: `V = [49,49,49,49]` per nucleus
- `R = 7` for every initial iota
- `vectors.mode = cube26`
- `constants.neighbor_mode = cube26`
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `run.ticks = 4096`
- Seed `42`

Global LCF early stopping was disabled. Multiple healthy coherent bodies necessarily reduce largest-component fraction.

### Result

| Nuclei | Final Active | Largest | LCF | Components | Top 1 | Top 2 | Top 3 | Top 2 Coverage | Top 3 Coverage |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 20447 | 10528 | 0.515 | 201 | 10528 | 9065 | 151 | 0.958 | 0.966 |
| 4 | 61642 | 35230 | 0.572 | 398 | 35230 | 17394 | 7548 | 0.854 | 0.976 |

### Interpretation

The two-nucleus run produced two dominant coherent bodies rather than one merged body or many fragments.

The low global LCF is therefore not failure. For two nuclei:

`(component_1 + component_2) / active = 0.958`

This indicates stable coexistence of separate coherent domains at large separation.

The four-nucleus run did not produce four equal coherent bodies. It produced one dominant body, two substantial secondary bodies, and a small fourth/fifth tail:

`top_3 / active = 0.976`

This suggests that far-separated coherent nuclei can coexist, but growth is not symmetric under this fixed seed and placement. Multi-nucleus systems introduce competition or unequal nucleation efficiency even when each nucleus has identical internal composition.

The current read is:

`coherent bodies can coexist at separation, but multi-domain morphology is not guaranteed to remain equal or independent`

### Next Test

Run a two-nucleus interaction-distance probe:

- Far baseline: existing `IOTA-000269`
- Medium separation: translated by ~64 cells
- Near separation: translated by ~24 cells

The question shifts from coexistence to interaction:

- merge
- exclude/domain-boundary formation
- fragment at collision
- absorb/competitive dominance

### Artifacts

- `output/findings/finding_012_multi_nucleus_256_summary.csv`

## Finding 013: Two-Nucleus Distance Controls Coexistence vs Integration

### Status

Controlled two-nucleus distance interaction probe.

### Setup

All runs used:

- `grid.size = 256`
- Two translated `A_4774` nuclei
- Uniform payload: `P = [4,4,4,4]` per nucleus
- Uniform vector state: `V = [49,49,49,49]` per nucleus
- `R = 7` for every initial iota
- `vectors.mode = cube26`
- `constants.neighbor_mode = cube26`
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `run.ticks = 4096`
- Seed `42`

The far baseline is `IOTA-000269`. The medium and near variants changed only the separation between translated nuclei.

### Result

| Separation | Experiment | Final Active | Largest | LCF | Top 1 | Top 2 | Top 2 Coverage | Components |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| far | IOTA-000269 | 20447 | 10528 | 0.515 | 10528 | 9065 | 0.958 | 201 |
| medium | IOTA-000271 | 20365 | 10624 | 0.522 | 10624 | 8881 | 0.958 | 207 |
| near | IOTA-000272 | 37845 | 37195 | 0.983 | 37195 | 105 | 0.986 | 142 |

### Interpretation

Far and medium separations produced effectively the same morphology: two dominant coherent bodies with high top-2 coverage.

This supports stable coexistence/domain separation at those distances:

`far top2 / active = 0.958`

`medium top2 / active = 0.958`

Near separation produced a qualitatively different result. The two nuclei integrated into one dominant coherent body:

`near largest / active = 0.983`

The near case is therefore an integration/absorption regime, not a complexity-generating collision regime. It is useful because it bounds the model:

- separated coherent bodies can coexist
- close coherent bodies can collapse into one dominant absorber
- the transition between those regimes depends on separation

The current distance read is:

`two-nucleus interaction has a separation-dependent phase: coexistence at far/medium distance, integration at near distance`

### Next Test

The next long-time test should not use the near case. Near already became the absorber case by tick `4096`.

The paper-relevant long-time question is whether the medium case remains two-domain or eventually collapses:

- `grid.size = 256`
- two `A_4774` nuclei
- medium separation
- seed `42`
- `ticks = 8192` first
- no global LCF early stop

If medium remains two-domain at longer time, that supports persistent domain formation. If it eventually integrates, then coexistence is finite-time metastability rather than a stable long-time structure.

### Artifacts

- `output/findings/finding_013_two_nucleus_distance_summary.csv`

## Finding 014: Medium-Separation Coexistence Is Metastable at Long Time

### Status

Long-time extension of the medium two-nucleus interaction case.

### Setup

The run extended `IOTA-000271` from `4096` ticks to `8192` ticks:

- `grid.size = 256`
- Two `A_4774` nuclei
- Medium separation
- Seed `42`
- Uniform payload: `P = [4,4,4,4]` per nucleus
- Uniform vector state: `V = [49,49,49,49]` per nucleus
- `R = 7`
- `vectors.mode = cube26`
- `constants.neighbor_mode = cube26`
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- No global LCF early stop
- `stop_active_iotas = 100000`

### Result

| Run | Final Tick | Final Active | Largest | LCF | Top 1 | Top 2 | Top 2 Coverage | Early Stop |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| medium 4096 | 4096 | 20365 | 10624 | 0.522 | 10624 | 8881 | 0.958 | no |
| medium 8192 | 7424 | 107437 | 105826 | 0.985 | 105826 | 402 | 0.989 | active cap |

The long run did not reach `8192` ticks. It hit the `100000` active-iota cap at the sampled tick `7424`.

### Transition

The decisive transition occurred between ticks `5120` and `5376`:

| Tick | Active | Largest | LCF | Top 1 | Top 2 | Top 2 Coverage |
|---:|---:|---:|---:|---:|---:|---:|
| 4096 | 20365 | 10624 | 0.522 | 10624 | 8881 | 0.958 |
| 4608 | 28683 | 14169 | 0.494 | 14169 | 13639 | 0.969 |
| 4864 | 33263 | 16205 | 0.487 | 16205 | 16129 | 0.972 |
| 5120 | 38052 | 18707 | 0.492 | 18707 | 18374 | 0.974 |
| 5376 | 43396 | 42582 | 0.981 | 42582 | 158 | 0.985 |
| 7424 | 107437 | 105826 | 0.985 | 105826 | 402 | 0.989 |

### Interpretation

Medium-separation two-domain coexistence is not stable at longer time under this rule set. It is metastable.

From tick `4096` through tick `5120`, the system preserves two dominant coherent domains with high top-2 coverage. By tick `5376`, those domains collapse into one dominant absorbing component.

This is the strongest evidence so far for a time-dependent interaction regime:

`far/medium separation -> temporary coexistence`

`longer time -> integration/absorption`

The important distinction from the near case is timing. Near separation integrates by tick `4096`; medium separation remains two-domain at tick `4096` but integrates by tick `5376`.

This weakens the “persistent complexity” interpretation for the current rule set. The model currently supports coherent nucleation and temporary multi-domain coexistence, but longer time favors absorption unless another stabilizing mechanism exists.

### Paper Implication

This is still paper-relevant, but it changes the claim.

The defensible claim is not yet persistent open-ended complexity. The defensible claim is:

`minimal local rules produce scale-stable coherent nucleation, multi-domain coexistence, and separation-dependent metastable integration`

The next scientific question is what rule or conserved quantity stabilizes domain boundaries without adding arbitrary behavior.

### Artifacts

- `output/findings/finding_014_medium_long_time_summary.csv`
- `output/findings/finding_014_medium_long_time_transition.csv`

## Finding 015: Payload Contrast Alone Does Not Protect Identity

### Status

Stopped diagnostic after the result was clear.

### Setup

The run used:

- `grid.size = 256`
- Two medium-separated `A_4774` nuclei
- Nucleus 1 payload: `P = 4`
- Nucleus 2 payload: `P = 0`
- Same amplitude, range, vector state, geometry, and seed as Finding 014
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `run.ticks = 8192`
- Seed `42`

Metrics were committed every 256 ticks. The run was manually stopped after tick `6400` because it had already integrated.

### Result

| Tick | Active | Largest | LCF | Components |
|---:|---:|---:|---:|---:|
| 4096 | 16007 | 15204 | 0.950 | 136 |
| 5120 | 24947 | 23981 | 0.961 | 168 |
| 5888 | 45568 | 44367 | 0.974 | 193 |
| 6400 | 61444 | 60053 | 0.977 | 219 |

The unprotected payload-contrast run crossed:

- `LCF >= 0.95` by tick `4352`
- `LCF >= 0.97` by tick `5888`

### Interpretation

Payload contrast alone does not protect coherent identity.

Changing one nucleus from `P=4` to `P=0` did not preserve a two-domain state. It integrated into one dominant component. Under the current exchange rule, payload labels state but does not meaningfully gate coupling.

This sharpens the missing-law diagnosis:

`different state, same coupling -> eventual absorption`

To support persistent difference, state labels must affect interaction probability or influence. Otherwise payload is descriptive metadata, not a physical state variable.

### Next Test

Add a single compatibility diagnostic:

- same medium-separated `P=4` vs `P=0` setup
- same-payload coupling multiplier: `1.0`
- cross-payload coupling multiplier: `0.1`
- run to `8192` ticks or active cap

If top-2 coverage stays high past the unprotected integration window, compatibility coupling is a plausible protection mechanism.

### Artifacts

- `output/findings/finding_015_payload_contrast_unprotected_timeseries.csv`
- `output/findings/finding_015_payload_contrast_unprotected_summary.csv`

## Finding 016: State-Dependent Coupling Protects Identity

### Status

Single protected-coupling diagnostic.

### Setup

The protected run repeated the medium-separated `P=4` vs `P=0` two-nucleus diagnostic from Finding 015, with one rule change:

- `same_payload_coupling = 1.0`
- `cross_payload_coupling = 0.1`

The attenuation applies only when the target is already active. Dark substrate cells still accept influence normally, so the default dark payload value does not privilege either payload state.

All other controlled variables remained fixed:

- `grid.size = 256`
- two medium-separated `A_4774` nuclei
- seed `42`
- `vectors.mode = cube26`
- `constants.neighbor_mode = cube26`
- `constants.bond_probability = 0.005`
- `constants.valence = 2`
- `run.ticks = 8192`
- no global LCF early stop

### Result

| Run | Tick | Active | Largest | LCF | Components | LCF >= 0.95 | LCF >= 0.97 |
|---|---:|---:|---:|---:|---:|---:|---:|
| unprotected payload contrast | 6400 | 61444 | 60053 | 0.977 | 219 | 4352 | 5888 |
| protected cross-payload `0.1` | 8192 | 1537 | 166 | 0.108 | 124 | — | — |

Final protected component sizes:

| Tick | Active | Top 1 | Top 2 | Top 3 | Top 4 | Top 5 | Top 2 Coverage |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8192 | 1537 | 166 | 156 | 51 | 50 | 50 | 0.209 |

### Interpretation

State-dependent coupling protected identity.

Plain payload contrast failed because different states still coupled with full strength. With cross-payload coupling reduced to `0.1`, the same medium-separated `P=4` vs `P=0` setup no longer integrated into a dominant absorber by tick `8192`.

This is the first result showing that the model can preserve persistent difference when state affects interaction strength.

The result also changes the interpretation of payload:

`payload as label -> absorbed`

`payload as coupling state -> protected`

This supports the working principle:

`not all information couples equally`

### Caveat

The protected result did not produce two large coherent domains. It produced many small-to-medium components with low global LCF. That means compatibility coupling prevented absorption, but it may also have suppressed large coherent growth too strongly at `cross_payload_coupling = 0.1`.

The next question is not whether compatibility matters. It does. The next question is where the useful regime lies between:

- `cross_payload_coupling = 1.0`: absorption
- `cross_payload_coupling = 0.1`: protected but weak/fragmented growth

### Next Test

Run a minimal compatibility-coupling band:

- `cross_payload_coupling = 0.25`
- `cross_payload_coupling = 0.50`
- `cross_payload_coupling = 0.75`

Same setup, same seed, same medium separation.

Success criterion is not maximum LCF. The target is persistent multi-domain structure:

- top-2 coverage remains meaningful
- no single absorber dominates
- active growth remains nontrivial

### Artifacts

- `output/findings/finding_016_protected_payload_coupling_summary.csv`
- `output/findings/finding_016_protected_payload_coupling_timeseries.csv`

## Finding 017: Payload-Coupling Transition Is Sharp and Discrete-Looking

### Status

Compatibility-coupling boundary localization at `256^3`, `4096` ticks.

### Setup

The boundary search repeated the medium-separated two-nucleus setup:

- two `A_4774` nuclei
- one nucleus payload `P = 4`
- one nucleus payload `P = 0`
- `grid.size = 256`
- seed `42`
- `R = 7`
- `vectors.mode = cube26`
- `constants.neighbor_mode = cube26`
- `constants.valence = 2`
- `constants.bond_probability = 0.005`
- `same_payload_coupling = 1.0`
- variable `cross_payload_coupling`
- `run.ticks = 4096`

The success criterion was morphology, not maximum LCF. The target was persistent hierarchy:

- nontrivial active growth
- no dust-only suppression
- no single absorber
- meaningful top-5 and top-20 component coverage

### Result

| Coupling | Run | Active | Largest | LCF | Components | Top 5 | Top 20 | Component Entropy | Class |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0.200000 | IOTA-000283 | 841 | 105 | 0.125 | 81 | 0.334 | 0.674 | 5.362 | protected |
| 0.206250 | IOTA-000286 | 927 | 106 | 0.114 | 93 | 0.309 | 0.672 | 5.497 | protected |
| 0.209375 | IOTA-000287 | 927 | 106 | 0.114 | 93 | 0.309 | 0.672 | 5.497 | protected |
| 0.2109375 | IOTA-000288 | 15713 | 15054 | 0.958 | 143 | 0.969 | 0.985 | 0.495 | absorber |
| 0.212500 | IOTA-000285 | 14271 | 13574 | 0.951 | 105 | 0.965 | 0.985 | 0.547 | absorber |
| 0.225000 | IOTA-000284 | 14573 | 13869 | 0.952 | 109 | 0.965 | 0.986 | 0.541 | absorber |
| 0.250000 | IOTA-000278 | 41586 | 40239 | 0.968 | 123 | — | — | — | absorber |

The localized bracket is:

`0.209375 < p* < 0.2109375`

### Interpretation

The transition is not smooth at the measured resolution.

Two adjacent protected rows, `0.20625` and `0.209375`, produced identical final metrics. The next tested value, `0.2109375`, crossed hard into a giant absorbing component. This suggests the decimal parameter is not directly creating a gradual morphology change. Instead, it changes whether a discrete event passes a downstream eligibility threshold.

Once the threshold is crossed, the system enters the same absorber attractor seen at higher coupling values. Coupling mainly changes event timing and trajectory details, not the final morphology class.

The useful question therefore shifted from:

`What exact decimal creates hierarchy?`

to:

`What discrete event flips the system from protected to absorber?`

### Artifacts

- `output/IOTA-000283/metrics.csv`
- `output/IOTA-000284/metrics.csv`
- `output/IOTA-000285/metrics.csv`
- `output/IOTA-000286/metrics.csv`
- `output/IOTA-000287/metrics.csv`
- `output/IOTA-000288/metrics.csv`

## Finding 018: A Single Vector-Inheritance Event Causes the Absorber Transition

### Status

Paired event-trace diagnostic and counterfactual continuation.

### Setup

Two paired runs were instrumented from identical initial state and seed:

- protected side: `cross_payload_coupling = 0.209375`
- absorber side: `cross_payload_coupling = 0.2109375`

The tracer logged productive exchange events with:

- tick and within-tick sequence
- actor and target coordinates
- actor and target state
- event subtype
- base influence
- payload multiplier
- final influence
- vector inheritance draw and threshold
- rounded A/R outcomes
- component identity and size
- bridge status

The trace stopped at the first semantic divergence between the two runs.

### First Numeric Difference

The first numeric cross-payload influence difference occurred at tick `2`, sequence `2`.

That event did not change semantic outcome:

- low influence: `0.039880952380952385`
- high influence: `0.04017857142857143`
- vector inheritance failed in both runs
- rounded A/R values remained identical
- payload takeover failed in both runs

This confirms that numeric differences existed early, but they were not yet state-changing.

### First Semantic Divergence

The first state-changing divergence occurred at tick `337`, sequence `15`.

| Field | Low `0.209375` | High `0.2109375` |
|---|---:|---:|
| Actor | `(40, 43, 24)` | `(40, 43, 24)` |
| Target | `(41, 43, 23)` | `(41, 43, 23)` |
| Actor state | `A=7, R=7, V=31, P=4` | `A=7, R=7, V=31, P=4` |
| Target prior state | `A=3, R=3, V=0, P=0` | `A=3, R=3, V=0, P=0` |
| Event subtype | primary | primary |
| Payload class | cross-payload | cross-payload |
| Base influence | `0.5` | `0.5` |
| Coupling multiplier | `0.209375` | `0.2109375` |
| Final influence | `0.1046875` | `0.10546875` |
| Vector inheritance draw | `0.01315728279463102` | `0.01315728279463102` |
| Vector inheritance threshold | `0.0130859375` | `0.01318359375` |
| Vector inheritance | false | true |
| Target next V | `0` | `31` |

The high-coupling run crossed the vector-inheritance threshold by:

`0.01318359375 - 0.01315728279463102 = 0.000026310955368977`

The low-coupling run missed it by:

`0.01315728279463102 - 0.0130859375 = 0.000071345294631022`

No payload takeover occurred. Rounded `A` and `R` were unchanged between the two cases. The semantic difference was specifically:

`target V remains 0`

versus

`target inherits V=31`

### Counterfactual Test

At tick `337`, immediately after the divergence:

- forced low run: set target `(41,43,23)` to `V=31`
- forced high run: set target `(41,43,23)` back to `V=0`

All other state remained unchanged.

### Counterfactual Result

| Variant | Coupling | Forced V | Active | Largest | LCF | Components | Class |
|---|---:|---:|---:|---:|---:|---:|---|
| low natural | 0.209375 | no | 927 | 106 | 0.114 | 93 | protected |
| high natural | 0.2109375 | no | 15713 | 15054 | 0.958 | 143 | absorber |
| low forced high-vector | 0.209375 | `V=31` | 15713 | 15054 | 0.958 | 143 | absorber |
| high forced low-vector | 0.2109375 | `V=0` | 927 | 106 | 0.114 | 93 | protected |

The forced variants swapped outcomes exactly.

This establishes the tick-337 vector-inheritance event as causal for the protected/absorber fate split under this seed and setup.

### Interpretation

The critical transition is caused by a discrete vector-state inheritance event, not by smooth accumulation of the coupling decimal.

The coupling value changes the vector inheritance threshold just enough for one random draw to pass. That single pass changes the local directional state from `V=0` to `V=31`. The altered vector state then seeds a connectivity cascade that becomes the giant absorbing component.

This is the strongest mechanistic result so far:

`near-boundary cross-payload coupling -> vector inheritance pass/fail -> directional state flip -> cascade fate`

### Angular-Momentum Read

The absorber run did not show a macroscopic angular-momentum signal:

- final vector persistence ratio: `0.999745`
- final mean vector alignment: `0.999598`
- final mean vector turn: `0.0319°`
- mean exchange turn: `0.447°`
- mean secondary-exchange turn: `90.516°`

The important directional mechanism was not sustained rotation. It was a single inherited vector state that redirected future growth.

### Artifacts

- `src/payload_coupling_divergence_trace.py`
- `src/payload_coupling_divergence_continuation.py`
- `output/findings/finding_018_payload_coupling_divergence_trace.json`
- `output/findings/finding_018_payload_coupling_first_semantic_divergence.csv`
- `output/findings/finding_018_payload_coupling_divergence_continuation.csv`
- `output/findings/finding_018_payload_coupling_divergence_continuation.json`

## Finding 019: Boundary Seed Ensemble Is Heavy-Tailed

### Status

Completed seed-ensemble boundary census for the Finding 017-018 bracket.

### Setup

The ensemble repeated the medium-separated two-nucleus setup:

- two `A_4774` nuclei
- one nucleus payload `P = 4`
- one nucleus payload `P = 0`
- `grid.size = 256`
- `R = 7`
- `vectors.mode = cube26`
- `constants.neighbor_mode = cube26`
- `constants.valence = 2`
- `constants.bond_probability = 0.005`
- `same_payload_coupling = 1.0`
- `run.ticks = 4096`
- seeds `42-71`

Only two cross-payload coupling values were tested:

- protected-side bracket: `cross_payload_coupling = 0.209375`
- absorber-side bracket: `cross_payload_coupling = 0.2109375`

The completed census contains `60` completed runs across `30` seeds. One interrupted partial seed-49 record exists in the database without `final_tick` and is excluded from the summary.

### Result

| Regime | Seeds | Count |
|---|---|---:|
| bracket-sensitive absorber flip | `42`, `56` | 2 |
| bracket-insensitive high-dominant | `45`, `50`, `61` | 3 |
| bracket-insensitive protected / dust-like | all remaining seeds | 25 |

Notable seeds:

| Seed | Low Active | Low LCF | High Active | High LCF | Read |
|---:|---:|---:|---:|---:|---|
| 42 | 927 | 0.114 | 15713 | 0.958 | bracket-sensitive absorber flip |
| 45 | 6906 | 0.906 | 6981 | 0.903 | high-dominant, bracket-insensitive |
| 50 | 9658 | 0.915 | 9658 | 0.915 | high-dominant, bracket-insensitive |
| 56 | 987 | 0.158 | 26193 | 0.974 | bracket-sensitive absorber flip |
| 61 | 14096 | 0.942 | 14096 | 0.942 | high-dominant, bracket-insensitive |

### Interpretation

The ensemble does not support a universal transition at the exact decimal bracket.

The stronger interpretation is a heavy-tailed basin landscape:

`many protected realizations -> few high-dominant near-absorber realizations -> rare bracket-sensitive absorber flips`

This reframes Finding 017. The seed-42 bracket remains real, but it is not a population-wide threshold at the tested resolution. Most stochastic realizations do not care about the `0.209375 -> 0.2109375` perturbation. Rare realizations do, and the rare transitions can have substantially different morphology.

Seed `56` is especially important because it also flips across the bracket, but its absorber-side morphology is not a replay of seed `42`:

- seed `42` high side: `15713` active, `LCF = 0.958`
- seed `56` high side: `26193` active, `LCF = 0.974`

The mechanism census is therefore now the central validation problem. The question is not only whether a rare seed flips. It is whether the same small set of event classes repeatedly selects the basin.

Candidate basin-selector classes remain:

- directional-state inheritance
- payload takeover
- rounded A/R threshold crossing
- target-selection or secondary-bond admission
- inter-component bridge formation
- early geometry attachment to a coherent growth front

### Complexity Boundary

This ensemble still does not establish persistent complexity.

The observed seed-level classes are:

- protected fragmented / dust-like regimes
- high-dominant but bracket-insensitive regimes
- absorbing-component takeover regimes

No run in this bracket produced a stable multi-domain or open-ended complex morphology. The current claim should remain basin selection and coherent nucleation, not persistent complexity.

### Next Test

Trace seed `56` using the same paired divergence method as Finding 018:

- identify the first semantic divergence;
- classify the event class;
- compare it to the seed-42 tick-337 directional-state inheritance event;
- if the event is plausible as a basin selector, run a bidirectional counterfactual continuation.

If seed `56` also flips by directional-state inheritance, Finding 018 begins to generalize as a mechanism. If it flips by another event class, then the transition may be robust while the seed-42 mechanism is only one member of a small basin-selection taxonomy.

### Seed 56 Trace Result

Seed `56` also flipped by directional-state inheritance.

The first numeric cross-payload influence difference again occurred at tick `2`, sequence `2`, without semantic effect.

The first gate divergence occurred at tick `288`, sequence `6`, but it did not change state. The high-coupling run passed vector inheritance while the low-coupling run failed, but actor and target already had the same vector state `V=27`, so `next_V` remained `27` on both sides.

The first state-changing divergence occurred at tick `408`, sequence `19`.

| Field | Low `0.209375` | High `0.2109375` |
|---|---:|---:|
| Actor | `(41, 43, 24)` | `(41, 43, 24)` |
| Target | `(42, 44, 24)` | `(42, 44, 24)` |
| Actor state | `A=7, R=7, V=27, P=4` | `A=7, R=7, V=27, P=4` |
| Target prior state | `A=4, R=4, V=0, P=0` | `A=4, R=4, V=0, P=0` |
| Event subtype | primary | primary |
| Payload class | cross-payload | cross-payload |
| Base influence | `0.5` | `0.5` |
| Coupling multiplier | `0.209375` | `0.2109375` |
| Final influence | `0.1046875` | `0.10546875` |
| Vector inheritance draw | `0.013103245979836031` | `0.013103245979836031` |
| Vector inheritance threshold | `0.0130859375` | `0.01318359375` |
| Vector inheritance | false | true |
| Target next V | `0` | `27` |

The high-coupling run crossed the vector-inheritance threshold by:

`0.01318359375 - 0.013103245979836031 = 0.000080347770163966`

The low-coupling run missed it by:

`0.013103245979836031 - 0.0130859375 = 0.000017308479836034`

As with seed `42`, there was no payload takeover and no rounded A/R divergence. The state-changing difference was specifically:

`target V remains 0`

versus

`target inherits V=27`

### Seed 56 Counterfactual

At tick `408`, immediately after the divergence:

- forced low run: set target `(42,44,24)` to `V=27`
- forced high run: set target `(42,44,24)` back to `V=0`

All other state remained unchanged.

| Variant | Coupling | Forced V | Active | Largest | LCF | Components | Class |
|---|---:|---:|---:|---:|---:|---:|---|
| low natural | 0.209375 | no | 987 | 156 | 0.158 | 85 | protected |
| high natural | 0.2109375 | no | 26193 | 25518 | 0.974 | 123 | absorber |
| low forced high-vector | 0.209375 | `V=27` | 26193 | 25518 | 0.974 | 123 | absorber |
| high forced low-vector | 0.2109375 | `V=0` | 987 | 156 | 0.158 | 85 | protected |

The forced variants swapped outcomes exactly.

This means seed `56` is also a single-event directional-state inheritance basin switch, not a diffuse multi-event accumulation or a late connectivity-threshold cascade.

### Mechanism Comparison

Seeds `42` and `56` differ substantially in final morphology, but share the same basin-selector class.

| Seed | Divergence Tick | Target | Low V Outcome | High V Outcome | High Active | High LCF |
|---:|---:|---|---:|---:|---:|---:|
| 42 | 337 | `(41,43,23)` | `0` | `31` | 15713 | 0.958 |
| 56 | 408 | `(42,44,24)` | `0` | `27` | 26193 | 0.974 |

The shared mechanism is:

`near-boundary cross-payload coupling -> vector inheritance pass/fail -> directional-state flip -> absorber/protected fate`

This now generalizes Finding 018 from one realization to two independent bracket-sensitive realizations.

The high-dominant controls `45`, `50`, and `61` are important because they show that high-LCF-ish morphology can occur without bracket sensitivity:

- seed `45`: low `LCF=0.906`, high `LCF=0.903`
- seed `50`: low `LCF=0.915`, high `LCF=0.915`
- seed `61`: low `LCF=0.942`, high `LCF=0.942`

Those controls separate two phenomena:

- high-dominant morphology can arise from seed geometry independent of the bracket perturbation;
- bracket-sensitive absorber takeover, in the two observed cases, is selected by a single vector-inheritance event.

### Artifacts

- `src/payload_coupling_seed_ensemble_4096_sweep.py`
- `src/payload_coupling_seed56_divergence_trace.py`
- `src/payload_coupling_seed56_divergence_continuation.py`
- `output/findings/finding_019_payload_coupling_seed_ensemble_raw.csv`
- `output/findings/finding_019_payload_coupling_seed_ensemble_summary.csv`
- `output/findings/finding_019_payload_coupling_seed_ensemble_summary.json`
- `output/findings/finding_019_seed56_payload_coupling_divergence_trace.json`
- `output/findings/finding_019_seed56_payload_coupling_first_state_divergence.csv`
- `output/findings/finding_019_seed56_payload_coupling_divergence_continuation.csv`
- `output/findings/finding_019_seed56_payload_coupling_divergence_continuation.json`

## Finding 020: Committor Test Shows Path-Dependent Basin Selection

### Status

Completed committor-style continuation test for the two bracket-sensitive seeds from Findings 018-019.

### Setup

The test saved the state at the traced state-changing directional-inheritance event for each seed, forced the target vector state to each alternative, and launched independent future random continuations.

Seeds and interventions:

- seed `42`: checkpoint at tick `337`, target `(41,43,23)`, alternatives `do(V=0)` and `do(V=31)`
- seed `56`: checkpoint at tick `408`, target `(42,44,24)`, alternatives `do(V=0)` and `do(V=27)`

For each seed, both coupling laws were tested:

- protected-side law: `cross_payload_coupling = 0.209375`
- absorber-side law: `cross_payload_coupling = 0.2109375`

Each condition used `50` independent continuations, for `400` total completed runs. Early absorber stopping was enabled, with the absorber criterion based on high largest-component fraction.

### Result

| Seed | Law | Forced V | Samples | Absorber | High-Dominant | Protected | Mean Active | Mean LCF |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 42 | high | 0 | 50 | 0.08 | 0.00 | 0.92 | 2032.22 | 0.196 |
| 42 | high | 31 | 50 | 0.10 | 0.02 | 0.88 | 2018.30 | 0.219 |
| 42 | low | 0 | 50 | 0.18 | 0.08 | 0.74 | 3308.92 | 0.339 |
| 42 | low | 31 | 50 | 0.04 | 0.10 | 0.86 | 2464.38 | 0.239 |
| 56 | high | 0 | 50 | 0.10 | 0.14 | 0.76 | 4009.04 | 0.371 |
| 56 | high | 27 | 50 | 0.04 | 0.12 | 0.84 | 2678.10 | 0.303 |
| 56 | low | 0 | 50 | 0.08 | 0.10 | 0.82 | 3488.50 | 0.323 |
| 56 | low | 27 | 50 | 0.06 | 0.06 | 0.88 | 2294.44 | 0.267 |

The expected strong-basin-selector result did not occur. Forcing the absorber-side vector did not produce absorber fate in most continuations.

Instead, absorber probabilities remained low across all conditions:

- seed `42`, `do(V=31)`: absorber probability `0.10` under the high law and `0.04` under the low law
- seed `56`, `do(V=27)`: absorber probability `0.04` under the high law and `0.06` under the low law

### Interpretation

The traced directional-state inheritance events are real path-specific causes, but they are not deterministic committor basin switches under independent future random continuations.

Findings 018-019 established:

`given the recorded future random stream, changing one target vector state swaps protected versus absorber fate`

Finding 020 establishes the stronger correction:

`under independent future random streams, the same forced vector state usually does not force absorber fate`

The best current interpretation is path-dependent basin selection:

`directional-state inheritance event + compatible downstream stochastic exchange history -> possible absorber takeover`

This weakens the strongest version of the basin-boundary claim. The microscopic vector inheritance event is necessary and sufficient for the recorded continuation, but not sufficient by itself across the sampled continuation ensemble.

Current causal frame:

- Law defines the reachable transition space.
- Kick resolves the first asymmetry and selects a basin/history.
- History compounds local constraints into valence.
- Valence changes which future transitions become easy, hard, or effectively inaccessible.
- Connectivity changes how coherent extent is observed or classified, but so far does not appear to be the primary selector of outcome.

The state space may be broadly reachable in principle, but reachability from here is history-conditioned.

### Complexity Boundary

The committor results are scientifically useful for the complexity search because they separate three regimes:

- absorber: high-LCF single-cluster takeover
- protected dust: low-activity, low-LCF fragmented continuation
- edge-coherent protected: high activity with incomplete component takeover

These labels are provisional until component metrics are recomputed under face6, face18, and cube26 connectivity. The current LCF values are face-connectivity LCF values. A case that looks fragmented under face6 may be coherent under the interaction-neighborhood graph that actually generated it.

The edge-coherent protected cases remain the immediate scientific target, but not the immediate engineering target. First verify that they are genuinely non-absorbing under matched connectivity. They preserve substantial activity without allowing one face-connected component to fully absorb the future.

Largest protected exception cases:

| Seed | Law | Condition | Forced V | Sample Index | Continuation Seed | Active | LCF | Component Entropy |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 56 | low | protected_vector | 0 | 35 | 76260657 | 33023 | 0.693 | 1.100 |
| 42 | high | protected_vector | 0 | 26 | 62360648 | 28327 | 0.630 | 1.125 |
| 56 | high | protected_vector | 0 | 48 | 76360670 | 21411 | 0.631 | 1.288 |

These are not absorber successes and should not be counted as stable complexity yet. They are candidate edge-coherent states: large, organized, and not fully monopolized by a single connected component.

High-dominant near-collapse cases should be retained as controls:

| Seed | Law | Condition | Forced V | Sample Index | Continuation Seed | Active | LCF |
|---:|---|---|---:|---:|---:|---:|---:|
| 56 | low | absorber_vector | 27 | 1 | 76270623 | 15450 | 0.948 |
| 56 | high | protected_vector | 0 | 41 | 76360663 | 14860 | 0.949 |
| 56 | high | absorber_vector | 27 | 16 | 76370638 | 14517 | 0.944 |
| 42 | low | absorber_vector | 31 | 17 | 62270639 | 14357 | 0.944 |

### Next Test

Do not run second-order coherence diagnostics as the next step. First repair and rerun connectivity-aware component measurement.

Immediate measurement pass:

1. Add component metrics for `face6`, `face18`, and `cube26`.
2. Recompute Finding 020 exception rows under all three connectivity graphs.
3. Reclassify edge-coherent protected cases using matched interaction-neighborhood connectivity.
4. Keep the original face6 rows for historical comparison.

Then run second-order coherence diagnostics on the largest cases that remain high-activity and non-absorbing under cube26.

Priority diagnostics:

1. component lineage and merge history;
2. top-k component persistence over time;
3. center-free circulation / directed exchange-loop bias;
4. centroid-relative rotation as a secondary spatial diagnostic;
5. vector-inheritance ancestry for the high-activity protected cases.

The immediate first target is:

`seed=56`, `law=low`, `condition=protected_vector`, `sample_index=35`, `continuation_seed=76260657`

### Artifacts

- `src/payload_coupling_committor_analysis.py`
- `src/second_order_coherence_diagnostic.py`
- `src/committor_exception_catalog.py`
- `output/findings/finding_020_committor_raw.csv`
- `output/findings/finding_020_committor_summary.csv`
- `output/findings/finding_020_committor_summary.json`

## Finding 021: Coherence Is Connectivity-Relative

### Status

Methodological synthesis from code review of the test rig and Findings 017-020. No new simulation result is claimed here.

### Trigger

The key payload-coupling experiments use full-neighborhood growth:

- `vectors.mode = cube26`
- `constants.neighbor_mode = cube26`

The current component measurement uses face-only connectivity in `coherence_stats`, and the second-order diagnostic also labels components with face-only connectivity. Therefore the reported LCF in Findings 017-020 is best read as `LCF_face6`, not as the largest-component fraction of the same relation graph that generated the structure.

### Synthesis

This does not invalidate the seed-42 and seed-56 causal replay results.

Those results depended on large active-count and fate swaps:

- seed `42`: low natural `927` active, high natural `15713` active, and bidirectional vector forcing swapped the outcomes exactly;
- seed `56`: low natural `987` active, high natural `26193` active, and bidirectional vector forcing swapped the outcomes exactly.

Those macroscopic active-count cascades survive the connectivity critique. What becomes provisional is the regime label attached to the final morphology:

- `protected`
- `fragmented`
- `high-dominant`
- `absorber`
- `edge-coherent protected`

Those labels must be recomputed under the measurement graph being used.

### Interpretation

There is not one absolute coherence measurement. Coherence is relative to an allowed relation graph.

Practical consequence:

- `face6` coherence measures literal face adjacency.
- `face18` coherence measures face-plus-edge adjacency.
- `cube26` coherence measures the full interaction-neighborhood adjacency used by the key growth experiments.

A run can therefore be face-fragmented but interaction-neighborhood coherent. That is not merely a bookkeeping artifact. It may be the scientifically interesting middle class: form that is coherent at the grammar scale that produced it, but fragmented under stricter local contact.

### Measurement Protocol

Going forward, component tables should report these side by side:

| Metric | Meaning |
|---|---|
| `largest_component_face6` | Largest face-connected active component. |
| `largest_component_face18` | Largest face-or-edge-connected active component. |
| `largest_component_cube26` | Largest full-neighborhood active component. |
| `LCF_face6` | `largest_component_face6 / active_sites`. |
| `LCF_face18` | `largest_component_face18 / active_sites`. |
| `LCF_cube26` | `largest_component_cube26 / active_sites`. |
| `component_count_face6` | Face-connected component count. |
| `component_count_face18` | Face-or-edge-connected component count. |
| `component_count_cube26` | Full-neighborhood component count. |

Historical `LCF` columns should not be overwritten. They should be relabeled or interpreted as `LCF_face6` unless a run explicitly used a different component graph.

### Reanalysis Targets

Minimum rows to recompute before second-order coherence:

| Group | Rows |
|---|---|
| Seed-42 bracket | low natural, high natural, low forced `V=31`, high forced `V=0`. |
| Seed-56 bracket | low natural, high natural, low forced `V=27`, high forced `V=0`. |
| High-dominant controls | seeds `45`, `50`, and `61` at both bracket couplings. |
| Protected/dust controls | representative non-flipping seeds from Finding 019. |
| Committor exceptions | largest high-activity protected rows from Finding 020. |

Classification rule:

- `absorber`: high LCF under all tested connectivity graphs, or explicitly high under the declared graph.
- `face-fragmented / cube-coherent`: low `LCF_face6` but high `LCF_cube26`.
- `protected dust`: low activity and low LCF under all tested graphs.
- `edge-coherent protected`: high activity, non-absorbing under cube26, and persistent multi-component structure under the relevant graph.

### Next Steps

1. Add a shared connectivity helper backed by the same neighbor sets used by the interaction rules.
2. Extend `coherence_stats` and diagnostics to compute `face6`, `face18`, and `cube26` metrics side by side.
3. Rerun the reanalysis targets above and write a compact comparison table.
4. Update Findings 017-020 labels only where the multi-graph results require it.
5. Run second-order coherence diagnostics only on cases that remain high-activity and non-absorbing after the multi-connectivity pass.

### Protocol Boundary

Use two run protocols from here forward:

- classification protocol: early stopping allowed, intended for cheap screening;
- comparison protocol: fixed horizon, early stopping disabled, intended for paper-grade morphology and time-series comparisons.

Finding 020 remains a strong correction to the deterministic story: the vector-inheritance events are replay-pivotal under the recorded future random stream, but not robust committor-pivotal states under independent continuations. The next measurement pass should preserve that distinction while making the morphology labels connectivity-explicit.

## Finding 022: Openness Timeline Instrument

### Status

Development-scale v0.1 single-seed run completed for seeds `42` and `56`.

### Trigger

The current project framing defines the hunted middle regime as:

`durable form without closed future`

Finding 020 already built the key causal instrument: save a state, resample independent future random continuations, and measure the outcome distribution. The next step is to run that instrument on scheduled checkpoints instead of only on traced divergence events.

### Definition

For a checkpoint state `s_t`:

```text
O(t) = H(Pr(outcome class | s_t)) / log(C)
```

where `C = 3` for the current outcome classes:

- `absorber`
- `high_dominant`
- `protected`

The commitment time is:

```text
t_c = first checkpoint where O(t) < epsilon
```

The constraint-accumulation rate is estimated between checkpoints:

```text
-dO/dt
```

The second-pass complexity score is:

```text
component_persistence(t) * O(t)
```

Do not block the O(t) run on persistence. O(t) alone is the first instrument. Persistence is added only after the openness timeline is stable enough to identify candidate states worth tracking. This is not an assertion that v0.1 produces complexity; it is the measurement needed to test whether v0.1 closes its future and whether v0.2 keeps it open longer.

### Operational Form

The runner:

1. follows one base trajectory;
2. saves checkpoints on a tick schedule;
3. launches `N` independent continuations from each checkpoint;
4. classifies each future under an explicit connectivity graph, defaulting to `cube26`;
5. emits per-continuation rows and per-checkpoint openness summaries;
6. optionally estimates top-k component persistence with `--with-persistence`.

Development-scale example:

```bash
python src/openness_timeline.py \
  --config config.yaml \
  --seed 42 \
  --ticks 1024 \
  --checkpoint-every 256 \
  --horizon 512 \
  --samples 8 \
  --connectivity cube26
```

### Interpretation

Pre-registered v0.1 hypothesis:

Under v0.1 irreversible growth, `O(t)` declines toward finite commitment across tested seed classes.

Interpretation:

- If every sampled trajectory reaches low openness within the observed horizon, then irreversible growth admits grammar and nucleation but not durable form without closed future.
- If seed `56` or another case retains openness longer than expected, that is not a failure. It becomes the first priority candidate for `--with-persistence`, second-order diagnostics, and possible complex-protected classification.

The first result is not a failure. It would justify `iota-rig-v0.2.0` as a scientific law change rather than an engineering preference.

### Development-Scale Result

Command family:

```bash
.venv/bin/python src/openness_timeline.py \
  --config config.yaml \
  --prefix finding_022_openness_timeline_seed${seed} \
  --seed ${seed} \
  --ticks 1024 \
  --checkpoint-every 256 \
  --horizon 512 \
  --samples 8 \
  --connectivity cube26
```

Result:

| Seed | First commitment tick | Checkpoints | Outcome distribution | Openness |
|---|---:|---:|---|---:|
| `42` | `0` | `0, 256, 512, 768, 1024` | `8/8 protected` at every checkpoint | `0.0` |
| `56` | `0` | `0, 256, 512, 768, 1024` | `8/8 protected` at every checkpoint | `0.0` |

Under the current `config.yaml` single-seed v0.1 setup, the sampled futures are closed from the initial checkpoint. Seed `42` reaches a base active count of `13`; seed `56` reaches a base active count of `5`. No checkpoint produced absorber or high-dominant futures under `cube26`.

Interpretation: this run supports the pre-registered negative result for the single-seed v0.1 substrate. It does not justify a persistence pass, because the complexity proxy would be multiplied by `O(t)=0`. The next useful step is the versioned `iota-rig-v0.2.0` conserved-ledger law path.

### v0.2 Boundary

The proposed v0.2 law is specified separately in:

- `docs/IOTA_RIG_V0_2_LAW_SPEC.md`

The central v0.2 requirements are:

- exact integer amplitude ledger;
- exhaustion deactivation;
- new metrics for `total_A`, `active_A`, `latent_A`, `depleted_cells`, and `ledger_error`;
- Finding 018 golden replay compatibility when the v0.1 law path is selected.

### Artifacts

- `src/continuation.py`
- `src/openness_timeline.py`
- `docs/IOTA_RIG_V0_2_LAW_SPEC.md`
- `output/findings/finding_022_openness_timeline_seed42_raw.csv`
- `output/findings/finding_022_openness_timeline_seed42_summary.csv`
- `output/findings/finding_022_openness_timeline_seed42_summary.json`
- `output/findings/finding_022_openness_timeline_seed42_states/`
- `output/findings/finding_022_openness_timeline_seed56_raw.csv`
- `output/findings/finding_022_openness_timeline_seed56_summary.csv`
- `output/findings/finding_022_openness_timeline_seed56_summary.json`
- `output/findings/finding_022_openness_timeline_seed56_states/`

## Finding 023: v0.2 Single-Seed Baseline Still Closes Immediately

### Status

Development-scale v0.2 baseline and openness comparison completed for seeds `42` and `56`.

### Setup

Versioned law path:

```yaml
simulation_version: iota-rig-v0.2.0
constants:
  conservation: hard
  deactivation: exhaustion
  vacuum_amplitude: 1
```

The default single-seed setup was retained. Baseline runs used `1024` ticks. Openness runs used the same development protocol as Finding 022:

```text
ticks=1024
checkpoint_every=256
horizon=512
samples=8
connectivity=cube26
```

### Baseline Result

| Seed | Final active | LCF_face6 | LCF_cube26 | Total A | Active A | Latent A | Depleted | Ledger error |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `42` | `6` | `0.500` | `1.000` | `262149` | `11` | `262138` | `0` | `0` |
| `56` | `4` | `0.250` | `1.000` | `262149` | `9` | `262140` | `0` | `0` |

The ledger invariant holds exactly, but the current single-seed v0.2 baseline does not produce depletion, exhaustion, or substantial propagation at this scale.

### Openness Result

| Version | Seed | First commitment tick | Openness values | Base active trajectory |
|---|---:|---:|---|---|
| `v0.1` | `42` | `0` | `0, 0, 0, 0, 0` | `1, 13, 13, 13, 13` |
| `v0.1` | `56` | `0` | `0, 0, 0, 0, 0` | `1, 5, 5, 5, 5` |
| `v0.2` | `42` | `0` | `0, 0, 0, 0, 0` | `1, 6, 6, 6, 6` |
| `v0.2` | `56` | `0` | `0, 0, 0, 0, 0` | `1, 2, 2, 4, 4` |

Interpretation: hard conservation alone is not enough. Under the current single-seed parameters, v0.2 makes energy accounting falsifiable but does not yet create durable form without closed future. The next v0.2 work should be a parameter search over transfer probability, vacuum budget, valence, and initial seed count, while keeping `ledger_error == 0`.

### Artifacts

- `experiments_v02/IOTA-000001.md`
- `experiments_v02/IOTA-000002.md`
- `output_v02/IOTA-000001/metrics.csv`
- `output_v02/IOTA-000002/metrics.csv`
- `output/findings/finding_023_v02_openness_timeline_seed42_raw.csv`
- `output/findings/finding_023_v02_openness_timeline_seed42_summary.csv`
- `output/findings/finding_023_v02_openness_timeline_seed42_summary.json`
- `output/findings/finding_023_v02_openness_timeline_seed42_states/`
- `output/findings/finding_023_v02_openness_timeline_seed56_raw.csv`
- `output/findings/finding_023_v02_openness_timeline_seed56_summary.csv`
- `output/findings/finding_023_v02_openness_timeline_seed56_summary.json`
- `output/findings/finding_023_v02_openness_timeline_seed56_states/`

## Finding 024: Static Component Diagnostics for Protected Exceptions

### Status

Static final-state component/vector diagnostics completed for the three largest high-activity protected committor exceptions.

### Targets

| Seed | Law | Condition | Sample | Active | LCF_face6 | LCF_cube26 | Top cube26 component |
|---:|---|---|---:|---:|---:|---:|---:|
| `56` | `low` | `protected_vector` | `35` | `33023` | `0.693` | `0.700` | `23112` |
| `42` | `high` | `protected_vector` | `26` | `28327` | `0.630` | `0.634` | `17970` |
| `56` | `high` | `protected_vector` | `48` | `21411` | `0.631` | `0.634` | `13575` |

### Interpretation

The top protected exceptions remain non-absorbing under cube26. Cube26 increases the largest-component fraction only slightly for these three cases, so they are not merely face6-fragmented artifacts. They are large, partially coherent, non-absorbed states.

Payload entropy inside the top cube26 component is near zero in all three cases, while vector entropy remains nonzero. That suggests payload identity has collapsed locally, but directional-state structure remains heterogeneous. These are still candidates for structural analysis, not evidence of open-ended complexity.

Full temporal second-order tracing is expensive for high-activity cases because it records per-tick event graphs. For broad triage, static final-state diagnostics from saved NPZ artifacts are the practical first pass; temporal lineage should be reserved for the smallest number of high-value candidates.

### Artifacts

- `output/findings/finding_024_static_component_diagnostics.csv`
- `output/findings/finding_024_static_component_diagnostics.json`

## Finding 025: Multiprocess Replay Queue and First v0.2 Parameter Search

### Status

Completed. The queue ran under an instrumented `screen` + `caffeinate` supervisor and exited cleanly with code `0`.

### Setup

The queue executed three phases:

1. branch-sensitive golden replay for seeds `42` and `56`;
2. targeted committor replay for the three highest-activity protected exceptions;
3. a 128-task v0.2 parameter search over `amplitude_coupling`, `vacuum_amplitude`, `valence`, initial active count, and `bond_probability`.

The long-running queue finished:

```text
started_at=2026-07-08T09:44:58-04:00
finished_at=2026-07-08T11:24:51-04:00
golden=completed exit 0
committor=completed exit 0
search=completed exit 0
```

### Golden Replay Result

The multiprocess golden replay reproduced all expected rows.

| Label | Active | LCF_face6 | Clusters |
|---|---:|---:|---:|
| `seed42_low_natural` | `927` | `0.114347` | `93` |
| `seed42_high_natural` | `15713` | `0.958060` | `143` |
| `seed42_low_force_high_vector` | `15713` | `0.958060` | `143` |
| `seed42_high_force_low_vector` | `927` | `0.114347` | `93` |
| `seed56_low_natural` | `987` | `0.158055` | `85` |
| `seed56_high_natural` | `26193` | `0.974230` | `123` |
| `seed56_low_force_high_vector` | `26193` | `0.974230` | `123` |
| `seed56_high_force_low_vector` | `987` | `0.158055` | `85` |

### Targeted Committor Result

The three targeted high-activity protected exceptions remained protected under `cube26` classification.

| Seed | Law | Condition | Sample | Active | LCF_cube26 | Classification |
|---:|---|---|---:|---:|---:|---|
| `42` | `high` | `protected_vector` | `26` | `28327` | `0.634377` | `protected` |
| `56` | `high` | `protected_vector` | `48` | `21411` | `0.634020` | `protected` |
| `56` | `low` | `protected_vector` | `35` | `33023` | `0.699876` | `protected` |

### Coarse v0.2 Search Result

The 128-task coarse search completed with `max_abs_ledger_error == 0` for every completed task. The top coarse candidate was:

| Seed | kA | Vacuum | Valence | Initial active | Peak active | Final active | Depleted | Transfers | LCF_cube26 | Ledger error |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `56` | `4.0` | `2` | `4` | `4` | `179` | `179` | `40` | `258` | `0.318436` | `0` |

Across the top rows, the useful basin was not the single-seed default. It concentrated at:

- `bond_probability = 1.0`;
- higher valence, initially `4`;
- initial active count `4`;
- `vacuum_amplitude = 2`;
- broad tolerance over `amplitude_coupling`.

### Interpretation

The replay queue is now practical and reproducible. The golden replay validates that the optimized multiprocess path preserves the branch-sensitive seed `42/56` replay facts. The targeted committor replay confirms that the largest protected exceptions are not face-connectivity artifacts and remain protected under the same replay machinery.

The first v0.2 search shows that exact conservation and depletion become materially active only after increasing local interaction opportunities and initial nuclei. This moves v0.2 from inert single-seed accounting to ledger-exact depletion-front search.

### Artifacts

- `src/parallel_replay.py`
- `src/queue_supervisor.py`
- `src/launch_queue.py`
- `src/v02_parameter_search.py`
- `output/findings/parallel_golden_replay.csv`
- `output/findings/parallel_golden_replay.json`
- `output/findings/parallel_committor_seed42_56_targets/committor_rows.csv`
- `output/findings/parallel_committor_seed42_56_targets/committor_summary.csv`
- `output/findings/parallel_committor_seed42_56_targets/committor_summary.json`
- `output/findings/parallel_committor_seed42_56_targets/states/`
- `output/findings/finding_025_v02_parameter_search.csv`
- `output/findings/finding_025_v02_parameter_search.json`
- `output/findings/queue_20260708_094458_state.json`
- `output/findings/queue_20260708_094458_supervisor.log`

## Finding 026: Focused v0.2 Search Finds a Valence-8 Depletion Basin

### Status

Completed. A focused 48-task follow-up search tightened around the Finding 025 basin.

### Setup

The search fixed `bond_probability = 1.0` and initial active count `16`, then crossed:

```text
seeds = 42, 56
amplitude_coupling = 2, 3, 4, 5, 6, 8
vacuum_amplitude = 2, 3
valence = 6, 8
ticks = 2048
stagnation_window = 512
stop_active_iotas = 1000
```

The `stop_active_iotas` cap was added after an intentionally broader 432-task refinement began spending cycles on runaway high-valence cases. The cap records scientifically interesting threshold crossings without wasting compute on already-successful growth explosions.

### Result

All 48 focused tasks completed with `max_abs_ledger_error == 0`.

Best full-horizon candidates, not stopped early:

| Seed | kA | Vacuum | Valence | Initial active | Final tick | Final active | Depleted | Transfers | LCF_cube26 | Ledger error |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `56` | `5.0` | `2` | `8` | `16` | `2048` | `933` | `327` | `74604` | `0.123258` | `0` |
| `56` | `4.0` | `2` | `8` | `16` | `2048` | `961` | `327` | `65164` | `0.119667` | `0` |
| `56` | `6.0` | `2` | `8` | `16` | `2048` | `938` | `323` | `64649` | `0.121535` | `0` |
| `56` | `8.0` | `2` | `8` | `16` | `2048` | `898` | `322` | `67507` | `0.122494` | `0` |

Best threshold-crossing candidates, stopped at tick `4` after crossing `1000` active sites:

| Seed | kA | Vacuum | Valence | Initial active | Final active | Depleted | Transfers | LCF_cube26 | Ledger error |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `56` | `5.0` | `3` | `8` | `16` | `2091` | `231` | `3459` | `0.086561` | `0` |
| `56` | `4.0` | `3` | `8` | `16` | `2086` | `231` | `3392` | `0.084851` | `0` |
| `56` | `6.0` | `3` | `8` | `16` | `2095` | `227` | `3477` | `0.086396` | `0` |
| `56` | `8.0` | `3` | `8` | `16` | `2101` | `224` | `3487` | `0.086625` | `0` |

### Interpretation

The focused search identifies a stronger v0.2 basin than Finding 025:

- `valence = 8` dominates `valence = 6` in the focused region.
- `vacuum_amplitude = 2` gives slower full-horizon depletion fronts with hundreds of depleted cells and tens of thousands of transfers.
- `vacuum_amplitude = 3` crosses the active threshold almost immediately, so it is a growth-explosion regime rather than a comparable 2048-tick stability result.
- Seed `56` is stronger than seed `42` in the focused top rows.
- The ledger invariant remains exact across all focused tasks.

This is the first v0.2 result that looks like a useful search substrate: not open-ended complexity, but ledger-exact growth/depletion dynamics with tunable regimes. The next experiment should compare openness and second-order structure for the two regimes separately: `vacuum=2` as a full-horizon depletion front, and `vacuum=3` as a threshold-crossing burst.

### Artifacts

- `src/v02_parameter_search.py`
- `output/findings/finding_026_v02_focused_parameter_search.csv`
- `output/findings/finding_026_v02_focused_parameter_search.json`

## Finding 027: v0.2 Vacuum-2 Front Is Durable but Classification-Closed

### Status

Completed for the best full-horizon candidate from Finding 026.

### Setup

Candidate:

```text
seed = 56
amplitude_coupling = 5.0
vacuum_amplitude = 2
valence = 8
initial_active_iotas = 16
bond_probability = 1.0
ticks = 2048
```

Openness protocol:

```text
checkpoint_ticks = 0, 256, 512, 1024, 1536, 2048
horizon = 256
samples = 8
connectivity = cube26
commitment_epsilon = 0.05
```

### Openness Result

| Checkpoint | Base active | Base depleted | Mean future active | Mean future LCF_cube26 | Openness | Max ledger error |
|---:|---:|---:|---:|---:|---:|---:|
| `0` | `16` | `0` | `950.5` | `0.122447` | `0.0` | `0` |
| `256` | `931` | `327` | `931.625` | `0.123440` | `0.0` | `0` |
| `512` | `933` | `327` | `933.0` | `0.123258` | `0.0` | `0` |
| `1024` | `933` | `327` | `933.0` | `0.123258` | `0.0` | `0` |
| `1536` | `933` | `327` | `933.0` | `0.123258` | `0.0` | `0` |
| `2048` | `933` | `327` | `933.0` | `0.123258` | `0.0` | `0` |

All sampled futures classified as `protected`; there were no absorber or high-dominant outcomes. By the current three-class openness metric, the run is committed from tick `0`.

### Component and Depletion Structure

Final tick `2048`, `cube26`:

| Mask | Cells | Components | Largest | Top-5 coverage | Top-20 coverage | Size entropy |
|---|---:|---:|---:|---:|---:|---:|
| `active` | `933` | `16` | `115` | `0.568060` | `1.000000` | `3.638004` |
| `depleted` | `327` | `17` | `36` | `0.510703` | `1.000000` | `3.766586` |

Depletion adjacency at final tick:

- `868 / 933` active cells are cube26-adjacent to depleted cells (`0.930332`).
- `327 / 327` depleted cells are cube26-adjacent to active cells.
- `109 / 115` cells in the top active component are cube26-adjacent to depleted cells (`0.947826`).
- Top active component payload entropy is `0.0`; dominant payload fraction is `1.0`.
- Top active component vector entropy is low but nonzero at `0.072016`.

### Interpretation

This is not the hoped-for open-ended candidate. It is, however, the first clean v0.2 durable-front substrate worth keeping:

- it completes the horizon;
- it remains ledger-exact;
- it leaves a persistent depleted trace;
- it avoids absorber takeover;
- it stabilizes into a multi-component active/depleted mosaic.

The negative result is that future classification remains degenerate under the current outcome classes. The structure persists, but the future is not open by the current openness metric. The next scientific question is whether the metric is too coarse for within-class structural variation, or whether the substrate has simply stabilized into protected dust with depleted halos.

### Artifacts

- `output/findings/configs/v02_front_seed56_ka5_vac2_val8_n16.yaml`
- `output/findings/finding_027_v02_front_openness_seed56_ka5_vac2_val8_n16_raw.csv`
- `output/findings/finding_027_v02_front_openness_seed56_ka5_vac2_val8_n16_summary.csv`
- `output/findings/finding_027_v02_front_openness_seed56_ka5_vac2_val8_n16_summary.json`
- `output/findings/finding_027_v02_front_openness_seed56_ka5_vac2_val8_n16_states/`
- `output/findings/finding_027_v02_front_seed56_ka5_vac2_val8_n16_metrics.csv`
- `output/findings/finding_027_v02_front_seed56_ka5_vac2_val8_n16_structures.csv`
- `output/findings/finding_027_v02_front_seed56_ka5_vac2_val8_n16.json`
- `output/findings/finding_027_v02_front_seed56_ka5_vac2_val8_n16.npz`

## Finding 028: v0.2 Vacuum-3 Is a Threshold-Crossing Burst Regime

### Status

Completed as a boundary/control comparison for Finding 027.

### Setup

Candidate:

```text
seed = 56
amplitude_coupling = 5.0
vacuum_amplitude = 3
valence = 8
initial_active_iotas = 16
bond_probability = 1.0
stop_active_iotas = 1000
```

Openness protocol:

```text
checkpoint_ticks = 0, 1, 2, 3, 4
horizon = 4
samples = 8
connectivity = cube26
stop_active_iotas = 1000
```

### Openness Result

| Checkpoint | Base active | Base depleted | Mean future active | Mean future LCF_cube26 | Openness | Max ledger error |
|---:|---:|---:|---:|---:|---:|---:|
| `0` | `16` | `0` | `2078.875` | `0.087372` | `0.0` | `0` |
| `1` | `73` | `16` | `2093.25` | `0.086649` | `0.0` | `0` |
| `2` | `289` | `67` | `2091.5` | `0.086601` | `0.0` | `0` |
| `3` | `919` | `139` | `2094.125` | `0.086432` | `0.0` | `0` |
| `4` | `2091` | `231` | `3895.25` | `0.085296` | `0.0` | `0` |

All sampled futures classified as `protected`, but this should not be read as durable-front closure. The regime is an ignition regime: the system crosses the active threshold in the first few ticks.

### Component and Depletion Structure

Final capped tick `4`, `cube26`:

| Mask | Cells | Components | Largest | Top-5 coverage | Top-20 coverage | Size entropy |
|---|---:|---:|---:|---:|---:|---:|
| `active` | `2091` | `16` | `181` | `0.407939` | `1.000000` | `3.921881` |
| `depleted` | `231` | `28` | `20` | `0.367965` | `0.965368` | `4.262964` |

Compared with the vacuum-2 front, the burst has higher active count, smaller largest-component fraction, and much higher top-component payload/vector entropy:

- top active payload entropy is `0.999449`;
- top active vector entropy is `1.654705`;
- dominant payload fraction is only `0.513812`;
- `1462 / 2091` active cells are cube26-adjacent to depleted cells (`0.699187`).

### Interpretation

Vacuum `3` behaves as a threshold-crossing drive regime rather than a candidate durable-front regime. It is useful for locating the transition boundary, but not yet for open-ended structure claims. The right use of this regime is capped classification and phase-boundary mapping, not full-horizon evolution.

The contrast with vacuum `2` is the core result:

- vacuum `2`: full-horizon, ledger-exact, stable active/depleted mosaic, classification-closed;
- vacuum `3`: early explosive activation, ledger-exact, high-entropy burst, classification-closed by the coarse outcome metric.

### Artifacts

- `output/findings/configs/v02_burst_seed56_ka5_vac3_val8_n16.yaml`
- `output/findings/finding_028_v02_burst_openness_seed56_ka5_vac3_val8_n16_raw.csv`
- `output/findings/finding_028_v02_burst_openness_seed56_ka5_vac3_val8_n16_summary.csv`
- `output/findings/finding_028_v02_burst_openness_seed56_ka5_vac3_val8_n16_summary.json`
- `output/findings/finding_028_v02_burst_openness_seed56_ka5_vac3_val8_n16_states/`
- `output/findings/finding_028_v02_burst_seed56_ka5_vac3_val8_n16_metrics.csv`
- `output/findings/finding_028_v02_burst_seed56_ka5_vac3_val8_n16_structures.csv`
- `output/findings/finding_028_v02_burst_seed56_ka5_vac3_val8_n16.json`
- `output/findings/finding_028_v02_burst_seed56_ka5_vac3_val8_n16.npz`

## Finding 029: Morphology-Aware Openness Separates Fate Closure from Structural Variation

### Status

Completed. The openness instrument now reports both the original fate alphabet and a morphology-aware alphabet.

### Instrument Change

The original fate classifier is unchanged:

```text
absorber
high_dominant
protected
```

The morphology layer adds:

- a coarse `morphology_class`, such as `front_coupled` or `burst`;
- a binned `morphology_signature` over active count, depleted count, active/depleted adjacency, LCF, top-5 coverage, top-component payload entropy, and top-component vector entropy;
- sample-normalized entropy for both morphology class and morphology signature.

This keeps the old result honest while testing whether within-class structure remains variable.

### Vacuum-2 Front Result

Same candidate as Finding 027:

```text
seed = 56
amplitude_coupling = 5.0
vacuum_amplitude = 2
valence = 8
initial_active_iotas = 16
```

| Checkpoint | Fate openness | Morph class | Morph class openness | Morph signature openness | Effective signatures |
|---:|---:|---|---:|---:|---:|
| `0` | `0.0` | `front_coupled:8` | `0.0` | `0.432932` | `2.460233` |
| `256` | `0.0` | `front_coupled:8` | `0.0` | `0.0` | `1.0` |
| `512` | `0.0` | `front_coupled:8` | `0.0` | `0.0` | `1.0` |
| `1024` | `0.0` | `front_coupled:8` | `0.0` | `0.0` | `1.0` |
| `1536` | `0.0` | `front_coupled:8` | `0.0` | `0.0` | `1.0` |
| `2048` | `0.0` | `front_coupled:8` | `0.0` | `0.0` | `1.0` |

Interpretation: the initial state has multiple reachable front signatures, but by tick `256` the morphology signature has also closed. The durable front exists, but the sampled future collapses into the same morphology bin after early transients.

### Vacuum-3 Burst Control

Same candidate as Finding 028:

```text
seed = 56
amplitude_coupling = 5.0
vacuum_amplitude = 3
valence = 8
initial_active_iotas = 16
stop_active_iotas = 1000
```

| Checkpoint | Fate openness | Morph class | Morph class openness | Morph signature openness | Effective signatures |
|---:|---:|---|---:|---:|---:|
| `0` | `0.0` | `burst:8` | `0.0` | `0.520426` | `2.951152` |
| `1` | `0.0` | `burst:8` | `0.0` | `0.468546` | `2.649351` |
| `2` | `0.0` | `burst:8` | `0.0` | `0.318145` | `1.937819` |
| `3` | `0.0` | `burst:8` | `0.0` | `0.432932` | `2.460233` |
| `4` | `0.0` | `burst:8` | `0.0` | `0.333333` | `2.0` |

Interpretation: vacuum `3` remains fate-closed and morphology-class-closed, but it retains within-burst signature variability across the sampled early checkpoints. That supports treating it as a transition/ignition regime, not as a durable-front candidate.

### Interpretation

The disciplined conclusion is narrower and stronger:

```text
The form changed before the fate metric did.
```

v0.2 has not produced open-endedness under the original committor fate classifier. It has produced a ledger-exact active/depleted front class. The morphology-aware layer shows that the front candidate has early within-class variation, but that variation closes by tick `256` under the current bins and continuation horizon.

For claims:

- do claim `durable active/depleted front morphology`;
- do claim `ledger-exact structural regime distinct from absorber, protected dust, and burst`;
- do not claim `durable form without closed future`;
- do not claim `open-ended complexity`.

The next useful test is front turnover, not more broad fate sampling: track whether active/depleted interface cells are replaced over time despite stable aggregate morphology.

### Artifacts

- `src/openness_timeline.py`
- `src/v02_candidate_diagnostics.py`
- `output/findings/finding_029_v02_front_morphology_openness_seed56_ka5_vac2_val8_n16_raw.csv`
- `output/findings/finding_029_v02_front_morphology_openness_seed56_ka5_vac2_val8_n16_summary.csv`
- `output/findings/finding_029_v02_front_morphology_openness_seed56_ka5_vac2_val8_n16_summary.json`
- `output/findings/finding_029_v02_burst_morphology_openness_seed56_ka5_vac3_val8_n16_raw.csv`
- `output/findings/finding_029_v02_burst_morphology_openness_seed56_ka5_vac3_val8_n16_summary.csv`
- `output/findings/finding_029_v02_burst_morphology_openness_seed56_ka5_vac3_val8_n16_summary.json`

## Finding 030: v0.2 Front Geometry Pins While Amplitude Continues Cycling

### Status

Completed as the turnover check requested after Finding 029.

### Instrument Change

Added `src/front_turnover_diagnostic.py` to measure turnover directly rather than inferring it from aggregate morphology. The diagnostic samples:

- active/depleted mask retention and Jaccard turnover;
- active-interface and depleted-interface retention;
- active/depleted interface union turnover;
- content changes on persistent active cells and persistent active-interface cells;
- per-window transfer, failed-gate, and deactivation rates.

This separates three cases that looked similar under aggregate morphology:

```text
moving front
pinned front with internal cycling
frozen static residue
```

### Setup

Candidate:

```text
seed = 56
amplitude_coupling = 5.0
vacuum_amplitude = 2
valence = 8
initial_active_iotas = 16
bond_probability = 1.0
connectivity = cube26
```

Runs:

```text
full horizon turnover: ticks 0..2048, sample_every = 16
mid-horizon tick check: ticks 400..448, sample_every = 1
late-horizon tick check: ticks 2000..2048, sample_every = 1
```

### Full-Horizon Geometry Result

At 16-tick resolution:

| Metric | Value |
|---|---:|
| Final active cells | `933` |
| Final depleted cells | `327` |
| Final active-interface cells | `868` |
| Final depleted-interface cells | `327` |
| Depleted mask freeze tick | `32` |
| Active-interface freeze tick | `336` |
| Interface-union freeze tick | `336` |
| Active mask freeze tick | `416` |
| Full-front freeze tick | `416` |
| Final ledger error | `0` |

This is not a migrating/replacing front after stabilization. The geometry becomes pinned.

### Tick-Level Cycling Result

The 16-tick samples alias the internal cycle, so tick-level checks were required. In both `400..448` and `2000..2048`, after the geometry is pinned:

| Metric | Mid horizon | Late horizon |
|---|---:|---:|
| Active turnover fraction | `0.0` | `0.0` |
| Active-interface turnover fraction | `0.0` | `0.0` |
| Mean amplitude transfers / tick | `35.5` | `35.5` |
| Mean persistent-active changed fraction / tick | `0.059798` | `0.059977` |
| Mean persistent-interface changed fraction / tick | `0.064276` | `0.064468` |

At the final sampled tick:

- active Jaccard is `1.0`;
- active-interface Jaccard is `1.0`;
- amplitude transfers are `35` per tick;
- `56 / 933` persistent active cells change amplitude per tick (`0.060021`);
- `56 / 868` persistent active-interface cells change amplitude per tick (`0.064516`);
- there are no `R`, `V`, or `P` changes in the final tick-level window.

### Interpretation

The vacuum-2 candidate is not a moving durable front. It is a pinned active/depleted interface with ongoing internal amplitude circulation.

The disciplined claim is:

```text
v0.2 seed56 vacuum=2 produces a ledger-exact pinned front: morphology and cell identity close after stabilization, while amplitude continues cycling on a stable active/depleted scaffold.
```

This improves the interpretation from Finding 029:

- not open-ended under fate openness;
- not open-ended under morphology signature openness after tick `256`;
- not front-turnover open after stabilization;
- still not static residue, because amplitude transfer persists at roughly `35.5` transfers per tick.

The next test should not be more broad committor sampling. It should be a targeted search for the nearby regime where active/depleted geometry does not pin: vary vacuum, valence, and coupling around the vacuum-2 front while selecting for nonzero post-stabilization interface turnover without vacuum-3 ignition.

### Artifacts

- `src/front_turnover_diagnostic.py`
- `output/findings/finding_030_v02_front_turnover_seed56_ka5_vac2_val8_n16_turnover.csv`
- `output/findings/finding_030_v02_front_turnover_seed56_ka5_vac2_val8_n16_turnover_summary.json`
- `output/findings/finding_030_v02_front_turnover_seed56_ka5_vac2_val8_n16_tick400_448_turnover.csv`
- `output/findings/finding_030_v02_front_turnover_seed56_ka5_vac2_val8_n16_tick400_448_turnover_summary.json`
- `output/findings/finding_030_v02_front_turnover_seed56_ka5_vac2_val8_n16_tick2000_2048_turnover.csv`
- `output/findings/finding_030_v02_front_turnover_seed56_ka5_vac2_val8_n16_tick2000_2048_turnover_summary.json`

## Finding 031: Residual Participation Unpins the v0.2 Scaffold

### Status

Completed as the direct follow-up to Finding 030.

### Objective

Finding 030 showed that the vacuum-2 scaffold is not dead, but its topology pins. The useful next question was not more openness sampling. It was:

```text
what minimal law knob converts pinned scaffold flow into topology-changing turnover?
```

Two candidate perturbations were tested:

1. `secondary_vector_kick_probability`: successful secondary transfers can rotate the target vector state.
2. `residual_participation_probability`: successful secondary handshake attempts into residual/depleted boundary sites can donate one amplitude unit and bring the site back into the active interface.

Both are default-off. Both preserve the hard amplitude ledger.

The initial implementation and artifact filenames used the phrase `depleted_reactivation`. That name is too ontologically strong. The better interpretation is residual participation: the iota was not dead, it was excluded by the previous active-only update rule. The current implementation restores handshake eligibility at the active/depleted boundary. Full universal source-side participation by every residual iota remains a larger next law change.

### Instrument Change

Added default-off secondary-kick and residual-participation knobs to `src/iota_rig.py`:

```text
constants.secondary_vector_kick_probability
constants.secondary_vector_kick_offset
constants.secondary_vector_kick_preserve_behavior
constants.residual_participation_probability
constants.residual_participation_secondary_only
```

Backward-compatible aliases are accepted:

```text
constants.depleted_reactivation_probability
constants.depleted_reactivation_secondary_only
```

Added `src/v02_unpin_probe.py` to score candidate settings by post-stabilization active/interface turnover while rejecting ledger errors and burst-like early stops.

Updated `src/front_turnover_diagnostic.py` to report:

- `secondary_vector_kicks`;
- `residual_participations`;
- per-tick rates for both.

### Setup

Base candidate:

```text
seed = 56
amplitude_coupling = 5.0
vacuum_amplitude = 2
valence = 8
initial_active_iotas = 16
bond_probability = 1.0
connectivity = cube26
stop_active_iotas = 2500
```

Probe horizon:

```text
ticks = 768
sample_every = 8
tail_start_tick = 416
```

Validation horizon:

```text
ticks = 2048
sample_every = 16
tail_start_tick = 416
```

### Negative Result: Vector Kick Alone Is Not Enough

Secondary vector kicks were tested across mild, strong, and cross-behavior variants.

Best vector-only rows:

| Probe | Kick probability | Offset | Preserve behavior | Final active | Tail active-interface turnover | Tail vector-change fraction | Ledger error |
|---|---:|---:|---|---:|---:|---:|---:|
| mild | `0.05` | `3` | true | `974` | `0.000127` | `0.005314` | `0` |
| strong | `0.10` | `3` | true | `984` | `0.000101` | `0.004785` | `0` |
| cross-behavior | `0.05` | `7` | false | `983` | `0.000173` | `0.004354` | `0` |

Interpretation:

```text
vector kicks perturb direction state, but they do not meaningfully unpin topology.
```

This is the correction to the initial “secondary vector kick” idea. The scaffold is not pinned primarily because vectors lack small perturbations. It is pinned because depleted sites are absorbing walls.

### Positive Result: Residual Participation Is the Lever

At `768` ticks, residual participation produced a monotonic increase in post-stabilization interface turnover without triggering the `2500` active cap.

Selected rows:

| Residual participation probability | Vector kick probability | Final active | Final depleted | Tail active turnover | Tail active-interface turnover | Residual participations / tick | Ledger error |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `0.001` | `0.0` | `1004` | `324` | `0.002613` | `0.005330` | `0.133333` | `0` |
| `0.005` | `0.0` | `1025` | `320` | `0.012776` | `0.021614` | `0.694444` | `0` |
| `0.010` | `0.0` | `1022` | `316` | `0.023337` | `0.040130` | `1.411111` | `0` |
| `0.020` | `0.0` | `1022` | `314` | `0.039824` | `0.067897` | `2.841667` | `0` |
| `0.050` | `0.0` | `1017` | `321` | `0.057473` | `0.108449` | `6.188889` | `0` |
| `0.100` | `0.0` | `1020` | `333` | `0.071666` | `0.143184` | `12.113889` | `0` |
| `0.200` | `0.0` | `1013` | `327` | `0.081862` | `0.169744` | `21.866667` | `0` |

The vector kick was not needed. Adding `secondary_vector_kick_probability = 0.01` did not materially improve the residual-participation rows.

### 2048-Tick Validation

Residual-participation-only candidates remained ledger-exact and did not hit the active cap.

| Residual participation probability | Final active | Final depleted | Tail active turnover | Tail active-interface turnover | Residual participations / tick | Ledger error | Early stop |
|---:|---:|---:|---:|---:|---:|---:|---|
| `0.02` | `1025` | `318` | `0.051767` | `0.103051` | `2.809466` | `0` | none |
| `0.05` | `1017` | `328` | `0.066824` | `0.138324` | `6.188107` | `0` | none |
| `0.10` | `1021` | `332` | `0.080618` | `0.166727` | `12.307646` | `0` | none |
| `0.20` | `1013` | `331` | `0.084552` | `0.181078` | `21.333131` | `0` | none |

The smallest strong setting is `residual_participation_probability = 0.02`: it produces durable nonzero topology turnover through the full `2048`-tick horizon while staying near the original activity scale.

Detailed turnover for `residual_participation_probability = 0.02`:

| Metric | Value |
|---|---:|
| Final active cells | `1025` |
| Final depleted cells | `318` |
| Final active-interface cells | `846` |
| Final depleted-interface cells | `318` |
| Full-front freeze tick | none |
| Mean active turnover, 16-tick samples | `0.060864` |
| Mean active-interface turnover, 16-tick samples | `0.111472` |
| Cumulative new active cells | `4555` |
| Cumulative lost active cells | `3546` |
| Cumulative new active-interface cells | `6799` |
| Cumulative lost active-interface cells | `5953` |
| Final ledger error | `0` |

At tick `2048`, compared with tick `2032`:

- active turnover fraction is `0.053181`;
- active-interface turnover fraction is `0.094595`;
- depleted turnover fraction is `0.161850`;
- residual participations occur at `2.9375` per tick;
- deactivations also occur at `2.9375` per tick;
- amplitude transfers occur at `4.375` per tick;
- ledger error remains `0`.

The tick-level `2000..2048` check confirms that turnover persists late in the run:

- mean active turnover is `0.024973`;
- mean active-interface turnover is `0.029381`;
- final one-tick active-interface turnover is `0.012881`;
- final one-tick residual participation rate is `3.0` per tick.

### Interpretation

This is the actionable correction:

```text
The missing unpinning mechanism is not directional perturbation by itself. It is residual participation at the active/depleted boundary.
```

The original vacuum-2 scaffold pinned because the active-only update rule made depleted cells behave like permanent topological walls. Secondary-only residual participation reopens those wall sites to handshake without creating amplitude and without requiring vacuum-3 ignition. That produces topology-changing turnover while preserving the hard ledger.

The safe claim is:

```text
v0.2.1 residual participation converts the vacuum-2 pinned scaffold into a ledger-exact turnover scaffold: active/depleted geometry no longer freezes, while activity remains non-explosive through the tested horizon.
```

This is still not the full universal-participation ontology. In this implementation, residual participation is boundary-mediated: an active source can productively handshake with a residual/depleted target. The deeper law repair should preserve residual state on stranded iotas and allow low-capacity source-side participation from non-active sites. That is the next implementation boundary.

Do not yet claim open-ended complexity. The next required test is morphology-aware openness on the `residual_participation_probability = 0.02` candidate, followed by component/connectivity diagnostics. The current result only establishes that the previously missing ingredient, topology-changing turnover, can be recovered with a minimal conserved perturbation.

### Artifacts

- `src/iota_rig.py`
- `src/front_turnover_diagnostic.py`
- `src/v02_unpin_probe.py`
- `output/findings/finding_031_v02_secondary_kick_unpin_probe.csv`
- `output/findings/finding_031_v02_secondary_kick_unpin_probe.json`
- `output/findings/finding_031_v02_secondary_kick_unpin_probe_strong_preserve.csv`
- `output/findings/finding_031_v02_secondary_kick_unpin_probe_strong_preserve.json`
- `output/findings/finding_031_v02_secondary_kick_unpin_probe_cross_behavior.csv`
- `output/findings/finding_031_v02_secondary_kick_unpin_probe_cross_behavior.json`
- `output/findings/finding_031_v02_depleted_reactivation_unpin_probe.csv`
- `output/findings/finding_031_v02_depleted_reactivation_unpin_probe.json`
- `output/findings/finding_031_v02_depleted_reactivation_unpin_probe_2048.csv`
- `output/findings/finding_031_v02_depleted_reactivation_unpin_probe_2048.json`
- `output/findings/finding_031_v02_depleted_reactivation0p02_turnover_seed56_ka5_vac2_val8_n16_turnover.csv`
- `output/findings/finding_031_v02_depleted_reactivation0p02_turnover_seed56_ka5_vac2_val8_n16_turnover_summary.json`
- `output/findings/finding_031_v02_depleted_reactivation0p02_tick2000_2048_seed56_ka5_vac2_val8_n16_turnover.csv`
- `output/findings/finding_031_v02_depleted_reactivation0p02_tick2000_2048_seed56_ka5_vac2_val8_n16_turnover_summary.json`

## Finding 032: Residual Participation Creates Turnover, Not Open Futures

### Status

Completed for the `residual_participation_probability = 0.02` candidate identified in Finding 031.

### Setup

Candidate:

```text
seed = 56
amplitude_coupling = 5.0
vacuum_amplitude = 2
valence = 8
initial_active_iotas = 16
bond_probability = 1.0
residual_participation_probability = 0.02
residual_participation_secondary_only = true
```

Openness protocol:

```text
checkpoint_ticks = 0, 256, 512, 1024, 1536, 2048
horizon = 256
samples = 8
connectivity = cube26
with_morphology = true
```

### Openness Result

| Checkpoint | Base active | Base depleted | Mean future active | Fate openness | Morph class openness | Morph signature openness | Morph class | Max ledger error |
|---:|---:|---:|---:|---:|---:|---:|---|---:|
| `0` | `16` | `0` | `1015.375` | `0.0` | `0.0` | `0.0` | `front_coupled:8` | `0` |
| `256` | `1016` | `318` | `1021.000` | `0.0` | `0.0` | `0.0` | `front_coupled:8` | `0` |
| `512` | `1020` | `320` | `1022.750` | `0.0` | `0.0` | `0.0` | `front_coupled:8` | `0` |
| `1024` | `1023` | `320` | `1023.750` | `0.0` | `0.0` | `0.0` | `front_coupled:8` | `0` |
| `1536` | `1024` | `319` | `1024.000` | `0.0` | `0.0` | `0.0` | `front_coupled:8` | `0` |
| `2048` | `1025` | `318` | `1025.000` | `0.0` | `0.0` | `0.0` | `front_coupled:8` | `0` |

All futures remain classified as `protected`, and all morphology samples share the same binned signature:

```text
front_coupled|1000-1999|128-511|0.8-0.9|0.1-0.2|0.5-0.6|0|0
```

### Structural Result

Final tick `2048`:

| Metric | Value |
|---|---:|
| Active cells | `1025` |
| Depleted cells | `318` |
| Total A | `524329` |
| Active A | `2727` |
| Latent A | `521602` |
| Ledger error | `0` |
| Amplitude transfers | `2392` |
| Failed transfer gates | `100864` |
| Deactivation events | `1414` |
| Residual participations | `1415` |

Final `cube26` structure:

| Mask | Cells | Components | Largest | Top-5 coverage | Top-20 coverage | Size entropy |
|---|---:|---:|---:|---:|---:|---:|
| `active` | `1025` | `16` | `131` | `0.587317` | `1.000000` | `3.597774` |
| `depleted` | `318` | `18` | `36` | `0.500000` | `1.000000` | `3.804556` |

Final adjacency:

- `846 / 1025` active cells are cube26-adjacent to depleted cells (`0.825366`).
- `318 / 318` depleted cells are cube26-adjacent to active cells.
- `88 / 131` cells in the top active component are adjacent to depleted cells (`0.671756`).
- Top active payload entropy is `0.0`.
- Top active vector entropy is `0.0`.

### Interpretation

Residual participation fixed the specific defect found in Finding 030: the interface no longer pins. Finding 031 showed durable post-stabilization topology turnover.

Finding 032 adds the negative result:

```text
topology-changing turnover is not sufficient to create morphology-open futures under the current classifier.
```

The system is now a ledger-exact turnover scaffold, not a pinned scaffold. But the sampled futures still collapse to the same fate class and the same morphology signature. The strongest disciplined claim is:

```text
Residual participation restores interface turnover while preserving ledger exactness, but it does not yet produce measurable open-endedness or morphology-class diversification.
```

The current morphology alphabet is also too coarse to see identity turnover directly. It bins aggregate active count, depleted count, adjacency, component coverage, and top-component content. Those bins stay fixed even though Finding 031 showed active/interface cell replacement. The next openness layer should include turnover-aware signatures, not just final aggregate morphology.

### Next Test

Do not broaden parameter search yet. The next targeted test is:

```text
turnover-aware openness
```

For each continuation, classify futures by:

- active-interface turnover fraction;
- depleted turnover fraction;
- residual participations per tick;
- deactivation/residual-participation balance;
- whether turnover persists, decays, or grows across the continuation horizon.

That asks the right question:

```text
from this state, how many distinct turnover regimes remain reachable?
```

### Artifacts

- `output/findings/configs/v021_residual_participation_seed56_ka5_vac2_val8_n16_rpp0p02.yaml`
- `output/findings/finding_032_v021_residual_participation_morphology_openness_seed56_ka5_vac2_val8_n16_rpp0p02_raw.csv`
- `output/findings/finding_032_v021_residual_participation_morphology_openness_seed56_ka5_vac2_val8_n16_rpp0p02_summary.csv`
- `output/findings/finding_032_v021_residual_participation_morphology_openness_seed56_ka5_vac2_val8_n16_rpp0p02_summary.json`
- `output/findings/finding_032_v021_residual_participation_seed56_ka5_vac2_val8_n16_rpp0p02_metrics.csv`
- `output/findings/finding_032_v021_residual_participation_seed56_ka5_vac2_val8_n16_rpp0p02_structures.csv`
- `output/findings/finding_032_v021_residual_participation_seed56_ka5_vac2_val8_n16_rpp0p02.json`
- `output/findings/finding_032_v021_residual_participation_seed56_ka5_vac2_val8_n16_rpp0p02.npz`

## Finding 033: Residual Turnover Lacks Rotational Recursion

### Status

Completed for the `residual_participation_probability = 0.02` candidate.

### Setup

Candidate:

```text
seed = 56
amplitude_coupling = 5.0
vacuum_amplitude = 2
valence = 8
initial_active_iotas = 16
bond_probability = 1.0
residual_participation_probability = 0.02
residual_participation_secondary_only = true
```

Diagnostic:

```text
rotational recursion
connectivity = cube26
late window = tick 2000 through tick 2048, sampled every tick
coarse horizon = tick 0 through tick 2048, sampled every 128 ticks
candidate targets = transfer-eligible targets, respecting secondary-only residual participation
```

The diagnostic measures:

- persistent-cell `V` transition rates and changed-transition entropy;
- active/interface vector entropy and dominant-vector fraction;
- new-active vector entropy and source-vector match fraction;
- transfer-eligible candidate-neighborhood turnover for persistent active/interface cells;
- aggregate active/interface candidate-target turnover;
- interface radial/tangential alignment against the depleted boundary.

### Late-Regime Result

For the stabilized late window, tick `2000` through tick `2048`:

| Metric | Value |
|---|---:|
| Rows | `48` |
| Mean active turnover fraction | `0.004700` |
| Mean active-interface turnover fraction | `0.009159` |
| Mean residual participations per tick | `2.416667` |
| Mean deactivation events per tick | `2.416667` |
| Mean persistent-active `V` changed fraction | `0.000000` |
| Mean persistent-interface `V` changed fraction | `0.000000` |
| Max persistent-active `V` changed fraction | `0.000000` |
| Max persistent-interface `V` changed fraction | `0.000000` |
| Mean persistent-active changed-transition entropy | `0.000000` |
| Mean persistent-interface changed-transition entropy | `0.000000` |
| Mean active vector entropy | `0.011164` |
| Mean active-interface vector entropy | `0.011618` |
| Mean new-active vector entropy | `0.000000` |
| Mean active dominant-vector fraction | `0.999024` |
| Mean active-interface dominant-vector fraction | `0.998959` |
| Mean new-active source-vector match fraction | `0.958333` |
| Mean persistent-active candidate turnover | `0.000026` |
| Mean persistent-interface candidate turnover | `0.000031` |
| Mean active candidate-target turnover | `0.018606` |
| Mean active-interface candidate-target turnover | `0.021732` |

Final one-tick row, tick `2047` to tick `2048`:

| Metric | Value |
|---|---:|
| Active cells | `1025` |
| Depleted cells | `318` |
| Active-interface cells | `846` |
| Active new / lost cells | `3 / 3` |
| Active-interface new / lost cells | `3 / 8` |
| Persistent active cells | `1022` |
| Persistent interface cells | `843` |
| Persistent active `V` changed fraction | `0.000000` |
| Persistent interface `V` changed fraction | `0.000000` |
| Persistent active candidate turnover | `0.000000` |
| Persistent interface candidate turnover | `0.000000` |
| New-active source-vector match fraction | `1.000000` |

### Coarse Full-Horizon Result

The full horizon confirms that turnover exists, but rotational phase change does not persist.

For tick `0` through tick `2048`, sampled every `128` ticks:

| Metric | Value |
|---|---:|
| Rows | `16` |
| Mean active turnover fraction | `0.145804` |
| Mean active-interface turnover fraction | `0.240469` |
| Mean residual participations per tick | `2.889648` |
| Mean deactivation events per tick | `3.044922` |
| Mean persistent-active `V` changed fraction | `0.062564` |
| Mean persistent-interface `V` changed fraction | `0.000083` |
| Max persistent-interface `V` changed fraction | `0.001330` |
| Mean persistent-interface changed-transition entropy | `0.000000` |
| Mean active-interface vector entropy | `0.009016` |
| Mean active-interface dominant-vector fraction | `0.999193` |
| Mean persistent-interface candidate turnover | `0.000127` |

The final coarse window, tick `1920` to tick `2048`, still has active-interface turnover fraction `0.183957`, but persistent-interface `V` changed fraction remains `0.000000` and persistent-interface candidate turnover remains only `0.000291`.

### Interpretation

Finding 031 showed that residual participation restores topology-changing turnover. Finding 032 showed that this turnover does not create morphology-open futures. Finding 033 identifies the mechanism-level reason:

```text
residual participation creates recursive re-entry, but the re-entry is canalized into the same directional channel.
```

This candidate is therefore not rotational recursion. It is recurrent replacement on a nearly fixed vector field:

- active/interface cells continue to enter and leave;
- deactivation and residual participation remain balanced late in the run;
- persistent active/interface sites do not rotate their `V` state;
- new active sites are almost always re-entering through the source vector channel;
- persistent-cell candidate neighborhoods are effectively unchanged.

The important separation is:

```text
residual participation supplies re-entry;
rotation is still missing.
```

The aggregate candidate-target sets do move because membership turns over. But the persistent local grammar does not rewrite itself. That is why the system can keep replacing cells without opening a new morphology class.

### Next Test

The next disciplined v0.3 lever is not a broad random kick. It should be a minimal history-coupled rotational update:

```text
on successful received influence, rotate target V as a bounded function of incoming V, target residual state, payload compatibility, and whether the transfer was secondary/residual-mediated.
```

The required counters for that test are:

- `rotation_events`;
- `rotation_events_on_residual_entry`;
- `rotation_events_on_secondary_exchange`;
- `persistent_active_v_changed_fraction`;
- `persistent_interface_v_changed_fraction`;
- `persistent_active_changed_transition_entropy`;
- `persistent_interface_changed_transition_entropy`;
- candidate-neighborhood turnover for persistent active/interface cells.

The acceptance criterion is not simply more activity. The first bar is:

```text
late-time residual turnover plus nonzero persistent-interface V transition entropy plus nonzero persistent-interface candidate-neighborhood turnover, without ledger error or explosive active growth.
```

### Artifacts

- `src/rotational_recursion_diagnostic.py`
- `output/findings/finding_033_v021_residual_participation_rotational_recursion_tick2000_2048_seed56_ka5_vac2_val8_n16_rpp0p02_rows.csv`
- `output/findings/finding_033_v021_residual_participation_rotational_recursion_tick2000_2048_seed56_ka5_vac2_val8_n16_rpp0p02_summary.json`
- `output/findings/finding_033_v021_residual_participation_rotational_recursion_fullhorizon_seed56_ka5_vac2_val8_n16_rpp0p02_rows.csv`
- `output/findings/finding_033_v021_residual_participation_rotational_recursion_fullhorizon_seed56_ka5_vac2_val8_n16_rpp0p02_summary.json`

## Finding 034: History-Coupled Rotation Creates Directional Recursion

### Status

Completed for the v0.3 targeted repair of the `residual_participation_probability = 0.02` candidate.

### Law Change

The v0.3 lever is default-off and only active when configured:

```text
received_rotation_probability = 1.0
received_rotation_max_offset = 3
received_rotation_preserve_behavior = true
received_rotation_residual_multiplier = 1.0
received_rotation_secondary_multiplier = 1.0
secondary_vector_kick_probability = 0.0
```

On successful received influence, the target vector state is rotated by a bounded offset computed from:

- incoming source `V`;
- source payload;
- target previous `A/R/V/P`;
- candidate order;
- whether the target was depleted;
- transfer influence.

This is not the earlier broad secondary kick. Rotation is tied to successful receipt and is deterministic conditional on local interaction state, with the probability knob only controlling whether the received interaction applies the update.

### Setup

Candidate:

```text
seed = 56
amplitude_coupling = 5.0
vacuum_amplitude = 2
valence = 8
initial_active_iotas = 16
bond_probability = 1.0
residual_participation_probability = 0.02
residual_participation_secondary_only = true
received_rotation_probability = 1.0
received_rotation_max_offset = 3
```

Diagnostics:

```text
front turnover: tick 0 through tick 2048, sampled every 128 ticks
rotational recursion: tick 0 through tick 2048, sampled every 128 ticks
late rotational recursion: tick 2000 through tick 2048, sampled every tick
structure: tick 0 through tick 2048, sampled every 256 ticks
stop_active_iotas = 5000
```

The run completed the full `2048`-tick horizon without triggering the `5000` active-cell stop.

### Structural Result

Final tick `2048`:

| Metric | Value |
|---|---:|
| Active cells | `1061` |
| Depleted cells | `468` |
| Active A | `3099` |
| Latent A | `521230` |
| Total A | `524329` |
| Ledger error | `0` |
| cube26 active components | `16` |
| cube26 largest component | `143` |
| cube26 top-5 coverage | `0.608860` |
| cube26 active component entropy | `3.571366` |
| cube26 active/depleted adjacency | `0.959472` |
| cube26 depleted/active adjacency | `1.000000` |
| Top active vector entropy | `1.728475` |

Full-horizon event totals from the `128`-tick turnover windows:

| Event | Count |
|---|---:|
| Amplitude transfers | `8256` |
| Failed transfer gates | `281949` |
| Deactivation events | `4565` |
| Residual participations | `4097` |
| Rotation events | `8256` |
| Rotation events on residual entry | `4097` |
| Rotation events on secondary exchange | `7421` |

### Coarse Rotational Result

For tick `0` through tick `2048`, sampled every `128` ticks:

| Metric | v0.2.1 residual | v0.3 history rotation |
|---|---:|---:|
| Mean active turnover fraction | `0.145804` | `0.122885` |
| Mean active-interface turnover fraction | `0.240469` | `0.171363` |
| Mean residual participations per tick | `2.889648` | `2.000488` |
| Mean rotation events per tick | `0.000000` | `4.031250` |
| Mean persistent-active `V` changed fraction | `0.062564` | `0.020498` |
| Mean persistent-interface `V` changed fraction | `0.000083` | `0.022662` |
| Mean persistent-interface changed-transition entropy | `0.000000` | `3.733349` |
| Mean active vector entropy | `0.014674` | `1.898864` |
| Mean active-interface vector entropy | `0.009016` | `1.907597` |
| Mean new-active vector entropy | `0.001298` | `2.048572` |
| Mean new-active source-vector match fraction | `0.685340` | `0.150824` |
| Mean persistent-interface candidate turnover | `0.000127` | `0.004468` |
| Mean active-interface candidate-target turnover | `0.363375` | `0.544875` |

The final coarse window, tick `1920` to tick `2048`, has:

| Metric | Value |
|---|---:|
| Active-interface turnover fraction | `0.078302` |
| Persistent-interface `V` changed fraction | `0.010235` |
| Persistent-interface changed-transition entropy | `3.121928` |
| Persistent-interface candidate turnover | `0.002080` |
| Active-interface candidate-target turnover | `0.516667` |

### Late-Regime Result

For the stabilized late window, tick `2000` through tick `2048`, sampled every tick:

| Metric | Value |
|---|---:|
| Mean active turnover fraction | `0.003017` |
| Mean active-interface turnover fraction | `0.004587` |
| Mean residual participations per tick | `1.583333` |
| Mean deactivation events per tick | `1.604167` |
| Mean rotation events per tick | `1.875000` |
| Mean rotation events on residual entry per tick | `1.583333` |
| Mean rotation events on secondary exchange per tick | `1.833333` |
| Mean persistent-active `V` changed fraction | `0.000256` |
| Mean persistent-interface `V` changed fraction | `0.000265` |
| Max persistent-interface `V` changed fraction | `0.001967` |
| Mean persistent-interface changed-transition entropy | `0.062500` |
| Mean active vector entropy | `1.794429` |
| Mean active-interface vector entropy | `1.796596` |
| Mean new-active vector entropy | `0.380971` |
| Mean new-active source-vector match fraction | `0.393750` |
| Mean persistent-interface candidate turnover | `0.000063` |
| Mean active-interface candidate-target turnover | `0.053940` |

Final one-tick row, tick `2047` to tick `2048`:

| Metric | Value |
|---|---:|
| Active cells | `1061` |
| Depleted cells | `468` |
| Active-interface cells | `1018` |
| Active new / lost cells | `2 / 2` |
| Active-interface new / lost cells | `2 / 2` |
| Rotation events | `3` |
| Rotation events on residual entry | `2` |
| Rotation events on secondary exchange | `3` |
| Persistent interface `V` changed fraction | `0.000984` |
| Persistent interface candidate turnover | `0.000219` |
| Active candidate-target turnover | `0.100457` |

### Interpretation

Finding 034 passes the first v0.3 acceptance gate:

```text
late-time residual turnover plus nonzero persistent-interface V transition entropy plus nonzero persistent-interface candidate-neighborhood turnover, without ledger error or explosive active growth.
```

The important mechanism-level change is not larger active count. Final active count only rises from `1025` to `1061`. The change is directional:

- top active vector entropy rises from `0.0` to `1.728475`;
- late active/interface vector entropy stays around `1.79`;
- new active source-vector match falls from `0.958333` late in v0.2.1 to `0.393750` late in v0.3;
- persistent-interface `V` transitions are no longer exactly zero;
- persistent-interface candidate neighborhoods now change, even if weakly in the one-tick late window.

The disciplined claim is:

```text
history-coupled received rotation converts residual re-entry from canalized replacement into weak directional recursion.
```

This is still not an open-endedness claim. The late one-tick rotational signal is real but small. The strong signal appears over `128`-tick windows, where persistent-interface `V` transition entropy and candidate-neighborhood turnover are clearly nonzero. That means v0.3 has the missing local mechanism, but the next test must determine whether it creates distinct reachable future regimes rather than only richer local cycling.

### Next Test

Do not broaden the global search yet. The next test should be:

```text
turnover-aware and rotation-aware openness for the v0.3 history-rotation candidate
```

Classify continuations by:

- persistent-interface `V` changed fraction;
- persistent-interface changed-transition entropy;
- persistent-interface candidate turnover;
- active/interface turnover;
- residual participation and deactivation balance;
- rotation events on residual entry;
- active-interface candidate-target turnover;
- final active/depleted structure.

That asks whether the new directional recursion creates multiple structured futures, not merely a richer deterministic-looking scaffold.

### Artifacts

- `src/iota_rig.py`
- `src/front_turnover_diagnostic.py`
- `src/rotational_recursion_diagnostic.py`
- `src/v02_candidate_diagnostics.py`
- `src/v02_parameter_search.py`
- `src/v02_unpin_probe.py`
- `src/experiment_runner.py`
- `output/findings/configs/v030_history_rotation_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3.yaml`
- `output/findings/finding_034_v030_history_rotation_front_turnover_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_turnover.csv`
- `output/findings/finding_034_v030_history_rotation_front_turnover_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_turnover_summary.json`
- `output/findings/finding_034_v030_history_rotation_rotational_recursion_fullhorizon_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_rows.csv`
- `output/findings/finding_034_v030_history_rotation_rotational_recursion_fullhorizon_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_summary.json`
- `output/findings/finding_034_v030_history_rotation_rotational_recursion_tick2000_2048_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_rows.csv`
- `output/findings/finding_034_v030_history_rotation_rotational_recursion_tick2000_2048_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_summary.json`
- `output/findings/finding_034_v030_history_rotation_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_metrics.csv`
- `output/findings/finding_034_v030_history_rotation_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_structures.csv`
- `output/findings/finding_034_v030_history_rotation_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3.json`
- `output/findings/finding_034_v030_history_rotation_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3.npz`

## Finding 035: Rotation-Aware Openness Detects Bounded Directional Plurality

### Status

Completed for the v0.3 history-rotation candidate, with the v0.2.1 residual-participation candidate as control.

### Protocol

Rotation-aware openness protocol:

```text
checkpoint_ticks = 0, 512, 1024, 1536, 2048
horizon = 256
samples = 8
connectivity = cube26
rotation_sample_every = 16
late_window = 128
stop_active_iotas = 5000
workers = 8
```

The classifier records the old fate label, but classifies rotation-aware futures separately using:

- late rotation events per tick;
- late persistent-interface `V` changed fraction;
- late persistent-interface changed-transition entropy;
- late persistent-interface candidate-neighborhood turnover;
- late active-interface turnover;
- late active-interface candidate-target turnover;
- vector distribution distance from checkpoint;
- new active vector-state count;
- ledger exactness and non-runaway status.

Rotation-aware classes:

```text
rotation_dead
canalized_rotation
directional_drift
rotational_branching
rotational_ignition
rotational_collapse
ledger_violation
```

### v0.3 Result

All v0.3 continuations were bounded, ledger-exact, and non-runaway. The old fate classifier remained closed:

```text
protected:8 at every checkpoint
```

Rotation-aware result:

| Checkpoint | Bounded | Rotation classes | Class openness | Signature openness | Late rotations/tick | Interface `V` change | Transition entropy | Interface candidate turnover |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `0` | `8/8` | `rotational_branching:8` | `0.000000` | `0.181188` | `4.421875` | `0.017565` | `3.659313` | `0.003876` |
| `512` | `8/8` | `rotational_branching:8` | `0.000000` | `0.750000` | `3.019965` | `0.010477` | `2.978736` | `0.002254` |
| `1024` | `8/8` | `rotational_branching:8` | `0.000000` | `0.916667` | `2.184028` | `0.006687` | `2.425145` | `0.001394` |
| `1536` | `8/8` | `directional_drift:5; rotational_branching:3` | `0.318145` | `0.916667` | `1.676215` | `0.004660` | `1.959884` | `0.001088` |
| `2048` | `8/8` | `directional_drift:7; rotational_branching:1` | `0.181188` | `0.801880` | `1.676215` | `0.004556` | `1.868088` | `0.000934` |

The mature checkpoints are the key result. At ticks `1536` and `2048`, independent continuations split between `directional_drift` and `rotational_branching` while every sample remains:

```text
ledger-exact
bounded below the 5000 active-cell stop
old-classifier protected
structurally active/depleted
```

This is the first positive openness result under a classifier that measures the new mechanism rather than only the old terminal fate.

### v0.2.1 Control

The v0.2.1 residual-participation control remains rotation-dead in the mature regime:

| Checkpoint | Bounded | Rotation classes | Class openness | Late rotations/tick | Interface `V` change | Transition entropy | Interface candidate turnover |
|---:|---:|---|---:|---:|---:|---:|---:|
| `1024` | `8/8` | `rotation_dead:8` | `0.000000` | `0.000000` | `0.000000` | `0.000000` | `0.000166` |
| `1536` | `8/8` | `rotation_dead:8` | `0.000000` | `0.000000` | `0.000000` | `0.000000` | `0.000160` |
| `2048` | `8/8` | `rotation_dead:8` | `0.000000` | `0.000000` | `0.000000` | `0.000000` | `0.000152` |

The control has nonzero rotation-signature entropy because residual turnover still creates small variations in non-rotational bins. That is the caveat:

```text
signature openness alone is not sufficient.
```

The mechanistic discriminator is the combination of nonzero late rotation events, nonzero persistent-interface `V` transition entropy, and nonzero candidate-neighborhood turnover. v0.3 has all three; mature v0.2.1 has none of the first two and only negligible candidate-neighborhood change.

### Interpretation

Finding 035 changes the claim again:

```text
v0.3 does not yet establish open-ended complexity, but it does establish bounded rotation-aware future plurality.
```

The old outcome alphabet still says every v0.3 future is `protected`. That is true but incomplete. Under the rotation-aware alphabet, futures from mature checkpoints branch into distinct directional regimes while remaining ledger-exact and non-runaway.

The strongest disciplined formulation is:

```text
History-coupled rotation creates bounded directional plurality: independent continuations from the same mature scaffold remain old-classifier closed, but diverge into distinct rotation-aware futures with persistent interface vector change and nonzero transition entropy.
```

This is not a claim of open-ended complexity because the horizon is still short, the sample count is small, and the futures remain within a bounded active/depleted scaffold. It is a claim that the future is no longer directionally singular under the mechanism-aware classifier.

### Next Test

The next gate should not be a broad parameter sweep. It should be a targeted robustness check:

```text
rotation-aware openness sensitivity over received_rotation_probability and received_rotation_max_offset
```

Minimal grid:

```text
received_rotation_probability = 0.25, 0.5, 1.0
received_rotation_max_offset = 1, 2, 3
checkpoint_ticks = 1024, 1536, 2048
horizon = 256
samples = 8
```

Acceptance criterion:

```text
nonzero rotation-aware class or mechanism-signature openness among bounded, ledger-exact, non-runaway futures, with mature v0.2.1 remaining rotation-dead under the same classifier.
```

### Artifacts

- `src/rotation_aware_openness.py`
- `output/findings/finding_035_v030_history_rotation_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_raw.csv`
- `output/findings/finding_035_v030_history_rotation_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_summary.csv`
- `output/findings/finding_035_v030_history_rotation_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_summary.json`
- `output/findings/finding_035_v030_history_rotation_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_states/checkpoint_tick_000000.npz`
- `output/findings/finding_035_v030_history_rotation_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_states/checkpoint_tick_000512.npz`
- `output/findings/finding_035_v030_history_rotation_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_states/checkpoint_tick_001024.npz`
- `output/findings/finding_035_v030_history_rotation_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_states/checkpoint_tick_001536.npz`
- `output/findings/finding_035_v030_history_rotation_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_states/checkpoint_tick_002048.npz`
- `output/findings/finding_035_v021_residual_participation_rotation_aware_openness_control_seed56_ka5_vac2_val8_n16_rpp0p02_raw.csv`
- `output/findings/finding_035_v021_residual_participation_rotation_aware_openness_control_seed56_ka5_vac2_val8_n16_rpp0p02_summary.csv`
- `output/findings/finding_035_v021_residual_participation_rotation_aware_openness_control_seed56_ka5_vac2_val8_n16_rpp0p02_summary.json`
- `output/findings/finding_035_v021_residual_participation_rotation_aware_openness_control_seed56_ka5_vac2_val8_n16_rpp0p02_states/checkpoint_tick_000000.npz`
- `output/findings/finding_035_v021_residual_participation_rotation_aware_openness_control_seed56_ka5_vac2_val8_n16_rpp0p02_states/checkpoint_tick_000512.npz`
- `output/findings/finding_035_v021_residual_participation_rotation_aware_openness_control_seed56_ka5_vac2_val8_n16_rpp0p02_states/checkpoint_tick_001024.npz`
- `output/findings/finding_035_v021_residual_participation_rotation_aware_openness_control_seed56_ka5_vac2_val8_n16_rpp0p02_states/checkpoint_tick_001536.npz`
- `output/findings/finding_035_v021_residual_participation_rotation_aware_openness_control_seed56_ka5_vac2_val8_n16_rpp0p02_states/checkpoint_tick_002048.npz`

## Finding 036: Directional Branching Is Real but Not Yet Persistent Lineage Diversification

### Status

Completed for mature v0.3 checkpoints, with the v0.2.1 residual-participation candidate as control.

### Protocol

Branch-lineage protocol:

```text
checkpoint_ticks = 1536, 2048
horizon = 512
phase_length = 256
samples = 8
sample_every = 16
connectivity = cube26
stop_active_iotas = 5000
cluster_distance_threshold = 0.55
```

For each continuation:

1. Split the `512`-tick continuation into two `256`-tick phases.
2. Build persistent-interface `V -> V` transition matrices for each phase.
3. Cluster phase matrices by Jensen-Shannon distance.
4. Track phase-1 family to phase-2 family transitions.
5. Compare rotation events, interface turnover, candidate-neighborhood turnover, and component deltas by family.

### v0.3 Result

All v0.3 lineages were bounded, ledger-exact, and non-runaway.

| Checkpoint | Combined families | Phase-1 families | Phase-2 families | Same-family fraction | Lineage table | Phase matrix distance | Phase-1 rotations/tick | Phase-2 rotations/tick |
|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `1536` | `3` | `1` | `3` | `0.75` | `0->0:6; 0->1:1; 0->2:1` | `0.588655` | `1.637695` | `1.667480` |
| `2048` | `3` | `1` | `3` | `0.75` | `0->0:6; 0->1:1; 0->2:1` | `0.600318` | `1.649902` | `1.604492` |

Mechanism metrics:

| Checkpoint | Phase | Interface `V` change | Transition entropy | Candidate turnover | Interface turnover | Candidate-target turnover |
|---:|---|---:|---:|---:|---:|---:|
| `1536` | phase 1 | `0.004801` | `2.004995` | `0.001082` | `0.037666` | `0.316142` |
| `1536` | phase 2 | `0.004649` | `1.914247` | `0.000956` | `0.037822` | `0.350595` |
| `2048` | phase 1 | `0.004718` | `1.888604` | `0.000971` | `0.038147` | `0.347575` |
| `2048` | phase 2 | `0.004462` | `1.916288` | `0.000911` | `0.037246` | `0.356645` |

Component-level result:

```text
phase1_mean_component_count_delta = 0
phase2_mean_component_count_delta = 0
phase1_mean_largest_component_delta = 0
phase2_mean_largest_component_delta = 0
```

So the branch-lineage signal is directional, not yet morphological.

### Family Details

At checkpoint `1536`, phase 1 is one shared transition family:

```text
family 0, size 8
transition_count = 612
transition_families = 96
top transitions = 2>3:50; 1>2:49; 1>3:41; 2>4:30; 3>5:30
```

Phase 2 splits into three families:

```text
family 0, size 6, transition_count = 436, transition_families = 96
family 1, size 1, transition_count = 78, transition_families = 40
family 2, size 1, transition_count = 82, transition_families = 44
```

At checkpoint `2048`, the same pattern repeats:

```text
phase 1: family 0, size 8
phase 2: family 0, size 6; family 1, size 1; family 2, size 1
```

This is a real split, but it is weak:

```text
mean_within_family_distance = 0.568091 at tick 1536, 0.574920 at tick 2048
mean_between_family_distance = 0.607178 at tick 1536, 0.631310 at tick 2048
```

The between-family distance is larger than the within-family distance, but not by enough to claim robust separated lineages.

### v0.2.1 Control

The control remains a single zero-transition family.

| Checkpoint | Combined families | Phase-1 families | Phase-2 families | Same-family fraction | Lineage table | Phase matrix distance | Phase-1 rotations/tick | Phase-2 rotations/tick |
|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `1536` | `1` | `1` | `1` | `1.0` | `0->0:8` | `0.000000` | `0.000000` | `0.000000` |
| `2048` | `1` | `1` | `1` | `1.0` | `0->0:8` | `0.000000` | `0.000000` | `0.000000` |

Control mechanism metrics:

| Checkpoint | Phase | Interface `V` change | Transition entropy | Candidate turnover | Interface turnover | Candidate-target turnover |
|---:|---|---:|---:|---:|---:|---:|
| `1536` | phase 1 | `0.000000` | `0.000000` | `0.000182` | `0.102294` | `0.195956` |
| `1536` | phase 2 | `0.000000` | `0.000000` | `0.000155` | `0.101145` | `0.192329` |
| `2048` | phase 1 | `0.000000` | `0.000000` | `0.000185` | `0.100498` | `0.196879` |
| `2048` | phase 2 | `0.000000` | `0.000000` | `0.000156` | `0.102802` | `0.195754` |

This confirms the lineage diagnostic is not inventing directional families from active/interface turnover alone. v0.2.1 has comparable or higher interface turnover, but zero transition matrices and one stable family.

### Interpretation

Finding 036 narrows Finding 035:

```text
v0.3 creates measurable directional branch splitting, but not yet persistent lineage diversification.
```

The important positive result is:

```text
v0.3 produces nonzero persistent-interface transition matrices that split into multiple second-phase directional families; v0.2.1 remains a single zero-transition family under the same protocol.
```

The important negative result is:

```text
the family split is late, weak, and not yet coupled to component-level morphological divergence.
```

The current best claim is therefore:

```text
v0.3 establishes incipient directional lineage splitting inside a bounded ledger-exact scaffold, but the split has not yet become persistent, strongly separated, or morphologically expressed.
```

### Next Test

The next gate should test whether the phase-2 split persists if the horizon is extended:

```text
checkpoint_ticks = 1536, 2048
horizon = 1024
phase_length = 256
samples = 8
```

Acceptance criterion:

```text
phase-2 families remain distinct into phases 3 and 4, or produce measurable divergence in component birth/death, interface turnover, candidate-target turnover, or active/depleted structure.
```

If they collapse back into one family, the correct interpretation is:

```text
v0.3 creates transient directional branchlets, not persistent lineages.
```

### Artifacts

- `src/rotation_branch_lineage.py`
- `output/findings/finding_036_v030_history_rotation_branch_lineage_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_lineages.csv`
- `output/findings/finding_036_v030_history_rotation_branch_lineage_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_families.csv`
- `output/findings/finding_036_v030_history_rotation_branch_lineage_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_summary.csv`
- `output/findings/finding_036_v030_history_rotation_branch_lineage_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_summary.json`
- `output/findings/finding_036_v021_residual_participation_branch_lineage_control_seed56_ka5_vac2_val8_n16_rpp0p02_lineages.csv`
- `output/findings/finding_036_v021_residual_participation_branch_lineage_control_seed56_ka5_vac2_val8_n16_rpp0p02_families.csv`
- `output/findings/finding_036_v021_residual_participation_branch_lineage_control_seed56_ka5_vac2_val8_n16_rpp0p02_summary.csv`
- `output/findings/finding_036_v021_residual_participation_branch_lineage_control_seed56_ka5_vac2_val8_n16_rpp0p02_summary.json`

## Finding 037: Directional Branchlets Recur but Collapse or Merge by Phase 4

### Status

Completed for mature v0.3 checkpoints, with the v0.2.1 residual-participation candidate as control.

### Protocol

Four-phase lineage persistence protocol:

```text
checkpoint_ticks = 1536, 2048
horizon = 1024
phase_length = 256
phase_count = 4
samples = 8
sample_every = 16
connectivity = cube26
stop_active_iotas = 5000
cluster_distance_threshold = 0.55
```

This directly tests the Finding 036 acceptance gate:

```text
Do phase-2 daughter families remain distinct into phases 3 and 4, or do they collapse back into the dominant family?
```

### v0.3 Result

All v0.3 continuations remained bounded, ledger-exact, and non-runaway.

| Checkpoint | Combined families | Full path table | Stable full path | Phase-2 persists to end | Mean adjacent distance | Within-family distance | Between-family distance |
|---:|---:|---|---:|---:|---:|---:|---:|
| `1536` | `4` | `0->0->0->0:5; 0->0->1->0:1; 0->0->2->0:1; 0->3->0->0:1` | `0.625` | `0.625` | `0.601354` | `0.579265` | `0.629364` |
| `2048` | `4` | `0->0->0->0:6; 0->1->0->2:1; 0->3->0->0:1` | `0.750` | `0.750` | `0.608114` | `0.585099` | `0.641744` |

Phase-family counts:

| Checkpoint | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---:|---|---|---|---|
| `1536` | `0:8` | `0:7; 3:1` | `0:6; 1:1; 2:1` | `0:8` |
| `2048` | `0:8` | `0:6; 1:1; 3:1` | `0:8` | `0:7; 2:1` |

Mechanism metrics remain nonzero across all four phases:

| Checkpoint | Phase | Rotations/tick | Interface `V` change | Transition entropy | Candidate turnover | Interface turnover | Candidate-target turnover |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `1536` | `1` | `1.637695` | `0.004801` | `2.004995` | `0.001082` | `0.037666` | `0.316142` |
| `1536` | `2` | `1.667480` | `0.004649` | `1.914247` | `0.000956` | `0.037822` | `0.350595` |
| `1536` | `3` | `1.635742` | `0.004458` | `1.819193` | `0.000956` | `0.036489` | `0.357578` |
| `1536` | `4` | `1.540527` | `0.004124` | `1.740759` | `0.000817` | `0.035719` | `0.355501` |
| `2048` | `1` | `1.649902` | `0.004718` | `1.888604` | `0.000971` | `0.038147` | `0.347575` |
| `2048` | `2` | `1.604492` | `0.004462` | `1.916288` | `0.000911` | `0.037246` | `0.356645` |
| `2048` | `3` | `1.572754` | `0.004155` | `1.737671` | `0.000887` | `0.034668` | `0.362558` |
| `2048` | `4` | `1.522461` | `0.003921` | `1.689348` | `0.000792` | `0.035531` | `0.378959` |

Component-level deltas are still zero:

```text
phase1_mean_component_count_delta = 0
phase2_mean_component_count_delta = 0
phase3_mean_component_count_delta = 0
phase4_mean_component_count_delta = 0

phase1_mean_largest_component_delta = 0
phase2_mean_largest_component_delta = 0
phase3_mean_largest_component_delta = 0
phase4_mean_largest_component_delta = 0
```

### v0.2.1 Control

The control remains a single zero-transition lineage through all four phases.

| Checkpoint | Combined families | Full path table | Stable full path | Mean adjacent distance | Rotations/tick | Interface `V` change | Transition entropy |
|---:|---:|---|---:|---:|---:|---:|---:|
| `1536` | `1` | `0->0->0->0:8` | `1.000` | `0.000000` | `0.000000` | `0.000000` | `0.000000` |
| `2048` | `1` | `0->0->0->0:8` | `1.000` | `0.000000` | `0.000000` | `0.000000` | `0.000000` |

The control still has active/interface turnover around `0.10`, but no directional transitions. This confirms again that the v0.3 family changes are not caused by interface turnover alone.

### Interpretation

Finding 037 does not pass the persistent-lineage gate.

The positive result:

```text
v0.3 directional branchlets recur over a 1024-tick continuation, and transition entropy remains nonzero in every phase.
```

The negative result:

```text
the minority daughter families are not stable across phases 3 and 4; they usually merge back into the dominant family or appear as transient later branchlets.
```

The precise claim is:

```text
v0.3 creates recurrent transient directional branchlets inside a bounded ledger-exact scaffold, but not persistent lineage differentiation.
```

This is still a meaningful rung above Finding 036. The branch split is not a one-window artifact; the system continues generating daughter transition families. But it has not yet crossed into durable lineage separation or morphology-level differentiation.

### Current Ladder

| Level | Status |
|---|---|
| Fate openness | closed |
| Morphology openness | closed/weak |
| Rotation-aware openness | positive |
| Branch-lineage splitting | positive |
| Recurrent directional branchlets | positive |
| Persistent lineage diversification | not yet |
| Component/morphology divergence | not yet |

### Next Test

The next lever should try to make daughter families persist without increasing active growth:

```text
rotation memory / inertia
```

Candidate knobs:

- preserve rotated `V` for a short refractory window;
- make rotation offset depend on prior target `V` age or repeated received history;
- slightly increase candidate-neighborhood effect only when a non-dominant transition family appears;
- lower rotation probability but increase persistence of successful rotations.

Acceptance criterion:

```text
minority daughter families persist across at least two later phases, or predict nonzero component/interface structural divergence, while remaining bounded and ledger-exact.
```

### Artifacts

- `src/rotation_lineage_persistence.py`
- `output/findings/finding_037_v030_history_rotation_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_phases.csv`
- `output/findings/finding_037_v030_history_rotation_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_lineages.csv`
- `output/findings/finding_037_v030_history_rotation_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_families.csv`
- `output/findings/finding_037_v030_history_rotation_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_summary.csv`
- `output/findings/finding_037_v030_history_rotation_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_summary.json`
- `output/findings/finding_037_v021_residual_participation_lineage_persistence_control_seed56_ka5_vac2_val8_n16_rpp0p02_phases.csv`
- `output/findings/finding_037_v021_residual_participation_lineage_persistence_control_seed56_ka5_vac2_val8_n16_rpp0p02_lineages.csv`
- `output/findings/finding_037_v021_residual_participation_lineage_persistence_control_seed56_ka5_vac2_val8_n16_rpp0p02_families.csv`
- `output/findings/finding_037_v021_residual_participation_lineage_persistence_control_seed56_ka5_vac2_val8_n16_rpp0p02_summary.csv`
- `output/findings/finding_037_v021_residual_participation_lineage_persistence_control_seed56_ka5_vac2_val8_n16_rpp0p02_summary.json`

## Finding 038: Vector-Coupled Angular Momentum Produces Non-Merging Directional Lineages

v0.3.1 adds a narrow angular-momentum state:

```text
L = retained signed turn memory of the information-exchange vector
```

The implementation is deliberately limited:

```text
V remains the information-exchange vector.
Received exchange creates a signed rotation offset.
Prior L biases only the next V rotation.
Observed V rotation updates L.
L does not alter A, R, P, valence, secondary valence, or ledger totals.
```

The tested law:

```yaml
angular_momentum_enabled: true
angular_momentum_decay: 0.90
angular_momentum_coupling: 0.50
angular_momentum_retention: 0.50
angular_momentum_cap: 2.0
```

Matched control:

```yaml
angular_momentum_enabled: true
angular_momentum_coupling: 0.0
angular_momentum_retention: 0.0
angular_momentum_cap: 2.0
```

The control keeps signed received exchange and the same cap, but removes retained angular memory and future-turn bias. This separates the signed-turn repair from the angular-momentum hypothesis.

### Protocol

Both v0.3.1 and the signed-exchange/no-memory control were tested at mature checkpoints:

```text
seed = 56
kA = 5
vacuum = 2
valence = 8
n = 16
residual_participation_probability = 0.02
received_rotation_probability = 1.0
checkpoint_ticks = 1536, 2048
horizon = 1024
phase_length = 256
phase_count = 4
samples = 8
sample_every = 16
workers = 8
stop_active_iotas = 5000
cluster_distance_threshold = 0.55
```

All runs remained bounded, ledger-exact, and non-runaway.

### Rotation-Aware Openness

Both variants remain in the old protected fate class, but both produce bounded directional-drift signatures.

| Variant | Checkpoint | Base active | Base depleted | Rotation class | Signature openness | Effective signatures | Late rotations/tick | Late transition entropy |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| v0.3.1 `L` | `1536` | `1059` | `473` | `directional_drift:8` | `0.916667` | `6.727171` | `1.551215` | `1.367908` |
| v0.3.1 `L` | `2048` | `1059` | `481` | `directional_drift:8` | `1.000000` | `8.000000` | `1.229167` | `0.766036` |
| signed/no-memory | `1536` | `1059` | `470` | `directional_drift:8` | `1.000000` | `8.000000` | `1.796007` | `1.855424` |
| signed/no-memory | `2048` | `1059` | `474` | `directional_drift:8` | `1.000000` | `8.000000` | `1.660590` | `1.499795` |

This means signed exchange alone is enough to produce bounded directional signature plurality. The important test is therefore not signature openness, but whether branch families keep merging back.

### Four-Phase Lineage Persistence

v0.3.1 with angular memory no longer shows collapse back to a dominant phase-4 family.

| Variant | Checkpoint | Combined families | Full path table | Stable full path | Phase-2 persists to end | Mean adjacent distance |
|---|---:|---:|---|---:|---:|---:|
| v0.3.1 `L` | `1536` | `20` | `0->1->2->3:1; 11->12->13->14:1; 4->4->15->16:1; 4->4->18->19:1; 4->4->4->17:1; 4->4->5->6:1; 4->4->9->10:1; 4->7->4->8:1` | `0.000` | `0.000` | `0.698204` |
| v0.3.1 `L` | `2048` | `29` | `0->1->2->3:1; 1->19->20->21:1; 1->22->23->24:1; 12->13->14->15:1; 12->16->17->18:1; 25->26->27->28:1; 4->5->6->7:1; 8->9->10->11:1` | `0.000` | `0.000` | `0.727426` |
| signed/no-memory | `1536` | `4` | `0->0->0->0:6; 0->0->1->2:1; 0->0->3->0:1` | `0.750` | `0.750` | `0.594665` |
| signed/no-memory | `2048` | `5` | `0->0->0->0:5; 0->0->0->1:1; 0->0->3->4:1; 0->2->0->0:1` | `0.625` | `0.625` | `0.615100` |

The `phase2_persists_to_end` field is no longer the right success measure for v0.3.1, because the daughter families do not remain static labels. They keep drifting. The relevant positive result is:

```text
v0.3.1 continuations do not merge back into a common directional family; by phase 4 all samples are separated at both checkpoints.
```

Phase-family counts make this explicit:

| Variant | Checkpoint | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---:|---|---|---|---|
| v0.3.1 `L` | `1536` | `0:1; 4:6; 11:1` | `1:1; 4:5; 7:1; 12:1` | `2:1; 4:2; 5:1; 9:1; 13:1; 15:1; 18:1` | `3:1; 6:1; 8:1; 10:1; 14:1; 16:1; 17:1; 19:1` |
| v0.3.1 `L` | `2048` | `0:1; 1:2; 4:1; 8:1; 12:2; 25:1` | `1:1; 5:1; 9:1; 13:1; 16:1; 19:1; 22:1; 26:1` | `2:1; 6:1; 10:1; 14:1; 17:1; 20:1; 23:1; 27:1` | `3:1; 7:1; 11:1; 15:1; 18:1; 21:1; 24:1; 28:1` |
| signed/no-memory | `1536` | `0:8` | `0:8` | `0:6; 1:1; 3:1` | `0:7; 2:1` |
| signed/no-memory | `2048` | `0:8` | `0:7; 2:1` | `0:7; 3:1` | `0:6; 1:1; 4:1` |

The control reproduces the old canalization pattern: most continuations remain in or return to family `0`. The angular-memory variant converts that into continued directional separation.

### Mechanism Metrics

The angular-memory effect is small in raw event rate but consequential in lineage space.

| Checkpoint | Phase | Rotations/tick | Biased `L` rotations/tick | Mean `|L|` active | Interface `V` change | Transition entropy | Component count delta | Largest component delta |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1536` | `1` | `1.648438` | `0.005859` | `0.008498` | `0.003354` | `1.527336` | `0.000` | `0.000` |
| `1536` | `2` | `1.445312` | `0.005371` | `0.007251` | `0.002438` | `1.117396` | `0.000` | `0.000` |
| `1536` | `3` | `1.244629` | `0.003418` | `0.006316` | `0.001806` | `0.700238` | `0.000` | `0.000` |
| `1536` | `4` | `1.090820` | `0.001953` | `0.005552` | `0.001358` | `0.510703` | `0.000` | `0.000` |
| `2048` | `1` | `1.316895` | `0.003418` | `0.006633` | `0.002032` | `0.850798` | `0.000` | `0.000` |
| `2048` | `2` | `1.152344` | `0.002441` | `0.006066` | `0.002037` | `0.903382` | `0.000` | `0.000` |
| `2048` | `3` | `1.041504` | `0.001953` | `0.005265` | `0.001301` | `0.547799` | `0.000` | `0.000` |
| `2048` | `4` | `0.933594` | `0.002441` | `0.004754` | `0.001039` | `0.327589` | `0.125` | `-0.125` |

The signed/no-memory control has `0.0` biased rotations/tick and `0.0` mean active `|L|` in every phase.

### Interpretation

Finding 038 passes the non-merging directional-lineage gate, but not the morphology-divergence gate.

The paper-safe claim:

```text
Vector-coupled angular momentum converts transient branchlets into continuing directional lineage separation. The effect remains bounded and ledger-exact, and it does not yet produce meaningful component-level morphology divergence.
```

The key distinction:

```text
signed exchange creates bounded directional plurality;
retained angular momentum prevents those plural directions from merging back into one dominant transition family.
```

This is not yet open-ended complexity. The coarse fate class remains protected, active count remains bounded at `1059`, and component deltas are essentially zero. But the earlier failure mode changed:

```text
Finding 037 failed because daughter families collapsed or merged.
Finding 038 no longer collapses; it drifts through separated directional histories.
```

The new next gate is structural consequence:

```text
Do separated directional lineages eventually produce distinguishable interface/component morphology, or are they purely directional histories over a fixed scaffold?
```

### Artifacts

- `src/iota_rig.py`
- `src/rotation_lineage_persistence.py`
- `output/findings/configs/v031_vector_angular_momentum_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2.yaml`
- `output/findings/configs/v031_signed_exchange_control_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2.yaml`
- `output/findings/finding_038_v031_vector_angular_momentum_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_summary.csv`
- `output/findings/finding_038_v031_vector_angular_momentum_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_summary.csv`
- `output/findings/finding_038_v031_signed_exchange_control_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2_summary.csv`
- `output/findings/finding_038_v031_signed_exchange_control_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2_summary.csv`

## Finding 039: Directional Lineages Are Not Yet Morphogenetic

Finding 038 showed that v0.3.1 angular momentum creates non-merging directional lineages. Finding 039 tests whether those directional lineages predict active/depleted geometry.

### Protocol

A new lineage-conditioned morphology diagnostic reruns the same continuation seeds and clusters directional families exactly as the lineage-persistence gate does. It then compares pairwise geometry by phase family and full lineage path.

```text
checkpoint_ticks = 1536, 2048
horizon = 1024
phase_length = 256
phase_count = 4
samples = 8
connectivity = cube26
cluster_distance_threshold = 0.55
```

Measured per pair:

```text
active Jaccard distance
depleted Jaccard distance
active-interface Jaccard distance
interface-union Jaccard distance
largest-component difference
component-count difference
component-entropy difference
transition-matrix distance
```

### Aggregate Result

| Variant | Mean transition distance | Active distance | Depleted distance | Active-interface distance | Interface-union distance | Largest-component delta | Component-count delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| v0.3.1 angular memory | `0.707355` | `0.048056` | `0.077674` | `0.071024` | `0.024380` | `0.031250` | `0.031250` |
| signed/no-memory control | `0.598069` | `0.051434` | `0.091308` | `0.080074` | `0.026525` | `0.000000` | `0.000000` |

The result is negative for morphogenesis.

v0.3.1 has stronger directional separation, but its active/depleted spatial divergence is not larger than the signed/no-memory control. In fact, the control has slightly larger mean active, depleted, active-interface, and interface-union Jaccard distances.

### Phase-4 Result

| Variant | Checkpoint | Phase families | Active distance | Depleted distance | Interface-union distance | Component-count delta | Transition/active correlation |
|---|---:|---:|---:|---:|---:|---:|---:|
| v0.3.1 angular memory | `1536` | `8` | `0.051256` | `0.071714` | `0.027538` | `0.000` | `-0.297988` |
| v0.3.1 angular memory | `2048` | `8` | `0.043283` | `0.061587` | `0.022483` | `0.250` | `-0.018523` |
| signed/no-memory control | `1536` | `2` | `0.055855` | `0.087229` | `0.032253` | `0.000` | `-0.048578` |
| signed/no-memory control | `2048` | `3` | `0.047790` | `0.079606` | `0.026826` | `0.000` | `-0.095875` |

The phase-4 directional families are distinct in transition space, but this does not translate into larger spatial distances. Correlations between transition distance and active/interface geometry are weak or negative.

### Interpretation

The precise claim is:

```text
v0.3.1 produces persistent directional lineage separation, but those lineages are not yet morphogenetic. The active/depleted scaffold undergoes small site-level differences, but directional family identity does not predict distinct component or interface geometry.
```

This closes the Finding 038 caveat. The system has directional memory, but not yet directional memory with structural consequence.

### Artifacts

- `src/lineage_conditioned_morphology.py`
- `output/findings/finding_039_v031_vector_angular_momentum_lineage_conditioned_morphology_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_summary.csv`
- `output/findings/finding_039_v031_signed_exchange_control_lineage_conditioned_morphology_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2_summary.csv`

## Finding 040: Secondary Candidate Bias Maximizes Directional Separation but Suppresses Morphology

Finding 040 tests one capacity-neutral morphogenetic coupling:

```text
retained angular momentum biases secondary candidate ordering
```

This does not change valence count, amplitude, range, payload, conservation, or transfer capacity. It only changes which secondary candidates are preferred when source `L` is nonzero.

Tested knob:

```yaml
angular_momentum_secondary_bias_enabled: true
angular_momentum_secondary_bias_strength: 0.10
angular_momentum_secondary_bias_preserve_behavior: true
```

### Lineage Result

All runs remained bounded, ledger-exact, and non-runaway.

| Variant | Checkpoint | Combined families | Phase-1 families | Phase-4 families | Adjacent distance | Phase-4 rotations/tick | Phase-4 transition entropy | Phase-4 interface turnover |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v0.3.1 angular memory | `1536` | `20` | `3` | `8` | `0.698204` | `1.090820` | `0.510703` | `0.025388` |
| v0.3.1 angular memory | `2048` | `29` | `6` | `8` | `0.727426` | `0.933594` | `0.327589` | `0.020332` |
| v0.3.2 secondary bias | `1536` | `32` | `8` | `8` | `0.786545` | `0.617676` | `0.126328` | `0.012663` |
| v0.3.2 secondary bias | `2048` | `31` | `8` | `8` | `0.862250` | `0.363770` | `0.043633` | `0.007599` |

The secondary-bias law maximizes directional family separation. Most phases become all-singleton families.

But this is not a complexity win: rotation rate, transition entropy, and interface turnover all drop sharply.

### Morphology Result

| Variant | Mean transition distance | Active distance | Depleted distance | Active-interface distance | Interface-union distance | Active/depleted adjacency | Largest cube26 component | Cube26 components |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v0.3.1 angular memory | `0.707355` | `0.048056` | `0.077674` | `0.071024` | `0.024380` | `0.984773` | `140.984375` | `17.015625` |
| v0.3.2 secondary bias | `0.826521` | `0.027289` | `0.040029` | `0.033884` | `0.010555` | `0.996127` | `137.000000` | `16.031250` |

The secondary-bias law increases directional separation but reduces spatial divergence. It also raises active/depleted adjacency toward near-total interface coupling and shifts the scaffold to a slightly smaller/lower-count component structure.

### Interpretation

The precise claim is:

```text
Coupling angular momentum to secondary candidate ordering does not produce morphogenesis. It over-partitions directional histories while suppressing interface turnover and reducing active/depleted spatial divergence.
```

This is an important negative result. It shows that simply letting `L` choose secondary handshakes is too canalizing at `strength = 0.10` under this regime.

The failure mode is now sharper:

```text
v0.3.1: directional memory without structural consequence.
v0.3.2 secondary bias: stronger directional separation with less structural motion.
```

The next lever should not be stronger secondary bias. The next principled test should either lower/condition the bias or make it event-gated:

```text
only apply secondary ordering bias when local interface turnover is present, or when a candidate would recruit a new/depleted boundary site.
```

That would ask whether angular momentum can bias real interface recruitment without globally freezing the scaffold.

### Artifacts

- `src/iota_rig.py`
- `src/lineage_conditioned_morphology.py`
- `output/findings/configs/v032_vector_angular_momentum_secondary_bias_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10.yaml`
- `output/findings/finding_040_v032_vector_angular_momentum_secondary_bias_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv`
- `output/findings/finding_040_v032_vector_angular_momentum_secondary_bias_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv`
- `output/findings/finding_040_v032_vector_angular_momentum_secondary_bias_lineage_conditioned_morphology_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv`

## Finding 041: Event-Gated Candidate Bias Further Canalizes the Interface

Finding 040 showed that global angular-momentum secondary candidate ordering bias over-partitions directional histories while suppressing morphology. Finding 041 tests whether applying the same ordering bias only at local interface opportunity sites avoids that failure mode.

Tested knob:

```yaml
angular_momentum_secondary_bias_enabled: true
angular_momentum_secondary_bias_strength: 0.10
angular_momentum_secondary_bias_preserve_behavior: true
angular_momentum_secondary_bias_gate: interface_recruitment
```

The gate preserves the v0.3.2 law unless explicitly enabled. With `interface_recruitment`, the secondary ordering bias is only scored for secondary candidates whose target is in the current active/depleted interface, an inactive recruitable boundary site, or the recent active-state turnover neighborhood.

### Protocol

```text
checkpoint_ticks = 1536, 2048
horizon = 1024 for lineage/morphology
phase_length = 256
phase_count = 4
samples = 8
connectivity = cube26
cluster_distance_threshold = 0.55
```

The openness gate remained clean:

```text
bounded_nonrunaway_count = 8 at both checkpoints
ledger_exact_count = 8 at both checkpoints
runaway_count = 0 at both checkpoints
```

### Lineage Result

Event-gating does not recover morphology. It makes directional path separation strong, but with still lower late rotation entropy and lower interface turnover than the global secondary-bias law.

| Variant | Checkpoint | Combined families | Phase-1 families | Phase-4 families | Adjacent distance | Phase-4 rotations/tick | Phase-4 transition entropy | Phase-4 interface turnover |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v0.3.1 `L` | `1536` | `20` | `3` | `8` | `0.698204` | `1.090820` | `0.510703` | `0.025388` |
| v0.3.1 `L` | `2048` | `29` | `6` | `8` | `0.727426` | `0.933594` | `0.327589` | `0.020332` |
| v0.3.2 global bias | `1536` | `32` | `8` | `8` | `0.786545` | `0.617676` | `0.126328` | `0.012663` |
| v0.3.2 global bias | `2048` | `31` | `8` | `8` | `0.862250` | `0.363770` | `0.043633` | `0.007599` |
| v0.3.3 event-gated bias | `1536` | `28` | `8` | `8` | `0.897186` | `0.334473` | `0.028008` | `0.007480` |
| v0.3.3 event-gated bias | `2048` | `29` | `8` | `7` | `0.924075` | `0.313965` | `0.015625` | `0.006402` |

The event gate increases adjacent phase distance beyond v0.3.2, but the mechanism metrics move in the wrong direction: phase-4 rotation rate, transition entropy, and active-interface turnover all fall.

### Morphology Result

Aggregate morphology distances across both checkpoints and four phases:

| Variant | Mean transition distance | Active distance | Depleted distance | Active-interface distance | Interface-union distance | Component-count delta | Active/depleted adjacency |
|---|---:|---:|---:|---:|---:|---:|---:|
| v0.3.1 `L` | `0.707355` | `0.048056` | `0.077674` | `0.071024` | `0.024380` | `0.031250` | `0.984773` |
| v0.3.2 global bias | `0.826521` | `0.027289` | `0.040029` | `0.033884` | `0.010555` | `0.062500` | `0.996127` |
| v0.3.3 event-gated bias | `0.903949` | `0.022345` | `0.029163` | `0.027105` | `0.009316` | `0.053571` | `0.997477` |

This is a second negative result for candidate ordering as a morphogenetic coupling. Event-gating raises directional transition distance again, but active/depleted and interface-union spatial divergence drop below both v0.3.1 and v0.3.2.

### Interpretation

The precise claim:

```text
Event-gating angular-momentum secondary candidate ordering does not produce structural consequence. It further canalizes the interface: directional histories separate more strongly while spatial divergence, transition entropy, and interface turnover shrink.
```

This sharpens the failure mode:

```text
v0.3.1: retained L creates persistent directional histories without morphology.
v0.3.2: global L ordering bias over-separates direction and suppresses morphology.
v0.3.3: event-gated L ordering bias suppresses morphology even more.
```

The next lever should stop changing secondary candidate ordering. A more principled test is to couple `L` to the local recruitment event itself while preserving the ledger:

```text
event-local residual participation modulation

At active/depleted interface candidates only, let the sign/magnitude of source or target L
slightly modulate residual participation probability, with a fixed global mean probability
and unchanged valence, payload, range, and conservation.
```

That asks whether angular memory can change which depleted boundary sites re-enter the active scaffold, without globally reordering all secondary handshakes.

### Artifacts

- `src/iota_rig.py`
- `output/findings/configs/v033_vector_angular_momentum_event_gated_bias_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10.yaml`
- `output/findings/finding_041_v033_vector_angular_momentum_event_gated_bias_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv`
- `output/findings/finding_041_v033_vector_angular_momentum_event_gated_bias_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv`
- `output/findings/finding_041_v033_vector_angular_momentum_event_gated_bias_lineage_conditioned_morphology_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv`

## Finding 042: Fixed-Mean Residual Recruitment Restores Turnover but Not Morphogenesis

Findings 040 and 041 showed that angular momentum should not be coupled to secondary candidate ordering. Finding 042 moves the coupling to the stranded-site re-entry gate:

```text
fixed-mean angular-momentum-biased residual recruitment
```

The physics-facing interpretation is:

```text
angular-momentum-coupled interfacial nucleation
```

The design principle is explicit symmetry breaking at fixed mean activation. Angular momentum is not added as energy. It redistributes residual re-entry probability among eligible active/depleted interface candidates while preserving the same expected residual participation rate.

Tested knob:

```yaml
angular_momentum_residual_bias_enabled: true
angular_momentum_residual_bias_strength: 1.0
angular_momentum_residual_bias_gate: depleted_interface
angular_momentum_residual_bias_mean_preserving: true
angular_momentum_residual_bias_preserve_behavior: true
```

The v0.3.4 config starts from the v0.3.1 angular-memory baseline. It does not enable global or event-gated secondary candidate ordering bias.

### Mechanism

For each active source's selected depleted-interface residual candidates, the baseline residual participation probability remains:

```text
base_event_probability = transfer_probability * residual_participation_probability
```

The source angular momentum creates a signed local multiplier from alignment between the candidate step and the source's `L`-biased exchange direction. The multipliers are renormalized by the probability-weighted mean across that source's eligible residual candidates:

```text
weighted mean biased probability = weighted mean base probability
```

This preserves expected residual recruitment under the actual local candidate influences.

### Fixed-Mean Audit

A full 2048-tick front-turnover audit confirms exact expected-probability preservation to floating precision:

| Quantity | Value |
|---|---:|
| Base residual probability sum | `3740.364285714283` |
| Biased residual probability sum | `3740.364285714283` |
| Probability delta | `0.000000000000e+00` |
| Mean residual participations/tick | `1.786133` |
| Mean active-interface turnover | `0.056318` |

The law therefore changes where residual participation happens, not the expected amount.

### Openness Gate

The boundedness/ledger gate passed:

```text
bounded_nonrunaway_count = 8 at both checkpoints
ledger_exact_count = 8 at both checkpoints
runaway_count = 0 at both checkpoints
```

The late-window interface turnover recovered relative to candidate-ordering bias:

| Checkpoint | Late rotations/tick | Late active-interface turnover |
|---:|---:|---:|
| `1536` | `1.599826` | `0.033518` |
| `2048` | `1.147569` | `0.024748` |

### Lineage Result

Compared with v0.3.2/v0.3.3, v0.3.4 restores rotation rate, transition entropy, and phase-4 interface turnover close to v0.3.1 levels. It no longer over-partitions every phase into singleton directional families.

| Variant | Checkpoint | Combined families | Adjacent distance | Phase-4 rotations/tick | Phase-4 transition entropy | Phase-4 interface turnover |
|---|---:|---:|---:|---:|---:|---:|
| v0.3.1 `L` | `1536` | `20` | `0.698204` | `1.090820` | `0.510703` | `0.025388` |
| v0.3.1 `L` | `2048` | `29` | `0.727426` | `0.933594` | `0.327589` | `0.020332` |
| v0.3.2 global ordering | `1536` | `32` | `0.786545` | `0.617676` | `0.126328` | `0.012663` |
| v0.3.2 global ordering | `2048` | `31` | `0.862250` | `0.363770` | `0.043633` | `0.007599` |
| v0.3.3 event-gated ordering | `1536` | `28` | `0.897186` | `0.334473` | `0.028008` | `0.007480` |
| v0.3.3 event-gated ordering | `2048` | `29` | `0.924075` | `0.313965` | `0.015625` | `0.006402` |
| v0.3.4 fixed-mean recruitment | `1536` | `22` | `0.667037` | `1.142578` | `0.912894` | `0.024840` |
| v0.3.4 fixed-mean recruitment | `2048` | `29` | `0.697571` | `0.924805` | `0.487094` | `0.021181` |

This is the important positive mechanism result: putting `L` at the residual recruitment gate avoids the candidate-ordering canalization failure.

### Morphology Result

The morphology result is still not a pass. v0.3.4 recovers much of v0.3.1's active/interface spatial divergence and beats v0.3.2/v0.3.3 by a wide margin, but it does not exceed the v0.3.1 angular-memory baseline or the signed/no-memory control.

| Variant | Mean transition distance | Active distance | Depleted distance | Active-interface distance | Interface-union distance | Component-count delta | Active/depleted adjacency |
|---|---:|---:|---:|---:|---:|---:|---:|
| signed/no-memory control | `0.598069` | `0.051434` | `0.091308` | `0.080074` | `0.026525` | `0.000000` | `0.977735` |
| v0.3.1 `L` | `0.707355` | `0.048056` | `0.077674` | `0.071024` | `0.024380` | `0.031250` | `0.984773` |
| v0.3.2 global ordering | `0.826521` | `0.027289` | `0.040029` | `0.033884` | `0.010555` | `0.062500` | `0.996127` |
| v0.3.3 event-gated ordering | `0.903949` | `0.022345` | `0.029163` | `0.027105` | `0.009316` | `0.053571` | `0.997477` |
| v0.3.4 fixed-mean recruitment | `0.671077` | `0.043893` | `0.074544` | `0.063453` | `0.019984` | `0.000000` | `0.985688` |

### Interpretation

The precise claim:

```text
Fixed-mean angular-momentum-biased residual recruitment is the right coupling site
mechanistically: it preserves expected activation and restores interface turnover,
rotation entropy, and spatial divergence relative to candidate-ordering bias.
However, at strength 1.0 it does not yet create morphology beyond the v0.3.1
angular-memory baseline or signed/no-memory control.
```

This is not an open-ended morphology result, but it is an informative narrowing:

```text
Candidate ordering is wrong because it canalizes the scaffold.
Residual recruitment is better because it breaks interface symmetry without adding fuel.
The remaining failure is effect size or score geometry, not coupling site.
```

The next principled test is a small strength/score sweep at fixed mean activation:

```text
v0.3.4b:
  strength in {0.5, 1.0, 2.0}
  score modes:
    source_L_alignment
    target_L_alignment
    source_target_L_contrast

Acceptance:
  residual probability sum remains fixed
  phase-4 turnover does not collapse
  active/interface spatial divergence exceeds v0.3.1 and signed/no-memory control
```

### Artifacts

- `src/iota_rig.py`
- `src/front_turnover_diagnostic.py`
- `output/findings/configs/v034_fixed_mean_residual_recruitment_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0.yaml`
- `output/findings/finding_042_v034_fixed_mean_residual_recruitment_front_turnover_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0_turnover.csv`
- `output/findings/finding_042_v034_fixed_mean_residual_recruitment_front_turnover_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0_turnover_summary.json`
- `output/findings/finding_042_v034_fixed_mean_residual_recruitment_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0_summary.csv`
- `output/findings/finding_042_v034_fixed_mean_residual_recruitment_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0_summary.csv`
- `output/findings/finding_042_v034_fixed_mean_residual_recruitment_lineage_conditioned_morphology_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0_summary.csv`

## Finding 043: Source-Target Contrast Breaks Interface Symmetry at Fixed Mean

Finding 042 established that residual recruitment is the correct coupling site, but the initial `source_L_alignment` score at strength `1.0` did not exceed the v0.3.1/control morphology gate. Finding 043 runs the planned fixed-mean score/strength sweep:

```text
score_modes = source_L_alignment, target_L_alignment, source_target_L_contrast
strengths = 0.5, 1.0, 2.0
```

All variants preserve the same residual-recruitment design:

```yaml
angular_momentum_residual_bias_enabled: true
angular_momentum_residual_bias_gate: depleted_interface
angular_momentum_residual_bias_mean_preserving: true
```

The new score modes are:

```text
source_L_alignment:
  candidate aligns with the source cell's L-biased exchange direction

target_L_alignment:
  candidate aligns with the depleted target cell's retained L-biased direction

source_target_L_contrast:
  candidate is biased by the signed source-minus-target L contrast along the source exchange direction
```

### Protocol

For each of 9 variants:

```text
checkpoint_ticks = 1536, 2048
horizon = 1024 for lineage/morphology
phase_length = 256
phase_count = 4
samples = 8
connectivity = cube26
cluster_distance_threshold = 0.55
```

The best variant by interface-union spatial divergence was:

```text
source_target_L_contrast, strength = 2.0
```

### Fixed-Mean Audit

A full 2048-tick front-turnover audit for the winning variant confirms expected probability preservation:

| Quantity | Value |
|---|---:|
| Base residual probability sum | `3920.499999999997` |
| Biased residual probability sum | `3920.499999999996` |
| Probability delta | `-4.547473508865e-13` |
| Mean residual participations/tick | `1.870605` |
| Mean active-interface turnover | `0.060657` |
| Mean interface-union turnover | `0.021693` |

This is still fixed-mean activation. The result comes from redistributing where re-entry happens.

### Sweep Result

Aggregate morphology distances across both checkpoints and all four phases:

| Rank | Score mode | Strength | Transition distance | Active distance | Depleted distance | Active-interface distance | Interface-union distance | Active/depleted adjacency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `source_target_L_contrast` | `2.0` | `0.598748` | `0.047655` | `0.084874` | `0.079331` | `0.027994` | `0.973621` |
| 2 | `source_target_L_contrast` | `0.5` | `0.637177` | `0.053477` | `0.087661` | `0.080064` | `0.027734` | `0.980900` |
| 3 | `target_L_alignment` | `1.0` | `0.647973` | `0.049770` | `0.082746` | `0.074972` | `0.025598` | `0.979401` |
| 4 | `source_L_alignment` | `0.5` | `0.660213` | `0.050091` | `0.082474` | `0.074149` | `0.025107` | `0.982902` |
| 5 | `target_L_alignment` | `2.0` | `0.661155` | `0.048087` | `0.081076` | `0.071749` | `0.023764` | `0.983891` |
| 6 | `source_target_L_contrast` | `1.0` | `0.690963` | `0.043303` | `0.072000` | `0.066169` | `0.022738` | `0.982604` |
| 7 | `source_L_alignment` | `2.0` | `0.696848` | `0.045226` | `0.074888` | `0.063883` | `0.020164` | `0.987482` |
| 8 | `source_L_alignment` | `1.0` | `0.671077` | `0.043893` | `0.074544` | `0.063453` | `0.019984` | `0.985688` |
| 9 | `target_L_alignment` | `0.5` | `0.723361` | `0.041423` | `0.067850` | `0.059627` | `0.019429` | `0.988057` |

The contrast score at strength `2.0` is the first tested law to beat both v0.3.1 and the signed/no-memory control on interface-union divergence.

Comparison to baselines:

| Variant | Transition distance | Active distance | Depleted distance | Active-interface distance | Interface-union distance | Active/depleted adjacency |
|---|---:|---:|---:|---:|---:|---:|
| signed/no-memory control | `0.598069` | `0.051434` | `0.091308` | `0.080074` | `0.026525` | `0.977735` |
| v0.3.1 `L` | `0.707355` | `0.048056` | `0.077674` | `0.071024` | `0.024380` | `0.984773` |
| v0.3.4b contrast `2.0` | `0.598748` | `0.047655` | `0.084874` | `0.079331` | `0.027994` | `0.973621` |

This is not a broad morphology win. Active-set distance is slightly below v0.3.1 and below the signed/no-memory control. Active-interface distance is above v0.3.1 and essentially tied with the control. Depleted and interface-union distances improve over v0.3.1, and interface-union distance improves over both baselines.

### Lineage and Turnover

The winning variant remains bounded and ledger-exact at both checkpoints:

```text
bounded_nonrunaway_count = 8
ledger_exact_count = 8
```

Lineage/turnover for the winner:

| Checkpoint | Combined families | Adjacent distance | Phase-4 rotations/tick | Phase-4 transition entropy | Phase-4 interface turnover |
|---:|---:|---:|---:|---:|---:|
| `1536` | `4` | `0.568057` | `1.349609` | `1.406804` | `0.030567` |
| `2048` | `6` | `0.617701` | `1.254395` | `1.298922` | `0.029274` |

This is qualitatively different from v0.3.2/v0.3.3. The law no longer maximizes directional family count. Instead, it preserves rich transition entropy and high interface turnover while increasing interface-union spatial divergence.

### Interpretation

The precise claim:

```text
Source-target L contrast at fixed mean residual participation produces the first
bounded, ledger-exact interface-symmetry-breaking result: it improves interface-union
spatial divergence beyond both the angular-memory and signed/no-memory baselines
without adding expected activation.
```

The important distinction:

```text
Candidate ordering changed the transition alphabet but froze the floor.
Fixed-mean source-target residual contrast changes which floor tiles re-enter.
```

This is still not component-level open-ended morphology:

```text
component-count delta remains 0.0
largest-component delta remains 0.0
active-set distance does not exceed both baselines
```

But it is the first clean evidence that retained angular memory can do boundary work under a fixed activation budget.

### Next Gate

The next step should validate robustness before adding any new mechanism:

```text
v0.3.5 seed robustness:
  law = fixed-mean source_target_L_contrast
  strength = 2.0
  seeds = multiple seed56-like protected-front seeds
  acceptance = interface-union distance above v0.3.1/control on most seeds
```

Only after seed robustness should the project test component-level mechanisms.

### Artifacts

- `src/iota_rig.py`
- `src/front_turnover_diagnostic.py`
- `output/findings/configs/v034b_fixed_mean_residual_recruitment_*`
- `output/findings/finding_043_v034b_fixed_mean_residual_recruitment_*_rotation_aware_openness_summary.csv`
- `output/findings/finding_043_v034b_fixed_mean_residual_recruitment_*_lineage_persistence_summary.csv`
- `output/findings/finding_043_v034b_fixed_mean_residual_recruitment_*_lineage_conditioned_morphology_summary.csv`
- `output/findings/finding_043_v034b_fixed_mean_residual_recruitment_contrast_amrb2p0_front_turnover_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_turnover.csv`
- `output/findings/finding_043_v034b_fixed_mean_residual_recruitment_contrast_amrb2p0_front_turnover_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_turnover_summary.json`

## Finding 044: Source-Target Contrast Is Seed-Robust at Fixed Mean

Finding 043 showed a narrow positive result on seed `56`: source-target angular-momentum contrast at residual re-entry increased interface-union divergence beyond both the v0.3.1 angular-memory baseline and the signed/no-memory control, while preserving the expected residual recruitment budget.

Finding 044 tests whether that result is seed-specific.

### Protocol

v0.3.5 keeps the same law:

```yaml
angular_momentum_residual_bias_enabled: true
angular_momentum_residual_bias_strength: 2.0
angular_momentum_residual_bias_gate: depleted_interface
angular_momentum_residual_bias_mean_preserving: true
angular_momentum_residual_bias_preserve_behavior: true
angular_momentum_residual_bias_score_mode: source_target_L_contrast
```

Test matrix:

```text
seeds: 42, 43, 44, 45, 46, 56
checkpoints: 1536, 2048
samples/checkpoint: 8
horizon: 1024
phase length: 256
baselines per seed:
  signed/no-memory control
  v0.3.1 angular memory
```

The pass gate was intentionally modest:

```text
interface-union distance beats both main baselines in a majority of seeds
bounded_nonrunaway_count = 8/8
ledger_exact_count = 8/8
fixed residual-recruitment mean conserved to floating precision
phase-4 interface turnover does not collapse
```

### Fixed-Mean Audit

The fixed-mean audit passed on every contrast seed:

| Seed | Base probability sum | Biased probability sum | Summed delta | Max row delta | Final ledger error |
|---:|---:|---:|---:|---:|---:|
| `42` | `3263.132857` | `3263.132857` | `-2.642331e-14` | `2.220446e-15` | `0.0` |
| `43` | `2181.701429` | `2181.701429` | `-1.704192e-14` | `2.220446e-15` | `0.0` |
| `44` | `2986.007143` | `2986.007143` | `-7.438494e-15` | `3.996803e-15` | `0.0` |
| `45` | `1337.225000` | `1337.225000` | `-1.573741e-14` | `1.332268e-15` | `0.0` |
| `46` | `3734.068571` | `3734.068571` | `-1.543210e-14` | `2.664535e-15` | `0.0` |
| `56` | `3920.500000` | `3920.500000` | `-3.330669e-15` | `1.776357e-15` | `0.0` |

Across the six tested seeds:

```text
fixed_mean_ok_count = 6/6
contrast_safety_ok_count = 6/6
max_abs_probability_delta = 3.996803e-15
max_abs_summed_probability_delta = 2.642331e-14
```

### Seed Robustness

Interface-union divergence beat both baselines on every tested seed:

| Seed | Contrast interface-union | v0.3.1 interface-union | Signed interface-union | Beats both? | Contrast active distance | Active beats both? | Phase-4 interface turnover |
|---:|---:|---:|---:|---|---:|---|---:|
| `42` | `0.023097` | `0.019906` | `0.018371` | yes | `0.043932` | yes | `0.025857` |
| `43` | `0.015844` | `0.012556` | `0.014801` | yes | `0.028338` | yes | `0.013378` |
| `44` | `0.030661` | `0.021671` | `0.021941` | yes | `0.051424` | yes | `0.031655` |
| `45` | `0.013536` | `0.011910` | `0.011821` | yes | `0.022234` | no | `0.017299` |
| `46` | `0.020421` | `0.016858` | `0.020237` | yes | `0.034456` | no | `0.022569` |
| `56` | `0.027994` | `0.024380` | `0.026525` | yes | `0.047655` | no | `0.029920` |

Counts:

```text
interface_union_beats_both = 6/6
active_distance_beats_both = 3/6
component_nonzero_seed_count = 1/6
```

The component signal remains weak. Component-count and largest-component deltas remain `0.0` for the contrast variant; the only nonzero component measure is a small component-entropy delta on seed `44`.

### Aggregate Comparison

Mean across all six seeds, two checkpoints, and four phases:

| Variant | Transition distance | Active distance | Depleted distance | Active-interface distance | Interface-union distance | Phase-4 interface turnover | Safety OK |
|---|---:|---:|---:|---:|---:|---:|---:|
| v0.3.5 contrast `2.0` | `0.683620` | `0.038007` | `0.065129` | `0.061793` | `0.021926` | `0.023446` | `6/6` |
| v0.3.1 angular memory | `0.748006` | `0.035978` | `0.058270` | `0.053058` | `0.017880` | `0.018258` | `6/6` |
| signed/no-memory control | `0.742398` | `0.036669` | `0.059559` | `0.055160` | `0.018949` | `0.018930` | `6/6` |

This is a stronger result than Finding 043. The seed-robust contrast law does not maximize transition distance; both baselines have higher average transition distance. Instead, the contrast law converts directional memory into interface-level spatial divergence under a fixed residual activation budget.

### Interpretation

The precise claim:

```text
Source-target angular-momentum contrast at the residual re-entry gate is a
seed-robust fixed-mean interface-symmetry-breaking law. It beats both the
v0.3.1 angular-memory baseline and signed/no-memory control on interface-union
divergence in 6/6 tested seeds, while all continuations remain bounded,
ledger-exact, and mean-preserving to floating precision.
```

The caveat:

```text
This is still interface-level, not component-level, morphology. Active-set distance
beats both baselines in only half of seeds, and component-count/largest-component
deltas do not move for the contrast variant.
```

The important narrowing:

```text
Candidate ordering changes the transition alphabet but suppresses boundary motion.
Fixed-mean residual contrast changes where the active/depleted boundary re-enters.
That effect is now seed-robust.
```

### Next Gate

Do not tune strength blindly. The next step should keep v0.3.5 contrast `2.0` as the seed-robust baseline and test component-level boundary work at fixed mean.

The next pass gate should require:

```text
interface-union distance remains above both baselines on most seeds
active-set distance beats both baselines on a majority of seeds
component-count, largest-component, or component-entropy deltas move above numerical dust
bounded_nonrunaway_count = 8/8
ledger_exact_count = 8/8
fixed residual probability sum within floating precision
```

### Artifacts

- `output/findings/configs/v035_contrast2_seed*_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2.yaml`
- `output/findings/configs/v035_v031_angular_memory_seed*_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2.yaml`
- `output/findings/configs/v035_signed_control_seed*_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2.yaml`
- `output/findings/finding_044_v035_seed_robustness_pass_table.csv`
- `output/findings/finding_044_v035_seed_robustness_aggregate_by_variant.csv`
- `output/findings/finding_044_v035_seed_robustness_fixed_mean_audit.csv`
- `output/findings/finding_044_v035_seed_robustness_summary.json`
- `output/findings/finding_044_v035_*_rotation_aware_openness_summary.csv`
- `output/findings/finding_044_v035_*_lineage_persistence_summary.csv`
- `output/findings/finding_044_v035_*_lineage_conditioned_morphology_summary.csv`
- `output/findings/finding_044_v035_contrast2_seed*_front_turnover_turnover.csv`
- `output/findings/finding_044_v035_contrast2_seed*_front_turnover_turnover_summary.json`

## Finding 045: Residual Geometry Audit Identifies the Component-Level Lever

Finding 044 established that v0.3.5 source-target contrast is seed-robust at the interface level, but not yet component-level. Finding 045 audits the residual-recruitment opportunities directly before adding a v0.3.6 mechanism.

The audit classifies each eligible depleted re-entry candidate by local active-neighbor geometry:

```text
component_bridge_cube26: activating the site locally connects multiple cube26 active-neighbor groups
local_bridge_face6: activating the site locally connects multiple face6 active-neighbor groups
flat_front: face-adjacent surface continuation with high cube26 support
edge_extension: face-adjacent lower-support extension
tip_seed: very low-support protrusion seed
diagonal_shear: diagonal-only active support
concave_fill: high-support fill-in site
```

The diagnostic preserves the simulation RNG stream by restoring RNG state after candidate enumeration, so the audit does not perturb the run it measures.

### Protocol

Audit target:

```text
baseline: v0.3.5 contrast 2.0
seeds: 42, 43, 44, 45, 46, 56
ticks: 2048
sample interval: 16
residual score mode: source_target_L_contrast
fixed mean: yes
```

### Geometry Opportunity

The current residual-recruitment opportunity distribution is not sparse. Across the six v0.3.5 contrast seeds:

```text
mean eligible candidates/tick:       99.118863
mean unique targets/tick:            69.509044
mean cube26 bridge targets/tick:      6.892765
mean face6 bridge targets/tick:      52.077519
mean flat-front targets/tick:         7.666667
mean tip-seed targets/tick:           0.012920
```

There are enough local bridge/neck opportunities to test component-level boundary work. The issue is not absence of candidate sites.

### Current Contrast Selection by Geometry

Class summary across all sampled ticks and seeds:

| Class | Base share | Biased share | Selection lift | Eligible candidates | Unique target observations | Mean score |
|---|---:|---:|---:|---:|---:|---:|
| `local_bridge_face6` | `0.808766` | `0.819628` | `1.013430` | `62047` | `40308` | `-0.005346` |
| `component_bridge_cube26` | `0.083627` | `0.078142` | `0.934422` | `6399` | `5335` | `-0.043113` |
| `flat_front` | `0.078673` | `0.075800` | `0.963477` | `6038` | `5934` | `-0.033748` |
| `edge_extension` | `0.028415` | `0.025844` | `0.909515` | `2166` | `2156` | `-0.055162` |
| `diagonal_shear` | `0.000369` | `0.000462` | `1.252205` | `56` | `56` | `0.180237` |
| `tip_seed` | `0.000132` | `0.000108` | `0.818888` | `10` | `10` | `-0.100840` |
| `concave_fill` | `0.000020` | `0.000017` | `0.878570` | `2` | `1` | `-0.131258` |

The key result is narrow but actionable:

```text
v0.3.5 slightly amplifies face6-local bridge recruitment, but suppresses the rarer
cube26 component-bridge class that is the most plausible local route to component
morphology.
```

The component bridge class is large enough to matter:

```text
component_bridge_cube26 base probability share:   8.362656%
component_bridge_cube26 biased probability share: 7.814247%
component_bridge_cube26 selection lift:           0.934422
component_bridge_cube26 target observations:      5335
```

This explains the Finding 044 caveat: v0.3.5 moves the interface, but its current contrast law does not preferentially select the sites most likely to change cube26 component morphology.

### Fixed-Mean Check

The audit independently reproduces fixed-mean conservation:

```text
total base probability sum:   1085.1985714285693
total biased probability sum: 1085.1985714285709
total probability delta:      1.859735e-12
max row probability delta:    1.243450e-14
final ledger error:           0.0 for all seeds
```

### Interpretation

The precise claim:

```text
The next component-level lever is not more angular momentum or more residual
participation. It is geometry-conditioned residual re-entry: keep the v0.3.5
source-target contrast law, but add a fixed-mean local bridge/neck preference that
specifically stops suppressing cube26 component-bridge candidates.
```

This is still an audit, not a mechanism result. It identifies where v0.3.6 should intervene.

### Next Gate

v0.3.6 should test a fixed-mean component-bridge residual score:

```text
base score:
  source_target_L_contrast

geometry score:
  positive for component_bridge_cube26
  optional secondary positive for local_bridge_face6
  neutral or negative for flat_front / edge_extension churn

normalization:
  preserve the per-event residual recruitment probability sum
```

Pass criteria:

```text
interface-union distance remains above both baselines on most seeds
active-set distance beats both baselines on a majority of seeds
component-count, largest-component, or component-entropy deltas move above numerical dust
bounded_nonrunaway_count = 8/8
ledger_exact_count = 8/8
fixed residual probability sum within floating precision
```

### Artifacts

- `src/residual_recruitment_geometry_audit.py`
- `output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed*_classes.csv`
- `output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed*_class_summary.csv`
- `output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed*_ticks.csv`
- `output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed*_targets.csv`
- `output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed*_summary.json`
- `output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed_ensemble_class_summary.csv`
- `output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed_ensemble_seed_summary.csv`
- `output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed_ensemble_summary.json`

## Finding 046: Component-Bridge Bias Improves Interface Divergence but Not Robust Component Morphology

Finding 045 identified the missing local lever: v0.3.5 source-target contrast slightly suppressed the `component_bridge_cube26` residual-recruitment class even though that class is the most plausible route to component-level morphology.

Finding 046 implements the direct v0.3.6 test: keep fixed-mean residual recruitment, keep the v0.3.5 source-target contrast law, and add a local geometry preference for component bridges.

### Mechanism

v0.3.6 adds one residual score mode:

```text
angular_momentum_residual_bias_score_mode = source_target_L_contrast_component_bridge
```

The score is:

```text
source_target_L_contrast + local_geometry_weight
```

with fixed-mean per-event renormalization preserved exactly.

The tested weights were intentionally conservative:

```yaml
component_bridge_cube26: 0.25
local_bridge_face6: 0.05
flat_front: -0.05
edge_extension: -0.05
tip_seed: 0.0
diagonal_shear: 0.0
concave_fill: 0.0
ridge_or_corner_fill: 0.0
interface_fill: 0.0
```

### Protocol

Test matrix:

```text
variant: v0.3.6 component_bridge
seeds: 42, 43, 44, 45, 46, 56
checkpoints: 1536, 2048
samples/checkpoint: 8
openness horizon: 256
morphology horizon: 1024
phase length: 256
baseline comparisons:
  v0.3.5 contrast 2.0
  v0.3.1 angular memory
  signed/no-memory control
```

### Fixed-Mean Audit

The fixed-mean audit passed on every seed:

| Seed | Base probability sum | Biased probability sum | Summed delta | Max row delta | Final ledger error |
|---:|---:|---:|---:|---:|---:|
| `42` | `189.551429` | `189.551429` | `3.512746e-13` | `8.881784e-15` | `0.0` |
| `43` | `139.397143` | `139.397143` | `1.917355e-13` | `6.661338e-15` | `0.0` |
| `44` | `182.570000` | `182.570000` | `3.175238e-13` | `7.105427e-15` | `0.0` |
| `45` | `88.910000` | `88.910000` | `5.834222e-14` | `4.440892e-15` | `0.0` |
| `46` | `244.368571` | `244.368571` | `4.805045e-13` | `1.421085e-14` | `0.0` |
| `56` | `239.005714` | `239.005714` | `4.729550e-13` | `1.154632e-14` | `0.0` |

Across the six tested seeds:

```text
fixed_mean_ok_count = 6/6
safety_ok_count = 6/6
max_abs_summed_probability_delta = 4.805045e-13
max_abs_row_probability_delta = 1.421085e-14
```

### Geometry Selection

The mechanism did what it was designed to do. It reversed the v0.3.5 suppression of component bridges:

| Class | Base share | Biased share | Selection lift | Eligible candidates | Unique target observations |
|---|---:|---:|---:|---:|---:|
| `local_bridge_face6` | `0.811189` | `0.813979` | `1.003440` | `62215` | `40274` |
| `component_bridge_cube26` | `0.082043` | `0.095296` | `1.161532` | `6298` | `5289` |
| `flat_front` | `0.075624` | `0.065748` | `0.869412` | `5802` | `5693` |
| `edge_extension` | `0.030195` | `0.024052` | `0.796561` | `2294` | `2287` |

The important class-level result:

```text
component_bridge_cube26 selection lift moved from 0.934422 in v0.3.5 to 1.161532
in v0.3.6, while the residual recruitment budget remained fixed to floating precision.
```

So the mechanism successfully biases bridge-like residual re-entry without adding expected activation.

### Morphology Gate

Per-seed summary:

| Seed | Interface-union | Beats v0.3.5 contrast? | Beats both baselines? | Active distance | Active beats both baselines? | Component nonzero? | Phase-4 interface turnover |
|---:|---:|---|---|---:|---|---|---:|
| `42` | `0.024825` | yes | yes | `0.039552` | no | no | `0.023614` |
| `43` | `0.015373` | no | yes | `0.024845` | no | no | `0.013271` |
| `44` | `0.029815` | no | yes | `0.050657` | yes | no | `0.029584` |
| `45` | `0.015463` | yes | yes | `0.025263` | yes | no | `0.019232` |
| `46` | `0.023164` | yes | yes | `0.040196` | yes | yes | `0.025233` |
| `56` | `0.029975` | yes | yes | `0.048657` | no | no | `0.033185` |

Counts:

```text
interface_union_beats_both_baselines = 6/6
interface_union_beats_v0.3.5_contrast = 4/6
active_distance_beats_both_baselines = 3/6
active_distance_beats_v0.3.5_contrast = 3/6
component_nonzero_seed_count = 1/6
```

### Aggregate Comparison

Mean across all six seeds, two checkpoints, and four phases:

| Variant | Transition distance | Active distance | Depleted distance | Active-interface distance | Interface-union distance | Component count delta | Largest component delta | Phase-4 interface turnover | Safety OK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v0.3.6 component bridge | `0.685436` | `0.038195` | `0.065213` | `0.063479` | `0.023103` | `0.005208` | `0.005208` | `0.024020` | `6/6` |
| v0.3.5 contrast `2.0` | `0.683620` | `0.038007` | `0.065129` | `0.061793` | `0.021926` | `0.000000` | `0.000000` | `0.023446` | `6/6` |
| v0.3.1 angular memory | `0.748006` | `0.035978` | `0.058270` | `0.053058` | `0.017880` | `0.015625` | `0.015625` | `0.018258` | `6/6` |
| signed/no-memory control | `0.742398` | `0.036669` | `0.059559` | `0.055160` | `0.018949` | `0.000000` | `0.000000` | `0.018930` | `6/6` |

v0.3.6 improves the interface-level metrics over v0.3.5 contrast on average:

```text
interface-union distance:      0.021926 -> 0.023103
active-interface distance:     0.061793 -> 0.063479
phase-4 interface turnover:    0.023446 -> 0.024020
```

But the component-level signal remains weak:

```text
component-count/largest-component nonzero movement appears in only seed 46.
active-set distance clears both baselines in only 3/6 seeds.
```

### Interpretation

The precise claim:

```text
Component-bridge residual bias is a valid fixed-mean interface lever: it successfully
amplifies cube26 component-bridge recruitment and improves seed-aggregate
interface-union divergence without violating boundedness, ledger exactness, or
fixed-mean residual recruitment.
```

The caveat:

```text
This is not yet a robust component-morphology result. v0.3.6 produces one nonzero
component seed and modest aggregate component deltas, but component-level morphology
does not clear the majority-seed gate.
```

The narrowing:

```text
The project now knows that the bridge class can be selected at fixed mean, but simply
lifting all cube26 bridge candidates by a conservative amount mostly strengthens the
interface effect. The remaining problem is not access to bridge opportunities; it is
which bridge opportunities are causally component-changing rather than interface-churn.
```

### Next Gate

Do not treat v0.3.6 as solved component morphology. The next step should separate bridge quality from bridge quantity.

Recommended v0.3.7 direction:

```text
component-bridge quality audit / targeted sweep

compare:
  component_bridge_cube26 weight = 0.25, 0.50, 0.75
  with and without local_bridge_face6 = 0.05
  flat_front / edge_extension penalties held fixed or strengthened

diagnose:
  realized residual re-entry events by geometry class
  post-entry component-count and largest-component changes
  seed 46 versus non-responding seeds
```

Pass gate remains:

```text
interface-union distance above both baselines on most seeds
active-set distance above both baselines on a majority of seeds
component-count, largest-component, or component-entropy deltas above numerical dust in a majority of seeds
bounded_nonrunaway_count = 8/8
ledger_exact_count = 8/8
fixed residual probability sum within floating precision
```

### Artifacts

- `src/iota_rig.py`
- `output/findings/configs/v036_component_bridge_seed*_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb2p0_cb0p25_lb0p05_ffn0p05_een0p05.yaml`
- `output/findings/finding_046_v036_component_bridge_pass_table.csv`
- `output/findings/finding_046_v036_component_bridge_aggregate_by_variant.csv`
- `output/findings/finding_046_v036_component_bridge_fixed_mean_audit.csv`
- `output/findings/finding_046_v036_component_bridge_geometry_class_summary.csv`
- `output/findings/finding_046_v036_component_bridge_summary.json`
- `output/findings/finding_046_v036_component_bridge_seed*_rotation_aware_openness_summary.csv`
- `output/findings/finding_046_v036_component_bridge_seed*_lineage_persistence_summary.csv`
- `output/findings/finding_046_v036_component_bridge_seed*_lineage_conditioned_morphology_summary.csv`
- `output/findings/finding_046_v036_component_bridge_seed*_front_turnover_turnover_summary.json`
- `output/findings/finding_046_v036_component_bridge_seed*_residual_geometry_audit_summary.json`

## Finding 047: The First Component Signal Is an Articulation-Source Exhaustion Event

Finding 046 produced one nonzero component seed. The next question was causal:

```text
When component signal appears in the 1/6 seed, what exactly happened?
```

Finding 047 traces the responder continuation against a matched no-component
continuation and logs actual hard-transfer residual recruitment events, not just
candidate opportunities.

### Protocol

Responder:

```text
config:      v0.3.6 component_bridge seed 46
checkpoint:  2048
sample:      6
continuation_seed: 2068260714
horizon:     1024
phase_length: 256
```

Matched no-component comparison:

```text
config:      v0.3.6 component_bridge seed 56
checkpoint:  2048
sample:      6
continuation_seed: 2068260714
horizon:     1024
phase_length: 256
```

The tracer records:

```text
actual residual recruitment events
source-target L contrast and residual multiplier
local residual geometry class
global cube26 neighbor component count
component-count / largest-component change at the event
deactivation events and single-cell articulation removals
active/depleted adjacency before the component signal
target persistence after 1, 16, 64, 128, 256 ticks and at horizon end
```

### Phase Alignment

The trace reproduces the Finding 046 component signal.

Seed 46, checkpoint 2048, sample 6:

| Offset | Active | Depleted | Cube26 components | Largest cube26 | Component entropy | Active/depleted adjacency |
|---:|---:|---:|---:|---:|---:|---:|
| `0` | `1151` | `520` | `16` | `139` | `3.542022` | `0.966985` |
| `256` | `1151` | `525` | `16` | `139` | `3.542022` | `0.980017` |
| `512` | `1151` | `528` | `17` | `138` | `3.549455` | `0.975673` |
| `768` | `1151` | `529` | `16` | `139` | `3.542022` | `0.973936` |
| `1024` | `1151` | `531` | `16` | `139` | `3.542022` | `0.986099` |

The component signal is transient:

```text
first_component_change_offset = 512
component_signal_offsets = 512, 513, 514
component_signal_vanish_offset = 515
```

Seed 56, same checkpoint/sample/continuation stream:

```text
cube26 components remain 17 throughout offsets 0, 256, 512, 768, 1024.
largest cube26 remains 141 throughout.
```

### Causal Chain

The component split is not caused by a high-L bridge recruitment directly changing
component count.

It is caused by a residual recruitment from a source cell that later becomes a
cube26 articulation point, followed by exhaustion of that source cell.

Key responder chain:

| Offset | Event | Source | Target | Geometry | L contrast | Multiplier | Component effect |
|---:|---|---|---|---|---:|---:|---|
| `499` | residual recruitment | `(12,3,38)` | `(13,3,38)` | `local_bridge_face6` | `-0.008958` | `0.990998` | latest activation of future articulation source |
| `512` | residual recruitment | `(13,3,38)` | `(12,2,38)` | `local_bridge_face6` | `0.142720` | `1.228732` | creates new active territory, no immediate component-count delta |
| `512` | deactivation | `(13,3,38)` | — | cube26 articulation removal | — | — | component count `+1`, largest component `-2` |
| `515` | residual recruitment | `(12,2,38)` | `(13,2,38)` | `component_bridge_cube26` | `0.411423` | `1.335856` | component count `-1`, largest component `+2` |

The exact split event:

```text
offset 512:
  cell (13,3,38) deactivates with A=0
  latest residual activation offset for that cell = 499
  age since latest residual activation = 13 ticks
  single_removal_component_count_delta = +1
  single_removal_largest_delta = -2
  neighbor_component_sizes_after_removal = 138;1
```

So the component signal is a one-cell singleton split from the main component by
the exhaustion of an articulation source.

The exact re-bridge event:

```text
offset 515:
  source (12,2,38) recruits target (13,2,38)
  event_geometry_class = component_bridge_cube26
  global_neighbor_component_count_pre = 2
  global_neighbor_component_sizes_pre = 138;1
  component_count_delta_event = -1
  largest_delta_event = +2
```

This closes the transient split and returns cube26 component count to baseline.

### Responder vs Non-Responder

The no-component seed did not lack residual events or bridge-looking local geometry.
It lacked the global event class that actually moved component count.

| Case | Residual events | Local component-bridge events | High `|L|` contrast events | Global bridge events | Articulation deactivations | Component signal |
|---|---:|---:|---:|---:|---:|---|
| seed 46 responder | `1010` | `109` | `40` | `1` | `1` | yes |
| seed 56 no-component | `1214` | `154` | `42` | `0` | `0` | no |

This is the important negative control. Seed 56 has more residual events, more
local component-bridge-class events, and a similar count of high-contrast events,
but no component signal.

### Interpretation

The first component-level signal is not "more component bridges" in the simple
local-class sense.

It is this event class:

```text
residual recruitment from a soon-exhausted articulation source, creating a small
active appendage/singleton, followed by source deactivation that splits the cube26
component.
```

The component signal is then erased by the complementary event class:

```text
global cube26 bridge recruitment between the singleton and the main component.
```

The source-target angular momentum contrast is present but not the decisive
feature in the split event:

```text
split-producing recruitment L_contrast = 0.142720
split-producing geometry = local_bridge_face6
split-producing residual_score = 0.166530
```

The re-bridge event has stronger contrast and the intended bridge geometry:

```text
re-bridge L_contrast = 0.411423
re-bridge geometry = component_bridge_cube26
re-bridge residual_score = 0.012465
```

The responder boundary had already changed before component count moved:

```text
active/depleted adjacency at checkpoint = 0.966985
active/depleted adjacency before signal = 0.976542
pre-signal adjacency delta = +0.009557
```

So Finding 047 converts the v0.3.6 partial positive into a sharper mechanism:

```text
interface divergence becomes component divergence when residual recruitment and
deactivation combine to remove a cube26 articulation point, not merely when a
candidate is locally classified as a component bridge.
```

### Next Gate

Do not increase component-bridge weight yet.

The next diagnostic should test whether this event class is seed-specific or
available but under-selected:

```text
articulation-source bridge audit across v0.3.6 seeds/samples

measure:
  residual recruitments from low-A / soon-exhausted sources
  source cells whose removal increases cube26 component count
  residual events that create singleton or small-component appendages
  global bridge closures that erase component splits
  active/depleted adjacency lead time before articulation events
```

Only after that audit should a v0.3.7 scoring law be considered.

Candidate v0.3.7 design principle:

```text
fixed-mean residual recruitment should bias bridge quality, not bridge quantity:
prefer events that create persistent nontrivial component separation, or delay
immediate re-bridging, without increasing total residual participation.
```

### Artifacts

- `src/component_bridge_causal_trace.py`
- `output/findings/finding_047_component_bridge_causal_trace_seed46_sample6_events.csv`
- `output/findings/finding_047_component_bridge_causal_trace_seed46_sample6_deactivations.csv`
- `output/findings/finding_047_component_bridge_causal_trace_seed46_sample6_timeline.csv`
- `output/findings/finding_047_component_bridge_causal_trace_seed46_sample6_summary.json`
- `output/findings/finding_047_component_bridge_causal_trace_seed56_sample6_events.csv`
- `output/findings/finding_047_component_bridge_causal_trace_seed56_sample6_deactivations.csv`
- `output/findings/finding_047_component_bridge_causal_trace_seed56_sample6_timeline.csv`
- `output/findings/finding_047_component_bridge_causal_trace_seed56_sample6_summary.json`
- `output/findings/finding_047_component_bridge_causal_trace_comparison.csv`
- `output/findings/finding_047_component_bridge_causal_trace_comparison.json`
- `output/findings/finding_047_component_bridge_causal_trace_chain.csv`

## Finding 048: Support-weighted recruitment stabilizes interface divergence but erases component transients

### Question

Finding 047 showed that the first v0.3.6 component signal was not caused by
more local component-bridge candidates. It came from a residual recruitment
through a source cell that later exhausted as a cube26 articulation point,
creating a three-tick singleton split before a later bridge closed it.

The v0.3.7 test asked whether fixed-mean residual recruitment could favor more
structurally supported recruits while preserving the same mean residual
participation budget:

```text
v0.3.7 support-weighted fixed-mean residual recruitment

score mode:
  source_target_L_contrast_support_weighted

support terms:
  multiple active neighbors
  multiple distinct source components
  supported component bridges
  non-articulation target support
  source amplitude/support continuity
  source exhaustion/articulation penalties

seeds:
  42, 43, 44, 45, 46, 56

checkpoints:
  1536 and 2048

samples:
  8 per checkpoint
```

### Result

The fixed-mean and safety gates pass:

```text
bounded + ledger exact seeds:       6 / 6
fixed-mean audit seeds:             6 / 6
max total probability delta:        5.043743e-13
max per-sample probability delta:   1.421085e-14
mean component_bridge selection lift: 1.147569
mean local_bridge selection lift:     1.003227
```

Aggregate morphology:

| Variant | Interface-union distance | Active distance | Component-count delta | Largest-comp delta | Phase-4 active-interface turnover |
|---|---:|---:|---:|---:|---:|
| `support_weighted` | `0.024344` | `0.040127` | `0.000000` | `0.000000` | `0.026020` |
| `component_bridge` | `0.023103` | `0.038195` | `0.005208` | `0.005208` | `0.024020` |
| `contrast2` | `0.021926` | `0.038007` | `0.000000` | `0.000000` | `0.023446` |
| `v031_angular_memory` | `0.017880` | `0.035978` | `0.015625` | `0.015625` | `0.018258` |
| `signed_control` | `0.018949` | `0.036669` | `0.000000` | `0.000000` | `0.018930` |

Per-seed gates:

```text
interface-union beats v0.3.6 component_bridge: 4 / 6
interface-union beats v0.3.5 contrast2:        6 / 6
interface-union beats v0.3.1 and signed:       6 / 6
active distance beats v0.3.6 component_bridge: 4 / 6
active distance beats v0.3.5 contrast2:        5 / 6
active distance beats v0.3.1 and signed:       2 / 6
nonzero component morphology seeds:            0 / 6
```

### Seed-46 Causal Check

The direct repeat of Finding 047's responder continuation no longer produces a
component signal:

| Case | Residual events | Local component-bridge events | High `|L|` contrast events | Global bridge events | Articulation deactivations | Component signal |
|---|---:|---:|---:|---:|---:|---|
| v0.3.6 seed46/sample6 | `1010` | `109` | `40` | `1` | `1` | `512, 513, 514` |
| v0.3.7 seed46/sample6 | `802` | `59` | `32` | `0` | `0` | none |

The v0.3.7 trace still creates bridge-class recruitments, but no source
deactivation removes a cube26 articulation point:

```text
component_count_checkpoint = 16
component_count_final = 16
largest_checkpoint = 141
largest_final = 141
articulation_deactivation_count = 0
ledger_exact = 1
```

### Interpretation

v0.3.7 is a useful negative/partial-positive result.

It improves fixed-mean interface divergence and aggregate active-set divergence
relative to v0.3.6/v0.3.5 while preserving boundedness and ledger exactness.
It also preferentially selects the intended component-bridge class.

But it does not convert interface divergence into component morphology. In the
critical seed-46 continuation, the support/source-continuity terms removed the
articulation-source failure mode that generated the v0.3.6 component transient,
instead of converting it into a persistent component-level structure.

So the missing mechanism is sharper:

```text
component morphology requires controlled articulation turnover, not blanket
articulation suppression.
```

Support is good for interface stability, but the component gate needs a
persistence-aware articulation mechanism: preserve newly recruited bridges long
enough to matter, while still allowing selected articulation events to create
nontrivial component separation.

### Next Gate

The next test should not add more bridge quantity.

The next test should isolate articulation turnover with fixed mean activation:

```text
v0.3.8 articulation-persistence audit / score

measure or bias:
  source cells that would be articulation points after recruitment
  recruits that create singleton vs nontrivial component separation
  source exhaustion risk over the next few ticks
  bridge closures that erase component splits
  minimum persistence window for new component signal

constraint:
  residual participation budget remains fixed mean
```

Success now requires:

```text
interface-union remains above v0.3.5/v0.3.1/signed baselines
active distance does not regress below v0.3.6 aggregate
component-count/largest-component/entropy signal appears in multiple seeds
component signal persists beyond a few ticks
boundedness, ledger exactness, and fixed-mean audit remain 6 / 6
```

### Artifacts

- `src/iota_rig.py`
- `src/residual_recruitment_geometry_audit.py`
- `src/component_bridge_causal_trace.py`
- `output/findings/finding_048_v037_support_weighted_pass_table.csv`
- `output/findings/finding_048_v037_support_weighted_aggregate_by_variant.csv`
- `output/findings/finding_048_v037_support_weighted_summary.json`
- `output/findings/finding_048_v037_support_weighted_seed46_sample6_causal_trace_summary.json`
- `output/findings/finding_048_v037_support_weighted_seed46_sample6_causal_trace_events.csv`
- `output/findings/finding_048_v037_support_weighted_seed46_sample6_causal_trace_deactivations.csv`
- `output/findings/finding_048_v037_support_weighted_seed46_sample6_causal_trace_timeline.csv`

---

## Finding 049 — Seed-46 erase-and-replay isolates the component-bridge causal channel

### Question

Finding 047 showed the first v0.3.6 component signal in seed46/sample6 was not
caused by bridge quantity alone. The decisive chain was:

```text
offset 499:
  residual recruitment (12,3,38) -> (13,3,38)
  reactivates the future articulation source

offset 512:
  residual recruitment (13,3,38) -> (12,2,38)
  then source (13,3,38) exhausts as a cube26 articulation
  component count rises by +1 for three ticks

offset 515:
  residual recruitment (12,2,38) -> (13,2,38)
  global bridge closes the split
```

The new test asked whether the offset-499 kick matters because of inherited
angular/vector memory, or because it places active state at the exact geometric
channel that later permits articulation turnover.

### Method

A deterministic erase-and-replay runner was added for the same checkpoint,
sample, continuation seed, RNG stream, and 1024-tick horizon:

```text
natural:
  unchanged v0.3.6 replay

erase_pivotal_transfer:
  after offset 499, restore source and target to their pre-kick state
  ledger remains exact by restoring the transferred amplitude to the source

erase_pivotal_L:
  preserve activation/A/R/V/P, but restore the target angular_L to pre-kick

erase_pivotal_memory:
  preserve activation and amplitude, but restore target R/V/P/angular_L

transplant_pivotal_state:
  move the post-kick target state from (13,3,38) to matched nearby depleted site
  (12,3,37), preserving source exhaustion and ledger exactness
```

### Result

All variants remained ledger exact with final ledger error `0.0`.

| Variant | Component signal | Split at 512 | Rebridge at 515 | Pivotal target active 499/511/512 | Residual events | Deactivations | Articulation deactivations |
|---|---:|---:|---:|---|---:|---:|---:|
| `natural` | `512;513;514` | `1` | `1` | `1/1/0` | `1010` | `1021` | `1` |
| `erase_pivotal_transfer` | none | `0` | `0` | `0/0/0` | `998` | `1010` | `0` |
| `erase_pivotal_L` | `512;513;514` | `1` | `1` | `1/1/0` | `1010` | `1021` | `1` |
| `erase_pivotal_memory` | `512;513;514` | `1` | `1` | `1/1/0` | `969` | `980` | `1` |
| `transplant_pivotal_state` | none | `0` | `0` | `0/0/0` | `963` | `975` | `0` |

The exact split event also survives angular-memory erasure:

| Variant | Offset-512 causal event | `L_contrast` | Multiplier | Component effect |
|---|---|---:|---:|---|
| `natural` | `(13,3,38) -> (12,2,38)` | `0.142720` | `1.228732` | split appears after source deactivation |
| `erase_pivotal_L` | `(13,3,38) -> (12,2,38)` | `0.001452` | `1.040684` | split still appears |
| `erase_pivotal_memory` | `(13,3,38) -> (12,2,38)` | `0.001452` | `1.040952` | split still appears |

### Interpretation

The offset-499 kick is necessary, but not because its inherited `angular_L` or
target vector state is necessary.

The necessary property is the exact active-state placement and timing:

```text
the pivotal site must be active at (13,3,38) through offset 511,
then spend its last amplitude into (12,2,38) at offset 512,
then disappear as a cube26 articulation point.
```

Moving the same post-kick consequence to a nearby matched depleted site removes
the component signal. Deleting the transfer removes the component signal.
Erasing angular/vector memory while preserving active placement does not.

This makes the causal channel sharper:

```text
component morphology begins when a residual recruitment creates a future
articulation source at the exact interface location where a later compatible
kick can spend it into bridge territory.
```

So the next mechanism should not be post-split protection or more bridge
quantity. The next diagnostic should identify pre-articulation causal channels:
newly reactivated cells that become future articulation sources, remain active
long enough to kick into compatible bridge territory, and then exhaust in a way
that creates nontrivial component separation.

### Artifacts

- `src/component_bridge_erase_replay.py`
- `output/findings/finding_049_seed46_erase_replay_summary.csv`
- `output/findings/finding_049_seed46_erase_replay_summary.json`
- `output/findings/finding_049_seed46_erase_replay_interventions.csv`
- `output/findings/finding_049_seed46_erase_replay_windows.csv`
- `output/findings/finding_049_seed46_erase_replay_events.csv`
- `output/findings/finding_049_seed46_erase_replay_deactivations.csv`
- `output/findings/finding_049_seed46_erase_replay_timeline.csv`

---

## Finding 050 — Payload is not part of the birth event, but can scaffold the pre-birth microstate

### Question

Finding 049 showed that the seed46/sample6 component split survives erasure of
the pivotal site's `R/V/P/angular_L` memory as long as exact active placement and
timing remain intact. That suggested a sharper hypothesis:

```text
complexity arises from constrained interaction history, not semantic payload.
```

The payload ablation ladder tested three levels:

```text
neutral_payload_coupling:
  force same_payload_coupling = cross_payload_coupling = 1.0

uniform_payload_initial:
  set P = 0 before replay, then let the normal rule run

clamp_payload_each_tick:
  set P = 0 before and after every tick
```

The ladder was run in two modes:

```text
checkpoint mode:
  start from the saved v0.3.6 checkpoint at tick 2048

init mode:
  regenerate the tick-2048 checkpoint from the initial condition first,
  with payload ablation active from tick zero
```

### Checkpoint-Mode Result

At the saved v0.3.6 tick-2048 checkpoints, payload was already collapsed:

```text
active payload values: [0]
all-grid payload values: [0]
checkpoint payload entropy: -0.0
```

For the known seed46/sample6 birth trajectory, all payload ablations were
bit-identical outside the payload array:

| Variant | Component signal | Split at 512 | Rebridge at 515 | Same non-payload state as natural |
|---|---:|---:|---:|---:|
| `natural` | `512;513;514` | `1` | `1` | reference |
| `neutral_payload_coupling` | `512;513;514` | `1` | `1` | `1` |
| `uniform_payload_initial` | `512;513;514` | `1` | `1` | `1` |
| `clamp_payload_each_tick` | `512;513;514` | `1` | `1` | `1` |

The six-seed sample-6 checkpoint smoke set also matched exactly:

| Seed | Natural signal | `P=0` clamped signal | Same non-payload state |
|---:|---|---|---:|
| `42` | none | none | `1` |
| `43` | none | none | `1` |
| `44` | `244;245;246;247;248` | `244;245;246;247;248` | `1` |
| `45` | none | none | `1` |
| `46` | `512;513;514` | `512;513;514` | `1` |
| `56` | none | none | `1` |

Checkpoint-mode aggregate:

```text
cases:                              6
component-signal cases natural:      2
component-signal cases P=0 clamped:  2
same component signal vs natural:    6 / 6
same non-payload state vs natural:   6 / 6
ledger exact:                        6 / 6
```

### Init-Mode Result

The stronger from-init seed46/sample6 test gives the necessary caveat:

| Variant | Component signal | Split at 512 | Rebridge at 515 | Checkpoint largest | Final active | Same non-payload state |
|---|---:|---:|---:|---:|---:|---:|
| `natural` | `512;513;514` | `1` | `1` | `139` | `1151` | reference |
| `neutral_payload_coupling` | `512;513;514` | `1` | `1` | `139` | `1151` | `1` |
| `uniform_payload_initial` | none | `0` | `0` | `145` | `1125` | `0` |
| `clamp_payload_each_tick` | none | `0` | `0` | `145` | `1125` | `0` |

Neutralizing payload compatibility does nothing, because v0.3.6 already used
`same_payload_coupling = cross_payload_coupling = 1.0`.

Removing payload state from tick zero changes the checkpoint microstate. It does
not change the component count at checkpoint (`16` in both cases), but it changes
the largest component (`139 -> 145`), active count by the end of continuation
(`1151 -> 1125`), and eliminates the future articulation channel:

```text
(13,3,38) active at offset 499:
  natural: 1
  P=0 from init: 0

component signal:
  natural: 512;513;514
  P=0 from init: none
```

### Interpretation

Payload is not part of the birth event itself. By the time the v0.3.6 component
birth trajectory begins at checkpoint 2048, payload has collapsed to a uniform
zero field and can be removed without changing any non-payload state or component
signal.

But payload can scaffold the formation of the pre-birth microstate. Its role is
not semantic compatibility: neutral payload coupling is exactly inert. The
remaining upstream role is phase-like: early `P` values can influence vector
diffusion/rotation history before they collapse, thereby selecting a later
topological state.

The safe conclusion is:

```text
Payload is not irreducible information at the birth event.
It is an upstream symmetry-breaking scaffold for producing some microstates.
```

This supports the austere hypothesis with a caveat:

```text
information is carried by interaction constraints at the moment of birth,
but early payload-like phase variables may help generate those constraints.
```

The next reduction target should not be payload semantics. It should be replacing
early payload phase with a non-semantic relational phase or deterministic
geometry/history phase, then checking whether the same pre-birth microstates and
component channels can be recovered without a payload field.

### Artifacts

- `src/payload_ablation_replay.py`
- `output/findings/finding_050_payload_ablation_seed46_sample6_summary.csv`
- `output/findings/finding_050_payload_ablation_seed46_sample6_summary.json`
- `output/findings/finding_050_payload_ablation_seed46_sample6_pairs.csv`
- `output/findings/finding_050_payload_ablation_seed46_sample6_timeline.csv`
- `output/findings/finding_050_payload_ablation_seedset_sample6_summary.csv`
- `output/findings/finding_050_payload_ablation_seedset_sample6_summary.json`
- `output/findings/finding_050_payload_ablation_seedset_sample6_pairs.csv`
- `output/findings/finding_050_payload_ablation_seedset_sample6_timeline.csv`
- `output/findings/finding_050_payload_ablation_from_init_seed46_sample6_summary.csv`
- `output/findings/finding_050_payload_ablation_from_init_seed46_sample6_summary.json`
- `output/findings/finding_050_payload_ablation_from_init_seed46_sample6_pairs.csv`
- `output/findings/finding_050_payload_ablation_from_init_seed46_sample6_timeline.csv`

---

## Finding 051 — Payload's upstream role is action-phase selection

### Question

Finding 050 showed that payload is not part of the component-birth event at the
v0.3.6 tick-2048 checkpoint, but that removing `P` from initialization changes
the checkpoint microstate and removes the later seed46/sample6 component split.

The next question was which current `P` path does the upstream work:

```text
semantic compatibility?
diffuse/vector action selection?
history-coupled rotation offset?
payload takeover rotation?
some hidden persistent payload memory?
```

### Method

A from-init action-path audit was added for v0.3.6 seed46/sample6:

```text
natural:
  unchanged run from init through checkpoint 2048 and continuation 1024

no_payload_vector_step:
  call vector_step with p=0, preserving P state elsewhere

no_payload_rotation_offset:
  ignore source/target P in history-coupled rotation offsets

no_payload_rotate_takeover:
  rotate by payload 0 on payload takeover

no_payload_all_action_paths:
  ignore P in vector_step, rotation offsets, and takeover rotation

clamp_payload_each_tick:
  set P=0 before and after every tick
```

The audit tracked:

```text
nonzero payload iotas
P-sensitive primary-action count
first non-payload state divergence from natural
checkpoint active/component/largest metrics
causal cell occupancy at offsets 499/511/512/515
component signal offsets
```

### Result

Payload acts only early, then disappears:

| Tick | Active iotas | Nonzero `P` iotas | `P`-sensitive primary actions | Payload entropy |
|---:|---:|---:|---:|---:|
| `0` | `16` | `13` | `1` | `2.655639` |
| `1` | `77` | `46` | `6` | `2.469358` |
| `2` | `227` | `8` | `1` | `0.296006` |
| `5` | `1046` | `3` | `1` | `0.032900` |
| `64` | `1144` | `0` | `0` | `-0.0` |
| `2048` | `1151` | `0` | `0` | `-0.0` |

Every action-path ablation diverges from natural at tick `1`, while the component
count and largest component are still unchanged. The action-phase difference is
therefore upstream of later topology:

```text
first non-payload divergence tick: 1
stage: precheckpoint
natural nonzero-P iotas at divergence: 46
natural P-sensitive primary actions at divergence: 6
natural component count / largest: 15 / 11
variant component count / largest: 15 / 11
```

By checkpoint 2048, `P` is gone everywhere, but its early action choices have
selected different later microstates:

| Variant | Component signal | Split 512 | Rebridge 515 | Checkpoint active | Checkpoint largest | Causal cell active at 499/511/512 |
|---|---:|---:|---:|---:|---:|---|
| `natural` | `512;513;514` | `1` | `1` | `1151` | `139` | `1/1/0` |
| `no_payload_vector_step` | none | `0` | `0` | `1151` | `141` | `0/0/0` |
| `no_payload_rotation_offset` | none | `0` | `0` | `1177` | `139` | `0/0/0` |
| `no_payload_rotate_takeover` | `444;445;888;889` | `0` | `0` | `1165` | `153` | `0/0/0` |
| `no_payload_all_action_paths` | none | `0` | `0` | `1125` | `145` | `0/0/0` |
| `clamp_payload_each_tick` | none | `0` | `0` | `1125` | `145` | `0/0/0` |

The all-action-path ablation and full `P=0` clamp are identical outside the
payload array:

```text
no_payload_all_action_paths state_hash_without_payload:
  b6937a72bea4bfab17704b51495b075bd93e328e105ad31ab4bcf17d2077e561

clamp_payload_each_tick state_hash_without_payload:
  b6937a72bea4bfab17704b51495b075bd93e328e105ad31ab4bcf17d2077e561
```

### Interpretation

Finding 051 closes the main ambiguity left by Finding 050.

`P` is not acting through semantic compatibility: same/cross payload coupling is
already neutral. It is also not persistent memory: `P` is zero everywhere by tick
64 and remains zero at checkpoint 2048.

The causal role of `P` is early action-phase selection:

```text
P changes early vector/diffuse choices,
P changes early history-coupled rotation offsets,
P changes early takeover rotations,
then P collapses,
while the geometric consequences persist as the future interaction graph.
```

The important negative result is that removing any one action path is enough to
destroy the exact seed46 offset-512 birth channel. Removing the takeover-rotation
path still permits component signals, but at different offsets (`444;445;888;889`)
and not through the Finding 049 causal channel.

So the right abstraction is:

```text
payload is a transient action-phase selector,
not a message and not irreducible information.
```

The next implementation should replace `P` with an explicit finite action-state
variable whose only allowed effects are:

```text
select among legal vector/diffuse actions
select among legal rotation offsets
select takeover rotation phase
decay/reset after acting
never alter energy, occupancy, or admissibility directly
```

The test is not exact global replay. The first success gate is narrower:

```text
recover the seed46 pre-birth articulation channel without semantic payload:
  (13,3,38) active at offsets 499 and 511,
  (12,2,38) active at offset 512,
  component signal at or near the offset-512 gate,
  ledger exact,
  P/action state collapsed or reset before birth.
```

### Artifacts

- `src/payload_action_phase_audit.py`
- `output/findings/finding_051_payload_action_phase_seed46_sample6_summary.csv`
- `output/findings/finding_051_payload_action_phase_seed46_sample6_summary.json`
- `output/findings/finding_051_payload_action_phase_seed46_sample6_pairs.csv`
- `output/findings/finding_051_payload_action_phase_seed46_sample6_timeline.csv`

---

## Finding 052 — Transient action-phase state exactly replaces payload

### Question

Finding 051 proved that `P` is an early action selector, not a semantic payload
or persistent message. Finding 052 asked whether the same behavior can be
reproduced while deleting payload from the iota state and carrying only a
separate transient action-phase side state.

The test was equivalence, not improvement:

```text
Can action-phase state reproduce the current payload-generated trajectory exactly
outside the deleted payload representation?
```

### Method

A lockstep audit compared two systems from identical v0.3.6 initial conditions:

```text
legacy:
  normal P array in the World state

replacement:
  World.P is held at zero at every recorded tick
  a separate action_phase array supplies the old P value only during step()
  after step(), the produced phase is copied back into action_phase
  World.P is immediately reset to zero
```

The replacement therefore preserves the current action-selection semantics but
removes payload as an iota-carried field at rest.

The audit compared every tick from initialization through:

```text
checkpoint: 2048
continuation horizon: 1024
total compared ticks per case: 3073
```

For each tick it required:

```text
non-payload state hash equality
action_phase == legacy P
replacement World.P == 0
RNG state equality
ledger exactness
component signal equality
```

### Seed46 Result

The known seed46/sample6 birth trajectory is exactly preserved:

```text
ticks compared:                 3073
non-payload equal ticks:         3073 / 3073
phase equal ticks:               3073 / 3073
replacement payload-zero ticks:  3073 / 3073
RNG equal ticks:                 3073 / 3073
ledger exact:                    1
phase collapse tick:             18
checkpoint phase nonzero iotas:  0
final phase nonzero iotas:       0
component signal:                512;513;514
split at 512:                    1
rebridge at 515:                 1
```

The Finding 049 channel is preserved:

```text
(13,3,38) active at offset 499: 1
(13,3,38) active at offset 511: 1
(12,2,38) active at offset 512: 1
(13,2,38) active at offset 515: 1
```

### Six-Seed Smoke Result

The six-seed sample-6 set used in Finding 050 also passes exact equivalence:

| Seed | Component signal | Ticks exact | Replacement `P=0` ticks | RNG exact | Phase collapse tick |
|---:|---|---:|---:|---:|---:|
| `42` | none | `3073/3073` | `3073/3073` | `3073/3073` | `11` |
| `43` | none | `3073/3073` | `3073/3073` | `3073/3073` | `81` |
| `44` | `244;245;246;247;248` | `3073/3073` | `3073/3073` | `3073/3073` | `11` |
| `45` | none | `3073/3073` | `3073/3073` | `3073/3073` | `26` |
| `46` | `512;513;514` | `3073/3073` | `3073/3073` | `3073/3073` | `18` |
| `56` | none | `3073/3073` | `3073/3073` | `3073/3073` | `86` |

Aggregate:

```text
cases:                         6
exact non-payload cases:        6 / 6
exact phase cases:              6 / 6
replacement payload-zero cases: 6 / 6
RNG exact cases:                6 / 6
ledger exact cases:             6 / 6
component-signal cases:         2 / 6
split-at-512 cases:             1 / 6
rebridge-at-515 cases:          1 / 6
```

### Interpretation

This is the semantic-preserving replacement result.

Payload can be removed from the iota state at rest and replaced with an explicit
transient action-phase variable without changing any tested non-payload dynamics.
The phase still exists, but it is no longer represented as semantic content
carried by an iota.

The cleaner ontology is:

```text
an interaction can leave a transient constraint on the next legal action;
that constraint is extinguished after action selection.
```

Finding 052 does not yet prove that action phase is fundamental. It proves that
payload is not fundamental. The current numeric phase can be factored out of the
world payload field and treated as an implementation of interaction history.

The next reduction ladder is now well defined:

```text
1. explicit 0..7 transient action_phase side state
2. finite action-mode state plus locally derived phase
3. binary action-enabled state plus locally derived action type
4. no stored action state: derive action selection directly from the interaction event
```

The next gate should try to remove the numeric phase storage while preserving the
seed46 pre-birth articulation channel.

### Artifacts

- `src/action_state_equivalence_audit.py`
- `output/findings/finding_052_action_state_equivalence_seed46_sample6_summary.csv`
- `output/findings/finding_052_action_state_equivalence_seed46_sample6_summary.json`
- `output/findings/finding_052_action_state_equivalence_seed46_sample6_timeline.csv`
- `output/findings/finding_052_action_state_equivalence_seedset_sample6_summary.csv`
- `output/findings/finding_052_action_state_equivalence_seedset_sample6_summary.json`
- `output/findings/finding_052_action_state_equivalence_seedset_sample6_timeline.csv`

---

## Finding 053 — Numeric action phase is not locally derivable under the current law

### Question

Finding 052 removed payload from the iota state at rest by moving the current
`P=0..7` value into a transient side-state `action_phase`. Finding 053 asked
whether the numeric phase itself can be removed:

```text
Can the required action outcome be derived from the interaction path and local
non-payload state, using only a finite action mode or no stored phase?
```

The intended pass gate was exact preservation while both `World.P` and stored
numeric `action_phase` are absent.

### Method

The derivability audit instrumented the three payload-sensitive action paths
identified in Finding 051:

```text
vector_step
rotate_takeover
rotation_offset / signed_rotation_offset
```

For each phase-sensitive call, the audit recorded:

```text
non-payload signature:
  action path
  vector state / behavior
  source and target non-payload state used by the action formula
  candidate order, target-depleted flag, influence, max offset

phase key:
  source_p and target_p, or takeover payload

result:
  vector step, rotated vector, or rotation offset
```

The key test was collision-based:

```text
If the same non-payload signature requires different action results for
different phase values, a finite action mode plus local derivation cannot exactly
replace numeric phase under the current law.
```

The audit used the same six-seed v0.3.6 sample-6 smoke set as Finding 052:

```text
42, 43, 44, 45, 46, 56
```

### Six-Seed Result

All six seeds fail the no-numeric-phase derivability gate:

| Seed | Collapse tick | Max nonzero phase iotas | Vector result collisions | Takeover result collisions | Rotation result collisions | Signed rotation result collisions | Numeric phase eliminable |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `42` | `11` | `32` | `0` | `0` | `6` | `6` | `0` |
| `43` | `81` | `34` | `0` | `2` | `7` | `12` | `0` |
| `44` | `11` | `21` | `0` | `0` | `7` | `8` | `0` |
| `45` | `26` | `17` | `0` | `0` | `2` | `3` | `0` |
| `46` | `18` | `46` | `0` | `2` | `3` | `9` | `0` |
| `56` | `86` | `35` | `0` | `0` | `0` | `3` | `0` |

Aggregate:

```text
mode-only locally derivable cases:     0 / 6
numeric-phase eliminable cases:        0 / 6
vector-step result collision cases:    0 / 6
takeover result collision cases:       2 / 6
rotation result collision cases:       5 / 6
signed-rotation result collision cases:6 / 6
```

The vector-step path is compressible in this audit. The blocker is rotation:
the current rotation formulas explicitly require phase-like information that is
not contained in the audited non-payload local signature.

### Seed46 Details

Seed46/sample6 is the known component-birth case. Its phase still collapses
early:

```text
initial nonzero phase iotas: 13
initial phase unique:        7
max nonzero phase iotas:     46
last nonzero phase tick:     17
phase collapse tick:         18
final nonzero phase iotas:   0
```

But before collapse, the same non-payload signatures require different
phase-conditioned outcomes:

```text
vector_step:
  events: 126
  result collision signatures: 0

rotate_takeover:
  events: 46
  result collision signatures: 2

rotation_offset:
  events: 236
  result collision signatures: 3

signed_rotation_offset:
  events: 236
  result collision signatures: 9
```

Representative seed46 collisions:

```text
rotate_takeover signature:
  behavior=reflect, v_idx=39

phase outcomes:
  p=3 -> rotated_v=42
  p=7 -> rotated_v=46

rotation_offset signature:
  source_v=44, target_v=0, target_a=0, target_r=0,
  candidate_order=0, target_depleted=false,
  influence=0.214285714286, max_offset=3

phase outcomes:
  source_p=3,target_p=0 -> offset=1
  source_p=7,target_p=0 -> offset=3
```

Those are decisive collisions: the current law cannot reconstruct the exact
action result from the action mode plus local non-payload signature alone.

### Interpretation

Finding 053 is a negative result, but it sharpens the ontology.

Finding 052 proved:

```text
payload is not fundamental;
World.P can be zero at rest while exact dynamics are preserved by transient
action_phase.
```

Finding 053 adds:

```text
the current numeric phase is not yet eliminable by local derivation under the
existing rotation/takeover formulas.
```

The remaining phase is not semantic content. It is short-lived action entropy:
seeded at initialization, inherited or transduced by early interactions, then
extinguished by ticks `11..86` across the six-seed smoke set. Its consequences
persist through the geometry, but the numeric carrier itself disappears early.

So the reduction ladder changes:

```text
1. explicit 0..7 transient action_phase side state      [passed Finding 052]
2. finite action-mode state plus locally derived phase  [failed Finding 053]
3. no stored action state                               [blocked by 2]
```

The next step should not be the minimal coherence seed ladder yet. That ladder
would still be confounded by this short-lived numeric phase. The next clean move
is a phase-source minimization test:

```text
replace current phase-dependent rotation/takeover formulas with phase-free
local formulas, or derive phase from a deterministic interaction-event property,
then test whether the seed46 pre-birth articulation channel survives by
mechanism rather than exact replay.
```

Exact replay is not the right gate for that rewrite. The gate should be:

```text
recover the same causal class:
  early transient action constraint,
  phase/action state extinguished before birth,
  seed46-style articulation channel,
  ledger exactness,
  component signal or matched bridge dependency,
  no semantic payload field.
```

### Artifacts

- `src/action_phase_derivability_audit.py`
- `output/findings/finding053/action_phase_derivability_summary.csv`
- `output/findings/finding053/action_phase_derivability_paths.csv`
- `output/findings/finding053/action_phase_derivability_collisions.csv`
- `output/findings/finding053/action_phase_derivability_timeline.csv`
- `output/findings/finding053/action_phase_derivability_local_collisions.csv`

---

## Finding 054 — Local phase-source rewrites do not preserve the seed46 birth channel

### Question

Finding 053 showed that the current numeric action phase cannot be reconstructed
from audited local non-payload signatures under the existing law. Finding 054
tested the next clean option:

```text
Can stored numeric phase be removed by replacing it with deterministic
interaction-local phase sources, while preserving the seed46 component-birth
causal class?
```

The gate was not exact replay. The gate was mechanism preservation:

```text
World.P = 0 at rest,
no stored numeric action_phase,
ledger exact,
seed46 pre-birth articulation channel survives,
component signal appears near the known offset-512 event.
```

### Method

The audit ran v0.3.6 seed46/sample6 from initialization to checkpoint `2048`,
then continued for horizon `1024` using the standard deterministic continuation
seed.

The natural run was compared with three no-stored-phase rewrites:

```text
zero_phase:
  World.P clamped to 0
  vector_step phase = 0
  takeover rotation phase = 0
  rotation source/target phase = 0

interaction_phase:
  World.P clamped to 0
  vector_step phase = (V + A + R) mod 8
  takeover rotation phase = V mod 8
  rotation source phase =
    source_v + candidate_order + influence_phase + residual_phase mod 8
  rotation target phase =
    target_v + target_a + target_r + candidate_order mod 8

rotation_only_interaction_phase:
  World.P clamped to 0
  vector_step phase = 0
  takeover rotation phase = 0
  rotation phases use the same interaction-derived rule above
```

All replacement variants therefore remove stored payload/action phase. Any phase
value used by an action is computed directly from non-payload event properties.

### Seed46 Result

None of the no-stored-phase rewrites preserves the known birth channel:

| Variant | Signal offsets | Split 512 | Rebridge 515 | Checkpoint active | Components | Largest | Payload at checkpoint | Ledger |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `natural` | `512;513;514` | `1` | `1` | `1151` | `16` | `139` | `0` | `1` |
| `zero_phase` | none | `0` | `0` | `1125` | `16` | `145` | `0` | `1` |
| `interaction_phase` | none | `0` | `0` | `1125` | `16` | `139` | `0` | `1` |
| `rotation_only_interaction_phase` | none | `0` | `0` | `1143` | `17` | `137` | `0` | `1` |

The causal-cell gate also fails in every no-stored-phase rewrite:

| Variant | `(13,3,38)` active at 499 | `(13,3,38)` active at 511 | `(12,2,38)` active at 512 | `(13,2,38)` active at 515 |
|---|---:|---:|---:|---:|
| `natural` | `1` | `1` | `1` | `1` |
| `zero_phase` | `0` | `0` | `0` | `0` |
| `interaction_phase` | `0` | `0` | `0` | `0` |
| `rotation_only_interaction_phase` | `0` | `0` | `0` | `0` |

The most informative near miss is `interaction_phase`: it matches the natural
checkpoint component count and largest-component size (`16`, `139`), but still
loses the causal articulation cells and produces no component signal.

### Interpretation

Finding 054 rules out a simple local deterministic replacement for the existing
numeric phase, at least for the seed46 birth channel.

This does not restore semantic payload. It says the current law uses an early,
short-lived phase variable as genuine symmetry-breaking action entropy:

```text
initial numeric phase
  -> early action selection
  -> altered checkpoint geometry
  -> specific articulation dependency
  -> component split/rebridge signal
```

The important refinement is that coarse checkpoint morphology is insufficient.
`interaction_phase` reaches the same checkpoint component count and largest
component size as the natural run, but the dependency path is absent. The birth
channel depends on specific inherited placement/timing constraints, not only on
coarse component statistics.

The reduction ladder now stands at:

```text
1. remove semantic payload from World.P                 [passed Finding 052]
2. derive current numeric phase from local state         [failed Finding 053]
3. replace current phase with local deterministic source [failed Finding 054]
```

The next step should be a law search, not another exact-replay attempt:

```text
Design a genuinely phase-free local interaction law, keep World.P/action_phase
absent, and search for a new birth channel by causal class:
  fixed ledger,
  bounded continuations,
  transient local action constraint,
  component split/rebridge or matched bridge dependency,
  no stored phase/payload variable.
```

Only after a phase-free law produces its own positive birth channel should the
minimal coherence seed ladder begin.

### Artifacts

- `src/phase_source_minimization_audit.py`
- `output/findings/finding054/phase_source_minimization_seed46_summary.csv`
- `output/findings/finding054/phase_source_minimization_seed46_summary.json`
- `output/findings/finding054/phase_source_minimization_seed46_pairs.csv`
- `output/findings/finding054/phase_source_minimization_seed46_timeline.csv`

---

## Finding 055 — Coupled vector-derived takeover and rotation phase gives a no-stored-phase component signal

### Question

Finding 054 showed that simple deterministic interaction-derived replacements
do not preserve the original seed46 offset-512 birth channel. Finding 055 asked
a broader search question:

```text
Can any no-stored-payload/no-stored-action-phase local law produce a component
split/rebridge signal by causal class, even if it does not replay the original
seed46 channel?
```

This is not yet a strict phase-free primitive test. The positive variant below
still computes a transient phase-like value from vector state. The important
change is that no phase is stored in `World.P` or in an auxiliary
`action_phase` array.

### Method

The law-search audit reused v0.3.6 seed46/sample6:

```text
checkpoint: 2048
primary search horizon: 600
boundedness follow-up horizon for the positive variant: 1024
World.P clamped to zero for all replacement variants
no stored action_phase
ledger must remain exact
```

The isolated variants were:

```text
zero_phase:
  all action paths receive phase 0

vector_step_only_interaction_phase:
  vector_step phase = (V + A + R) mod 8
  takeover and rotation phase = 0

takeover_only_vector_phase:
  takeover phase = V mod 8
  vector_step and rotation phase = 0

rotation_only_vector_phase:
  rotation source/target phase = source_v mod 8 / target_v mod 8
  vector_step and takeover phase = 0

takeover_rotation_vector_phase:
  takeover phase = V mod 8
  rotation source/target phase = source_v mod 8 / target_v mod 8
  vector_step phase = 0

interaction_phase:
  vector_step, takeover, and rotation all receive deterministic
  interaction-derived phases

rotation_only_interaction_phase:
  only rotation receives deterministic interaction-derived phases
```

### Seed46 Search Result

Only the coupled takeover+rotation vector-derived variant produced a component
signal:

| Variant | Signal offsets | Vanish offset | Checkpoint active | Components | Largest | Payload at checkpoint | Ledger |
|---|---:|---:|---:|---:|---:|---:|---:|
| `natural` | `512;513;514` | `515` | `1151` | `16` | `139` | `0` | `1` |
| `zero_phase` | none | none | `1125` | `16` | `145` | `0` | `1` |
| `vector_step_only_interaction_phase` | none | none | `1121` | `16` | `143` | `0` | `1` |
| `takeover_only_vector_phase` | none | none | `1185` | `16` | `137` | `0` | `1` |
| `rotation_only_vector_phase` | none | none | `1175` | `16` | `145` | `0` | `1` |
| `takeover_rotation_vector_phase` | `134;135;136;137;138;139;140` | `141` | `1125` | `15` | `135` | `0` | `1` |
| `interaction_phase` | none | none | `1125` | `16` | `139` | `0` | `1` |
| `rotation_only_interaction_phase` | none | none | `1143` | `17` | `137` | `0` | `1` |

The positive variant was extended to horizon `1024` and remained bounded:

```text
variant:                       takeover_rotation_vector_phase
signal offsets:                134;135;136;137;138;139;140
component signal vanish offset:141
checkpoint active/components:  1125 / 15
final active/components:       1125 / 15
payload at checkpoint/final:   0 / 0
ledger exact:                  1
max ledger error:              0.0
```

During the signal window:

```text
offset 133: component_count = 15
offset 134: component_count = 16  (+1 split)
offset 140: component_count = 16
offset 141: component_count = 15  (-1 rebridge)
active_iotas stayed 1125
largest component stayed 135
World.P stayed zero
```

### Interpretation

This is the first positive post-payload result:

```text
component split/rebridge can occur with no stored payload and no stored
action_phase.
```

It is not the original seed46 channel. The original causal-cell checks are all
absent in the positive variant, and the signal appears at offsets `134..140`
rather than `512..514`.

The path decomposition is informative:

```text
takeover-only vector-derived phase: no signal
rotation-only vector-derived phase: no signal
takeover + rotation vector-derived phase: signal
```

So the working hypothesis changes:

```text
stored phase is not required, but coupled orientation-derived action constraints
may be required.
```

In other words, the system does not need a payload-like phase token, but it does
need a local symmetry breaker that is shared across takeover rotation and
received rotation. `V mod 8` is currently acting as that local orientation phase.

This keeps the ontology moving in the desired direction:

```text
information is not carried as payload;
interaction history and orientation constrain which local actions are available;
component-level events can arise from those constraints without stored phase.
```

### Next Gate

The next step is not tuning strength. It is a causal trace of the new signal:

```text
Finding 056:
  trace takeover_rotation_vector_phase around offsets 128..145
  identify active-set changes at split offset 134 and rebridge offset 141
  compare against zero_phase, takeover_only_vector_phase, and
  rotation_only_vector_phase
  determine whether the signal is a true bridge/articulation event
  verify World.P/action_phase remain absent
```

Only after the new event class is identified should seed robustness be run.

### Artifacts

- `src/phase_source_minimization_audit.py`
- `output/findings/finding055/phase_free_law_search_seed46_summary.csv`
- `output/findings/finding055/phase_free_law_search_seed46_summary.json`
- `output/findings/finding055/phase_free_law_search_seed46_pairs.csv`
- `output/findings/finding055/phase_free_law_search_seed46_timeline.csv`
- `output/findings/finding055/phase_free_positive_seed46_summary.csv`
- `output/findings/finding055/phase_free_positive_seed46_summary.json`
- `output/findings/finding055/phase_free_positive_seed46_timeline.csv`

---

## Finding 056 — The no-stored-phase signal is a bridge-loss split with paired rebridge

### Question

Finding 055 produced the first component split/rebridge signal with no stored
payload and no stored `action_phase`. Finding 056 asked whether that signal is a
real topology event and which active-set transition causes it.

The trace focused on the positive variant:

```text
takeover_rotation_vector_phase:
  takeover phase = V mod 8
  rotation source/target phase = source_v mod 8 / target_v mod 8
  vector_step phase = 0
  World.P = 0 throughout the recorded window
```

Controls:

```text
zero_phase
takeover_only_vector_phase
rotation_only_vector_phase
```

### Method

The trace replayed v0.3.6 seed46/sample6 through checkpoint `2048`, cloned the
standard continuation, and recorded offsets `128..145`.

For each offset and transition it measured:

```text
active-set gained/lost cells
cube26 component count and largest component
payload nonzero count
ledger error
whether gained cells act as bridges if removed
whether lost cells act as bridges if restored
```

### Result

Only the coupled takeover+rotation variant shows a signal in the traced window:

| Variant | Signal offsets | Min components | Max components | Max transition delta | Payload zero | Ledger exact |
|---|---:|---:|---:|---:|---:|---:|
| `zero_phase` | none | `16` | `16` | `0` | `1` | `1` |
| `takeover_only_vector_phase` | none | `16` | `16` | `0` | `1` | `1` |
| `rotation_only_vector_phase` | none | `16` | `16` | `0` | `1` | `1` |
| `takeover_rotation_vector_phase` | `134;135;136;137;138;139;140` | `15` | `16` | `+1/-1` | `1` | `1` |

The split transition is precise:

```text
offset 133 -> 134
component count: 15 -> 16
active count:    1125 -> 1125
gained cell:     (16,26,24)
lost cell:       (16,27,24)
```

The lost cell is a bridge:

```text
restoring lost cell (16,27,24) to the offset-134 active set reduces component
count from 16 back to 15.
```

The gained cell is not itself a bridge or isolated-component artifact under the
single-cell removal test.

The component-size signature confirms a small split:

```text
offset 133 top sizes: 135;131;123;121;106;101;98;79
offset 134 top sizes: 135;130;123;121;106;101;98;79
offset 141 top sizes: 135;131;123;121;106;101;98;79
```

So the signal is consistent with one small fragment separating from the
second-largest component when `(16,27,24)` is lost, then reintegrating at offset
`141`.

The rebridge transition is not attributable to a single gained bridge cell:

```text
offset 140 -> 141
component count: 16 -> 15
active count:    1125 -> 1125
gained cells:    (17,29,25), (40,16,20)
lost cells:      (17,28,25), (40,15,20)
single-cell bridge tests: no single gained/lost cell explains the merge
```

This points to a paired relocation or multi-cell topology change rather than a
single articulation-cell restoration.

### Interpretation

Finding 056 upgrades Finding 055 from "component-count blip" to a real
topological event:

```text
the no-stored-phase signal is born when a bridge cell is lost.
```

The important mechanism is not stored payload and not stored numeric phase. It
is a coupled orientation-derived action constraint that changes active-set
placement enough to remove an articulation bridge.

The controls matter:

```text
takeover-only vector phase: no split
rotation-only vector phase: no split
takeover + rotation vector phase: bridge-loss split
```

That suggests the component event requires coordination between the state
assigned during takeover and the received-rotation update. One path alone can
change morphology, but not enough to create the bridge-loss component event in
this seed/window.

### Next Gate

The next gate is seed robustness for the new event class, not tuning:

```text
Finding 057:
  run takeover_rotation_vector_phase on seeds 42, 43, 44, 45, 46, 56
  checkpoint 2048, horizon at least 600
  require World.P = 0 and ledger exact
  measure component signals, bridge-loss splits, and paired rebridges
  compare against zero_phase and single-path controls
```

Pass criterion:

```text
at least a minority of seeds show component split/rebridge or bridge-loss events
under the coupled law, while controls remain mostly silent and safety holds.
```

### Artifacts

- `src/phase_free_signal_trace.py`
- `output/findings/finding056/phase_free_signal_trace_seed46_summary.csv`
- `output/findings/finding056/phase_free_signal_trace_seed46_summary.json`
- `output/findings/finding056/phase_free_signal_trace_seed46_snapshots.csv`
- `output/findings/finding056/phase_free_signal_trace_seed46_transitions.csv`

---

## Finding 057 — No-stored-phase bridge-loss events are seed-replicated but not exclusive to the coupled law

### Question

Finding 056 identified a real bridge-loss split/rebridge event in seed46 under
`takeover_rotation_vector_phase`. Finding 057 asked whether this causal
morphology is seed-robust and enriched relative to single-path controls.

The tested event class was:

```text
local orientation-derived action constraint
-> bridge/articulation loss
-> component separation
-> rebridge
```

The pass condition was deliberately not same coordinate or same offset. The
event only needed the same causal morphology, with `World.P=0`, no stored
`action_phase`, and exact ledger.

### Method

The robustness audit ran:

```text
seeds:       42, 43, 44, 45, 46, 56
checkpoint:  2048
horizon:     600
sample:      6
continuation seed base: 20260708
```

Variants:

```text
zero_phase
vector_step_only_vector_phase
takeover_only_vector_phase
rotation_only_vector_phase
takeover_rotation_vector_phase
```

For each seed/variant the audit measured:

```text
component-signal incidence
signal intervals and duration
bridge-loss events
lost-cell articulation before loss
rebridge transitions and delay
payload-zero audit
ledger exactness
event coordinates
```

### Aggregate Result

All cases remained payload-free and ledger-exact:

| Variant | Cases | Component signal cases | Bridge-loss/rebridge passes | Bridge-loss events | Rebridge transitions | Payload zero | Ledger exact |
|---|---:|---:|---:|---:|---:|---:|---:|
| `zero_phase` | `6` | `0` | `0` | `0` | `0` | `6` | `6` |
| `vector_step_only_vector_phase` | `6` | `0` | `0` | `0` | `0` | `6` | `6` |
| `rotation_only_vector_phase` | `6` | `0` | `0` | `0` | `0` | `6` | `6` |
| `takeover_only_vector_phase` | `6` | `1` | `1` | `1` | `1` | `6` | `6` |
| `takeover_rotation_vector_phase` | `6` | `2` | `2` | `2` | `2` | `6` | `6` |

The coupled law therefore replicates the event class in multiple seeds, but it
does not have exclusive ownership: `takeover_only_vector_phase` produces one
bridge-loss/rebridge event in seed56.

### Positive Event Cases

| Seed | Variant | Signal offsets | Duration | Rebridge delay | Bridge-loss coords | Articulation before loss |
|---:|---|---:|---:|---:|---|---:|
| `44` | `takeover_rotation_vector_phase` | `444;445;446;447` | `4` | `4` | `(63,38,31);(63,40,31)` | `0` |
| `46` | `takeover_rotation_vector_phase` | `134;135;136;137;138;139;140` | `7` | `7` | `(16,27,24)` | `1` |
| `56` | `takeover_only_vector_phase` | `94;95;96;97;98;99;100;101;102;103` | `10` | `10` | `(14,5,5)` | `0` |

The seed46 result is the cleanest single-cell articulation case:

```text
lost bridge cell:      (16,27,24)
articulation before:   yes
restoring after loss:  merges components
signal duration:       7 offsets
```

Seed44 under the coupled law is a two-cell bridge-loss case:

```text
lost bridge cells:     (63,38,31), (63,40,31)
articulation before:   no under single-cell removal
restoring after loss:  merges components
signal duration:       4 offsets
```

Seed56 under the takeover-only control is a real control caveat:

```text
lost bridge cell:      (14,5,5)
variant:               takeover_only_vector_phase
signal duration:       10 offsets
```

### Interpretation

Finding 057 is a partial positive:

```text
The no-stored-phase bridge-loss/rebridge event class is seed-replicated.
```

But the stronger claim fails:

```text
The event class is not unique to the coupled takeover+rotation law.
```

The refined claim is:

```text
Coupled takeover+rotation vector phase enriches the event class relative to
zero phase, vector-step-only, and rotation-only controls, but takeover-only can
also produce the same morphology in at least one seed.
```

This matters scientifically. It suggests that the irreducible ingredient may
not be "takeover plus rotation coupling" as such. The more basic ingredient may
be:

```text
orientation-derived takeover state can place active cells on knife-edge
articulation paths; received rotation increases incidence but is not strictly
necessary in every seed.
```

The current evidence supports:

```text
no payload,
no stored phase,
local orientation-derived action constraint,
bridge-loss component separation,
lawful rebridge.
```

It does not yet support:

```text
the coupled law is uniquely responsible for the event class.
```

### Next Gate

The next gate should isolate the seed56 takeover-only exception and compare it
directly to the coupled-law positives:

```text
Finding 058:
  trace seed56 takeover_only_vector_phase around offsets 90..105
  trace seed44 takeover_rotation_vector_phase around offsets 440..449
  compare both to seed46 takeover_rotation_vector_phase
  classify whether they share the same bridge-loss mechanism or represent
  distinct subclasses
```

If seed56 is mechanistically the same, then takeover-phase orientation is the
minimal sufficient local constraint. If seed56 differs, the coupled law may
still define the cleaner component-birth class.

### Artifacts

- `src/phase_free_seed_robustness.py`
- `src/phase_source_minimization_audit.py`
- `output/findings/finding057/phase_free_seed_robustness_summary.csv`
- `output/findings/finding057/phase_free_seed_robustness_summary.json`
- `output/findings/finding057/phase_free_seed_robustness_aggregate.csv`
- `output/findings/finding057/phase_free_seed_robustness_events.csv`
- `output/findings/finding057/phase_free_seed_robustness_signals.csv`

---

## Finding 058 — Bridge-loss events split into single-articulation and multi-cell relocation subclasses

### Question

Finding 057 showed that no-stored-phase bridge-loss/rebridge events replicate
across seeds, but not exclusively under the coupled takeover+rotation law:
seed56 produced a takeover-only event. Finding 058 asked whether the seed56
exception is the same mechanism as the coupled-law positives.

The trace compared:

```text
seed44 takeover_rotation_vector_phase, offsets 440..449
seed46 takeover_rotation_vector_phase, offsets 128..145
seed56 takeover_only_vector_phase, offsets 90..105
```

Each run also compared the opposite takeover/coupled variant in the same window.

### Result Summary

| Seed | Variant | Signal offsets | Vanish | Split transition | Rebridge transition | Max lost bridge count | Payload zero | Ledger exact |
|---:|---|---:|---:|---|---|---:|---:|---:|
| `44` | `takeover_rotation_vector_phase` | `444;445;446;447` | `448` | `443 -> 444` | `447 -> 448` | `2` | `1` | `1` |
| `46` | `takeover_rotation_vector_phase` | `134;135;136;137;138;139;140` | `141` | `133 -> 134` | `140 -> 141` | `1` | `1` | `1` |
| `56` | `takeover_only_vector_phase` | `94;95;96;97;98;99;100;101;102;103` | `104` | `93 -> 94` | `103 -> 104` | `1` | `1` | `1` |

Window controls:

```text
seed44 takeover_only_vector_phase: no signal
seed46 takeover_only_vector_phase: no signal
seed56 takeover_rotation_vector_phase: no signal
```

So seed56 is a real takeover-only exception, not a trace-window artifact.

### Subclass A — Single-Articulation Bridge Loss

Seed46 coupled law:

```text
offset 133 -> 134
component count: 15 -> 16
gained cells:    (16,26,24)
lost cells:      (16,27,24)
lost bridge:     (16,27,24)
articulation before loss: yes
```

The same cell is both:

```text
an articulation before loss,
and a bridge whose restoration merges the split components.
```

This is the cleanest causal form:

```text
single articulation loss -> temporary split -> paired rebridge.
```

### Subclass B — Multi-Cell Bridge-Loss Relocation

Seed44 coupled law:

```text
offset 443 -> 444
component count: 15 -> 16
gained cells:    (52,25,45), (63,37,31), (63,39,31)
lost cells:      (52,26,44), (63,38,31), (63,40,31)
lost bridges:    (63,38,31), (63,40,31)
articulation before loss: no under single-cell removal
```

Seed56 takeover-only exception:

```text
offset 93 -> 94
component count: 19 -> 20
gained cells:    (15,5,5), (23,61,35)
lost cells:      (14,5,5), (22,61,35)
lost bridge:     (14,5,5)
articulation before loss: no under single-cell removal
```

Both are bridge-loss events because restoring the lost bridge cell after the
split merges components. But neither is a single-cell articulation before loss.
The split depends on the simultaneous active-set relocation.

This is a distinct subclass:

```text
multi-cell relocation removes bridge support -> temporary split -> multi-cell rebridge.
```

### Seed56 Coupled-Law Suppression

Seed56 is especially informative because the coupled law does not produce the
takeover-only signal in the same window. Instead it shows a non-splitting bridge
swap:

```text
seed56 takeover_rotation_vector_phase, offset 92 -> 93
component count: 21 -> 21
gained bridge-if-removed: (45,22,56)
lost articulation-before: (45,22,55)
component delta: 0
```

So adding received-rotation vector phase can suppress or reroute a takeover-only
bridge-loss split. The coupled law is not a monotonic "more bridge events" knob.
It changes which local topology transitions are realized.

### Interpretation

Finding 058 resolves the seed56 caveat:

```text
seed56 is the same broad bridge-loss/rebridge morphology,
but not the same single-articulation subclass as seed46.
```

The current taxonomy is:

```text
Class A: single-articulation bridge loss
  observed: seed46 coupled law
  cleanest causal mechanism

Class B: multi-cell bridge-loss relocation
  observed: seed44 coupled law, seed56 takeover-only law
  bridge loss is real, but causal support is distributed across simultaneous
  gained/lost cells
```

This strengthens the overall no-payload/no-stored-phase result while narrowing
the precise claim:

```text
Local orientation-derived action constraints can produce lawful temporary
component separation and rebridge without payload or stored phase.
```

But:

```text
the clean single-articulation event is not yet seed-robust;
the broader bridge-loss/rebridge class is seed-replicated.
```

### Next Gate

The next gate should track these subclasses separately:

```text
Finding 059:
  run a larger seed/sample matrix for takeover_rotation_vector_phase and
  takeover_only_vector_phase
  classify signals as:
    A. single-articulation bridge loss
    B. multi-cell bridge-loss relocation
    C. non-bridge component signal
  measure incidence, duration, rebridge delay, and safety
```

Pass condition:

```text
Class A or B appears above control frequency while World.P/action_phase remain
absent and ledger exactness holds.
```

### Artifacts

- `src/phase_free_signal_trace.py`
- `output/findings/finding058/seed44_coupled_positive_summary.csv`
- `output/findings/finding058/seed44_coupled_positive_transitions.csv`
- `output/findings/finding058/seed46_coupled_positive_summary.csv`
- `output/findings/finding058/seed46_coupled_positive_transitions.csv`
- `output/findings/finding058/seed56_takeover_exception_summary.csv`
- `output/findings/finding058/seed56_takeover_exception_transitions.csv`
