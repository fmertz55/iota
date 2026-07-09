# IOTA Session Handoff

Date: 2026-07-09

## Local Checkout State

This MacBook checkout is intentionally sparse to save disk.

Current sparse checkout includes:

```text
src
experiments
experiments_v02
docs
root files
```

Large tracked artifacts are in Git but are not checked out locally:

```bash
git sparse-checkout list
git sparse-checkout add output
git sparse-checkout add data
git sparse-checkout disable
```

Recent local size cleanup:

```text
repo before cleanup: ~1.9G
repo after cleanup:  ~156M
.git before gc:     ~1.3G
.git after gc:      ~33M
```

## Recent Commits

Most recent relevant commits:

```text
7624f30 Findings 042-043: fixed-mean residual recruitment
5979f42 Finding 041: event-gated candidate bias
360dec6 Created SESSION_HANDOFF.md
18a8351 Findings 039/040: lineage-conditioned morphology and secondary-bias test
bd6f71d Finding 038: vector-coupled angular momentum
fa7872d Finding 037: four-phase lineage persistence
```

## Current Scientific Ladder

| Version / Finding | Result |
|---|---|
| v0.2 | pinned active/depleted scaffold |
| v0.2.1 | residual participation / turnover, but canalized |
| v0.3 | weak directional recursion |
| Finding 037 | recurrent transient directional branchlets |
| Finding 038 | persistent non-merging directional lineage separation |
| Finding 039 | directional lineages are not yet morphogenetic |
| Finding 040 | secondary candidate bias over-separates direction but suppresses morphology |
| Finding 041 | event-gated candidate bias further canalizes the interface |
| Finding 042 | fixed-mean residual recruitment restores turnover but not morphology |
| Finding 043 | source-target contrast breaks interface symmetry at fixed mean |
| Finding 044 | source-target contrast is seed-robust at fixed mean |
| Finding 045 | residual geometry audit identifies the component-level lever |

## Core Interpretation

Current paper-safe claim:

```text
Retained angular momentum coupled to the information-exchange vector creates bounded,
ledger-exact, non-merging directional lineages. Candidate-ordering bias is now a
tested negative lever: both global and event-gated versions increase directional
separation while suppressing interface turnover and spatial divergence. Fixed-mean
residual recruitment is the better coupling site. The source-target `L` contrast law
at strength `2.0` is now seed-robust: it beats both the v0.3.1 angular-memory baseline
and signed/no-memory control on interface-union divergence in 6/6 tested seeds while
preserving expected residual participation to floating precision. The residual geometry
audit shows why component morphology has not moved yet: the current contrast law
slightly suppresses the rarer cube26 component-bridge candidates.
```

Current negative result:

```text
Adding capacity-neutral secondary candidate ordering bias at strength 0.10 maximizes
directional family separation but reduces interface turnover and spatial divergence.
Event-gating that same ordering bias to interface/recruitment opportunities suppresses
morphology even more.
Fixed-mean residual recruitment at strength 1.0 preserves expected residual
participation exactly and restores interface turnover, but still does not produce
above-baseline morphology.
Source-target fixed-mean residual contrast at strength 2.0 improves interface-union
spatial divergence above both v0.3.1 and signed/no-memory control, without increasing
expected activation. v0.3.5 confirms this is seed-robust at the interface level. It is
not yet component-level morphology.
```

The system now has:

```text
rotation with memory
directional lineage persistence
bounded ledger-exact dynamics
fixed-mean seed-robust interface symmetry breaking
geometry audit for residual re-entry opportunities
```

It does not yet have:

```text
component-level divergence
open-ended complexity
```

## Key Files

Code:

```text
src/iota_rig.py
src/rotation_aware_openness.py
src/rotation_branch_lineage.py
src/rotation_lineage_persistence.py
src/lineage_conditioned_morphology.py
src/rotational_recursion_diagnostic.py
src/front_turnover_diagnostic.py
```

Findings:

