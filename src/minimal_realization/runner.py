from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from .detector import (
    FORMATION_HORIZON,
    LAST_REQUIRED_LAYER,
    DetectorResult,
    canonical_initial_state,
    detect_proto_object,
)
from .dynamics import CYCLE_SIZE, run_trajectory, translate_state
from .spec import canonical_json, sha256_file


DEVELOPMENT_TRANSLATIONS = tuple(range(48))
HELD_OUT_TRANSLATIONS = tuple(range(48, 64))
RESULT_SCHEMA_REF = "specs/icp_minimal_realization/v0.2-draft/result.schema.json"
RESULT_PATH = Path(
    "output/minimal_realization/MIR-REFERENCE-SEARCH-001/development_results.json"
)


class DevelopmentRunError(ValueError):
    pass


TranslationEvaluator = Callable[[tuple[str, ...], int], DetectorResult]


def candidate_sha256(candidate: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(candidate).encode("utf-8")).hexdigest()


@lru_cache(maxsize=16)
def _reference_trajectories(
    rows: tuple[str, ...],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return (
        run_trajectory(canonical_initial_state(0), rows, LAST_REQUIRED_LAYER),
        run_trajectory(0, rows, LAST_REQUIRED_LAYER),
    )


def _exact_translation_evaluator(rows: tuple[str, ...], origin: int) -> DetectorResult:
    """Evaluate one registered development translation exactly.

    This function is deliberately not called by import, audit, compilation, seal
    creation, or unit tests. Only the development runner calls it.
    """

    if type(origin) is not int or origin not in DEVELOPMENT_TRANSLATIONS:
        raise DevelopmentRunError("attempted access outside development translations 0..47")
    reference, baseline = _reference_trajectories(rows)
    seeded = (
        reference
        if origin == 0
        else run_trajectory(canonical_initial_state(origin), rows, LAST_REQUIRED_LAYER)
    )
    translated_reference = tuple(translate_state(state, origin) for state in reference)
    if seeded != translated_reference:
        raise DevelopmentRunError("seeded trajectory violates exact cycle translation equivariance")
    if any(translate_state(state, origin) != state for state in baseline):
        raise DevelopmentRunError("matched baseline violates exact cycle translation equivariance")
    return detect_proto_object(seeded, baseline, rows, origin=origin)


def _translation_record(origin: int, result: DetectorResult) -> dict[str, Any]:
    if type(result.passed) is not bool:
        raise DevelopmentRunError("detector pass flag must be Boolean")
    if result.passed:
        if result.t_proto is None or result.anchor is None or result.successor_anchor is None:
            raise DevelopmentRunError("passing detector result is incomplete")
        if type(result.t_proto) is not int or not 1 <= result.t_proto <= FORMATION_HORIZON:
            raise DevelopmentRunError("passing T_proto must be an integer in 1..16")
        if type(result.anchor) is not int or not 0 <= result.anchor < CYCLE_SIZE:
            raise DevelopmentRunError("passing anchor must be a cycle locus")
        if (
            type(result.successor_anchor) is not int
            or not 0 <= result.successor_anchor < CYCLE_SIZE
        ):
            raise DevelopmentRunError("passing successor anchor must be a cycle locus")
        if result.sham_future not in (0, 1) or result.breaking_future not in (0, 1):
            raise DevelopmentRunError("passing causal endpoints must be binary")
        if type(result.sham_future) is not int or type(result.breaking_future) is not int:
            raise DevelopmentRunError("passing causal endpoints must be integer bits")
        if result.sham_future == result.breaking_future:
            raise DevelopmentRunError("passing causal endpoints must differ")
        return {
            "translation_offset": origin,
            "status": "passed_by_H16",
            "t_proto": result.t_proto,
            "anchor": result.anchor,
            "anchor_offset_from_seed": (result.anchor - origin) % CYCLE_SIZE,
            "successor_anchor": result.successor_anchor,
            "successor_anchor_offset_from_seed": (
                result.successor_anchor - origin
            )
            % CYCLE_SIZE,
            "sham_future": result.sham_future,
            "breaking_future": result.breaking_future,
        }
    if any(
        value is not None
        for value in (
            result.t_proto,
            result.anchor,
            result.successor_anchor,
            result.sham_future,
            result.breaking_future,
        )
    ):
        raise DevelopmentRunError("nonpassing detector result contains outcome fields")
    return {
        "translation_offset": origin,
        "status": "right_censored_T_proto_gt_16",
        "t_proto": None,
        "anchor": None,
        "anchor_offset_from_seed": None,
        "successor_anchor": None,
        "successor_anchor_offset_from_seed": None,
        "sham_future": None,
        "breaking_future": None,
    }


def _equivariance_signature(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record["status"],
        record["t_proto"],
        record["anchor_offset_from_seed"],
        record["successor_anchor_offset_from_seed"],
        record["sham_future"],
        record["breaking_future"],
    )


def evaluate_candidate(
    candidate: dict[str, Any],
    evaluator: TranslationEvaluator,
) -> dict[str, Any]:
    rows = tuple(str(law["signature"]) for law in candidate["laws"])
    translations = [
        _translation_record(origin, evaluator(rows, origin))
        for origin in DEVELOPMENT_TRANSLATIONS
    ]
    signatures = {_equivariance_signature(record) for record in translations}
    if len(signatures) != 1:
        raise DevelopmentRunError(
            f"{candidate['candidate_id']}: development translations are not exactly equivariant"
        )
    first = translations[0]
    passed = first["status"] == "passed_by_H16"
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate_sha256(candidate),
        "normalized_n_p": candidate["primitive_accounting"]["normalized_n_p"],
        "atomic_n_l": len(rows),
        "evaluation_status": (
            "passed_by_H16" if passed else "right_censored_T_proto_gt_16"
        ),
        "pass_by_H16": passed,
        "t_proto": first["t_proto"],
        "translation_equivariance_exact": True,
        "translations_evaluated": len(translations),
        "translations": translations,
    }


