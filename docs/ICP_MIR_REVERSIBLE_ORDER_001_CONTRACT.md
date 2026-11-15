# MIR-REVERSIBLE-ORDER-001: does the background remember the ORDER of two interactions? (v0.1)

Status: **frozen at tag `mir-reversible-order-001-v0.1-frozen`; implementation erratum v0.1.1 (tag `mir-reversible-order-001-v0.1.1-frozen`)**. 2026-11-15. Code: `order1.py`. Line: replaces the
PREDICT/COMPOSE plan (see `docs/literature/compose_prior_art_screen_2026-11-15.md`: PREDICT-001's held-out-probe test and
separated-regime composition are guaranteed by DESCRIBE-001 + locality + determinism and cannot fail). Approved by the
user 2026-11-15 ("ORDER-001: does the background remember order").

## Question (information-first)
When two things happen to the same coherence one after the other, does the world afterwards hold the information *which
came first*, and if so, where: in what moves away (movers) or in what stays behind (the background record)? In integrable
reversible CA (Rule 54 / RCA54) outcomes are order-blind: two-body shifts add and commute (Yang-Baxter). Nothing forces
the shadow rules either way.

## Design (frozen)
- Target X: one mover species. Readers alpha, beta: two distinct species from the other side, started from the same port.
  All species are SPECIES-001's (unchanged catalog, both splits; no fitting here, so no discovery/confirmation split).
- Slots: slot 1 reader seeded at (its phase, X0 - side*d); slot 2 = slot 1 translated exactly by g = (v_X Delta, Delta),
  Delta a multiple of L = lcm(pv, P_X) with v_X Delta integer. A reader alone therefore meets X identically in either
  slot. V_slot checks this cell by cell (both layers) on the first 20 cases of every job.
- AB = alpha slot 1, beta slot 2; BA = the swap. Nothing else differs (same X, X phase tau_X, d, Delta, clocks).
- Grid per rule and side: X in all target-side species; {alpha, beta} all unordered pairs of the other side; tau_X in
  X's phase + m pv, m < P_X / pv; d in 24..87; Delta in {smallest multiple of L >= 400, >= 800}. Sample (fixed seed
  20261115, per rule and side): 800 cases (eligible), 400 (nulls, control). Both sides (mirror) are run.
- Ring N = 32768, X0 = 16384. Readouts at Delta + 1600, 2400, 3200 (common to both orders).
- Coarse outcome (translation- and age-invariant): movers = multiset of (orbit species id, direction); background =
  multiset of residue component words after movers are erased (word = INVENTORY-001 decomposition's sequence of domain
  records; compact still oscillators = ('osc', id); components without domains = ('nodom',)).
- touched: the slot-2 reader interacted (the AB world differs from {slot-1 world + free slot-2 reader}) in BOTH orders.
  Untouched cases differ trivially (whoever comes first reacts) and are excluded from the hypotheses (reported).
- Classes per case (persistent = holds at all three readout times): order (AB != BA); movers-only; background-only
  (movers equal, background differs); both; gate (background present in one order only); written (background present in
  both orders and different).
- Order bits: for an equiprobable order bit, I(order; coarse outcome) = 1 bit in a case where AB != BA, else 0. Reported as
  bits per touched case, split into bits readable from the background and from the movers.

## Validity controls (frozen; invalid if any fails)
- V0 (calibration reproduced, exposed rule 91): X = 77faeae98c25bc25, alpha = 7c044ea74008e3ff, beta = 0d34f6ea613699c3,
  tau_X in {0, 3}, d = 24, 26, .., 86, Delta = 240, first readout: 64 valid, 32 order cases.
- V_slot: every checked case exact, and >= 10 checked cases per job.
- V_C54 (integrable positive control): second-order rule 250 (f = l OR r) is Bobenko's RCA54 on each of the two
  decoupled sublattices (checked before freezing: f250 = l|r on all 8 inputs; a right/left soliton pair either does not
  meet, other sublattice, or both survive with a -2 cell shift and no residue). NOT second-order Wolfram 54
  (f = c XOR (l|r), the '54s' of the shadow tables). Reader species: SPECIES-001 acceptance applied unchanged to 250
  (30 species, 15 per side, all |v| = 1, P = 1: soliton packets). Required on >= 100 touched cases: no order effect at
  any readout time, no background ever, and the target-direction movers' (species, position) equal in AB and BA at every
  readout time (exact Yang-Baxter additivity).
