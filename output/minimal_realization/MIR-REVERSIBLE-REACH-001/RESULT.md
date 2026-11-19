# MIR-REVERSIBLE-REACH-001: result (2026-11-19)
Frozen tag mir-reversible-reach-001-v0.1-frozen (7769b45). Run by the user in Terminal.

## Frozen verdict: VALID. H_R supported 7/7, H_P supported 7/7.
- V_C: RCA54 reach 0 in 100/100 cases; background never differs. All 588 + 100 cases valid.

| pair | cases | mean reach (of 6) | background still differs after 6 |
|---|---|---|---|
| 114s | 58 | 5.81 | 100% |
| 58s | 69 | 5.52 | 100% |
| 82s | 43 | 5.14 | 100% |
| 26s | 34 | 5.03 | 100% |
| 201 | 73 | 4.38 | 97% |
| 147 | 143 | 3.61 | 100% |
| 22s | 168 | 2.67 | 100% |
| RCA54 | 100 | 0 | 0% |

## Reading
A single order distinction, held at the start only by the background, conditions on average 2.7-5.8 of 6 successive
fresh encounters, and the background keeps it throughout (97-100%). The record is neither consumed nor erased by
reading. It is reused.

## Caveat (mechanism)
Before the first traveller, the movers are identical in AB and BA, so every difference originates in the background.
After the first affected encounter, later differences can also propagate through that traveller's products, so reach
counts total downstream influence originating in the background, not background-to-traveller transfers alone.
Separating the two (later travellers that never meet earlier products) is a follow-up. Redundancy (how many outgoing
travellers each reveal the order on their own) was not measured.

## Lay
One footprint that alone remembers who went first changed what came out of most of the next six travellers, and the
footprint was still there, unchanged in what it remembered, afterwards. In the perfect world: no footprint and no
effect, in all 100 cases.
