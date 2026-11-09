# MIR-REVERSIBLE-SPECIES-001: every probe species up to width 8, under the catalog's own definition (v0.1)

Status: **frozen at tag `mir-reversible-species-001-v0.1-frozen`**. 2026-11-09. Code: `species1.py`. Line: PREDICT
(handoff 2026-11-09h, step 3). Infrastructure, not a test: it supplies the probe set and its pre-registered
discovery/confirmation split for PREDICT-001.

## Question
How many distinct probe species (exact, isolated movers) does each of the 28 shadow/null rules have, if every seed up
to width 8 is tried at every vacuum phase? The current probe lists hold at most 2 right and 2 left movers per rule
(width-5 seeds at vacuum phase 0 for active rules; width-8 seeds, first 2 per speed class, for silent rules).

## Definition (unchanged from the existing catalogs; user decision 2026-11-09)
A new definition of species could be read as a disqualification of new species, so none is introduced.
- Acceptance (VACUUM-COLLIDE-001 / SHADOW-004, constants imported and asserted): ring 256, horizon 120 ticks; the
  layer-t difference from the vacuum is nonzero and <= 8 cells wide at every tick.
- Mover test, per role: active rules use `collide2.catalogue` (drift class sub-light, 2 < |drift| < 116 over 120
  ticks; exact orbit within PMAX = 240; v != 0; |v| >= 1/8); silent rules use `shadow4.catalogue4` (exact orbit;
  v != 0; |v| >= 1/8; light movers allowed). Still objects are not probes and are not catalogued.
- Species = the exact orbit's state set (`C2.orbit`: vacuum phase pair plus translation-normalized difference pattern,
  over one period). Equal sets <=> the same cycle up to ring translation. Two orbits whose difference patterns agree
  but sit on different vacuum phases are different species (phase variants); the count of distinct shapes is reported.
- Width cap: 8, because the 8-cell containment test cannot be passed by a wider seed (user decision: keep the test,
  stop at 8; no wider run).

## Search (what is new)
- Seeds: all 2^16 - 1 two-layer patterns in 8 cells (contains every narrower seed and its translates).
- Vacuum phases: the seed is XORed onto the vacuum at every phase k = 0 .. pv - 1 (pv = 3 or 4 for active rules,
  1 for silent). The existing catalogs used k = 0 only. This changes where seeds are placed, not what counts as a
  species.
- Width of a species = the smallest seed extent (cells spanned in either layer) that produces it; ties broken by
  (phase, seed index).

## Pre-registered split (for PREDICT-001; user decision 2026-11-09)
- Discovery: species of width <= 6. Confirmation: width 7 or 8.
- Fallback: in a rule with fewer than 2 confirmation species, all of that rule's species are split instead by the
  parity of the first 8 hex digits of the species id (sha256 of the sorted state set): odd = confirmation.
- The split is fixed here, before any PREDICT probe is run.

## Validity controls (frozen; invalid if any fails)
- V0 (reproduces the catalogs): active rules: the phase-0 accepted seeds restricted to cells 0-4 equal
  VACUUM-COLLIDE-001's stored accepted objects (seed and drift), all classes. Silent rules: phase-0 accepted count,
  distinct tick-120 patterns and the mover-speed list equal SHADOW-004's stored catalogue entry.
- V1 (nothing lost): every current probe species (`shadow7.lists`) is in the new catalog, all 28 rules.

## Readouts (descriptive; no hypotheses)
Per rule: number of species (right, left), distinct shapes, yield curve (species of width <= w, w = 1..8), the same at
phase 0 only, the split counts and mode. `rising_at_8`: the rules whose count still grows from width 7 to 8. Prior: most
active rules still rising at 8 (rule 91 calibration roughly doubles per width). A curve still rising at 8 is reported
as "not saturated at this depth", never as a total count.

## Exposure (before freezing; disclosed)
- SHADOW-004 already enumerated all width-8 seeds of the silent rules at their single vacuum phase and stored the mover
  speeds, so for silent rules this run mainly recounts exposed material; the new information is in the active rules.
- Calibration on rule 91 (exposed in all earlier contracts), full output: V0 true (98 accepted width-5 seeds), V1 no
  species missing; 258 species (129 right, 129 left), 255 shapes; split by width, 56 discovery, 202 confirmation; yield
  w = 2..8: 2, 8, 20, 30, 56, 118, 258; phase 0 alone gives the same curve. 28 s per rule. No other rule was run.

## Limits
Width <= 8 and the 8-cell containment test exclude wide and breathing species; "all species" means all under this
definition at this depth. Phase variants are counted as distinct species; whether a probe's phase matters is a PREDICT
question.
