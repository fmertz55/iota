"""Certified primary engines for the direct symmetry-derived Dirac QCA.

Registered constructors require an opaque Git-bound permit.  The only public
pre-freeze execution helpers are separately guarded N=6/N=10 and cutoff-3
fixtures; they cannot load a registered scenario or state.
"""

from __future__ import annotations

from contextlib import contextmanager
from fractions import Fraction
from typing import Any, Iterator, Sequence

from flint import acb, acb_mat, arb, ctx

from .authorization import RegisteredEvaluationPermit, validate_registered_permit
from .protocol import (
    CONFIRMATION_SCENARIOS,
    DEVELOPMENT_SCENARIOS,
    INPUT_R_MAX,
    INPUT_R_MIN,
    PHYSICAL_LENGTH,
    PRECISION_BITS,
    REGISTERED_OBSERVATION_TIMES,
    REGISTERED_SIZES,
    SPEC_DIR_REF,
    TARGET_R_CUTOFF,
)
from .spec import (
    SymmetryQCASpecError,
    guard_pre_freeze_candidate,
    guard_pre_freeze_target,
    load_json,
    parse_fraction,
)


@contextmanager
def ball_precision(bits: int = PRECISION_BITS) -> Iterator[None]:
    if type(bits) is not int or bits < PRECISION_BITS:
        raise SymmetryQCASpecError(
            f"certified arithmetic requires at least {PRECISION_BITS} bits"
        )
    previous = ctx.prec
    ctx.prec = bits
    try:
        yield
    finally:
        ctx.prec = previous


def arb_exact(value: Fraction | int | str) -> arb:
    fraction = value if isinstance(value, Fraction) else Fraction(value)
    return arb(fraction.numerator) / arb(fraction.denominator)


def _copy(value: acb_mat) -> acb_mat:
    result = acb_mat(value.nrows(), value.ncols())
    for row in range(value.nrows()):
        for column in range(value.ncols()):
            result[row, column] = value[row, column]
    return result


def _require_shape(state: acb_mat, n_sites: int) -> None:
    if not isinstance(state, acb_mat) or state.nrows() != 2 * n_sites or state.ncols() < 1:
        raise SymmetryQCASpecError("candidate state shape must be (2N, columns)")


def certified_direct_step(
    state: acb_mat,
    *,
    n_sites: int,
    mu: Fraction | int | str,
) -> acb_mat:
    """Apply the real-space direct law in the fixed positive-k convention."""

    _require_shape(state, n_sites)
    mass = arb_exact(mu)
    if not (abs(mass) < 1):
        raise SymmetryQCASpecError("direct-QCA mu must satisfy abs(mu)<1")
    normalization = (1 - mass * mass).sqrt()
    coupling = acb(0, -mass)
    result = acb_mat(state.nrows(), state.ncols())
    for site in range(n_sites):
        right = 2 * site
        left = right + 1
        previous_right = 2 * ((site - 1) % n_sites)
        next_left = 2 * ((site + 1) % n_sites) + 1
        for column in range(state.ncols()):
            result[right, column] = (
                normalization * state[previous_right, column]
                + coupling * state[left, column]
            )
            result[left, column] = (
                coupling * state[right, column]
                + normalization * state[next_left, column]
            )
    return result


def _certified_direct_step_adjoint(
    state: acb_mat,
    *,
    n_sites: int,
    mu: Fraction | int | str,
) -> acb_mat:
    """Apply the exact one-excitation adjoint of ``certified_direct_step``."""

    _require_shape(state, n_sites)
    mass = arb_exact(mu)
    if not (abs(mass) < 1):
        raise SymmetryQCASpecError("direct-QCA mu must satisfy abs(mu)<1")
    normalization = (1 - mass * mass).sqrt()
    coupling = acb(0, mass)
    result = acb_mat(state.nrows(), state.ncols())
    for site in range(n_sites):
        right = 2 * site
        left = right + 1
        next_right = 2 * ((site + 1) % n_sites)
        previous_left = 2 * ((site - 1) % n_sites) + 1
        for column in range(state.ncols()):
            result[right, column] = (
                normalization * state[next_right, column]
                + coupling * state[left, column]
            )
            result[left, column] = (
                coupling * state[right, column]
                + normalization * state[previous_left, column]
            )
    return result


