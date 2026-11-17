# MIR-REVERSIBLE-ORDER-002: result (2026-11-17)

Frozen tag `mir-reversible-order-002-v0.1-frozen` (b86c809). Confirmatory replication of ORDER-001 (INVALID) with the
mover detector fixed (WMOV 16) and a fresh sample (seed 20261116). Run in the user's Terminal; 23/23 job checkpoints.
Data: results.json (untracked, regenerable), jobs/ (untracked), run.log.

## Frozen verdict: VALID. H_O, H_B, H_W supported (7/7 each). H_N supported (evaluated by hand, see below).
- V0 ✓ (64 valid, 32 order). V_slot ✓. V_valid ✓ (1600/1600 valid in every pair; 1395-1600 touched).
- V_C54 ✓, on 772 touched RCA54 cases: no order effect at any readout, no background ever, and target positions equal in
  AB and BA at every readout (exact Yang-Baxter additivity).
- H_O: order recorded in 147 201 22s 26s 58s 82s 114s. H_B: a background-only case in all 7. H_W: a written case in all 7.
- H_N (contract hypothesis, **not implemented in order2.py's verdict code**; evaluated by hand from the frozen output
  table): nulls 1 and 5 have 0 background-only and 0 written cases → supported. Rule 1: order 0.927 bits, all in the movers.
  Rule 5: order-blind. 90s: no touched cases (uninformative, as in ORDER-001).

## Table (bits per touched case; persistent over readouts Delta + 1600, 2400, 3200)
| pair | touched | order | background holds | movers hold | background only | written cases |
|---|---|---|---|---|---|---|
| 147 | 1600 | 0.990 | 0.948 | 0.889 | 0.101 | 1384 |
| 201 | 1600 | 0.993 | 0.949 | 0.931 | 0.059 | 1370 |
| 22s | 1448 | 0.937 | 0.866 | 0.708 | 0.216 | 1229 |
| 26s | 1395 | 0.872 | 0.472 | 0.689 | 0.028 | 661 |
| 58s | 1600 | 0.825 | 0.555 | 0.638 | 0.049 | 883 |
| 82s | 1411 | 0.846 | 0.446 | 0.667 | 0.035 | 646 |
| 114s | 1600 | 0.815 | 0.529 | 0.589 | 0.054 | 857 |
| null 1 | 800 | 0.927 | 0 | 0.927 | 0 | 0 |
| null 5 | 778 | 0 | 0 | 0 | 0 | 0 |
| RCA54 (250) | 772 | 0 | 0 | 0 | 0 | 0 |

These replicate the post hoc ORDER-001 reading in sign and size: background-only falls within the predicted range of
0.03-0.3 in all 7 pairs. Residual ('nodom',) readout entries, now genuine non-orbit residue (wider than 16 cells or not an
orbit): 58s 617, 114s 608, 22s 73, 201 22, 147 11, 26s 3. They are counted as background, as frozen.

## Reading (information-first)
When two interactions happen to the same coherence, the world records their order. Where the vacuum keeps a shadow,
most of the order information is held by the background (0.45-0.95 bits per case). In 3-22% of cases it is held only by
the background: the outgoing coherences are the same species in both orders, and only the record left behind tells which
came first. Where there is no shadow, order goes nowhere (5; RCA54, exactly) or into the outgoing coherences (1). The
integrable control confirms that the instrument is order-blind where theory says it must be.

## Limits
- Movers are compared at the species level. Their positions and timing (the integrable-style carrier of history) are not
  compared, so "background only" means only background at the species/type level. Comparing mover timing is the next
  refinement.
- Background words are coarse (domain sequences), so background counts are lower bounds at the wall-detail level.
- Readouts are at fixed common times, not asymptotic. One target and two readers. Seven rules in one family of 1-D
  second-order CA.
- This is a replication with the predictions informed by ORDER-001's outcomes, not a blind test.

## Prior art (see contract)
Order-independence of integrable RCA scattering is established (Rule 54 / RCA54, Yang-Baxter), and the control reproduces
it. A 5-query screen found no study measuring which part of a reversible CA (movers vs. background) holds the order of
interactions. That is a screen, not a full review; a proper search is owed before any novelty claim in a paper.

## Lay version
Two travellers take turns walking into the same target. Then we swap who goes first and ask whether the world can tell
afterwards. In the textbook "perfect" world it can't: everyone ends up exactly where they would have anyway, and our test
confirms this in all 772 such cases. In every world that leaves footprints, it almost always can. Most of that memory is
in the footprints, and in a few percent up to about a fifth of cases it is only in the footprints: the travellers walking
away look exactly the same either way. In worlds without footprints the order is either forgotten or carried by the
travellers themselves.
