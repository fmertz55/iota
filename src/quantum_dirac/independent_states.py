"""Independent mpmath reconstruction of the frozen registered states.

This module deliberately imports no primary candidate, target, certified, or
reducer implementation.  It restates the state formulas from the exact JSON
records so clean-checkpoint replay has an independent import graph.
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
    CONFIRMATION_STATES,
    DEVELOPMENT_STATES,
    INPUT_R_MAX,
    INPUT_R_MIN,
    PHYSICAL_LENGTH,
    SPEC_DIR_REF,
)
from .spec import QuantumDiracSpecError, load_json, parse_fraction, parse_phase


RegisteredAccess = RegisteredEvaluationPermit | RegisteredVerificationPermit


@dataclass(frozen=True)
class IndependentStateDefinition:
    state_id: str
    coefficients: mp.matrix
    incoherent_components: tuple[mp.matrix, ...]


def _normalize(value: mp.matrix) -> mp.matrix:
    norm = mp.sqrt(mp.fsum(abs(value[row, 0]) ** 2 for row in range(value.rows)))
    if norm == 0:
        raise QuantumDiracSpecError("independent state normalization is zero")
    return value / norm


def _energy_spinor(r: int, mass: Fraction, sign: int) -> tuple[Any, Any]:
    if sign not in (-1, 1) or mass <= 0:
        raise QuantumDiracSpecError("independent energy spinor request is invalid")
    momentum = 2 * mp.pi * r / PHYSICAL_LENGTH
    mass_value = mp.mpf(mass.numerator) / mass.denominator
    energy = mp.sqrt(momentum**2 + mass_value**2)
    upper = mp.sqrt((energy + momentum) / (2 * energy))
    lower = mp.sqrt((energy - momentum) / (2 * energy))
    return (upper, lower) if sign == 1 else (lower, -upper)


def _packet(
    *, r0: Fraction, width: Fraction, x0: Fraction, mass: Fraction, sign: int
) -> mp.matrix:
    result = mp.matrix(2 * (INPUT_R_MAX - INPUT_R_MIN + 1), 1)
    r0_value = mp.mpf(r0.numerator) / r0.denominator
    width_value = mp.mpf(width.numerator) / width.denominator
    x0_value = mp.mpf(x0.numerator) / x0.denominator
    for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
        envelope = mp.exp(-((r - r0_value) ** 2) / (2 * width_value**2))
        phase = mp.exp(-2j * mp.pi * r * x0_value / PHYSICAL_LENGTH)
        spinor = _energy_spinor(r, mass, sign)
        row = 2 * (r - INPUT_R_MIN)
        result[row, 0] = envelope * phase * spinor[0]
        result[row + 1, 0] = envelope * phase * spinor[1]
    return _normalize(result)


def _record(access: RegisteredAccess, state_id: str) -> dict[str, Any]:
    validate_registered_access(access)
    expected = DEVELOPMENT_STATES if access.stage == "development" else CONFIRMATION_STATES
    if state_id not in expected:
        raise QuantumDiracSpecError("state is outside the independent partition")
    states = load_json(access.root / SPEC_DIR_REF / "states.json")
    records = states[access.stage]
    if tuple(record["id"] for record in records) != expected:
        raise QuantumDiracSpecError("independent state order differs from the partition")
    return next(record for record in records if record["id"] == state_id)


def build_independent_state(
    access: RegisteredAccess,
    *,
    state_id: str,
    initial_mass: Fraction,
    dps: int,
) -> IndependentStateDefinition:
    record = _record(access, state_id)
    with mp.workdps(dps):
        state_type = record["type"]
        components: tuple[mp.matrix, ...] = ()
        if state_type in ("positive", "negative"):
            coefficients = _packet(
                r0=parse_fraction(record["r0"]),
                width=parse_fraction(record["width"]),
                x0=parse_fraction(record["x0"]),
                mass=initial_mass,
                sign=1 if state_type == "positive" else -1,
            )
        elif state_type == "positive_interference":
            packets = tuple(
                _packet(
                    r0=parse_fraction(packet[0]),
                    width=parse_fraction(packet[1]),
                    x0=parse_fraction(packet[2]),
                    mass=initial_mass,
                    sign=1,
                )
                for packet in record["packets"]
            )
            coefficient, includes_pi = parse_phase(record["relative_phase"])
            if not includes_pi:
                raise QuantumDiracSpecError("independent interference phase is invalid")
            phase = mp.exp(
                1j * mp.pi * coefficient.numerator / coefficient.denominator
            )
            coefficients = _normalize(packets[0] + phase * packets[1])
            components = packets
        elif state_type == "energy_mixture":
            positive = _packet(
                r0=parse_fraction(record["r0"]),
                width=parse_fraction(record["width"]),
                x0=parse_fraction(record["x0"]),
                mass=initial_mass,
                sign=1,
            )
            negative = _packet(
                r0=parse_fraction(record["r0"]),
                width=parse_fraction(record["width"]),
                x0=parse_fraction(record["x0"]),
                mass=initial_mass,
                sign=-1,
            )
            coefficient, includes_pi = parse_phase(record["relative_phase"])
            if not includes_pi:
                raise QuantumDiracSpecError("independent energy-mixture phase is invalid")
            phase = mp.exp(
                1j * mp.pi * coefficient.numerator / coefficient.denominator
            )
            coefficients = _normalize(positive + phase * negative)
            components = (positive, negative)
        else:
            raise QuantumDiracSpecError("unknown independent registered state type")
        return IndependentStateDefinition(state_id, coefficients, components)
