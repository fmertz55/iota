from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .engine import (
    CONE_SATURATION_LAYER,
    FIRST_NEW_OUTCOME_LAYER,
    MAX_LAYERS_PER_CANDIDATE,
    OrbitRunError,
    evaluate_candidate_exact_orbit,
    reproduce_parent_H16,
)
from .runner import (
    BASE_CONTRACT_VERSION,
    BASE_OUTCOME_SEAL_REF,
    CANDIDATE_MANIFEST_REF,
    OPEN_SEAL_REF,
    OUTCOME_SEAL_REF,
    PARENT_BOUNDED_RESULT_REF,
    PROTOCOL_REF,
    PROTOCOL_VERSION,
    DETECTOR_ID,
    INHERITED_DETECTOR_ID,
    RESULT_PATH,
    RESULT_SCHEMA_REF,
    SEARCH_ID,
    SPEC_DIR_REF,
    OrbitLedgerError,
    build_result_ledger,
    candidate_trace_domain,
    canonical_json,
    expected_candidate_rows,
    load_canonical_json,
    load_canonical_json_bytes,
    read_candidate_snapshot_bytes,
    require_binding,
    sha256_file,
    strict_json_equal,
    validate_parent_bounded_result,
    validate_result_ledger,
    write_result_ledger,
)
from .verifier import verify_ledger_independently


ARCHIVAL_COMMIT = "4e999bb7ef48cbf10a0a4e15c3e708c3ea1c6f9f"
ARCHIVAL_TAG = "mir-reference-search-001-v0.2-complete"
BASE_OPEN_SEAL_REF = (
    "experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/"
    "development_open_manifest.json"
)
CONTRACT_REF = "docs/ICP_MINIMAL_INFORMATIONAL_REALIZATION_EXACT_ORBIT_CONTRACT.md"
PRE_RESULT_LITERATURE_REF = (
    "docs/literature/minimal_realization_exact_orbit_search_2026-07-13.md"
)
OPENING_CONDITION = (
    "commit the outcome-free exact-orbit preregistration, then commit only the open manifest"
)
OPENING_CONDITION_SATISFIED = (
    "outcome-free exact-orbit preregistration committed; open manifest must be its direct child"
)

SPEC_FILES = (
    f"{SPEC_DIR_REF}/README.md",
    PROTOCOL_REF,
    RESULT_SCHEMA_REF,
)
FROZEN_DEPENDENCIES = (
    "src/minimal_realization/__init__.py",
    "src/minimal_realization/search.py",
    "src/minimal_realization/dynamics.py",
    "src/minimal_realization/detector.py",
    "specs/icp_minimal_realization/v0.2-draft/topology.json",
    "specs/icp_minimal_realization/v0.2-draft/causal_cone.json",
    "specs/icp_minimal_realization/v0.2-draft/proto_object_detector.json",
)
IMPLEMENTATION_FILES = (
    "Makefile",
    CONTRACT_REF,
    PRE_RESULT_LITERATURE_REF,
    "src/minimal_realization_orbit/__init__.py",
    "src/minimal_realization_orbit/engine.py",
    "src/minimal_realization_orbit/runner.py",
    "src/minimal_realization_orbit/verifier.py",
    "src/minimal_realization_orbit/cli.py",
    "scripts/validate_minimal_realization_exact_orbit.py",
    "tests/minimal_realization_orbit/test_engine.py",
    "tests/minimal_realization_orbit/test_runner.py",
    "tests/minimal_realization_orbit/test_verifier.py",
    "tests/minimal_realization_orbit/test_cli.py",
)
POST_RESULT_DOCUMENTATION_FILES = {
    "README.md",
    "SESSION_HANDOFF.md",
    "docs/reviewer_guide.md",
    "docs/literature/minimal_realization_exact_orbit_result_followup_2026-07-13.md",
}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise OrbitLedgerError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise OrbitLedgerError(f"non-finite JSON number {value!r} is forbidden")


