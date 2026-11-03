# MIR-REVERSIBLE-LEDGER-001 — where does collision information go? (v0.1-draft)

Status: **outcome-free; frozen at tag `mir-reversible-ledger-001-v0.1-frozen`**. 2026-11-03.
Framing: information-first. The law is reversible, so the information distinguishing incoming
configurations is never lost; the question is *where it is carried* after an interaction —
in the coherences (objects) or in the background (a shadow/residue). Code: `ledger.py`.

## Design
Same rules and R/L choice as COLLIDE-002 (lowest-seed right/left objects with |v| >= 1/8).
Input variable: the impact offset, 64 values (24..87), uniform, so H(I) = 6 bits per rule. N=2048,
T=600. At T, each bounded (width <= 8), exactly periodic cluster is an object, described by
species (orbit-invariant id), internal state (pattern on both layers plus phase), and position.
Anything else (wide, non-periodic, bubble) is residue.
Recoverable fraction f(X) = I(input; X) / H(I) for:
- f_objects: X = all objects' (species, state, position);
- f_internal: X = all objects' (species, state), position ignored. This is the history written into
  the carriers' own internal state;
- f_species: X = species only.

## Hypotheses (frozen)
- H_I1 complete carriers: in every rule with no residue in any of the 64 runs, f_objects = 1.
  (Expected and partly trivial, since positions encode the offset; it serves as a control.)
- H_I2 the residue holds information: in every rule with residue in some run, f_objects < 1.
- Descriptive, the main informational readout: f_internal and f_species in clean rules, i.e. how
  much of the interaction history is embodied in the carriers' internal state rather than only in
  where they are.
- Theorem: no run ends in pure vacuum.
Baseline literature: computational mechanics treats CA particles as information-bearing defects
(Crutchfield & Hanson 1993); this ledger asks the ICP carrier/shadow question of them.

## Amendment v0.1.1
The v0.1 run crashed on numpy-int64 JSON serialization before printing or writing anything; no outcome was seen. The fix is limited to serialization. Tag `mir-reversible-ledger-001-v0.1.1-frozen`.
