"""Registered state construction and certified observable reducers.

The public helpers in this module are numerical primitives.  Loading a frozen
state record requires a Git-bound registered access permit, so importing this
module cannot expose a registered state before the stage opening.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Sequence

from flint import acb, acb_mat, arb
from mpmath import mp

from .authorization import (
    RegisteredEvaluationPermit,
    RegisteredVerificationPermit,
    validate_registered_access,
)
from .certified import arb_exact, ball_precision
from .protocol import (
    CONFIRMATION_STATES,
    DEVELOPMENT_STATES,
    INPUT_R_MAX,
    INPUT_R_MIN,
    PHYSICAL_LENGTH,
    PRECISION_BITS,
    SPEC_DIR_REF,
)
from .spec import QuantumDiracSpecError, load_json, parse_fraction, parse_phase


RegisteredAccess = RegisteredEvaluationPermit | RegisteredVerificationPermit


@dataclass(frozen=True)
class CertifiedStateDefinition:
    state_id: str
    coefficients: acb_mat
    incoherent_components: tuple[acb_mat, ...]


def arb_upper_text(value: arb, *, digits: int = 70) -> str:
    """Serialize a rigorous decimal upper enclosure as integer times 10^exp."""

    middle, radius, exponent = value.mid_rad_10exp(digits)
    upper = int(middle) + abs(int(radius))
    return f"{upper}e{int(exponent)}"


def arb_lower_text(value: arb, *, digits: int = 70) -> str:
    middle, radius, exponent = value.mid_rad_10exp(digits)
    lower = int(middle) - abs(int(radius))
    return f"{lower}e{int(exponent)}"


def arb_abs_upper_text(value: arb, *, digits: int = 70) -> str:
    return arb_upper_text(abs(value), digits=digits)


def mp_text(value: Any, *, digits: int = 80) -> str:
    with mp.workdps(digits + 10):
        return mp.nstr(mp.mpf(value), digits, min_fixed=0, max_fixed=0)


def _probability(value: acb) -> arb:
    return value.real * value.real + value.imag * value.imag


def _copy_ball_column(value: acb_mat) -> acb_mat:
    if value.ncols() != 1:
        raise QuantumDiracSpecError("state coefficient payload must be one column")
    result = acb_mat(value.nrows(), 1)
    for row in range(value.nrows()):
        result[row, 0] = value[row, 0]
    return result


def _normalize_ball(value: acb_mat) -> acb_mat:
    norm_squared = arb(0)
    for row in range(value.nrows()):
        norm_squared += _probability(value[row, 0])
    if norm_squared.contains(0):
        raise QuantumDiracSpecError("registered state normalization contains zero")
    norm = norm_squared.sqrt()
    result = acb_mat(value.nrows(), 1)
    for row in range(value.nrows()):
        result[row, 0] = value[row, 0] / norm
    return result


def _ball_energy_spinor(r: int, mass: Fraction, sign: int) -> tuple[arb, arb]:
    if sign not in (-1, 1) or mass <= 0:
        raise QuantumDiracSpecError("registered energy spinor request is invalid")
    momentum = 2 * arb.pi() * arb(r) / arb(PHYSICAL_LENGTH)
    energy = (momentum * momentum + arb_exact(mass) ** 2).sqrt()
    upper = ((energy + momentum) / (2 * energy)).sqrt()
    lower = ((energy - momentum) / (2 * energy)).sqrt()
    return (upper, lower) if sign == 1 else (lower, -upper)


def _ball_packet(
    *, r0: Fraction, width: Fraction, x0: Fraction, mass: Fraction, sign: int
) -> acb_mat:
    result = acb_mat(2 * (INPUT_R_MAX - INPUT_R_MIN + 1), 1)
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
        spinor = _ball_energy_spinor(r, mass, sign)
        row = 2 * (r - INPUT_R_MIN)
        result[row, 0] = envelope * phase * spinor[0]
        result[row + 1, 0] = envelope * phase * spinor[1]
    return _normalize_ball(result)


def _state_record(access: RegisteredAccess, state_id: str) -> dict[str, Any]:
    validate_registered_access(access)
    expected = DEVELOPMENT_STATES if access.stage == "development" else CONFIRMATION_STATES
    if state_id not in expected:
        raise QuantumDiracSpecError("state is outside the opened partition")
    states = load_json(access.root / SPEC_DIR_REF / "states.json")
    records = states[access.stage]
    if tuple(record["id"] for record in records) != expected:
        raise QuantumDiracSpecError("registered state order differs from the partition")
    return next(record for record in records if record["id"] == state_id)


def build_certified_state(
    access: RegisteredAccess,
    *,
    state_id: str,
    initial_mass: Fraction,
    bits: int = PRECISION_BITS,
) -> CertifiedStateDefinition:
    record = _state_record(access, state_id)
    with ball_precision(bits):
        state_type = record["type"]
        components: tuple[acb_mat, ...] = ()
        if state_type in ("positive", "negative"):
            coefficients = _ball_packet(
                r0=parse_fraction(record["r0"]),
                width=parse_fraction(record["width"]),
                x0=parse_fraction(record["x0"]),
                mass=initial_mass,
                sign=1 if state_type == "positive" else -1,
            )
        elif state_type == "positive_interference":
            packets = tuple(
                _ball_packet(
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
                raise QuantumDiracSpecError("interference phase must be a pi multiple")
            phase = acb(0, arb.pi() * arb_exact(coefficient)).exp()
            coefficients = acb_mat(packets[0].nrows(), 1)
            for row in range(coefficients.nrows()):
                coefficients[row, 0] = packets[0][row, 0] + phase * packets[1][row, 0]
            coefficients = _normalize_ball(coefficients)
            components = packets
        elif state_type == "energy_mixture":
            positive = _ball_packet(
                r0=parse_fraction(record["r0"]),
                width=parse_fraction(record["width"]),
                x0=parse_fraction(record["x0"]),
                mass=initial_mass,
                sign=1,
            )
            negative = _ball_packet(
                r0=parse_fraction(record["r0"]),
                width=parse_fraction(record["width"]),
                x0=parse_fraction(record["x0"]),
                mass=initial_mass,
                sign=-1,
            )
            coefficient, includes_pi = parse_phase(record["relative_phase"])
            if not includes_pi:
                raise QuantumDiracSpecError("energy-mixture phase must be a pi multiple")
            phase = acb(0, arb.pi() * arb_exact(coefficient)).exp()
            coefficients = acb_mat(positive.nrows(), 1)
            for row in range(coefficients.nrows()):
                coefficients[row, 0] = positive[row, 0] + phase * negative[row, 0]
            coefficients = _normalize_ball(coefficients)
            components = (positive, negative)
        else:
            raise QuantumDiracSpecError("unknown registered state type")
        return CertifiedStateDefinition(state_id, coefficients, components)


def theta_ball(state: acb_mat, *, n_sites: int) -> acb_mat:
    result = acb_mat(state.nrows(), state.ncols())
    for site in range(n_sites):
        for column in range(state.ncols()):
            result[2 * site, column] = state[2 * site + 1, column].conjugate()
            result[2 * site + 1, column] = state[2 * site, column].conjugate()
    return result


def parity_ball(state: acb_mat, *, n_sites: int) -> acb_mat:
    result = acb_mat(state.nrows(), state.ncols())
    for site in range(n_sites):
        reflected = (-site) % n_sites
        for column in range(state.ncols()):
            result[2 * site, column] = state[2 * reflected + 1, column]
            result[2 * site + 1, column] = state[2 * reflected, column]
    return result


def _fft(values: list[acb]) -> list[acb]:
    size = len(values)
    if size < 1 or size & (size - 1):
        raise QuantumDiracSpecError("registered Fourier grid must be a power of two")
    result = list(values)
    target = 0
    for source in range(1, size):
        bit = size >> 1
        while target & bit:
            target ^= bit
            bit >>= 1
        target ^= bit
        if source < target:
            result[source], result[target] = result[target], result[source]
    length = 2
    while length <= size:
        root = acb(0, -2 * arb.pi() / arb(length)).exp()
        half = length // 2
        for start in range(0, size, length):
            twiddle = acb(1)
            for offset in range(half):
                even = result[start + offset]
                odd = twiddle * result[start + offset + half]
                result[start + offset] = even + odd
                result[start + offset + half] = even - odd
                twiddle *= root
        length *= 2
    normalization = arb(size).sqrt()
    return [value / normalization for value in result]


def momentum_probabilities_ball(state: acb_mat, *, n_sites: int) -> list[arb]:
    if state.nrows() != 2 * n_sites or state.ncols() != 1:
        raise QuantumDiracSpecError("momentum reducer requires one candidate-space state")
    right = _fft([state[2 * site, 0] for site in range(n_sites)])
    left = _fft([state[2 * site + 1, 0] for site in range(n_sites)])
    return [_probability(right[index]) + _probability(left[index]) for index in range(n_sites)]


def position_probabilities_ball(state: acb_mat, *, n_sites: int) -> list[arb]:
    if state.nrows() != 2 * n_sites or state.ncols() != 1:
        raise QuantumDiracSpecError("position reducer requires one candidate-space state")
    return [
        _probability(state[2 * site, 0]) + _probability(state[2 * site + 1, 0])
        for site in range(n_sites)
    ]


def total_current_ball(state: acb_mat, *, n_sites: int) -> arb:
    return sum(
        (
            _probability(state[2 * site, 0])
            - _probability(state[2 * site + 1, 0])
            for site in range(n_sites)
        ),
        arb(0),
    )


def local_current_ball(state: acb_mat, *, n_sites: int) -> list[arb]:
    return [
        _probability(state[2 * site, 0]) - _probability(state[2 * site + 1, 0])
        for site in range(n_sites)
    ]


def _sum_abs_upper(values: Sequence[arb]) -> arb:
    return sum((abs(value) for value in values), arb(0)).upper()


def distribution_tv_upper(left: Sequence[arb], right: Sequence[arb]) -> arb:
    if len(left) != len(right):
        raise QuantumDiracSpecError("certified distributions have different lengths")
    return (_sum_abs_upper([a - b for a, b in zip(left, right)]) / 2).upper()


def vector_l1_upper(left: Sequence[arb], right: Sequence[arb]) -> arb:
    if len(left) != len(right):
        raise QuantumDiracSpecError("certified vectors have different lengths")
    return _sum_abs_upper([a - b for a, b in zip(left, right)]).upper()


def state_norm_residual_upper(state: acb_mat) -> arb:
    norm_squared = sum((_probability(state[row, 0]) for row in range(state.nrows())), arb(0))
    return abs(norm_squared - 1).upper()


def state_distance_upper(primary: acb_mat, independent: mp.matrix) -> arb:
    if primary.nrows() != independent.rows or primary.ncols() != independent.cols:
        raise QuantumDiracSpecError("state comparison dimensions differ")
    total = arb(0)
    for row in range(primary.nrows()):
        real = mp.nstr(mp.re(independent[row, 0]), 105)
        imaginary = mp.nstr(mp.im(independent[row, 0]), 105)
        difference = primary[row, 0] - acb(real, imaginary)
        total += difference.real * difference.real + difference.imag * difference.imag
    return total.sqrt().upper()


def operator_gram_residual_upper(columns: acb_mat) -> arb:
    gram = columns.conjugate().transpose() * columns
    for index in range(gram.nrows()):
        gram[index, index] -= 1
    from .certified import certified_spectral_norm_upper

    return certified_spectral_norm_upper(gram).upper()


def witness_metrics_ball(
    candidate: acb_mat,
    target: acb_mat,
    *,
    n_sites: int,
) -> dict[str, arb]:
    candidate_position = position_probabilities_ball(candidate, n_sites=n_sites)
    target_position = position_probabilities_ball(target, n_sites=n_sites)
    candidate_momentum = momentum_probabilities_ball(candidate, n_sites=n_sites)
    target_momentum = momentum_probabilities_ball(target, n_sites=n_sites)
    candidate_local = local_current_ball(candidate, n_sites=n_sites)
    target_local = local_current_ball(target, n_sites=n_sites)
    overlap = acb(0)
    for row in range(candidate.nrows()):
        overlap += candidate[row, 0].conjugate() * target[row, 0]
    fidelity_lower = overlap.abs_lower() ** 2
    infidelity_upper = (arb(1) - fidelity_lower).upper().max(arb(0)).upper()
    return {
        "position_tv_upper": distribution_tv_upper(candidate_position, target_position),
        "momentum_tv_upper": distribution_tv_upper(candidate_momentum, target_momentum),
        "total_current_error_upper": abs(
            total_current_ball(candidate, n_sites=n_sites)
            - total_current_ball(target, n_sites=n_sites)
        ).upper(),
        "local_current_l1_upper": vector_l1_upper(candidate_local, target_local),
        "infidelity_upper": infidelity_upper,
        "candidate_norm_residual_upper": state_norm_residual_upper(candidate),
        "target_norm_residual_upper": state_norm_residual_upper(target),
    }
