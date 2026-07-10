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
fbc7fc0 Finding 046: component-bridge partial morphology test
d7f07f0 Finding 045: residual geometry audit
9132bd2 Finding 044: seed-robust fixed-mean contrast
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
| Finding 046 | component-bridge bias improves interface divergence but not robust component morphology |
| Finding 047 | first component signal is articulation-source exhaustion |

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
audit showed why component morphology had not moved: v0.3.5 slightly suppressed rarer
cube26 component-bridge candidates. v0.3.6 successfully reverses that class-level
suppression at fixed mean and improves aggregate interface-union divergence, but it
does not yet produce robust component-level morphology. Finding 047 traces the lone
component responder and shows the first component signal is not bridge quantity; it is
residual recruitment from a soon-exhausted articulation source, followed by source
deactivation that splits off a one-cell cube26 component.
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
v0.3.6 component-bridge geometry bias improves the aggregate interface result and
produces one nonzero component seed, but active-set improvement remains 3/6 seeds and
component-level movement remains 1/6 seeds.
Finding 047 shows that the lone component signal is transient: the split appears at
offset 512, vanishes at offset 515, and is caused by articulation-source exhaustion
rather than a high-contrast bridge event directly moving component count.
```

The system now has:

```text
rotation with memory
directional lineage persistence
bounded ledger-exact dynamics
fixed-mean seed-robust interface symmetry breaking
geometry audit for residual re-entry opportunities
fixed-mean component-bridge selection control
causal component-bridge trace identifying articulation-source exhaustion
```

It does not yet have:

```text
robust component-level divergence
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
src/residual_recruitment_geometry_audit.py
src/component_bridge_causal_trace.py
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
Finding 046: Component-Bridge Bias Improves Interface Divergence but Not Robust Component Morphology
Finding 047: The First Component Signal Is an Articulation-Source Exhaustion Event
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
output/findings/configs/v036_component_bridge_seed*_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amrb2p0_cb0p25_lb0p05_ffn0p05_een0p05.yaml
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

Finding 046:

```text
output/findings/finding_046_v036_component_bridge_pass_table.csv
output/findings/finding_046_v036_component_bridge_aggregate_by_variant.csv
output/findings/finding_046_v036_component_bridge_fixed_mean_audit.csv
output/findings/finding_046_v036_component_bridge_geometry_class_summary.csv
output/findings/finding_046_v036_component_bridge_summary.json
output/findings/finding_046_v036_component_bridge_seed*_rotation_aware_openness_summary.csv
output/findings/finding_046_v036_component_bridge_seed*_lineage_persistence_summary.csv
output/findings/finding_046_v036_component_bridge_seed*_lineage_conditioned_morphology_summary.csv
output/findings/finding_046_v036_component_bridge_seed*_front_turnover_turnover_summary.json
output/findings/finding_046_v036_component_bridge_seed*_residual_geometry_audit_summary.json
```

Finding 047:

```text
output/findings/finding_047_component_bridge_causal_trace_seed46_sample6_events.csv
output/findings/finding_047_component_bridge_causal_trace_seed46_sample6_deactivations.csv
output/findings/finding_047_component_bridge_causal_trace_seed46_sample6_timeline.csv
output/findings/finding_047_component_bridge_causal_trace_seed46_sample6_summary.json
output/findings/finding_047_component_bridge_causal_trace_seed56_sample6_events.csv
output/findings/finding_047_component_bridge_causal_trace_seed56_sample6_deactivations.csv
output/findings/finding_047_component_bridge_causal_trace_seed56_sample6_timeline.csv
output/findings/finding_047_component_bridge_causal_trace_seed56_sample6_summary.json
output/findings/finding_047_component_bridge_causal_trace_comparison.csv
output/findings/finding_047_component_bridge_causal_trace_comparison.json
output/findings/finding_047_component_bridge_causal_trace_chain.csv
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

Finding 046:

```text
v0.3.6 component-bridge test:
  seeds:                                  42, 43, 44, 45, 46, 56
  score mode:                             source_target_L_contrast_component_bridge
  residual bias strength:                 2.0
  component_bridge_cube26 weight:          0.25
  local_bridge_face6 weight:               0.05
  flat_front / edge_extension weights:    -0.05

