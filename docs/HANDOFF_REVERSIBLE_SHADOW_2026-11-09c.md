# Handoff: PHASE-001 done (invalid); next is the wall/domain species inventory (2026-11-09c)

Supersedes HANDOFF_REVERSIBLE_SHADOW_2026-11-09b.md. Working rules unchanged (contract, seal, frozen tag, run, result
commit; information-first vocabulary; check pictures; token thrift; check git log before writing a result file).
Machine: use 4 workers. Strategic rule: no tests for their own sake. Commit from bash, not the python kernel.

## Done this session
- PHASE-001 (handoff 11-09b direction 2). Contract/code/seal 7434356, tag mir-reversible-phase-001-v0.1-frozen; result
  and erratum 263d448. Code: phase1.py. Contact phase class phi = off mod Delta, Delta = (v_R - v_L) lcm(p_R, p_L, p_v)
  (exact translation reduction; Delta = 2 or 4 except 37). Age-aligned erasure (fixed-T erasure is age-dependent: 37
  failed V1 with it).
- Verdict INVALID: V2 assumed the nulls have no residue; null 5 has 64 residue runs (already in SHADOW-009). Not re-run.
- Descriptive (post hoc): the contact phase gates record formation in 24/24 unexposed pairs. In 10 pairs it is only a
  gate. In the other 14 pairs distinct phase classes always give distinct residues (H_place = 0). This is weak, because the
  full-residue key counts any internal difference as a new shape.
- Lesson: before freezing a null control, check the stored values of the nulls. Rigid movers (both edges at one speed)
  are unrecognised carriers: null 5, and 37 (13 runs), 201, 139 and 209 (32 runs each).

## Next (new thread): wall/domain species inventory (11-09b direction 1)
- Question: does contact phase (and species pair) select different domain/wall *species*, or the same species with
  different internal detail? Is the shadow a bound state of a small wall/domain alphabet?
- Coarse descriptor per residue: ordered list of domains (interior spatial period and pattern up to shift, vacuum phase)
  and walls (speed, w2 budget, flank pair). BUDGET-001 `segments()` is a starting point; phase1.py has age alignment.
- Must first separate rigid movers (unrecognised carriers) from domains. Calibrate on null 5.
- Null control: decide from stored values (null 5 has residue; 1 and 90s none).

## Deferred
- Carrier-phase-as-record-bit, beyond gating: will be answered by the inventory. Write-up of the budget line.
  SHADOW-008 chirality (shelved). Q3 2D rules (later).
