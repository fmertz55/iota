# MIR-REVERSIBLE-SHADOW-009: result (2026-11-08)

Frozen tag mir-reversible-shadow-009-v0.1-frozen (38903b4). 25 shadow pairs (21 unexposed, 4 exposed: 26s, 82s, 94s,
218s) + 3 nulls. Reader bank: up to 2 species x 2 sides x 2 launch parities, equal launch distances. Dropped duplicates: 0.
Run: 78 min wall, 4 workers.

## Frozen verdict: VALID; H_B supported; H_Phi supported (at threshold); H_E not supported
- V0 (R0,s=0 reproduces SHADOW-007 footprint_a, 28/28), V1, V2 (every transparent run gives the free-probe readout) pass.
- H_B (bank completes, >= 90% of 21): 21/21. Plus the 4 exposed pairs: the bank completes 25/25.
- H_Phi (launch parity changes a reader's footprint by > 0.01 bit, >= 7/21): 7/21 (37, 91, 139, 147, 209, 22s, 154s). Exposed: 26s, 94s, 218s also.
- H_E (|joint_left - I_L| and |joint_right - I_R| <= 0.05, >= 14/21): 8/21. Fails mainly on the right: right-side
  readers often read far more than the 16-cell right-edge window holds (37: 5.00 vs 4.43; 147: 3.50 vs 0.75;
  114s: 5.69 vs 1.94; 182s: 2.50 vs 0.50; 22s: 1.05 vs 0.30). Left readers match I_L in 16/21.
  Prior (supported for extended domains) failed; all 25 records are extended (0 compact runs).

## Which edge reader a misses (descriptive; reader a = R0 from the left, s=0)
- Far edge: unread bits lie outside its near (left) edge window, a_near = 0: 33 (0.25), 58s (0.83), 114s (1.41), 186s (0.24), 82s (0.58).
- Near edge, crossed transparently or at the wrong phase: 218s (1.5 of 1.5), 94s (0.24), 26s (0.25 near + 0.25 far).
- In 91, 147, 201, 22s reader a reads more than its left window holds (a_near < 0): it reads past the near edge.
- 37: mostly far edge (a_far 0.302) plus a small near-edge shortfall (a_near 0.053).
- The record is its outline: I(in; E_L, E_R | O) = only in 23/25 (37: 5.016 of 5.024, 147: 3.25 of 3.5).

## Reading
No bit of any shadow here is out of reach. What a single reader misses depends on two things. (1) Reach: a record whose
edges recede at light speed exposes only its near edge to a light-speed reader. (2) Coupling: in the rule's XOR (linear)
sector a reader at the wrong species or lattice phase passes through the record with zero superposition defect and reads
nothing (218s). The SHADOW-007 "neither reader" bits are coupling misses, not lost information. Readers from the
right reach deeper into records than readers from the left (H_E failure), a left/right asymmetry still mixed with
rule and preparation handedness (SHADOW-008 will separate these).

## Lay version
The collision's mark can always be read, but only by the right passer-by arriving in step with it. Out of step, a
reader walks straight through without noticing; and an edge that runs away at the speed of the readers can only be
read from its own side.
