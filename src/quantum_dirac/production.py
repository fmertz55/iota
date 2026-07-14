"""Registered production engines, reachable only through a Git provenance permit."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

from mpmath import mp

from .authorization import RegisteredEvaluationPermit, validate_registered_permit
from .candidate import (
    mass_mix_layer,
    scalar_phase_layer,
    transport_via_swaps,
)
from .protocol import (
    CONFIRMATION_SCENARIOS,
    DEVELOPMENT_SCENARIOS,
    INPUT_R_MAX,
    INPUT_R_MIN,
    PHYSICAL_LENGTH,
    REGISTERED_OBSERVATION_TIMES,
    REGISTERED_SIZES,
    SPEC_DIR_REF,
    TARGET_R_CUTOFF,
    WORK_DPS,
)
from .spec import QuantumDiracSpecError, load_json, parse_fraction, parse_phase
from .target import build_spectral_hamiltonian, hermitian_exponential, mode_index


def _mpf(value: Fraction | int | str):
    if isinstance(value, Fraction):
        return mp.mpf(value.numerator) / value.denominator
    return mp.mpf(value)


def _copy_matrix(value: mp.matrix) -> mp.matrix:
    result = mp.matrix(value.rows, value.cols)
    for row in range(value.rows):
        for column in range(value.cols):
            result[row, column] = value[row, column]
    return result


class _RegisteredScenarioSet:
    def __init__(self, permit: RegisteredEvaluationPermit):
        validate_registered_permit(permit)
        self.permit = permit
        spec = load_json(permit.root / SPEC_DIR_REF / "scenarios.json")
        records = spec[permit.stage]
        expected = (
            DEVELOPMENT_SCENARIOS
            if permit.stage == "development"
            else CONFIRMATION_SCENARIOS
        )
        if tuple(record["id"] for record in records) != expected:
            raise QuantumDiracSpecError("stage scenario manifest order mismatch")
        allowed_records = list(records)
        if permit.stage == "confirmation":
            development = spec["development"]
            if tuple(record["id"] for record in development) != DEVELOPMENT_SCENARIOS:
                raise QuantumDiracSpecError("development scenario order mismatch")
            allowed_records.append(development[0])
        self.records = {record["id"]: record for record in allowed_records}

    def get(self, scenario_id: str) -> dict[str, Any]:
        validate_registered_permit(self.permit)
        try:
            return self.records[scenario_id]
        except KeyError as exc:
            raise QuantumDiracSpecError(
                f"scenario is outside the opened {self.permit.stage} partition"
            ) from exc


def _interval_value(records: list[list[str]], time: Fraction) -> Fraction:
    for start, end, value in records:
        if parse_fraction(start) <= time < parse_fraction(end):
            return parse_fraction(value)
    raise QuantumDiracSpecError(f"schedule does not cover time {time}")


def _potential_parameters(
    records: list[list[str]], time: Fraction
) -> tuple[Fraction, Fraction] | None:
    for start, end, amplitude, phase in records:
        if parse_fraction(start) <= time < parse_fraction(end):
            coefficient, includes_pi = parse_phase(phase)
            if phase != "0" and not includes_pi:
                raise QuantumDiracSpecError("potential phase is not a pi multiple")
            return parse_fraction(amplitude), coefficient
    return None


def _observation_steps(delta: Fraction) -> tuple[int, ...]:
    steps: list[int] = []
    for value in REGISTERED_OBSERVATION_TIMES:
        quotient = parse_fraction(value) / delta
        if quotient.denominator != 1:
            raise QuantumDiracSpecError("observation does not align with macrostep grid")
        steps.append(quotient.numerator)
    return tuple(steps)


class RegisteredCandidateEngine:
    def __init__(
        self,
        permit: RegisteredEvaluationPermit,
        *,
        n_sites: int,
        dps: int = WORK_DPS,
    ):
        validate_registered_permit(permit)
        if n_sites not in REGISTERED_SIZES:
            raise QuantumDiracSpecError("registered candidate size is outside the ladder")
        if dps < 80:
            raise QuantumDiracSpecError("registered candidate requires at least 80 digits")
        self.permit = permit
        self.n_sites = n_sites
        self.delta = Fraction(PHYSICAL_LENGTH, n_sites)
        self.dps = dps
        self.scenarios = _RegisteredScenarioSet(permit)

    def input_basis_columns(self) -> mp.matrix:
        validate_registered_permit(self.permit)
        with mp.workdps(self.dps):
            columns = 2 * (INPUT_R_MAX - INPUT_R_MIN + 1)
            result = mp.matrix(2 * self.n_sites, columns)
            normalization = mp.sqrt(self.n_sites)
            column = 0
            for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
                for component in (0, 1):
                    for site in range(self.n_sites):
                        result[2 * site + component, column] = (
                            mp.exp(2j * mp.pi * r * site / self.n_sites)
                            / normalization
                        )
                    column += 1
            return result

    def _potential_vector(
        self,
        parameters: tuple[Fraction, Fraction] | None,
    ) -> list | None:
        if parameters is None:
            return None
        amplitude, phase_pi = parameters
        with mp.workdps(self.dps):
            return [
                _mpf(amplitude)
                * mp.cos(
                    2 * mp.pi * site / self.n_sites
                    + mp.pi * _mpf(phase_pi)
                )
                for site in range(self.n_sites)
            ]

    def evolve_scenario_columns(self, scenario_id: str) -> dict[int, mp.matrix]:
        validate_registered_permit(self.permit)
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        current = self.input_basis_columns()
        outputs: dict[int, mp.matrix] = {}
        with mp.workdps(self.dps):
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                if potential is not None:
                    current = scalar_phase_layer(
                        current,
                        n_sites=self.n_sites,
                        delta=self.delta,
                        potentials=self._potential_vector(potential),
                        dps=self.dps,
                    )
                current = mass_mix_layer(
                    current,
                    n_sites=self.n_sites,
                    angle=_mpf(self.delta) * _mpf(mass),
                    dps=self.dps,
                )
                current = transport_via_swaps(current, n_sites=self.n_sites)
                layer = step + 1
                if layer in observations:
                    outputs[layer] = _copy_matrix(current)
        return outputs


class RegisteredTargetSolver:
    def __init__(
        self,
        permit: RegisteredEvaluationPermit,
        *,
        n_sites: int,
        dps: int = WORK_DPS,
    ):
        validate_registered_permit(permit)
        if n_sites not in REGISTERED_SIZES:
            raise QuantumDiracSpecError("registered target size is outside the ladder")
        if dps < 80:
            raise QuantumDiracSpecError("registered target requires at least 80 digits")
        self.permit = permit
        self.n_sites = n_sites
        self.delta = Fraction(PHYSICAL_LENGTH, n_sites)
        self.dps = dps
        self.scenarios = _RegisteredScenarioSet(permit)

    @property
    def dimension(self) -> int:
        return 2 * (2 * TARGET_R_CUTOFF + 1)

    def input_basis_columns(self) -> mp.matrix:
        validate_registered_permit(self.permit)
        result = mp.matrix(
            self.dimension,
            2 * (INPUT_R_MAX - INPUT_R_MIN + 1),
        )
        column = 0
        for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
            for component in (0, 1):
                result[mode_index(r, component, TARGET_R_CUTOFF), column] = 1
                column += 1
        return result

    def evolve_scenario_columns(self, scenario_id: str) -> dict[int, mp.matrix]:
        validate_registered_permit(self.permit)
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        current = self.input_basis_columns()
        outputs: dict[int, mp.matrix] = {}
        propagators: dict[tuple[Fraction, Fraction, Fraction], mp.matrix] = {}
        with mp.workdps(self.dps):
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                amplitude, phase_pi = (
                    (Fraction(0), Fraction(0))
                    if potential is None
                    else potential
                )
                key = mass, amplitude, phase_pi
                propagator = propagators.get(key)
                if propagator is None:
                    hamiltonian = build_spectral_hamiltonian(
                        cutoff=TARGET_R_CUTOFF,
                        mass=mass,
                        length=PHYSICAL_LENGTH,
                        potential_amplitude=amplitude,
                        potential_phase_pi=phase_pi,
                        dps=self.dps,
                    )
                    propagator = hermitian_exponential(
                        hamiltonian,
                        duration=self.delta,
                        dps=self.dps,
                    )
                    propagators[key] = propagator
                current = propagator * current
                layer = step + 1
                if layer in observations:
                    outputs[layer] = _copy_matrix(current)
        return outputs

    def embed_in_candidate_space(self, columns: mp.matrix) -> mp.matrix:
        validate_registered_permit(self.permit)
        if columns.rows != self.dimension:
            raise QuantumDiracSpecError("target columns have the wrong reference dimension")
        with mp.workdps(self.dps):
            result = mp.matrix(2 * self.n_sites, columns.cols)
            normalization = mp.sqrt(self.n_sites)
            for r in range(-TARGET_R_CUTOFF, TARGET_R_CUTOFF + 1):
                for component in (0, 1):
                    source_row = mode_index(r, component, TARGET_R_CUTOFF)
                    for site in range(self.n_sites):
                        phase = (
                            mp.exp(2j * mp.pi * r * site / self.n_sites)
                            / normalization
                        )
                        target_row = 2 * site + component
                        for column in range(columns.cols):
                            result[target_row, column] += (
                                phase * columns[source_row, column]
                            )
            return result