def _load_strict_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(
                handle,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
    except (OSError, json.JSONDecodeError) as exc:
        raise OrbitLedgerError(f"{path}: {exc}") from exc
    if type(value) is not dict:
        raise OrbitLedgerError(f"{path}: root must be an object")
    return value


def _repo_path(root: Path, relative: str) -> Path:
    return root / relative


def _require_no_symlink_components(root: Path, path: Path, label: str) -> Path:
    root = root.resolve()
    absolute = path.absolute()
    try:
        relative = absolute.relative_to(root)
    except ValueError as exc:
        raise OrbitLedgerError(f"{label} is outside the repository") from exc
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise OrbitLedgerError(f"{label} may not use a symbolic-link path component")
        if cursor.exists() and cursor != absolute and not cursor.is_dir():
            raise OrbitLedgerError(f"{label} has a non-directory path component")
    return absolute


def _require_registered(path: Path, relative: str, label: str) -> Path:
    root = repository_root()
    expected = _repo_path(root, relative)
    _require_no_symlink_components(root, path, label)
    _require_no_symlink_components(root, expected, label)
    if path.absolute() != expected.absolute():
        raise OrbitLedgerError(f"{label} must use registered path {relative}")
    return expected


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise OrbitLedgerError(
            f"git {' '.join(arguments)} failed: {detail or 'unknown error'}"
        )
    return completed


def _git_head(root: Path) -> str:
    value = _git(root, "rev-parse", "--verify", "HEAD").stdout.decode("ascii").strip()
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise OrbitLedgerError("Git HEAD is not a full SHA-1 commit id")
    return value


def _require_clean_worktree(root: Path) -> None:
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout
    if status:
        raise OrbitLedgerError("exact-orbit opening/execution requires a clean worktree")


def _require_result_verification_worktree(root: Path) -> None:
    status = _git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ).stdout.decode("utf-8", errors="strict")
    allowed = f"?? {RESULT_PATH.as_posix()}\n"
    if status not in ("", allowed):
        raise OrbitLedgerError(
            "result verification permits only a clean worktree or the sole untracked exact-orbit result"
        )


