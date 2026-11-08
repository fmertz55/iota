# MIR-REVERSIBLE-SHADOW-007 — partial reading with alias-free species, and a second reader (v0.1)

Status: **outcome-free; frozen at tag `mir-reversible-shadow-007-v0.1-frozen`**. 2026-11-08. Code: `shadow7.py`.
Parent: SHADOW-006 (invalid as frozen: species-family aliasing; alias-free subset showed 9 partial pairs).

## Questions
1. With alias-free species mixes, does a single probe type still read only part of the shadow's record?
2. Does a second, independent reader coming from the other side recover the rest?

## Exposure (before freezing)
SHADOW-006 species-family values (2x2 catalogue lists, aliased in 7 pairs) are known: 9 alias-free pairs partial
for the R0 reader (0.06-1.5 bits). Unseen: deduplicated lists for the 6 aliased rules, any left-side reader, any
joint reading.

## Design
Pairs: the 25 SHADOW-006 shadow pairs (14 active, 11 silent) and its 3 nulls (rules 1, 5, 90).
Species lists: per direction, the pair's own mover first, then catalogue entries (collide2.catalogue for active;
SHADOW-004 pair seeds for silent) whose orbit species set does not intersect an already chosen one; first 2.
Inputs: (Ri, Lk, offset), offsets 24..87. Starting states are hashed (both layers); an input whose state equals an
earlier input's is dropped (count reported). N = 16384, X0 = 8192.
T = ceil(552 / min closing speed) + 300 (as SHADOW-006); carriers erased at T as before. RUN = 1500.
Readers, each in its own world (the shadow is read independently, never by both at once):
- a: free R0 copy (at tick T) launched GAP=24 left of everything (SHADOW-003 launch rule);
- b: free L0 copy (at tick T) launched GAP=24 right of everything (mirror rule).
Readouts: only = H(in|O); footprint_a = I(in;Y_a|O); footprint_b; joint = I(in;Y_a,Y_b|O);
unrecovered_x = only - footprint_x.

## Validity controls (frozen)
- V0: reader a at T = 600, RUN = 1500, single pair (R0, L0), 64 offsets, reproduces the stored SHADOW-003 (active)
  or SHADOW-004 (silent) only_shadow and footprint_beyond for every shadow pair.
- V1: every cell in which no run leaves residue has only = 0 and all footprints = 0 (aliasing check included).

## Hypotheses (frozen; over shadow pairs with only > 0)
- H_P partial replicates: unrecovered_a > 0 in >= 1/3 of pairs.
- H_J second reader completes: joint unrecovered = 0 in >= 2/3 of the pairs that are partial for reader a.
  Stated prior: supported (the first reader alters the record before reaching its far edge; the far edge is
  intact for a reader from the other side).
- Descriptive: unrecovered_b; pairs partial for both readers alone but full jointly; dropped duplicate inputs;
  number of distinct species per direction.
