# Directed-Percolation Persistence Literature Basis

Date reviewed: `2026-10-27`

Status: **pre-registration design evidence only; primary-source verification
pending for every item marked below**

Nothing in this protocol claims novelty for directed percolation (DP), dynamic
isotropic percolation (DyP), partial immunization, or their exponents. They are
used as externally fixed comparison classes.

## Universality and the absorbing-state transition

H. K. Janssen (1981) and P. Grassberger (1982) proposed that local dynamics with
a single absorbing state, short-range interactions, and no extra symmetry,
conservation law, or quenched disorder generically belong to the DP class
(the Janssen–Grassberger conjecture).

Design use: the applicability conditions in `reference_classes.json` and the
questions in `structural_audit.json`.

Claim boundary: the conjecture is unproven in general and is widely supported;
this protocol tests IOTA's fit to it, not the conjecture.

H. Hinrichsen, "Non-equilibrium critical phenomena and phase transitions into
absorbing states," *Advances in Physics* 49 (2000) 815,
<https://arxiv.org/abs/cond-mat/0001070>.

Design use: seed-spreading observables `P(t)`, `N(t)`, `R²(t)`; Domany–Kinzel
calibration; the list of non-DP classes (parity-conserving, conserved DP, long
memory).

Verification: pending (exponent tables and thresholds were read from secondary
sources).

## Exponent values

Wikipedia, "Directed percolation" and "Percolation critical exponents," read
2026-10-27. These tables collect the DP estimates of Jensen (series),
Grassberger and Zhang (simulation), and Wang et al. (arXiv:1201.3006), and the
isotropic and dynamic-percolation values used for DyP.

Design use: every exponent in `reference_classes.json`.

Verification: pending; secondary source. The DyP spreading values were checked
for internal consistency with the static 3D exponents
(`delta = beta/(nu d_min)` and `eta = d_f/d_min - 1 - delta`).

## Thresholds

I. Jensen, "Low-density series expansions for directed percolation I,"
*J. Phys. A* 32 (1999) 5233, <https://arxiv.org/abs/cond-mat/9906036>.

Design use: Domany–Kinzel bond and site thresholds.

Verification: pending; values `0.644700185(5)` and `0.705485(5)` were entered
from memory and must be checked against the paper before freeze.

C. D. Lorenz and R. M. Ziff, *Phys. Rev. E* 57 (1998) 230; J. Wang et al.,
*Phys. Rev. E* 87 (2013) 052107.

Design use: simple-cubic bond-percolation threshold `0.24881182(10)` for the
one-tick SIR calibration.

Wikipedia, "Percolation threshold," 3D table, read 2026-10-27: simple-cubic
site threshold `0.31160768(15)` (face neighbours, z = 6) and `0.0976445(10)`
(NN+2NN+3NN, z = 26).

Design use: the H1 reference for `IOTA-MIN-L0`, the threshold gate of
`CAL-SITE-BFS-SC-3`, and the ladder rung 1b reference.

Wikipedia, "Percolation critical exponents," read 2026-10-27: 3D Fisher
exponent `τ = 2.18906(8)` (published spread 2.186–2.1938).

Design use: the H3 cluster-tail exponent `τ − 2`.

Verification: secondary tables; primary-source check pending for all three.

## Immunization and memory

P. Grassberger, "On the critical behavior of the general epidemic process and
dynamical percolation," *Math. Biosci.* 63 (1983) 157; J. L. Cardy and
P. Grassberger, *J. Phys. A* 18 (1985) L267.

Design use: permanent immunization moves spreading into the DyP class.

Verification: pending.

P. Grassberger, H. Chaté, and G. Rousseau, "Spreading in media with long-time
memory," *Phys. Rev. E* 55 (1997) 2488.

Design use: the partial-immunization phase diagram (a DyP transition into fresh
territory, a DP transition of reinfection, and an intermediate regime of a
surviving front with a dying interior). Context for ladder rung 7 and for the
L1 analytic result; with an exact amplitude ledger, IOTA's reactivation channel
removes the absorbing state entirely, which is stronger than the
partial-immunization case.

Verification: pending; the summary is from memory and must be checked.

"Crossover from dynamical percolation class to directed percolation class on a
two dimensional lattice," <https://arxiv.org/abs/2311.06306>.

Design use: finite recovery memory (SIRS) is DP for every finite recovery time;
only the infinite-memory limit is DyP; a crossover exponent `1/phi ≈ 0.67`
governs the approach.

Verification: abstract and results read 2026-10-27.

A. B. Harris, *J. Phys. C* 7 (1974) 1671 (Harris criterion); for DP,
`d ν⊥ > 2` is required for weak disorder to be irrelevant.

Design use: the reason no clean class is registered if H1 is "budget_shifted"
(3D DP: `3 × 0.584 = 1.75 < 2`).

Verification: pending.

## Experimental status of DP

K. A. Takeuchi, M. Kuroda, H. Chaté, and M. Sano, *Phys. Rev. Lett.* 99 (2007)
234503; M. Sano and K. Tamai, *Nature Physics* 12 (2016) 249; G. Lemoult
et al., *Nature Physics* 12 (2016) 254; K. Avila et al., *Science* 333 (2011)
192.

Design use: motivation only. DP exponents have been measured in liquid-crystal
turbulence and at the onset of shear-flow turbulence; puff lifetimes in pipe
flow give a laboratory example of localized, self-sustaining organization whose
persistence is set by decay against splitting.

Verification: pending; no value from these papers enters a gate.

## Critical-point persistence (context for deferred stage R)

C. Bezuidenhout and G. Grimmett, "The critical contact process dies out,"
*Ann. Probab.* 18 (1990) 1462.

G. Kozma and S. Nitzan (2024) reduction of the dying-percolation conjecture,
and the 2026 claimed resolution reported by G. Kalai,
<https://gilkalai.wordpress.com/2026/09/03/amazing-there-is-no-percolation-at-the-critical-probability-in-all-dimensions-solved-by-ai-via-a-conjecture-of-gady-kozma-and-shahaf-nitzan/>.

Design use: motivation for the deferred noise-sensitivity hypothesis only. The
2026 claim is unverified and is not used in any gate.