def _require_committed_bytes(root: Path, path: Path, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise OrbitLedgerError(f"{label} must be a regular committed file")
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    committed = _git(root, "show", f"HEAD:{relative}", check=False)
    if committed.returncode != 0:
        raise OrbitLedgerError(f"{label} is absent from the current Git commit")
    if path.read_bytes() != committed.stdout:
        raise OrbitLedgerError(f"{label} differs from current committed bytes")


def _require_bytes_at_commit(
    root: Path,
    path: Path,
    commit: str,
    label: str,
) -> None:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    committed = _git(root, "show", f"{commit}:{relative}", check=False)
    if committed.returncode != 0:
        raise OrbitLedgerError(f"{label} was absent from commit {commit}")
    if path.read_bytes() != committed.stdout:
        raise OrbitLedgerError(f"{label} differs from bytes at commit {commit}")


def _commit_changes(root: Path, commit: str) -> set[str]:
    output = _git(
        root,
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "--no-renames",
        "-r",
        commit,
    ).stdout.decode("utf-8", errors="strict")
    return set(output.splitlines())


def _require_opening_history(
    root: Path,
    preregistration_commit: str,
    *,
    allow_result: bool,
) -> None:
    commits = _git(
        root,
        "rev-list",
        "--reverse",
        "--first-parent",
        f"{preregistration_commit}..HEAD",
    ).stdout.decode("ascii", errors="strict").splitlines()
    if not commits:
        raise OrbitLedgerError("exact-orbit open manifest has not been committed")
    first_parents = _git(root, "rev-list", "--parents", "-n", "1", commits[0]).stdout.decode(
        "ascii"
    ).split()
    if len(first_parents) != 2 or first_parents[1] != preregistration_commit:
        raise OrbitLedgerError("open manifest commit is not the direct preregistration child")
    if _commit_changes(root, commits[0]) != {f"A\t{OPEN_SEAL_REF}"}:
        raise OrbitLedgerError("first post-preregistration commit must add only the open manifest")
    if not allow_result:
        if len(commits) != 1:
            raise OrbitLedgerError("exact-orbit execution must occur at the opening commit")
        return
    if len(commits) == 1:
        # The independent verifier is deliberately allowed to check the sole
        # untracked result before its result-only commit is created.
        return
    second_parents = _git(root, "rev-list", "--parents", "-n", "1", commits[1]).stdout.decode(
        "ascii"
    ).split()
    if len(second_parents) != 2 or second_parents[1] != commits[0]:
        raise OrbitLedgerError("result commit is not the direct open-manifest child")
    if _commit_changes(root, commits[1]) != {f"A\t{RESULT_PATH.as_posix()}"}:
        raise OrbitLedgerError("second post-preregistration commit must add only the result")
    for index, commit in enumerate(commits[2:], start=2):
        parents = _git(root, "rev-list", "--parents", "-n", "1", commit).stdout.decode(
            "ascii"
        ).split()
        if len(parents) != 2 or parents[1] != commits[index - 1]:
            raise OrbitLedgerError("exact-orbit history must remain a linear one-parent chain")
        touched = {entry.split("\t", 1)[1] for entry in _commit_changes(root, commit)}
        forbidden = touched - POST_RESULT_DOCUMENTATION_FILES
        if forbidden:
            raise OrbitLedgerError(
                f"post-result commit {commit} changed non-documentation files: {sorted(forbidden)}"
            )


def _audit_protocol(root: Path) -> None:
    protocol = _load_strict_json(_repo_path(root, PROTOCOL_REF))
    expected = {
        "protocol_version": PROTOCOL_VERSION,
        "base_contract_version": BASE_CONTRACT_VERSION,
        "search_id": SEARCH_ID,
        "status": "design_frozen_outcomes_sealed",
        "data_class": "development",
        "objective": (
            "resolve each fixed canonical candidate by first complete proto-object "
            "pass or exact post-saturation joint-state recurrence"
        ),
        "candidate_source": CANDIDATE_MANIFEST_REF,
        "parent_result": PARENT_BOUNDED_RESULT_REF,
        "detector": DETECTOR_ID,
        "inherited_detector": INHERITED_DETECTOR_ID,
        "temporal_extension": (
            "unchanged_local_predicates_extended_prospectively_beyond_H16_with_"
            "C64_cone_wrap_and_saturation"
        ),
        "canonical_origin": 0,
        "parent_censoring_layer": 16,
        "first_new_outcome_layer": FIRST_NEW_OUTCOME_LAYER,
        "cone_saturation_layer": CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "dynamic_candidate_count": 15,
        "candidate_processing": "all_nonempty_candidates_no_shell_stopping",
        "recurrence_state": ["cone_phase", "seeded_state", "baseline_state"],
        "recurrence_equality": "exact_full_64_bit_seeded_and_baseline_state",
        "recurrence_check_order": "evaluate_detector_then_test_repeat",
        "stopping_rule": (
            "for each nonempty candidate stop at its first complete detector pass, "
            "an exact full-state equality with a registered post-saturation checkpoint, "
            "or the fixed resource ceiling; process every candidate"
        ),
        "terminal_statuses": [
            "exact_pass_on_fixed_orbit",
            "recurrence_excluded_on_fixed_orbit",
            "resource_censored_before_recurrence",
        ],
        "resource_limit_status": "incomplete_no_family_claim",
        "trace_digest_encoding": (
            "sha256_domain_separated_decimal_length_layer_u64_seeded_u64_"
            "baseline_including_layer_0"
        ),
        "translation_offsets_evaluated": [0],
        "reserved_translation_offsets_accessed": False,
        "translation_equivariance_basis": (
            "formal_commutation_only_no_nonzero_offset_evaluation"
        ),
        "claim_scope": (
            "complete fixed-family existential falsification only if every "
            "nonempty candidate resolves by pass or recurrence"
        ),
        "claim_limits": [
            "not an exclusion of alternative N_P=2 grammars",
            "not an exclusion of other seeds backgrounds sizes or topologies",
            "not a general object impossibility",
            "not current-physics recovery",
            "not global minimality",
            "not a novelty claim",
            "not persistence stability attractor membership or a long-lived object claim",
            "not transferable across cycle sizes especially for at-or-post-saturation passes",
        ],
        "schema_role": (
            "structural_transport_plus_normative_cross_field_python_validation"
        ),
        "global_minimality_claimed": False,
    }
    if not strict_json_equal(protocol, expected):
        mismatches = sorted(
            key
            for key in set(protocol) | set(expected)
            if not strict_json_equal(protocol.get(key), expected.get(key))
        )
        raise OrbitLedgerError(f"protocol.json exact freeze mismatch: {mismatches}")

    schema = _load_strict_json(_repo_path(root, RESULT_SCHEMA_REF))
    if (
        schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("type") != "object"
        or schema.get("additionalProperties") is not False
    ):
        raise OrbitLedgerError("result schema root is not a closed draft-2020-12 object")
    expected_description = (
        "Structural transport schema. Normative cross-field arithmetic, chronology, "
        "candidate identity, recurrence, and aggregate checks are enforced by the "
        "sealed Python validator and independent replay."
    )
    if schema.get("description") != expected_description:
        raise OrbitLedgerError("result schema role description mismatch")
    properties = schema.get("properties")
    required = schema.get("required")
    definitions = schema.get("$defs")
    if (
        type(properties) is not dict
        or type(required) is not list
        or set(required) != set(properties)
        or type(definitions) is not dict
    ):
        raise OrbitLedgerError("result schema root properties/required mismatch")
    critical_constants = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": "MIR-EXACT-ORBIT-001-DEVELOPMENT",
        "detector": DETECTOR_ID,
        "data_class": "development",
        "canonical_origin": 0,
        "translation_offsets_evaluated": [0],
        "reserved_translation_offsets_accessed": False,
        "reserved_translation_offsets_evaluated": [],
        "first_new_outcome_layer": FIRST_NEW_OUTCOME_LAYER,
        "cone_saturation_layer": CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "global_minimality_claimed": False,
        "alternative_grammar_excluded": False,
    }
    for key, value in critical_constants.items():
        if not strict_json_equal(properties.get(key, {}).get("const"), value):
            raise OrbitLedgerError(f"result schema {key} const mismatch")
    candidates = properties.get("candidate_results", {})
    if (
        candidates.get("minItems") != 16
        or candidates.get("maxItems") != 16
        or candidates.get("items") != {"$ref": "#/$defs/candidate_result"}
    ):
        raise OrbitLedgerError("result schema candidate allocation mismatch")
    candidate_schema = definitions.get("candidate_result", {})
    if (
        candidate_schema.get("type") != "object"
        or candidate_schema.get("additionalProperties") is not False
        or set(candidate_schema.get("required", []))
        != set(candidate_schema.get("properties", {}))
        or len(candidate_schema.get("oneOf", [])) != 4
    ):
        raise OrbitLedgerError("result schema candidate terminal branches mismatch")
    terminal_branches = candidate_schema["oneOf"]
    branch_statuses = {
        branch.get("properties", {}).get("evaluation_status", {}).get("const")
        for branch in terminal_branches
    }
    if branch_statuses != {
        "analytically_excluded",
        "exact_pass_on_fixed_orbit",
        "recurrence_excluded_on_fixed_orbit",
        "resource_censored_before_recurrence",
    }:
        raise OrbitLedgerError("result schema terminal status conditions mismatch")
    if properties.get("completion_status", {}).get("enum") != [
        "complete_all_candidate_endpoints_resolved",
        "incomplete_resource_censored",
    ]:
        raise OrbitLedgerError("result schema completion status mismatch")
    recurrence = definitions.get("recurrence", {})
    recurrence_properties = recurrence.get("properties", {})
    if (
        recurrence.get("additionalProperties") is not False
        or set(recurrence.get("required", [])) != set(recurrence_properties)
        or recurrence_properties.get("cone_saturation_layer", {}).get("const")
        != CONE_SATURATION_LAYER
        or "checkpoint_layer" not in recurrence_properties
        or "checkpoint_state" not in recurrence_properties
        or "first_seen_layer" in recurrence_properties
        or "first_seen_state" in recurrence_properties
    ):
        raise OrbitLedgerError("result schema recurrence certificate mismatch")
    if len(schema.get("allOf", [])) != 4:
        raise OrbitLedgerError("result schema aggregate conditions mismatch")


