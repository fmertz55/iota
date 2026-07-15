"""Outcome-free continuum fixtures for the direct symmetry-derived Dirac QCA.

The primary effective generator uses the exact SU(2) axis--angle form.  The
independent fixture deliberately reconstructs the principal matrix logarithm
from its power series instead of reusing that reduction.
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
MINIMUM_LOG_TERMS = 200
CONTINUUM_FIXTURE_BOUND = Fraction(1, 4)


def _require_precision(dps: int) -> None:
    if type(dps) is not int or dps < MINIMUM_DPS:
        raise SymmetryQCAFixtureError(
            "fixture arithmetic requires at least 80 digits"
        )


def _finite_number(value: NumberInput, name: str):
    number = _number(value)
    if not mp.isfinite(number):
        raise SymmetryQCAFixtureError(f"{name} must be finite")
    return number


def _continuum_parameters(
    *,
    n_sites: int,
    k: NumberInput,
    mass: NumberInput,
    delta: NumberInput,
    dps: int,
):
    _require_fixture_size(n_sites)
    _require_precision(dps)
    wave_number = _finite_number(k, "k")
    physical_mass = _finite_number(mass, "mass")
    step = _finite_number(delta, "delta")
    if step == 0:
        raise SymmetryQCAFixtureError("delta must be nonzero")
    dimensionless_mass = physical_mass * step
    dimensionless_wave_number = wave_number * step
    bound = _number(CONTINUUM_FIXTURE_BOUND)
    if (
        abs(dimensionless_mass) >= bound
        or abs(dimensionless_wave_number) >= bound
    ):
        raise SymmetryQCAFixtureError(
            "continuum fixtures require abs(mass*delta) and abs(k*delta) < 1/4"
        )
    normalization = mp.sqrt(1 - dimensionless_mass * dimensionless_mass)
    return (
        wave_number,
        physical_mass,
        step,
        dimensionless_wave_number,
        dimensionless_mass,
        normalization,
    )


def momentum_update(
    *,
    n_sites: int,
    k: NumberInput,
    mass: NumberInput,
    delta: NumberInput,
    dps: int = 90,
) -> mp.matrix:
    """Return the exact direct-QCA momentum block on a disclosed fixture."""

    with mp.workdps(dps):
        _, _, _, q, mu, normalization = _continuum_parameters(
            n_sites=n_sites, k=k, mass=mass, delta=delta, dps=dps
        )
        update = mp.matrix(2, 2)
        update[0, 0] = normalization * mp.exp(-1j * q)
        update[0, 1] = -1j * mu
        update[1, 0] = -1j * mu
        update[1, 1] = normalization * mp.exp(1j * q)
        return update


def dirac_generator(
    *,
    n_sites: int,
    k: NumberInput,
    mass: NumberInput,
    dps: int = 90,
) -> mp.matrix:
    """Return ``k sigma_z + mass sigma_x`` with fixture access guards."""

    with mp.workdps(dps):
        _require_fixture_size(n_sites)
        _require_precision(dps)
        wave_number = _finite_number(k, "k")
        physical_mass = _finite_number(mass, "mass")
        return mp.matrix(
            [[wave_number, physical_mass], [physical_mass, -wave_number]]
        )


def effective_generator(
    *,
    n_sites: int,
    k: NumberInput,
    mass: NumberInput,
    delta: NumberInput,
    dps: int = 90,
) -> mp.matrix:
    """Return the exact principal effective generator by SU(2) reduction."""

    with mp.workdps(dps):
        _, _, step, q, mu, normalization = _continuum_parameters(
            n_sites=n_sites, k=k, mass=mass, delta=delta, dps=dps
        )
        scalar = normalization * mp.cos(q)
        x_axis = mu
        z_axis = normalization * mp.sin(q)
        radius = mp.sqrt(x_axis * x_axis + z_axis * z_axis)
        if radius == 0:
            return mp.matrix(2, 2)
        angle = mp.atan2(radius, scalar)
        scale = angle / (step * radius)
        return scale * mp.matrix([[z_axis, x_axis], [x_axis, -z_axis]])


def first_correction_coefficient(
    *,
    n_sites: int,
    k: NumberInput,
    mass: NumberInput,
    dps: int = 90,
) -> mp.matrix:
    """Return ``K_2`` in ``H_eff = H_D + delta**2 K_2 + O(delta**4)``."""

    with mp.workdps(dps):
        _require_fixture_size(n_sites)
        _require_precision(dps)
        wave_number = _finite_number(k, "k")
        physical_mass = _finite_number(mass, "mass")
        z_correction = -(physical_mass**2) * wave_number / 3
        x_correction = (
            physical_mass * (wave_number**2 + physical_mass**2) / 6
        )
        return mp.matrix(
            [
                [z_correction, x_correction],
                [x_correction, -z_correction],
            ]
        )


def corrected_generator(
    *,
    n_sites: int,
    k: NumberInput,
    mass: NumberInput,
    delta: NumberInput,
    dps: int = 90,
) -> mp.matrix:
    """Return the Dirac generator plus the derived first correction."""

    with mp.workdps(dps):
        _, _, step, _, _, _ = _continuum_parameters(
            n_sites=n_sites, k=k, mass=mass, delta=delta, dps=dps
        )
        return dirac_generator(
            n_sites=n_sites, k=k, mass=mass, dps=dps
        ) + step**2 * first_correction_coefficient(
            n_sites=n_sites, k=k, mass=mass, dps=dps
        )


def independent_log_generator(
    *,
    n_sites: int,
    k: NumberInput,
    mass: NumberInput,
    delta: NumberInput,
    terms: int = 256,
    dps: int = 90,
) -> mp.matrix:
    """Independently recover ``(i/delta) log(U)`` from a matrix-log series."""

    if type(terms) is not int or terms < MINIMUM_LOG_TERMS:
        raise SymmetryQCAFixtureError(
            f"independent matrix log requires at least {MINIMUM_LOG_TERMS} terms"
        )
    with mp.workdps(dps):
        _, _, step, q, mu, normalization = _continuum_parameters(
            n_sites=n_sites, k=k, mass=mass, delta=delta, dps=dps
        )

        # Construct this block independently of momentum_update and do not use
        # the SU(2) axis--angle reduction employed by effective_generator.
        update = mp.matrix(2, 2)
        update[0, 0] = normalization * (mp.cos(q) - 1j * mp.sin(q))
        update[0, 1] = -1j * mu
        update[1, 0] = -1j * mu
        update[1, 1] = normalization * (mp.cos(q) + 1j * mp.sin(q))

        displacement = update - mp.eye(2)
        power = displacement.copy()
        logarithm = mp.matrix(2, 2)
        for order in range(1, terms + 1):
            coefficient = mp.mpf(1 if order % 2 else -1) / order
            logarithm += coefficient * power
            power = power * displacement
        return (1j / step) * logarithm
