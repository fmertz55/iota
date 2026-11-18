# MIR-REVERSIBLE-BREAK-001: result (2026-11-18)
Frozen tag mir-reversible-break-001-v0.1-frozen (3421f1f). Run by the user in Terminal.

## Frozen verdict: VALID. H_O supported, H_B supported (10/13). H_L (spine) NOT supported: rho = -0.48, p = 0.096, n = 13.
- V_C: RCA54 (250) order 0, background 0 (290 touched cases). V_slot ok. 13 testable non-control rules (of 36).
- H_O: every testable broken rule records order (0.32-1.00 bits/case).

| rule | dist | elasticity | order | background | background-only |
|---|---|---|---|---|---|
| 250 | 0 | 0.16 | 0 | 0 | 0 |
| 254 | 1 | 0.79 | 0.32 | 0 | 0 |
| 126 / 222 | 2 | 0.54 / 0.52 | 0.69 / 0.74 | 0 | 0 |
| 178 | 2 | 0.27 | 0.60 | 0.02 | 0 |
| 154 / 210 | 2 | 0.11 / 0.10 | 1.00 | 1.00 | 0 |
| 242 / 186 | 1 | 0.07 / 0.05 | 0.93 / 0.94 | 0.92 | 0 |
| 122 / 218 | 1 | 0.04 / 0.03 | 0.95 / 0.91 | 0.29 / 0.46 | 0 |
| 58 / 114 / 123 | 2 | 0.04 / 0.03 / 0.01 | 0.82-0.98 | 0.52-0.87 | 0.05-0.07 |

## Why H_L failed (post hoc)
The elasticity proxy is broken at the control: RCA54 scores 0.16 although it is exactly elastic. Its soliton packets
change shape (species id) after scattering, and pairs on opposite sublattices never meet. So the proxy mislabels the
integrable end, and order is near its ceiling (0.6-1.0) in every broken rule, which leaves little room for a rank trend.

## Post hoc pattern (exploratory; needs its own test)
The **background** share separates cleanly by elasticity: all 4 rules with elasticity >= 0.27 hold order in movers only
(background <= 0.02); all 9 with elasticity <= 0.11 hold it mostly in the background (0.29-1.00). Background-only order
appears only in the 3 least elastic rules. Reading: breaking integrability makes the world order-aware; whether the
background keeps the order depends on how inelastic collisions are.

## Lay
One bit away from the perfect world, every world we could test starts remembering who went first. Whether the ground
keeps that memory depends on how messy collisions are: clean bounces leave it with the travellers, messy collisions leave
footprints that hold it. Our "how perfect is it" ruler was faulty, so the smooth trend we predicted wasn't confirmed.
