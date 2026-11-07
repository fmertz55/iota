# MIR-REVERSIBLE-SHADOW-004: result (2026-11-07)

Frozen tag mir-reversible-shadow-004-v0.1-frozen (831ec0e). Erratum to the exposure prose:
docs/ICP_MIR_REVERSIBLE_SHADOW_004_ERRATUM.md (23 light-mover rules, 21 oscillator rules; counts were swapped).

## Automated summary (results.json)
- Valid: V0 (rule-37 SHADOW-003 pair reproduced exactly) and V1 (all 47 clean pairs give 0 bits).
- 128 silent rules, 8-wide seeds. Rules with movers: 23, all light-speed. Rules with finite-speed movers: 0.
  So all 86 pairs are light-light (no finite, mixed or still-target pairs were possible).
- S = 31 pairs in 12 rules (22 26 54 58 82 94 114 154 182 186 218 222) left residue holding unique information;
  8 more left residue with none. Stationary residue: 0/31. Footprint ratio 1 in 26/31 (H_R not supported as
  coded); probe-state ratio > 0 in 9/31, median 0.

## Picture check (contract step 5) and post-hoc checks (disclosed: not pre-registered)
- Pictures (16 drawn): the collision nucleates a bubble, a region of a new periodic background whose walls run
  into the silent vacuum at light speed. The "residue" after carrier erasure is that whole domain.
- Post-hoc widths (posthoc_bubble_widths.json): in 30/31 pairs every residue run is >= 1000 cells wide at T=600
  (max 1184, consistent with two light-speed walls). The 31st (rule 222) is a 9-cell, period-1, light-speed
  left-mover in all 32 runs: an unerased carrier just over the width-8 object limit.
- Verdict: no candidate survives the picture check. Q1 = none at this depth. Prior P (S = 0) failed as coded,
  but every counted case is either a bubble or a classifier-width artifact.

## Reading (information-first)
A silent vacuum never held the record itself. When a collision's record outlived its carriers, it lived in a new
background the collision created (a light-speed bubble of a phased domain), never in the empty vacuum. Together with
SHADOW-003 (all 14 shadow rules have f(000)=1), this says: off-carrier records need a background with internal
structure, either already there (an active vacuum) or nucleated by the interaction. A featureless vacuum has no
place to keep one. Caveat: silent rules gave no finite-speed movers even with 8-wide seeds, so slow silent
collisions are untested.

## Lay version
We asked whether truly empty space (a background that does nothing) can keep a memory of a collision after the
colliding objects are removed. In every case where something seemed to be left behind, it was not the empty
background remembering. Either the collision had created a growing patch of a new, patterned background, or a
moving object was too wide for our detector. Empty space kept nothing; memory needed structure to live in.

## Addendum (2026-11-07, after SHADOW-005): the verdict above used a stricter criterion than SHADOW-003
SHADOW-003 counted every residue holding unique information that a probe reads; most of those shadows are
extended domains of the opposite vacuum phase (see SHADOW-005 RESULT). By that same criterion, the silent
vacuum DOES hold shadows here: 31 pairs in 12 silent rules, footprint ratio 1 in 26/31, all as collision-nucleated
domains of a new periodic background (one rule-222 pair is a 9-wide unerased carrier and does not count).
What silent rules lack, at this depth, is a compact or stationary shadow. Whether active rules have compact
stationary shadows has not been checked by the strict criterion either. Corrected reading: a featureless vacuum
cannot store a record as it is; a collision can store one by creating structured background (a domain).
