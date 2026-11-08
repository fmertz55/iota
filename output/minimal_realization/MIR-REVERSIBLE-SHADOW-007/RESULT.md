# MIR-REVERSIBLE-SHADOW-007: result (2026-11-08)

Frozen tag mir-reversible-shadow-007-v0.1-frozen (bf78658). 25 shadow pairs + 3 nulls; 0 duplicate starting states.
Valid: V0 (all pairs reproduce SHADOW-003/004) and V1 (no-residue cells give 0 everywhere, aliasing check included).

- H_P partial replicates: SUPPORTED. Reader a (from the left) is partial in 11/25 pairs: ['33a', '37a', '147a', '201a', '26s', '58s', '82s', '94s', '114s', '186s', '218s'].
- H_J second reader completes: NOT SUPPORTED. Joint reading is complete in 7/11 of those: ['33a', '37a', '147a', '201a', '58s', '114s', '186s'].
  Reader b (from the right) alone is partial in 20 pairs: ['33a', '37a', '91a', '123a', '139a', '143a', '151a', '171a', '209a', '213a', '233a', '241a', '26s', '54s', '58s', '82s', '94s', '154s', '186s', '218s'].
  Pairs partial for each reader alone but complete jointly: ['33a', '37a', '58s', '186s'].
  Joint reading complete overall in 21/25 pairs.
- Per pair [only, unrecovered_a, unrecovered_b, unrecovered_joint] (bits): {"33a": [2.469, 0.25, 2.125, 0.0], "37a": [5.024, 0.355, 0.36, 0.0], "91a": [1.5, 0.0, 0.25, 0.0], "123a": [0.625, 0.0, 0.625, 0.0], "139a": [1.75, 0.0, 1.375, 0.0], "143a": [0.25, 0.0, 0.25, 0.0], "147a": [3.5, 0.779, 0.0, 0.0], "151a": [4.189, 0.0, 2.0, 0.0], "171a": [0.782, 0.0, 0.25, 0.0], "201a": [2.469, 0.18, 0.0, 0.0], "209a": [1.75, 0.0, 1.375, 0.0], "213a": [0.782, 0.0, 0.25, 0.0], "233a": [4.189, 0.0, 2.0, 0.0], "241a": [0.25, 0.0, 0.25, 0.0], "22s": [1.047, 0.0, 0.0, 0.0], "26s": [2.469, 0.5, 0.584, 0.25], "54s": [2.5, 0.0, 2.0, 0.0], "58s": [6.314, 0.834, 0.477, 0.0], "82s": [2.469, 0.584, 0.584, 0.242], "94s": [1.5, 0.242, 1.5, 0.242], "114s": [5.689, 1.413, 0.0, 0.0], "154s": [1.533, 0.0, 0.308, 0.0], "182s": [2.5, 0.0, 0.0, 0.0], "186s": [3.525, 0.242, 3.025, 0.0], "218s": [1.5, 1.5, 1.25, 1.25]}
- Species per direction: {"33a": [2, 2], "37a": [2, 2], "91a": [2, 2], "123a": [2, 2], "139a": [2, 2], "143a": [2, 2], "147a": [2, 2], "151a": [1, 1], "171a": [2, 2], "201a": [2, 2], "209a": [2, 2], "213a": [2, 2], "233a": [1, 1], "241a": [2, 2], "22s": [2, 2], "26s": [2, 2], "54s": [1, 1], "58s": [2, 2], "82s": [2, 2], "94s": [2, 2], "114s": [2, 2], "154s": [2, 2], "182s": [1, 1], "186s": [2, 2], "218s": [2, 2], "1t": [2, 2], "5t": [2, 2], "90l": [2, 2]}

Reading: when colliding object types vary, part of the record is invisible to one reader type, and a second
independent reader from the other side does not, in most cases, recover it. Stated prior (far-edge explanation) failed.
The missing part is not simply an unread edge. Lay version: two passers-by from opposite sides still miss part of
what the mark remembers when the colliding objects differ.
