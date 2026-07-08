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
