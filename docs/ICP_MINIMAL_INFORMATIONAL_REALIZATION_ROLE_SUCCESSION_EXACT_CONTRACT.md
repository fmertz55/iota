# MIR Role-Succession Exact-Closure Contract

Version: `0.1-draft`

Base program contract: `ICP Minimal Informational Realization Contract 0.2-draft`

Parent search: `MIR-ROLE-SUCCESSION-001`

Search ID: `MIR-ROLE-SUCCESSION-EXACT-001`

Date: `2026-07-14`

Status: **outcome-free exact-continuation design; continuation outcomes sealed**

Data class: **`development_outcome_contingent_exact_closure`**

## 1. Question and inherited result

The committed parent result is fixed at:

```text
commit  9b83fc8e1c9f0a034d6240677c9220bbcafa04cf
path    output/minimal_realization/MIR-ROLE-SUCCESSION-001/role_succession_results.json
SHA-256 1af33377789c117c913c0a5a613f2f102e2a5511f720714a609739c5d362a6f5
```

That result completely classified the pre-wrap window. It also classified 245
of the 255 nonempty rules by exact fixed-`C64` recurrence. Ten rules reached
the registered one-million-layer operational ceiling without a pass or a
recurrence certificate. The exact fixed-ring family conclusion therefore
remains resource-censored.

This continuation asks only:

> Can every remaining parent candidate be resolved as incapable of a future
> complete detector pass, or does at least one produce such a pass on its exact
> `C64` orbit?

It changes no grammar, primitive accounting, topology, seed, comparator,
detector, anchor order, intervention, endpoint, or cross-size rule. It first
applies a generic local impossibility proof. A candidate not excluded by that
proof is replayed from layer zero and continued without a layer ceiling until
the inherited detector passes or exact joint-state recurrence makes every
later complete pass unreachable.

The continuation is family-relative development work. It does not reopen the
already complete pre-wrap result, and it is not a new test of global `N_P=2`
minimality.

## 2. Outcome boundary

The parent ledger through layer `1,000,000` is an authorized input. No state at
layer `1,000,001` or later, no registered symbolic-certificate classification,
and no registered local-context evaluation may be generated or inspected until
all of the following are committed together and tagged:

- this contract and the complete machine-readable protocol;
- the exact derivation and canonical order of the ten continuation candidates;
- the symbolic-certificate implementation and transparent result encoding;
- the no-ceiling prefix-replay and Brent continuation implementation;
- the independently expressed certificate, transition, detector, and replay
  implementation;
- the schemas, outcome-free tests, candidate manifest, and content-hash seal;
  and
- a disabled production command.

Pre-freeze tests may use disclosed nonregistered rules and synthetic local
contexts. They may not classify any of the ten registered candidates, evolve
one of them from the canonical seed, or inspect any registered post-million
state. Candidate-manifest compilation is allowed because it only filters and
copies committed parent metadata; it performs neither local-context evaluation
nor dynamics.

After the freeze, the production run is indivisible at the result boundary.
An interrupt, exception, worker death, machine restart, or unfinished
cross-size control produces no result file and no scientific status. In
particular, there is no resource-censored terminal status in this protocol.
Restarting repeats the registered computation from its beginning.

## 3. Candidate derivation

The continuation manifest is derived mechanically from the parent
`candidate_results` array by retaining records whose
`evaluation_status` is exactly
`resource_censored_before_recurrence`, without sorting the retained records.
The parent order is therefore preserved. The derivation must return exactly
the following ten records or the run aborts:

