# MIR-REVERSIBLE-SHADOW-005: result (2026-11-07)

Frozen tag mir-reversible-shadow-005-v0.1-frozen (8d4b614). 14 shadow rules + 2 null pairs.

## Frozen verdicts
- Valid: V0 (all 14 SHADOW-003 pairs reproduced exactly) and V1 (no-residue cells give 0 bits).
- H_sat: n/a. H_R: not_supported (1 eligible cell). Both are artifacts of a mis-set gate: hypotheses were
  restricted to bubble-free cells (no residue cluster > 64 cells), but 1610/1945 residue runs in A(256) are
  wider than 64 cells. The SHADOW-003 shadows are themselves mostly extended vacuum-phase domains (known since
  SHADOW-001/002, which were designed around bubble rules), so the gate excluded the shadows being measured.
  Only 335/1945 A(256) residue runs are compact. The frozen test therefore did not test its question.

## Ungated reading (post hoc, disclosed; not the frozen test)
- Capacity grows with diversity; no saturation. H(input | carriers) by offset range M = 8 / 64 / 256:
  {"33": [1.0, 2.5, 3.5], "37": [1.45, 3.12, 4.34], "91": [1.0, 2.5, 3.5], "123": [1.0, 2.5, 3.5], "139": [1.0, 2.5, 3.5], "143": [0.25, 1.91, 3.3], "147": [1.0, 2.5, 3.5], "151": [1.94, 4.19, 5.69], "171": [0.25, 2.08, 3.35], "201": [1.0, 2.5, 3.5], "209": [1.0, 2.5, 3.5], "213": [0.25, 1.98, 3.32], "233": [1.94, 4.19, 5.69], "241": [0.25, 2.01, 3.34]}
  Gain 64 -> 256: {"33": 1.0, "37": 1.22, "91": 1.0, "123": 1.0, "139": 1.0, "143": 1.39, "147": 1.0, "151": 1.5, "171": 1.27, "201": 1.0, "209": 1.0, "213": 1.34, "233": 1.5, "241": 1.33} (>= 1 bit in 14/14; stated prior of saturation fails).
  Roughly +0.5 bit per doubling of the offset range: the shadow keeps a growing share of where the collision was.
- Probe recovers all of it for offsets: unrecovered = 0 in 84/84 family-A cells with only > 0.
- Phase (B): gain over A(64) [0.0, 1.12, -1.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]; unrecovered = 0 in 13/14.
- Species (C): gain over A(64) [-0.36, 2.38, -0.39, -0.85, 0.64, 0.09, 1.0, 0.0, 0.68, 1.39, 0.63, 0.74, 0.0, 0.05]; unrecovered = 0 in 3/14; footprint/only [0.95, 0.99, 0.61, 0.6, 0.76, 0.67, 1.0, 1.0, 0.76, 0.83, 0.76, 0.76, 1.0, 0.68].
  A fixed R0 probe does not read everything once the colliding species vary.
- Null rule 5, family C: 1.21 bits held off-carrier with residue in 128 runs, 0 bubbles: some species pairs
  of a SHADOW-003 clean rule do leave compact shadows.
- RUN cap never hit.

## Consequence
Shadow type must be a measured variable, not a gate: extended domain (walls) versus compact residue.
Next frozen test should classify each residue run by type and measure capacity per type, in active and silent rules.
