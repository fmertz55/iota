"""Canonical enumeration of the complete eight-row grammar family."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import combinations
from typing import Iterator

from .dynamics import normalize_rows
from .protocol import GRAMMAR_ID, INPUT_PORTS, SIGNATURE_ORDER


ROW_SIGNATURES = SIGNATURE_ORDER
RULE_ORDER = SIGNATURE_ORDER


def canonical_rows(rows: Iterable[str]) -> tuple[str, ...]:
    selected = normalize_rows(rows)
    return tuple(signature for signature in SIGNATURE_ORDER if signature in selected)


def enumerate_rule_rows() -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for law_count in range(len(SIGNATURE_ORDER) + 1):
        rows.extend(combinations(SIGNATURE_ORDER, law_count))
    return tuple(rows)


def candidate_id(rows: Iterable[str]) -> str:
    ordered = canonical_rows(rows)
    suffix = "NONE" if not ordered else "-".join(ordered)
    return f"MIR-RS-P2-L{len(ordered)}-{suffix}"


def law_records(rows: Iterable[str]) -> list[dict[str, object]]:
    return [
        {
            "id": f"L_{signature}",
            "operator": "emit_one_if_neighborhood_signature",
            "signature": signature,
            "governed_degree": "event",
            "input_ports": list(INPUT_PORTS),
            "duration_ticks": 1,
            "write_count": 1,
            "grammar_id": GRAMMAR_ID,
        }
        for signature in canonical_rows(rows)
    ]


def wolfram_code(rows: Iterable[str]) -> int:
    """Return the conventional ECA code for a selected output-one row set."""

    return sum(1 << int(signature, 2) for signature in canonical_rows(rows))


def reflected_rows(rows: Iterable[str]) -> tuple[str, ...]:
    """Swap predecessor/successor ports and return the canonical row tuple."""

    return canonical_rows(signature[::-1] for signature in canonical_rows(rows))


def iter_candidate_rows() -> Iterator[tuple[str, tuple[str, ...]]]:
    for rows in enumerate_rule_rows():
        yield candidate_id(rows), rows
