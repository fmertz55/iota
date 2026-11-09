# MIR-REVERSIBLE-DESCRIBE-001 result (v0.1, tag mir-reversible-describe-001-v0.1-frozen)

**Valid; H_D supported (7/7 eligible pairs).** V0 (n and run classes equal WALL-001, all 28 pairs), V1 (no edge hit, no
lost or unclosed wall in eligible pairs) and V_S (92 sensitivity controls, every one non-exact) hold. Run: 6 min 6 s,
4 workers. Full output: `results.json`, `run.log`.

## Lay summary
Each shadow was written down as a short list: every wall's type, clock phase and position, and every domain's type
and phase. From that list alone, plus a small dictionary of types, the code redrew every cell of both layers at every
tick of a later 192-tick window that played no part in making the list. Every shadow the language can describe was
redrawn exactly, in every rule, not only the 7 tested ones. The list is a complete coordinate system and carries its
own time: walls tick and drift by their own clocks, and domains run their own cycles. Shifting one wall by one cell, or
its clock by one tick, always breaks the redraw, so the test can fail. The language's failures are the runs it cannot
write down at all. These are disordered walls (154s, 182s, 186s), walls without a clean speed ("open": 37, 143, 151,
171, 213, 233, 241) and rule 37's walls that never repeat within 96 ticks. None is in an eligible pair.

## Per pair (described = runs of class followed or movers; future window [tw + 192, tw + 384))
| pair | described | exact | not describable | walls | wall types | domain states | mean cells |
|---|---|---|---|---|---|---|---|
| **147** | 128 | 128 | 0 | 384 | 5 | 2 | 3521 |
| **201** | 128 | 128 | 0 | 320 | 7 | 2 | 2645 |
| **22s** | 48 | 48 | 0 | 144 | 7 | 8 | 12389 |
| **26s** | 96 | 96 | 0 | 288 | 4 | 3 | 12382 |
| **58s** | 224 | 224 | 0 | 672 | 4 | 4 | 10318 |
| **82s** | 96 | 96 | 0 | 288 | 4 | 3 | 12383 |
| **114s** | 224 | 224 | 0 | 672 | 4 | 4 | 10318 |
| 33 | 128 | 128 | 0 | 256 | 6 | 3 | 4503 |
| 37 | 148 | 124 | 24 wall untracked + 46 open | 334 | 71 | 3 | 2963 |
| 91 (exposed) | 64 | 64 | 0 | 160 | 8 | 3 | 3755 |
| 123 | 32 | 32 | 0 | 64 | 2 | 1 | 4507 |
| 139 | 96 | 96 | 0 | 160 | 7 | 3 | 4318 |
| 143 | 16 | 16 | 208 open | 32 | 2 | 1 | 6474 |
| 151 | 32 | 32 | 16 open | 64 | 4 | 1 | 3254 |
| 171 | 16 | 16 | 208 open | 32 | 2 | 1 | 6470 |
| 209 | 96 | 96 | 0 | 160 | 7 | 3 | 4318 |
| 213 | 16 | 16 | 208 open | 32 | 2 | 1 | 6474 |
| 233 | 32 | 32 | 16 open | 64 | 4 | 1 | 3253 |
| 241 | 16 | 16 | 208 open | 32 | 2 | 1 | 6470 |
| 54s | 32 | 32 | 0 | 64 | 4 | 0 | 18 |
| 94s | 64 | 64 | 0 | 128 | 4 | 1 | 12385 |
| 154s | 0 | 0 | 96 dis | 0 | 0 | 0 | - |
| 182s | 0 | 0 | 32 dis | 0 | 0 | 0 | - |
| 186s | 0 | 0 | 160 dis | 0 | 0 | 0 | - |
| 218s | 64 | 64 | 0 | 128 | 4 | 2 | 12382 |
| 1 (null) | 0 | 0 | 0 (all none) | 0 | 0 | 0 | - |
| 5 (null) | 64 | 64 | 0 | 64 | 2 | 0 | 4 |
| 90s (null) | 0 | 0 | 0 (all none) | 0 | 0 | 0 | - |

Walls and types count exact runs only ("mean cells": non-vacuum cells per exact run at the first future tick).
Mismatched cells: none in any pair (no wall, interior or outside failures), so no first failing tick exists.

## Reading
- In the eligible pairs, 944 runs and 2768 walls are described by 4 to 7 wall types and 2 to 8 domain states. Each run
  covers about 2600 to 12400 non-vacuum cells. The dictionary is shared across runs, so D is a coordinate in a small
  language and does not re-encode each microstate.
- Time is complete for free evolution: D read once (walls in the build window, domains at the earlier snapshot)
  predicts every cell 192 to 384 ticks after tw.
- Language gaps for a v0.2 (none blocks PREDICT on the eligible pairs): disordered walls (> 64 cells wide), walls
  without a resolved speed in the 4096-tick window, and wall orbits longer than 96 ticks (37: 71 wall types among 124
  exact runs; WALL-001 reported 30 unclosed walls there).
- Kill criterion not triggered; PREDICT-001 may proceed on the eligible pairs.

## Limits
As in the contract: the build-window windows are measured; the test is the future window. A defect within 8 cells of a
wall is absorbed into that wall's type. Completeness is for free evolution, not for probe responses.
