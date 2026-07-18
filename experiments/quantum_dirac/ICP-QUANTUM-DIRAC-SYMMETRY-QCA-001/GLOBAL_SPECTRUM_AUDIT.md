# Global Spectrum, Branch, Doubling, and Full-Space-Extension Audit

Search ID: `ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001`

Date: `2026-07-15`

Status: **audit complete; outcome-free; protocol design may proceed only with
the boundaries below**

## Audit conclusion

The direct QCA has an exact two-band unitary spectrum over the complete
Brillouin zone.  For a nonzero dimensionless mass `|mu|<1`, both the zero- and
pi-quasienergy gaps are open and equal.  There is no additional low-energy
Dirac cone at zero quasienergy in `1+1D`.  There is, however, an exact
zone-edge partner: after removal of the Floquet phase `-1`, the law near
`q=-pi` is the same low-momentum direct law with the opposite mass sign.  This
is a high-quasienergy Dirac-like mode and therefore a **pi-mode
pseudodoubler**, not a traditional zero-energy fermion doubler.

The pseudodoubler does not invalidate a prospectively bounded, low-momentum,
single-particle role test.  It does invalidate any claim that the candidate is
globally Dirac-equivalent, doubler-free, safe for an interacting Dirac sea, or
adequate over the whole Brillouin zone.  The prospective protocol must exclude
and monitor the zone-edge sector rather than hiding it.

The declared full-space circuit remains an honest local qubit QCA, but it is
not the canonical fermionic second quantization of the one-particle walk.  The
two lifts agree on vacuum and one-excitation action and differ by local
double-occupation phases.  Consequently, the present experiment can make no
multiparticle free-fermion or interacting-field claim.

These are algebraic design results on disclosed fixtures, not registered
Dirac-role outcomes.

## Exact global spectrum

Write

```text
q  = k delta in [-pi,pi),
mu = m delta,
n  = sqrt(1-mu^2),       |mu| <= 1.
```

The direct momentum block is

```text
U_mu(q) = [[n exp(-i q), -i mu],
           [-i mu,       n exp(+i q)]].
```

It has

```text
det U_mu(q) = 1,
tr  U_mu(q) = 2 n cos(q).
```

Define the principal band angle

```text
omega(q,mu) = arccos(n cos(q)) in [0,pi].
```

The exact eigenvalues and principal quasienergies are

```text
lambda_+(q) = exp(-i omega),     E_+(q) = +omega/delta,
lambda_-(q) = exp(+i omega),     E_-(q) = -omega/delta,
```

where quasienergy is defined modulo `2 pi/delta`.  If

```text
alpha = asin(|mu|),
```

then

```text
alpha <= omega(q,mu) <= pi-alpha.
```

The minimum occurs at `q=0`; the maximum occurs at the identified zone edge
`q=-pi = +pi`.  Measured on the quasienergy circle, the two band gaps are

```text
zero-quasienergy gap = 2 alpha,
pi-quasienergy gap   = 2 alpha.
```

For `mu != 0`, no eigenvalue lies on the negative-real-axis branch cut and the
principal logarithm is defined throughout the Brillouin zone.  At `mu=0`, the
zero gap closes at `q=0`, while the pi gap closes at `q=-pi`; there
`U_0(-pi)=-I`, so a principal matrix logarithm is branch-ambiguous.  The
small-step effective generator in `CONTINUUM_AUDIT.md` is intentionally
restricted to the branch-safe neighborhood of `q=0` and must not be presented
as a global continuous Hamiltonian.

The sign of `mu` does not change the two eigenvalue sets, but it changes their
eigenvectors and the orientation of the effective mass axis.  A protocol must
therefore retain the signed mass in state and intervention maps rather than
inferring it from eigenvalues alone.

## Group velocity and causal bound

For the two principal bands,

```text
v_+(q) = + n sin(q) / sqrt(1-n^2 cos(q)^2),
v_-(q) = - n sin(q) / sqrt(1-n^2 cos(q)^2).
```

Because `q=k delta` and `E=omega/delta`, this dimensionless derivative is the
physical group velocity in units with one cell per macrostep.  Its exact bound
is

```text
|v_s(q)| <= n = sqrt(1-mu^2) <= 1,
```

