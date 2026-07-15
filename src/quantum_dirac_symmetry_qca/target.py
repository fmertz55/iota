"""Target-only cutoff-3 harmonic-2 fixtures for the protocol draft."""

from __future__ import annotations

from fractions import Fraction

from mpmath import mp

from .candidate import MINIMUM_DPS, SymmetryQCAFixtureError, _number
from .spec import guard_pre_freeze_target


FIXTURE_CUTOFF = 3
FIXTURE_HARMONIC = 2
MINIMUM_TAYLOR_TERMS = 180


def _require_precision(dps: int) -> None:
    if type(dps) is not int or dps < MINIMUM_DPS:
        raise SymmetryQCAFixtureError("target fixture requires at least 80 digits")


def mode_index(r: int, component: int, cutoff: int = FIXTURE_CUTOFF) -> int:
    guard_pre_freeze_target(cutoff=cutoff)
    if type(r) is not int or not -cutoff <= r <= cutoff:
        raise SymmetryQCAFixtureError("Fourier mode is outside the fixture cutoff")
    if component not in (0, 1):
        raise SymmetryQCAFixtureError("component index must be zero or one")
    return 2 * (r + cutoff) + component


def build_harmonic_two_hamiltonian(
    *,
    cutoff: int = FIXTURE_CUTOFF,
    mass: int | str | Fraction,
    length: int | str | Fraction = 16,
    potential_amplitude: int | str | Fraction = 0,
    potential_phase_pi: int | str | Fraction = 0,
    dps: int = 90,
) -> mp.matrix:
    """Build the disclosed small Dirac target with a harmonic-2 potential."""

    guard_pre_freeze_target(cutoff=cutoff)
    _require_precision(dps)
    with mp.workdps(dps):
        physical_length = _number(length)
        mass_value = _number(mass)
        amplitude = _number(potential_amplitude)
        phase = mp.pi * _number(potential_phase_pi)
        if (
            not mp.isfinite(physical_length)
            or physical_length <= 0
            or not mp.isfinite(mass_value)
            or not mp.isfinite(amplitude)
            or not mp.isfinite(phase)
        ):
            raise SymmetryQCAFixtureError("target fixture parameters are invalid")
        dimension = 2 * (2 * cutoff + 1)
        hamiltonian = mp.matrix(dimension, dimension)
        for mode in range(-cutoff, cutoff + 1):
            wave_number = 2 * mp.pi * mode / physical_length
            right = mode_index(mode, 0, cutoff)
            left = mode_index(mode, 1, cutoff)
            hamiltonian[right, right] = wave_number
            hamiltonian[left, left] = -wave_number
            hamiltonian[right, left] = mass_value
            hamiltonian[left, right] = mass_value
        upward = amplitude * mp.exp(1j * phase) / 2
        downward = amplitude * mp.exp(-1j * phase) / 2
        for source_mode in range(-cutoff, cutoff + 1):
            for component in (0, 1):
                source = mode_index(source_mode, component, cutoff)
                if source_mode + FIXTURE_HARMONIC <= cutoff:
                    target = mode_index(
                        source_mode + FIXTURE_HARMONIC, component, cutoff
                    )
                    hamiltonian[target, source] += upward
                if source_mode - FIXTURE_HARMONIC >= -cutoff:
                    target = mode_index(
                        source_mode - FIXTURE_HARMONIC, component, cutoff
                    )
                    hamiltonian[target, source] += downward
        return hamiltonian


def eigensystem_propagator(
    hamiltonian: mp.matrix,
    *,
    duration: int | str | Fraction,
    dps: int = 90,
) -> mp.matrix:
    _require_precision(dps)
    if not isinstance(hamiltonian, mp.matrix) or hamiltonian.rows != 14 or hamiltonian.cols != 14:
        raise SymmetryQCAFixtureError("target fixture Hamiltonian must be 14 by 14")
    with mp.workdps(dps):
        time = _number(duration)
        if not mp.isfinite(time):
            raise SymmetryQCAFixtureError("target duration must be finite")
        eigenvalues, eigenvectors = mp.eighe(hamiltonian)
        phases = mp.diag(
            [mp.exp(-1j * time * eigenvalues[index]) for index in range(14)]
        )
        return eigenvectors * phases * eigenvectors.H


def independent_taylor_propagator(
    hamiltonian: mp.matrix,
    *,
    duration: int | str | Fraction,
    terms: int = 220,
    dps: int = 100,
) -> mp.matrix:
    """Independently exponentiate the fixture by a direct matrix series."""

    _require_precision(dps)
    if type(terms) is not int or terms < MINIMUM_TAYLOR_TERMS:
        raise SymmetryQCAFixtureError(
            f"independent target fixture requires at least {MINIMUM_TAYLOR_TERMS} terms"
        )
    if not isinstance(hamiltonian, mp.matrix) or hamiltonian.rows != 14 or hamiltonian.cols != 14:
        raise SymmetryQCAFixtureError("target fixture Hamiltonian must be 14 by 14")
    with mp.workdps(dps):
        generator = -1j * _number(duration) * hamiltonian
        result = mp.eye(14)
        term = mp.eye(14)
        for order in range(1, terms + 1):
            term = term * generator / order
            result += term
        return result

