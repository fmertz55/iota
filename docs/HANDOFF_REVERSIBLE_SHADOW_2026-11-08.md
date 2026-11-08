# Handoff: reversible shadow line (2026-11-08)

Supersedes HANDOFF_REVERSIBLE_SHADOW_2026-11-07.md. Working rules there still apply (contract, seal, frozen tag,
run, result commit; information-first vocabulary; check pictures; token thrift).

## In flight
Nothing. SHADOW-007 is finished and committed (RESULT.md in output/minimal_realization/MIR-REVERSIBLE-SHADOW-007/;
final text aa2de4c, which replaced the earlier ede0e7d/a06f30f wording with the same verdicts; post hoc chirality
addendum 54971df).

## Results so far (read each RESULT.md)
- SHADOW-004 (+ addendum): silent vacuum holds shadows by the SHADOW-003 criterion, but only as collision-nucleated
  extended domains; silent movers are light-speed only (seeds <= 8 wide). Contract erratum file exists.
- SHADOW-005: valid but frozen gate (bubble-free only) excluded the shadows; ungated: capacity grows ~0.5 bit per
  doubling. Its species family C is aliased; do not cite.
- SHADOW-007: valid. H_P supported: reader a (R0 copy from the left) is partial in 11/25 pairs; alias-free species
  mixes still leave a single reader partial. H_J narrowly not supported: a second reader (L0 copy from the right)
  completes the read in 7/11 (8 needed). Jointly complete in 21/25. Active pairs complete jointly 4/4, silent pairs 3/7.
  26s, 82s, 94s and 218s keep 0.24-1.25 bit that neither reader reads. Reader b alone is partial in 20/25. Null rule 5
  leaves residue under species mixes (64/256 runs, 0.625 bit): not a null for mixed inputs.
- SHADOW-007 addendum (post hoc): the left/right reader asymmetry has three sources that the frozen counts mix:
  handed rules (12/25 pairs, rule not self-mirror; includes 26s, 82s), handed shadows (91, 123, 54s, 182s: no
  shadow's mirror image occurs), and handed preparation (151, 233, 33, 147, null 5: shapes mirror-closed, yet chi != 0).
  218s is not chirality (symmetric rule, mirror-closed shapes, chi = 0, still 1.25 of 1.5 bits unread by both).
- SHADOW-006: formally invalid (V1 failed: species-family input aliasing). Family A (unaffected): logarithmic growth
  (19/25), content share 0 in 25/25 (the shadow is its outline: two end sites), 0 compact-stationary shadows.

## Lessons (do not repeat)
- Never gate on shadow type; most shadows are extended domains. Measure type.
- Deduplicate inputs by physical starting state, not by label; catalogue lists can repeat a species shifted.
- Left/right comparisons need a mirror-closed preparation; otherwise rule, record and set-up handedness are confounded.
- Match reader launch distances: shadow7.py puts reader a GAP cells from the record, reader b GAP-1 (inclusive spans).
  The mirror control showed the effect is negligible here, but fix it in new code.
- Two sessions committed to the same RESULT.md within a minute. Check git log before writing a result file.

## Next (new thread, in order)
1. What a single reader misses: for pairs partial for reader a, which edge or which part of the outline holds the
   unread bits (e.g. condition on the outline and on reader footprints); and why 26s, 82s, 94s and 218s hold bits that
   neither reader reaches. 218s is the clean case: symmetric rule, mirror-closed shapes, chi = 0, 1.25 of 1.5 bits
   unread. Also consider readers of the other species. New contract, seal, frozen tag as usual.
2. Question 3: 2D reversible (second-order) rules, where an outline is a curve and outline capacity could scale
   differently.

## Future work (do not lose)
- SHADOW-008 (proposed, not started; pick up after items 1 and 2): a clean chirality test. Mirror-closed input
  preparation (every input paired with its mirror image), equal reader launch distances, mirror-symmetric rules only.
  Then chi = footprint_a - footprint_mirror measures only the handedness of the record. Questions: which rules make
  handed records, and is the handed part where single readers fall short? Start from the post hoc scripts
  src/minimal_realization_reversible/shadow7_mirror_species_posthoc.py, shadow7_mirror_posthoc.py and
  shadow7_mirror_shapes_posthoc.py, with outputs posthoc_mirror_{check,control,shapes}.json in the SHADOW-007 folder.
