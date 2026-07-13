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

## Finding 054 Update

Finding 054 tested whether the remaining numeric phase can be removed by
replacing it with deterministic interaction-local phase sources.

Tool added:

```text
src/phase_source_minimization_audit.py
```

Primary test:

```text
v0.3.6 seed46/sample6
checkpoint: 2048
continuation horizon: 1024
World.P clamped to zero for all replacement variants
no stored numeric action_phase
```

Variants:

```text
natural:
  reference run; known signal at offsets 512, 513, 514

zero_phase:
  all action paths receive phase 0

interaction_phase:
  vector_step phase = (V + A + R) mod 8
  takeover phase = V mod 8
  rotation source/target phase derived from source_v, target_v, target A/R,
  candidate order, influence phase, and target-depleted flag

rotation_only_interaction_phase:
  vector_step and takeover phase are zero
  rotation source/target phase uses the interaction-derived rule
```

Result:

```text
natural:
  signal = 512, 513, 514
  split_at_512 = yes
  rebridge_at_515 = yes
  checkpoint active/components/largest = 1151 / 16 / 139

zero_phase:
  signal = none
  split_at_512 = no
  rebridge_at_515 = no
  checkpoint active/components/largest = 1125 / 16 / 145

interaction_phase:
  signal = none
  split_at_512 = no
  rebridge_at_515 = no
  checkpoint active/components/largest = 1125 / 16 / 139

rotation_only_interaction_phase:
  signal = none
  split_at_512 = no
  rebridge_at_515 = no
  checkpoint active/components/largest = 1143 / 17 / 137
```

Causal cells:

```text
natural:
  (13,3,38) active at offsets 499 and 511
  (12,2,38) active at offset 512
  (13,2,38) active at offset 515

all no-stored-phase rewrites:
  all four causal-cell checks = no
```

Interpretation:

```text
Finding 054 rules out a simple deterministic local phase-source replacement for
the existing seed46 birth channel.
```

This still does not restore semantic payload. The remaining phase behaves like
short-lived action entropy:

```text
initial numeric phase -> early action selection -> altered geometry -> inherited
articulation dependency -> component split/rebridge
```

Important near miss:

```text
interaction_phase matches natural checkpoint component count and largest
component size (16 / 139), but loses the causal articulation path and produces
no component signal.
```

Updated reduction status:

```text
1. remove semantic payload from World.P                 [passed Finding 052]
2. derive current numeric phase from local state         [failed Finding 053]
3. replace current phase with local deterministic source [failed Finding 054]
```

Next recommended gate:

```text
Stop trying exact replay of the existing phase-bearing law.

Design/search a genuinely phase-free local interaction law with World.P and
action_phase absent, then search for a new birth channel by causal class:
  fixed ledger
  bounded continuations
  transient local action constraint
  component split/rebridge or matched bridge dependency
  no stored phase/payload variable

Only after a phase-free law produces a positive birth channel should the minimal
coherence seed ladder begin.
```

Artifacts:

```text
output/findings/finding054/phase_source_minimization_seed46_summary.csv
output/findings/finding054/phase_source_minimization_seed46_summary.json
output/findings/finding054/phase_source_minimization_seed46_pairs.csv
output/findings/finding054/phase_source_minimization_seed46_timeline.csv
```

## Finding 055 Update

Finding 055 broadened the search after Finding 054 failed to preserve the
original seed46 offset-512 channel.

Question:

```text
Can a no-stored-payload/no-stored-action-phase local law produce any component
split/rebridge signal by causal class?
```

Important caveat:

```text
The positive variant is no-stored-phase, not strictly phase-free.
It computes transient phase-like values from vector state (`V mod 8`) but stores
no phase in World.P and uses no auxiliary action_phase array.
```

Search setup:

```text
v0.3.6 seed46/sample6
checkpoint: 2048
search horizon: 600
positive follow-up horizon: 1024
World.P clamped to zero in all replacement variants
ledger exactness required
```

Variants tested:

```text
zero_phase
vector_step_only_interaction_phase
takeover_only_vector_phase
rotation_only_vector_phase
takeover_rotation_vector_phase
interaction_phase
rotation_only_interaction_phase
```

Result:

```text
Only takeover_rotation_vector_phase produced a component signal.

takeover_rotation_vector_phase:
  takeover phase = V mod 8
  rotation source/target phase = source_v mod 8 / target_v mod 8
  vector_step phase = 0
  World.P = 0 at checkpoint and final
  no stored action_phase
```

Positive signal:

```text
signal offsets:                 134, 135, 136, 137, 138, 139, 140
component signal vanish offset: 141
checkpoint active/components:   1125 / 15
final active/components:        1125 / 15
payload at checkpoint/final:    0 / 0
ledger exact:                   yes
max ledger error:               0.0
```

Signal-window detail:

```text
offset 133: component_count = 15
offset 134: component_count = 16  (+1 split)
offset 140: component_count = 16
offset 141: component_count = 15  (-1 rebridge)
active_iotas stayed 1125
largest component stayed 135
World.P stayed zero
```

Negative controls:

```text
takeover_only_vector_phase: no signal
rotation_only_vector_phase: no signal
zero_phase: no signal
interaction_phase: no signal
rotation_only_interaction_phase: no signal
```

Interpretation:

```text
Stored phase is not required for a component split/rebridge signal.
But coupled orientation-derived action constraints appear to matter:
takeover and received rotation both need the same local vector-derived phase
source for this positive seed46 signal.
```

This is not the original Finding 049 channel:

```text
original channel: offsets 512, 513, 514
new no-stored-phase signal: offsets 134..140
original causal-cell checks are absent
```

Next gate:

```text
Finding 056 should be a causal trace of takeover_rotation_vector_phase around
offsets 128..145:
  identify active-set changes at split offset 134 and rebridge offset 141
  compare against zero_phase, takeover_only_vector_phase, and
  rotation_only_vector_phase
  determine whether the signal is a true bridge/articulation event
  verify World.P/action_phase remain absent
```

Artifacts:

```text
output/findings/finding055/phase_free_law_search_seed46_summary.csv
output/findings/finding055/phase_free_law_search_seed46_summary.json
output/findings/finding055/phase_free_law_search_seed46_pairs.csv
output/findings/finding055/phase_free_law_search_seed46_timeline.csv
output/findings/finding055/phase_free_positive_seed46_summary.csv
output/findings/finding055/phase_free_positive_seed46_summary.json
output/findings/finding055/phase_free_positive_seed46_timeline.csv
```

## Finding 056 Update

Finding 056 traced the new no-stored-phase signal from Finding 055.

Positive variant:

```text
takeover_rotation_vector_phase
  takeover phase = V mod 8
  rotation source/target phase = source_v mod 8 / target_v mod 8
  vector_step phase = 0
  World.P = 0 throughout trace window
```

Controls:

```text
zero_phase
takeover_only_vector_phase
rotation_only_vector_phase
```

Trace window:

```text
seed46/sample6
checkpoint: 2048
offsets: 128..145
```

Result summary:

```text
zero_phase:                    no signal
takeover_only_vector_phase:    no signal
rotation_only_vector_phase:    no signal
takeover_rotation_vector_phase signal: 134,135,136,137,138,139,140
vanish/rebridge offset:        141
payload zero all snapshots:    yes
ledger exact all snapshots:    yes
```

Split transition:

```text
offset 133 -> 134
component count: 15 -> 16
active count:    1125 -> 1125
gained cell:     (16,26,24)
lost cell:       (16,27,24)
```

Bridge test:

```text
restoring lost cell (16,27,24) to the offset-134 active set reduces component
count from 16 back to 15.
```

Interpretation:

```text
The no-stored-phase component signal is a real topology event born from loss of
a bridge/articulation cell.
```

Component-size signature:

```text
offset 133 top sizes: 135;131;123;121;106;101;98;79
offset 134 top sizes: 135;130;123;121;106;101;98;79
offset 141 top sizes: 135;131;123;121;106;101;98;79
```

So the signal is consistent with a small fragment separating from the
second-largest component, then reintegrating.

Rebridge transition:

```text
offset 140 -> 141
component count: 16 -> 15
active count:    1125 -> 1125
gained cells:    (17,29,25), (40,16,20)
lost cells:      (17,28,25), (40,15,20)
single-cell bridge tests: no single gained/lost cell explains the merge
```

Interpretation of rebridge:

```text
The rebridge appears to be a paired relocation or multi-cell topology change,
not a single articulation restoration.
```

Mechanistic takeaway:

```text
Stored payload/phase is not required for component split/rebridge.
The key is coupled orientation-derived action constraint: takeover and received
rotation must both use the vector-derived phase source. Single-path controls do
not produce the event.
```

Next gate:

```text
Finding 057 should test seed robustness:
  run takeover_rotation_vector_phase on seeds 42,43,44,45,46,56
  checkpoint 2048
  horizon at least 600
  World.P/action_phase absent
  ledger exact
  measure component signals and bridge-loss split events
  compare against zero_phase, takeover_only_vector_phase, rotation_only_vector_phase
```

Artifacts:

```text
output/findings/finding056/phase_free_signal_trace_seed46_summary.csv
output/findings/finding056/phase_free_signal_trace_seed46_summary.json
output/findings/finding056/phase_free_signal_trace_seed46_snapshots.csv
output/findings/finding056/phase_free_signal_trace_seed46_transitions.csv
```

## Finding 057 Update

Finding 057 tested seed robustness of the no-stored-phase bridge-loss/rebridge
event class.

Setup:

```text
seeds:      42,43,44,45,46,56
checkpoint: 2048
horizon:    600
sample:     6
World.P:    zero for all replacement variants
action_phase: absent
```

Variants:

```text
zero_phase
vector_step_only_vector_phase
takeover_only_vector_phase
rotation_only_vector_phase
takeover_rotation_vector_phase
```

Aggregate:

```text
zero_phase:
  component signal cases = 0 / 6
  bridge-loss/rebridge passes = 0 / 6

vector_step_only_vector_phase:
  component signal cases = 0 / 6
  bridge-loss/rebridge passes = 0 / 6

rotation_only_vector_phase:
  component signal cases = 0 / 6
  bridge-loss/rebridge passes = 0 / 6

takeover_only_vector_phase:
  component signal cases = 1 / 6
  bridge-loss/rebridge passes = 1 / 6

takeover_rotation_vector_phase:
  component signal cases = 2 / 6
  bridge-loss/rebridge passes = 2 / 6
```

All cases:

```text
payload zero: 30 / 30
ledger exact: 30 / 30
```

Positive event cases:

```text
seed44 takeover_rotation_vector_phase:
  signal offsets: 444,445,446,447
  duration/rebridge delay: 4
  bridge-loss coords: (63,38,31), (63,40,31)
  single-cell articulation before loss: no

seed46 takeover_rotation_vector_phase:
  signal offsets: 134,135,136,137,138,139,140
  duration/rebridge delay: 7
  bridge-loss coord: (16,27,24)
  single-cell articulation before loss: yes

seed56 takeover_only_vector_phase:
  signal offsets: 94,95,96,97,98,99,100,101,102,103
  duration/rebridge delay: 10
  bridge-loss coord: (14,5,5)
  single-cell articulation before loss: no
```

Interpretation:

```text
Finding 057 is partial positive.

The no-stored-phase bridge-loss/rebridge event class replicates across seeds
under takeover_rotation_vector_phase (2/6), but it is not exclusive to the
coupled law because takeover_only_vector_phase also passes once (seed56).
```

Refined claim:

```text
Coupled takeover+rotation vector phase enriches the event class relative to
zero phase, vector-step-only, and rotation-only controls, but takeover-only can
also produce the same causal morphology in at least one seed.
```

Mechanistic implication:

```text
The minimal sufficient ingredient may be orientation-derived takeover state
placing active cells on bridge/articulation paths. Received rotation may increase
incidence, but it is not strictly necessary in every seed.
```

Next gate:

```text
Finding 058 should trace and compare:
  seed56 takeover_only_vector_phase around offsets 90..105
  seed44 takeover_rotation_vector_phase around offsets 440..449
  seed46 takeover_rotation_vector_phase around offsets 128..145

Goal:
  decide whether seed56 is the same bridge-loss mechanism or a distinct subclass.
```

Artifacts:

```text
output/findings/finding057/phase_free_seed_robustness_summary.csv
output/findings/finding057/phase_free_seed_robustness_summary.json
output/findings/finding057/phase_free_seed_robustness_aggregate.csv
output/findings/finding057/phase_free_seed_robustness_events.csv
output/findings/finding057/phase_free_seed_robustness_signals.csv
```

## Finding 058 Update

Finding 058 traced the seed56 takeover-only exception against the coupled-law
positives.

Compared windows:

```text
seed44 takeover_rotation_vector_phase: offsets 440..449
seed46 takeover_rotation_vector_phase: offsets 128..145
seed56 takeover_only_vector_phase:     offsets 90..105
```

Window controls:

```text
seed44 takeover_only_vector_phase:        no signal
seed46 takeover_only_vector_phase:        no signal
seed56 takeover_rotation_vector_phase:    no signal
```

Result:

```text
seed56 is a real takeover-only exception, not a trace-window artifact.
```

Subclass A: single-articulation bridge loss

```text
Observed in seed46 takeover_rotation_vector_phase.

offset 133 -> 134
component count: 15 -> 16
gained cell:     (16,26,24)
lost cell:       (16,27,24)
lost bridge:     (16,27,24)
articulation before loss: yes
rebridge:        offset 141
```

This is the cleanest causal form:

```text
single articulation loss -> temporary split -> paired rebridge
```

Subclass B: multi-cell bridge-loss relocation

```text
Observed in seed44 takeover_rotation_vector_phase and seed56 takeover_only_vector_phase.
```

Seed44 coupled:

```text
offset 443 -> 444
component count: 15 -> 16
gained cells:    (52,25,45), (63,37,31), (63,39,31)
lost cells:      (52,26,44), (63,38,31), (63,40,31)
lost bridges:    (63,38,31), (63,40,31)
articulation before loss: no under single-cell removal
rebridge:        offset 448
```

