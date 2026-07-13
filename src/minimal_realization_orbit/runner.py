from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from .engine import (
    CONE_SATURATION_LAYER,
    FIRST_NEW_OUTCOME_LAYER,
    MAX_LAYERS_PER_CANDIDATE,
    PARENT_CENSORING_LAYER,
    ExactOrbitOutcome,
    OrbitRunError,
)


PROTOCOL_VERSION = "0.1-draft"
BASE_CONTRACT_VERSION = "0.2-draft"
SEARCH_ID = "MIR-EXACT-ORBIT-001"
RUN_ID = "MIR-EXACT-ORBIT-001-DEVELOPMENT"
DETECTOR_ID = "MIR-ISOLATED-DYAD-OUTWARD-EFFECT-EXACT-ORBIT-V0.1"
INHERITED_DETECTOR_ID = "MIR-ISOLATED-DYAD-OUTWARD-EFFECT-V0.2"
RULE_ORDER = ("00", "01", "10", "11")
SPEC_DIR_REF = "specs/icp_minimal_realization_exact_orbit/v0.1-draft"
PROTOCOL_REF = f"{SPEC_DIR_REF}/protocol.json"
RESULT_SCHEMA_REF = f"{SPEC_DIR_REF}/result.schema.json"
CANDIDATE_MANIFEST_REF = (
    "experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/"
    "development_candidates.jsonl"
)
BASE_OUTCOME_SEAL_REF = (
    "experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/"
    "outcome_sealed_manifest.json"
)
PARENT_BOUNDED_RESULT_REF = (
    "output/minimal_realization/MIR-REFERENCE-SEARCH-001/development_results.json"
)
OUTCOME_SEAL_REF = (
    "experiments/minimal_realization/MIR-EXACT-ORBIT-001/"
    "outcome_sealed_manifest.json"
)
OPEN_SEAL_REF = (
    "experiments/minimal_realization/MIR-EXACT-ORBIT-001/"
    "exact_orbit_open_manifest.json"
)
RESULT_PATH = Path(
    "output/minimal_realization/MIR-EXACT-ORBIT-001/exact_orbit_results.json"
)


class OrbitLedgerError(ValueError):
    pass


