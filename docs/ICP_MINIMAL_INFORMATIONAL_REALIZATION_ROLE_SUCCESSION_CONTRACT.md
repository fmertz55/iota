# MIR Endogenous Role-Succession Falsification Contract

Version: `0.1-draft`

Base program contract: `ICP Minimal Informational Realization Contract 0.2-draft`

Search ID: `MIR-ROLE-SUCCESSION-001`

Date: `2026-07-13`

Status: **outcome-free design; new outcomes sealed**

Data class: **development, outcome-contingent on `MIR-EXACT-ORBIT-001`**

## 1. Question

The complete frozen two-input production-row family failed on its exact fixed
orbits. Thirteen dynamic rules never formed the attributed isolated dyad. The
two rules that formed it did so at layer 1, then never produced the registered
one-tick successor. No rule reached the matched intervention.

This protocol changes one expressive coordinate while holding the event
alphabet, seed, comparator, local role, succession direction, matched
intervention, outward endpoint, scheduler, and primary `C64` topology fixed:

> Does allowing a governed event to read both incidences of the same charged
> oriented nearest-neighbor relation permit endogenous relational-role
> succession at `N_P=2`?

The mechanism target is an attributed isolated dyad with an attributed eligible
successor one elementary layer later. The construction target remains the full
proto-object detector, including the outward matched-intervention effect. A
successor without that effect is diagnostic progress, not a proto-object pass.

## 2. Outcome boundary

The grammar was chosen after the `MIR-EXACT-ORBIT-001` null was known. Every
result from this search is development data. No custom trajectory, candidate
stage, first-passage value, ranking, or cross-size result from the new grammar
may be generated or inspected before all items below are committed together:

- this contract and the machine-readable specification;
- the complete candidate-enumeration rule;
- the detector and synthetic fixtures;
- the exact transition engine and result writer;
- the independent replay implementation;
- the schemas, validators, tests, and literature record; and
- a content-hash outcome seal with the production command disabled.

Tests before that commit may use only disclosed synthetic states. In
particular, no test may evolve a registered rule from the canonical one-event
seed or write the registered result path. The supplied-dyad copy-predecessor
fixture in Section 8 is detector-development data, not a candidate outcome.

A later direct-child commit may add only the registered open manifest. The
production run may begin only from that clean opening commit. Its result must be
written atomically and exactly once. Conditional size controls must finish
before any primary result is serialized, so the `C64` outcome cannot be opened
first and used to redesign them.

## 3. Primitive accounting

The candidate has two normalized binary schemas:

```text
event                one binary dynamic channel at each locus
oriented_cycle_edge  one binary directed relation channel
```

Thus the registered normalized count remains:

```text
N_P = 1 dynamic channel + 1 relation channel = 2
```

The fixed topology contains the 64 true edges `i -> (i+1) mod 64`. At governed
locus `i`, `predecessor` is the source of its unique incoming edge and
`successor` is the target of its unique outgoing edge. They are two incidence
reads of the same relation predicate. No inverse-edge table, second adjacency
matrix, port-state bit, phase bit, memory bit, scheduler bit, or dynamic bond is
stored.

This accounting convention is admissible only because reversing the arguments
of the same oriented relation derives the incoming incidence without supplied
candidate data. If an implementation stores the inverse relation, gives either
port mutable state, or uses a second relation predicate, it is not this
`N_P=2` grammar.

The complete fixed resource record is:

```text
N_P_kind                         2
N_P_seed                         1
N_P_rel                          1
candidate-supplied bits          0
dynamic storage bits/layer      64
true relation instances         64
event-value input ports/site     3
relation-incidence reads/site    2
event writes/site                1
site evaluations/layer          64
maximum relation hops/tick       1
causal radius                    1
exogenous channels               0
persistent helper state          0
```

The extra outgoing-incidence read is real added capacity. It is not hidden by
the unchanged `N_P`: relative to the failed grammar, fan-in rises from 2 to 3,
relation-incidence reads rise from 1 to 2, possible exact signatures rise from
4 to 8, and the deterministic family rises from 16 to 256 rules. These
coordinates must accompany every complexity comparison.

The directed orientation is inherited from the frozen `C64` relation rather
than supplied per candidate. Reflection is a family symmetry check, not an
independent replicate. Complementing event labels remains outside the grammar
because fresh-output quiescence privileges `0`.

## 4. Alternative atomic-law grammar

The ordered local signature is:

```text
(event at predecessor, event at governed locus, event at successor)
```

For each `p` in `000..111`, the grammar admits one atomic production row:

```text
EMIT_1_IF_NEIGHBORHOOD(p)
```

