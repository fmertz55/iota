# ICP Minimal Informational Realization Contract

Version: `0.2-draft`

Date: `2026-07-13`

Status: **controlling discovery contract; ranked outcomes sealed**

Version `0.2-draft` repairs two outcome-free ambiguities found during the first
independent audit of `0.1-draft`. A connected relational role may not use free
topology, so the reference grammar charges one dynamic channel plus one
interaction-relation channel. The proto-object causal endpoint must also be an
outward future consequence rather than the role-persistence predicate itself.
No candidate outcome was generated or inspected before either change.

## 1. Objective

The program is not searching for new physics. It asks whether the smallest
admissible informational construction can generate localized causal organization
whose reachable futures agree with a declared domain of current physics.

The construction objective is:

> Use the fewest informational primitives acting under the fewest atomic laws.
> Among candidates with identical primitive and law counts, prefer the candidate
> that first produces the frozen proto-object in the fewest elementary ticks.

A disagreement with the target physics counts against the construction. It is
not treated as a novel-physics result. Success establishes bounded constructive
realization. It does not establish that information is the unique ontology of
the universe.

## 2. Program stages

The first target is a proto-object, not a particle analogue. A passing
proto-object demonstrates a minimal localized organization that causally
constrains a reachable future. Later target tiers must compare the same frozen
construction with preregistered roles from current physical theories.

The active stages are:

1. define the admissible primitive, law, clock, and proto-object grammars;
2. search the lowest primitive/law complexity shells;
3. identify the best proto-object-producing candidates found;
4. freeze maps to specific current-physics role benchmarks;
5. test reachable futures, interventions, symmetries, conservation behavior,
   composition, scaling, and known failure boundaries; and
6. certify a minimum only after every lower admissible shell is exhausted or
   excluded by proof.

There is no active novel-physics gate.

## 3. Candidate boundary

An informational candidate `C` must declare:

```text
C = (P, L, G, X_0, U, E, M, Phi)
```

where:

- `P` is the primitive inventory;
- `L` is the atomic-law inventory;
- `G` is the declared interaction topology;
- `X_0` is the initial condition;
- `U` is the exogenous-input law, or `none`;
- `E` maps a target initial condition into the construction;
- `M` maps construction states to target observables; and
- `Phi` maps target interventions to construction interventions.

Every state, relation, scheduler choice, random input, lookup entry, constant,
or persistent memory that can change a candidate outcome must occur in this
declaration. A detector may read candidate state. It may not alter candidate
dynamics.

The evaluation harness is not charged only when it is identical across the
compared candidates and demonstrably has no candidate-specific causal effect.
Topology, scheduling, or geometry that changes reachable futures belongs to the
candidate rather than to a free implementation layer.

## 4. Primitive grammar

An informational primitive is one declared binary degree of freedom. It has no
hidden field, substate, precision, behavior table, or persistent identity.

A finite nonbinary state requires enough declared binary degrees of freedom to
encode its alternatives. An unbounded integer, arbitrary-precision real,
target-specific table, or initial state containing future outcomes is
inadmissible.

The primitive record distinguishes:

```text
N_P_kind   number of causally distinct binary degree schemas
N_P_seed   number of nonquiescent primitive instances in X_0
N_P_rel    number of primitive relation schemas in G
```

The three values form the candidate's primitive signature. They are not hidden
inside a single bundled `Iota` count. Within one frozen substrate grammar, the
normalized primary count is:

```text
N_P = binary dynamic channels
    + binary relation channels
    + binary exogenous channels
    + candidate-specific supplied information bits
```

Candidate-specific initial conditions, constants, boundaries, topology entries,
or program data therefore cannot supply free hidden primitives. Repeated uses of
one uniform primitive schema are reported separately as storage and update-work
budgets. Candidates on different ambient substrate sizes are not directly ranked
until substrate cost is frozen. A result is minimal only relative to the
declared grammar and resource envelope unless a later proof covers alternative
substrate grammars.

