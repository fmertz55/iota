# MIR Exact-Orbit Pre-Result Literature Search — 2026-07-13

Status: outcome-free search performed before any registered candidate layer
after `H=16` was generated or inspected

Search date and timezone: 2026-07-13, America/New_York

Search surface: OpenAI web-search index with primary publisher and arXiv pages
used for the scientific comparison.

## Question

The search asked whether following a deterministic finite cellular automaton to
an exact repeated state is novel, whether an arbitrary horizon can support an
asymptotic conclusion, and which state must recur for this detector.

## Exact queries

1. `primary paper finite cellular automata exact orbit recurrence periodic boundary deterministic`
2. `primary paper one-sided binary cellular automata 16 Boolean rules classification periodic ring`
3. `primary paper exhaustive cellular automata state transition cycle detection finite configurations`
4. `primary paper cellular automata nilpotency finite periodic configurations decidability`
5. `Richard P Brent 1980 cycle detection algorithm primary paper DOI`

The earlier post-result search also supplied the exact queries and primary
comparators recorded in
`minimal_realization_result_followup_2026-07-13.md`.

## Primary comparisons

Tadaki and Matsufuji, *Periodicity in One-Dimensional Finite Linear Cellular
Automata* ([DOI](https://doi.org/10.1143/ptp/89.2.325)), analyze periodic
trajectory structure for finite Rule-90 cellular automata and show that periods
depend strongly on system size. Exact finite-orbit analysis is established
practice, not a novel method.

Alonso-Sanz and Bull, *Elementary Cellular Automata with Minimal Memory and
Random Number Generation*
([DOI](https://doi.org/10.25088/ComplexSystems.18.2.195)), explicitly enumerate
16 two-input Boolean feature maps on periodic rings. Those maps supply temporal
memory features layered onto separate elementary spatial dynamics; they are not
an equivalent 16-rule spatial CA family. The comparison removes novelty from
the Boolean-map count, not from the present grammar or detector.

Dekking, van Driel, and Fey, *Stability in Random Boolean Cellular Automata on
the Integer Lattice* ([primary manuscript](https://arxiv.org/abs/0704.2183)),
study all 16 two-input maps and circular-lattice stabilization in an
inhomogeneous Boolean-CA setting. Their neighborhood and per-cell rule
assignment differ from this uniform directed-predecessor grammar. Their
recurring `0110` motif also shows that the bit motif alone is not a novel object
definition.

Eppstein, *Searching for Spaceships*
([arXiv](https://arxiv.org/abs/cs/0004003)), demonstrates that localized-pattern
search conclusions are conditional on declared state-space bounds. By analogy,
not as a result proved by that paper, the present continuation can replace a
finite horizon only when exact recurrence is reached. Its one-million-layer cap
remains a resource-censoring horizon, and the underlying search idea is
standard.

Brent, *An Improved Monte Carlo Factorization Algorithm*
([DOI](https://doi.org/10.1007/BF01933190)), describes the power-of-two
checkpoint cycle-finding strategy adapted by the streaming runner. The custom
joint seeded/comparator state, cone phase, and detector-before-repeat order are
internal derivations, not consequences of Brent's paper.

Kari, *The Nilpotency Problem of One-Dimensional Cellular Automata*
([publisher](https://epubs.siam.org/doi/10.1137/0221036)), proves undecidability
for a general infinite one-dimensional CA property. That theorem does not make
this fixed 64-locus, 15-rule, one-orbit question undecidable. Conversely, the
finite-state argument gives eventual recurrence but not a practical runtime
bound.

Rupe and Crutchfield, *Local Causal States and Discrete Coherent Structures*
([arXiv](https://arxiv.org/abs/1801.00515)), reinforce that other coherent-
structure definitions can be domain-relative. Exact rejection of this dyad
detector would not reject those alternatives.

This search did not locate a primary source classifying exactly the present
uniform, one-sided, two-spatial-input, point-seeded 16-rule family. The cited
16-map systems are useful comparisons but are not equivalent classifications;
no novelty inference is made from that search gap.

## Effect on the frozen design

The literature comparison and the project's own formal derivation fixed five
cautions before outcomes:

1. recurrence uses the joint seeded and baseline states because the baseline
   can evolve under row `00`;
2. a repeated natural state is conclusive only after the forward cone has
   saturated the 64-cycle;
3. full state equality, not hash equality, is the recurrence proof;
4. the one-million-layer operational ceiling produces an incomplete record,
   never an infinity claim; and
5. the inherited local v0.2 predicates require a separately named temporal
   extension beyond `H=16`, including finite-`C64` wrap and saturation.

The recurrence state and translation-commutation proof are internal formal
arguments. The cited literature establishes comparison context, not the
correctness of those custom arguments. A pass at or after cone saturation can
be a finite-ring recirculation effect and cannot be generalized to a larger
ring or infinite line.

No novelty claim is established for finite-orbit enumeration, Boolean-rule
enumeration, or cellular-automaton falsification. A contribution, if useful, is
limited to the transparent linkage between the fixed relational detector,
matched intervention, complete joint-state certificate, and outcome chronology.