def _binding(root: Path, relative: str) -> dict[str, str]:
    path = _require_no_symlink_components(root, _repo_path(root, relative), relative)
    return {"path": relative, "sha256": sha256_file(path)}


def _verify_archival_identity(root: Path) -> None:
    if _git(root, "cat-file", "-e", f"{ARCHIVAL_COMMIT}^{{commit}}", check=False).returncode != 0:
        raise OrbitLedgerError("archival commit does not exist")
    tag_commit = _git(root, "rev-parse", f"{ARCHIVAL_TAG}^{{commit}}", check=False)
    if tag_commit.returncode != 0 or tag_commit.stdout.decode("ascii").strip() != ARCHIVAL_COMMIT:
        raise OrbitLedgerError("archival tag does not identify the completed bounded pilot")


def _verify_frozen_dependencies_against_parent(root: Path) -> None:
    parent_seal_path = _repo_path(root, BASE_OUTCOME_SEAL_REF)
    _require_bytes_at_commit(
        root,
        parent_seal_path,
        ARCHIVAL_COMMIT,
        "parent outcome seal",
    )
    parent_seal = load_canonical_json(parent_seal_path)
    implementation_hashes = parent_seal.get("implementation_files")
    specification_hashes = parent_seal.get("spec_files")
    if type(implementation_hashes) is not dict or type(specification_hashes) is not dict:
        raise OrbitLedgerError("parent outcome seal dependency maps are invalid")
    for relative in FROZEN_DEPENDENCIES:
        if relative.startswith("src/"):
            expected_hash = implementation_hashes.get(relative)
        else:
            expected_hash = specification_hashes.get(Path(relative).name)
        if (
            type(expected_hash) is not str
            or len(expected_hash) != 64
            or any(character not in "0123456789abcdef" for character in expected_hash)
        ):
            raise OrbitLedgerError(
                f"frozen dependency is absent from the parent outcome seal: {relative}"
            )
        path = _repo_path(root, relative)
        if sha256_file(path) != expected_hash:
            raise OrbitLedgerError(
                f"frozen dependency differs from the parent outcome seal: {relative}"
            )
        _require_bytes_at_commit(root, path, ARCHIVAL_COMMIT, relative)


