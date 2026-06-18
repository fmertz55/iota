# Findings

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
