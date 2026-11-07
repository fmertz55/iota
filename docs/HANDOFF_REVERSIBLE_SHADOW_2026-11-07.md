# Handoff: reversible shadow line (2026-11-07)

## Status
- Submitted: ICP "The Constrained Future" (BioSystems, Hypothesis; SSRN preprint opted in, DOI pending)
  and the Iota shadow paper (Complex Systems, ID 37438c04; source in shadow_paper/complex_systems/).
- Code: src/minimal_realization_reversible/ (engine, core, autonomy, vacuum_collide, collide2, shadow, shadow2, shadow3).
  Each test has docs/ICP_MIR_REVERSIBLE_*_CONTRACT.md, a seal in specs/icp_minimal_realization_reversible/,
  a frozen tag mir-reversible-*-frozen, and results in output/minimal_realization/MIR-REVERSIBLE-*/.
- Key result (SHADOW-003): 91 pairs / 25 rules. Clean pairs give 0 bits; in 45/45 shadow pairs (14 rules) a probe
  recovers all information held only by the background; the probe coherence itself carries it out in 27/45.
  All shadow rules have f(000)=1 (active vacuum).

## Working rules
- Information-first framing: ask where information goes and what constrains reachable futures;
  avoid particle-physics vocabulary.
- Every test: an outcome-free contract and a seal, then a frozen git tag, then the run, then a result commit. Disclose exposure.
- Objects: cluster on the union of both time layers (gap < 3), width <= 8, exact periodicity; erase carriers
  only after resolution (T=600); launch the probe from a fixed site outside all shadows.
- Check spacetime pictures before trusting any classifier; past classifier bugs are listed in the paper's limits section.
- Token thrift: one script per test, writing a summary file; long waits; short replies.

## Next questions
1. Can a silent vacuum (f(000)=0) ever hold a shadow? Search more collision pairs and seeds among silent rules.
2. Shadow capacity versus collision diversity: vary impact offset ranges, phases and species; measure H(input|objects).
3. Two dimensions: second-order reversible 2D rules (e.g. a Margolus neighbourhood or a 2D Fredkin extension);
   re-establish objects, then the ledger, then the shadow.