def verify_outcome_seal(path: Path, *, require_committed: bool = False) -> dict[str, Any]:
    root = repository_root()
    path = _require_registered(path, OUTCOME_SEAL_REF, "exact-orbit outcome seal")
    _audit_protocol(root)
    _verify_archival_identity(root)
    _verify_frozen_dependencies_against_parent(root)
    seal = load_canonical_json(path)
    expected_keys = {
        "base_contract_version",
        "protocol_version",
        "search_id",
        "status",
        "archival_commit",
        "archival_tag",
        "base_outcome_seal",
        "base_open_seal",
        "candidate_manifest",
        "parent_bounded_result",
        "spec_files",
        "frozen_dependencies",
        "implementation_files",
        "run_command_enabled",
        "reserved_translation_command_available",
        "canonical_origin",
        "translation_offsets_evaluated",
        "cone_saturation_layer",
        "max_layers_per_candidate",
        "opening_condition",
    }
    if set(seal) != expected_keys:
        raise OrbitLedgerError("outcome seal has missing or unexpected keys")
    fixed = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "archival_commit": ARCHIVAL_COMMIT,
        "archival_tag": ARCHIVAL_TAG,
        "run_command_enabled": False,
        "reserved_translation_command_available": False,
        "canonical_origin": 0,
        "translation_offsets_evaluated": [0],
        "cone_saturation_layer": CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "opening_condition": OPENING_CONDITION,
    }
    for key, expected in fixed.items():
        if not strict_json_equal(seal[key], expected):
            raise OrbitLedgerError(f"outcome seal {key} mismatch")
    registered_bindings = {
        "base_outcome_seal": BASE_OUTCOME_SEAL_REF,
        "base_open_seal": BASE_OPEN_SEAL_REF,
        "candidate_manifest": CANDIDATE_MANIFEST_REF,
        "parent_bounded_result": PARENT_BOUNDED_RESULT_REF,
    }
    for name, relative in registered_bindings.items():
        value = require_binding(seal[name], name)
        if value["path"] != relative:
            raise OrbitLedgerError(f"outcome seal {name} path mismatch")
        path_value = _require_no_symlink_components(root, _repo_path(root, relative), name)
        if sha256_file(path_value) != value["sha256"]:
            raise OrbitLedgerError(f"outcome seal {name} hash mismatch")
        _require_bytes_at_commit(root, path_value, ARCHIVAL_COMMIT, name)
        if require_committed:
            _require_committed_bytes(root, path_value, name)
    expected_sets = {
        "spec_files": set(SPEC_FILES),
        "frozen_dependencies": set(FROZEN_DEPENDENCIES),
        "implementation_files": set(IMPLEMENTATION_FILES),
    }
    for section, expected_paths in expected_sets.items():
        values = seal[section]
        if type(values) is not dict or set(values) != expected_paths:
            raise OrbitLedgerError(f"outcome seal {section} set mismatch")
        for relative, expected_hash in values.items():
            if require_binding({"path": relative, "sha256": expected_hash}, relative)["path"] != relative:
                raise OrbitLedgerError("unreachable binding mismatch")
            file_path = _require_no_symlink_components(root, _repo_path(root, relative), relative)
            if sha256_file(file_path) != expected_hash:
                raise OrbitLedgerError(f"outcome seal hash mismatch: {relative}")
            if require_committed:
                _require_committed_bytes(root, file_path, relative)
    if require_committed:
        _require_committed_bytes(root, path, "exact-orbit outcome seal")
    return seal


