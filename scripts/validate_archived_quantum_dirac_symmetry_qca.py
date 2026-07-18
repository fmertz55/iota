#!/usr/bin/env python3

"""Validate the content-addressed direct symmetry-QCA v0.4 archive and replay receipt.

The normal invocation is intentionally useful before the documentation commit
and annotated completion tag exist.  Release validation additionally passes
``--require-completion-tag``.  During preparation, ``--skip-receipt`` validates
only the exact stage checkpoints and is explicitly reported as a
pre-receipt, pre-tag mode.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEARCH_ID = "ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001"
PROTOCOL_VERSION = "0.1-draft"
FREEZE_TAG = "icp-quantum-dirac-symmetry-qca-001-v0.4-frozen"
FREEZE_COMMIT = "890962df6a86637cf9a4fe8b40d88f21a02f2399"
COMPLETION_TAG = "icp-quantum-dirac-symmetry-qca-001-v0.4-complete"
OUTCOME_SEAL_REF = (
    "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/"
    "outcome_seal_v0.4.json"
)
OUTCOME_SEAL_SHA256 = (
    "ff3f58461559578b07ea7e93b8819edbad2bde66c95cc1af89f971a4110b974b"
)
RESULT_BASE = "output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001"
RECEIPT_REF = (
    "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/"
    "independent_verification_receipt_v0.4.json"
)
RECEIPT = ROOT / RECEIPT_REF
CHECKPOINT_PYTHON = ROOT / ".venv/bin/python"

STAGES = {
    "development": {
        "checkpoint_commit": "b96e70a1c0c61f64bd1bd51a0ecb9d021d9bef50",
        "opening_commit": "f5f5d6048a472b8a0d5506ead983993a37c8b68b",
        "ledger": {
            "path": f"{RESULT_BASE}/development_results_v0.4.json",
            "sha256": "89d7c65a37bf8d38fea3a87b7f656c02cae57664fcf6b53b725fb8ace7c228c4",
            "classification": "development_passed",
        },
    },
    "confirmation": {
        "checkpoint_commit": "0795a6efa0252411c66479cb87863349e20ec886",
        "opening_commit": "6398124a213584e2747aacbbc742596df054ab19",
        "ledger": {
            "path": f"{RESULT_BASE}/confirmation_results_v0.4.json",
            "sha256": "be5a9f85770e1d201abbc269c26da25d821f11f67db364c434473b5c70517e65",
            "classification": (
                "constructive_sufficiency_passed_direct_symmetry_qca_sector"
            ),
        },
    },
}
RESULT_COMMIT = STAGES["confirmation"]["checkpoint_commit"]

RUNTIME = {
    "mpmath_version": "1.3.0",
    "python_flint_version": "0.9.0",
    "python_implementation": "CPython",
    "python_version": "3.14.0",
}

KNOWN_EXCEPTION = {
    "affected_records": [
        "scenario_results[*].pi_sector.candidate_probability_upper",
        "scenario_results[*].pi_sector.pass",
        "aggregate.failure_controls[id=ROUGH-POTENTIAL]",
    ],
    "id": "shared_empty_pi_sector_predicate",
    "implemented_predicate": "4*abs(r)>=3*N",
    "registered_predicate": "8*abs(r)>=3*N",
    "remaining_support": (
        "pre-outcome analytic pi-tail bounds use the registered boundary"
    ),
    "replay_scope": (
        "the primary reducer and algorithmically separate verifier shared the "
        "empty implemented predicate"
    ),
    "status": "empirical_pi_sector_and_rough_potential_records_withdrawn",
}


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key!r}")
        value[key] = item
    return value


def reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def load_canonical_json(data: bytes, *, label: str) -> Any:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} is not UTF-8") from error
    value = json.loads(
        text,
        object_pairs_hook=no_duplicate_object,
        parse_constant=reject_nonfinite_constant,
    )
    if data != canonical_bytes(value):
        raise ValueError(f"{label} is not canonical JSON with one trailing newline")
    return value


def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(arguments)} failed: {detail}")
    return result


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def commit_changes(commit: str) -> list[str]:
    return git(
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "--no-renames",
        "-r",
        commit,
    ).stdout.decode("utf-8").splitlines()


def verify_annotated_tag(tag: str, expected_commit: str | None = None) -> str:
    reference = f"refs/tags/{tag}"
    kind = git("cat-file", "-t", reference, check=False)
    if kind.returncode or kind.stdout.strip() != b"tag":
        raise RuntimeError(f"missing annotated tag: {tag}")
    commit = git("rev-parse", f"{reference}^{{commit}}").stdout.decode().strip()
    if expected_commit is not None and commit != expected_commit:
        raise RuntimeError(f"{tag} resolves to {commit}, expected {expected_commit}")
    return commit


def verify_git_identity(*, require_completion_tag: bool) -> str | None:
    verify_annotated_tag(FREEZE_TAG, FREEZE_COMMIT)
    expected_parent = FREEZE_COMMIT
    for stage in ("development", "confirmation"):
        record = STAGES[stage]
        opening = str(record["opening_commit"])
        checkpoint = str(record["checkpoint_commit"])
        if git("rev-parse", f"{checkpoint}^{{commit}}").stdout.decode().strip() != checkpoint:
            raise RuntimeError(f"content-addressed {stage} checkpoint is unavailable")
        parent = git("rev-parse", f"{opening}^").stdout.decode().strip()
        if parent != expected_parent:
            raise RuntimeError(f"{stage} opening does not descend directly from {expected_parent}")
        if git("rev-parse", f"{checkpoint}^").stdout.decode().strip() != opening:
            raise RuntimeError(f"{stage} result is not the direct child of its opening")
        ledger_path = str(record["ledger"]["path"])
        expected_open_path = ledger_path.replace("results", "open_manifest").replace(
            f"{RESULT_BASE}/", f"experiments/quantum_dirac/{SEARCH_ID}/"
        )
        if commit_changes(opening) != [f"A\t{expected_open_path}"]:
            raise RuntimeError(f"{stage} opening commit does not add only its manifest")
        if commit_changes(checkpoint) != [f"A\t{ledger_path}"]:
            raise RuntimeError(f"{stage} result commit does not add only its ledger")
        if not git("show", f"{opening}:{ledger_path}", check=False).returncode:
            raise RuntimeError(f"{stage} ledger already existed at its opening commit")
        expected_parent = checkpoint

    if not require_completion_tag:
        return None
    completion = verify_annotated_tag(COMPLETION_TAG)
    if git("merge-base", "--is-ancestor", RESULT_COMMIT, completion, check=False).returncode:
        raise RuntimeError("completion tag does not descend from the content-addressed result")
    tagged_receipt = git("show", f"{completion}:{RECEIPT_REF}", check=False)
    if tagged_receipt.returncode:
        raise RuntimeError("completion-tagged commit does not contain the replay receipt")
    if tagged_receipt.stdout != RECEIPT.read_bytes():
        raise RuntimeError("completion-tagged receipt differs from the validated receipt")
    return completion


def verify_archived_json_blobs() -> None:
    seal = git("show", f"{FREEZE_COMMIT}:{OUTCOME_SEAL_REF}").stdout
    if digest(seal) != OUTCOME_SEAL_SHA256:
        raise RuntimeError("frozen outcome-seal hash mismatch")
    seal_value = load_canonical_json(seal, label="frozen outcome seal")
    if seal_value.get("required_freeze_tag") != FREEZE_TAG:
        raise RuntimeError("frozen outcome seal names a different freeze tag")

    for stage in ("development", "confirmation"):
        record = STAGES[stage]
        ledger_record = record["ledger"]
        path = str(ledger_record["path"])
        checkpoint = str(record["checkpoint_commit"])
        blob = git("show", f"{checkpoint}:{path}").stdout
        actual = digest(blob)
        if actual != ledger_record["sha256"]:
            raise RuntimeError(f"{stage} ledger: expected {ledger_record['sha256']}, got {actual}")
        ledger = load_canonical_json(blob, label=f"{stage} ledger")
        required_identity = {
            "protocol_version": PROTOCOL_VERSION,
            "search_id": SEARCH_ID,
            "stage": stage,
            "status": ledger_record["classification"],
        }
        for key, expected in required_identity.items():
            if ledger.get(key) != expected:
                raise RuntimeError(f"{stage} ledger field {key!r} is invalid")
        numerics = ledger.get("numerics", {})
        if (
            numerics.get("primary_library_version") != RUNTIME["python_flint_version"]
            or numerics.get("independent_library_version") != RUNTIME["mpmath_version"]
        ):
            raise RuntimeError(f"{stage} ledger runtime binding is invalid")


def extract_checkpoint(commit: str, destination: Path) -> None:
    archive = git("archive", "--format=tar", commit).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
        root = destination.resolve()
        for member in bundle.getmembers():
            target = (destination / member.name).resolve()
            if root != target and root not in target.parents:
                raise RuntimeError(f"unsafe path in checkpoint archive: {member.name}")
            if member.issym() or member.islnk():
                raise RuntimeError(f"links are not accepted in checkpoint archive: {member.name}")
        # Python 3.9 is still supported by the repository Make target.  The
        # explicit path and link checks above provide the extraction guard.
        bundle.extractall(destination)


def run_checkpoint_validation(checkpoint: Path, *, stage: str) -> None:
    code = f"""
