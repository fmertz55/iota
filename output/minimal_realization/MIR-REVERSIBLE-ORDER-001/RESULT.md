# MIR-REVERSIBLE-ORDER-001: result (2026-11-16)

Frozen tags `mir-reversible-order-001-v0.1-frozen` (762d666) and erratum `v0.1.1-frozen` (f6c7bd0). The run was resumed from
per-job checkpoints in the user's Terminal overnight. Data: results.json (43 MB, untracked; regenerable from the frozen
code), jobs/ (per-job checkpoints, untracked), run.log, posthoc_blobfree.json.

## Frozen verdict: INVALID (V_C54 failed). H_O, H_B, H_W are therefore not assessed.
- V0 ✓ (rule 91 slice: 64 valid, 32 order). V_slot ✓. V_valid ✓ (all cases valid; touched 1382-1600 per pair).
- V_C54 ✗. On the 769 touched RCA54 cases, two of the three clauses held: there was no order effect at any readout time,
  and the target's final (species, position) was equal in AB and BA at every readout time, so Yang-Baxter additivity was
  exact in 769/769. The clause that failed was "no background ever": 226 cases had a persistent ('nodom',) component.
- Had the run been valid, all 7 pairs would have passed H_O, H_B and H_W (7/7 each). These passes do not count.

## Diagnosis (post hoc): an instrument error, not physics
The ('nodom',) components in RCA54 are reader soliton packets moving at +1, 9 cells wide in the union of the two
layers. The readout's mover detector skips clusters wider than 8 (a cut copied from SHADOW-001's `objects`). SPECIES-001
limits width on layer t only, so some genuine movers are filed as background. The same error can move movers into
the background in the shadow rules, which inflates background counts. It can also hide mover differences (when a blob
in AB is a different wide mover than in BA).

## Post hoc, exploratory: blob-free subset (cases with no ('nodom',) component in either order at any readout time)
Bits per touched case (order bit equiprobable; 1 bit where coarse AB != BA), persistent over all three readouts.

| pair | n | order | background holds | movers hold | background only | written (records in both, differ) |
|---|---|---|---|---|---|---|
| 147 | 1115 | 0.98 | 0.95 | 0.86 | 0.120 | 974 |
| 201 | 1268 | 0.99 | 0.95 | 0.91 | 0.087 | 1085 |
| 22s | 1291 | 0.94 | 0.88 | 0.62 | 0.311 | 1115 |
| 26s | 1359 | 0.85 | 0.48 | 0.67 | 0.034 | 661 |
| 58s | 1044 | 0.78 | 0.62 | 0.67 | 0.070 | 590 |
| 82s | 1375 | 0.83 | 0.45 | 0.65 | 0.047 | 636 |
| 114s | 1151 | 0.81 | 0.56 | 0.60 | 0.098 | 608 |
| null 1 | 426 | 0.86 | 0 | 0.86 | 0 | 0 |
| null 5 | 476 | 0 | 0 | 0 | 0 | 0 |
| RCA54 (250) | 769 touched (all) | 0 | 0 (all blobs) | 0 | 0 | 0 |

Null 90s: no touched cases (its readers never interact with the target), so it is not informative.
The pattern: in the shadow rules the order of two interactions is held mostly by the background. In 3-31% of cases
it is held ONLY by the background (the mover species are identical in both orders). Where there is no shadow, order goes
nowhere (5, RCA54) or into the movers only (1).

## Limits of this reading
- Post hoc subset, chosen after the data were seen. It removes 2-36% of cases, and they are not removed at random.
- "Movers identical" means equal species multisets. Mover positions and timing are not compared, so "background only"
  means only background at the species/type level.
- Background words are coarse (domain sequences). Wall-level detail is not seen.

## Next (pre-registered separately): ORDER-002
A confirmatory replication with the detector fixed: an orbit test for clusters up to 16 cells wide, a fresh sample seed,
and predictions frozen from the table above.

## Lay version
We had two travellers take turns walking into the same target. Then we swapped who went first and asked whether the
world afterwards can tell the difference. In the "perfect" textbook world (Rule 54) it can't. Everyone ends up exactly
where they would have anyway. In our shadow worlds it almost always can. Most of that memory of who went first is kept
in the footprints left behind, and sometimes ONLY in the footprints: the travellers walking away look identical either
way. In worlds without footprints the order is either forgotten or carried by the travellers. The checking tool had a
flaw (it mistook some wide travellers for footprints), so this run doesn't count as proof. The clean re-run is next.