def _candidate_snapshot(root: Path, binding: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    value = require_binding(binding, "candidate manifest")
    if value["path"] != CANDIDATE_MANIFEST_REF:
        raise OrbitLedgerError("candidate snapshot path mismatch")
    path = _require_no_symlink_components(root, _repo_path(root, value["path"]), "candidate manifest")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != value["sha256"]:
        raise OrbitLedgerError("candidate snapshot hash mismatch")
    return read_candidate_snapshot_bytes(data, CANDIDATE_MANIFEST_REF)


def _parent_snapshot(
    root: Path,
    binding: dict[str, Any],
    candidates: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    value = require_binding(binding, "parent bounded result")
    if value["path"] != PARENT_BOUNDED_RESULT_REF:
        raise OrbitLedgerError("parent result path mismatch")
    path = _require_no_symlink_components(root, _repo_path(root, value["path"]), "parent result")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != value["sha256"]:
        raise OrbitLedgerError("parent result hash mismatch")
    result = load_canonical_json_bytes(data, PARENT_BOUNDED_RESULT_REF)
    validate_parent_bounded_result(result, candidates)
    return result


def _write_new_canonical(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise OrbitLedgerError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(value) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_open_seal(path: Path, *, require_clean: bool) -> dict[str, Any]:
    root = repository_root()
    path = _require_registered(path, OPEN_SEAL_REF, "exact-orbit open manifest")
    open_seal = load_canonical_json(path)
    expected_keys = {
        "base_contract_version",
        "protocol_version",
        "search_id",
        "status",
        "data_class",
        "parent_outcome_seal",
        "base_outcome_seal",
        "candidate_manifest",
        "parent_bounded_result",
        "result_schema",
        "result_path",
        "preregistration_commit",
        "run_command_enabled",
        "reserved_translation_command_available",
        "canonical_origin",
        "translation_offsets_evaluated",
        "cone_saturation_layer",
        "max_layers_per_candidate",
        "opening_condition_satisfied",
    }
    if set(open_seal) != expected_keys:
        raise OrbitLedgerError("open manifest has missing or unexpected keys")
    fixed = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "exact_orbit_open",
        "data_class": "development",
        "result_path": RESULT_PATH.as_posix(),
        "run_command_enabled": True,
        "reserved_translation_command_available": False,
        "canonical_origin": 0,
        "translation_offsets_evaluated": [0],
        "cone_saturation_layer": CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "opening_condition_satisfied": OPENING_CONDITION_SATISFIED,
    }
    for key, expected in fixed.items():
        if not strict_json_equal(open_seal[key], expected):
            raise OrbitLedgerError(f"open manifest {key} mismatch")
    parent = require_binding(open_seal["parent_outcome_seal"], "parent outcome seal")
    if parent["path"] != OUTCOME_SEAL_REF:
        raise OrbitLedgerError("open manifest parent seal path mismatch")
    outcome_path = _repo_path(root, OUTCOME_SEAL_REF)
    if sha256_file(outcome_path) != parent["sha256"]:
        raise OrbitLedgerError("open manifest parent seal hash mismatch")
    outcome_seal = verify_outcome_seal(outcome_path, require_committed=True)
    for name in ("base_outcome_seal", "candidate_manifest", "parent_bounded_result"):
        if open_seal[name] != outcome_seal[name]:
            raise OrbitLedgerError(f"open manifest {name} binding drift")
    schema = require_binding(open_seal["result_schema"], "result schema")
    if schema["path"] != RESULT_SCHEMA_REF or sha256_file(_repo_path(root, RESULT_SCHEMA_REF)) != schema["sha256"]:
        raise OrbitLedgerError("open manifest result schema binding mismatch")
    _require_committed_bytes(root, _repo_path(root, RESULT_SCHEMA_REF), "result schema")
    _require_committed_bytes(root, path, "exact-orbit open manifest")
    preregistration = open_seal["preregistration_commit"]
    if (
        type(preregistration) is not str
        or len(preregistration) != 40
        or any(character not in "0123456789abcdef" for character in preregistration)
    ):
        raise OrbitLedgerError("open manifest preregistration commit is invalid")
    if _git(root, "cat-file", "-e", f"{preregistration}^{{commit}}", check=False).returncode != 0:
        raise OrbitLedgerError("preregistration commit does not exist")
    if _git(root, "cat-file", "-e", f"{preregistration}:{OPEN_SEAL_REF}", check=False).returncode == 0:
        raise OrbitLedgerError("open manifest existed in the preregistration commit")
    for relative in set(SPEC_FILES) | set(FROZEN_DEPENDENCIES) | set(IMPLEMENTATION_FILES) | {
        OUTCOME_SEAL_REF,
        CANDIDATE_MANIFEST_REF,
        PARENT_BOUNDED_RESULT_REF,
    }:
        _require_bytes_at_commit(root, _repo_path(root, relative), preregistration, relative)
    _require_opening_history(root, preregistration, allow_result=not require_clean)
    if require_clean:
        _require_clean_worktree(root)
    return open_seal


def command_audit(_: argparse.Namespace) -> int:
    root = repository_root()
    _audit_protocol(root)
    print(
        f"PASS {SEARCH_ID}: protocol={PROTOCOL_VERSION} origin=0 "
        f"cone_saturation={CONE_SATURATION_LAYER} cap={MAX_LAYERS_PER_CANDIDATE}"
    )
    return 0


def command_freeze_seal(_: argparse.Namespace) -> int:
    root = repository_root()
    _audit_protocol(root)
    _verify_archival_identity(root)
    _verify_frozen_dependencies_against_parent(root)
    output = _require_registered(_repo_path(root, OUTCOME_SEAL_REF), OUTCOME_SEAL_REF, "outcome seal")
    if _repo_path(root, OPEN_SEAL_REF).exists() or _repo_path(root, RESULT_PATH.as_posix()).exists():
        raise OrbitLedgerError("cannot regenerate an outcome seal after opening or results")
    seal = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_sealed",
        "archival_commit": ARCHIVAL_COMMIT,
        "archival_tag": ARCHIVAL_TAG,
        "base_outcome_seal": _binding(root, BASE_OUTCOME_SEAL_REF),
        "base_open_seal": _binding(root, BASE_OPEN_SEAL_REF),
        "candidate_manifest": _binding(root, CANDIDATE_MANIFEST_REF),
        "parent_bounded_result": _binding(root, PARENT_BOUNDED_RESULT_REF),
        "spec_files": {relative: sha256_file(_repo_path(root, relative)) for relative in SPEC_FILES},
        "frozen_dependencies": {
            relative: sha256_file(_repo_path(root, relative))
            for relative in FROZEN_DEPENDENCIES
        },
        "implementation_files": {
            relative: sha256_file(_repo_path(root, relative))
            for relative in IMPLEMENTATION_FILES
        },
        "run_command_enabled": False,
        "reserved_translation_command_available": False,
        "canonical_origin": 0,
        "translation_offsets_evaluated": [0],
        "cone_saturation_layer": CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "opening_condition": OPENING_CONDITION,
    }
    _write_new_canonical(output, seal)
    print(f"WROTE {output}: sha256={sha256_file(output)} status=outcomes_sealed")
    return 0


def command_verify_seal(args: argparse.Namespace) -> int:
    verify_outcome_seal(args.seal)
    print(f"PASS {args.seal}: exact-orbit outcome seal hashes verified")
    return 0


def command_open(args: argparse.Namespace) -> int:
    root = repository_root()
    seal_path = _require_registered(args.seal, OUTCOME_SEAL_REF, "outcome seal")
    seal = verify_outcome_seal(seal_path, require_committed=True)
    _require_clean_worktree(root)
    open_path = _repo_path(root, OPEN_SEAL_REF)
    if open_path.exists():
        raise OrbitLedgerError(f"refusing to overwrite existing open manifest: {open_path}")
    open_seal = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "exact_orbit_open",
        "data_class": "development",
        "parent_outcome_seal": _binding(root, OUTCOME_SEAL_REF),
        "base_outcome_seal": dict(seal["base_outcome_seal"]),
        "candidate_manifest": dict(seal["candidate_manifest"]),
        "parent_bounded_result": dict(seal["parent_bounded_result"]),
        "result_schema": _binding(root, RESULT_SCHEMA_REF),
        "result_path": RESULT_PATH.as_posix(),
        "preregistration_commit": _git_head(root),
        "run_command_enabled": True,
        "reserved_translation_command_available": False,
        "canonical_origin": 0,
        "translation_offsets_evaluated": [0],
        "cone_saturation_layer": CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "opening_condition_satisfied": OPENING_CONDITION_SATISFIED,
    }
    _write_new_canonical(open_path, open_seal)
    print(
        f"WROTE {open_path}: status=exact_orbit_open sha256={sha256_file(open_path)}; "
        "commit this manifest before run-exact-orbit"
    )
    return 0


