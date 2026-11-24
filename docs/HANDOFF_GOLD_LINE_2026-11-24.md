# Handoff: the GOLD line (r < 1 with theta, from a local quantum rule) — 2026-11-24

Start a new thread from this note. Status: rung 0 and rung 1 done (exploratory, NOT frozen);
rung 2 designed in lay terms and approved in principle; next action = stage-1 quick probe.

## 1. What "gold" means
- r = visibility of interference = |<record_A|record_B>|; theta = fringe shift (phase).
- r < 1 from gravity already exists in standard physics: an internal clock ticks differently on two
  heights, so the clock records the path (Zych et al., Nat. Commun. 2011; V = |cos(pi dtau / T_clock)|).
  Folman's group simulated this with magnetic gradients (Margalit et al. 2015). Reproducing it = SILVER.
- GOLD = the substrate itself keeps which-path records, giving extra fringe loss beyond the clock effect,
  with a scaling that can be checked against Folman's sharp fringes. Folman's observed visibility losses are
  attributed to recombination imperfections (T^3 SGI, arXiv 1908.03879).
- PRE paper (ORDER/BREAK/REACH) is PARKED, not dropped (one prose pass from done).

## 2. Vocabulary rule (user)
Never use mass as a primitive. In the Dirac QCA the coin parameter (`mu` in
src/quantum_dirac_symmetry_qca/candidate.py) is the TURN RATE eps: how often a coherence swaps information
between its right- and left-moving parts = its internal clock. "Mass" is only the continuum translation.
"Gravity" = a local TICK-RATE field N(x) that scales every coherence's turn rate.

## 3. Rung 0 — prior art (screen: 15 OpenAlex queries + citation chase of 6 anchors)
- Established: Dirac quantum walks in curved spacetime (Di Molfetta et al. PRA 88:042301 2013; Arrighi et al.
  QIP 2016, QIC 2017, Quantum 2018; Mallick et al. J. Phys. Commun. 2019); clock interferometry (Zych 2011;
  Pikovski et al. Nat. Phys. 2015 universal decoherence).
- No paper found combining clock interferometry with a QCA/quantum walk. Rung 1 is therefore a re-derivation.
- Also relevant: "Detecting discrete spacetime via matter interferometry" (PRD 99:015012, 2019);
  "An experiment to test the discreteness of time" (Quantum 2022). Not read.

## 4. Rung 1 — result (script output/minimal_realization/EXPLORE-GOLD-RUNG1/rung1_probe.py)
Setup: coin-then-shift Dirac QCA (same local coin and dispersion cos w = cos a cos k as direct_qca_step),
turn angle a(x) = eps*N(x), hand-placed N(x) = 1 + g(x - x0); clock = equal superposition of turn rates
eps0 +/- delta; branches at heights x0 -/+ dh/2 evolved separately, ideal recombiner = translation by dh.
- theta = eps0*g*dh*T: fitted exponents (eps0, g, dh, T) = 1.0005, 0.9999, 1.0000, 1.0000; prefactor 1.0001.
- r = |cos(delta*g*dh*T)| (Zych): max deviation 2.6e-4 over the 1728-point sweep; 5.2e-3 in the long
  collapse run; collapse to r = 0.0109 at g*dh*T = 10.4 (predicted pi/2/delta = 10.47), then revival.
- Per-mode spatial overlap >= 0.99999: the which-path record is held ENTIRELY by the internal clock;
  the hand-placed field keeps no record. (Why this is silver.)
- Free fall: a/g = eps*cot(eps) (simulated 0.9947, 0.9954, 0.9862, 0.9459, 0.7770, 0.4666 for
  eps = 0.05, 0.1, 0.2, 0.4, 0.8, 1.2). Universal only as eps -> 0. Rb-87 at a Planck tick: eps = 6.6e-18,
  violation ~1e-35 (untestable).