| Parent order | Candidate ID | Rows | Wolfram rule |
|---:|---|---|---:|
| 1 | `MIR-RS-P2-L4-000-001-010-111` | `000,001,010,111` | 135 |
| 2 | `MIR-RS-P2-L4-000-001-011-110` | `000,001,011,110` | 75 |
| 3 | `MIR-RS-P2-L4-000-010-011-101` | `000,010,011,101` | 45 |
| 4 | `MIR-RS-P2-L4-000-010-100-111` | `000,010,100,111` | 149 |
| 5 | `MIR-RS-P2-L4-000-010-101-110` | `000,010,101,110` | 101 |
| 6 | `MIR-RS-P2-L4-000-011-100-110` | `000,011,100,110` | 89 |
| 7 | `MIR-RS-P2-L4-000-011-101-111` | `000,011,101,111` | 169 |
| 8 | `MIR-RS-P2-L4-000-101-110-111` | `000,101,110,111` | 225 |
| 9 | `MIR-RS-P2-L4-001-010-011-100` | `001,010,011,100` | 30 |
| 10 | `MIR-RS-P2-L4-001-010-100-110` | `001,010,100,110` | 86 |

Every selected parent record must also have `atomic_n_l=4`,
`last_assessed_layer=1,000,000`, `resource_limit=1,000,000`, no complete pass,
and no recurrence. The candidate ID, ordered rows, Wolfram number, candidate
SHA-256, parent trace SHA-256, and inherited stage witnesses are copied into
the new candidate manifest. Any mismatch in the parent path, bytes, commit,
record count, order, or fields aborts before analysis.

The other 245 nonempty rules are not rerun. Their committed exact recurrence
certificates are reconciled into the final family conclusion by binding the
complete parent ledger, not by copying an unverified aggregate.

## 4. Frozen local impossibility certificate

Write the candidate update as the exact Boolean function

```text
f(predecessor, self, successor) -> {0,1}.
```

The certificate concerns the complete inherited detector, not merely role
formation. It is evaluated for every continuation candidate before any
post-million dynamics. Two exhaustive branches are frozen.

### 4.1 Homogeneous-comparator obstruction

The comparator begins uniformly zero. A radius-one deterministic rule maps a
uniform state to a uniform state. If row `000` is selected, then an attributed
role at layer `t` implies the uniform comparator is `0^64` at `t`: attribution
requires zero comparator values at both active role loci. Its next state is
then `1^64`, because `f(0,0,0)=1`. Every eligible successor at layer `t+1`
requires zero comparator values at its two active loci, which is impossible in
`1^64`.

Thus, for any rule selecting `000`, the inherited attributed successor and all
downstream complete passes are unreachable at every layer. This proof does not
claim the seeded orbit cannot form an unattributed `0110` pattern.

The result still carries all eight local contexts so raw seeded succession and
endpoint calculations remain transparent, but comparator attribution empties
every successor set. It also carries the selected `000` truth-table value and
the proof statement. The independently expressed verifier reconstructs the
proof from the candidate rows; it does not trust a certificate label.

### 4.2 Exhaustive local-context obstruction

If row `000` is absent, the comparator remains exactly `0^64`, so attribution
adds no further local constraint. Translation and radius-one causality permit a
formation anchor to be written as offset zero. Every possible complete pass at
that anchor is determined by formation offsets `-2..+5`.

The current attributed role and outward guard fix:

```text
offset      -2  -1   0  +1  +2  +3  +4  +5
value        u   0   1   1   0   0   v   w
```

where `(u,v,w)` ranges in lexicographic binary order from `000` through `111`.
There are exactly eight contexts. For each context the analyzer must:

1. compute the exact natural next-layer bits needed at offsets `-1..+3`;
2. test the inherited attributed `0110` successor first at displacement `0`
   and then at displacement `+1`;
3. replace formation offsets `0,+1,+2` by the sham `011` and breaking `101`
   arms, leaving the rest of the context unchanged;
4. evolve each arm for exactly two fresh-output radius-one steps; and
5. compare the two exact values at endpoint offset `+3`.

A joint local witness is a context and successor displacement for which the
successor predicate holds and the two endpoint bits differ. The result records
all eight contexts, the ordered raw and comparator-attributed successor
displacements, both endpoint bits, and their joint-witness displacements.

If and only if the union of joint local witnesses is empty, no global state on
any cycle or line can satisfy the complete detector for this rule: any alleged
pass would restrict to one of the eight enumerated causal neighborhoods and
contradict the table. The empty table is therefore an exact universal local
impossibility certificate. A nonempty table is only a failure to exclude; it
does not show that the canonical orbit reaches a witness.

