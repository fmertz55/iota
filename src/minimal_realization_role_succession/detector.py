"""Frozen staged detector for endogenous isolated-dyad succession."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Optional

from .dynamics import (
    CYCLE_SIZE,
    canonical_initial_state,
    event_at,
    normalize_rows,
    require_cycle_size,
    require_state,
    state_mask,
    step,
)
from .protocol import (
    CAUSAL_ENDPOINT_LAG,
    EXTERNAL_ENDPOINT_OFFSET,
    FORMATION_HORIZON,
    INTERVENTION_WINDOW_OFFSETS,
    NATURAL_INTERVENTION_WINDOW,
    ROLE_BREAKING_ARM,
    ROLE_PRESERVING_SHAM,
    SUCCESSOR_ANCHOR_OFFSETS,
    graph_distance,
)


LAST_REQUIRED_LAYER = FORMATION_HORIZON + CAUSAL_ENDPOINT_LAG


@dataclass(frozen=True)
class DetectorResult:
    passed: bool
    t_proto: Optional[int]
    anchor: Optional[int]
    successor_anchor: Optional[int]
    sham_future: Optional[int]
    breaking_future: Optional[int]


@dataclass(frozen=True)
class LayerAssessment:
    first_role_anchor: Optional[int]
    first_successor: Optional[tuple[int, int]]
    first_intervention_eligible: Optional[tuple[int, int]]
    detector_result: DetectorResult


def forward_offset(locus: int, origin: int, cycle_size: int = CYCLE_SIZE) -> int:
    size = require_cycle_size(cycle_size)
    if type(locus) is not int or type(origin) is not int:
        raise TypeError("cycle loci must be integers")
    return (locus - origin) % size


def in_bidirectional_cone(
    locus: int,
    origin: int,
    layer: int,
    cycle_size: int = CYCLE_SIZE,
) -> bool:
    size = require_cycle_size(cycle_size)
    if type(layer) is not int or layer < 0:
        raise ValueError("cone layer must be a nonnegative integer")
    return graph_distance(locus, origin, size) <= layer


@lru_cache(maxsize=512)
def ordered_anchors(
    origin: int = 0,
    cycle_size: int = CYCLE_SIZE,
) -> tuple[int, ...]:
    """Return the frozen centered order ``0,+1,-1,+2,-2,...``."""

    size = require_cycle_size(cycle_size)
    if type(origin) is not int or not 0 <= origin < size:
        raise ValueError("origin must be a cycle locus")
    return tuple(
        sorted(
            range(size),
            key=lambda locus: (
                graph_distance(locus, origin, size),
                forward_offset(locus, origin, size),
            ),
        )
    )


def _rotate_left(state: int, distance: int, cycle_size: int, mask: int) -> int:
    shift = distance % cycle_size
    if shift == 0:
        return state
    return ((state << shift) | (state >> (cycle_size - shift))) & mask


def _rotate_right(state: int, distance: int, cycle_size: int, mask: int) -> int:
    shift = distance % cycle_size
    if shift == 0:
        return state
    return ((state >> shift) | (state << (cycle_size - shift))) & mask


def _role_anchor_mask_unchecked(
    state: int,
    baseline: int,
    cycle_size: int,
    mask: int,
) -> int:
    """Return bits at anchors satisfying attributed ``0,1,1,0`` exactly."""

    successor_values = _rotate_right(state, 1, cycle_size, mask)
    predecessor_values = _rotate_left(state, 1, cycle_size, mask)
    second_successor_values = _rotate_right(state, 2, cycle_size, mask)
    baseline_successor_values = _rotate_right(baseline, 1, cycle_size, mask)
    return (
        state
        & successor_values
        & ~predecessor_values
        & ~second_successor_values
        & ~baseline
        & ~baseline_successor_values
        & mask
    )


def role_anchor_mask(
    state: int,
    baseline: int,
    cycle_size: int = CYCLE_SIZE,
) -> int:
    """Return the exact attributed-role anchors as a ring-width bit mask."""

    size = require_cycle_size(cycle_size)
    require_state(state, size)
    require_state(baseline, size)
    mask = state_mask(size)
    return _role_anchor_mask_unchecked(state, baseline, size, mask)


@lru_cache(maxsize=1024)
def _cone_mask_at_radius(origin: int, radius: int, cycle_size: int) -> int:
    if radius >= cycle_size // 2:
        return state_mask(cycle_size)
    output = 0
    for locus in range(cycle_size):
        if graph_distance(locus, origin, cycle_size) <= radius:
            output |= 1 << locus
    return output


def _cone_mask(origin: int, layer: int, cycle_size: int) -> int:
    # Normalizing saturated layers prevents a million equivalent cache keys.
    radius = min(layer, cycle_size // 2)
    return _cone_mask_at_radius(origin, radius, cycle_size)


@lru_cache(maxsize=1024)
def _eligible_anchor_mask_at_radius(
    origin: int,
    radius: int,
    cycle_size: int,
) -> int:
    mask = state_mask(cycle_size)
    cone = _cone_mask_at_radius(origin, radius, cycle_size)
    return cone & _rotate_right(cone, 1, cycle_size, mask)


def _eligible_anchor_mask(origin: int, layer: int, cycle_size: int) -> int:
    radius = min(layer, cycle_size // 2)
    return _eligible_anchor_mask_at_radius(origin, radius, cycle_size)


def role_at(
    state: int,
    baseline: int,
    anchor: int,
    cycle_size: int = CYCLE_SIZE,
) -> bool:
    """Test the attributed isolated-dyad pattern ``0110`` at ``anchor``."""

    size = require_cycle_size(cycle_size)
    require_state(state, size)
    require_state(baseline, size)
    if type(anchor) is not int:
        raise TypeError("anchor must be an integer")
    anchors = _role_anchor_mask_unchecked(state, baseline, size, state_mask(size))
    return bool(anchors & (1 << (anchor % size)))


def successor_anchor(
    next_state: int,
    next_baseline: int,
    formation_anchor: int,
    *,
    origin: int,
    next_layer: int,
    cycle_size: int = CYCLE_SIZE,
) -> Optional[int]:
    """Select an eligible same-or-forward successor using frozen offset order."""

    size = require_cycle_size(cycle_size)
    require_state(next_state, size)
    require_state(next_baseline, size)
    if type(formation_anchor) is not int:
        raise TypeError("formation_anchor must be an integer")
    if type(origin) is not int:
        raise TypeError("origin must be an integer")
    if type(next_layer) is not int or next_layer < 0:
        raise ValueError("next_layer must be a nonnegative integer")
    role_anchors = _role_anchor_mask_unchecked(
        next_state,
        next_baseline,
        size,
        state_mask(size),
    ) & _eligible_anchor_mask(origin, next_layer, size)
    for offset in SUCCESSOR_ANCHOR_OFFSETS:
        anchor = (formation_anchor + offset) % size
        if role_anchors & (1 << anchor):
            return anchor
    return None


def _replace_window(
    state: int,
    anchor: int,
    values: tuple[int, int, int],
    cycle_size: int,
) -> int:
    output = state
    for offset, value in zip(INTERVENTION_WINDOW_OFFSETS, values):
        bit = 1 << ((anchor + offset) % cycle_size)
        if value:
            output |= bit
        else:
            output &= ~bit
    return output


def matched_intervention_states(
    state: int,
    anchor: int,
    cycle_size: int = CYCLE_SIZE,
) -> tuple[int, int]:
    size = require_cycle_size(cycle_size)
    require_state(state, size)
    if type(anchor) is not int:
        raise TypeError("anchor must be an integer")
    natural = tuple(
        event_at(state, anchor + offset, size)
        for offset in INTERVENTION_WINDOW_OFFSETS
    )
    if natural != NATURAL_INTERVENTION_WINDOW:
        raise ValueError(
            "intervention precondition must be natural window (1, 1, 0)"
        )
    if event_at(state, anchor + EXTERNAL_ENDPOINT_OFFSET, size) != 0:
        raise ValueError(
            "role-preserving sham requires quiescent external guard at offset +3"
        )
    sham = _replace_window(state, anchor, ROLE_PRESERVING_SHAM, size)
    breaking = _replace_window(state, anchor, ROLE_BREAKING_ARM, size)
    return sham, breaking


def outward_future_values(
    state: int,
    rows: Iterable[str],
    anchor: int,
    cycle_size: int = CYCLE_SIZE,
) -> tuple[int, int]:
    """Return matched-arm values at ``anchor+3`` after two exact steps.

    Radius-one causality means this endpoint depends only on formation offsets
    ``+1..+5``.  Evaluating that local causal diamond is exactly equivalent to
    constructing two full fresh layers, while avoiding four full-ring updates
    for every eligible anchor on a role-dense state.
    """

    size = require_cycle_size(cycle_size)
    production_rows = normalize_rows(rows)
    sham, breaking = matched_intervention_states(state, anchor, size)
    if CAUSAL_ENDPOINT_LAG != 2:
        raise RuntimeError("local endpoint evaluator is frozen to a two-layer lag")
    rule_number = sum(1 << int(signature, 2) for signature in production_rows)

    def local_endpoint(arm: int) -> int:
        formation = tuple(
            (arm >> ((anchor + offset) % size)) & 1
            for offset in range(1, 6)
        )
        first_layer = tuple(
            (rule_number >> (
                (formation[index] << 2)
                | (formation[index + 1] << 1)
                | formation[index + 2]
            ))
            & 1
            for index in range(3)
        )
        second_signature = (
            (first_layer[0] << 2)
            | (first_layer[1] << 1)
            | first_layer[2]
        )
        return (rule_number >> second_signature) & 1

    return local_endpoint(sham), local_endpoint(breaking)


def assess_layer(
    seeded_state: int,
    baseline_state: int,
    rows: Iterable[str],
    *,
    layer: int,
    origin: int = 0,
    cycle_size: int = CYCLE_SIZE,
) -> LayerAssessment:
    """Assess every eligible anchor at one formation layer.

    This streaming primitive deliberately does not impose the pre-wrap horizon;
    the exact fixed-ring continuation uses it after cone saturation as well.
    """

    size = require_cycle_size(cycle_size)
    require_state(seeded_state, size)
    require_state(baseline_state, size)
    production_rows = normalize_rows(rows)
    if type(layer) is not int or layer < 1:
        raise ValueError("detector layer must be a positive integer")
    if type(origin) is not int or not 0 <= origin < size:
        raise ValueError("origin must be a cycle locus")

    mask = state_mask(size)
    role_anchors = _role_anchor_mask_unchecked(
        seeded_state,
        baseline_state,
        size,
        mask,
    ) & _eligible_anchor_mask(origin, layer, size)
    if role_anchors == 0:
        return LayerAssessment(
            first_role_anchor=None,
            first_successor=None,
            first_intervention_eligible=None,
            detector_result=DetectorResult(False, None, None, None, None, None),
        )

    next_seeded = step(seeded_state, production_rows, size)
    next_baseline = step(baseline_state, production_rows, size)
    successor_roles = _role_anchor_mask_unchecked(
        next_seeded,
        next_baseline,
        size,
        mask,
    ) & _eligible_anchor_mask(origin, layer + 1, size)
    endpoint_cone = _cone_mask(origin, layer + CAUSAL_ENDPOINT_LAG, size)
    role_witness: Optional[int] = None
    successor_witness: Optional[tuple[int, int]] = None
    eligible_witness: Optional[tuple[int, int]] = None

    for anchor in ordered_anchors(origin, size):
        if not role_anchors & (1 << anchor):
            continue
        if role_witness is None:
            role_witness = anchor

        successor = None
        for displacement in SUCCESSOR_ANCHOR_OFFSETS:
            candidate = (anchor + displacement) % size
            if successor_roles & (1 << candidate):
                successor = candidate
                break
        if successor is None:
            continue
        if successor_witness is None:
            successor_witness = (anchor, successor)

        endpoint = (anchor + EXTERNAL_ENDPOINT_OFFSET) % size
        if not endpoint_cone & (1 << endpoint):
            continue
        if seeded_state & (1 << endpoint):
            continue
        if eligible_witness is None:
            eligible_witness = (anchor, successor)

        sham_future, breaking_future = outward_future_values(
            seeded_state,
            production_rows,
            anchor,
            size,
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


evaluate_detector_layer = assess_layer


def detect_proto_object(
    seeded_trajectory: tuple[int, ...],
    baseline_trajectory: tuple[int, ...],
    rows: Iterable[str],
    *,
    origin: int = 0,
    cycle_size: int = CYCLE_SIZE,
) -> DetectorResult:
    """Evaluate the frozen pre-wrap helper on supplied law-exact trajectories."""

    size = require_cycle_size(cycle_size)
    if (
        len(seeded_trajectory) <= LAST_REQUIRED_LAYER
        or len(baseline_trajectory) <= LAST_REQUIRED_LAYER
    ):
        raise ValueError(
            f"trajectories must include layers 0 through {LAST_REQUIRED_LAYER}"
        )
    production_rows = normalize_rows(rows)
    expected_seed = canonical_initial_state(origin, size)
    if seeded_trajectory[0] != expected_seed:
        raise ValueError("seeded trajectory has the wrong initial condition")
    if baseline_trajectory[0] != 0:
        raise ValueError("baseline trajectory must begin all-zero")
    for layer in range(LAST_REQUIRED_LAYER):
        require_state(seeded_trajectory[layer], size)
        require_state(baseline_trajectory[layer], size)
        if seeded_trajectory[layer + 1] != step(
            seeded_trajectory[layer], production_rows, size
        ):
            raise ValueError(f"seeded trajectory is not law-exact at layer {layer + 1}")
        if baseline_trajectory[layer + 1] != step(
            baseline_trajectory[layer], production_rows, size
        ):
            raise ValueError(
                f"baseline trajectory is not law-exact at layer {layer + 1}"
            )
    require_state(seeded_trajectory[LAST_REQUIRED_LAYER], size)
    require_state(baseline_trajectory[LAST_REQUIRED_LAYER], size)

    if any(
        role_at(seeded_trajectory[0], baseline_trajectory[0], anchor, size)
        for anchor in range(size)
    ):
        raise ValueError("initial state already contains the registered proto-object role")

    for layer in range(1, FORMATION_HORIZON + 1):
        result = assess_layer(
            seeded_trajectory[layer],
            baseline_trajectory[layer],
            production_rows,
            layer=layer,
            origin=origin,
            cycle_size=size,
        ).detector_result
        if result.passed:
            return result
    return DetectorResult(False, None, None, None, None, None)
