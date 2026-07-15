"""Permit-guarded certified reconstruction of prospective state witnesses."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from flint import acb, acb_mat, arb

from .authorization import (
    RegisteredEvaluationPermit,
    RegisteredVerificationPermit,
    validate_registered_access,
)
from .production import arb_exact, ball_precision
from .protocol import (
    CONFIRMATION_STATES,
    DEVELOPMENT_STATES,
    INPUT_R_MAX,
    INPUT_R_MIN,
    PHYSICAL_LENGTH,
    PRECISION_BITS,
    SPEC_DIR_REF,
)
from .spec import SymmetryQCASpecError, load_json, parse_fraction


RegisteredAccess = RegisteredEvaluationPermit | RegisteredVerificationPermit


@dataclass(frozen=True)
class CertifiedStateDefinition:
    state_id: str
    coefficients: acb_mat
    incoherent_components: tuple[acb_mat, ...]


def _phase_fraction(value: str) -> Fraction:
    grammar = {
        "2pi/7": Fraction(2, 7),
        "2pi/5": Fraction(2, 5),
        "-pi/6": Fraction(-1, 6),
        "3pi/7": Fraction(3, 7),
    }
    try:
        return grammar[value]
    except KeyError as exc:
        raise SymmetryQCASpecError("state phase is outside the fixed grammar") from exc


def _probability(value: acb) -> arb:
    return value.real * value.real + value.imag * value.imag


def _normalize(value: acb_mat) -> acb_mat:
    norm_squared = sum(
        (_probability(value[row, 0]) for row in range(value.nrows())), arb(0)
    )
    if norm_squared.contains(0):
        raise SymmetryQCASpecError("state normalization contains zero")
    norm = norm_squared.sqrt()
    result = acb_mat(value.nrows(), 1)
    for row in range(value.nrows()):
        result[row, 0] = value[row, 0] / norm
    return result


def _energy_spinor(r: int, mass: Fraction, sign: int) -> tuple[arb, arb]:
    if sign not in (-1, 1) or mass == 0 and r == 0:
        raise SymmetryQCASpecError("energy spinor is degenerate")
    momentum = 2 * arb.pi() * arb(r) / arb(PHYSICAL_LENGTH)
    mass_ball = arb_exact(mass)
    energy = (momentum * momentum + mass_ball * mass_ball).sqrt()
    if sign == 1:
        if r >= 0:
            first, second = energy + momentum, mass_ball
        else:
            first, second = mass_ball, energy - momentum
    else:
        if r >= 0:
            first, second = -mass_ball, energy + momentum
        else:
            first, second = energy - momentum, -mass_ball
    # Fix the first nonzero component real and positive using exact r/m signs.
    first_negative = (
        (sign == 1 and r < 0 and mass < 0)
        or (sign == -1 and r >= 0 and mass > 0)
    )
    if first_negative:
        first, second = -first, -second
    norm = (first * first + second * second).sqrt()
    return first / norm, second / norm


def _packet(
    *, r0: Fraction, width: Fraction, x0: Fraction, mass: Fraction, sign: int
) -> acb_mat:
    result = acb_mat(18, 1)
    for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
        displacement = arb_exact(Fraction(r) - r0)
        envelope = (
            -(displacement * displacement)
            / (2 * arb_exact(width) * arb_exact(width))
        ).exp()
        phase = acb(
            0,
            -2 * arb.pi() * arb_exact(Fraction(r) * x0) / arb(PHYSICAL_LENGTH),
        ).exp()
        spinor = _energy_spinor(r, mass, sign)
        row = 2 * (r - INPUT_R_MIN)
        result[row, 0] = envelope * phase * spinor[0]
        result[row + 1, 0] = envelope * phase * spinor[1]
    return _normalize(result)


def _record(access: RegisteredAccess, state_id: str) -> dict[str, Any]:
    validate_registered_access(access)
    expected = DEVELOPMENT_STATES if access.stage == "development" else CONFIRMATION_STATES
    if state_id not in expected:
        raise SymmetryQCASpecError("state is outside the opened partition")
    value = load_json(access.root / SPEC_DIR_REF / "states.json")
    records = value[access.stage]
    if tuple(item["id"] for item in records) != expected:
        raise SymmetryQCASpecError("registered state order mismatch")
    return next(item for item in records if item["id"] == state_id)


def build_certified_state(
    access: RegisteredAccess,
    *,
    state_id: str,
    initial_mass: Fraction,
    bits: int = PRECISION_BITS,
) -> CertifiedStateDefinition:
    record = _record(access, state_id)
    with ball_precision(bits):
        state_type = record["type"]
        components: tuple[acb_mat, ...] = ()
        if state_type in ("positive", "negative"):
            coefficients = _packet(
                r0=parse_fraction(record["r0"]),
                width=parse_fraction(record["width"]),
                x0=parse_fraction(record["x0"]),
                mass=initial_mass,
                sign=1 if state_type == "positive" else -1,
            )
        elif state_type == "positive_interference":
            components = tuple(
                _packet(
                    r0=parse_fraction(packet[0]),
                    width=parse_fraction(packet[1]),
                    x0=parse_fraction(packet[2]),
                    mass=initial_mass,
                    sign=1,
                )
                for packet in record["packets"]
            )
            phase = acb(0, arb.pi() * arb_exact(_phase_fraction(record["relative_phase"]))).exp()
            coefficients = acb_mat(18, 1)
            for row in range(18):
                coefficients[row, 0] = components[0][row, 0] + phase * components[1][row, 0]
            coefficients = _normalize(coefficients)
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
            components = positive, negative
            phase = acb(0, arb.pi() * arb_exact(_phase_fraction(record["relative_phase"]))).exp()
            coefficients = acb_mat(18, 1)
            for row in range(18):
                coefficients[row, 0] = positive[row, 0] + phase * negative[row, 0]
            coefficients = _normalize(coefficients)
        else:
            raise SymmetryQCASpecError("unknown registered state type")
        return CertifiedStateDefinition(state_id, coefficients, components)
