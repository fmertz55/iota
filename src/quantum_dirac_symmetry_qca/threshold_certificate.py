"""Outward-rounded analytic envelope for the prospective absolute gates.

The certificate never constructs a registered state, lattice, or propagator.
It bounds one-step unitary discrepancies uniformly over the declared
``|k|<=pi/2``, ``|m|<=3/5``, ``delta<=1/20`` box and telescopes those bounds
through the horizon.  Refinement-ratio and observable gates remain outcomes.
"""

from __future__ import annotations

from contextlib import contextmanager
from fractions import Fraction
from typing import Iterator

from flint import arb, ctx

from .protocol import (
    DIRECT_DISTANCE_THRESHOLDS,
    PHYSICAL_HORIZON,
    POTENTIAL_DISTANCE_THRESHOLDS,
    PRECISION_BITS,
    REGISTERED_DELTAS,
    REGISTERED_SIZES,
)


class ThresholdCertificateError(ValueError):
    """Raised when the analytic certificate cannot prove its declared gate."""


@contextmanager
def _precision(bits: int = PRECISION_BITS) -> Iterator[None]:
    if type(bits) is not int or bits < PRECISION_BITS:
        raise ThresholdCertificateError(
            f"threshold certificate requires at least {PRECISION_BITS} bits"
        )
    previous = ctx.prec
    ctx.prec = bits
    try:
        yield
    finally:
        ctx.prec = previous


def _exact(value: int | str | Fraction) -> arb:
    fraction = value if isinstance(value, Fraction) else Fraction(value)
    return arb(fraction.numerator) / arb(fraction.denominator)


def _upper_text(value: arb, *, digits: int = 70) -> str:
    middle, radius, exponent = value.mid_rad_10exp(digits)
    upper = int(middle) + abs(int(radius))
    return f"{upper}e{int(exponent)}"


def _strict_upper_less(value: arb, threshold: str) -> bool:
    return bool(value.upper() < _exact(threshold).lower())


def free_step_cubic_coefficient(
    *,
    mode_abs_max: int | None = None,
    delta_max: str = "1/20",
    bits: int = PRECISION_BITS,
) -> dict[str, arb]:
    """Bound ``||U_direct-exp(-i delta H_D)|| <= C delta**3``.

    Write ``x=k delta``, ``y=m delta``, and ``s^2=x^2+y^2``.  The x-axis
    coefficient uses ``|1-sinc(s)|<=s^2/6``.  For the z-axis, regard
    ``sinc(sqrt(u))`` as a function of ``u``; its derivative has magnitude at
    most ``1/6`` from the integral representation of sinc.  A second integral
    comparison retains the cancellation in the scalar term.  All maxima are
    monotone in ``|k|``, ``|m|``, and ``delta`` on the declared box.
    """

    with _precision(bits):
        if mode_abs_max is not None and (
            type(mode_abs_max) is not int or mode_abs_max < 4
        ):
            raise ThresholdCertificateError("mode cutoff must be an integer at least four")
        k_max = (
            arb.pi() / 2
            if mode_abs_max is None
            else 2 * arb.pi() * mode_abs_max / 16
        )
        m_max = _exact("3/5")
        step_max = _exact(delta_max)
        u_max = (m_max * step_max) ** 2
        n_min = (1 - u_max).sqrt()

        x_axis = m_max * (k_max**2 + m_max**2) / 6
        z_axis = k_max * m_max**2 * (1 / (1 + n_min) + _exact("1/6"))

        scalar_as_cubic = step_max * m_max**2 * (
            k_max**2 / 6
            + m_max**2
            * (_exact("1/24") + 1 / (2 * (1 + n_min) ** 2))
        )
        total = (x_axis**2 + z_axis**2 + scalar_as_cubic**2).sqrt()
        return {
            "x_axis_coefficient": x_axis,
            "z_axis_coefficient": z_axis,
            "scalar_as_cubic_coefficient": scalar_as_cubic,
            "total_cubic_coefficient": total,
        }


def _tail_bound(*, amplitude: str, duration: str, first_order: int) -> arb:
    z_value = abs(_exact(amplitude) * _exact(duration))
    factorial = 1
    for value in range(2, first_order + 1):
        factorial *= value
    return 2 * z_value.exp() * z_value**first_order / factorial


