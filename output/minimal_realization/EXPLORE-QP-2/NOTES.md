# EXPLORE-QP-2 (exploratory, not frozen) — 2026-11-24/25
Parent: QP-001 (tag qp-001-v0.1-frozen), open question 2. Exploratory only: no contract, no seal, no claim.
Vocabulary: clock = turns per tick; push-resistance = kick / speed gained. No mass/energy terms.

## Step 0: real cashier notebook on a QP-001 pocket (route abandoned)
`qp2_step1.py`, `qp2_step1.csv`. Frozen qp001.py (sha256 1865bd2e... checked) + the GOLD-001 cashier carried over
as one shared handshake term. The pocket stays held and still, the run reverses exactly and the cashier stays inside the 1-cell/tick cone,
but the cashier under a lone pocket deepens forever (no spring), clock follows it, pocket loosens.
The user then restated the premise: N nodes, each with its own degrees of freedom, exchanging only information; any
bag of data held away from a node is a penalty flag. Audit of the QP-001 substrate: 6 flags (glue layer, cashier layer,
a0, hand-set slope, mean field, lump weight). Route abandoned for route B.

## Route B: node-only rule, zero bags
Rule = the frozen direct Dirac QCA (docs/ICP_QUANTUM_DIRAC_*; LOCALIZATION_AUDIT.md): each node has two yes/no slots
(R, L); one tick = edge exchange on (L_x, R_{x-1}) with one-coherence block [[-i mu, n],[n, -i mu]], n = sqrt(1-mu^2),
then in-node swap R_x <-> L_x. ONE addition: phase e^{i theta} when both slots of a node are full at the swap
(the frozen code fixed this "both-full" phase at +1 at both steps; the one-coherence law leaves it free).
Rule constants: mu (still supplied, as in the Dirac work) and theta. Penalty flags: 0.
Two coherences, ring of N nodes, exact (number of full slots conserved; blocks of fixed total phase-wind K per node).

Validation (`b1_pair.py`): pair code = full qubit circuit (error 0); both-full phases -1/-1 give free coherences
(sums of one-coherence clocks, antiperiodic wrap, 4e-15); K-blocks reproduce the full spectrum.
Side fact: the frozen rule (+1, +1) is NOT free; two coherences already affect each other under it.

Step 1 (`b1_theta_scan_K0_N60.csv`, `b1_held_states_detail.csv`): held pairs exist at rest, stable N 60 vs 120.
Step 2 (`b2_*.csv`): held pairs stay held at every pair speed K (all K on N = 120), top speed < 1 node/tick.
Step 3, the law (`b3_law.py`, `b3_law_verification.csv`): for the theta-held pair, exactly

    cos(clock at K) = n^2 cos K - mu^2 cos(theta)

(72 well-held cases, mu 0.2/0.5/0.8, five theta, five K: median error 5e-15; loose pairs up to 2e-4, ring wrap).
Reading: the pair's two parts hop together (amplitude n*n) and turn together at one node (mu*mu, meeting phase theta).
- theta = pi/2: the meeting term drops out, so the pair obeys the lone-coherence law with n -> n^2 exactly:
  push-resistance = tan(own clock), top speed n^2.
- Any theta != 0 holds a pair at rest (theta = 0 touches the edge of the free range); theta = pi gives clock 0
  (the "clock-zero held states" of step 1).
- Smooth limit (small mu): pair clock / two lone clocks = |cos(theta/2)|, and push-resistance = own clock for every theta.
A second, theta-independent pair is held by the frozen edge step: cos(clock) = (1-mu^2)/(1+mu^2) cos K (not derived).

Step 4, smooth limit (`c1_smooth_limit.py`, `c1_smooth_limit.csv`, `c1_gap_profiles.csv`): the theta-held pair at
rest (K = 0), picked by the law's clock (law error <= 3e-4, mostly 0), mu 0.8 -> 0.05, theta = pi/4, pi/2, 3pi/4,
rings N = 240 and 360 (agree). The pair SPREADS as mu gets small, and stays held: the chance of finding the two parts
d nodes apart falls off exponentially in d, so the pair has a finite size at every mu. Rule found (small mu):
    mean gap (nodes) x mu x sin(theta/2) -> 1/2,  i.e. mean gap ~ 1 / (2 mu sin(theta/2))
(mu = 0.05: 0.499-0.51 for the three theta). mu = 0.05, theta = pi/2: mean gap 14 nodes; theta = pi/4: about 27 nodes.
At large mu the pair is tighter than this (mu = 0.8: under 1 node). Reading: mu sets the lattice-to-pair size ratio,
so small mu gives pairs many nodes across with no new rule. Not derived yet; the scaling is a numerical fit.

## Limits and cautions
Two coherences, 1D, empty vacuum. Pairs are about 1 node across at mu ~ 0.5-0.8 and spread as 1/(2 mu sin(theta/2)) nodes at small mu (step 4). mu supplied. Pairs are settled
states; in an empty vacuum a free pair can never become held (the rule loses nothing, so free and held states never
mix). No shadow and no drift toward slow clocks are possible here: an empty node stays empty, so nothing outside the
pair can carry a record. Prior-art flag only (no search done): Thirring QCA bound states are the nearby road.

## Running
`python qp2_step1.py` needs src/quantum_gold/qp001.py (frozen) on the path. b1_pair.py and b3_law.py are modules
(numpy, scipy, pandas); see the handoff for the calls used.