def _excluded_candidate_record(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate_sha256(candidate),
        "normalized_n_p": candidate["primitive_accounting"]["normalized_n_p"],
        "atomic_n_l": len(candidate["laws"]),
        "evaluation_status": "analytically_excluded",
        "pass_by_H16": False,
        "t_proto": None,
        "translation_equivariance_exact": None,
        "translations_evaluated": 0,
        "translations": [],
        "exclusion_reason": candidate["exclusion_reason"],
    }


def _not_evaluated_record(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate_sha256(candidate),
        "normalized_n_p": candidate["primitive_accounting"]["normalized_n_p"],
        "atomic_n_l": len(candidate["laws"]),
        "evaluation_status": "not_evaluated_after_first_passing_shell",
        "pass_by_H16": None,
        "t_proto": None,
        "translation_equivariance_exact": None,
        "translations_evaluated": 0,
        "translations": [],
    }


def run_bounded_development_search(
    candidates: Iterable[dict[str, Any]],
    evaluator: TranslationEvaluator,
) -> dict[str, Any]:
    """Run shell-complete H=16 development evaluation.

    Tests supply a synthetic evaluator. The registered evaluator is used only by
    the explicitly opened development command.
    """

    ordered = tuple(candidates)
    results_by_id: dict[str, dict[str, Any]] = {}
    evaluated_shells: list[int] = []
    first_passing_shell: Optional[int] = None

    if len(ordered) != 16:
        raise DevelopmentRunError("candidate manifest must contain exactly 16 candidates")
    candidate_ids = [candidate.get("candidate_id") for candidate in ordered]
    if any(type(candidate_id) is not str for candidate_id in candidate_ids):
        raise DevelopmentRunError("candidate manifest contains an invalid candidate id")
    if len(set(candidate_ids)) != len(candidate_ids):
        raise DevelopmentRunError("candidate manifest contains duplicate candidate ids")
    shell_sizes = {law_count: 0 for law_count in range(5)}
    for candidate in ordered:
        laws = candidate.get("laws")
        if type(laws) is not list or len(laws) not in shell_sizes:
            raise DevelopmentRunError("candidate manifest contains an invalid law shell")
        shell_sizes[len(laws)] += 1
    if shell_sizes != {0: 1, 1: 4, 2: 6, 3: 4, 4: 1}:
        raise DevelopmentRunError("candidate manifest shell sizes are not 1,4,6,4,1")

    for candidate in ordered:
        if len(candidate["laws"]) == 0:
            if candidate.get("status") != "analytically_excluded":
                raise DevelopmentRunError("zero-law candidate is not analytically excluded")
            results_by_id[candidate["candidate_id"]] = _excluded_candidate_record(candidate)

    for law_count in range(1, 5):
        shell = [candidate for candidate in ordered if len(candidate["laws"]) == law_count]
        if not shell:
            raise DevelopmentRunError(f"candidate manifest is missing N_L={law_count} shell")
        evaluated_shells.append(law_count)
        shell_results = [evaluate_candidate(candidate, evaluator) for candidate in shell]
        for result in shell_results:
            results_by_id[result["candidate_id"]] = result
        if any(result["pass_by_H16"] for result in shell_results):
            first_passing_shell = law_count
            break

    for candidate in ordered:
        if candidate["candidate_id"] not in results_by_id:
            results_by_id[candidate["candidate_id"]] = _not_evaluated_record(candidate)

    candidate_results = [results_by_id[candidate["candidate_id"]] for candidate in ordered]
    eligible = [
        result
        for result in candidate_results
        if result["pass_by_H16"] is True
        and result["atomic_n_l"] == first_passing_shell
    ]
    winners: list[str] = []
    if eligible:
        best_t = min(int(result["t_proto"]) for result in eligible)
        winners = [
            str(result["candidate_id"])
            for result in eligible
            if result["t_proto"] == best_t
        ]
    return {
        "evaluated_shells": evaluated_shells,
        "first_passing_shell": first_passing_shell,
        "stopping_reason": (
            "first_shell_with_pass_by_H16_completed"
            if first_passing_shell is not None
            else "all_bounded_shells_completed_without_pass_by_H16"
        ),
        "bounded_winner_candidate_ids": winners,
        "candidate_results": candidate_results,
    }


