# Literature record: finite local information capacity (Neukart & Marx) and QMM

- **Finding / gate:** prior-art and methods update for the reversible-shadow line
  (shadow paper, BUDGET line). Not tied to a new gate.
- **Search status:** update (post-outcome; paper supplied by the user, 2026-11-15).
- **Researcher:** D. Clark, with assistant.
- **Sources:** full text of the Research Square preprint (rs-10484305/v1, 26 Oct 2026),
  plus the published Entropy abstract; Crossref metadata for all three keys below.
- **Bibliography keys added** (`shadow_paper/bibliography.bib`, DOIs verified on Crossref):
  - `neukart2026capacity`: Neukart & Marx, *Finite Local Information Capacity in
    Continuum Dynamics*, Entropy 28(11):1209 (2026), doi:10.3390/e28111209
  - `neukart2024qmm`: Neukart, Brasher & Marx, *The Quantum Memory Matrix: A Unified
    Framework for the Black Hole Information Paradox*, Entropy 26(12):1039 (2024),
    doi:10.3390/e26121039
  - `watanabe1960`: Watanabe, *Information Theoretical Analysis of Multivariate
    Correlation*, IBM J. Res. Dev. 4(1):66–82 (1960), doi:10.1147/rd.41.0066

## Version caveat

The published abstract is more cautious than the preprint. It says there is no new
inequality, the sigma-model form is not an effective action derived from the
Hamiltonian, and the test chain uses a single spacing a = 1. Cite the published
version, and do not lean on preprint-only claims.

## What we can use (Iota)

1. **Commuting-diagram defect.** They define deviation as
   D = C∘Φ − Φ_eff∘C, i.e. "evolve, then coarse-grain" minus
   "coarse-grain, then evolve", measured in one common effective state space.
   Shadow reading: a carrier-level description C (keep moving structures, drop the
   background) does not close under the reversible rule, because the interaction
   record sits in what C drops and later changes what C sees. A non-zero defect is
   an information-first statement of "the record outlives its carrier". It can be
   reported as one number per pair and needs no particle vocabulary.
2. **Total-correlation identity (cite `watanabe1960` for the identity).** The sum of
   one-cell entropies minus the block entropy equals the total correlation,
   D(ρ_B ‖ ⊗ρ_x) ≥ 0, which is zero only if the block factorises. This is the formal
   reason per-cell measures cannot see relationally held records (LEDGER/BUDGET
   readings). Neukart & Marx make the same point: averaging local entropies
   "removes a correlation term".
3. **Keep a, d and ℓ separate.** In Iota, a = 1 and d is fixed and exact. The only
   free scale is ℓ, the readout window (w2, w3, ...). BUDGET-001 results that
   depend on the window should be reported as coarse-graining dependence, with the
   matching map held fixed while w varies, and not as a property of the substrate.
4. **Reconstruction loss.** I_loss = D(ρ ‖ R∘C(ρ)) measures information lost by a
   chosen description. It depends on the map, which is the point. It is a candidate
   measure of how much of a record the carrier view cannot recover.
5. **Development chain (§6.2).** Each step has a failure criterion, which matches
   our sealed-contract practice. Useful if a reviewer asks how a toy substrate
   connects to physics claims.

## Prior-art flag

QMM (`neukart2024qmm`) treats space-time cells as memory registers that hold
"imprints" of interactions. This is conceptually close to "interaction records
that outlive their carriers". The differences: QMM is quantum and geometric, and
imprinting is postulated. The shadow work is a classical reversible CA, and the
records emerge in the background state. Neither paper was cited in iota or ICP
before this record.

## Not applicable

Their quantum-truncation machinery (Hilbert-space cutoff, leakage across the
cutoff, Fannes–Audenaert bounds, the Klein–Gordon benchmark) does not transfer.
Iota has no Hamiltonian and no truncation, and it seeks no continuum limit. Their
direction is physics-first: continuum QFT is the target and finite information is
a regulator or capacity. Ours is information-first. Use the paper for method, not
for thesis.

## ICP

No citation added. The paper is about local capacity and continuum matching, not
about how constraint narrows reachable futures. At most, "entropy alone is too
coarse a coordinate" could support a BioSystems revision if a reviewer presses on
entropy-based readings.

## Draft text for the shadow-paper revision

The submitted Complex Systems file (`shadow_paper/complex_systems/clark_shadow_complexsystems.tex`)
was **not** edited. At revision, add something like this to related work:

> Neukart and coworkers' Quantum Memory Matrix postulates that interactions leave
> imprints in finite-capacity space-time cells [neukart2024qmm]. Here an analogous
> persistence of interaction records is not postulated but emerges in a minimal
> classical reversible substrate. In the operational terms of [neukart2026capacity],
> a shadow is a non-zero defect between "evolve, then coarse-grain to carriers" and
> "coarse-grain to carriers, then evolve". Because the record is held in
> correlations rather than in single cells, per-cell entropies miss it by exactly
> the total correlation [watanabe1960].

Matching `\bibitem`s for the inline bibliography of the Complex Systems file:

```latex
\bibitem{watanabe1960}
S.~Watanabe, ``Information Theoretical Analysis of Multivariate Correlation,''
\textit{IBM Journal of Research and Development}, \textbf{4}(1), 1960 pp.~66--82.
doi:10.1147/rd.41.0066.
\bibitem{neukart2024qmm}
F.~Neukart, R.~Brasher, and E.~Marx, ``The Quantum Memory Matrix: A Unified
Framework for the Black Hole Information Paradox,'' \textit{Entropy}, \textbf{26}(12),
2024 1039. doi:10.3390/e26121039.
\bibitem{neukart2026capacity}
F.~Neukart and E.~Marx, ``Finite Local Information Capacity in Continuum Dynamics,''
\textit{Entropy}, \textbf{28}(11), 2026 1209. doi:10.3390/e28111209.
```

## Unresolved gaps

- The full published Entropy text was not read. Only the preprint plus the
  published abstract were available.
- Not read: Neukart, Marx & Vinokur, *Discrete electromagnetism in a
  finite-information space–time framework*, Results in Physics 84:108629 (2026),
  doi:10.1016/j.rinp.2026.108629. It is a further QMM paper and could be checked
  if a referee raises QMM.