Seed56 takeover-only:

```text
offset 93 -> 94
component count: 19 -> 20
gained cells:    (15,5,5), (23,61,35)
lost cells:      (14,5,5), (22,61,35)
lost bridge:     (14,5,5)
articulation before loss: no under single-cell removal
rebridge:        offset 104
```

Subclass B causal form:

```text
multi-cell relocation removes bridge support -> temporary split -> multi-cell rebridge
```

Seed56 coupled-law suppression:

```text
seed56 takeover_rotation_vector_phase does not split in the traced window.
It shows a non-splitting bridge swap at offset 92 -> 93:
  component count: 21 -> 21
  gained bridge-if-removed: (45,22,56)
  lost articulation-before: (45,22,55)
```

Interpretation:

```text
The broad no-stored-phase bridge-loss/rebridge morphology is seed-replicated.
The clean single-articulation subclass is not yet seed-robust.
The seed56 takeover-only exception belongs to the multi-cell relocation subclass,
not the seed46 single-articulation subclass.
```

Refined claim:

```text
Local orientation-derived action constraints can produce lawful temporary
component separation and rebridge without payload or stored phase.
```

Next gate:

```text
Finding 059 should run a larger seed/sample matrix for:
  takeover_rotation_vector_phase
  takeover_only_vector_phase

Classify every component signal as:
  A. single-articulation bridge loss
  B. multi-cell bridge-loss relocation
  C. non-bridge component signal

Measure incidence, duration, rebridge delay, and safety.
```

Artifacts:

```text
output/findings/finding058/seed44_coupled_positive_summary.csv
output/findings/finding058/seed44_coupled_positive_transitions.csv
output/findings/finding058/seed46_coupled_positive_summary.csv
output/findings/finding058/seed46_coupled_positive_transitions.csv
output/findings/finding058/seed56_takeover_exception_summary.csv
output/findings/finding058/seed56_takeover_exception_transitions.csv
```

## Finding 059 Update

Finding 059 ran the larger seed/sample class-distribution matrix.

Question:

```text
Does the coupled law change the distribution of structural reorganization
classes?
```

Operational classes:

```text
Class A:
  same single bridge cell is lost and later returns as the bridge path

Class B:
  bridge-loss signal rebridges through a changed bridge/path configuration

Non-bridge:
  component signal without bridge-loss cause

No signal:
  no component signal within horizon
```

Strict single-articulation restoration was also tracked separately:

```text
same bridge restored AND lost bridge was an articulation before loss
```

Matrix:

```text
seeds:       42,43,44,45,46,56
samples:     0..7
checkpoint:  2048
horizon:     600
cases/law:   48
World.P:     zero
action_phase: absent
```

Laws:

```text
zero_phase
takeover_only_vector_phase
takeover_rotation_vector_phase
```

Aggregate:

```text
zero_phase:
  no signal cases:      45 / 48
  Class A cases:         0 / 48
  Class B cases:         3 / 48
  signal intervals:      5
  mean J:                0.000
  mean displacement:     1.000

takeover_only_vector_phase:
  no signal cases:      40 / 48
  Class A cases:         1 / 48
  Class B cases:         7 / 48
  signal intervals:     19
  mean J:                0.053
  mean displacement:     0.947

takeover_rotation_vector_phase:
  no signal cases:      36 / 48
  Class A cases:         2 / 48
  Class B cases:        10 / 48
  signal intervals:     15
  mean J:                0.156
  mean displacement:     0.844
```

Safety:

```text
payload-zero cases: 144 / 144
ledger-exact cases: 144 / 144
```

Strict Class A:

```text
same bridge restored AND articulation-before-loss:
  zero_phase:                     0
  takeover_only_vector_phase:     0
  takeover_rotation_vector_phase: 0
```

So observed Class A rows are same-bridge restorations, not strict
single-articulation-restoration events.

Class B transport:

```text
Class B events:
  zero_phase:                      5
  takeover_only_vector_phase:     18
  takeover_rotation_vector_phase: 13

Class B events with J = 0:
  zero_phase:                      5 / 5
  takeover_only_vector_phase:     18 / 18
  takeover_rotation_vector_phase: 12 / 13
```

Interpretation:

```text
Finding 059 is a distributional positive with a caveat.
```

Supported:

```text
No-stored-phase local laws can repeatedly preserve component connectivity
through changes in the cells that instantiate the bridge relation.
```

Also supported:

```text
Orientation-derived takeover and takeover+rotation laws increase the probability
of bridge-reorganization cases relative to zero_phase.
```

Not supported:

```text
Class B is unique to the coupled law.
```

Strongest current statement:

```text
Bridge-path relocation is latent in the payload-free dynamics, and
orientation-derived action constraints increase its incidence.
```

PSA-facing interpretation:

```text
The particular bridge is not the information.
The invariant connectivity constraint is what survives.
```

Next gate:

```text
Finding 060 should separate seed geometry from law effect:
  compare susceptible seeds 44,46,56 against silent seeds 42,43,45
  inspect checkpoint component geometry
  measure bridge/articulation inventory
  measure interface activity before continuation

Question:
  Do orientation-derived laws create bridge relocation, or do they activate a
  pre-existing susceptible bridge geometry?
```

Artifacts:

```text
output/findings/finding059/phase_free_class_matrix_cases.csv
output/findings/finding059/phase_free_class_matrix_signals.csv
output/findings/finding059/phase_free_class_matrix_aggregate.csv
output/findings/finding059/phase_free_class_matrix_summary.json
```

## Finding 060 Update

Finding 060 replaced the planned static susceptibility audit with the stronger
constraint-transport gate suggested after Finding 059.

Question:

```text
Does a Class B successor bridge preserve the relational role of its predecessor
by reconnecting the same pre-existing regions?
```

Method:

```text
replayed all 36 Finding 059 Class B events
required the predecessor bridge set to be role-bearing before loss
tracked the exact predecessor regions through split and rebridge
measured pairwise reachability and shortest-path accessibility
removed the successor bridge to test its causal role
```

Result:

```text
                         Class B   role-bearing predecessor   strict transport
zero_phase                   5               1                       0
takeover_only               18               6                       3
takeover+rotation           13               5                       0
total                       36              12                       3
```

Strict positives:

```text
seed46 sample7 offset 61 -> 65:
  original  (17,27,24)
  successor (16,28,25)

seed46 sample7 offset 420 -> 424:
  original  (39,16,19)
  successor (40,17,20)

seed56 sample3 offset 106 -> 112:
  original  (14,4,5)
  successor (15,5,6)
```

All three strict positives:

```text
bridge Jaccard:                    0.0
pre-loss reachability:            1.0
split reachability:               0.0
post-rebridge reachability:       1.0
successor-removed reachability:   0.0
pre/post shortest path:           2 / 2
flow-accessibility ratio:         1.0
World.P:                          zero
ledger:                           exact
```

Interpretation:

```text
Strict constraint transport exists, but broad Class B is not equivalent to it.
```

`24/36` Class B events lacked a genuinely role-bearing predecessor bridge. In
`9/12` role-bearing cases, the one-cell side disappeared before count recovery.
The three strict positives preserve a large-region/singleton relation through
complete replacement of a causally necessary bridge. The result is replicated
across two seeds, but is still a minimal relation rather than a general
multi-region invariant.

The takeover-plus-rotation law produced no strict transport event despite its
higher broad Class B incidence. The strict positive currently belongs to the
takeover-only law.

Next gate:

```text
Finding 061: predecessor-region lineage and iterated transport
  follow both region descendants after the three strict positives
  measure post-rebridge relation lifetime
  test for a second bridge replacement preserving the same relation
  compare against the nine role-bearing failures
```

Artifacts:

```text
src/phase_free_constraint_transport.py
output/findings/finding060/phase_free_constraint_transport_events.csv
output/findings/finding060/phase_free_constraint_transport_aggregate.csv
output/findings/finding060/phase_free_constraint_transport_summary.json
```

## Finding 061 Kickoff

The repository now has an automation-first research compendium rooted in the
organizing hypothesis:

```text
Information is the change in the reachable caused by interaction.
```

Organizational commits:

```text
a4c034e  Add automation-first research compendium
10d3616  Verify research compendium in CI
de49813  Stop tracking macOS metadata
```

Finding 061 is mapped onto the three strict Finding 060 positives. The
experimental target is now:

```text
track the two predecessor-region lineages beyond rebridge;
measure the lifetime of the restored relation;
detect a second causally necessary bridge replacement;
compare the three strict positives with the nine role-bearing failures.
```

The first lineage definition should be conservative and explicit. A predecessor
region remains address-alive while at least one of its original stationary iota
addresses remains active. A relation remains alive while both address lineages
remain nonempty and mutually reachable. A second strict transport requires:

```text
1. both predecessor address lineages survive;
2. their restored reachability is subsequently lost;
3. their reachability is restored again;
4. the new successor is causally necessary for that restoration;
5. the new successor is disjoint from the prior causal bridge;
6. World.P remains zero and the conservation ledger remains exact.
```

This address-lineage test is intentionally stricter than a future relational or
expression-lineage definition. Failure under this test does not rule out a
relocating expression lineage; it establishes the lifetime of the strongest
identity claim available without adding a lineage-matching assumption.

## Finding 061 Update

Finding 061 replayed all 12 role-bearing predecessor cases from Finding 060
through offset 1024 under the preregistered conservative address-lineage rule.

Result:

```text
strict Finding 060 transports:
  seed46 sample7 rebridge 65:  relation lifetime 9,  lineage loss 74
  seed46 sample7 rebridge 424: relation lifetime 3,  lineage loss 427
  seed56 sample3 rebridge 112: relation lifetime 51, lineage loss 163

role-bearing Finding 060 failures:
  positive relation lifetime at nominal rebridge: 0 / 9

second continuous strict transports through offset 1024: 0 / 12
payload zero: 12 / 12
ledger exact: 12 / 12
```

The strict Finding 060 positives therefore separate perfectly from the nine
role-bearing failures on positive post-rebridge address persistence in this
sample. Every positive terminates because the singleton predecessor address goes
inactive. Later same-address reactivation is not counted as lineage survival.

Next gate:

```text
preregister a non-resurrecting expression-lineage matcher;
use local transition ancestry to define singleton relocation prospectively;
test whether relational persistence continues past address-lineage termination.
```

Artifacts:

```text
src/predecessor_region_lineage.py
output/findings/finding061/predecessor_region_lineage_cases.csv
output/findings/finding061/predecessor_region_lineage_timeline.csv
output/findings/finding061/predecessor_region_lineage_summary.json
```

## Finding 062 Kickoff

Finding 062 tests whether the singleton predecessor expression continues after
its original stationary address becomes inactive.

Prospective expression-lineage rule:

```text
At each tick, a lineage retains its addresses that remain active.

A newly activated target inherits a lineage only when the successful transfer
that activates it has a source in that lineage at the start of the tick.

An already-active target does not acquire lineage through a later transfer.

If two predecessor lineages claim the same newly activated target in one tick,
the identity is marked collided and is not eligible for a strict result.

Once a lineage has no retained address and no directly activated child, it
terminates permanently. Later same-address activation cannot resurrect it.
```

The matcher is deliberately local and prospective. It uses only successful
source-to-target activation events available at the tick being classified. It
does not select a descendant using later connectivity or knowledge of the
desired outcome.

Instrumentation gate:

```text
run identical hooked and unhooked continuations;
require exact equality of all world arrays, counters, and RNG state;
do not proceed if the measurement hook changes dynamics.
```

Finding 062 success requires a singleton expression lineage to survive beyond
the Finding 061 address-lineage termination and preserve or later restore its
relation to the independently tracked large-region expression lineage. A second
strict transport additionally requires a surviving pair, a genuine intervening
disconnection, and causal reconnection through a bridge disjoint from the prior
bridge.

## Finding 062 Update

Finding 062 passed its instrumentation gate and replayed all 12 role-bearing
Finding 060 cases through offset 1024.

Instrumentation equivalence:

```text
paired hooked/unhooked steps: 128
successful transfers observed: 94
world arrays equal after every step: yes
RNG states equal after every step: yes
```

Strict-positive result:

```text
seed46 sample7 event 61 -> 65:
  address relation lifetime:       9
  expression relation lifetime:  170
  survival beyond address death: 161
  expression loss offset:        235

seed46 sample7 event 420 -> 424:
  address relation lifetime:       3
  expression relation lifetime:  601 (alive at horizon)
  survival beyond address death: at least 598

seed56 sample3 event 106 -> 112:
  address relation lifetime:      51
  expression relation lifetime:  51
  survival beyond address death:  0
```

The first seed46 terminal-address handoff is explicit:

```text
offset 74: (17,28,25) -> (17,29,25)
target newly activated by the lineage source
source inactive after the step
```

Controls and safety:

```text
positive expression lifetime among role-bearing failures: 0 / 9
lineage collisions:                                      0 / 12
second continuous strict transports:                     0 / 12
payload zero:                                           12 / 12
ledger exact:                                           12 / 12
```

Interpretation:

```text
Prospective expression transport exists in two seed46 trajectories, but is not
yet seed-robust. The seed56 strict relation terminates without a qualifying
child. No iterated disconnection/rebridge was observed.
```

Next gate:

```text
branch continuations immediately before the two seed46 address losses and the
seed56 termination;
test expression-handoff robustness across continuation RNG;
identify the local condition separating handoff from termination.
```

Artifacts:

```text
src/expression_lineage_transport.py
output/findings/finding062/expression_lineage_cases.csv
output/findings/finding062/expression_lineage_ancestry.csv
output/findings/finding062/expression_lineage_timeline.csv
output/findings/finding062/expression_lineage_summary.json
```

## Finding 063 Kickoff

Finding 063 branches the exact natural trajectories at strict rebridge, the
earliest shared point at which predecessor expression identity is established:

```text
seed46 sample7 event 61 -> 65:   branch state offset 65,  natural loss 74
seed46 sample7 event 420 -> 424: branch state offset 424, first child 426,
                                     natural loss 427
seed56 sample3 event 106 -> 112: branch state offset 112, natural loss 163
```