fixed-mean / safety:
  fixed_mean_ok_count:                    6/6
  safety_ok_count:                        6/6
  max_abs_summed_probability_delta:       4.805045e-13
  max_abs_row_probability_delta:          1.421085e-14

geometry selection:
  component_bridge_cube26 base share:     0.082043
  component_bridge_cube26 biased share:   0.095296
  component_bridge_cube26 lift:           1.161532
  local_bridge_face6 lift:                1.003440
  flat_front lift:                        0.869412
  edge_extension lift:                    0.796561

seed pass counts:
  interface-union beats both baselines:   6/6
  interface-union beats v0.3.5 contrast:  4/6
  active distance beats both baselines:   3/6
  active distance beats v0.3.5 contrast:  3/6
  component nonzero seeds:                1/6

aggregate morphology:
  component-bridge interface-union:       0.023103
  v0.3.5 contrast interface-union:        0.021926
  v0.3.1 interface-union:                 0.017880
  signed interface-union:                 0.018949
  component-bridge active distance:       0.038195
  component-bridge component-count delta: 0.005208
  component-bridge largest-comp delta:    0.005208
  component-bridge phase-4 turnover:      0.024020

interpretation:
  v0.3.6 is a partial positive. It proves component-bridge candidates can be
  preferentially selected at fixed mean and improves interface divergence, but
  component-level morphology remains seed-specific rather than robust.
```

Finding 047:

```text
causal trace:
  responder:        seed 46, checkpoint 2048, sample 6, continuation_seed 2068260714
  non-responder:    seed 56, checkpoint 2048, sample 6, continuation_seed 2068260714

responder component signal:
  first_component_change_offset:      512
  component_signal_offsets:           512, 513, 514
  component_signal_vanish_offset:     515
  component_count_checkpoint/final:   16 / 16
  largest_component_checkpoint/final: 139 / 139

causal event:
  latest activation of future articulation source:
    offset 499, residual recruitment (12,3,38) -> (13,3,38)
  split-producing recruitment:
    offset 512, residual recruitment (13,3,38) -> (12,2,38)
    geometry: local_bridge_face6
    L_contrast: 0.142720
    residual_bias_multiplier: 1.228732
  split-producing deactivation:
    offset 512, cell (13,3,38) deactivates
    single_removal_component_count_delta: +1
    single_removal_largest_delta: -2
    neighbor_component_sizes_after_removal: 138;1
  re-bridge:
    offset 515, residual recruitment (12,2,38) -> (13,2,38)
    geometry: component_bridge_cube26
    global_neighbor_component_sizes_pre: 138;1
    component_count_delta_event: -1
    largest_delta_event: +2

comparison:
  seed46 residual events:                  1010
  seed46 local component-bridge events:     109
  seed46 global bridge events:                1
  seed46 articulation deactivations:          1

  seed56 residual events:                  1214
  seed56 local component-bridge events:     154
  seed56 global bridge events:                0
  seed56 articulation deactivations:          0

interpretation:
  The first component signal is not caused by more local component-bridge-class
  recruitment or high-L contrast alone. Interface divergence becomes component
  divergence when residual recruitment creates a small appendage through a source
  that then exhausts as a cube26 articulation point.
```

Finding 048:

```text
test:
  v0.3.7 support-weighted fixed-mean residual recruitment
  score mode: source_target_L_contrast_support_weighted
  seeds: 42, 43, 44, 45, 46, 56
  checkpoints: 1536 and 2048
  samples: 8 per checkpoint

safety:
  bounded + ledger exact seeds:       6 / 6
  fixed-mean audit seeds:             6 / 6
  max total probability delta:        5.043743e-13
  max per-sample probability delta:   1.421085e-14

aggregate:
  support-weighted interface-union:   0.024344
  component-bridge interface-union:   0.023103
  v0.3.5 contrast interface-union:    0.021926
  v0.3.1 interface-union:             0.017880
  signed interface-union:             0.018949

  support-weighted active distance:   0.040127
  component-bridge active distance:   0.038195
  v0.3.5 contrast active distance:    0.038007

  support-weighted component-count delta: 0.000000
  support-weighted largest-comp delta:    0.000000
  support-weighted phase-4 turnover:      0.026020

