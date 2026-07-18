# Direct Symmetry-QCA Result

Date: `2026-07-18`

Terminal classification:
`constructive_sufficiency_passed_direct_symmetry_qca_sector`

The frozen v0.4 direct symmetry-derived QCA ledgers record positive terminal
classifications for all four development scenarios, both single-use
confirmation scenarios, every state-witness group, and the registered
structural tests. Algorithmically separate clean-checkpoint reconstruction
reproduced both committed ledgers. A later semantic audit found one shared
empty empirical pi-sector predicate; the affected empirical records and pass
flags are withdrawn below, while the correct pre-outcome analytic tail remains
valid.

## Gate summary

| Partition | Scenarios | Witness groups | Structure / leakage gates | Independent replay |
|---|---:|---:|---:|---:|
| Development | 4 / 4 | 16 / 16 | positive, except withdrawn empirical pi reducer | pass, with shared-predicate exception |
| Confirmation | 2 / 2 | 8 / 8 | positive, except withdrawn empirical pi reducer | pass, with shared-predicate exception |

The largest direct-only certified operator-distance upper bounds were:

| Lattice size | Largest upper bound | Absolute gate |
|---:|---:|---:|
| 320 | `0.000560191117713` | `0.0040` |
| 640 | `0.000139960025446` | `0.0012` |
| 1280 | `0.0000349845247903` | `0.0004` |

The largest potential-split upper bounds were:

| Lattice size | Largest upper bound | Absolute gate |
|---:|---:|---:|
| 320 | `0.00275976665161` | `0.020` |
| 640 | `0.00137607978225` | `0.011` |
| 1280 | `0.000687867298787` | `0.006` |

Direct-only refinement ratios were approximately `0.24984..0.24997`, inside
the frozen `0.35` gate. Potential-split ratios were approximately
`0.49444..0.49987`, inside `0.62`.

The largest certified witness upper bounds over both partitions were:

| Metric | Largest value | Gate |
|---|---:|---:|
| Position total variation | `0.0000989023619157` | `0.010` |
| Momentum total variation | `0.000139706533026` | `0.010` |
| Total-current error | `0.0000367366409624` | `0.020` |
| Local-current L1 error | `0.000196393479817` | `0.020` |
| Infidelity | `0.000000315463599415` | `0.0001` |
| Primary/independent state disagreement | `5.06257855764e-17` | `1e-11` |
| Zitterbewegung current supremum error | `0.0000228399814400` | `0.020` |
| Measured pi-sector probability | withdrawn (serialized `0`) | `1e-24` |
| Analytic pi-tail upper bound | `1.83340201803e-164` | `1e-24` |

All unitarity, parity, time-reversal-role, exact causal-support,
architecture-integrity, resource-accounting, refinement, target-tail, and
analytic zone-edge-leakage checks remain supported. The empirical zone-edge
reducer does not: both implementations evaluated `4*abs(r) >= 3*N`, an empty
sector, instead of the registered `8*abs(r) >= 3*N`. Its serialized zeros and
pass flags are not scientific evidence. The largest parity and unitarity
residuals were `9.63631915265e-74` and `1.22267893008e-67`.

## Resource result

The full-space hard-core-qubit localization has local Hilbert dimension `4`,
storage `2N` qubits, no ancillas, and exact causal radius one. A free
macrostep has depth `2` and gate-work `2N`; an active-potential macrostep has
depth `3` and gate-work `3N`. At `N=1280`, the free `T=2` run used 160
macrosteps, 320 elementary layers, and 409,600 gates. The confirmation H3
potential run used 416 layers and 532,480 gates.

These totals are not an efficiency head-to-head with the product walk because
the registered refinements, scenarios, observation grids, and gates differ.
They are exact counts for the sealed, nonminimal decompositions only. The
product mass mixer can be fused with a neighboring SWAP into the direct
two-mode gate form, so the counts do not imply a compilation-invariant or
hardware resource advantage.

## Post-primary boundary controls

| Control | Metric | Value |
|---|---|---:|
| Opposite-mass pi partner | maximum matrix residual | `2.49489834375e-111` |
| High momentum | operator distance | `0.00791313128731` |
| `|mu|=1` endpoint | maximum group velocity | `0` |
| Long horizon `T=12` | low-band operator distance | `0.000821366329862` |
| Rough potential | measured pi probability | withdrawn (serialized `0`) |
| Fermionic lift | double-occupation phase distance | `2` |

