from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .search import candidate_id, enumerate_rule_rows, law_records
from .spec import canonical_json, sha256_file


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value!r} is forbidden")


def build_candidate(rows: tuple[str, ...], spec_dir: Path) -> dict[str, Any]:
    excluded = len(rows) == 0
    candidate: dict[str, Any] = {
        "contract_version": "0.2-draft",
        "grammar_id": "MIR-BOOLEAN-PRODUCTION-ROW-V0.2",
        "candidate_id": candidate_id(rows),
        "status": "analytically_excluded" if excluded else "development",
        "primitive_accounting": {
            "normalized_n_p": 2,
            "dynamic_kind_count": 1,
            "relation_kind_count": 1,
            "exogenous_kind_count": 0,
            "candidate_supplied_bits": 0,
            "seed_nonquiescent_instances": 1,
            "dynamic_storage_bits_per_layer": 64,
            "relation_instances": 64,
            "site_evaluations_per_layer": 64,
        },
        "primitives": [
            {"id": "event", "scope": "dynamic", "alphabet": [0, 1]},
            {"id": "predecessor", "scope": "relation", "alphabet": [0, 1]},
        ],
        "laws": law_records(rows),
        "clock": {
            "tick_unit": "elementary_causal_layer",
            "causal_layers_per_tick": 1,
            "within_tick_cascade": False,
            "max_relation_hops_per_tick": 1,
        },
        "substrate": {
            "ref": "topology.json",
            "sha256": sha256_file(spec_dir / "topology.json"),
        },
        "initial_condition": {
            "family": "single_active_translation",
            "canonical_origin": 0,
            "active_count": 1,
            "description_bits": 0,
            "contains_proto_object": False,
        },
        "proto_object_detector": {
            "ref": "proto_object_detector.json",
            "version": "0.2-draft",
            "sha256": sha256_file(spec_dir / "proto_object_detector.json"),
        },
        "maps": {
            "initialization": "single_active_translation",
            "readout": "MIR-ISOLATED-DYAD-OUTWARD-EFFECT-V0.2",
            "intervention": "matched_dyad_relocation",
        },
        "randomness": {"kind": "none", "exogenous_channel_count": 0},
        "data_class": "development",
    }
    if excluded:
        candidate["exclusion_reason"] = "No registered production row can emit a nonquiescent event after layer zero."
    return candidate


def compile_candidates(spec_dir: Path) -> tuple[dict[str, Any], ...]:
    return tuple(build_candidate(rows, spec_dir) for rows in enumerate_rule_rows())


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(canonical_json(record))
            handle.write("\n")


def read_jsonl_bytes(data: bytes, source: str) -> tuple[dict[str, Any], ...]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{source}: invalid UTF-8: {exc}") from exc
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        if not line.strip():
            raise ValueError(f"{source}:{line_number}: blank lines are forbidden")
        value = json.loads(
            line,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
        if type(value) is not dict:
            raise ValueError(f"{source}:{line_number}: record must be an object")
        if line != canonical_json(value) + "\n":
            raise ValueError(f"{source}:{line_number}: record is not canonical JSONL")
        records.append(value)
    return tuple(records)


def read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    return read_jsonl_bytes(path.read_bytes(), str(path))
