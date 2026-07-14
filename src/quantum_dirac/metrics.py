"""High-precision metric primitives shared by future sealed runners."""

from __future__ import annotations

from collections.abc import Sequence

from mpmath import mp

from .protocol import WORK_DPS
from .spec import QuantumDiracSpecError


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
    ratio=mp.mpf("0.60"),
    margin=mp.mpf("1e-8"),
    near_zero=mp.mpf("1e-10"),
) -> bool:
    coarse = mp.mpf(coarse)
    middle = mp.mpf(middle)
    fine = mp.mpf(fine)
    if min(coarse, middle, fine) < 0:
        raise QuantumDiracSpecError("refinement errors must be nonnegative")
    if coarse <= near_zero:
        return middle <= near_zero and fine <= near_zero
    return middle <= ratio * coarse + margin and fine <= ratio * middle + margin