Only the continuation RNG changes after the branch state. Model law, world
arrays, tracked expression lineages, payload clamp, and all configuration values
remain fixed.

Primary endpoint:

```text
Among branches in which the original singleton address becomes inactive within
the declared horizon, what fraction retain a nonempty singleton expression
lineage immediately after that first deactivation through a successful
source-to-new-target activation on or before the death step?
```

Censoring and exclusions:

```text
address does not deactivate within horizon -> censored, not failure
lineage collision before endpoint          -> ambiguous, excluded from strict rate
lineage terminates before address death    -> failure
same-address reactivation after termination -> never resurrection
```

Secondary measurements:

```text
time to first address loss;
number and coordinates of qualifying children on the death tick;
source/target action order and depleted status;
post-loss expression survival and relation lifetime;
payload-zero and ledger-exact safety.
```

The seed56 state is the preregistered negative comparator. Finding 063 tests RNG
robustness of the two seed46 handoff-capable states; it does not yet establish
robustness across independently generated geometries.

Preregistration correction before execution:

```text
The second seed46 branch was moved from offset 426 to offset 425 because Finding
062 ancestry shows its first qualifying child is already active at 426. Branching
at 426 would hold the handoff fixed rather than test its RNG robustness. No
Finding 063 branch outcomes had been generated when this correction was made.
```

Second preregistration correction before execution:

```text
Following review of the causal question, all three branch states were moved to
their strict-rebridge offsets: 65, 424, and 112. Rebridge is the earliest point
at which the same predecessor expression relation is prospectively established
in every source case. This retains the complete post-transport pre-handoff
history rather than varying only the final one or two draws. It also prevents
the second seed46 handoff from being baked into the branch state. No Finding 063
branch outcomes had been generated when this correction was made.
```

## Finding 063 Update

Finding 063 launched 32 continuation-RNG branches from each strict-rebridge
state, before any qualifying expression child activation.

Result:

```text
seed46 event 61:   16 / 32 handoffs = 0.500
  Wilson 95%: [0.336, 0.664]

seed46 event 420:  29 / 32 handoffs = 0.906
  Wilson 95%: [0.758, 0.968]

seed56 event 106:  28 / 32 handoffs = 0.875
  Wilson 95%: [0.719, 0.950]
```

Pairwise two-sided Fisher exact tests:

```text
seed46 event61 vs seed46 event420: p = 0.0007517
seed46 event61 vs seed56 event106: p = 0.0025144
seed46 event420 vs seed56 event106: p = 1.0
```

All 96 original singleton addresses deactivated within horizon 128. There were
no censored endpoints, no lineage collisions, no payload, and no ledger error.

Interpretation:

```text
The natural seed56 failure is continuation-contingent, not a state-level
prohibition. Expression handoff is possible from all three source states, but
its probability is state-conditioned. The first seed46 state is lower
susceptibility; the second seed46 and seed56 states are indistinguishable here.
```

Next gate:

```text
record prospective pre-death local features for all successful and failed
branches;
derive a compact candidate continuation rule on training branch seeds;
freeze the rule;
test prediction on held-out branch seeds.
```

Artifacts:

```text
src/expression_handoff_branch_ensemble.py
output/findings/finding063/expression_handoff_cases.csv
output/findings/finding063/expression_handoff_aggregate.csv
output/findings/finding063/expression_handoff_comparisons.csv
output/findings/finding063/expression_handoff_summary.json
```

## Finding 064 Kickoff

Finding 064 tests whether a compact prospective local condition predicts
singleton expression handoff.

Frozen dataset split:

```text
training: branch_sample 0..15 from each of the three Finding 063 source states
held out: branch_sample 16..31 from each source state
training rows: 48
held-out rows: 48
```

Every feature is captured from the world state immediately before the step that
first deactivates the original singleton address. No successful-transfer,
target-child, post-step, future-connectivity, or outcome field is eligible as a
predictor.

Preregistered candidate features:

```text
time from strict rebridge to terminal step;
singleton expression-lineage size;
original-address A, R, V, and angular_L;
face6, face18, and cube26 active-neighbor counts;
cube26 depleted and latent inactive-neighbor counts;
whether original-address removal increases component count;
primary vector target active/depleted/latent status;
number of cube26 directions within declared range leading to active, depleted,
or latent targets;
current predecessor-lineage reachability and shortest-path distance.
```

Frozen learner:

```text
enumerate every midpoint threshold for each numeric feature;
test both <= and > prediction directions;
select the decision stump with maximum training balanced accuracy;
break ties by feature name, threshold, then direction;
freeze that one-feature rule;
evaluate it once on held-out branch samples 16..31.
```

Reported held-out metrics:

```text
accuracy, sensitivity, specificity, balanced accuracy;
confusion matrix;
two-sided Fisher exact association between prediction and handoff;
per-source performance.
```

This is a compact candidate continuation rule, not an if-and-only-if law. Failure
to generalize rejects the stump without invalidating expression lineage.

## Finding 064 Update

Finding 064 reproduced the Finding 063 outcomes on the same 96 branch seeds,
captured 20 strictly pre-step terminal features, trained on branch samples 0..15,
and evaluated once on held-out samples 16..31.

Frozen training-selected stump:

```text
singleton_lineage_size > 1.5 -> predict handoff
training balanced accuracy: 0.676
```

Held-out result:

```text
TP=13 FP=0 TN=12 FN=23
accuracy:          0.521
sensitivity:       0.361
specificity:       1.000
balanced accuracy: 0.681
two-sided Fisher:  p=0.0210103
```

Interpretation:

```text
A preexisting descendant is a sufficient terminal-state marker in this sample,
but it is not the continuation law. It misses most handoffs created on the death
tick and every held-out positive from seed46 event61.
```

Next gate:

```text
restrict to terminal rows with singleton_lineage_size == 1;
exclude the preexisting-descendant marker;
retain the frozen train/test split;
test whether strictly pre-step local geometry predicts death-tick child creation.
```

Artifacts:

```text
src/lineage_continuation_rule.py
output/findings/finding064/lineage_continuation_rule_dataset.csv
output/findings/finding064/lineage_continuation_rule_model.json
output/findings/finding064/lineage_continuation_rule_per_source.csv
output/findings/finding064/lineage_continuation_rule_summary.json
```

## Finding 065 Update

Finding 065 restricted discovery to single-address terminal rows, excluded the
preexisting-descendant marker, froze a new stump, and evaluated it on 96 fresh
branch samples 32..63.

Frozen discovery rule:

```text
cube26_active_neighbors <= 1.5 -> predict death-tick child
eligible discovery rows: 35
discovery balanced accuracy: 0.669
```

Fresh confirmation:

```text
eligible single-address endpoints: 71
excluded preexisting descendants: 25
TP=39 FP=12 TN=8 FN=12
accuracy:          0.662
sensitivity:       0.765
specificity:       0.400
balanced accuracy: 0.582
two-sided Fisher:  p=0.240255
```

The rule did not confirm. No threshold was retuned on confirmation data.

Interpretation:

```text
Static terminal scalar geometry, as currently measured, is insufficient for a
general death-tick continuation rule. The missing variable may be the ordered
candidate-selection and RNG-gated transfer process within the terminal tick.
```

Next gate:

```text
instrument every ordered singleton-source candidate on the terminal tick;
record eligibility, influence, probability, gate draw, activation, and source
exhaustion;
determine whether the event process fully accounts for continuation.
```

Artifacts:

```text
src/death_tick_child_rule.py
output/findings/finding065/death_tick_child_rule_confirmation.csv
output/findings/finding065/death_tick_child_rule_model.json
output/findings/finding065/death_tick_child_rule_per_source.csv
output/findings/finding065/death_tick_child_rule_summary.json
```

## Finding 066 Kickoff

Finding 066 tests whether the ordered lawful event process within the terminal
tick completely accounts for death-tick child creation.

Conceptual caution:

```text
Different outcomes from similar scalar geometry do not by themselves establish
non-Markovian history dependence. The complete simulation state includes all
attribute arrays, angular state, previous-state arrays, and RNG state. Finding
066 separates observed static geometry from hidden-but-present state, stochastic
gate realization, and fixed within-tick evaluation order.
```

Fresh ensemble:

```text
branch_sample 64..95 from each strict-rebridge state
96 new continuation RNG streams
branch offsets 65, 424, and 112
horizon 128
```

The candidate observer is default-off and measurement-only. Before scientific
use it must pass paired hooked/unhooked equality after every step for all world
arrays and RNG state.

For every candidate considered from the singleton expression source on the step
that first deactivates its original address, record in actual evaluation order:

```text
source and target coordinates;
candidate order and spatial step;
source available amplitude before evaluation;
target active/depleted/latent status at evaluation;
eligibility or rejection reason;
influence and residual multiplier;
transfer probability;
gate draw when evaluated;
gate pass/fail;
whether the transfer succeeded;
whether the target changed inactive -> active;
whether that activation inherited singleton ancestry;
source active/amplitude state after the completed tick.
```

Predeclared outcome classes:

```text
preexisting_descendant:
  lineage already has another active address before original-address death

no_eligible_successor:
  no evaluated candidate could lawfully activate a new target

eligible_not_selected_or_reached:
  a potential successor existed but source exhaustion/order prevented evaluation

gate_failed:
  at least one eligible new-target candidate was evaluated and every gate failed

activated_child:
  a singleton-lineage source passed its gate and newly activated a child

target_preempted:
  another source activated the target before singleton-source evaluation

ambiguous_collision:
  more than one predecessor lineage claims the same newly activated target
```

Finding 066 first asks for complete accounting: every branch must map to exactly
one declared terminal class with no unexplained outcome. Only after inspecting
that frozen ledger may a one-event causal replay be specified. The replay must
change one gate or ordering event and preserve all other state and random draws
as far as the implementation permits.

## Finding 065 Kickoff

Finding 065 targets the 23 held-out Finding 064 handoffs that were created on
the address-death tick rather than existing beforehand.

To avoid reusing an inspected held-out set as fresh confirmation:

```text
discovery rows:
  Finding 064 branch_sample 0..15 only
  restrict to singleton_lineage_size == 1 immediately before address death

fresh confirmation branches:
  branch_sample 32..63 from each of the three strict-rebridge states
  96 new continuation RNG streams
  restrict evaluation to singleton_lineage_size == 1 at address death

branch_sample 16..31:
  not used for Finding 065 selection or confirmation
```

The preexisting-descendant feature is removed. Candidate features are the
remaining preregistered Finding 064 features available before the death step.

Frozen learner:

```text
one numeric feature, one midpoint threshold, both prediction directions;
maximize balanced accuracy on eligible discovery rows;
deterministic tie break by feature, threshold, direction;
freeze once;
evaluate once on eligible fresh confirmation rows.
```

Primary confirmation report:

```text
eligible and excluded endpoint counts;
confusion matrix;
sensitivity, specificity, balanced accuracy;
two-sided Fisher exact association;
per-source metrics;
payload-zero, ledger-exact, and lineage-collision safety.
```

This experiment may reject the current local feature set. A null confirmation
means these terminal scalar features do not capture a general death-tick child
rule; it does not negate the prospectively observed lineages.

## Finding 066 Update

Finding 066 completed the preregistered ordered terminal-event audit on fresh
branch samples 64..95 from each of the three strict Finding 060 states.

The default-off candidate observer passed exact world-state and RNG equivalence
while observing 21,160 events. The terminal dataset contains 96 branches and
20,748 ordered candidate records. All 96 outcomes map to exactly one declared
class: 57 `activated_child`, 16 `preexisting_descendant`, 19
`source_exhausted`, 3 `gate_failed`, and 1 `target_preempted`. There were zero
lineage collisions; payload remained zero and the conservation ledger remained
exact in every branch.

After the complete ledger was inspected, one replay target was frozen:

```text
source state: seed 46, Finding 060 start offset 420
branch sample/seed: 78 / 2026081178
terminal offset: 435
source: (40,17,19)
successor: (39,17,19)
candidate order: 5
natural probability/draw: 0.014745667567410982 / 0.12253392848602684
intervention: permit this gate while still consuming the natural RNG draw
```

The baseline died with no descendant. The one-gate intervention created exactly
one ancestry-preserving child and flipped the branch to collision-free handoff.
This is bounded causal evidence that continuation in this case depends on an
eligible successor being realized before the singleton source spends its final
amplitude on a later candidate. It does not yet establish a universal law or
show that the simulator's iteration order is substrate-independent.

Next: replicate frozen one-event interventions across the remaining natural
failure mechanisms, then test the temporal rule on independently generated
source geometries.

## Finding 067 Kickoff

Finding 067 is a prospective matched causal-replication study of the three
natural death labels isolated in Finding 066. The labels are hierarchical, not
mechanistically exclusive: gate-labeled and preemption-labeled cases may still
terminate by spending their final amplitude. The intervention semantics
below are frozen before examining any Finding 067 branch outcome.

Confirmation ensemble:

```text
source states: the three strict Finding 060 rebridge states
fresh branch_sample: 96..159 inclusive
branches per source: 64
total natural baselines: 192
branch offsets: 65, 424, 112
natural horizon: 128 offsets
post-intervention horizon: 256 offsets
```

Only collision-free, single-address natural deaths enter a death-class causal
cohort. Preexisting-descendant and natural-child cases remain negative controls
for accounting but receive no rescue intervention.

Frozen one-decision interventions:

```text
gate_failed:
  permit the first naturally failed singleton-source gate whose target is
  inactive at evaluation

source_exhausted:
  veto the successful singleton-source transfer to an already-active target
  that consumes its last available amplitude immediately before exhaustion

target_preempted:
  veto the earlier successful activation that changes the singleton's first
  preempted target from inactive-at-tick-start to active-before-evaluation
```

Each intervention changes exactly one gate result, consumes the original gate
draw, and leaves the world identical through that decision. A matched sham uses
the same override path but returns the natural gate result unchanged. Exact
baseline/sham equality is mandatory. RNG alignment is claimed only through the
intervened draw; subsequent random-draw counts may lawfully diverge after state
divergence.