```text
experiments/FINDINGS.md
Finding 037: Directional Branchlets Recur but Collapse or Merge by Phase 4
Finding 038: Vector-Coupled Angular Momentum Produces Non-Merging Directional Lineages
Finding 039: Directional Lineages Are Not Yet Morphogenetic
Finding 040: Secondary Candidate Bias Maximizes Directional Separation but Suppresses Morphology
Finding 041: Event-Gated Candidate Bias Further Canalizes the Interface
Finding 042: Fixed-Mean Residual Recruitment Restores Turnover
Finding 043: Source-Target Contrast Breaks Interface Symmetry at Fixed Mean
Finding 044: Source-Target Contrast Is Seed-Robust at Fixed Mean
Finding 045: Residual Geometry Audit Identifies the Component-Level Lever
```

## Key Configs

These may require restoring `output` into the sparse checkout:

```text
output/findings/configs/v031_vector_angular_momentum_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2.yaml
output/findings/configs/v031_signed_exchange_control_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2.yaml
output/findings/configs/v032_vector_angular_momentum_secondary_bias_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10.yaml
output/findings/configs/v033_vector_angular_momentum_event_gated_bias_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10.yaml
output/findings/configs/v034_fixed_mean_residual_recruitment_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0.yaml
output/findings/configs/v034b_fixed_mean_residual_recruitment_contrast_amrb2p0_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2.yaml
output/findings/configs/v035_contrast2_seed*_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2.yaml
output/findings/configs/v035_v031_angular_memory_seed*_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2.yaml
output/findings/configs/v035_signed_control_seed*_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2.yaml
```

## Key Artifacts

Finding 038:

```text
output/findings/finding_038_v031_vector_angular_momentum_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_summary.csv
output/findings/finding_038_v031_vector_angular_momentum_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_summary.csv
output/findings/finding_038_v031_signed_exchange_control_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2_summary.csv
output/findings/finding_038_v031_signed_exchange_control_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2_summary.csv
```

Finding 039:

```text
output/findings/finding_039_v031_vector_angular_momentum_lineage_conditioned_morphology_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_summary.csv
output/findings/finding_039_v031_signed_exchange_control_lineage_conditioned_morphology_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2_summary.csv
```

Finding 040:

```text
output/findings/finding_040_v032_vector_angular_momentum_secondary_bias_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv
output/findings/finding_040_v032_vector_angular_momentum_secondary_bias_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv
output/findings/finding_040_v032_vector_angular_momentum_secondary_bias_lineage_conditioned_morphology_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv
```

Finding 041:

```text
output/findings/finding_041_v033_vector_angular_momentum_event_gated_bias_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv
output/findings/finding_041_v033_vector_angular_momentum_event_gated_bias_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv
output/findings/finding_041_v033_vector_angular_momentum_event_gated_bias_lineage_conditioned_morphology_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10_summary.csv
```

Finding 042:

```text
output/findings/finding_042_v034_fixed_mean_residual_recruitment_front_turnover_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0_turnover.csv
output/findings/finding_042_v034_fixed_mean_residual_recruitment_front_turnover_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0_turnover_summary.json
output/findings/finding_042_v034_fixed_mean_residual_recruitment_rotation_aware_openness_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0_summary.csv
output/findings/finding_042_v034_fixed_mean_residual_recruitment_lineage_persistence_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0_summary.csv
output/findings/finding_042_v034_fixed_mean_residual_recruitment_lineage_conditioned_morphology_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb1p0_summary.csv
```

Finding 043:

```text
output/findings/finding_043_v034b_fixed_mean_residual_recruitment_*_rotation_aware_openness_summary.csv
output/findings/finding_043_v034b_fixed_mean_residual_recruitment_*_lineage_persistence_summary.csv
output/findings/finding_043_v034b_fixed_mean_residual_recruitment_*_lineage_conditioned_morphology_summary.csv
output/findings/finding_043_v034b_fixed_mean_residual_recruitment_contrast_amrb2p0_front_turnover_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_turnover.csv
output/findings/finding_043_v034b_fixed_mean_residual_recruitment_contrast_amrb2p0_front_turnover_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_turnover_summary.json
```

Finding 044:

