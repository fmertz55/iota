# MIR-REVERSIBLE-SHADOW-005 — shadow capacity versus collision diversity (v0.1)

Status: **outcome-free; frozen at tag `mir-reversible-shadow-005-v0.1-frozen`**. 2026-11-07. Code: `shadow5.py`.
Parents: SHADOW-003 (45/45 shadow pairs, footprint ratio 1), SHADOW-004 (silent vacuum: no shadow; bubbles mimic shadows).

## Question
As the set of possible collisions grows, does the information held only by the shadow,
H(input | departing carriers), keep growing (an open-ended store) or saturate (a bounded capacity per
collision)? Does a probe still recover all of it?

## Exposure (before freezing)
SHADOW-003 values at 64 offsets (24..87), phase 0, one species pair per rule, T=600, RUN=1500 are known
(only_shadow 1.0 to 4.6 bits). Nothing at other offset ranges, phases, species mixes or T is known.
Smoke test before freezing: V0 path on rule 37 only.

## Design
Rules and pairs: the 14 SHADOW-003 shadow rules, each with its first shadow pair (R0, L0) in SHADOW-003
output order; plus 2 null pairs (first clean pair of rules 1 and 5). Catalogue: collide2.catalogue
(|v| >= 1/8), first 3 right-movers and first 3 left-movers.
Input families (uniform over distinct inputs; input = (R species, L species, offset, L phase)):
- A offset range: (R0, L0, off, 0) for off in 24..24+M-1, M in {8, 16, 32, 64, 128, 256} (nested prefixes
  of one 256-offset set).
- B phase: (R0, L0, off, j) for off in 24..87, j in 0..J-1. L's internal state is taken from its isolated
  orbit at tick q*j (q = homogeneous vacuum period, so the background phase is unchanged) and placed with
  its leftmost cell where the phase-0 seed's leftmost cell is. J = min(8, number of distinct such states).
- C species: (Ri, Lk, off, 0), every Ri, Lk in the first-3 lists, off in 24..87.
One erasure time per rule, T = ceil(296 / min closing speed over used species) + 300, and one probe (a free
R0 copy at tick T) launched from one site, GAP=24 left of everything in every input of every family. RUN =
ceil((rightmost non-bubble residue - launch + 64) / vR0), capped at 6000 (cap hits reported); 1500 if no input leaves residue.
Carriers erased at T exactly as in SHADOW-003 (union-layer clusters, width <= 8, exact orbit, +/-2 margin).
Readouts per family cell: H_in = log2(#inputs); only = H(in | O) = H_in - H(O); footprint = I(in; Y | O);
probe_state = I(in; Yp | O); unrecovered = only - footprint (Y, Yp as in SHADOW-003).
Bubble flag: any residue cluster wider than 64 cells at T. Cells are reported with and without bubble runs
(bubble-free = no bubble run in the cell); hypotheses use bubble-free cells.

## Validity controls (frozen)
- V0: with T=600, RUN=1500, family A M=64 and SHADOW-003's launch rule, the new code reproduces the
  SHADOW-003 only_shadow, footprint_beyond and probe_state_beyond of all 14 pairs exactly. Else invalid.
- V1: every cell whose runs all leave no residue gives footprint = probe_state = 0. Else invalid.

## Hypotheses (frozen)
- H_sat (stated prior): only(A, 256) - only(A, 64) <= 0.5 bit in >= 2/3 of bubble-free shadow rules
  (only(A, 64) > 0). H_grow: >= 1 bit in >= 2/3. Otherwise: mixed.
- H_R generalizes: unrecovered = 0 (footprint ratio 1) in >= 90% of bubble-free cells with only > 0.
- Descriptive: only(M) curves; gain from phase (B) and species (C) over A at M=64; probe_state ratio;
  bubble counts; RUN cap hits.
