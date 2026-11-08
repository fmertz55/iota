# Handoff: reversible shadow line -> information budget (2026-11-08, evening)

Supersedes HANDOFF_REVERSIBLE_SHADOW_2026-11-08.md. Working rules unchanged (contract, seal, frozen tag, run, result
commit; information-first vocabulary; check pictures; token thrift; check git log before writing a result file).
Machine note: the Mac is memory-starved on long runs (wall time >> CPU time); use 4 workers.

## Done this session
- SHADOW-009 (tag mir-reversible-shadow-009-v0.1-frozen, result beb07bc): valid. Reader bank (2 species x 2 sides x 2
  launch parities) completes 25/25 shadow pairs. No shadow bit is out of reach. Single-reader misses = (1) reach: edges
  recede at light speed, so only the near edge is readable; (2) coupling: in the rule's XOR sector a reader of the wrong
  species or launch phase crosses with zero superposition defect and reads nothing (218s). H_E failed (8/21): right-side
  readers read past the right edge window. The reader-mechanics sub-line is closed.

## Strategic decision (user, 2026-11-08)
Stop tests for their own sake. Next line must advance the core hypothesis: information coherences that look like particles AND energy.
Assessment: quasi-particles in reversible second-order rules are prior art (Wolfram 37R, Fredkin). Our own result is
the shadow (records held by active backgrounds after carriers leave; exact ledger; 25 rules). The gap is "energy".

## Next: INFORMATION-BUDGET line (user chose this)
Question (information vocabulary): is there a conserved additive budget that coherences carry and exchange, and does
writing a record into the background (shadow) move budget with it? Can a record be written budget-free?
Prior art (do not claim): Pomeau 1984 J Phys A 17 L415 (an energy-like invariant in reversible CA); Hattori & Takesue 1991
Physica D 49:295 (necessary and sufficient condition for additive conserved quantities; ECA table); Takesue 1987 PRL (statistical
mechanics of elementary reversible CA, = our rules); Takesue: energy transport ballistic in 90R, diffusive in 26R;
Taati, Conservation laws in CA (Handbook of Natural Computing). Novel part: the carrier vs shadow split of the
budget, and the budget-record link.
Pre-contract feasibility (rules only, no shadow outcomes seen; kernel only, PROVISIONAL: rings L=7/8, must verify on
larger rings): number of nontrivial additive invariants for windows of 1/2/3 cells (2-layer cells, minus constant + coboundaries):
  with >= 1: 22s, 26s, 33, 37, 54s, 82s, 91, 94s, 123, 139, 147, 201, 209, 218s (14);
  none up to window 3: 58s, 114s, 143, 151, 154s, 171, 182s, 186s, 213, 233, 241 (11). Nulls: 1 [1,5,16], 5 [0,2,7], 90 [0,2,4].
Suggested steps: (1) verify invariants exactly (larger rings / Hattori-Takesue criterion), extract the densities;
(2) contract BUDGET-001: for each shadow pair and input, budget of incoming carriers, outgoing carriers and residue
(relative to the vacuum density); questions: is the shadow budget-neutral or budget-bearing; does shadow information
require deposited budget (record cost); do rules without invariants hold shadows as readily (the 14/11 split above).
Keep it information-first: the budget is a ledger quantity, not a "particle energy" primitive.

## Deferred
- SHADOW-008 chirality (design in HANDOFF_REVERSIBLE_SHADOW_2026-11-08.md): shelved, low value for the core hypothesis.
- Q3 2D rules: robustness, later.
