# Exploratory quick probe (2026-11-18; not pre-registered): one table bit away from Rule 54

Rules: 250 (Bobenko RCA54, integrable) and its 8 one-bit neighbours (250 XOR 2^k). Species: SPECIES-001 acceptance.
ORDER-002 machinery (order2.py, unchanged), 50 sampled cases per side (seed [7, w, side+1]). Bits per touched case.

| rule | species | order L / R | background L / R | background-only |
|---|---|---|---|---|
| 250 (RCA54) | 30 | 0.00 (L only) | 0.00 | 0 |
| 251, 248, 234 | 0 | no movers: untestable | | |
| 254 | 6 | 0.36 / 0.18 | 0 / 0 | 0 |
| 242 | 12 | 0.96 / 0.96 | 0.96 / 0.96 | 0 |
| 218 | 74 | 0.94 / 0.90 | 0.59 / 0.55 | 0 |
| 186 | 12 | 0.92 / 0.92 | 0.88 / 0.92 | 0 |
| 122 | 56 | 0.93 / 0.98 | 0.28 / 0.33 | 0 |

Reading (exploratory): every testable one-bit step from integrability breaks order-blindness (5/5). In 4/5 the background
records the order, mostly in full. 254 breaks only through the movers. With 50 cases there is no background-only case.
