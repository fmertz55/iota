# Outline: Physical Review E submission (draft 0, 2026-11-23)

**Working title:** Breaking integrability makes reversible cellular automata remember the order of events, in the background

**Author:** Douglas Clark, Independent Researcher

## One-sentence claim
In one-dimensional second-order reversible cellular automata, the integrable rules RCA54 and RCA201 are exactly blind to
the order of two interactions (the known Yang-Baxter result). Breaking integrability makes the dynamics record that order.
How much is recorded, and whether it is held by the background rather than the outgoing particles, tracks the
inelasticity of collisions. A background-held order record is read back and reused by later particles.

## Abstract (about 200 words, to be written)
Problem: integrability breaking is studied through charges, thermalization and transport; what the dynamics *remembers*
is not measured. Approach: matched worlds that differ only in the order of two collisions (exact space-time translates);
order information counted in outgoing particles vs background. Results: C1-C4 below with numbers. Controls: two
integrable rules give exactly zero.

## Claims, with the evidence each rests on (all pre-registered; frozen tags in the repository)
- **C1 Integrable zero (control, known).** RCA54 (second-order Wolfram 250) and RCA201 (second-order Wolfram 5):
  0 order bits in 772 and 778 touched cases; for RCA54 also target positions equal in AB and BA (ORDER-002).
  Cite Ablowitz et al. 2005.
- **C2 Order memory tracks integrability breaking (headline).** 24 testable rules within table distance 3 of RCA54:
  Spearman rho(elasticity, order bits) = -0.67 (p = 3.4e-4); rho(elasticity, background bits) = -0.72 (p = 6.3e-5);
  clean-vs-inelastic split 13/14 (BREAK-002). Elastic but non-integrable rules (254, 50) record order only in the movers.
- **C3 The background holds it, sometimes alone.** 7 shadow-forming rules: 0.82-0.99 order bits per case, 0.45-0.95
  of them readable from the background, 0.03-0.22 from the background alone (ORDER-002).
- **C4 The background record is causally live and reusable.** With movers identical in species, position and delay
  (710/823 cases), a later particle reads the order back (588 cases; RCA54 0/1470) (ORDER-003). One record conditions
  2.7-5.8 of 6 successive encounters and persists in 97-100% (REACH-001); crossing alone, with no earlier products,
  2.4-5.2 of 6 (REACH-002; >= 80% of the sequential reach in 4/7 rules).

## Sections
I. Introduction: integrability breaking in RCA54 and its observables; order-invariance <=> Yang-Baxter; the open
   question of where history goes when it fails. One paragraph of motivation (information-first view).
II. Model and methods: second-order reversible ECA; **convention table** (our Wolfram numbers vs Bobenko RCA54/RCA201;
   our "201" pair is not RCA201); particle catalog (SPECIES-001); swap design and exact slot translation; coarse
   readout (movers / background words); touched criterion; order bits; elasticity (v2); pre-registration and validity
   controls.
III. Results: A. Integrable zero (C1). B. Order memory across the RCA54 neighbourhood (C2). C. Where the order is held
   (C3). D. Read-back and reach (C4).
IV. Discussion: elastic non-integrable rules; relation to damage spreading, active information storage and quantum
   Darwinism (redundancy as future work); limits.
Appendix: A. The invalid first run and its fix (ORDER-001), and the failed elasticity proxy (BREAK-001). B. Sample sizes
   and validity checks per run. C. Code and data availability (repository, tags).

## Figures (5)
1. Design: AB vs BA space-time diagrams for one shadow rule and for RCA54.
2. Headline: order bits and background bits vs elasticity (24 rules), with the integrable zeros marked.
3. Partition per rule: movers / background / background-only (shadow rules, nulls, controls).
4. Read-back and reach: fraction read back; sequential vs fresh reach per rule; persistence after 6 encounters.
5. (Appendix) Validity: slot-equivalence checks, control distributions.

## Left out on purpose
CLOCK-001/002 (separate question), SHADOW capacity results (cited to the Complex Systems paper), redshift, ICP beyond
one paragraph.

## To do before prose
1. Bootstrap confidence intervals for all bit estimates (from the stored per-case outputs; no new runs).
2. Figure scripts (figure-style).
3. Check Bobenko et al. 1993 and the RCA201 identification against the original paper.
4. Check PRE length and format rules and arXiv endorsement.