These controls characterize the boundary and cannot broaden or repair the
registered primary result. The `ROUGH-POTENTIAL` reducer shared the same empty
predicate as the primary and replay reducers. An audit-only recomputation with
the intended predicate gives approximately `3.48603454401e-8`; it is neither a
registered outcome nor a repair. See [POST_RESULT_AUDIT.md](POST_RESULT_AUDIT.md).

## Content-addressed ledgers and provenance

- Development ledger: `output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/development_results_v0.4.json`, SHA-256 `89d7c65a37bf8d38fea3a87b7f656c02cae57664fcf6b53b725fb8ace7c228c4`.
- Confirmation ledger: `output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/confirmation_results_v0.4.json`, SHA-256 `be5a9f85770e1d201abbc269c26da25d821f11f67db364c434473b5c70517e65`.
- Outcome seal SHA-256: `ff3f58461559578b07ea7e93b8819edbad2bde66c95cc1af89f971a4110b974b`.
- Freeze tag: `icp-quantum-dirac-symmetry-qca-001-v0.4-frozen` at commit `890962df6a86637cf9a4fe8b40d88f21a02f2399`.
- Linear lifecycle: freeze `890962df` -> development open `f5f5d604` -> development result `b96e70a1` -> confirmation open `6398124a` -> confirmation result `0795a6ef`.
- Content-addressed result commit: `0795a6efa0252411c66479cb87863349e20ec886`.
- Independent verification receipt: `independent_verification_receipt_v0.4.json` in this directory.

The v0.1 execution-incomplete lineage and the v0.2/v0.3 independently
unverified development ledgers remain preserved. Neither earlier primary pass
is counted as a result, and confirmation was not opened in those lineages.

## Exact replay and archive validation

Each stage must be reconstructed in a clean detached worktree at its own exact
result commit. From the repository root, using the recorded CPython
3.14.0 environment with `python-flint==0.9.0` and `mpmath==1.3.0`, run:

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

Expected verifier stdout:

```json
{"classification":"development_passed","path":"output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/development_results_v0.4.json","stage":"development","status":"registered_stage_result_independently_verified"}
```

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

Expected verifier stdout:

```json
{"classification":"constructive_sufficiency_passed_direct_symmetry_qca_sector","path":"output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/confirmation_results_v0.4.json","stage":"confirmation","status":"registered_stage_result_independently_verified"}
```

Replay proves reconstruction under the same frozen mathematical specification;
it is not external replication or semantic specification diversity. In
particular, both implementations copied the withdrawn empirical pi-sector
predicate. The archive validator rejects duplicate JSON keys, noncanonical
bytes, wrong per-stage blobs, hashes, classifications, runtime versions, CLI
outputs, seal binding, or missing exception disclosure. Its preparation-only
mode is:

```sh
.venv/bin/python scripts/validate_archived_quantum_dirac_symmetry_qca.py --skip-receipt
```

Normal validation requires the canonical receipt by omitting that option.
Release validation additionally requires the documentation commit to carry the
annotated tag `icp-quantum-dirac-symmetry-qca-001-v0.4-complete`:

```sh
.venv/bin/python scripts/validate_archived_quantum_dirac_symmetry_qca.py --require-completion-tag
```

## Supported claim

The intact evidence supports only a qualified constructive-sufficiency claim
for the shared bounded role core across two separately registered strictly
local quantum-information update specifications in their single-excitation,
low-momentum domains. It does not establish the complete originally registered
direct role because the empirical zone-edge gate is withdrawn. The direct
free one-excitation block is exactly related to a mass-angle-remapped product block
by a half-cell time-frame conjugacy, and adjacent product gates admit fusion
into the same parameterized form. Moreover, the product registration did not
freeze the mass mixer's vacuum or double-occupation phases. The result
therefore does not establish breadth across inequivalent architecture classes,
full-space product-versus-direct inequivalence, or a resource advantage.

It does not establish discovery of the direct automaton, architecture
independence, whole-zone or doubler-free Dirac equivalence, a canonical
fermionic lift, multiparticle or interacting quantum field theory, minimality,
necessity, uniqueness, or ontology. The measured pi-sector and rough-potential
zeros are withdrawn; only the correct pre-outcome analytic leakage bound is
used in the bounded claim.