- Gap: light (eps = 0) does not fall — this field only changes turn rates, not propagation.
Data: rung1_sweep.csv, rung1_collapse_run.csv, rung1_freefall.csv (same folder). Figure: rung1_probe.png
(Claude Science artifact, not in repo).

## 5. Decisions (user, 2026-11-24)
1. Test TWO source versions for the tick-rate field:
   - BUSY CASHIER: current update activity slows nearby clocks (marks passed on by word of mouth, ripple away).
   - HEAVY MEMORY (QMM-inspired): stored marks/records slow clocks; marks stay where written.
2. Borrow from QMM ONLY "memory weighs". Do not borrow E=mc^2/temperature, the fitted coupling lambda,
   or geometry inserted by hand.
3. Ruler option (b): one measured number (strength of ordinary gravity) fixes the tick size; the rule has
   one dial (handshake strength) that is NOT tuned to fit; everything else is predicted.

## 6. QMM reading
- Read in full: QMM core (Entropy 26:1039, 2024; arXiv 2504.00039), Geometry-Information Duality
  (Ann. Phys. 2025; arXiv 2409.12206), imprint-retrieval hardware paper (arXiv 2502.15766).
  None works out which-path fringe loss in matter-wave interferometers; the core paper only gestures at an
  unquantified QMM term in BEC-analogue interference. Open ground; Folman's fringes constrain QMM too.
- Abstract only (MDPI refuses automated downloads, 403): "The Geometry and Flow of Informational Time"
  (Universe 12:2, 2025 — time flow from gradients of stored information; closest prior art for HEAVY
  MEMORY, must cite), "Informational Second Law" (Information 17:169, 2026), dark-energy paper
  (Astronomy 4:16, 2025). User may download PDFs manually.
- QMM dark-matter claim overlaps the user's "shadow = dark matter" hunch — cite.

## 7. Rung 2 design (lay version approved in principle; not yet a contract)
- Each cell = Dirac-QCA coherence part + a tiny NOTEBOOK (quantum ledger).
- One local reversible HANDSHAKE: a coherence turning in a cell nudges the notebook; a nudged notebook slows
  turning in that cell. Same term both ways (in a unitary rule you cannot be slowed by a field without
  marking it — related to the Bose et al. / Marletto–Vedral 2017 and Belenchia et al. 2018 line of argument;
  cited from memory, NOT checked).
- Versions differ only in what a mark does afterwards: stays (heavy memory) vs passed to neighbours
  (busy cashier). Must obey the speed limit (neighbour-only, one cell per tick) and lose nothing.
- Stage 1: does it make gravity? An "Earth" lump of coherences at one end; clocks near it slow; test
  coherences of different turn rates fall at the same rate. If neither version falls, stop (itself a result).
- Stage 2: interferometer near the lump; theta; split fringe loss into clock part (Zych) and notebook part
  (the gold number).
- Stage 3: ruler — convert notebook loss to Folman's units using only the strength of gravity; compare.
- Hunch (not computed): heavy memory may fail badly because marks pile up every tick; busy cashier likely
  gives a tiny extra loss. Hardest piece: a notebook rule that makes clean falling, obeys the speed limit,
  and is reversible.

## 8. Next action
Stage-1 QUICK PROBE only (exploratory): build both notebook rules on a small line, check slowdown near a
lump and universal fall. Then a lay summary, then a frozen contract for stages 1-3.
Working style: KISS lay versions with explicit decisions; silence during long runs; quick probe before any
pre-registered run; check prior art before recommending.

## 9. Origin
Visibility-on-ORDER-002 readout from an external chat (visibility.py, summarize.py; not frozen;
RCA54 V = 1.000, shadow rules 0.000-0.048). Reframed: AB vs BA are distinct initial worlds, so this is an
order-superposition (quantum-switch) question belonging to the ORDER line, not a which-path interferometer;
r = 0 for fully reunited movers is a unitarity theorem.
