# MIR-REVERSIBLE-SHADOW-009: what a single reader misses (reach, phase, edges) (v0.1)

Status: **outcome-free for the 21 unexposed shadow pairs; frozen at tag `mir-reversible-shadow-009-v0.1-frozen`**.
2026-11-08. Code: `shadow9.py`. Parent: SHADOW-007 (valid; H_J missed narrowly; 26s, 82s, 94s and 218s keep bits
that neither frozen reader reads). Numbering: SHADOW-008 stays reserved for the mirror-closed chirality test (handoff
2026-11-08, future work).

## Questions
1. When a single reader misses part of a shadow's record, which edge holds the missing bits, and why does the reader miss them?
2. Are the bits that neither SHADOW-007 reader reached out of reach of every probe, or only of those two?

## Exposure (before freezing; disclosed)
A diagnostic was run on the four SHADOW-007 pairs that neither reader completes (kernel only; not committed): 26s, 82s, 94s, 218s.
Seen: (a) 218s's record is one extended domain whose edges recede at light speed. It never contains a 111
neighbourhood, so rule 218 acts on it as XOR (rule 90). The R0 reader has zero superposition-defect events and reads 0
bits; launched one cell further it reads 1.25 bits; the second species launched one cell further reads all 1.5 bits.
Right-side readers read only 0.25 bit (the right edge). (b) With 2 species x 2 sides x 2 launch parities (equal launch
distances), the joint read is complete in all four (26s and 82s 2.469 bits, 94s and 218s 1.5 bits). These four pairs are
therefore **exposed**: they are reported, but are excluded from every frozen hypothesis count. Nothing was seen for the other 21 shadow
pairs or for the 3 nulls beyond the SHADOW-007 RESULT.md values.

## Design
Pairs, species lists, inputs, T, carrier erasure, N, X0 and RUN=1500 are identical to SHADOW-007 (`shadow7.lists`,
`shadow7.core` conventions; 256 or 64 inputs per pair; duplicate starting states dropped).
Reader bank, each reader in its own world (the shadow is read independently):
- Left readers: each alias-free right-moving species Ri (up to 2), free copy at tick T, its right end placed so that
  exactly GAP+s vacuum cells separate it from the leftmost residue/object site over all inputs; s in {0, 1}.
- Right readers: each alias-free left-moving species Lk (up to 2), placed so that GAP+s vacuum cells separate its left
  end from the rightmost site; s in {0, 1}. GAP = 24. (Equal launch distances on both sides.)
Readout Y = (shape, leftmost site) of P XOR N on the current layer after RUN ticks (as SHADOW-007).
Superposition defect per site and tick: d = f(P) xor f(N) xor f(P xor N xor v) xor f(v) on the current layer
(v = homogeneous vacuum value of that layer). A run is *touched* if d != 0 at any site and tick; else *transparent*.
Edge content at T (carriers erased): E_L = (leftmost residue site, residue pattern of both layers within 16 cells of it),
E_R likewise from the right end; None if no residue.
Readouts: only = H(in|O); footprint_x = I(in;Y_x|O); joint_left / joint_right / joint_all over the bank's readers on
each side / all readers; I_L = I(in;E_L|O), I_R = I(in;E_R|O), I_LR = I(in;E_L,E_R|O).

## Validity controls (frozen)
- V0: reader (R0, s=0) is exactly SHADOW-007 reader a; its footprint equals the stored SHADOW-007 footprint_a for all
  28 pairs (|diff| < 1e-12).
- V1: in every pair in which no run leaves residue, only = 0 and every footprint = 0.
- V2 (superposition): every transparent run yields the vacuum-only free-probe readout (the same reader launched into the
  pure vacuum, same ticks). This holds exactly for second-order rules; a failure means a code error.

## Hypotheses (frozen; over the unexposed shadow pairs with only > 1e-9; tolerance 1e-9 unless stated)
- H_B (bank completes): joint_all recovers all of `only` in >= 90% of pairs. Stated prior: supported.
- H_Phi (launch phase matters): in >= 1/3 of pairs, at least one (side, species) reader's footprint differs between
  s=0 and s=1 by > 0.01 bit. Stated prior: supported.
- H_E (each side reads its own edge): |joint_left - I_L| <= 0.05 bit and |joint_right - I_R| <= 0.05 bit, both, in
  >= 2/3 of pairs. Stated prior: supported for extended domains, uncertain for compact records.
- Descriptive (not frozen as tests): for SHADOW-007 reader a (R0, s=0), split its unread bits into far-edge
  (H(in|O,E_L), not on its near edge) and near-edge-unread (I_L - footprint_a); fraction of transparent runs per
  reader; I_LR vs only (is the record its outline?); results for the four exposed pairs and the nulls; shadow type
  (SHADOW-006 rule: extended vs compact) per pair.
