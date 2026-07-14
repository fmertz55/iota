"""Outcome-safe command surface for MIR-ROLE-SUCCESSION-001."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .manifest import (
    canonical_json,
    compile_candidates,
    read_jsonl,
    sha256_file,
    validate_candidate_manifest,
    write_jsonl,
)
from .protocol import (
    BASE_CONTRACT_VERSION,
    CANDIDATE_COUNT,
    CANDIDATE_MANIFEST_REF,
    CANONICAL_ORIGIN,
    DATA_CLASS,
    DETECTOR_ID,
    DYNAMIC_CANDIDATE_COUNT,
    EMBEDDING_CYCLE_SIZES,
    FORMATION_HORIZON,
    FREEZE_TAG,
    GRAMMAR_ID,
    INPUT_PORTS,
    MAX_LAYERS_PER_CANDIDATE,
    OPEN_MANIFEST_REF,
    OUTCOME_SEAL_REF,
    PARENT_EXACT_RESULT_REF,
    PARENT_EXACT_RESULT_SHA256,
    PRIMARY_CONE_SATURATION_LAYER,
    PRIMARY_CYCLE_SIZE,
    PROTOCOL_VERSION,
    REGISTERED_WORKER_PROCESSES,
    RESULT_PATH_REF,
    RUN_ID,
    SEARCH_ID,
    SHELL_SIZES,
    SIGNATURE_ORDER,
)
from .seal import (
    CONTRACT_REF,
    LITERATURE_REF,
    OPENING_CONDITION,
    SPEC_DIR_REF,
    SealError,
    build_outcome_seal,
    load_canonical_json,
    repository_root,
    require_registered_path,
    verify_outcome_seal,
    write_canonical_json_once,
)


RESULT_SCHEMA_REF = f"{SPEC_DIR_REF}/result.schema.json"
OPENING_CONDITION_SATISFIED = (
    f"outcome-free seal first added at annotated {FREEZE_TAG}; open manifest is "
    "its direct child and sole change"
)


class CommandError(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CommandError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise CommandError(f"non-finite JSON number {value!r} is forbidden")


def _load_spec_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(
                handle,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
    except (OSError, json.JSONDecodeError) as exc:
        raise CommandError(f"{path}: {exc}") from exc
    if type(value) is not dict:
        raise CommandError(f"{path}: root must be an object")
    return value


def _repo_path(root: Path, relative: str) -> Path:
    return require_registered_path(root, root / relative, relative)


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
    output = _git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout
    if output:
        raise CommandError("worktree must be clean")


def _freeze_tag_commit(root: Path) -> str:
    """Return the commit selected by the required annotated freeze tag."""

    tag_ref = f"refs/tags/{FREEZE_TAG}"
    tag_type = _git(root, "cat-file", "-t", tag_ref, check=False)
    if tag_type.returncode != 0 or tag_type.stdout.strip() != b"tag":
        raise CommandError(f"required annotated freeze tag is missing: {FREEZE_TAG}")
    tagged_commit = _git(root, "rev-parse", f"{tag_ref}^{{commit}}")
    return tagged_commit.stdout.decode("ascii").strip()


def _require_freeze_tag_at_head(root: Path) -> str:
    """Require the annotated protocol-freeze tag to select current HEAD."""

    tagged = _freeze_tag_commit(root)
    head = _git_head(root)
    if tagged != head:
        raise CommandError(
            f"required freeze tag {FREEZE_TAG} does not select current HEAD"
        )
    _require_outcome_seal_introduced(root, tagged)
    return head


def _require_committed_bytes(root: Path, path: Path, label: str) -> None:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    result = _git(root, "show", f"HEAD:{relative}", check=False)
    if result.returncode != 0 or result.stdout != path.read_bytes():
        raise CommandError(f"{label} bytes must equal the current commit")


def _commit_parent(root: Path, commit: str) -> str:
    result = _git(root, "rev-parse", f"{commit}^")
    return result.stdout.decode("ascii").strip()


def _commit_changes(root: Path, commit: str) -> set[str]:
    result = _git(
        root,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        commit,
    )
    return set(result.stdout.decode("utf-8").splitlines())


def _commit_has_path(root: Path, commit: str, relative: str) -> bool:
    result = _git(root, "cat-file", "-e", f"{commit}:{relative}", check=False)
    return result.returncode == 0


def _require_outcome_seal_introduced(root: Path, commit: str) -> None:
    """Anchor preregistration to the commit that first adds the disabled seal."""

    parent = _commit_parent(root, commit)
    if _commit_has_path(root, parent, OUTCOME_SEAL_REF):
        raise CommandError("outcome seal already existed before the freeze commit")
    status = _git(
        root,
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "--no-renames",
        "-r",
        commit,
        "--",
        OUTCOME_SEAL_REF,
    ).stdout.decode("utf-8").splitlines()
    if status != [f"A\t{OUTCOME_SEAL_REF}"]:
        raise CommandError("freeze tag does not select the commit that added the outcome seal")
    if not _commit_has_path(root, commit, OUTCOME_SEAL_REF):
        raise CommandError("outcome seal is absent from the freeze commit")


def _binding(root: Path, relative: str) -> dict[str, str]:
    path = _repo_path(root, relative)
    if not path.is_file():
        raise CommandError(f"registered file is missing: {relative}")
    return {"path": relative, "sha256": sha256_file(path)}


def _require_binding(value: Any, label: str) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"path", "sha256"}:
        raise CommandError(f"{label} binding shape mismatch")
    if type(value["path"]) is not str or not value["path"]:
        raise CommandError(f"{label} path is invalid")
    digest = value["sha256"]
    if (
        type(digest) is not str
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise CommandError(f"{label} digest is invalid")
    return value


def _audit_machine_spec(root: Path) -> None:
    protocol = _load_spec_json(_repo_path(root, f"{SPEC_DIR_REF}/protocol.json"))
    fixed_protocol = {
        "protocol_version": PROTOCOL_VERSION,
        "base_contract_version": BASE_CONTRACT_VERSION,
        "search_id": SEARCH_ID,
        "normalized_n_p": 2,
        "candidate_count": CANDIDATE_COUNT,
        "dynamic_candidate_count": DYNAMIC_CANDIDATE_COUNT,
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "canonical_origin": CANONICAL_ORIGIN,
        "pre_wrap_formation_horizon": FORMATION_HORIZON,
        "cone_saturation_layer": PRIMARY_CONE_SATURATION_LAYER,
        "max_layers_per_dynamic_candidate": MAX_LAYERS_PER_CANDIDATE,
        "registered_worker_processes": REGISTERED_WORKER_PROCESSES,
        "parallel_execution_rule": (
            "candidate-level spawn workers only; collect all 255 dynamic results "
            "in canonical manifest order before ledger construction; no partial "
            "result artifact"
        ),
        "terminal_check_order": [
            "evaluate complete detector and award any same-layer pass",
            "test exact post-saturation recurrence",
            "classify resource ceiling if neither earlier terminal applies",
        ],
        "trace_and_state_encoding": {
            "locus_bit_mapping": (
                "event at locus i is unsigned-state bit i; locus 0 is the "
                "least-significant bit"
            ),
            "state_hex_primary": (
                "unsigned C64 state as exactly 16 lowercase hexadecimal digits, "
                "most-significant digit first"
            ),
            "trace_hash": "SHA-256",
            "trace_prefix_ascii_plus_nul": (
                "ASCII IOTA-MIR-ROLE-SUCCESSION-TRACE-V1 followed by byte 0x00"
            ),
            "candidate_domain": (
                "ASCII search_id + NUL + candidate_id + NUL + SHA-256(canonical "
                "candidate JSON without LF)"
            ),
            "canonical_candidate_json": (
                "keys sorted; separators comma and colon without spaces; ASCII "
                "escapes; finite JSON only"
            ),
            "length_encoding": "unsigned 8-byte big-endian",
            "layer_encoding": (
                "nonnegative decimal ASCII preceded by its 8-byte big-endian byte length"
            ),
            "state_byte_encoding": "unsigned big-endian in exactly ceil(N/8) bytes",
            "digest_sequence": (
                "prefix; domain byte length; domain; then for every natural joint "
                "state from layer 0 through terminal: layer byte length, layer bytes, "
                "seeded bytes, comparator bytes"
            ),
            "excluded_from_trace": (
                "intervention arms and conditional larger-ring controls"
            ),
        },
        "cross_size_controls": list(EMBEDDING_CYCLE_SIZES),
        "run_command_enabled": False,
        "registered_result_path": RESULT_PATH_REF,
        "registered_open_manifest_path": OPEN_MANIFEST_REF,
        "required_freeze_tag": FREEZE_TAG,
    }
    for key, expected in fixed_protocol.items():
        if protocol.get(key) != expected:
            raise CommandError(f"protocol.json {key} mismatch")

    grammar = _load_spec_json(_repo_path(root, f"{SPEC_DIR_REF}/grammar.json"))
    if (
        grammar.get("grammar_id") != GRAMMAR_ID
        or grammar.get("input_order") != list(INPUT_PORTS)
        or grammar.get("signature_order") != list(SIGNATURE_ORDER)
        or grammar.get("candidate_space", {}).get("candidate_count") != CANDIDATE_COUNT
        or list(grammar.get("candidate_space", {}).get("shell_sizes_by_n_l", {}).values())
        != list(SHELL_SIZES)
    ):
        raise CommandError("grammar.json differs from executable grammar")

    detector = _load_spec_json(_repo_path(root, f"{SPEC_DIR_REF}/detector.json"))
    expected_cone_eligibility = {
        "formation": (
            "active role loci a and a+1 are both in the centered cone at layer t"
        ),
        "successor": (
            "both active loci at the selected successor anchor are in the "
            "centered cone at layer t+1"
        ),
        "intervention_endpoint": "locus a+3 is in the centered cone at layer t+2",
        "isolation_zero_loci_excluded": [-1, 2],
    }
    if (
        detector.get("detector_id") != DETECTOR_ID
        or detector.get("succession", {}).get("eligible_anchor_offsets") != [0, 1]
        or detector.get("cone_eligibility") != expected_cone_eligibility
        or detector.get("pre_wrap", {}).get("maximum_formation_layer")
        != FORMATION_HORIZON
        or detector.get("pre_wrap", {}).get(
            "all_dynamic_candidates_must_receive_classification"
        )
        is not True
        or "all_candidates_must_receive_classification"
        in detector.get("pre_wrap", {})
        or detector.get("pre_wrap", {}).get("zero_row_classification", "missing")
        is not None
    ):
        raise CommandError("detector.json differs from executable detector")

    topology = _load_spec_json(_repo_path(root, f"{SPEC_DIR_REF}/topology.json"))
    expected_signed_offset = {
        "forward_residue": "d = (anchor - origin) mod N in 0 through N-1",
        "mapping": "d if d <= floor(N/2), otherwise d-N",
        "even_antipode": "positive +N/2",
        "registered_ranges": {
            "64": [-31, 32],
            "96": [-47, 48],
            "128": [-63, 64],
        },
    }
    if (
        topology.get("primary_cycle_size") != PRIMARY_CYCLE_SIZE
        or topology.get("centered_cone", {}).get("saturation_layer_primary")
        != PRIMARY_CONE_SATURATION_LAYER
        or topology.get("centered_cone", {}).get("signed_offset")
        != expected_signed_offset
        or topology.get("resource_envelope", {}).get(
            "relation_incidence_reads_per_site_tick"
        )
        != 2
        or topology.get("resource_envelope", {}).get(
            "registered_candidate_worker_processes"
        )
        != REGISTERED_WORKER_PROCESSES
        or topology.get("resource_envelope", {}).get("result_collection_order")
        != "canonical candidate manifest order"
        or topology.get("resource_envelope", {}).get("partial_result_artifacts")
        != 0
    ):
        raise CommandError("topology.json differs from executable topology")

    partitions = _load_spec_json(_repo_path(root, f"{SPEC_DIR_REF}/partitions.json"))
    if (
        partitions.get("primary", {}).get("dynamic_candidate_count")
        != DYNAMIC_CANDIDATE_COUNT
        or partitions.get("conditional_size_controls", {}).get("cycle_sizes")
        != list(EMBEDDING_CYCLE_SIZES)
        or partitions.get("conditional_size_controls", {}).get(
            "signed_anchor_encoding"
        )
        != {
            "forward_residue": "d = (anchor - origin) mod N",
            "mapping": "d if d <= floor(N/2), otherwise d-N",
            "even_antipode": "positive +N/2",
            "ranges_by_cycle_size": {
                "64": [-31, 32],
                "96": [-47, 48],
                "128": [-63, 64],
            },
        }
    ):
        raise CommandError("partitions.json differs from executable allocation")

    result_schema = _load_spec_json(_repo_path(root, RESULT_SCHEMA_REF))
    schema_properties = result_schema.get("properties")
    schema_required = result_schema.get("required")
    if (
        result_schema.get("$schema")
        != "https://json-schema.org/draft/2020-12/schema"
        or result_schema.get("type") != "object"
        or result_schema.get("additionalProperties") is not False
        or type(schema_properties) is not dict
        or type(schema_required) is not list
        or set(schema_required) != set(schema_properties)
    ):
        raise CommandError("result.schema.json root is not a closed complete object")
    schema_constants = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": RUN_ID,
        "grammar_id": GRAMMAR_ID,
        "detector": DETECTOR_ID,
        "data_class": DATA_CLASS,
        "endpoint": "first_complete_proto_object_or_exact_post_saturation_recurrence",
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "embedding_cycle_sizes": list(EMBEDDING_CYCLE_SIZES),
        "formation_horizon": FORMATION_HORIZON,
        "cone_saturation_layer": PRIMARY_CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
    }
    for key, expected in schema_constants.items():
        if schema_properties.get(key, {}).get("const") != expected:
            raise CommandError(f"result.schema.json {key} const mismatch")
    if schema_properties.get("parent_exact_result") != {
        "const": {
            "path": PARENT_EXACT_RESULT_REF,
            "sha256": PARENT_EXACT_RESULT_SHA256,
        }
    }:
        raise CommandError("result.schema.json parent exact-result binding mismatch")
    candidate_results = schema_properties.get("candidate_results", {})
    if (
        candidate_results.get("minItems") != CANDIDATE_COUNT
        or candidate_results.get("maxItems") != CANDIDATE_COUNT
        or candidate_results.get("items") != {"$ref": "#/$defs/candidate_result"}
    ):
        raise CommandError("result.schema.json candidate allocation mismatch")

    for relative in (CONTRACT_REF, LITERATURE_REF, RESULT_SCHEMA_REF):
        if not _repo_path(root, relative).is_file():
            raise CommandError(f"required outcome-free artifact is missing: {relative}")


def audit_outcome_free_design(root: Path | None = None) -> None:
    root = repository_root() if root is None else root.resolve()
    _audit_machine_spec(root)
    candidates = compile_candidates()
    if len(candidates) != CANDIDATE_COUNT:
        raise CommandError("candidate compiler did not produce 256 candidates")
    validate_candidate_manifest(candidates)


def command_audit(_: argparse.Namespace) -> int:
    audit_outcome_free_design()
    print(
        f"PASS {SEARCH_ID}: outcome-free design candidates={CANDIDATE_COUNT} "
        f"H_pre={FORMATION_HORIZON} cap={MAX_LAYERS_PER_CANDIDATE} "
        f"workers={REGISTERED_WORKER_PROCESSES}"
    )
    return 0


def command_compile_candidates(_: argparse.Namespace) -> int:
    root = repository_root()
    audit_outcome_free_design(root)
    path = _repo_path(root, CANDIDATE_MANIFEST_REF)
    if _repo_path(root, OUTCOME_SEAL_REF).exists() or _repo_path(root, OPEN_MANIFEST_REF).exists():
        raise CommandError("cannot compile candidates after sealing or opening")
    write_jsonl(path, compile_candidates())
    print(f"WROTE {path}: records={CANDIDATE_COUNT} sha256={sha256_file(path)}")
    return 0


def command_freeze_seal(_: argparse.Namespace) -> int:
    root = repository_root()
    audit_outcome_free_design(root)
    seal = build_outcome_seal(root)
    path = _repo_path(root, OUTCOME_SEAL_REF)
    write_canonical_json_once(path, seal)
    print(f"WROTE {path}: status=outcomes_sealed sha256={sha256_file(path)}")
    return 0


def _verify_seal_committed(root: Path, path: Path) -> dict[str, Any]:
    seal = verify_outcome_seal(path, root=root)
    _require_committed_bytes(root, path, "outcome seal")
    for name in ("parent_exact_result", "candidate_manifest", "contract", "literature_record"):
        binding = _require_binding(seal[name], name)
        bound_path = _repo_path(root, binding["path"])
        _require_committed_bytes(root, bound_path, name)
    for section in ("spec_files", "source_files", "test_files"):
        for relative in seal[section]:
            _require_committed_bytes(root, _repo_path(root, relative), relative)
    return seal


def command_verify_seal(_: argparse.Namespace) -> int:
    root = repository_root()
    verify_outcome_seal(_repo_path(root, OUTCOME_SEAL_REF), root=root)
    print(f"PASS {OUTCOME_SEAL_REF}: all outcome-free content hashes verified")
    return 0


def command_open(_: argparse.Namespace) -> int:
    root = repository_root()
    seal_path = _repo_path(root, OUTCOME_SEAL_REF)
    seal = _verify_seal_committed(root, seal_path)
    _require_clean_worktree(root)
    preregistration_commit = _require_freeze_tag_at_head(root)
    open_path = _repo_path(root, OPEN_MANIFEST_REF)
    if open_path.exists() or _repo_path(root, RESULT_PATH_REF).exists():
        raise CommandError("registered open manifest or result already exists")
    manifest = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": RUN_ID,
        "status": "development_open",
        "data_class": DATA_CLASS,
        "parent_outcome_seal": _binding(root, OUTCOME_SEAL_REF),
        "candidate_manifest": dict(seal["candidate_manifest"]),
        "parent_exact_result": dict(seal["parent_exact_result"]),
        "result_schema": _binding(root, RESULT_SCHEMA_REF),
        "result_path": RESULT_PATH_REF,
        "freeze_tag": FREEZE_TAG,
        "preregistration_commit": preregistration_commit,
        "run_command_enabled": True,
        "canonical_origin": CANONICAL_ORIGIN,
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "pre_wrap_formation_horizon": FORMATION_HORIZON,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "registered_worker_processes": REGISTERED_WORKER_PROCESSES,
        "conditional_cycle_sizes": list(EMBEDDING_CYCLE_SIZES),
        "opening_condition_satisfied": OPENING_CONDITION_SATISFIED,
    }
    write_canonical_json_once(open_path, manifest)
    print(
        f"WROTE {open_path}: status=development_open; commit only this manifest "
        "before run-development"
    )
    return 0


def load_open_manifest(
    path: Path,
    *,
    root: Path | None = None,
    require_committed: bool,
) -> dict[str, Any]:
    root = repository_root() if root is None else root.resolve()
    path = require_registered_path(root, path, OPEN_MANIFEST_REF)
    manifest = load_canonical_json(path)
    expected_keys = {
        "base_contract_version",
        "protocol_version",
        "search_id",
        "run_id",
        "status",
        "data_class",
        "parent_outcome_seal",
        "candidate_manifest",
        "parent_exact_result",
        "result_schema",
        "result_path",
        "freeze_tag",
        "preregistration_commit",
        "run_command_enabled",
        "canonical_origin",
        "primary_cycle_size",
        "pre_wrap_formation_horizon",
        "max_layers_per_candidate",
        "registered_worker_processes",
        "conditional_cycle_sizes",
        "opening_condition_satisfied",
    }
    if set(manifest) != expected_keys:
        raise CommandError("open manifest has missing or unexpected fields")
    fixed = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": RUN_ID,
        "status": "development_open",
        "data_class": DATA_CLASS,
        "result_path": RESULT_PATH_REF,
        "freeze_tag": FREEZE_TAG,
        "run_command_enabled": True,
        "canonical_origin": CANONICAL_ORIGIN,
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "pre_wrap_formation_horizon": FORMATION_HORIZON,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "registered_worker_processes": REGISTERED_WORKER_PROCESSES,
        "conditional_cycle_sizes": list(EMBEDDING_CYCLE_SIZES),
        "opening_condition_satisfied": OPENING_CONDITION_SATISFIED,
    }
    for key, expected in fixed.items():
        if manifest[key] != expected:
            raise CommandError(f"open manifest {key} mismatch")
    bindings = {
        "parent_outcome_seal": OUTCOME_SEAL_REF,
        "candidate_manifest": CANDIDATE_MANIFEST_REF,
        "parent_exact_result": PARENT_EXACT_RESULT_REF,
        "result_schema": RESULT_SCHEMA_REF,
    }
    for name, relative in bindings.items():
        binding = _require_binding(manifest[name], name)
        if binding["path"] != relative or binding != _binding(root, relative):
            raise CommandError(f"open manifest {name} binding mismatch")
    verify_outcome_seal(_repo_path(root, OUTCOME_SEAL_REF), root=root)

    preregistration = manifest["preregistration_commit"]
    if (
        type(preregistration) is not str
        or len(preregistration) != 40
        or any(character not in "0123456789abcdef" for character in preregistration)
    ):
        raise CommandError("open manifest preregistration commit is invalid")
    if require_committed:
        _require_clean_worktree(root)
        _require_committed_bytes(root, path, "open manifest")
        head = _git_head(root)
        tagged = _freeze_tag_commit(root)
        if tagged != preregistration:
            raise CommandError("open manifest preregistration is not the freeze tag commit")
        _require_outcome_seal_introduced(root, tagged)
        if _commit_parent(root, head) != preregistration:
            raise CommandError("open manifest commit is not a direct child of preregistration")
        if _commit_has_path(root, preregistration, OPEN_MANIFEST_REF):
            raise CommandError("open manifest already existed in the freeze commit")
        if _commit_changes(root, head) != {OPEN_MANIFEST_REF}:
            raise CommandError("opening commit contains changes besides the open manifest")
        _verify_seal_committed(root, _repo_path(root, OUTCOME_SEAL_REF))
    return manifest


def _verify_result_commit_provenance(
    root: Path,
    manifest: dict[str, Any],
) -> None:
    """Require the frozen freeze -> opening -> result-only commit chain."""

    _require_clean_worktree(root)
    result_path = _repo_path(root, RESULT_PATH_REF)
    open_path = _repo_path(root, OPEN_MANIFEST_REF)
    _require_committed_bytes(root, result_path, "result ledger")
    _require_committed_bytes(root, open_path, "open manifest")

    result_commit = _git_head(root)
    opening_commit = _commit_parent(root, result_commit)
    preregistration = manifest["preregistration_commit"]
    if _commit_changes(root, result_commit) != {RESULT_PATH_REF}:
        raise CommandError("result commit contains changes besides the result ledger")
    if _commit_has_path(root, opening_commit, RESULT_PATH_REF):
        raise CommandError("registered result already existed in the opening commit")
    if _commit_has_path(root, preregistration, OPEN_MANIFEST_REF):
        raise CommandError("open manifest already existed in the freeze commit")
    if _commit_changes(root, opening_commit) != {OPEN_MANIFEST_REF}:
        raise CommandError("opening commit contains changes besides the open manifest")
    if _commit_parent(root, opening_commit) != preregistration:
        raise CommandError("result is not the direct child of the committed opening")
    tagged = _freeze_tag_commit(root)
    if tagged != preregistration:
        raise CommandError("result lineage does not descend from the freeze tag commit")
    _require_outcome_seal_introduced(root, tagged)
    _verify_seal_committed(root, _repo_path(root, OUTCOME_SEAL_REF))


def command_run(_: argparse.Namespace) -> int:
    """Authorized entry point; outcome-free tests exercise only pre-write failure."""

    root = repository_root()
    open_path = _repo_path(root, OPEN_MANIFEST_REF)
    open_manifest = load_open_manifest(open_path, root=root, require_committed=True)
    result_path = _repo_path(root, RESULT_PATH_REF)
    if result_path.exists():
        raise CommandError(f"refusing to overwrite registered result: {result_path}")
    candidates = read_jsonl(_repo_path(root, CANDIDATE_MANIFEST_REF))
    validate_candidate_manifest(candidates)

    # Importing the evaluator happens only after the committed open-manifest gate.
    from .runner import (
        build_result_ledger,
        evaluate_candidate_exact_orbit,
        validate_result_ledger,
        write_result_ledger,
    )

    ledger = build_result_ledger(
        candidates=candidates,
        evaluator=evaluate_candidate_exact_orbit,
        open_manifest_binding=_binding(root, OPEN_MANIFEST_REF),
        outcome_seal_binding=dict(open_manifest["parent_outcome_seal"]),
        candidate_manifest_binding=dict(open_manifest["candidate_manifest"]),
        result_schema_binding=dict(open_manifest["result_schema"]),
        parent_exact_result_binding=dict(open_manifest["parent_exact_result"]),
        worker_processes=REGISTERED_WORKER_PROCESSES,
    )
    validate_result_ledger(ledger, candidates)

    # Revalidate every authority and binding after the potentially long run.
    reverified = load_open_manifest(open_path, root=root, require_committed=True)
    if canonical_json(reverified) != canonical_json(open_manifest):
        raise CommandError("open manifest changed during production evaluation")
    if result_path.exists():
        raise CommandError("registered result appeared during production evaluation")
    write_result_ledger(
        result_path,
        ledger,
        open_manifest_verified=True,
    )
    print(
        f"WROTE {result_path}: sha256={sha256_file(result_path)} "
        f"data_class={DATA_CLASS}; commit only this result as the direct child "
        "of opening, then run verify-results"
    )
    return 0


def command_verify_results(_: argparse.Namespace) -> int:
    root = repository_root()
    open_manifest = load_open_manifest(
        _repo_path(root, OPEN_MANIFEST_REF),
        root=root,
        require_committed=False,
    )
    _verify_result_commit_provenance(root, open_manifest)
    candidates = read_jsonl(_repo_path(root, CANDIDATE_MANIFEST_REF))
    validate_candidate_manifest(candidates)
    ledger = load_canonical_json(_repo_path(root, RESULT_PATH_REF))
    from .runner import validate_result_ledger
    from .verifier import verify_ledger_independently

    validate_result_ledger(ledger, candidates)
    verify_ledger_independently(
        ledger,
        candidates,
        worker_processes=REGISTERED_WORKER_PROCESSES,
    )
    expected = {
        "open_manifest": _binding(root, OPEN_MANIFEST_REF),
        "outcome_seal": dict(open_manifest["parent_outcome_seal"]),
        "candidate_manifest": dict(open_manifest["candidate_manifest"]),
        "result_schema": dict(open_manifest["result_schema"]),
        "parent_exact_result": dict(open_manifest["parent_exact_result"]),
    }
    for key, binding in expected.items():
        if ledger.get(key) != binding:
            raise CommandError(f"verified result {key} binding mismatch")
    print(f"PASS {RESULT_PATH_REF}: independent replay and ledger checks passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Outcome-safe MIR endogenous role-succession tooling."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    commands = (
        ("audit", command_audit, "audit outcome-free design constants"),
        ("compile-candidates", command_compile_candidates, "write canonical candidates"),
        ("freeze-seal", command_freeze_seal, "write disabled outcome seal"),
        ("verify-seal", command_verify_seal, "verify outcome-free seal hashes"),
        ("open-development", command_open, "write the no-outcome open manifest"),
        ("run-development", command_run, "run only from committed opening commit"),
        ("verify-results", command_verify_results, "independently verify result ledger"),
    )
    for name, function, help_text in commands:
        command = subparsers.add_parser(name, help=help_text)
        command.set_defaults(func=function)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, KeyError, SealError, CommandError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
