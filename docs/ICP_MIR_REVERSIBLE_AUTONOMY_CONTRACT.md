# MIR-REVERSIBLE-AUTONOMY-001 — is the core an object on its own? (v0.1-draft)

Status: **outcome-free; frozen at tag `mir-reversible-autonomy-001-v0.1-frozen`**. Date 2026-11-03.
Parent: MIR-REVERSIBLE-CORE-001 (243 confirmed rule-seed cores; post-hoc classes
light 194 / sub-light 45 / still-isolated 4). Class labels use the frozen parent
drift: light |drift|=64, still |drift|<=2, sub-light otherwise.

## Test (frozen; `src/minimal_realization_reversible/autonomy.py`)
For every confirmed parent core, at the mature layer t* = t0+64 (end of its
frozen track): copy both state layers (x[t*-1], x[t*]) of the seeded run in the
core window widened by 2 sites per side into the matched vacuum (the comparator
state at the same layers, which is all-zero or a homogeneous oscillation).
Everything else (radiation, wake, parent structure) is removed. Evolve on N=256.
- autonomous: a core-sized (width <= 8) isolated cluster overlapping the window
  is tracked for 64 ticks under the parent tracking rules.
- same_object: autonomous and its 64-tick drift has the parent's sign (or both
  zero) and differs from the parent drift by <= 8 sites.
Exposure disclosure: before freezing I had seen the parent summary, the speed
class counts, and the rule-61 spacetime (a growth front). No transplant was run.

## Decision rule
- Any sub-light or still core that is same_object: first candidate particle-like
  coherence (bounded, persistent, self-sustaining, slower than light). Ordered by
  N_L, Wolfram code, seed length, seed.
- None: slow cores in this family are features of larger structures, not objects.
Light-class cores are reported as a positive control (a moving bit is expected
to be autonomous). Rule 61 predicted to fail (front of a growing structure).
