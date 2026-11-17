# MIR-REVERSIBLE-ORDER-003: is the order held ONLY by the background, timing included, and can it be read back? (v0.1)

Status: **frozen at tag `mir-reversible-order-003-v0.1-frozen`**. 2026-11-17. Code: `order3.py` (imports the frozen
`order2.py`). Approved by the user 2026-11-17. Parent: ORDER-002 (valid; H_O, H_B, H_W 7/7).

## Questions (information-first)
1. ORDER-002's "background only" compared the movers by species. In integrable worlds, history sits in the movers' time
   shifts. Is the order still absent from the movers when exact timing is compared?
2. Is the background's order record causally effective? When a later traveller crosses the world, does what it carries
   away depend on the order that only the background held? Nothing guarantees this: two different backgrounds can answer
   a given probe identically.

## Cases (frozen, exhaustive; no sampling)
Every ORDER-002 valid, touched, persistent background-only case: 147 161, 201 94, 22s 313, 26s 39, 58s 79, 82s 50,
114s 87 (823 cases). Control: the first 100 valid touched RCA54 (rule 250) cases of ORDER-002, in stored row order.

## Part T (timing), at the readouts Delta + 1600, 2400, 3200
- Target-direction movers: sorted (species, cell position) equal in AB and BA.
- Reader-direction movers: assessable only if in both orders they are exactly {alpha, beta} (one each), or there are
  none. Each reader's displacement = its position minus its own free flight launched from the same slot, alone in vacuum.
  It must be equal for alpha (slot 1 in AB, slot 2 in BA) and for beta. Raw reader positions are NOT compared: launch
  order alone puts the first-launched reader ahead in any world.
- timing_ok = target-direction equal and reader timing 'equal' at all readouts. Cases with reader timing
  'unassessable' (readers changed species) are reported and do not count as timing_ok.

## Part R (read-back)
Third reader gamma = each reader-side species in turn (gamma may equal alpha or beta), in slot 3 = slot 1 translated by
2g = (2 v_X Delta, 2 Delta). gamma is touched if the world with gamma differs from {world without gamma + free gamma} at
2 Delta + 1600, in both orders. Read-back in (case, gamma) iff gamma is touched in both orders and the mover species
multiset differs between AB+gamma and BA+gamma at every readout 2 Delta + 1600, 2400, 3200. Since the AB and BA mover
species were equal before gamma (background-only cases), a difference means gamma carried the order out of the
background into the movers.

## Validity controls (frozen; invalid if any fails)
- V0_repro: every case is valid and its re-run coarse outcomes (movers, background, at all three readouts, both orders)
  equal ORDER-002's stored values exactly. (Pre-freeze check on 2 cases each of 147, 201, 22s and 250c: identical.)
- V_C (integrable control, 100 RCA54 cases): all valid; target-direction movers equal at all readouts in all cases; no
  reader-timing 'differ'; zero read-back; and >= 100 touched (case, gamma) pairs.

## Hypotheses (frozen; 7 eligible pairs)
- **H_T (only the background, timing included)**: >= 1 timing_ok case. Supported if >= 4 of 7. Prior: uncertain.
- **H_R (the order is read back)**: >= 1 read-back (case, gamma). Supported if >= 4 of 7. Prior: likely.
- **H_RT (both in one case)**: >= 1 case that is timing_ok AND has a read-back. Supported if >= 3 of 7. This is the
  strongest form: order held by nothing but the background, later turned into a different outgoing coherence.
- Descriptive: counts of timing_ok, tdir_ok and reader timing (equal / differ / unassessable / none); touched and
  read-back (case, gamma) pairs; fraction of cases with any read-back; per pair.

## Exposure (disclosed)
ORDER-002's coarse outcomes for all of these cases were known (that is how they were selected). Timing and read-back
outcomes were not seen. Smoke on 3 cases per rule printed validity and timing only. The V0 pre-check compared only the
already-known coarse outcomes.

## Limits
- Same coarse readout as ORDER-001/002. One third reader at a time, at one delay (2 Delta).
- Reader timing is assessable only when the readers survive as themselves.
- Read-back at the species level; mover timing after gamma is not used.

## Prior art
As ORDER-001/002. Order-independence in integrable RCA: the control reproduces it. Reading stored information with a
later probe is the SHADOW line's own method (SHADOW-003/009). New here: the bit read back is the ORDER of two earlier
events, held only by the background.
