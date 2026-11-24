# QP-001 results (v0.1, tag qp-001-v0.1-frozen, commit cb734b2) — 2026-11-24
Run `python qp001.py run` on the tagged file (sha256 1865bd2e… matches seal); 50 s. Data: qp001.csv, summary.txt.
## Verdict: V1, H-POCKET, H-CLOCK, H-PUSH PASS; H-DRIFT and H-LINK FAIL.
| Check | Result | Rule |
|---|---|---|
| V1 | settle error <= 9.3e-12; still pocket moves <= 7e-11 cell, width change <= 1.7e-6; clock match 7.9e-12 | < 1e-9; < 1e-6; < 1e-4; < 1e-8 |
| H-POCKET | settled, still pocket at all 6 settings | all 6 |
| H-CLOCK | pocket clock slower than lone coherence by 1.57% (G 0.4) and 3.88-3.89% (G 0.7) | > 0.1%, all 6 |
| H-PUSH | gap 0.0217 -> 0.0107 -> 0.0052 (G 0.4), 0.0958 -> 0.0486 -> 0.0244 (G 0.7); intercepts +0.0003, -0.0008 | monotone; < 0.03; abs intercept < 0.01 |
| H-DRIFT | G 0.4: 0.0116, 0.0009, 0.0046 (NOT monotone), intercept -0.0100; G 0.7: 0.0772, 0.0267, 0.0024, intercept -0.0228 | monotone; < 0.03; abs intercept < 0.01 |
| H-LINK | G 0.4: 0.0103, 0.0098, 0.0099 (pass); G 0.7: 0.0261, 0.0232, 0.0220 (fail) | < 0.02, all 6 |
## What the failure says (descriptive, not pre-registered)
- In the smooth limit push-resistance equals total ticking (coherence clock + glue-notebook cycling): H-PUSH.
- The drift toward slow clocks does NOT follow total ticking. It extrapolates to 0.990 (G 0.4) and 0.977 (G 0.7)
  of the lone-coherence rate, matching clock / total ticking = 0.990 and 0.976. drift x push equals
  clock / total ticking at every a0 (0.9901 vs 0.9899; 0.978 vs 0.9755).
- So the pull follows the coherence's own clock only; the glue notebook's share of the ticking is not pulled,
  although the rule lets gravity slow the glue's spring and mark-passing. The pocket lags by exactly that share
  (1.0% and 2.4%). This is a sharp, quantitative violation of fair drift for a composite.
## Reading
A settled quasi-particle exists, keeps its own (slower) clock, and its push-resistance equals its total ticking.
But in this rule the pull toward slow clocks only reaches the turning coherence, not the glue that binds it.
Fair drift for composites needs a rule in which gravity's pull reaches the glue notebook's cycling as well.
Limits: mean field, one coherence, 1D, hand-set gravity slope, supplied vacuum entry.
