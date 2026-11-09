# MIR-REVERSIBLE-SPECIES-001 result (v0.1, tag mir-reversible-species-001-v0.1-frozen)

**Valid.** V0 (reproduces VACUUM-COLLIDE-001 and SHADOW-004 at phase 0) and V1 (every current probe species found)
hold in all 28 rules. Run: 3 min 52 s, 4 workers. Full output: `results.json`, `run.log`.

## Lay summary
Under the catalog's own definition of a species (unchanged), trying every seed up to 8 cells wide at every vacuum
phase finds **1486 probe species** in the 28 rules, against at most 4 per rule in the current lists. Every rule has
exactly as many left movers as right movers (mirror pairs). In half the rules the count is still growing at width 8,
so these are counts at this depth, not totals. The extra vacuum phases found no new species; they only reach some
species from narrower seeds.

## Per rule (species of width <= w; split = discovery / confirmation, pre-registered)
| rule | species | shapes | w=4 | 5 | 6 | 7 | 8 | disc | conf | split | current |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 33 | 30 | 30 | 6 | 12 | 20 | 30 | 30 | 20 | 10 | width | 4 |
| 37 | 44 | 44 | 12 | 24 | 38 | 44 | 44 | 38 | 6 | width | 4 |
| 91 (exposed) | 258 | 255 | 20 | 30 | 56 | 118 | 258 | 56 | 202 | width | 4 |
| 123 | 592 | 588 | 20 | 46 | 110 | 256 | 592 | 110 | 482 | width | 4 |
| 139 | 20 | 20 | 6 | 8 | 12 | 20 | 20 | 12 | 8 | width | 4 |
| 143 | 10 | 10 | 4 | 6 | 8 | 10 | 10 | 8 | 2 | width | 4 |
| **147** | 16 | 16 | 4 | 8 | 12 | 16 | 16 | 12 | 4 | width | 4 |
| 151 | 16 | 16 | 0 | 2 | 6 | 10 | 16 | 6 | 10 | width | 2 |
| 171 | 10 | 10 | 4 | 6 | 8 | 10 | 10 | 8 | 2 | width | 4 |
| **201** | 16 | 16 | 4 | 8 | 12 | 16 | 16 | 12 | 4 | width | 4 |
| 209 | 20 | 20 | 6 | 8 | 12 | 20 | 20 | 12 | 8 | width | 4 |
| 213 | 10 | 10 | 4 | 6 | 8 | 10 | 10 | 8 | 2 | width | 4 |
| 233 | 16 | 16 | 0 | 2 | 6 | 10 | 16 | 6 | 10 | width | 2 |
| 241 | 10 | 10 | 4 | 6 | 8 | 10 | 10 | 8 | 2 | width | 4 |
| **22s** | 6 | 6 | 2 | 2 | 2 | 2 | 6 | 2 | 4 | width | 4 |
| **26s** | 26 | 26 | 4 | 6 | 10 | 16 | 26 | 10 | 16 | width | 4 |
| 54s | 2 | 2 | 0 | 2 | 2 | 2 | 2 | 1 | 1 | hash | 2 |
| **58s** | 12 | 12 | 2 | 4 | 6 | 8 | 12 | 6 | 6 | width | 4 |
| **82s** | 26 | 26 | 4 | 6 | 10 | 16 | 26 | 10 | 16 | width | 4 |
| 94s | 32 | 32 | 4 | 6 | 10 | 18 | 32 | 10 | 22 | width | 4 |
| **114s** | 12 | 12 | 2 | 4 | 6 | 8 | 12 | 6 | 6 | width | 4 |
| 154s | 26 | 26 | 4 | 6 | 10 | 16 | 26 | 10 | 16 | width | 4 |
| 182s | 2 | 2 | 0 | 2 | 2 | 2 | 2 | 1 | 1 | hash | 2 |
| 186s | 12 | 12 | 2 | 4 | 6 | 8 | 12 | 6 | 6 | width | 4 |
| 218s | 74 | 74 | 6 | 12 | 22 | 40 | 74 | 22 | 52 | width | 4 |
| 1 (null) | 30 | 30 | 6 | 12 | 20 | 30 | 30 | 20 | 10 | width | 4 |
| 5 (null) | 30 | 30 | 2 | 4 | 12 | 30 | 30 | 12 | 18 | width | 4 |
| 90s (null) | 128 | 128 | 8 | 16 | 32 | 64 | 128 | 32 | 96 | width | 4 |

Bold: the WALL-001 eligible pairs, where PREDICT will run. Each has 4 to 16 confirmation species.
"current" = species in the current probe lists (all recovered, V1).

- Still rising from width 7 to 8 (not saturated at this depth): 91 123 151 233 22s 26s 58s 82s 94s 114s 154s 186s 218s
  90s. Flat from 7 to 8: 33 37 139 143 147 171 201 209 213 241 54s 182s 1 5 (flat for one width step is not proof of
  saturation).
- Phase variants: shapes = species in every rule except 91 (255 of 258) and 123 (588 of 592).
- Split: width rule in 26 rules; hash fallback in 54s and 182s (1 confirmation species each by width).

## Readout error (disclosed) and post hoc correction
The frozen readout `yield_phase0` (in `results.json`) does not measure what the contract describes. It counts species
whose minimum-width representative happens to be at phase 0 (ties go to phase 0), not species reachable from phase-0
seeds. For example it reads 0 for 147, whose current phase-0 species are in the catalog. Not a verdict and no control
depends on it. The described quantity was computed post hoc (`species1_phase0_posthoc.py`, frozen functions unchanged;
`posthoc_phase0_yield.json`): **phase-0 seeds alone reach the same width-8 total in all 28 rules**. Other phases only
reach some species from narrower seeds (147, phase 0: 0, 4, 8, 12, 16 at w = 4..8; all phases: 4, 8, 12, 16, 16).
So the extra phases changed the widths, and with them the discovery/confirmation assignment, but not the species set.

## Exposure note
For the silent rules (single vacuum phase) the width-8 enumeration repeats SHADOW-004; the counts of distinct species
are new, the existence of the movers is not.
