# Iota Rig v0.2 Law Spec

Status: design specification, not implemented by the default engine.

## Purpose

`iota-rig-v0.1.1` is an irreversible growth model. It is useful for testing grammar, nucleation, compatibility coupling, and replay-vs-committor causality, but it has no hard conserved quantity and no deactivation. That means "energy", "mass", "maintenance", and "durable form without closed future" are not yet falsifiable claims in the substrate.

`iota-rig-v0.2.0` should be a versioned law change that introduces a conserved execution budget and exhaustion deactivation. The openness timeline should be run before and after the law change so v0.1 closure and v0.2 openness can be compared with the same instrument.

## Proposed Config

```yaml
simulation_version: iota-rig-v0.2.0

constants:
  conservation: hard        # soft | overwrite | hard
  deactivation: exhaustion  # none | exhaustion
  vacuum_amplitude: 1       # latent integer budget held by unspent dark cells
```

These keys should not be added to the default v0.1 config until the engine consumes them and the version boundary is explicit.

## State Ledger

The current v0.1 state arrays are:

```text
active, A, R, V, P
```

v0.2 needs one additional ledger concept:

```text
latent_A
```

`latent_A` is the unspent vacuum budget of inactive cells. A cell can be dark but still hold latent budget, or dark and depleted. The invariant is:

```text
sum(A over active cells) + sum(latent_A over inactive cells) == initial_total_A
```

This must hold exactly as an integer equality at every tick.

## Laws

### L1. Hard Transfer

Amplitude exchange moves integer quanta.

- An actor can transfer only if `A_actor > 0`.
- Transfer is down-gradient or into unspent dark vacuum; depleted dark cells are not valid amplitude targets in v0.2.0.
- The transfer amount is an integer debit from the actor and an equal integer credit to the target.
- Sub-integer influence is converted into a stochastic single-quantum transfer gate.
- A failed transfer changes no amplitude ledger state.

The first implementation should use a one-quantum gate:

```text
transfer_q = 1 with probability clamp(kA * influence, 0, 1)
transfer_q = 0 otherwise
```

### L2. Activation

If a dark target has latent budget and receives a transfer, activation moves that local latent budget into active amplitude:

```text
A_target += latent_A_target + transfer_q
latent_A_target = 0
active_target = true
```

The incoming transfer is still debited from the actor. The target's latent budget is not created; it was already part of the global invariant.

If a dark target has `latent_A == 0`, no transfer gate is attempted for that target in v0.2.0. This is what makes depletion shadows persistent constraints instead of temporarily empty cells.

### L3. Exhaustion Deactivation

At tick end:

```text
if active and A == 0:
    active = false
    V = 0
    P = 0
```

No recharge is included in v0.2.0. Depleted dark cells remain depleted unless a later version explicitly adds recharge or fossil-state retention.

### L4. Information Labels

Payload takeover and vector inheritance remain information-label dynamics, but they must not change the amplitude ledger. If a transfer fails, label updates tied to that transfer should also fail unless an explicit label-only channel is added in a later version.

## Metrics

Add these metrics before running v0.2 experiments:

```text
total_A
active_A
latent_A
depleted_cells
deactivation_events
amplitude_transfers
failed_transfer_gates
ledger_error
```

`ledger_error` must be exactly `0` for accepted v0.2 runs.

## Golden Gate

The implementation must preserve a v0.1 compatibility path:

```yaml
constants:
  conservation: soft
  deactivation: none
```

Under that path, the Finding 018 replay suite must still reproduce:

- protected/absorber split at `cross_payload_coupling = 0.209375` versus `0.2109375`;
- first semantic divergence at tick `337`, sequence `15`;
- vector inheritance draw `0.01315728279463102`;
- final paired active-site counts, largest connected component, LCF, and cluster count.

## First Predictions

1. Budget-bounded growth: active count is bounded by the conserved amplitude ledger.
2. Depletion shadows: irreversible spending leaves spatial constraints that future growth must route around.
3. Absorber is no longer structurally guaranteed: fronts can stall on depleted regions.
4. Identity may become structural: domains may be protected by depleted moats even with `cross_payload_coupling = 1.0`.
5. Openness should improve: v0.2 should increase commitment time or leave some runs uncommitted within the same sampled horizon.
6. Motion becomes testable: propagating packets can advance by spending budget and deactivating behind themselves.

## Non-Goals

- Do not claim mass without localized propagating structures and a measured dispersion relation.
- Do not claim energy without exact ledger invariance.
- Do not compare v0.1 and v0.2 runs as one-parameter sweeps; this is a model-class boundary.