- V_valid: in every eligible pair, >= 90% of sampled cases valid and >= 50 touched cases.

## Hypotheses (frozen; 7 eligible pairs 147 201 22s 26s 58s 82s 114s, both sides pooled)
- **H_O (order is recorded)**: >= 1 persistent order case among touched cases. Supported if >= 5 of 7 pairs.
  Prior: likely (rule 91 calibration: 32/64, all via gating).
- **H_B (the background alone holds order)**: >= 1 persistent background-only case (movers identical, background
  differs). Supported if >= 4 of 7. Prior: uncertain (rule 91: 0; its order cases differed in both).
- **H_W (order is written into the record's content)**: >= 1 persistent written case (records in both orders, different).
  Supported if >= 4 of 7. Prior: uncertain.
- Descriptive: bits per touched case (order, background, movers, background-only), class counts, by Delta and side;
  nulls 1, 5, 90s (rules whose standard pair leaves no shadow; other species may); rule 91 full sample not run.

## Exposure (before freezing; disclosed)
- Rule 91 (exposed since INVENTORY/DESCRIBE): calibration slice above, run in full with an earlier readout (Delta + 1200
  and settle check): 64 valid, 32 order, all 32 gate-type (record in one order only; movers differ too). Mechanism seen:
  the first reader's passage shifts the target's phase, which gates whether the second contact writes a record.
- Rule 250: single-pair scattering check above (16 contacts). No order runs.
- Smoke on all jobs (8 cases each) printed validity, touched and timing only. An earlier smoke (v0 of this code, ring
  16384, settle requirement) printed validity only and showed many unsettled cases in 58s, 82s, 114s. Diagnosis on
  single-reader runs and on AB-only runs (no AB/BA comparison): records keep spreading and interacting long after the
  second event (light-speed growth) and wrap a 16384 ring. Fixes, made before any order outcome was seen on these rules:
  three common readout times instead of settling, ring 32768, and the touched-both restriction (the untouched case was a
  flaw in my "built-in null": AB and BA differ trivially there).

## Limits
- Coarse words do not see wall-level detail (WALL/PHASE lines): background order counts are lower bounds.
- Readout is at fixed common times, not asymptotic (records in growing rules have no asymptotic state); persistence over
  1600 ticks guards against flicker, not against slow systematic lags.
- A mover trapped inside a growing domain counts as background.
- One target and two readers; no claim about longer histories.

## Prior art (do not claim)
Integrable RCA scattering and order-independence (Bobenko et al. 1993, cited from memory, not checked; buca2021; klobas2022; wilkinson2022); soliton CA
(park1986); glider-collision phenomenology (martinez2006/2011/2012); Pivato defect kinematics (pivato2007); coarse-graining
commuting diagrams (Israeli & Goldenfeld 2006). Screen of 5 OpenAlex queries found no study measuring which part of a
reversible CA (movers vs. background) holds the order of interactions. Candidate contribution: that measurement, against
an exact integrable control in the same engine.

## Erratum v0.1.1 (2026-11-15, implementation only; no output was read)
The v0.1 run was stopped after 4.5 h with no output written (results are written only at the end). Cause: the case grid
was materialised as a Python list (16.5 million entries for 90s, in two concurrent workers) on an 8 GB machine, with
heavy paging (about 900k pageouts) and a load average of 35-70 from other processes. Changes: (1) the grid is indexed
lazily in the same enumeration order (checked element by element against the v0.1 grid for 22s, 147 and 26s, both
sides: identical), so the fixed seed draws exactly the same cases; (2) each job writes a checkpoint file; (3) 5 workers
instead of 6. Hypotheses, sample, controls and readouts are unchanged.
