# Post-result audit: reducer defect and architecture-equivalence scope

Date: `2026-07-18`

Status: **confirmed implementation defect and exact one-excitation time-frame
relation; content-addressed v0.4 ledgers preserved and scientific
interpretation qualified**

## Defect

The sealed protocol defines the monitored zone-edge sector by
`|q| >= 3 pi / 4`.  With the discrete convention `q = 2 pi r / N`, this is

```
8 |r| >= 3 N.
```

The primary reducer, the algorithmically separate verifier, and the
non-gating rough-potential control instead implemented

```
4 |r| >= 3 N.
```

Because every serialized lattice mode satisfies `|r| <= N/2`, the implemented
predicate selects no modes.  The serialized candidate pi-sector probabilities
and the rough-potential value `0` are therefore vacuous and are withdrawn as
scientific evidence.  The duplicated predicate also means that independent
replay does not independently validate this reducer.

The audit counts `0` selected modes at every registered size under the
implemented predicate, versus `81`, `161`, and `321` under the intended
predicate at `N=320`, `640`, and `1280`.

Affected sealed code:

- `src/quantum_dirac_symmetry_qca/reducers.py`,
  `pi_sector_probability_ball`;
- `src/quantum_dirac_symmetry_qca/independent_verifier.py`,
  `_pi_probability`; and
- `src/quantum_dirac_symmetry_qca/runner.py`,
  `_rough_potential_pi_probability`.

The existing reducer test probes a low mode but does not test the boundary
modes `r=119` and `r=120` at `N=320`, so it did not expose the empty
sector.

## Scope and impact

The defect affects only the empirical pi-sector reducer and the
`ROUGH-POTENTIAL` post-primary control.  It does not alter:

- any uniform operator-distance value or refinement classification;
- position or momentum total variation, current, fidelity, norm, parity,
  time-reversal-role, causality, architecture-integrity, or resource records;
- the exact global-spectrum and opposite-mass partner analysis; or
- the pre-outcome analytic zone-edge tail.

The analytic tail routines use the correct coarsest boundary
`3 * 320 / 8 = 120`.  Their content-addressed serialized probability upper bounds are
approximately `1.6213e-261` for the development harmonic-2 potential and
`1.8334e-164` for the confirmation harmonic-3 potential, both below the
frozen `1e-24` threshold.  Thus the intended low-band leakage threshold
remains supported analytically, but the paper must not claim that its separate
empirical reducer was validly evaluated.

The positive terminal classification remains a content-addressed ledger fact.  It is
reported only with this audit qualification: the statement “every intended
registered gate was executed correctly” is withdrawn.  The qualified
bounded-core claim now rests on the intact uniform evolution and witness
certificates plus the pre-outcome analytic leakage bound.

## Audit-only diagnostic

`scripts/audit_direct_qca_pi_sector.py` reproduces the empty-sector logic,
checks the correct boundary, reads and threshold-checks the content-addressed
analytic-tail values, and recomputes only
the disclosed non-gating rough-potential control with the intended predicate.
That audit-only diagnostic is

```
3.4860345440118994972e-8
```

rather than the ledger's vacuous zero.  It is not a registered outcome and
cannot repair, replace, or broaden the single-use confirmation result.

## Architecture-equivalence scope

The manuscript audit also exposed an exact relation that narrows the original
architecture-breadth interpretation. With
`K(q) = exp(-i q sigma_z)` and `theta = arcsin(mu)`, the direct free block is

```
U_direct(q) = K(q)^(1/2) exp(-i theta sigma_x) K(q)^(1/2)
            = K(q)^(-1/2) [K(q) exp(-i theta sigma_x)] K(q)^(1/2).
```

Thus it is exactly conjugate to a mass-angle-remapped product block by a
chiral half-cell time-frame change. The registered finite circuits still have
different gate partitions, parameterizations, and protocol clocks, but their
free one-excitation laws are not algebraically independent under that frame
equivalence.

The apparent resource difference is also compilation-convention-dependent.
For a product mass rotation `R_theta = exp(-i theta X)`, an adjacent SWAP
fuses as `X R_theta = cos(theta) X - i sin(theta) I`, the same parameterized
one-excitation gate form used by the direct edge scatter after remapping. The
sealed depth/work totals remain exact for the registered, nonminimal clocks;
they do not imply a hardware or compilation-invariant advantage.

Finally, the product registration specifies its mass mixer only on the
one-excitation block. It does not freeze the `|00>` and `|11>` phases. The
direct hard-core lift is explicit, but the archive cannot use the two records
to establish full-space product-versus-direct inequivalence.

## Disposition

- Do not modify or replace the v0.4 ledgers.
- Do not describe confirmation replay as validating the intended pi-sector
  reducer.
- Mark the empirical pi-sector and rough-potential records as withdrawn in the
  manuscript, result summary, handoff, and figures.
- Describe the scientific result as two separately registered update
  specifications recovering a shared bounded role core, not as two proven
  inequivalent architecture classes or a resource advantage.
- Treat any corrected registered empirical leakage test as a separately
  versioned and prospectively opened follow-on.
- In that follow-on, add exact boundary tests at `r=119`, `r=120`, the
  Nyquist mode, and their signed partners.
