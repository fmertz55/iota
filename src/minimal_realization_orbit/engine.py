from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable, Optional

from src.minimal_realization.detector import (
    DetectorResult,
    LAST_REQUIRED_LAYER,
    canonical_initial_state,
    detect_proto_object,
    forward_distance,
    in_forward_cone,
    outward_future_values,
    role_at,
    successor_anchor,
)
from src.minimal_realization.dynamics import (
    CYCLE_SIZE,
    event_at,
    normalize_rows,
    require_state,
    run_trajectory,
    step,
)


CONE_SATURATION_LAYER = CYCLE_SIZE - 1
PARENT_CENSORING_LAYER = 16
FIRST_NEW_OUTCOME_LAYER = PARENT_CENSORING_LAYER + 1
MAX_LAYERS_PER_CANDIDATE = 1_000_000


class OrbitRunError(ValueError):
    pass


@dataclass(frozen=True)
class LayerAssessment:
    first_role_anchor: Optional[int]
    first_successor: Optional[tuple[int, int]]
    first_intervention_eligible: Optional[tuple[int, int]]
    detector_result: DetectorResult


@dataclass(frozen=True)
class ExactOrbitOutcome:
    status: str
    t_proto: Optional[int]
    last_evaluated_layer: int
    first_role: Optional[tuple[int, int]]
    first_successor: Optional[tuple[int, int, int]]
    first_intervention_eligible: Optional[tuple[int, int, int]]
    pass_witness: Optional[tuple[int, int, int, int, int, int, int]]
    recurrence: Optional[tuple[int, int, int, int, int]]
    trace_sha256: str


JointState = tuple[int, int]
Transition = Callable[[JointState], JointState]
Assessor = Callable[[JointState, int], LayerAssessment]


def _require_joint_state(state: object) -> JointState:
    if type(state) is not tuple or len(state) != 2:
        raise OrbitRunError("joint state must be a seeded/baseline pair")
    seeded_state, baseline_state = state
    require_state(seeded_state)
    require_state(baseline_state)
    return seeded_state, baseline_state


def _update_trace_digest(digest: "hashlib._Hash", layer: int, state: JointState) -> None:
    seeded_state, baseline_state = state
    layer_bytes = str(layer).encode("ascii")
    digest.update(len(layer_bytes).to_bytes(8, "big"))
    digest.update(layer_bytes)
    digest.update(seeded_state.to_bytes(8, "big"))
    digest.update(baseline_state.to_bytes(8, "big"))


def _require_detector_result(result: DetectorResult) -> None:
    if type(result.passed) is not bool:
        raise OrbitRunError("detector pass flag must be Boolean")
    fields = (
        result.t_proto,
        result.anchor,
        result.successor_anchor,
        result.sham_future,
        result.breaking_future,
    )
    if not result.passed:
        if any(value is not None for value in fields):
            raise OrbitRunError("nonpassing detector result contains outcome fields")
        return
    if any(value is None for value in fields):
        raise OrbitRunError("passing detector result is incomplete")
    if type(result.t_proto) is not int or result.t_proto < 1:
        raise OrbitRunError("passing detector layer is invalid")
    if type(result.anchor) is not int or not 0 <= result.anchor < CYCLE_SIZE:
        raise OrbitRunError("passing anchor is invalid")
    if (
        type(result.successor_anchor) is not int
        or not 0 <= result.successor_anchor < CYCLE_SIZE
    ):
        raise OrbitRunError("passing successor anchor is invalid")
    if (
        type(result.sham_future) is not int
        or type(result.breaking_future) is not int
        or result.sham_future not in (0, 1)
        or result.breaking_future not in (0, 1)
        or result.sham_future == result.breaking_future
    ):
        raise OrbitRunError("passing causal endpoints are invalid")


