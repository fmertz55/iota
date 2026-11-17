# MIR-REVERSIBLE-ORDER-003: result (2026-11-17)

Frozen tag `mir-reversible-order-003-v0.1-frozen` (cbced18). Run: 57.7 min, 5 workers. Data: results.json, jobs/, run.log.

## Frozen verdict: VALID. H_T, H_R and H_RT all supported, 7/7 each.
- V0_repro ✓: all 923 cases valid. Coarse outcomes are identical to ORDER-002's stored values in every case.
- V_C ✓ (RCA54, 100 cases): target-direction movers equal in all 100; no reader timing 'differ'; **0 read-backs in
  1470 touched (case, gamma) pairs**.

| pair | cases | timing_ok | target-dir equal | reader timing equal / unassessable | gamma touched | read-backs | cases with read-back | timing_ok AND read-back |
|---|---|---|---|---|---|---|---|---|
| 147 | 161 | 145 | 161 | 145 / 16 | 1288 | 592 | 159 | 143 |
| 201 | 94 | 73 | 94 | 73 / 21 | 752 | 461 | 94 | 73 |
| 22s | 313 | 272 | 313 | 272 / 41 | 913 | 238 | 184 | 168 |
| 26s | 39 | 35 | 39 | 35 / 4 | 491 | 320 | 38 | 34 |
| 58s | 79 | 73 | 79 | 73 / 6 | 474 | 347 | 75 | 69 |
| 82s | 50 | 48 | 48 | 50 / 0 | 642 | 479 | 44 | 43 |
| 114s | 87 | 64 | 85 | 66 / 21 | 522 | 403 | 81 | 58 |
| **total** | **823** | **710** | | | **5082** | **2840** | **675** | **588** |
| RCA54 | 100 | 22 | 100 | 22 / 78 | 1470 | **0** | 0 | 0 |

No case had reader timing 'differ'. Where the readers could be compared, their delays were identical in both orders.

## Reading (information-first)
1. **Timing included, the order is still held only by the background** in 710 of 823 cases (86%). The movers are the
   same species, the target-direction movers are at the same cells, and each reader is delayed by exactly the same
   amount in both orders. 113 cases could not be fully assessed (readers changed species) or showed target-direction
   differences (4 cases in 82s and 114s).
2. **The background's order record is causally effective.** A later traveller carries the order out into what it
   emits: in 56% of touched (case, gamma) pairs (2840/5082), and in 675/823 cases for at least one gamma.
3. **Strongest form, in all 7 pairs: 588 cases.** No mover (species, position or delay) distinguishes the two orders,
   yet a later traveller's outgoing coherences do. The only place the order can have been in between is the background.
4. In the integrable world (RCA54) nothing is read back, in all 1470 touched pairs, as required.

In ICP terms: what happened earlier, and in what order, constrains what a later coherence becomes. The constraint
passes through the shadow alone.

## Limits
- Coarse background words; species-level read-back; one third reader at one delay (2 Delta).
- Reader timing is assessable only when the readers survive as themselves. **In the RCA54 control, 78/100 cases were
  unassessable** (soliton packets change shape after scattering), so the control tests the reader-timing clause only
  weakly (22 cases, all equal). Target-direction equality and zero read-back are tested in full.
- One substrate family (1-D second-order CA), 7 rules. Prior-art screen only (5 queries for the order idea).

## Lay version
Two travellers take turns walking into a target, and then we swap who went first. In 588 of the cases we checked,
nothing about the travellers afterwards gives the order away: not what they are, where they are, or how much they were
delayed. Yet when a third traveller walks through later, it comes out *different* depending on who went first. The only
thing that could have told it is the footprints. In the textbook "perfect" world (Rule 54) this never happens, in 1470
tries. The footprints don't just remember who went first; they pass it on, and that changes what happens next.
