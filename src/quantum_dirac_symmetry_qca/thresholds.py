"""Outcome-free analytic quantities used to design, but not freeze, gates."""

from __future__ import annotations

from fractions import Fraction

from mpmath import mp

from .candidate import MINIMUM_DPS, SymmetryQCAFixtureError, _number


def first_interaction_order(
    *, initial_abs_mode: int, boundary_abs_mode: int, harmonic: int
) -> int:
    """Minimum harmonic interactions needed to reach a mode boundary."""

    if any(type(value) is not int for value in (initial_abs_mode, boundary_abs_mode, harmonic)):
        raise SymmetryQCAFixtureError("mode boundaries and harmonic must be integers")
    if initial_abs_mode < 0 or boundary_abs_mode <= initial_abs_mode or harmonic <= 0:
        raise SymmetryQCAFixtureError("invalid interaction-order arguments")
    distance = boundary_abs_mode - initial_abs_mode
    return (distance + harmonic - 1) // harmonic


def amplitude_tail_bound(
    *,
    amplitude: int | str | Fraction,
    duration: int | str | Fraction,
    first_order: int,
    dps: int = 90,
):
    """Return ``2 exp(z) z**s/s!`` for ``z=|amplitude*duration|``."""

    if type(dps) is not int or dps < MINIMUM_DPS:
        raise SymmetryQCAFixtureError("tail arithmetic requires at least 80 digits")
    if type(first_order) is not int or first_order < 1:
        raise SymmetryQCAFixtureError("first interaction order must be positive")
    with mp.workdps(dps):
        z_value = abs(_number(amplitude) * _number(duration))
        if not mp.isfinite(z_value):
            raise SymmetryQCAFixtureError("tail parameters must be finite")
        return 2 * mp.exp(z_value) * z_value**first_order / mp.factorial(first_order)


def leading_correction_endpoint_norm(*, dps: int = 90):
    """Norm of the derived ``K_2`` at ``|k|=pi/2, |m|=3/5``.

    Monotonicity in ``k**2`` and ``m**2`` makes this the maximum of the
    *leading coefficient* on the declared box.  It is not an enclosure of the
    full finite-delta effective-generator remainder and therefore cannot by
    itself freeze the thresholds.
    """

    if type(dps) is not int or dps < MINIMUM_DPS:
        raise SymmetryQCAFixtureError("correction arithmetic requires at least 80 digits")
    with mp.workdps(dps):
        wave_number = mp.pi / 2
        mass = mp.mpf(3) / 5
        x_axis = mass * (wave_number**2 + mass**2) / 6
        z_axis = -(mass**2) * wave_number / 3
        return mp.sqrt(x_axis**2 + z_axis**2)


def draft_threshold_evidence() -> dict[str, object]:
    """Return analytic design quantities without evaluating a registered law."""

    h2_target_order = first_interaction_order(
        initial_abs_mode=4, boundary_abs_mode=73, harmonic=2
    )
    h2_pi_order = first_interaction_order(
        initial_abs_mode=4, boundary_abs_mode=120, harmonic=2
    )
    h3_target_order = first_interaction_order(
        initial_abs_mode=4, boundary_abs_mode=73, harmonic=3
    )
    h3_pi_order = first_interaction_order(
        initial_abs_mode=4, boundary_abs_mode=120, harmonic=3
    )
    return {
        "status": "design_evidence_only_interval_certificate_required",
        "leading_correction_endpoint_norm": leading_correction_endpoint_norm(),
        "h2_target_first_order": h2_target_order,
        "h2_pi_first_order": h2_pi_order,
        "h3_target_first_order": h3_target_order,
        "h3_pi_first_order": h3_pi_order,
        "h2_target_tail": amplitude_tail_bound(
            amplitude="1/8", duration="1", first_order=h2_target_order
        ),
        "h2_pi_tail": amplitude_tail_bound(
            amplitude="1/8", duration="1", first_order=h2_pi_order
        ),
        "h3_target_tail": amplitude_tail_bound(
            amplitude="1/10", duration="6/5", first_order=h3_target_order
        ),
        "h3_pi_tail": amplitude_tail_bound(
            amplitude="1/10", duration="6/5", first_order=h3_pi_order
        ),
    }