from pathlib import Path
from src.quantum_dirac_symmetry_qca.ledger import validate_result_ledger
from src.quantum_dirac_symmetry_qca.lifecycle import verify_ledger_bindings
from src.quantum_dirac_symmetry_qca.manifest import validate_committed_manifests
from src.quantum_dirac_symmetry_qca.seal import verify_outcome_seal
from src.quantum_dirac_symmetry_qca.spec import load_json

root = Path.cwd()
validate_committed_manifests(root)
verify_outcome_seal(root)
stage = {stage!r}
ledger = load_json(root / {str(STAGES[stage]["ledger"]["path"])!r})
validate_result_ledger(ledger, expected_stage=stage)
verify_ledger_bindings(ledger, stage=stage, root=root)
print(f"{{stage}} checkpoint seal, manifests, ledger schema, and bindings verified")
"""
    python = CHECKPOINT_PYTHON if CHECKPOINT_PYTHON.is_file() else Path(sys.executable)
    subprocess.run([str(python), "-c", code], cwd=checkpoint, check=True)


def expected_cli_output(stage: str) -> str:
    ledger = STAGES[stage]["ledger"]
    return json.dumps(
        {
            "classification": ledger["classification"],
            "path": ledger["path"],
            "stage": stage,
            "status": "registered_stage_result_independently_verified",
        },
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def expected_receipt() -> dict[str, Any]:
    stage_receipts: dict[str, Any] = {}
    for stage in ("development", "confirmation"):
        record = STAGES[stage]
        stage_receipts[stage] = {
            "checkpoint_commit": record["checkpoint_commit"],
            "ledger": record["ledger"],
            "verification": {
                "command": (
                    "python -m src.quantum_dirac_symmetry_qca.cli --root . "
                    f"verify-result --stage {stage}"
                ),
                "status": "registered_stage_result_independently_verified",
                "stdout": expected_cli_output(stage),
            },
        }
    return {
        "completion_tag": COMPLETION_TAG,
        "known_exception": KNOWN_EXCEPTION,
        "outcome_seal": {"path": OUTCOME_SEAL_REF, "sha256": OUTCOME_SEAL_SHA256},
        "protocol_version": PROTOCOL_VERSION,
        "receipt_schema": "iota.independent-verification-receipt.v1",
        "runtime": RUNTIME,
        "search_id": SEARCH_ID,
        "stages": stage_receipts,
    }


def verify_receipt() -> None:
    if not RECEIPT.is_file() or RECEIPT.is_symlink():
        raise RuntimeError(f"independent verification receipt is missing: {RECEIPT_REF}")
    receipt = load_canonical_json(RECEIPT.read_bytes(), label="verification receipt")
    expected = expected_receipt()
    if receipt != expected:
        raise RuntimeError(
            "verification receipt does not match the exact v1 evidence schema"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-receipt",
        action="store_true",
        help=(
            "preparation only: validate exact checkpoints without requiring "
            "the replay receipt or completion tag"
        ),
    )
    parser.add_argument(
        "--require-completion-tag",
        action="store_true",
        help=(
            "release mode: require the annotated completion tag and require its "
            "target commit to contain the validated receipt bytes"
        ),
    )
    arguments = parser.parse_args(argv)
    if arguments.skip_receipt and arguments.require_completion_tag:
        parser.error("--skip-receipt cannot be combined with --require-completion-tag")
    try:
        if not arguments.skip_receipt:
            verify_receipt()
        verify_git_identity(require_completion_tag=arguments.require_completion_tag)
        verify_archived_json_blobs()
        with tempfile.TemporaryDirectory(prefix="iota-direct-qca-archive-") as temporary:
            for stage in ("development", "confirmation"):
                checkpoint = Path(temporary) / stage
                checkpoint.mkdir()
                extract_checkpoint(str(STAGES[stage]["checkpoint_commit"]), checkpoint)
                run_checkpoint_validation(checkpoint, stage=stage)
    except (
        RuntimeError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"FAIL archived direct-QCA validation: {error}", file=sys.stderr)
        return 2
    if arguments.skip_receipt:
        scope = "exact stage checkpoints (pre-receipt, pre-tag mode)"
    elif arguments.require_completion_tag:
        scope = "stage checkpoints, replay receipt, and annotated completion tag"
    else:
        scope = "stage checkpoints and replay receipt (pre-tag mode)"
    print(f"PASS archived direct symmetry-QCA v0.4 {scope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
