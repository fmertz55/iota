"""Canonical, outcome-free candidate manifests for role-succession search."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .protocol import (
    BASE_CONTRACT_VERSION,
    CANONICAL_ORIGIN,
    DATA_CLASS,
    DETECTOR_ID,
    EMBEDDING_CYCLE_SIZES,
    FORMATION_HORIZON,
    GRAMMAR_ID,
    INPUT_PORTS,
    PRIMARY_CYCLE_SIZE,
    PROTOCOL_VERSION,
    SEARCH_ID,
)
from .search import candidate_id, enumerate_rule_rows, law_records, wolfram_code


class ManifestError(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ManifestError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ManifestError(f"non-finite JSON number {value!r} is forbidden")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_sha256(candidate: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(candidate).encode("ascii"))


def build_candidate(rows: tuple[str, ...]) -> dict[str, Any]:
    """Build one candidate record without evaluating its dynamics."""

    excluded = not rows
    record: dict[str, Any] = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "grammar_id": GRAMMAR_ID,
        "candidate_id": candidate_id(rows),
        "wolfram_rule_number": wolfram_code(rows),
        "status": "analytically_excluded" if excluded else "development_sealed",
        "primitive_accounting": {
            "normalized_n_p": 2,
            "dynamic_kind_count": 1,
            "relation_kind_count": 1,
            "exogenous_kind_count": 0,
            "candidate_supplied_bits": 0,
            "seed_nonquiescent_instances": 1,
            "dynamic_storage_bits_per_layer": PRIMARY_CYCLE_SIZE,
            "oriented_relation_instances": PRIMARY_CYCLE_SIZE,
            "relation_incidence_reads_per_site": 2,
            "event_reads_per_site": 3,
            "site_evaluations_per_layer": PRIMARY_CYCLE_SIZE,
            "local_signature_fan_in": 3,
            "causal_traversal_directions": 2,
        },
        "primitives": [
            {"id": "event", "scope": "dynamic", "alphabet": [0, 1]},
            {
                "id": "oriented_cycle_edge",
                "scope": "relation",
                "alphabet": [0, 1],
                "incidence_ports": ["predecessor", "successor"],
            },
        ],
        "laws": law_records(rows),
        "clock": {
            "tick_unit": "elementary_causal_layer",
            "read_layer": "t",
            "write_layer": "t+1",
            "fresh_output_default": 0,
            "within_tick_cascade": False,
            "maximum_relation_hops_per_tick": 1,
        },
        "substrate": {
            "topology": "oriented_periodic_cycle",
            "cycle_size": PRIMARY_CYCLE_SIZE,
            "relation_definition": "edge(i,j)=1 iff j=(i+1) mod 64",
            "input_ports": list(INPUT_PORTS),
            "scheduler": "synchronous_atomic_layer",
        },
        "initial_condition": {
            "family": "canonical_single_active_event",
            "canonical_origin": CANONICAL_ORIGIN,
            "active_count": 1,
            "all_other_events": 0,
            "matched_comparator": "all_zero",
            "contains_registered_role": False,
        },
        "proto_object_detector": {
            "id": DETECTOR_ID,
            "formation_horizon": FORMATION_HORIZON,
            "read_only": True,
        },
        "embedding_crosschecks": {
            "cycle_sizes": list(EMBEDDING_CYCLE_SIZES),
            "pre_wrap_rule": "exact centered embedding through layer 31",
            "conditional_rule": (
                "every primary passer is evaluated through its C64 pass layer before "
                "result serialization"
            ),
        },
        "maps": {
            "initialization": "canonical_single_active_event",
            "readout": DETECTOR_ID,
            "intervention": "matched_dyad_relocation",
        },
        "randomness": {"kind": "none", "exogenous_channel_count": 0},
        "data_class": DATA_CLASS,
    }
    if excluded:
        record["exclusion_reason"] = (
            "With no registered production row, the fresh layer is all zero after "
            "the singleton initial condition and cannot form the registered dyad."
        )
    return record


def compile_candidates() -> tuple[dict[str, Any], ...]:
    return tuple(build_candidate(rows) for rows in enumerate_rule_rows())


def manifest_bytes(records: Iterable[dict[str, Any]]) -> bytes:
    return "".join(canonical_json(record) + "\n" for record in records).encode("ascii")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    if path.exists():
        raise ManifestError(f"refusing to overwrite candidate manifest: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = manifest_bytes(records)
    with path.open("xb") as handle:
        handle.write(data)


def read_jsonl_bytes(data: bytes, source: str = "<bytes>") -> tuple[dict[str, Any], ...]:
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ManifestError(f"{source}: manifest must be ASCII: {exc}") from exc
    if text and not text.endswith("\n"):
        raise ManifestError(f"{source}: manifest must end with LF")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        if not line.strip():
            raise ManifestError(f"{source}:{line_number}: blank lines are forbidden")
        try:
            record = json.loads(
                line,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
        except json.JSONDecodeError as exc:
            raise ManifestError(f"{source}:{line_number}: {exc}") from exc
        if type(record) is not dict:
            raise ManifestError(f"{source}:{line_number}: record must be an object")
        if line != canonical_json(record) + "\n":
            raise ManifestError(f"{source}:{line_number}: noncanonical JSONL")
        records.append(record)
    return tuple(records)


def read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        return read_jsonl_bytes(path.read_bytes(), str(path))
    except OSError as exc:
        raise ManifestError(f"{path}: {exc}") from exc


def validate_candidate_manifest(records: Iterable[dict[str, Any]]) -> None:
    actual = tuple(records)
    expected = compile_candidates()
    if tuple(map(canonical_json, actual)) != tuple(map(canonical_json, expected)):
        raise ManifestError("candidate manifest is not the exact canonical 256-record family")
