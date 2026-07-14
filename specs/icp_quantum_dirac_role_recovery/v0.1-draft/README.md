# ICP Quantum-Dirac Role Recovery `0.1-draft`

This directory contains the machine-readable outcome-free design for
`ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001`.

Current state:

```text
implementation complete
not frozen
production runner present and disabled by Git provenance
registered outcomes forbidden
v0.1 execution incomplete with no result; v0.2 numerical retry pending freeze
```

The controlling human-readable draft is
`docs/ICP_QUANTUM_DIRAC_ROLE_RECOVERY_CONTRACT.md`. `protocol.json` records the
same choices for schema and implementation work. It is not an outcome seal and
does not authorize a candidate run.

The directory now includes the canonical candidate, target, map, scenario,
state, partition, fixture, and schema records. Prospective manifests live in
the experiment directory. The implementation has a certified Arb/Acb fixture
backend and a separately expressed `mpmath` verifier.

The outcome-free package now includes the registered stage runner,
formula-derived witnesses, observable and symmetry reducers, strict ledger
validation, independent clean-checkpoint replay, atomic writers, and the
linear seal/open/run/verify command surface. The next legal step is to commit
this complete implementation, generate the disabled outcome seal as the sole
change in its direct child, and attach the annotated freeze tag.
