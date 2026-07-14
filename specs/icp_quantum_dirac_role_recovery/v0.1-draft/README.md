# ICP Quantum-Dirac Role Recovery `0.1-draft`

This directory contains the machine-readable outcome-free design for
`ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001`.

Current state:

```text
implementation active
not frozen
production outcome runner absent and disabled
registered outcomes forbidden
```

The controlling human-readable draft is
`docs/ICP_QUANTUM_DIRAC_ROLE_RECOVERY_CONTRACT.md`. `protocol.json` records the
same choices for schema and implementation work. It is not an outcome seal and
does not authorize a candidate run.

The directory now includes the canonical candidate, target, map, scenario,
state, partition, fixture, and schema records. Prospective manifests live in
the experiment directory. The implementation has a certified Arb/Acb fixture
backend and a separately expressed `mpmath` verifier.

The remaining freeze blockers are the complete registered stage runner,
state-witness and symmetry reducers, full result validation and independent
ledger replay, atomic writer, and final freeze/open/result command provenance.
