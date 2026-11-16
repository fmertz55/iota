# MIR-REVERSIBLE-ORDER-002: confirmatory replication of ORDER-001 (v0.1)

Status: **frozen at tag `mir-reversible-order-002-v0.1-frozen`**. 2026-11-16. Code: `order2.py` = `order1.py` v0.1.1 plus
three changes only: (1) the mover detector tests clusters up to WMOV = 16 cells wide for an exact orbit (was 8); (2) a fresh
sample seed 20261116; (3) outputs to MIR-REVERSIBLE-ORDER-002. The design, grid, sample sizes, readouts, classes, touched
rule and validity controls are ORDER-001's (see its contract).

## Why
ORDER-001 was INVALID: V_C54 failed because reader soliton packets 9 cells wide (union of the two layers) were filed as
background. SPECIES-001 limits width on layer t only. Its post hoc blob-free reading (RESULT.md) suggested a clear
pattern. This run tests that pattern on new cases with the detector fixed. **Exposure: all ORDER-001 outcomes were seen.**
The predictions below come from them, so this is a replication, not a blind test.

## Pre-freeze checks (exposed material only)
- V0 (rule 91 slice) with the new detector: 64 valid, 32 order (unchanged).
- The RCA54 case that produced a blob in ORDER-001 (X 230a4595d046ec99, alpha 221c851d5cd1c044, beta 3bb251e5c6a5d826,
  d 37, Delta 400, side +1): background empty at all readouts; no order effect; target positions equal.

## Validity controls (unchanged from ORDER-001)
V0 (64 valid, 32 order), V_slot, V_C54 (>= 100 touched RCA54 cases; no order effect at any readout, no background ever,
target-direction movers' (species, position) equal in AB and BA at every readout), V_valid.

## Hypotheses (frozen; all touched cases, no subsetting)
- **H_O (order is recorded)**: >= 1 persistent order case. Supported if >= 5 of 7 eligible pairs. Prediction: 7/7.
- **H_B (the background alone holds order)**: >= 1 persistent background-only case (mover species multisets equal at
  every readout, background differs at every readout). Supported only if **7 of 7**. Prediction: 7/7, with background-only
  fractions of about 0.03-0.3.
- **H_W (order is written into the record's content)**: >= 1 persistent written case. Supported only if 7 of 7.
- **H_N (no shadow, no background order; new)**: in nulls 1 and 5, zero background-only and zero written cases. Supported
  if both hold. Prediction: rule 1 holds order in its movers only; rule 5 is order-blind. 90s is reported only (in
  ORDER-001 none of its cases were touched).
- Descriptive: bits per touched case (order / background / movers / background-only), by pair, side and Delta, plus the
  number of residual ('nodom',) components.

## Limits (as in ORDER-001)
Mover comparison is at the species level; positions and timing are not compared. Background words are coarse. Readouts
are at fixed common times, not asymptotic.