Outcomes, reported separately by natural death label and causal mediator:

```text
immediate ancestry-preserving child on the intervention tick;
route reopened immediately afterward (capacity retained, a previously unreached
candidate evaluated, or the preempted target remains available);
delay to original-address death;
ancestry-preserving handoff at first post-intervention address death;
collision, payload-zero, and ledger-exact safety;
paired flip counts and exact binomial intervals.
```

The gate-failure manipulation is an efficacy test, not an estimate of natural
gate probability. The exhaustion and preemption manipulations test whether the
identified closing event is causally necessary in that branch; a still-negative
outcome is informative because removing one closure need not realize a child.
No class-level replication claim is permitted for a death class with fewer than
five eligible fresh branches.

Pre-outcome implementation refinement: the first fresh branch revealed that the
Finding 066 precedence label `gate_failed` includes failed gates to already
active targets, which are not successor opportunities. Before producing any
Finding 067 aggregate, causal-cohort assignment was therefore frozen directly
from the ledger mechanism:

```text
target_preempted: an inactive-at-start target is active before singleton review;
gate_failed: a singleton gate to a target inactive at evaluation naturally fails;
source_exhausted: a successful non-child transfer spends the final amplitude
                  before a selected candidate is reached.
```

The original Finding 066 outcome label is retained in the data, but intervention
and aggregation use this causal ledger label. This changes no threshold and
uses no counterfactual outcome.

After these semantics are frozen and evaluated, the same protocol may be
carried unchanged to a preregistered fresh-initialization geometry screen. New
geometries must be selected by the strict Finding 060 transport criteria alone,
without inspecting their Finding 067 intervention outcomes.

Independent-geometry stage, frozen before the screen:

```text
initialization seeds: 57..72 inclusive (16 never-used seeds)
law/config: canonical v0.3.6; change only init.seed and objective in memory
variant: takeover_only_vector_phase
checkpoint: 2048
continuation samples: 0..7 for every initialization seed
continuation RNG: unique stream keyed by initialization seed and sample
horizon: 600
screen completion: all 128 cases, regardless of when positives appear
```

Every Class B event receives the frozen Finding 060 strict-transport audit.
Temporal-test eligibility additionally requires exactly two reconstructed
predecessor regions, exactly one singleton predecessor, singleton persistence
and activity at rebridge, a causally necessary successor, and bridge Jaccard
zero. All candidates and exclusions remain in the manifest. For the primary
independent analysis, select at most one eligible event per initialization seed:
the lexicographically first `(sample_index, start_offset, rebridge_offset)`.
Selection is frozen and hashed before terminal outcomes are examined.

Each selected source is branched at rebridge, never at a terminal-aligned offset:

```text
branch samples per independent source: 32 (0..31)
natural and replay horizon from rebridge: 256
same causal-label detector and one-decision intervention policy as Finding 067A
primary unit of generalization: initialization seed/source geometry
```

Zero qualifying geometries is inconclusive. Results are source-clustered; branch
replicates are conditional stochastic trials and are not counted as independent
geometries.

## Finding 067A Result and 067B Source Freeze

The prospective same-state confirmation completed 192 fresh natural branches
(samples 96..159). The frozen causal-ledger detector yielded 36 eligible
one-decision replays:

```text
successor-gate failures: 6
  route reopened: 6/6
  immediate ancestry child: 6/6
  eventual handoff: 6/6

source exhaustion: 30
  route reopened: 30/30
  immediate ancestry child: 3/30
  eventual handoff: 28/30
  median address-loss delay: 5.5 offsets

target preemption: 0 fresh eligible cases; unreplicated
```

All matched shams were exact, each intervention matched exactly one frozen gate,
and all natural and intervention trajectories were collision-free, payload-zero,
and ledger-exact. The two exhaustion non-rescues still reopened the route but
later died without handoff, demonstrating that extending opportunity lifetime is
not identical to realizing a successor.

The independent screen then completed all 128 preregistered cases across
initialization seeds 57..72. It audited 29 Class B candidates, found four strict
singleton-eligible transports across two initialization seeds, and froze one
primary source per seed before terminal outcomes:

```text
f067b-source-001: seed 58, sample 1, split 447, rebridge 458
f067b-source-002: seed 71, sample 6, split 188, rebridge 194
```

The two additional eligible events (seed 58 sample 5; seed 71 sample 7) remain
in the manifest but are excluded from the primary geometry analysis. Frozen
source-manifest SHA-256:

```text
15ed649a3db93492e1b2cbe4ea72261c10717cf2cdb6a07f6df6eb25b59d717e
```

No independent terminal or intervention outcome had been inspected when this
selection was frozen.

## Finding 067 Independent Result

Commit `0e22828` froze the complete independent screen and source-manifest hash
before any selected-source terminal outcome was evaluated. The unchanged
protocol then ran 32 rebridge branches from each of the two primary geometries.

Across 64 independent-geometry branches, natural outcomes were 54 immediate
children, 8 successor-gate deaths, 1 exhaustion death, and 1 preemption death.
The frozen interventions produced:

```text
seed 71 successor-gate cohort:
  8/8 routes reopened
  8/8 immediate ancestry children
  8/8 eventual handoffs

seed 58 exhaustion cohort:
  1/1 route reopened
  0/1 immediate child
  0/1 eventual handoff; address death delayed 24 offsets

seed 71 preemption cohort:
  1/1 target made available
  0/1 immediate child
  1/1 eventual handoff; address death delayed 4 offsets
```

All ten independent replays had exact matched shams and exactly one overridden
gate; all were collision-free, payload-zero, and ledger-exact. Only the
successor-gate cohort meets the preregistered minimum of five cases. The two
singleton cohorts are case-level causal demonstrations, not class-level
replications.

Finding 067 therefore supports a two-stage mechanism: a successor route must
remain available, and it must be realized while available. Reopening a route is
causal but does not guarantee realization, as shown by the independent seed-58
exhaustion non-rescue. The claim remains about this declared simulator and its
selected-candidate schedule, not a substrate-independent law of time.

## Finding 068 Kickoff

Finding 068 prospectively tests necessity and redundancy of realized
continuation. The intervention policy below is frozen before inspecting any
Finding 068 natural or counterfactual outcome.

Fresh cohorts:

```text
original three strict source states:
  branch_sample 160..223 inclusive
  64 branches per source; 192 total
  branch offsets 65, 424, 112
  natural terminal horizon 128

two independently initialized Finding 067 source geometries:
  frozen source manifest SHA-256
    15ed649a3db93492e1b2cbe4ea72261c10717cf2cdb6a07f6df6eb25b59d717e
  branch_sample 32..63 inclusive
  32 branches per source; 64 total
  branch exactly at rebridge
  natural terminal horizon 256
```

Natural intervention eligibility:

```text
collision-free Finding 066 outcome label activated_child;
singleton lineage size exactly one immediately before address death;
no preexisting descendant;
at least one successful singleton-source transfer that newly activates its
target on the death tick.
```

Frozen selector and intervention:

```text
select the earliest such child-producing candidate in actual terminal-tick
event order;
consume its natural RNG draw but force that one gate to fail;
change no geometry, amplitude, target state, or other gate directly;
follow for 128 offsets after the intervention tick or until first subsequent
original-address death, whichever supplies the declared endpoint.
```

A matched sham traverses the identical override path but returns the natural
gate result. Exact world/RNG equality through the natural terminal tick and
exactly one selector match are mandatory.

Primary outcomes:

```text
targeted child-producing event suppressed;
alternate ancestry child on the same tick;
source capacity retained after veto;
original-address death delay;
ancestry-preserving handoff at first post-veto address death;
same-target versus different-target alternate child;
first alternate-child delay;
censoring when the original address remains active through follow-up.
```

Predeclared causal classes:

```text
alternate-child timing (independent axis):
  same_tick / delayed / none

fixed-follow-up endpoint (independent axis):
  handoff_at_first_address_loss
  lineage_loss_at_first_address_loss
  source_survival_censored
```

The experiment tests necessity of the selected realization, not an abstract
claim that no other lawful realization could exist. Vetoing a successful gate
retains source amplitude and therefore intentionally exposes redundant routes;
that exposure is the estimand. Results are reported per source geometry, with
initialization seed as the independent unit. A minimum of five eligible branches
permits a within-source conditional rate estimate; replication requires
directional agreement across independent initialization seeds. Payload-zero, ledger-exact, and
collision-free safety remain mandatory.

Pre-outcome audit refinement: Finding 068 uses a two-stage prospective freeze.
First, every scheduled factual branch is run with no veto. All eligible natural
children are written to a selector manifest containing exact event identity,
draw, probability, and natural child multiplicity; that manifest is hashed and
committed. Only then may the counterfactual stage consume it. No branch is
selected from a veto outcome, and the full scheduled factual matrix is retained.

Eligibility requires an exact inherited-child join: the successful candidate's
source is in the pre-step singleton lineage, its target is inactive at
evaluation and newly activated, the terminal lineage is collision-free, and the
target is therefore claimed by that lineage under the frozen `advance_lineages`
rule. Natural unique-child and multi-child cases are stratified but both remain
in the intervention cohort. Alternate-child timing and address-loss endpoint
are reported orthogonally. RNG identity is asserted only through the selected
draw; downstream draw counts may diverge lawfully after veto.

## Finding 068 Selector Freeze

The factual-only stage completed all 256 scheduled branches without invoking a
veto. Natural outcomes were 164 `activated_child`, 38
`preexisting_descendant`, 40 `source_exhausted`, 11 `gate_failed`, and 3
`target_preempted`.

All 164 activated-child cases passed the frozen necessity eligibility rule and
all had natural child multiplicity exactly one. Selector counts by source were:

```text
original seed 46 / start 61:   33
original seed 46 / start 420:  39
original seed 56 / start 106:  36
independent seed 58 source:    30
independent seed 71 source:    26
```

Every inheritance join was verified; there were zero selector collisions,
payload remained zero, and the ledger remained exact. Frozen selector-manifest
SHA-256:

```text
9e4a70d8d0b829b4a4b288da69b8a740c398b5c161a0e5a26a7605015e8c8cb0
```

No veto outcome had been run or inspected when this manifest was frozen.

## Finding 068 Result

The replay stage consumed only selector manifest
`9e4a70d8d0b829b4a4b288da69b8a740c398b5c161a0e5a26a7605015e8c8cb0`,
which was committed in `a951f59` before any veto outcome was run.

All 164 selected natural child events were suppressed by exactly one gate veto.
The response decomposed cleanly:

```text
alternate ancestry child timing:
  same tick:   5
  delayed:   117
  none:       42

address-loss endpoint:
  handoff:    122
  lineage loss: 42
  source-survival censoring: 0
```

The two axes matched exactly in this experiment: every one of the 122 branches
that realized an alternate child handed off, and all 42 branches without an
alternate child lost the lineage at first address death. The first alternative
used the originally selected target in 17/122 cases and a different target in
105/122. Source capacity was retained immediately after veto in 161/164 cases.

Per-source eventual handoff after veto:

```text
original seed 46 / start 61:   17/33
original seed 46 / start 420:  31/39
original seed 56 / start 106:  31/36
independent seed 58:           23/30
independent seed 71:           20/26
```

Thus the one natural child event was branch-necessary in 42/164 cases and
temporally redundant in 122/164. Redundancy and necessity both occurred in
every initialization seed represented. This estimates robustness conditional
on factual continuation; it does not estimate necessity prevalence across all
branches. The exact alternate-child/handoff correspondence partly follows the
operational lineage definition and is not treated as an independent predictive
association.

All shams preserved exact world and RNG state through the selector. Every
selector identity, original draw, and probability matched; there was exactly
one override per replay, zero lineage collisions, zero payload, and exact
conservation.

## Finding 069 Kickoff

Finding 069 measures a prospective sequential realization cut depth. It does
not claim the graph-theoretic minimum over every possible intervention subset.
The estimand is the number of ancestry-producing events that must be vetoed
along the nested counterfactual path generated by the frozen policy before the
original address dies without a descendant.

Starting cohort and depth 1 are fixed by Finding 068:

```text
committed depth-1 selector manifest:
  9e4a70d8d0b829b4a4b288da69b8a740c398b5c161a0e5a26a7605015e8c8cb0
branches: 164 factual unique-child continuations
depth-1 cuts: 42 lineage losses
depth-1 survivors: 122 alternate-child handoffs
```

Staged protocol for depths 2 through 8:

```text
1. Reproduce the prior committed veto chain exactly.
2. On every surviving branch, permit and record the first next
   ancestry-preserving child, including its gate ordinal, complete candidate
   identity, probability, and draw.
3. Write and hash the complete next-depth selector manifest.
4. Commit that manifest before vetoing any selector it contains.
5. Replay from the branch state, veto every committed child in order through
   the current depth, and follow to first original-address death or the fixed
   Finding 068 horizon (128 offsets after the depth-1 intervention).
6. Record the first still-unvetoed child as the next prospective selector.
```

No survivor-count stopping is permitted. The process stops only when no next
selector exists or after depth 8. A branch losing lineage for the first time at
depth `d` has sequential cut depth `d`; a branch still handing off after depth 8
is right-censored above 8; continued original-address activity is separately
source-survival censored.

Each stage must reproduce every earlier selector exactly and match the new
selector's source, target, candidate step/order, gate ordinal, amplitude, target
state, probability, draw, and natural pass before intervention. The original
draw is consumed. RNG identity is claimed only through each intervened event;
later draws may diverge lawfully. Collision, payload, and conservation failures
remain recorded protocol failures rather than post-treatment exclusions.

Primary reports:

```text
sequential cut-depth distribution 1..8;
survival curve after each added veto;
same-target versus different-target route replacement;
child delay and address-loss delay by depth;
per-source and per-initialization-seed conditional rates;
right-censoring and source-survival censoring.
```

This experiment characterizes redundancy under a specific retained-amplitude,
ordered veto policy. It does not prove that the discovered set is the smallest
possible cut under arbitrary state interventions or schedulers.

