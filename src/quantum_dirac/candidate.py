"""Partitioned product-walk engine for disclosed outcome-free fixtures.

The public engine constructor accepts only the preregistered synthetic fixture
sizes. There is intentionally no registered-evaluation permit in this draft.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Iterable, Sequence

from mpmath import mp

from .protocol import WORK_DPS
from .spec import QuantumDiracSpecError, guard_pre_freeze_fixture


def _mpf(value: int | str | Fraction):
    if isinstance(value, Fraction):
        return mp.mpf(value.numerator) / value.denominator
    return mp.mpf(value)


def _copy_matrix(value: mp.matrix) -> mp.matrix:
    result = mp.matrix(value.rows, value.cols)
    for row in range(value.rows):
        for column in range(value.cols):
            result[row, column] = value[row, column]
    return result


def _require_state(state: mp.matrix, n_sites: int) -> None:
    if not isinstance(state, mp.matrix):
        raise QuantumDiracSpecError("state must be an mpmath matrix")
    if state.rows != 2 * n_sites or state.cols < 1:
        raise QuantumDiracSpecError(
            f"state shape must be (2N,columns), received ({state.rows},{state.cols})"
        )


def basis_state(n_sites: int, site: int, component: str) -> mp.matrix:
    if type(n_sites) is not int or n_sites <= 0:
        raise QuantumDiracSpecError("N must be positive")
    if type(site) is not int or not 0 <= site < n_sites:
        raise QuantumDiracSpecError("basis site is outside the cycle")
    if component not in ("R", "L"):
        raise QuantumDiracSpecError("component must be R or L")
    state = mp.matrix(2 * n_sites, 1)
    state[2 * site + (component == "L"), 0] = 1
    return state


def norm_squared(state: mp.matrix):
    total = mp.mpf("0")
    for row in range(state.rows):
        for column in range(state.cols):
            total += abs(state[row, column]) ** 2
    return total


def scalar_phase_layer(
    state: mp.matrix,
    *,
    n_sites: int,
    delta: int | str | Fraction,
    potentials: Sequence,
    dps: int = WORK_DPS,
) -> mp.matrix:
    _require_state(state, n_sites)
    if len(potentials) != n_sites:
        raise QuantumDiracSpecError("potential vector must contain one value per site")
    with mp.workdps(dps):
        dt = _mpf(delta)
        result = _copy_matrix(state)
        for site, potential in enumerate(potentials):
            phase = mp.exp(-1j * dt * _mpf(potential))
            for component in (0, 1):
                row = 2 * site + component
                for column in range(state.cols):
                    result[row, column] = phase * state[row, column]
        return result


def mass_mix_layer(
    state: mp.matrix,
    *,
    n_sites: int,
    angle: int | str | Fraction,
    dps: int = WORK_DPS,
) -> mp.matrix:
    _require_state(state, n_sites)
    with mp.workdps(dps):
        theta = _mpf(angle)
        cosine = mp.cos(theta)
        off_diagonal = -1j * mp.sin(theta)
        result = mp.matrix(state.rows, state.cols)
        for site in range(n_sites):
            r_row = 2 * site
            l_row = r_row + 1
            for column in range(state.cols):
                r_value = state[r_row, column]
                l_value = state[l_row, column]
                result[r_row, column] = cosine * r_value + off_diagonal * l_value
                result[l_row, column] = off_diagonal * r_value + cosine * l_value
        return result


def on_site_swap_layer(state: mp.matrix, *, n_sites: int) -> mp.matrix:
    _require_state(state, n_sites)
    result = mp.matrix(state.rows, state.cols)
    for site in range(n_sites):
        r_row = 2 * site
        l_row = r_row + 1
        for column in range(state.cols):
            result[r_row, column] = state[l_row, column]
            result[l_row, column] = state[r_row, column]
    return result


def directed_edge_swap_layer(state: mp.matrix, *, n_sites: int) -> mp.matrix:
    _require_state(state, n_sites)
    result = mp.matrix(state.rows, state.cols)
    for site in range(n_sites):
        l_row = 2 * site + 1
        right_neighbor_r_row = 2 * ((site + 1) % n_sites)
        for column in range(state.cols):
            result[l_row, column] = state[right_neighbor_r_row, column]
            result[right_neighbor_r_row, column] = state[l_row, column]
    return result


def transport_via_swaps(state: mp.matrix, *, n_sites: int) -> mp.matrix:
    return directed_edge_swap_layer(
        on_site_swap_layer(state, n_sites=n_sites),
        n_sites=n_sites,
    )


def direct_logical_transport(state: mp.matrix, *, n_sites: int) -> mp.matrix:
    """Transparent logical S used only as an algebraic fixture oracle."""

    _require_state(state, n_sites)
    result = mp.matrix(state.rows, state.cols)
    for site in range(n_sites):
        for column in range(state.cols):
            result[2 * ((site + 1) % n_sites), column] = state[2 * site, column]
            result[2 * ((site - 1) % n_sites) + 1, column] = state[2 * site + 1, column]
    return result


@dataclass(frozen=True)
class FixturePermit:
    n_sites: int

    @classmethod
    def issue(cls, n_sites: int) -> "FixturePermit":
        guard_pre_freeze_fixture(n_sites=n_sites)
        return cls(n_sites=n_sites)


class FixtureCandidateEngine:
    """High-precision engine restricted to N=8 and N=16 fixtures."""

    def __init__(self, permit: FixturePermit, *, dps: int = WORK_DPS):
        if not isinstance(permit, FixturePermit):
            raise QuantumDiracSpecError("a disclosed fixture permit is required")
        guard_pre_freeze_fixture(n_sites=permit.n_sites)
        if type(dps) is not int or dps < 80:
            raise QuantumDiracSpecError("fixture engine requires at least 80 decimal digits")
        self.n_sites = permit.n_sites
        self.dps = dps

    def macrostep(
        self,
        state: mp.matrix,
        *,
        delta: int | str | Fraction,
        mass: int | str | Fraction,
        potentials: Sequence | None = None,
    ) -> mp.matrix:
        _require_state(state, self.n_sites)
        with mp.workdps(self.dps):
            current = state
            if potentials is not None:
                current = scalar_phase_layer(
                    current,
                    n_sites=self.n_sites,
                    delta=delta,
                    potentials=potentials,
                    dps=self.dps,
                )
            angle = _mpf(delta) * _mpf(mass)
            current = mass_mix_layer(
                current,
                n_sites=self.n_sites,
                angle=angle,
                dps=self.dps,
            )
            return transport_via_swaps(current, n_sites=self.n_sites)

    def evolve(
        self,
        state: mp.matrix,
        *,
        steps: int,
        delta: int | str | Fraction,
        mass: int | str | Fraction,
        potential_at_step: Callable[[int], Sequence | None] | None = None,
    ) -> mp.matrix:
        if type(steps) is not int or steps < 0:
            raise QuantumDiracSpecError("steps must be a nonnegative integer")
        current = state
        for step in range(steps):
            potentials = None if potential_at_step is None else potential_at_step(step)
            current = self.macrostep(
                current,
                delta=delta,
                mass=mass,
                potentials=potentials,
            )
        return current
