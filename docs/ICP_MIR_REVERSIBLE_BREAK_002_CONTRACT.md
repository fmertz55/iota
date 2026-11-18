# MIR-REVERSIBLE-BREAK-002 (v0.1)
Status: **frozen at tag `mir-reversible-break-002-v0.1-frozen`**. 2026-11-18. Code `break2.py` (= break1.py + elastic2.py).
Parent BREAK-001 (valid; H_L failed because its elasticity proxy scored RCA54 at 0.16; post hoc split seen. Exposed).
Changes: elasticity v2 (no background, and per-direction mover cell mass equals the free incoming mass); rules at table
distance <= 3 from 250; fresh seed 20261119; 100 cases per side.
Pre-freeze checks (disclosed): v2 on 30 single collisions gives 250: 30/30, 242: 5/30.
## Validity
V_slot; V_C: 250 order 0, background 0, elasticity >= 0.95; >= 10 testable non-control rules.
## Hypotheses (testable non-control rules)
- **H_L:** Spearman rho(elasticity, order bits) <= -0.5, p < 0.01.
- **H_S:** rho(elasticity, background bits) <= -0.5, p < 0.01.
- **H_X (split, from BREAK-001 post hoc):** among rules with elasticity >= 0.25 (background <= 0.05 expected) or <= 0.12
  (background >= 0.25 expected), >= 80% match, with >= 5 such rules.
H_O and H_B as in BREAK-001 (reported). Limits as in BREAK-001; one substrate family.