## Finding 069 Depth-2 Selector Freeze

The committed depth-1 policy was reproduced across all 164 Finding 068
selectors and matched the prior replay table exactly: 42 lineage losses and 122
handoffs. No transient child occurred in a depth-1 loss case, and there was no
source-survival censoring.

Each of the 122 handoff survivors exposed exactly one first next inherited child.
Those depth-2 selectors span all five source states:

```text
original seed 46 / start 61:   17
original seed 46 / start 420:  31
original seed 56 / start 106:  31
independent seed 58:           23
independent seed 71:           20
```

Every earlier selector and every new inheritance join matched exactly; payload
remained zero, the ledger remained exact, and there were zero collisions.
Frozen depth-2 selector-manifest SHA-256:

```text
37376530450191f0889060a8bc51a2b5de0cc464fa85b42a1c2ced644d517a4b
```

No depth-2 selector had been vetoed when this manifest was frozen.

## Finding 069 Depth-2 Result and Depth-3 Freeze

Vetoing both committed realization events produced 20 new lineage cuts among
the 122 depth-2 risk-set branches. The other 102 handed off and each exposed
exactly one first next inherited child. There were no transient-child losses,
source-survival censoring, collisions, payload, or ledger errors.

```text
cut depth 1: 42
cut depth 2: 20
surviving beyond depth 2: 102
```

Frozen depth-3 selector-manifest SHA-256:

```text
3d131049d9a28582e805536893d2ad522cece467e1ed23fc6d258f64cfaa2a2c
```

No depth-3 selector had been vetoed when this manifest was frozen.

## Finding 069 Depth-3 Result and Depth-4 Freeze

The depth-3 policy produced 22 new lineage cuts among 102 risk-set branches.
The other 80 handed off and supplied the committed depth-4 selector cohort.

```text
cut depth 1: 42
cut depth 2: 20
cut depth 3: 22
surviving beyond depth 3: 80
```

There were no transient-child losses, source-survival censoring, collisions,
payload, or ledger errors. Frozen depth-4 selector-manifest SHA-256:

```text
508934719eeb66d9105c48e14833bb296b34e35040b9cfb5aac43e0e3c714a0f
```

No depth-4 selector had been vetoed when this manifest was frozen.

## Finding 069 Depth-4 Result and Depth-5 Freeze

The depth-4 policy produced 17 new lineage cuts among 80 risk-set branches.
The other 63 handed off and supplied the committed depth-5 selector cohort.

```text
cut depth 1: 42
cut depth 2: 20
cut depth 3: 22
cut depth 4: 17
surviving beyond depth 4: 63
```

There were no transient-child losses, source-survival censoring, collisions,
payload, or ledger errors. Frozen depth-5 selector-manifest SHA-256:

```text
78ddc60ccb9a7d2823998eaccccd455732d30de4cf69a2e3a9c0f29ee26a364c
```

No depth-5 selector had been vetoed when this manifest was frozen.

## Finding 069 Depth-5 Result and Depth-6 Freeze

The depth-5 policy produced 11 new lineage cuts among 63 risk-set branches.
The other 52 handed off and supplied the committed depth-6 selector cohort.

```text
cut depth 1: 42
cut depth 2: 20
cut depth 3: 22
cut depth 4: 17
cut depth 5: 11
surviving beyond depth 5: 52
```

There were no transient-child losses, source-survival censoring, collisions,
payload, or ledger errors. Frozen depth-6 selector-manifest SHA-256:

```text
db63523c994ce4ac12ba7d5af6dfdaa1ba0122e9195773a9f62835e1a4043c9c
```

No depth-6 selector had been vetoed when this manifest was frozen.

## Finding 069 Depth-6 Result and Depth-7 Freeze

The depth-6 policy produced 13 new lineage cuts among 52 risk-set branches.
The other 39 handed off and supplied the committed depth-7 selector cohort.

```text
cut depth 1: 42
cut depth 2: 20
cut depth 3: 22
cut depth 4: 17
cut depth 5: 11
cut depth 6: 13
surviving beyond depth 6: 39
```

There were no transient-child losses, source-survival censoring, collisions,
payload, or ledger errors. Frozen depth-7 selector-manifest SHA-256:

```text
23b39596337afb467d948401af6eea1c381fc2649d07407e77c75868827ad1c3
```

No depth-7 selector had been vetoed when this manifest was frozen.

## Finding 069 Depth-7 Result and Depth-8 Freeze

The depth-7 policy produced 13 new lineage cuts among 39 risk-set branches.
The other 26 handed off and supplied the committed depth-8 selector cohort.

```text
cut depth 1: 42
cut depth 2: 20
cut depth 3: 22
cut depth 4: 17
cut depth 5: 11
cut depth 6: 13
cut depth 7: 13
surviving beyond depth 7: 26
```

There were no transient-child losses, source-survival censoring, collisions,
payload, or ledger errors. Frozen depth-8 selector-manifest SHA-256:

```text
68ffdaba1825f300b007dfd962e54f3fbe64d2a95cfc69f5e8115f9f32dd8a98
```

No depth-8 selector had been vetoed when this manifest was frozen.

## Finding 069 Final Depth-8 Result

The final preregistered depth-8 policy was applied to all 26 committed risk-set
branches. It produced 5 additional lineage cuts, 19 confirmed handoffs, and 2
branches whose original addresses remained active through the fixed endpoint.

```text
sequential cut depth 1: 42
sequential cut depth 2: 20
sequential cut depth 3: 22
sequential cut depth 4: 17
sequential cut depth 5: 11
sequential cut depth 6: 13
sequential cut depth 7: 13
sequential cut depth 8:  5
handoff after eight vetoes (D_seq > 8): 19
source-survival censored at depth 8:      2
total:                                  164
```

The 19 depth-8 handoffs exposed recorded but unvetoed next selectors. Their
artifact SHA-256 is:

```text
e547492ccc891edc4f261e6326a2fa7e7676eb307fdad2aadd64134a8b62b9c4
```

No depth-9 intervention is permitted under the frozen administrative cap.
The 19 handoffs are therefore right-censored above depth 8; the 2 active-source
cases remain separately time-censored and are not counted as handoffs.

All eight stages matched every committed selector and full selector identity.
Payload remained zero, the conservation ledger remained exact, and there were
no collisions or transient-child lineage losses. Finding 069 therefore supports
heterogeneous ordered realization cut depth under the frozen retained-amplitude
veto policy. It does not estimate a graph-theoretic minimum: later opportunities
are observed in counterfactual histories created by earlier vetoes.

## Finding 069 Evidence Integration

Finding 069 is registered as Golden Claim GC-010, with sequential realization
cut depth defined operationally as `DEF-SEQUENTIAL-CUT-DEPTH`. The validated
synthesis is generated from all eight committed stage summaries, case tables,
and selector manifests by:

```text
src/summarize_sequential_cut.py
```

Primary reviewer artifacts:

```text
output/findings/finding069/sequential_realization_cut_summary.json
output/findings/finding069/sequential_realization_cut_assignments.csv
output/findings/finding069/sequential_realization_cut_depths.csv
output/findings/finding069/sequential_realization_cut_sources.csv
output/findings/finding069/sequential_realization_cut_selector_hashes.csv
```

The synthesis independently validates full six-field branch identities, exact
risk-set nesting, all selector and parent-chain hashes, selector-to-parent-case
joins, strict event order, the fixed 128-offset horizon, and both committed
Finding 068 base hashes. It accounts for 648 distinct branch-selector identities
and 2,142 gate-override executions across the nested stage replays. Eighty
branches revisit at least one earlier selector target; this is temporal route
reuse, not a static route count. The longest observed selector span is 120
offsets, the largest inter-selector delay is 71, and the latest classified
address loss remains inside the horizon at delay 121.

`make verify` regenerates the Finding 069 synthesis before building manuscript
macros and evidence manifests, then validates 10 claims and 16 definitions. The
working paper includes a generated depth table and builds successfully as a
10-page PDF.

The next experimental gate is prospective replication on newly screened
independent initialization geometries. Only after that should we compare
alternate selector/scheduler policies or exhaustive small intervention subsets
toward a graph-theoretic minimum or necessary-and-sufficient continuation law.

## Finding 070 Preregistration — Independent Persistence-Depth Replication

Finding 070 tests whether the ordered counterfactual persistence depth observed
in Finding 069 generalizes to newly initialized source geometries. No Finding
070 branch, selector-veto, or cut-depth outcome may be inspected before the
complete source screen and its selected-source manifest are committed.

Frozen geometry screen:

```text
initialization seeds: 73..104 inclusive (32 unused seeds)
continuation samples: 0..7 for every seed
complete matrix: 256 cases; no outcome-dependent stopping
law/config: canonical v0.3.6
allowed in-memory config changes: init.seed and experiment.objective only
variant: takeover_only_vector_phase
checkpoint: 2048
classification horizon: 600
continuation stream base: 20260711
```

Every Class B event receives the unchanged Finding 060 strict-transport audit
and independent predecessor-region reconstruction. Eligibility is unchanged
from Finding 067: strict transport, exactly two predecessor regions, exactly one
singleton predecessor, singleton persistence and activity at rebridge, a
causally necessary successor bridge, bridge Jaccard zero, and exact
reconstruction. All candidates and exclusions remain in the source manifest.

For each qualifying initialization seed, select exactly one primary source: the
lexicographically first `(sample_index, start_offset, rebridge_offset)` eligible
event. All qualifying seeds are retained. The primary unit of geometry
generalization is initialization seed, not continuation branch.

After the screen manifest is committed, run exactly 32 factual branches per
selected source from rebridge using branch samples `0..31`, natural horizon 256,
and a frozen branch-seed base of `2026071500 + source_index*10000`. A branch
enters the primary cut-depth cohort only when it naturally produces exactly one
new ancestry-preserving child from a singleton lineage, with no preexisting
descendant, collision, payload, or ledger error. Freeze the earliest such child
in candidate event order and commit the complete selector manifest before any
veto outcome.

The counterfactual policy is identical to Finding 069:

1. veto the first committed natural child while consuming its recorded draw and
   retaining source amplitude;
2. follow to original-address death or the fixed endpoint 128 offsets after the
   depth-1 natural address-loss tick;
3. for confirmed handoffs, freeze and commit the earliest next inherited child
   before applying the next veto;
4. repeat through depth 8, never resetting the endpoint;
5. classify first lineage loss as ordered cut depth, depth-8 handoff as
   right-censored above 8, and continued original-address activity as separate
   source-survival censoring.

Each depth must reproduce all earlier selectors exactly and match full event
identity before intervention. A matched sham is required through the factual
depth-1 selector. Payload, ledger, collision, selector, and provenance failures
are protocol failures rather than post-treatment exclusions.

Primary reports are the per-depth risk set, new cuts, confirmed handoffs,
source-survival censoring, cut-depth assignments, selector target reuse, and
per-initialization-source distributions. Zero selected geometries is
inconclusive. A geometry-level replication statement requires at least two new
selected initialization seeds and at least five factual eligible selectors in
each; otherwise results remain case-level. Nontrivial counterfactual support is
replicated when a confirmed depth-1 handoff occurs in at least two qualifying
initialization seeds. The estimand remains prefix-minimal under this frozen
retained-amplitude policy, not a graph-theoretic minimum or static route count.

## Finding 070 Independent Source Freeze

The complete preregistered screen finished all 256 cases across initialization
seeds 73..104. It audited 33 Class B candidates and found exactly four strict
singleton-eligible transports, each from a different initialization seed:

```text
f070-source-001: seed 74, sample 2, split 446, rebridge 447
f070-source-002: seed 76, sample 1, split 132, rebridge 135
f070-source-003: seed 81, sample 6, split 204, rebridge 206
f070-source-004: seed 95, sample 3, split 248, rebridge 257
```

All four are retained under the frozen one-source-per-seed rule. There were no
additional eligible events, so no within-seed choice remained after eligibility.
All 256 continuation streams were unique; classification and transport replays
remained payload-zero and ledger-exact. Source-manifest SHA-256:

```text
c2749807dbbd06d8ec6ff52762ca9e1154c5c56be8d037c86e692c66d2114618
```

No selected-source factual branch, child-selector, or veto outcome had been run
when this manifest was frozen.

## Finding 070 Factual Selector Freeze

The committed four-source geometry cohort produced 128 complete factual
branches, 32 per source. Natural terminal outcomes were:

```text
activated unique child: 79
successor gate failed:   18
source exhausted:        24
target preempted:          7
total:                   128
```

All 79 natural child cases produced exactly one inherited child and passed the
frozen primary selector rule. Eligible selectors by independent geometry:

```text
f070-source-001 / seed 74: 22
f070-source-002 / seed 76: 21
f070-source-003 / seed 81: 23
f070-source-004 / seed 95: 13
```

Every source exceeds the preregistered five-selector geometry threshold.
Inheritance joins, payload, conservation, collision, and branch-identity audits
all passed. Frozen factual selector-manifest SHA-256:

```text
01ad7968c7bdd2795c5d7029b481a4420982f3e4c940e99dcf5fd71297bc17e7
```

No selector veto or counterfactual endpoint had been run when this manifest was
frozen.

## Finding 070 Depth-1 Result and Depth-2 Freeze

Vetoing the 79 committed factual child events produced 23 lineage cuts and 56
confirmed handoffs. Nontrivial counterfactual support replicated independently
in all four new initialization geometries:

```text
seed 74: 16 handoffs /  6 cuts
seed 76: 15 handoffs /  6 cuts
seed 81: 19 handoffs /  4 cuts
seed 95:  6 handoffs /  7 cuts
total:   56 handoffs / 23 cuts
```

Every matched sham was state/RNG exact through the factual selector. Every
selector matched once with full identity; payload remained zero, conservation
remained exact, and there were no collisions, transient-child losses, or source
censors. The 56 confirmed handoffs each supplied one committed depth-2
selector. Frozen depth-2 selector-manifest SHA-256:

