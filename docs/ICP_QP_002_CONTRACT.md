# QP-002 (v0.1): node-only held pairs, their exact clock law, and their size in the smooth limit
Status: **draft, to be frozen at tag `qp-002-v0.1-frozen`**. 2026-11-25. Code `src/quantum_gold/qp002.py`
(`check` = validity only; `run` = all outcomes). Parent: EXPLORE-QP-2 route B (exploratory, NOTES.md steps 1-4).
Vocabulary: clock = turns per tick; pair speed K = total phase-wind per node; gap = nodes between the two parts;
held = the two parts stay a finite number of nodes apart. No mass, energy or force terms.
## Rule (fixed, zero penalty flags)
Node x = two yes/no slots (R_x, L_x). One tick = (1) edge exchange on (L_x, R_{x-1}) with one-coherence block
[[-i mu, n],[n, -i mu]], n = sqrt(1-mu^2), both-full left unchanged; (2) in-node swap R_x <-> L_x, both-full
gets phase e^{i theta}. Ring of N nodes. Only node slots exist: no notebook layer, no supplied field, no mean field.
Rule constants: mu (supplied) and theta. Exact two-coherence sector (two full slots), split into blocks of fixed K.
Law (from EXPLORE-QP-2): cos(clock) = (1-mu^2) cos K - mu^2 cos(theta). Held state at each (mu, theta, K) = the
eigenstate nearest the law's clock (either sign). law_err = distance of its eigenvalue from e^{-+i clock_law}.
P_edge = chance the gap is within 2 nodes of the far side of the ring. s = mean gap x mu x sin(theta/2).
## Grids (none run before this freeze)
LAW: N = 160; mu in {0.35, 0.65}; theta/pi in {0.3, 0.6, 0.8}; every K = 2 pi m / N, m = 0..80 (486 cases).
SIZE: K = 0; mu in {0.24, 0.12, 0.06} on N = 160, 240, 432; theta/pi in {0.4, 0.6, 0.8} (9 cases).
## Validity
V1: two-coherence code = full 2N-qubit gate circuit restricted to two full slots (N = 4): max error < 1e-12.
V2: two-coherence tick is unitary (N = 12): error < 1e-12.
V3: the K blocks hold exactly as many states as the full sector, and reproduce its spectrum (N = 12): < 1e-10.
V4: one-coherence clocks obey cos(clock) = n cos k (N = 40): < 1e-10.
## Hypotheses
- H-HELD: at all 486 LAW cases and all 9 SIZE cases, the law state is held: P_edge < 1e-6.
- H-LAW: over the 486 LAW cases, max law_err < 1e-6 and median law_err < 1e-12.
- H-SPREAD: for each theta, the mean gap at mu = 0.06 is more than 3 times the mean gap at mu = 0.24
  (the pair gets bigger as mu gets small, while staying held).
- H-SIZE: for each theta, |s - 1/2| < 0.02 at mu = 0.06, and |s - 1/2| at mu = 0.06 is smaller than at mu = 0.24
  (small-mu size rule: mean gap -> 1 / (2 mu sin(theta/2)) nodes).
Descriptive: SIZE law errors; mean gap across all K on the LAW grid; clocks.
## Exposure
EXPLORE-QP-2 outcomes are known: the law on mu 0.2/0.5/0.8, theta/pi 0.1/0.25/0.5/0.7/0.9, five K (N 40-120);
the smooth-limit series mu 0.8-0.05, theta/pi 0.25/0.5/0.75 (N 240/360), s -> 0.50. Before this freeze a
calibration ran on exposed settings only (mu 0.5 and 0.2, theta/pi 0.25/0.5/0.7, N = 160, all K; and mu = 0.05,
theta = pi/2, N = 432, K = 0): max law_err 4.2e-7 (mu 0.2, theta 0.25 pi, largest pair), median 3.6e-15, max P_edge
5.4e-6 (same case). Thresholds were set from it; the frozen grids avoid all exposed settings. The validity checks
were run once on this code (all pass). theta near pi was avoided because there the pair's clock nears zero and the
pair loosens (exploratory theta = 0.9 pi).
## Limits
Two coherences, 1D, empty vacuum; mu supplied. The size rule is a numerical fit, not derived. In an empty vacuum a
free pair can never become held and no shadow can be left (NOTES.md). The second, theta-independent edge-held pair
(cos(clock) = (1-mu^2)/(1+mu^2) cos K) is not tested here. Prior art not searched (flag: Thirring QCA bound states).
