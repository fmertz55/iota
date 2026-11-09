# MIR-REVERSIBLE-BUDGET-001: where the budget goes in a shadow collision (carriers vs shadow) (v0.1)

Status: **outcome-free for all budget values; frozen at tag `mir-reversible-budget-001-v0.1-frozen`**. 2026-11-09.
Code: `budget1.py`. Parents: BUDGET-000 (exact window-2 invariants; vacuum density 0 in every phase) and its window-3
extension (`budget0_w3.py`, BUDGET-000/window3.json), SHADOW-009 (pairs, inputs, record sizes).

## Questions
1. When a collision leaves a shadow, does the shadow carry conserved budget, or do the outgoing carriers take it all?
2. Record cost: can a shadow record be written at zero deposited budget? How many record bits can the budget carry?
3. Does the budget's *distribution* inside the shadow (its walls) carry record bits that the total cannot?

## Exposure (before freezing; disclosed)
- BUDGET-000 and its window-3 extension: rules only. Window-3 adds new invariants in 9/14 rules (22 91 218: +1;
  33 37 54 147 201: +2; 26 82 94 123 139 209: 0); all are exactly conserved in simulation; vacuum shift phase-independent.
- SHADOW-007/009 stored values are known (n, residue_runs, only, residue type, reader results).
- Smoke runs of `budget1.py` on all 14 pairs printed **validity flags and segmentation counts only**: V0-type counts
  (n, dropped, residue_runs) match SHADOW-009; V1 true; V2 (closure) failures 0; V4 failures 0 in all 14. A first
  edge-split design (cut only at homogeneous vacuum-orbit cells) found no cut in 26s 82s 94s 218s and was replaced
  by the segment design below; with it, runs with >= 1 cut / residue runs: 22s 48/48, 26s 96/96, 33 128/128,
  37 184/188, 54s 32/32, 82s 96/96, 91 64/64, 94s 64/64, 123 32/32, 139 64/96, 147 128/128, 201 96/128, 209 64/96,
  218s 64/64; drifting stretches 0; segment-count histograms and flank periods (1, 2, 4) were seen. No budget value
  (B_in, B_out, B_res, segment budget) and no information quantity was printed or seen.
- Original question (c) (do invariant-free rules hold shadows as readily?) is answered by stored data and is **not
  tested**: the 11 invariant-free rules hold shadows (only median 2.50 bits, range 0.25-6.31; residue fraction median
  0.875) vs the 14 invariant rules (only median 2.11, range 0.625-5.02; residue fraction median 0.375). Records need
  no additive budget to exist (window <= 4); invariants beyond window 4 or non-additive ones are not excluded.

## Analytic reduction (derived before freezing; frozen as validity control V3)
Given closure, B_res = B_in(ri, li) - B_out(O). Within one outcome class O the residue's total budget is a function of
the input species pair alone, never of the offset: I(in; B_res | O) <= H(ri, li | O) <= 2 bits, and = 0 when there is one
species per direction (54s here). The offset bits of the record are budget-free for every additive invariant at every
window. Only the distribution of budget inside the residue (question 3) can escape this bound.

## Design
Pairs: the 14 shadow pairs of the invariant rules (22s 26s 33 37 54s 82s 91 94s 123 139 147 201 209 218s). The 11
invariant-free pairs have B identically 0 and are only listed. Nulls are not run.
Inputs, species lists, T and carrier erasure are identical to SHADOW-009 (`shadow7.lists`; N = 16384, X0 = 8192; 256 or
64 inputs; duplicate starting states dropped).
Budget vector per state: ring totals of the BUDGET-000 window-2 basis ('w2', primary) followed by the new window-3
tables ('full' = w2 + w3). Vacuum density is 0 in every phase, so every ring total is gauge-free.
Per input: B_in (placed state, t = 0); B_R, B_L (each seed alone); at T, objects from `shadow.objects`; B_obj = ring
total of the object's window [a-2, b+2] pasted into the homogeneous vacuum of phase T; B_out = sum of B_obj; B_res =
ring total of the erased state (erasure as SHADOW-009; time-independent afterwards). Elastic run: outgoing species
multiset equals the incoming one.
Segments (w2 only): the residue support [lo, hi] is cut at background stretches, maximal runs of >= 16 cells that are
spatially periodic with smallest period s <= 8 (smaller s first; no overlap). A stretch is a valid cut only if its w2
budget per period is exactly 0 (else counted as drifting). Cut value = left sum of local w2 densities averaged over one
period at the stretch middle (exact rational). Segment budgets = differences of successive cut values (last = B_res
minus last cut). Flank descriptor of a cut = (s, period pattern read from the first site m = 0 mod s in the stretch).
Gauge note: a coboundary changes each segment budget by a fixed function of its flank descriptors, so quantities
conditioned on the flank sequence (FL) are gauge-invariant.
Readouts per pair (inputs uniform; exact): only = H(in|O); bound = I(in; ri,li | O); for w2 and for full: I_B =
I(in; B_res | O), I_free = only - I_B, only_Z = sum over classes (O, B_res = 0) of p log2(class size), f_bear = fraction of
residue runs with B_res != 0, distinct B_res values, B_res in elastic runs. Segments: I_seg = I(in; SEG | O);
I(in; FL | O); H_W_bits = I(in; SEG | O, FL, ri, li); outermost-segment information I_segL, I_segR (against SHADOW-009
I_L, I_R); segment-count histogram; elastic fraction.

## Validity controls (frozen)
- V0: n, dropped, residue_runs equal SHADOW-009 and |only - stored| < 1e-12 for all 14 pairs.
- V1 (conservation): B_in = B_R + B_L for every input; each R/L species has equal budget at t = 0 and at T.
- V2 (closure): B_in = B_out + B_res exactly for every input. A pair with any failure is excluded from hypothesis
  counts; the test is invalid if more than 2 pairs are excluded.
- V3 (derived bound): I_B <= bound + 1e-9 for w2 and full in every included pair; I_B = 0 in 54s.
- V4: every residue-free run has B_res = 0.

## Hypotheses (frozen; over included pairs, n_i of them; budget-bearing pair: f_bear > 1/2)
- H_A (the shadow is budget-bearing, w2): budget-bearing pairs >= ceil(n_i / 2). Stated prior: not supported (guess:
  walls nucleate in opposite-budget pairs, so the residue total is mostly 0).
- H_A3: the same with the full (w2 + w3) vector. Stated prior: not supported.
- H_Z (zero-budget records exist, w2): only_Z > 1e-9 in >= 1 pair. Stated prior: supported.
- H_Z3: the same with the full vector (B_res = 0 in every component). Stated prior: supported.
- H_W (wall budgets carry record bits beyond species and domain phases): H_W_bits > 1e-9 in >= 1 pair. Stated prior:
  uncertain; leaning supported in at least one pair (several wall species with equal flanks).
- Descriptive (not tests): all readouts above per pair; the 11 invariant-free pairs listed with B = 0.

## Prior art (do not claim)
Pomeau 1984; Takesue 1987; Hattori & Takesue 1991 (additive conserved quantities in reversible CA). Candidates for
novelty: the carrier/shadow split of the budget; the bound that record information beyond species identity is
budget-free in total; whether the budget's distribution in the shadow carries record bits.