Each registered row governs the one event degree at the governed locus in the
next fresh layer. Exact rows are mutually exclusive. A nonregistered signature
produces `0`. There is no implicit carry, alternative branch, helper, lookup,
coordinate query, time query, within-tick cascade, or detector feedback.

A candidate is one subset of the eight rows. Its law count is the number of
registered rows, not one law for the complete Boolean map. The complete family
has 256 candidates and binomial shell sizes:

```text
N_L       0   1   2   3   4   5   6   7   8
count     1   8  28  56  70  56  28   8   1
```

Candidates are enumerated by increasing `N_L`, then lexicographic row tuple in
the order `000,001,010,011,100,101,110,111`. The conventional Wolfram rule
number is also recorded, with row `abc` assigned bit position equal to the
integer represented by `abc`, hence weight `2^int(abc)`. No reflection,
complement, unreachable-row, or
behavioral quotient reduces the family.

The zero-row candidate is analytically excluded because fresh-output dynamics
cannot emit a nonquiescent event after layer zero. All 255 nonempty candidates
are dynamically processed; there is no shell stopping.

This is the ordinary radius-one binary elementary-cellular-automaton rule
space expressed in the project's production-row accounting. Exhaustive ECA
enumeration, point-seed classification, localized CA structures, and glider
search are established prior art. No novelty is claimed for the grammar or
search space.

## 5. Clock, seed, comparator, and topology

One tick is one synchronous causal layer. Every row reads layer `t`; every row
writes a fresh event opportunity at layer `t+1`. Influence crosses at most one
edge in either incidence direction per tick. There are no ordered subevents.

The primary substrate is the oriented periodic cycle `C64`. The canonical
seeded state has one event at origin `0`; the matched comparator is all zero.
The comparator is evolved under the same candidate because row `000` can make
it nonquiescent. Translation copies are algebraic corollaries and are not run
as evidence.

For attribution, the centered causal cone at layer `t` is the set of loci whose
cycle-graph distance from origin `0` is at most `t`. It first covers `C64` at
layer 32. Eligible anchors are ordered

```text
0, +1, -1, +2, -2, ..., +31, -31, +32
```

with offsets reduced modulo the cycle size. This is a tie-break only; every
eligible anchor is tested before a layer is declared a nonpass.

All serialized local anchors use the same frozen signed-offset map. For a
physical anchor `a`, origin `o`, and cycle size `N`, let
`d = (a - o) mod N` in `0,...,N-1`; serialize `d` when
`d <= floor(N/2)`, and otherwise serialize `d-N`. On an even cycle the
antipode is therefore positive. The registered ranges are `[-31,+32]` on
`C64`, `[-47,+48]` on `C96`, and `[-63,+64]` on `C128`.

## 6. Frozen endogenous-succession detector

The local predicates remain those of the failed reference test. At formation
layer `t`, an isolated active dyad at anchor `a` is:

```text
offset       -1   0   +1   +2
event         0   1    1    0
```

Both active witnesses must be zero in the matched comparator at the same
layer. The initial state must fail the role predicate. An eligible successor at
layer `t+1` is the same attributed isolated dyad at anchor `a`, then at anchor
`a+1`, in that selection order. The predecessor-shifted anchor is deliberately
not added: retaining `[0,+1]` isolates the grammar change. The complete rule
family is closed under reflection, but the forward endpoint is not a
reflection-symmetric detector. The registered conclusion is therefore limited
to this inherited forward-oriented role; it does not exclude a mirrored role
under a separately reflected detector.

Cone eligibility is exact and stage-specific. At formation, the two active
role loci `a` and `a+1` must both lie in the centered cone at layer `t`. At
succession, the two active loci of the selected successor must both lie in the
centered cone at layer `t+1`. For intervention eligibility, endpoint `a+3`
must lie in the centered cone at layer `t+2`. The isolation-zero loci `a-1`
and `a+2` are predicate checks but are deliberately not additional cone-
eligibility requirements. These rules apply at the boundary before the cone
saturates and continue trivially after saturation.

The matched interventions at formation remain:

```text
window offsets                 0  +1  +2
natural formation window       1   1   0
role-preserving sham           0   1   1
role-breaking arm              1   0   1
```

Both arms have Hamming distance two from natural and retain two active events.
All state outside the window is unchanged. Offset `+3` must be zero at
formation. Both arms evolve normally for two layers. The exact event at
`a+3` at layer `t+2` is the reachable-future variable. Unequal sham and
breaking values pass the outward-effect criterion.

Under a centered radius-one rule, the endpoint's first update reads formation
offsets `+2,+3,+4`. Those values are identical in both intervention arms.
Consequently an endpoint difference cannot be a one-layer direct read of an
edited bit; it must arrive on the second layer through the registered local
dynamics.

