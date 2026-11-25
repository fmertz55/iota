# EXPLORE-QP-3: filled vacuum (fork a), exploratory — not a contract
Start: HANDOFF_FILLED_VACUUM_2026-11-25.md. The user's choices: rule unchanged, starting state = ALL R full (step 1);
probe 1 setup as proposed (step 2). Rule code: frozen QP-002 (`src/quantum_gold/qp002.py`, tag qp-002-v0.1-frozen),
reused unchanged; slots are plain yes/no switches (no sign rule), as in QP-002.

## Step 1 (slot choice), by hand from the rule
- All L is the mirror image of all R (x -> -x with R <-> L maps the rule onto itself): same physics, mirrored.
- Alternating R/L is stuck: every edge is both-full or both-empty, so the edge step does nothing; the swap flips each
  node and the state returns exactly every 2 ticks. No information moves. Rejected for that reason.
- All R: every edge holds exactly one full slot, so everything mixes from tick 1. The user picked all R.

## Probe 1: the vacuum alone (files in this folder)
- `p1_vacuum.py` engine (exact: all C(2N, N) states, state vector; N = 12 is 2,704,156 amplitudes).
- `p1_check.py` validity: engine = QP-002 one- and two-coherence ticks to 2.2e-16 (N = 4, 5; three (mu, theta)); back*fwd = 1.
- `p1_drive.py` grid: N = 8, 10, 12; mu = 0.5, 0.8; theta = 0.5 pi and 0; T = 3N ticks -> `p1_vacuum_N{8,10,12}.csv`.
- `p1_reference.py` -> `p1_summary.csv` (per run) and `p1_reference.csv` (random references); conserved-count search.
- Vacuum A = all R. Changed copy B = A with node 0's full slot moved R -> L (same number of full slots).
- Read-outs: return chance of A; per-node trace distance A vs B; far-half / near-half trace distance A vs B
  (half = N/2 nodes); far-half entropy of A (bits); forward T then back T.

## What came out
1. Churn. The all-R vacuum does not stay put. Return chance after tick 1 is at most 0.10 (N = 8) and 0.03 (N = 12) at
   theta = 0.5 pi; late average 2e-4 at N = 12. Each slot ends ~half full (0.50) and both-full ~0.25.
2. Cone. Strict: a one-node change reaches exactly 1 node per tick, both directions, in every run; outside the cone
   the nodes are untouched to machine zero (0.0). Wrap-around at N/2 ticks.
3. Reversibility. Forward then back returns B with fidelity 1.0 (to 1e-14) in every run; norms exact.
4. A second conserved count (new, exact, by hand and checked numerically). Colour the slots:
   P = {R at even nodes, L at odd nodes}, Q = the rest (needs even N on a ring). Every edge exchange (L_x, R_{x-1})
   stays inside one colour; the in-node swap trades P <-> Q. So the number of full P slots is conserved every 2 ticks
   (P and Q trade places each tick). The search over all linear slot counts finds exactly 1 per tick (total) and 2 per
   2 ticks (total + colour) at N = 6, 8, 10, mu = 0.5, 0.8. Moving node 0's slot R -> L shifts one full slot from P to Q
   (P count N/2 -> N/2 - 1 at N = 8, 10, 12).
5. Where the change's information goes (theta = 0.5 pi). Late in the run, A and B look like two random states that
   differ only in the colour count. Per-node distance 0.0900 / 0.0909 (mu 0.5 / 0.8) vs colour-matched random 0.0903
   at N = 12 (plain random: 0.0009); half-ring distance 0.657 / 0.653 vs 0.653; far-half entropy 11.02 / 10.98 bits
   vs 11.03. Same at N = 8, 10. Node distance x N stays ~1.1: the colour record is spread evenly, ~1/N per node.
   Everything else about the change is scrambled into whole-ring correlations (global distance stays 1).
6. theta = 0 runs mix less in 3N ticks: far-half entropy 8.39 / 7.06 bits at N = 12 vs 11.03, node distance
   0.16 / 0.14, return chance up to 0.09-0.26. Correction to the step-2 proposal: theta = 0 is NOT interaction-free
   (two-coherence clocks differ from free pair sums by up to 0.38 rad at N = 6), so it is a theta comparison, not a
   no-interaction control.

