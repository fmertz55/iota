"""Exact, sealed runner for the role-succession falsification.

Importing this module is outcome-free.  The registered dynamics are reached
only through :func:`evaluate_candidate_exact_orbit`, and the family search
requires an evaluator argument explicitly so tests can use synthetic outcomes.
"""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from .detector import DetectorResult, LayerAssessment, assess_layer, role_at
from .dynamics import (
    canonical_initial_state,
    normalize_rows,
    reflect_state,
    require_state,
    step,
    translate_state,
)
from .manifest import candidate_sha256, canonical_json, validate_candidate_manifest
from .protocol import (
    BASE_CONTRACT_VERSION,
    CANONICAL_ORIGIN,
    CANDIDATE_COUNT,
    CAUSAL_ENDPOINT_LAG,
    DATA_CLASS,
    DETECTOR_ID,
    DYNAMIC_CANDIDATE_COUNT,
    EMBEDDING_CYCLE_SIZES,
    FORMATION_HORIZON,
    GRAMMAR_ID,
    INPUT_PORTS,
    MAX_LAYERS_PER_CANDIDATE,
    PARENT_EXACT_RESULT_REF,
    PARENT_EXACT_RESULT_SHA256,
    PRIMARY_CONE_SATURATION_LAYER,
    PRIMARY_CYCLE_SIZE,
    PROTOCOL_VERSION,
    REGISTERED_WORKER_PROCESSES,
    RESULT_ENDPOINT,
    RUN_ID,
    SEARCH_ID,
    SHELL_SIZES,
    SIGNATURE_ORDER,
)
from .search import candidate_id, enumerate_rule_rows


TRACE_PREFIX = b"IOTA-MIR-ROLE-SUCCESSION-TRACE-V1\x00"
SYMMETRY_AUDIT_LAST_LAYER = FORMATION_HORIZON + CAUSAL_ENDPOINT_LAG
TERMINAL_STATUSES = frozenset(
    {
        "exact_pass_on_fixed_orbit",
        "recurrence_excluded_on_fixed_orbit",
        "resource_censored_before_recurrence",
    }
)


class RoleSuccessionRunError(ValueError):
    """Raised when a trace, audit, or result ledger violates the contract."""


# Compatibility-friendly short name for callers that treat this as a ledger
# module.  Both names denote the same exception class.
RoleSuccessionLedgerError = RoleSuccessionRunError


@dataclass(frozen=True)
class ExactOrbitOutcome:
    status: str
    t_proto: Optional[int]
    last_assessed_layer: int
    first_role: Optional[tuple[int, int]]
    first_successor: Optional[tuple[int, int, int]]
    first_intervention_eligible: Optional[tuple[int, int, int]]
    first_complete_pass: Optional[tuple[int, int, int, int, int, int, int]]
    recurrence: Optional[tuple[int, int, int, int, int]]
    trace_sha256: str


@dataclass(frozen=True)
class TransitionSymmetryAudit:
    translation_offsets: tuple[int, ...]
    last_audited_layer: int
    translation_covariance_exact: bool
    reflection_covariance_exact: bool
    reflected_production_rows: tuple[str, ...]


@dataclass(frozen=True)
class SizeControlOutcome:
    cycle_size: int
    evaluated_through_layer: int
    first_complete_pass: Optional[tuple[int, int, int, int, int]]
    matches_primary_witness: bool
    pre_wrap_agreement_required: bool
    exact_pre_wrap_agreement: Optional[bool]


@dataclass(frozen=True)
class CandidateEvaluation:
    orbit: ExactOrbitOutcome
    symmetry_audit: TransitionSymmetryAudit
    size_controls: tuple[SizeControlOutcome, ...]


JointState = tuple[int, int]
Transition = Callable[[JointState], JointState]
Assessor = Callable[[JointState, int], LayerAssessment]
TraceHook = Callable[[JointState, JointState, int], None]
CandidateEvaluator = Callable[
    [dict[str, Any], tuple[str, ...]],
    CandidateEvaluation,
]


def _registered_evaluation_payload(
    payload: tuple[dict[str, Any], tuple[str, ...]],
) -> CandidateEvaluation:
    """Top-level spawn-safe adapter for one registered candidate."""

    candidate, rows = payload
    return evaluate_candidate_exact_orbit(candidate, rows)


def _require_digest(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise RoleSuccessionRunError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RoleSuccessionRunError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise RoleSuccessionRunError(f"non-finite JSON number {value!r} is forbidden")


def load_canonical_json_bytes(data: bytes, source: str = "<bytes>") -> dict[str, Any]:
    try:
        text = data.decode("ascii")
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RoleSuccessionRunError(f"{source}: {exc}") from exc
    if type(value) is not dict:
        raise RoleSuccessionRunError(f"{source}: root must be an object")
    if text != canonical_json(value) + "\n":
        raise RoleSuccessionRunError(f"{source}: file is not byte-canonical JSON")
    return value


def load_canonical_json(path: Path) -> dict[str, Any]:
    try:
        return load_canonical_json_bytes(path.read_bytes(), str(path))
    except OSError as exc:
        raise RoleSuccessionRunError(f"{path}: {exc}") from exc


def require_binding(value: Any, label: str) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"path", "sha256"}:
        raise RoleSuccessionRunError(f"{label} binding shape mismatch")
    if type(value["path"]) is not str or not value["path"]:
        raise RoleSuccessionRunError(f"{label} binding path is invalid")
    _require_digest(value["sha256"], f"{label} binding hash")
    return value


