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

## Opportunity lifetime

- ID: `DEF-OPPORTUNITY-LIFETIME`
- Kind: causal observable
- Status: operational
- Symbol: `\tau_{\mathrm{opp}}`

The ordered event or tick interval during which a specified successor transition remains admissible, ending when that transition is realized or a declared lawful event makes the route unavailable.

## Realization redundancy

- ID: `DEF-REALIZATION-REDUNDANCY`
- Kind: causal observable
- Status: operational
- Symbol: none

For a factual ancestry-producing event selected before intervention, temporal redundancy occurs when vetoing that event leads to another ancestry-preserving child within the declared follow-up. The selected event is branch-necessary when the address instead dies without inherited continuation; continued source activity at the horizon is censored.

## Sequential realization cut depth

- ID: `DEF-SEQUENTIAL-CUT-DEPTH`
- Kind: causal observable
- Status: operational
- Symbol: `D_{\mathrm{seq}}`

Under a frozen retained-amplitude veto policy and fixed follow-up, the smallest depth d along a branch's prospectively committed selector chain at which vetoing the first d ancestry-producing events causes the original address to deactivate without a live collision-free descendant. Handoff after the administrative maximum is right-censored above that depth; continued original-address activity at the horizon is source-survival censored. The depth is prefix-minimal for this ordered policy, not a graph-theoretic minimum over arbitrary intervention sets.

## Latent counterfactual structure

- ID: `DEF-LATENT-COUNTERFACTUAL-STRUCTURE`
- Kind: working theoretical construct
- Status: provisional
- Symbol: none

The marked relational structure of lawful successor events still realizable from a declared complete state under the declared law, including their conditional order, compatibility, and closure. It is not the single factual trajectory, a scalar field, or a claim that every successor is simultaneously available.

## Frozen rooted graph-role signature

- ID: `DEF-ROOTED-GRAPH-ROLE`
- Kind: operational representation
- Status: provisional and representation-specific
- Symbol: none

For Finding 075, the tuple of face6 and face18 active-neighbor counts, face6 and cube26 neighbor-component counts, and the sorted induced cube26-degree sequence among a target's active cube26 neighbors, conditioned on exact cube26 shell-one and Chebyshev shell-two occupancy. Equality of this signature is a declared matching representation, not graph isomorphism or an established sufficient statistic for successor dynamics.

## Coherence-conditioned transition geometry

- ID: `DEF-COHERENCE-TRANSITION-GEOMETRY`
- Kind: working theoretical construct
- Status: provisional; not an established field or physical law
- Symbol: none

The organized, potentially anisotropic and history-dependent structure of lawful next transitions conditioned on a focal coherence, its marked relational neighborhood, and its recent causal history. The term does not presuppose a scalar, vector, tensor, Euclidean field, force, gravity analogue, or independently confirmed predictive representation.

## Successor openness

- ID: `DEF-SUCCESSOR-OPENNESS`
- Kind: developmental causal instrument
- Status: operational for Finding 078 only
- Symbol: `O_{\mathrm{succ}}`

For a declared pre-step state and radius-two basin, the sum of frozen transfer probabilities over tick-start-eligible inactive-target activation edges in the marked hard-transfer candidate graph, accompanied by the number of distinct activation targets. It is not an entropy, an exhaustive multi-tick reachable set, or an independently confirmed predictor.

## Repair affordance

- ID: `DEF-REPAIR-AFFORDANCE`
- Kind: developmental causal instrument
- Status: operational for Finding 078 only; predictive role untested
- Symbol: `A_{\mathrm{repair}}`

For a declared pre-step state and radius-two basin, the sum of frozen transfer probabilities over eligible depleted-target secondary edges classified as component_bridge_cube26 or local_bridge_face6, accompanied by distinct target and source counts. It measures one-step bridge/reclosure accessibility under the declared representation, not realized repair or a universal counterfactual quantity.

## Factorial interaction

- ID: `DEF-FACTORIAL-INTERACTION`
- Kind: operational contrast
- Status: operational
- Symbol: `I_{T\times M}`

For natural, topology-only, marks-only, and joint states, the declared instrument contrast joint minus topology-only minus marks-only plus natural. A nonzero value establishes non-additivity of the instrument under those interventions; by itself it does not establish a downstream causal or predictive effect.
