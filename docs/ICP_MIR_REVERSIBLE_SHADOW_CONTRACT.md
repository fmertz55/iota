# MIR-REVERSIBLE-SHADOW-001 — does the shadow know? (v0.1-draft)

Status: **outcome-free; frozen at tag `mir-reversible-shadow-001-v0.1-frozen`**. 2026-11-03. Code: `shadow.py`.
ICP claim under test: information is embodied constraint on reachable futures and can persist
beyond its carriers. Here: after a collision, erase the carriers. Does what is left in the background
still constrain what a later coherence can become?

## Part A: ledger re-run with corrected object extraction
Defect found in LEDGER-001 (rule 5 check, exploratory): objects were clustered on the current layer
only, so an object's previous-layer bits up to 3 sites away were cut off and it was misread as
residue (rule 5's lone object fails at margin 2 and is periodic at margin 4). Fix: cluster on the
union of both layers. Outcome-free check: rule 5's lone object now resolves as 1 object, 0 residue.
Part A repeats LEDGER-001 (same rules, 64 offsets, T=600) with the fix; it supersedes LEDGER-001's
clean/residue split.

## Part B: shadow test
For each rule (same R/L), a probe (a second copy of R) trails R by 64 sites. Two universes per
offset: P (probe, R, L) and N (R, L). At contact + 24 ticks every resolved carrier is erased (set to
vacuum, both layers) in both universes, except the probe in P. Residue (the shadow) is kept. Both
universes then run to the common absolute time 1400. Y = the probe's footprint on the future:
the pattern P XOR N at t=1400 (shape and position). Measure I(offset; Y) in bits over valid runs
(the probe is identified and is > 3 sites from every other object at erasure).
- Control: in rules whose Part-A ledger shows no residue, I must be exactly 0 (after erasure the
  background is pure vacuum). Otherwise the test is invalid.
- Verdict `shadow_constrains_future` if I > 0 in >= 1 residue rule; else `no_shadow_effect`.
Reported: I per residue rule, valid run counts, and whether a shadow remained after erasure.

## Amendment v0.2 (2026-11-03), after v0.1 outcome was seen
v0.1 result (commit cbe5db2): INVALID. 12/13 clean controls gave I=0 exactly, but control rule 205
gave I=5 bits with material left after erasure in all 64 runs. Cause (design flaw): erasure at
contact+24 happens before the outgoing coherences have separated, so unresolved collision debris
was kept as "shadow". The same flaw contaminates the residue-rule values (seen: 3.5-6 bits), which are
therefore void. Exposure disclosed: v0.1 per-rule I values were seen before v0.2 was frozen.
v0.2 changes (Part B only): erase at T=600, the ledger's own resolution time, so shadow = ledger
residue by definition; the probe starts DP = ceil(vR*620)+64 behind R and must still be in exact free
flight at T (validity); it must be > 3 sites from every carrier and residue at T; both universes run to
TF = T + ceil(256/vR); N=8192. Control and verdict rules unchanged. Part A is unchanged.
Tag `mir-reversible-shadow-001-v0.2-frozen`.