The `0.2-draft` reference grammar charges two schemas:

```text
event        one binary dynamic channel at each registered locus
predecessor  one binary directed interaction-relation channel
```

Thus its fixed score begins at `N_P = 2`. The same-locus input and write target
are explicit ports of the atomic update law; they do not assert persistence of
an entity. The directed predecessor relation is separately charged because it
changes reachable futures. Its 64 uniform instances, the 64 dynamic storage
bits per layer, and 64 site evaluations per layer are fixed resource budgets,
not hidden reductions of `N_P`.

Candidate-specific initial bits, exceptions, boundary labels, nonuniform edge
entries, or constants are charged as supplied information. A relation generated
uniformly by the frozen group action is charged once as a relation schema and
its instance count is reported. This convention is not a claim that substrate
size or storage is physically free.

The single active initial event is also fixed across every reference candidate.
It is recorded as `N_P_seed = 1` rather than misreported as zero construction
cost. Its address needs no candidate-specific description because translations
are a frozen symmetry and locus `0` is the canonical representative. The score
is conditional on this one-seed budget; candidates with another seed count are
not comparable under `S(C)` until that resource coordinate is expanded.

No continuant may be assumed. Under this draft, a continuant is an entity whose
identity is presumed to persist between ticks without a declared successor
transition. Every observed persistence must be reconstructed from lawful
succession. An undeclared continuation register or helper state is a primitive
violation.

The charged predecessor relation belongs to the timeless topology `G`; it is
not a state value copied from one layer to the next. Same-locus succession is
created by an explicit law write into a fresh output layer, so no entity identity
is presumed to persist through the address label.

## 5. Atomic-law grammar

Each law must be one hundred percent self-contained. Each law must express one
degree of freedom.

The surface statement of an admissible law contains none of these standalone
tokens:

```text
and
but
or
```

The semantic normal form is:

```text
<one governed degree at t+1> := <one declared atomic operation over one
declared local input signature at t>
```

An atomic law therefore has:

- one governed degree of freedom;
- one local input signature;
- one next-state effect;
- one elementary-tick duration;
- no alternative branch;
- no exception;
- no `else` or `otherwise` case;
- no sequential sub-update;
- no invocation of another law;
- no helper function;
- no hidden lookup table; and
- no assumed persistent bearer.

Each branch, dispatcher case, independently removable effect, truth-table row,
exception, or lookup entry is a separate law. A named formula does not count as
atomic merely because it appears on one line. Symmetry-related instances count
as one schema only when a frozen group action generates them without additional
cases.

The law statement, declared input signature, governed degree, and implementation
must agree. Passing the surface-word check is necessary. It is not sufficient.

### Reference production-row normal form

The `0.2-draft` reference search admits only one operator:

```text
EMIT_1_IF_SIGNATURE(p), p in {00, 01, 10, 11}
```

The ordered inputs are `(event at the governed locus, event at its unique
predecessor)` from layer `t`. Each registered exact signature that produces an
event is one law. Rows are mutually exclusive. Every output degree at layer
`t+1` is a fresh binary event opportunity; if no registered row matches, no
event is produced and the output is `0`. This absence-of-production semantics
is part of the grammar rather than an implicit carry or an uncounted `else`
branch.

This grammar deliberately privileges `0` as quiescent absence and `1` as a
produced event. Its law count is therefore not invariant under complementing
the binary labels. A label-complemented system is a different grammar, not a
free relabeling of the same candidate. Any later robustness claim must test that
alternative explicitly; the present minimum is grammar-relative.

No constant writer, negation helper, coordinate query, neighborhood summary,
lookup, callback, time input, detector input, or additional port is admitted.
The 16 subsets of the four production rows exhaust the reference rule space,
with shell sizes `1, 4, 6, 4, 1` for `N_L = 0, 1, 2, 3, 4`.

## 6. Elementary tick

