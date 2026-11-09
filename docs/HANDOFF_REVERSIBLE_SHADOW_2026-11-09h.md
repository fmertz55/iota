# Handoff: new line PREDICT (is the shadow an effective object?) designed, not started (2026-11-09h)

Supersedes HANDOFF_REVERSIBLE_SHADOW_2026-11-09g.md. Working rules unchanged (contract, seal, frozen tag, run, result
commit; information-first vocabulary; check pictures; token thrift; check git log before writing a result file; 4
workers; commit from bash; lay version before any contract or seal). Strategic rule: no tests for their own sake.

## State
- Budget line closed: docs/BUDGET_LINE_WRITEUP_2026-11-09.md (59fa6f5). Open nit: define the "s" pair-label suffix.
- Post hoc interior/probe look (not a test; one input, one probe, in exposed rules 26s and 147; script
  interior_probe_posthoc.py exists only as a session artifact, NOT committed). Undisturbed, the interior is a dark,
  homogeneous, growing domain that holds no bits. A probe rewrites it: in 147 it crosses almost invisibly (a 1-cell edge
  shift, i.e. a delay) and nucleates a new shadow at the static wall; in 26s the swept domain stays changed (~573
  cells) and a fixed-width band runs on at c.

## The new question (user's, from ICP)
Does a compact description D of a shadow (wall positions, domain identities, relative phases) predict its responses to
NEW interactions? Take different histories with the same D, challenge them with untested probe species, phases and
arrival times, and check that D predicts responses consistently. Predicting new interactions is a stronger result than
recovering the old record: it makes the shadow an effective object with its own dynamics. The bridge to mass-like and
gravity-like behaviour comes later.

## User's rules for this line (stated)
1. No hand-picked hold-outs. Which fields of D can be dropped must be chosen empirically: pre-register the selection
   procedure, not its result.
2. Hunt for as many probe species as possible.
3. Strongest possible case: he is an independent researcher using AI, without pedigree. So: exact results, frozen
   tags, one-command reproduction, public code and data, nulls where the claim should fail, kill criteria in advance,
   plain disclosure of AI use.
4. Is the description language complete, including time? Not assumed; tested (step 2).

## Design points (agreed in discussion)
- Trivial-pass trap: if D pins down the microstate, determinism guarantees identical responses. The substantive
  questions are then how small D can be, which fields the future uses, and whether a law carries over to new probes.
- Second-order state = two layers (t, t-1). D must rebuild both.
- Time appears three ways: global tick phase vs the vacuum clock, each wall's clock phase (mod P), and age (edge
  distance from the static wall).
- Response = outgoing carriers (species, velocity, phase, timing relative to the probe's arrival) + the new
  description D'. Compared up to space-time translation (lattice symmetry), fixed before any run.
- Criterion (exact): I(history; response | D_min, probe) = 0 on the confirmation set. Also report the share of the
  record bits the future can see (the partition of histories by response). Prediction to freeze: the contact
  coordinate acts on the future only as a space-time shift (translate lemma), so the species pair and the phase carry
  the bits the future depends on.
- Carrying over to new probes requires a compositional law: scattering tables measured on ISOLATED walls (wall species
  x wall phase x probe species x probe phase -> outgoing state) predict whole-shadow responses as sequences of wall
  events plus the interior crossing shift.
- Closure: D' must again be in the language, and the table must predict a SECOND probe without consulting the
  microstate.
- Mass bridge tension: records are budget-free and about half the shadows carry no budget. Measure mass-like behaviour
  as response: probe delay vs shadow size (147's 1-cell shift is already a delay), and wall-drift recoil. Compare
  budget-bearing with neutral shadows. 1D gives delay only, no bending. These shadows grow forever (not compact).

## Planned order (user approved the direction; the new thread starts at step 1)
1. Prior-art addendum (short note in docs/literature). The paper ALREADY cites Hanson & Crutchfield 1992/1997,
   Hordijk-Shalizi-Crutchfield 2001 and Rupe-Crutchfield 2018. Missing: Hordijk, Crutchfield & Mitchell, embedded-
   particle models (Proc. Physics and Computation 1996; PPSN V 1998, Springer doi 10.1007/BFb0056903): a particle catalog
   plus pairwise interaction tables predict CA behaviour, with particle phases suggested as an improvement. This is the
   direct precedent for PREDICT. Our difference: reversible dynamics, exact information accounting, a memory-bearing
   composite, a pre-registered exact screening-off criterion, confirmation on held-out probes (theirs: irreversible
   evolved CAs, statistical agreement on task performance).
2. DESCRIBE-001 (contract): rebuild both layers cell by cell from D in every shadow run of all pairs. If exact
   everywhere, D is a lossless coordinate system. If it fails, the failures list what the language misses (debris,
   compact movers per the shadow.objects pitfall, interior defects); fix the language before any prediction test.
3. SPECIES-001 (can run in parallel with step 2): exhaustive two-layer seed enumeration per rule, all vacuum phases, up
   to a stated width (4^w seeds: w = 8 ~65k, w = 10 ~1M; pilot-time first; w = 12 only if yield is still rising).
   Dedupe by space-time translation; classify by period and velocity; report a yield curve vs width. Split
   pre-registered: narrow species for discovery, widest for confirmation.
4. PREDICT-001: exhaustive search over all subsets of D's fields for the minimal subsets that leave the
   response partition unchanged on the discovery probes (report all ties); freeze; test on confirmation probes and new
   histories. Includes null rules where the claim should fail.
5. PREDICT-002: second-probe closure. Then mass-like observables (delay, recoil vs budget).
