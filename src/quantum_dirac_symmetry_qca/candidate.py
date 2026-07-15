"""Direct Dirac-QCA primitives restricted to nonregistered fixture sizes."""

from __future__ import annotations

from fractions import Fraction

from mpmath import mp


FIXTURE_SIZES = (6, 10)
MINIMUM_DPS = 80


class SymmetryQCAFixtureError(ValueError):
    """Raised when an outcome-free fixture request crosses its boundary."""


def _number(value: int | str | Fraction):
    if isinstance(value, Fraction):
        return mp.mpf(value.numerator) / value.denominator
    return mp.mpf(value)


def _require_fixture_size(n_sites: int) -> None:
    if type(n_sites) is not int or n_sites not in FIXTURE_SIZES:
        raise SymmetryQCAFixtureError(
            f"only disclosed nonregistered sizes {FIXTURE_SIZES} are allowed"
        )


def _require_state(state: mp.matrix, n_sites: int) -> None:
    if not isinstance(state, mp.matrix) or state.rows != 2 * n_sites or state.cols < 1:
        raise SymmetryQCAFixtureError("state shape must be (2N, columns)")


def basis_state(n_sites: int, site: int, component: str) -> mp.matrix:
    _require_fixture_size(n_sites)
    if type(site) is not int or not 0 <= site < n_sites:
        raise SymmetryQCAFixtureError("basis site is outside the cycle")
    if component not in ("R", "L"):
        raise SymmetryQCAFixtureError("component must be R or L")
    state = mp.matrix(2 * n_sites, 1)
    state[2 * site + (component == "L"), 0] = 1
    return state


def translate(state: mp.matrix, *, n_sites: int, offset: int = 1) -> mp.matrix:
    _require_fixture_size(n_sites)
    _require_state(state, n_sites)
    if type(offset) is not int:
        raise SymmetryQCAFixtureError("translation offset must be an integer")
    result = mp.matrix(state.rows, state.cols)
    for site in range(n_sites):
        target = (site + offset) % n_sites
        for component in (0, 1):
            for column in range(state.cols):
                result[2 * target + component, column] = state[
                    2 * site + component, column
                ]
    return result


def direct_qca_step(
    state: mp.matrix,
    *,
    n_sites: int,
    mu: int | str | Fraction,
    dps: int = 90,
) -> mp.matrix:
    """Apply the direct `[[n S_-,-i mu],[-i mu,n S_+]]` update."""

    _require_fixture_size(n_sites)
    _require_state(state, n_sites)
    if type(dps) is not int or dps < MINIMUM_DPS:
        raise SymmetryQCAFixtureError("fixture arithmetic requires at least 80 digits")
    with mp.workdps(dps):
        mass = _number(mu)
        if not mp.isfinite(mass) or abs(mass) >= 1:
            raise SymmetryQCAFixtureError("mu must be finite with abs(mu) < 1")
        normalization = mp.sqrt(1 - mass * mass)
        result = mp.matrix(state.rows, state.cols)
        for site in range(n_sites):
            r_row = 2 * site
            l_row = r_row + 1
            # The target Fourier convention is exp(+ikx).  R therefore reads
            # from x-1 (right-moving profile) and L from x+1.
            right_r = 2 * ((site - 1) % n_sites)
            left_l = 2 * ((site + 1) % n_sites) + 1
            for column in range(state.cols):
                result[r_row, column] = (
                    normalization * state[right_r, column]
                    - 1j * mass * state[l_row, column]
                )
                result[l_row, column] = (
                    -1j * mass * state[r_row, column]
                    + normalization * state[left_l, column]
                )
        return result


def local_phase_probe(
    state: mp.matrix,
    *,
    n_sites: int,
    site: int,
    phase_pi: int | str | Fraction,
    dps: int = 90,
) -> mp.matrix:
    """Apply a disclosed on-site number phase to both directional modes.

    This is a causal-support fixture, not a registered scalar-potential
    evaluator.  The supplied phase is an exact coefficient of ``pi``.
    """

    _require_fixture_size(n_sites)
    _require_state(state, n_sites)
    if type(site) is not int or not 0 <= site < n_sites:
        raise SymmetryQCAFixtureError("phase-probe site is outside the cycle")
    if type(dps) is not int or dps < MINIMUM_DPS:
        raise SymmetryQCAFixtureError("fixture arithmetic requires at least 80 digits")
    with mp.workdps(dps):
        coefficient = _number(phase_pi)
        if not mp.isfinite(coefficient):
            raise SymmetryQCAFixtureError("phase-probe coefficient must be finite")
        result = state.copy()
        phase = mp.exp(-1j * mp.pi * coefficient)
        for component in (0, 1):
            row = 2 * site + component
            for column in range(state.cols):
                result[row, column] *= phase
        return result


def direct_qca_probe_step(
    state: mp.matrix,
    *,
    n_sites: int,
    mu: int | str | Fraction,
    site: int,
    phase_pi: int | str | Fraction,
    dps: int = 90,
) -> mp.matrix:
    """Apply the leading local phase and then the exact direct recurrence."""

    phased = local_phase_probe(
        state,
        n_sites=n_sites,
        site=site,
        phase_pi=phase_pi,
        dps=dps,
    )
    return direct_qca_step(phased, n_sites=n_sites, mu=mu, dps=dps)


def update_matrix(*, n_sites: int, mu: int | str | Fraction, dps: int = 90) -> mp.matrix:
    _require_fixture_size(n_sites)
    identity = mp.eye(2 * n_sites)
    return direct_qca_step(identity, n_sites=n_sites, mu=mu, dps=dps)