Every candidate records the earliest occurrence of four nested stages:

1. `first_role`;
2. `first_successor`;
3. `first_intervention_eligible`; and
4. `first_complete_pass`.

The first mechanism endpoint is `first_successor`. The proto-object endpoint is
only `first_complete_pass`. Formation time `T_proto` is the first complete pass,
not the first role or successor.

## 7. Pre-wrap gate

The detector endpoint is observed two layers after formation. A `C64` witness
is strictly pre-wrap when the complete seed-to-endpoint causal interval embeds
injectively in the cycle:

```text
2 * (t + 2) < 64
```

Therefore the frozen pre-wrap formation horizon is:

```text
H_pre = 29
```

This is not selected from a trajectory. It is the largest integer formation
layer whose two-layer endpoint remains strictly before centered-cone aliasing
on `C64`.

The pre-wrap mechanism hypothesis is:

> At least one of the 255 nonempty candidates endogenously forms an attributed
> isolated dyad with an attributed eligible one-tick successor by `H_pre=29`.

The pre-wrap construction hypothesis is:

> At least one candidate produces a complete proto-object pass by `H_pre=29`.

Failure of the first hypothesis falsifies the chosen wider-fan-in axis as a
pre-wrap repair of the observed succession bottleneck. Survival of the first
with failure of the second moves the bottleneck downstream without recovering
a proto-object. All 255 nonempty dynamic candidates necessarily receive their complete pre-wrap
classification even if a later exact-orbit trace is resource-censored.

## 8. Outcome-free positive fixture

The detector is not allowed to fail merely because the new grammar cannot
express succession when a role is supplied. The disclosed synthetic positive
uses the copy-predecessor rows:

```text
100, 101, 110, 111
```

Starting from a synthetic isolated dyad, these rows shift the dyad one locus
forward in one layer. Under the fixed intervention, the event at `a+3` two
layers later copies the original value at `a+1`, which is `1` under sham and
`0` under the breaking arm. This fixture therefore reaches every detector
stage.

The fixture does not begin from the canonical one-event seed. It gives no
candidate formation time or registered search result. Its rule rows and exact
expected local states are committed as detector-development data before the
outcome seal.

Synthetic negative fixtures cover role without succession, succession without
outward difference, comparator attribution failure, guard failure, wrong
successor displacement, cone boundary, reflection of the transition rule, and
full-state recurrence bookkeeping. None may run a registered canonical
candidate trajectory.

## 9. Exact fixed-ring continuation

After every candidate has been assessed through `H_pre`, the same in-memory
trace continues on primary `C64` until the first complete pass, an exact
post-saturation recurrence, or the fixed resource ceiling.

Write seeded and comparator states as `S_t` and `B_t`. The complete recurrence
state is:

```text
Z_t = (min(t, 32), S_t, B_t)
```

At every layer, the full detector is evaluated before recurrence classification;
a same-layer detector pass wins. Only if neither occurs is the resource ceiling
classified. Thus the terminal order is detector, exact recurrence, then resource
ceiling. A repeat of
`S_t` alone is invalid. A repeat of `(S_t,B_t)` before cone saturation is also
invalid. After saturation, exact equality of both full bit states proves that
all future natural successors and two-layer intervention futures repeat. Hash
equality is never the recurrence proof.

The registered streaming checkpoint schedule is the same deterministic
power-of-two schedule used by `MIR-EXACT-ORBIT-001`, prospectively reimplemented
for the new transition and cone. The operational ceiling is:

```text
1,000,000 fully assessed formation layers per nonempty candidate
```

Reaching the ceiling is `resource_censored_before_recurrence`, never an
infinity conclusion. The exact family null is supported only if all 255
nonempty candidates receive exact recurrence exclusions and none passes.

Registered execution uses exactly four spawned worker processes at candidate
granularity. A worker completes one primary orbit and any triggered size
controls. The parent collects all 255 dynamic evaluations in canonical
manifest order before constructing the ledger; workers never write partial
outcome artifacts. Independent replay uses the same four-candidate allocation
but a separate transition and detector implementation. Scheduling cannot alter
first passage, recurrence, ordering, or result bytes, and no worker-count CLI
override exists.

State and trace bytes are frozen independently of Python serialization. Locus
`i` is bit `i` of an unsigned state integer, so locus `0` is the least-
significant bit; a `C64` result state is exactly 16 lowercase hexadecimal
digits. State bytes are unsigned big-endian in exactly `ceil(N/8)` bytes.
The trace SHA-256 begins with ASCII
`IOTA-MIR-ROLE-SUCCESSION-TRACE-V1` plus NUL, then the 8-byte big-endian
length and bytes of the candidate domain. That domain is ASCII
`search_id + NUL + candidate_id + NUL + candidate_sha256`, where the candidate
hash covers canonical sorted-key, compact, ASCII JSON without a trailing LF.
For every natural joint state from layer 0 through the terminal layer, append
the 8-byte big-endian length of the layer's unsigned decimal ASCII, those layer
bytes, then fixed-width seeded and comparator bytes. Intervention arms and
larger-ring controls are not trace-digest inputs. `protocol.json` carries the
same normative field-by-field encoding.

