# Handoff: reversible shadow line (2026-11-08)

Supersedes HANDOFF_REVERSIBLE_SHADOW_2026-11-07.md. Working rules there still apply (contract, seal, frozen tag,
run, result commit; information-first vocabulary; check pictures; token thrift).

## In flight
SHADOW-007 (tag mir-reversible-shadow-007-v0.1-frozen; shadow7.py; contract docs/ICP_MIR_REVERSIBLE_SHADOW_007_CONTRACT.md)
was started 2026-11-08 in the background. It writes output/minimal_realization/MIR-REVERSIBLE-SHADOW-007/results.json
and run.log. If results.json exists, write RESULT.md from it and commit. If not, rerun:
`python src/minimal_realization_reversible/shadow7.py > output/minimal_realization/MIR-REVERSIBLE-SHADOW-007/run.log 2>&1`
(deterministic; about 15-30 min on 6 workers). Questions: H_P (alias-free species mixes still partial for one reader,
>= 1/3 of pairs) and H_J (a second reader from the other side completes the read in >= 2/3 of partial pairs).

## Results so far (read each RESULT.md)
- SHADOW-004 (+ addendum): silent vacuum holds shadows by the SHADOW-003 criterion, but only as collision-nucleated
  extended domains; silent movers are light-speed only (seeds <= 8 wide). Contract erratum file exists.
- SHADOW-005: valid but frozen gate (bubble-free only) excluded the shadows; ungated: capacity grows ~0.5 bit per
  doubling. Its species family C is aliased; do not cite.
- SHADOW-006: formally invalid (V1 failed: species-family input aliasing). Family A (unaffected): logarithmic growth
  (19/25), content share 0 in 25/25 (the shadow is its outline: two end sites), 0 compact-stationary shadows.

## Lessons (do not repeat)
- Never gate on shadow type; most shadows are extended domains. Measure type.
- Deduplicate inputs by physical starting state, not by label; catalogue lists can repeat a species shifted.

## Next after SHADOW-007
What a single reader misses (if H_J holds, which edge it fails to read), then question 3: 2D reversible rules,
where an outline is a curve and outline capacity could scale differently.
