"""Independent spectral Dirac target machinery for disclosed small fixtures.

The public solver is intentionally capped at the synthetic |r|<=2 fixture.
Registered |r|<=64 target evaluation is not exposed before a freeze.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from mpmath import mp

from .protocol import PHYSICAL_LENGTH, WORK_DPS
from .spec import QuantumDiracSpecError


def _mpf(value: int | str | Fraction):
    if isinstance(value, Fraction):
        return mp.mpf(value.numerator) / value.denominator
    return mp.mpf(value)


def mode_index(r: int, component: int, cutoff: int) -> int:
    if type(r) is not int or not -cutoff <= r <= cutoff:
        raise QuantumDiracSpecError("Fourier mode is outside the target cutoff")
    if component not in (0, 1):
        raise QuantumDiracSpecError("component index must be zero or one")
    return 2 * (r + cutoff) + component


def build_spectral_hamiltonian(
    *,
    cutoff: int,
    mass: int | str | Fraction,
    length: int | str | Fraction = PHYSICAL_LENGTH,
    potential_amplitude: int | str | Fraction = 0,
    potential_phase_pi: int | str | Fraction = 0,
    dps: int = WORK_DPS,
) -> mp.matrix:
    if type(cutoff) is not int or cutoff < 0:
        raise QuantumDiracSpecError("target cutoff must be a nonnegative integer")
    with mp.workdps(dps):
        physical_length = _mpf(length)
        mass_value = _mpf(mass)
        amplitude = _mpf(potential_amplitude)
        phase = mp.pi * _mpf(potential_phase_pi)
        dimension = 2 * (2 * cutoff + 1)
        hamiltonian = mp.matrix(dimension, dimension)
        for r in range(-cutoff, cutoff + 1):
            k_value = 2 * mp.pi * r / physical_length
            r_index = mode_index(r, 0, cutoff)
            l_index = mode_index(r, 1, cutoff)
            hamiltonian[r_index, r_index] = k_value
            hamiltonian[l_index, l_index] = -k_value
            hamiltonian[r_index, l_index] = mass_value
            hamiltonian[l_index, r_index] = mass_value

        if amplitude:
            upward = amplitude * mp.exp(1j * phase) / 2
            downward = amplitude * mp.exp(-1j * phase) / 2
            for source_r in range(-cutoff, cutoff + 1):
                for component in (0, 1):
                    source = mode_index(source_r, component, cutoff)
                    if source_r + 1 <= cutoff:
                        target = mode_index(source_r + 1, component, cutoff)
                        hamiltonian[target, source] += upward
                    if source_r - 1 >= -cutoff:
                        target = mode_index(source_r - 1, component, cutoff)
                        hamiltonian[target, source] += downward
        return hamiltonian


def hermitian_exponential(
    hamiltonian: mp.matrix,
    *,
    duration: int | str | Fraction,
    dps: int = WORK_DPS,
) -> mp.matrix:
    if not isinstance(hamiltonian, mp.matrix) or hamiltonian.rows != hamiltonian.cols:
        raise QuantumDiracSpecError("Hamiltonian must be a square mpmath matrix")
    with mp.workdps(dps):
        eigenvalues, eigenvectors = mp.eighe(hamiltonian)
        phases = mp.diag(
            [mp.exp(-1j * _mpf(duration) * eigenvalues[index]) for index in range(eigenvalues.rows)]
        )
        return eigenvectors * phases * eigenvectors.H


def apply_propagator(propagator: mp.matrix, state: mp.matrix) -> mp.matrix:
    if propagator.cols != state.rows:
        raise QuantumDiracSpecError("target propagator and state dimensions differ")
    return propagator * state


def dyson_tail_bound(
    *,
    amplitude: int | str | Fraction,
    duration: int | str | Fraction,
    first_omitted_order: int,
    dps: int = WORK_DPS,
):
    if type(first_omitted_order) is not int or first_omitted_order < 1:
        raise QuantumDiracSpecError("first omitted Dyson order must be positive")
    with mp.workdps(dps):
        lam = abs(_mpf(amplitude) * _mpf(duration))
        return 2 * mp.exp(lam) * lam**first_omitted_order / mp.factorial(
            first_omitted_order
        )


@dataclass(frozen=True)
class FixtureTargetSolver:
    cutoff: int = 2
    dps: int = WORK_DPS

    def __post_init__(self) -> None:
        if self.cutoff != 2:
            raise QuantumDiracSpecError(
                "pre-freeze target solver is restricted to disclosed cutoff 2"
            )
        if self.dps < 80:
            raise QuantumDiracSpecError("target fixture requires at least 80 decimal digits")

    def propagator(
        self,
        *,
        mass: int | str | Fraction,
        duration: int | str | Fraction,
        length: int | str | Fraction = PHYSICAL_LENGTH,
        potential_amplitude: int | str | Fraction = 0,
        potential_phase_pi: int | str | Fraction = 0,
    ) -> mp.matrix:
        hamiltonian = build_spectral_hamiltonian(
            cutoff=self.cutoff,
            mass=mass,
            length=length,
            potential_amplitude=potential_amplitude,
            potential_phase_pi=potential_phase_pi,
            dps=self.dps,
        )
        return hermitian_exponential(
            hamiltonian,
            duration=duration,
            dps=self.dps,
        )