```text
256dfe0ad291ce835aab6a239032c7d0089f8755e985779a2bea44d79cd8ed5d
```

No depth-2 selector had been vetoed when this manifest was frozen.

## Finding 070 Depth-2 Result and Depth-3 Freeze

The depth-2 policy produced 15 new lineage cuts among 56 risk-set branches.
The other 41 handed off and supplied the committed depth-3 selector cohort.

```text
cut depth 1: 23
cut depth 2: 15
surviving beyond depth 2: 41
```

There were no transient-child losses, source-survival censoring, collisions,
payload, selector, or ledger errors. Frozen depth-3 selector-manifest SHA-256:

```text
4942e4441901548eb68a7ddd8cf8dc2b8290f103d475b50bf59f155114e8fb94
```

No depth-3 selector had been vetoed when this manifest was frozen.

## Finding 070 Depth-3 Result and Depth-4 Freeze

The depth-3 policy produced 7 new lineage cuts among 41 risk-set branches.
The other 34 handed off and supplied the committed depth-4 selector cohort.

```text
cut depth 1: 23
cut depth 2: 15
cut depth 3:  7
surviving beyond depth 3: 34
```

There were no transient-child losses, source-survival censoring, collisions,
payload, selector, or ledger errors. Frozen depth-4 selector-manifest SHA-256:

```text
1c452b3cf4d3eb9012a38760bb910ce86a9e5d0235966035be98eb525193dcc8
```

No depth-4 selector had been vetoed when this manifest was frozen.

## Finding 070 Depth-4 Result and Depth-5 Freeze

The depth-4 policy produced 9 new lineage cuts among 34 risk-set branches.
The other 25 handed off and supplied the committed depth-5 selector cohort.

```text
cut depth 1: 23
cut depth 2: 15
cut depth 3:  7
cut depth 4:  9
surviving beyond depth 4: 25
```

There were no transient-child losses, source-survival censoring, collisions,
payload, selector, or ledger errors. Frozen depth-5 selector-manifest SHA-256:

```text
d75774c9d22f990b73cc2099a52535e64d06f7d3ccecc0222b48bd02db69b17a
```

No depth-5 selector had been vetoed when this manifest was frozen.

## Finding 070 Depth-5 Result and Depth-6 Freeze

The depth-5 policy produced 4 new lineage cuts among 25 risk-set branches.
The other 21 handed off and supplied the committed depth-6 selector cohort.

```text
cut depth 1: 23
cut depth 2: 15
cut depth 3:  7
cut depth 4:  9
cut depth 5:  4
surviving beyond depth 5: 21
```

There were no transient-child losses, source-survival censoring, collisions,
payload, selector, or ledger errors. Frozen depth-6 selector-manifest SHA-256:

```text
ab28004fa128082da395256a32ddb08800ff62f07d6d80356df46c75a283ad05
```

No depth-6 selector had been vetoed when this manifest was frozen.

## Finding 070 Depth-6 Result and Depth-7 Freeze

The depth-6 policy produced 3 new lineage cuts among 21 risk-set branches.
The other 18 handed off and supplied the committed depth-7 selector cohort.

```text
cut depth 1: 23
cut depth 2: 15
cut depth 3:  7
cut depth 4:  9
cut depth 5:  4
cut depth 6:  3
surviving beyond depth 6: 18
```

There were no transient-child losses, source-survival censoring, collisions,
payload, selector, or ledger errors. Frozen depth-7 selector-manifest SHA-256:

```text
a6a6e956eabb23c4d2c3f39f1a3ab0170bc91aa71b7a11a705e51bcbff00748b
```

No depth-7 selector had been vetoed when this manifest was frozen.

## Finding 070 Depth-7 Result and Depth-8 Freeze

The depth-7 policy partitioned 18 risk-set branches into 5 lineage cuts, 12
confirmed handoffs, and 1 source-survival censor. One cut branch produced a
transient inherited child that disappeared before original-address death; it
remains a cut because no live descendant existed at the endpoint.

```text
cut depth 1: 23
cut depth 2: 15
cut depth 3:  7
cut depth 4:  9
cut depth 5:  4
cut depth 6:  3
cut depth 7:  5
source-survival censored through depth 7: 1
surviving beyond depth 7: 12
```

There were no collisions, payload, selector, or ledger errors. Only the 12
confirmed handoffs enter the final depth-8 risk set. Frozen depth-8
selector-manifest SHA-256:

```text
e12ffc786b232b9d411c01878df8717a1bed45d0a9c37920deafaacfd0f1424d
```

No depth-8 selector had been vetoed when this manifest was frozen.

## Finding 070 Final Depth-8 Result

The final preregistered depth-8 policy was applied to all 12 committed risk-set
branches. It produced 2 additional lineage cuts and 10 confirmed handoffs.

```text
ordered cut depth 1: 23
ordered cut depth 2: 15
ordered cut depth 3:  7
ordered cut depth 4:  9
ordered cut depth 5:  4
ordered cut depth 6:  3
ordered cut depth 7:  5
ordered cut depth 8:  2
handoff after eight vetoes (D_seq > 8): 10
source-survival censored at depth 7:       1
total factual selector cohort:            79
```

The 10 depth-8 handoffs exposed recorded but unvetoed next selectors. Their
artifact SHA-256 is:

```text
755e049ef27c6022fd8ec660f2b2a0dc4b048d27cbb6b84e3a3dca036e3d4d23
```

No depth-9 intervention is permitted. All eight stages matched every committed
selector and full event identity. The depth-1 matched shams were exact; payload
remained zero, conservation remained exact, and there were no collisions. One
depth-7 loss branch contained a transient inherited child, and one depth-7
branch was source-survival censored; both remain separate from the 10 confirmed
depth-right-censored handoffs.

## Finding 070 Synthesis

The independent replication met its preregistered nontrivial-support gate. All
four newly selected initialization geometries produced at least one confirmed
handoff after the first retained-amplitude veto. Across 79 frozen factual
unique-child continuations, the observed prefix-minimal ordered cut depths were
23, 15, 7, 9, 4, 3, 5, and 2 at depths one through eight. Ten branches still
handed off after eight vetoes and one branch was source-survival censored at
depth seven. Thus 68 cuts were directly observed, while the remaining 11 cases
retain their explicit censoring labels.

The complete chain comprised 286 distinct committed selector events and 923
selector-override executions. Thirty-eight branches revisited at least one
previously vetoed target address, demonstrating that selector depth is an
ordered route-policy measurement rather than a count of unique spatial lanes.
Every selector hash and selector-to-case join verified, every risk set nested
exactly, and all depth-one matched shams were exact. Payload remained zero,
conservation remained exact, and no lineage collision occurred.

Finding 070 therefore independently replicates the bounded causal result from
Finding 069: under the frozen first-next-child, retained-amplitude policy,
continuation commonly has more than one sequentially realized lawful route.
It does not establish a substrate-independent topology, equate cut depth with
entropy, or identify the full reachable set. It measures one intervention- and
order-dependent section of counterfactual continuation structure in four new
Iota initialization geometries.

## Finding 071 Preregistration — Local Continuation-Affordance Field

### Question and claim gate

Finding 071 asks whether a bounded, pre-outcome description of local substrate
geometry predicts a multidimensional continuation-affordance profile on
completely held-out initialization seeds. The narrow claim is:

> A bounded local substrate geometry induces a reproducible and transportable
> profile of ancestry-preserving continuation affordance.

This is a locality and transportability test, not yet a constructed-gradient,
force, or reciprocal-interaction experiment. Passing the gate will license
"local affordance field" as an operational simulator term. It will not establish
a physical field, causality of geometry, or substrate-independent behavior.

### Frozen independent screen

- Canonical substrate: unchanged Iota v0.3.6 configuration and
  `takeover_only_vector_phase` law used in Findings 067B and 070.
- Fresh initialization seeds: `105..232`, inclusive.
- Fixed classification samples: `0..7` per seed.
- Checkpoint, classification horizon, and coordinate limit: 2048, 600, and 64.
- Only `init.seed` and `experiment.objective` may differ from the canonical
  configuration; all effective changes are audited in memory.
- Every seed/sample case is completed before source selection.
- Eligibility is the unchanged strict, causally necessary, completely displaced
  bridge transport with exactly one persistent singleton predecessor at
  rebridge.
- At most one source is selected per initialization seed: the lexicographically
  first eligible `(sample, split, rebridge)` event.
- Discovery seeds are `105..168`; confirmation seeds are `169..232`. This split
  is fixed by seed before any Finding 071 branch response exists.
- The experiment proceeds only if each split supplies at least six eligible
  source geometries. Failure of that support gate is an inconclusive screen;
  the ranges will not be expanded after response inspection.

### Frozen pre-outcome geometry representation

Each selected source is reconstructed at rebridge before any fresh branch RNG
is applied. The singleton address is the origin. Source-intrinsic controls are
its amplitude, range, vector-state identity, angular-memory value, and vector
step class. Environmental features are cumulative Chebyshev-shell summaries at
radii 1, 2, and 3, excluding the source itself:

- active, depleted, and latent cell counts;
- active amplitude and range sums;
- active absolute angular-memory sum;
- active same-vector-state count;
- counts by rotation-invariant vector step-length and behavior classes.

Cube shells, vector-state equality, and step-class counts make the environmental
features invariant to translation and coordinate-axis rotations/reflections.
The source-intrinsic control retains exact vector-state identity and is not used
to claim rotational transportability. No feature encodes the whole trajectory
or any post-branch information. A whole-world summary is retained only as a
descriptive ceiling and cannot be selected for the local field claim.

### Frozen response protocol and chronology

Each source receives 48 fresh natural branches over a 256-offset horizon.
Discovery response branches are run and committed first. Natural outcomes then
freeze every collision-free, single-address, exactly-one-child selector before
any retained-amplitude veto outcome is run. Depth-1 veto responses are committed
next. Only then is the discovery model frozen. Confirmation natural branches,
selectors, and vetoes remain unrun until that model commit.

The source-level response vector is:

1. natural handoff fraction at first original-address death;
2. mean first-address-loss delay divided by 256;
3. depth-1 alternate-handoff fraction among frozen unique-child selectors;
4. natural gate-failure fraction;
5. natural source-exhaustion fraction;
6. natural target-preemption fraction.

Source-survival censoring, collisions, transient children, payload, and ledger
status remain separate audit fields. At least 16 observed address losses and at
least 8 unique-child veto selectors are required per source for model
eligibility. Sources failing this measurement-support gate remain reported but
are excluded by the frozen rule rather than post-hoc judgment.

### Frozen learner and confirmation test

All preprocessing is learned from discovery sources only. Constant discovery
columns are removed; predictors and responses are standardized by discovery
means and standard deviations. Multi-response ridge regression is fitted for:

- the discovery-mean null;
- source-intrinsic controls only;
- intrinsic controls plus environmental summaries through radius 1, 2, or 3.

The radius and ridge penalty in `{0.1, 1, 10, 100}` are selected by
leave-one-initialization-seed-out discovery error. Ties choose the smaller
radius, then larger penalty. The frozen model produces one six-dimensional
prediction per eligible confirmation source.

The primary statistic is mean squared standardized error across confirmation
sources and response dimensions. A local-field confirmation requires all of:

1. at least six eligible sources in each split;
2. local-model error below both the intrinsic-only and discovery-mean baselines;
3. local-model absolute error below the intrinsic baseline in at least two of
   the six response dimensions;
4. a one-sided permutation p-value at or below 0.05, obtained by permuting
   complete confirmation response vectors across source predictions and using
   the local-model mean squared error as the statistic. All permutations are
   enumerated when at most nine confirmation sources qualify; otherwise the
   identity plus 100,000 permutations from frozen RNG seed `20260719` are used.

The model, feature schema, discovery source hashes, selector hashes, and
pre-confirmation state are committed before confirmation outcomes. A negative
or inconclusive result is retained as Finding 071; no alternate learner or
radius may replace the frozen primary analysis after confirmation.

## Finding 071 Screen Result — Preregistered Support Gate Failed

The complete frozen screen ran all 1,024 seed/sample trajectories from
initialization seeds 105 through 232 and causally audited all 159 Class B
candidates. Seventeen candidates were strict singleton-eligible transports.
Applying the frozen one-source-per-seed rule selected 12 independent source
geometries:

```text
discovery seeds 105..168:     9 selected sources
confirmation seeds 169..232: 3 selected sources
required per split:           6 selected sources
source-support gate:          failed
```

Selected seeds were 107, 109, 116, 118, 132, 143, 149, 153, 156, 183, 195,
and 203. All 1,024 classification trajectories and all 159 transport audits
remained payload-free and ledger-exact. The frozen source-manifest SHA-256 is:

```text
4b581df79c68eb71edb2d11e4c2aba9add88a1684f805b9eed8895a81f1e25b3
```

Per preregistration, Finding 071 stops here as an inconclusive locality and
transportability test. No natural affordance-response branch, child selector,
depth-1 veto, discovery fit, or confirmation evaluation was run. The imbalance
cannot be repaired by expanding or repartitioning this finding after observing
the source yield. A subsequent experiment may preregister a new source-
acquisition design, but it must retain Finding 071's failed gate and keep all
affordance outcomes sealed.

## Finding 072 Preregistration — Independent Source Acquisition and Locality Confirmation

Finding 072 is a new experiment, not an expansion or repartition of Finding
071. Finding 071 remains an inconclusive 9/3 support-gate stop. All 12 of its
selected sources retain sealed affordance outcomes.

### Fixed acquisition batch

- Fresh initialization seeds: `233..360`, inclusive.
- Fixed classification samples: `0..7` per seed.
- Canonical v0.3.6 configuration, `takeover_only_vector_phase`, checkpoint
  2048, horizon 600, and coordinate limit 64 remain unchanged.
- Only `init.seed` and `experiment.objective` may change.
- Eligibility and selection are unchanged: strict causally necessary,
  completely displaced transport with exactly one persistent singleton
  predecessor; at most the lexicographically first eligible source per seed.
