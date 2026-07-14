"""Certified Arb/Acb backend for future sealed quantum-Dirac evaluation."""

from __future__ import annotations

from contextlib import contextmanager
from fractions import Fraction
from typing import Any, Iterator, Sequence

from flint import acb, acb_mat, arb, ctx

from .authorization import RegisteredEvaluationPermit, validate_registered_permit
from .production import (
    _RegisteredScenarioSet,
    _interval_value,
    _observation_steps,
    _potential_parameters,
)
from .protocol import (
    INPUT_R_MAX,
    INPUT_R_MIN,
    PHYSICAL_LENGTH,
    PRECISION_BITS,
    REGISTERED_SIZES,
    TARGET_R_CUTOFF,
)
from .spec import QuantumDiracSpecError, guard_pre_freeze_fixture
from .target import mode_index


@contextmanager
def ball_precision(bits: int = PRECISION_BITS) -> Iterator[None]:
    if type(bits) is not int or bits < PRECISION_BITS:
        raise QuantumDiracSpecError(
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


def _copy_matrix(matrix: acb_mat) -> acb_mat:
    result = acb_mat(matrix.nrows(), matrix.ncols())
    for row in range(matrix.nrows()):
        for column in range(matrix.ncols()):
            result[row, column] = matrix[row, column]
    return result


def certified_input_basis(*, n_sites: int) -> acb_mat:
    columns = 2 * (INPUT_R_MAX - INPUT_R_MIN + 1)
    result = acb_mat(2 * n_sites, columns)
    normalization = arb(n_sites).sqrt()
    two_pi = 2 * arb.pi()
    column = 0
    for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
        for component in (0, 1):
            for site in range(n_sites):
                angle = two_pi * arb(r * site) / arb(n_sites)
                result[2 * site + component, column] = acb(0, angle).exp() / normalization
            column += 1
    return result


def certified_mass_layer(
    state: acb_mat,
    *,
    n_sites: int,
    angle: Fraction | int | str,
) -> acb_mat:
    theta = arb_exact(angle)
    cosine = theta.cos()
    off_diagonal = acb(0, -theta.sin())
    result = acb_mat(state.nrows(), state.ncols())
    for site in range(n_sites):
        r_row = 2 * site
        l_row = r_row + 1
        for column in range(state.ncols()):
            r_value = state[r_row, column]
            l_value = state[l_row, column]
            result[r_row, column] = cosine * r_value + off_diagonal * l_value
            result[l_row, column] = off_diagonal * r_value + cosine * l_value
    return result


def certified_phase_layer(
    state: acb_mat,
    *,
    n_sites: int,
    delta: Fraction | int | str,
    potentials: Sequence[arb],
) -> acb_mat:
    if len(potentials) != n_sites:
        raise QuantumDiracSpecError("certified potential length mismatch")
    dt = arb_exact(delta)
    result = acb_mat(state.nrows(), state.ncols())
    for site, potential in enumerate(potentials):
        phase = acb(0, -(dt * potential)).exp()
        for component in (0, 1):
            row = 2 * site + component
            for column in range(state.ncols()):
                result[row, column] = phase * state[row, column]
    return result


def certified_transport(state: acb_mat, *, n_sites: int) -> acb_mat:
    result = acb_mat(state.nrows(), state.ncols())
    for site in range(n_sites):
        for column in range(state.ncols()):
            result[2 * ((site + 1) % n_sites), column] = state[2 * site, column]
            result[2 * ((site - 1) % n_sites) + 1, column] = state[
                2 * site + 1, column
            ]
    return result


def certified_inverse_transport(state: acb_mat, *, n_sites: int) -> acb_mat:
    result = acb_mat(state.nrows(), state.ncols())
    for site in range(n_sites):
        for column in range(state.ncols()):
            result[2 * ((site - 1) % n_sites), column] = state[2 * site, column]
            result[2 * ((site + 1) % n_sites) + 1, column] = state[
                2 * site + 1, column
            ]
    return result


def certified_fixture_step(
    state: acb_mat,
    *,
    n_sites: int,
    delta: Fraction | int | str,
    mass: Fraction | int | str,
    bits: int = PRECISION_BITS,
) -> acb_mat:
    guard_pre_freeze_fixture(n_sites=n_sites)
    with ball_precision(bits):
        return certified_transport(
            certified_mass_layer(
                state,
                n_sites=n_sites,
                angle=Fraction(delta) * Fraction(mass),
            ),
            n_sites=n_sites,
        )


def _potential_vector(
    *,
    n_sites: int,
    amplitude: Fraction,
    phase_pi: Fraction,
) -> list[arb]:
    amplitude_ball = arb_exact(amplitude)
    phase = arb.pi() * arb_exact(phase_pi)
    two_pi = 2 * arb.pi()
    return [
        amplitude_ball
        * (two_pi * arb(site) / arb(n_sites) + phase).cos()
        for site in range(n_sites)
    ]


def certified_spectral_norm_upper(matrix: acb_mat) -> arb:
    gram = matrix.conjugate().transpose() * matrix
    eigenvalues = gram.eig()
    upper = arb(0)
    for value in eigenvalues:
        upper = upper.max(value.real.upper())
    return upper.sqrt()


def build_certified_target_hamiltonian(
    *,
    cutoff: int,
    mass: Fraction,
    potential_amplitude: Fraction,
    potential_phase_pi: Fraction,
) -> acb_mat:
    dimension = 2 * (2 * cutoff + 1)
    hamiltonian = acb_mat(dimension, dimension)
    two_pi = 2 * arb.pi()
    length = arb(PHYSICAL_LENGTH)
    mass_ball = arb_exact(mass)
    for r in range(-cutoff, cutoff + 1):
        k_value = two_pi * arb(r) / length
        r_index = mode_index(r, 0, cutoff)
        l_index = mode_index(r, 1, cutoff)
        hamiltonian[r_index, r_index] = k_value
        hamiltonian[l_index, l_index] = -k_value
        hamiltonian[r_index, l_index] = mass_ball
        hamiltonian[l_index, r_index] = mass_ball

    if potential_amplitude:
        amplitude = arb_exact(potential_amplitude)
        phase = arb.pi() * arb_exact(potential_phase_pi)
        upward = amplitude * acb(0, phase).exp() / 2
        downward = amplitude * acb(0, -phase).exp() / 2
        for source_r in range(-cutoff, cutoff + 1):
            for component in (0, 1):
                source = mode_index(source_r, component, cutoff)
                if source_r + 1 <= cutoff:
                    target = mode_index(source_r + 1, component, cutoff)
                    hamiltonian[target, source] += upward
                if source_r - 1 >= -cutoff:
                    target = mode_index(source_r - 1, component, cutoff)
                    hamiltonian[target, source] += downward
    return hamiltonian


def certified_free_target_step(
    state: acb_mat,
    *,
    cutoff: int,
    mass: Fraction,
    duration: Fraction,
) -> acb_mat:
    """Apply exact 2x2 free Dirac blocks without a dense exponential."""

    result = acb_mat(state.nrows(), state.ncols())
    mass_ball = arb_exact(mass)
    time = arb_exact(duration)
    for r in range(-cutoff, cutoff + 1):
        momentum = 2 * arb.pi() * arb(r) / arb(PHYSICAL_LENGTH)
        omega = (momentum * momentum + mass_ball * mass_ball).sqrt()
        cosine = (omega * time).cos()
        factor = acb(0, -(omega * time).sin() / omega)
        right = mode_index(r, 0, cutoff)
        left = right + 1
        for column in range(state.ncols()):
            r_value = state[right, column]
            l_value = state[left, column]
            result[right, column] = (
                cosine * r_value
                + factor * (momentum * r_value + mass_ball * l_value)
            )
            result[left, column] = (
                cosine * l_value
                + factor * (mass_ball * r_value - momentum * l_value)
            )
    return result


def certified_target_input_basis() -> acb_mat:
    result = acb_mat(
        2 * (2 * TARGET_R_CUTOFF + 1),
        2 * (INPUT_R_MAX - INPUT_R_MIN + 1),
    )
    column = 0
    for r in range(INPUT_R_MIN, INPUT_R_MAX + 1):
        for component in (0, 1):
            result[mode_index(r, component, TARGET_R_CUTOFF), column] = 1
            column += 1
    return result


def embed_certified_target(columns: acb_mat, *, n_sites: int) -> acb_mat:
    expected_rows = 2 * (2 * TARGET_R_CUTOFF + 1)
    if columns.nrows() != expected_rows:
        raise QuantumDiracSpecError("certified target column dimension mismatch")
    result = acb_mat(2 * n_sites, columns.ncols())
    normalization = arb(n_sites).sqrt()
    two_pi = 2 * arb.pi()
    for r in range(-TARGET_R_CUTOFF, TARGET_R_CUTOFF + 1):
        for component in (0, 1):
            source = mode_index(r, component, TARGET_R_CUTOFF)
            for site in range(n_sites):
                phase = acb(
                    0,
                    two_pi * arb(r * site) / arb(n_sites),
                ).exp() / normalization
                target = 2 * site + component
                for column in range(columns.ncols()):
                    result[target, column] += phase * columns[source, column]
    return result


class CertifiedRegisteredEvaluator:
    """Ball-arithmetic primary evaluator guarded by a registered permit."""

    def __init__(
        self,
        permit: RegisteredEvaluationPermit,
        *,
        n_sites: int,
        bits: int = PRECISION_BITS,
    ):
        validate_registered_permit(permit)
        if n_sites not in REGISTERED_SIZES:
            raise QuantumDiracSpecError("certified size is outside the registered ladder")
        if bits < PRECISION_BITS:
            raise QuantumDiracSpecError("certified precision is below the frozen minimum")
        self.permit = permit
        self.n_sites = n_sites
        self.delta = Fraction(PHYSICAL_LENGTH, n_sites)
        self.bits = bits
        self.scenarios = _RegisteredScenarioSet(permit)
        self._target_propagators: dict[
            tuple[Fraction, Fraction, Fraction], acb_mat
        ] = {}

    def _candidate_evolve(
        self,
        scenario_id: str,
        initial: acb_mat,
        *,
        every_step: bool = False,
        reflected_potential: bool = False,
    ) -> dict[int, acb_mat]:
        validate_registered_permit(self.permit)
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        with ball_precision(self.bits):
            current = _copy_matrix(initial)
            outputs: dict[int, acb_mat] = {}
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                if potential is not None:
                    amplitude, phase_pi = potential
                    if reflected_potential:
                        phase_pi = -phase_pi
                    current = certified_phase_layer(
                        current,
                        n_sites=self.n_sites,
                        delta=self.delta,
                        potentials=_potential_vector(
                            n_sites=self.n_sites,
                            amplitude=amplitude,
                            phase_pi=phase_pi,
                        ),
                    )
                current = certified_mass_layer(
                    current,
                    n_sites=self.n_sites,
                    angle=self.delta * mass,
                )
                current = certified_transport(current, n_sites=self.n_sites)
                layer = step + 1
                if every_step or layer in observations:
                    outputs[layer] = _copy_matrix(current)
            return outputs

    def candidate_outputs(self, scenario_id: str) -> dict[int, acb_mat]:
        return self._candidate_evolve(
            scenario_id,
            certified_input_basis(n_sites=self.n_sites),
        )

    def candidate_state_series(
        self,
        scenario_id: str,
        coefficients: acb_mat,
    ) -> dict[int, acb_mat]:
        validate_registered_permit(self.permit)
        initial = certified_input_basis(n_sites=self.n_sites) * coefficients
        return self._candidate_evolve(scenario_id, initial, every_step=True)

    def candidate_final_from(
        self,
        scenario_id: str,
        initial: acb_mat,
        *,
        reflected_potential: bool = False,
    ) -> acb_mat:
        outputs = self._candidate_evolve(
            scenario_id,
            initial,
            reflected_potential=reflected_potential,
        )
        return outputs[max(outputs)]

    def candidate_reversed_schedule_adjoint(self, scenario_id: str) -> acb_mat:
        """Apply U[a^R]^dagger to the registered input basis.

        With the reversed macrostep schedule, the adjoint is obtained by
        applying each original schedule step's adjoint in chronological order.
        """

        validate_registered_permit(self.permit)
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        with ball_precision(self.bits):
            current = certified_input_basis(n_sites=self.n_sites)
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                current = certified_inverse_transport(current, n_sites=self.n_sites)
                current = certified_mass_layer(
                    current,
                    n_sites=self.n_sites,
                    angle=-(self.delta * mass),
                )
                if potential is not None:
                    amplitude, phase_pi = potential
                    potentials = _potential_vector(
                        n_sites=self.n_sites,
                        amplitude=amplitude,
                        phase_pi=phase_pi,
                    )
                    current = certified_phase_layer(
                        current,
                        n_sites=self.n_sites,
                        delta=self.delta,
                        potentials=[-value for value in potentials],
                    )
            return current

    def target_outputs(self, scenario_id: str) -> dict[int, acb_mat]:
        validate_registered_permit(self.permit)
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        with ball_precision(self.bits):
            current = certified_target_input_basis()
            outputs: dict[int, acb_mat] = {}
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                amplitude, phase_pi = (
                    (Fraction(0), Fraction(0))
                    if potential is None
                    else potential
                )
                key = mass, amplitude, phase_pi
                if amplitude == 0:
                    current = certified_free_target_step(
                        current,
                        cutoff=TARGET_R_CUTOFF,
                        mass=mass,
                        duration=self.delta,
                    )
                else:
                    propagator = self._target_propagators.get(key)
                    if propagator is None:
                        hamiltonian = build_certified_target_hamiltonian(
                            cutoff=TARGET_R_CUTOFF,
                            mass=mass,
                            potential_amplitude=amplitude,
                            potential_phase_pi=phase_pi,
                        )
                        propagator = (
                            acb(0, -arb_exact(self.delta)) * hamiltonian
                        ).exp()
                        self._target_propagators[key] = propagator
                    current = propagator * current
                layer = step + 1
                if layer in observations:
                    outputs[layer] = _copy_matrix(current)
            return outputs

    def target_state_series(
        self,
        scenario_id: str,
        coefficients: acb_mat,
    ) -> dict[int, acb_mat]:
        validate_registered_permit(self.permit)
        scenario = self.scenarios.get(scenario_id)
        observations = _observation_steps(self.delta)
        with ball_precision(self.bits):
            current = certified_target_input_basis() * coefficients
            outputs: dict[int, acb_mat] = {}
            for step in range(max(observations)):
                time = step * self.delta
                mass = _interval_value(scenario["mass"], time)
                potential = _potential_parameters(scenario["potential"], time)
                amplitude, phase_pi = (
                    (Fraction(0), Fraction(0))
                    if potential is None
                    else potential
                )
                key = mass, amplitude, phase_pi
                if amplitude == 0:
                    current = certified_free_target_step(
                        current,
                        cutoff=TARGET_R_CUTOFF,
                        mass=mass,
                        duration=self.delta,
                    )
                else:
                    propagator = self._target_propagators.get(key)
                    if propagator is None:
                        hamiltonian = build_certified_target_hamiltonian(
                            cutoff=TARGET_R_CUTOFF,
                            mass=mass,
                            potential_amplitude=amplitude,
                            potential_phase_pi=phase_pi,
                        )
                        propagator = (
                            acb(0, -arb_exact(self.delta)) * hamiltonian
                        ).exp()
                        self._target_propagators[key] = propagator
                    current = propagator * current
                outputs[step + 1] = _copy_matrix(current)
            return outputs
