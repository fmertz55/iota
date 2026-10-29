"""Outcome-safe command line for ICP-DP-PERSISTENCE-001.

Run as ``python -m src.dp_persistence.cli <command>``.  Every stage command
refuses unless the committed seal, the annotated freeze tag on the
seal-introduction commit, a clean worktree, and (for runs) the stage's
committed open manifest all exist.  Runners are imported only after the
gates pass.  No command takes a grid, run-count, worker, or output override.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import calibration_models
from .ledger import LedgerError, canonical_json, validate_result, write_canonical_json_once
from .protocol import (
    ALL_PROTECTED_PATHS,
    CALIBRATION_OPEN_MANIFEST_REF,
    CALIBRATION_RESULT_REF,
    CONFIRMATION_OPEN_MANIFEST_REF,
    CONFIRMATION_RESULT_REF,
    DEVELOPMENT_OPEN_MANIFEST_REF,
    DEVELOPMENT_RESULT_REF,
    FREEZE_REVISION,
    FREEZE_TAG,
    OUTCOME_SEAL_REF,
    PROTOCOL_VERSION,
    REGISTERED_PATHS,
    REGISTERED_WORKER_PROCESSES,
    RESULT_SCHEMA_REF,
    SEARCH_ID,
    SPEC_FILES,
    STRUCTURAL_AUDIT_ANSWERS_REF,
    SUPERSEDED_FREEZE_TAG,
    SUPERSEDED_SEAL_REF,
    load_spec_file,
    repository_root,
)
from .seal import SealError, binding, load_canonical_json, repo_path, verify_outcome_seal, write_outcome_seal


STAGES = {
    "calibration": {
        "open_manifest": CALIBRATION_OPEN_MANIFEST_REF,
        "result": CALIBRATION_RESULT_REF,
        "result_kind": "calibration",
    },
    "development": {
        "open_manifest": DEVELOPMENT_OPEN_MANIFEST_REF,
        "result": DEVELOPMENT_RESULT_REF,
        "result_kind": "development",
    },
    "confirmation": {
        "open_manifest": CONFIRMATION_OPEN_MANIFEST_REF,
        "result": CONFIRMATION_RESULT_REF,
        "result_kind": "confirmation",
    },
}


class CommandError(ValueError):
    pass


# ----------------------------------------------------------------------------
# git helpers
# ----------------------------------------------------------------------------


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise CommandError(f"git {' '.join(arguments)} failed: {message}")
    return result


def _git_head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD").stdout.decode("ascii").strip()


def _require_clean_worktree(root: Path) -> None:
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise CommandError("worktree must be clean")


def _require_committed_bytes(root: Path, relative: str, label: str) -> None:
    path = repo_path(root, relative)
    if not path.is_file():
        raise CommandError(f"{label} is missing: {relative}")
    result = _git(root, "show", f"HEAD:{relative}", check=False)
    if result.returncode != 0 or result.stdout != path.read_bytes():
        raise CommandError(f"{label} bytes must equal the current commit")


def _commit_has_path(root: Path, commit: str, relative: str) -> bool:
    return _git(root, "cat-file", "-e", f"{commit}:{relative}", check=False).returncode == 0


def _freeze_tag_commit(root: Path) -> str:
    tag_ref = f"refs/tags/{FREEZE_TAG}"
    tag_type = _git(root, "cat-file", "-t", tag_ref, check=False)
    if tag_type.returncode != 0 or tag_type.stdout.strip() != b"tag":
        raise CommandError(f"required annotated freeze tag is missing: {FREEZE_TAG}")
    return _git(root, "rev-parse", f"{tag_ref}^{{commit}}").stdout.decode("ascii").strip()


def _require_seal_introduced(root: Path, commit: str) -> None:
    parent = _git(root, "rev-parse", f"{commit}^", check=False)
    if parent.returncode == 0 and _commit_has_path(root, parent.stdout.decode("ascii").strip(), OUTCOME_SEAL_REF):
        raise CommandError("outcome seal already existed before the freeze commit")
    status = _git(
        root, "diff-tree", "--root", "--no-commit-id", "--name-status", "--no-renames", "-r", commit, "--", OUTCOME_SEAL_REF
    ).stdout.decode("utf-8").splitlines()
    if status != [f"A\t{OUTCOME_SEAL_REF}"]:
        raise CommandError("freeze tag does not select the commit that added the outcome seal")


def _require_tag_lineage(root: Path) -> str:
    tagged = _freeze_tag_commit(root)
    _require_seal_introduced(root, tagged)
    head = _git_head(root)
    if _git(root, "merge-base", "--is-ancestor", tagged, head, check=False).returncode != 0:
        raise CommandError("freeze tag commit is not an ancestor of HEAD")
    return tagged


def _head_adds_only(root: Path, relative: str) -> None:
    changes = _git(root, "diff-tree", "--no-commit-id", "--name-status", "--no-renames", "-r", "HEAD").stdout
    if changes.decode("utf-8").splitlines() != [f"A\t{relative}"]:
        raise CommandError(f"HEAD must add only {relative}")


# ----------------------------------------------------------------------------
# Gates
# ----------------------------------------------------------------------------


def _verify_seal_committed(root: Path) -> dict[str, Any]:
    seal_path = repo_path(root, OUTCOME_SEAL_REF)
    if not seal_path.is_file():
        raise CommandError(f"outcome seal is missing: {OUTCOME_SEAL_REF}")
    seal = verify_outcome_seal(seal_path, root=root)
    _require_committed_bytes(root, OUTCOME_SEAL_REF, "outcome seal")
    for section in ("spec_files", "source_files", "test_files"):
        for relative in seal[section]:
            _require_committed_bytes(root, relative, relative)
    _require_committed_bytes(root, seal["contract"]["path"], "contract")
    return seal


def _base_gate(root: Path) -> str:
    """Seal committed and verified, tag on the seal commit, clean tree."""

    _verify_seal_committed(root)
    _require_tag_lineage(root)
    _require_clean_worktree(root)
    return _freeze_tag_commit(root)


def _load_committed_result(root: Path, relative: str, label: str) -> dict[str, Any]:
    _require_committed_bytes(root, relative, label)
    result = load_canonical_json(repo_path(root, relative))
    validate_result(result, root=root)
    return result


def _development_prerequisites(root: Path) -> dict[str, Any]:
    from .runner import calibration_gates_pass

    calibration = _load_committed_result(root, CALIBRATION_RESULT_REF, "calibration result")
    passed, failures = calibration_gates_pass(calibration)
    if not passed:
        raise CommandError("calibration gates failed: " + "; ".join(failures))
    _require_committed_bytes(root, STRUCTURAL_AUDIT_ANSWERS_REF, "Stage A answers")
    answers = load_canonical_json(repo_path(root, STRUCTURAL_AUDIT_ANSWERS_REF))
    if answers.get("all_checks_passed") is not True:
        raise CommandError("Stage A answers do not record every check passing")
    return answers


def gate_open(root: Path, stage: str) -> dict[str, Any]:
    """Every condition for writing the stage's open manifest."""

    tagged = _base_gate(root)
    info = STAGES[stage]
    for relative in (info["open_manifest"], info["result"]):
        if repo_path(root, relative).exists():
            raise CommandError(f"registered artifact already exists: {relative}")
    context: dict[str, Any] = {"preregistration_commit": tagged}
    if stage == "development":
        _development_prerequisites(root)
        context["calibration_result"] = binding(root, CALIBRATION_RESULT_REF)
        context["structural_audit_answers"] = binding(root, STRUCTURAL_AUDIT_ANSWERS_REF)
    if stage == "confirmation":
        _require_committed_bytes(root, DEVELOPMENT_OPEN_MANIFEST_REF, "development open manifest")
        development = _load_committed_result(root, DEVELOPMENT_RESULT_REF, "development result")
        context["development_result"] = binding(root, DEVELOPMENT_RESULT_REF)
        context["frozen_rho"] = frozen_confirmation_values(development)
    return context


