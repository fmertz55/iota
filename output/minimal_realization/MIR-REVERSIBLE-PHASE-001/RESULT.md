# MIR-REVERSIBLE-PHASE-001: result (2026-11-09)

Frozen tag mir-reversible-phase-001-v0.1-frozen (7434356). Erratum: docs/ICP_MIR_REVERSIBLE_PHASE_001_ERRATUM.md.
Data: results.json, run.log. Run: 1 min 40 s, 4 workers.

## Frozen verdict: INVALID (V2 mis-specified); H_G, H_I, H_F not decided
- V0 (28/28 match SHADOW-009), V1 (one shape and status per contact class), V3 (window saturated), V4 (no edge hits),
  V5 pass. V2 fails: null rule 5 has 64 residue runs (2 shape types moving rigidly at +-0.33), as SHADOW-009 already showed.
- Everything below is **descriptive and post hoc**, not a frozen verdict.

## Descriptive (24 unexposed shadow pairs; 91 exposed)
- Gate: G = I(res; phi | sp) > 0 in 24/24. The contact phase decides whether a record forms.
- Gate only (H_C = 0; per species pair a single phase class leaves residue): 147 201 33 123 22s 26s 82s 94s 154s 218s.
- Phase available (H_C > 0): 37 139 143 151 171 209 213 233 241 54s 58s 114s 182s 186s (14). In all 14, H_place = 0:
  distinct contact classes always give distinct residues, never a displaced copy. 91 (exposed) behaves alike (0.5 of 0.5).
- I_rec_S (record bits held by shape, against only): 37 4.34/5.02, 151 and 233 1.19/4.19, 58s and 114s 1.94 of
  6.31/5.69; the rest of each record is placement.

## Why the descriptive result is weak
1. The shape key is the full cropped residue, so any internal difference counts as a different shape. "Never kept as
   placement" was close to guaranteed by the key and says little about domain or wall species.
2. Rigid movers (both edges at one speed, as in null 5): 13 runs in 37, 32 runs each in 201, 139, 209. These are likely
   unrecognised carriers and would inflate the internal-state count.

## Reading
Contact phase is the gate of every record here: it decides shadow vs pass-through in every pair. Whether it also selects
domain or wall *species* is not answered, because the key is too fine. That question is the wall/domain species
inventory (handoff direction 1), which must also separate the unrecognised carriers.

## Lay version
When two travellers meet matters more than who they are: in every rule tested, their step at the moment of meeting
decides whether they leave a mark at all. Whether that step also changes what kind of mark is left is still open.