One elementary tick is one causal layer of the frozen atomic-law grammar.
Independent local instances may execute in parallel. An effect produced during
tick `t` may not be consumed by another effect until tick `t+1`.

No candidate may pack a cascade, loop, scheduler sweep, or multiple causal
layers into one tick. Influence may cross at most one declared local relation
per tick unless the longer-range relation is itself charged as a primitive.

`T_proto` is reported in dimensionless elementary causal layers. No conversion
to Planck time, seconds, or an existing IOTA simulator tick is claimed. A
physical-time comparison requires an independently justified clock map; current
IOTA ticks contain ordered subevents and are ineligible until rewritten into
elementary layers.

## 7. Proto-object version 0.2

A proto-object first exists at tick `t > 0` when a finite set of at least two
nonquiescent primitive instances satisfies every condition below:

1. it is localized and connected under the preregistered interaction relation;
2. no qualifying set existed in the candidate initial condition;
3. an identity-independent relational role is realized at `t`;
4. the role remains identifiable after one further elementary tick through a
   declared successor relation; and
5. a matched intervention that breaks only the internal role, while preserving
   primitive states and external conditions, changes the support or probability
   of a preregistered reachable-future variable relative to sham.

Connectedness alone is not a proto-object. Longevity alone is not a
proto-object. The causal constraint on a reachable future is mandatory.

The formation time is:

```text
T_proto = min { t > 0 : PO(C_t) = 1 and PO(C_(t-1)) = 0 }
```

The tick after formation confirms the minimum persistence condition. Formation
time remains `t`. Failure to produce a confirmed proto-object within a finite
horizon is right-censored and recorded as `T_proto > H`. `T_proto = infinity`
is permitted only after an analytic impossibility proof or exact recurrence of
the complete deterministic state needed by the detector.

Carrier replacement is not required at the base proto-object tier. A stronger
carrier-independent tier requires the same causal role to survive replacement
of its local witness.

The future variable used for the causal criterion may not be the role predicate
whose persistence is already required. For the `0.2-draft` reference search,
the identity-independent role is an isolated adjacent active dyad. The two
matched interventions have equal Hamming cost and preserve the local bit
multiset: one relocates the dyad while preserving adjacency, and one relocates a
bit to break adjacency. The causal endpoint is a bit two causal layers later at
the first forward locus outside the intervention window. A difference there is
an outward consequence of the internal arrangement; merely observing or
deleting the dyad does not pass. The exact witness, matching, attribution,
tie-breaking, and intervention algorithms are frozen in
`specs/icp_minimal_realization/v0.2-draft/proto_object_detector.json`.

The matched intervention is eligible only when the first external forward locus
at offset `+3` is quiescent. This makes the shifted sham an isolated dyad rather
than part of a longer active run and gives both arms the same quiescent external
endpoint before evolution.

This contrast is intentionally weak. It establishes sensitivity of an outward
future bit to the relative position of the second event under matched local
rearrangements. It does not by itself identify Boolean synergy, an irreducible
two-event causal mechanism, holistic organization, self-maintenance, or
self-reproduction, and it is not current-physics role recovery. Those require
stronger preregistered tiers.

Version `0.2` is a development definition. Data may motivate a revision. Every
revision creates a new detector version, and all data already inspected become
development data for that later version.

## 8. Candidate comparison

Passing candidates are ranked lexicographically:

```text
S(C) = (N_P, N_L, T_proto)
```

Fewer normalized primitives wins first. With equal `N_P`, fewer atomic laws
wins. With equal `N_P` and `N_L`, the smaller `T_proto` wins. No weighted trade
between these coordinates is permitted. The primitive-accounting components and
the Pareto frontier are also published so the cost structure remains visible.

Deterministic candidates use exact first passage. Stochastic candidates report
the complete first-passage distribution, nonproduction probability, median,
mean, and declared upper quantiles; no single stochastic speed winner is named
until a reliability threshold and reducer are frozen.

