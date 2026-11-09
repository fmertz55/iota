# Records are budget-free: what a collision's shadow keeps, and where (write-up, 2026-11-09)

For collaborators. Lay summary first, technical account second. Every number below is copied from a frozen result:
BUDGET-001 (tag mir-reversible-budget-001-v0.1-frozen, result output/minimal_realization/MIR-REVERSIBLE-BUDGET-001/RESULT.md),
WALL-001 (mir-reversible-wall-001-v0.1-frozen, 619a8bd / 4862053, 3195a38) and WALL-002 (mir-reversible-wall-002-v0.1-frozen,
38bbd89 / d2521b0). The rule-91 wall analysis and the elastic/carrier-survival check are post hoc and are marked as such.
Statements labelled *derived* are proofs or lemmas, not measurements.

## Lay summary

Two travelling objects collide in a reversible one-dimensional world and leave a lasting mark (a *shadow*). The world
has nothing like friction, so the mark is a genuine memory of the collision: from it you can recover part of what
happened. Some of these worlds also have conserved quantities, like money each traveller carries.

1. **Memory costs no money.** Within a given kind of outcome, the money left in the mark can only tell you *which*
   travellers met, never *when* or *where*. This is a theorem. In 8 of the 14 worlds that have money, the mark's
   whole memory sits at zero money. The 11 worlds with no money at all make marks just as readily.
2. **The travellers become the mark.** They usually do not walk away. They turn into the mark's edges, and the mark
   simply inherits whatever money they brought.
3. **Where the memory lives.** Where the mark has a fixed seam, the seam remembers *which collision* happened, in the
   sense of when-and-where. In this setup the two cannot be told apart, because a later collision is also a
   collision further along. The expanding edges add *who* collided, and in two worlds a little about the step the
   travellers were in. The edges never add anything about the time.
4. **What symmetry adds (not yet measured).** If place and time could be varied separately, a fixed seam could keep
   the time only up to its own short beat. The edges, whose distance from the seam grows with age, could keep it in
   full.

Money is bookkeeping. Memory is shape.

## Technical account

### Setting
Second-order (reversible) cellular automata, carriers (gliders) launched toward each other at a set of relative
offsets over a uniform input ensemble, as in SHADOW-009 (pair labels, species lists and inputs as defined there;
N = 16384, 256 or 64 inputs per pair). A *shadow* is the residue left after the outgoing carriers are erased. The
*record* is `only = H(in | O)`, the input information that survives in the residue given the outcome class O.
*Budgets* are the exact additive invariants of BUDGET-000: the window-2 basis ('w2', primary) and the window-3
additions ('full'). The vacuum density is 0 in every phase, so ring totals are gauge-free. Of the 25 shadow pairs,
14 belong to rules with invariants and 11 to rules with none (window <= 4).

### 1. The bound (derived, frozen as validity control V3)
Closure holds exactly: B_res = B_in(ri, li) − B_out(O), checked in every input of all 14 pairs. Inside an outcome
class the residue's total budget is therefore a function of the incoming species pair alone:

    I(in; B_res | O) <= H(ri, li | O) <= 2 bits,   and = 0 with one species per direction.

The offset bits of the record, meaning contact place and time, are budget-free for every additive invariant at
every window. Only the *distribution* of budget inside the residue can escape the bound.

### 2. What the budget actually carries (BUDGET-001, frozen)
- The bound is far from tight. I_B = 0 in 13/14 pairs at w2 (218s: 0.25 bit). In the full vector it is nonzero in
  three pairs: 37 (0.92), 91 (0.25) and 218s (0.25).
- In 8/14 pairs the entire record is written at zero w2 budget (37 147 201 33 139 209 54s 94s; H_Z supported).
  In the full vector this holds in 7/14 (37 drops out).
- About half the shadows carry nonzero budget (6/14 at w2, 7/14 full). H_A not supported, H_A3 at threshold;
  the two verdicts differ by one pair. f_bear is all-or-none in every pair.
- Invariant-free rules hold shadows as readily. The stored medians for `only` are 2.50 bits (11 invariant-free) and
  2.11 bits (14 invariant). This comes from stored data and was not tested. Records need no additive budget to exist.

### 3. Carriers become walls (post hoc, disclosed)
Outgoing carrier count in residue runs is 0 in every residue run of 147, 22s, 26s, 54s, 82s, 91, 94s, 123 and 218s.
It is mostly 0, and at most 2, in the rest. No shadow run returns the incoming species unchanged (the frozen
elastic fraction of 0 is real). So "carriers versus shadow" is mostly not a split: the colliding coherences turn
into the walls of a new domain, and B_res = B_in. Whether a shadow is budget-bearing is a property of its carriers,
not of record keeping. Neutral carriers give neutral shadows, for example 94s (R +2, L −2) and 54s (w3: R −6, L +6).

### 4. Wall budgets: one bit, and it is a label (BUDGET-001 H_W; rule-91 addendum post hoc)
Inside a shadow, the budget sits on the walls, often in equal and opposite amounts (147: −1 / 0 / +1; 209: −1 / +1;
94s: −2 / +2). Once the flanking domain phases are known, the segment budgets carry no further record bit, except in
rule 91 (H_W = 0.125 bit, 1/14).

