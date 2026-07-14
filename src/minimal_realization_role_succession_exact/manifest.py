"""Canonical allocation of the parent's ten unresolved candidates."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from src.minimal_realization_role_succession.manifest import (
    canonical_json,
    read_jsonl as read_parent_candidate_jsonl,
    sha256_bytes,
    sha256_file,
)
from src.minimal_realization_role_succession.runner import (
    load_canonical_json,
    validate_result_ledger,
)

from .protocol import (
    PARENT_RESOURCE_BOUNDARY,
    PARENT_RESOURCE_CENSORED_COUNT,
    PARENT_RESULT_REF,
    PARENT_RESULT_SHA256,
    PROTOCOL_VERSION,
    SEARCH_ID,
)


class ExactManifestError(ValueError):
    pass


def _record_sha256(record: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(record).encode("ascii"))


def parent_censor_predicate(record: dict[str, Any]) -> bool:
    """The frozen, complete predicate selecting continuation candidates."""

    return (
        record.get("evaluation_status") == "resource_censored_before_recurrence"
        and record.get("last_assessed_layer") == PARENT_RESOURCE_BOUNDARY
        and record.get("resource_limit") == PARENT_RESOURCE_BOUNDARY
        and record.get("first_complete_pass") is None
        and record.get("recurrence") is None
    )


def build_continuation_record(
    parent_index: int,
    parent_record: dict[str, Any],
) -> dict[str, Any]:
    if type(parent_index) is not int or parent_index < 0:
        raise ExactManifestError("parent candidate index is invalid")
    if not parent_censor_predicate(parent_record):
        raise ExactManifestError("parent record does not satisfy the frozen censor predicate")
    required = {
        "candidate_id",
        "candidate_sha256",
        "production_rows",
        "wolfram_rule_number",
        "atomic_n_l",
        "trace_sha256",
        "first_role",
        "first_successor",
        "first_intervention_eligible",
        "pre_wrap_classification",
    }
    if not required <= set(parent_record):
        raise ExactManifestError("parent censor record is incomplete")
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "development_sealed_exact_closure",
        "parent_candidate_index": parent_index,
        "candidate_id": parent_record["candidate_id"],
        "candidate_sha256": parent_record["candidate_sha256"],
        "parent_record_sha256": _record_sha256(parent_record),
        "production_rows": parent_record["production_rows"],
        "wolfram_rule_number": parent_record["wolfram_rule_number"],
        "atomic_n_l": parent_record["atomic_n_l"],
        "parent_boundary_layer": PARENT_RESOURCE_BOUNDARY,
        "parent_prefix_trace_sha256": parent_record["trace_sha256"],
        "inherited_first_role": parent_record["first_role"],
        "inherited_first_successor": parent_record["first_successor"],
        "inherited_first_intervention_eligible": parent_record[
            "first_intervention_eligible"
        ],
        "inherited_pre_wrap_classification": parent_record[
            "pre_wrap_classification"
        ],
    }


def compile_continuation_candidates(
    parent_ledger: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    records = parent_ledger.get("candidate_results")
    if type(records) is not list:
        raise ExactManifestError("parent result lacks candidate records")
    selected = tuple(
        build_continuation_record(index, record)
        for index, record in enumerate(records)
        if type(record) is dict and parent_censor_predicate(record)
    )
    if len(selected) != PARENT_RESOURCE_CENSORED_COUNT:
        raise ExactManifestError("parent censor predicate did not select exactly ten records")
    indices = tuple(record["parent_candidate_index"] for record in selected)
    if indices != tuple(sorted(indices)) or len(set(indices)) != len(indices):
        raise ExactManifestError("continuation allocation is not in unique parent order")
    return selected


def load_and_validate_parent(root: Path) -> dict[str, Any]:
    path = root.resolve() / PARENT_RESULT_REF
    if sha256_file(path) != PARENT_RESULT_SHA256:
        raise ExactManifestError("parent result hash differs from the frozen binding")
    ledger = load_canonical_json(path)
    candidate_binding = ledger.get("candidate_manifest")
    if (
        type(candidate_binding) is not dict
        or set(candidate_binding) != {"path", "sha256"}
        or type(candidate_binding["path"]) is not str
    ):
        raise ExactManifestError("parent candidate-manifest binding is invalid")
    candidate_path = root.resolve() / candidate_binding["path"]
    if sha256_file(candidate_path) != candidate_binding["sha256"]:
        raise ExactManifestError("parent candidate manifest hash mismatch")
    parent_candidates = read_parent_candidate_jsonl(candidate_path)
    validate_result_ledger(ledger, parent_candidates)
    return ledger


def continuation_record_sha256(record: dict[str, Any]) -> str:
    return _record_sha256(record)


def manifest_bytes(records: Iterable[dict[str, Any]]) -> bytes:
    return "".join(canonical_json(record) + "\n" for record in records).encode("ascii")


def write_jsonl_once(path: Path, records: Iterable[dict[str, Any]]) -> None:
    if path.exists():
        raise ExactManifestError(f"refusing to overwrite manifest: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = manifest_bytes(records)
    with path.open("xb") as handle:
        handle.write(data)


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ExactManifestError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ExactManifestError(f"non-finite number {value!r} is forbidden")


def read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        text = path.read_text(encoding="ascii")
    except OSError as exc:
        raise ExactManifestError(f"{path}: {exc}") from exc
    if not text or not text.endswith("\n"):
        raise ExactManifestError("continuation manifest must be nonempty and LF terminated")
    output: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        try:
            value = json.loads(
                line,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
        except json.JSONDecodeError as exc:
            raise ExactManifestError(f"{path}:{number}: {exc}") from exc
        if type(value) is not dict or line != canonical_json(value) + "\n":
            raise ExactManifestError(f"{path}:{number}: noncanonical record")
        output.append(value)
    return tuple(output)


def validate_continuation_manifest(
    records: Iterable[dict[str, Any]],
    parent_ledger: dict[str, Any],
) -> None:
    actual = tuple(records)
    expected = compile_continuation_candidates(parent_ledger)
    if manifest_bytes(actual) != manifest_bytes(expected):
        raise ExactManifestError("manifest is not the exact parent-derived allocation")


def sha256_manifest_record(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(record).encode("ascii")).hexdigest()
