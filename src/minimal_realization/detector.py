from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .dynamics import CYCLE_SIZE, event_at, normalize_rows, state_from_active, step


FORMATION_HORIZON = 16
LAST_REQUIRED_LAYER = 18


@dataclass(frozen=True)
class DetectorResult:
    passed: bool
    t_proto: Optional[int]
    anchor: Optional[int]
    successor_anchor: Optional[int]
    sham_future: Optional[int]
    breaking_future: Optional[int]


def forward_distance(locus: int, origin: int) -> int:
    return (locus - origin) % CYCLE_SIZE


def in_forward_cone(locus: int, origin: int, layer: int) -> bool:
    return 0 <= forward_distance(locus, origin) <= layer


def role_at(state: int, baseline: int, anchor: int) -> bool:
    pattern = ((-1, 0), (0, 1), (1, 1), (2, 0))
    if any(event_at(state, anchor + offset) != expected for offset, expected in pattern):
        return False
    return event_at(baseline, anchor) == 0 and event_at(baseline, anchor + 1) == 0


def successor_anchor(
    next_state: int,
    next_baseline: int,
    formation_anchor: int,
    *,
    origin: int,
    next_layer: int,
) -> Optional[int]:
    for offset in (0, 1):
        anchor = (formation_anchor + offset) % CYCLE_SIZE
        if not in_forward_cone(anchor, origin, next_layer):
            continue
        if not in_forward_cone(anchor + 1, origin, next_layer):
            continue
        if role_at(next_state, next_baseline, anchor):
            return anchor
    return None


def _replace_window(state: int, anchor: int, values: tuple[int, int, int]) -> int:
    output = state
    for offset, value in enumerate(values):
        bit = 1 << ((anchor + offset) % CYCLE_SIZE)
        if value:
            output |= bit
        else:
            output &= ~bit
    return output


def matched_intervention_states(state: int, anchor: int) -> tuple[int, int]:
    natural = tuple(event_at(state, anchor + offset) for offset in range(3))
    if natural != (1, 1, 0):
        raise ValueError("intervention precondition must be natural window (1, 1, 0)")
    if event_at(state, anchor + 3) != 0:
        raise ValueError("role-preserving sham requires quiescent external guard at offset +3")
    sham = _replace_window(state, anchor, (0, 1, 1))
    breaking = _replace_window(state, anchor, (1, 0, 1))
    return sham, breaking


def outward_future_values(state: int, rows: Iterable[str], anchor: int) -> tuple[int, int]:
    production_rows = normalize_rows(rows)
    sham, breaking = matched_intervention_states(state, anchor)
    for _ in range(2):
        sham = step(sham, production_rows)
        breaking = step(breaking, production_rows)
    endpoint = anchor + 3
    return event_at(sham, endpoint), event_at(breaking, endpoint)


def detect_proto_object(
    seeded_trajectory: tuple[int, ...],
    baseline_trajectory: tuple[int, ...],
    rows: Iterable[str],
    *,
    origin: int = 0,
) -> DetectorResult:
    if len(seeded_trajectory) <= LAST_REQUIRED_LAYER or len(baseline_trajectory) <= LAST_REQUIRED_LAYER:
        raise ValueError(f"trajectories must include layers 0 through {LAST_REQUIRED_LAYER}")
    production_rows = normalize_rows(rows)
    expected_seed = canonical_initial_state(origin)
    if seeded_trajectory[0] != expected_seed:
        raise ValueError("seeded trajectory has the wrong initial condition")
    if baseline_trajectory[0] != 0:
        raise ValueError("baseline trajectory must begin all-zero")
    for layer in range(LAST_REQUIRED_LAYER):
        if seeded_trajectory[layer + 1] != step(seeded_trajectory[layer], production_rows):
            raise ValueError(f"seeded trajectory is not law-exact at layer {layer + 1}")
        if baseline_trajectory[layer + 1] != step(baseline_trajectory[layer], production_rows):
            raise ValueError(f"baseline trajectory is not law-exact at layer {layer + 1}")
    if role_at(seeded_trajectory[0], baseline_trajectory[0], origin):
        raise ValueError("initial state already contains the registered proto-object role")

    for layer in range(1, FORMATION_HORIZON + 1):
        anchors = sorted(
            range(CYCLE_SIZE),
            key=lambda locus: (forward_distance(locus, origin), locus),
        )
        for anchor in anchors:
            if not in_forward_cone(anchor, origin, layer):
                continue
            if not in_forward_cone(anchor + 1, origin, layer):
                continue
            if not role_at(seeded_trajectory[layer], baseline_trajectory[layer], anchor):
                continue
            successor = successor_anchor(
                seeded_trajectory[layer + 1],
                baseline_trajectory[layer + 1],
                anchor,
                origin=origin,
                next_layer=layer + 1,
            )
            if successor is None:
                continue
            if not in_forward_cone(anchor + 3, origin, layer + 2):
                continue
            if event_at(seeded_trajectory[layer], anchor + 3) != 0:
                continue
            sham_future, breaking_future = outward_future_values(
                seeded_trajectory[layer], production_rows, anchor
            )
            if sham_future == breaking_future:
                continue
            return DetectorResult(
                passed=True,
                t_proto=layer,
                anchor=anchor,
                successor_anchor=successor,
                sham_future=sham_future,
                breaking_future=breaking_future,
            )
    return DetectorResult(False, None, None, None, None, None)


def canonical_initial_state(origin: int = 0) -> int:
    return state_from_active([origin])