with equality in magnitude at `q=+/-pi/2` for `|mu|<1`.  The spectral speed
therefore respects the radius-one causal cone but does not generally saturate
it.  Near `q=0`, with `mu=m delta`, it reduces to the Dirac value
`+/- k/sqrt(k^2+m^2)` under refinement.

At `mu=0`, the principal bands have cusps at the degeneracies because a
principal-band label swaps there.  The underlying chiral eigenphases remain
smooth between the identified crossings.

## Exact pi-mode partner and doubling classification

For a small zone-edge displacement `p`, there is an exact identity, not only a
series approximation:

```text
U_mu(-pi+p) = -U_-mu(p).
```

The prefactor `-1` shifts quasienergy by `pi/delta`.  After that shift, the
zone-edge mode has the same dispersion and local spinor dynamics as the
low-momentum mode with the mass sign reversed.  In particular, at `mu=0`,

```text
omega(p,0)          = |p|,
pi-omega(-pi+p,0)  = |p|.
```

Thus the classification is:

- **no traditional `1+1D` zero-energy doubler:** the only zero-quasienergy
  Dirac crossing is at `q=0`;
- **one identified pi-mode pseudodoubler:** the zone-edge crossing is high in
  principal quasienergy but locally Dirac-like after the Floquet phase shift;
  and
- **no doubler-free global claim:** an interacting or filled-sea extension can
  make the modular quasienergy boundary physically consequential.

Gupta and Short define pseudo-doublers precisely as high-energy modes that
behave like low-energy Dirac particles and warn that they can destabilize an
interacting discrete-time vacuum.  Their 2026 paper is now accepted by
*Physical Review A*: <https://doi.org/10.1103/kkz3-fthm> and
<https://arxiv.org/abs/2601.15885>.  The exact identity above places this
candidate on the limited side of that boundary.  It is not evidence against
the frozen single-particle low-momentum role; it is evidence against expanding
that role without a new architecture and protocol.

## Mass-domain endpoints

The complete mathematical mass domain is `|mu|<=1`:

- `mu=0`: the gaps close at both zero and pi quasienergy; the two massless
  chiral channels propagate at unit speed away from the crossings;
- `0<|mu|<1`: both circular gaps are open, the spectrum is dispersive, and the
  maximum group speed is `sqrt(1-mu^2)`;
- `|mu|=1`: `n=0`, the update is the momentum-independent on-site matrix
  `-i mu sigma_x`, both bands are flat at `+/-pi/2`, and group velocity is zero;
  and
- `|mu|>1`: `n` is imaginary and the displayed block is not unitary, so this
  is outside the candidate family.

The existing executable candidate deliberately keeps the strict guard
`|mu|<1`.  A prospective registered domain must add a numerical margin from
`|mu|=1`; the endpoints are analytic failure boundaries, not suggested
registered cases.

## Hard-core qubit extension versus canonical fermionic lift

The one-particle update does not uniquely determine collision sectors.  The
current two-layer qubit circuit makes the following local choices:

| Local gate | One-particle block determinant | Current `|11>` phase | Canonical fermionic `|11>` phase |
|---|---:|---:|---:|
| edge scatter `C_mu=n X-i mu I` | `-1` | `+1` | `-1` |
| on-site routing `X` | `-1` | `+1` | `-1` |

For a number-preserving two-mode one-particle unitary `V`, canonical fermionic
second quantization acts on the double-occupation wedge sector by `det(V)`.
The present ordinary qubit gates instead fix `|11>`.  The local lifts therefore
agree on `|00>` and the complete one-excitation block, but differ on
collisions.  Those controlled collision phases can change multiparticle
scattering and the full many-body spectrum even though every one-particle
witness is unchanged.

This distinction is consistent with the published separation between
single-particle walks, causal fermionic lifts, and multiparticle QCA field
constructions:

- Farrelly and Short, *Physical Review A* 89, 012302 (2014),
  <https://arxiv.org/abs/1303.4652>;
- Mlodinow and Brun, *Physical Review A* 102, 042211 (2020),
  <https://arxiv.org/abs/2006.08927>.

The current experiment remains a hard-core occupation-qubit existence witness
on `4^N`, not a canonical fermionic Fock lift.  Replacing the collision phases,
declaring anticommutation conventions on the periodic boundary, or adding
interactions would create a different architecture requiring its own audit.

## Local implementability and index position