def strict_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without accepting Boolean/integer substitution."""

    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return set(left) == set(right) and all(
            strict_json_equal(left[key], right[key]) for key in left
        )
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(
            strict_json_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def wolfram_rule_number(rows: Iterable[str]) -> int:
    production_rows = normalize_rows(rows)
    return sum(1 << int(signature, 2) for signature in production_rows)


def reflected_rows(rows: Iterable[str]) -> tuple[str, ...]:
    """Swap predecessor and successor incidence bits in every selected row."""

    production_rows = normalize_rows(rows)
    reflected = {signature[::-1] for signature in production_rows}
    return tuple(signature for signature in SIGNATURE_ORDER if signature in reflected)


def candidate_trace_domain(candidate: dict[str, Any]) -> bytes:
    identifier = candidate.get("candidate_id")
    if type(identifier) is not str or not identifier:
        raise RoleSuccessionRunError("candidate id is invalid for trace binding")
    try:
        return f"{SEARCH_ID}\0{identifier}\0{candidate_sha256(candidate)}".encode("ascii")
    except UnicodeEncodeError as exc:
        raise RoleSuccessionRunError("candidate id must be ASCII") from exc


def _new_trace_digest(domain: bytes) -> "hashlib._Hash":
    if type(domain) is not bytes or not domain:
        raise RoleSuccessionRunError("trace domain must be nonempty bytes")
    digest = hashlib.sha256()
    digest.update(TRACE_PREFIX)
    digest.update(len(domain).to_bytes(8, "big"))
    digest.update(domain)
    return digest


def _update_trace_digest(
    digest: "hashlib._Hash",
    layer: int,
    state: JointState,
    *,
    cycle_size: int,
) -> None:
    seeded_state, baseline_state = state
    require_state(seeded_state, cycle_size)
    require_state(baseline_state, cycle_size)
    if type(layer) is not int or layer < 0:
        raise RoleSuccessionRunError("trace layer must be a nonnegative integer")
    layer_bytes = str(layer).encode("ascii")
    width = (cycle_size + 7) // 8
    digest.update(len(layer_bytes).to_bytes(8, "big"))
    digest.update(layer_bytes)
    digest.update(seeded_state.to_bytes(width, "big"))
    digest.update(baseline_state.to_bytes(width, "big"))


def _require_detector_result(result: DetectorResult, layer: int, cycle_size: int) -> None:
    if type(result) is not DetectorResult or type(result.passed) is not bool:
        raise RoleSuccessionRunError("assessor returned an invalid detector result")
    fields = (
        result.t_proto,
        result.anchor,
        result.successor_anchor,
        result.sham_future,
        result.breaking_future,
    )
    if not result.passed:
        if any(value is not None for value in fields):
            raise RoleSuccessionRunError("nonpassing detector result contains outcome fields")
        return
    if any(value is None for value in fields):
        raise RoleSuccessionRunError("passing detector result is incomplete")
    if type(result.t_proto) is not int or result.t_proto != layer:
        raise RoleSuccessionRunError("passing detector layer differs from scan layer")
    for value in (result.anchor, result.successor_anchor):
        if type(value) is not int or not 0 <= value < cycle_size:
            raise RoleSuccessionRunError("passing detector anchor is invalid")
    if (
        type(result.sham_future) is not int
        or type(result.breaking_future) is not int
        or result.sham_future not in (0, 1)
        or result.breaking_future not in (0, 1)
        or result.sham_future == result.breaking_future
    ):
        raise RoleSuccessionRunError("passing detector endpoints are invalid")


def trace_joint_orbit(
    initial_state: JointState,
    transition: Transition,
    assessor: Assessor,
    *,
    saturation_layer: int,
    max_layers: int,
    trace_domain: bytes,
    cycle_size: int = PRIMARY_CYCLE_SIZE,
    trace_hook: Optional[TraceHook] = None,
) -> ExactOrbitOutcome:
    """Stream a deterministic joint orbit to pass, recurrence, or fixed cap.

    The detector is evaluated before the recurrence check at every layer.  The
    power-of-two checkpoint equality is an equality of both full states and is
    enabled only after the centered cone has saturated.
    """

    if type(saturation_layer) is not int or saturation_layer < 1:
        raise RoleSuccessionRunError("saturation layer must be positive")
    if type(max_layers) is not int or max_layers < saturation_layer:
        raise RoleSuccessionRunError("resource ceiling must reach saturation")
    if type(initial_state) is not tuple or len(initial_state) != 2:
        raise RoleSuccessionRunError("joint state must be a seeded/comparator pair")
    current = (require_state(initial_state[0], cycle_size), require_state(initial_state[1], cycle_size))
    digest = _new_trace_digest(trace_domain)
    _update_trace_digest(digest, 0, current, cycle_size=cycle_size)

    checkpoint: Optional[JointState] = None
    checkpoint_layer: Optional[int] = None
    checkpoint_power = 1
    checkpoint_distance = 0
    first_role: Optional[tuple[int, int]] = None
    first_successor: Optional[tuple[int, int, int]] = None
    first_eligible: Optional[tuple[int, int, int]] = None

    for layer in range(1, max_layers + 1):
        previous = current
        candidate_state = transition(previous)
        if type(candidate_state) is not tuple or len(candidate_state) != 2:
            raise RoleSuccessionRunError("transition returned an invalid joint state")
        current = (
            require_state(candidate_state[0], cycle_size),
            require_state(candidate_state[1], cycle_size),
        )
        if trace_hook is not None:
            trace_hook(previous, current, layer)
        _update_trace_digest(digest, layer, current, cycle_size=cycle_size)
        assessment = assessor(current, layer)
        if type(assessment) is not LayerAssessment:
            raise RoleSuccessionRunError("assessor returned the wrong result type")
        _require_detector_result(assessment.detector_result, layer, cycle_size)

        if assessment.first_role_anchor is not None and first_role is None:
            anchor = assessment.first_role_anchor
            if type(anchor) is not int or not 0 <= anchor < cycle_size:
                raise RoleSuccessionRunError("role witness anchor is invalid")
            first_role = (layer, anchor)
        if assessment.first_successor is not None and first_successor is None:
            anchor, successor = assessment.first_successor
            if any(type(v) is not int or not 0 <= v < cycle_size for v in (anchor, successor)):
                raise RoleSuccessionRunError("successor witness is invalid")
            first_successor = (layer, anchor, successor)
        if assessment.first_intervention_eligible is not None and first_eligible is None:
            anchor, successor = assessment.first_intervention_eligible
            if any(type(v) is not int or not 0 <= v < cycle_size for v in (anchor, successor)):
                raise RoleSuccessionRunError("intervention witness is invalid")
            first_eligible = (layer, anchor, successor)

        result = assessment.detector_result
        if result.passed:
            return ExactOrbitOutcome(
                "exact_pass_on_fixed_orbit",
                layer,
                layer,
                first_role,
                first_successor,
                first_eligible,
                (
                    layer,
                    int(result.anchor),
                    int(result.successor_anchor),
                    int(result.sham_future),
                    int(result.breaking_future),
                    current[0],
                    current[1],
                ),
                None,
                digest.hexdigest(),
            )

        if layer == saturation_layer:
            checkpoint = current
            checkpoint_layer = layer
            checkpoint_power = 1
            checkpoint_distance = 0
        elif layer > saturation_layer:
            if checkpoint is None or checkpoint_layer is None:
                raise RoleSuccessionRunError("recurrence checkpoint is missing")
            checkpoint_distance += 1
            if current == checkpoint:
                return ExactOrbitOutcome(
                    "recurrence_excluded_on_fixed_orbit",
                    None,
                    layer,
                    first_role,
                    first_successor,
                    first_eligible,
                    None,
                    (
                        checkpoint_layer,
                        layer,
                        checkpoint_distance,
                        current[0],
                        current[1],
                    ),
                    digest.hexdigest(),
                )
            if checkpoint_distance == checkpoint_power:
                checkpoint = current
                checkpoint_layer = layer
                checkpoint_power *= 2
                checkpoint_distance = 0

    return ExactOrbitOutcome(
        "resource_censored_before_recurrence",
        None,
        max_layers,
        first_role,
        first_successor,
        first_eligible,
        None,
        None,
        digest.hexdigest(),
    )


def _audit_natural_transition(
    previous: JointState,
    current: JointState,
    layer: int,
    rows: tuple[str, ...],
) -> None:
    if layer > SYMMETRY_AUDIT_LAST_LAYER:
        return
    reflected = reflected_rows(rows)
    for prior_state, next_state in zip(previous, current):
        for offset in range(PRIMARY_CYCLE_SIZE):
            shifted_prior = translate_state(prior_state, offset, PRIMARY_CYCLE_SIZE)
            shifted_next = step(shifted_prior, rows, PRIMARY_CYCLE_SIZE)
            expected = translate_state(next_state, offset, PRIMARY_CYCLE_SIZE)
            if shifted_next != expected:
                raise RoleSuccessionRunError("transition violates exact translation covariance")
        reflected_prior = reflect_state(prior_state, PRIMARY_CYCLE_SIZE)
        reflected_next = step(reflected_prior, reflected, PRIMARY_CYCLE_SIZE)
        if reflected_next != reflect_state(next_state, PRIMARY_CYCLE_SIZE):
            raise RoleSuccessionRunError("transition violates exact reflection covariance")


def _signed_offset(locus: int, origin: int, cycle_size: int) -> int:
    offset = (locus - origin) % cycle_size
    return offset if offset <= cycle_size // 2 else offset - cycle_size


def _size_pass_tuple(result: DetectorResult, cycle_size: int) -> tuple[int, int, int, int, int]:
    if not result.passed:
        raise RoleSuccessionRunError("cannot encode a nonpassing size result")
    anchor = int(result.anchor)
    successor = int(result.successor_anchor)
    displacement = (successor - anchor) % cycle_size
    return (
        int(result.t_proto),
        _signed_offset(anchor, CANONICAL_ORIGIN, cycle_size),
        displacement,
        int(result.sham_future),
        int(result.breaking_future),
    )


def _primary_pass_tuple(outcome: ExactOrbitOutcome) -> tuple[int, int, int, int, int]:
    if outcome.first_complete_pass is None:
        raise RoleSuccessionRunError("primary passing outcome lacks a witness")
    layer, anchor, successor, sham, breaking, _, _ = outcome.first_complete_pass
    return (
        layer,
        _signed_offset(anchor, CANONICAL_ORIGIN, PRIMARY_CYCLE_SIZE),
        (successor - anchor) % PRIMARY_CYCLE_SIZE,
        sham,
        breaking,
    )


def _evaluate_size_control(
    rows: tuple[str, ...],
    primary: ExactOrbitOutcome,
    cycle_size: int,
) -> SizeControlOutcome:
    if primary.t_proto is None:
        raise RoleSuccessionRunError("size controls are conditional on a primary pass")
    seeded = canonical_initial_state(CANONICAL_ORIGIN, cycle_size)
    baseline = 0
    first_pass: Optional[tuple[int, int, int, int, int]] = None
    for layer in range(1, primary.t_proto + 1):
        seeded = step(seeded, rows, cycle_size)
        baseline = step(baseline, rows, cycle_size)
        result = assess_layer(
            seeded,
            baseline,
            rows,
            layer=layer,
            origin=CANONICAL_ORIGIN,
            cycle_size=cycle_size,
        ).detector_result
        if result.passed and first_pass is None:
            first_pass = _size_pass_tuple(result, cycle_size)
    primary_tuple = _primary_pass_tuple(primary)
    matches = first_pass == primary_tuple
    required = primary.t_proto <= FORMATION_HORIZON
    if required and not matches:
        raise RoleSuccessionRunError(
            f"C{cycle_size} failed the mandatory exact pre-wrap embedding crosscheck"
        )
    return SizeControlOutcome(
        cycle_size,
        primary.t_proto,
        first_pass,
        matches,
        required,
        matches if required else None,
    )


def evaluate_candidate_exact_orbit(
    candidate: dict[str, Any],
    rows: tuple[str, ...],
) -> CandidateEvaluation:
    """Evaluate one registered nonempty rule under the fully frozen protocol."""

    production_rows = tuple(signature for signature in SIGNATURE_ORDER if signature in normalize_rows(rows))
    if not production_rows:
        raise RoleSuccessionRunError("the zero-row candidate is analytically excluded")
    if candidate.get("candidate_id") != candidate_id(production_rows):
        raise RoleSuccessionRunError("candidate identity and production rows differ")
    initial_seeded = canonical_initial_state(CANONICAL_ORIGIN, PRIMARY_CYCLE_SIZE)
    if any(
        role_at(initial_seeded, 0, anchor, PRIMARY_CYCLE_SIZE)
        for anchor in range(PRIMARY_CYCLE_SIZE)
    ):
        raise RoleSuccessionRunError("registered initial state already contains the role")

    def transition(state: JointState) -> JointState:
        return (
            step(state[0], production_rows, PRIMARY_CYCLE_SIZE),
            step(state[1], production_rows, PRIMARY_CYCLE_SIZE),
        )

    def assessor(state: JointState, layer: int) -> LayerAssessment:
        return assess_layer(
            state[0],
            state[1],
            production_rows,
            layer=layer,
            origin=CANONICAL_ORIGIN,
            cycle_size=PRIMARY_CYCLE_SIZE,
        )

    orbit = trace_joint_orbit(
        (initial_seeded, 0),
        transition,
        assessor,
        saturation_layer=PRIMARY_CONE_SATURATION_LAYER,
        max_layers=MAX_LAYERS_PER_CANDIDATE,
        trace_domain=candidate_trace_domain(candidate),
        cycle_size=PRIMARY_CYCLE_SIZE,
        trace_hook=lambda previous, current, layer: _audit_natural_transition(
            previous, current, layer, production_rows
        ),
    )
    audit = TransitionSymmetryAudit(
        tuple(range(PRIMARY_CYCLE_SIZE)),
        min(orbit.last_assessed_layer, SYMMETRY_AUDIT_LAST_LAYER),
        True,
        True,
        reflected_rows(production_rows),
    )
    controls: tuple[SizeControlOutcome, ...] = ()
    if orbit.status == "exact_pass_on_fixed_orbit":
        controls = tuple(
            _evaluate_size_control(production_rows, orbit, cycle_size)
            for cycle_size in EMBEDDING_CYCLE_SIZES
        )
    return CandidateEvaluation(orbit, audit, controls)


def _hex_state(state: int) -> str:
    require_state(state, PRIMARY_CYCLE_SIZE)
    return f"{state:0{PRIMARY_CYCLE_SIZE // 4}x}"


def _role_record(value: Optional[tuple[int, int]]) -> Optional[dict[str, int]]:
    if value is None:
        return None
    return {"layer": value[0], "anchor": value[1]}


def _successor_record(
    value: Optional[tuple[int, int, int]],
) -> Optional[dict[str, int]]:
    if value is None:
        return None
    return {"layer": value[0], "anchor": value[1], "successor_anchor": value[2]}


def _pass_record(
    value: Optional[tuple[int, int, int, int, int, int, int]],
) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    layer, anchor, successor, sham, breaking, seeded, baseline = value
    return {
        "layer": layer,
        "anchor": anchor,
        "signed_anchor": _signed_offset(anchor, CANONICAL_ORIGIN, PRIMARY_CYCLE_SIZE),
        "successor_anchor": successor,
        "successor_displacement": (successor - anchor) % PRIMARY_CYCLE_SIZE,
        "sham_future": sham,
        "breaking_future": breaking,
        "seeded_state_hex": _hex_state(seeded),
        "baseline_state_hex": _hex_state(baseline),
    }


def _bounded_witness(value: Optional[tuple[int, ...]]) -> Optional[tuple[int, ...]]:
    return value if value is not None and value[0] <= FORMATION_HORIZON else None


def _pre_wrap_record(outcome: ExactOrbitOutcome) -> dict[str, Any]:
    role = _bounded_witness(outcome.first_role)
    successor = _bounded_witness(outcome.first_successor)
    eligible = _bounded_witness(outcome.first_intervention_eligible)
    complete = _bounded_witness(outcome.first_complete_pass)
    return {
        "formation_horizon": FORMATION_HORIZON,
        "role_by_H29": role is not None,
        "successor_by_H29": successor is not None,
        "intervention_eligible_by_H29": eligible is not None,
        "pass_by_H29": complete is not None,
        "first_role": _role_record(role),  # type: ignore[arg-type]
        "first_successor": _successor_record(successor),  # type: ignore[arg-type]
        "first_intervention_eligible": _successor_record(eligible),  # type: ignore[arg-type]
        "first_complete_pass": _pass_record(complete),  # type: ignore[arg-type]
    }


def _recurrence_record(
    value: Optional[tuple[int, int, int, int, int]],
) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    checkpoint, repeat, period, seeded, baseline = value
    state = {
        "seeded_state_hex": _hex_state(seeded),
        "baseline_state_hex": _hex_state(baseline),
    }
    return {
        "cone_saturation_layer": PRIMARY_CONE_SATURATION_LAYER,
        "checkpoint_layer": checkpoint,
        "repeat_layer": repeat,
        "period": period,
        "checkpoint_state": dict(state),
        "repeat_state": dict(state),
        "exact_full_state_equality": True,
    }


def _size_control_record(value: SizeControlOutcome) -> dict[str, Any]:
    witness = value.first_complete_pass
    return {
        "cycle_size": value.cycle_size,
        "evaluated_through_layer": value.evaluated_through_layer,
        "first_complete_pass": None
        if witness is None
        else {
            "layer": witness[0],
            "signed_anchor": witness[1],
            "successor_displacement": witness[2],
            "sham_future": witness[3],
            "breaking_future": witness[4],
        },
        "matches_primary_witness": value.matches_primary_witness,
        "pre_wrap_agreement_required": value.pre_wrap_agreement_required,
        "exact_pre_wrap_agreement": value.exact_pre_wrap_agreement,
    }


def _dynamic_candidate_record(
    candidate: dict[str, Any],
    rows: tuple[str, ...],
    evaluation: CandidateEvaluation,
) -> dict[str, Any]:
    if type(evaluation) is not CandidateEvaluation:
        raise RoleSuccessionRunError("candidate evaluator returned the wrong result type")
    outcome = evaluation.orbit
    if outcome.status not in TERMINAL_STATUSES:
        raise RoleSuccessionRunError("candidate evaluator returned an unknown terminal status")
    _require_digest(outcome.trace_sha256, "candidate trace")
    if evaluation.symmetry_audit.translation_covariance_exact is not True:
        raise RoleSuccessionRunError("candidate translation audit did not pass exactly")
    if evaluation.symmetry_audit.reflection_covariance_exact is not True:
        raise RoleSuccessionRunError("candidate reflection audit did not pass exactly")
    if (
        any(type(offset) is not int for offset in evaluation.symmetry_audit.translation_offsets)
        or evaluation.symmetry_audit.translation_offsets
        != tuple(range(PRIMARY_CYCLE_SIZE))
    ):
        raise RoleSuccessionRunError("candidate translation audit allocation mismatch")
    if (
        type(evaluation.symmetry_audit.last_audited_layer) is not int
        or evaluation.symmetry_audit.last_audited_layer
        != min(outcome.last_assessed_layer, SYMMETRY_AUDIT_LAST_LAYER)
    ):
        raise RoleSuccessionRunError("candidate symmetry audit horizon mismatch")
    if evaluation.symmetry_audit.reflected_production_rows != reflected_rows(rows):
        raise RoleSuccessionRunError("candidate reflected-row audit mismatch")

    if outcome.status == "exact_pass_on_fixed_orbit":
        if outcome.t_proto is None or outcome.first_complete_pass is None or outcome.recurrence is not None:
            raise RoleSuccessionRunError("passing outcome has inconsistent terminal fields")
        if outcome.last_assessed_layer != outcome.t_proto:
            raise RoleSuccessionRunError("passing outcome continued past first passage")
        if tuple(control.cycle_size for control in evaluation.size_controls) != EMBEDDING_CYCLE_SIZES:
            raise RoleSuccessionRunError("primary passer lacks both frozen size controls")
        required = outcome.t_proto <= FORMATION_HORIZON
        if any(control.pre_wrap_agreement_required is not required for control in evaluation.size_controls):
            raise RoleSuccessionRunError("size-control pre-wrap classification mismatch")
        if required and any(control.exact_pre_wrap_agreement is not True for control in evaluation.size_controls):
            raise RoleSuccessionRunError("mandatory pre-wrap size agreement failed")
    elif outcome.status == "recurrence_excluded_on_fixed_orbit":
        if outcome.t_proto is not None or outcome.first_complete_pass is not None or outcome.recurrence is None:
            raise RoleSuccessionRunError("recurrence outcome has inconsistent terminal fields")
        if evaluation.size_controls:
            raise RoleSuccessionRunError("nonpassing candidate contains conditional size controls")
    else:
        if outcome.t_proto is not None or outcome.first_complete_pass is not None or outcome.recurrence is not None:
            raise RoleSuccessionRunError("resource-censored outcome has terminal proof fields")
        if evaluation.size_controls:
            raise RoleSuccessionRunError("nonpassing candidate contains conditional size controls")

    pre_wrap = _pre_wrap_record(outcome)
    bounded_status = "pass_by_H29" if pre_wrap["pass_by_H29"] else "right_censored_T_proto_gt_29"
    localized = bool(
        pre_wrap["pass_by_H29"]
        and all(control.exact_pre_wrap_agreement is True for control in evaluation.size_controls)
    )
    record = {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate_sha256(candidate),
        "normalized_n_p": 2,
        "atomic_n_l": len(rows),
        "production_rows": list(rows),
        "wolfram_rule_number": wolfram_rule_number(rows),
        "evaluation_status": outcome.status,
        "bounded_status": bounded_status,
        "pass_by_H29": pre_wrap["pass_by_H29"],
        "t_proto_exact": outcome.t_proto,
        "last_assessed_layer": outcome.last_assessed_layer,
        "first_role": _role_record(outcome.first_role),
        "first_successor": _successor_record(outcome.first_successor),
        "first_intervention_eligible": _successor_record(outcome.first_intervention_eligible),
        "first_complete_pass": _pass_record(outcome.first_complete_pass),
        "pre_wrap_classification": pre_wrap,
        "recurrence": _recurrence_record(outcome.recurrence),
        "resource_limit": MAX_LAYERS_PER_CANDIDATE
        if outcome.status == "resource_censored_before_recurrence"
        else None,
        "trace_sha256": outcome.trace_sha256,
        "transition_symmetry_audit": {
            "translation_offsets": list(evaluation.symmetry_audit.translation_offsets),
            "last_audited_layer": evaluation.symmetry_audit.last_audited_layer,
            "translation_covariance_exact": True,
            "reflection_covariance_exact": True,
            "reflected_production_rows": list(
                evaluation.symmetry_audit.reflected_production_rows
            ),
        },
        "cross_size_controls": [
            _size_control_record(control) for control in evaluation.size_controls
        ],
        "localized_interpretation": localized,
    }
    _validate_size_controls(record)
    return record


def _excluded_candidate_record(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate_sha256(candidate),
        "normalized_n_p": 2,
        "atomic_n_l": 0,
        "production_rows": [],
        "wolfram_rule_number": 0,
        "evaluation_status": "analytically_excluded",
        "bounded_status": "not_applicable",
        "pass_by_H29": False,
        "t_proto_exact": None,
        "last_assessed_layer": None,
        "first_role": None,
        "first_successor": None,
        "first_intervention_eligible": None,
        "first_complete_pass": None,
        "pre_wrap_classification": None,
        "recurrence": None,
        "resource_limit": None,
        "trace_sha256": None,
        "transition_symmetry_audit": None,
        "cross_size_controls": [],
        "localized_interpretation": False,
        "exclusion_reason": candidate.get("exclusion_reason"),
    }


def _summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    dynamic = results[1:]
    role_count = sum(row["pre_wrap_classification"]["role_by_H29"] for row in dynamic)
    successor_count = sum(
        row["pre_wrap_classification"]["successor_by_H29"] for row in dynamic
    )
    eligible_count = sum(
        row["pre_wrap_classification"]["intervention_eligible_by_H29"]
        for row in dynamic
    )
    pass_count = sum(row["pass_by_H29"] for row in dynamic)
    exact_passers = [row for row in dynamic if row["evaluation_status"] == "exact_pass_on_fixed_orbit"]
    resource = [row for row in dynamic if row["evaluation_status"] == "resource_censored_before_recurrence"]
    localized = [row["candidate_id"] for row in dynamic if row["localized_interpretation"]]
    finite_ring = [
        row["candidate_id"]
        for row in exact_passers
        if type(row["t_proto_exact"]) is int and row["t_proto_exact"] > FORMATION_HORIZON
    ]

    if successor_count == 0:
        mechanism = "pre_wrap_succession_repair_falsified"
    elif pass_count == 0:
        mechanism = "succession_bottleneck_moved_without_pre_wrap_proto_object"
    else:
        mechanism = "one_or_more_pre_wrap_successors"
    construction = (
        "localized_development_falsification_survived"
        if localized
        else "no_localized_pre_wrap_construction"
    )
    if exact_passers:
        completion = (
            "complete_all_candidate_endpoints_resolved"
            if not resource
            else "existential_pass_with_resource_censoring"
        )
        exact_conclusion = "one_or_more_exact_passes"
    elif resource:
        completion = "incomplete_resource_censored"
        exact_conclusion = "resource_censored_incomplete"
    else:
        completion = "complete_all_candidate_endpoints_resolved"
        exact_conclusion = "all_dynamic_candidates_recurrence_excluded"

    winners: list[str] = []
    minimum_law_ranking_status = "no_exact_passer"
    if exact_passers:
        best_law = min(row["atomic_n_l"] for row in exact_passers)
        lower_resource = any(
            row["evaluation_status"] == "resource_censored_before_recurrence"
            and row["atomic_n_l"] < best_law
            for row in dynamic
        )
        if lower_resource:
            minimum_law_ranking_status = "blocked_by_lower_shell_resource_censoring"
        else:
            shell = [row for row in exact_passers if row["atomic_n_l"] == best_law]
            best_time = min(row["t_proto_exact"] for row in shell)
            winners = [
                row["candidate_id"]
                for row in shell
                if row["t_proto_exact"] == best_time
            ]
            minimum_law_ranking_status = "resolved_within_frozen_family"

    return {
        "completion_status": completion,
        "exact_family_conclusion": exact_conclusion,
        "pre_wrap_mechanism_conclusion": mechanism,
        "pre_wrap_construction_conclusion": construction,
        "pre_wrap_stage_counts": {
            "role": role_count,
            "successor": successor_count,
            "intervention_eligible": eligible_count,
            "complete_pass": pass_count,
        },
        "exact_pass_candidate_ids": [row["candidate_id"] for row in exact_passers],
        "localized_candidate_ids": localized,
        "finite_ring_exposed_candidate_ids": finite_ring,
        "minimum_law_ranking_status": minimum_law_ranking_status,
        "minimum_law_winner_candidate_ids": winners,
    }


def run_development_search(
    candidates: Iterable[dict[str, Any]],
    evaluator: CandidateEvaluator,
    *,
    worker_processes: int = 1,
) -> dict[str, Any]:
    """Process the complete family without shell stopping.

    Generic and synthetic evaluators remain sequential.  The only parallel
    mode is the frozen four-process registered evaluator; results are fully
    collected in canonical candidate order before any ledger is built.
    """

    ordered = tuple(candidates)
    validate_candidate_manifest(ordered)
    expected_rows = enumerate_rule_rows()
    if len(ordered) != CANDIDATE_COUNT or len(expected_rows) != CANDIDATE_COUNT:
        raise RoleSuccessionRunError("candidate allocation is not the complete 256-rule family")
    row_family = set(expected_rows)
    if any(reflected_rows(rows) not in row_family for rows in expected_rows):
        raise RoleSuccessionRunError("candidate enumerator is not reflection closed")
    if type(worker_processes) is not int or worker_processes not in (
        1,
        REGISTERED_WORKER_PROCESSES,
    ):
        raise RoleSuccessionRunError("candidate worker allocation is not frozen")
    parallel_evaluations: tuple[CandidateEvaluation, ...] = ()
    if worker_processes == REGISTERED_WORKER_PROCESSES:
        if evaluator is not evaluate_candidate_exact_orbit:
            raise RoleSuccessionRunError(
                "parallel execution is restricted to the registered evaluator"
            )
        payloads = tuple(zip(ordered[1:], expected_rows[1:]))
        try:
            with ProcessPoolExecutor(
                max_workers=REGISTERED_WORKER_PROCESSES,
                mp_context=get_context("spawn"),
            ) as executor:
                parallel_evaluations = tuple(
                    executor.map(
                        _registered_evaluation_payload,
                        payloads,
                        chunksize=1,
                    )
                )
        except RoleSuccessionRunError:
            raise
        except Exception as exc:
            raise RoleSuccessionRunError(
                "registered candidate worker pool failed before serialization"
            ) from exc
        if len(parallel_evaluations) != DYNAMIC_CANDIDATE_COUNT:
            raise RoleSuccessionRunError("candidate worker result allocation mismatch")
    parallel_index = 0
    results: list[dict[str, Any]] = []
    for index, (candidate, rows) in enumerate(zip(ordered, expected_rows)):
        if candidate.get("candidate_id") != candidate_id(rows):
            raise RoleSuccessionRunError("candidate order changed before evaluation")
        if index == 0:
            results.append(_excluded_candidate_record(candidate))
            continue
        if parallel_evaluations:
            evaluation = parallel_evaluations[parallel_index]
            parallel_index += 1
        else:
            evaluation = evaluator(candidate, rows)
        results.append(_dynamic_candidate_record(candidate, rows, evaluation))
    if len(results) != CANDIDATE_COUNT:
        raise RoleSuccessionRunError("family search did not produce every candidate record")
    return {
        "all_nonempty_candidates_processed": True,
        "shell_stopping_used": False,
        "candidate_results": results,
        **_summarize_results(results),
    }


# Name mirrors the earlier development runner while preserving the new exact
# continuation semantics.
run_bounded_development_search = run_development_search


LEDGER_KEYS = {
    "base_contract_version",
    "protocol_version",
    "search_id",
    "run_id",
    "grammar_id",
    "detector",
    "data_class",
    "endpoint",
    "primary_cycle_size",
    "embedding_cycle_sizes",
    "canonical_origin",
    "formation_horizon",
    "causal_endpoint_lag",
    "cone_saturation_layer",
    "max_layers_per_candidate",
    "primitive_capacity",
    "candidate_allocation",
    "trace_digest_encoding",
    "open_manifest",
    "outcome_seal",
    "candidate_manifest",
    "result_schema",
    "parent_exact_result",
    "global_minimality_claimed",
    "alternative_grammar_excluded",
    "all_nonempty_candidates_processed",
    "shell_stopping_used",
    "completion_status",
    "exact_family_conclusion",
    "pre_wrap_mechanism_conclusion",
    "pre_wrap_construction_conclusion",
    "pre_wrap_stage_counts",
    "exact_pass_candidate_ids",
    "localized_candidate_ids",
    "finite_ring_exposed_candidate_ids",
    "minimum_law_ranking_status",
    "minimum_law_winner_candidate_ids",
    "candidate_results",
}


def build_result_ledger(
    *,
    candidates: Iterable[dict[str, Any]],
    evaluator: CandidateEvaluator,
    open_manifest_binding: dict[str, str],
    outcome_seal_binding: dict[str, str],
    candidate_manifest_binding: dict[str, str],
    result_schema_binding: dict[str, str],
    parent_exact_result_binding: dict[str, str],
    worker_processes: int = 1,
) -> dict[str, Any]:
    for label, binding in (
        ("open_manifest", open_manifest_binding),
        ("outcome_seal", outcome_seal_binding),
        ("candidate_manifest", candidate_manifest_binding),
        ("result_schema", result_schema_binding),
        ("parent_exact_result", parent_exact_result_binding),
    ):
        require_binding(binding, label)
    expected_parent = {
        "path": PARENT_EXACT_RESULT_REF,
        "sha256": PARENT_EXACT_RESULT_SHA256,
    }
    if not strict_json_equal(parent_exact_result_binding, expected_parent):
        raise RoleSuccessionRunError("parent exact-result binding mismatch")
    search = run_development_search(
        candidates,
        evaluator,
        worker_processes=worker_processes,
    )
    ledger = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": RUN_ID,
        "grammar_id": GRAMMAR_ID,
        "detector": DETECTOR_ID,
        "data_class": DATA_CLASS,
        "endpoint": RESULT_ENDPOINT,
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "embedding_cycle_sizes": list(EMBEDDING_CYCLE_SIZES),
        "canonical_origin": CANONICAL_ORIGIN,
        "formation_horizon": FORMATION_HORIZON,
        "causal_endpoint_lag": CAUSAL_ENDPOINT_LAG,
        "cone_saturation_layer": PRIMARY_CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "primitive_capacity": {
            "normalized_n_p": 2,
            "input_ports": list(INPUT_PORTS),
            "relation_incidence_reads_per_site": 2,
            "local_signature_fan_in": 3,
            "truth_table_row_capacity": 8,
            "scheduler": "synchronous_atomic_layer",
            "seed": "one_event_at_origin_0",
            "comparator": "all_zero_evolved_under_same_rule",
            "topology": "oriented_periodic_cycle",
        },
        "candidate_allocation": {
            "candidate_count": CANDIDATE_COUNT,
            "dynamic_candidate_count": DYNAMIC_CANDIDATE_COUNT,
            "shell_sizes": list(SHELL_SIZES),
            "enumeration_order": "increasing_N_L_then_lexicographic_signature_tuple",
        },
        "trace_digest_encoding": (
            "sha256_domain_separated_decimal_length_layer_fixed_width_seeded_"
            "fixed_width_comparator_including_layer_0"
        ),
        "open_manifest": dict(open_manifest_binding),
        "outcome_seal": dict(outcome_seal_binding),
        "candidate_manifest": dict(candidate_manifest_binding),
        "result_schema": dict(result_schema_binding),
        "parent_exact_result": dict(parent_exact_result_binding),
        "global_minimality_claimed": False,
        "alternative_grammar_excluded": False,
        **search,
    }
    validate_result_ledger(ledger, candidates)
    return ledger


def _validate_stage(value: Any, keys: set[str], last_layer: int) -> None:
    if value is None:
        return
    if type(value) is not dict or set(value) != keys:
        raise RoleSuccessionRunError("stage witness shape mismatch")
    if type(value["layer"]) is not int or not 1 <= value["layer"] <= last_layer:
        raise RoleSuccessionRunError("stage witness layer mismatch")
    for key in keys - {"layer"}:
        if type(value[key]) is not int or not 0 <= value[key] < PRIMARY_CYCLE_SIZE:
            raise RoleSuccessionRunError("stage witness anchor mismatch")
    if "successor_anchor" in keys:
        displacement = (value["successor_anchor"] - value["anchor"]) % PRIMARY_CYCLE_SIZE
        if displacement not in (0, 1):
            raise RoleSuccessionRunError("stage successor displacement mismatch")


def _valid_state_hex(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == PRIMARY_CYCLE_SIZE // 4
        and all(character in "0123456789abcdef" for character in value)
    )


PASS_KEYS = {
    "layer",
    "anchor",
    "signed_anchor",
    "successor_anchor",
    "successor_displacement",
    "sham_future",
    "breaking_future",
    "seeded_state_hex",
    "baseline_state_hex",
}


def _validate_pass(value: Any, last_layer: int) -> None:
    if type(value) is not dict or set(value) != PASS_KEYS:
        raise RoleSuccessionRunError("complete-pass witness shape mismatch")
    if type(value["layer"]) is not int or not 1 <= value["layer"] <= last_layer:
        raise RoleSuccessionRunError("complete-pass layer mismatch")
    for key in ("anchor", "successor_anchor"):
        if type(value[key]) is not int or not 0 <= value[key] < PRIMARY_CYCLE_SIZE:
            raise RoleSuccessionRunError("complete-pass anchor mismatch")
    expected_signed = _signed_offset(
        value["anchor"], CANONICAL_ORIGIN, PRIMARY_CYCLE_SIZE
    )
    expected_displacement = (
        value["successor_anchor"] - value["anchor"]
    ) % PRIMARY_CYCLE_SIZE
    if (
        type(value["signed_anchor"]) is not int
        or value["signed_anchor"] != expected_signed
        or type(value["successor_displacement"]) is not int
        or value["successor_displacement"] != expected_displacement
        or expected_displacement not in (0, 1)
    ):
        raise RoleSuccessionRunError("complete-pass geometry mismatch")
    if (
        type(value["sham_future"]) is not int
        or type(value["breaking_future"]) is not int
        or value["sham_future"] not in (0, 1)
        or value["breaking_future"] not in (0, 1)
        or value["sham_future"] == value["breaking_future"]
        or not _valid_state_hex(value["seeded_state_hex"])
        or not _valid_state_hex(value["baseline_state_hex"])
    ):
        raise RoleSuccessionRunError("complete-pass endpoint or state mismatch")


def _expected_pre_wrap(
    role: Any,
    successor: Any,
    eligible: Any,
    complete: Any,
) -> dict[str, Any]:
    def bounded(value: Any) -> Any:
        return (
            value
            if value is not None and value["layer"] <= FORMATION_HORIZON
            else None
        )

    role_pre = bounded(role)
    successor_pre = bounded(successor)
    eligible_pre = bounded(eligible)
    complete_pre = bounded(complete)
    return {
        "formation_horizon": FORMATION_HORIZON,
        "role_by_H29": role_pre is not None,
        "successor_by_H29": successor_pre is not None,
        "intervention_eligible_by_H29": eligible_pre is not None,
        "pass_by_H29": complete_pre is not None,
        "first_role": role_pre,
        "first_successor": successor_pre,
        "first_intervention_eligible": eligible_pre,
        "first_complete_pass": complete_pre,
    }


SIZE_CONTROL_KEYS = {
    "cycle_size",
    "evaluated_through_layer",
    "first_complete_pass",
    "matches_primary_witness",
    "pre_wrap_agreement_required",
    "exact_pre_wrap_agreement",
}
SIZE_PASS_KEYS = {
    "layer",
    "signed_anchor",
    "successor_displacement",
    "sham_future",
    "breaking_future",
}


def _validate_size_controls(record: dict[str, Any]) -> None:
    controls = record["cross_size_controls"]
    if type(controls) is not list:
        raise RoleSuccessionRunError("cross-size controls must be a list")
    if record["evaluation_status"] != "exact_pass_on_fixed_orbit":
        if controls:
            raise RoleSuccessionRunError("nonpass contains conditional size controls")
        return
    if len(controls) != len(EMBEDDING_CYCLE_SIZES):
        raise RoleSuccessionRunError("primary passer lacks the frozen size controls")
    primary = record["first_complete_pass"]
    primary_compact = {
        "layer": primary["layer"],
        "signed_anchor": primary["signed_anchor"],
        "successor_displacement": primary["successor_displacement"],
        "sham_future": primary["sham_future"],
        "breaking_future": primary["breaking_future"],
    }
    required = record["pass_by_H29"]
    for control, cycle_size in zip(controls, EMBEDDING_CYCLE_SIZES):
        if type(control) is not dict or set(control) != SIZE_CONTROL_KEYS:
            raise RoleSuccessionRunError("cross-size control shape mismatch")
        if (
            type(control["cycle_size"]) is not int
            or control["cycle_size"] != cycle_size
            or type(control["evaluated_through_layer"]) is not int
            or control["evaluated_through_layer"] != record["t_proto_exact"]
            or type(control["matches_primary_witness"]) is not bool
            or control["pre_wrap_agreement_required"] is not required
        ):
            raise RoleSuccessionRunError("cross-size control allocation mismatch")
        witness = control["first_complete_pass"]
        if witness is not None:
            if type(witness) is not dict or set(witness) != SIZE_PASS_KEYS:
                raise RoleSuccessionRunError("cross-size pass witness shape mismatch")
            if (
                type(witness["layer"]) is not int
                or not 1 <= witness["layer"] <= record["t_proto_exact"]
                or type(witness["signed_anchor"]) is not int
                or not -(cycle_size // 2 - 1) <= witness["signed_anchor"] <= cycle_size // 2
                or type(witness["successor_displacement"]) is not int
                or witness["successor_displacement"] not in (0, 1)
                or type(witness["sham_future"]) is not int
                or type(witness["breaking_future"]) is not int
                or witness["sham_future"] not in (0, 1)
                or witness["breaking_future"] not in (0, 1)
                or witness["sham_future"] == witness["breaking_future"]
            ):
                raise RoleSuccessionRunError("cross-size pass witness mismatch")
        matches = witness == primary_compact
        if control["matches_primary_witness"] is not matches:
            raise RoleSuccessionRunError("cross-size primary comparison mismatch")
        expected_exact = matches if required else None
        if control["exact_pre_wrap_agreement"] is not expected_exact:
            raise RoleSuccessionRunError("cross-size pre-wrap agreement mismatch")
        if required and not matches:
            raise RoleSuccessionRunError("mandatory cross-size agreement failed")


def validate_result_ledger(
    ledger: dict[str, Any],
    candidates: Optional[Iterable[dict[str, Any]]] = None,
) -> None:
    if type(ledger) is not dict or set(ledger) != LEDGER_KEYS:
        raise RoleSuccessionRunError("result ledger has missing or unexpected keys")
    fixed = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": RUN_ID,
        "grammar_id": GRAMMAR_ID,
        "detector": DETECTOR_ID,
        "data_class": DATA_CLASS,
        "endpoint": RESULT_ENDPOINT,
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "embedding_cycle_sizes": list(EMBEDDING_CYCLE_SIZES),
        "canonical_origin": CANONICAL_ORIGIN,
        "formation_horizon": FORMATION_HORIZON,
        "causal_endpoint_lag": CAUSAL_ENDPOINT_LAG,
        "cone_saturation_layer": PRIMARY_CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "global_minimality_claimed": False,
        "alternative_grammar_excluded": False,
        "all_nonempty_candidates_processed": True,
        "shell_stopping_used": False,
    }
    for key, expected in fixed.items():
        if not strict_json_equal(ledger.get(key), expected):
            raise RoleSuccessionRunError(f"result ledger {key} mismatch")
    expected_capacity = {
        "normalized_n_p": 2,
        "input_ports": list(INPUT_PORTS),
        "relation_incidence_reads_per_site": 2,
        "local_signature_fan_in": 3,
        "truth_table_row_capacity": 8,
        "scheduler": "synchronous_atomic_layer",
        "seed": "one_event_at_origin_0",
        "comparator": "all_zero_evolved_under_same_rule",
        "topology": "oriented_periodic_cycle",
    }
    expected_allocation = {
        "candidate_count": CANDIDATE_COUNT,
        "dynamic_candidate_count": DYNAMIC_CANDIDATE_COUNT,
        "shell_sizes": list(SHELL_SIZES),
        "enumeration_order": "increasing_N_L_then_lexicographic_signature_tuple",
    }
    if not strict_json_equal(ledger.get("primitive_capacity"), expected_capacity):
        raise RoleSuccessionRunError("result ledger primitive capacity mismatch")
    if not strict_json_equal(ledger.get("candidate_allocation"), expected_allocation):
        raise RoleSuccessionRunError("result ledger candidate allocation mismatch")
    expected_trace_encoding = (
        "sha256_domain_separated_decimal_length_layer_fixed_width_seeded_"
        "fixed_width_comparator_including_layer_0"
    )
    if ledger.get("trace_digest_encoding") != expected_trace_encoding:
        raise RoleSuccessionRunError("result ledger trace encoding mismatch")
    for name in (
        "open_manifest",
        "outcome_seal",
        "candidate_manifest",
        "result_schema",
        "parent_exact_result",
    ):
        require_binding(ledger[name], name)
    expected_parent = {
        "path": PARENT_EXACT_RESULT_REF,
        "sha256": PARENT_EXACT_RESULT_SHA256,
    }
    if not strict_json_equal(ledger["parent_exact_result"], expected_parent):
        raise RoleSuccessionRunError("result ledger parent exact-result binding mismatch")

    canonical_candidates = tuple(candidates) if candidates is not None else None
    if canonical_candidates is not None:
        validate_candidate_manifest(canonical_candidates)
    results = ledger.get("candidate_results")
    if type(results) is not list or len(results) != CANDIDATE_COUNT:
        raise RoleSuccessionRunError("candidate result allocation mismatch")
    expected_rows = enumerate_rule_rows()
    common_keys = {
        "candidate_id",
        "candidate_sha256",
        "normalized_n_p",
        "atomic_n_l",
        "production_rows",
        "wolfram_rule_number",
        "evaluation_status",
        "bounded_status",
        "pass_by_H29",
        "t_proto_exact",
        "last_assessed_layer",
        "first_role",
        "first_successor",
        "first_intervention_eligible",
        "first_complete_pass",
        "pre_wrap_classification",
        "recurrence",
        "resource_limit",
        "trace_sha256",
        "transition_symmetry_audit",
        "cross_size_controls",
        "localized_interpretation",
    }
    statuses: list[str] = []
    for index, (record, rows) in enumerate(zip(results, expected_rows)):
        expected_keys = common_keys | ({"exclusion_reason"} if index == 0 else set())
        if type(record) is not dict or set(record) != expected_keys:
            raise RoleSuccessionRunError("candidate result shape mismatch")
        if record["candidate_id"] != candidate_id(rows):
            raise RoleSuccessionRunError("candidate result identity mismatch")
        if (
            type(record["atomic_n_l"]) is not int
            or record["atomic_n_l"] != len(rows)
            or record["production_rows"] != list(rows)
        ):
            raise RoleSuccessionRunError("candidate result row allocation mismatch")
        if type(record["normalized_n_p"]) is not int or record["normalized_n_p"] != 2:
            raise RoleSuccessionRunError("candidate primitive count mismatch")
        if (
            type(record["wolfram_rule_number"]) is not int
            or record["wolfram_rule_number"] != wolfram_rule_number(rows)
        ):
            raise RoleSuccessionRunError("candidate Wolfram code mismatch")
        if canonical_candidates is not None and record["candidate_sha256"] != candidate_sha256(canonical_candidates[index]):
            raise RoleSuccessionRunError("candidate result hash mismatch")
        else:
            _require_digest(record["candidate_sha256"], "candidate")
        status = record["evaluation_status"]
        statuses.append(status)
        if index == 0:
            if (
                status != "analytically_excluded"
                or record["bounded_status"] != "not_applicable"
                or record["pass_by_H29"] is not False
                or record["cross_size_controls"] != []
                or type(record.get("exclusion_reason")) is not str
                or not record["exclusion_reason"]
                or any(
                    record[key] is not None
                    for key in (
                        "t_proto_exact",
                        "last_assessed_layer",
                        "first_role",
                        "first_successor",
                        "first_intervention_eligible",
                        "first_complete_pass",
                        "pre_wrap_classification",
                        "recurrence",
                        "resource_limit",
                        "trace_sha256",
                        "transition_symmetry_audit",
                    )
                )
                or record["localized_interpretation"] is not False
            ):
                raise RoleSuccessionRunError("zero-row exclusion record mismatch")
            continue
        if status not in TERMINAL_STATUSES:
            raise RoleSuccessionRunError("dynamic terminal status mismatch")
        last_layer = record["last_assessed_layer"]
        if type(last_layer) is not int or not 1 <= last_layer <= MAX_LAYERS_PER_CANDIDATE:
            raise RoleSuccessionRunError("dynamic terminal layer mismatch")
        _require_digest(record["trace_sha256"], "candidate trace")
        _validate_stage(record["first_role"], {"layer", "anchor"}, last_layer)
        _validate_stage(
            record["first_successor"],
            {"layer", "anchor", "successor_anchor"},
            last_layer,
        )
        _validate_stage(
            record["first_intervention_eligible"],
            {"layer", "anchor", "successor_anchor"},
            last_layer,
        )
        if record["first_complete_pass"] is not None:
            _validate_pass(record["first_complete_pass"], last_layer)
        stage_sequence = (
            record["first_role"],
            record["first_successor"],
            record["first_intervention_eligible"],
            record["first_complete_pass"],
        )
        seen_gap = False
        stage_layers: list[int] = []
        for witness in stage_sequence:
            if witness is None:
                seen_gap = True
                continue
            if seen_gap:
                raise RoleSuccessionRunError("nested detector stage lacks a prior stage")
            stage_layers.append(witness["layer"])
        if stage_layers != sorted(stage_layers):
            raise RoleSuccessionRunError("detector stage chronology mismatch")
        pre = record["pre_wrap_classification"]
        expected_pre = _expected_pre_wrap(*stage_sequence)
        if type(pre) is not dict or not strict_json_equal(pre, expected_pre):
            raise RoleSuccessionRunError("pre-wrap classification shape mismatch")
        if (
            type(record["pass_by_H29"]) is not bool
            or record["pass_by_H29"] is not pre["pass_by_H29"]
        ):
            raise RoleSuccessionRunError("pre-wrap pass classification mismatch")
        expected_bounded = "pass_by_H29" if record["pass_by_H29"] else "right_censored_T_proto_gt_29"
        if record["bounded_status"] != expected_bounded:
            raise RoleSuccessionRunError("bounded status mismatch")
        audit = record["transition_symmetry_audit"]
        if (
            type(audit) is not dict
            or not strict_json_equal(
                audit.get("translation_offsets"),
                list(range(PRIMARY_CYCLE_SIZE)),
            )
            or audit.get("last_audited_layer")
            != min(last_layer, SYMMETRY_AUDIT_LAST_LAYER)
            or audit.get("translation_covariance_exact") is not True
            or audit.get("reflection_covariance_exact") is not True
            or audit.get("reflected_production_rows") != list(reflected_rows(rows))
        ):
            raise RoleSuccessionRunError("transition symmetry audit mismatch")
        if status == "exact_pass_on_fixed_orbit":
            if (
                type(record["t_proto_exact"]) is not int
                or record["t_proto_exact"] != last_layer
                or record["first_complete_pass"] is None
                or record["first_complete_pass"]["layer"] != last_layer
                or record["recurrence"] is not None
                or record["resource_limit"] is not None
                or len(record["cross_size_controls"]) != len(EMBEDDING_CYCLE_SIZES)
            ):
                raise RoleSuccessionRunError("passing terminal fields mismatch")
        elif status == "recurrence_excluded_on_fixed_orbit":
            recurrence = record["recurrence"]
            recurrence_keys = {
                "cone_saturation_layer",
                "checkpoint_layer",
                "repeat_layer",
                "period",
                "checkpoint_state",
                "repeat_state",
                "exact_full_state_equality",
            }
            if (
                record["t_proto_exact"] is not None
                or record["first_complete_pass"] is not None
                or type(recurrence) is not dict
                or set(recurrence) != recurrence_keys
                or recurrence.get("cone_saturation_layer")
                != PRIMARY_CONE_SATURATION_LAYER
                or recurrence.get("repeat_layer") != last_layer
                or recurrence.get("exact_full_state_equality") is not True
                or record["resource_limit"] is not None
                or record["cross_size_controls"] != []
            ):
                raise RoleSuccessionRunError("recurrence terminal fields mismatch")
            checkpoint = recurrence.get("checkpoint_layer")
            repeat = recurrence.get("repeat_layer")
            period = recurrence.get("period")
            if (
                type(checkpoint) is not int
                or type(repeat) is not int
                or type(period) is not int
                or checkpoint < PRIMARY_CONE_SATURATION_LAYER
                or repeat <= checkpoint
                or period != repeat - checkpoint
            ):
                raise RoleSuccessionRunError("recurrence arithmetic mismatch")
            state = recurrence["checkpoint_state"]
            if (
                type(state) is not dict
                or set(state) != {"seeded_state_hex", "baseline_state_hex"}
                or not _valid_state_hex(state["seeded_state_hex"])
                or not _valid_state_hex(state["baseline_state_hex"])
                or not strict_json_equal(state, recurrence["repeat_state"])
            ):
                raise RoleSuccessionRunError("recurrence state encoding mismatch")
        else:
            if (
                record["t_proto_exact"] is not None
                or record["first_complete_pass"] is not None
                or record["recurrence"] is not None
                or record["resource_limit"] != MAX_LAYERS_PER_CANDIDATE
                or last_layer != MAX_LAYERS_PER_CANDIDATE
                or record["cross_size_controls"] != []
            ):
                raise RoleSuccessionRunError("resource terminal fields mismatch")
        _validate_size_controls(record)
        expected_localized = bool(
            record["pass_by_H29"]
            and record["evaluation_status"] == "exact_pass_on_fixed_orbit"
            and all(
                control["exact_pre_wrap_agreement"] is True
                for control in record["cross_size_controls"]
            )
        )
        if record["localized_interpretation"] is not expected_localized:
            raise RoleSuccessionRunError("localized interpretation mismatch")

    expected_summary = _summarize_results(results)
    for key, value in expected_summary.items():
        if not strict_json_equal(ledger.get(key), value):
            raise RoleSuccessionRunError(f"aggregate {key} mismatch")


def write_result_ledger(
    path: Path,
    ledger: dict[str, Any],
    *,
    open_manifest_verified: bool,
) -> None:
    """Atomically create one canonical ledger after the caller's open gate."""

    if open_manifest_verified is not True:
        raise RoleSuccessionRunError(
            "result writing requires a caller-verified open manifest"
        )
    validate_result_ledger(ledger)
    if path.exists():
        raise RoleSuccessionRunError(f"refusing to overwrite result ledger: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RoleSuccessionRunError(
            f"refusing to overwrite stale temporary ledger: {temporary}"
        )
    try:
        with temporary.open("x", encoding="ascii", newline="\n") as handle:
            handle.write(canonical_json(ledger) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        temporary.unlink()
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


def synthetic_candidate_evaluation(
    rows: tuple[str, ...],
    orbit: ExactOrbitOutcome,
    *,
    size_controls: tuple[SizeControlOutcome, ...] = (),
) -> CandidateEvaluation:
    """Build a fully shaped fake evaluation for outcome-free orchestration tests."""

    return CandidateEvaluation(
        orbit,
        TransitionSymmetryAudit(
            tuple(range(PRIMARY_CYCLE_SIZE)),
            min(orbit.last_assessed_layer, SYMMETRY_AUDIT_LAST_LAYER),
            True,
            True,
            reflected_rows(rows),
        ),
        size_controls,
    )