def build_result_ledger(
    *,
    root: Path,
    open_seal_path: Path,
    open_seal: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
    evaluator: TranslationEvaluator,
) -> dict[str, Any]:
    search = run_bounded_development_search(candidates, evaluator)
    result_schema = root / RESULT_SCHEMA_REF
    return {
        "contract_version": "0.2-draft",
        "search_id": "MIR-REFERENCE-SEARCH-001",
        "run_id": "MIR-REFERENCE-SEARCH-001-DEVELOPMENT",
        "data_class": "development",
        "endpoint": "formation_by_H16",
        "formation_horizon_ticks": FORMATION_HORIZON,
        "last_required_layer": LAST_REQUIRED_LAYER,
        "translation_offsets": list(DEVELOPMENT_TRANSLATIONS),
        "held_out_accessed": False,
        "held_out_offsets_evaluated": [],
        "open_seal": {
            "path": open_seal_path.resolve().relative_to(root).as_posix(),
            "sha256": sha256_file(open_seal_path),
        },
        "parent_outcome_seal": dict(open_seal["parent_outcome_seal"]),
        "candidate_manifest": dict(open_seal["candidate_manifest"]),
        "result_schema": {
            "path": RESULT_SCHEMA_REF,
            "sha256": sha256_file(result_schema),
        },
        "nonpass_interpretation": "right_censored_T_proto_gt_16",
        "stopping_rule": "shell_complete_first_pass_by_H16",
        **search,
    }


