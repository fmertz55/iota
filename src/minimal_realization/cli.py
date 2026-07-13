from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .manifest import compile_candidates, read_jsonl, read_jsonl_bytes, write_jsonl
from .runner import (
    RESULT_PATH,
    RESULT_SCHEMA_REF,
    DevelopmentRunError,
    build_result_ledger,
    _exact_translation_evaluator,
    validate_result_ledger,
    write_result_ledger,
)
from .spec import (
    DESIGN_FILENAMES,
    SpecError,
    audit_design,
    canonical_json,
    load_json,
    sha256_file,
)


SPEC_DIR_REF = "specs/icp_minimal_realization/v0.2-draft"
CANDIDATE_MANIFEST_REF = (
    "experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/"
    "development_candidates.jsonl"
)
OUTCOME_SEAL_REF = (
    "experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/"
    "outcome_sealed_manifest.json"
)
DEVELOPMENT_OPEN_REF = (
    "experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/"
    "development_open_manifest.json"
)
POST_RESULT_RECORD_PATHS = {
    "README.md",
    "SESSION_HANDOFF.md",
    "docs/reviewer_guide.md",
    "paper/bibliography.bib",
    "docs/literature/minimal_realization_result_followup_2026-07-13.md",
}
OPENING_CONDITION = (
    "record outcome-free preregistration commit, then create a new development-open seal"
)
OPENING_CONDITION_SATISFIED = (
    "outcome-free preregistration commit recorded; this development-open manifest "
    "must itself be committed before execution"
)

IMPLEMENTATION_FILES = (
    "docs/ICP_MINIMAL_INFORMATIONAL_REALIZATION_CONTRACT.md",
    "docs/literature/minimal_realization_search_2026-07-13.md",
    "src/minimal_realization/__init__.py",
    "src/minimal_realization/dynamics.py",
    "src/minimal_realization/detector.py",
    "src/minimal_realization/search.py",
    "src/minimal_realization/spec.py",
    "src/minimal_realization/manifest.py",
    "src/minimal_realization/runner.py",
    "src/minimal_realization/cli.py",
    "scripts/validate_minimal_realization.py",
    "tests/minimal_realization/test_validation.py",
    "tests/minimal_realization/test_dynamics.py",
    "tests/minimal_realization/test_detector.py",
    "tests/minimal_realization/test_search.py",
    "tests/minimal_realization/test_spec.py",
    "tests/minimal_realization/test_runner.py",
)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical_path(root: Path, relative_path: str) -> Path:
    return root / relative_path


def _require_repo_path_without_symlinks(root: Path, path: Path, label: str) -> Path:
    root = root.resolve()
    absolute = path.absolute()
    try:
        relative = absolute.relative_to(root)
    except ValueError as exc:
        raise SpecError(f"{label} is outside the repository") from exc
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise SpecError(f"{label} may not use a symbolic-link path component")
        if cursor.exists() and cursor != absolute and not cursor.is_dir():
            raise SpecError(f"{label} has a non-directory path component")
    return absolute


def _require_registered_path(path: Path, relative_path: str, label: str) -> Path:
    root = repository_root()
    expected = _canonical_path(root, relative_path)
    if path.resolve() != expected.resolve():
        raise SpecError(f"{label} must use the registered path {relative_path}")
    _require_repo_path_without_symlinks(root, path, label)
    _require_repo_path_without_symlinks(root, expected, label)
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
        raise SpecError(f"git {' '.join(arguments)} failed: {detail or 'unknown error'}")
    return completed


def _git_head(root: Path) -> str:
    head = _git(root, "rev-parse", "--verify", "HEAD").stdout.decode("ascii").strip()
    if len(head) != 40 or any(character not in "0123456789abcdef" for character in head):
        raise SpecError("Git HEAD is not a full SHA-1 commit id")
    return head


def _require_clean_worktree(root: Path) -> None:
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout
    if status:
        raise SpecError("development opening/execution requires a clean worktree")


def _require_result_verification_worktree(root: Path) -> None:
    status = _git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ).stdout.decode("utf-8", errors="strict")
    allowed_untracked = f"?? {RESULT_PATH.as_posix()}\n"
    if status not in ("", allowed_untracked):
        raise SpecError(
            "result verification permits only a clean worktree or the single "
            "untracked registered result ledger"
        )


