# MIR-REVERSIBLE-LEDGER-001: where collision information goes (2026-11-03)
Frozen tag v0.1.1. The v0.1 run crashed on serialization before any output.

## Frozen result (25 rules, 64 impact offsets each, H(I) = 6 bits)
- No run ended in pure vacuum (theorem).
- H_I1 complete carriers: SUPPORTED. In all 13 rules with no residue, the outgoing coherences
  carry all 6 bits (f_objects = 1).
- Where in the carriers: f_internal = 0 in 10 of the 13 rules, so the interaction history is
  carried only by *where* the coherences are, not by their internal state. In rules 123, 183
  and 237, f_internal = f_species = 1/6: exactly 1 bit of the history is written into *which kind*
  of coherence leaves (these are the transmuting rules).
- H_I2 the residue holds information: FALSIFIED by one rule (143: residue present, objects
  still carry 6/6). In the other 11 residue rules the coherences carry 0-89%, and the rest sits in the
  background (wide or non-periodic material, bubbles).

## Audit (exploratory)
- All 12 residue rules have an active vacuum (f(000)=1), as do all bubble rules.
- Rule 5 shows residue in all 64 runs and f_objects = 0. Its coherences may exceed the width-8
  object window at T, which would make this a detection artifact; to be checked before interpreting.
- f_objects = 1 in the clean rules is partly trivial (positions encode the offset). The
  informative readouts are the 1-bit internal record and the background share in residue rules.

## Information-first reading
A reversible substrate conserves the interaction's information, but there are two routes:
1. carried by the coherences, overwhelmingly as relational information (where they are relative
   to each other); occasionally 1 bit is embodied in the carrier's own identity;
2. deposited in the background as a shadow, which happens only where the background is itself active.

## Lay version
When two information-coherences meet, nothing is lost, but the record of how they met has to go
somewhere. In about half the rules the two coherences leave carrying the full record, almost
entirely in *where* they end up; in three rules they also keep one bit of it in *what they turn into*.
In the other half, part of the record is left behind in the background, like a footprint in the
vacuum. That only happens where the background is itself active.