OrbitEvaluator = Callable[
    [dict[str, Any], tuple[str, ...], dict[str, Any]],
    ExactOrbitOutcome,
]


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise OrbitLedgerError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise OrbitLedgerError(f"non-finite JSON number {value!r} is forbidden")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def strict_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON-like values without treating Booleans as integers."""

    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return set(left) == set(right) and all(
            strict_json_equal(left[key], right[key]) for key in left
        )
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(
            strict_json_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return left == right


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_canonical_json_bytes(data: bytes, source: str) -> dict[str, Any]:
    try:
        text = data.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OrbitLedgerError(f"{source}: {exc}") from exc
    if type(value) is not dict:
        raise OrbitLedgerError(f"{source}: root must be an object")
    if text != canonical_json(value) + "\n":
        raise OrbitLedgerError(f"{source}: file is not byte-canonical JSON")
    return value


def load_canonical_json(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise OrbitLedgerError(f"{path}: {exc}") from exc
    return load_canonical_json_bytes(data, str(path))


def _require_digest(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise OrbitLedgerError(f"{label} is not a lowercase SHA-256 digest")
    return value


def require_binding(value: Any, label: str) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"path", "sha256"}:
        raise OrbitLedgerError(f"{label} binding shape mismatch")
    if type(value["path"]) is not str or not value["path"]:
        raise OrbitLedgerError(f"{label} path is invalid")
    _require_digest(value["sha256"], f"{label} hash")
    return value


def expected_candidate_rows() -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = [()]
    for law_count in range(1, len(RULE_ORDER) + 1):
        rows.extend(itertools.combinations(RULE_ORDER, law_count))
    return tuple(rows)


def expected_candidate_id(rows: tuple[str, ...]) -> str:
    if not rows:
        return "MIR-P2-L0-NONE"
    return f"MIR-P2-L{len(rows)}-{'-'.join(rows)}"


def read_candidate_snapshot_bytes(
    data: bytes,
    source: str,
) -> tuple[dict[str, Any], ...]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OrbitLedgerError(f"{source}: {exc}") from exc
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        if not line.strip():
            raise OrbitLedgerError(f"{source}:{line_number}: blank line is forbidden")
        try:
            value = json.loads(
                line,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
        except json.JSONDecodeError as exc:
            raise OrbitLedgerError(f"{source}:{line_number}: {exc}") from exc
        if type(value) is not dict:
            raise OrbitLedgerError(f"{source}:{line_number}: record must be an object")
        if line != canonical_json(value) + "\n":
            raise OrbitLedgerError(f"{source}:{line_number}: noncanonical JSONL record")
        records.append(value)

    expected_rows = expected_candidate_rows()
    if len(records) != len(expected_rows):
        raise OrbitLedgerError("candidate snapshot must contain exactly 16 records")
    for candidate, rows in zip(records, expected_rows):
        if candidate.get("contract_version") != BASE_CONTRACT_VERSION:
            raise OrbitLedgerError("candidate contract version mismatch")
        if candidate.get("candidate_id") != expected_candidate_id(rows):
            raise OrbitLedgerError("candidate order or identity mismatch")
        if candidate.get("grammar_id") != "MIR-BOOLEAN-PRODUCTION-ROW-V0.2":
            raise OrbitLedgerError("candidate grammar mismatch")
        laws = candidate.get("laws")
        if type(laws) is not list:
            raise OrbitLedgerError("candidate laws must be a list")
        signatures = tuple(law.get("signature") for law in laws if type(law) is dict)
        if signatures != rows or len(laws) != len(rows):
            raise OrbitLedgerError("candidate production rows mismatch")
        normalized_n_p = candidate.get("primitive_accounting", {}).get("normalized_n_p")
        if type(normalized_n_p) is not int or normalized_n_p != 2:
            raise OrbitLedgerError("candidate normalized primitive count mismatch")
        expected_status = "analytically_excluded" if not rows else "development"
        if candidate.get("status") != expected_status:
            raise OrbitLedgerError("candidate status mismatch")
    return tuple(records)


def read_candidate_snapshot(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise OrbitLedgerError(f"{path}: {exc}") from exc
    return read_candidate_snapshot_bytes(data, str(path))


def candidate_sha256(candidate: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(candidate).encode("utf-8")).hexdigest()


def candidate_trace_domain(candidate: dict[str, Any]) -> bytes:
    candidate_id = candidate.get("candidate_id")
    if type(candidate_id) is not str or not candidate_id:
        raise OrbitLedgerError("candidate id is invalid for trace-domain binding")
    return (
        f"{SEARCH_ID}\0{candidate_id}\0{candidate_sha256(candidate)}"
    ).encode("ascii")


def validate_parent_bounded_result(
    ledger: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
) -> None:
    if ledger.get("search_id") != "MIR-REFERENCE-SEARCH-001":
        raise OrbitLedgerError("parent result search identity mismatch")
    if ledger.get("run_id") != "MIR-REFERENCE-SEARCH-001-DEVELOPMENT":
        raise OrbitLedgerError("parent result run identity mismatch")
    formation_horizon = ledger.get("formation_horizon_ticks")
    if type(formation_horizon) is not int or formation_horizon != PARENT_CENSORING_LAYER:
        raise OrbitLedgerError("parent result horizon mismatch")
    if not strict_json_equal(ledger.get("translation_offsets"), list(range(48))):
        raise OrbitLedgerError("parent result translation allocation mismatch")
    if ledger.get("held_out_accessed") is not False:
        raise OrbitLedgerError("parent result reports reserved-offset access")
    if ledger.get("held_out_offsets_evaluated") != []:
        raise OrbitLedgerError("parent result contains reserved offsets")
    results = ledger.get("candidate_results")
    canonical_candidates = tuple(candidates)
    if type(results) is not list or len(results) != 16 or len(canonical_candidates) != 16:
        raise OrbitLedgerError("parent result candidate allocation mismatch")
    for index, (result, candidate) in enumerate(zip(results, canonical_candidates)):
        if type(result) is not dict:
            raise OrbitLedgerError("parent candidate result must be an object")
        if result.get("candidate_id") != candidate.get("candidate_id"):
            raise OrbitLedgerError("parent candidate order mismatch")
        if result.get("candidate_sha256") != candidate_sha256(candidate):
            raise OrbitLedgerError("parent candidate hash mismatch")
        if index == 0:
            if result.get("evaluation_status") != "analytically_excluded":
                raise OrbitLedgerError("parent zero-law exclusion mismatch")
        elif (
            result.get("evaluation_status") != "right_censored_T_proto_gt_16"
            or result.get("pass_by_H16") is not False
            or result.get("t_proto") is not None
            or type(result.get("translations_evaluated")) is not int
            or result.get("translations_evaluated") != 48
        ):
            raise OrbitLedgerError("parent dynamic result was not the registered H=16 censoring")
        if index > 0:
            translations = result.get("translations")
            if type(translations) is not list or len(translations) != 48:
                raise OrbitLedgerError("parent dynamic result translation ledger mismatch")
            expected_origin_keys = {
                "translation_offset",
                "status",
                "t_proto",
                "anchor",
                "anchor_offset_from_seed",
                "successor_anchor",
                "successor_anchor_offset_from_seed",
                "sham_future",
                "breaking_future",
            }
            origin = translations[0]
            if (
                type(origin) is not dict
                or set(origin) != expected_origin_keys
                or type(origin.get("translation_offset")) is not int
                or origin.get("translation_offset") != 0
                or origin.get("status") != "right_censored_T_proto_gt_16"
                or any(origin[key] is not None for key in expected_origin_keys - {"translation_offset", "status"})
            ):
                raise OrbitLedgerError("parent canonical-origin record mismatch")
    if ledger.get("bounded_winner_candidate_ids") != []:
        raise OrbitLedgerError("parent result unexpectedly contains a bounded winner")


def _hex_state(state: int) -> str:
    if type(state) is not int or not 0 <= state < (1 << 64):
        raise OrbitLedgerError("state is outside the unsigned 64-bit range")
    return f"{state:016x}"


def _role_witness(value: Optional[tuple[int, int]]) -> Optional[dict[str, int]]:
    if value is None:
        return None
    layer, anchor = value
    return {"layer": layer, "anchor": anchor}


def _successor_witness(
    value: Optional[tuple[int, int, int]],
) -> Optional[dict[str, int]]:
    if value is None:
        return None
    layer, anchor, successor = value
    return {"layer": layer, "anchor": anchor, "successor_anchor": successor}


def _dynamic_candidate_record(
    candidate: dict[str, Any],
    rows: tuple[str, ...],
    outcome: ExactOrbitOutcome,
) -> dict[str, Any]:
    if outcome.status == "exact_pass_on_fixed_orbit":
        t_proto_status = "finite"
        if outcome.pass_witness is None or outcome.recurrence is not None:
            raise OrbitLedgerError("passing orbit outcome is internally inconsistent")
        (
            layer,
            anchor,
            successor,
            sham_future,
            breaking_future,
            seeded_state,
            baseline_state,
        ) = outcome.pass_witness
        pass_witness: Optional[dict[str, Any]] = {
            "layer": layer,
            "anchor": anchor,
            "successor_anchor": successor,
            "sham_future": sham_future,
            "breaking_future": breaking_future,
            "seeded_state_hex": _hex_state(seeded_state),
            "baseline_state_hex": _hex_state(baseline_state),
        }
        recurrence = None
        resource_limit = None
    elif outcome.status == "recurrence_excluded_on_fixed_orbit":
        t_proto_status = "infinite_on_fixed_orbit"
        if outcome.recurrence is None or outcome.pass_witness is not None:
            raise OrbitLedgerError("recurrence orbit outcome is internally inconsistent")
        checkpoint, repeat, period, seeded_state, baseline_state = outcome.recurrence
        state = {
            "seeded_state_hex": _hex_state(seeded_state),
            "baseline_state_hex": _hex_state(baseline_state),
        }
        recurrence = {
            "cone_saturation_layer": CONE_SATURATION_LAYER,
            "checkpoint_layer": checkpoint,
            "repeat_layer": repeat,
            "period": period,
            "checkpoint_state": dict(state),
            "repeat_state": dict(state),
            "exact_full_state_equality": True,
        }
        pass_witness = None
        resource_limit = None
    elif outcome.status == "resource_censored_before_recurrence":
        t_proto_status = "right_censored_at_resource_limit"
        if outcome.recurrence is not None or outcome.pass_witness is not None:
            raise OrbitLedgerError("resource-censored outcome contains terminal proof fields")
        pass_witness = None
        recurrence = None
        resource_limit = MAX_LAYERS_PER_CANDIDATE
    else:
        raise OrbitLedgerError("unknown exact-orbit outcome status")

    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate_sha256(candidate),
        "normalized_n_p": 2,
        "atomic_n_l": len(rows),
        "production_rows": list(rows),
        "parent_H16_status": "right_censored_T_proto_gt_16",
        "evaluation_status": outcome.status,
        "t_proto_status": t_proto_status,
        "t_proto_exact": outcome.t_proto,
        "last_evaluated_layer": outcome.last_evaluated_layer,
        "first_role": _role_witness(outcome.first_role),
        "first_successor": _successor_witness(outcome.first_successor),
        "first_intervention_eligible": _successor_witness(
            outcome.first_intervention_eligible
        ),
        "pass_witness": pass_witness,
        "recurrence": recurrence,
        "resource_limit": resource_limit,
        "trace_sha256": outcome.trace_sha256,
        "exclusion_reason": None,
    }


def _excluded_candidate_record(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate_sha256(candidate),
        "normalized_n_p": 2,
        "atomic_n_l": 0,
        "production_rows": [],
        "parent_H16_status": "analytically_excluded",
        "evaluation_status": "analytically_excluded",
        "t_proto_status": "not_applicable",
        "t_proto_exact": None,
        "last_evaluated_layer": None,
        "first_role": None,
        "first_successor": None,
        "first_intervention_eligible": None,
        "pass_witness": None,
        "recurrence": None,
        "resource_limit": None,
        "trace_sha256": None,
        "exclusion_reason": candidate.get("exclusion_reason"),
    }


def run_exact_orbit_search(
    candidates: Iterable[dict[str, Any]],
    parent_result: dict[str, Any],
    evaluator: OrbitEvaluator,
) -> dict[str, Any]:
    ordered = tuple(candidates)
    if len(ordered) != 16:
        raise OrbitLedgerError("exact-orbit search requires all 16 candidate records")
    validate_parent_bounded_result(parent_result, ordered)
    parent_rows = parent_result["candidate_results"]
    results: list[dict[str, Any]] = []
    for index, (candidate, rows) in enumerate(zip(ordered, expected_candidate_rows())):
        if candidate.get("candidate_id") != expected_candidate_id(rows):
            raise OrbitLedgerError("candidate order changed before exact-orbit search")
        if not rows:
            results.append(_excluded_candidate_record(candidate))
            continue
        parent_origin_record = parent_rows[index]["translations"][0]
        outcome = evaluator(candidate, rows, parent_origin_record)
        if type(outcome) is not ExactOrbitOutcome:
            raise OrbitLedgerError("exact-orbit evaluator returned the wrong result type")
        results.append(_dynamic_candidate_record(candidate, rows, outcome))

    dynamic = results[1:]
    resource_censored = [
        row for row in dynamic if row["evaluation_status"] == "resource_censored_before_recurrence"
    ]
    passing = [row for row in dynamic if row["evaluation_status"] == "exact_pass_on_fixed_orbit"]
    if resource_censored:
        completion_status = "incomplete_resource_censored"
        conclusion = "resource_censored_incomplete"
        winners: list[str] = []
        resolved = False
    elif passing:
        completion_status = "complete_all_candidate_endpoints_resolved"
        conclusion = "one_or_more_exact_passes"
        best_law_count = min(row["atomic_n_l"] for row in passing)
        shell = [row for row in passing if row["atomic_n_l"] == best_law_count]
        best_t = min(row["t_proto_exact"] for row in shell)
        winners = [
            row["candidate_id"] for row in shell if row["t_proto_exact"] == best_t
        ]
        resolved = True
    else:
        completion_status = "complete_all_candidate_endpoints_resolved"
        conclusion = "all_dynamic_candidates_recurrence_excluded"
        winners = []
        resolved = True
    return {
        "completion_status": completion_status,
        "search_conclusion": conclusion,
        "all_dynamic_candidates_resolved": resolved,
        "exact_orbit_winner_candidate_ids": winners,
        "candidate_results": results,
    }


def build_result_ledger(
    *,
    root: Path,
    open_seal_path: Path,
    open_seal: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
    parent_result: dict[str, Any],
    evaluator: OrbitEvaluator,
) -> dict[str, Any]:
    search = run_exact_orbit_search(candidates, parent_result, evaluator)
    return {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": RUN_ID,
        "detector": DETECTOR_ID,
        "data_class": "development",
        "endpoint": "first_proto_object_or_exact_post_saturation_recurrence",
        "canonical_origin": 0,
        "translation_offsets_evaluated": [0],
        "reserved_translation_offsets_accessed": False,
        "reserved_translation_offsets_evaluated": [],
        "parent_H16_crosscheck": {
            "last_layer": PARENT_CENSORING_LAYER,
            "dynamic_candidate_count": 15,
            "all_right_censored_reproduced": True,
        },
        "first_new_outcome_layer": FIRST_NEW_OUTCOME_LAYER,
        "cone_saturation_layer": CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "recurrence_state": ["cone_phase", "seeded_state", "baseline_state"],
        "trace_digest_encoding": "sha256_domain_separated_decimal_length_layer_u64_seeded_u64_baseline_including_layer_0",
        "open_seal": {
            "path": open_seal_path.resolve().relative_to(root.resolve()).as_posix(),
            "sha256": sha256_file(open_seal_path),
        },
        "outcome_seal": dict(open_seal["parent_outcome_seal"]),
        "base_outcome_seal": dict(open_seal["base_outcome_seal"]),
        "candidate_manifest": dict(open_seal["candidate_manifest"]),
        "parent_bounded_result": dict(open_seal["parent_bounded_result"]),
        "result_schema": dict(open_seal["result_schema"]),
        "global_minimality_claimed": False,
        "alternative_grammar_excluded": False,
        **search,
    }


def _valid_state_hex(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 16
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_stage_witness(
    value: Any,
    keys: set[str],
    *,
    last_layer: int,
) -> None:
    if value is None:
        return
    if type(value) is not dict or set(value) != keys:
        raise OrbitLedgerError("stage witness shape mismatch")
    if type(value["layer"]) is not int or not 1 <= value["layer"] <= last_layer:
        raise OrbitLedgerError("stage witness layer mismatch")
    for key in keys - {"layer"}:
        if type(value[key]) is not int or not 0 <= value[key] < 64:
            raise OrbitLedgerError("stage witness anchor mismatch")


def validate_result_ledger(
    ledger: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
) -> None:
    expected_keys = {
        "base_contract_version",
        "protocol_version",
        "search_id",
        "run_id",
        "detector",
        "data_class",
        "endpoint",
        "canonical_origin",
        "translation_offsets_evaluated",
        "reserved_translation_offsets_accessed",
        "reserved_translation_offsets_evaluated",
        "parent_H16_crosscheck",
        "first_new_outcome_layer",
        "cone_saturation_layer",
        "max_layers_per_candidate",
        "recurrence_state",
        "trace_digest_encoding",
        "open_seal",
        "outcome_seal",
        "base_outcome_seal",
        "candidate_manifest",
        "parent_bounded_result",
        "result_schema",
        "global_minimality_claimed",
        "alternative_grammar_excluded",
        "completion_status",
        "search_conclusion",
        "all_dynamic_candidates_resolved",
        "exact_orbit_winner_candidate_ids",
        "candidate_results",
    }
    if set(ledger) != expected_keys:
        raise OrbitLedgerError("exact-orbit ledger has missing or unexpected keys")
    fixed = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": RUN_ID,
        "detector": DETECTOR_ID,
        "data_class": "development",
        "endpoint": "first_proto_object_or_exact_post_saturation_recurrence",
        "canonical_origin": 0,
        "translation_offsets_evaluated": [0],
        "reserved_translation_offsets_accessed": False,
        "reserved_translation_offsets_evaluated": [],
        "first_new_outcome_layer": FIRST_NEW_OUTCOME_LAYER,
        "cone_saturation_layer": CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "recurrence_state": ["cone_phase", "seeded_state", "baseline_state"],
        "trace_digest_encoding": "sha256_domain_separated_decimal_length_layer_u64_seeded_u64_baseline_including_layer_0",
        "global_minimality_claimed": False,
        "alternative_grammar_excluded": False,
    }
    for key, expected in fixed.items():
        if not strict_json_equal(ledger[key], expected):
            raise OrbitLedgerError(f"exact-orbit ledger {key} mismatch")
    if not strict_json_equal(ledger["parent_H16_crosscheck"], {
        "last_layer": 16,
        "dynamic_candidate_count": 15,
        "all_right_censored_reproduced": True,
    }):
        raise OrbitLedgerError("parent H=16 crosscheck mismatch")
    for name in (
        "open_seal",
        "outcome_seal",
        "base_outcome_seal",
        "candidate_manifest",
        "parent_bounded_result",
        "result_schema",
    ):
        require_binding(ledger[name], name)
    if ledger["result_schema"]["path"] != RESULT_SCHEMA_REF:
        raise OrbitLedgerError("result schema path mismatch")

    canonical_candidates = tuple(candidates)
    results = ledger["candidate_results"]
    if len(canonical_candidates) != 16 or type(results) is not list or len(results) != 16:
        raise OrbitLedgerError("candidate result allocation mismatch")
    statuses: list[str] = []
    passing: list[dict[str, Any]] = []
    for index, (result, candidate, rows) in enumerate(
        zip(results, canonical_candidates, expected_candidate_rows())
    ):
        expected_result_keys = {
            "candidate_id",
            "candidate_sha256",
            "normalized_n_p",
            "atomic_n_l",
            "production_rows",
            "parent_H16_status",
            "evaluation_status",
            "t_proto_status",
            "t_proto_exact",
            "last_evaluated_layer",
            "first_role",
            "first_successor",
            "first_intervention_eligible",
            "pass_witness",
            "recurrence",
            "resource_limit",
            "trace_sha256",
            "exclusion_reason",
        }
        if type(result) is not dict or set(result) != expected_result_keys:
            raise OrbitLedgerError("candidate result shape mismatch")
        expected_binding = {
            "candidate_id": expected_candidate_id(rows),
            "candidate_sha256": candidate_sha256(candidate),
            "normalized_n_p": 2,
            "atomic_n_l": len(rows),
            "production_rows": list(rows),
        }
        for key, expected in expected_binding.items():
            if not strict_json_equal(result[key], expected):
                raise OrbitLedgerError(f"candidate result {key} mismatch")
        status = result["evaluation_status"]
        statuses.append(status)
        if index == 0:
            if (
                status != "analytically_excluded"
                or result["parent_H16_status"] != "analytically_excluded"
                or result["t_proto_status"] != "not_applicable"
                or result["exclusion_reason"] != candidate.get("exclusion_reason")
                or any(
                    result[key] is not None
                    for key in (
                        "t_proto_exact",
                        "last_evaluated_layer",
                        "first_role",
                        "first_successor",
                        "first_intervention_eligible",
                        "pass_witness",
                        "recurrence",
                        "resource_limit",
                        "trace_sha256",
                    )
                )
            ):
                raise OrbitLedgerError("zero-law result mismatch")
            continue
        if result["parent_H16_status"] != "right_censored_T_proto_gt_16":
            raise OrbitLedgerError("dynamic parent status mismatch")
        if result["exclusion_reason"] is not None:
            raise OrbitLedgerError("dynamic candidate has an exclusion reason")
        last_layer = result["last_evaluated_layer"]
        if type(last_layer) is not int or not FIRST_NEW_OUTCOME_LAYER <= last_layer <= MAX_LAYERS_PER_CANDIDATE:
            raise OrbitLedgerError("dynamic last evaluated layer mismatch")
        _require_digest(result["trace_sha256"], "candidate trace digest")
        _validate_stage_witness(result["first_role"], {"layer", "anchor"}, last_layer=last_layer)
        _validate_stage_witness(
            result["first_successor"],
            {"layer", "anchor", "successor_anchor"},
            last_layer=last_layer,
        )
        _validate_stage_witness(
            result["first_intervention_eligible"],
            {"layer", "anchor", "successor_anchor"},
            last_layer=last_layer,
        )
        if result["first_successor"] is not None and result["first_role"] is None:
            raise OrbitLedgerError("succession witness lacks a role witness")
        if result["first_intervention_eligible"] is not None and result["first_successor"] is None:
            raise OrbitLedgerError("intervention witness lacks a succession witness")
        stage_layers = [
            witness["layer"]
            for witness in (
                result["first_role"],
                result["first_successor"],
                result["first_intervention_eligible"],
            )
            if witness is not None
        ]
        if stage_layers != sorted(stage_layers):
            raise OrbitLedgerError("stage witness chronology mismatch")

        if status == "exact_pass_on_fixed_orbit":
            passing.append(result)
            if (
                result["t_proto_status"] != "finite"
                or type(result["t_proto_exact"]) is not int
                or result["t_proto_exact"] <= PARENT_CENSORING_LAYER
                or result["t_proto_exact"] != last_layer
                or result["recurrence"] is not None
                or result["resource_limit"] is not None
                or result["first_role"] is None
                or result["first_successor"] is None
                or result["first_intervention_eligible"] is None
            ):
                raise OrbitLedgerError("passing candidate terminal fields mismatch")
            witness = result["pass_witness"]
            required = {
                "layer",
                "anchor",
                "successor_anchor",
                "sham_future",
                "breaking_future",
                "seeded_state_hex",
                "baseline_state_hex",
            }
            if type(witness) is not dict or set(witness) != required:
                raise OrbitLedgerError("pass witness shape mismatch")
            if witness["layer"] != result["t_proto_exact"]:
                raise OrbitLedgerError("pass witness layer mismatch")
            for key in ("anchor", "successor_anchor"):
                if type(witness[key]) is not int or not 0 <= witness[key] < 64:
                    raise OrbitLedgerError("pass witness anchor mismatch")
            if (
                type(witness["sham_future"]) is not int
                or type(witness["breaking_future"]) is not int
                or witness["sham_future"] not in (0, 1)
                or witness["breaking_future"] not in (0, 1)
                or witness["sham_future"] == witness["breaking_future"]
                or not _valid_state_hex(witness["seeded_state_hex"])
                or not _valid_state_hex(witness["baseline_state_hex"])
            ):
                raise OrbitLedgerError("pass witness endpoint or state mismatch")
        elif status == "recurrence_excluded_on_fixed_orbit":
            if (
                result["t_proto_status"] != "infinite_on_fixed_orbit"
                or result["t_proto_exact"] is not None
                or result["pass_witness"] is not None
                or result["resource_limit"] is not None
            ):
                raise OrbitLedgerError("recurrence candidate terminal fields mismatch")
            recurrence = result["recurrence"]
            required = {
                "cone_saturation_layer",
                "checkpoint_layer",
                "repeat_layer",
                "period",
                "checkpoint_state",
                "repeat_state",
                "exact_full_state_equality",
            }
            if type(recurrence) is not dict or set(recurrence) != required:
                raise OrbitLedgerError("recurrence certificate shape mismatch")
            checkpoint = recurrence["checkpoint_layer"]
            repeat = recurrence["repeat_layer"]
            if (
                type(recurrence["cone_saturation_layer"]) is not int
                or recurrence["cone_saturation_layer"] != CONE_SATURATION_LAYER
                or type(checkpoint) is not int
                or type(repeat) is not int
                or checkpoint < CONE_SATURATION_LAYER
                or repeat <= checkpoint
                or repeat != last_layer
                or type(recurrence["period"]) is not int
                or recurrence["period"] != repeat - checkpoint
                or recurrence["exact_full_state_equality"] is not True
                or recurrence["checkpoint_state"] != recurrence["repeat_state"]
            ):
                raise OrbitLedgerError("recurrence certificate arithmetic mismatch")
            state = recurrence["checkpoint_state"]
            if type(state) is not dict or set(state) != {"seeded_state_hex", "baseline_state_hex"}:
                raise OrbitLedgerError("recurrence state shape mismatch")
            if not _valid_state_hex(state["seeded_state_hex"]) or not _valid_state_hex(state["baseline_state_hex"]):
                raise OrbitLedgerError("recurrence state encoding mismatch")
        elif status == "resource_censored_before_recurrence":
            if (
                result["t_proto_status"] != "right_censored_at_resource_limit"
                or result["t_proto_exact"] is not None
                or result["pass_witness"] is not None
                or result["recurrence"] is not None
                or result["resource_limit"] != MAX_LAYERS_PER_CANDIDATE
                or last_layer != MAX_LAYERS_PER_CANDIDATE
            ):
                raise OrbitLedgerError("resource-censored candidate terminal fields mismatch")
        else:
            raise OrbitLedgerError("dynamic candidate has an unknown status")

    resource_count = statuses.count("resource_censored_before_recurrence")
    if resource_count:
        expected_aggregate = (
            "incomplete_resource_censored",
            "resource_censored_incomplete",
            False,
            [],
        )
    elif passing:
        best_n_l = min(row["atomic_n_l"] for row in passing)
        shell = [row for row in passing if row["atomic_n_l"] == best_n_l]
        best_t = min(row["t_proto_exact"] for row in shell)
        expected_winners = [
            row["candidate_id"] for row in shell if row["t_proto_exact"] == best_t
        ]
        expected_aggregate = (
            "complete_all_candidate_endpoints_resolved",
            "one_or_more_exact_passes",
            True,
            expected_winners,
        )
    else:
        if statuses[1:] != ["recurrence_excluded_on_fixed_orbit"] * 15:
            raise OrbitLedgerError("complete no-pass result lacks 15 recurrence proofs")
        expected_aggregate = (
            "complete_all_candidate_endpoints_resolved",
            "all_dynamic_candidates_recurrence_excluded",
            True,
            [],
        )
    actual_aggregate = (
        ledger["completion_status"],
        ledger["search_conclusion"],
        ledger["all_dynamic_candidates_resolved"],
        ledger["exact_orbit_winner_candidate_ids"],
    )
    if not strict_json_equal(actual_aggregate, expected_aggregate):
        raise OrbitLedgerError("exact-orbit aggregate conclusion mismatch")


def write_result_ledger(
    path: Path,
    ledger: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
) -> None:
    validate_result_ledger(ledger, candidates)
    if path.exists():
        raise OrbitLedgerError(f"refusing to overwrite existing result ledger: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise OrbitLedgerError(f"refusing to overwrite stale temporary ledger: {temporary}")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(ledger) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        temporary.unlink()
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