The `0.2-draft` reference run is explicitly a bounded pilot. Its eligibility
endpoint is `formation_by_H16`; only candidates with a confirmed proto-object by
tick 16 enter its within-pilot ranking. A no-pass is `T_proto > 16`, not an
exclusion of that law count for unbounded time. Consequently this pilot may name
the best `H=16`-bounded candidate found, but it cannot certify a globally
minimum-law construction or pass over a censored lower-law candidate in an
unbounded-minimality claim.

The phrase `minimum construction` is reserved for a candidate whose lower
complexity shells have been exhausted or excluded by proof. Otherwise the
correct phrase is `best candidate found under the declared search budget`.

## 9. Construction closure

A candidate is closed only when its next state follows from its declared
primitives, atomic laws, topology, initial condition, and exogenous-input law.
It fails closure if it uses:

- an undeclared variable;
- an external oracle;
- a target trajectory or target equation as a lookup;
- a detector output fed back into dynamics;
- mutable execution-order behavior absent from the candidate record;
- an uncharged constant or table;
- a hidden continuation state; or
- candidate-specific author interpretation.

The same candidate description must reproduce from a clean checkout. An
independent implementation must be possible from the frozen description alone.

## 10. Current-physics role recovery

For a frozen target theory `T`, target state `x`, admissible target intervention
`a`, and horizon `H`, the construction criterion is:

```text
M_# P_C^H(. | E(x), do(Phi(a))) = P_T^H(. | x, do(a)).
```

The reachable support must also agree:

```text
M(R_C^H(E(x), Phi(a))) = R_T^H(x, a).
```

Use exact equality for finite enumerable benchmarks. A nonzero tolerance is
allowed only when frozen in advance and attributable to numerical precision or
the declared accuracy of the target theory. One fixed `E`, `M`, and `Phi` must
serve the entire preregistered benchmark tier.

Jensen-Shannon divergence may measure a discrepancy or internal intervention
effect. It is not the ICP thesis and is not a substitute for mapped role
recovery.

## 11. Data-informed search

Development data may guide candidate construction. They may not certify the
candidate that they helped create.

Each search round must record:

- the complexity shell;
- the candidate manifest and hash;
- the development seeds or exact state enumeration;
- the proto-object detector version;
- the search budget and stopping rule;
- every failure and exclusion; and
- which outcomes were inspected before the next candidate was designed.

Before a confirmatory comparison, freeze the candidates, grammar, detector,
maps, horizon, stochastic reducer, exclusions, and held-out partition. Any
data-driven change creates a new version and a fresh held-out partition.

Existing IOTA findings are development evidence. They may inform roles and
detectors. They may not be retroactively ranked in the reference grammar's
elementary causal layers.

## 12. Immediate search boundary

The empty primitive class cannot express an informational distinction. Within
the `0.2-draft` reference grammar, one channel cannot simultaneously supply the
dynamic event degree and the charged interaction relation required by the
proto-object definition. The classes `N_P = 0` and `N_P = 1` are therefore
excluded for this grammar. They are not claimed impossible under every future
informational grammar.

At `N_P = 2`, a zero-law candidate produces no events after the initial layer
under the frozen fresh-output semantics. The first open reference shell is:

```text
N_P = 2
N_L = 1
```

The reference pilot uses a directed periodic cycle of 64 loci, a single
canonical active event at layer zero, no exogenous channel, formation horizon
16, and exact deterministic enumeration. It exhausts all candidates in a shell
before stopping at the first shell containing a pass by tick 16, or stops after
all 15 evaluated `N_L=1..4` candidates are right-censored; the `N_L=0`
candidate remains analytically excluded. That stopping rule applies only to the
frozen `formation_by_H16` endpoint; it does not prove later formation impossible.
Development translations `0..47` and reserved translations `48..63` test exact
translation equivariance and implementation closure. Because the latter are
algebraically implied by the same cycle-translation action, they are reserved
bookkeeping rather than independent confirmation or evidence of generalization.
A meaningful generalization holdout requires a
separately defined population of initial conditions or topologies.

