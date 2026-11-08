# MIR-REVERSIBLE-SHADOW-007: result (2026-11-08)

Frozen tag mir-reversible-shadow-007-v0.1-frozen (bf78658). 25 shadow pairs (14 active, 11 silent) + 3 nulls (1, 5, 90).
Inputs per pair: 256 (2 R species x 2 L species x 64 offsets; 4 pairs had only 1 alias-free species per direction:
151, 233, 54s, 182s). Duplicate starting states dropped: 0 of 7168.

## Frozen verdict: VALID; H_P supported; H_J not supported (narrow miss)
- V0 passed for every pair (reader a at T=600 reproduces stored SHADOW-003/004 values). V1 holds (no residue-free
  cell carries information; aliasing check included).
- H_P (single reader partial in >= 1/3 of pairs): reader a is partial in 11/25 = 0.44. Supported. The SHADOW-006
  family-C gap was not only an aliasing artifact: with alias-free species mixes, one probe type still misses
  part of the record.
- H_J (second reader completes in >= 2/3 of pair partial for a): 7/11 = 0.636 (8 needed). Not supported.
  Stated prior (supported) failed by one pair.

## Per-pair (bits; only / unrecovered by a / by b / by both jointly)
Partial for a, completed jointly (7): 33 (2.47/0.25/2.13/0), 37 (5.02/0.36/0.36/0), 147 (3.50/0.78/0/0),
201 (2.47/0.18/0/0), 58s (6.31/0.83/0.48/0), 114s (5.69/1.41/0/0), 186s (3.53/0.24/3.03/0).
Partial for a, not completed (4, all silent): 26s (2.47/0.50/0.58/0.25), 82s (2.47/0.58/0.58/0.24),
94s (1.50/0.24/1.50/0.24), 218s (1.50/1.50/1.25/1.25).
Full for a (14): 91, 123, 139, 143, 151, 171, 209, 213, 233, 241, 22s, 54s, 154s, 182s.

## Descriptive
- Reader b alone is partial in 20/25 pairs; reader a in 11/25. The right-going probe from the left reads more.
- Pairs partial for both readers alone but full jointly: 33, 37, 58s, 186s. Here each edge of the record is read
  only by the reader that reaches it first; the two readers read complementary parts.
- b alone completes what a misses in 147, 201, 114s (unrecovered_b = 0).
- Split by type (post hoc, not frozen): active pairs partial for a are completed jointly in 4/4; silent pairs
  in 3/7. The H_J failure is entirely a silent-vacuum effect.
- 218s: reader a reads 0 of 1.5 bits; reader b reads 0.25; 1.25 bits are unread by either reader. The record
  is there (carriers erased, residue determines input) but neither L0 nor R0 probes read it.
- Null rule 5 is not clean under species mixes: 64/256 runs leave residue, 0.625 bit, fully read by reader a.
  This does not violate V1 (V1 concerns residue-free cells only), but rule 5 is a null only for single-species
  inputs. Flag it before using rule 5 as a null again.

## Reading
A single probe type reads only part of the shadow's record in nearly half the pairs, also with alias-free inputs.
In active vacua a second reader from the other side recovers the rest (4/4). In silent vacua, some of the record
(0.24-1.25 bit in 4 pairs) is out of reach of both probe types, even when each reads a fresh copy of the shadow.
The missing part is not lost (it is in the residue), but the two available probes cannot read it.

## Lay version
A collision's mark is like a footprint's outline. Look from one side and you often miss part of the outline.
In busy backgrounds, looking from the other side fills in the gap. In quiet backgrounds some of the outline
can't be seen from either side by the passers-by we have: the memory is there, but these readers can't see it.

## Next
What a single reader misses (which edge; which bits of 26s, 82s, 94s, 218s neither reader reaches), then
question 3 (2D reversible rules).

## Addendum (post hoc, not frozen): is the left/right difference chirality?
Scripts: shadow7_mirror_species_posthoc.py, shadow7_mirror_posthoc.py, shadow7_mirror_shapes_posthoc.py; outputs
posthoc_mirror_check.json, posthoc_mirror_control.json, posthoc_mirror_shapes.json. The vacuum is homogeneous (achiral).
1. Rule chirality. 12/25 shadow pairs use rules that are not their own mirror image (139/209, 143/213, 171/241,
   26/82, 58/114 are mirror pairs within the set; 154, 186 have partners 210, 242 outside it). There the physics is
   handed and a left/right difference is expected. Included: 26s and 82s, two of the four pairs neither reader completes.
2. Exact mirror control on the 13 mirror-symmetric shadow rules: reader a's own procedure applied to the reflected
   state (the mirror image of reader a reading the right edge with exactly mirrored geometry). Reader a reproduced in
   all 13. It matches the stored reader b except 37 (4.685 vs 4.664) and 218s (0 vs 0.25): the one-cell launch
   asymmetry (reader a GAP cells from the record, reader b GAP-1) is not the cause. chi = footprint_a - footprint_mirror
   is nonzero in 10/13 (33: 1.875, 151: 2.0, 233: 2.0, 54s: 2.0, 94s: 1.258, 147: -0.779, 123: 0.625, 91: 0.25,
   201: -0.18, 37: -0.017); 0 in 22s, 182s, 218s. Null 5: 0.625.
3. Where the handedness sits (shape closure; carriers erased, translation-normalised):
   - Handed shadows: in 91, 123, 54s, 182s, no shadow's mirror image occurs in the ensemble. The record is a chiral
     object. (182s is chiral yet reads the same from both sides: chi = 0.)
   - Handed placement: in 151 and 233 every shadow is individually mirror-symmetric, yet chi = 2 bits; 33 and 147 have
     mirror-closed shape sets, and chi = 1.875 and -0.779. Here the asymmetry is not in the shapes but in the preparation:
     inputs anchor the right-mover at X0 and vary the left-mover's offset, so which shape sits where (and when each reader arrives) is
     not mirror-symmetric. This is a handedness of the experiment, not of the record.
   - 218s: mirror-closed shapes, chi = 0, still 1.25 bits unread by both. Not chirality.
Reading: the reader asymmetry has three sources: handed rules (12 pairs), handed shadows (4 pairs), and handed preparation
(at least 151, 233, 33, 147, plus null 5). The frozen counts (partial_b 20 vs partial_a 11) mix all three. A clean chirality test
needs a mirror-closed preparation (each input together with its mirror image), where chi is then exactly a property
of the rule and the record.
