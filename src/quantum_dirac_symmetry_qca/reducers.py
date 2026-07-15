"""Canonical certified reducers for direct-QCA registered ledgers.

These helpers contain no registered constructor and can be exercised on the
disclosed fixtures.  Stage data can reach them only through the permit-guarded
engines.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any, Sequence

from flint import acb, acb_mat, arb
from mpmath import mp

from .production import arb_exact
from .protocol import (
    DIRECT_DISTANCE_THRESHOLDS,
    DIRECT_REFINEMENT_RATIO,
    NEAR_ZERO_THRESHOLD,
    PHYSICAL_HORIZON,
    PHYSICAL_LENGTH,
    POTENTIAL_DISTANCE_THRESHOLDS,
    POTENTIAL_REFINEMENT_RATIO,
    REFINEMENT_MARGIN,
)
from .spec import SymmetryQCASpecError, parse_fraction


def arb_upper_text(value: arb, *, digits: int = 70) -> str:
    middle, radius, exponent = value.mid_rad_10exp(digits)
    return f"{int(middle) + abs(int(radius))}e{int(exponent)}"


def arb_lower_text(value: arb, *, digits: int = 70) -> str:
    middle, radius, exponent = value.mid_rad_10exp(digits)
    return f"{int(middle) - abs(int(radius))}e{int(exponent)}"


def mp_text(value: Any, *, digits: int = 80) -> str:
    with mp.workdps(digits + 10):
        return mp.nstr(mp.mpf(value), digits, min_fixed=0, max_fixed=0)


def _decimal(value: str) -> Decimal:
    if type(value) is not str or not value:
        raise SymmetryQCASpecError("canonical reducer requires a decimal string")
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise SymmetryQCASpecError("invalid reducer decimal") from exc
    if not result.is_finite() or result < 0:
        raise SymmetryQCASpecError("reducer decimal must be finite and nonnegative")
    return result


def decimal_leq(left: str, right: str) -> bool:
    return _decimal(left) <= _decimal(right)


def _probability(value: acb) -> arb:
    return value.real * value.real + value.imag * value.imag


def certified_spectral_norm_upper(matrix: acb_mat) -> arb:
    gram = matrix.conjugate().transpose() * matrix
    maximum = arb(0)
    for row in range(gram.nrows()):
        row_sum = sum(
            (gram[row, column].abs_upper() for column in range(gram.ncols())),
            arb(0),
        )
        maximum = maximum.max(row_sum)
    return maximum.upper().sqrt()


def operator_gram_residual_upper(columns: acb_mat) -> arb:
    gram = columns.conjugate().transpose() * columns
    for index in range(gram.nrows()):
        gram[index, index] -= 1
    return certified_spectral_norm_upper(gram).upper()


def position_probabilities_ball(state: acb_mat, *, n_sites: int) -> list[arb]:
    if state.nrows() != 2 * n_sites or state.ncols() != 1:
        raise SymmetryQCASpecError("position reducer requires one candidate state")
    return [
        _probability(state[2 * site, 0]) + _probability(state[2 * site + 1, 0])
        for site in range(n_sites)
    ]


def _dft(values: Sequence[acb]) -> list[acb]:
    """Normalized negative-sign DFT for arbitrary registered N."""

    size = len(values)
    if size < 1:
        raise SymmetryQCASpecError("momentum reducer received an empty grid")
    normalization = arb(size).sqrt()
    # FLINT's arbitrary-length certified DFT avoids an O(N^2) Python loop at
    # the registered N=1280 while retaining outward ball enclosures.
    return [value / normalization for value in acb.dft(values)]


def momentum_probabilities_ball(state: acb_mat, *, n_sites: int) -> list[arb]:
    if state.nrows() != 2 * n_sites or state.ncols() != 1:
        raise SymmetryQCASpecError("momentum reducer requires one candidate state")
    right = _dft([state[2 * site, 0] for site in range(n_sites)])
    left = _dft([state[2 * site + 1, 0] for site in range(n_sites)])
    return [_probability(right[index]) + _probability(left[index]) for index in range(n_sites)]


def pi_sector_probability_ball(state: acb_mat, *, n_sites: int) -> arb:
    probabilities = momentum_probabilities_ball(state, n_sites=n_sites)
    total = arb(0)
    for index, probability in enumerate(probabilities):
        signed = index if index <= n_sites // 2 else index - n_sites
        if 4 * abs(signed) >= 3 * n_sites:
            total += probability
    return total.upper()


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


def distribution_tv_upper(left: Sequence[arb], right: Sequence[arb]) -> arb:
    if len(left) != len(right):
        raise SymmetryQCASpecError("distribution reducer dimensions differ")
    return (sum((abs(a - b) for a, b in zip(left, right)), arb(0)) / 2).upper()


def vector_l1_upper(left: Sequence[arb], right: Sequence[arb]) -> arb:
    if len(left) != len(right):
        raise SymmetryQCASpecError("vector reducer dimensions differ")
    return sum((abs(a - b) for a, b in zip(left, right)), arb(0)).upper()


def state_norm_residual_upper(state: acb_mat) -> arb:
    norm = sum((_probability(state[row, 0]) for row in range(state.nrows())), arb(0))
    return abs(norm - 1).upper()


def state_distance_upper(primary: acb_mat, independent: mp.matrix) -> arb:
    if primary.nrows() != independent.rows or primary.ncols() != independent.cols:
        raise SymmetryQCASpecError("independent state dimensions differ")
    total = arb(0)
    for row in range(primary.nrows()):
        for column in range(primary.ncols()):
            value = independent[row, column]
            difference = primary[row, column] - acb(
                mp.nstr(mp.re(value), 105), mp.nstr(mp.im(value), 105)
            )
            total += difference.real * difference.real + difference.imag * difference.imag
    return total.sqrt().upper()


def parity_ball(state: acb_mat, *, n_sites: int) -> acb_mat:
    result = acb_mat(state.nrows(), state.ncols())
    for site in range(n_sites):
        reflected = (-site) % n_sites
        for column in range(state.ncols()):
            result[2 * site, column] = state[2 * reflected + 1, column]
            result[2 * site + 1, column] = state[2 * reflected, column]
    return result


def theta_ball(state: acb_mat, *, n_sites: int) -> acb_mat:
    result = acb_mat(state.nrows(), state.ncols())
    for site in range(n_sites):
        for column in range(state.ncols()):
            result[2 * site, column] = state[2 * site + 1, column].conjugate()
            result[2 * site + 1, column] = state[2 * site, column].conjugate()
    return result


def witness_metrics_ball(
    candidate: acb_mat, target: acb_mat, *, n_sites: int
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
    infidelity = (arb(1) - overlap.abs_lower() ** 2).max(arb(0)).upper()
    return {
        "position_tv_upper": distribution_tv_upper(candidate_position, target_position),
        "momentum_tv_upper": distribution_tv_upper(candidate_momentum, target_momentum),
        "total_current_error_upper": abs(
            total_current_ball(candidate, n_sites=n_sites)
            - total_current_ball(target, n_sites=n_sites)
        ).upper(),
        "local_current_l1_upper": vector_l1_upper(candidate_local, target_local),
        "infidelity_upper": infidelity,
        "candidate_norm_residual_upper": state_norm_residual_upper(candidate),
        "target_norm_residual_upper": state_norm_residual_upper(target),
        "candidate_pi_sector_probability_upper": pi_sector_probability_ball(
            candidate, n_sites=n_sites
        ),
    }


def canonical_refinement_reduction(
    maxima: Sequence[str], *, scenario_class: str
) -> dict[str, Any]:
    if len(maxima) != 3:
        raise SymmetryQCASpecError("refinement reducer requires exactly three maxima")
    values = [_decimal(value) for value in maxima]
    if scenario_class == "direct_only":
        thresholds = DIRECT_DISTANCE_THRESHOLDS
        ratio = Decimal(DIRECT_REFINEMENT_RATIO)
    elif scenario_class == "potential_split":
        thresholds = POTENTIAL_DISTANCE_THRESHOLDS
        ratio = Decimal(POTENTIAL_REFINEMENT_RATIO)
    else:
        raise SymmetryQCASpecError("unknown scenario class")
    sizes = (320, 640, 1280)
    absolute = [value <= Decimal(thresholds[size]) for size, value in zip(sizes, values)]
    near_zero = all(value <= Decimal(NEAR_ZERO_THRESHOLD) for value in values)
    margin = Decimal(REFINEMENT_MARGIN)
    successive = [
        near_zero or values[1] <= ratio * values[0] + margin,
        near_zero or values[2] <= ratio * values[1] + margin,
    ]
    return {
        "scenario_class": scenario_class,
        "absolute_passes": absolute,
        "near_zero_waiver": near_zero,
        "successive_passes": successive,
        "pass": all(absolute) and all(successive),
    }


def canonical_resource_record(
    *, n_sites: int, scenario: dict[str, Any]
) -> dict[str, int]:
    delta = Fraction(PHYSICAL_LENGTH, n_sites)
    steps = Fraction(PHYSICAL_HORIZON, 1) / delta
    if steps.denominator != 1:
        raise SymmetryQCASpecError("resource macrostep count is not integral")
    active = 0
    for step in range(steps.numerator):
        time = step * delta
        if any(parse_fraction(start) <= time < parse_fraction(end) for start, end, *_ in scenario["potential"]):
            active += 1
    elementary_layers = 2 * steps.numerator + active
    return {
        "n_sites": n_sites,
        "macrosteps": steps.numerator,
        "active_potential_steps": active,
        "elementary_layers": elementary_layers,
        "gate_work": n_sites * elementary_layers,
        "occupation_qubits": 2 * n_sites,
        "ancillas": 0,
        "causal_radius_per_macrostep": 1,
    }
