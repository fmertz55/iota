# MIR-REVERSIBLE-SHADOW-006 — shadow scaling, outline vs content, regimes and type (v0.1)

Status: **outcome-free; frozen at tag `mir-reversible-shadow-006-v0.1-frozen`**. 2026-11-07. Code: `shadow6.py`.
Parents: SHADOW-003/004/005. Lesson carried in: shadow type is measured, never used as a gate.

## Questions
1. Does shadow capacity H(input | departing carriers) keep growing with collision diversity, and how fast?
2. Is the shadow's information only its outline (where the residue extends), or does its interior hold content?
3. How are interactions split among regimes: clean (no shadow), partial (probe reads only part), full?
4. Is any shadow compact and stationary, in active or silent rules?

## Exposure (before freezing)
Known: SHADOW-005 family A (offset range M = 8..256) for the 14 active pairs (only grows about 0.5 bit per
doubling; most residue runs wider than 64 cells); SHADOW-005 species family for those pairs; SHADOW-004 values at
M = 64 for the silent pairs, which are light-speed-nucleated domains. Unseen: M = 512 anywhere, silent pairs at any
M other than 64, residue outlines, stationarity of active-rule residue, regimes of silent species mixes.

## Design
Pairs: (a) the 14 active shadow pairs of SHADOW-005; (b) per silent rule in SHADOW-004's shadow list, its first
shadow pair, excluding pairs whose residue was the known 9-wide unerased carrier (post-hoc width < 1000 in
SHADOW-004's posthoc_bubble_widths.json), so 11 rules; (c) nulls: first clean pair of rules 1, 5 (active) and 90
(silent, linear). Seeds are explicit two-layer patterns (5-wide catalogue seeds for active rules; SHADOW-004
patterns for silent rules). N = 16384, X0 = 8192.
Families: A = (R0, L0, offset) for offset in 24..24+M-1, M in {8, 16, 32, 64, 128, 256, 512} (nested);
C = (Ri, Lk, offset), first 2 right- and first 2 left-movers of the pair's rule, offsets 24..87.
Per pair one erasure time T = ceil(552 / min closing speed over used species) + 300, one probe (free R0 copy at T)
launched GAP=24 left of everything, RUN as in SHADOW-005 (cap 6000). Carrier erasure and readouts O, Y, Yp exactly
as in SHADOW-005.
New readouts per run, after erasure at T:
- outline G = (min, max) site of all residue (or none);
- type: none / compact (extent <= 64 cells and support stays within its T-extent +/- 8 for 300 ticks) / extended.
Per cell: only = H(in|O); footprint = I(in;Y|O); unrecovered = only - footprint;
content = H(in | O, G) (what the shadow holds beyond its outline); content share = content / only.
Regime per cell: clean (only = 0), full (only > 0, unrecovered = 0), partial (only > 0, unrecovered > 0).

## Validity controls (frozen)
- V0: with T = 600, RUN = 1500, family A M = 64 and SHADOW-003's launch rule, reproduce the stored only_shadow and
  footprint_beyond of every non-null pair (SHADOW-003 rows for active, SHADOW-004 rows for silent). Else invalid.
- V1: every cell whose runs all leave no residue gives footprint = 0 and content = 0. Else invalid.

## Hypotheses (frozen; decided on the union of active and silent shadow pairs with only(A,256) > 0)
- H1 scaling (stated prior: logarithmic). gain = only(A,512) - only(A,256).
  log: 0.25 <= gain <= 0.75 in >= 2/3 of pairs; saturating: gain < 0.25 in >= 2/3; full transfer: gain > 0.75 in
  >= 2/3; otherwise mixed.
- H2 outline (stated prior: outline). content share at A(512): outline if < 0.05 in >= 2/3 of pairs; content if
  >= 0.5 in >= 2/3; otherwise mixed.
- Descriptive: active vs silent split for H1/H2; regime counts per family; type counts; pairs in which every
  residue run is compact; probe-state; RUN cap hits.
