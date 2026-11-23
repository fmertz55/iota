# Prior-art review for the ORDER/BREAK/REACH paper (2026-11-23)

## Search (records in order_break_search_records_2026-11-23.csv)
- 27 OpenAlex keyword queries (25 results each): order/commutation of collisions, Yang-Baxter, integrability breaking,
  deformed Rule 54, inelastic solitons, glider collision memory, collision-based computing, information storage in
  domains, active information storage, history/path dependence, damage spreading, quantum Darwinism/redundant records,
  box-ball systems, second-order reversible CA.
- Citation chasing one step forward (up to 100 citing works) and backward (up to 100 references) from 6 anchors:
  Buca-Klobas-Prosen 2021, Lopez-Piqueres et al. 2022, Klobas-Prosen 2022, Hordijk-Shalizi-Crutchfield 2001, Pivato 2007,
  deformed RCA54 (J. Phys. A 2026).
- 994 unique records; 74 flagged by title. All 74 titles were screened; abstracts were read for the 9 highest-risk.
  Not done: Semantic Scholar; full texts.

## Established (cite, do not claim)
| Our element | Prior art |
|---|---|
| Integrable soliton interactions are pairwise and independent of collision order; order-invariance follows from the Yang-Baxter property | Ablowitz, Prinari & Trubatch, Stud. Appl. Math. 2005, doi 10.1111/j.1467-9590.2005.00320.x; Gombor & Pozsgay, SciPost Phys. 2022, doi 10.21468/scipostphys.12.3.102 |
| RCA54/RCA201 integrability, deformations, integrability breaking (charges, thermalization, transport) | Bobenko et al. 1993 (from memory, not checked); Prosen 2021, arXiv 2106.01292; Buca-Klobas-Prosen 2021; Lopez-Piqueres et al. 2022; deformed RCA54 2026 |
| Classification of reversible CA by ergodic behaviour | Sharipov, Koterle, Grozdanov et al., SciPost Phys. 2026, doi 10.21468/scipostphys.20.5.145 |
| Integrability can be generic (U(1) qubit circuits) | Žnidarič, Duh & Zadnik, PRB 2025, doi 10.1103/tqy8-ynpd |
| Domains as dominant information storage (statistical) | Lizier et al.; Wibral, Lizier et al. 2014, doi 10.3389/fninf.2014.00001 |
| Perturbation spreading / Lyapunov measures | Vispoel, Daly & Baetens 2024, doi 10.1016/j.chaos.2024.114989 (abstract unavailable) |
| Collisions writing state that later gliders read | Martínez/Adamatzky (already cited) |

## Not found (candidate contribution)
No record measures where the order of two interactions is held (movers vs background) in non-integrable reversible CA,
shows a background-only order record read back and reused by later coherences, or relates order memory and its
background share to the degree of integrability breaking across a rule neighbourhood.

## Consequences for the paper
1. Present Rule 54's order-blindness as the known Yang-Baxter result (Ablowitz et al. 2005) that our control reproduces.
2. Naming clash: second-order Wolfram 5 (f = NOR(l, r), checked) is Bobenko's RCA201, which is integrable. Our null "5"
   was exactly order-blind in ORDER-002, so it is a second integrable control. Our pair "201" is NOT RCA201. Add a
   convention table.
3. Distinguish reach (matched AB/BA, a specific held bit, integrable zero) from damage spreading (perturbation growth).
4. Lizier storage is statistical; ours is interventional with an exact control.
5. Order memory is a new observable for the integrability-breaking field; Sharipov et al. 2026 is the closest
   classification work.

## Residual risk
Title-level screen beyond the 9 abstracts read; Semantic Scholar not queried; quantum-Darwinism literature used only as
framing.
