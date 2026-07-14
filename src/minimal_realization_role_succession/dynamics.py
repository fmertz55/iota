"""Exact synchronous dynamics for the role-succession grammar.

The production signature at a locus is ordered
``(predecessor, self, successor)``.  A selected truth-table row emits one at
that locus in a fresh output layer; an unselected row emits zero.  All reads
therefore come from the same input layer.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
from typing import Any

from .protocol import PRIMARY_CYCLE_SIZE, SIGNATURE_ORDER


CYCLE_SIZE = PRIMARY_CYCLE_SIZE
STATE_MASK = (1 << CYCLE_SIZE) - 1
VALID_SIGNATURES = frozenset(SIGNATURE_ORDER)


def require_cycle_size(cycle_size: int = CYCLE_SIZE) -> int:
    """Validate and return a cycle size supported by the local predicates."""

    if type(cycle_size) is not int or cycle_size < 4:
        raise ValueError("cycle_size must be an integer of at least four")
    return cycle_size


@lru_cache(maxsize=16, typed=True)
def state_mask(cycle_size: int = CYCLE_SIZE) -> int:
    return (1 << require_cycle_size(cycle_size)) - 1


@lru_cache(maxsize=512)
def _normalize_frozen_rows(rows: frozenset[Any]) -> frozenset[str]:
    unknown = rows - VALID_SIGNATURES
    if unknown:
        rendered = sorted((repr(value) for value in unknown))
        raise ValueError(f"unknown production signatures: {rendered}")
    return rows  # type: ignore[return-value]


@lru_cache(maxsize=512)
def _normalize_tuple_rows(rows: tuple[Any, ...]) -> frozenset[str]:
    return _normalize_frozen_rows(frozenset(rows))


def normalize_rows(rows: Iterable[str]) -> frozenset[str]:
    """Return an interned, validated production-row set.

    Registered traces repeatedly reuse one tuple or frozen set.  Caching both
    forms removes row parsing and allocation from the per-layer hot path while
    retaining the public iterable API for fixtures and validation calls.
    """

    try:
        if type(rows) is frozenset:
            return _normalize_frozen_rows(rows)
        if type(rows) is tuple:
            return _normalize_tuple_rows(rows)
        normalized = frozenset(rows)
    except TypeError as exc:
        raise TypeError("production rows must be an iterable of signatures") from exc
    return _normalize_frozen_rows(normalized)


@lru_cache(maxsize=256)
def _compiled_row_codes(rows: frozenset[str]) -> tuple[int, ...]:
    """Compile selected signatures to three-bit truth-table indices."""

    return tuple(int(signature, 2) for signature in rows)


def require_state(state: int, cycle_size: int = CYCLE_SIZE) -> int:
    size = require_cycle_size(cycle_size)
    if type(state) is not int or state < 0 or state > state_mask(size):
        raise ValueError(f"state must be an unsigned {size}-bit integer")
    return state


def event_at(state: int, locus: int, cycle_size: int = CYCLE_SIZE) -> int:
    size = require_cycle_size(cycle_size)
    require_state(state, size)
    if type(locus) is not int:
        raise TypeError("locus must be an integer")
    return (state >> (locus % size)) & 1


def state_from_active(
    active_loci: Iterable[int],
    cycle_size: int = CYCLE_SIZE,
) -> int:
    size = require_cycle_size(cycle_size)
    state = 0
    for locus in active_loci:
        if type(locus) is not int:
            raise TypeError("active locus must be an integer")
        state |= 1 << (locus % size)
    return state


def active_loci(state: int, cycle_size: int = CYCLE_SIZE) -> tuple[int, ...]:
    size = require_cycle_size(cycle_size)
    require_state(state, size)
    return tuple(index for index in range(size) if (state >> index) & 1)


def signature_at(state: int, locus: int, cycle_size: int = CYCLE_SIZE) -> str:
    """Return the frozen predecessor/self/successor signature at ``locus``."""

    size = require_cycle_size(cycle_size)
    require_state(state, size)
    if type(locus) is not int:
        raise TypeError("locus must be an integer")
    predecessor = (state >> ((locus - 1) % size)) & 1
    self_value = (state >> (locus % size)) & 1
    successor = (state >> ((locus + 1) % size)) & 1
    return f"{predecessor}{self_value}{successor}"


def step(
    state: int,
    rows: Iterable[str],
    cycle_size: int = CYCLE_SIZE,
) -> int:
    """Apply one fresh-output synchronous production layer on a cycle."""

    size = require_cycle_size(cycle_size)
    require_state(state, size)
    production_rows = normalize_rows(rows)
    row_codes = _compiled_row_codes(production_rows)
    mask = state_mask(size)
    predecessor_values = ((state << 1) | (state >> (size - 1))) & mask
    successor_values = ((state >> 1) | ((state & 1) << (size - 1))) & mask
    output = 0
    for code in row_codes:
        predecessor_mask = predecessor_values if code & 0b100 else ~predecessor_values
        self_mask = state if code & 0b010 else ~state
        successor_mask = successor_values if code & 0b001 else ~successor_values
        output |= predecessor_mask & self_mask & successor_mask
    return output & mask


def run_trajectory(
    initial_state: int,
    rows: Iterable[str],
    last_layer: int,
    cycle_size: int = CYCLE_SIZE,
) -> tuple[int, ...]:
    size = require_cycle_size(cycle_size)
    require_state(initial_state, size)
    if type(last_layer) is not int or last_layer < 0:
        raise ValueError("last_layer must be a nonnegative integer")
    production_rows = normalize_rows(rows)
    states = [initial_state]
    for _ in range(last_layer):
        states.append(step(states[-1], production_rows, size))
    return tuple(states)


def translate_state(
    state: int,
    offset: int,
    cycle_size: int = CYCLE_SIZE,
) -> int:
    size = require_cycle_size(cycle_size)
    require_state(state, size)
    if type(offset) is not int:
        raise TypeError("offset must be an integer")
    shift = offset % size
    if shift == 0:
        return state
    return ((state << shift) | (state >> (size - shift))) & state_mask(size)


def reflect_state(state: int, cycle_size: int = CYCLE_SIZE) -> int:
    """Reflect a cycle state through locus zero (``x -> -x``)."""

    size = require_cycle_size(cycle_size)
    require_state(state, size)
    reflected = 0
    for locus in active_loci(state, size):
        reflected |= 1 << ((-locus) % size)
    return reflected


def canonical_initial_state(
    origin: int = 0,
    cycle_size: int = CYCLE_SIZE,
) -> int:
    """Return the registered one-event initial state without evolving it."""

    size = require_cycle_size(cycle_size)
    if type(origin) is not int or not 0 <= origin < size:
        raise ValueError("origin must be a cycle locus")
    return state_from_active((origin,), size)
