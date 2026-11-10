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

## Update 2026-11-10: prior-art check done; PREDICT reframed (commit 55d2533)
User asked whether PREDICT "rolls over prior art with our unique terms". Yes for the concept: see
docs/literature/predict_prior_art_mapping_2026-11-10.md. "Same response to every probe = same state" is the
Myhill-Nerode partition / epsilon-transducer (Barnett & Crutchfield 2015). One citation step from that paper finds no
transducer of CA collision products. Candidate results: physical fields generate the minimal partition; position acts
only as a shift; held-out probes; compositional law (strongest).

### Revised lay version (sent to the user 2026-11-10; awaiting his OK before the pilot/contract)
A collision leaves a footprint (the shadow), and DESCRIBE-001 showed it can be written on a short index card. The idea
that "two things are the same if they react the same to everything you throw at them", and that the smallest such card
is the true state, is old (automata theory 1958; Crutchfield's epsilon-transducer 2015). So PREDICT-001 does not claim
it. It asks three narrower things. (1) Is the smallest card made of our physical lines (wall types, beats, domain
phases), and which lines? Our bet, written down first: a ridge's position only shifts the response in space and time;
which objects collided and their relative beat decide everything else. (2) Does it hold for wide probes never used to
find it? (3) Later, the main prize: can a table measured on single ridges predict whole footprints, like a rulebook for
collisions?

### Open decisions (proposed defaults in brackets)
- Arrival beats and times per probe [every vacuum beat, 3 arrival times].
- All 944 histories or a pre-registered sample [time a pilot first, then decide].
- Same response = equal up to a space-time shift [yes, fixed before any run].

### Pick-up point
Next action: get the user's OK on the lay version and defaults, then a timing pilot (print time only), then the
PREDICT-001 contract. Unpushed: local main is ahead of origin by about 11 commits plus tags
mir-reversible-species-001-v0.1-frozen and mir-reversible-describe-001-v0.1-frozen. The push needs the user's
approval.

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
