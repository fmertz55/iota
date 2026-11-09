# MIR-REVERSIBLE-WALL-001: where in the static wall does the record live? Clock vs placement (v0.1)

Status: **frozen at tag `mir-reversible-wall-001-v0.1-frozen`; H_1, H_T, H_I outcome-free in all unexposed pairs**.
2026-11-09. Code: `wall1.py` (imports the frozen `inventory1.py`). Parent: INVENTORY-001 (valid; one shadow word per
rule; static central wall between two growing domains). Handoff 2026-11-09d, open direction 1.

## Question
Seen at a fixed absolute tick, a contact that happens later (an offset shift) leaves the residue displaced in space and
younger in time. A stationary wall can therefore hold the collision's timing in two places: its **placement** (where it
sits) and its **clock** (its internal orbit phase). If the clock alone carries the record, the record reduces to the
internal state of one stationary wall. Which is it, and is one wall enough?

## Correction to the 11-09d handoff (from stored INVENTORY words; exposed)
"Most rules have one static central wall" overstates it. Of the 24 unexposed shadow pairs, every shadow run has exactly
one static (v = 0) wall in only 7: 147 201 22s 26s 58s 82s 114s. Six others (33 123 139 209 94s 218s) have a single
domain with two outer walls and **no static wall**; the rest are open, disordered or mover-only (or 37, mixed).

## Design
Everything up to and including the word, mover keys M and outgoing ledger O is INVENTORY-001's code path, recomputed
(V0). For each settled run whose shadow components are all non-disordered, every wall of every shadow component is
tracked locally from the last aligned snapshot (t0 + L, where the frozen decomposition gives exact walls) to the common
absolute tick tw = T + E + SETTLE + S2 + L and on for WT = 192 ticks. Each wall boundary is where its flank's known
periodicity breaks (domain period s, or equality with the ambient vacuum), walking from an anchor 40 cells inside the
flank; overlapping flank extents (width down to -8; phase-slip walls in 22s) are allowed. A wall is lost if it widens
past 64 cells or a boundary jumps by more than 80 cells in a tick.
- Wall state per tick k in [0, WT): (lo, width, window = wall cells plus 8 flank cells each side). Orbit period P = the
  minimal P <= 96 with the (width, window) sequence P-periodic over WT and lo advancing by a constant d per period.
- sub = orbit up to rotation (lexicographically minimal rotation; hashed with P and d); t* = absolute tick of that
  canonical phase in [tw, tw + P); **clock** = t* mod P; **place** = lo(t*) - (d/P) t* (space-time intercept; the
  position at the canonical phase for a static wall). Capture-tick invariant by construction.
- W = (sub, clock, place) of the static wall(s) of a run (runs with no residue, mover-only, open or disordered runs get
  their class label). Readouts (inputs uniform and distinct, so H(in | K) = log2 n - H(K); exact):
  rec = H(in | O, M); r_W = H(in | O, M, W); r_clock = H(in | O, M, sub, clock); r_place = H(in | O, M, place);
  r_subplace = H(in | O, M, sub, place); r_sub; **clock_beyond_place = r_subplace - r_W = I(in; clock | O, M, sub, place)**;
  r_outer (all non-static walls), r_allwalls, r_left_edge, r_right_edge (outermost walls); alphabet sizes of sub, (sub,
  clock), place and full state of static walls; static-wall periods.

## Validity controls (frozen)
- V0: n and rec equal INVENTORY-001 (|diff| < 1e-12) and the per-pair word counts equal the stored words, all 28 pairs.
- V1 (eligible pairs): no lost wall, every orbit closes (P <= 96), tracked speed d/P equals the INVENTORY speed.
- V2 (covariance, first fully tracked run of each pair; required in every eligible pair): translating the ring by one cell
  leaves (sub, clock) and shifts place by +1; capturing one tick later leaves (sub, clock, place) unchanged.
- V3: no tracked wall window within 64 cells of the ring ends.
- V4 (order): 0 <= r_allwalls <= r_W <= min(r_clock, r_subplace) up to 1e-9.
- V5: the nulls (1, 5, 90s) have no tracked wall.
Invalid if any fails.

## Hypotheses (frozen; tolerance 1e-9; 91 exposed and excluded)
Eligible pairs: unexposed shadow pairs with rec > 1e-9 in which every shadow run (residue that is not mover-only) is
settled with exactly one static wall (expected from stored words: the 7 above; computed by the code). Threshold:
>= ceil(n_E / 2) eligible pairs.
- **H_1 (the record is one stationary wall)**: r_W < 1e-9. Prior: supported, moderately (the domains and outer walls grow
  from the contact; but nothing forces the central wall alone to fix the input; in 91 the outer walls alone do).
- **H_T (the wall's clock holds timing that its placement does not)**: clock_beyond_place > 1e-9. Prior: uncertain,
  leaning not supported (exposed 91: the static wall's clock is constant within each sub-species).
- **H_I (the record is the wall's internal phase alone)**: r_clock < 1e-9. Prior: not supported (an internal orbit of
  period P holds at most log2(P * n_sub) bits, and offsets span 64 positions; placement should dominate).
- Descriptive (not tests): r_outer and r_allwalls (is the record redundant across walls or localised in the static
  wall?); left/right edge records in the six no-static-wall pairs (where the record must live in the edges); alphabet
  sizes and static-wall periods; 37 (mixed words) reported only.

## Exposure (before freezing; disclosed)
- Stored INVENTORY-001 values (rec, words, run classes for all pairs; the eligible set follows from them).
- Calibration, full output seen, rule 91 only (exposed): rec 1.5; r_W 0.625 (half the shadow runs have no static wall);
  r_clock 1.125; r_place 0.75; r_subplace 0.625; clock_beyond_place 0; r_outer 0; r_allwalls 0; left edge 0.125, right
  edge 0.875; static walls: P = 6 (32 runs), 2 sub-species, 2 (sub, clock), 16 places, 32 states. Null 5 smoke.
- Smoke on all 28 pairs printed validity counts only (covariance controls, lost walls, edge hits, unclosed orbits, speed
  mismatches). First version re-decomposed every tick and changed structure in 32/48 22s runs (and in 37); diagnosis
  printed component and domain counts, wall widths and a 20-cell window of the 22s static wall for six ticks of six
  runs: the frozen domains() drops a whole s = 4 stretch at some tick parities, and the 22s static wall is a phase slip
  whose flank extents overlap by 1-2 cells. Design changes from this: local tracking from the aligned snapshot;
  negative widths allowed. Final smoke: all controls pass; 0 lost, 0 edge, 0 speed mismatch everywhere; 30 unclosed
  orbits in 37 only (ineligible; hence V1 is scoped to eligible pairs). No rec-type readout, alphabet, period or
  clock/place value was printed for any unexposed pair.

## Limits (stated before running)
The clock is defined against absolute time; parts of it locked to the vacuum period are counted as clock but cannot vary
with the collision. Window = wall plus 8 flank cells: domain phase within 8 cells of the wall counts as wall state.
Orbit periods <= 96. One input ensemble per pair (64 offsets x species pairs); no contact-time variation independent of
offset.

## Prior art (do not claim)
Domain walls as particles in CA (Hanson & Crutchfield); phase of a periodic defect as a clock is standard. Candidate
contribution: an exact ledger of a reversible collision record split into the placement and internal phase of one wall.
