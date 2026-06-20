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
