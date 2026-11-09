# MIR-REVERSIBLE-INVENTORY-001: wall/domain species inventory of the shadows; does contact phase select species? (v0.1)

Status: **frozen at tag `mir-reversible-inventory-001-v0.1-frozen`; H_S and H_D outcome-free; class split exposed (below)**.
2026-11-09. Code: `inventory1.py`. Parents: PHASE-001 (invalid; descriptive: contact phase gates the record in 24/24,
full-residue key too fine), BUDGET-001 (91: one wall-budget bit = drift direction). Handoff 2026-11-09c.

## Questions
1. Is a shadow a bound state of a small alphabet of domain and wall species, or something without such a description?
2. Where a coarse description exists: does the carriers' contact phase select *different species* (I_word > 0), or the
   same species word with different internal detail or placement (H_detail = H(phi | sp, word) > 0)?
3. How much of the PHASE-001 record is in fact carried away by rigid movers (unrecognised carriers)?

## Design
Inputs, species, T, N, offsets, duplicate dropping, carrier erasure and age alignment are identical to PHASE-001 (residue
status at aligned age t_a = T + e + SETTLE). The stripped residue then evolves alone for S2 = 1024 ticks (window start
t0), and is observed at t0, t0 + L/2, t0 + L (L = 4096; age-aligned) and at the common absolute tick
tc = T + E + SETTLE + S2 (for exact mover keys only).
- Components: maximal clusters of cells differing from the ambient vacuum, split at ambient-vacuum gaps of >= 16 cells.
- Domains: maximal s-periodic stretches (s <= 8, >= 16 cells; smallest s first). Domain species = (s, orbit-canonical
  pattern: minimum over the time orbit of the periodic ring and over spatial shifts); vacuum states (s = 1, on the vacuum
  orbit) are labelled (1, vac, lag), lag = time lag to the ambient vacuum mod p_v.
- Walls: the gaps between consecutive domains and between the component and the ambient vacuum (width may be 0).
  Wall species = (left domain species, right domain species, speed). Speed = displacement of the wall midpoint over L,
  snapped to the nearest rational with denominator <= 12, accepted if within 12/L and consistent over L/2 within 24/L.
- Component kinds: mover (all walls one speed v != 0: an unrecognised carrier), static (all 0), growing (otherwise),
  disordered (some wall wider than 64 cells at an aligned snapshot; described by its two edge speeds only).
- Run classes: open (component count changes over the four snapshots, or the domain sequence of a non-disordered
  component changes over the aligned snapshots, or any speed is unresolved), else settled or disordered.
- Word (coarse descriptor) of a non-open run = ordered tuple over non-mover components of (kind, domain species
  sequence, wall speeds); open runs have word = open. Movers are added to the outgoing ledger: M = exact (position,
  cropped state) of every mover at tc.
- Wall budgets (invariant rules only, descriptive): window-2 budget between cuts at domain middles (as BUDGET-001),
  time-averaged exactly over its minimal period within the first 120 ticks of the window (per-tick wall budgets
  oscillate with the vacuum phase; seen on 91, below).
Readouts (inputs uniform; exact): only (= PHASE-001); rec = H(in | O, M) (record held by the shadow once movers count as
carriers); carried_by_movers = only - rec; rec_word = I(in; word | O, M); G_shadow = I(shadow present; phi | sp).
Over non-open shadow runs: H_C = H(phi | sp); I_word = I(word; phi | sp); H_detail = H_C - I_word = H(phi | sp, word);
I_sp_word = I(word; sp); n_words; alphabets (domain, wall, mover species); run class counts.

## Validity controls (frozen)
- V0: n, T, aligned residue runs equal PHASE-001 and |only - stored| < 1e-12 in all 28 pairs.
- V1 (symmetry): within every contact class (sp, phi) all inputs have the same residue status, run class, word and
  mover species list. A failure is a code error.
- V2 (null, decided from stored values): nulls 1 and 90s have no aligned residue; in null 5 every residue component is a
  mover (no shadow run, no open run; at least one mover).
