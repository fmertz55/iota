# Minimal-Realization Reference Search - 2026-07-13

Status: pre-outcome search supporting contract `0.2-draft`

Chronology: performed after the outcome-free audit of contract `0.1-draft` and
before any minimal-realization candidate trajectory, detector result, or ranked
outcome was generated or inspected.

## Question and terminology map

The search asked whether a binary local-rule system, a minimal persistent
localized object, a rule-space enumeration, or a causal analysis of a cellular
automaton lookup table is itself new.

| Project phrase | Established search terms |
|---|---|
| informational primitive | binary cell state; Boolean degree of freedom |
| atomic law | local transition rule; Boolean production rule; lookup-table row |
| proto-object | localized persistent structure; glider; coherent structure |
| reachable-future constraint | intervention effect; causal coupling; state-transition graph |
| minimum construction | minimal cellular automaton; exhaustive rule-space search |

## Search surfaces and exact queries

Searches used the scholarly web, publisher pages, journal pages, DOI metadata,
and arXiv. No date restriction was applied. Primary research was included when
it defined or exhaustively analyzed binary cellular automata, localized
persistent structures, self-reproduction, or rule-level causal architecture.

Queries:

1. `site:link.springer.com Langton 1984 self reproduction cellular automata loops primary paper DOI`
2. `site:doi.org elementary cellular automata minimal rules localized structures gliders primary paper`
3. `site:arxiv.org cellular automata emergence localized structures minimal local rule exact enumeration`
4. `site:direct.mit.edu artificial life proto organism causal intervention cellular automata local organization`
5. `Wolfram 1983 Statistical mechanics of cellular automata Reviews of Modern Physics DOI primary`
6. `Cook universality in elementary cellular automata Rule 110 primary paper PDF`
7. `Langton 1984 self-reproduction cellular automata Physica D DOI primary`
8. `Beer 2020 origin autopoiesis Game of Life glider intervention primary DOI`

## Closest primary work

### Wolfram (1983)

`Statistical Mechanics of Cellular Automata`, DOI
[`10.1103/RevModPhys.55.601`](https://doi.org/10.1103/RevModPhys.55.601),
established the elementary-cellular-automaton setting: binary states, uniform
synchronous local updates, exhaustive finite rule spaces, and phenomenological
classes including localized complex structures. The IOTA reference grammar is
much narrower—two ordered inputs and 16 production-row subsets—and uses a
different, explicitly grammar-relative law count. Exhausting that small space
cannot establish novelty for simple rules producing structure.

### Cook (2004)

`Universality in Elementary Cellular Automata`, DOI
[`10.25088/ComplexSystems.15.1.1`](https://doi.org/10.25088/ComplexSystems.15.1.1),
proved that binary one-dimensional Rule 110 supports universal computation.
This is strong prior evidence that a small state alphabet and a uniform local
rule can support very rich behavior. Primitive count alone is not a measure of
the organization or physical relevance of the resulting trajectories.

### Langton (1984)

`Self-reproduction in Cellular Automata`, DOI
[`10.1016/0167-2789(84)90256-2`](https://doi.org/10.1016/0167-2789(84)90256-2),
showed a simplified self-reproducing loop and explicitly separated
self-reproduction from the stronger requirement of universal construction.
It also rejected passive spreading of a single active cell by the transition
rule as self-reproduction because the copying organization resides in the rule,
not the configuration.
The present dyad detector is intentionally far weaker than self-reproduction
and must be called a proto-object rather than an artificial organism.

### Beer (2020)

`An Investigation into the Origin of Autopoiesis`, DOI
[`10.1162/artl_a_00307`](https://doi.org/10.1162/artl_a_00307), used a Game of
Life glider as a toy model of a minimal persistent individual and analyzed
formation and persistence questions. This directly precedes the use of a
localized CA pattern as a minimal organizational toy model. The IOTA detector's
distinctive feature, if useful, is the matched outward intervention criterion,
not the existence of a small persistent pattern.

### Pita (2026)

`How local rules generate emergent structure in cellular automata`,
[`arXiv:2604.00273`](https://arxiv.org/abs/2604.00273), derives causal coupling
architecture from prime implicants of elementary-CA rule tables and validates
the analysis over all 256 rules. It is a preprint and does not use the same
proto-object intervention, but it is the closest current rule-to-causal-
structure comparator. The reference search must report its complete rule table
and may not imply that forward causal analysis of local Boolean rules is new.

Rupe and Crutchfield (2018), already recorded under `rupe2018local`, provide the
complementary observed-dynamics route to localized coherent structures through
local causal states.

## Effect on the preregistration

No novelty is established for binary local dynamics, exhaustive small-rule
searches, localized persistent CA structures, or causal organization derived
from Boolean rules. The `0.2-draft` claim is restricted to a transparent
grammar-relative construction record and a matched intervention whose endpoint
lies outside the role-breaking window. Any later methods claim must compare that
specific intervention and accounting scheme with the works above.

The search also changed the design before outcomes: arbitrary named Boolean
operators were rejected in favor of four explicit production rows, and the
rule-space table, resource envelope, and complete enumeration order were frozen.

## Remaining literature work

Before a confirmatory or current-physics role-recovery claim, perform backward
and forward citation chasing from Beer (2020), Rupe and Crutchfield (2018), and
Pita (2026), plus a dedicated search on causal interventions for cellular-
automaton particles. A post-result search must use the observed rule's standard
Wolfram number or Boolean expression and the ordinary name of its pattern.