def trace_joint_orbit(
    initial_state: JointState,
    transition: Transition,
    assess: Assessor,
    *,
    saturation_layer: int,
    max_layers: int,
    trace_domain: bytes,
) -> ExactOrbitOutcome:
    """Trace a deterministic state until pass, post-saturation repeat, or cap.

    A repeated state closes the detector search only when both occurrences are
    at or after ``saturation_layer``. Before then, the expanding causal cone is
    detector state that is not encoded in the dynamical state itself.
    """

    if type(saturation_layer) is not int or saturation_layer < 1:
        raise OrbitRunError("saturation layer must be a positive integer")
    if type(max_layers) is not int or max_layers < saturation_layer:
        raise OrbitRunError("resource cap must reach the saturation layer")
    if type(trace_domain) is not bytes or not trace_domain:
        raise OrbitRunError("trace domain must be nonempty bytes")
    current = _require_joint_state(initial_state)
    trace_digest = hashlib.sha256()
    trace_digest.update(b"IOTA-MIR-EXACT-ORBIT-TRACE-V1\x00")
    trace_digest.update(len(trace_domain).to_bytes(8, "big"))
    trace_digest.update(trace_domain)
    _update_trace_digest(trace_digest, 0, current)
    checkpoint: Optional[JointState] = None
    checkpoint_layer: Optional[int] = None
    checkpoint_power = 1
    checkpoint_distance = 0
    first_role: Optional[tuple[int, int]] = None
    first_successor: Optional[tuple[int, int, int]] = None
    first_eligible: Optional[tuple[int, int, int]] = None

    for layer in range(1, max_layers + 1):
        current = _require_joint_state(transition(current))
        _update_trace_digest(trace_digest, layer, current)
        assessment = assess(current, layer)
        if type(assessment) is not LayerAssessment:
            raise OrbitRunError("assessor returned the wrong result type")
        _require_detector_result(assessment.detector_result)

        if assessment.first_role_anchor is not None:
            anchor = assessment.first_role_anchor
            if type(anchor) is not int or not 0 <= anchor < CYCLE_SIZE:
                raise OrbitRunError("role witness anchor is invalid")
            if first_role is None:
                first_role = (layer, anchor)
        if assessment.first_successor is not None:
            anchor, successor = assessment.first_successor
            if any(type(value) is not int or not 0 <= value < CYCLE_SIZE for value in (anchor, successor)):
                raise OrbitRunError("succession witness is invalid")
            if first_successor is None:
                first_successor = (layer, anchor, successor)
        if assessment.first_intervention_eligible is not None:
            anchor, successor = assessment.first_intervention_eligible
            if any(type(value) is not int or not 0 <= value < CYCLE_SIZE for value in (anchor, successor)):
                raise OrbitRunError("intervention-eligibility witness is invalid")
            if first_eligible is None:
                first_eligible = (layer, anchor, successor)

        result = assessment.detector_result
        if result.passed:
            if result.t_proto != layer:
                raise OrbitRunError("detector result layer differs from scan layer")
            return ExactOrbitOutcome(
                status="exact_pass_on_fixed_orbit",
                t_proto=layer,
                last_evaluated_layer=layer,
                first_role=first_role,
                first_successor=first_successor,
                first_intervention_eligible=first_eligible,
                pass_witness=(
                    layer,
                    int(result.anchor),
                    int(result.successor_anchor),
                    int(result.sham_future),
                    int(result.breaking_future),
                    current[0],
                    current[1],
                ),
                recurrence=None,
                trace_sha256=trace_digest.hexdigest(),
            )

        if layer == saturation_layer:
            checkpoint = current
            checkpoint_layer = layer
            checkpoint_power = 1
            checkpoint_distance = 0
        elif layer > saturation_layer:
            if checkpoint is None or checkpoint_layer is None:
                raise OrbitRunError("post-saturation recurrence checkpoint is missing")
            checkpoint_distance += 1
            if current == checkpoint:
                seeded_state, baseline_state = current
                return ExactOrbitOutcome(
                    status="recurrence_excluded_on_fixed_orbit",
                    t_proto=None,
                    last_evaluated_layer=layer,
                    first_role=first_role,
                    first_successor=first_successor,
                    first_intervention_eligible=first_eligible,
                    pass_witness=None,
                    recurrence=(
                        checkpoint_layer,
                        layer,
                        checkpoint_distance,
                        seeded_state,
                        baseline_state,
                    ),
                    trace_sha256=trace_digest.hexdigest(),
                )
            if checkpoint_distance == checkpoint_power:
                checkpoint = current
                checkpoint_layer = layer
                checkpoint_power *= 2
                checkpoint_distance = 0

    return ExactOrbitOutcome(
        status="resource_censored_before_recurrence",
        t_proto=None,
        last_evaluated_layer=max_layers,
        first_role=first_role,
        first_successor=first_successor,
        first_intervention_eligible=first_eligible,
        pass_witness=None,
        recurrence=None,
        trace_sha256=trace_digest.hexdigest(),
    )