```text
output/findings/finding_044_v035_seed_robustness_pass_table.csv
output/findings/finding_044_v035_seed_robustness_aggregate_by_variant.csv
output/findings/finding_044_v035_seed_robustness_fixed_mean_audit.csv
output/findings/finding_044_v035_seed_robustness_summary.json
output/findings/finding_044_v035_*_rotation_aware_openness_summary.csv
output/findings/finding_044_v035_*_lineage_persistence_summary.csv
output/findings/finding_044_v035_*_lineage_conditioned_morphology_summary.csv
output/findings/finding_044_v035_contrast2_seed*_front_turnover_turnover.csv
output/findings/finding_044_v035_contrast2_seed*_front_turnover_turnover_summary.json
```

Finding 045:

```text
output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed_ensemble_class_summary.csv
output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed_ensemble_seed_summary.csv
output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed_ensemble_summary.json
output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed*_class_summary.csv
output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed*_classes.csv
output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed*_ticks.csv
output/findings/finding_045_v036_residual_geometry_audit_v035_contrast2_seed*_targets.csv
```

## Important Numbers

Finding 038:

```text
v0.3.1 angular memory combined families:
  checkpoint 1536: 20
  checkpoint 2048: 29

signed/no-memory control combined families:
  checkpoint 1536: 4
  checkpoint 2048: 5
```

Finding 039:

```text
v0.3.1 active spatial distance:       0.048056
signed/no-memory active distance:     0.051434
v0.3.1 interface-union distance:      0.024380
signed/no-memory interface distance:  0.026525
```

Finding 040:

```text
v0.3.2 secondary-bias combined families:
  checkpoint 1536: 32
  checkpoint 2048: 31

v0.3.2 active spatial distance:       0.027289
v0.3.2 interface-union distance:      0.010555
v0.3.2 phase-4 interface turnover:
  checkpoint 1536: 0.012663
  checkpoint 2048: 0.007599
```

Finding 041:

```text
v0.3.3 event-gated combined families:
  checkpoint 1536: 28
  checkpoint 2048: 29

v0.3.3 phase-4 interface turnover:
  checkpoint 1536: 0.007480
  checkpoint 2048: 0.006402

v0.3.3 aggregate morphology:
  mean transition distance:       0.903949
  active spatial distance:        0.022345
  depleted spatial distance:      0.029163
  interface-union distance:       0.009316
  active/depleted adjacency:      0.997477
```

Finding 042:

```text
v0.3.4 fixed-mean residual recruitment probability audit:
  base residual probability sum:    3740.364285714283
  biased residual probability sum:  3740.364285714283
  probability delta:                0.000000000000e+00

v0.3.4 phase-4 interface turnover:
  checkpoint 1536: 0.024840
  checkpoint 2048: 0.021181

v0.3.4 aggregate morphology:
  mean transition distance:       0.671077
  active spatial distance:        0.043893
  depleted spatial distance:      0.074544
  active-interface distance:      0.063453
  interface-union distance:       0.019984
  active/depleted adjacency:      0.985688
```

Finding 043:

```text
v0.3.4b winner:
  score mode: source_target_L_contrast
  strength:   2.0

fixed-mean probability audit:
  base residual probability sum:    3920.499999999997
  biased residual probability sum:  3920.499999999996
  probability delta:               -4.547473508865e-13

winner morphology:
  mean transition distance:       0.598748
  active spatial distance:        0.047655
  depleted spatial distance:      0.084874
  active-interface distance:      0.079331
  interface-union distance:       0.027994
  active/depleted adjacency:      0.973621

baseline interface-union distances:
  signed/no-memory control:       0.026525
  v0.3.1 angular memory:          0.024380
  v0.3.4b contrast 2.0:           0.027994

winner phase-4 interface turnover:
  checkpoint 1536: 0.030567
  checkpoint 2048: 0.029274
```

Finding 044:

```text
v0.3.5 robustness seeds:
  42, 43, 44, 45, 46, 56

fixed-mean audit:
  fixed_mean_ok_count:                  6/6
  contrast_safety_ok_count:             6/6
  max_abs_probability_delta:            3.996803e-15
  max_abs_summed_probability_delta:     2.642331e-14

seed pass counts:
  interface-union beats both baselines: 6/6
  active distance beats both baselines: 3/6
  component nonzero seeds:              1/6

aggregate morphology:
  contrast interface-union distance:    0.021926
  v0.3.1 interface-union distance:      0.017880
  signed interface-union distance:      0.018949
  contrast active distance:             0.038007
  v0.3.1 active distance:               0.035978
  signed active distance:               0.036669
  contrast phase-4 interface turnover:  0.023446
```

