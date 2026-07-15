"""Outcome-free global-spectrum fixtures for the direct Dirac QCA.

The functions in this module cover the complete one-particle Brillouin zone,
but remain restricted to the two disclosed nonregistered fixture labels.  The
finite-size label is an access guard only; the analytic momentum block itself
does not depend on a registered lattice.
"""

from __future__ import annotations

from fractions import Fraction

from mpmath import mp

from .candidate import (
    MINIMUM_DPS,
    SymmetryQCAFixtureError,
    _number,
    _require_fixture_size,
)


NumberInput = int | str | Fraction


def _require_precision(dps: int) -> None:
    if type(dps) is not int or dps < MINIMUM_DPS:
        raise SymmetryQCAFixtureError(
            "fixture arithmetic requires at least 80 digits"
        )


def _global_parameters(
    *,
    n_sites: int,
    q: NumberInput,
    mu: NumberInput,
    dps: int,
):
    _require_fixture_size(n_sites)
    _require_precision(dps)
    momentum = _number(q)
    mass = _number(mu)
    if not mp.isfinite(momentum) or abs(momentum) > mp.pi:
        raise SymmetryQCAFixtureError(
            "dimensionless momentum q must lie in the closed Brillouin zone"
        )
    if not mp.isfinite(mass) or abs(mass) > 1:
        raise SymmetryQCAFixtureError(
            "dimensionless mass mu must be finite with abs(mu) <= 1"
        )
    normalization = mp.sqrt(1 - mass * mass)
    return momentum, mass, normalization


def global_momentum_update(
    *,
    n_sites: int,
    q: NumberInput,
    mu: NumberInput,
    dps: int = 90,
) -> mp.matrix:
    """Return the direct update at dimensionless momentum ``q``."""

    with mp.workdps(dps):
        momentum, mass, normalization = _global_parameters(
            n_sites=n_sites, q=q, mu=mu, dps=dps
        )
        return mp.matrix(
            [
                [normalization * mp.exp(-1j * momentum), -1j * mass],
                [-1j * mass, normalization * mp.exp(1j * momentum)],
            ]
        )


def principal_band_angle(
    *,
    n_sites: int,
    q: NumberInput,
    mu: NumberInput,
    dps: int = 90,
):
    """Return ``omega in [0,pi]`` with ``cos(omega)=n cos(q)``."""

    with mp.workdps(dps):
        momentum, _, normalization = _global_parameters(
            n_sites=n_sites, q=q, mu=mu, dps=dps
        )
        return mp.acos(normalization * mp.cos(momentum))


def principal_eigenvalues(
    *,
    n_sites: int,
    q: NumberInput,
    mu: NumberInput,
    dps: int = 90,
) -> tuple[object, object]:
    """Return the two exact principal-branch eigenvalue expressions."""

    with mp.workdps(dps):
        angle = principal_band_angle(
            n_sites=n_sites, q=q, mu=mu, dps=dps
        )
        return mp.exp(-1j * angle), mp.exp(1j * angle)


def group_velocity(
    *,
    n_sites: int,
    q: NumberInput,
    mu: NumberInput,
    band: int,
    dps: int = 90,
):
    """Return ``d(+/- omega)/dq`` for ``band=+1`` or ``band=-1``."""

    if type(band) is not int or band not in (-1, 1):
        raise SymmetryQCAFixtureError("band must be +1 or -1")
    with mp.workdps(dps):
        momentum, _, normalization = _global_parameters(
            n_sites=n_sites, q=q, mu=mu, dps=dps
        )
        denominator = mp.sqrt(
            1 - normalization * normalization * mp.cos(momentum) ** 2
        )
        if denominator == 0:
            raise SymmetryQCAFixtureError(
                "band velocity is undefined at a massless degeneracy"
            )
        return band * normalization * mp.sin(momentum) / denominator


def global_band_summary(
    *, n_sites: int, mu: NumberInput, dps: int = 90
) -> dict[str, object]:
    """Return exact band edges, circular gaps, and the speed bound."""

    with mp.workdps(dps):
        _, mass, normalization = _global_parameters(
            n_sites=n_sites, q=0, mu=mu, dps=dps
        )
        edge = mp.asin(abs(mass))
        return {
            "principal_angle_minimum": edge,
            "principal_angle_maximum": mp.pi - edge,
            "zero_quasienergy_gap": 2 * edge,
            "pi_quasienergy_gap": 2 * edge,
            "maximum_group_speed": normalization,
        }


def finite_cycle_momenta(
    *, n_sites: int, dps: int = 90
) -> tuple[object, ...]:
    """Return the disclosed even-cycle momenta in ``[-pi,pi)``."""

    _require_fixture_size(n_sites)
    _require_precision(dps)
    if n_sites % 2:
        raise SymmetryQCAFixtureError("the disclosed spectrum fixtures are even")
    with mp.workdps(dps):
        return tuple(
            2 * mp.pi * mode / n_sites
            for mode in range(-(n_sites // 2), n_sites // 2)
        )


def zone_edge_partner_residual(
    *,
    n_sites: int,
    offset: NumberInput,
    mu: NumberInput,
    dps: int = 90,
):
    """Check ``U_mu(-pi+p) = -U_-mu(p)`` at the Floquet-zone edge."""

    with mp.workdps(dps):
        displacement = _number(offset)
        if not mp.isfinite(displacement) or not 0 <= displacement <= mp.pi:
            raise SymmetryQCAFixtureError(
                "zone-edge offset must lie between zero and pi"
            )
        edge = global_momentum_update(
            n_sites=n_sites, q=-mp.pi + displacement, mu=mu, dps=dps
        )
        partner = global_momentum_update(
            n_sites=n_sites, q=displacement, mu=-_number(mu), dps=dps
        )
        return max(
            abs(edge[row, column] + partner[row, column])
            for row in range(2)
            for column in range(2)
        )


def canonical_fermionic_two_mode_lift(one_particle: mp.matrix) -> mp.matrix:
    """Lift a two-mode one-particle block with its determinant on ``|11>``.

    The computational basis is ``|00>,|01>,|10>,|11>``.  The supplied block
    occupies the one-particle rows and columns in that same local convention.
    """

    if not isinstance(one_particle, mp.matrix) or (
        one_particle.rows != 2 or one_particle.cols != 2
    ):
        raise SymmetryQCAFixtureError("one-particle gate must be a 2 by 2 matrix")
    result = mp.matrix(4, 4)
    result[0, 0] = 1
    for row in range(2):
        for column in range(2):
            result[row + 1, column + 1] = one_particle[row, column]
    result[3, 3] = mp.det(one_particle)
    return result


def full_space_extension_summary(
    *, n_sites: int, mu: NumberInput, dps: int = 90
) -> dict[str, object]:
    """Expose the collision phases distinguishing the two local lifts."""

    with mp.workdps(dps):
        _, mass, normalization = _global_parameters(
            n_sites=n_sites, q=0, mu=mu, dps=dps
        )
        edge_one_particle = mp.matrix(
            [[-1j * mass, normalization], [normalization, -1j * mass]]
        )
        onsite_one_particle = mp.matrix([[0, 1], [1, 0]])
        return {
            "hard_core_edge_double_occupation_phase": mp.mpf(1),
            "fermionic_edge_double_occupation_phase": mp.det(
                edge_one_particle
            ),
            "hard_core_onsite_double_occupation_phase": mp.mpf(1),
            "fermionic_onsite_double_occupation_phase": mp.det(
                onsite_one_particle
            ),
        }
