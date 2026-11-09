# Handoff: information-budget line, BUDGET-001 done (2026-11-09b)

Supersedes HANDOFF_REVERSIBLE_SHADOW_2026-11-09.md. Working rules unchanged (contract, seal, frozen tag, run, result
commit; information-first vocabulary; check pictures; token thrift; check git log before writing a result file).
Machine: use 4 workers. Strategic rule: no tests for their own sake.

## Done this session
- BUDGET-000 window-3 extension (4a4d1db; budget0_w3.py, BUDGET-000/window3.json): 8/14 rules gain 1-2 new window-3
  invariants (22 91 218: +1; 33 37 54 147 201: +2); exact, vacuum-zeroed, simulation-conserved.
- BUDGET-001 (contract f9624d0, tag mir-reversible-budget-001-v0.1-frozen; erratum bb7a23c; result fb5c0ae; 91 addendum
  50108e2). Valid; closure exact in every run. H_A 6/14 not supported; H_A3 7/14 supported (threshold); H_Z 8 and H_Z3 7
  pairs with the whole record at zero budget; H_W 1/14 (91, 0.125 bit).
- Analytic bound (frozen as V3, held): I(in; B_res | O) <= H(species pair | O). The total budget can never carry timing.
- Key structural fact (post hoc): in most shadow runs no carrier leaves; the carriers become the shadow's walls, so
  B_res = B_in. "Shadow budget-bearing" is decided by the carriers' own budgets. Walls often hold opposite amounts.
- Rule 91: the wall-budget bit is the drift direction of an asymmetric domain (walls at 1/3 and 1/9), set by the
  carriers' internal phase at contact (period 6), not by the vacuum clock (period 3). The budget labels wall species.
- Reading: records are budget-free; the budget is a label on the coherences that hold the record, not a store.

## Open directions (none started; choose by value, not for completeness)
- The shadow as a bound state of the transformed carriers: classify wall species (speed, budget, flanks) across the 14
  rules. This would turn "residue" into a wall/domain particle inventory.
- Whether the carrier internal phase at contact is generally the record's main bit (cf. SHADOW-009 launch phase).
- Lay + technical write-up of the budget line (bound + carriers-become-walls) for collaborators; one figure:
  output/minimal_realization/MIR-REVERSIBLE-BUDGET-001/posthoc_91_walls.png.

## Deferred
- SHADOW-008 chirality (shelved); Q3 2D rules (later).