def validate_result_ledger(
    ledger: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
) -> None:
    expected_keys = {
        "contract_version",
        "search_id",
        "run_id",
        "data_class",
        "endpoint",
        "formation_horizon_ticks",
        "last_required_layer",
        "translation_offsets",
        "held_out_accessed",
        "held_out_offsets_evaluated",
        "open_seal",
        "parent_outcome_seal",
        "candidate_manifest",
        "result_schema",
        "nonpass_interpretation",
        "stopping_rule",
        "evaluated_shells",
        "first_passing_shell",
        "stopping_reason",
        "bounded_winner_candidate_ids",
        "candidate_results",
    }
    if set(ledger) != expected_keys:
        raise DevelopmentRunError("development result ledger has missing or unexpected keys")
    fixed_values = {
        "contract_version": "0.2-draft",
        "search_id": "MIR-REFERENCE-SEARCH-001",
        "run_id": "MIR-REFERENCE-SEARCH-001-DEVELOPMENT",
        "data_class": "development",
        "endpoint": "formation_by_H16",
        "formation_horizon_ticks": 16,
        "last_required_layer": 18,
        "nonpass_interpretation": "right_censored_T_proto_gt_16",
        "stopping_rule": "shell_complete_first_pass_by_H16",
    }
    for key, expected in fixed_values.items():
        if ledger[key] != expected:
            raise DevelopmentRunError(f"result ledger {key} mismatch")
    if ledger["translation_offsets"] != list(DEVELOPMENT_TRANSLATIONS):
        raise DevelopmentRunError("result ledger translation allocation mismatch")
    if ledger["held_out_accessed"] is not False or ledger["held_out_offsets_evaluated"] != []:
        raise DevelopmentRunError("result ledger reports held-out access")
    for binding_name in (
        "open_seal",
        "parent_outcome_seal",
        "candidate_manifest",
        "result_schema",
    ):
        binding = ledger[binding_name]
        if type(binding) is not dict or set(binding) != {"path", "sha256"}:
            raise DevelopmentRunError(f"result ledger {binding_name} binding mismatch")
        if type(binding["path"]) is not str or not binding["path"]:
            raise DevelopmentRunError(f"result ledger {binding_name} path is invalid")
        digest = binding["sha256"]
        if (
            type(digest) is not str
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise DevelopmentRunError(f"result ledger {binding_name} hash is invalid")
    if ledger["result_schema"]["path"] != RESULT_SCHEMA_REF:
        raise DevelopmentRunError("result ledger schema path mismatch")
    if type(ledger["candidate_results"]) is not list or len(ledger["candidate_results"]) != 16:
        raise DevelopmentRunError("result ledger must contain exactly 16 candidate records")
    canonical_candidates = tuple(candidates)
    if len(canonical_candidates) != 16:
        raise DevelopmentRunError("canonical candidate snapshot must contain 16 records")
    for result, candidate in zip(ledger["candidate_results"], canonical_candidates):
        if type(candidate) is not dict:
            raise DevelopmentRunError("canonical candidate snapshot contains a non-object")
        expected_binding = {
            "candidate_id": candidate.get("candidate_id"),
            "candidate_sha256": candidate_sha256(candidate),
            "normalized_n_p": candidate.get("primitive_accounting", {}).get("normalized_n_p"),
            "atomic_n_l": len(candidate.get("laws", [])),
        }
        for key, expected in expected_binding.items():
            if type(result) is not dict or result.get(key) != expected:
                raise DevelopmentRunError(
                    f"candidate result {key} does not match the canonical manifest order"
                )
    candidate_ids: list[str] = []
    shell_sizes = {law_count: 0 for law_count in range(5)}
    passing_shells: set[int] = set()
    for candidate in ledger["candidate_results"]:
        if type(candidate) is not dict:
            raise DevelopmentRunError("candidate result must be an object")
        common_keys = {
            "candidate_id",
            "candidate_sha256",
            "normalized_n_p",
            "atomic_n_l",
            "evaluation_status",
            "pass_by_H16",
            "t_proto",
            "translation_equivariance_exact",
            "translations_evaluated",
            "translations",
        }
        status = candidate.get("evaluation_status")
        expected_candidate_keys = common_keys | (
            {"exclusion_reason"} if status == "analytically_excluded" else set()
        )
        if set(candidate) != expected_candidate_keys:
            raise DevelopmentRunError("candidate result has missing or unexpected keys")
        candidate_id = candidate["candidate_id"]
        if type(candidate_id) is not str or not candidate_id:
            raise DevelopmentRunError("candidate result id is invalid")
        candidate_ids.append(candidate_id)
        digest = candidate["candidate_sha256"]
        if (
            type(digest) is not str
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise DevelopmentRunError("candidate result hash is invalid")
        if candidate["normalized_n_p"] != 2:
            raise DevelopmentRunError("candidate result N_P mismatch")
        law_count = candidate["atomic_n_l"]
        if type(law_count) is not int or not 0 <= law_count <= 4:
            raise DevelopmentRunError("candidate result N_L mismatch")
        shell_sizes[law_count] += 1
        if candidate["translations_evaluated"] not in (0, 48):
            raise DevelopmentRunError("candidate has a partial translation allocation")
        if candidate["translations_evaluated"] == 48:
            if status not in {"passed_by_H16", "right_censored_T_proto_gt_16"}:
                raise DevelopmentRunError("evaluated candidate has an invalid status")
            if candidate["translation_equivariance_exact"] is not True:
                raise DevelopmentRunError("evaluated candidate lacks exact equivariance")
            if type(candidate["translations"]) is not list or len(candidate["translations"]) != 48:
                raise DevelopmentRunError("evaluated candidate translation count mismatch")
            offsets = [row["translation_offset"] for row in candidate["translations"]]
            if offsets != list(DEVELOPMENT_TRANSLATIONS):
                raise DevelopmentRunError("candidate translation ledger mismatch")
            if any(offset in HELD_OUT_TRANSLATIONS for offset in offsets):
                raise DevelopmentRunError("candidate ledger contains held-out translation")
            expected_pass = status == "passed_by_H16"
            if candidate["pass_by_H16"] is not expected_pass:
                raise DevelopmentRunError("candidate pass flag contradicts its status")
            first_signature: Optional[tuple[Any, ...]] = None
            for origin, row in enumerate(candidate["translations"]):
                expected_translation_keys = {
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
                if type(row) is not dict or set(row) != expected_translation_keys:
                    raise DevelopmentRunError("translation result shape mismatch")
                if row["translation_offset"] != origin or row["status"] != status:
                    raise DevelopmentRunError("translation result identity mismatch")
                if expected_pass:
                    if row["t_proto"] != candidate["t_proto"]:
                        raise DevelopmentRunError("translation T_proto mismatch")
                    if type(row["t_proto"]) is not int or not 1 <= row["t_proto"] <= 16:
                        raise DevelopmentRunError("translation T_proto is outside 1..16")
                    for key in ("anchor", "anchor_offset_from_seed", "successor_anchor", "successor_anchor_offset_from_seed"):
                        if type(row[key]) is not int or not 0 <= row[key] < CYCLE_SIZE:
                            raise DevelopmentRunError("translation anchor is invalid")
                    if row["anchor_offset_from_seed"] != (row["anchor"] - origin) % CYCLE_SIZE:
                        raise DevelopmentRunError("translation anchor offset mismatch")
                    if row["successor_anchor_offset_from_seed"] != (row["successor_anchor"] - origin) % CYCLE_SIZE:
                        raise DevelopmentRunError("translation successor offset mismatch")
                    if (
                        type(row["sham_future"]) is not int
                        or type(row["breaking_future"]) is not int
                        or row["sham_future"] not in (0, 1)
                        or row["breaking_future"] not in (0, 1)
                        or row["sham_future"] == row["breaking_future"]
                    ):
                        raise DevelopmentRunError("translation causal endpoint mismatch")
                elif any(
                    row[key] is not None
                    for key in (
                        "t_proto",
                        "anchor",
                        "anchor_offset_from_seed",
                        "successor_anchor",
                        "successor_anchor_offset_from_seed",
                        "sham_future",
                        "breaking_future",
                    )
                ):
                    raise DevelopmentRunError("right-censored translation contains outcome fields")
                signature = _equivariance_signature(row)
                if first_signature is None:
                    first_signature = signature
                elif signature != first_signature:
                    raise DevelopmentRunError("translation records are not exactly equivariant")
            if expected_pass:
                passing_shells.add(law_count)
            elif candidate["t_proto"] is not None:
                raise DevelopmentRunError("right-censored candidate has a formation time")
        else:
            if candidate["translations"] != []:
                raise DevelopmentRunError("unevaluated candidate contains translations")
            if candidate["t_proto"] is not None or candidate["translation_equivariance_exact"] is not None:
                raise DevelopmentRunError("unevaluated candidate contains outcome fields")
            if status == "analytically_excluded":
                if law_count != 0 or candidate["pass_by_H16"] is not False:
                    raise DevelopmentRunError("analytic exclusion record mismatch")
                if type(candidate["exclusion_reason"]) is not str or not candidate["exclusion_reason"]:
                    raise DevelopmentRunError("analytic exclusion reason is missing")
            elif status == "not_evaluated_after_first_passing_shell":
                if candidate["pass_by_H16"] is not None:
                    raise DevelopmentRunError("not-evaluated candidate has a pass flag")
            else:
                raise DevelopmentRunError("unevaluated candidate has an invalid status")
    if len(set(candidate_ids)) != len(candidate_ids):
        raise DevelopmentRunError("result ledger contains duplicate candidate ids")
    if shell_sizes != {0: 1, 1: 4, 2: 6, 3: 4, 4: 1}:
        raise DevelopmentRunError("result ledger shell sizes are not 1,4,6,4,1")
    evaluated_shells = ledger["evaluated_shells"]
    if evaluated_shells not in ([1], [1, 2], [1, 2, 3], [1, 2, 3, 4]):
        raise DevelopmentRunError("result ledger evaluated-shell sequence mismatch")
    first_passing_shell = ledger["first_passing_shell"]
    if first_passing_shell is None:
        if passing_shells or evaluated_shells != [1, 2, 3, 4]:
            raise DevelopmentRunError("no-pass stopping record mismatch")
        if ledger["stopping_reason"] != "all_bounded_shells_completed_without_pass_by_H16":
            raise DevelopmentRunError("no-pass stopping reason mismatch")
    elif (
        type(first_passing_shell) is not int
        or first_passing_shell != evaluated_shells[-1]
        or passing_shells != {first_passing_shell}
    ):
        raise DevelopmentRunError("first-passing-shell record mismatch")
    elif ledger["stopping_reason"] != "first_shell_with_pass_by_H16_completed":
        raise DevelopmentRunError("passing stopping reason mismatch")
    for candidate in ledger["candidate_results"]:
        law_count = candidate["atomic_n_l"]
        status = candidate["evaluation_status"]
        if law_count == 0:
            if status != "analytically_excluded":
                raise DevelopmentRunError("zero-law candidate is not analytically excluded")
        elif law_count in evaluated_shells:
            if status not in {"passed_by_H16", "right_censored_T_proto_gt_16"}:
                raise DevelopmentRunError(
                    "declared evaluated shell contains a non-evaluated candidate"
                )
        elif status != "not_evaluated_after_first_passing_shell":
            raise DevelopmentRunError(
                "candidate after the first passing shell was evaluated"
            )
    winner_ids = ledger["bounded_winner_candidate_ids"]
    if (
        type(winner_ids) is not list
        or any(type(candidate_id) is not str for candidate_id in winner_ids)
        or len(set(winner_ids)) != len(winner_ids)
    ):
        raise DevelopmentRunError("bounded winner list is invalid")
    passing_results = [
        candidate
        for candidate in ledger["candidate_results"]
        if candidate["pass_by_H16"] is True
    ]
    expected_winners: list[str] = []
    if passing_results:
        best_t = min(candidate["t_proto"] for candidate in passing_results)
        expected_winners = [
            candidate["candidate_id"]
            for candidate in passing_results
            if candidate["t_proto"] == best_t
        ]
    if winner_ids != expected_winners:
        raise DevelopmentRunError("bounded winner list does not contain every co-best candidate")


def write_result_ledger(
    path: Path,
    ledger: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
) -> None:
    validate_result_ledger(ledger, candidates)
    if path.exists():
        raise DevelopmentRunError(f"refusing to overwrite existing result ledger: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise DevelopmentRunError(f"refusing to overwrite stale temporary ledger: {temporary}")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(canonical_json(ledger))
            handle.write("\n")
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
