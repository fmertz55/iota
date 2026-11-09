# MIR-REVERSIBLE-INVENTORY-001: result (2026-11-09)

Frozen tag mir-reversible-inventory-001-v0.1-frozen (534e08c). Data: results.json, run.log, inventory001_spacetime.png.
Run: 4 min 41 s, 4 workers.

## Frozen verdict: VALID. H_S not supported (1/6). H_D not supported (1/6).
- V0-V5 all pass (V0: 28/28 match PHASE-001; V1 symmetry; V2 nulls: 1 and 90s no residue, null 5 all movers).
- Eligible (H_C > 0 and open runs <= 1/4 of shadow runs): 139 209 58s 114s 182s 186s (n_E = 6).
- H_S (contact phase selects species, I_word > 0): only 186s (0.4 of 0.4; disordered, edge speeds only). Need 3.
- H_D (phase wholly species): only 186s. In 139, 209, 58s, 114s, 182s all of H_C goes to H_detail.
- Disclosure correction: the contract quoted 37's open fraction as 46/194 = 0.237. The frozen code divides by shadow runs
  (pure-mover runs excluded): 46/180 = 0.256, so 37 is not eligible. Had it been: I_word 3.24 > 0, H_detail 0.62 > 0,
  giving H_S 2/7 and H_D 1/7. Verdicts unchanged.

## Descriptive (question 1: is a shadow a bound state of a small alphabet?)
- Yes, in most rules, and the alphabet is tiny. Settled in all runs, with one word per rule: 147 33 123 139 209 22s 26s
  58s 82s 94s 114s 218s (201: 2 words; 91 exposed: 4). Per rule: 1-2 domain species, 2-5 wall species.
- Anatomy of the common word: two domains meeting at a **static central wall** (speed 0), with outer walls running into
  the vacuum at +-v (147, 201: phase-shifted vacuum domains, +-1/4; 58s, 22s: periodic domains, +-1). The static wall
  is the stationary record and the domains are the spreading part (picture).
- No small-alphabet description: 143 171 213 241 (open in 208/224: light-cone expansion with fragmenting interior),
  151 233 (16/48 open), 154s 182s 186s (disordered in all runs), 37 (46 words in 134 settled runs; 46 open).
- Wall budgets (invariant rules) are a function of wall species in 11/12 eligible rules (all but 218s, where one wall
  species carries two averaged budgets). Descriptive only.

## Descriptive (question 3: carriers hidden in the record)
- 54s: the whole PHASE-001 record (2.5 bits) is carried by movers; rec = 0. **54 has no shadow** in this ensemble.
- Carried by movers: 151, 233 2.19 of 4.19; 37 1.11 of 5.02; 186s 0.5; 139, 209 0.25; null 5 0.625 (all). 0 elsewhere.
- The record held by the coarse word, rec_word = I(in; word | O, M): 37 2.03, 91 0.5, 201 0.34, 0 elsewhere.

## Reading
A shadow is mostly one bound state per rule: a static wall flanked by two growing domains. The contact phase gates
whether it forms (PHASE-001), but it does not choose *which* bound state forms. Where the phase is kept, it sits below the
species level, in internal detail of the same walls and domains (PHASE-001 found the full residues always distinct, so it
is not pure translation). The record is placement plus sub-species detail, not species identity. 91 (phase = drift
direction = wall species) and 37 (many words) are the exceptions, not the rule. Rule 54 must be removed from the shadow
list, and 151/233 records halved, in any paper table that counts residue bits as shadow bits.

## Lay version
When two travellers collide, most rules leave the same kind of mark every time: a fixed seam with two growing patches
on either side. What differs between collisions is fine detail of that seam, not the kind of mark. One rule's "mark"
turned out to be nothing more than travellers the detector had missed.
