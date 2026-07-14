"""Algorithmically separate fixture verifier.

This module does not import the production-style candidate or target engines.
It reconstructs circuit matrices directly and uses a Taylor exponential for
the disclosed small target fixture.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from mpmath import mp

from .protocol import WORK_DPS
from .spec import QuantumDiracSpecError, guard_pre_freeze_fixture


def _mpf(value):
    if isinstance(value, Fraction):
        return mp.mpf(value.numerator) / value.denominator
    return mp.mpf(value)


def matrix_max_abs(matrix: mp.matrix):
    return max(abs(matrix[row, column]) for row in range(matrix.rows) for column in range(matrix.cols))


def independent_mass_matrix(
    *, n_sites: int, angle, dps: int = WORK_DPS
) -> mp.matrix:
    guard_pre_freeze_fixture(n_sites=n_sites)
    with mp.workdps(dps):
        cosine = mp.cos(_mpf(angle))
        off_diagonal = -1j * mp.sin(_mpf(angle))
        result = mp.matrix(2 * n_sites, 2 * n_sites)
        for site in range(n_sites):
            row = 2 * site
            result[row, row] = cosine
            result[row, row + 1] = off_diagonal
            result[row + 1, row] = off_diagonal
            result[row + 1, row + 1] = cosine
        return result


def independent_phase_matrix(
    *, n_sites: int, delta, potentials: Sequence, dps: int = WORK_DPS
) -> mp.matrix:
    guard_pre_freeze_fixture(n_sites=n_sites)
    if len(potentials) != n_sites:
        raise QuantumDiracSpecError("potential vector length mismatch")
    with mp.workdps(dps):
        result = mp.matrix(2 * n_sites, 2 * n_sites)
        for site, value in enumerate(potentials):
            phase = mp.exp(-1j * _mpf(delta) * _mpf(value))
            result[2 * site, 2 * site] = phase
            result[2 * site + 1, 2 * site + 1] = phase
        return result


def independent_transport_matrix(*, n_sites: int) -> mp.matrix:
    guard_pre_freeze_fixture(n_sites=n_sites)
    result = mp.matrix(2 * n_sites, 2 * n_sites)
    for site in range(n_sites):
        result[2 * ((site + 1) % n_sites), 2 * site] = 1
        result[2 * ((site - 1) % n_sites) + 1, 2 * site + 1] = 1
    return result


def independent_fixture_step(
    state: mp.matrix,
    *,
    n_sites: int,
    delta,
    mass,
    potentials: Sequence | None = None,
    dps: int = WORK_DPS,
) -> mp.matrix:
    guard_pre_freeze_fixture(n_sites=n_sites)
    with mp.workdps(dps):
        mass_matrix = independent_mass_matrix(
            n_sites=n_sites,
            angle=_mpf(delta) * _mpf(mass),
            dps=dps,
        )
        step = independent_transport_matrix(n_sites=n_sites) * mass_matrix
        if potentials is not None:
            step *= independent_phase_matrix(
                n_sites=n_sites,
                delta=delta,
                potentials=potentials,
                dps=dps,
            )
        return step * state


def closed_form_dirac_block(
    *, k, mass, duration, dps: int = WORK_DPS
) -> mp.matrix:
    """Independent exp(-it(k sigma_z + m sigma_x))."""

    with mp.workdps(dps):
        k_value = _mpf(k)
        mass_value = _mpf(mass)
        time = _mpf(duration)
        omega = mp.sqrt(k_value**2 + mass_value**2)
        identity = mp.eye(2)
        hamiltonian = mp.matrix(
            [[k_value, mass_value], [mass_value, -k_value]]
        )
        if omega == 0:
            return identity
        return (
            mp.cos(omega * time) * identity
            - 1j * mp.sin(omega * time) * hamiltonian / omega
        )


def taylor_exponential(
    matrix: mp.matrix,
    *,
    multiplier,
    dps: int = WORK_DPS,
    max_terms: int = 2000,
) -> mp.matrix:
    """Independent high-precision exponential for disclosed small matrices."""

    if matrix.rows != matrix.cols:
        raise QuantumDiracSpecError("Taylor exponential requires a square matrix")
    with mp.workdps(dps):
        scaled = mp.mpc(multiplier) * matrix
        norm_bound = max(
            mp.fsum(abs(scaled[row, column]) for column in range(scaled.cols))
            for row in range(scaled.rows)
        )
        squarings = 0
        while norm_bound > mp.mpf("0.5"):
            scaled /= 2
            norm_bound /= 2
            squarings += 1

        result = mp.eye(matrix.rows)
        term = mp.eye(matrix.rows)
        tolerance = mp.power(10, -(dps - 15))
        for order in range(1, max_terms + 1):
            term = term * scaled / order
            result += term
            if matrix_max_abs(term) <= tolerance:
                break
        else:
            raise QuantumDiracSpecError("Taylor exponential did not converge")

        for _ in range(squarings):
            result = result * result
        return result


def independent_target_propagator(
    hamiltonian: mp.matrix,
    *,
    duration,
    dps: int = WORK_DPS,
) -> mp.matrix:
    with mp.workdps(dps):
        return taylor_exponential(
            hamiltonian,
            multiplier=-mp.j * _mpf(duration),
            dps=dps,
        )
