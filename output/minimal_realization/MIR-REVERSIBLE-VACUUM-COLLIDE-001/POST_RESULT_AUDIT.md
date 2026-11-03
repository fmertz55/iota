# MIR-REVERSIBLE-VACUUM-COLLIDE-001: result and post-result audit (2026-11-03)
Frozen tag v0.1.1. The v0.1 run crashed on JSON serialization before any output.

## Part V: frozen verdict FALSIFIED
Bounded objects (width <=8 for 120 ticks) by vacuum type, as rules hosting >=1 object:
silent vacuum f(000)=0: still 32, sub-light 21, light 23.
active vacuum f(000)=1: still 40, sub-light 37, light 5.
Slow objects do not need an active vacuum. The AUTONOMY-001 pattern came from its seed set
(single-layer seeds); two-layer seeds find silent-vacuum slow objects (rules 12, 36, 40, 44, 68, ...,
all multiples of 4, so f(000)=f(001)=0; post-hoc).

## Part C: frozen counts and corrections
Frozen: 58 rules, 464 collisions; annihilated 0 (the reversibility theorem holds); "transparent" 296;
interacting 168.
Audit (exploratory) found two classifier defects:
1. 272 "transparent" cases never met within 240 ticks (slow objects too far apart), so the outcome is vacuous.
2. The frozen radiation flag mislabels clean outgoing pairs.
Corrected, for the 192 collisions that actually met (24 rules):
- 24 exact pass-through (superposition);
- 126 two bounded objects out, but not a superposition (interaction with a shift or swap);
- 42 merged into a wide region. For 41 of these the region keeps growing; 1 stays bounded (rule 37, possibly a composite).
Inspection (rule 139): the growing region is a bubble of the vacuum in the opposite phase,
bounded by outward-moving walls. The collision converts vacuum rather than shedding radiation.
Velocity estimates over a 32-tick window alias for period-3 objects, so momentum conclusions are deferred.
Next: a frozen v0.2 collision test with a contact check, a corrected outcome classifier, period-matched
velocity windows, and object identity matching. Also a frozen test of vacuum-bubble creation.
