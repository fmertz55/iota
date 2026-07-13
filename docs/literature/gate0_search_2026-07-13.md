# Gate 0 Literature Search - 2026-07-13

Status: initial pre-validation search; incomplete until Gate 0 is frozen

Research stage: performed before any Gate 0 held-out IOTA outcome and after the
decision to separate the operational definition from the Formal Gate. No new
simulator outcome was generated or inspected.

## Terminology map

| Project phrase | Common search terms |
|---|---|
| change in the reachable | interventional distribution shift; causal strength; stochastic reachability; path-space law |
| reachable futures | support of a conditional future distribution; accessible trajectories; probabilistic reachable set |
| interaction-induced information | causal information flow; information-theoretic causal effect; divergence between interventional distributions |
| relational persistence | organizational persistence; dynamic reconnection; temporal reachability; recovery after intervention |
| constraint | entropy reduction; concentration of a future distribution; support reduction |
| counterfactual structure | counterfactual trajectory distribution; path-space measure; cause-effect repertoire |

## Search surfaces

- general scholarly web search restricted where possible to arXiv, publisher
  pages, institutional repositories, and PubMed Central;
- publisher and institutional metadata pages for DOI and bibliographic checks;
- the existing IOTA bibliography and its cited primary works.

Coverage still required before freeze: an independent search in at least one
broad citation index, backward and forward citation chasing from the closest
papers, and a targeted cellular-automata/temporal-network search.

## Exact initial queries

1. `site:arxiv.org intervention future trajectory distributions stochastic dynamical systems information Jensen-Shannon divergence`
2. `site:direct.mit.edu semantic information counterfactual intervention future trajectory distribution Kolchinsky Wolpert`
3. `site:pmc.ncbi.nlm.nih.gov causal information flow interventions Ay Polani 2008`
4. `site:arxiv.org reachable sets stochastic systems probability distribution support information measure intervention`
5. `Ay Polani 2008 Information Flows in Causal Networks primary paper DOI`
6. `Janzing Balduzzi Grosse-Wentrup Schölkopf Quantifying causal influences 2013 primary paper`
7. `Kolchinsky Wolpert semantic information autonomous agency 2018 primary paper PDF`
8. `Lin 1991 divergence measures based on Shannon entropy Jensen-Shannon primary paper`
9. `"interventional distribution" "stochastic dynamical system" causal effect primary research`
10. `"future trajectory distributions" counterfactual intervention dynamical systems information`
11. `"causal strength" divergence interventional distribution dynamical systems`
12. `"relational persistence" stochastic systems intervention organization`
13. `cellular automata coherent structures causal states intervention primary research`
14. `temporal networks reachability intervention dynamic reconnection primary research`
15. `organizational persistence material turnover stochastic dynamical systems primary research`
16. `relational role re-instantiation cellular automaton graph intervention`
17. `"Minimal interaction conditions for the emergence of biological-like organization" authors DOI`
18. `Efficient limited-time reachability estimation in temporal networks DOI`
19. `Spatio-temporal networks reachability centrality robustness DOI`

No date restriction was applied. English-language records were searched. A work
was included when its primary contribution defined or computed interventions on
probability distributions, future path distributions, stochastic reachable
sets, or an information-theoretic measure of causal effect. Mere use of the
words `information`, `future`, or `constraint` was insufficient.

## Closest primary work found in this pass

### Ay and Polani (2008)

