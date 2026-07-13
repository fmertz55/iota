# MIR Exact-Orbit Falsification Contract

Version: `0.1-draft`

Base contract: `ICP Minimal Informational Realization Contract 0.2-draft`

Search ID: `MIR-EXACT-ORBIT-001`

Status: **outcome-free design frozen; layers after 16 remain sealed**

Data class: **development continuation**

## 1. Purpose

The bounded reference search found no registered proto-object by layer 16 in
any of the 15 nonempty production-row rules. That result is right-censored. The
present continuation asks the sharper falsification question:

> Does any rule in the complete frozen 16-member production-row family ever
> produce the exact-orbit v0.1 extension of the inherited proto-object from the
> canonical one-event seed against the all-zero initial comparator on the fixed
> directed `C64` cycle?

This protocol changes no primitive, law, topology, seed, initial comparator,
local role predicate, succession predicate, intervention, endpoint, or
tie-breaking rule. It does extend the detector's registered temporal domain
beyond the inherited `H=16` limit and defines forward-cone wrap and saturation
on `C64`. That prospective extension is versioned as
`MIR-ISOLATED-DYAD-OUTWARD-EFFECT-EXACT-ORBIT-V0.1`; its inherited local
predicate is `MIR-ISOLATED-DYAD-OUTWARD-EFFECT-V0.2`. It replaces a finite
horizon with an exact deterministic stopping condition only for candidates
that reach pass or recurrence before the resource ceiling.

The empty rule remains analytically excluded. All 15 nonempty rules are traced;
there is no shell stopping.

## 2. Outcome-aware status

This is not confirmation data. The `H=16` outcome and its post-result failure
anatomy are already known, and choosing this continuation was
outcome-contingent. It follows the same deterministic trajectories rather than
drawing a new sample or replication. The freeze is prospective only for
previously unseen layers `t >= 17` under the versioned temporal extension.

Before evaluating any new layer, the implementation must recompute every
canonical-origin detector field through layer 16 and compare the result with
the committed parent ledger. Any disagreement is an implementation failure,
not a scientific outcome.

The completed parent search is archived at Git commit
`4e999bb7ef48cbf10a0a4e15c3e708c3ea1c6f9f` and tag
`mir-reference-search-001-v0.2-complete`.

## 3. Frozen inherited system

For each nonempty production-row subset `R`:

- the lattice is the directed periodic cycle with 64 loci;
- the canonical seeded state is one active event at origin `0`;
- the matched baseline is the all-zero state;
- updates are exact synchronous fresh-output transitions;
- the two ordered inputs are `(self, predecessor)`;
- the four possible production signatures are `00`, `01`, `10`, and `11`;
- the detector is `MIR-ISOLATED-DYAD-OUTWARD-EFFECT-EXACT-ORBIT-V0.1`, which
  inherits the v0.2 local predicates and extends their formation-time domain;
- sham is `110 -> 011` within the registered window;
- role breaking is `110 -> 101` within the registered window;
- the external `+3` guard must be zero-valued/event-absent at formation;
- both intervention arms evolve for two exact normal layers; and
- the endpoint is the exact bit at anchor `+3`.

Only origin `0` is evaluated for any registered candidate trajectory. No
candidate translation in `1..63` is run by this continuation. In particular,
reserved offsets `48..63` remain untouched. Outcome-free unit tests may rotate
disclosed synthetic fixtures; those are not candidate evaluations or outcomes.
The all-zero comparator is an initial condition, not necessarily an invariant
or quiescent background: a rule containing row `00` can evolve it.

Translation equivalents are formal algebraic corollaries, not independent
data. For every cycle rotation `tau_k`, the uniform local update satisfies
`F_R(tau_k X) = tau_k F_R(X)`. Forward distance and cone eligibility are
preserved when seed, anchor, successor, and endpoint are rotated together;
the same-anchor-before-`+1` successor order is origin-relative; and the two
bit replacements, two intervention evolutions, and `+3` endpoint commute with
the same rotation. Thus every all-time origin-`k` trace is the rotation of the
origin-`0` trace. This is a proof from the frozen operations, not an empirical
evaluation of offsets `1..63`.

## 4. Complete deterministic recurrence state

Write the seeded and baseline states at layer `t` as `S_t` and `B_t`. The
detector's forward cone is still growing before it covers the cycle, so the
complete recurrence state is:

```text
Z_t = (min(t, 63), S_t, B_t)
```

The cone first covers every locus at formation layer 63. A repeat of only
`S_t` is insufficient because a rule containing row `00` can evolve the
baseline. A repeat of `(S_t, B_t)` before layer 63 is also insufficient because
new anchors can become detector-eligible as the cone grows.

After layer 63, exact equality of the two full unsigned 64-bit states is
sufficient. The natural successors and both two-layer intervention futures are
deterministic functions of that state and the fixed rule. No hash, local
window, active count, detector summary, or separately aligned component cycle
may substitute for full joint-state equality.

## 5. Per-layer evaluation

At every formation layer beginning with `t=1`, in ascending order:

1. evolve the seeded and baseline states by one exact registered layer;
2. enumerate anchors by smallest forward distance from origin `0`;
3. require the isolated dyad and matched-baseline attribution;
4. select a same-anchor or `+1` successor in the frozen order;
5. require all formation, successor, endpoint-cone, and `+3` guard checks;
6. construct the frozen sham and breaking states;
7. evolve both intervention arms by two exact layers;
8. compare the exact outward endpoint bits;
9. stop the candidate immediately on the first complete pass; and
10. only after checking the detector, test the full recurrence state.

