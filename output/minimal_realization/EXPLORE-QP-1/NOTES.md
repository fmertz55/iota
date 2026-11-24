# Quasi-particle quick probe (exploratory, NOT pre-registered) — 2026-11-24
Script qp_probe.py (hold test); run2/run3 variants (kick, drift toward slow clocks, travelling glue) were run in-session with the same
update rule plus optional kick phase exp(ikx), travelling glue (Laplacian, speed c) and lapse arms.
1D mean field, L 4096, packet sigma 20, vacuum standing entry a0, glue strength G (static pocket chi = a0 - G*S).
Prior-art screen: 15 OpenAlex queries, hits in qp_prior_art_hits.csv (Thirring QCA 2018, nonlinear Dirac QW solitons
2015/2019, self-trapped QW 2020, Gross-Neveu fermion bags, Friedberg-Lee/non-topological solitons, Nordstrom & EP 2011).
Results
- Silent vacuum (a0 = 0): no pocket for any G (held 23-34%, = free spreading). Movers cannot be held without a gap.
- Standing entry a0 = 0.2, stay-glue, mu 0.1: G 0.5 holds 99.2% at T 4000 (free 12.9%); clock 0.1941 vs bare 0.2015.
  Stronger glue (G >= 1) shrinks then radiates (held 89%, 75%). G 5-100 collapse to lattice scale (first pass, discarded).
- Kick: pocket moves as one piece (held 99%), speed linear in kick.
- Fair drift toward slow clocks FAILS: stay-glue pocket drifts toward slow clocks at a/g 1.131 vs bare 0.972 (law 0.987); travelling glue G 0.5: 1.03,
  G 1: 1.31, G 2: 2.1. Drift toward slow clocks tracks 1/(push/clock): the pocket is easier to push than its clock rate says.
  Lapsing the glue too ('all') changes nothing: gravity acts only through the coin, so the glue notebook's cycling never feels the slope.
- Spring mu 0.5 resonates with the clock (2*a0 = 0.4) and breaks the pocket; discarded.
Reading: a quasi-particle (self-held, moves as one, own clock) forms only on a vacuum with a standing entry. Its
"weight" (clock) and "push-resistance" disagree, increasingly with glue strength, so it does not drift toward slow clocks fairly.
Mean field single coherence; glue-notebook cycling has no route to gravity; diagnosis of the push anomaly open.

## Step 2 (fair weight), same day
- Push-resistance vs total ticking rate (coherence clock + glue-notebook cycling), travelling glue c 0.995: push/ticking = 0.965 (G 0.5), 0.777 (G 1)
  at a0 0.2; independent of kick size. Continuum check (a0 0.2 -> 0.1 -> 0.05, same pocket shape): G 0.5: 0.965 ->
  0.985 -> 0.993; G 1: 0.777 -> 0.891 -> 0.972. Gap is a lattice-step artefact; in the continuum push-resistance = total ticking rate.
- Fair-drift rule (gravity slows the glue notebook's spring and mark-passing too): pocket drift toward slow clocks / bare law:
  G 0.5: 1.034 -> 0.999 -> 0.987; G 1: 1.244 -> 1.068 -> 0.958 (a0 0.2, 0.1, 0.05). Letting gravity slow the glue notebook too shifts drift toward slow clocks
  by only 0.2-1%. Near the continuum the drift toward slow clocks is within a few % of fair, BUT the measurement is not precise:
  at a0 0.05 it moves 0.98 -> 0.89 with starting width and fit window (starting packet is not the exact pocket;
  breathing and shedding bias the centroid). Bare-packet drift toward slow clocks at small a0 unusable (spreads); bare law used.
Next: prepare exact stationary pockets (relaxation) before any frozen fair-drift test.

Vocabulary: 'energy' here = total ticking rate (coherence clock + notebook cycling), the tally the rule keeps fixed; 'inertia' = push-resistance (kick / speed gained). Neither is a primitive.