Ranked outcomes remain sealed until the structured validator, exact detector,
detector fixtures, isolated transition engine, candidate enumeration,
development-only runner and result schema, and content-hash run seal all pass.
Stochastic inputs are inadmissible in this reference search, so the stochastic
speed reducer is not applicable.

Finding 080 remains archived and paused unless a later role-recovery tier maps
it explicitly to this contract.

## 13. Current implementation state

The superseded `0.1-draft` artifacts are retained as the outcome-free audit
record. The controlling machine-readable design artifacts are:

```text
specs/icp_minimal_realization/v0.2-draft/candidate.schema.json
specs/icp_minimal_realization/v0.2-draft/lower_shell_exclusions.json
specs/icp_minimal_realization/v0.2-draft/operator_alphabet.json
specs/icp_minimal_realization/v0.2-draft/topology.json
specs/icp_minimal_realization/v0.2-draft/causal_cone.json
specs/icp_minimal_realization/v0.2-draft/proto_object_detector.json
specs/icp_minimal_realization/v0.2-draft/detector_fixtures.json
specs/icp_minimal_realization/v0.2-draft/partitions.json
specs/icp_minimal_realization/v0.2-draft/search_plan.json
scripts/validate_minimal_realization.py
src/minimal_realization/dynamics.py
src/minimal_realization/detector.py
src/minimal_realization/search.py
src/minimal_realization/spec.py
src/minimal_realization/manifest.py
src/minimal_realization/runner.py
src/minimal_realization/cli.py
specs/icp_minimal_realization/v0.2-draft/result.schema.json
```

The seven design choices that blocked `0.1-draft` are explicit in these files.
The executable detector-development fixtures, strict structured validator,
isolated exact engine and detector, canonical 16-candidate enumeration,
development-only runner, and result schema are hash-bound before outcomes may
open. The immutable outcome seal remains `outcomes_sealed`; after it is
committed, a separate committed `development_open` manifest authorizes exactly
one fixed development ledger path. The runner must reject overwrite, any
translation outside `0..47`, any hash drift, and any uncommitted open manifest.
No held-out command is permitted in this version.

The `copy_predecessor_outward_effect` fixture analytically evaluates one
two-layer matched intervention under production rows `01` and `11`. It is
explicit development data. No full single-seed search trajectory, `T_proto`
detector result, candidate ranking, or held-out result has been inspected.

The development runner is preregistered but cannot execute from the immutable
outcome seal. `open-development` first verifies the byte-canonical 16-candidate
manifest, every bound design and implementation hash, a clean worktree, and an
outcome seal present in the current Git commit. It then writes the sole
`development_open` manifest at the registered path without evaluating dynamics.
That manifest must itself be committed before `run-development` will execute.

The run command has no translation, candidate, horizon, or output override. It
evaluates translations `0..47`, records all translation-level detector fields,
requires exact translated-anchor agreement, exhausts the complete first law
shell containing an `H=16` pass, and otherwise stops after `N_L=4` with finite
nonpasses recorded as `T_proto > 16`. It writes canonical JSON exactly once to
`output/minimal_realization/MIR-REFERENCE-SEARCH-001/development_results.json`
under `result.schema.json`; overwrite and partial output are forbidden. A
separately preregistered verifier recomputes only this development ledger and
requires byte equality. No runner or result-verification path in this version
evaluates translations `48..63`.

This gate is a scientific provenance protocol, not an operating-system security
sandbox. Generic transition and detector functions remain importable for unit
testing, but invoking them directly is outside the registered search and cannot
produce a valid ledger. The registered CLI must reject uncommitted inputs,
unregistered offsets or paths, result overwrite, opening-commit code injection,
and any bound-file drift detected before result publication.