per-seed:
  interface beats component_bridge:   4 / 6
  interface beats contrast2:          6 / 6
  interface beats v0.3.1 + signed:    6 / 6
  active beats component_bridge:      4 / 6
  active beats contrast2:             5 / 6
  active beats v0.3.1 + signed:       2 / 6
  nonzero component morphology:       0 / 6

causal repeat:
  v0.3.6 seed46/sample6 component signal: 512, 513, 514
  v0.3.7 seed46/sample6 component signal: none
  v0.3.6 articulation deactivations:      1
  v0.3.7 articulation deactivations:      0
```

Interpretation:

```text
v0.3.7 is a clean negative/partial-positive result.

Support weighting preserves fixed-mean activation, improves interface-union
divergence, improves aggregate active-set divergence, and preferentially selects
component-bridge candidates. But it suppresses the articulation-source turnover
that created the only v0.3.6 component transient, yielding 0 / 6 component
morphology seeds.

The issue is not support in general. The issue is that blanket articulation/source
stabilization removes the event class needed for component-level morphology.
```

## Next Hypothesis

Do not continue secondary candidate ordering bias.

Do not add more component-bridge quantity.

Keep the coupling at local residual recruitment, but make the next gate about
controlled articulation persistence rather than generic bridge support:

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

Why:

```text
v0.3.1 has directional memory without structural consequence.
v0.3.2 proves global secondary bias over-partitions direction and suppresses motion.
v0.3.3 proves event-gated candidate ordering suppresses motion even more.
v0.3.4 proves residual recruitment is the better coupling site: it restores turnover
without adding expected activation, but source-L alignment does not beat baseline
morphology.
v0.3.4b proves source-target L contrast can beat both baselines on interface-union
divergence at fixed mean activation.
v0.3.5 proves that contrast result is seed-robust at the interface level.
Finding 045 proves there are enough local bridge/neck opportunities and that current
contrast slightly suppresses the cube26 component-bridge class.
Finding 046 proves component bridges can be selected at fixed mean and improve
interface-union divergence, but robust component-level morphology still fails.
Finding 047 proves the first component signal is articulation-source exhaustion,
not bridge quantity or high source-target L contrast alone.
Finding 048 proves support-weighting improves interface/active divergence but
removes the articulation-source transient instead of stabilizing it into persistent
component morphology.
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
component-count, largest-component, or component-entropy deltas above numerical dust in a majority of seeds
phase-4 interface turnover not collapsed
```

Minimum useful diagnostic:

```text
articulation-persistence audit
component-bridge causal trace
rotation-aware openness
four-phase lineage persistence
lineage-conditioned morphology
residual recruitment geometry audit
v0.3.1 angular-memory control
signed/no-memory control if needed
```

## Suggested New Thread Prompt

```text
Read SESSION_HANDOFF.md and experiments/FINDINGS.md Findings 038-048.
Continue from Finding 048: v0.3.7 support-weighted fixed-mean residual recruitment
improved interface-union and aggregate active-set divergence, preserved safety and
fixed-mean audits at 6/6 seeds, but produced 0/6 component morphology seeds. The
seed46/sample6 causal repeat removed the v0.3.6 articulation-source component
transient entirely: articulation deactivations dropped from 1 to 0.
Next goal: design v0.3.8 articulation-persistence audit/score. Keep fixed-mean
residual participation, but identify events that allow controlled articulation
turnover and component signal persistence rather than blanket articulation suppression
or more component-bridge quantity.
```

## Finding 049 Update

Finding 049 supersedes the immediate "design v0.3.8 score" next step with an
erase-and-replay causal-channel result on the v0.3.6 seed46/sample6 responder.

Interventions used the same checkpoint, continuation seed, RNG stream, and
1024-tick horizon:

```text
natural:
  component signal at offsets 512, 513, 514

erase_pivotal_transfer:
  after offset 499, restore (12,3,38) and (13,3,38) to pre-kick state
  component signal disappears

erase_pivotal_L:
  preserve active/A/R/V/P at (13,3,38), restore only target angular_L
  component signal survives

erase_pivotal_memory:
  preserve active/A at (13,3,38), restore R/V/P/angular_L
  component signal survives

transplant_pivotal_state:
  move post-kick state from (13,3,38) to nearby depleted (12,3,37)
  component signal disappears
