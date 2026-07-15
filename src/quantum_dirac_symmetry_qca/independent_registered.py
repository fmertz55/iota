"""Algorithmically separate mpmath replay for the direct-QCA experiment.

Free candidate evolution is assembled from 2x2 momentum blocks.  Potential
evolution is rebuilt from explicit sparse phase, edge-scatter, and routing
operators.  The target uses a separately written sparse Hamiltonian action and
Taylor exponential.  This module imports no primary or fixture constructor.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from mpmath import mp

from .authorization import (
    RegisteredEvaluationPermit,
    RegisteredVerificationPermit,
    validate_registered_access,
)
from .protocol import (
    CONFIRMATION_SCENARIOS,
    DEVELOPMENT_SCENARIOS,
    INDEPENDENT_DPS,
    INPUT_R_MAX,
    INPUT_R_MIN,
    PHYSICAL_LENGTH,
    REGISTERED_OBSERVATION_TIMES,
    REGISTERED_SIZES,
    SPEC_DIR_REF,
    TARGET_R_CUTOFF,
)
from .spec import (
    SymmetryQCASpecError,
    guard_pre_freeze_candidate,
    guard_pre_freeze_target,
    load_json,
    parse_fraction,
)


RegisteredAccess = RegisteredEvaluationPermit | RegisteredVerificationPermit


def _mpf(value: Fraction | int | str):
    if isinstance(value, Fraction):
        return mp.mpf(value.numerator) / value.denominator
    return mp.mpf(value)


def _copy(value: mp.matrix) -> mp.matrix:
    result = mp.matrix(value.rows, value.cols)
    for row in range(value.rows):
        for column in range(value.cols):
            result[row, column] = value[row, column]
    return result


def _maximum_abs(value: mp.matrix):
    return max(
        abs(value[row, column])
        for row in range(value.rows)
        for column in range(value.cols)
    )


def _phase_coefficient(value: str) -> Fraction:
    if value == "0":
        return Fraction(0)
    if value == "pi/2":
        return Fraction(1, 2)
    raise SymmetryQCASpecError("independent potential phase is invalid")


def _interval_value(records: list[list[Any]], time: Fraction) -> Fraction:
    for start, end, value in records:
        if parse_fraction(start) <= time < parse_fraction(end):
            return parse_fraction(value)
    raise SymmetryQCASpecError("independent mass schedule is incomplete")


def _potential_parameters(
    records: list[list[Any]], time: Fraction
) -> tuple[int, Fraction, Fraction] | None:
    for start, end, harmonic, amplitude, phase in records:
        if parse_fraction(start) <= time < parse_fraction(end):
            return harmonic, parse_fraction(amplitude), _phase_coefficient(phase)
    return None


def _observation_steps(delta: Fraction) -> tuple[int, ...]:
    result = []
    for value in REGISTERED_OBSERVATION_TIMES:
        quotient = parse_fraction(value) / delta
        if quotient.denominator != 1:
            raise SymmetryQCASpecError("independent observation grid is misaligned")
        result.append(quotient.numerator)
    return tuple(result)


@dataclass(frozen=True)
class _SparseOperator:
    rows: int
    entries: tuple[tuple[int, int, Any], ...]

    def apply(self, value: mp.matrix) -> mp.matrix:
        if value.rows != self.rows:
            raise SymmetryQCASpecError("sparse operator dimension mismatch")
        result = mp.matrix(self.rows, value.cols)
        for target, source, coefficient in self.entries:
            for column in range(value.cols):
                result[target, column] += coefficient * value[source, column]
        return result

    def adjoint(self) -> "_SparseOperator":
        return _SparseOperator(
            self.rows,
            tuple(
                (source, target, mp.conj(coefficient))
                for target, source, coefficient in self.entries
            ),
        )


def _phase_operator(
    n_sites: int,
    *,
    delta: Fraction,
    potential: tuple[int, Fraction, Fraction] | None,
    reflect: bool = False,
) -> _SparseOperator:
    entries: list[tuple[int, int, Any]] = []
    for site in range(n_sites):
        if potential is None:
            phase = mp.mpc(1)
        else:
            harmonic, amplitude, phase_pi = potential
            coordinate = -site if reflect else site
            value = _mpf(amplitude) * mp.cos(
                2 * mp.pi * harmonic * coordinate / n_sites
                + mp.pi * _mpf(phase_pi)
            )
            phase = mp.exp(-1j * _mpf(delta) * value)
        entries.extend(
            ((2 * site, 2 * site, phase), (2 * site + 1, 2 * site + 1, phase))
        )
    return _SparseOperator(2 * n_sites, tuple(entries))


def _edge_scatter_operator(n_sites: int, mu: Fraction) -> _SparseOperator:
    mass = _mpf(mu)
    if not mp.isfinite(mass) or abs(mass) >= 1:
        raise SymmetryQCASpecError("independent mu is outside the direct-QCA domain")
    normalization = mp.sqrt(1 - mass * mass)
    entries: list[tuple[int, int, Any]] = []
    for site in range(n_sites):
        left = 2 * site + 1
        previous_right = 2 * ((site - 1) % n_sites)
        entries.extend(
            (
                (left, left, -1j * mass),
                (left, previous_right, normalization),
                (previous_right, left, normalization),
                (previous_right, previous_right, -1j * mass),
            )
        )
    return _SparseOperator(2 * n_sites, tuple(entries))


def _routing_swap_operator(n_sites: int) -> _SparseOperator:
    return _SparseOperator(
        2 * n_sites,
        tuple(
            entry
            for site in range(n_sites)
            for entry in (
                (2 * site, 2 * site + 1, 1),
                (2 * site + 1, 2 * site, 1),
            )
        ),
    )


def independent_candidate_fixture(
    state: mp.matrix,
    *,
    n_sites: int,
    mu: Fraction | int | str,
    dps: int = INDEPENDENT_DPS,
) -> mp.matrix:
    guard_pre_freeze_candidate(n_sites=n_sites)
    if not isinstance(state, mp.matrix) or state.rows != 2 * n_sites or state.cols < 1:
        raise SymmetryQCASpecError("independent fixture state shape mismatch")
    if dps < INDEPENDENT_DPS:
        raise SymmetryQCASpecError("independent fixture precision is below 110 digits")
    with mp.workdps(dps):
        scattered = _edge_scatter_operator(n_sites, Fraction(mu)).apply(state)
        return _routing_swap_operator(n_sites).apply(scattered)


def independent_target_fixture(
    *,
    cutoff: int,
    mass: Fraction | int | str,
    potential_amplitude: Fraction | int | str,
    potential_phase_pi: Fraction | int | str = 0,
    dps: int = INDEPENDENT_DPS,
) -> mp.matrix:
    guard_pre_freeze_target(cutoff=cutoff)
    if dps < INDEPENDENT_DPS:
        raise SymmetryQCASpecError("independent target precision is below 110 digits")
    with mp.workdps(dps):
        return _build_target_matrix(
            cutoff=cutoff,
            mass=Fraction(mass),
            harmonic=2,
            amplitude=Fraction(potential_amplitude),
            phase_pi=Fraction(potential_phase_pi),
        )


def _target_row(r: int, component: int, cutoff: int) -> int:
    return 2 * (r + cutoff) + component


def _build_target_matrix(
    *,
    cutoff: int,
    mass: Fraction,
    harmonic: int,
    amplitude: Fraction,
    phase_pi: Fraction,
) -> mp.matrix:
    dimension = 2 * (2 * cutoff + 1)
    result = mp.matrix(dimension, dimension)
    for r in range(-cutoff, cutoff + 1):
        momentum = 2 * mp.pi * r / PHYSICAL_LENGTH
        right = _target_row(r, 0, cutoff)
        left = right + 1
        result[right, right] = momentum
        result[left, left] = -momentum
        result[right, left] = _mpf(mass)
        result[left, right] = _mpf(mass)
    upward = _mpf(amplitude) * mp.exp(1j * mp.pi * _mpf(phase_pi)) / 2
    downward = _mpf(amplitude) * mp.exp(-1j * mp.pi * _mpf(phase_pi)) / 2
    for source_r in range(-cutoff, cutoff + 1):
        for component in (0, 1):
            source = _target_row(source_r, component, cutoff)
            if source_r + harmonic <= cutoff:
                result[_target_row(source_r + harmonic, component, cutoff), source] += upward
            if source_r - harmonic >= -cutoff:
                result[_target_row(source_r - harmonic, component, cutoff), source] += downward
    return result


class IndependentRegisteredEvaluator:
    def __init__(
        self,
        access: RegisteredAccess,
        *,
        n_sites: int,
        dps: int = INDEPENDENT_DPS,
    ):
        validate_registered_access(access)
        if n_sites not in REGISTERED_SIZES:
            raise SymmetryQCASpecError("independent size is outside the refinement ladder")
        if dps < INDEPENDENT_DPS:
            raise SymmetryQCASpecError("independent replay precision is below 110 digits")
        self.access = access
        self.n_sites = n_sites
        self.delta = Fraction(PHYSICAL_LENGTH, n_sites)
        self.dps = dps
        value = load_json(access.root / SPEC_DIR_REF / "scenarios.json")
        expected = DEVELOPMENT_SCENARIOS if access.stage == "development" else CONFIRMATION_SCENARIOS
        records = value[access.stage]
        if tuple(record["id"] for record in records) != expected:
            raise SymmetryQCASpecError("independent scenario order mismatch")
        self.scenarios = {record["id"]: record for record in records}

    def _scenario(self, scenario_id: str) -> dict[str, Any]:
        validate_registered_access(self.access)
        try:
            return self.scenarios[scenario_id]
        except KeyError as exc:
            raise SymmetryQCASpecError("scenario is outside the independent partition") from exc

    def input_basis_columns(self) -> mp.matrix:
        with mp.workdps(self.dps):
            result = mp.matrix(2 * self.n_sites, 18)
            normalization = mp.sqrt(self.n_sites)
            for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
                for component in (0, 1):
                    column = 2 * (r - INPUT_R_MIN) + component
                    for site in range(self.n_sites):
                        result[2 * site + component, column] = (
                            mp.exp(2j * mp.pi * r * site / self.n_sites) / normalization
                        )
            return result

    def _momentum_block(self, r: int, mass: Fraction) -> mp.matrix:
        mu = _mpf(self.delta * mass)
        normalization = mp.sqrt(1 - mu * mu)
        q = 2 * mp.pi * r / self.n_sites
        return mp.matrix(
            [
                [normalization * mp.exp(-1j * q), -1j * mu],
                [-1j * mu, normalization * mp.exp(1j * q)],
            ]
        )

    def _free_candidate_outputs(
        self,
        scenario: dict[str, Any],
        *,
        coefficients: mp.matrix | None = None,
        every_step: bool = False,
    ) -> dict[int, mp.matrix]:
        observations = _observation_steps(self.delta)
        blocks = {r: mp.eye(2) for r in range(INPUT_R_MIN, INPUT_R_MAX + 1)}
        outputs: dict[int, mp.matrix] = {}
        with mp.workdps(self.dps):
            for step in range(max(observations)):
                mass = _interval_value(scenario["mass"], step * self.delta)
                for r in blocks:
                    blocks[r] = self._momentum_block(r, mass) * blocks[r]
                layer = step + 1
                if every_step or layer in observations:
                    columns = 18 if coefficients is None else 1
                    result = mp.matrix(2 * self.n_sites, columns)
                    normalization = mp.sqrt(self.n_sites)
                    for r, block in blocks.items():
                        for site in range(self.n_sites):
                            phase = mp.exp(2j * mp.pi * r * site / self.n_sites) / normalization
                            if coefficients is None:
                                for source_component in (0, 1):
                                    column = 2 * (r - INPUT_R_MIN) + source_component
                                    for target_component in (0, 1):
                                        result[2 * site + target_component, column] = (
                                            phase * block[target_component, source_component]
                                        )
                            else:
                                source = mp.matrix(
                                    [
                                        coefficients[2 * (r - INPUT_R_MIN), 0],
                                        coefficients[2 * (r - INPUT_R_MIN) + 1, 0],
                                    ]
                                )
                                evolved = block * source
                                for target_component in (0, 1):
                                    result[2 * site + target_component, 0] += (
                                        phase * evolved[target_component]
                                    )
                    outputs[layer] = result
        return outputs

    def _sparse_candidate_outputs(
        self, scenario: dict[str, Any], *, initial: mp.matrix, every_step: bool
    ) -> dict[int, mp.matrix]:
        observations = _observation_steps(self.delta)
        current = _copy(initial)
        outputs: dict[int, mp.matrix] = {}
        routing = _routing_swap_operator(self.n_sites)
        with mp.workdps(self.dps):
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                current = _phase_operator(
                    self.n_sites, delta=self.delta, potential=potential
                ).apply(current)
                current = _edge_scatter_operator(
                    self.n_sites, self.delta * mass
                ).apply(current)
                current = routing.apply(current)
                layer = step + 1
                if every_step or layer in observations:
                    outputs[layer] = _copy(current)
        return outputs

    def _sparse_candidate_final(
        self,
        scenario: dict[str, Any],
        *,
        initial: mp.matrix,
        reflect_potential: bool = False,
    ) -> mp.matrix:
        observations = _observation_steps(self.delta)
        current = _copy(initial)
        routing = _routing_swap_operator(self.n_sites)
        with mp.workdps(self.dps):
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                current = _phase_operator(
                    self.n_sites,
                    delta=self.delta,
                    potential=potential,
                    reflect=reflect_potential,
                ).apply(current)
                current = _edge_scatter_operator(
                    self.n_sites, self.delta * mass
                ).apply(current)
                current = routing.apply(current)
        return current

    @staticmethod
    def _parity(value: mp.matrix, n_sites: int) -> mp.matrix:
        result = mp.matrix(value.rows, value.cols)
        for site in range(n_sites):
            reflected = (-site) % n_sites
            for column in range(value.cols):
                result[2 * site, column] = value[2 * reflected + 1, column]
                result[2 * site + 1, column] = value[2 * reflected, column]
        return result

    @staticmethod
    def _theta(value: mp.matrix, n_sites: int) -> mp.matrix:
        result = mp.matrix(value.rows, value.cols)
        for site in range(n_sites):
            for column in range(value.cols):
                result[2 * site, column] = mp.conj(value[2 * site + 1, column])
                result[2 * site + 1, column] = mp.conj(value[2 * site, column])
        return result

    def parity_role_pair(self, scenario_id: str) -> tuple[mp.matrix, mp.matrix]:
        scenario = self._scenario(scenario_id)
        basis = self.input_basis_columns()
        left = self._parity(
            self._sparse_candidate_final(
                scenario,
                initial=self._parity(basis, self.n_sites),
            ),
            self.n_sites,
        )
        right = self._sparse_candidate_final(
            scenario, initial=basis, reflect_potential=True
        )
        return left, right

    def time_reversal_role_pair(
        self, scenario_id: str
    ) -> tuple[mp.matrix, mp.matrix]:
        scenario = self._scenario(scenario_id)
        observations = _observation_steps(self.delta)
        basis = self.input_basis_columns()
        routing = _routing_swap_operator(self.n_sites)
        with mp.workdps(self.dps):
            left = self._theta(
                self._sparse_candidate_final(
                    scenario,
                    initial=self._theta(basis, self.n_sites),
                ),
                self.n_sites,
            )
            right = _copy(basis)
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                right = routing.adjoint().apply(right)
                right = _edge_scatter_operator(
                    self.n_sites, self.delta * mass
                ).adjoint().apply(right)
                right = _phase_operator(
                    self.n_sites, delta=self.delta, potential=potential
                ).adjoint().apply(right)
        return left, right

    def candidate_outputs(self, scenario_id: str) -> dict[int, mp.matrix]:
        scenario = self._scenario(scenario_id)
        if scenario["potential"]:
            return self._sparse_candidate_outputs(
                scenario, initial=self.input_basis_columns(), every_step=False
            )
        return self._free_candidate_outputs(scenario)

    def candidate_state_series(
        self, scenario_id: str, coefficients: mp.matrix
    ) -> dict[int, mp.matrix]:
        if not isinstance(coefficients, mp.matrix) or coefficients.rows != 18 or coefficients.cols != 1:
            raise SymmetryQCASpecError("independent witness coefficients must be 18 by 1")
        scenario = self._scenario(scenario_id)
        if scenario["potential"]:
            return self._sparse_candidate_outputs(
                scenario,
                initial=self.input_basis_columns() * coefficients,
                every_step=True,
            )
        return self._free_candidate_outputs(
            scenario, coefficients=coefficients, every_step=True
        )

    @property
    def target_dimension(self) -> int:
        return 2 * (2 * TARGET_R_CUTOFF + 1)

    def target_input_basis(self) -> mp.matrix:
        result = mp.matrix(self.target_dimension, 18)
        for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
            for component in (0, 1):
                result[
                    _target_row(r, component, TARGET_R_CUTOFF),
                    2 * (r - INPUT_R_MIN) + component,
                ] = 1
        return result

    def _target_action(
        self,
        value: mp.matrix,
        *,
        mass: Fraction,
        potential: tuple[int, Fraction, Fraction] | None,
    ) -> mp.matrix:
        result = mp.matrix(value.rows, value.cols)
        mass_value = _mpf(mass)
        if potential is None:
            harmonic, upward, downward = 1, mp.mpc(0), mp.mpc(0)
        else:
            harmonic, amplitude, phase_pi = potential
            upward = _mpf(amplitude) * mp.exp(1j * mp.pi * _mpf(phase_pi)) / 2
            downward = _mpf(amplitude) * mp.exp(-1j * mp.pi * _mpf(phase_pi)) / 2
        for r in range(-TARGET_R_CUTOFF, TARGET_R_CUTOFF + 1):
            momentum = 2 * mp.pi * r / PHYSICAL_LENGTH
            right = _target_row(r, 0, TARGET_R_CUTOFF)
            left = right + 1
            for column in range(value.cols):
                result[right, column] = momentum * value[right, column] + mass_value * value[left, column]
                result[left, column] = mass_value * value[right, column] - momentum * value[left, column]
                if r - harmonic >= -TARGET_R_CUTOFF:
                    source = _target_row(r - harmonic, 0, TARGET_R_CUTOFF)
                    result[right, column] += upward * value[source, column]
                    result[left, column] += upward * value[source + 1, column]
                if r + harmonic <= TARGET_R_CUTOFF:
                    source = _target_row(r + harmonic, 0, TARGET_R_CUTOFF)
                    result[right, column] += downward * value[source, column]
                    result[left, column] += downward * value[source + 1, column]
        return result

    def _target_taylor_step(
        self,
        value: mp.matrix,
        *,
        mass: Fraction,
        potential: tuple[int, Fraction, Fraction] | None,
    ) -> mp.matrix:
        result = _copy(value)
        term = _copy(value)
        tolerance = mp.power(10, -(self.dps - 20))
        multiplier = -1j * _mpf(self.delta)
        for order in range(1, 700):
            term = multiplier / order * self._target_action(
                term, mass=mass, potential=potential
            )
            result += term
            if _maximum_abs(term) <= tolerance:
                return result
        raise SymmetryQCASpecError("independent target Taylor action did not converge")

    def target_outputs(self, scenario_id: str) -> dict[int, mp.matrix]:
        scenario = self._scenario(scenario_id)
        observations = _observation_steps(self.delta)
        current = self.target_input_basis()
        outputs: dict[int, mp.matrix] = {}
        with mp.workdps(self.dps):
            for step in range(max(observations)):
                time = step * self.delta
                current = self._target_taylor_step(
                    current,
                    mass=_interval_value(scenario["mass"], time),
                    potential=_potential_parameters(scenario["potential"], time),
                )
                layer = step + 1
                if layer in observations:
                    outputs[layer] = _copy(current)
        return outputs

    def target_state_series(
        self, scenario_id: str, coefficients: mp.matrix
    ) -> dict[int, mp.matrix]:
        if not isinstance(coefficients, mp.matrix) or coefficients.rows != 18 or coefficients.cols != 1:
            raise SymmetryQCASpecError("independent target coefficients must be 18 by 1")
        scenario = self._scenario(scenario_id)
        observations = _observation_steps(self.delta)
        current = self.target_input_basis() * coefficients
        outputs: dict[int, mp.matrix] = {}
        with mp.workdps(self.dps):
            for step in range(max(observations)):
                time = step * self.delta
                current = self._target_taylor_step(
                    current,
                    mass=_interval_value(scenario["mass"], time),
                    potential=_potential_parameters(scenario["potential"], time),
                )
                outputs[step + 1] = _copy(current)
        return outputs

    def embed_target(self, value: mp.matrix) -> mp.matrix:
        if value.rows != self.target_dimension:
            raise SymmetryQCASpecError("independent target embedding dimension mismatch")
        with mp.workdps(self.dps):
            result = mp.matrix(2 * self.n_sites, value.cols)
            normalization = mp.sqrt(self.n_sites)
            for r in range(-TARGET_R_CUTOFF, TARGET_R_CUTOFF + 1):
                for component in (0, 1):
                    source = _target_row(r, component, TARGET_R_CUTOFF)
                    for site in range(self.n_sites):
                        phase = mp.exp(2j * mp.pi * r * site / self.n_sites) / normalization
                        for column in range(value.cols):
                            result[2 * site + component, column] += phase * value[source, column]
            return result


def spectral_norm_from_gram(value: mp.matrix, *, dps: int = INDEPENDENT_DPS):
    if dps < INDEPENDENT_DPS:
        raise SymmetryQCASpecError("independent norm precision is below 110 digits")
    with mp.workdps(dps):
        gram = value.H * value
        eigenvalues = mp.eigsy(gram, eigvals_only=True)
        return mp.sqrt(max(mp.re(eigenvalues[index]) for index in range(eigenvalues.rows)))
