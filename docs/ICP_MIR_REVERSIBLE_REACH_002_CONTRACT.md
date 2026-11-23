# MIR-REVERSIBLE-REACH-002 (v0.1)
Status: **frozen at tag `mir-reversible-reach-002-v0.1-frozen`**. 2026-11-23. Code `reach2.py` (REACH-001's cases,
travellers and slots via reach1.load). Parent: REACH-001 (valid; H_R and H_P 7/7). Its open caveat: after the first
affected traveller, later differences can also travel through that traveller's products.
## Question
Is the reach carried by the background record alone? Each traveller i = 1..6 crosses ALONE (no earlier travellers,
hence no products) at the same slot and time as in REACH-001. It is affected iff its mover-species increment over the
traveller-free base world differs between AB and BA.
## Validity
V_C: RCA54 mean fresh reach = 0 over >= 50 valid cases; >= 80% of cases valid in every group.
## Hypotheses (7 pairs)
- **H_D (direct):** mean fresh reach > 1 in >= 4 of 7 pairs. The background alone conditions several later
  encounters, at delays up to 7 Delta.
- **H_E (most of the reach is background-borne):** mean fresh reach >= 0.8 x REACH-001's mean sequential reach in
  >= 4 of 7 pairs.
Descriptive: affected count by i; fresh vs sequential reach per pair.
## Exposure
REACH-001 outcomes (sequential reach) are known; fresh outcomes are not. A one-case load check printed validity only.
## Limits
Fresh travellers read a background that no earlier traveller has read, so this tests the background's standing
influence, not reuse after reading (REACH-001's persistence result covers that). Species-level increments.
