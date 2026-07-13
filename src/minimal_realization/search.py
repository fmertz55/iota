from __future__ import annotations

from itertools import combinations
from typing import Iterator


SIGNATURE_ORDER = ("00", "01", "10", "11")


def enumerate_rule_rows() -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for law_count in range(len(SIGNATURE_ORDER) + 1):
        rows.extend(combinations(SIGNATURE_ORDER, law_count))
    return tuple(rows)


def candidate_id(rows: tuple[str, ...]) -> str:
    suffix = "NONE" if not rows else "-".join(rows)
    return f"MIR-P2-L{len(rows)}-{suffix}"


def law_records(rows: tuple[str, ...]) -> list[dict[str, object]]:
    return [
        {
            "id": f"L_{signature}",
            "operator": "emit_one_if_signature",
            "signature": signature,
            "governed_degree": "event",
            "input_ports": ["self", "predecessor"],
            "duration_ticks": 1,
            "write_count": 1,
        }
        for signature in rows
    ]


def iter_candidate_rows() -> Iterator[tuple[str, tuple[str, ...]]]:
    for rows in enumerate_rule_rows():
        yield candidate_id(rows), rows
