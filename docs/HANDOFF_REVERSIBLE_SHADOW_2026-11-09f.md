# Handoff: WALL-002 done (valid; H_C0, H_S not supported; edges hold "which", not "when") (2026-11-09f)

Supersedes HANDOFF_REVERSIBLE_SHADOW_2026-11-09e.md. Working rules unchanged (contract, seal, frozen tag, run, result
commit; information-first vocabulary; check pictures; token thrift; check git log before writing a result file; 4
workers; commit from bash). Strategic rule: no tests for their own sake.

## Done this session
- WALL-002 (11-09e direction 2, channel form). Code wall2.py (imports wall1; runs() = verbatim wall1.job copy + offset);
  contract/seal 38bbd89, tag mir-reversible-wall-002-v0.1-frozen; result output/minimal_realization/MIR-REVERSIBLE-WALL-002/RESULT.md.
- Translate lemma (contract): inside a contact class (sp, phi) translate k is contact k*tau later, v_R*k*tau right; every
  wall obeys sub same, clock + k*tau mod P, place + k*tau*(v_R - u). Checked exactly (V_L 1728/1728).
- Valid. Record = contact coordinate 71-77% + species pair 23-29%. Static-wall placement names the contact (locked
  place+time), species only 0.01-0.17 bit. Edge-only part is never age (J_k = 0, all 7): species pair (26s 82s all
  0.584; 58s 114s 1.171) + contact phase 0.242 (58s 114s).
- Correction to 11-09e: "static wall = place, edges = age" is wrong for this ensemble. Static wall = when-and-where (one
  coordinate); edges = which species. The independent place/age split is a lemma, not data: with place varied
  separately, a static wall holds age only mod P (<= log2 P), an edge's distance from the wall holds it fully.

## Open directions
1. Budget line write-up (BUDGET-001 + wall budgets) with the corrected split: static wall = contact coordinate, edges =
   collision identity; place/age separation stated as the lemma.
2. 143-family light-cone shadows (deferred).