The static analyzer may not use the parent candidate trajectories, post-million
states, Wolfram-class folklore, or a learned/SAT heuristic. Production uses
direct truth-table evaluation. Independent verification separately expresses
the same Boolean functions in algebraic normal form and exhausts the eight
contexts again.

## 5. No-ceiling exact continuation

Only a candidate not statically excluded enters orbit continuation. Its run
starts again from the canonical singleton seeded state and uniform-zero
comparator at layer zero. It replays every layer through `1,000,000`, including
the detector assessment, trace hashing, and the original power-of-two Brent
checkpoint updates. At the boundary it must reproduce all of the following
from the bound parent record:

- the complete parent trace SHA-256;
- the absence of a complete pass and checkpoint recurrence;
- every inherited first-stage witness;
- `last_assessed_layer=resource_limit=1,000,000`; and
- the canonical candidate identity and candidate-domain hash.

The trace encoding and domain are inherited unchanged from
`MIR-ROLE-SUCCESSION-001`. The SHA-256 state is reconstructed by replay rather
than deserialized. The continuation trace therefore hashes the natural joint
states continuously from layer zero through the eventual terminal layer and
has the parent digest as its exact prefix digest.

The Brent recurrence state is likewise not reset at the boundary. The frozen
schedule initializes the joint-state checkpoint at cone saturation layer 32,
with power one and distance zero. At each later layer it first compares the
complete `(seeded_state, comparator_state)` pair with the checkpoint, then
promotes the checkpoint when the current distance equals the current power.
Replay reconstructs the checkpoint, checkpoint layer, power, distance, and
checkpoint state that exist after layer `1,000,000`; those values are recorded
in the result.

The first newly eligible formation layer is `1,000,001`. At every later layer
the frozen order is:

```text
1. evolve the exact seeded and comparator states
2. append the joint state to the inherited trace digest
3. evaluate the complete detector at every anchor in inherited order
4. if a complete pass exists, terminate as exact_pass_on_fixed_orbit
5. otherwise test exact joint-state checkpoint equality
6. otherwise update the Brent checkpoint schedule and continue
```

Detector precedence means a pass on the same layer as a repeated joint state
wins. Hash equality is never recurrence evidence. Exact equality after cone
saturation proves that the natural orbit, every detector assessment, and every
two-step intervention future repeat; a later first complete pass is therefore
unreachable.

There is no registered layer ceiling, wall-clock ceiling, iteration budget,
or resource-censored status. The state space is finite: after saturation, the
seeded state has at most `2^64` values and the comparator remains homogeneous,
so the joint state has at most `2^65` values. Absent a pass, exact recurrence is
mathematically inevitable. Operational interruption is not an outcome and
writes no result.

Production uses four spawned candidate-level workers. All static analyses,
all required dynamic terminals, and all triggered controls are collected in
the fixed ten-candidate order before the ledger is constructed. Workers do not
write scientific artifacts. There is no worker-count override and no partial
ledger.

## 6. Conditional `C96` and `C128` controls

Every continuation candidate that passes on primary `C64` is evaluated on
`C96` and `C128` from the inherited canonical seed and comparator through the
primary first-passage layer. Both controls finish before any result is written.
Their first complete pass, or exact absence of a pass through that finite
horizon, is recorded.

Every continuation pass occurs after the parent boundary and hence after the
pre-wrap horizon `H_pre=29`. It is classified `finite_ring_exposed`; larger-ring
agreement cannot upgrade it to a localized construction. The controls remain
mandatory diagnostics under the inherited protocol.

An interrupted or incomplete control invalidates the whole run. It is not a
control result and does not permit serialization of the already known primary
pass.

## 7. Resolution and family reconciliation

Each of the ten selected candidates receives exactly one terminal resolution:

- `symbolically_unreachable`;
- `exact_pass_on_fixed_orbit`; or
- `recurrence_excluded_on_fixed_orbit`.