def _production_evaluator(
    candidate: dict[str, Any],
    rows: tuple[str, ...],
    _parent_origin_record: dict[str, Any],
):
    return evaluate_candidate_exact_orbit(
        rows,
        trace_domain=candidate_trace_domain(candidate),
    )


def _preflight_parent_H16(
    candidates: tuple[dict[str, Any], ...],
    parent_result: dict[str, Any],
) -> None:
    validate_parent_bounded_result(parent_result, candidates)
    parent_rows = parent_result["candidate_results"]
    for index, rows in enumerate(expected_candidate_rows()[1:], start=1):
        reproduce_parent_H16(rows, parent_rows[index]["translations"][0])


def command_run(args: argparse.Namespace) -> int:
    root = repository_root()
    open_path = _require_registered(args.open_seal, OPEN_SEAL_REF, "open manifest")
    open_seal = load_open_seal(open_path, require_clean=True)
    result_path = _require_no_symlink_components(root, _repo_path(root, RESULT_PATH.as_posix()), "result")
    if result_path.exists():
        raise OrbitLedgerError(f"refusing to overwrite existing result: {result_path}")
    candidates = _candidate_snapshot(root, open_seal["candidate_manifest"])
    parent_result = _parent_snapshot(root, open_seal["parent_bounded_result"], candidates)
    _preflight_parent_H16(candidates, parent_result)
    ledger = build_result_ledger(
        root=root,
        open_seal_path=open_path,
        open_seal=open_seal,
        candidates=candidates,
        parent_result=parent_result,
        evaluator=_production_evaluator,
    )
    validate_result_ledger(ledger, candidates)

    reverified_open = load_open_seal(open_path, require_clean=True)
    if canonical_json(reverified_open) != canonical_json(open_seal):
        raise OrbitLedgerError("open manifest changed during exact-orbit evaluation")
    reverified_candidates = _candidate_snapshot(root, reverified_open["candidate_manifest"])
    reverified_parent = _parent_snapshot(root, reverified_open["parent_bounded_result"], reverified_candidates)
    if tuple(map(canonical_json, reverified_candidates)) != tuple(map(canonical_json, candidates)):
        raise OrbitLedgerError("candidate snapshot changed during exact-orbit evaluation")
    if canonical_json(reverified_parent) != canonical_json(parent_result):
        raise OrbitLedgerError("parent bounded result changed during exact-orbit evaluation")
    expected_bindings = {
        "open_seal": _binding(root, OPEN_SEAL_REF),
        "outcome_seal": reverified_open["parent_outcome_seal"],
        "base_outcome_seal": reverified_open["base_outcome_seal"],
        "candidate_manifest": reverified_open["candidate_manifest"],
        "parent_bounded_result": reverified_open["parent_bounded_result"],
        "result_schema": reverified_open["result_schema"],
    }
    for name, expected in expected_bindings.items():
        if ledger[name] != expected:
            raise OrbitLedgerError(f"result ledger {name} binding drifted")
    final_result_path = _require_no_symlink_components(
        root,
        _repo_path(root, RESULT_PATH.as_posix()),
        "result",
    )
    if final_result_path != result_path or final_result_path.exists():
        raise OrbitLedgerError("registered result path changed during exact-orbit evaluation")
    write_result_ledger(final_result_path, ledger, candidates)
    print(f"WROTE {result_path}: sha256={sha256_file(result_path)} data_class=development")
    return 0


