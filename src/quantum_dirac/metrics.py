"""High-precision metric primitives shared by future sealed runners."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, InvalidOperation, localcontext

from mpmath import mp

from .protocol import WORK_DPS
from .spec import QuantumDiracSpecError


def _gate_decimal(value) -> Decimal:
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise QuantumDiracSpecError("gate value is not a finite decimal") from exc
    if not number.is_finite():
        raise QuantumDiracSpecError("gate value is not a finite decimal")
    return number


def decimal_leq(value, threshold) -> bool:
    """Compare canonical decimal values without binary or context rounding."""

    return _gate_decimal(value) <= _gate_decimal(threshold)


def spectral_norm_from_gram(matrix: mp.matrix, *, dps: int = WORK_DPS):
    if not isinstance(matrix, mp.matrix) or matrix.cols < 1:
        raise QuantumDiracSpecError("operator matrix is invalid")
    with mp.workdps(dps):
        gram = matrix.H * matrix
        eigenvalues, _ = mp.eighe(gram)
        maximum = max(mp.mpf("0"), eigenvalues[eigenvalues.rows - 1])
        return mp.sqrt(maximum)


def certified_spectral_distance(
    left: mp.matrix,
    right: mp.matrix,
    *,
    target_tail=0,
    numerical_bound=0,
    dps: int = WORK_DPS,
):
    if left.rows != right.rows or left.cols != right.cols:
        raise QuantumDiracSpecError("operator columns must share a common space")
    with mp.workdps(dps):
        tail = mp.mpf(target_tail)
        numeric = mp.mpf(numerical_bound)
        if tail < 0 or numeric < 0:
            raise QuantumDiracSpecError("certification bounds must be nonnegative")
        return spectral_norm_from_gram(left - right, dps=dps) + tail + numeric


def total_variation(left: Sequence, right: Sequence):
    if len(left) != len(right):
        raise QuantumDiracSpecError("distributions have different lengths")
    return mp.fsum(abs(mp.mpf(a) - mp.mpf(b)) for a, b in zip(left, right)) / 2


def l1_distance(left: Sequence, right: Sequence):
    if len(left) != len(right):
        raise QuantumDiracSpecError("vectors have different lengths")
    return mp.fsum(abs(mp.mpf(a) - mp.mpf(b)) for a, b in zip(left, right))


def refinement_gate(
    coarse,
    middle,
    fine,
    *,
    ratio="0.60",
    margin="1e-8",
    near_zero="1e-10",
) -> bool:
    coarse_decimal = _gate_decimal(coarse)
    middle_decimal = _gate_decimal(middle)
    fine_decimal = _gate_decimal(fine)
    ratio_decimal = _gate_decimal(ratio)
    margin_decimal = _gate_decimal(margin)
    near_zero_decimal = _gate_decimal(near_zero)
    if min(coarse_decimal, middle_decimal, fine_decimal) < 0:
        raise QuantumDiracSpecError("refinement errors must be nonnegative")
    with localcontext() as context:
        context.prec = 120
        if coarse_decimal <= near_zero_decimal:
            return middle_decimal <= near_zero_decimal and fine_decimal <= near_zero_decimal
        return (
            middle_decimal <= ratio_decimal * coarse_decimal + margin_decimal
            and fine_decimal <= ratio_decimal * middle_decimal + margin_decimal
        )