The first status proves the complete local pass predicate unreachable in every
future. The third proves every future on the inherited fixed orbit repeats a
previously assessed nonpass. The second resolves the family existential in the
opposite direction. No fourth status is permitted.

The combined conclusion is computed from the bound parent records and all ten
continuation resolutions:

```text
at least one continuation exact pass:
  one_or_more_exact_passes

no continuation pass and all ten statically or recurrently excluded:
  all_dynamic_candidates_exactly_no_pass
```

All ten candidates have parent law count four. If a pass occurs, minimum-law
ranking within this frozen 256-rule family is resolved only after the complete
parent reconciliation confirms every lower shell is an exact nonpass and all
law-count-four co-winners have been resolved. A pass does not erase the
requirement to finish the remaining selected candidates and controls.

The final ledger records the exact partition of the ten candidates, the 245
bound parent recurrence exclusions, any exact passers, all transparent static
tables, every dynamic terminal certificate, and the resulting 255-candidate
reconciliation. Cross-field validation, not a narrative aggregate, establishes
completion.

## 8. Trace and result transport

For dynamic continuations, locus `i` remains bit `i` of the unsigned state and
locus zero is the least-significant bit. `C64` states are exactly 16 lowercase
hexadecimal digits. The inherited trace begins with ASCII
`IOTA-MIR-ROLE-SUCCESSION-TRACE-V1` plus NUL, followed by the inherited parent
candidate domain. Every joint state from layer zero through the terminal is
encoded with the inherited decimal-layer length and fixed-width seeded and
comparator bytes. No continuation-specific prefix is inserted at layer
`1,000,000`.

The result schema makes the static proof checkable without prose: it carries
the context order, fixed and free loci, successor options,
matched-arm endpoint values, joint witnesses, and exact classification. For a
dynamic continuation it carries the parent-prefix match, boundary state, Brent
boundary state, full trace digest, and pass or recurrence terminal.

Production and verification independently validate the parent ledger's
canonical JSON bytes and SHA-256 before interpreting it. Neither accepts a
semantically similar reserialization.

## 9. Provenance sequence

The required linear history is:

1. the freeze commit has parent exactly
   `9b83fc8e1c9f0a034d6240677c9220bbcafa04cf`, introduces the complete
   outcome-free continuation implementation and seal, leaves every frozen
   parent source/specification/result path byte-identical, and is tagged with
   the annotated tag `mir-role-succession-exact-001-v0.1-frozen`;
2. a direct child adds only the registered continuation open manifest; and
3. its direct child adds only the canonical continuation result.

The opening command requires the annotated tag to peel to the freeze commit,
requires the seal to be added at that tagged commit and absent in its parent,
and rejects any intervening commit. The production command requires a clean
opening commit with the result path absent. It writes the result atomically and
exactly once only after every candidate and control has completed.

Independent verification runs only after the result-only commit. It requires a
clean worktree, proves the exact direct-child path chronology, re-derives the
ten candidates from the bound parent bytes, reconstructs every static proof
without calling the production analyzer, and independently replays every
dynamic terminal without calling the production transition, detector, trace,
or Brent helpers.

The current freeze task ends at step 1. No open manifest, registered
certificate outcome, post-million state, or result belongs in the freeze
commit.

## 10. Claim limits

A complete null closes only the exact `C64` existential for the frozen
`MIR-ROLE-SUCCESSION-001` grammar, seed, comparator, forward detector, and
intervention. It does not exclude another `N_P=2` grammar, another seed or
background, another topology or size, an infinite-line trajectory, a mirrored
detector, a different object definition, dynamic relations, or other primitive
accounting.

A pass is development evidence for finite-ring behavior after wrap exposure.
It is not a localized-object construction, confirmation data, a novelty claim,
carrier independence, a current-physics role, or global minimality.

The static certificate is exact only for the complete inherited local detector.
It does not classify all coherent structures or all notions of role succession.
The recurrence certificate is exact only for the fixed finite joint orbit. All
claims remain family-relative and development-only.
