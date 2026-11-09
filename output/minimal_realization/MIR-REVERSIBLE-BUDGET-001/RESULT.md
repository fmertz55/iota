# MIR-REVERSIBLE-BUDGET-001: result (2026-11-09)

Frozen tag mir-reversible-budget-001-v0.1-frozen (f9624d0). Erratum (prose only): docs/ICP_MIR_REVERSIBLE_BUDGET_001_ERRATUM.md
(window-3 adds invariants in 8/14 rules, not 9/14). Data: results.json, run.log; post hoc: posthoc_elastic_check.json.

## Frozen verdict: VALID; H_A not supported (6/14, 7 needed); H_A3 supported (7/14, at threshold); H_Z, H_Z3, H_W supported
- V0-V4 all pass. Closure B_in = B_out + B_res is exact in every input of all 14 pairs (none excluded). The derived
  bound V3 holds in every pair; I_B = 0 in 54s.
- H_A (w2): budget-bearing pairs 91 123 22s 26s 82s 218s = 6/14. Stated prior (not supported) held, by one pair.
- H_A3 (full): adds 37 (window-3 budget only) = 7/14, exactly at the threshold. Stated prior (not supported) failed.
  The two verdicts differ by a single pair; read them together as "about half".
- H_Z (w2): the whole record is written at zero w2 budget in 8 pairs (37 147 201 33 139 209 54s 94s; only_Z = only).
  H_Z3 (full): 7 pairs (37 drops out). Prior (supported) held.
- H_W: 1/14 (91, 0.125 bit). Prior (leaning supported) held, but only marginally.

## Per pair (bits; f_bear is all-or-none in every pair: 0 or 1)
| pair | only | bound | I_B w2/full | only_Z w2/full | bearing w2/full | I(SEG) | H_W | I(flanks) |
|---|---|---|---|---|---|---|---|---|
| 37 | 5.02 | 1.33 | 0 / 0.92 | 5.02 / 0 | no / yes | 1.12 | 0 | 2.63 |
| 147 | 3.50 | 1.00 | 0 / 0 | 3.50 / 3.50 | no / no | 0 | 0 | 0 |
| 201 | 2.47 | 0.59 | 0 / 0 | 2.47 / 2.47 | no / no | 0 | 0 | 0.34 |
| 33 | 2.47 | 0.59 | 0 / 0 | 2.47 / 2.47 | no / no | 0 | 0 | 0 |
| 91 | 1.50 | 0.38 | 0 / 0.25 | 0 / 0 | yes / yes | 0.50 | 0.125 | 0.38 |
| 123 | 0.62 | 0 | 0 / 0 | 0 / 0 | yes / yes | 0 | 0 | 0 |
| 139 | 1.75 | 0.38 | 0 / 0 | 1.75 / 1.75 | no / no | 0 | 0 | 0 |
| 209 | 1.75 | 0.38 | 0 / 0 | 1.75 / 1.75 | no / no | 0 | 0 | 0 |
| 22s | 1.05 | 0.30 | 0 / 0 | 0 / 0 | yes / yes | 0.30 | 0 | 0.30 |
| 26s | 2.47 | 0.59 | 0 / 0 | 0 / 0 | yes / yes | 0 | 0 | 0 |
| 54s | 2.50 | 0 | 0 / 0 | 2.50 / 2.50 | no / no | 0 | 0 | 0 |
| 82s | 2.47 | 0.59 | 0 / 0 | 0 / 0 | yes / yes | 0 | 0 | 0 |
| 94s | 1.50 | 0.25 | 0 / 0 | 1.50 / 1.50 | no / no | 0 | 0 | 0 |
| 218s | 1.50 | 0.25 | 0.25 / 0.25 | 0 / 0 | yes / yes | 0.25 | 0 | 0 |
Invariant-free pairs (58s 114s 143 151 154s 171 182s 186s 213 233 241): B identically 0 (window <= 4).

## What decides H_A (descriptive; species budgets in results.json)
- In most residue runs **no carrier leaves** (post hoc check, below): the colliding objects become the shadow's walls,
  so B_res = B_in. Whether a shadow is budget-bearing is then fixed by the carriers' own budgets.
  Bearing: 22s (each species +1 at w2), 26s and 82s (+1 each), 91 and 123 (R +1/-1, L +3/+1), 218s.
  Neutral: 33 147 201 139 209 (every species has w2 budget 0); 94s (R +2, L -2 cancel); 54s (w3: R -6, L +6 cancel);
  37 (w2 0, but w3 -2/-3 per species, so bearing in the full vector).
