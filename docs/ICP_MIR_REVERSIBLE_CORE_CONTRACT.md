# MIR-REVERSIBLE-CORE-001 — bounded persistent core detector (contract v0.4-draft)

Status: **outcome-free for this detector; frozen at tag `mir-reversible-core-001-v0.1-frozen`**
Date: 2026-11-03. Parent: MIR-REVERSIBLE-001 (formal pass, substantive negative:
all 16 passers were expanding wedges).

## Question
Under the same reversible second-order family (all 256 f; x[t+1]=f(nbhd) XOR x[t-1]),
does any rule form a *bounded* informational coherence that *persists*: an
isolated, small, attributed core that survives many ticks, alone or while
shedding outward "radiation"?

## Disclosure of prior exposure
Before this freeze I had seen, for MIR-REVERSIBLE-001's 16 passers only, the
total difference-support width at t=10/30/60/100 (all expanding) and the
rule-134 spacetime diagram for t<=22. No cluster tracking, no other rule's
dynamics, and no non-canonical seed was evolved before the freeze.

## Detector (frozen; `src/minimal_realization_reversible/core.py`)
- Field: D_t = seeded state XOR comparator state (comparator: all-zero both
  layers, same rule), ring N=256, layers 0..120 (no wrap of the radius-t cone).
- Clusters: maximal groups of difference sites with internal zero gaps < 3,
  so each cluster is flanked by >= 3 non-difference sites (isolation).
- Core: cluster width <= 8. Track: start at layer t0 in 1..29; at each next
  tick, successor = leftmost core-sized cluster whose span overlaps the
  predecessor span widened by 1 per side (speed <= 1, the causal limit).
- Pass: track survives K=64 consecutive ticks. Kind = `isolated_object` if the
  core is the only cluster at every tracked tick, else `core_with_radiation`.
- Control: identical result (same t0, start, end, drift, kind) on N=384.
- No outward-intervention criterion: in a reversible law any edit propagates,
  so that test would be trivially passed; persistence plus boundedness is the
  content here.

## Seeds
Primary: canonical one-event seed `1`. Secondary (declared initial-condition
capacity): x[0] patterns `11,101,111,1001,1011,1101,1111` at loci 0..3, x[-1]=0.

## Decision rule
- Primary pass >= 1: a lone event condenses into a bounded persistent coherence.
- Primary 0, secondary >= 1: bounded persistent coherences exist but need a
  structured initial event (they do not form from a single event).
- Both 0: no bounded persistent core at width <= 8, K=64 in this family.
Winner ordering: min N_L, then min t0, then min Wolfram code, then shortest seed.
Report kinds. Prior art: reversible CA gliders (Fredkin; Toffoli & Margolus).
