# MIR-REVERSIBLE-SHADOW-001: does the shadow know? (2026-11-03)

## Rule 5 check (exploratory, led to Part A)
LEDGER-001's rule-5 "objects carry nothing" was an artifact. Objects were clustered on the current
layer only, so previous-layer bits up to 3 sites away were cut off (rule 5's lone object is periodic
with margin 4 and fails with margin 2). Fixed by clustering on the union of both layers.

## v0.1 (commit cbe5db2): INVALID
Erasure at contact+24 came before the outgoing coherences had separated, so control rule 205 kept
debris (I = 5 bits). All v0.1 residue-rule values are void.

## v0.2 frozen result (tag mir-reversible-shadow-001-v0.2-frozen; result 2566b67)
- Part A (corrected ledger): 13 clean rules, 12 residue rules (5 and 205 are now clean).
- Control: all 13 clean rules give I(offset; probe future) = 0 exactly. Erasing the carriers leaves a
  pure vacuum, and the probe's future carries no trace of the collision. The test is valid.
- Residue rules: 11 of 12 are untestable (0-1 valid runs). By T=600 their shadow (expanding bubbles)
  has already reached the probe, so there is no clean free-flight probe to send in.
- Rule 37 (21 valid runs, 16 with a shadow remaining): I = 3.84 bits of a possible 4.39.
  With the carriers gone, the probe's future still depends strongly on how the earlier collision
  happened. Verdict per frozen rule: `shadow_constrains_future`.

## Limits
- One testable rule. The 11 bubble rules need a probe design that does not require free flight
  ahead of an expanding shadow (e.g. a probe launched from outside after the bubble passes, or a
  probe in the bubble's own vacuum).
- I is a plug-in estimate on 21 runs; with all runs distinct the maximum is log2(21) = 4.39 bits.
  The value means "nearly every shadow sends the probe to a different future", not a precise capacity.
- A figure was drafted but not shipped: the plotted window's probe position could not be verified
  quickly.

## Lay version
We let two coherences collide, then deleted them, leaving only the faint disturbance they left in the
background. Then we sent a fresh coherence through that spot. Where the background had been left
clean, the newcomer's future was exactly the same no matter how the earlier collision happened.
The shadow there knows nothing. In rule 37 a shadow remains, and the newcomer's future depends on
the details of a collision whose participants no longer exist. The shadow knows. Only one rule could
be tested cleanly so far; in the others the shadow spreads too fast for this design.
