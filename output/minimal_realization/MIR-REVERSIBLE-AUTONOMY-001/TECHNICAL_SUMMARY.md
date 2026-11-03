# MIR-REVERSIBLE series: technical summary (2026-11-03, iota main)
Family: x[t+1]=f(x[t][i-1..i+1]) XOR x[t-1], all 256 f; comparator = same rule from vacuum.
1. MIR-REVERSIBLE-001 (tag mir-reversible-001-v0.1-frozen): inherited dyad detector.
   Engine order=1 reproduces the parent ECA ledger (59/6/6/0). Result 120/61/56/16; 16 localized passes.
   Audit: all 16 are expanding wedges, so the pass is formal only.
2. MIR-REVERSIBLE-CORE-001 (tag ...-core-001-v0.1-frozen): isolated core width<=8 persisting
   64 ticks, N=256, confirmed on C384. Single event: 22 rules pass. With seeds up to 4 bits: 57 rules / 243 pairs.
   Post-hoc speed classes: 194 light / 46 sub-light / 3 still.
3. MIR-REVERSIBLE-AUTONOMY-001 (tag ...-autonomy-001-v0.1-frozen): transplant the mature core
   (both layers, +/-2 margin) into the matched vacuum and track 64 ticks.
   Light: 48/194 autonomous. Sub-light: 36/46 autonomous and same object. Still: 0/3.
   Rule 61 failed as predicted. The 36 candidates come from 13 rules
   (29,71,123,139,143,171,175,183,209,213,237,241,245), all from 2-4 bit seeds, none from the single event,
   all isolated when alone. Speeds 1/2 (period 4, shift 2) or ~1/3 (rules 29/71/123; mirror pair 29/71).
   Post-hoc observation: all 13 have f(000)=1 (odd Wolfram code), i.e. an oscillating vacuum.
Limits: moving structures in reversible CA are prior art (Fredkin; Toffoli & Margolus).
The vacuum-activity pattern is post hoc and needs its own frozen test.
Collisions, conserved quantities and speed-versus-structure relations are untested.
