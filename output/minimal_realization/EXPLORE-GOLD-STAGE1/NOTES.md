# GOLD rung 2 — stage-1 quick probe (exploratory, NOT pre-registered) — 2026-11-24

Script: stage1_probe.py (run `python stage1_probe.py`, ~40 s). Figure: stage1_probe.png.
Setup: rung-1 Dirac QCA + one notebook value phi per cell, mean-field (classical) in stage 1.
One shared handshake term: turn angle = eps(1 + kappa*phi); notebook driven by -kappa*sum n*eps*2Re(R*L).
CASHIER: marks passed to both neighbours each tick (Courant-1 lattice wave rule). MEMORY: same, no passing.
Lump: n_E = 16.67 coherences, eps_E = 1.2, sigma 150, at x = 2048; kappa = 1e-3 (chosen so g = 1e-5).
Tests: eps = 0.05/0.1/0.2 at D = 800/1200; control = same test with no lump. L = 8192, T = 4000.

Results
- Reversible: forward 1500 + back 1500 returns the start to 1.5e-12 (cashier), 4.6e-11 (memory).
- Speed limit: field exactly 0 outside the lump's light cone (compact-support lump, 1200 ticks).
- CASHIER: clocks slow near lump (N = 0.961 at lump, gradient 9.99e-6 = predicted kappa^2 n_E eps_E S/2).
  All tests fall toward the lump; nothing moves before the news arrives (|disp| <= 1.1e-4 at t = D-600).
  Displacement at T (D=800): -52.18, -52.33, -51.89 cells for eps 0.05/0.1/0.2 (spread 0.85%).
  Matches momentum law dp/dt = -eps dN/dx, v = p/tan(eps N): fit factor 0.989-0.999.
  Sign (attraction) is fixed by the single shared term, not chosen. Test self-sourcing changes accel by 0.02%.
  1D artefact: N drifts down uniformly at rate g inside the cone (N_lump = 0.9609 at T = 4000 = 1 - gT).
- MEMORY: no fall at a distance (D=1200: |disp| 0.5/0.013/0.002 cells vs ~40 for cashier); D=800 motion
  is tail capture, not fall. Pile-up: N at lump hits 0 at t = 3225, reaches -1.30 at T. Test coherences dig
  their own wells and narrow (width -0.4/-5.4/-12.0 cells vs control): self-trapping.

Reading: the cashier arm is a lattice scalar (Nordstrom-type) gravity — textbook physics, so stage 1 is
groundwork (silver-grade), not gold. Heavy memory fails by locality: marks that stay put cannot reach
a distant clock. Prior-art screen for this exact coupling was 2 web searches only (Arrighi/Di Molfetta
curved-space walks; walker-driven dynamical triangulations); full screen at contract stage.