def gate_run(root: Path, stage: str) -> dict[str, Any]:
    """Every condition for running a stage; returns the open manifest."""

    tagged = _base_gate(root)
    info = STAGES[stage]
    _require_committed_bytes(root, info["open_manifest"], f"{stage} open manifest")
    _head_adds_only(root, info["open_manifest"])
    manifest = load_canonical_json(repo_path(root, info["open_manifest"]))
    expected = {
        "search_id": SEARCH_ID,
        "protocol_version": PROTOCOL_VERSION,
        "stage": stage,
        "status": f"{stage}_open",
        "parent_outcome_seal": binding(root, OUTCOME_SEAL_REF),
        "result_schema": binding(root, RESULT_SCHEMA_REF),
        "result_path": info["result"],
        "freeze_tag": FREEZE_TAG,
        "preregistration_commit": tagged,
        "run_command_enabled": True,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise CommandError(f"{stage} open manifest {key} mismatch")
    if repo_path(root, info["result"]).exists():
        raise CommandError(f"refusing to overwrite registered result: {info['result']}")
    if stage == "development":
        _development_prerequisites(root)
        for key, relative in (
            ("calibration_result", CALIBRATION_RESULT_REF),
            ("structural_audit_answers", STRUCTURAL_AUDIT_ANSWERS_REF),
        ):
            if manifest.get(key) != binding(root, relative):
                raise CommandError(f"development open manifest {key} binding mismatch")
    if stage == "confirmation":
        if manifest.get("development_result") != binding(root, DEVELOPMENT_RESULT_REF):
            raise CommandError("confirmation open manifest development binding mismatch")
    return manifest


def frozen_confirmation_values(development: dict[str, Any]) -> dict[str, float]:
    """Lower endpoint, final point, and upper endpoint of the development run.

    The final bracket is reconstructed by replaying the registered bracketing
    rule over the recorded points (Q-K-2).
    """

    from .estimators import EvaluatedPoint, PointEvaluation, bracket_search

    model = development["models"][0]
    if model["terminal_status"] != "classified":
        raise CommandError("no confirmation: development terminal status is not 'classified'")
    recorded = [p for p in model["points"] if p["role"] in ("coarse", "bisection")]
    coarse = [p for p in recorded if p["role"] == "coarse"]
    queue = list(recorded)

    def lookup(control: float, role: str, index: int) -> EvaluatedPoint:
        point = queue.pop(0)
        if point["role"] != role or point["control_value"] != control:
            raise CommandError("development points do not replay the registered bracketing")
        evaluation = PointEvaluation(
            t_min=point["t_min"],
            t_max=point["t_max"],
            criticality=point["criticality"],
            slope_s=point["slope_s"],
            slope_ci95=point["slope_ci95"],
            ladder=point["ladder"],
            censored_run_fraction=point.get("censored_run_fraction", 0.0),
            runs=point["runs"],
        )
        return EvaluatedPoint(control, role, evaluation)

    from .runner import iota_plan

    plan = iota_plan()
    search = bracket_search(lookup, [p["control_value"] for p in coarse], len(recorded) - len(coarse), plan.midpoint_kind)
    if search.final_bracket is None or search.final_control != model["final_control_value"]:
        raise CommandError("development final point does not replay")
    lo, hi = search.final_bracket
    return {"lower": lo.control, "final": search.final_control, "upper": hi.control}


# ----------------------------------------------------------------------------
# Audit
# ----------------------------------------------------------------------------


def audit_outcome_free_design(root: Path | None = None) -> list[str]:
    """Outcome-free consistency checks between the spec and the package."""

    from . import estimators, l0_engine, l1

    root = repository_root() if root is None else root.resolve()
    specs = {name: load_spec_file(name, root) for name in SPEC_FILES}
    notes: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise CommandError(f"audit: {message}")

    for name, value in specs.items():
        require(value.get("search_id") == SEARCH_ID, f"{name} search_id")
        require(value.get("protocol_version") == PROTOCOL_VERSION, f"{name} protocol_version")
    protocol = specs["protocol.json"]
    require(protocol["registered_paths"] == REGISTERED_PATHS, "registered paths differ from protocol.json")
    require(protocol["required_freeze_tag"] == FREEZE_TAG, "freeze tag differs from protocol.json")
    require(protocol.get("freeze_revision") == FREEZE_REVISION, "freeze revision differs from protocol.json")
    superseded = protocol.get("superseded_freeze", {})
    require(
        superseded.get("freeze_tag") == SUPERSEDED_FREEZE_TAG and superseded.get("seal") == SUPERSEDED_SEAL_REF,
        "superseded freeze record differs from protocol.json",
    )

    law = specs["minimal_law.json"]["laws"]["L0"]
    require(law["constants"] == {"v": l0_engine.V, "a0": l0_engine.A0}, "L0 constants")
    require(law["lattice"]["shape"] == "64 x 64 x 64" and l0_engine.REGISTERED_L == 64, "L0 lattice")
    require(specs["minimal_law.json"]["laws"]["L1"]["constants"]["r"] == l1.REGISTERED_R, "L1 r")

    spreading = specs["iota_spreading.json"]
    require(spreading["lattice"]["seed_site"] == list(l0_engine.default_seed(64)), "seed site")
    require(spreading["constants"] == {"v": l0_engine.V, "a0": l0_engine.A0}, "spreading constants")
    require(
        spreading["resource_envelope"]["worker_processes"] == REGISTERED_WORKER_PROCESSES,
        "worker processes",
    )

    est = specs["estimators.json"]
    require(est["local_slopes"]["m"] == estimators.M, "local slope m")
    require(est["criticality_test"]["bootstrap"]["resamples"] == estimators.BOOTSTRAP_RESAMPLES, "bootstrap resamples")
    require(est["censoring"]["fit_window_lower"] == {"1p1": 32, "3d": 16}, "t_min")
    tolerances = est["classification"]["absolute_tolerances"]["3d"]
    refs = specs["reference_classes.json"]["classes"]
    for key, dp_key, dyp_key in (("delta", "delta", "delta"), ("theta_or_eta", "theta", "eta"), ("z", "z", "z")):
        separation = abs(refs["DP_3p1"]["exponents"][dp_key]["value"] - refs["DyP_3"]["exponents"][dyp_key]["value"])
        require(tolerances[key] < separation / 2, f"3D tolerance {key} not below half the class separation")
    for dim in ("1p1", "3d"):
        for class_id in est["classification"][f"registered_classes_{dim}"]:
            require(class_id in refs, f"registered class {class_id} has reference values")

    calibration = specs["calibration.json"]
    require(
        tuple(m["model_id"] for m in calibration["models"]) == calibration_models.MODEL_IDS,
        "calibration model ids",
    )
    for model in calibration["models"]:
        gate = model.get("threshold_gate")
        if gate is not None:
            value: Any = specs["reference_classes.json"]
            for part in gate["reference"].split("."):
                value = value[part]
            require(isinstance(value, float), f"{model['model_id']} threshold reference resolves")

    partitions = specs["partitions.json"]
    dev = partitions["iota_development"]["run_seed_range"]
    grid = spreading["control_grid"]
    require(max(grid["runs_per_coarse_point"], grid["runs_per_bisection_point"], grid["runs_at_final_point"]) <= 25000, "seed capacity")
    require(dev["first"] + 25000 * 16 + grid["runs_at_final_point"] - 1 <= dev["last"], "development seed range")
    conf = partitions["iota_confirmation"]
    require(conf["run_seed_range"]["first"] + 25000 * 2 + conf["runs_per_point"] - 1 <= conf["run_seed_range"]["last"], "confirmation seed range")
    require(dev["last"] < conf["run_seed_range"]["first"], "development and confirmation ranges overlap")

    import jsonschema

    schema = load_spec_file("result.schema.json", root)
    jsonschema.Draft202012Validator.check_schema(schema)

    for relative in ALL_PROTECTED_PATHS:
        if repo_path(root, relative).exists():
            notes.append(f"registered artifact present: {relative}")
    return notes


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------


def command_audit(_: argparse.Namespace) -> int:
    notes = audit_outcome_free_design()
    for note in notes:
        print(f"NOTE {note}")
    print(f"PASS {SEARCH_ID}: outcome-free spec and implementation consistency")
    return 0


def command_structural_audit(args: argparse.Namespace, root: Path | None = None) -> int:
    from .structural_audit import build_answers

    root = repository_root() if root is None else root.resolve()
    output = Path(args.output).resolve()
    for relative in ALL_PROTECTED_PATHS:
        if output == repo_path(root, relative):
            raise CommandError(f"structural-audit never writes a registered path: {relative}")
    experiments = repo_path(root, "experiments/dp_persistence")
    outputs = repo_path(root, "output/dp_persistence")
    for protected in (experiments, outputs):
        if output == protected or protected in output.parents:
            raise CommandError("structural-audit output must lie outside the registered directories")
    answers = build_answers(load_spec_file("structural_audit.json", root))
    write_canonical_json_once(output, answers)
    status = "PASS" if answers["all_checks_passed"] else "FAIL"
    print(f"{status} structural audit: wrote {output}")
    return 0 if answers["all_checks_passed"] else 1


def command_freeze_seal(_: argparse.Namespace) -> int:
    root = repository_root()
    audit_outcome_free_design(root)
    path = repo_path(root, OUTCOME_SEAL_REF)
    write_outcome_seal(root, path)
    print(f"WROTE {path}: status=outcomes_sealed run_command_enabled=false")
    return 0


def command_verify_seal(_: argparse.Namespace) -> int:
    root = repository_root()
    verify_outcome_seal(repo_path(root, OUTCOME_SEAL_REF), root=root)
    print(f"PASS {OUTCOME_SEAL_REF}: all outcome-free content hashes verified")
    return 0


def open_stage(stage: str, root: Path | None = None) -> Path:
    root = repository_root() if root is None else root.resolve()
    context = gate_open(root, stage)
    info = STAGES[stage]
    manifest = {
        "search_id": SEARCH_ID,
        "protocol_version": PROTOCOL_VERSION,
        "stage": stage,
        "status": f"{stage}_open",
        "parent_outcome_seal": binding(root, OUTCOME_SEAL_REF),
        "result_schema": binding(root, RESULT_SCHEMA_REF),
        "result_path": info["result"],
        "freeze_tag": FREEZE_TAG,
        "head_at_opening": _git_head(root),
        "run_command_enabled": True,
        **context,
    }
    path = repo_path(root, info["open_manifest"])
    write_canonical_json_once(path, manifest)
    return path


def run_stage(stage: str, root: Path | None = None) -> Path:
    root = repository_root() if root is None else root.resolve()
    manifest = gate_run(root, stage)
    info = STAGES[stage]
    seal_sha = binding(root, OUTCOME_SEAL_REF)["sha256"]
    parent = _git_head(root)

    # Runners are imported only after every gate has passed.
    from . import runner

    result: dict[str, Any] = {
        "search_id": SEARCH_ID,
        "protocol_version": PROTOCOL_VERSION,
        "result_kind": info["result_kind"],
        "seal_sha256": seal_sha,
        "parent_commit": parent,
    }
    if stage == "calibration":
        result["models"] = runner.run_calibration()
    else:
        answers = load_canonical_json(repo_path(root, STRUCTURAL_AUDIT_ANSWERS_REF))
        result["predicted_classes"] = dict(answers["predicted_classes"])
        if stage == "development":
            result["models"] = [runner.development_model_result()]
        else:
            development = load_canonical_json(repo_path(root, DEVELOPMENT_RESULT_REF))
            result["models"] = [
                runner.confirmation_model_result(manifest["frozen_rho"], development["models"][0])
            ]
    validate_result(result, root=root)

    # Re-verify every authority after the potentially long run.
    reverified = gate_run(root, stage)
    if canonical_json(reverified) != canonical_json(manifest) or _git_head(root) != parent:
        raise CommandError("authority changed during the run; nothing written")
    path = repo_path(root, info["result"])
    write_canonical_json_once(path, result)
    return path


def _open_command(stage: str):
    def command(_: argparse.Namespace) -> int:
        path = open_stage(stage)
        print(f"WROTE {path}: status={stage}_open; commit only this manifest before run-{stage}")
        return 0

    return command


def _run_command(stage: str):
    def command(_: argparse.Namespace) -> int:
        path = run_stage(stage)
        print(f"WROTE {path}: commit only this result as the direct child of its opening")
        return 0

    return command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Outcome-safe ICP-DP-PERSISTENCE-001 tooling.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    commands = [
        ("audit", command_audit, "outcome-free spec and implementation consistency checks"),
        ("freeze-seal", command_freeze_seal, "write the disabled content-hash seal"),
        ("verify-seal", command_verify_seal, "verify the outcome-free seal hashes"),
    ]
    for stage in STAGES:
        commands.append((f"open-{stage}", _open_command(stage), f"write the {stage} open manifest"))
        commands.append((f"run-{stage}", _run_command(stage), f"run {stage} from its committed opening"))
    for name, function, help_text in commands:
        command = subparsers.add_parser(name, help=help_text)
        command.set_defaults(func=function)
    audit = subparsers.add_parser("structural-audit", help="Stage A checks on synthetic states")
    audit.add_argument("--output", required=True, help="temporary path for the answers (never the registered path)")
    audit.set_defaults(func=command_structural_audit)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, KeyError, SealError, CommandError, LedgerError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