- The budget's total carries at most which species met (I_B <= bound) and never the timing, as derived. Observed I_B is
  well below the bound: 0 in 13/14 pairs at w2.
- Walls: segment budgets often split opposite (147: -1 / 0 / +1; 209: -1 / +1; 94s: -2 / +2; 218s: half-integers),
  which was the stated guess for neutral totals. Segment budgets carry some bits (37 1.12, 91 0.50, 22s 0.30, 218s 0.25),
  but once the flanking domain phases are known they carry nothing more, except 91 (0.125 bit).

## Post hoc (disclosed; not frozen): the elastic readout, and carrier survival
budget1_elastic_posthoc.py -> posthoc_elastic_check.json. Pass-through (residue-free) runs register as elastic, so
the frozen elastic_frac = 0 is real: no shadow run returns the incoming species unchanged. Outgoing carrier count in
residue runs: 0 in all residue runs of 147 22s 26s 54s 82s 91 94s 123 218s; 0 or 1 in 139 and 209 (32 runs with one
survivor each); 0 or 2 in 33 and 201 (32 runs with two); 37: 173 zero, 14 one, 1 two. So "carriers versus shadow" is mostly
not a split: the shadow is what the carriers turned into.

## Reading (information-first)
A conserved budget is a label that follows the carriers. When a shadow forms, the carriers usually do not leave. They
become the walls of a new domain, and the shadow inherits their whole budget. The shadow is therefore budget-bearing
exactly when its carriers were (about half the pairs here). That is a fact about the carriers, not about record
keeping. The record itself (when and where the collision happened, which domain phase it set) is written into the
geometry and phase of the domain. It costs no budget in any pair (the total cannot carry timing, by V3), and in 8/14
pairs the entire record sits at budget 0. Inside the shadow the budget sits on the walls, often as equal and opposite
amounts. Beyond what the domain phases already say, the walls' budgets add a record bit in one pair only (91, 0.125 bit).
Records are budget-free. Budgets are carried along by the coherences that make the record, but they are not the record.

## Lay version
Think of a conserved quantity as money each traveller carries. When two travellers collide and leave a mark, they
usually do not walk away. They turn into the edges of the mark, and the mark ends up holding exactly the money they
brought, which is often none. The mark's memory of when and where the collision happened costs no money at all.
Marks made by penniless travellers remember just as much as marks made by rich ones. Money is bookkeeping; memory is shape.

## Limits
Additive invariants up to window 3 only (window 4 counted, not extracted). One input ensemble per pair (SHADOW-009).
The segment split uses w2 only, with background stretches of at least 16 cells and period at most 8. The H_A and H_A3
verdicts sit on the threshold.

## Addendum (post hoc, not frozen): the one wall-budget bit, rule 91
Script budget1_91_posthoc.py; outputs posthoc_91.json, posthoc_91_states.npz, posthoc_91_walls.png.
- H_W's 0.125 bit is one bit in one class: species pair (R0, L0), the 32 even offsets 24..86 (odd offsets leave no
  residue). Outcome, single homogeneous interior (cell state 1) and total budget (4, 0) are identical across the class.
  The walls split the budget two ways, alternating with offset mod 4: left (3, 1) / right (1, -1) at 0 mod 4, and
  left (1, 1) / right (3, -1) at 2 mod 4. 1 bit x 32/256 of the inputs = 0.125 bit.
- Picture: the domain is asymmetric. One wall moves at 1/3 (the carriers' speed) and one at 1/9 (measured exactly at
  offset 24: -1/9 and +1/3). The bit is which side the fast wall goes. The fast wall carries first component 1 and the
  slow wall 3; the second component (+1/-1) marks the side. The budget labels the two wall species.
- Cause: not the vacuum clock (vacuum period 3; contact tick = 2 mod 3 for every offset). Both carriers have period 6
  and shift 2 per cycle; offset +2 delays contact by 3 ticks, i.e. half a carrier cycle. The internal phase in which the
  carriers meet decides which way the domain drifts, and with it which wall holds the extra (2, 0).
- Reading: here the budget's distribution does track a record bit, but only because the bit chooses between two wall
  species that have different budgets. The same bit is also written in the geometry (drift direction, wall positions).
  The budget is a label on the coherences that hold the record, not an independent store.
