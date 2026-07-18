# ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001

Status: **v0.4 ledgers complete with positive classifications; independent
replay complete with one shared-reducer exception disclosed**

Started: `2026-07-14`

Content-addressed result commit: `0795a6efa0252411c66479cb87863349e20ec886`

Terminal classification:
`constructive_sufficiency_passed_direct_symmetry_qca_sector`

This experiment is the first separately registered follow-up to
`ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001`. It replaces the parent's ordered
product mass-mix/transport walk with the established direct symmetry-derived
Dirac QCA family, under a fresh registration.

The content-addressed v0.4 ledgers record:

- 4/4 development scenarios and 16/16 development witness groups;
- clean-checkpoint development replay of the committed result;
- 2/2 single-use confirmation scenarios and 8/8 confirmation witness groups;
- clean-checkpoint confirmation replay of the committed result;
- positive operator, refinement, observable, analytic-leakage,
  architecture-integrity, causality, parity, time-reversal, unitarity, and
  resource classifications; and
- six serialized post-primary boundary controls.

A post-result semantic audit found that the primary empirical pi-sector
reducer, the algorithmically separate replay reducer, and the non-gating
`ROUGH-POTENTIAL` control all used `4*abs(r) >= 3*N` instead of the registered
`8*abs(r) >= 3*N`. The implemented predicate selects no lattice modes. The
serialized measured pi-sector zeros, their pass flags, and the
`ROUGH-POTENTIAL` zero are withdrawn as evidence. Replay reproduced the same
defect and therefore did not independently validate that predicate. The
pre-outcome analytic tails used the correct registered boundary and remain
valid. See [POST_RESULT_AUDIT.md](POST_RESULT_AUDIT.md).

The authoritative human-readable result is [RESULTS.md](RESULTS.md). Canonical
numeric evidence is in:

- `output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/development_results_v0.4.json`;
- `output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/confirmation_results_v0.4.json`; and
- `independent_verification_receipt_v0.4.json` in this directory.

The outcome-free localization, continuum, global-spectrum, and prospective
protocol audits remain the construction record. They establish the two-layer
full-space Margolus witness, exact resource clock, leading Dirac generator
with a quadratic finite-step correction, exact signed-step reversal, the
opposite-mass pi-mode pseudodoubler, and the boundary between the declared
hard-core qubit lift and canonical fermionic second quantization.

Historical infrastructure lineages are preserved:

- v0.1 stopped before ledger creation on an independent complex-Gram
  eigensolver error;
- v0.2 wrote a primary-passing development ledger rejected by replay because
  the Fourier basis was constructed at ambient 53-bit precision;
- v0.3 wrote a primary-passing development ledger rejected by replay because
  a rigorous row-sum norm bound was too loose under potential coupling; and
- v0.4 changed only the certified norm reducer and lifecycle paths, not any
  scientific scenario, state, map, threshold, gate, control, or stopping rule.

Together with the verified product walk, the intact evidence supports a
qualified constructive-sufficiency claim for the shared bounded role core
across two registered update specifications. It does not establish the
complete originally registered direct role because the empirical zone-edge
gate is withdrawn. For free one-excitation evolution, the direct block is
exactly a half-cell time-frame
conjugate of the product block after mass-angle remapping, and adjacent product
gates can be fused into the same parameterized two-mode form. The product
registration also did not freeze the mass mixer's vacuum and
double-occupation phases. Consequently this comparison does not establish
architecture-class breadth, full-space update inequivalence, or a
resource advantage. The depth and gate-work totals are exact only for the two
sealed, nonminimal protocol clocks. It also does not support a new-automaton,
whole-zone, fermionic-QFT, minimality, uniqueness, necessity, or ontological
claim.

## Exact clean-detached-worktree replay

Run each replay at the stage checkpoint whose ledger it verifies. From the
repository root, with the recorded CPython 3.14.0 environment containing
`python-flint==0.9.0` and `mpmath==1.3.0`:

```sh
IOTA_QCA_REPLAY_PYTHON="$PWD/.venv/bin/python"
IOTA_QCA_DEV_REPLAY=$(mktemp -d /tmp/iota-qca-v04-dev-replay.XXXXXX)
git worktree add --detach "$IOTA_QCA_DEV_REPLAY/worktree" b96e70a1c0c61f64bd1bd51a0ecb9d021d9bef50
(
  cd "$IOTA_QCA_DEV_REPLAY/worktree"
  PYTHONDONTWRITEBYTECODE=1 "$IOTA_QCA_REPLAY_PYTHON" -m src.quantum_dirac_symmetry_qca.cli --root . verify-result --stage development
)
git worktree remove "$IOTA_QCA_DEV_REPLAY/worktree"
rmdir "$IOTA_QCA_DEV_REPLAY"
```

The verifier's exact stdout line is:

```json
{"classification":"development_passed","path":"output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/development_results_v0.4.json","stage":"development","status":"registered_stage_result_independently_verified"}
```

Then replay confirmation independently:

```sh
IOTA_QCA_REPLAY_PYTHON="$PWD/.venv/bin/python"
IOTA_QCA_CONFIRM_REPLAY=$(mktemp -d /tmp/iota-qca-v04-confirm-replay.XXXXXX)
git worktree add --detach "$IOTA_QCA_CONFIRM_REPLAY/worktree" 0795a6efa0252411c66479cb87863349e20ec886
(
  cd "$IOTA_QCA_CONFIRM_REPLAY/worktree"
  PYTHONDONTWRITEBYTECODE=1 "$IOTA_QCA_REPLAY_PYTHON" -m src.quantum_dirac_symmetry_qca.cli --root . verify-result --stage confirmation
)
git worktree remove "$IOTA_QCA_CONFIRM_REPLAY/worktree"
rmdir "$IOTA_QCA_CONFIRM_REPLAY"
```

The verifier's exact stdout line is:

```json
{"classification":"constructive_sufficiency_passed_direct_symmetry_qca_sector","path":"output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/confirmation_results_v0.4.json","stage":"confirmation","status":"registered_stage_result_independently_verified"}
```

These commands establish byte-bound, algorithmically separate reconstruction
at the two exact checkpoint commits. They are not external replication, and—by
the disclosed shared predicate—do not independently validate the withdrawn
empirical pi-sector records. The `--skip-receipt` form is preparation-only and
is not a release check:

```sh
.venv/bin/python scripts/validate_archived_quantum_dirac_symmetry_qca.py --skip-receipt
```

Normal archive validation requires the canonical receipt by omitting that
flag. Release validation additionally requires the annotated completion tag:

```sh
.venv/bin/python scripts/validate_archived_quantum_dirac_symmetry_qca.py --require-completion-tag
```
