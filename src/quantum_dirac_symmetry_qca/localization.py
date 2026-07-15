"""Strictly local full-space lift of the direct symmetry-derived Dirac QCA.

The local Hilbert space is two qubits, labelled ``R`` and ``L``.  Sparse
states use a computational-basis integer whose bit ``2*x`` is ``R_x`` and
whose bit ``2*x + 1`` is ``L_x``.  The construction deliberately exposes
every local gate; no whole-lattice translation operation is available here.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from fractions import Fraction

from mpmath import mp

from .candidate import (
    MINIMUM_DPS,
    SymmetryQCAFixtureError,
    _number,
    _require_fixture_size,
)


SparseFullState = dict[int, object]


def _require_precision(dps: int) -> None:
    if type(dps) is not int or dps < MINIMUM_DPS:
        raise SymmetryQCAFixtureError(
            "fixture arithmetic requires at least 80 digits"
        )


def _mass_parameters(mu: int | str | Fraction, dps: int):
    _require_precision(dps)
    mass = _number(mu)
    if not mp.isfinite(mass) or abs(mass) >= 1:
        raise SymmetryQCAFixtureError("mu must be finite with abs(mu) < 1")
    return mass, mp.sqrt(1 - mass * mass)


def _require_sparse_state(
    state: Mapping[int, object], n_sites: int
) -> SparseFullState:
    _require_fixture_size(n_sites)
    if not isinstance(state, Mapping):
        raise SymmetryQCAFixtureError("full-space state must be a sparse mapping")
    dimension = 1 << (2 * n_sites)
    result: SparseFullState = {}
    for basis, amplitude in state.items():
        if type(basis) is not int or not 0 <= basis < dimension:
            raise SymmetryQCAFixtureError(
                "full-space basis index is outside the Hilbert space"
            )
        if not mp.isfinite(amplitude):
            raise SymmetryQCAFixtureError("full-space amplitudes must be finite")
        if amplitude != 0:
            result[basis] = amplitude
    return result


def _mode_index(n_sites: int, site: int, component: str) -> int:
    _require_fixture_size(n_sites)
    if type(site) is not int or not 0 <= site < n_sites:
        raise SymmetryQCAFixtureError("basis site is outside the cycle")
    if component not in ("R", "L"):
        raise SymmetryQCAFixtureError("component must be R or L")
    return 2 * site + (component == "L")


def full_basis_state(
    n_sites: int, occupied_modes: Iterable[tuple[int, str]] = ()
) -> SparseFullState:
    """Return a computational basis state in the complete ``4**N`` space."""

    _require_fixture_size(n_sites)
    basis = 0
    for site, component in occupied_modes:
        mode = _mode_index(n_sites, site, component)
        if basis & (1 << mode):
            raise SymmetryQCAFixtureError("an occupation mode was supplied twice")
        basis |= 1 << mode
    return {basis: mp.mpf(1)}


def edge_scatter_gate(*, mu: int | str | Fraction, dps: int = 90) -> mp.matrix:
    """Return the full two-qubit gate on ``(L_x, R_(x+1))``.

    The basis order is ``|00>, |01>, |10>, |11>``.  Vacuum and double
    occupation are fixed explicitly.  On the one-excitation block the gate is
    ``[[-i*mu, n], [n, -i*mu]]`` in the mode-amplitude order ``(L, R)``.
    """

    with mp.workdps(dps):
        mass, normalization = _mass_parameters(mu, dps)
        gate = mp.matrix(4, 4)
        gate[0, 0] = 1
        gate[1, 1] = -1j * mass
        gate[1, 2] = normalization
        gate[2, 1] = normalization
        gate[2, 2] = -1j * mass
        gate[3, 3] = 1
        return gate


def on_site_swap_gate() -> mp.matrix:
    """Return the full two-qubit SWAP gate on ``(R_x, L_x)``."""

    gate = mp.matrix(4, 4)
    gate[0, 0] = 1
    gate[1, 2] = 1
    gate[2, 1] = 1
    gate[3, 3] = 1
    return gate


def _apply_two_mode_gate(
    state: Mapping[int, object],
    *,
    mode_a: int,
    mode_b: int,
    gate: mp.matrix,
) -> SparseFullState:
    if mode_a == mode_b:
        raise SymmetryQCAFixtureError("a two-mode gate requires distinct modes")
    clear_mask = ~((1 << mode_a) | (1 << mode_b))
    result: SparseFullState = {}
    for basis, amplitude in state.items():
        local_input = 2 * ((basis >> mode_a) & 1) + ((basis >> mode_b) & 1)
        cleared = basis & clear_mask
        for local_output in range(4):
            coefficient = gate[local_output, local_input]
            if coefficient == 0:
                continue
            output = cleared
            if local_output & 2:
                output |= 1 << mode_a
            if local_output & 1:
                output |= 1 << mode_b
            result[output] = result.get(output, 0) + coefficient * amplitude
    return {
        basis: amplitude
        for basis, amplitude in result.items()
        if amplitude != 0
    }


def _apply_edge_layer(
    state: Mapping[int, object],
    *,
    n_sites: int,
    gate: mp.matrix,
) -> SparseFullState:
    current = dict(state)
    for site in range(n_sites):
        current = _apply_two_mode_gate(
            current,
            mode_a=2 * site + 1,
            mode_b=2 * ((site + 1) % n_sites),
            gate=gate,
        )
    return current


def _apply_on_site_layer(
    state: Mapping[int, object], *, n_sites: int
) -> SparseFullState:
    current = dict(state)
    gate = on_site_swap_gate()
    for site in range(n_sites):
        current = _apply_two_mode_gate(
            current,
            mode_a=2 * site,
            mode_b=2 * site + 1,
            gate=gate,
        )
    return current


def margolus_step(
    state: Mapping[int, object],
    *,
    n_sites: int,
    mu: int | str | Fraction,
    dps: int = 90,
) -> SparseFullState:
    """Apply edge scatter then on-site routing on the complete Hilbert space."""

    with mp.workdps(dps):
        current = _require_sparse_state(state, n_sites)
        current = _apply_edge_layer(
            current,
            n_sites=n_sites,
            gate=edge_scatter_gate(mu=mu, dps=dps),
        )
        return _apply_on_site_layer(current, n_sites=n_sites)


def margolus_inverse(
    state: Mapping[int, object],
    *,
    n_sites: int,
    mu: int | str | Fraction,
    dps: int = 90,
) -> SparseFullState:
    """Apply the exact reverse causal order of :func:`margolus_step`."""

    with mp.workdps(dps):
        mass, _ = _mass_parameters(mu, dps)
        current = _require_sparse_state(state, n_sites)
        current = _apply_on_site_layer(current, n_sites=n_sites)
        return _apply_edge_layer(
            current,
            n_sites=n_sites,
            gate=edge_scatter_gate(mu=-mass, dps=dps),
        )


def _permute_modes(
    state: Mapping[int, object], *, n_sites: int, targets: tuple[int, ...]
) -> SparseFullState:
    current = _require_sparse_state(state, n_sites)
    if tuple(sorted(targets)) != tuple(range(2 * n_sites)):
        raise SymmetryQCAFixtureError(
            "mode transformation must be a permutation"
        )
    result: SparseFullState = {}
    for basis, amplitude in current.items():
        output = 0
        for source, target in enumerate(targets):
            if basis & (1 << source):
                output |= 1 << target
        result[output] = amplitude
    return result


def translate_full(
    state: Mapping[int, object], *, n_sites: int, offset: int = 1
) -> SparseFullState:
    """Translate a state for covariance tests; this is not used by the update."""

    if type(offset) is not int:
        raise SymmetryQCAFixtureError("translation offset must be an integer")
    targets = tuple(
        2 * ((mode // 2 + offset) % n_sites) + mode % 2
        for mode in range(2 * n_sites)
    )
    return _permute_modes(state, n_sites=n_sites, targets=targets)


def parity_full(
    state: Mapping[int, object], *, n_sites: int
) -> SparseFullState:
    """Apply parity ``x -> -x`` together with ``R <-> L``."""

    targets = tuple(
        2 * ((-(mode // 2)) % n_sites) + (1 - mode % 2)
        for mode in range(2 * n_sites)
    )
    return _permute_modes(state, n_sites=n_sites, targets=targets)


def time_reverse_full(
    state: Mapping[int, object], *, n_sites: int
) -> SparseFullState:
    """Apply the antiunitary time reversal ``Theta = (prod_x SWAP_x) K``."""

    targets = tuple(
        2 * (mode // 2) + (1 - mode % 2) for mode in range(2 * n_sites)
    )
    conjugated = {
        basis: mp.conj(amplitude)
        for basis, amplitude in _require_sparse_state(state, n_sites).items()
    }
    return _permute_modes(conjugated, n_sites=n_sites, targets=targets)


def one_excitation_vector(
    state: Mapping[int, object], *, n_sites: int
) -> mp.matrix:
    """Read a full-space state as the existing ``(R_0,L_0,...)`` fixture."""

    current = _require_sparse_state(state, n_sites)
    result = mp.matrix(2 * n_sites, 1)
    for basis, amplitude in current.items():
        if basis.bit_count() != 1:
            raise SymmetryQCAFixtureError("state is not in the one-excitation sector")
        result[basis.bit_length() - 1, 0] = amplitude
    return result


def resource_clock(*, n_sites: int, macrosteps: int = 1) -> dict[str, int | str]:
    """Return explicit storage, depth, and gate-work coordinates."""

    _require_fixture_size(n_sites)
    if type(macrosteps) is not int or macrosteps < 0:
        raise SymmetryQCAFixtureError("macrosteps must be a nonnegative integer")
    return {
        "local_hilbert_dimension": 4,
        "occupation_modes": 2 * n_sites,
        "ancilla_modes": 0,
        "macrosteps": macrosteps,
        "elementary_layers": 2 * macrosteps,
        "two_mode_gate_work": 2 * n_sites * macrosteps,
        "causal_radius_per_macrostep": 1,
        "gate_order": "edge_scatter_then_on_site_swap",
    }
