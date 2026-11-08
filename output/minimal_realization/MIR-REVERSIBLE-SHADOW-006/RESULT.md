# MIR-REVERSIBLE-SHADOW-006: result (2026-11-08)

Frozen tag mir-reversible-shadow-006-v0.1-frozen (97b5760). 25 shadow pairs (14 active, 11 silent) + 3 nulls.

## Frozen verdict: INVALID (V1 failed in one cell)
V0 passed for all pairs. V1 failed in exactly one cell: null rule 5, species family C (no residue in any run, yet
0.984 bits not held by carriers). Cause (diagnosed after the run): input aliasing. In the species family, the
second catalogue entry of a rule can be the same physical object as the first, shifted, so distinct input labels give
identical starting states. Counted over starting states: 7 of 28 pairs alias (130 distinct states of 256 inputs;
0.984 spurious bits): rules 139, 143, 171, 209, 213, 241 and null 5. Family A (one pair, distinct offsets) cannot alias.
By the contract, H1 and H2 are formally invalid.

## Family A readings (the pre-specified computations; V1 holds in every family-A cell: True; no aliasing possible)
- H1 scaling: gain 256 -> 512 is 0.25-0.75 bit in 19/25 pairs (threshold 17), > 0.75 in 4
  (rules 143, 171, 213, 241, which start low and catch up), < 0.25 in 2 (silent 154: -0.19; silent 186: 0.12).
  Reading: logarithmic. The shadow keeps about half a bit of each new bit of collision diversity. Stated prior held.
- H2 outline: content share = 0 in 25/25 pairs. The departing carriers plus the residue's outline (its two end sites)
  determine the input exactly; the residue's interior holds no further information. Stated prior held.
- Regimes at A(512): full 22/25, partial 3 (rules [37, 26, 218]), clean 0.
- Type: of 12800 runs at A(512), 6574 leave residue, all extended; 0 compact-stationary. No pair has only compact shadows.
  At this depth every shadow, active or silent, is an extended domain whose walls hold the record.
- Probe reads all: RUN cap never hit.

## Species family C, corrected for aliasing (post hoc)
15/25 shadow pairs were 'partial'. In 6 of them (139, 143, 171, 209, 213, 241) the unrecovered bits equal the
aliasing entropy exactly: artifact. In the 9 alias-free pairs (37, 147; silent 26, 58, 82, 94, 114, 186, 218)
the gap is genuine: 0.06-1.5 bits. When colliding object types vary, a fixed probe type reads only part of the record.
SHADOW-005 family C has the same aliasing defect (its 3x3 lists); its C numbers should not be cited.

## Lay version
A collision's leftover mark is a patch of changed background, and all of its memory sits in where the patch's edges
are, like the outline of a footprint, not in the pattern inside it. Make collisions twice as varied and the outline
remembers about half a bit more: memory grows, but slowly. A passer-by reads the whole outline when only the place
of the collision varies, but misses part of it when the colliding objects themselves differ.
