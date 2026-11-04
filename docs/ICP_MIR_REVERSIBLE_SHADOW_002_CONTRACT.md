# MIR-REVERSIBLE-SHADOW-002 — is the shadow typical, and how much does it hold? (v0.1-draft)

Status: **outcome-free; frozen at tag `mir-reversible-shadow-002-v0.1-frozen`**. 2026-11-04. Code: `shadow2.py`.
Parent: SHADOW-001 v0.2 (rule 37: shadow constrains the probe, 3.84 bits; 11 bubble rules untestable
because the expanding shadow reaches a trailing probe before erasure).

## Probe design (changed)
Same 25 rules, R/L choice and 64 impact offsets. At T=600 (resolution time), erase every resolved
carrier (union-layer clusters, as in SHADOW-001 Part A) and keep the shadow. Then *launch* the probe:
a copy of R's exact free-flight state at T (both layers, so the vacuum phase matches), written at one
fixed site per rule, 24 sites left of the leftmost shadow or carrier over *all* 64 offsets (fixed, so
its position carries no offset information). Both universes (with and without the probe) run 1500
more ticks on N=16384. Y = their difference (shape and position).

## Measures (exact: deterministic maps of a uniform 64-value input)
- only_shadow = H(input | objects): the bits only the shadow holds (the ledger's background share).
- probe = I(input; Y): what the probe's future reveals.
- probe_beyond_objects = I(input; Y | objects) = H(objects, Y) - H(objects).
- capacity ratio = probe_beyond_objects / only_shadow.

## Hypotheses and decision rules (frozen)
- Control: rules with no shadow in any run must give probe = 0; otherwise invalid.
- H_S (typical): `typical` if probe > 0 in at least half of the shadow rules; else `exception`.
- H_C (capacity): `supported` if the capacity ratio is > 0 in at least half of the shadow rules.
- Descriptive: ratios per rule. A ratio of 1 means one probe pass reads everything only the shadow knows.
