# Direct Dirac-QCA Global-Spectrum Literature Search

Date searched: `2026-07-15`

Search ID: `ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001`

Chronology: **pre-registration and pre-outcome**.  The mandatory anchor works
were named in `SESSION_HANDOFF.md` before this audit.  Searches explicitly
using `doubling`, `pseudo-doublers`, and `Dirac vacuum` were follow-up searches
after deriving the exact zone-edge identity but before finalizing any claim.
No registered candidate input or outcome existed.

## Question

What prior work controls claims about the complete spectrum, quasienergy
branches, doubling or pseudodoubling, local implementability, and the
distinction between a hard-core qubit lift and canonical fermionic
second-quantization of the direct `1+1D` Dirac QCA?

## Sources and query method

Indexes and primary-source hosts:

- general scholarly web index, restricted where possible to `arxiv.org` and
  `journals.aps.org`;
- arXiv abstract, HTML, and version records;
- American Physical Society article and accepted-paper records; and
- publisher DOI metadata for journal status.

Date range: no lower bound; all results available through `2026-07-15` were
eligible.  Priority was given to the exact automaton family, rigorous
one-dimensional QCA structure, causal fermionic lifts, multiparticle Dirac
QCA, and the newest direct treatment of doubling in discrete-time walks.

Exact query strings used:

```text
site:arxiv.org/abs/1212.2839 Quantum Field as a quantum cellular automaton Dirac free evolution dispersion relation
site:journals.aps.org/pra 042211 Mlodinow Brun quantum cellular automata fermions 2020
site:arxiv.org Gross Nesme Vogts Werner index theory one dimensional quantum walks cellular automata 2012
"10.1103/kkz3-fthm" Gupta Short quantum cellular automata
"Fermion doubling in Dirac quantum walks" Gupta Short arXiv
site:arxiv.org "pseudo-doublers" Dirac quantum walks
site:arxiv.org/abs/2006.08918 Mlodinow Brun quantum cellular automaton fermions
site:arxiv.org fermionic quantum cellular automata second quantization one dimensional quantum walk local
"Quantum field theory from a quantum cellular automaton in one spatial dimension" arXiv
site:arxiv.org/abs "Mlodinow" "no-go theorem in higher dimensions"
site:arxiv.org/abs/1212.2839 "dispersion relation" "cos" Dirac automaton
site:arxiv.org "second quantization" "Dirac quantum cellular automaton" one dimension
site:arxiv.org "Causal fermions in discrete space-time" quantum cellular automata
site:arxiv.org "Fermion doubling in quantum cellular automata" 2025
site:arxiv.org "The Dirac Vacuum in Discrete Spacetime"
site:arxiv.org "Quantum cellular automata" "Dirac" "fermionic swap"
"Causal fermions in discrete space-time" Farrelly Short arXiv
site:arxiv.org fermionization one-dimensional quantum walk QCA Mlodinow Brun
```

One query contained the mistyped arXiv suffix `2006.08918`; the correct work
was recovered by title and is `arXiv:2006.08927`.  The typo is retained above
to preserve the actual search record.

## Inclusion criteria

Include a work when it does at least one of the following:

1. defines or derives the same direct two-channel Dirac-QCA law;
2. gives its dispersion, group velocity, continuum regime, or physical claim
   boundary;
3. treats fermion doubling or high-quasienergy Dirac-like modes in
   discrete-time Dirac walks/QCAs;
4. proves a structural result about local implementation or index in one
   dimension; or
5. constructs or analyzes a causal fermionic/multiparticle lift relevant to
   the collision-sector distinction.

Exclude generic quantum-walk applications, secondary summaries, unrelated
uses of “Dirac,” and work whose only overlap is broad information-processing
language.  Search snippets were used only for routing; claims below were based
on primary papers or publisher records.

## Closest primary works and claim effects

### Exact direct automaton and spectrum

Alessandro Bisio, Giacomo Mauro D'Ariano, and Alessandro Tosini, “Quantum Field
as a quantum cellular automaton: the Dirac free evolution in one dimension,”
*Annals of Physics* 354 (2015) 244–264.

- Primary record: <https://arxiv.org/abs/1212.2839>
- Publisher DOI: <https://doi.org/10.1016/j.aop.2014.12.016>
- Relevance: same direct symmetry-derived automaton family; low-mass,
  low-momentum Dirac regime; exact dispersive treatment and unitary-channel
  comparison.
- Claim effect: defeats discovery claims for the law, spectrum, symmetry
  derivation, group velocity, or general Dirac correspondence.

### Pseudodoubling and the modular-energy boundary