The first complete pass is the exact `T_proto`. First dyad formation or first
succession alone is diagnostic, not a pass.

## 6. Streaming recurrence search

The registered runner uses a deterministic power-of-two checkpoint schedule
after cone saturation, equivalent to a streaming Brent cycle search:

- layer 63 establishes the first full-cone checkpoint;
- every intervening layer is evaluated by the detector before comparison;
- exact equality with the current checkpoint closes the candidate orbit;
- after a checkpoint span is exhausted without equality, the current state
  becomes the next checkpoint and the span doubles.

The recorded checkpoint need not be the first repeated state. Exact equality
at any two post-saturation layers, after all intervening layers were evaluated,
is a sufficient recurrence proof.

The independent verifier separately replays the registered checkpoint,
power, and distance schedule and also keeps a table of post-saturation states
as a diagnostic. It recomputes all parent `H=16` records before any later
layer, then all detector witnesses, the trace digest, the claimed checkpoint
states, and the family summary. It does not call the production search or
production layer-assessment function. It is algorithmically independent over
shared, hash-frozen dynamics and detector primitives; it is not a separate
semantic or cross-language implementation of those primitives.

## 7. Resource ceiling

The seeded state has at most `2^64` values. Starting from all zero under a
uniform rule, the comparator remains spatially homogeneous and therefore has
at most the all-zero and all-one configurations. The per-rule joint state
space consequently has at most `2^65` natural states after cone saturation.
Finiteness guarantees eventual pass or recurrence but gives no practical
runtime guarantee.

The operational ceiling is exactly `1,000,000` fully evaluated formation layers
per nonempty candidate. It is a resource-censoring observation horizon, not an
infinity argument. If a candidate reaches the ceiling without pass or
registered checkpoint recurrence, its status is
`resource_censored_before_recurrence`, the entire family result is
`incomplete_resource_censored`, and no family-level falsification or winner is
reported. Exact asymptotic closure replaces a finite horizon only for the
candidates that resolve before this ceiling.

There is no command-line override for this ceiling.

## 8. Terminal candidate records

Each nonempty candidate receives exactly one status:

### `exact_pass_on_fixed_orbit`

Record the first exact `T_proto`, formation anchor, successor anchor, sham and
breaking endpoint bits, full formation seeded/baseline states, first stage
witnesses, last evaluated layer, and trace digest.

### `recurrence_excluded_on_fixed_orbit`

Record `T_proto_status = infinite_on_fixed_orbit`, the registered checkpoint
and repeat layers, their period, the full fixed-width hexadecimal
seeded/baseline states at both layers, exact equality, first stage witnesses,
last evaluated layer, and trace digest. The checkpoint need not be the state's
first occurrence.

### `resource_censored_before_recurrence`

Record no pass or recurrence certificate. Record the last fully evaluated
layer, first stage witnesses, trace digest, and the fixed resource ceiling. The
candidate and family remain incomplete.

The empty rule retains `analytically_excluded` and is not dynamically traced.

## 9. Trace identity

Each candidate trace SHA-256 is domain-separated by search ID, candidate ID,
and canonical candidate hash. It covers layer 0 and every fully evaluated layer.
Each layer is encoded as an eight-byte length followed by its unbounded decimal
ASCII representation, then the seeded and baseline states as two unsigned
big-endian 64-bit integers.

The digest is audit metadata. Recurrence itself is proved only by the recorded
full-state equality and independent replay.

## 10. Family conclusions

If every nonempty candidate has an exact terminal status:

- one or more passes produce exact grammar-relative first-passage records and
  the preregistered minimum-law-count, then minimum-`T_proto`, co-winner set
  within this frozen family; or
- 15 recurrence exclusions plus the empty-rule analytic exclusion support:

> No rule in the complete frozen production-row family produces the
> `MIR-ISOLATED-DYAD-OUTWARD-EFFECT-EXACT-ORBIT-V0.1` proto-object from the
> canonical one-event seed against the all-zero initial comparator on `C64` at
> any finite time.

Any resource-censored candidate leaves the family-level existential question
unresolved.

## 11. Claim limits

Even a complete 16-rule falsification does not establish:

- failure of other `N_P=2` grammars;
- failure under other seeds, backgrounds, cycle sizes, or topologies;
- absence of transient dyads or other localized structures;
- failure under a different object definition;
- a general computational or physical impossibility;
- global primitive or law minimality;
- current-physics recovery;
- self-maintenance, reproduction, or carrier independence; or
- novelty of finite-state orbit enumeration.

A pass establishes only the inherited one-tick succession and registered
two-layer positional endpoint. It does not establish persistence, stability,
periodic localization, attractor membership, or a long-lived object. Any pass
must be interpreted and reported from its recorded `T_proto` as
`pre-saturation` for `t < 63` or `at/post-saturation` for `t >= 63`; the latter
can depend on finite-ring recirculation and cannot be transferred to an
infinite line or another cycle size.

## 12. Provenance sequence

The outcome-free contract, protocol JSON, schema, implementation, independent
verifier, tests, literature record, and content-hash seal must be committed
together. A direct-child commit may then add only the registered open manifest.
Only that clean opening commit can run the production search. Its direct child
must add only the canonical result.

Historical parent verification and the complete parent seal remain available
at the archival tag. The inherited runtime/specification files used by this
continuation must equal both their parent-seal hashes and their archival-commit
bytes. The new seal also binds the parent candidate and result artifacts and
every new executable or specification file used here.