def evaluate_detector_layer(
    seeded_state: int,
    baseline_state: int,
    rows: tuple[str, ...],
    *,
    layer: int,
    origin: int = 0,
) -> LayerAssessment:
    """Evaluate the exact-orbit extension of the frozen v0.2 local predicates."""

    require_state(seeded_state)
    require_state(baseline_state)
    production_rows = normalize_rows(rows)
    if type(layer) is not int or layer < 1:
        raise OrbitRunError("detector layer must be a positive integer")
    if type(origin) is not int or not 0 <= origin < CYCLE_SIZE:
        raise OrbitRunError("origin must be a cycle locus")

    next_seeded = step(seeded_state, production_rows)
    next_baseline = step(baseline_state, production_rows)
    role_witness: Optional[int] = None
    successor_witness: Optional[tuple[int, int]] = None
    eligible_witness: Optional[tuple[int, int]] = None

    anchors = sorted(
        range(CYCLE_SIZE),
        key=lambda locus: (forward_distance(locus, origin), locus),
    )
    for anchor in anchors:
        if not in_forward_cone(anchor, origin, layer):
            continue
        if not in_forward_cone(anchor + 1, origin, layer):
            continue
        if not role_at(seeded_state, baseline_state, anchor):
            continue
        if role_witness is None:
            role_witness = anchor
        successor = successor_anchor(
            next_seeded,
            next_baseline,
            anchor,
            origin=origin,
            next_layer=layer + 1,
        )
        if successor is None:
            continue
        if successor_witness is None:
            successor_witness = (anchor, successor)
        if not in_forward_cone(anchor + 3, origin, layer + 2):
            continue
        if event_at(seeded_state, anchor + 3) != 0:
            continue
        if eligible_witness is None:
            eligible_witness = (anchor, successor)
        sham_future, breaking_future = outward_future_values(
            seeded_state,
            production_rows,
            anchor,
        )
        if sham_future == breaking_future:
            continue
        return LayerAssessment(
            first_role_anchor=role_witness,
            first_successor=successor_witness,
            first_intervention_eligible=eligible_witness,
            detector_result=DetectorResult(
                passed=True,
                t_proto=layer,
                anchor=anchor,
                successor_anchor=successor,
                sham_future=sham_future,
                breaking_future=breaking_future,
            ),
        )

    return LayerAssessment(
        first_role_anchor=role_witness,
        first_successor=successor_witness,
        first_intervention_eligible=eligible_witness,
        detector_result=DetectorResult(False, None, None, None, None, None),
    )


def reproduce_parent_H16(
    rows: tuple[str, ...],
    parent_origin_record: dict[str, object],
) -> None:
    """Recompute and field-compare the committed canonical-origin H=16 row."""

    production_rows = tuple(sorted(normalize_rows(rows)))
    seeded = run_trajectory(
        canonical_initial_state(0),
        production_rows,
        LAST_REQUIRED_LAYER,
    )
    baseline = run_trajectory(0, production_rows, LAST_REQUIRED_LAYER)
    result = detect_proto_object(seeded, baseline, production_rows, origin=0)
    actual = {
        "translation_offset": 0,
        "status": (
            "passed_by_H16" if result.passed else "right_censored_T_proto_gt_16"
        ),
        "t_proto": result.t_proto,
        "anchor": result.anchor,
        "anchor_offset_from_seed": result.anchor,
        "successor_anchor": result.successor_anchor,
        "successor_anchor_offset_from_seed": result.successor_anchor,
        "sham_future": result.sham_future,
        "breaking_future": result.breaking_future,
    }
    if actual != parent_origin_record:
        raise OrbitRunError("canonical-origin H=16 reproduction differs from the parent ledger")


def evaluate_candidate_exact_orbit(
    rows: tuple[str, ...],
    *,
    trace_domain: bytes,
) -> ExactOrbitOutcome:
    """Run one registered canonical candidate without evaluating translations."""

    production_rows = tuple(sorted(normalize_rows(rows)))
    if not production_rows:
        raise OrbitRunError("the zero-law candidate is analytically excluded, not traced")

    initial = (canonical_initial_state(0), 0)

    def transition(state: tuple[int, int]) -> tuple[int, int]:
        seeded, baseline = state
        return step(seeded, production_rows), step(baseline, production_rows)

    def assess(state: tuple[int, int], layer: int) -> LayerAssessment:
        seeded, baseline = state
        return evaluate_detector_layer(
            seeded,
            baseline,
            production_rows,
            layer=layer,
            origin=0,
        )

    outcome = trace_joint_orbit(
        initial,
        transition,
        assess,
        saturation_layer=CONE_SATURATION_LAYER,
        max_layers=MAX_LAYERS_PER_CANDIDATE,
        trace_domain=trace_domain,
    )
    if outcome.t_proto is not None and outcome.t_proto <= PARENT_CENSORING_LAYER:
        raise OrbitRunError("exact-orbit result contradicts the committed H=16 parent ledger")
    return outcome