Chaitanya Gupta and Anthony J. Short, “Fermion Doubling in Dirac Quantum
Walks,” accepted by *Physical Review A* on `2026-07-01`.

- Accepted-paper record: <https://doi.org/10.1103/kkz3-fthm>
- Primary manuscript: <https://arxiv.org/abs/2601.15885>
- Relevance: defines pseudo-doublers as high-energy states with low-energy
  Dirac-like behavior, distinguishes them from traditional low-energy
  doublers, carries the issue into second-quantized QCA, and proposes a
  different stay-amplitude family to avoid the identified modes.
- Claim effect: the exact identity `U_mu(-pi+p)=-U_-mu(p)` must be called a
  pi-mode pseudodoubler.  The active candidate cannot be called globally
  doubler-free and must not be silently changed into the proposed alternative
  family.

Chaitanya Gupta and Anthony J. Short, “The Dirac Vacuum in Discrete
Spacetime,” *Quantum* 9 (2025) 1845.

- Primary record: <https://arxiv.org/abs/2412.03466>
- Relevance: isolates the extra positive/negative-energy boundary created by
  modular energy in discrete time and the associated pair-creation concern.
- Claim effect: the zone-edge mode is not merely a plotting curiosity if a
  future interacting or filled-sea interpretation is attempted.

Dogukan Bakircioglu, Pablo Arnault, and Pablo Arrighi, “Fermion Doubling in
Quantum Cellular Automaton Models,” `arXiv:2505.07900` (2025).

- Primary record: <https://arxiv.org/abs/2505.07900>
- Relevance: extends doubling analysis to discrete-space, discrete-time QCA
  and discusses the relationship with Nielsen--Ninomiya constraints.
- Claim effect: reinforces that full-zone doubling is an explicit QCA design
  obligation, not something a low-momentum continuum expansion resolves.
- Status boundary: this source was treated as a relevant preprint, not as a
  substitute for the accepted Gupta--Short paper.

### Local implementation and index

David Gross, Vincent Nesme, Holger Vogts, and Reinhard F. Werner, “Index theory
of one dimensional quantum walks and cellular automata,” *Communications in
Mathematical Physics* 310 (2012) 419–454.

- Primary record: <https://arxiv.org/abs/0910.3675>
- Relevance: defines the one-dimensional walk/QCA index and proves that the
  trivial-index class is locally implementable by partitioned unitaries.
- Claim effect: the present two-layer circuit is a specific existence and
  resource witness in a known structural class, not a new general
  partitionability theorem.

### Fermionic and multiparticle lifts

Terence C. Farrelly and Anthony J. Short, “Causal Fermions in Discrete
Spacetime,” *Physical Review A* 89 (2014) 012302.

- Primary record: <https://arxiv.org/abs/1303.4652>
- Publisher DOI: <https://doi.org/10.1103/PhysRevA.89.012302>
- Relevance: causal fermionic evolution, local-unitary decomposition, and the
  relationship between fermionic systems and qubit QCA.
- Claim effect: supports treating a fermionic lift as a separate declared
  construction with parity/encoding conventions, not as an automatic
  consequence of matching one-excitation amplitudes.

Leonard Mlodinow and Todd A. Brun, “Quantum field theory from a quantum
cellular automaton in one spatial dimension and a no-go theorem in higher
dimensions,” *Physical Review A* 102 (2020) 042211.

- Primary record: <https://arxiv.org/abs/2006.08927>
- Publisher DOI: <https://doi.org/10.1103/PhysRevA.102.042211>
- Relevance: a one-dimensional multiparticle QCA matching a quantum walk in
  the one-particle sector and recovering free fermionic QFT in the
  long-wavelength limit; explicit higher-dimensional limitation.
- Claim effect: defeats novelty claims for a generic one-dimensional
  fermionic promotion and underscores that the current hard-core collision
  phases do not themselves establish such a promotion.

## Synthesis

The literature and analytic audit agree on a narrow conclusion:

```text
The active direct law is established prior art with a valid low-momentum Dirac
regime and an exact local qubit realization.  Its complete discrete-time
spectrum contains a high-quasienergy Dirac-like zone-edge partner.  The present
hard-core qubit collision rule is not a canonical free-fermion lift.
```

No novelty is established for the automaton, dispersion, group velocity,
local implementability, pseudodoubler, or existence of fermionic QCA lifts.
The project-level novelty target remains the prospective causal-role and
reproducibility framework described in `SESSION_HANDOFF.md`.

## Post-result follow-up rule

There is no registered result to follow up.  After any future development or
confirmation disposition, rerun searches using the observed common-language
failure or success terms.  Do not use that search to change a frozen endpoint,
threshold, or scenario allocation.
