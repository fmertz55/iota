# MIR-REVERSIBLE-CLOCK-001: does a record change every clock by one factor (metric-like) or each differently (medium-like)? (v0.1)

Status: **frozen at tag `mir-reversible-clock-001-v0.1-frozen`**. 2026-11-17. Code: `clock1.py` (imports the frozen
`order2.py` world/readout). Approved by the user 2026-11-17 ("let's do the clock ratio test").

## Question (information-first; seed of redshift / time dilation)
Observable redshift is a ratio between clocks: bound coherences (emitters) against free ones (signals). A change that hits
every coherence by the same factor is unobservable from inside. Is the influence of a record (shadow domain) on the
coherences that cross it **universal** (one factor for all, like a metric: gravity-like), or **species-specific** (like a
medium: chromatic)? Only a universal effect could underwrite an achromatic, redshift-like effect.

## Design (frozen; details in clock1.py docstring)
- Media: each eligible rule's standard shadow (first collision in SPECIES-001 order that leaves no movers at T = 600). Its
  left domain for probes from the left and its right domain for probes from the right (14 media).
- Probes: every species of the side, launched just outside the shadow edge at TL in {1000, 1600}, offsets j in 0..7
  (16 entry conditions per species).
- In-medium clock: exact orbit (P', D') of the full-state window at the traveller's leading edge while it is inside the
  domain. kappa_f = P_vac / P' (clock factor), kappa_v = (D'/P') / v_vac (speed factor).
- Types: localized (the traveller stays a <= 16-cell coherence in the medium), front (the difference behind it grows: it
  rewrites the medium), no_entry, short, *_noorbit, placement.

## Validity (frozen)
- **V_lag (exact control):** in 147 and 201 the domains are the vacuum shifted in time (record (1,'vac',1)). By time
  translation invariance a localized traveller there must have kappa_f = kappa_v = 1 exactly. Required on both sides of
  both rules, with >= 2 localized species each.
- At least one non-control medium with >= 2 localized species (otherwise H_U and H_M are not assessable: INVALID).

## Hypotheses (frozen; non-control media 22s 26s 58s 82s 114s, L and R sides)
- **H_U (universal clock):** in every medium with >= 2 localized species, all localized transits (all species and entry
  conditions) share a single kappa_f and a single kappa_v. Supported only if this holds in all such media. **Prediction:
  not supported (medium-like).**
- **H_M (metric-like):** additionally kappa_f = kappa_v for every localized transit. Supported only if all such media pass.
  Prediction: not supported.
- **H_F (records have their own light cone):** in media with >= 2 front species, every front moves at a single speed.
  Supported if >= 2/3 of those media pass. Prediction: open.
- Descriptive: type fractions per medium (how many travellers stay themselves inside a record), kappa values, front speeds.

## Exposure (disclosed)
A feasibility pass (TL = 1000, j in {0, 1}, all species, both sides) printed type counts only: localized clocks are
common in the controls (147, 201) and rare elsewhere (22s R 1, 26s R 8, 82s L 8 of 26 transits; none in 58s, 114s). Most
travellers become fronts. No kappa values or front speeds were printed.

## Limits
1-D second-order CA, one shadow per rule. A coherence's "clock" is its exact orbit period, which is defined but not
unique (internal symmetries). Moving clocks only: SPECIES-001 has no still species, so there is no rest-frame clock.
CA have no Lorentz structure, so kappa_f mixes "rate" and "motion" in a way that a relativistic theory would separate.

## Prior art (screen, 7 OpenAlex queries)
Domain-dependent particle speeds in CA (computational mechanics: Hanson & Crutchfield; embedded-particle models) are
known. Quantum-CA derivations of Lorentz/Dirac behaviour (D'Ariano, Bisio and co-workers) and 't Hooft's CA
interpretation do not test universality of a domain's effect across species. Gorard 2020 derives time dilation from
causal-graph structure in the Wolfram model. No study found that tests whether a CA domain changes all particles' clocks
by one factor.
