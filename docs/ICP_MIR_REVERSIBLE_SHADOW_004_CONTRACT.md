# MIR-REVERSIBLE-SHADOW-004 — can a silent vacuum hold a shadow? (v0.1)

Status: **outcome-free; frozen at tag `mir-reversible-shadow-004-v0.1-frozen`**. 2026-11-07. Code: `shadow4.py`.
Parent: SHADOW-003 (45/45 shadow pairs, 14 rules, all with f(000)=1).

## Why this test
SHADOW-003 tested 25 rules, all with an active vacuum (f(000)=1). No silent-vacuum rule (f(000)=0,
vacuum all zeros at every tick) was tested, so "no silent shadow observed" was a sampling fact, not a
negative result.

## Exposure (before freezing)
Read only the VACUUM-COLLIDE-001 catalogue (5-wide seeds). Seen: of 128 silent rules, 55 have bounded
objects. In each rule the non-still objects are either all exactly light-speed (|v|=1, 21 rules) or
exact period-p oscillators with v=0 (no finite-speed mover). No silent rule has both still objects and
light movers in that catalogue. No silent collision, residue or shadow outcome has been computed or seen.
Timing of a random-state step loop was measured (no outcome). Smoke test before freezing: V0 path on
rule 37 (reproduced) and search() on rule 37 (active, out of scope); no silent rule was run.

## Design
Silent rules only (Wolfram code even). Same second-order dynamics, ring and readouts as SHADOW-003.
1. Seed search (wider than before). Seeds of width k=8 on both layers (65535 seeds; contains every
   narrower seed). Same acceptance as VACUUM-COLLIDE-001: ring 256, horizon 120, layer-t difference
   from vacuum nonzero and width <= 8 at every tick. Candidates with |drift| > 2 are de-duplicated by
   final pattern and given an exact orbit (collide2.orbit, PMAX 240) started from their tick-120 state,
   which (vacuum being 0 at every tick) is then the placed seed. Movers: exact v with |v| >= 1/8.
   Still targets: exact orbit with v = 0 (first 2 distinct species in seed order, from the first 64
   distinct still final patterns).
2. Per rule: R list = first 2 distinct finite-speed right-movers (1/8 <= v < 1) plus first 2 distinct
   light right-movers; L list likewise. Pairs:
   - head-on: every R x L;
   - still-target: every R with v >= 1/4 against the first still species (placed at X0 + offset).
   Stratum label: finite, light, mixed, still-target.
3. Each pair runs `shadow3.pair` unchanged (T=600 erasure, 64 offsets 24..87, probe = free R copy
   launched from one fixed site outside all shadows, 1500 ticks, N=8192, exact entropies). Only the seed
   placement function is replaced, to accept width-8 seeds.
4. Stationarity (descriptive): for each shadow pair, in the probe-free world after erasure, does the
   residue's support stay within its T-span +/- 8 cells for 300 ticks in every offset? (moving residue =
   an unresolved carrier rather than a background record.)
5. Spacetime pictures for every silent shadow pair (up to 16) and 4 clean pairs, checked before reporting.

## Validity controls (frozen)
- V0 positive control: the patched placement path, on rule 37 with its first SHADOW-003 pair
  (5-wide seeds converted), must reproduce the stored SHADOW-003 values (shadow_runs, only_shadow,
  footprint_beyond, probe_state_beyond) exactly. Else invalid.
- V1: every silent pair with no shadow gives 0 bits for both readouts. Else invalid.

## Question and hypotheses (frozen)
- Q1 primary: S = number of silent pairs with shadow_runs > 0 and only_shadow > 0.
  S >= 1 (surviving the picture check) answers "yes, a silent vacuum can hold a shadow";
  S = 0 answers "none at this depth" (silent rules, seeds <= 8 wide, <= 4+4 movers, 64 offsets).
- P (stated prior, may fail): S = 0.
- H_R (only if S >= 1): footprint ratio = 1 in >= 90% of silent shadow pairs.
- Descriptive: mover counts by stratum and speed; pairs per stratum; stationary subcount;
  probe-state ratio; linear rule 90 is expected transparent (a built-in null).
