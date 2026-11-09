# Handoff: information-budget line, step 1 done -> BUDGET-001 contract (2026-11-09)

Supersedes HANDOFF_REVERSIBLE_SHADOW_2026-11-08b.md. Working rules unchanged (contract, seal, frozen tag, run, result
commit; information-first vocabulary; check pictures; token thrift; check git log before writing a result file).
Machine note: the Mac is memory-starved on long runs; use 4 workers. Strategic rule: no tests for their own sake.

## Done this session
- MIR-REVERSIBLE-BUDGET-000 (commit 76cf24f; code src/minimal_realization_reversible/budget0.py; output
  output/minimal_realization/MIR-REVERSIBLE-BUDGET-000/{RESULT.md, results.json, run.log}). Rules only: no shadow
  outcomes seen.
- Method: exact coboundary criterion on 2-layer cells, (p,c) = (x[t-1], x[t]). A window-k density is conserved
  iff its one-step change on (k+2)-cell words is h(w[1:]) - h(w[:-1]). This is valid for all ring sizes; it
  replaces the provisional L=7/8 kernel.
- The 14/11 split is confirmed exactly. With invariants: 22s 26s 33 37 54s 82s 91 94s 123 139 147 201 209 218s.
  None up to window 4: 58s 114s 143 151 154s 171 182s 186s 213 233 241. The null rules 1/5/90 match.
- Window-2 densities were extracted (exact rationals, in RESULT.md and results.json). They are exactly conserved
  in simulation on L=37/64/101.
- Normal form: no constant term; terms that involve cell i+1 alone are folded onto cell i. In this form the
  vacuum density is 0 in every phase for all 14 rules, so the budget of a finite disturbance is sum_i phi
  (gauge-free against a homogeneous background).
- Recurring forms: p0c1 - c0p1 (Pomeau-type; 91, 94, 123, 218) and p0c0p1c1 (22, 33, 37, 54). Only 33 has a
  one-cell invariant (p0c0). Windows 3 and 4 add more invariants (counted, not extracted).

## Next: BUDGET-001 contract (draft, then seal)
For each shadow pair and input (reuse the SHADOW-003/004 pair set and the preparation code), compute the window-2
budget(s) of: the incoming carriers (before the collision), the outgoing carriers (after they separate), and the
residue/shadow region (after the carriers have left). Budget is sum_i phi over a region, with vacuum = 0.
Hypotheses to freeze:
- (a) Is the shadow budget-bearing or budget-neutral?
- (b) Record cost: does shadow information (bits the readers recover) require deposited budget, or can a record be
  written budget-free?
- (c) Do the 11 invariant-free rules hold shadows as readily as the 14?
Design points:
- Choose the region boundaries for carriers and residue so that the coboundary gauge cannot leak; the simplest
  safe choice is to measure the residue after the carriers are erased, over the whole ring.
- A rule with several invariants gives a budget vector.
- Decide whether to use window-2 only, or also extract the window-3 invariants.
Prior art (do not claim): Pomeau 1984; Hattori & Takesue 1991; Takesue 1987. The novel part is the split of the
budget between carriers and shadow, and the link between budget and record.

## Deferred
- SHADOW-008 chirality (shelved); Q3 2D rules (later).
