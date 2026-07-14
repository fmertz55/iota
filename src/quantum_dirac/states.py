"""Frozen encoding and measurement maps for disclosed synthetic fixtures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction

from mpmath import mp

from .protocol import PHYSICAL_LENGTH, WORK_DPS
from .spec import QuantumDiracSpecError, guard_pre_freeze_fixture


def _mpf(value: int | str | Fraction):
    if isinstance(value, Fraction):
        return mp.mpf(value.numerator) / value.denominator
    return mp.mpf(value)


def _component_index(component: str) -> int:
    if component == "R":
        return 0
    if component == "L":
        return 1
    raise QuantumDiracSpecError("component must be R or L")


def encode_fixture_fourier(
    *,
    n_sites: int,
    coefficients: Mapping[tuple[int, str], object],
    dps: int = WORK_DPS,
) -> mp.matrix:
    guard_pre_freeze_fixture(n_sites=n_sites)
    if not coefficients:
        raise QuantumDiracSpecError("fixture Fourier coefficient map is empty")
    with mp.workdps(dps):
        state = mp.matrix(2 * n_sites, 1)
        normalization = mp.sqrt(n_sites)
        seen_modes: set[int] = set()
        for (r, component), coefficient in coefficients.items():
            if type(r) is not int:
                raise QuantumDiracSpecError("Fourier mode must be an integer")
            if not (-n_sites // 2 < r < n_sites // 2):
                raise QuantumDiracSpecError("fixture Fourier mode aliases on the lattice")
            seen_modes.add(r)
            component_index = _component_index(component)
            value = mp.mpc(coefficient)
            for site in range(n_sites):
                phase = mp.exp(2j * mp.pi * r * site / n_sites)
                state[2 * site + component_index, 0] += value * phase / normalization
        return state


def decode_fourier(
    state: mp.matrix,
    *,
    n_sites: int,
    modes: Sequence[int],
    dps: int = WORK_DPS,
) -> dict[tuple[int, str], object]:
    if state.rows != 2 * n_sites or state.cols != 1:
        raise QuantumDiracSpecError("state must be a single (2N)-component column")
    with mp.workdps(dps):
        normalization = mp.sqrt(n_sites)
        result: dict[tuple[int, str], object] = {}
        for r in modes:
            if type(r) is not int:
                raise QuantumDiracSpecError("Fourier modes must be integers")
            for component_index, component in enumerate(("R", "L")):
                value = mp.mpc(0)
                for site in range(n_sites):
                    phase = mp.exp(-2j * mp.pi * r * site / n_sites)
                    value += state[2 * site + component_index, 0] * phase
                result[(r, component)] = value / normalization
        return result


def position_probabilities(state: mp.matrix, *, n_sites: int) -> tuple:
    if state.rows != 2 * n_sites or state.cols != 1:
        raise QuantumDiracSpecError("state must be a single (2N)-component column")
    return tuple(
        abs(state[2 * site, 0]) ** 2 + abs(state[2 * site + 1, 0]) ** 2
        for site in range(n_sites)
    )


def momentum_probabilities(
    state: mp.matrix,
    *,
    n_sites: int,
    modes: Sequence[int],
    dps: int = WORK_DPS,
) -> dict[int, object]:
    coefficients = decode_fourier(
        state,
        n_sites=n_sites,
        modes=modes,
        dps=dps,
    )
    return {
        r: abs(coefficients[(r, "R")]) ** 2 + abs(coefficients[(r, "L")]) ** 2
        for r in modes
    }


def total_directional_current(state: mp.matrix, *, n_sites: int):
    if state.rows != 2 * n_sites or state.cols != 1:
        raise QuantumDiracSpecError("state must be a single (2N)-component column")
    return mp.fsum(
        abs(state[2 * site, 0]) ** 2 - abs(state[2 * site + 1, 0]) ** 2
        for site in range(n_sites)
    )


def local_directional_current(state: mp.matrix, *, n_sites: int) -> tuple:
    if state.rows != 2 * n_sites or state.cols != 1:
        raise QuantumDiracSpecError("state must be a single (2N)-component column")
    return tuple(
        abs(state[2 * site, 0]) ** 2 - abs(state[2 * site + 1, 0]) ** 2
        for site in range(n_sites)
    )


def state_norm_squared(state: mp.matrix):
    return mp.fsum(abs(state[row, 0]) ** 2 for row in range(state.rows))


def pure_state_fidelity(left: mp.matrix, right: mp.matrix):
    if left.rows != right.rows or left.cols != 1 or right.cols != 1:
        raise QuantumDiracSpecError("fidelity requires equal state columns")
    overlap = mp.fsum(
        mp.conj(left[row, 0]) * right[row, 0] for row in range(left.rows)
    )
    return abs(overlap) ** 2


def energy_spinor(
    *,
    r: int,
    mass: int | str | Fraction,
    energy_sign: int,
    length: int | str | Fraction = PHYSICAL_LENGTH,
    dps: int = WORK_DPS,
) -> tuple:
    if type(r) is not int or energy_sign not in (-1, 1):
        raise QuantumDiracSpecError("invalid energy-spinor request")
    with mp.workdps(dps):
        k_value = 2 * mp.pi * r / _mpf(length)
        mass_value = _mpf(mass)
        hamiltonian = mp.matrix([[k_value, mass_value], [mass_value, -k_value]])
        eigenvalues, eigenvectors = mp.eigsy(hamiltonian)
        column = 1 if energy_sign == 1 else 0
        first = eigenvectors[0, column]
        second = eigenvectors[1, column]
        pivot = first if abs(first) > mp.mpf("1e-70") else second
        phase = mp.exp(-1j * mp.arg(pivot))
        first *= phase
        second *= phase
        norm = mp.sqrt(abs(first) ** 2 + abs(second) ** 2)
        return first / norm, second / norm