```

All variants remained ledger exact with final ledger error `0.0`.

Result:

```text
The offset-499 kick is necessary, but its inherited angular/vector memory is not.
The necessary property is exact active-state placement and timing: (13,3,38)
must remain active through offset 511, kick into (12,2,38) at offset 512, then
deactivate as a cube26 articulation point.
```

The next step should be a pre-articulation causal-channel diagnostic, not a new
law yet:

```text
identify newly reactivated cells that become future articulation sources,
remain active long enough to perform a compatible downstream kick,
and then exhaust in a way that creates component separation.
```

Updated thread prompt:

```text
Read SESSION_HANDOFF.md and experiments/FINDINGS.md Findings 038-049.
Continue from Finding 049: the v0.3.6 seed46/sample6 erase-and-replay test shows
that the offset-499 residual recruitment is necessary for the first component
split, but not because of inherited angular_L/R/V/P memory. Erasing the transfer
or transplanting the post-kick state removes the split; preserving active
placement while erasing angular/vector memory leaves the split intact. Next goal:
build a pre-articulation causal-channel diagnostic for residual recruits that
become future articulation sources, remain active until a compatible downstream
kick, and exhaust into component separation. Do not add a v0.3.8 mechanism until
that event class is characterized.
```

## Finding 050 Update

Finding 050 tested payload ablation after the Finding 049 result suggested that
the birth event is carried by placement/timing/topology rather than by internal
payload content.

Tool added:

```text
src/payload_ablation_replay.py
```

Checkpoint-mode result:

```text
At saved v0.3.6 checkpoint 2048, all tested seeds already have P = 0 everywhere.

Seed46/sample6:
  natural signal:                 512, 513, 514
  neutral_payload_coupling:        512, 513, 514
  uniform_payload_initial:         512, 513, 514
  clamp_payload_each_tick:         512, 513, 514
  same non-payload state:          yes for all ablations

Six-seed sample-6 smoke:
  seeds:                           42, 43, 44, 45, 46, 56
  same component signal vs natural: 6 / 6
  same non-payload state:           6 / 6
  ledger exact:                     6 / 6
```

This means payload is not part of the component-birth event once the tick-2048
microstate exists.

Init-mode caveat:

```text
Regenerating seed46 from tick zero with P clamped to zero changes the checkpoint
microstate and kills the later component signal.

natural from init:
  component signal:       512, 513, 514
  checkpoint largest:     139
  final active:           1151

neutral_payload_coupling from init:
  component signal:       512, 513, 514
  same non-payload state: yes

uniform/clamped P=0 from init:
  component signal:       none
  checkpoint largest:     145
  final active:           1125
  pivotal cell active at offset 499: no
```

Interpretation:

```text
Payload is not irreducible information at the birth event.
It can be an upstream phase/symmetry-breaking scaffold that helps generate the
pre-birth microstate. It is not acting through semantic compatibility; same/cross
payload coupling is already neutral.
```

Next reduction target:

```text
replace early payload phase with a non-semantic relational or geometry/history
phase, then test whether the same pre-birth microstate and articulation channel
can be recovered without a payload field.
```

Updated thread prompt:

```text
Read SESSION_HANDOFF.md and experiments/FINDINGS.md Findings 038-050.
Continue from Finding 050: checkpoint-mode payload ablation proves the v0.3.6
component-birth event is payload-free once the tick-2048 microstate exists; P is
already zero everywhere, and clamping P to zero preserves component signals and
non-payload state across the six-seed sample-6 smoke set. But from-init ablation
of P in seed46 changes the checkpoint microstate and removes the later split,
while neutral same/cross payload coupling is inert. Next goal: replace early
payload phase with non-semantic relational/geometry/history phase and test
whether the same pre-birth articulation channel can be recovered without payload.
```

## Finding 051 Update

Finding 051 audited which current payload action paths matter upstream of the
seed46/sample6 birth channel.

Tool added:

```text
src/payload_action_phase_audit.py
```

Variants:

```text
natural
no_payload_vector_step
no_payload_rotation_offset
no_payload_rotate_takeover
no_payload_all_action_paths
clamp_payload_each_tick
```

Result:

```text
P acts only early:

