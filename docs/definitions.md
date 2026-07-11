# Iota Definitions

This document is generated from `evidence/definitions.yaml`. Do not edit it directly.

## Iota

- ID: `DEF-IOTA`
- Kind: primitive
- Status: provisional
- Symbol: `I_x(t)`

A stationary lattice address together with the local attribute and expression state instantiated at that address.

## Reachable set

- ID: `DEF-REACHABLE`
- Kind: derived
- Status: provisional
- Symbol: `\mathcal{R}_x(t+1\mid s_t)`

The set of next local states admissible from state s_t under the declared local law.

## Interaction-induced information

- ID: `DEF-INFORMATION`
- Kind: hypothesis
- Status: organizing hypothesis
- Symbol: `\Delta I_x`

The change in the reachable caused by interaction. For strict reachable-set reduction, the current cardinality measure is the logarithm of the prior-to-posterior reachable-set size ratio.

## Coherence

- ID: `DEF-COHERENCE`
- Kind: observable
- Status: operational
- Symbol: none

A connected active structure measured using the explicitly declared neighborhood connectivity. It is not assumed to be a fundamental physical object.

## Bridge

- ID: `DEF-BRIDGE`
- Kind: observable
- Status: operational
- Symbol: `B`

A set of active lattice cells whose removal changes reachability between tracked regions in the audited state.

## Strict constraint transport

- ID: `DEF-CONSTRAINT-TRANSPORT`
- Kind: observable
- Status: operational
- Symbol: none

Loss and restoration of reachability between the same tracked predecessor regions through a causally necessary successor bridge disjoint from the predecessor bridge.

## Payload-free

- ID: `DEF-PAYLOAD-FREE`
- Kind: condition
- Status: operational
- Symbol: `P=0`

World.P is zero at every observed offset in the audited continuation.

## Ledger exactness

- ID: `DEF-LEDGER-EXACT`
- Kind: safety condition
- Status: operational
- Symbol: none

The experiment's conservation ledger has zero recorded discrepancy at every audited offset.

## Predecessor address lineage

- ID: `DEF-ADDRESS-LINEAGE`
- Kind: observable
- Status: operational
- Symbol: none

A conservative lineage that remains alive while at least one original stationary iota address of the predecessor region remains active; later reactivation after complete address loss does not restore the terminated lineage.

## Prospective expression lineage

- ID: `DEF-EXPRESSION-LINEAGE`
- Kind: observable
- Status: operational
- Symbol: none

A non-resurrecting lineage propagated only when a successful transfer from a current lineage address newly activates its target in that tick; retained active addresses remain members, already-active targets do not inherit identity, and ambiguous dual claims invalidate a strict result.

## Expression-handoff susceptibility

- ID: `DEF-HANDOFF-SUSCEPTIBILITY`
- Kind: observable
- Status: operational
- Symbol: `p_{\mathrm{handoff}}`

Among continuation branches from a fixed state in which the original singleton address becomes inactive within the declared horizon, the fraction retaining a nonempty, collision-free prospective singleton expression lineage immediately after that first deactivation.

## Candidate lineage-continuation rule

- ID: `DEF-CONTINUATION-RULE`
- Kind: hypothesis
- Status: operational candidate
- Symbol: none

A frozen mapping from features available immediately before original-address deactivation to the presence or absence of a nonempty prospective expression lineage immediately afterward; a predictive marker is not treated as a primitive law unless it is both sufficiently sensitive and independently replicated.

## Temporal continuation gate

- ID: `DEF-TEMPORAL-GATE`
- Kind: causal mechanism
- Status: operational
- Symbol: none

An ordered event decision whose resolution before source termination changes whether an ancestry-preserving successor is realized; it is identified by a frozen intervention that changes that decision while leaving the pre-intervention state and consumed random draw fixed.
