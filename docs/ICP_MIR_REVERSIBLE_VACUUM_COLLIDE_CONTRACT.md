# MIR-REVERSIBLE-VACUUM-COLLIDE-001 (v0.1-draft)

Status: **outcome-free; frozen at tag `mir-reversible-vacuum-collide-001-v0.1-frozen`**. 2026-11-03.
Family unchanged: x[t+1]=f(nbhd) XOR x[t-1], all 256 f. Code: `src/minimal_realization_reversible/vacuum_collide.py`
(vectorized step checked equal to the frozen engine on all 256 rules before freezing).

## Part V — does slow matter need an active vacuum?
Hypothesis (from the post-hoc observation in AUTONOMY-001: all 13 rules hosting autonomous
sub-light objects have f(000)=1, an oscillating homogeneous vacuum). New, independent search:
every nonzero 5-site pattern on both layers (1023 seeds per rule; 261,888 runs), placed in the
vacuum, N=256, 120 ticks. An *object* = difference from the vacuum stays nonzero and width <= 8 at
every tick 0..120 (bounded, no radiation). Classes by 120-tick drift: still |d|<=2, light |d|>=116,
sub-light otherwise.
Decision: supported iff no silent-vacuum rule (f(000)=0) has a sub-light object and >=1
active-vacuum rule does; falsified iff any silent-vacuum rule has one.

## Part C — collisions
For every rule with both a right- and a left-moving sub-light object from Part V, take the
lowest-index seed of each, place them head-on (R at 200, L at 200+off, off = 40..47; N=512) and run
240 ticks. Outcomes at tick 240: `annihilated` (exact vacuum), `transparent` (state equals the XOR
superposition of the two free flights), else `interacting`; for interacting, bounded clusters are
tracked over the last 32 ticks for velocities; radiation = any unbounded or untrackable cluster.
Reported: counts per outcome; among interacting, count conserved (exactly 2 bounded outgoing, no
radiation) and velocity-sum conserved (|sum v_out - (vR+vL)| <= 0.05, no radiation); collisions
producing a still object.
Pre-stated prediction (theorem, not hypothesis): annihilated = 0, because a reversible law maps
only the vacuum to the vacuum. Part C rates are descriptive (no pass threshold).
Prior art: reversible CA gliders and collisions (Fredkin; Toffoli & Margolus); second-order rule
families (Wolfram's "R" rules).

## Amendment v0.1.1 (2026-11-03)
The v0.1 run crashed while serializing numpy int64 to JSON, after computing but before printing or
writing any outcome; no outcome was seen. Fix: JSON default converts numpy scalars. Nothing else changed.
New tag `mir-reversible-vacuum-collide-001-v0.1.1-frozen`.