tick 0:  nonzero-P iotas = 13, P-sensitive primary actions = 1
tick 1:  nonzero-P iotas = 46, P-sensitive primary actions = 6
tick 2:  nonzero-P iotas = 8,  P-sensitive primary actions = 1
tick 64: nonzero-P iotas = 0,  P-sensitive primary actions = 0
tick 2048 checkpoint: P = 0 everywhere
```

Every P action-path ablation diverges from natural at tick 1, before component
topology differs:

```text
first non-payload divergence tick: 1
natural component count / largest at divergence: 15 / 11
variant component count / largest at divergence: 15 / 11
```

Checkpoint and birth-channel outcomes:

```text
natural:
  signal = 512,513,514
  checkpoint active/largest = 1151 / 139
  causal cell at 499/511/512 = 1/1/0

no_payload_vector_step:
  signal = none
  checkpoint active/largest = 1151 / 141
  causal cell at 499/511/512 = 0/0/0

no_payload_rotation_offset:
  signal = none
  checkpoint active/largest = 1177 / 139
  causal cell at 499/511/512 = 0/0/0

no_payload_rotate_takeover:
  signal = 444,445,888,889
  checkpoint active/largest = 1165 / 153
  causal cell at 499/511/512 = 0/0/0

no_payload_all_action_paths:
  signal = none
  checkpoint active/largest = 1125 / 145

clamp_payload_each_tick:
  signal = none
  checkpoint active/largest = 1125 / 145
```

`no_payload_all_action_paths` and full `P=0` clamping produce the same
non-payload final state hash, so there is no hidden semantic payload channel
beyond the audited action paths.

Interpretation:

```text
P is a transient action-phase selector.
It is not semantic compatibility and not persistent memory.
It selects early legal vector/diffuse actions, rotation offsets, and takeover
rotations; then it collapses while the geometric consequences persist.
```

Next implementation target:

```text
Replace P with an explicit finite action-state variable:
  selects among legal vector/diffuse actions
  selects among legal rotation offsets
  selects takeover rotation phase
  decays/resets after acting
  never directly changes energy, occupancy, or admissibility
```

First success gate:

```text
recover the seed46 pre-birth articulation channel without semantic payload:
  (13,3,38) active at offsets 499 and 511
  (12,2,38) active at offset 512
  component signal at or near the offset-512 gate
  ledger exact
  action state collapsed/reset before birth
```

Updated thread prompt:

```text
Read SESSION_HANDOFF.md and experiments/FINDINGS.md Findings 038-051.
Continue from Finding 051: payload is now identified as a transient action-phase
selector, not semantic information. In v0.3.6 seed46/sample6, P is nonzero only
in the first few ticks and gone by tick 64/checkpoint 2048. Removing P from
vector-step, rotation-offset, or takeover-rotation action paths from init changes
the checkpoint microstate and destroys the Finding 049 offset-512 birth channel.
Removing all P action paths is identical to clamping P=0, proving there is no
hidden payload channel beyond action selection. Next goal: replace P with an
explicit finite action-state variable that only selects among legal actions,
resets/decays after acting, and tries to recover the seed46 pre-birth articulation
channel without semantic payload.
```

## Finding 052 Update

Finding 052 performed the semantic-preserving replacement test.

Tool added:

```text
src/action_state_equivalence_audit.py
```

Replacement setup:

```text
legacy:
  normal World.P payload array

replacement:
  World.P is held at zero at every recorded tick
  separate action_phase array carries the old P phase during step()
  after step(), action_phase receives the produced next phase
  World.P is immediately reset to zero
