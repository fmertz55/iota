# MIR-REVERSIBLE-CLOCK-002: universal (metric-like) or species-specific (medium-like) clock change, sub-light clocks (v0.1)

Status: **frozen at tag `mir-reversible-clock-002-v0.1-frozen`**. 2026-11-17. Code: `clock2.py` (CLOCK-001's tracker,
probes, entry conditions and kappa definitions, unchanged). Requested by the user: "Clock two is needed before we do
anything else."

## Why
CLOCK-001 was valid but uninformative. Every probe that crossed a non-vacuum domain moved at |v| = 1, so kappa = 1 was
forced by the light-cone limit. The question needs sub-light coherences crossing a genuinely different medium.

## Medium (frozen)
A scan of all 14 active rules (first 4 x 4 species, all phases, d = 24..39 step 3; printed domain types only) found
exactly one shadow domain that is neither time-shifted vacuum nor unstructured: rule 37's period-2 (0, 3) domain, on both
sides. Its probes are sub-light (|v| in {1/4, 1/3, 5/12}). **One rule only.** Control: 147 (time-shifted vacuum), both
sides, as in CLOCK-001.

## Validity
- V_lag: in 147L and 147R, >= 2 localized species and every localized transit has kappa_f = kappa_v = 1.
- At least one of 37L and 37R has >= 2 localized species (otherwise not assessable: INVALID).

## Hypotheses (frozen; assessed on 37L and 37R where >= 2 localized species)
- **H_S (the medium acts on clocks):** some localized transit has kappa_f != 1 or kappa_v != 1. Prediction: supported.
- **H_U (universal):** all localized transits share one kappa_f and one kappa_v. **Prediction: not supported
  (medium-like).**
- **H_M (metric-like):** H_U and kappa_f = kappa_v. Prediction: not supported.
- Descriptive: types, kappa by species, front speeds.

## Reading, fixed in advance
If H_S holds and H_U fails, records act like a medium: their effect on clocks is chromatic, so they cannot by themselves
give an achromatic, redshift-like effect in this substrate. If H_U and H_M hold with kappa != 1, that is a metric-like
result, surprising and to be checked for a hidden symmetry before any reading.

## Exposure
Only the medium scan's domain types (above). No transit in rule 37 has been run.

## Limits
One rule, one medium type, 1-D. Clock = exact orbit period (moving clocks only). No Lorentz structure.

## Erratum v0.1.1 (2026-11-17; no outcome existed)
The v0.1 run crashed: a background word ("nodom",) evaluates to the string "nodom", which passed the non-vacuum check
and was used as a domain. Fix: the medium must be a 3-field domain record. Tag mir-reversible-clock-002-v0.1.1-frozen.
