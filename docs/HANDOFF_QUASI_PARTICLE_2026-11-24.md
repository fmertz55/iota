# Handoff: the quasi-particle line (after GOLD-001 and QP-001) — 2026-11-24
Start a new thread from this note. Repo state: everything below is committed (HEAD 86f38a3).

## 1. Lane rules (user, binding)
- Iota is information-first. We follow OUR rules; we do not chase today's physics. Known physics is never a design
  target or a reason to change a rule. Mapping Iota terms to physics is a later, separate step, not now.
- Vocabulary: no mass, energy, inertia, force, "falling". Use:
  - turn rate / clock = how often a coherence swaps its right- and left-moving parts per tick;
  - total ticking rate = coherence clock + notebook cycling (the tally the rule keeps fixed);
  - push-resistance = kick size / speed gained;
  - drift toward slow clocks = what physics would call falling.
- No prior-art or novelty hunting unless the user asks.
- Working style: quick exploratory probe first, then a frozen contract (code + seal + tag) before any claim.
  KISS lay summaries (analogies, "my pick", yes/no decisions), skipped when the user is short on tokens.
  Silence during long runs.

## 2. The substrate as it now stands (all 1D, reversible, local, one cell per tick)
- Coherence: coin-then-shift QCA with NO turn rate of its own; it turns only by reading a notebook.
- Vacuum standing entry a0: the vacuum's notebook holds a resting value. Without it nothing can be held
  (EXPLORE-QP-1: a silent vacuum holds no pocket at any glue strength).
- Glue notebook: per-cell value; marks passed to neighbours, a spring back to a0, written by turning
  (one shared handshake term both ways).
- Gravity notebook ("busy cashier", GOLD-001): marks passed to neighbours, no spring, written by turning; makes
  clocks slower near a lump. QP-001 used a hand-set slope in its place.

## 3. Results (in lane vocabulary)
- GOLD-001 (tag gold-001-v0.1-frozen; results in output/quantum_gold/GOLD-001/): the cashier notebook makes
  coherences drift toward slow clocks at one common rate, never outruns the one-cell-per-tick limit, loses
  nothing, and keeps a which-path record that survives recombination (up to 0.4% fringe loss at lattice scale).
  The stage-3 comparison to atoms is only a conditional "if" (no quasi-particle existed then).
- EXPLORE-QP-1 (output/minimal_realization/EXPLORE-QP-1/): first pockets; heavy memory (marks that stay put)
  gives a preferred rest frame and is retired; travelling glue works better.
- QP-001 (tag qp-001-v0.1-frozen; results in output/quantum_gold/QP-001/):
  PASS: a settled, self-held pocket exists at all 6 settings; its clock is slower than a lone coherence's
  (1.6% / 3.9%); its push-resistance equals its total ticking in the smooth limit.
  FAIL: its drift toward slow clocks reaches only the coherence's own clock, not the glue notebook's cycling.
  It lags by exactly the glue's share of ticking (drift 0.990 / 0.977 vs clock/total ticking 0.990 / 0.976).

## 4. Open questions (stated in our terms; no physics target implied)
1. QP-001's mismatch: the slow-clock slope acts on turning but not on glue cycling. Is that something our rules
   should change, and if so by which rule? The user decides, from Iota's own principles.
2. Replace the hand-set slope with the actual cashier notebook sourced by a lump of pockets.
3. The vacuum standing entry a0 is supplied by hand. Can the substrate make it itself?
4. Records: how do the notebook records of a pocket (glue plus coherence) combine? This was the gold-line question;
   it needs the quantum notebook of GOLD-001, which is not built for pockets yet.
5. Everything so far is mean field, one coherence, 1D.

## 5. Workflow facts
- Sandbox: repo folders are read-only to code. Write in the workspace, then host.save_to_folder, one file per call.
  JSON seals are refused: hand them over as artifacts (create the target folder first with host.make_folder).
- The user commits, tags and pushes from his own terminal; the agent supplies the exact git commands.
- Frozen runs use `git show <tag>:<path>` into the workspace, with the sha256 checked against the seal.
- Code: src/quantum_gold/gold001.py, src/quantum_gold/qp001.py; contracts docs/ICP_GOLD_001_CONTRACT.md,
  docs/ICP_QP_001_CONTRACT.md; seals specs/icp_quantum_gold/.

## 6. Next action
The user picks among the open questions in section 4. Do not propose physics-motivated fixes.