```

This means payload is deleted from the iota state at rest, but current
action-selection semantics are preserved.

Seed46/sample6 result:

```text
ticks compared:                 3073
non-payload equal ticks:         3073 / 3073
phase equal ticks:               3073 / 3073
replacement payload-zero ticks:  3073 / 3073
RNG equal ticks:                 3073 / 3073
ledger exact:                    yes
phase collapse tick:             18
checkpoint phase nonzero iotas:  0
final phase nonzero iotas:       0
component signal:                512, 513, 514
split at 512:                    yes
rebridge at 515:                 yes
```

The Finding 049 causal channel is preserved exactly:

```text
(13,3,38) active at offset 499: yes
(13,3,38) active at offset 511: yes
(12,2,38) active at offset 512: yes
(13,2,38) active at offset 515: yes
```

Six-seed sample-6 smoke:

```text
seeds:                           42, 43, 44, 45, 46, 56
exact non-payload cases:          6 / 6
exact phase cases:                6 / 6
replacement payload-zero cases:   6 / 6
RNG exact cases:                  6 / 6
ledger exact cases:               6 / 6
component-signal cases:           2 / 6
split-at-512 cases:               1 / 6
rebridge-at-515 cases:            1 / 6
phase collapse ticks by seed:     42=11, 43=81, 44=11, 45=26, 46=18, 56=86
```

Interpretation:

```text
Payload is not fundamental.
The current numeric phase can be factored out of World.P and represented as a
transient action-phase consequence of interaction history.
```

Cleaner primitive:

```text
An interaction can leave a transient constraint on the next legal action;
that constraint is extinguished after action selection.
```

Next reduction ladder:

```text
1. explicit 0..7 transient action_phase side state      [passed equivalence]
2. finite action-mode state plus locally derived phase
3. binary action-enabled state plus locally derived action type
4. no stored action state: derive action selection directly from the interaction event
```

Next thread prompt:

```text
Read SESSION_HANDOFF.md and experiments/FINDINGS.md Findings 038-052.
Continue from Finding 052: replacing World.P with a separate transient
action_phase side state gives exact non-payload, phase, RNG, ledger, and component
signal equivalence across seed46/sample6 and the six-seed sample-6 smoke set,
while World.P remains zero at every recorded tick. The seed46 offset-512 birth
channel is preserved exactly. Next goal: reduce action_phase further by replacing
the explicit 0..7 phase storage with a finite action-mode state plus locally
derived phase, then test whether the seed46 pre-birth articulation channel still
forms.
```

## Finding 053 Update

Finding 053 tested whether the numeric `action_phase=0..7` can be removed
entirely and derived from local non-payload state plus the action path.

Tool added:

```text
src/action_phase_derivability_audit.py
```

Method:

```text
Instrument the three phase-sensitive paths:
  vector_step
  rotate_takeover
  rotation_offset / signed_rotation_offset

For each call, group by non-payload signature and ask whether different phase
values require different action results.
```

Six-seed sample-6 result:

```text
seeds:                              42, 43, 44, 45, 46, 56
mode-only locally derivable cases:   0 / 6
numeric-phase eliminable cases:      0 / 6
vector-step result collision cases:  0 / 6
takeover result collision cases:     2 / 6
rotation result collision cases:     5 / 6
signed-rotation collision cases:     6 / 6
phase collapse ticks:                42=11, 43=81, 44=11, 45=26, 46=18, 56=86
```

Seed46 details:

```text
initial nonzero phase iotas: 13
max nonzero phase iotas:     46
phase collapse tick:         18
vector_step result collisions:        0
rotate_takeover result collisions:    2
rotation_offset result collisions:    3
signed_rotation result collisions:    9
```

Representative seed46 collision:

```text
same non-payload rotate_takeover signature:
  behavior=reflect, v_idx=39

different phase-conditioned outcomes:
  p=3 -> rotated_v=42
  p=7 -> rotated_v=46
```

Interpretation:

```text
Finding 052 removed semantic payload from the iota state.
Finding 053 shows the current numeric action phase is still required by the
current rotation/takeover law and cannot be reconstructed from audited local
non-payload state.
```

This is not evidence for semantic payload. It is evidence for short-lived action
entropy:

```text
initial phase -> early legal-action selection -> phase collapse -> inherited
geometric constraint
```

Updated reduction ladder:

```text
1. explicit 0..7 transient action_phase side state      [passed Finding 052]
2. finite action-mode state plus locally derived phase  [failed Finding 053]
3. no stored action state                               [blocked by 2]
```

Next recommended gate:

```text
Do not start the minimal coherence seed ladder yet.

Run a phase-source minimization rewrite:
  replace phase-dependent rotation/takeover formulas with phase-free local
  formulas, or derive phase from a deterministic interaction-event property;
  then test whether the seed46 pre-birth articulation channel survives by
  causal class rather than exact replay.
```

Artifacts:

```text
output/findings/finding053/action_phase_derivability_summary.csv
output/findings/finding053/action_phase_derivability_paths.csv
output/findings/finding053/action_phase_derivability_collisions.csv
output/findings/finding053/action_phase_derivability_timeline.csv
output/findings/finding053/action_phase_derivability_local_collisions.csv
```
