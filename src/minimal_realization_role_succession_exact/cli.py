"""Outcome-safe command surface for the exact role-succession closure."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.minimal_realization_role_succession.manifest import canonical_json, sha256_file

from .manifest import (
    compile_continuation_candidates,
    load_and_validate_parent,
    read_jsonl,
    validate_continuation_manifest,
    write_jsonl_once,
)
from .protocol import (
    CANDIDATE_MANIFEST_REF,
    FREEZE_TAG,
    OPEN_MANIFEST_REF,
    OUTCOME_SEAL_REF,
    PARENT_RESULT_COMMIT,
    PARENT_RESULT_REF,
    PARENT_RESULT_SHA256,
    PROTOCOL_VERSION,
    REGISTERED_WORKER_PROCESSES,
    RESULT_PATH_REF,
    RESULT_SCHEMA_REF,
    SEARCH_ID,
    opening_condition,
)
from .runner import build_result_ledger, validate_result_ledger
from .seal import (
    ExactSealError,
    build_outcome_seal,
    load_canonical_json,
    repository_root,
    verify_outcome_seal,
    write_canonical_json_once,
)
from .verifier import verify_ledger_independently


class ExactCommandError(ValueError):
    pass


def _path(root: Path, relative: str) -> Path:
    root = root.resolve()
    value = (root / relative).resolve()
    try:
        value.relative_to(root)
    except ValueError as exc:
        raise ExactCommandError(f"registered path escapes repository: {relative}") from exc
    return value


def _binding(root: Path, relative: str) -> dict[str, str]:
    path = _path(root, relative)
    if not path.is_file():
        raise ExactCommandError(f"registered file is missing: {relative}")
    return {"path": relative, "sha256": sha256_file(path)}


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise ExactCommandError(f"git {' '.join(arguments)} failed: {message}")
    return result


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD").stdout.decode("ascii").strip()


def _parent(root: Path, commit: str) -> str:
    return _git(root, "rev-parse", f"{commit}^").stdout.decode("ascii").strip()


def _clean(root: Path) -> None:
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise ExactCommandError("worktree must be clean")


def _tag_commit(root: Path) -> str:
    ref = f"refs/tags/{FREEZE_TAG}"
    kind = _git(root, "cat-file", "-t", ref, check=False)
    if kind.returncode or kind.stdout.strip() != b"tag":
        raise ExactCommandError(f"required annotated freeze tag is missing: {FREEZE_TAG}")
    return _git(root, "rev-parse", f"{ref}^{{commit}}").stdout.decode("ascii").strip()


def _path_at(root: Path, commit: str, relative: str) -> bool:
    return _git(root, "cat-file", "-e", f"{commit}:{relative}", check=False).returncode == 0


def _changes(root: Path, commit: str) -> list[str]:
    output = _git(
        root,
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "--no-renames",
        "-r",
        commit,
    ).stdout.decode("utf-8").splitlines()
    return output


def _require_committed(root: Path, relative: str) -> None:
    result = _git(root, "show", f"HEAD:{relative}", check=False)
    path = _path(root, relative)
    if result.returncode or not path.is_file() or result.stdout != path.read_bytes():
        raise ExactCommandError(f"registered bytes are not committed at HEAD: {relative}")


def _require_freeze(root: Path) -> str:
    freeze = _tag_commit(root)
    freeze_parent = _parent(root, freeze)
    if freeze_parent != PARENT_RESULT_COMMIT:
        raise ExactCommandError("freeze commit is not the direct child of the parent result")
    if _path_at(root, freeze_parent, OUTCOME_SEAL_REF):
        raise ExactCommandError("outcome seal existed before the freeze commit")
    if _changes(root, freeze).count(f"A\t{OUTCOME_SEAL_REF}") != 1:
        raise ExactCommandError("freeze commit did not introduce the outcome seal")
    if not _path_at(root, freeze, OUTCOME_SEAL_REF):
        raise ExactCommandError("outcome seal is absent from the freeze commit")
    return freeze


def _expected_open(root: Path, freeze: str) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": "outcomes_opened",
        "freeze_tag": FREEZE_TAG,
        "freeze_commit": freeze,
        "parent_result_commit": PARENT_RESULT_COMMIT,
        "parent_result": {"path": PARENT_RESULT_REF, "sha256": PARENT_RESULT_SHA256},
        "candidate_manifest": _binding(root, CANDIDATE_MANIFEST_REF),
        "outcome_seal": _binding(root, OUTCOME_SEAL_REF),
        "result_schema": _binding(root, RESULT_SCHEMA_REF),
        "opening_condition_satisfied": opening_condition(),
        "run_command_enabled": True,
        "result_path": RESULT_PATH_REF,
    }


def _require_open_commit(root: Path) -> tuple[str, str]:
    freeze = _require_freeze(root)
    opening = _head(root)
    if _parent(root, opening) != freeze:
        raise ExactCommandError("opening commit is not the direct child of the freeze")
    if _path_at(root, freeze, OPEN_MANIFEST_REF):
        raise ExactCommandError("open manifest already existed at freeze")
    if _changes(root, opening) != [f"A\t{OPEN_MANIFEST_REF}"]:
        raise ExactCommandError("opening commit must add only the open manifest")
    _require_committed(root, OPEN_MANIFEST_REF)
    open_value = load_canonical_json(_path(root, OPEN_MANIFEST_REF))
    if open_value != _expected_open(root, freeze):
        raise ExactCommandError("open manifest differs from registered provenance")
    return freeze, opening


def compile_candidates_command(root: Path) -> None:
    if _path(root, CANDIDATE_MANIFEST_REF).exists():
        raise ExactCommandError("continuation candidate manifest already exists")
    parent = load_and_validate_parent(root)
    records = compile_continuation_candidates(parent)
    write_jsonl_once(_path(root, CANDIDATE_MANIFEST_REF), records)
    print(
        f"WROTE {CANDIDATE_MANIFEST_REF} records={len(records)} "
        f"sha256={sha256_file(_path(root, CANDIDATE_MANIFEST_REF))}"
    )


def seal_command(root: Path) -> None:
    value = build_outcome_seal(root)
    write_canonical_json_once(_path(root, OUTCOME_SEAL_REF), value)
    print(
        f"SEALED disabled {OUTCOME_SEAL_REF} "
        f"sha256={sha256_file(_path(root, OUTCOME_SEAL_REF))}"
    )


def verify_seal_command(root: Path, *, require_tag_at_head: bool) -> None:
    verify_outcome_seal(_path(root, OUTCOME_SEAL_REF), root=root)
    if require_tag_at_head:
        _clean(root)
        freeze = _require_freeze(root)
        if freeze != _head(root):
            raise ExactCommandError("freeze tag does not select HEAD")
    print("PASS exact-closure outcome seal and registered content hashes")


def open_command(root: Path) -> None:
    _clean(root)
    freeze = _require_freeze(root)
    if freeze != _head(root):
        raise ExactCommandError("outcomes may open only at the tagged freeze commit")
    verify_outcome_seal(_path(root, OUTCOME_SEAL_REF), root=root)
    for forbidden in (OPEN_MANIFEST_REF, RESULT_PATH_REF):
        if _path(root, forbidden).exists():
            raise ExactCommandError(f"registered artifact already exists: {forbidden}")
    write_canonical_json_once(_path(root, OPEN_MANIFEST_REF), _expected_open(root, freeze))
    print(f"OPENED {OPEN_MANIFEST_REF}; commit this file alone before running")


def run_command(root: Path) -> None:
    _clean(root)
    _, opening = _require_open_commit(root)
    verify_outcome_seal(_path(root, OUTCOME_SEAL_REF), root=root)
    if _path(root, RESULT_PATH_REF).exists() or _path_at(root, opening, RESULT_PATH_REF):
        raise ExactCommandError("registered result already exists")
    parent = load_and_validate_parent(root)
    candidates = read_jsonl(_path(root, CANDIDATE_MANIFEST_REF))
    validate_continuation_manifest(candidates, parent)
    ledger = build_result_ledger(
        root=root,
        candidates=candidates,
        open_manifest_binding=_binding(root, OPEN_MANIFEST_REF),
        outcome_seal_binding=_binding(root, OUTCOME_SEAL_REF),
        candidate_manifest_binding=_binding(root, CANDIDATE_MANIFEST_REF),
        result_schema_binding=_binding(root, RESULT_SCHEMA_REF),
        worker_processes=REGISTERED_WORKER_PROCESSES,
    )
    write_canonical_json_once(_path(root, RESULT_PATH_REF), ledger)
    print(
        f"WROTE {RESULT_PATH_REF} sha256={sha256_file(_path(root, RESULT_PATH_REF))}; "
        "commit this result alone before inspection or verification"
    )


def verify_results_command(root: Path) -> None:
    _clean(root)
    freeze = _require_freeze(root)
    result_commit = _head(root)
    opening = _parent(root, result_commit)
    if _parent(root, opening) != freeze:
        raise ExactCommandError("result/open/freeze commits are not direct descendants")
    if _changes(root, opening) != [f"A\t{OPEN_MANIFEST_REF}"]:
        raise ExactCommandError("opening commit provenance mismatch")
    if _changes(root, result_commit) != [f"A\t{RESULT_PATH_REF}"]:
        raise ExactCommandError("result commit must add only the registered result")
    if _path_at(root, opening, RESULT_PATH_REF):
        raise ExactCommandError("result existed before the result commit")
    for relative in (OPEN_MANIFEST_REF, RESULT_PATH_REF):
        _require_committed(root, relative)
    verify_outcome_seal(_path(root, OUTCOME_SEAL_REF), root=root)
    parent = load_and_validate_parent(root)
    candidates = read_jsonl(_path(root, CANDIDATE_MANIFEST_REF))
    ledger = load_canonical_json(_path(root, RESULT_PATH_REF))
    validate_result_ledger(ledger, candidates, parent)
    verify_ledger_independently(root, ledger, candidates)
    print("PASS exact-closure result, ANF certificates, and any dynamic replays")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("compile-candidates")
    subparsers.add_parser("seal-outcomes")
    verify = subparsers.add_parser("verify-seal")
    verify.add_argument("--require-freeze-tag-at-head", action="store_true")
    subparsers.add_parser("open-outcomes")
    subparsers.add_parser("run")
    subparsers.add_parser("verify-results")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    root = repository_root() if arguments.root is None else arguments.root.resolve()
    try:
        if arguments.command == "compile-candidates":
            compile_candidates_command(root)
        elif arguments.command == "seal-outcomes":
            seal_command(root)
        elif arguments.command == "verify-seal":
            verify_seal_command(
                root,
                require_tag_at_head=arguments.require_freeze_tag_at_head,
            )
        elif arguments.command == "open-outcomes":
            open_command(root)
        elif arguments.command == "run":
            run_command(root)
        elif arguments.command == "verify-results":
            verify_results_command(root)
        else:  # pragma: no cover
            raise ExactCommandError("unknown command")
    except (ExactCommandError, ExactSealError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
