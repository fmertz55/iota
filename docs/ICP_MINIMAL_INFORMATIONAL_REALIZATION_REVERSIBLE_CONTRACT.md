# MIR-REVERSIBLE-001 — Reversible second-order grammar (contract v0.3-draft)

Status: **outcome-free; frozen at tag `mir-reversible-001-v0.1-frozen`**
Date: 2026-11-03. Parent: MIR-ROLE-SUCCESSION-001 / -EXACT-001 (closed: 255/255 no pass).

## Question
The parent radius-1 family could carry a coherence forward (6 rules) or change an
outward reachable future, but never both. Does adding exactly one information-
preserving capacity, a one-layer memory combined by XOR (Fredkin second-order
construction), join succession to outward causal discrimination?

## Grammar (only change)
`x[t+1][i] = f(x[t][i-1], x[t][i], x[t][i+1]) XOR x[t-1][i]`, f = any of the 256
truth tables (Wolfram code). Every rule is exactly reversible
(`x[t-1] = f(x[t]) XOR x[t+1]`): no information is ever destroyed.
Added capacity, charged explicitly: temporal depth 1 -> 2, state bits per site
1 -> 2 (128 bits on C64), fan-in 3 -> 4, one fixed XOR combination (not a free
row). N_L = popcount(f). All 256 rules are evaluated; no quotients, no exclusions.

## Fixed, inherited unchanged
Detector `MIR-ISOLATED-DYAD-OUTWARD-EFFECT-CENTERED-V0.1` (role `0110`,
attribution against the all-zero comparator under the same rule, succession at
anchor offset 0 or +1 after 1 tick, centered cone gates, guard x[a+3]=0, sham
`011`, break `101` on window a..a+2, endpoint x[t+2][a+3], pass iff sham and
break endpoints differ). Seed x[0]=e_0; C64; synchronous clock; pre-wrap
horizon H=29. Memory semantics, declared before outcomes: seed and comparator
have x[-1]=0; interventions edit layer t only, layer t-1 is left unchanged.

## Implementation check (outcome-free for this family)
`src/minimal_realization_reversible/engine.py` with `order=1` reproduces the
already-opened parent ledger exactly on all 256 rules (first_role,
first_successor, first_intervention_eligible, first_complete_pass; counts
59/6/6/0; 0 mismatches). No `order=2` rule was evolved before the freeze.

## Outcomes and decision rule (frozen)
Primary: number of rules with a complete pass at formation layer t <= 29 on C64.
Every passer is re-evaluated on C96 and C128; *localized pass* requires the same
first-pass layer and signed anchor on all three rings.
- >=1 localized pass: the reversible capacity is sufficient for a proto-object
  under the inherited detector. Winner = min N_L, then min T_proto, then min
  Wolfram code. This is a construction result, not global minimality.
- 0 localized passes: reversibility does not lift the parent obstruction under
  this detector; report stage counts (role, successor, eligible).
Post-wrap behaviour is out of scope (any later pass would be finite-ring-exposed).
Prior art: Fredkin/Toffoli & Margolus reversible CA are known to carry moving
structures; a pass is therefore expected-possible, not novel physics.

## Provenance
Freeze commit + annotated tag, then a result-only child commit writing
`output/minimal_realization/MIR-REVERSIBLE-001/results.json`. `run.py` refuses to
run unless the tag exists and the sealed file hashes match.