That 0.125 bit is one bit in one class: species pair (R0, L0), 32 even offsets, 32/256 of the inputs. The domain is
asymmetric, with one wall at speed 1/3 and one at 1/9. The bit is which side the fast wall goes. The fast wall
carries budget first-component 1 and the slow wall carries 3, so the wall budgets alternate with offset mod 4:
left (3, 1) / right (1, −1), or left (1, 1) / right (3, −1). The cause is the carriers' internal phase at contact
(period 6; offset +2 delays contact by half a cycle), not the vacuum clock. The same bit is written in the geometry
(drift direction). The budget labels which wall species formed. It is not an independent store.

![Rule 91: the record bit is which way the fast wall goes; budgets ride on the two wall species](../output/minimal_realization/MIR-REVERSIBLE-BUDGET-001/posthoc_91_walls.png)

*Figure.* Rule 91, species pair (R0, L0). (a) Offset 24: the fast wall goes right. (b) Offset 26: the fast wall goes
left. Labels give the w2 budget of each wall. The total budget (4, 0) and the interior are identical in both panels.

### 5. Where the budget-free record lives: static wall versus edges (WALL-001, WALL-002, frozen)
Seven pairs have one static wall in every shadow run (147 201 22s 26s 58s 82s 114s). These include invariant-free
pairs, so this part of the line holds whether or not there is a budget. Splitting the record by channel (WALL-002,
exact):

| rule | rec | species pair c_sp | contact coordinate c_off = phase + translate | edge-only R_E | of which species / phase / age |
|---|---|---|---|---|---|
| 147 | 3.5 | 1.0 | 2.5 | 0 | 0 / 0 / 0 |
| 201 | 2.469 | 0.594 | 1.875 | 0 | 0 / 0 / 0 |
| 22s | 1.047 | 0.297 | 0.75 | 0 | 0 / 0 / 0 |
| 26s | 2.469 | 0.594 | 1.875 | 0.584 | 0.584 / 0 / 0 |
| 58s | 6.314 | 1.439 | 4.875 | 1.413 | 1.171 / 0.242 / 0 |
| 82s | 2.469 | 0.594 | 1.875 | 0.584 | 0.584 / 0 / 0 |
| 114s | 5.689 | 1.439 | 4.25 | 1.413 | 1.171 / 0.242 / 0 |

- **The record is mostly contact coordinate (71-77%) plus species pair (23-29%).** H_C0 (the record names no contact)
  is not supported in 0/7.
- **The static wall's placement names the contact.** Inside a contact class (species pair, contact phase), offsets
  differ by a translate k: contact k·τ later and v_R·k·τ further right. Place and time move together, so the wall's
  position holds them as one coordinate. The static wall holds all the record's age inside a class (W_age = c_k in
  all 7). Its position says almost nothing about species (0.01-0.17 bit).
- **The edges hold "which", never "when".** What only the moving outer walls hold is the species pair (all of it in
  26s and 82s, 1.171 of 1.413 bit in 58s and 114s). In 58s and 114s they also hold 0.242 bit of contact phase.
  Age held only by the edges is J_k = 0 in all 7, as the translate lemma predicts.
- This corrects the earlier reading (WALL-001, handoff 11-09e) that "the static wall keeps place, the edges keep age".
  In this ensemble, offset is the only input parameter, so place and age are not separate channels.

### 6. Place/age separation (derived: translate lemma, WALL-002 contract (c); checked exactly, V_L 1728/1728)
Every wall obeys: same sub-species, clock + k·τ mod P, place + k·τ·(v_R − u). Hence, *if* contact place and time were
varied independently, a static wall (u = 0) could hold contact age only as k·τ mod P, which is at most log2 P bits:
1 bit for 26s and 82s (P = 2), 1.58 bits for 58s and 114s (P = 3). A moving edge's distance from the wall grows with
age and holds it without bound. This is a statement about what the channels *can* hold. It has not been measured.

## Synthesis (information-first)
A conserved budget is a label that follows coherences. It does not store where information went. When two carriers
meet and a record forms, the carriers become the record's walls and carry their budget into it unchanged. The
record's content (which contact, which species) is written in geometry: the wall's position for the contact
coordinate, and the edges for the species pair. The total budget cannot hold the contact coordinate at all (§1).
In practice it holds almost none of the species information either (§2). Its distribution adds a bit only where the
bit already chose between two wall species with different labels (§4). The constraint on reachable records comes
from geometry and symmetry (§6), not from the budget.

## Limits
- Additive invariants up to window 3 only (window 4 counted, not extracted). Non-additive invariants and invariants
  beyond window 4 are not excluded.
- One input ensemble per pair, with offset as the only parameter. The place/age split (§6) is derived, not measured.
- §5 covers the 7 one-static-wall pairs only. In the six no-static-wall invariant pairs the two outer edges together
  hold the whole record (WALL-001, descriptive).
- H_A and H_A3 sit on the threshold. §3 and §4 are post hoc.

## Possible next test (not scheduled; listed for value)
An ensemble that varies contact place and contact time independently, for example by varying both launch positions,
would turn §6 from a lemma into a measurement. The prediction is that a static wall's age information saturates at
log2 P while the edges' age information keeps growing.