- The complete 1,024-case batch is run before selection.
- All selected seeds `233..360` are assigned to confirmation. Discovery remains
  exactly the nine frozen Finding 071 discovery sources. The three Finding 071
  confirmation sources remain confirmation sources.
- The acquisition gate requires at least three newly selected sources, yielding
  at least six total confirmation geometries. Failure stops Finding 072 before
  every affordance response.

The acquisition range will not be extended after its yield is observed. Source
manifests, transport ledgers, combined cohort membership, and hashes are
committed before feature extraction or response branching.

### Locality-confirmation protocol

If acquisition passes, Finding 072 executes the already committed Finding 071
feature, response, veto, and model protocol without changing its primary
analysis:

- translation-invariant and axis-rotation/reflection-invariant environmental
  summaries through Chebyshev radii 1, 2, and 3;
- source-intrinsic controls and a discovery-mean null;
- 48 natural branches per source, a 256-offset natural horizon, and the frozen
  depth-1 retained-amplitude veto on unique factual child selectors;
- at least 16 observed address losses and 8 veto selectors per modeled source;
- multi-response ridge penalties `{0.1, 1, 10, 100}` selected with radius by
  leave-one-discovery-seed-out error;
- the same six-component affordance response vector;
- the same held-out confirmation requirements: local standardized MSE below
  both intrinsic and null baselines, improvement in at least two response
  dimensions, and one-sided permutation `p <= 0.05`.

Discovery natural outcomes and selectors are committed before discovery
vetoes. The fitted model is committed before any confirmation natural response.
Confirmation factual selectors are committed before confirmation vetoes. No
alternate model may replace the frozen primary analysis after confirmation.

### Conditional Finding 073 gate

Finding 073 may begin only if Finding 072 passes every held-out local-field
confirmation criterion. Its subject will be controlled response to a frozen
affordance gradient, not another post-hoc classifier. A failure or inconclusive
Finding 072 stops the field-to-gradient sequence and is registered as such.

## Finding 072 Final Result — Local-Field Confirmation Failed

The acquisition batch selected 14 new confirmation geometries. The combined
cohort contained 9 discovery and 17 confirmation sources. All 26 pre-outcome
feature rows were frozen before responses. Every source met response support:
discovery supplied 432 natural branches and 346 unique-child veto selectors;
confirmation supplied 816 natural branches and 651 selectors. All shams,
selector identities, payload checks, conservation ledgers, and collision checks
passed.

Discovery selected cumulative radius 3 with ridge penalty 100. On confirmation:

```text
local standardized MSE:       1.2887142111
intrinsic-only MSE:            1.3033842696
discovery-mean null MSE:       1.2720478754
dimensions beating intrinsic: 4 / 6
permutation p:                 0.3536564634
```

The local model narrowly beat the intrinsic control and improved four response
dimensions, but it failed two mandatory gates: it did not beat the null and its
permutation p-value exceeded 0.05. Finding 072 therefore does not confirm that
the preregistered bounded local representation carries transportable predictive
information about the multidimensional affordance profile.

This is a negative confirmation for the declared representation and learner,
not proof that no local field exists. Shell histograms may discard relational
arrangements that matter. Finding 073 is not opened: no field gradient should
be constructed from a predictor that failed held-out confirmation.

## Durable Long-Run Convention

The working theoretical term is now **coherence-conditioned transition
geometry**: the potentially anisotropic and history-dependent structure of
lawful next transitions conditioned on a coherence and its marked relational
history. It is provisional and does not imply an established physical field,
tensor, force, or gravity analogue.

All future commands expected to run longer than an interactive tool window
should use `scripts/run_with_heartbeat.py`. The wrapper writes an atomically
updated `.run_state/latest-<name>.json` every 30 seconds by default and preserves
the full timestamped stdout/stderr log locally. Commentary remains useful, but
the local state file is the source of truth if an API 400, browser disconnect,
or conversation compaction interrupts observation. Important preregistration,
freeze, and terminal-result barriers still require committed repository
artifacts; heartbeat files are operational recovery records and remain
untracked.

## Research-Program Guardrail — Successor Structure Before Physics Analogues

The immediate primitive target is the latent counterfactual structure of lawful
successor events: which relations are available, which ordered transitions can
realize them, which routes close, and which successor structure can be inherited.
The lattice stores state; the marked relational transition graph represents
possibility; coherence provisionally organizes persistence across succession.

Every proposed test must identify the successor-graph quantity it changes and
measures. A test aimed primarily at mass, energy, force, attraction, radial
decay, particle motion, or a classical field is downstream unless its underlying
counterfactual mechanism has already been demonstrated. Mass- and energy-like
behavior remain possible coarse-grained outputs to explain, not substrate
variables to imitate. The current mechanistic target is causal transformation
of the successor graph by a coherence, under the disciplined working term
`coherence-conditioned transition geometry`.

## Finding 074 Preregistration — Pre-Articulation Transition Geometry

Finding 074 tests whether Finding 049's exact-placement causal channel recurs
across independent strict transport geometries. It is mechanism-first and does
not reopen the failed GC-013 representation search.

### Factual channel screen

The frozen factual input is every strict constraint-transport event in the
combined Finding 071/072 screen (`105..360`, eight classification samples per
seed). No counterfactual outcome has been run for these channels. Each natural
event is replayed from its canonical v0.3.6 checkpoint under the recorded
`takeover_only_vector_phase` law.

A pre-articulation channel is eligible only when all of the following are true:

1. the strict event has exactly one original bridge address;
2. that address is active immediately before the recorded split and inactive
   immediately afterward;
3. removing it alone from the pre-split world increases cube26 component count;
4. its natural deactivation increases actual cube26 component count;
5. within the preceding 64 offsets, a successful transfer into a depleted
   target most recently activated that exact future articulation address;
6. the future articulation source makes at least one successful outgoing
   transfer on its death transition;
7. the recorded successor bridge naturally restores the predecessor relation;
8. payload remains zero and the conservation ledger remains exact.

Selection is at most one channel per initialization seed: lexicographically
first by `(sample, split, rebridge, precursor offset, source, target)`. The full
factual audit is completed before selection. At least six independent seeds are
required; otherwise Finding 074 stops before intervention. The selected channel
manifest, complete event identities, natural endpoints, and hashes are
committed before any paired replay.

### Frozen paired interventions

For every selected channel, replay the same checkpoint, continuation RNG, and
fixed endpoint through 256 offsets after natural split:

- `natural`: unchanged trajectory;
- `sham`: observe and exactly match the frozen precursor without changing it;
- `erase_precursor_gate`: consume the natural gate draw but force the frozen
  successful precursor transfer to fail, retaining its amplitude at the source;
- `erase_inherited_memory`: preserve the natural activation and amplitude at the
  exact articulation address but restore its pre-transfer `R`, `V`, `P`, and
  angular-memory state;
- `transplant_poststate`: after the natural precursor step, restore the factual
  target to its pre-transfer state and move the exact post-transfer state to a
  preregistered nearby depleted address.

The transplant address is selected before intervention outcomes from Chebyshev
radius two around the factual target. Candidates must be depleted before the
precursor, distinct from precursor source/target and recorded bridge cells. Rank
by absolute difference from the factual target's pre-step face6 count,
cube26 count, and cube26 neighbor-component count, then distance, then
lexicographic coordinate. The chosen address and all pre-state matching fields
are part of the frozen manifest.

A separate `veto_first_rebridge` replay consumes and suppresses the first frozen
successful activation belonging to the natural successor bridge, when that
activation has a unique candidate-ledger identity. It tests closure lifetime,
not precursor necessity.

### Outcomes and gates

Primary outcomes are split occurrence at the natural split offset, first split
offset if shifted, split lifetime, maximum component-count delta, largest-
component delta, successor-bridge realization, alternate closure, and
component/interface divergence at 128 and 256 offsets. Every sham, candidate
identity, payload check, ledger check, and intervention count must be exact.

The coherence-conditioned transition-geometry pattern is supported only if:

1. at least six independent eligible channels enter intervention;
2. natural and sham reproduce every factual split and rebridge exactly;
3. in at least two thirds of channels, precursor erasure suppresses the natural
   split and transplantation suppresses it while memory erasure preserves it;
4. the paired pattern occurs in at least four initialization seeds;
5. no lineage ambiguity, payload, ledger, or multi-intervention failure occurs.

The durability extension is a separate secondary positive: among uniquely
vetoable rebridges, at least two thirds must extend separation beyond its natural
lifetime, and at least one independent seed must remain separated for 128
offsets. Failure of this secondary gate does not negate a precursor-placement
result and cannot be relabeled durable morphogenesis.

All long stages must run through `scripts/run_with_heartbeat.py`; local heartbeat
state is operational recovery evidence, while scientific barriers are committed
repository artifacts.

## Finding 074 Final Result — Placement Gate Passed; Durability Gate Failed

The factual screen completed all 37 strict Finding 071/072 transports. It found
35 eligible channels and selected one channel in each of 25 independent
initialization seeds, exceeding the frozen six-seed acquisition gate. Every
factual row was payload-free and ledger-exact. The full manifest and its
`1ffcac698b397dc956e0ff0b22398fb8c7a3241f7d65e39cfa46feb77733af5c`
hash were committed at `5ef57cc` before intervention code or outcomes.

An initial full-run attempt exposed an instrumentation error: an earlier death
of the future articulation address, before its frozen precursor reactivated it,
was incorrectly treated as the experimental split. The run was stopped after
two invalid channel diagnostics, produced no scientific artifact, and was not
interpreted. The detector was bounded to offsets at or after the frozen
precursor and committed at `f0e49cc`. A one-channel instrumentation replay then
passed every selector, intervention, payload, ledger, natural, and sham check
before the complete cohort was reopened.

The completed 150-row paired replay produced:

```text
erase precursor gate suppresses recorded split: 25 / 25
transplant exact post-state suppresses split:    25 / 25
erase inherited memory preserves split:         18 / 25
complete frozen composite pattern:               18 / 25
required composite threshold:                    17 / 25
represented composite-pattern seeds:             18
```

Natural and sham trajectories reproduced all factual splits and rebridges.
Every targeted selector matched exactly once, every intervention count was
exact, all payload checks remained zero, and every conservation ledger was
exact. The primary coherence-conditioned transition-geometry gate therefore
passes. Exact relational placement is causal for the recorded articulation in
this conditional cohort; seven channels additionally require some member of
the bundled inherited `R/V/P/angular_L` state and prevent a placement-only law.

The first-rebridge veto extended split lifetime in `23/25` channels (median
paired extension `+5` offsets; no negative extensions), but zero channels
remained separated for 128 offsets. The separate durability extension fails and
Finding 074 does not support durable morphogenesis.

Raw outcomes were frozen at commit `b2ef3a6`; the replay-results hash is
`7405d1db8f2e6a425d594f9daa82c7280da8d60a4795ed8f270dacc6f9c7a788`.
The bounded result is registered as GC-014. The next experiment must manipulate
successor-graph structure directly—bridge topology, signed angular contrast,
and recruitment order under matched counts and budgets—rather than search for
a mass, energy, force, particle, or classical-field analogue.

## Finding 075 Protocol-Development Audit — Role Versus Address

The already observed Finding 074 cohort may be used only to qualify a factual
matching rule; it cannot provide Finding 075 confirmatory evidence. For each
frozen precursor pre-state, enumerate depleted candidate addresses within
Chebyshev radius six of the factual target. Hold radial occupancy fixed by exact
active counts in cube26 shell one and Chebyshev shell two.

The provisional rooted graph-role signature consists of face6 and face18 active
counts, face6 and cube26 neighbor-component counts, and the sorted induced
cube26-degree sequence among the target's active cube26 neighbors. A
role-preserving candidate must match both the radial and complete role
signatures at a different address. A role-breaking control must match the
radial signature exactly while differing in the role signature. Candidates are
ranked by distance from the factual target and then lexicographic coordinate.

This audit reports support yield only. It does not replay a split, inspect a
counterfactual response, fit a classifier, or permit a causal claim. If support
is adequate, Finding 075 must use newly initialized channels, freeze its cohort
and selectors before intervention, and distinguish graph-role preservation from
literal coordinate preservation under exact payload and conservation controls.

### Development result and revised intervention

The radius-six audit found zero role-preserving address matches, one
role-breaking radial match, and zero paired matches across all 25 Finding 074
channels. Payload remained zero and conservation was exact. A natural
matched-address design is therefore infeasible under the declared controls and
must not be rescued by loosening them.

The revised factual-only feasibility audit holds the factual target address and
exact post-transfer state fixed. Immediately after the natural precursor step,
it considers swapping the complete state of one active cube26 neighbor with one
depleted cube26 position. Both positions remain in radial shell one, so active
count, amplitude budget, payload, shell-one occupancy, and shell-two occupancy
are conserved exactly. A role-preserving swap must leave the complete rooted
role signature unchanged; a role-breaking swap must change it. Donor selection
requires the preserving and breaking variants to move the same donor state,
prioritizes donors outside the frozen precursor source and recorded bridge
cells, and then ranks lexicographically. No downstream split or counterfactual
response is observed during feasibility selection.

## Finding 075 Preregistration — Graph Role Conditions Reachable Articulation Futures

Finding 075 uses initialization seeds `361..552`, eight classification samples
per seed, and the unchanged v0.3.6 law. These worlds are new to every Finding
074/075 outcome. The complete strict-transport screen runs first, followed by
the unchanged pre-articulation factual screen and the frozen common-donor
rewire selector. Selection is at most one paired channel per initialization
seed, lexicographically first under the existing channel ordering. At least 12
independent paired channels are required; otherwise Finding 075 stops without
intervention.

For each selected channel, the natural precursor step must reproduce its exact
frozen selector and target post-state. The complete state of one unprotected
active cube26 donor is then swapped with one depleted cube26 receiver:

- `natural`: no state swap;
- `sham`: observes all selectors but does not change state;
- `role_preserving`: the frozen donor/receiver swap leaves the target's radial
  and rooted graph-role signatures unchanged;
- `role_breaking`: the same donor state moves to a different frozen depleted
  receiver, preserving radial occupancy but changing rooted graph role.