## Lay reading
The full vacuum is busy: any one-node change spreads at exactly one node per tick and, within a few ring lengths,
is mixed into the whole ring. The only part that stays readable at each node is a count the rule itself conserves
(the colour balance), and that record is shared evenly by every node. Nothing is lost (it runs back exactly), but
nothing local survives except the conserved count.

## Caveats
Small rings (N <= 12, even only), 3N ticks, two mu and two theta values. Late = t >= N, so N = 8 numbers include
several wraps. The vacuum is translation-symmetric; its far-half entropy sits 0.01-0.2 bits under the colour-matched
random value. Random references: 20 / 10 / 3 samples at N = 8 / 10 / 12 (std <= 0.007 on distances).

## Probe 2: one extra full slot (the user's pick)
- `p2_extra.py` -> `p2_extra_N{8,10,12}.csv`, `p2_free.csv`, `p2_reference.csv`. `p2_long.py` -> `p2_long.csv`.
- A = all R (N full). B = all R plus L_0 full (N+1 full; node 0 both-full; colour P count unchanged, Q + 1).
  N = 8, 10, 12; mu = 0.5, 0.8; theta = 0.5 pi; 3N ticks (long check: 100 ticks, N = 10, 12).
- Where the extra slot sits: dn(x) = node occupation B - A (sums to 1 to machine precision in every run).
  spread = effective number of nodes; near = share within 1 node of node 0 (even spread = 3/N).
- Baselines: (free) one slot in an EMPTY ring, same rule; (random) random states with matched total and colour counts.

Results
1. Not held. The extra slot spreads to the whole ring: spread reaches 0.9 N by tick 6-7 (mu 0.5) and 12-18
   (mu 0.8, N = 10, 12). Late peak share at N = 12: 0.086 / 0.112 (mu 0.5 / 0.8, t >= N) vs even 0.083, random 0.085.
2. The full vacuum spreads it faster than empty space does. At t = N/2 (before wrap-around), spread at N = 12 is
   10.2 nodes vs 3.4 for the free slot (mu 0.5), 6.8 vs 5.3 (mu 0.8). Late, the free slot keeps refocusing
   (peak ~0.37-0.49) while the slot in the full vacuum stays flat.
3. mu = 0.8 is a slow leak, not a held part: near share at N = 12 falls 0.299 (t 20-40) -> 0.263 -> 0.254 -> 0.252
   (t 80-100) vs even 0.250; peak 0.0848 at t 80-100 vs random 0.0849. Same at N = 10.
4. No dip: dn >= 0 at every node and tick (min -1.1e-16). The vacuum is never pushed away from the extra slot.
5. Halves and entropy match count-matched random late: half-ring distance 0.613 / 0.612 vs 0.612; far-half entropy of
   B 10.82 / 10.78 bits vs 10.83 (N = 12). Per-node distance = 1/N exactly on average (equals dn).
6. Forward then back: fidelity 1.0 in every run.

Lay reading: the full vacuum (theta = 0.5 pi) dissolves a single extra slot into an even 1/N per node, faster than an
empty ring spreads it. What lasts is again only conserved counts (total + 1, colour Q + 1), shared evenly. No held
object and no local shadow at these sizes and settings.

Caveats: N <= 12 even, theta = 0.5 pi only, two mu, one disturbance (L_0). Untested: theta near pi, theta = 0
(mixes slower), pairs of extra slots (the QP-002 held pair) in the full vacuum.

## Notes written before probe 2
- Risk flagged at step 1 has shown up: at theta = 0.5 pi the vacuum scrambles a change within a few ring lengths, so a
  held object would have to beat this background.
- Disturbances that change a conserved count (one extra full slot = total; R -> L in one node = colour) leave a
  permanent, evenly spread record. Candidate link to the working hypothesis (forming an object and leaving a shadow may
  be the same event): the shadow may be exactly this conserved-count record. Untested.
