# MIR-REVERSIBLE-BUDGET-000: exact additive invariants of the 25 shadow rules

Feasibility step 1 of the information-budget line (HANDOFF_REVERSIBLE_SHADOW_2026-11-08b.md). Rules only: no shadow
outcomes were computed or looked at, so no contract or seal is needed. Code: src/minimal_realization_reversible/budget0.py.
Data: results.json, run.log.

## Method
Cell i carries both layers (p_i, c_i) = (x[t-1]_i, x[t]_i). Step: (p, c) -> (c, f(c_{i-1}, c_i, c_{i+1}) XOR p).
A window-k density phi is conserved iff its one-step change Delta(w), on (k+2)-cell words, equals h(w[1:]) - h(w[:-1])
for some h. This is the coboundary criterion on the full shift (Hattori-Takesue type). It holds for every ring size
at once, so the earlier dependence on L=7/8 is gone. Nontrivial count = dim(phi solutions) - 4^(k-1), which removes
constants and coboundaries. Ranks: float, plus two primes for k <= 3 (they all agree); float only for k = 4.
The window-2 densities are extracted in exact rationals and checked by simulation on L = 37, 64, 101
(50 random states each, 400 steps): exact conservation in 14/14 rules.

## Result
The provisional 14/11 split is confirmed exactly. The 11 rules with no invariant still have none at window 4.

| rule | silent | nontrivial (k=1,2,3,4) | window-2 basis (normal form) |
|---|---|---|---|
| 22 | s | 0,2,3,4 | p0+c0-p0c0-p0c1-c0p1 ; p0c0p1c1 |
| 26 | s | 0,1,1,1 | p0+c0-p0c1-c0p1 |
| 33 | | 1,2,4,10 | p0c0 ; p0c0p1c1 |
| 37 | | 0,1,3,4 | p0c0p1c1 |
| 54 | s | 0,1,3,6 | p0c0p1c1 |
| 82 | s | 0,1,1,1 | p0+c0-p0c1-c0p1 |
| 91 | | 0,2,3,3 | (long form, see json) ; p0c1-c0p1 |
| 94 | s | 0,1,1,1 | p0c1-c0p1 |
| 123 | | 0,2,2,2 | (same as 91) ; p0c1-c0p1 |
| 139 | | 0,1,1,2 | p0c0-p0c0p1-p0c0c1+p0c0p1c1 |
| 147 | | 0,1,3,5 | (long form, see json) |
| 201 | | 0,1,3,5 | p0c1+c0p1-2p0c0p1c1 |
| 209 | | 0,1,1,2 | p0c0-p0p1c1-c0p1c1+p0c0p1c1 |
| 218 | s | 0,2,3,3 | p0+c0-p0c0-2c0p1+2p0c0p1c1 ; p0c1-c0p1 |
| 58s 114s 143 151 154s 171 182s 186s 213 233 241 | | 0,0,0,0 | none |
| nulls 1 / 5 / 90 | | 1,5,16,50 / 0,2,7,19 / 0,2,4,8 | (k<=3 values match the provisional kernel) |

Notation: p0, c0 = cell i; p1, c1 = cell i+1 (p = earlier layer, c = later layer). The normal form has no constant term,
and terms that involve cell i+1 alone are folded onto cell i. A basis is fixed only up to linear combination.

## Facts that BUDGET-001 can use
1. Vacuum reference: in this normal form the homogeneous vacuum has density 0 in every phase (14/14 rules, silent
   and oscillating). The budget of any finite disturbance of the vacuum is therefore just sum_i phi, and it does
   not depend on the gauge (coboundaries telescope to zero against a homogeneous background).
2. Two recurring forms: the antisymmetric Pomeau-type cross term p0c1 - c0p1 (91, 94, 123, 218), and the
   block count p0c0p1c1 (22, 33, 37, 54).
3. Windows 3 and 4 add further independent invariants in most rules (e.g. 33: 2 -> 4 -> 10). These have been
   counted but not extracted. The window-2 basis is the smallest budget set, and the starting set for BUDGET-001.
   Only 33 has a one-cell invariant (p0c0).
4. Prior art for the method and for invariants of this kind: Pomeau 1984; Hattori & Takesue 1991; Takesue 1987.
   Only the carrier-versus-shadow split, and the link between budget and record, are candidates for novelty.