The target address and complete transferred target state remain identical.
Both swaps preserve global active count, amplitude, payload, shell-one and
shell-two occupancy, and the state multiset exactly. The donor must be the same
in the preserving and breaking variants and cannot be the precursor source or
any recorded predecessor/successor bridge cell.

Immediately after the precursor state is established, each of `natural`,
`role_preserving`, and `role_breaking` is cloned into 16 common continuation RNG
branches. Branch seeds are deterministic from the frozen channel index and
branch index and are committed before outcomes. Each branch runs for 128
offsets. Its primary endpoint is whether the frozen articulation address
undergoes an active-to-inactive transition that increases cube26 component
count. First articulation offset, separation lifetime, successor realization,
component count, largest component, interface metrics, payload, and ledger are
also recorded. The original factual continuation is replayed separately with a
matched sham and must reproduce the recorded split and rebridge exactly.

The graph-role hypothesis is supported only if:

1. at least 12 independent paired channels enter intervention;
2. every factual natural/sham, selector, swap, target-state, state-multiset,
   payload, and ledger check is exact;
3. across paired branch outcomes, discordances favor articulation after the
   role-preserving swap over the role-breaking swap under a frozen one-sided
   exact McNemar/binomial test at `p < 0.05`;
4. at least eight channels are branch-informative, and at least two thirds of
   informative channels have a higher articulation rate under role preservation
   than role breaking; and
5. in at least two thirds of all selected channels, the role-preserving
   articulation rate is strictly closer to the natural rate than the
   role-breaking rate.

Failure of any gate stops the sequence before Finding 076. A positive result is
limited to graph-role-conditioned articulation susceptibility under this law,
scheduler, signature, swap policy, and 128-offset branch horizon. It is not a
field, force, mass, energy, or matter claim.

## Finding 075 Final Result — Frozen Rooted Role Signature Failed

The complete new-world acquisition covered all 1,536 scheduled cases from
seeds `361..552`. It produced 46 strict singleton transports in 29 independent
initialization seeds. The pre-articulation audit retained 45/46 events, and the
common-donor selector found 37 paired events and froze one channel in each of
25 independent seeds. The 400 channel/branch assignments were committed before
outcomes; each assignment used one common RNG seed for natural,
role-preserving, and role-breaking variants.

All 50 factual natural/sham controls reproduced their frozen split and rebridge.
Every precursor selector, target post-state, common donor, receiver, radial
signature, rooted role signature, state multiset, payload check, and
conservation ledger was exact. Across 1,200 branch outcomes:

```text
natural articulations:          20 / 400
role-preserving articulations:  24 / 400
role-breaking articulations:    14 / 400

preserve-over-break discordances: 21
break-over-preserve discordances: 11
one-sided exact McNemar p:          0.0550921  (required < 0.05)

informative channels:                    11
informative channels preserve > break:    8  (required 8; passed)
preserving strictly closer to natural:     5 / 25
required closer-to-natural channels:      17 / 25
```

The directional channel gate passed exactly, but the exact paired test missed
its threshold and the natural-closeness gate failed decisively. The composite
graph-role hypothesis is therefore rejected as preregistered. The declared
rooted signature contains a suggestive directional contrast but is not a
sufficient representation of behaviorally equivalent relational role.

This is a representation-specific negative, not evidence that topology is
irrelevant. Ten channels were all-zero within the 128-offset horizon, and
signature-preserving swaps often changed susceptibility away from the natural
state, showing that the frozen summary discards causally relevant marked or
larger-context structure.

Finding 076 was permitted only after a positive Finding 075 result. It therefore
does not open; Finding 077 likewise remains unopened. No memory-coordinate or
recruitment-order outcome was run. Finding 075 is registered as GC-015. A future
experiment requires a new preregistration and should construct a richer marked
successor-event representation from outcome-sealed factual ledgers before
another causal confirmation cohort.

## ICP Approval and Finding 078 Preregistration — Factorial Successor Accessibility

The Finding 075 stop is permanent: the previously conditional Findings 076 and
077 remain unopened and will not be repurposed. Under the ICP approval, later
work may proceed only when the frozen result leaves the next preregistered route
open. A failed gate stops its dependent sequence without threshold movement,
endpoint substitution, or post-outcome representation tuning.

Finding 078 is a developmental feasibility audit, not a confirmation result. It
uses the 25 completed Finding 075 common-donor channels only to determine whether
topological placement and inherited state marks can be manipulated separately
and whether an engine-native continuous successor-accessibility instrument is
identifiable. Finding 075 susceptibility outcomes are not inputs to the
intervention, instrument, channel selection, or Finding 078 gates.

For each frozen post-precursor world, the common active donor is paired in turn
with the already frozen role-preserving and role-breaking receivers. Each pair
creates a complete two-factor intervention:

- `natural`: no exchange;
- `topology_only`: exchange the structural bundle `active`, `A`, and `latent_A`
  between donor and receiver while leaving address-bound `R`, `V`, `P`, and
  `angular_L` marks fixed;
- `marks_only`: exchange `R`, `V`, `P`, and `angular_L` while leaving the
  structural bundle fixed;
- `joint`: exchange both bundles; this must equal the previously frozen full
  donor/receiver state swap exactly.

The representation is computed from the intervention state before any branch
step, gate draw, realized transfer, or articulation outcome. It enumerates every
tick-start-eligible hard-transfer candidate whose source or target lies within
Chebyshev radius two of the frozen future-articulation address. Directed edges
retain source scheduler rank, relative source and target coordinates, candidate
order and direction, source amplitude and inherited marks, target
active/depleted/latent status and inherited marks, influence, residual-bias
multiplier, transfer probability, and the target's frozen residual geometry
class. Candidate generation uses the declared simulator law with bond
probability 1.0; no stochastic gate is sampled.

Two continuous instruments are frozen:

1. `successor_openness`: the sum of transfer probabilities over eligible
   inactive-target activation edges in the radius-two basin, accompanied by the
   count of distinct activation targets;
2. `repair_affordance`: the sum of transfer probabilities over depleted-target
   secondary edges classified by the existing engine as
   `component_bridge_cube26` or `local_bridge_face6`, accompanied by distinct
   repair-target and source counts.

For each receiver and instrument, the factorial interaction is

```text
joint - topology_only - marks_only + natural
```

Finding 078 passes feasibility only if all of the following hold:

1. all 175 states (25 channels times natural plus two receivers times three
   interventions) are payload-free and ledger-exact, preserve global active
   count and conserved amplitude, preserve the appropriate structural and mark
   multisets, and reproduce the frozen joint swaps exactly;
2. all candidate enumeration is RNG-neutral and repeat-exact;
3. at least 20/25 channels have at least one receiver for which
   `topology_only` changes the marked edge set while `marks_only` leaves the
   active mask exact, and `marks_only` changes the marked edge set while
   `topology_only` leaves the global inherited-mark multiset exact;
4. at least 12/25 channels have a nonzero factorial interaction in either
   successor-openness probability mass or repair-affordance probability mass
   for at least one receiver.

These are identifiability and support gates, not evidence that either instrument
predicts articulation. If they pass, one receiver per channel is selected
without outcomes by maximum absolute repair-affordance interaction, then maximum
absolute successor-openness interaction, then the frozen preserving receiver on
an exact tie. The complete representation, instrument definitions, selector,
and Finding 078 artifacts must be committed before any Finding 079 acquisition
or susceptibility outcome. If any gate fails, Finding 079 does not open.

Finding 079, if permitted, requires newly initialized channels and a separate
prospective preregistration. Its primary test will be a topology-by-state
interaction under common RNG. Split latency, rebridge timing, separation
duration, articulation location, and component imbalance may be frozen secondary
endpoints but cannot replace a failed primary result. Recruitment history is a
later hypothesis and is not inferred from Finding 078.

## Finding 078 Frozen Feasibility Result — Factorial Instrument Identifiable

Finding 078 completed all 175 preregistered pre-outcome states. All states were
payload-free and ledger-exact, preserved active count and conserved amplitude,
preserved the declared structural and mark multisets, reproduced the joint full
swap, left the source RNG untouched, and repeated exactly.

```text
channels:                         25
factorial states:                175 / 175
identifiable channels:            25 / 25  (required 20)
nonzero interaction channels:     23 / 25  (required 12)
selected preserving receivers:    14
selected breaking receivers:      11
```

The outcome-free receiver selector was heterogeneous and therefore did not
reduce to the failed Finding 075 binary role label. Among selected receivers,
repair-affordance interaction was nonzero in 22/25 channels and
successor-openness interaction was nonzero in 12/25. These values establish
instrument feasibility only. They do not show that either continuous measure
predicts articulation or that the topology-by-state interaction is causal for a
later branch endpoint.

The frozen artifacts are:

- `output/findings/finding078/factorial_successor_accessibility_summary.json`
- `output/findings/finding078/factorial_successor_accessibility_channels.csv`
- `output/findings/finding078/factorial_successor_accessibility_states.csv`

Finding 078 passed all preregistered gates and permits a separately
preregistered Finding 079 independent confirmation. No Finding 079 acquisition,
branch assignment, or outcome existed when these artifacts and their selector
were frozen.

## Finding 079 Preregistration — State-Conditioned Repair Affordance

Finding 079 prospectively tests whether the frozen topology-by-state interaction
in repair affordance conditions later articulation susceptibility. It uses new
initialization seeds `553..744`, eight continuation samples per seed, the
canonical v0.3.6 law, checkpoint tick 2048, a 600-offset factual acquisition
horizon, the existing 64-offset precursor lookback, and the existing strict
singleton-transport and pre-articulation definitions. No seed in this range was
used by Finding 075 or Finding 078.

Acquisition proceeds without counterfactual branch outcomes:

1. acquire all 1,536 scheduled factual continuations;
2. screen strict transports for an eligible precursor and natural rebridge;
3. enumerate the existing common-donor preserving and breaking receiver pair
   without susceptibility outcomes;
4. construct the exact Finding 078 natural, topology-only, marks-only, and joint
   states for both receivers;
5. select one receiver per channel by maximum absolute repair-affordance
   interaction, then maximum absolute successor-openness interaction, then the
   preserving receiver on an exact tie;
6. retain only channels with nonzero selected repair-affordance interaction,
   exact factorial integrity, and one lexicographically first channel per
   initialization seed.

At least 20 independent retained channels are required. Otherwise Finding 079
stops without branch assignment or outcomes. The channel manifest and its hash
must be committed first.

For each retained channel, freeze 32 branch seeds from base `2,026,079,000`.
Each common RNG branch runs four variants for 128 offsets:

- `natural`;
- `topology_only`;
- `marks_only`;
- `joint`.

The topology and mark bundles, continuous instruments, radius-two basin, and
candidate representation are exactly those committed for Finding 078. Natural
and sham factual controls must reproduce the frozen precursor, split, rebridge,
and trajectory hash. All selectors, state bundles, active counts, conserved
amplitude, payload checks, ledgers, RNG assignments, and intervention multisets
must remain exact.

The primary endpoint is binary articulation within 128 offsets. For each channel
and branch define the factorial articulation contrast

```text
D = joint - topology_only - marks_only + natural
```

Repair affordance is specifically bridge/reclosure accessibility, so the frozen
directional prediction is inverse: a positive repair-affordance interaction
predicts a negative articulation interaction and vice versa. For channel `c`,
the signed primary effect is

```text
E_c = -sign(repair_interaction_c) * mean_branch(D)
```

The primary gate passes only if both conditions hold:

1. at least two thirds of informative channels have `E_c > 0`; zero effects are
   not informative but at least 12 informative channels are required;
2. an exact one-sided channel-level sign-flip permutation test of the mean
   signed effect gives `p < 0.05`. Channels, not branches, are the exchangeable
   units; all `2^n` sign assignments are enumerated when feasible.

The preregistered mechanistic claim, if supported, is limited to: under the
frozen law, factorial intervention, instrument, receiver selector, branch panel,
and horizon, the direction of state-conditioned repair-affordance change
predicts the direction of later articulation-susceptibility interaction across
independent initialization geometries.

Secondary endpoints are split latency, separation lifetime, first closure
timing, successor activation, final component count, largest-component size,
interface union, and active/depleted adjacency. They are descriptive and cannot
rescue a failed primary gate. Failure stops the dependent route before any
recruitment-history experiment. Passing permits a separately preregistered
history-matched intervention; it does not establish a universal law, physical
field, force, mass, energy, matter, or entropy correspondence.

## Finding 079A Frozen Acquisition — Independent Source Support

The complete new-seed factual acquisition finished before any factorial branch
outcome. All 1,536 scheduled continuations from seeds `553..744` were retained.

```text
factual cases:                    1,536
Class-B candidates:                 249
strict singleton transports:         30
independent strict seeds:             22
required downstream channels:         20
payload/ledger failures:                0
```

The 22 selected initialization seeds are `554, 555, 566, 574, 579, 583, 585,
586, 588, 595, 613, 619, 621, 665, 673, 674, 688, 699, 705, 720, 730, 732`.
This is factual source support only. The precursor, common-donor, nonzero
repair-interaction, and independent-channel gates remain unevaluated, and no
Finding 079 branch assignment or susceptibility outcome exists.

## Finding 079B Frozen Precursor Screen — Support at the Boundary

The outcome-sealed precursor screen evaluated all 30 strict factual events from
22 independent seeds. Twenty-five events were eligible, and the frozen
one-per-initialization selector retained exactly 20 independent precursor
channels.

```text
strict events:                      30
strict independent seeds:           22
eligible precursor events:          25
independent precursor channels:     20
required final factorial channels:  20
payload/ledger failures:              0
```

Five strict events failed precursor eligibility; two of those also failed the
reconstructed singleton-bridge conditions. The cohort now has no remaining
support cushion. Every one of the 20 independent precursor seeds must retain a
common-donor pair and a nonzero selected repair-affordance interaction for
Finding 079 branches to open. No common-donor result, repair-interaction result,
branch assignment, or susceptibility outcome existed when this screen was
frozen.
