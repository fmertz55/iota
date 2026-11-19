# MIR-REVERSIBLE-REACH-001 (v0.1)
Status: **frozen at tag `mir-reversible-reach-001-v0.1-frozen`**. 2026-11-19. Code `reach1.py` (ORDER-002 machinery).
Question: can one background-held order record condition a succession of fresh encounters (reach), and does it survive
them (persistence)? Prior art to keep distinct: damage spreading in CA counts perturbation growth; here the conditioning
bit is held only by the background (ORDER-003 timing_ok cases). Redundancy framing: Zurek's quantum Darwinism (cited as a
framework, not checked here).
Design: see reach1.py docstring. Cases: ORDER-003 timing_ok with read-back (588; 7 pairs) plus 100 RCA54 control cases.
K = 6 travellers.
## Validity
V_C: RCA54 mean reach = 0 over >= 50 valid cases; >= 80% of cases valid in every group.
## Hypotheses
- **H_R (reach):** mean reach > 1 (the record conditions more than one later encounter) in >= 4 of 7 pairs.
- **H_P (persistence):** after all 6 travellers the background still differs between AB and BA in >= 25% of cases,
  in >= 4 of 7 pairs.
Descriptive: reach histogram, affected count by position i, background-difference survival curve.
## Exposure
None (ORDER-003 outcomes only, which select the cases). One-case load check printed validity only.
## Limits
Species-level increments; one traveller sequence per case; ring 32768 with readouts up to 7 Delta + 1600 (<= 7200 ticks).
