# MIR-REVERSIBLE-PHASE-001: does a shadow keep the carriers' contact phase as internal state, or only as placement? (v0.1)

Status: **outcome-free for all shape-type and information values; frozen at tag `mir-reversible-phase-001-v0.1-frozen`**.
2026-11-09. Code: `phase1.py`. Parents: BUDGET-001 (rule 91 post hoc: the one wall-budget bit is the drift direction of an
asymmetric domain, set by the carriers' internal phase at contact), SHADOW-009 (pairs, inputs, launch phase matters for
readers). Handoff 2026-11-09b, open direction 2.

## Questions
1. Where does a collision put the carriers' relative internal phase at contact: into the shadow's internal state (a
   different domain shape / wall species), or only into its placement (the same shape, displaced in space and time)?
2. Does the contact phase decide whether a record forms at all (shadow vs pass-through)?

## Analytic reduction (derived before freezing)
For species pair (R, L) with periods p_R, p_L, vacuum period p_v and speeds v_R > 0 > v_L, let tau = lcm(p_R, p_L, p_v) and
Delta = (v_R - v_L) tau (an integer in every pair). During free flight the state of offset off at tick tau is the
state of offset off - Delta at tick 0, translated by v_R tau. Hence every input decomposes exactly into
(species pair, contact class phi = off mod Delta, placement), and all offsets of one contact class give one history up
to space-time translation. Any shape descriptor that is translation-invariant is a function of (species pair, phi).
Counting bits is therefore arithmetic (phi has Delta values, mostly 2 or 4 here; placement has the rest) and is **not**
the question. The question is whether different contact classes give *different* shapes (phase kept as internal state)
or the *same* shape (phase converted into a sub-Delta shift of placement). Reversibility guarantees that the phase is
kept somewhere; only its form is open.

## Exposure (before freezing; disclosed)
- Rule-level facts (no outcome): p_v, species periods/shifts and Delta for all 28 pairs. Delta = 2 or 4 in all pairs
  except 37 (Delta in {12, 70, 70, 10}).
- Stored values known: SHADOW-007/009 (n, residue_runs, only, readers), BUDGET-001 (budgets, segments; I(flanks | O)
  > 0 in 37, 201, 91, 22s). Flank descriptors are not translation-invariant (they include the spatial phase), so they
  do not determine shape types; disclosed anyway.
- Rule 91 is **exposed**: BUDGET-001 post hoc showed that in (R0, L0) the even offsets give two drift directions
  alternating with off mod 4 (two shape types). 91 is run and reported but excluded from every hypothesis count.
- Smoke runs of `phase1.py` printed **validity flags and counts only** (n, dropped, residue_runs at T, V1 failures, edge
  hits). A first design erased carriers at the fixed tick T (the SHADOW-009 convention). It failed V1 in rule 37 in one
  contact class ((R1, L1), phi = 1, offsets 31..81). Diagnosis seen: at T two objects are recognised only at
  offset 71, and the residue cluster widths are 320, 314, 312, 306, 292, 296. Conclusion: at fixed T the object/residue
  split depends on age. The design was changed to erase at equal collision age (below). With it, V1 failures = 0,
  edge hits = 0 and dropped = 0 in all 28 pairs. No shape count, shape type, or information quantity was
  printed or seen for any pair.

## Design
Pairs: all 25 shadow pairs of SHADOW-009 (14 invariant + 11 invariant-free rules) and the 3 nulls (1, 5, 90s).
Inputs, species lists, T, N = 16384, X0 = 8192, offsets 24..87, duplicate dropping: identical to SHADOW-009.
Per input: (i) run to T; objects and erasure exactly as SHADOW-009, giving O (outgoing objects) and the SHADOW-009
residue status (for V0 only). (ii) Continue the full state for e = floor((off - 24) / (v_R - v_L)) + SETTLE ticks
(SETTLE = 300), so all inputs reach roughly equal collision age and all inputs of one contact class reach exactly equal age. Then
recognise objects (`shadow.objects`) and erase them as in SHADOW-009. This gives the aligned residue. (iii) If the
residue is non-empty, evolve it alone for 2D further ticks, D = 3 max tau + 32, recording at every tick a key = hash of
(vacuum pair (V[t], V[t+1]), the cropped vacuum difference of both layers). Centre key = key at tick D.
Shape type S: union-find over residue runs of a pair. Run a and run b are joined if b's centre key equals a's key at any
tick within +-D of a's centre (an exact space-time translate, same vacuum phase). Runs with no aligned residue have S = None.
Readouts (inputs uniform; exact):
- only = H(in | O) (as SHADOW-009).
- Gate G = I(res; phi | species pair), over all inputs (res = aligned residue present).
- Over residue runs: H_C = H(phi | sp) (phase available to keep); I_int = I(S; phi | sp) (phase kept as internal state;
  = H(S, sp) - H(sp) because S is a function of (sp, phi)); H_place = H_C - I_int = H(phi | sp, S) (phase kept only as
  placement); I_sp_int = I(S; sp) (species identity kept as shape); n_shapes, n_contact (distinct (sp, phi)).
- I_rec_S = I(in; S | O): the record bits held by shape, against only.
- Shape-type inventory (descriptive): per type, number of runs, contact classes, edge speeds over the 2D window.

## Validity controls (frozen)
- V0: n, dropped, residue_runs (at T) and T equal SHADOW-009, and |only - stored| < 1e-12, for all 28 pairs.
- V1 (symmetry): within every contact class (sp, phi), all inputs have the same aligned-residue status, the same centre
  key and the same shape type. A failure is a code error.
- V2: the nulls have no residue and n_shapes = 0.
- V3 (window saturation): the shape partition with window +-D equals the one with +-D/2 in every pair.
- V4: the residue stays more than 64 cells from the ring ends at every recorded tick.
- V5: I_int equals the full form H(S,sp) + H(phi,sp) - H(S,phi,sp) - H(sp) to 1e-9.
The test is invalid if any of V0-V5 fails.

## Hypotheses (frozen; over the 24 unexposed shadow pairs; tolerance 1e-9)
Eligible pairs for H_I and H_F: those with H_C > 1e-9, where residue runs occur in at least two contact classes of some species pair.
- H_G (phase gates the record): G > 1e-9 in >= 12 of 24 pairs. Stated prior: supported (in 91 odd offsets pass through).
- H_I (phase is kept as internal state): I_int > 1e-9 in >= ceil(n_E / 2) eligible pairs. Stated prior: supported
  (91 is the model case; walls of different species in BUDGET-001).
- H_F (phase is kept fully as internal state): H_place < 1e-9 in >= ceil(n_E / 2) eligible pairs. Stated prior:
  uncertain, leaning not supported (expect some phases to give the same domain displaced).
- Descriptive (not tests): all readouts per pair; the shape-type inventory with edge speeds (input to the wall/domain
  species inventory, handoff direction 1); 91 and the nulls; the count of inputs whose residue status differs between
  T and the aligned erasure.

## Limits (stated before running)
Matching is exact but windowed (+-D ticks around equal nominal age). Matches outside the window are not found, which
would inflate I_int; V3 checks that the window is saturated. One input ensemble per pair. The shape key is the full
cropped residue, so two shapes that differ only in an internal detail away from the walls count as different.

## Prior art (do not claim)
Collision phase dependence of soliton and glider interactions in CA is well known (e.g. phase-dependent outcomes of
glider collisions in rule 110 and in soliton CA; Park, Steiglitz and Thurston 1986). Candidate novelty: the exact split of
a reversible collision record into internal state vs placement, and the reading of shadow domains as phase memories.