def certified_phase_layer(
    state: acb_mat,
    *,
    n_sites: int,
    delta: Fraction,
    potentials: Sequence[arb],
) -> acb_mat:
    _require_shape(state, n_sites)
    if len(potentials) != n_sites:
        raise SymmetryQCASpecError("potential vector length mismatch")
    time_step = arb_exact(delta)
    result = acb_mat(state.nrows(), state.ncols())
    for site, potential in enumerate(potentials):
        phase = acb(0, -(time_step * potential)).exp()
        for component in (0, 1):
            row = 2 * site + component
            for column in range(state.ncols()):
                result[row, column] = phase * state[row, column]
    return result


def _certified_phase_layer_adjoint(
    state: acb_mat,
    *,
    n_sites: int,
    delta: Fraction,
    potentials: Sequence[arb],
) -> acb_mat:
    _require_shape(state, n_sites)
    if len(potentials) != n_sites:
        raise SymmetryQCASpecError("potential vector length mismatch")
    time_step = arb_exact(delta)
    result = acb_mat(state.nrows(), state.ncols())
    for site, potential in enumerate(potentials):
        phase = acb(0, time_step * potential).exp()
        for component in (0, 1):
            row = 2 * site + component
            for column in range(state.ncols()):
                result[row, column] = phase * state[row, column]
    return result


def certified_input_basis(*, n_sites: int) -> acb_mat:
    result = acb_mat(2 * n_sites, 2 * (INPUT_R_MAX - INPUT_R_MIN + 1))
    normalization = arb(n_sites).sqrt()
    two_pi = 2 * arb.pi()
    for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
        for component in (0, 1):
            column = 2 * (r - INPUT_R_MIN) + component
            for site in range(n_sites):
                angle = two_pi * arb(r * site) / arb(n_sites)
                result[2 * site + component, column] = acb(0, angle).exp() / normalization
    return result


def production_candidate_fixture(
    state: acb_mat,
    *,
    n_sites: int,
    mu: Fraction | int | str,
    bits: int = PRECISION_BITS,
) -> acb_mat:
    guard_pre_freeze_candidate(n_sites=n_sites)
    with ball_precision(bits):
        return certified_direct_step(state, n_sites=n_sites, mu=mu)


def _target_row(r: int, component: int, cutoff: int) -> int:
    if type(r) is not int or not -cutoff <= r <= cutoff or component not in (0, 1):
        raise SymmetryQCASpecError("target mode is outside its declared basis")
    return 2 * (r + cutoff) + component


def build_certified_target_hamiltonian(
    *,
    cutoff: int,
    mass: Fraction,
    harmonic: int,
    potential_amplitude: Fraction,
    potential_phase_pi: Fraction,
) -> acb_mat:
    if type(cutoff) is not int or cutoff < 1:
        raise SymmetryQCASpecError("target cutoff must be positive")
    if type(harmonic) is not int or harmonic < 1:
        raise SymmetryQCASpecError("target harmonic must be positive")
    dimension = 2 * (2 * cutoff + 1)
    result = acb_mat(dimension, dimension)
    mass_ball = arb_exact(mass)
    for r in range(-cutoff, cutoff + 1):
        momentum = 2 * arb.pi() * arb(r) / arb(PHYSICAL_LENGTH)
        right = _target_row(r, 0, cutoff)
        left = right + 1
        result[right, right] = momentum
        result[left, left] = -momentum
        result[right, left] = mass_ball
        result[left, right] = mass_ball
    if potential_amplitude:
        amplitude = arb_exact(potential_amplitude)
        phase = arb.pi() * arb_exact(potential_phase_pi)
        upward = amplitude * acb(0, phase).exp() / 2
        downward = amplitude * acb(0, -phase).exp() / 2
        for source_r in range(-cutoff, cutoff + 1):
            for component in (0, 1):
                source = _target_row(source_r, component, cutoff)
                if source_r + harmonic <= cutoff:
                    target = _target_row(source_r + harmonic, component, cutoff)
                    result[target, source] += upward
                if source_r - harmonic >= -cutoff:
                    target = _target_row(source_r - harmonic, component, cutoff)
                    result[target, source] += downward
    return result


def production_target_fixture(
    *,
    cutoff: int,
    mass: Fraction | int | str,
    potential_amplitude: Fraction | int | str,
    potential_phase_pi: Fraction | int | str = 0,
    bits: int = PRECISION_BITS,
) -> acb_mat:
    guard_pre_freeze_target(cutoff=cutoff)
    with ball_precision(bits):
        return build_certified_target_hamiltonian(
            cutoff=cutoff,
            mass=Fraction(mass),
            harmonic=2,
            potential_amplitude=Fraction(potential_amplitude),
            potential_phase_pi=Fraction(potential_phase_pi),
        )


