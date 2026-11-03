# MIR-REVERSIBLE-COLLIDE-002 — exact-species collisions and vacuum bubbles (v0.1-draft)

Status: **outcome-free; frozen at tag `mir-reversible-collide-002-v0.1-frozen`**. 2026-11-03.
Repairs the two classifier defects in VACUUM-COLLIDE-001 (no contact check; bad radiation flag)
and replaces 32-tick velocity estimates with exact period/shift. Code: `collide2.py`.

## Objects
Catalogue input: the frozen Part-V object list of VACUUM-COLLIDE-001 (already opened). Each
sub-light object is evolved alone; its exact period p, shift s (pattern on both layers and vacuum
phase must recur, translated, within 240 ticks) give v = s/p exactly. Kept if |v| >= 1/8.
Species = the set of (vacuum phase, normalized pattern) states on its orbit. Outcome-free check
before freezing: on 59 catalogue objects, exact s/p agrees with the 120-tick drift except for 2
non-periodic objects with drift 3 (they are excluded by |v| >= 1/8).

## Collisions
Rules with at least one right- and one left-moving kept object: lowest-seed R at 400 and lowest-seed L
at 400+off, off = 24..31, N=1024, 400 ticks. Only runs whose free flights come within 3 sites
(contact) are scored. Outcomes at tick 400:
`annihilated` | `superposition` (exact XOR of free flights) | `bubble` (a run of >= 32 consecutive
difference sites) | otherwise each outgoing cluster (width <= 8) is cut out (+/-2, both layers) and
must be exactly periodic. `elastic` = 2 outgoing, species {R, L}, velocities {vR, vL};
`transmuted` = all outgoing resolved but not elastic; `unresolved` = any wide or non-periodic cluster.

## Predictions and hypotheses (frozen)
- Theorem: annihilated = 0.
- H_M (momentum-like conservation): report the fraction of bounded outcomes (elastic + transmuted)
  with sum of v_out = vR + vL exactly. There is no threshold; elastic outcomes conserve it trivially,
  so the informative number is the fraction among transmuted.
- Also reported: object count conserved, fusion (2 -> 1 bounded), new species.
- H_B1: bubbles occur only in active-vacuum rules (f(000)=1). Falsified by any silent-vacuum bubble.
- H_B2: bubble walls move at light speed (|v| within 0.05 of 1, both walls, measured over the last
  40 ticks) in >= 90% of bubbles.
Prior art: reversible CA glider collisions (Fredkin; Toffoli & Margolus; Margolus 1984).
