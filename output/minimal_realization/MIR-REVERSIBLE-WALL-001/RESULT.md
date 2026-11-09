# MIR-REVERSIBLE-WALL-001: result (2026-11-09)

Frozen tag mir-reversible-wall-001-v0.1-frozen (619a8bd). Data: results.json, run.log, wall001_ledger.png.
Run: 4 min 43 s, 4 workers.

## Frozen verdict: VALID. H_1 not supported (3/7). H_T not supported (3/7). H_I not supported (0/7).
- V0-V5 all pass (V0: n, rec and word counts equal INVENTORY-001 in 28/28; covariance controls pass in every tracked pair).
- Eligible (one static wall in every shadow run, rec > 0): 147 201 22s 26s 58s 82s 114s (n_E = 7; need 4).
- H_1 (one stationary wall holds the whole record, r_W = 0): 147 201 22s. Not 26s, 82s (0.584 bit left), 58s, 114s (1.413).
- H_T (clock holds timing beyond placement): 147 (0.227 bit), 58s, 114s (0.482 each). 0 elsewhere.
- H_I (internal state alone): none. r_clock / rec: 147 2.18/3.5, 201 1.55/2.47, 22s 0.47/1.05, 26s, 82s 2.09/2.47,
  58s 4.93/6.31, 114s 4.50/5.69.

## Ledger of the record (bits; eligible pairs; exact)
| rule | rec | placement | sub-species beyond placement | clock beyond placement | only in moving outer walls |
|---|---|---|---|---|---|
| 147 | 3.5 | 2.566 | 0.707 | 0.227 | 0 |
| 201 | 2.469 | 1.896 | 0.573 | 0 | 0 |
| 22s | 1.047 | 0.922 | 0.125 | 0 | 0 |
| 26s | 2.469 | 1.885 | 0 | 0 | 0.584 |
| 58s | 6.314 | 4.418 | 0 | 0.482 | 1.413 |
| 82s | 2.469 | 1.885 | 0 | 0 | 0.584 |
| 114s | 5.689 | 3.793 | 0 | 0.482 | 1.413 |
r_allwalls = 0 in all 7: the wall set holds the whole record. r_outer (outer walls without the static wall) = 0 in 6/7
(147: 0.25). Static-wall orbit periods: 26s, 82s P = 2; 58s, 114s P = 3; 147 8 and 12; 201 4, 8, 12; 22s 4 and 12.

## Descriptive
- No-static-wall pairs (33 123 139 209 94s 218s): the two outer edges together hold the whole record (r_outer = 0); either
  edge alone does not (right edge leaves 0.625-2.125 bits; left 0-0.25).
- The clock is short: P = 2 or 3 in four rules, so it can hold at most 1-1.58 bits, and holds 0.482 beyond placement
  only in 58s/114s. Where several sub-species exist (147, 201, 22s), the static wall is sufficient; with one
  sub-species, it is not.

## Reading
The static wall does not keep the collision's timing in its internal phase. It keeps mainly *where* the contact
happened (placement, 67-88% of the record), plus which sub-species of wall formed. Its clock adds a fraction of a bit
in three rules, and the clock alone never suffices. In four of seven rules, part of the record (0.58-1.41 bit) is
absent from the stationary wall and present only in the moving outer walls. Their positions are place plus
velocity times age, so a moving edge registers *when* as well as *where*. In every rule the outer walls alone hold the
whole record except 147. Information-first: a stationary bound state remembers place; a record of time needs a
moving boundary, or a clock with a period long enough to hold it, and these walls' clocks are short.
Caveats: offset is the only input parameter, so contact place and time are not varied independently; "placement" and
"timing" here are the two coordinates of one family of contacts. The clock is defined against absolute time.

## Lay version
After a collision, the fixed seam at the centre mostly remembers where the collision happened. Its internal ticking
remembers almost nothing extra. In several rules the "when" lives in the expanding edges, whose distance from the seam
grows with age.