def _phase_coefficient(value: str) -> Fraction:
    if value == "0":
        return Fraction(0)
    if value == "pi/2":
        return Fraction(1, 2)
    raise SymmetryQCASpecError("potential phase is outside the fixed grammar")


def _interval_value(records: list[list[Any]], time: Fraction) -> Fraction:
    for start, end, value in records:
        if parse_fraction(start) <= time < parse_fraction(end):
            return parse_fraction(value)
    raise SymmetryQCASpecError(f"schedule does not cover time {time}")


def _potential_parameters(
    records: list[list[Any]], time: Fraction
) -> tuple[int, Fraction, Fraction] | None:
    for start, end, harmonic, amplitude, phase in records:
        if parse_fraction(start) <= time < parse_fraction(end):
            return harmonic, parse_fraction(amplitude), _phase_coefficient(phase)
    return None


def _observation_steps(delta: Fraction) -> tuple[int, ...]:
    result: list[int] = []
    for value in REGISTERED_OBSERVATION_TIMES:
        quotient = parse_fraction(value) / delta
        if quotient.denominator != 1:
            raise SymmetryQCASpecError("observation does not align with the macrostep grid")
        result.append(quotient.numerator)
    return tuple(result)


class _RegisteredScenarios:
    def __init__(self, permit: RegisteredEvaluationPermit):
        validate_registered_permit(permit)
        value = load_json(permit.root / SPEC_DIR_REF / "scenarios.json")
        expected = DEVELOPMENT_SCENARIOS if permit.stage == "development" else CONFIRMATION_SCENARIOS
        records = value[permit.stage]
        if tuple(record["id"] for record in records) != expected:
            raise SymmetryQCASpecError("registered scenario order mismatch")
        self.permit = permit
        self.records = {record["id"]: record for record in records}

    def get(self, scenario_id: str) -> dict[str, Any]:
        validate_registered_permit(self.permit)
        try:
            return self.records[scenario_id]
        except KeyError as exc:
            raise SymmetryQCASpecError("scenario is outside the opened partition") from exc


def _potential_vector(
    *, n_sites: int, harmonic: int, amplitude: Fraction, phase_pi: Fraction
) -> list[arb]:
    phase = arb.pi() * arb_exact(phase_pi)
    return [
        arb_exact(amplitude)
        * (2 * arb.pi() * arb(harmonic * site) / arb(n_sites) + phase).cos()
        for site in range(n_sites)
    ]


def _target_input_basis(cutoff: int) -> acb_mat:
    result = acb_mat(2 * (2 * cutoff + 1), 18)
    for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
        for component in (0, 1):
            result[_target_row(r, component, cutoff), 2 * (r - INPUT_R_MIN) + component] = 1
    return result


def _free_target_step(
    state: acb_mat, *, cutoff: int, mass: Fraction, duration: Fraction
) -> acb_mat:
    result = acb_mat(state.nrows(), state.ncols())
    mass_ball = arb_exact(mass)
    time = arb_exact(duration)
    for r in range(-cutoff, cutoff + 1):
        momentum = 2 * arb.pi() * arb(r) / arb(PHYSICAL_LENGTH)
        omega = (momentum * momentum + mass_ball * mass_ball).sqrt()
        right = _target_row(r, 0, cutoff)
        left = right + 1
        if omega.contains(0):
            for column in range(state.ncols()):
                result[right, column] = state[right, column]
                result[left, column] = state[left, column]
            continue
        cosine = (omega * time).cos()
        factor = acb(0, -(omega * time).sin() / omega)
        for column in range(state.ncols()):
            right_value = state[right, column]
            left_value = state[left, column]
            result[right, column] = cosine * right_value + factor * (
                momentum * right_value + mass_ball * left_value
            )
            result[left, column] = cosine * left_value + factor * (
                mass_ball * right_value - momentum * left_value
            )
    return result