- V3: every domain orbit closes within 20000 ticks.
- V4: no component within 64 cells of the ring ends at any snapshot.
- V5: I_word + H_detail = H_C to 1e-9 and H_detail >= -1e-9.
Invalid if any of V0-V5 fails.

## Hypotheses (frozen; over the 24 unexposed shadow pairs; 91 excluded; tolerance 1e-9)
Eligible pairs: H_C > 1e-9 over non-open shadow runs, and open runs <= 1/4 of all shadow runs (the coarse descriptor
describes the pair). n_E = number of eligible pairs.
- H_S (contact phase selects species): I_word > 1e-9 in >= ceil(n_E / 2) eligible pairs. Prior: supported (91: the
  drift-direction bit is a different wall species; I_word = H_C there).
- H_D (contact phase is wholly species, none left to detail/placement): H_detail < 1e-9 in >= ceil(n_E / 2) eligible
  pairs. Prior: uncertain, leaning not supported (the coarse word discards internal detail that PHASE-001 counted).
- Descriptive (not tests): run class split per pair (question 1), alphabets and their sizes against PHASE-001 shape
  counts, carried_by_movers and rec_word (question 3), I_sp_word, G_shadow, wall budgets as a function of wall species
  (was a candidate H_B; demoted because the budget measurement was repaired during calibration).

## Exposure (before freezing; disclosed)
- Everything seen in PHASE-001, BUDGET-001 and SHADOW-009 stored values (including which pairs have H_C > 0 under the
  full key, rigid-mover counts in 37, 201, 139, 209).
- Calibration, full output seen: null 5 (64 runs; two vac|vac particles at +-1/3, all movers) and rule 91 (exposed):
  4 words; domains (1,vac,1), (1,vac,2); walls at -1/3, -1/9, 0, +1/3, +1/9; rec = 1.5, rec_word = 0.5, I_word = H_C = 0.5,
  H_detail = 0, carried_by_movers = 0; each wall species one averaged budget. Design changes from this: speed
  denominator 6 -> 12 and L 1536 -> 4096 (a 1/9 wall was unresolved); per-tick budgets oscillate with period p_v, so
  budgets are period-averaged.
- Smoke runs on all 28 pairs printed validity counts only: unsettled runs, unresolved speeds, orbit caps, edge hits,
  V1 failures, aperiodic budgets, disordered runs. Diagnosis of unsettled runs printed only component counts, domain
  counts, widest wall and hull width over time for a few runs of 143, 154, 186, 151, 37 and 22. Seen: in 143 (and by
  counts 171, 213, 241) the residue spreads at about 1 cell/tick on both sides with component and domain counts rising;
  151 holds a single aperiodic region hundreds to thousands of cells wide; 154, 182, 186 are disordered in all runs;
  37 has slowly growing regions with flickering domain counts. Smoke open-run counts: 143, 171, 213, 241 208/224;
  151, 233 16/48; 37 46/194 (0.237, under the 1/4 eligibility threshold, which was set when the count was 28/194 under
  an earlier classification); 0 elsewhere. The run class split (question 1) is therefore **exposed** and is descriptive.
  Design changes from this: S2 = 1024, disordered kind, open class, and classification on age-aligned snapshots only
  (the late common-tick snapshot broke V1 in 22 at the 64-cell threshold). No word, species, I_word, H_detail, H_C or
  record value was printed for any unexposed pair.

## Limits (stated before running)
Domains must be spatially periodic with s <= 8 and >= 16 cells; longer-period or aperiodic phases are walls or
disordered. Speeds are rationals with denominator <= 12. Open runs get no word (their movers are not separated, so rec
is not corrected there). Disordered components keep only edge speeds, so I_word there is a lower bound on species
selection. One input ensemble per pair; window-limited (S2 + L ticks).

## Prior art (do not claim)
Domain/particle decompositions of CA space-time (Hanson & Crutchfield computational mechanics; domain walls as
particles), collision-based computing (Adamatzky, Martinez). Candidate novelty: an exact information ledger of a
reversible collision record split into carried movers, species word and placement.
