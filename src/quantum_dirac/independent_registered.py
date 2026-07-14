"""Algorithmically separate registered replay engines.

Free and quench candidate schedules are reconstructed from independent 2x2
momentum blocks.  Potential schedules use explicit sparse circuit operators.
The target generator is rebuilt here and its sparse action is exponentiated by
an independent Taylor action, without importing production constructors.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable

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
from .spec import QuantumDiracSpecError, load_json, parse_fraction, parse_phase


RegisteredAccess = RegisteredEvaluationPermit | RegisteredVerificationPermit


def _interval_value(records: list[list[str]], time: Fraction) -> Fraction:
    for start, end, value in records:
        if parse_fraction(start) <= time < parse_fraction(end):
            return parse_fraction(value)
    raise QuantumDiracSpecError("independent schedule does not cover the requested time")


def _potential_parameters(
    records: list[list[str]], time: Fraction
) -> tuple[Fraction, Fraction] | None:
    for start, end, amplitude, phase in records:
        if parse_fraction(start) <= time < parse_fraction(end):
            coefficient, includes_pi = parse_phase(phase)
            if phase != "0" and not includes_pi:
                raise QuantumDiracSpecError("independent potential phase is invalid")
            return parse_fraction(amplitude), coefficient
    return None


def _observation_steps(delta: Fraction) -> tuple[int, ...]:
    result = []
    for value in REGISTERED_OBSERVATION_TIMES:
        quotient = parse_fraction(value) / delta
        if quotient.denominator != 1:
            raise QuantumDiracSpecError("independent observation grid is misaligned")
        result.append(quotient.numerator)
    return tuple(result)


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


def _max_abs(value: mp.matrix):
    return max(
        abs(value[row, column])
        for row in range(value.rows)
        for column in range(value.cols)
    )


@dataclass(frozen=True)
class _SparseOperator:
    rows: int
    entries: tuple[tuple[int, int, Any], ...]

    def apply(self, value: mp.matrix) -> mp.matrix:
        if value.rows != self.rows:
            raise QuantumDiracSpecError("sparse circuit operand has the wrong dimension")
        result = mp.matrix(self.rows, value.cols)
        for target, source, coefficient in self.entries:
            for column in range(value.cols):
                result[target, column] += coefficient * value[source, column]
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
            raise QuantumDiracSpecError("independent size is outside the registered ladder")
        if dps < INDEPENDENT_DPS:
            raise QuantumDiracSpecError("independent replay precision is below the seal")
        self.access = access
        self.n_sites = n_sites
        self.delta = Fraction(PHYSICAL_LENGTH, n_sites)
        self.dps = dps
        spec = load_json(access.root / SPEC_DIR_REF / "scenarios.json")
        expected = (
            DEVELOPMENT_SCENARIOS
            if access.stage == "development"
            else CONFIRMATION_SCENARIOS
        )
        records = spec[access.stage]
        if tuple(record["id"] for record in records) != expected:
            raise QuantumDiracSpecError("independent scenario partition order mismatch")
        allowed_records = list(records)
        if access.stage == "confirmation":
            development = spec["development"]
            if tuple(record["id"] for record in development) != DEVELOPMENT_SCENARIOS:
                raise QuantumDiracSpecError("independent development scenario order mismatch")
            allowed_records.append(development[0])
        self.scenarios = {record["id"]: record for record in allowed_records}

    def _scenario(self, scenario_id: str) -> dict[str, Any]:
        validate_registered_access(self.access)
        try:
            return self.scenarios[scenario_id]
        except KeyError as exc:
            raise QuantumDiracSpecError("scenario is outside the independent partition") from exc

    def input_basis_columns(self) -> mp.matrix:
        with mp.workdps(self.dps):
            result = mp.matrix(2 * self.n_sites, 18)
            normalization = mp.sqrt(self.n_sites)
            for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
                for component in (0, 1):
                    column = 2 * (r - INPUT_R_MIN) + component
                    for site in range(self.n_sites):
                        result[2 * site + component, column] = (
                            mp.exp(2j * mp.pi * r * site / self.n_sites)
                            / normalization
                        )
            return result

    def _mass_block(self, mass: Fraction) -> mp.matrix:
        angle = _mpf(self.delta * mass)
        cosine = mp.cos(angle)
        sine = -1j * mp.sin(angle)
        return mp.matrix([[cosine, sine], [sine, cosine]])

    def _transport_block(self, r: int) -> mp.matrix:
        angle = 2 * mp.pi * r / self.n_sites
        return mp.matrix(
            [[mp.exp(-1j * angle), 0], [0, mp.exp(1j * angle)]]
        )

    def _momentum_candidate_outputs(
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
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                for r in blocks:
                    blocks[r] = self._transport_block(r) * self._mass_block(mass) * blocks[r]
                layer = step + 1
                if every_step or layer in observations:
                    if coefficients is None:
                        result = mp.matrix(2 * self.n_sites, 18)
                    else:
                        result = mp.matrix(2 * self.n_sites, 1)
                    normalization = mp.sqrt(self.n_sites)
                    for r, block in blocks.items():
                        phase_values = [
                            mp.exp(2j * mp.pi * r * site / self.n_sites)
                            / normalization
                            for site in range(self.n_sites)
                        ]
                        if coefficients is None:
                            for source_component in (0, 1):
                                column = 2 * (r - INPUT_R_MIN) + source_component
                                for target_component in (0, 1):
                                    amplitude = block[target_component, source_component]
                                    for site, phase in enumerate(phase_values):
                                        result[2 * site + target_component, column] = phase * amplitude
                        else:
                            source = mp.matrix(
                                [
                                    coefficients[2 * (r - INPUT_R_MIN), 0],
                                    coefficients[2 * (r - INPUT_R_MIN) + 1, 0],
                                ]
                            )
                            evolved = block * source
                            for target_component in (0, 1):
                                for site, phase in enumerate(phase_values):
                                    result[2 * site + target_component, 0] += (
                                        phase * evolved[target_component]
                                    )
                    outputs[layer] = result
        return outputs

    def _phase_operator(
        self, parameters: tuple[Fraction, Fraction] | None
    ) -> _SparseOperator:
        entries: list[tuple[int, int, Any]] = []
        for site in range(self.n_sites):
            if parameters is None:
                phase = mp.mpc(1)
            else:
                amplitude, phase_pi = parameters
                potential = _mpf(amplitude) * mp.cos(
                    2 * mp.pi * site / self.n_sites + mp.pi * _mpf(phase_pi)
                )
                phase = mp.exp(-1j * _mpf(self.delta) * potential)
            entries.append((2 * site, 2 * site, phase))
            entries.append((2 * site + 1, 2 * site + 1, phase))
        return _SparseOperator(2 * self.n_sites, tuple(entries))

    def _coin_operator(self, mass: Fraction) -> _SparseOperator:
        block = self._mass_block(mass)
        entries: list[tuple[int, int, Any]] = []
        for site in range(self.n_sites):
            base = 2 * site
            for target in (0, 1):
                for source in (0, 1):
                    entries.append((base + target, base + source, block[target, source]))
        return _SparseOperator(2 * self.n_sites, tuple(entries))

    def _on_site_swap_operator(self) -> _SparseOperator:
        return _SparseOperator(
            2 * self.n_sites,
            tuple(
                entry
                for site in range(self.n_sites)
                for entry in (
                    (2 * site, 2 * site + 1, 1),
                    (2 * site + 1, 2 * site, 1),
                )
            ),
        )

    def _edge_swap_operator(self) -> _SparseOperator:
        entries: list[tuple[int, int, Any]] = []
        for site in range(self.n_sites):
            left = 2 * site + 1
            neighbor_right = 2 * ((site + 1) % self.n_sites)
            entries.append((left, neighbor_right, 1))
            entries.append((neighbor_right, left, 1))
        return _SparseOperator(2 * self.n_sites, tuple(entries))

    def _sparse_candidate_outputs(
        self,
        scenario: dict[str, Any],
        *,
        initial: mp.matrix,
        every_step: bool,
    ) -> dict[int, mp.matrix]:
        observations = _observation_steps(self.delta)
        current = _copy(initial)
        outputs: dict[int, mp.matrix] = {}
        on_site = self._on_site_swap_operator()
        edge = self._edge_swap_operator()
        with mp.workdps(self.dps):
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                current = self._phase_operator(potential).apply(current)
                current = self._coin_operator(mass).apply(current)
                current = on_site.apply(current)
                current = edge.apply(current)
                layer = step + 1
                if every_step or layer in observations:
                    outputs[layer] = _copy(current)
        return outputs

    def candidate_outputs(self, scenario_id: str) -> dict[int, mp.matrix]:
        scenario = self._scenario(scenario_id)
        if scenario["potential"]:
            return self._sparse_candidate_outputs(
                scenario,
                initial=self.input_basis_columns(),
                every_step=False,
            )
        return self._momentum_candidate_outputs(scenario)

    def candidate_state_series(
        self, scenario_id: str, coefficients: mp.matrix
    ) -> dict[int, mp.matrix]:
        scenario = self._scenario(scenario_id)
        if scenario["potential"]:
            return self._sparse_candidate_outputs(
                scenario,
                initial=self.input_basis_columns() * coefficients,
                every_step=True,
            )
        return self._momentum_candidate_outputs(
            scenario,
            coefficients=coefficients,
            every_step=True,
        )

    @property
    def target_dimension(self) -> int:
        return 2 * (2 * TARGET_R_CUTOFF + 1)

    @staticmethod
    def _target_row(r: int, component: int) -> int:
        return 2 * (r + TARGET_R_CUTOFF) + component

    def target_input_basis(self) -> mp.matrix:
        result = mp.matrix(self.target_dimension, 18)
        for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
            for component in (0, 1):
                result[self._target_row(r, component), 2 * (r - INPUT_R_MIN) + component] = 1
        return result

    def _dirac_block(self, r: int, mass: Fraction, duration: Fraction) -> mp.matrix:
        momentum = 2 * mp.pi * r / PHYSICAL_LENGTH
        mass_value = _mpf(mass)
        omega = mp.sqrt(momentum**2 + mass_value**2)
        hamiltonian = mp.matrix(
            [[momentum, mass_value], [mass_value, -momentum]]
        )
        if omega == 0:
            return mp.eye(2)
        return (
            mp.cos(omega * _mpf(duration)) * mp.eye(2)
            - 1j
            * mp.sin(omega * _mpf(duration))
            * hamiltonian
            / omega
        )

    def _target_h_apply(
        self,
        value: mp.matrix,
        *,
        mass: Fraction,
        potential: tuple[Fraction, Fraction] | None,
    ) -> mp.matrix:
        result = mp.matrix(value.rows, value.cols)
        mass_value = _mpf(mass)
        if potential is None:
            upward = downward = mp.mpc(0)
        else:
            amplitude, phase_pi = potential
            upward = _mpf(amplitude) * mp.exp(1j * mp.pi * _mpf(phase_pi)) / 2
            downward = _mpf(amplitude) * mp.exp(-1j * mp.pi * _mpf(phase_pi)) / 2
        for r in range(-TARGET_R_CUTOFF, TARGET_R_CUTOFF + 1):
            momentum = 2 * mp.pi * r / PHYSICAL_LENGTH
            right = self._target_row(r, 0)
            left = right + 1
            for column in range(value.cols):
                result[right, column] = (
                    momentum * value[right, column]
                    + mass_value * value[left, column]
                )
                result[left, column] = (
                    mass_value * value[right, column]
                    - momentum * value[left, column]
                )
                if r > -TARGET_R_CUTOFF:
                    source = self._target_row(r - 1, 0)
                    result[right, column] += upward * value[source, column]
                    result[left, column] += upward * value[source + 1, column]
                if r < TARGET_R_CUTOFF:
                    source = self._target_row(r + 1, 0)
                    result[right, column] += downward * value[source, column]
                    result[left, column] += downward * value[source + 1, column]
        return result

    def _target_taylor_step(
        self,
        value: mp.matrix,
        *,
        mass: Fraction,
        potential: tuple[Fraction, Fraction] | None,
    ) -> mp.matrix:
        result = _copy(value)
        term = _copy(value)
        tolerance = mp.power(10, -(self.dps - 20))
        multiplier = -1j * _mpf(self.delta)
        for order in range(1, 600):
            term = (
                multiplier
                / order
                * self._target_h_apply(term, mass=mass, potential=potential)
            )
            result += term
            if _max_abs(term) <= tolerance:
                return result
        raise QuantumDiracSpecError("independent sparse target Taylor action did not converge")

    def _target_outputs(
        self,
        scenario: dict[str, Any],
        *,
        initial: mp.matrix,
        every_step: bool,
    ) -> dict[int, mp.matrix]:
        observations = _observation_steps(self.delta)
        current = _copy(initial)
        outputs: dict[int, mp.matrix] = {}
        potential_active = bool(scenario["potential"])
        with mp.workdps(self.dps):
            if not potential_active:
                blocks = {
                    r: mp.eye(2) for r in range(-TARGET_R_CUTOFF, TARGET_R_CUTOFF + 1)
                }
                for step in range(max(observations)):
                    time = step * self.delta
                    mass = _interval_value(scenario["mass"], time)
                    for r in blocks:
                        blocks[r] = self._dirac_block(r, mass, self.delta) * blocks[r]
                    layer = step + 1
                    if every_step or layer in observations:
                        operator = mp.matrix(self.target_dimension, self.target_dimension)
                        for r, block in blocks.items():
                            row = self._target_row(r, 0)
                            for target in (0, 1):
                                for source in (0, 1):
                                    operator[row + target, row + source] = block[target, source]
                        outputs[layer] = operator * initial
                return outputs
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                current = self._target_taylor_step(
                    current,
                    mass=mass,
                    potential=potential,
                )
                layer = step + 1
                if every_step or layer in observations:
                    outputs[layer] = _copy(current)
        return outputs

    def target_outputs(self, scenario_id: str) -> dict[int, mp.matrix]:
        return self._target_outputs(
            self._scenario(scenario_id),
            initial=self.target_input_basis(),
            every_step=False,
        )

    def target_state_series(
        self, scenario_id: str, coefficients: mp.matrix
    ) -> dict[int, mp.matrix]:
        return self._target_outputs(
            self._scenario(scenario_id),
            initial=self.target_input_basis() * coefficients,
            every_step=True,
        )

    def embed_target(self, value: mp.matrix) -> mp.matrix:
        if value.rows != self.target_dimension:
            raise QuantumDiracSpecError("independent target embedding dimension mismatch")
        with mp.workdps(self.dps):
            result = mp.matrix(2 * self.n_sites, value.cols)
            normalization = mp.sqrt(self.n_sites)
            for r in range(-TARGET_R_CUTOFF, TARGET_R_CUTOFF + 1):
                for component in (0, 1):
                    source = self._target_row(r, component)
                    for site in range(self.n_sites):
                        phase = (
                            mp.exp(2j * mp.pi * r * site / self.n_sites)
                            / normalization
                        )
                        for column in range(value.cols):
                            result[2 * site + component, column] += phase * value[source, column]
            return result