def _absolute_envelope(
    *,
    delta: str,
    potential_amplitude: str | None,
    potential_harmonic: int | None,
    potential_duration: str | None,
    target_tail_first_order: int | None,
    band_tail_first_order: int | None,
    coefficient: arb,
) -> dict[str, arb]:
    step = _exact(delta)
    direct = _exact(PHYSICAL_HORIZON) * coefficient * step**2
    splitting = arb(0)
    target_tail = arb(0)
    band_amplitude_tail = arb(0)
    band_leakage_penalty = arb(0)
    pi_amplitude_tail = arb(0)
    if potential_amplitude is not None:
        if potential_harmonic is None or potential_duration is None:
            raise ThresholdCertificateError("potential certificate is incomplete")
        derivative = (
            abs(_exact(potential_amplitude))
            * 2
            * arb.pi()
            * potential_harmonic
            / 16
        )
        splitting = _exact(potential_duration) * step * derivative / 2
        if target_tail_first_order is None:
            raise ThresholdCertificateError("target-tail order is missing")
        target_tail = _tail_bound(
            amplitude=potential_amplitude,
            duration=potential_duration,
            first_order=target_tail_first_order,
        )
        if band_tail_first_order is None:
            raise ThresholdCertificateError("intermediate-band tail order is missing")
        band_amplitude_tail = _tail_bound(
            amplitude=potential_amplitude,
            duration=potential_duration,
            first_order=band_tail_first_order,
        )
        band_leakage_penalty = (
            2
            * _exact(PHYSICAL_HORIZON)
            / step
            * band_amplitude_tail
        )
        pi_order = 58 if potential_harmonic == 2 else 39
        pi_amplitude_tail = _tail_bound(
            amplitude=potential_amplitude,
            duration=potential_duration,
            first_order=pi_order,
        )
    numerical_budget = _exact("1e-10")
    return {
        "direct_telescoped": direct,
        "potential_splitting": splitting,
        "target_tail": target_tail,
        "intermediate_band_amplitude_tail": band_amplitude_tail,
        "intermediate_band_leakage_penalty": band_leakage_penalty,
        "pi_amplitude_tail": pi_amplitude_tail,
        "pi_probability_tail": pi_amplitude_tail**2,
        "numerical_budget": numerical_budget,
        "certified_distance_envelope": direct
        + splitting
        + target_tail
        + band_leakage_penalty
        + numerical_budget,
    }


def build_threshold_certificate(*, bits: int = PRECISION_BITS) -> dict[str, object]:
    """Build and verify the complete outcome-free absolute-gate certificate."""

    with _precision(bits):
        coefficients = free_step_cubic_coefficient(bits=bits)
        total = coefficients["total_cubic_coefficient"]
        potential_bands = {320: 13, 640: 17, 1280: 20}
        refinements: dict[str, dict[str, object]] = {}
        for n_sites, delta in zip(REGISTERED_SIZES, REGISTERED_DELTAS, strict=True):
            direct = _absolute_envelope(
                delta=delta,
                potential_amplitude=None,
                potential_harmonic=None,
                potential_duration=None,
                target_tail_first_order=None,
                band_tail_first_order=None,
                coefficient=total,
            )
            band_mode_abs_max = potential_bands[n_sites]
            band_coefficients = free_step_cubic_coefficient(
                mode_abs_max=band_mode_abs_max,
                delta_max=delta,
                bits=bits,
            )
            band_total = band_coefficients["total_cubic_coefficient"]
            h2_band_order = (band_mode_abs_max - 4) // 2 + 1
            h3_band_order = (band_mode_abs_max - 4) // 3 + 1
            h2 = _absolute_envelope(
                delta=delta,
                potential_amplitude="1/8",
                potential_harmonic=2,
                potential_duration="1",
                target_tail_first_order=35,
                band_tail_first_order=h2_band_order,
                coefficient=band_total,
            )
            h3 = _absolute_envelope(
                delta=delta,
                potential_amplitude="1/10",
                potential_harmonic=3,
                potential_duration="6/5",
                target_tail_first_order=23,
                band_tail_first_order=h3_band_order,
                coefficient=band_total,
            )
            worst_potential = h2
            if h3["certified_distance_envelope"].upper() > h2[
                "certified_distance_envelope"
            ].upper():
                worst_potential = h3
            direct_pass = _strict_upper_less(
                direct["certified_distance_envelope"],
                DIRECT_DISTANCE_THRESHOLDS[n_sites],
            )
            potential_pass = _strict_upper_less(
                worst_potential["certified_distance_envelope"],
                POTENTIAL_DISTANCE_THRESHOLDS[n_sites],
            )
            if not direct_pass or not potential_pass:
                raise ThresholdCertificateError(
                    f"analytic envelope does not fit the N={n_sites} absolute gate"
                )
            refinements[str(n_sites)] = {
                "delta": delta,
                "potential_intermediate_mode_abs_max": band_mode_abs_max,
                "potential_band_coefficient_uppers": {
                    key: _upper_text(value)
                    for key, value in band_coefficients.items()
                },
                "direct": {key: _upper_text(value) for key, value in direct.items()},
                "potential_h2": {key: _upper_text(value) for key, value in h2.items()},
                "potential_h3": {key: _upper_text(value) for key, value in h3.items()},
                "direct_threshold": DIRECT_DISTANCE_THRESHOLDS[n_sites],
                "potential_threshold": POTENTIAL_DISTANCE_THRESHOLDS[n_sites],
                "direct_absolute_gate_certified": direct_pass,
                "potential_absolute_gate_certified": potential_pass,
            }
        return {
            "certificate_version": "0.1-draft",
            "search_id": "ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001",
            "status": "outward_analytic_absolute_gate_certificate",
            "precision_bits": bits,
            "registered_propagation_performed": False,
            "scope": (
                "absolute operator-distance threshold rationale only; "
                "refinement ratios observables and outcomes remain uncomputed"
            ),
            "proof_lemmas": [
                "1-sin(s)/s <= s^2/6 for real s",
                "abs(d/du sinc(sqrt(u))) <= 1/6 by its cosine integral",
                "the scalar cancellation is retained by an integral sinc bound",
                "unitary telescoping sums one-step norm errors without growth",
                "intermediate-band projection adds at most two times its amplitude tail per step",
                "Lie product error <= delta^2 norm([H_D,V])/2",
                "norm([H_D,V])=norm(V prime)<=2 pi h abs(A)/16",
            ],
            "coefficient_uppers": {
                key: _upper_text(value) for key, value in coefficients.items()
            },
            "refinements": refinements,
        }
