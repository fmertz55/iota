# GOLD-001 (v0.1): notebook gravity and the gold number
Status: **draft, to be frozen at tag `gold-001-v0.1-frozen`**. 2026-11-24. Code `src/quantum_gold/gold001.py`
(`python gold001.py check` = validity only; `run` = all outcomes). Parent: EXPLORE-GOLD-STAGE1 (exploratory).
## Model (fixed)
Rung-1 Dirac QCA (coin-then-shift) + one notebook value phi per cell. Discrete Lagrangian
L = sum 1/2(phi_{t+1}-phi_t)^2 - 1/2(phi_{x+1}-phi_x)^2 - kappa*eps*phi*S, S = 2Re(R*L); hbar = tick = cell = 1.
One shared term: turn angle eps(1+kappa*phi); notebook source kappa*eps*S. BUSY CASHIER (marks passed to neighbours,
1 cell/tick) is the source arm; HEAVY MEMORY is re-tested only as the negative control. Dial kappa = 2e-3, not fitted.
Lump ("Earth") = mean field of n_E coherences (eps_E = 1.0, sigma 150) sized so the field slope is g = 1.5e-5.
Quantum notebook (stage 2): the cashier rule is linear, so its exact quantum form is one oscillator per cell;
each branch leaves a coherent notebook state; r_note = exp(-G), G = sum_k |Delta a_k|^2/(4 sin|k|) (k != 0, pi),
leading order in kappa with each branch's mean source.
## Stage 1: does the cashier make gravity? (new settings; tests eps 0.04/0.12/0.25, sigma 200, D 900/1400, T 3500)
- V1: forward-back round trip < 1e-9 (both arms); field exactly 0 outside the lump's light cone.
- H1-SLOW: after the news arrives, N(lump) < N(test) < 1 at every sample, all 6 cashier runs.
- H1-FALL: momentum-law factor lambda (dp/dt = -eps dN/dx, v = p/tan(eps N)) in [0.97, 1.03], all 6 runs;
  and |displacement| <= 0.01 cell until 600 ticks before the news can arrive.
- H1-MEM: heavy memory at D = 1400 moves < 2% of the cashier displacement for all 3 eps, and N(lump) < 0 at T.
## Stage 2: interferometer near the lump; the gold number (eps0 = 0.3, sigma 100, D 1000)
Branch A stays; branch B gets momentum kicks +,-,-,+ at t = 0, t1, t1+Th, 2t1+Th (t1 = 800, Th = 1400) for group
speed v in {0.05, 0.1, 0.2}; read out at recombination t = 3000. Runs: 3 with no clock (delta = 0), 3 with clock
eps0 +/- 0.02, 1 with sigma 150 (v = 0.1). Clock part = r_space_clock (atom overlap); notebook part = r_note.
- V2: free-evolution invariant error < 1e-10; r_space_clock >= 0.95 in delta = 0 runs; cutoff share of G < 1e-2.
- H2-GOLD: G > 1e-10 after recombination in all 3 delta = 0 runs (a which-path record survives recombination).
- H2-SCALE: log-log slope of G vs max separation over the 3 delta = 0 runs in [1.6, 2.6]
  (dipole radiation predicts 2; proper-time monopole may raise it).
- H2-WL: worldline formula (point charges at branch centroids, Gaussian form factor) within 10% of lattice G, all 7.
- H2-SPLIT: |r_total - r_space_clock * r_note| <= 1e-3, all 7.
Descriptive: theta; G vs clock loss; G during hold vs after recombination; sigma sensitivity.
## Stage 3: ruler and Folman comparison (3D continuum, same coupling, worldline formula validated by H2-WL)
Ruler (b): 3D static field gives G_Newton = kappa^2 c^5 tau^2/(4 pi hbar), so the tick tau = sqrt(4 pi) t_P / kappa;
kappa in {1e-6, 1e-3, 1}. Benchmark: Rb-87 closed loop (+a, -a for 2T1, +a), max separation 1.4 um, max relative
speed 19 mm/s (Amit et al., PRL 123, 083601, 2019). G_3D = (m/m_P)^2/(6 pi) int w^3 |dX(w)|^2 dw, cut at pi/tau.
- V3: loop closure |A(w->0)| / (a T1/c) < 1e-6.
- H3: G_3D < 1e-30 for every kappa (Folman-class visibility resolution ~1e-2): the cashier gold number is
  unmeasurable in atom interferometers. Descriptive: kappa dependence of G_3D.
## Expectation (stated before running; not a hypothesis)
Stage 3 reduces to scalar-gravity radiation decoherence, about (m/m_P)^2 (dv/c)^2, roughly 1e-55; kappa should drop out.
## Exposure
EXPLORE-GOLD-STAGE1 outcomes are known (other settings). Stage-2/3 code was debugged on development settings outside
this grid (t1 = 300, Th = 400, D = 700, v = 0.07, clock delta 0.03; stage 3 with 1.0 um / 10 mm/s): G = 5.0e-5,
worldline within 1.2%, G_3D = 1.6e-56. A check run on the frozen settings printed validity only.
## Limits
1D lattice for stages 1-2; mean-field lump; branch-mean source (ignores each packet's own spread; sigma run is a
probe of this). Stage 3 is a continuum formula, not a 3D lattice run. Scalar (Nordstrom-type) gravity: light does
not fall. Field-radiation decoherence is prior art (e.g. Blencowe 2013; Danielson, Satishchandran & Wald 2022;
cited from memory, not checked). 1D artefact: N drifts down uniformly at rate g.
