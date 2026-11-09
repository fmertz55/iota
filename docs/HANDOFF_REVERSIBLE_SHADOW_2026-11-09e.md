# Handoff: WALL-001 done (valid; H_1, H_T, H_I not supported) (2026-11-09e)

Supersedes HANDOFF_REVERSIBLE_SHADOW_2026-11-09d.md. Working rules unchanged (contract, seal, frozen tag, run, result
commit; information-first vocabulary; check pictures; token thrift; check git log before writing a result file; 4
workers; commit from bash). Strategic rule: no tests for their own sake.

## Done this session
- WALL-001 (11-09d direction 1). Code wall1.py (imports inventory1); contract/seal 619a8bd, tag
  mir-reversible-wall-001-v0.1-frozen; result output/minimal_realization/MIR-REVERSIBLE-WALL-001/RESULT.md (+ figure).
- Correction to 11-09d: only 7/24 unexposed pairs have one static wall in every shadow run (147 201 22s 26s 58s 82s
  114s); 33 123 139 209 94s 218s have one domain and two edges, no static wall.
- Method note: re-decomposing every tick with inventory1.domains() fails at some tick parities (22s); walls are tracked
  locally by flank-periodicity breaks. 22s static wall is a phase slip (negative width allowed).
- Valid. H_1 3/7 (147 201 22s), H_T 3/7 (147 58s 114s; <= 0.48 bit), H_I 0/7. Static wall = placement (59-88% of rec)
  + sub-species; clock periods 2-12, short. In 26s 82s 58s 114s 0.58-1.41 bit lives only in the moving outer walls; outer
  walls alone hold everything in 6/7. Reading: a stationary wall remembers where; when needs a moving edge.

## Open directions
1. Budget line write-up (BUDGET-001 + wall budgets), now with the place/time split: static wall = place, edges = age.
2. Vary contact time independently of place (e.g. carrier launch phase as in SHADOW-009) to separate where/when
   properly; only worth it if the write-up needs it.
3. 143-family light-cone shadows (deferred).
