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
18a8351 Findings 039/040: lineage-conditioned morphology and secondary-bias test
bd6f71d Finding 038: vector-coupled angular momentum
fa7872d Finding 037: four-phase lineage persistence
7664344 Finding 035: rotation-aware openness
da5e245 Finding 034: history-coupled received rotation
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

## Core Interpretation

Current paper-safe claim:

```text
Retained angular momentum coupled to the information-exchange vector creates bounded,
ledger-exact, non-merging directional lineages. However, those lineages do not yet
produce meaningful active/depleted morphology divergence.
```

Current negative result:

```text
Adding capacity-neutral secondary candidate ordering bias at strength 0.10 maximizes
directional family separation but reduces interface turnover and spatial divergence.
```

The system now has:

```text
rotation with memory
directional lineage persistence
bounded ledger-exact dynamics
```

It does not yet have:

```text
morphogenetic consequence
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
```

## Key Configs

These may require restoring `output` into the sparse checkout:

```text
output/findings/configs/v031_vector_angular_momentum_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2.yaml
output/findings/configs/v031_signed_exchange_control_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0_amr0_cap2.yaml
output/findings/configs/v032_vector_angular_momentum_secondary_bias_seed56_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_amc0p5_amr0p5_cap2_amsb0p10.yaml
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

## Next Hypothesis

Do not increase global secondary bias.

The next principled test should make angular momentum affect real interface recruitment only when local structural opportunity exists.

Candidate v0.3.3 rule:

```text
event-gated L bias

Apply angular-momentum secondary ordering bias only when the candidate target is:
  - depleted and adjacent to active interface, or
  - newly recruitable boundary site, or
  - part of an active/depleted interface turnover event.

Keep valence, amplitude, range, payload, and conservation unchanged.
```

Why:

```text
v0.3.1 has directional memory without structural consequence.
v0.3.2 proves global secondary bias over-partitions direction and suppresses motion.
Event-gating asks whether L can bias morphology only at the actual interface frontier.
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
Read SESSION_HANDOFF.md and experiments/FINDINGS.md Findings 038-040.
Continue from the v0.3.2 negative result: global angular-momentum secondary
candidate bias over-partitions directional histories but suppresses morphogenesis.
Next goal: implement and test event-gated angular-momentum coupling to interface
recruitment, preserving bounded ledger-exact dynamics.
```
