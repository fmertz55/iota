"""Outcome-safe design, seal, and authorization commands for direct QCA."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .authorization import authorization_status
from .manifest import validate_committed_manifests
from .protocol import CONFIRMATION_RESULT_REF, DEVELOPMENT_RESULT_REF
from .seal import preview_disabled_seal, verify_outcome_seal, write_disabled_seal
from .spec import SymmetryQCASpecError, audit_design, load_json, repository_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("audit-design")
    commands.add_parser("validate-manifests")
    commands.add_parser("preview-disabled-seal")
    commands.add_parser("authorization-status")
    commands.add_parser("seal-outcomes")
    verify = commands.add_parser("verify-seal")
    verify.add_argument("--require-freeze-tag-at-head", action="store_true")
    opening = commands.add_parser("open-stage")
    opening.add_argument(
        "--stage", choices=("development", "confirmation"), required=True
    )
    authorize = commands.add_parser("authorize-stage")
    authorize.add_argument(
        "--stage", choices=("development", "confirmation"), required=True
    )
    run = commands.add_parser("run-stage")
    run.add_argument(
        "--stage", choices=("development", "confirmation"), required=True
    )
    verify_result = commands.add_parser("verify-result")
    verify_result.add_argument(
        "--stage", choices=("development", "confirmation"), required=True
    )
    return parser


def _result_ref(stage: str) -> str:
    return DEVELOPMENT_RESULT_REF if stage == "development" else CONFIRMATION_RESULT_REF


def _seal(root: Path) -> dict[str, object]:
    from .lifecycle import require_clean

    require_clean(root)
    path = write_disabled_seal(root)
    return {
        "status": "outcomes_sealed_disabled",
        "path": path.relative_to(root).as_posix(),
        "instruction": "commit this seal alone, then create the required annotated tag",
    }


def _verify(root: Path, *, require_tag: bool) -> dict[str, object]:
    value = verify_outcome_seal(root)
    result: dict[str, object] = {
        "status": "outcome_seal_verified",
        "freeze_parent_commit": value["freeze_parent_commit"],
    }
    if require_tag:
        from .lifecycle import freeze_commit, require_clean

        require_clean(root)
        freeze = freeze_commit(root)
        head = __import__("subprocess").run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            stdout=__import__("subprocess").PIPE,
            text=True,
        ).stdout.strip()
        if freeze != head:
            raise SymmetryQCASpecError("freeze tag does not identify HEAD")
        result["freeze_commit"] = freeze
    return result


def _open(root: Path, *, stage: str) -> dict[str, object]:
    from .lifecycle import write_open_manifest

    path = write_open_manifest(stage=stage, root=root)
    return {
        "status": "stage_open_manifest_written",
        "stage": stage,
        "path": path.relative_to(root).as_posix(),
        "instruction": "commit this opening file alone before requesting a permit",
    }


def _authorize(root: Path, *, stage: str) -> dict[str, object]:
    from .authorization import issue_registered_permit

    permit = issue_registered_permit(stage=stage, root=root)
    return {
        "status": "registered_stage_authorized_without_evaluation",
        "stage": permit.stage,
        "freeze_commit": permit.freeze_commit,
        "opening_commit": permit.opening_commit,
        "registered_evaluation_performed": False,
    }


def _run(root: Path, *, stage: str) -> dict[str, object]:
    # Cross the Git/provenance gate before importing any evaluator.
    from .authorization import issue_registered_permit

    permit = issue_registered_permit(stage=stage, root=root)
    from .ledger import write_result_ledger
    from .lifecycle import result_bindings
    from .runner import build_stage_ledger

    result_ref = _result_ref(stage)
    path = root / result_ref
    if path.exists():
        raise SymmetryQCASpecError("registered result already exists")
    ledger = build_stage_ledger(
        permit, bindings=result_bindings(stage=stage, root=root)
    )
    write_result_ledger(path, ledger, stage=stage)
    return {
        "status": "registered_stage_result_written",
        "stage": stage,
        "classification": ledger["status"],
        "path": result_ref,
        "instruction": "commit this file alone before inspection or verification",
    }


def _verify_result(root: Path, *, stage: str) -> dict[str, object]:
    from .authorization import issue_verification_permit

    permit = issue_verification_permit(stage=stage, root=root)
    from .independent_verifier import verify_ledger_independently
    from .ledger import validate_result_ledger
    from .lifecycle import verify_ledger_bindings

    result_ref = _result_ref(stage)
    ledger = load_json(root / result_ref)
    validate_result_ledger(ledger, expected_stage=stage)
    verify_ledger_bindings(ledger, stage=stage, root=root)
    verify_ledger_independently(permit, ledger)
    return {
        "status": "registered_stage_result_independently_verified",
        "stage": stage,
        "classification": ledger["status"],
        "path": result_ref,
    }


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    root = repository_root() if arguments.root is None else arguments.root.resolve()
    try:
        if arguments.command == "audit-design":
            value = audit_design(root)
        elif arguments.command == "validate-manifests":
            value = validate_committed_manifests(root)
        elif arguments.command == "preview-disabled-seal":
            value = preview_disabled_seal(root)
        elif arguments.command == "authorization-status":
            value = authorization_status(root)
        elif arguments.command == "seal-outcomes":
            value = _seal(root)
        elif arguments.command == "verify-seal":
            value = _verify(
                root, require_tag=arguments.require_freeze_tag_at_head
            )
        elif arguments.command == "open-stage":
            value = _open(root, stage=arguments.stage)
        elif arguments.command == "authorize-stage":
            value = _authorize(root, stage=arguments.stage)
        elif arguments.command == "run-stage":
            value = _run(root, stage=arguments.stage)
        elif arguments.command == "verify-result":
            value = _verify_result(root, stage=arguments.stage)
        else:  # pragma: no cover
            raise SymmetryQCASpecError("unknown command")
    except (SymmetryQCASpecError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
