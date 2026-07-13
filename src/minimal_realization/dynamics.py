from __future__ import annotations

from collections.abc import Iterable


CYCLE_SIZE = 64
STATE_MASK = (1 << CYCLE_SIZE) - 1
VALID_SIGNATURES = frozenset({"00", "01", "10", "11"})


def normalize_rows(rows: Iterable[str]) -> frozenset[str]:
    normalized = frozenset(rows)
    unknown = normalized - VALID_SIGNATURES
    if unknown:
        raise ValueError(f"unknown production signatures: {sorted(unknown)}")
    return normalized


def require_state(state: int) -> int:
    if type(state) is not int or state < 0 or state > STATE_MASK:
        raise ValueError(f"state must be an unsigned {CYCLE_SIZE}-bit integer")
    return state


def event_at(state: int, locus: int) -> int:
    require_state(state)
    if type(locus) is not int:
        raise TypeError("locus must be an integer")
    return (state >> (locus % CYCLE_SIZE)) & 1


def state_from_active(active_loci: Iterable[int]) -> int:
    state = 0
    for locus in active_loci:
        if type(locus) is not int:
            raise TypeError("active locus must be an integer")
        state |= 1 << (locus % CYCLE_SIZE)
    return state


def active_loci(state: int) -> tuple[int, ...]:
    require_state(state)
    return tuple(index for index in range(CYCLE_SIZE) if (state >> index) & 1)


def step(state: int, rows: Iterable[str]) -> int:
    """Apply one synchronous production layer on the frozen directed cycle."""

    require_state(state)
    production_rows = normalize_rows(rows)
    output = 0
    for locus in range(CYCLE_SIZE):
        self_value = (state >> locus) & 1
        predecessor_value = (state >> ((locus - 1) % CYCLE_SIZE)) & 1
        signature = f"{self_value}{predecessor_value}"
        if signature in production_rows:
            output |= 1 << locus
    return output


def run_trajectory(initial_state: int, rows: Iterable[str], last_layer: int) -> tuple[int, ...]:
    require_state(initial_state)
    if type(last_layer) is not int or last_layer < 0:
        raise ValueError("last_layer must be a nonnegative integer")
    production_rows = normalize_rows(rows)
    states = [initial_state]
    for _ in range(last_layer):
        states.append(step(states[-1], production_rows))
    return tuple(states)


def translate_state(state: int, offset: int) -> int:
    require_state(state)
    if type(offset) is not int:
        raise TypeError("offset must be an integer")
    shift = offset % CYCLE_SIZE
    if shift == 0:
        return state
    return ((state << shift) | (state >> (CYCLE_SIZE - shift))) & STATE_MASK
