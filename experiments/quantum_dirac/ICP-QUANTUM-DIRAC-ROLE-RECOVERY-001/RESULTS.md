# Quantum-Dirac Role-Recovery Result

Date: `2026-07-14`

Terminal classification:
`constructive_sufficiency_passed_frozen_dirac_sector`

The frozen product-walk construction passed all four development scenarios,
both single-use confirmation scenarios, the confirmation-state cross-witness
suite, and the algorithmically separate clean-checkpoint replay of both
ledgers.

## Gate summary

| Partition | Scenarios passed | Operator gates | Witness groups | Structure gates | Independent replay |
|---|---:|---:|---:|---:|---:|
| Development | 4 / 4 | 4 / 4 | 16 / 16 | 4 / 4 | pass |
| Confirmation | 2 / 2 | 2 / 2 | 8 / 8 | 2 / 2 | pass |
| Confirmation cross-witness | 1 / 1 | n/a | 4 / 4 | n/a | pass |

The largest operator-distance upper bound over all six scenarios was:

| Lattice size | Largest upper bound | Absolute gate |
|---:|---:|---:|
| 256 | `0.0300073` | `0.20` |
| 512 | `0.0149955` | `0.10` |
| 1024 | `0.00749669` | `0.05` |

The largest registered witness values over both partitions were:

| Metric | Largest value | Gate |
|---|---:|---:|
| Position total variation | `0.00194047` | `0.05` |
| Momentum total variation | `0.000200605` | `0.05` |
| Total-current error | `0.00844655` | `0.10` |
| Local-current L1 error | `0.00844655` | `0.10` |
| Infidelity | `0.0000450699` | `0.0025` |
| Numerical norm residual | `3.39037e-13` | `1e-12` |
| Primary/independent state disagreement | `0` | `1e-11` |
| Zitterbewegung current supremum error | `0.00881467` | `0.10` |

All parity, time-reversal refinement, exact causal-support, massless boundary,
unitarity, resource-accounting, negative-coherence, and refinement gates also
passed. The five declared non-gating boundary controls (`HIGH-K`,
`HIGH-MASS`, `LONG-HORIZON`, `FINITE-RING`, and `DEPHASED`) were emitted only
after confirmation passed.

## Immutable ledgers

- Development: `output/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001/development_results_v0.4.json`, SHA-256 `c9f445358a7ada5d8d20208c485529e6c6da93768f2ee1c9dea76afed2baab7b`.
- Confirmation: `output/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001/confirmation_results_v0.4.json`, SHA-256 `34c16fd959148d99a5e32c4836d69acb33794d548c11c8ac83986990742fac72`.
- Freeze tag: `icp-quantum-dirac-role-recovery-001-v0.4-frozen`.
- Completion tag: `icp-quantum-dirac-role-recovery-001-v0.4-complete`.

## Supported claim

The result supports only that the declared quantum-information primitives are
constructively sufficient to realize the frozen 1+1D single-particle Dirac
operational role within the registered low-momentum domain, horizon, maps,
and accuracy.

It does not establish minimality, necessity, uniqueness, all-scale continuum
equivalence, multiparticle or interacting field theory, or an ontological
reduction. Architectural breadth requires new prospective experiments rather
than parameter variations of this product walk.
