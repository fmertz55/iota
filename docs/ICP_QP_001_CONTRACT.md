# QP-001 (v0.1): a settled pocket, its clock, its push-resistance and its drift toward slow clocks
Status: **draft, to be frozen at tag `qp-001-v0.1-frozen`**. 2026-11-24. Code `src/quantum_gold/qp001.py`
(`check` = validity only; `run` = all outcomes). Parent: EXPLORE-QP-1 (exploratory).
Vocabulary: no energy or mass. clock = turns per tick of the coherence; total ticking rate = clock + glue-notebook
cycling (the tally the rule keeps fixed); push-resistance = kick / speed gained; "drift" = drift toward slow clocks.
## Rule (fixed)
Coherence: coin-then-shift QCA with NO turn rate of its own; turn angle = N * chi. Vacuum has a standing entry a0.
Glue notebook chi: marks passed to neighbours (speed c = 0.985), spring mu = a0/2 back to a0, source G*mu^2*S,
S = 2Re(R*L). Gravity: hand-set slope N = 1 + g(x - x0), g = 4e-6, slowing the coin, the glue spring and the glue
mark-passing. Mean field, one coherence, 1D, L = 4096.
Settled pocket: coherence and glue solved together (stationary QCA pattern + static glue) to 1e-9.
Grid: a0 in {0.16, 0.08, 0.04} (smooth-limit series; T = 600/a0) x G in {0.4, 0.7}.
Lone-coherence references (lattice law): push-resistance/clock = tan(a0)/a0; drift = a0*cot(a0) * g.
push_norm = push-resistance / total ticking / (tan a0/a0); drift_norm = drift / (g * a0 cot a0).
## Validity
V1: settle error < 1e-9 for all 6; still pocket (g = 0) moves < 1e-6 cell and changes width < 1e-4 cell over T;
clock from the run matches the settled clock to 1e-8.
## Hypotheses
- H-POCKET: all 6 settled pockets pass V1 (a self-held pattern exists at every setting).
- H-CLOCK: the pocket clock is slower than a lone coherence's (a0): relative slowdown > 1e-3 at all 6.
- H-PUSH: for each G, |push_norm - 1| falls monotonically along a0 = 0.16, 0.08, 0.04, is < 0.03 at a0 = 0.04,
  and a straight-line fit of (push_norm - 1) vs a0 has |intercept| < 0.01 (push-resistance = total ticking in
  the smooth limit).
- H-DRIFT: same three conditions for drift_norm (window from T/6): the pocket drifts toward slow clocks at the
  lone-coherence rate in the smooth limit.
- H-LINK: |drift_norm x push_norm - 1| < 0.02 at all 6 (the remaining unfairness is exactly the push-resistance
  gap; the pull toward slow clocks follows total ticking).
Descriptive: drift with window from T/3; widths; clocks.
## Exposure
EXPLORE-QP-1 (rough and settled pockets at a0 0.2/0.1, G 0.5/1.0) outcomes known: gaps shrink roughly in
proportion to a0; drift_norm x push_norm near 1 at G 0.5. A check printed validity only for (0.16, 0.4, 600 ticks);
a load check printed settle convergence only for a0 = 0.04.
## Limits
Mean field, single coherence, 1D; gravity is a hand-set slope (the cashier notebook is not run here); the vacuum
entry a0 is supplied. The quantum notebook and many-coherence pockets come later. Prior art (EXPLORE-QP-1 screen):
fermion bags, Friedberg-Lee, nonlinear Dirac quantum-walk solitons, Thirring QCA bound states, Nordstrom and
the equivalence principle.