The explicit edge-scatter/on-site-SWAP partition already proves that the
full-space qubit QCA is a finite-depth local circuit.  In the terminology of
Gross, Nesme, Vogts, and Werner, it is therefore in the locally implementable,
trivial-index class: QCA index `1`; correspondingly, the one-particle walk has
zero net left/right flow.  See *Communications in Mathematical Physics* 310,
419–454 (2012), <https://arxiv.org/abs/0910.3675>.

This positions the localization correctly.  It is not a new general theorem
about partitionability or one-dimensional QCA classification.

## Mandatory prospective protocol boundaries

The protocol stage may proceed only if it incorporates all of the following:

1. **Low-momentum encoding.** Freeze an input band with a stated positive
   distance from the Brillouin-zone edge.  Do not claim whole-zone recovery.
2. **Zone-edge leakage accounting.** For every position-dependent intervention,
   bound or certify momentum leakage outside the target band over the complete
   horizon.  A low-momentum initial state alone is insufficient if the
   intervention can transfer it toward the pi sector.
3. **Explicit pseudodoubler failure control.** Include a prospectively declared
   high-momentum control showing the known zone-edge departure or classify it
   as an analytic excluded boundary.  It must not be discovered and suppressed
   after registered inspection.
4. **Branch-safe metrics.** Operator/channel comparison may be global on the
   registered input subspace, but any effective-Hamiltonian metric must remain
   on a declared logarithm branch separated from `-1`.
5. **Mass margin.** Register only `|m delta| <= mu_max < 1` with a justified
   margin and report the mass-dependent speed bound.
6. **Single-excitation claim.** Keep the registered target, maps, and outcomes
   in the one-excitation sector.  Do not infer free-fermion, Dirac-sea,
   multiparticle, or interaction behavior from the chosen hard-core lift.
7. **Architecture integrity.** Do not replace this law with the 2026
   doubler-reducing walk family or a canonical fermionic lift to improve the
   result.  Either change is a new search identifier, not a protocol tweak.

## Literature and novelty disposition

Bisio, D'Ariano, and Tosini already derive the direct one-dimensional Dirac
automaton from homogeneity and discrete symmetries, give its dispersion, and
compare it with Dirac evolution: *Annals of Physics* 354, 244–264 (2015),
<https://arxiv.org/abs/1212.2839>.  Gross et al. already characterize locally
implementable one-dimensional walks and QCAs by their index.  Farrelly--Short
and Mlodinow--Brun already supply causal fermionic and multiparticle-lift
context.  Gupta--Short now supply the closest explicit pseudo-doubling and
interacting-vacuum boundary.

Accordingly:

```text
no novelty is claimed for the direct automaton, its exact dispersion, the
existence of local QCA decompositions, the pi-mode phenomenon, or fermionic
lifting in general.
```

The prospective project-level contribution remains the operational and
reproducible combination of a frozen causal-role benchmark, two separately
registered local update specifications, declared protocol-resource accounting,
prospective development/confirmation separation, and algorithmically separate
replay.  A later post-result comparison showed that the free one-excitation
blocks are exact time-frame conjugates after mass-angle remapping, while the
product registration did not freeze the full-space phases needed for a
collision-sector comparison.  The global and post-result audits therefore
narrow this to enumerative registered-specification coverage; they do not
support two inequivalent architecture classes or enlarge the claim.

The dated search record is
`docs/literature/symmetry_qca_global_spectrum_2026-07-15.md`.

## Executable evidence and disposition

`src/quantum_dirac_symmetry_qca/spectrum.py` implements the exact global band
angle, eigenvalues, group velocity, circular gaps, endpoint behavior,
zone-edge partner identity, and local fermionic-lift phase accounting.  It
accepts only the disclosed fixture labels `N=6` and `N=10` and rejects
registered or undeclared sizes.

Seven tests independently check the characteristic polynomial on every
momentum of both disclosed even cycles, exact band edges and gaps, the velocity
derivative and speed bound, the opposite-mass pi partner, flat unitary mass
endpoints, hard-core/fermionic collision phases, and access guards.

The global-spectrum audit is complete.  No registered lattice, state,
scenario, threshold, seal, opening manifest, or result was created or
evaluated.  The next stage is outcome-free prospective protocol design with
the seven mandatory boundaries above.