def _require_committed_bytes(root: Path, path: Path, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise SpecError(f"{label} must be a regular committed file")
    try:
        relative_path = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise SpecError(f"{label} is outside the repository") from exc
    committed = _git(root, "show", f"HEAD:{relative_path}", check=False)
    if committed.returncode != 0:
        raise SpecError(f"{label} is absent from the current Git commit")
    if path.read_bytes() != committed.stdout:
        raise SpecError(f"{label} differs from its bytes in the current Git commit")


def _require_bytes_at_commit(
    root: Path,
    path: Path,
    commit: str,
    label: str,
) -> None:
    try:
        relative_path = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise SpecError(f"{label} is outside the repository") from exc
    committed = _git(root, "show", f"{commit}:{relative_path}", check=False)
    if committed.returncode != 0:
        raise SpecError(f"{label} was absent from preregistration commit {commit}")
    if path.read_bytes() != committed.stdout:
        raise SpecError(f"{label} differs from its preregistration-commit bytes")


def _require_digest(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise SpecError(f"{label} is not a lowercase SHA-256 digest")
    return value


def _require_binding(binding: Any, label: str) -> dict[str, Any]:
    if type(binding) is not dict or set(binding) != {"path", "sha256"}:
        raise SpecError(f"{label} binding shape mismatch")
    if type(binding["path"]) is not str or not binding["path"]:
        raise SpecError(f"{label} path is invalid")
    _require_digest(binding["sha256"], f"{label} hash")
    return binding


def _candidate_snapshot(
    root: Path,
    binding: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    binding = _require_binding(binding, "candidate manifest")
    if binding["path"] != CANDIDATE_MANIFEST_REF:
        raise SpecError("candidate snapshot path is not registered")
    path = _require_repo_path_without_symlinks(
        root,
        _canonical_path(root, CANDIDATE_MANIFEST_REF),
        "candidate manifest",
    )
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != binding["sha256"]:
        raise SpecError("candidate snapshot hash differs from the open seal")
    records = read_jsonl_bytes(data, CANDIDATE_MANIFEST_REF)
    expected = compile_candidates(_canonical_path(root, SPEC_DIR_REF))
    if tuple(map(canonical_json, records)) != tuple(map(canonical_json, expected)):
        raise SpecError("candidate snapshot is not the canonical 16-candidate enumeration")
    return records


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
    allow_committed_result: bool,
) -> None:
    commits = _git(
        root,
        "rev-list",
        "--reverse",
        "--ancestry-path",
        f"{preregistration_commit}..HEAD",
    ).stdout.decode("ascii", errors="strict").splitlines()
    if not commits:
        raise SpecError("development-open manifest has not been committed")
    previous = preregistration_commit
    for commit in commits:
        ancestry = _git(root, "rev-list", "--parents", "-n", "1", commit).stdout.decode(
            "ascii", errors="strict"
        ).split()
        if len(ancestry) != 2 or ancestry[1] != previous:
            raise SpecError("development opening history must be a linear direct-child chain")
        previous = commit
    if _commit_changes(root, commits[0]) != {f"A\t{DEVELOPMENT_OPEN_REF}"}:
        raise SpecError(
            "the first post-preregistration commit must add only the registered "
            "development-open manifest"
        )
    if not allow_committed_result and len(commits) != 1:
        raise SpecError("development execution must occur at the opening commit")
    if len(commits) >= 2 and _commit_changes(root, commits[1]) != {
        f"A\t{RESULT_PATH.as_posix()}"
    }:
        raise SpecError("the second post-preregistration commit must add only the result ledger")
    allowed_record_changes = {
        f"{status}\t{path}"
        for path in POST_RESULT_RECORD_PATHS
        for status in ("A", "M")
    }
    for commit in commits[2:]:
        changes = _commit_changes(root, commit)
        if not changes or not changes <= allowed_record_changes:
            raise SpecError(
                "post-result commits used during verification may change only "
                "registered non-executable research records"
            )


def _require_canonical_json_file(path: Path, value: dict[str, Any], label: str) -> None:
    expected = (canonical_json(value) + "\n").encode("ascii")
    if path.read_bytes() != expected:
        raise SpecError(f"{label} is not byte-canonical JSON")


def verify_outcome_seal(path: Path, *, require_committed: bool = False) -> dict[str, Any]:
    root = repository_root()
    path = _require_registered_path(path, OUTCOME_SEAL_REF, "outcome seal")
    audit = audit_design(_canonical_path(root, SPEC_DIR_REF))
    seal = load_json(path)
    _require_canonical_json_file(path, seal, "outcome seal")
    expected_seal_keys = {
        "contract_version",
        "search_id",
        "status",
        "spec_files",
        "candidate_manifest",
        "implementation_files",
        "development_command_enabled",
        "held_out_command_available",
        "opening_condition",
    }
    if set(seal) != expected_seal_keys:
        raise SpecError("seal has missing or unexpected top-level keys")
    if seal["contract_version"] != "0.2-draft" or seal["search_id"] != "MIR-REFERENCE-SEARCH-001":
        raise SpecError("seal identity mismatch")
    if seal["status"] != "outcomes_sealed":
        raise SpecError("seal status is not outcomes_sealed")
    if seal["development_command_enabled"] is not False:
        raise SpecError("sealed manifest enables development outcomes")
    if seal["held_out_command_available"] is not False:
        raise SpecError("sealed manifest exposes held-out access")
    if seal["opening_condition"] != OPENING_CONDITION:
        raise SpecError("sealed manifest opening condition mismatch")
    if set(seal["spec_files"]) != set(DESIGN_FILENAMES):
        raise SpecError("seal spec_files set is incomplete or unexpected")
    if set(seal["implementation_files"]) != set(IMPLEMENTATION_FILES):
        raise SpecError("seal implementation_files set is incomplete or unexpected")
    candidate_binding = _require_binding(seal["candidate_manifest"], "candidate manifest")
    if candidate_binding["path"] != CANDIDATE_MANIFEST_REF:
        raise SpecError("seal candidate manifest path is not registered")
    for relative_path, expected in seal["spec_files"].items():
        _require_digest(expected, f"spec hash for {relative_path}")
        spec_path = _canonical_path(root, f"{SPEC_DIR_REF}/{relative_path}")
        if sha256_file(spec_path) != expected or audit.hashes[relative_path] != expected:
            raise SpecError(f"spec hash mismatch: {relative_path}")
        if require_committed:
            _require_committed_bytes(root, spec_path, f"spec file {relative_path}")
    candidate_path = _canonical_path(root, CANDIDATE_MANIFEST_REF)
    if sha256_file(candidate_path) != candidate_binding["sha256"]:
        raise SpecError("candidate manifest hash mismatch")
    compiled = read_jsonl(candidate_path)
    expected_candidates = compile_candidates(_canonical_path(root, SPEC_DIR_REF))
    if tuple(map(canonical_json, compiled)) != tuple(map(canonical_json, expected_candidates)):
        raise SpecError("candidate manifest is not the canonical 16-candidate enumeration")
    if require_committed:
        _require_committed_bytes(root, candidate_path, "candidate manifest")
    for relative_path, expected in seal["implementation_files"].items():
        _require_digest(expected, f"implementation hash for {relative_path}")
        implementation_path = _canonical_path(root, relative_path)
        if sha256_file(implementation_path) != expected:
            raise SpecError(f"implementation hash mismatch: {relative_path}")
        if require_committed:
            _require_committed_bytes(root, implementation_path, f"implementation file {relative_path}")
    if require_committed:
        _require_committed_bytes(root, path, "outcome seal")
    return seal


def _write_new_canonical(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise SpecError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(value) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_development_open(path: Path, *, require_clean: bool) -> dict[str, Any]:
    root = repository_root()
    path = _require_registered_path(path, DEVELOPMENT_OPEN_REF, "development-open manifest")
    open_seal = load_json(path)
    _require_canonical_json_file(path, open_seal, "development-open manifest")
    expected_keys = {
        "contract_version",
        "search_id",
        "status",
        "data_class",
        "parent_outcome_seal",
        "candidate_manifest",
        "result_schema",
        "result_path",
        "preregistration_commit",
        "development_command_enabled",
        "held_out_command_available",
        "translation_offsets",
        "formation_horizon_ticks",
        "last_required_layer",
        "endpoint",
        "nonpass_record",
        "opening_condition_satisfied",
    }
    if set(open_seal) != expected_keys:
        raise SpecError("development-open manifest has missing or unexpected keys")
    expected_values = {
        "contract_version": "0.2-draft",
        "search_id": "MIR-REFERENCE-SEARCH-001",
        "status": "development_open",
        "data_class": "development",
        "result_path": RESULT_PATH.as_posix(),
        "development_command_enabled": True,
        "held_out_command_available": False,
        "translation_offsets": {"first": 0, "last": 47, "count": 48},
        "formation_horizon_ticks": 16,
        "last_required_layer": 18,
        "endpoint": "formation_by_H16",
        "nonpass_record": "right_censored_T_proto_gt_16",
        "opening_condition_satisfied": OPENING_CONDITION_SATISFIED,
    }
    for key, expected in expected_values.items():
        if open_seal[key] != expected:
            raise SpecError(f"development-open manifest {key} mismatch")
    parent = _require_binding(open_seal["parent_outcome_seal"], "parent outcome seal")
    if parent["path"] != OUTCOME_SEAL_REF:
        raise SpecError("development-open parent seal path mismatch")
    parent_path = _canonical_path(root, OUTCOME_SEAL_REF)
    if sha256_file(parent_path) != parent["sha256"]:
        raise SpecError("development-open parent seal hash mismatch")
    outcome_seal = verify_outcome_seal(parent_path, require_committed=True)
    candidate = _require_binding(open_seal["candidate_manifest"], "candidate manifest")
    if candidate != outcome_seal["candidate_manifest"]:
        raise SpecError("development-open candidate binding differs from parent seal")
    schema = _require_binding(open_seal["result_schema"], "result schema")
    if schema["path"] != RESULT_SCHEMA_REF:
        raise SpecError("development-open result schema path mismatch")
    schema_path = _canonical_path(root, RESULT_SCHEMA_REF)
    if sha256_file(schema_path) != schema["sha256"]:
        raise SpecError("development-open result schema hash mismatch")
    _require_committed_bytes(root, schema_path, "result schema")
    _require_committed_bytes(root, path, "development-open manifest")
    preregistration_commit = open_seal["preregistration_commit"]
    if (
        type(preregistration_commit) is not str
        or len(preregistration_commit) != 40
        or any(character not in "0123456789abcdef" for character in preregistration_commit)
    ):
        raise SpecError("development-open preregistration commit is invalid")
    head = _git_head(root)
    if head == preregistration_commit:
        raise SpecError("development-open manifest must be committed after preregistration")
    if _git(root, "cat-file", "-e", f"{preregistration_commit}^{{commit}}", check=False).returncode != 0:
        raise SpecError("development-open preregistration commit does not exist")
    if _git(root, "merge-base", "--is-ancestor", preregistration_commit, head, check=False).returncode != 0:
        raise SpecError("development-open preregistration commit is not an ancestor of HEAD")
    if _git(root, "cat-file", "-e", f"{preregistration_commit}:{DEVELOPMENT_OPEN_REF}", check=False).returncode == 0:
        raise SpecError("development-open manifest already existed in the preregistration commit")
    _require_bytes_at_commit(
        root,
        parent_path,
        preregistration_commit,
        "parent outcome seal",
    )
    candidate_path = _canonical_path(root, outcome_seal["candidate_manifest"]["path"])
    _require_bytes_at_commit(
        root,
        candidate_path,
        preregistration_commit,
        "candidate manifest",
    )
    for relative_path in outcome_seal["spec_files"]:
        _require_bytes_at_commit(
            root,
            _canonical_path(root, f"{SPEC_DIR_REF}/{relative_path}"),
            preregistration_commit,
            f"spec file {relative_path}",
        )
    for relative_path in outcome_seal["implementation_files"]:
        _require_bytes_at_commit(
            root,
            _canonical_path(root, relative_path),
            preregistration_commit,
            f"implementation file {relative_path}",
        )
    _require_opening_history(
        root,
        preregistration_commit,
        allow_committed_result=not require_clean,
    )
    if require_clean:
        _require_clean_worktree(root)
    return open_seal


def command_audit(args: argparse.Namespace) -> int:
    audit = audit_design(args.spec_dir)
    print(
        f"PASS {audit.search_id}: contract={audit.contract_version} "
        f"status={audit.status} files={len(audit.hashes)}"
    )
    return 0


def command_compile(args: argparse.Namespace) -> int:
    audit_design(args.spec_dir)
    candidates = compile_candidates(args.spec_dir)
    write_jsonl(args.output, candidates)
    print(f"WROTE {args.output}: candidates={len(candidates)} sha256={sha256_file(args.output)}")
    return 0


def command_freeze_seal(args: argparse.Namespace) -> int:
    root = repository_root()
    spec_dir = _require_registered_path(args.spec_dir, SPEC_DIR_REF, "spec directory")
    candidates_path = _require_registered_path(args.candidates, CANDIDATE_MANIFEST_REF, "candidate manifest")
    output_path = _require_registered_path(args.output, OUTCOME_SEAL_REF, "outcome seal")
    audit = audit_design(spec_dir)
    compiled = read_jsonl(candidates_path)
    expected = compile_candidates(spec_dir)
    if tuple(map(canonical_json, compiled)) != tuple(map(canonical_json, expected)):
        raise SpecError("candidate manifest does not equal the canonical 16-candidate enumeration")
    seal = {
        "contract_version": audit.contract_version,
        "search_id": audit.search_id,
        "status": "outcomes_sealed",
        "spec_files": {name: audit.hashes[name] for name in DESIGN_FILENAMES},
        "candidate_manifest": {
            "path": CANDIDATE_MANIFEST_REF,
            "sha256": sha256_file(candidates_path),
        },
        "implementation_files": {
            name: sha256_file(root / name) for name in IMPLEMENTATION_FILES
        },
        "development_command_enabled": False,
        "held_out_command_available": False,
        "opening_condition": OPENING_CONDITION,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_json(seal) + "\n", encoding="utf-8")
    print(f"WROTE {output_path}: sha256={sha256_file(output_path)} status=outcomes_sealed")
    return 0


def command_verify_seal(args: argparse.Namespace) -> int:
    verify_outcome_seal(args.seal)
    print(f"PASS {args.seal}: status=outcomes_sealed hashes=verified")
    return 0


def command_open_development(args: argparse.Namespace) -> int:
    root = repository_root()
    seal_path = _require_registered_path(args.seal, OUTCOME_SEAL_REF, "outcome seal")
    seal = verify_outcome_seal(seal_path, require_committed=True)
    _require_clean_worktree(root)
    open_path = _canonical_path(root, DEVELOPMENT_OPEN_REF)
    if open_path.exists():
        raise SpecError(f"refusing to overwrite existing development-open manifest: {open_path}")
    preregistration_commit = _git_head(root)
    open_seal = {
        "contract_version": "0.2-draft",
        "search_id": "MIR-REFERENCE-SEARCH-001",
        "status": "development_open",
        "data_class": "development",
        "parent_outcome_seal": {
            "path": OUTCOME_SEAL_REF,
            "sha256": sha256_file(seal_path),
        },
        "candidate_manifest": dict(seal["candidate_manifest"]),
        "result_schema": {
            "path": RESULT_SCHEMA_REF,
            "sha256": sha256_file(_canonical_path(root, RESULT_SCHEMA_REF)),
        },
        "result_path": RESULT_PATH.as_posix(),
        "preregistration_commit": preregistration_commit,
        "development_command_enabled": True,
        "held_out_command_available": False,
        "translation_offsets": {"first": 0, "last": 47, "count": 48},
        "formation_horizon_ticks": 16,
        "last_required_layer": 18,
        "endpoint": "formation_by_H16",
        "nonpass_record": "right_censored_T_proto_gt_16",
        "opening_condition_satisfied": OPENING_CONDITION_SATISFIED,
    }
    _write_new_canonical(open_path, open_seal)
    print(
        f"WROTE {open_path}: status=development_open sha256={sha256_file(open_path)}; "
        "commit this manifest before run-development"
    )
    return 0


def command_run_development(args: argparse.Namespace) -> int:
    root = repository_root()
    open_path = _require_registered_path(args.open_seal, DEVELOPMENT_OPEN_REF, "development-open manifest")
    open_seal = load_development_open(open_path, require_clean=True)
    result_path = _require_repo_path_without_symlinks(
        root,
        _canonical_path(root, RESULT_PATH.as_posix()),
        "development result",
    )
    if result_path.exists():
        raise DevelopmentRunError(f"refusing to overwrite existing result ledger: {result_path}")
    candidates = _candidate_snapshot(root, open_seal["candidate_manifest"])
    ledger = build_result_ledger(
        root=root,
        open_seal_path=open_path,
        open_seal=open_seal,
        candidates=candidates,
        evaluator=_exact_translation_evaluator,
    )
    validate_result_ledger(ledger, candidates)
    reverified_open_seal = load_development_open(open_path, require_clean=True)
    if canonical_json(reverified_open_seal) != canonical_json(open_seal):
        raise DevelopmentRunError("development-open manifest changed during evaluation")
    reverified_candidates = _candidate_snapshot(
        root,
        reverified_open_seal["candidate_manifest"],
    )
    if tuple(map(canonical_json, reverified_candidates)) != tuple(
        map(canonical_json, candidates)
    ):
        raise DevelopmentRunError("candidate snapshot changed during evaluation")
    expected_ledger_bindings = {
        "open_seal": {
            "path": DEVELOPMENT_OPEN_REF,
            "sha256": sha256_file(open_path),
        },
        "parent_outcome_seal": reverified_open_seal["parent_outcome_seal"],
        "candidate_manifest": reverified_open_seal["candidate_manifest"],
        "result_schema": reverified_open_seal["result_schema"],
    }
    for key, expected in expected_ledger_bindings.items():
        if ledger[key] != expected:
            raise DevelopmentRunError(
                f"result ledger {key} binding drifted during evaluation"
            )
    reverified_result_path = _require_repo_path_without_symlinks(
        root,
        _canonical_path(root, RESULT_PATH.as_posix()),
        "development result",
    )
    if reverified_result_path != result_path:
        raise DevelopmentRunError("development result path changed during evaluation")
    write_result_ledger(result_path, ledger, candidates)
    print(f"WROTE {result_path}: sha256={sha256_file(result_path)} data_class=development")
    return 0


def command_verify_development_results(args: argparse.Namespace) -> int:
    root = repository_root()
    _require_result_verification_worktree(root)
    open_path = _require_registered_path(args.open_seal, DEVELOPMENT_OPEN_REF, "development-open manifest")
    open_seal = load_development_open(open_path, require_clean=False)
    result_path = _require_repo_path_without_symlinks(
        root,
        _canonical_path(root, RESULT_PATH.as_posix()),
        "development result",
    )
    ledger = load_json(result_path)
    canonical_bytes = (canonical_json(ledger) + "\n").encode("ascii")
    if result_path.read_bytes() != canonical_bytes:
        raise DevelopmentRunError("development result is not byte-canonical JSON")
    candidates = _candidate_snapshot(root, open_seal["candidate_manifest"])
    validate_result_ledger(ledger, candidates)
    expected = build_result_ledger(
        root=root,
        open_seal_path=open_path,
        open_seal=open_seal,
        candidates=candidates,
        evaluator=_exact_translation_evaluator,
    )
    if canonical_json(ledger) != canonical_json(expected):
        raise DevelopmentRunError("development result differs from exact in-memory recomputation")
    print(f"PASS {result_path}: exact development recomputation and canonical bytes verified")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Outcome-safe minimal-realization tooling.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit", help="audit the sealed design without running dynamics")
    audit_parser.add_argument("--spec-dir", type=Path, required=True)
    audit_parser.set_defaults(func=command_audit)

    compile_parser = subparsers.add_parser("compile", help="compile the canonical outcome-free candidate list")
    compile_parser.add_argument("--spec-dir", type=Path, required=True)
    compile_parser.add_argument("--output", type=Path, required=True)
    compile_parser.set_defaults(func=command_compile)

    seal_parser = subparsers.add_parser("freeze-seal", help="bind an outcome-sealed manifest to content hashes")
    seal_parser.add_argument("--spec-dir", type=Path, required=True)
    seal_parser.add_argument("--candidates", type=Path, required=True)
    seal_parser.add_argument("--output", type=Path, required=True)
    seal_parser.set_defaults(func=command_freeze_seal)

    verify_parser = subparsers.add_parser("verify-seal", help="verify every content hash in an outcome seal")
    verify_parser.add_argument("--seal", type=Path, required=True)
    verify_parser.set_defaults(func=command_verify_seal)

    open_parser = subparsers.add_parser(
        "open-development",
        help="create the registered development-open manifest without running dynamics",
    )
    open_parser.add_argument("--seal", type=Path, required=True)
    open_parser.set_defaults(func=command_open_development)

    run_parser = subparsers.add_parser(
        "run-development",
        help="run the committed, fixed development allocation to a no-clobber ledger",
    )
    run_parser.add_argument("--open-seal", type=Path, required=True)
    run_parser.set_defaults(func=command_run_development)

    result_parser = subparsers.add_parser(
        "verify-development-results",
        help="recompute and byte-verify the fixed development result without overwrite",
    )
    result_parser.add_argument("--open-seal", type=Path, required=True)
    result_parser.set_defaults(func=command_verify_development_results)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, SpecError, DevelopmentRunError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
