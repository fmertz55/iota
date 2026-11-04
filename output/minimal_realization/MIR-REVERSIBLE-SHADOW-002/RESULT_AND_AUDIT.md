# MIR-REVERSIBLE-SHADOW-002: result (2026-11-04)

## Frozen result
- Control valid: in all 13 rules with no shadow, the probe's footprint carries 0 bits.
- H_S `typical`: in 12/12 shadow rules the probe's future depends on the erased collision
  (I = 3.5-5.0 bits of 6). Rule 37 is not an exception.
- H_C `supported`. In 12/12 shadow rules the capacity ratio is exactly 1.0: one probe pass reads
  *all* the information that only the shadow held (1.8-4.2 bits per rule, the ledger's background share).
  Together with the carriers' record (before erasure), it fully determines the original collision.

| rule | only the shadow knows (bits) | probe reads beyond carriers (bits) |
|---|---|---|
| 33, 139, 147, 201, 209 | 2.5 | 2.5 |
| 37 | 3.116 | 3.116 |
| 143 / 171 / 213 / 241 | 1.814 / 1.984 / 1.888 / 1.91 | same |
| 151, 233 | 4.189 | 4.189 |

## Limits (stated before interpretation)
- Y is the probe's *whole footprint* on the future (the world with the probe XOR the world without it),
  not the state of the probe coherence alone. The claim is that the shadow fully constrains the reachable
  future that the probe's passage opens. Whether the probe coherence itself leaves carrying the record is
  a separate, untested question.
- The entropies are exact for this ensemble (64 offsets, deterministic dynamics). They are not
  estimates of a capacity over all possible collisions.
- All 12 shadow rules have an active vacuum (f(000)=1). One collision pair per rule was tested.

## Lay version
After two coherences collide, we erase them and leave only the faint mark in the background. We then
send in a fresh coherence. In every rule that leaves a mark (12 of 12), what happens when the newcomer
passes depends on the erased collision. And it depends on *all* of it: the mark held a few bits that the
departing coherences did not carry, and the newcomer's passage reveals every one of them. Where
there is no mark (13 rules), the newcomer learns nothing, exactly as it should. The shadow knows,
and it gives up what it knows when something passes through it.