def command_verify_results(args: argparse.Namespace) -> int:
    root = repository_root()
    _require_result_verification_worktree(root)
    open_path = _require_registered(args.open_seal, OPEN_SEAL_REF, "open manifest")
    open_seal = load_open_seal(open_path, require_clean=False)
    result_path = _require_no_symlink_components(root, _repo_path(root, RESULT_PATH.as_posix()), "result")
    ledger = load_canonical_json(result_path)
    candidates = _candidate_snapshot(root, open_seal["candidate_manifest"])
    parent_result = _parent_snapshot(root, open_seal["parent_bounded_result"], candidates)
    validate_result_ledger(ledger, candidates)
    verify_ledger_independently(ledger, candidates, parent_result)
    expected_bindings = {
        "open_seal": _binding(root, OPEN_SEAL_REF),
        "outcome_seal": open_seal["parent_outcome_seal"],
        "base_outcome_seal": open_seal["base_outcome_seal"],
        "candidate_manifest": open_seal["candidate_manifest"],
        "parent_bounded_result": open_seal["parent_bounded_result"],
        "result_schema": open_seal["result_schema"],
    }
    for name, expected in expected_bindings.items():
        if ledger[name] != expected:
            raise OrbitLedgerError(f"verified result {name} binding mismatch")
    print(
        f"PASS {result_path}: independent full-state replay, recurrence certificates, "
        "trace digests, and canonical bytes verified"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Outcome-safe MIR exact-orbit falsification tooling.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="audit the outcome-free exact-orbit protocol")
    audit.set_defaults(func=command_audit)

    freeze = subparsers.add_parser("freeze-seal", help="write the registered exact-orbit outcome seal")
    freeze.set_defaults(func=command_freeze_seal)

    verify = subparsers.add_parser("verify-seal", help="verify the registered exact-orbit outcome seal")
    verify.add_argument("--seal", type=Path, required=True)
    verify.set_defaults(func=command_verify_seal)

    open_parser = subparsers.add_parser("open-exact-orbit", help="create the no-outcome open manifest")
    open_parser.add_argument("--seal", type=Path, required=True)
    open_parser.set_defaults(func=command_open)

    run = subparsers.add_parser("run-exact-orbit", help="run every canonical candidate to pass, recurrence, or cap")
    run.add_argument("--open-seal", type=Path, required=True)
    run.set_defaults(func=command_run)

    results = subparsers.add_parser("verify-exact-orbit-results", help="independently replay and verify the result")
    results.add_argument("--open-seal", type=Path, required=True)
    results.set_defaults(func=command_verify_results)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, OrbitRunError, OrbitLedgerError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
