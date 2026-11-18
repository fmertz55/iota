# MIR-REVERSIBLE-BREAK-001: order memory as integrability breaks (v0.1)
Status: **frozen at tag `mir-reversible-break-001-v0.1-frozen`**. 2026-11-18. Code `break1.py` (ORDER-002 machinery unchanged).
Parent: exploratory quick probe (output/minimal_realization/EXPLORE-RCA54-NEIGHBOURS, 6b5256f; exposed, 1-bit neighbours,
50 cases/side, different seed). This run uses fresh samples (seed 20261118), 150 cases/side, and adds 2-bit neighbours.

## Question
Integrable RCA54 (rule 250) is order-blind. Does order memory, and its background share, rise as the dynamics move away
from integrability, measured independently by two-body elasticity e (fraction of single collisions returning exactly the
two incoming species with no background)?

## Rules
250 and all 36 rules at table distance 1 and 2. Rules without L and R movers are untestable (reported).

## Validity
V_slot (all checked slot-equivalence cases exact); V_C (250: order = 0 and background = 0); >= 10 testable non-control rules.

## Hypotheses (testable non-control rules)
- **H_L (the spine):** Spearman rho(elasticity, order bits) <= -0.5 with p < 0.01.
- **H_O:** every testable rule with elasticity < 1 has order > 0.
- **H_B:** background bits > 0 in >= 2/3 of testable rules.
Descriptive: order, background, background-only, elasticity and distance per rule.

## Prior art
Integrability breaking in Rule 54 is studied through charges, thermalization and transport (Lopez-Piqueres et al. 2022;
deformed RCA54 2026). A 3-query screen found no work on record or order memory. A full search is owed.

## Limits
Coarse ORDER readout; species-level movers; elasticity is a crude integrability proxy; one substrate family.