Finding 045:

```text
residual geometry audit over v0.3.5 contrast seeds:
  seeds:                              42, 43, 44, 45, 46, 56
  mean eligible candidates/tick:      99.118863
  mean unique targets/tick:           69.509044
  mean cube26 bridge targets/tick:     6.892765
  mean face6 bridge targets/tick:     52.077519
  fixed-mean total probability delta:  1.859735e-12

selection by class:
  local_bridge_face6 base share:       0.808766
  local_bridge_face6 biased share:     0.819628
  local_bridge_face6 selection lift:   1.013430

  component_bridge_cube26 base share:  0.083627
  component_bridge_cube26 biased share: 0.078142
  component_bridge_cube26 lift:        0.934422
  component_bridge_cube26 observations: 5335

interpretation:
  v0.3.5 moves the interface but slightly suppresses cube26 component-bridge
  candidates, which are the most plausible local route to component morphology.
```

## Next Hypothesis

Do not continue secondary candidate ordering bias.

Keep the coupling at the local residual recruitment event. v0.3.5 has already passed
the seed-robustness gate for the fixed-mean source-target contrast law. The next
principled test is component-bridge boundary work at fixed mean, using v0.3.5
contrast `2.0` as the baseline and Finding 045's geometry classes as the target.

Candidate v0.3.6 direction:

```text
component-bridge fixed-mean residual recruitment

baseline law:
  angular_momentum_residual_bias_score_mode = source_target_L_contrast
  angular_momentum_residual_bias_strength = 2.0

possible extension:
  add positive local geometry weight for component_bridge_cube26 candidates.
  optionally add weaker positive weight for local_bridge_face6 candidates.
  keep flat_front / edge_extension neutral or slightly negative.
  renormalize residual recruitment probabilities back to the same expected mean.
```

Why:

```text
v0.3.1 has directional memory without structural consequence.
v0.3.2 proves global secondary bias over-partitions direction and suppresses motion.
v0.3.3 proves event-gated candidate ordering suppresses motion even more.
v0.3.4 proves residual recruitment is the better coupling site: it restores turnover
without adding expected activation, but the current source-L alignment score does not
beat baseline morphology.
v0.3.4b proves source-target L contrast can beat both baselines on interface-union
divergence at fixed mean activation.
v0.3.5 proves that contrast result is seed-robust at the interface level.
Finding 045 proves there are enough local bridge/neck opportunities and that current
contrast slightly suppresses the cube26 component-bridge class.
```

## Acceptance Gate

A successful next finding should show:

```text
bounded_nonrunaway_count = samples
ledger_exact_count = samples
nonzero directional lineage persistence
higher active/depleted or interface-union spatial divergence than v0.3.1/control
nonzero component/interface metric separation
no burst, absorber, or active runaway
```

For the immediate component-level gate, require:

```text
fixed residual probability sum within floating precision
bounded_nonrunaway_count = samples
ledger_exact_count = samples
interface-union distance above v0.3.1/control on most tested seeds
active-set distance above v0.3.1/control on a majority of tested seeds
component-count, largest-component, or component-entropy deltas above numerical dust
phase-4 interface turnover not collapsed
```

Minimum useful diagnostic:

```text
rotation-aware openness
four-phase lineage persistence
lineage-conditioned morphology
v0.3.1 angular-memory control
signed/no-memory control if needed
```

## Suggested New Thread Prompt

```text
Read SESSION_HANDOFF.md and experiments/FINDINGS.md Findings 038-045.
Continue from Finding 045: v0.3.5 fixed-mean source-target L contrast is seed-robust
at the interface level, but the residual geometry audit shows it slightly suppresses
cube26 component-bridge candidates.
Next goal: implement v0.3.6 component-bridge fixed-mean residual recruitment, using
v0.3.5 contrast 2.0 as the baseline and preserving mean activation exactly.
```