class CertifiedRegisteredEvaluator:
    """Primary registered candidate and target evaluator."""

    def __init__(
        self,
        permit: RegisteredEvaluationPermit,
        *,
        n_sites: int,
        bits: int = PRECISION_BITS,
    ):
        validate_registered_permit(permit)
        if n_sites not in REGISTERED_SIZES:
            raise SymmetryQCASpecError("registered size is outside the refinement ladder")
        if bits < PRECISION_BITS:
            raise SymmetryQCASpecError("registered precision is below the fixed minimum")
        self.permit = permit
        self.n_sites = n_sites
        self.delta = Fraction(PHYSICAL_LENGTH, n_sites)
        self.bits = bits
        self.scenarios = _RegisteredScenarios(permit)
        self._target_propagators: dict[tuple[Fraction, int, Fraction, Fraction], acb_mat] = {}

    def _candidate_evolve(
        self, scenario_id: str, initial: acb_mat, *, every_step: bool = False
    ) -> dict[int, acb_mat]:
        validate_registered_permit(self.permit)
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        with ball_precision(self.bits):
            current = _copy(initial)
            outputs: dict[int, acb_mat] = {}
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                if potential is not None:
                    harmonic, amplitude, phase_pi = potential
                    current = certified_phase_layer(
                        current,
                        n_sites=self.n_sites,
                        delta=self.delta,
                        potentials=_potential_vector(
                            n_sites=self.n_sites,
                            harmonic=harmonic,
                            amplitude=amplitude,
                            phase_pi=phase_pi,
                        ),
                    )
                current = certified_direct_step(
                    current,
                    n_sites=self.n_sites,
                    mu=self.delta * mass,
                )
                layer = step + 1
                if every_step or layer in observations:
                    outputs[layer] = _copy(current)
            return outputs

    def candidate_outputs(self, scenario_id: str) -> dict[int, acb_mat]:
        return self._candidate_evolve(
            scenario_id, certified_input_basis(n_sites=self.n_sites)
        )

    def candidate_state_series(
        self, scenario_id: str, coefficients: acb_mat
    ) -> dict[int, acb_mat]:
        initial = certified_input_basis(n_sites=self.n_sites) * coefficients
        return self._candidate_evolve(scenario_id, initial, every_step=True)

    def _candidate_final(
        self,
        scenario_id: str,
        initial: acb_mat,
        *,
        reflect_potential: bool = False,
    ) -> acb_mat:
        """Apply the registered schedule, optionally with ``V(x)->V(-x)``."""

        validate_registered_permit(self.permit)
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        with ball_precision(self.bits):
            current = _copy(initial)
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                if potential is not None:
                    harmonic, amplitude, phase_pi = potential
                    values = _potential_vector(
                        n_sites=self.n_sites,
                        harmonic=harmonic,
                        amplitude=amplitude,
                        phase_pi=phase_pi,
                    )
                    if reflect_potential:
                        values = [values[(-site) % self.n_sites] for site in range(self.n_sites)]
                    current = certified_phase_layer(
                        current,
                        n_sites=self.n_sites,
                        delta=self.delta,
                        potentials=values,
                    )
                current = certified_direct_step(
                    current, n_sites=self.n_sites, mu=self.delta * mass
                )
            return current

    def parity_role_pair(self, scenario_id: str) -> tuple[acb_mat, acb_mat]:
        """Return both sides of ``P U[V] P = U[V(-x)]`` on the input sector."""

        from .reducers import parity_ball

        basis = certified_input_basis(n_sites=self.n_sites)
        left = parity_ball(
            self._candidate_final(
                scenario_id,
                parity_ball(basis, n_sites=self.n_sites),
            ),
            n_sites=self.n_sites,
        )
        right = self._candidate_final(
            scenario_id, basis, reflect_potential=True
        )
        return left, right

    def time_reversal_role_pair(
        self, scenario_id: str
    ) -> tuple[acb_mat, acb_mat]:
        """Return ``Theta U Theta^-1`` and the reversed-schedule adjoint.

        The free direct law agrees exactly.  With the declared prefixed scalar
        phase, their difference is the prospectively gated splitting residual.
        """

        from .reducers import theta_ball

        validate_registered_permit(self.permit)
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        basis = certified_input_basis(n_sites=self.n_sites)
        with ball_precision(self.bits):
            left = theta_ball(
                self._candidate_final(
                    scenario_id,
                    theta_ball(basis, n_sites=self.n_sites),
                ),
                n_sites=self.n_sites,
            )
            # If the reversed schedule is evolved forward and then adjointed,
            # its adjoint acts by the original schedule's adjoint steps in
            # chronological order.  Each S=D P contributes S^dagger=P^dagger
            # D^dagger, hence the direct adjoint is applied first.
            right = _copy(basis)
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                right = _certified_direct_step_adjoint(
                    right,
                    n_sites=self.n_sites,
                    mu=self.delta * mass,
                )
                if potential is not None:
                    harmonic, amplitude, phase_pi = potential
                    right = _certified_phase_layer_adjoint(
                        right,
                        n_sites=self.n_sites,
                        delta=self.delta,
                        potentials=_potential_vector(
                            n_sites=self.n_sites,
                            harmonic=harmonic,
                            amplitude=amplitude,
                            phase_pi=phase_pi,
                        ),
                    )
            return left, right

    def target_outputs(self, scenario_id: str) -> dict[int, acb_mat]:
        validate_registered_permit(self.permit)
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        with ball_precision(self.bits):
            current = _target_input_basis(TARGET_R_CUTOFF)
            outputs: dict[int, acb_mat] = {}
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                if potential is None:
                    current = _free_target_step(
                        current,
                        cutoff=TARGET_R_CUTOFF,
                        mass=mass,
                        duration=self.delta,
                    )
                else:
                    harmonic, amplitude, phase_pi = potential
                    key = mass, harmonic, amplitude, phase_pi
                    propagator = self._target_propagators.get(key)
                    if propagator is None:
                        hamiltonian = build_certified_target_hamiltonian(
                            cutoff=TARGET_R_CUTOFF,
                            mass=mass,
                            harmonic=harmonic,
                            potential_amplitude=amplitude,
                            potential_phase_pi=phase_pi,
                        )
                        try:
                            propagator = (acb(0, -arb_exact(self.delta)) * hamiltonian).exp()
                        except ValueError as exc:
                            raise SymmetryQCASpecError("certified target exponential failed") from exc
                        self._target_propagators[key] = propagator
                    current = propagator * current
                layer = step + 1
                if layer in observations:
                    outputs[layer] = _copy(current)
            return outputs

    def target_state_series(
        self, scenario_id: str, coefficients: acb_mat
    ) -> dict[int, acb_mat]:
        """Evolve a formula-reconstructed target witness at every macrostep."""

        validate_registered_permit(self.permit)
        if coefficients.nrows() != 18 or coefficients.ncols() != 1:
            raise SymmetryQCASpecError("target witness coefficients must be 18 by 1")
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        with ball_precision(self.bits):
            current = _target_input_basis(TARGET_R_CUTOFF) * coefficients
            outputs: dict[int, acb_mat] = {}
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                if potential is None:
                    current = _free_target_step(
                        current,
                        cutoff=TARGET_R_CUTOFF,
                        mass=mass,
                        duration=self.delta,
                    )
                else:
                    harmonic, amplitude, phase_pi = potential
                    key = mass, harmonic, amplitude, phase_pi
                    propagator = self._target_propagators.get(key)
                    if propagator is None:
                        hamiltonian = build_certified_target_hamiltonian(
                            cutoff=TARGET_R_CUTOFF,
                            mass=mass,
                            harmonic=harmonic,
                            potential_amplitude=amplitude,
                            potential_phase_pi=phase_pi,
                        )
                        try:
                            propagator = (
                                acb(0, -arb_exact(self.delta)) * hamiltonian
                            ).exp()
                        except ValueError as exc:
                            raise SymmetryQCASpecError(
                                "certified target exponential failed"
                            ) from exc
                        self._target_propagators[key] = propagator
                    current = propagator * current
                outputs[step + 1] = _copy(current)
            return outputs

    def embed_target(self, columns: acb_mat) -> acb_mat:
        validate_registered_permit(self.permit)
        if columns.nrows() != 2 * (2 * TARGET_R_CUTOFF + 1):
            raise SymmetryQCASpecError("target embedding dimension mismatch")
        with ball_precision(self.bits):
            result = acb_mat(2 * self.n_sites, columns.ncols())
            normalization = arb(self.n_sites).sqrt()
            for r in range(-TARGET_R_CUTOFF, TARGET_R_CUTOFF + 1):
                for component in (0, 1):
                    source = _target_row(r, component, TARGET_R_CUTOFF)
                    for site in range(self.n_sites):
                        phase = acb(
                            0, 2 * arb.pi() * arb(r * site) / arb(self.n_sites)
                        ).exp() / normalization
                        for column in range(columns.ncols()):
                            result[2 * site + component, column] += phase * columns[source, column]
            return result