`Information Flows in Causal Networks`, DOI
[`10.1142/S0219525908001465`](https://doi.org/10.1142/S0219525908001465).
It defines information flow using post-interventional distributions and
explicitly distinguishes the proposal from observational transfer entropy.
This establishes that an intervention-based information quantity is not itself
novel.

### Janzing et al. (2013)

`Quantifying Causal Influences`, DOI
[`10.1214/13-AOS1145`](https://doi.org/10.1214/13-AOS1145). It measures causal
strength by a divergence between an original distribution and a distribution
after a causal mechanism is corrupted. This is the closest established framing
to the proposed divergence between natural and reference future distributions.
The choice of Jensen-Shannon rather than Kullback-Leibler divergence is a
bounded-support engineering choice unless a stronger scientific distinction is
proved.

### Lin (1991)

`Divergence Measures Based on the Shannon Entropy`, DOI
[`10.1109/18.61115`](https://doi.org/10.1109/18.61115). It establishes the
Jensen-Shannon divergence and its finiteness and boundedness properties. ICP
cannot claim novelty for the divergence itself.

### Kolchinsky and Wolpert (2018)

`Semantic Information, Autonomous Agency and Non-equilibrium Statistical
Physics`, DOI
[`10.1098/rsfs.2018.0041`](https://doi.org/10.1098/rsfs.2018.0041). It uses
counterfactual interventions and consequences for future viability. It remains
a central precedent for any claim that intervening on information-bearing
relations changes future behavior.

### Buzea et al. (2026)

`Life as Counterfactual Geometry: An Adversarial Theory of Biological
Function`, DOI
[`10.3390/e28030255`](https://doi.org/10.3390/e28030255). It explicitly defines
conditional laws over future trajectories, probabilistically accessible future
sets, entropy/divergence properties of those laws, and interventions as
operators reshaping future distributions. Its biological, self-modifying-law
scope differs from IOTA, but its mathematical vocabulary is very close. It must
be discussed alongside the January 2026 Witte preprint before any broad
future-space novelty claim.

### Shi et al. (2026)

`Deciphering Interventional Dynamical Causality from Non-Intervention Complex
Systems`, DOI
[`10.1016/j.xinn.2026.101358`](https://doi.org/10.1016/j.xinn.2026.101358). It
uses the common terms *interventional dynamical causality* and *causal strength*
for dynamical systems. Its goal is inference from observational time series,
whereas IOTA can execute interventions directly, but the terminology and causal
comparison are relevant.

### Jafarpour, Liu, and Chen (2024)

`Probabilistic Reachability Analysis of Stochastic Control Systems`,
[`arXiv:2407.12225`](https://arxiv.org/abs/2407.12225). It confirms that
*probabilistic reachability* already has a control-theoretic meaning involving
high-probability state or trajectory sets. IOTA must use `support of the
conditional future distribution` when that is what it means and must not imply
identity with control-theoretic reachability results.

### Rupe and Crutchfield (2018)

`Local Causal States and Discrete Coherent Structures`, DOI
[`10.1063/1.5021130`](https://doi.org/10.1063/1.5021130). It supplies established
behavior-driven terminology for coherent structures in cellular automata and
shows that observer construction of structure from spatiotemporal fields is an
existing research program. ICP must distinguish its intervention method from
structure discovery by local causal states.

### Williams and Musolesi (2016); Badie-Modiri, Karsai, and Kivelä (2020)

`Spatio-temporal Networks: Reachability, Centrality and Robustness`, DOI
[`10.1098/rsos.160196`](https://doi.org/10.1098/rsos.160196), and `Efficient
Limited-time Reachability Estimation in Temporal Networks`, DOI
[`10.1103/PhysRevE.101.052303`](https://doi.org/10.1103/PhysRevE.101.052303),
establish ordinary temporal-network language for time-respecting paths,
limited-time reachability, bridge importance, and robustness under attack.
IOTA's graph-event endpoints must be compared with this literature and should
not call temporal reachability a new construct.

### Chen (2026)

`Minimal Interaction Conditions for the Emergence of Biological-Like
Organization`, DOI
[`10.1016/j.biosystems.2026.105857`](https://doi.org/10.1016/j.biosystems.2026.105857).
This is a direct contemporary comparator: a stochastic spatial cellular
automaton, persistent organization from local interactions, and operational
entropy/coherence/closure-like observables. Its measurements are primarily
observational and its closure proxy is neighborhood agreement rather than the
IOTA intervention battery, but recurrence in a tuned stochastic automaton is
plainly not sufficient for a broad novelty claim.

## Initial effect on the Gate 0 claim

The common-language operational object is an **interventional divergence between
conditional future-trajectory distributions**. Calling that object an
information constraint does not create a new mathematical principle. The
current candidate endpoint is best described as a bounded measure of
distributional causal effect, accompanied by a signed entropy change.

Any potentially original contribution must therefore lie in a more specific
combination: the relational-role intervention, material-disjoint
re-instantiation observable, ordered temporal realization cuts, or a robust
cross-system empirical regularity. Gate 0 must make that distinction explicit.

## Bibliography actions

Added stable entries for Shannon (1948), Lin (1991), Ay and Polani (2008),
Janzing et al. (2013), Buzea et al. (2026), Shi et al. (2026), Chen (2026),
Williams and Musolesi (2016), and Badie-Modiri et al. (2020). Direct
mathematical comparison remains required before Gate 0 freezes.
