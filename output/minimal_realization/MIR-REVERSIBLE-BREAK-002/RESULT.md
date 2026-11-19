# MIR-REVERSIBLE-BREAK-002: result (2026-11-19)
Frozen tag mir-reversible-break-002-v0.1-frozen (8ce8ad5). Run by the user in Terminal.

## Frozen verdict: VALID. H_L, H_S, H_X all supported.
- V_C: RCA54 (250) elasticity 1.00, order 0, background 0. 24 testable non-control rules (of 92 within distance 3).
- **H_L:** Spearman rho(elasticity, order bits) = -0.67, p = 3.4e-4.
- **H_S:** rho(elasticity, background bits) = -0.72, p = 6.3e-5.
- **H_X:** the split holds in 13/14 qualifying rules. The exception is 146 (elasticity 0.73, background 0.63).
- Every testable broken rule records order (0.37-1.00 bits/case). Background-only order appears only at elasticity
  <= 0.18 (82, 114, 26, 91, 58, 94, 233, 123; max 0.11 in 123).

## Reading
Moving away from integrability, worlds become order-aware. How inelastic their collisions are predicts how much order
they record, and above all whether the background holds it. Two rules (254, 50) are fully elastic by this measure yet
record order (0.37-0.44 bits) in the movers only: elastic but not order-blind, so Yang-Baxter fails without any record
being left. Elasticity is a proxy; integrability is not just elasticity.

## Limits
One substrate family (1-D second-order CA, radius 1); coarse readout; species-level movers; the elasticity measure is
ours (v2, checked only on 250 and 242 before freezing); 24 testable rules.

## Lay
Starting from the "perfect" world and changing its rule a little at a time, every world we could test began remembering
who went first. The messier its collisions, the more it remembers, and the more of that memory is kept in the ground
rather than by the travellers. In the perfect world: nothing, exactly.
