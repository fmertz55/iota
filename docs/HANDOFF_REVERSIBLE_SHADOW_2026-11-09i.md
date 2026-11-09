# Handoff: PREDICT steps 1-3 done; next is PREDICT-001 (2026-11-09i)

Supersedes HANDOFF_REVERSIBLE_SHADOW_2026-11-09h.md. Working rules and the user's PREDICT rules are unchanged (see 11-09h).

## Done this thread
1. Prior-art addendum: docs/literature/shadow_prior_art_addendum_embedded_particles_2026-11-09.md (f18eacd, fix 3ea8101).
   Read the 1998 Hordijk-Crutchfield-Mitchell paper from its text. The precedent is a particle catalog plus pairwise
   tables that predicts task performance; phase dependence is replaced by stochastic outcomes, and the authors suggest
   phases as the improvement. Signal machines (Becker, Durand-Lose et al. 2021) are to be cited at the
   compositional-law step. NOT yet done: add the citations to shadow_paper .tex/.bib.
2. SPECIES-001 (tag mir-reversible-species-001-v0.1-frozen; result 3ac23ac): valid. The catalog definition is
   unchanged (user: a new definition could be read as a disqualification); WS = 8, so widths <= 8 at every vacuum
   phase. 1486 species in 28 rules (<= 4 before), mirror pairs; 14 rules still rising at w = 8. Phase 0 alone gives the
   same species set (post hoc). Split pre-registered: width <= 6 discovery, 7-8 confirmation, hash fallback in 54s and
   182s. Eligible pairs have 4-16 confirmation species. Disclosed: the frozen readout yield_phase0 is mis-specified.
3. DESCRIBE-001 (tag mir-reversible-describe-001-v0.1-frozen; result f3eb8ca): valid, H_D supported 7/7. D (wall
   sub/clock/place/v/P plus domain record/phase) rebuilds both layers cell by cell in a held-out future window
   [tw+192, tw+384), in every describable run of all 28 pairs; 92/92 sensitivity controls fail. The language cannot
   describe open runs (37 143 151 171 213 233 241), dis runs (154s 182s 186s) or 37's walls longer than 96 ticks.
   None of these is in an eligible pair.

## Next: PREDICT-001 (lay version to the user first)
- Pairs: the 7 eligible ones (147 201 22s 26s 58s 82s 114s). Histories = their described shadow runs (944). Probes =
  SPECIES-001 species, discovery set for the field-subset search and confirmation set for the test, at several
  arrival phases and times.
- Response = outgoing carriers (species id, velocity, phase, timing relative to the arrival) + D' (DESCRIBE language),
  compared up to lattice space-time translation.
- Exhaustive search over subsets of D's fields for the minimal subsets with I(history; response | D_sub, probe) = 0
  on the discovery probes (report all ties); freeze; test on confirmation probes. Nulls where the claim should fail.
- Code to reuse: describe1.runs/check give D per run; species1 results.json gives the probes (seed index, phase, v).
- Compute note: 944 histories x (probes x phases) runs, each about 10^4 ticks on N = 16384. Pilot-time first; a
  remote target may be needed.
