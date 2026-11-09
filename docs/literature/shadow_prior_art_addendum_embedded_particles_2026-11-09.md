# Prior-art addendum: embedded-particle models (for the PREDICT line), 2026-11-09

Addendum to `shadow_prior_art_review_2026-11-04.md`. That review was about the *record* claim (a background holds what
the carriers did not take away). The new PREDICT line asks something else: does a compact description D of a shadow
predict how it responds to probes that were never used to build D? For that question the direct precedent is one the
review and the paper do not cite. This note records it and states the difference.

## Records checked (2026-11-09)
- Crossref record for 10.1007/BFb0056903: Hordijk, Crutchfield & Mitchell, "Mechanisms of emergent computation in
  cellular automata", *Parallel Problem Solving from Nature, PPSN V*, LNCS 1498, Springer 1998, pp. 613-622.
- OpenAlex: "Embedded particle computation in evolved cellular automata", same authors, *Proc. Conference on Physics
  and Computation* (PhysComp '96), 1996; no DOI (Santa Fe Institute working paper; PDXScholar compsci_fac/118).
- Full text read: the authors' PDF of the 1998 paper (melaniemitchell.me/PapersContent/mecca.pdf, 12 pp.). The 1996
  paper was not read. Its abstract describes the same model class and evaluation.
- One step forward from the 1998 paper: all 63 citing works in OpenAlex, screened by title (abstracts read for the
  three below). Relevant: Hordijk, Shalizi & Crutchfield 2001 and Pivato 2007, defect particle kinematics (both already
  cited); Pivato 2006, algebraic invariants for crystallographic defects (not cited); Becker, Durand-Lose et al.,
  "Abstract geometrical computation 10" (ACM ToCT 2021, doi 10.1145/3442359; arXiv 1804.09018). Signal machines are the
  idealized limit of a particle model, with dimensionless signals at constant speeds and collision replacement rules.
  They are the formal precedent for a *compositional collision law*, but they are a model of computation, not a
  description extracted from a CA and tested against it. Also: Marques-Pita 2026 (arXiv 2604.00273), which derives
  emergent-structure mechanisms forward from the ECA look-up table rather than from observed dynamics; adjacent, not
  a precedent. No citing title reports a phase-resolved, deterministic or held-out-probe test of a particle model.
  This is a title screen of one citation step, not a full reading.
- Also in this family and not cited by the paper: Das, Mitchell & Crutchfield 1994, "A genetic algorithm discovers
  particle-based computation in cellular automata" (PPSN III, doi 10.1007/3-540-58484-6_278); Crutchfield, Mitchell &
  Das 1998, "The evolutionary design of collective computation in cellular automata" (arXiv adap-org/9809001).

## What the 1998 paper establishes (from its text)
- An *embedded-particle model* of a CA has two parts. One is a catalog of regular domains, particle types (with
  temporal period and velocity) and pairwise particle interactions with their results. The other is a particle
  distribution at the "condensation time" t_c, from which the model starts.
- The model runs at the particle level alone. It computes geometrically when the next pair meets, looks up the result
  in the catalog and replaces the pair, without consulting the cells.
- It rests on five stated simplifications: (1) the dynamics before t_c are ignored; (2) particles have zero width;
  (3) interactions are pairwise only; (4) interactions are instantaneous; (5) the result of a collision depends on the
  two particles' phases, but the model replaces that dependence with a random choice weighted by result frequencies
  estimated from 10^4 random initial conditions.
- Evaluation: the model's *average task performance* (density classification, synchronization) is compared with the
  CA's, for ten GA-evolved CAs. The agreement is close. Discrepancies are traced to the simplifications, and the
  authors name "taking particle phases into account" as the next improvement.

So the idea that a domain-and-particle catalog with an interaction table *predicts* a CA's behaviour without the
microstate is theirs, not ours. So is the observation that collision outcomes depend on particle phase. Our design
inherits both, and the paper must say so.

## What PREDICT would add (the claim to make, if the tests pass)
| | Embedded-particle models (1996/1998) | PREDICT line |
|---|---|---|
| Substrate | Irreversible, GA-evolved binary r=3 CAs | Reversible second-order (Fredkin) ECAs, with exact information accounting |
| Object described | Particles moving through domains | A composite that carries memory (a shadow: walls, domains and phases left after a collision, carriers erased) |
| Phase | Averaged out (stochastic outcomes) | Explicit fields of D (wall clock phases, vacuum tick phase), with age, so outcomes are deterministic |
| Fit | Interaction frequencies estimated on the same random ensemble the model is judged on | Interaction tables measured on isolated walls; whole-shadow responses predicted to the cell |
| Criterion | Statistical agreement in task performance | Exact screening-off: I(history; response \| D_min, probe) = 0, over all histories in the set |
| Which description | Chosen by the analyst | Minimal field subsets found by a pre-registered exhaustive search on discovery probes, then frozen |
| Generalization | Same task ensemble | Held-out probe species, phases and arrival times, plus second-probe closure (D' stays in the language) |
| Nulls | None stated | Rules where the claim should fail |

## Consequences for the paper and the PREDICT contracts
1. Cite Hordijk, Crutchfield & Mitchell 1998 (and the 1996 PhysComp paper) in the related-work section, next to Hanson &
   Crutchfield and Hordijk-Shalizi-Crutchfield 2001. Describe them as the precedent for particle-level prediction.
2. Do not claim that "a particle-level description predicts CA behaviour" is new. The claim is narrower: in a
   reversible substrate, a *pre-registered minimal* description of a memory-bearing composite screens off its history
   *exactly*, on probes held out from its construction, and phase is the field that turns their stochastic table
   into a deterministic one.
3. Their simplification (2), zero-width particles, and their pre-condensation transient are exactly what
   DESCRIBE-001 must not assume. D has to rebuild both layers cell for cell, debris and wall interiors included.
4. When PREDICT reaches the compositional law (isolated-wall scattering tables predicting whole-shadow responses),
   cite signal machines (Durand-Lose line) as the idealized form of such a law.
5. Their simplification (4), instantaneous interactions, maps onto our interior crossing shift (the 1-cell delay in
   rule 147). In PREDICT that delay is measured, not assumed away.
