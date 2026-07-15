"""Separate mpmath reconstruction of direct-QCA state witnesses."""

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
    INDEPENDENT_DPS,
    INPUT_R_MAX,
    INPUT_R_MIN,
    PHYSICAL_LENGTH,
    SPEC_DIR_REF,
)
from .spec import SymmetryQCASpecError, load_json, parse_fraction


RegisteredAccess = RegisteredEvaluationPermit | RegisteredVerificationPermit


@dataclass(frozen=True)
class IndependentStateDefinition:
    state_id: str
    coefficients: mp.matrix


def _mpf(value: Fraction | int | str):
    if isinstance(value, Fraction):
        return mp.mpf(value.numerator) / value.denominator
    return mp.mpf(value)


def _phase(value: str):
    grammar = {
        "2pi/7": Fraction(2, 7),
        "2pi/5": Fraction(2, 5),
        "-pi/6": Fraction(-1, 6),
        "3pi/7": Fraction(3, 7),
    }
    try:
        return mp.exp(1j * mp.pi * _mpf(grammar[value]))
    except KeyError as exc:
        raise SymmetryQCASpecError("independent state phase is invalid") from exc


def _normalize(value: mp.matrix) -> mp.matrix:
    norm = mp.sqrt(sum(abs(value[row, 0]) ** 2 for row in range(value.rows)))
    if norm == 0:
        raise SymmetryQCASpecError("independent state normalization is zero")
    return value / norm


def _spinor(r: int, mass: Fraction, sign: int) -> tuple[Any, Any]:
    if sign not in (-1, 1) or mass == 0 and r == 0:
        raise SymmetryQCASpecError("independent energy spinor is degenerate")
    momentum = 2 * mp.pi * r / PHYSICAL_LENGTH
    mass_value = _mpf(mass)
    energy = mp.sqrt(momentum * momentum + mass_value * mass_value)
    if sign == 1:
        first, second = (
            (energy + momentum, mass_value)
            if r >= 0
            else (mass_value, energy - momentum)
        )
    else:
        first, second = (
            (-mass_value, energy + momentum)
            if r >= 0
            else (energy - momentum, -mass_value)
        )
    if (sign == 1 and r < 0 and mass < 0) or (sign == -1 and r >= 0 and mass > 0):
        first, second = -first, -second
    norm = mp.sqrt(first * first + second * second)
    return first / norm, second / norm


def _packet(
    *, r0: Fraction, width: Fraction, x0: Fraction, mass: Fraction, sign: int
) -> mp.matrix:
    result = mp.matrix(18, 1)
    for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
        displacement = _mpf(Fraction(r) - r0)
        envelope = mp.exp(-(displacement**2) / (2 * _mpf(width) ** 2))
        phase = mp.exp(-2j * mp.pi * r * _mpf(x0) / PHYSICAL_LENGTH)
        spinor = _spinor(r, mass, sign)
        row = 2 * (r - INPUT_R_MIN)
        result[row, 0] = envelope * phase * spinor[0]
        result[row + 1, 0] = envelope * phase * spinor[1]
    return _normalize(result)


def _record(access: RegisteredAccess, state_id: str) -> dict[str, Any]:
    validate_registered_access(access)
    expected = DEVELOPMENT_STATES if access.stage == "development" else CONFIRMATION_STATES
    if state_id not in expected:
        raise SymmetryQCASpecError("state is outside the independent partition")
    records = load_json(access.root / SPEC_DIR_REF / "states.json")[access.stage]
    if tuple(item["id"] for item in records) != expected:
        raise SymmetryQCASpecError("independent state order mismatch")
    return next(item for item in records if item["id"] == state_id)


def build_independent_state(
    access: RegisteredAccess,
    *,
    state_id: str,
    initial_mass: Fraction,
    dps: int = INDEPENDENT_DPS,
) -> IndependentStateDefinition:
    if dps < INDEPENDENT_DPS:
        raise SymmetryQCASpecError("independent state precision is below 110 digits")
    record = _record(access, state_id)
    with mp.workdps(dps):
        state_type = record["type"]
        if state_type in ("positive", "negative"):
            coefficients = _packet(
                r0=parse_fraction(record["r0"]),
                width=parse_fraction(record["width"]),
                x0=parse_fraction(record["x0"]),
                mass=initial_mass,
                sign=1 if state_type == "positive" else -1,
            )
        elif state_type == "positive_interference":
            packets = [
                _packet(
                    r0=parse_fraction(packet[0]),
                    width=parse_fraction(packet[1]),
                    x0=parse_fraction(packet[2]),
                    mass=initial_mass,
                    sign=1,
                )
                for packet in record["packets"]
            ]
            coefficients = _normalize(
                packets[0] + _phase(record["relative_phase"]) * packets[1]
            )
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
            coefficients = _normalize(
                positive + _phase(record["relative_phase"]) * negative
            )
        else:
            raise SymmetryQCASpecError("unknown independent state type")
        return IndependentStateDefinition(state_id, coefficients)