## 10. Cross-size controls

Every primary `C64` passer is conditionally evaluated on `C96` and `C128` from
the same one-event seed and all-zero comparator, under the same rule and local
detector, through the primary candidate's `C64` first-passage layer. These
controls are frozen now and execute before the result file is written.

For a `C64` pre-wrap passer, both larger rings must reproduce the same first
passage layer, signed local anchor, successor displacement, and endpoint bits.
A mismatch is an implementation failure because the causal interval embeds in
all three rings. Agreement is an algebraic finite-support validation, not an
independent replicate.

A pass with `T_proto > 29` is classified `finite_ring_exposed` regardless of
larger-ring behavior. Larger-ring records for it are diagnostic only and cannot
upgrade it to a localized-object result. A localized interpretation requires a
pre-wrap primary pass plus exact `C96` and `C128` agreement.

The transition implementation also checks reflection covariance on synthetic
states and the complete candidate enumerator is closed under swapping the two
relation incidences. This checks dynamics only. The forward detector is not
silently treated as reflection invariant. Reflected candidates and translations
are symmetry checks, not additional observations.

## 11. Result statuses and decision rules

Each nonempty primary candidate ends with exactly one status:

- `exact_pass_on_fixed_orbit`;
- `recurrence_excluded_on_fixed_orbit`; or
- `resource_censored_before_recurrence`.

Every record also contains the four stage witnesses, the complete pre-wrap
classification, law count, row set, Wolfram code, last assessed layer, trace
digest, and terminal certificate or pass witness.

Family decisions are frozen as follows:

```text
zero pre-wrap successors:
  falsify wider centered fan-in as a pre-wrap repair of endogenous succession

one or more pre-wrap successors, zero pre-wrap complete passes:
  succession bottleneck moved; proto-object recovery failed in the pre-wrap window

one or more pre-wrap complete passes with size agreement:
  grammar survives the localized development falsification

only post-wrap complete passes:
  record finite-ring behavior; no localized-object interpretation

all 255 nonempty candidates recurrence-excluded:
  exact fixed-C64 family falsification

any resource-censored candidate with no pass:
  exact fixed-C64 family existential remains unresolved
```

An exact passer at law count `k` is a minimum-law passer within this family only
if every candidate below `k` is exactly resolved as a nonpass and every
candidate in shell `k` is resolved sufficiently to enumerate all co-winners at
the minimum first-passage layer. A resource-censored candidate in a lower shell
blocks that ranking. It does not erase an observed existential pass.

No p-value or multiplicity correction applies to the deterministic exhaustive
family. The declared family-level endpoints are existential Boolean statements,
not a sample estimate. Counts by diagnostic stage are descriptive.

## 12. Claim limits

A pass would establish only a grammar-relative development construction under
the fixed seed, comparator, detector, topology panel, and accounting convention.
It would not establish global `N_P=2` minimality, novelty of elementary CA,
carrier independence, a current-physics role, open-ended complexity, or an
information-first ontology.

A complete null would not exclude another `N_P=2` grammar, a dynamic relation
state, another seed or background, a larger substrate, an infinite-line late
formation, a different localized-object definition, or a domain-relative
coherent structure. A pre-wrap null is `T_proto > 29` under this resource
envelope, not `T_proto = infinity` outside the exact fixed-ring certificate.

The old and new families use different fan-in and update-work budgets. Their
`N_L` values must not be compared without the published fan-in, relation-read,
and truth-table-capacity coordinates. No global minimum follows even if the new
family passes.

## 13. Provenance sequence

The required linear history is:

1. commit the complete outcome-free protocol, implementation, tests,
   literature record, and content-hash seal, with the seal absent from the
   parent and added by this commit, then place the annotated tag
   `mir-role-succession-001-v0.1-frozen` on that exact seal-introduction commit;
2. in a direct child, add only the registered open manifest; and
3. in its direct child, add only the canonical result.

Independent result verification is a post-commit provenance check: the
worktree must be clean, the result bytes must equal `HEAD`, the result commit
must be the direct child of the committed opening, and that commit must change
only the registered result path. The verifier then replays every recorded
trajectory independently.

The current task ends at step 1. No open manifest or result belongs in the
protocol-freeze commit.
