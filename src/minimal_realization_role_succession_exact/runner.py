"""Registered symbolic-first exact closure runner.

No registered work occurs at import.  The public evaluator first applies a
finite local all-state proof.  Only a rule with at least one logically possible
complete-pass context is replayed through the parent boundary and continued
without a resource ceiling.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from src.minimal_realization_role_succession.detector import LayerAssessment, assess_layer
from src.minimal_realization_role_succession.dynamics import canonical_initial_state, step
from src.minimal_realization_role_succession.manifest import (
    candidate_sha256,
    read_jsonl as read_parent_candidates,
)
from src.minimal_realization_role_succession.runner import strict_json_equal

from .manifest import (
    continuation_record_sha256,
    load_and_validate_parent,
    validate_continuation_manifest,
)
from .protocol import (
    CANONICAL_ORIGIN,
    CONE_SATURATION_LAYER,
    DATA_CLASS,
    EMBEDDING_CYCLE_SIZES,
    PARENT_RECURRENCE_EXCLUDED_COUNT,
    PARENT_RESOURCE_BOUNDARY,
    PARENT_RESOURCE_CENSORED_COUNT,
    PARENT_RESULT_REF,
    PARENT_RESULT_SHA256,
    PARENT_SEARCH_ID,
    PRIMARY_CYCLE_SIZE,
    PROTOCOL_VERSION,
    REGISTERED_WORKER_PROCESSES,
    RUN_ID,
    SEARCH_ID,
)
from .local_impossibility import (
    LocalImpossibilityCertificate,
    analyze_local_impossibility,
)


TRACE_PREFIX = b"IOTA-MIR-ROLE-SUCCESSION-TRACE-V1\x00"


class ExactClosureError(ValueError):
    pass


Analyzer = Callable[[tuple[str, ...]], LocalImpossibilityCertificate]
DynamicEvaluator = Callable[
    [dict[str, Any], dict[str, Any], dict[str, Any]],
    dict[str, Any],
]


def _digest_ok(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _new_trace_digest(candidate: dict[str, Any]) -> "hashlib._Hash":
    identifier = candidate.get("candidate_id")
    if type(identifier) is not str or not identifier:
        raise ExactClosureError("parent candidate id is invalid")
    domain = (
        f"{PARENT_SEARCH_ID}\0{identifier}\0{candidate_sha256(candidate)}"
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(TRACE_PREFIX)
    digest.update(len(domain).to_bytes(8, "big"))
    digest.update(domain)
    return digest


def _update_trace(
    digest: "hashlib._Hash",
    layer: int,
    seeded: int,
    comparator: int,
    cycle_size: int = PRIMARY_CYCLE_SIZE,
) -> None:
    width = (cycle_size + 7) // 8
    if (
        type(layer) is not int
        or layer < 0
        or type(seeded) is not int
        or type(comparator) is not int
        or not 0 <= seeded < 1 << cycle_size
        or not 0 <= comparator < 1 << cycle_size
    ):
        raise ExactClosureError("trace input is outside its frozen encoding")
    layer_bytes = str(layer).encode("ascii")
    digest.update(len(layer_bytes).to_bytes(8, "big"))
    digest.update(layer_bytes)
    digest.update(seeded.to_bytes(width, "big"))
    digest.update(comparator.to_bytes(width, "big"))


def _state_hex(state: int, cycle_size: int) -> str:
    return f"{state:0{(cycle_size + 3) // 4}x}"


def _signed_anchor(anchor: int, cycle_size: int) -> int:
    residue = (anchor - CANONICAL_ORIGIN) % cycle_size
    return residue if residue <= cycle_size // 2 else residue - cycle_size


def _role_record(value: Optional[tuple[int, int]]) -> Optional[dict[str, int]]:
    if value is None:
        return None
    return {"layer": value[0], "anchor": value[1]}


def _successor_record(
    value: Optional[tuple[int, int, int]],
) -> Optional[dict[str, int]]:
    if value is None:
        return None
    return {"layer": value[0], "anchor": value[1], "successor_anchor": value[2]}


def _pass_record(
    layer: int,
    assessment: LayerAssessment,
    seeded: int,
    comparator: int,
) -> dict[str, Any]:
    result = assessment.detector_result
    if not result.passed:
        raise ExactClosureError("cannot encode a nonpassing detector assessment")
    anchor = int(result.anchor)
    successor = int(result.successor_anchor)
    return {
        "layer": layer,
        "anchor": anchor,
        "signed_anchor": _signed_anchor(anchor, PRIMARY_CYCLE_SIZE),
        "successor_anchor": successor,
        "successor_displacement": (successor - anchor) % PRIMARY_CYCLE_SIZE,
        "sham_future": int(result.sham_future),
        "breaking_future": int(result.breaking_future),
        "seeded_state_hex": _state_hex(seeded, PRIMARY_CYCLE_SIZE),
        "baseline_state_hex": _state_hex(comparator, PRIMARY_CYCLE_SIZE),
    }


def _capture_stages(
    assessment: LayerAssessment,
    layer: int,
    first_role: Optional[tuple[int, int]],
    first_successor: Optional[tuple[int, int, int]],
    first_eligible: Optional[tuple[int, int, int]],
) -> tuple[
    Optional[tuple[int, int]],
    Optional[tuple[int, int, int]],
    Optional[tuple[int, int, int]],
]:
    if first_role is None and assessment.first_role_anchor is not None:
        first_role = (layer, assessment.first_role_anchor)
    if first_successor is None and assessment.first_successor is not None:
        first_successor = (layer, *assessment.first_successor)
    if first_eligible is None and assessment.first_intervention_eligible is not None:
        first_eligible = (layer, *assessment.first_intervention_eligible)
    return first_role, first_successor, first_eligible


def _compact_pass(record: dict[str, Any]) -> dict[str, int]:
    return {
        "layer": record["layer"],
        "signed_anchor": record["signed_anchor"],
        "successor_displacement": record["successor_displacement"],
        "sham_future": record["sham_future"],
        "breaking_future": record["breaking_future"],
    }


def _size_controls(rows: tuple[str, ...], primary: dict[str, Any]) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    target_layer = primary["layer"]
    primary_compact = _compact_pass(primary)
    for cycle_size in EMBEDDING_CYCLE_SIZES:
        seeded = canonical_initial_state(CANONICAL_ORIGIN, cycle_size)
        comparator = 0
        first: Optional[dict[str, int]] = None
        for layer in range(1, target_layer + 1):
            seeded = step(seeded, rows, cycle_size)
            comparator = step(comparator, rows, cycle_size)
            result = assess_layer(
                seeded,
                comparator,
                rows,
                layer=layer,
                origin=CANONICAL_ORIGIN,
                cycle_size=cycle_size,
            ).detector_result
            if result.passed and first is None:
                anchor = int(result.anchor)
                successor = int(result.successor_anchor)
                first = {
                    "layer": layer,
                    "signed_anchor": _signed_anchor(anchor, cycle_size),
                    "successor_displacement": (successor - anchor) % cycle_size,
                    "sham_future": int(result.sham_future),
                    "breaking_future": int(result.breaking_future),
                }
        controls.append(
            {
                "cycle_size": cycle_size,
                "evaluated_through_layer": target_layer,
                "first_complete_pass": first,
                "matches_primary_witness": first == primary_compact,
                "pre_wrap_agreement_required": False,
                "exact_pre_wrap_agreement": None,
            }
        )
    return controls


def _require_parent_prefix(
    continuation: dict[str, Any],
    parent_record: dict[str, Any],
    digest: "hashlib._Hash",
    first_role: Optional[tuple[int, int]],
    first_successor: Optional[tuple[int, int, int]],
    first_eligible: Optional[tuple[int, int, int]],
) -> None:
    actual = {
        "first_role": _role_record(first_role),
        "first_successor": _successor_record(first_successor),
        "first_intervention_eligible": _successor_record(first_eligible),
        "first_complete_pass": None,
        "trace_sha256": digest.copy().hexdigest(),
        "last_assessed_layer": PARENT_RESOURCE_BOUNDARY,
        "evaluation_status": "resource_censored_before_recurrence",
        "recurrence": None,
        "resource_limit": PARENT_RESOURCE_BOUNDARY,
    }
    for key, value in actual.items():
        if not strict_json_equal(parent_record.get(key), value):
            raise ExactClosureError(f"parent prefix replay differs at {key}")
    if continuation.get("parent_prefix_trace_sha256") != actual["trace_sha256"]:
        raise ExactClosureError("continuation manifest prefix digest mismatch")


def evaluate_uncapped_continuation(
    continuation: dict[str, Any],
    parent_record: dict[str, Any],
    parent_candidate: dict[str, Any],
) -> dict[str, Any]:
    """Replay the prefix, then continue until pass or exact recurrence.

    There is deliberately no layer/resource parameter.  An interrupted process
    emits no scientific record and must be rerun.
    """

    if continuation.get("candidate_id") != parent_record.get("candidate_id"):
        raise ExactClosureError("continuation and parent candidate ids differ")
    if continuation.get("candidate_sha256") != candidate_sha256(parent_candidate):
        raise ExactClosureError("parent candidate hash differs from continuation")
    if continuation_record_sha256(parent_record) != continuation.get(
        "parent_record_sha256"
    ):
        raise ExactClosureError("parent result record hash differs from continuation")
    rows = tuple(continuation.get("production_rows", ()))
    if not rows:
        raise ExactClosureError("continuation production rows are invalid")

    seeded = canonical_initial_state(CANONICAL_ORIGIN, PRIMARY_CYCLE_SIZE)
    comparator = 0
    digest = _new_trace_digest(parent_candidate)
    _update_trace(digest, 0, seeded, comparator)
    checkpoint: Optional[tuple[int, int]] = None
    checkpoint_layer: Optional[int] = None
    checkpoint_power = 1
    checkpoint_distance = 0
    first_role: Optional[tuple[int, int]] = None
    first_successor: Optional[tuple[int, int, int]] = None
    first_eligible: Optional[tuple[int, int, int]] = None
    boundary_state: Optional[tuple[int, int]] = None
    boundary_prefix: Optional[dict[str, Any]] = None

    layer = 0
    while True:
        layer += 1
        seeded = step(seeded, rows, PRIMARY_CYCLE_SIZE)
        comparator = step(comparator, rows, PRIMARY_CYCLE_SIZE)
        current = (seeded, comparator)
        _update_trace(digest, layer, seeded, comparator)
        assessment = assess_layer(
            seeded,
            comparator,
            rows,
            layer=layer,
            origin=CANONICAL_ORIGIN,
            cycle_size=PRIMARY_CYCLE_SIZE,
        )
        first_role, first_successor, first_eligible = _capture_stages(
            assessment,
            layer,
            first_role,
            first_successor,
            first_eligible,
        )
        if assessment.detector_result.passed:
            if layer <= PARENT_RESOURCE_BOUNDARY:
                raise ExactClosureError("prefix replay found a pass absent from parent")
            primary = _pass_record(layer, assessment, seeded, comparator)
            if boundary_prefix is None:
                raise ExactClosureError("parent boundary certificate is missing")
            return {
                "classification": "exact_pass_on_fixed_orbit",
                "prefix_replay": dict(boundary_prefix),
                "last_assessed_layer": layer,
                "first_role": _role_record(first_role),
                "first_successor": _successor_record(first_successor),
                "first_intervention_eligible": _successor_record(first_eligible),
                "first_complete_pass": primary,
                "recurrence": None,
                "full_trace_sha256": digest.hexdigest(),
                "cross_size_controls": _size_controls(rows, primary),
            }

        if layer == CONE_SATURATION_LAYER:
            checkpoint = current
            checkpoint_layer = layer
            checkpoint_power = 1
            checkpoint_distance = 0
        elif layer > CONE_SATURATION_LAYER:
            if checkpoint is None or checkpoint_layer is None:
                raise ExactClosureError("Brent checkpoint is missing")
            checkpoint_distance += 1
            if current == checkpoint:
                if layer <= PARENT_RESOURCE_BOUNDARY:
                    raise ExactClosureError("prefix replay found recurrence absent from parent")
                if boundary_state is None:
                    raise ExactClosureError("parent boundary was not replayed")
                state = {
                    "seeded_state_hex": _state_hex(seeded, PRIMARY_CYCLE_SIZE),
                    "comparator_state_hex": _state_hex(comparator, PRIMARY_CYCLE_SIZE),
                }
                if boundary_prefix is None:
                    raise ExactClosureError("parent boundary certificate is missing")
                return {
                    "classification": "recurrence_excluded_on_fixed_orbit",
                    "prefix_replay": dict(boundary_prefix),
                    "last_assessed_layer": layer,
                    "first_role": _role_record(first_role),
                    "first_successor": _successor_record(first_successor),
                    "first_intervention_eligible": _successor_record(first_eligible),
                    "first_complete_pass": None,
                    "recurrence": {
                        "cone_saturation_layer": CONE_SATURATION_LAYER,
                        "checkpoint_layer": checkpoint_layer,
                        "repeat_layer": layer,
                        "period": checkpoint_distance,
                        "checkpoint_state": dict(state),
                        "repeat_state": dict(state),
                        "exact_full_state_equality": True,
                    },
                    "full_trace_sha256": digest.hexdigest(),
                    "cross_size_controls": [],
                }
            if checkpoint_distance == checkpoint_power:
                checkpoint = current
                checkpoint_layer = layer
                checkpoint_power *= 2
                checkpoint_distance = 0

        if layer == PARENT_RESOURCE_BOUNDARY:
            _require_parent_prefix(
                continuation,
                parent_record,
                digest,
                first_role,
                first_successor,
                first_eligible,
            )
            boundary_state = current
            if checkpoint is None or checkpoint_layer is None:
                raise ExactClosureError("boundary Brent schedule is incomplete")
            boundary_prefix = {
                "boundary_layer": PARENT_RESOURCE_BOUNDARY,
                "parent_trace_sha256": parent_record["trace_sha256"],
                "exact_match": True,
                "boundary_seeded_state_hex": _state_hex(
                    seeded, PRIMARY_CYCLE_SIZE
                ),
                "boundary_comparator_state_hex": _state_hex(
                    comparator, PRIMARY_CYCLE_SIZE
                ),
                "brent_checkpoint_layer": checkpoint_layer,
                "brent_checkpoint_seeded_state_hex": _state_hex(
                    checkpoint[0], PRIMARY_CYCLE_SIZE
                ),
                "brent_checkpoint_comparator_state_hex": _state_hex(
                    checkpoint[1], PRIMARY_CYCLE_SIZE
                ),
                "brent_power": checkpoint_power,
                "brent_distance": checkpoint_distance,
            }


def _registered_payload(
    payload: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
) -> dict[str, Any]:
    return evaluate_uncapped_continuation(*payload)


def _parent_maps(
    candidates: tuple[dict[str, Any], ...],
    parent_ledger: dict[str, Any],
    parent_candidates: tuple[dict[str, Any], ...],
) -> tuple[tuple[dict[str, Any], dict[str, Any]], ...]:
    results = parent_ledger.get("candidate_results")
    if type(results) is not list or len(results) != len(parent_candidates):
        raise ExactClosureError("parent result/candidate allocation mismatch")
    output: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for continuation in candidates:
        index = continuation.get("parent_candidate_index")
        if type(index) is not int or not 0 <= index < len(results):
            raise ExactClosureError("continuation parent index is invalid")
        parent_record = results[index]
        parent_candidate = parent_candidates[index]
        if type(parent_record) is not dict or type(parent_candidate) is not dict:
            raise ExactClosureError("parent allocation contains a non-object")
        output.append((parent_record, parent_candidate))
    return tuple(output)


def _static_record(
    candidate: dict[str, Any],
    certificate: LocalImpossibilityCertificate,
) -> dict[str, Any]:
    certificate_record = certificate.to_dict()
    if certificate_record.get("symbolically_unreachable") is not True:
        raise ExactClosureError("static record requires an impossibility certificate")
    return {
        "candidate_id": candidate["candidate_id"],
        "wolfram_rule_number": candidate["wolfram_rule_number"],
        "atomic_n_l": candidate["atomic_n_l"],
        "parent_candidate_index": candidate["parent_candidate_index"],
        "parent_record_sha256": candidate["parent_record_sha256"],
        "classification": "symbolically_unreachable",
        "symbolic_certificate": certificate_record,
        "dynamic_continuation": None,
        "future_unreachable": True,
    }


def _dynamic_record(
    candidate: dict[str, Any],
    certificate: LocalImpossibilityCertificate,
    outcome: dict[str, Any],
) -> dict[str, Any]:
    if certificate.symbolically_unreachable:
        raise ExactClosureError("statically excluded candidate cannot continue dynamically")
    if outcome.get("classification") not in (
        "exact_pass_on_fixed_orbit",
        "recurrence_excluded_on_fixed_orbit",
    ):
        raise ExactClosureError("dynamic continuation did not reach an exact terminal")
    return {
        "candidate_id": candidate["candidate_id"],
        "wolfram_rule_number": candidate["wolfram_rule_number"],
        "atomic_n_l": candidate["atomic_n_l"],
        "parent_candidate_index": candidate["parent_candidate_index"],
        "parent_record_sha256": candidate["parent_record_sha256"],
        "classification": outcome["classification"],
        "symbolic_certificate": certificate.to_dict(),
        "dynamic_continuation": outcome,
        "future_unreachable": True,
    }


def _summary(
    records: list[dict[str, Any]],
    parent_ledger: dict[str, Any],
) -> dict[str, Any]:
    parent_dynamic = [
        record
        for record in parent_ledger.get("candidate_results", [])
        if type(record) is dict and record.get("atomic_n_l", 0) > 0
    ]
    parent_recurrence = sum(
        record.get("evaluation_status") == "recurrence_excluded_on_fixed_orbit"
        for record in parent_dynamic
    )
    parent_resource = sum(
        record.get("evaluation_status") == "resource_censored_before_recurrence"
        for record in parent_dynamic
    )
    parent_passes = sum(
        record.get("evaluation_status") == "exact_pass_on_fixed_orbit"
        for record in parent_dynamic
    )
    if (
        parent_recurrence != PARENT_RECURRENCE_EXCLUDED_COUNT
        or parent_resource != PARENT_RESOURCE_CENSORED_COUNT
        or parent_passes != 0
    ):
        raise ExactClosureError("parent terminal counts differ from frozen allocation")
    static = [r for r in records if r["classification"] == "symbolically_unreachable"]
    recurrence = [
        r for r in records if r["classification"] == "recurrence_excluded_on_fixed_orbit"
    ]
    passes = [r for r in records if r["classification"] == "exact_pass_on_fixed_orbit"]
    if len(static) + len(recurrence) + len(passes) != PARENT_RESOURCE_CENSORED_COUNT:
        raise ExactClosureError("not every remaining candidate reached a terminal proof")
    exact_pass_ids = [r["candidate_id"] for r in passes]
    winners: list[str] = []
    ranking = "no_exact_passer"
    if passes:
        best_law = min(r["atomic_n_l"] for r in passes)
        shell = [r for r in passes if r["atomic_n_l"] == best_law]
        best_time = min(r["dynamic_continuation"]["first_complete_pass"]["layer"] for r in shell)
        winners = [
            r["candidate_id"]
            for r in shell
            if r["dynamic_continuation"]["first_complete_pass"]["layer"] == best_time
        ]
        ranking = "resolved_within_frozen_family"
    return {
        "all_remaining_candidates_terminal": True,
        "symbolically_unreachable_count": len(static),
        "continued_recurrence_excluded_count": len(recurrence),
        "continued_exact_pass_count": len(passes),
        "combined_exact_pass_count": len(passes),
        "combined_no_pass_proved_count": (
            PARENT_RECURRENCE_EXCLUDED_COUNT + len(static) + len(recurrence)
        ),
        "combined_exact_family_conclusion": (
            "one_or_more_exact_passes"
            if passes
            else "all_dynamic_candidates_exactly_no_pass"
        ),
        "exact_pass_candidate_ids": exact_pass_ids,
        "finite_ring_exposed_candidate_ids": exact_pass_ids,
        "minimum_law_ranking_status": ranking,
        "minimum_law_winner_candidate_ids": winners,
        "inherited_pre_wrap_mechanism_conclusion": parent_ledger[
            "pre_wrap_mechanism_conclusion"
        ],
        "inherited_pre_wrap_construction_conclusion": parent_ledger[
            "pre_wrap_construction_conclusion"
        ],
        "inherited_pre_wrap_stage_counts": parent_ledger["pre_wrap_stage_counts"],
    }


def run_exact_closure(
    candidates: Iterable[dict[str, Any]],
    parent_ledger: dict[str, Any],
    parent_candidates: tuple[dict[str, Any], ...],
    *,
    analyzer: Analyzer = analyze_local_impossibility,
    dynamic_evaluator: DynamicEvaluator = evaluate_uncapped_continuation,
    worker_processes: int = 1,
) -> dict[str, Any]:
    ordered = tuple(candidates)
    validate_continuation_manifest(ordered, parent_ledger)
    allocation = _parent_maps(ordered, parent_ledger, parent_candidates)
    if worker_processes not in (1, REGISTERED_WORKER_PROCESSES):
        raise ExactClosureError("worker allocation is not registered")
    certificates = tuple(
        analyzer(tuple(candidate["production_rows"])) for candidate in ordered
    )
    if any(type(certificate) is not LocalImpossibilityCertificate for certificate in certificates):
        raise ExactClosureError("symbolic analyzer returned the wrong certificate type")
    for candidate, certificate in zip(ordered, certificates):
        if certificate.production_rows != tuple(candidate["production_rows"]):
            raise ExactClosureError("symbolic certificate is not bound to candidate rows")

    survivor_indices = tuple(
        index
        for index, certificate in enumerate(certificates)
        if certificate.to_dict().get("symbolically_unreachable") is not True
    )
    outcomes: dict[int, dict[str, Any]] = {}
    if survivor_indices and worker_processes == REGISTERED_WORKER_PROCESSES:
        if dynamic_evaluator is not evaluate_uncapped_continuation:
            raise ExactClosureError("parallel mode is restricted to registered evaluator")
        payloads = tuple(
            (ordered[index], allocation[index][0], allocation[index][1])
            for index in survivor_indices
        )
        try:
            with ProcessPoolExecutor(
                max_workers=REGISTERED_WORKER_PROCESSES,
                mp_context=get_context("spawn"),
            ) as executor:
                values = tuple(executor.map(_registered_payload, payloads, chunksize=1))
        except ExactClosureError:
            raise
        except Exception as exc:
            raise ExactClosureError(
                "continuation worker pool failed before complete collection"
            ) from exc
        outcomes.update(zip(survivor_indices, values))
    else:
        for index in survivor_indices:
            outcomes[index] = dynamic_evaluator(
                ordered[index], allocation[index][0], allocation[index][1]
            )

    records: list[dict[str, Any]] = []
    for index, (candidate, certificate) in enumerate(zip(ordered, certificates)):
        if index in outcomes:
            records.append(_dynamic_record(candidate, certificate, outcomes[index]))
        else:
            records.append(_static_record(candidate, certificate))
    return {"candidate_results": records, **_summary(records, parent_ledger)}


def build_result_ledger(
    *,
    root: Path,
    candidates: Iterable[dict[str, Any]],
    open_manifest_binding: dict[str, str],
    outcome_seal_binding: dict[str, str],
    candidate_manifest_binding: dict[str, str],
    result_schema_binding: dict[str, str],
    worker_processes: int = REGISTERED_WORKER_PROCESSES,
) -> dict[str, Any]:
    ordered_candidates = tuple(candidates)
    parent = load_and_validate_parent(root)
    parent_candidate_binding = parent["candidate_manifest"]
    parent_candidates = read_parent_candidates(root / parent_candidate_binding["path"])
    for label, binding in (
        ("open_manifest", open_manifest_binding),
        ("outcome_seal", outcome_seal_binding),
        ("candidate_manifest", candidate_manifest_binding),
        ("result_schema", result_schema_binding),
    ):
        if (
            type(binding) is not dict
            or set(binding) != {"path", "sha256"}
            or type(binding["path"]) is not str
            or not _digest_ok(binding["sha256"])
        ):
            raise ExactClosureError(f"{label} binding is invalid")
    search = run_exact_closure(
        ordered_candidates,
        parent,
        parent_candidates,
        worker_processes=worker_processes,
    )
    ledger = {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": RUN_ID,
        "data_class": DATA_CLASS,
        "parent_result": {"path": PARENT_RESULT_REF, "sha256": PARENT_RESULT_SHA256},
        "parent_recurrence_excluded_count": PARENT_RECURRENCE_EXCLUDED_COUNT,
        "parent_resource_censored_count": PARENT_RESOURCE_CENSORED_COUNT,
        "parent_exact_pass_count": 0,
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "parent_boundary_layer": PARENT_RESOURCE_BOUNDARY,
        "dynamic_layer_ceiling": None,
        "terminal_check_order": [
            "evaluate complete detector and award any same-layer pass",
            "test exact post-saturation full joint-state recurrence",
        ],
        "open_manifest": dict(open_manifest_binding),
        "outcome_seal": dict(outcome_seal_binding),
        "candidate_manifest": dict(candidate_manifest_binding),
        "result_schema": dict(result_schema_binding),
        "global_minimality_claimed": False,
        **search,
    }
    validate_result_ledger(ledger, ordered_candidates, parent)
    return ledger


LEDGER_KEYS = {
    "protocol_version",
    "search_id",
    "run_id",
    "data_class",
    "parent_result",
    "parent_recurrence_excluded_count",
    "parent_resource_censored_count",
    "parent_exact_pass_count",
    "primary_cycle_size",
    "parent_boundary_layer",
    "dynamic_layer_ceiling",
    "terminal_check_order",
    "open_manifest",
    "outcome_seal",
    "candidate_manifest",
    "result_schema",
    "global_minimality_claimed",
    "all_remaining_candidates_terminal",
    "symbolically_unreachable_count",
    "continued_recurrence_excluded_count",
    "continued_exact_pass_count",
    "combined_exact_pass_count",
    "combined_no_pass_proved_count",
    "combined_exact_family_conclusion",
    "exact_pass_candidate_ids",
    "finite_ring_exposed_candidate_ids",
    "minimum_law_ranking_status",
    "minimum_law_winner_candidate_ids",
    "inherited_pre_wrap_mechanism_conclusion",
    "inherited_pre_wrap_construction_conclusion",
    "inherited_pre_wrap_stage_counts",
    "candidate_results",
}


DYNAMIC_OUTCOME_KEYS = {
    "classification",
    "prefix_replay",
    "last_assessed_layer",
    "first_role",
    "first_successor",
    "first_intervention_eligible",
    "first_complete_pass",
    "recurrence",
    "full_trace_sha256",
    "cross_size_controls",
}
PREFIX_KEYS = {
    "boundary_layer",
    "parent_trace_sha256",
    "exact_match",
    "boundary_seeded_state_hex",
    "boundary_comparator_state_hex",
    "brent_checkpoint_layer",
    "brent_checkpoint_seeded_state_hex",
    "brent_checkpoint_comparator_state_hex",
    "brent_power",
    "brent_distance",
}


def _valid_state_hex(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == PRIMARY_CYCLE_SIZE // 4
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_stage_record(value: Any, *, successor: bool, last_layer: int) -> None:
    if value is None:
        return
    keys = {"layer", "anchor", "successor_anchor"} if successor else {"layer", "anchor"}
    if type(value) is not dict or set(value) != keys:
        raise ExactClosureError("dynamic stage witness shape mismatch")
    if type(value["layer"]) is not int or not 1 <= value["layer"] <= last_layer:
        raise ExactClosureError("dynamic stage layer mismatch")
    if type(value["anchor"]) is not int or not 0 <= value["anchor"] < PRIMARY_CYCLE_SIZE:
        raise ExactClosureError("dynamic stage anchor mismatch")
    if successor:
        target = value["successor_anchor"]
        if type(target) is not int or not 0 <= target < PRIMARY_CYCLE_SIZE:
            raise ExactClosureError("dynamic successor anchor mismatch")
        if (target - value["anchor"]) % PRIMARY_CYCLE_SIZE not in (0, 1):
            raise ExactClosureError("dynamic successor displacement mismatch")


def _validate_pass_record(value: Any, last_layer: int) -> None:
    keys = {
        "layer", "anchor", "signed_anchor", "successor_anchor",
        "successor_displacement", "sham_future", "breaking_future",
        "seeded_state_hex", "baseline_state_hex",
    }
    if type(value) is not dict or set(value) != keys or value.get("layer") != last_layer:
        raise ExactClosureError("dynamic pass witness shape or layer mismatch")
    anchor = value.get("anchor")
    successor = value.get("successor_anchor")
    if (
        type(anchor) is not int
        or type(successor) is not int
        or not 0 <= anchor < PRIMARY_CYCLE_SIZE
        or not 0 <= successor < PRIMARY_CYCLE_SIZE
        or value.get("signed_anchor") != _signed_anchor(anchor, PRIMARY_CYCLE_SIZE)
        or value.get("successor_displacement")
        != (successor - anchor) % PRIMARY_CYCLE_SIZE
        or value.get("successor_displacement") not in (0, 1)
        or value.get("sham_future") not in (0, 1)
        or value.get("breaking_future") not in (0, 1)
        or value.get("sham_future") == value.get("breaking_future")
        or not _valid_state_hex(value.get("seeded_state_hex"))
        or not _valid_state_hex(value.get("baseline_state_hex"))
    ):
        raise ExactClosureError("dynamic pass witness values mismatch")


def _validate_dynamic_outcome(
    outcome: dict[str, Any],
    candidate: dict[str, Any],
    classification: str,
) -> None:
    if set(outcome) != DYNAMIC_OUTCOME_KEYS:
        raise ExactClosureError("dynamic outcome has missing or unexpected fields")
    last_layer = outcome.get("last_assessed_layer")
    if type(last_layer) is not int or last_layer <= PARENT_RESOURCE_BOUNDARY:
        raise ExactClosureError("dynamic terminal is not beyond the parent boundary")
    if outcome.get("classification") != classification:
        raise ExactClosureError("dynamic classification mismatch")
    if not _digest_ok(outcome.get("full_trace_sha256")):
        raise ExactClosureError("dynamic trace digest is invalid")
    prefix = outcome.get("prefix_replay")
    if type(prefix) is not dict or set(prefix) != PREFIX_KEYS:
        raise ExactClosureError("prefix replay certificate shape mismatch")
    power = prefix.get("brent_power")
    distance = prefix.get("brent_distance")
    checkpoint_layer = prefix.get("brent_checkpoint_layer")
    if (
        prefix.get("boundary_layer") != PARENT_RESOURCE_BOUNDARY
        or prefix.get("parent_trace_sha256")
        != candidate["parent_prefix_trace_sha256"]
        or prefix.get("exact_match") is not True
        or not _valid_state_hex(prefix.get("boundary_seeded_state_hex"))
        or not _valid_state_hex(prefix.get("boundary_comparator_state_hex"))
        or not _valid_state_hex(prefix.get("brent_checkpoint_seeded_state_hex"))
        or not _valid_state_hex(prefix.get("brent_checkpoint_comparator_state_hex"))
        or type(checkpoint_layer) is not int
        or not CONE_SATURATION_LAYER <= checkpoint_layer <= PARENT_RESOURCE_BOUNDARY
        or type(power) is not int
        or power < 1
        or power & (power - 1)
        or type(distance) is not int
        or not 0 <= distance < power
        or checkpoint_layer + distance != PARENT_RESOURCE_BOUNDARY
    ):
        raise ExactClosureError("prefix replay certificate values mismatch")
    _validate_stage_record(outcome.get("first_role"), successor=False, last_layer=last_layer)
    _validate_stage_record(outcome.get("first_successor"), successor=True, last_layer=last_layer)
    _validate_stage_record(
        outcome.get("first_intervention_eligible"),
        successor=True,
        last_layer=last_layer,
    )
    inherited = (
        ("first_role", "inherited_first_role"),
        ("first_successor", "inherited_first_successor"),
        ("first_intervention_eligible", "inherited_first_intervention_eligible"),
    )
    for outcome_key, candidate_key in inherited:
        if candidate[candidate_key] is not None and not strict_json_equal(
            outcome.get(outcome_key), candidate[candidate_key]
        ):
            raise ExactClosureError("dynamic continuation changed an inherited first witness")

    controls = outcome.get("cross_size_controls")
    if type(controls) is not list:
        raise ExactClosureError("dynamic size controls must be a list")
    if classification == "exact_pass_on_fixed_orbit":
        _validate_pass_record(outcome.get("first_complete_pass"), last_layer)
        if outcome.get("recurrence") is not None:
            raise ExactClosureError("passing continuation contains recurrence")
        if [control.get("cycle_size") for control in controls if type(control) is dict] != list(
            EMBEDDING_CYCLE_SIZES
        ) or len(controls) != len(EMBEDDING_CYCLE_SIZES):
            raise ExactClosureError("passing continuation lacks both size controls")
        for control in controls:
            if (
                set(control) != {
                    "cycle_size", "evaluated_through_layer", "first_complete_pass",
                    "matches_primary_witness", "pre_wrap_agreement_required",
                    "exact_pre_wrap_agreement",
                }
                or control.get("evaluated_through_layer") != last_layer
                or type(control.get("matches_primary_witness")) is not bool
                or control.get("pre_wrap_agreement_required") is not False
                or control.get("exact_pre_wrap_agreement") is not None
            ):
                raise ExactClosureError("size-control record mismatch")
            witness = control.get("first_complete_pass")
            if witness is not None:
                if (
                    type(witness) is not dict
                    or set(witness) != {
                        "layer", "signed_anchor", "successor_displacement",
                        "sham_future", "breaking_future",
                    }
                    or type(witness.get("layer")) is not int
                    or not 1 <= witness["layer"] <= last_layer
                    or type(witness.get("signed_anchor")) is not int
                    or witness.get("successor_displacement") not in (0, 1)
                    or witness.get("sham_future") not in (0, 1)
                    or witness.get("breaking_future") not in (0, 1)
                    or witness.get("sham_future") == witness.get("breaking_future")
                ):
                    raise ExactClosureError("size-control witness mismatch")
            primary_compact = _compact_pass(outcome["first_complete_pass"])
            if control.get("matches_primary_witness") is not (
                witness == primary_compact
            ):
                raise ExactClosureError("size-control primary comparison mismatch")
    else:
        if outcome.get("first_complete_pass") is not None or controls:
            raise ExactClosureError("recurrence continuation contains pass data")
        recurrence = outcome.get("recurrence")
        recurrence_keys = {
            "cone_saturation_layer", "checkpoint_layer", "repeat_layer", "period",
            "checkpoint_state", "repeat_state", "exact_full_state_equality",
        }
        if type(recurrence) is not dict or set(recurrence) != recurrence_keys:
            raise ExactClosureError("recurrence certificate shape mismatch")
        checkpoint = recurrence.get("checkpoint_layer")
        period = recurrence.get("period")
        state = recurrence.get("checkpoint_state")
        if (
            recurrence.get("cone_saturation_layer") != CONE_SATURATION_LAYER
            or recurrence.get("repeat_layer") != last_layer
            or type(checkpoint) is not int
            or type(period) is not int
            or period < 1
            or checkpoint + period != last_layer
            or recurrence.get("exact_full_state_equality") is not True
            or type(state) is not dict
            or set(state) != {"seeded_state_hex", "comparator_state_hex"}
            or not _valid_state_hex(state.get("seeded_state_hex"))
            or not _valid_state_hex(state.get("comparator_state_hex"))
            or not strict_json_equal(recurrence.get("repeat_state"), state)
        ):
            raise ExactClosureError("recurrence certificate values mismatch")


def validate_result_ledger(
    ledger: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
    parent_ledger: dict[str, Any],
) -> None:
    if type(ledger) is not dict or set(ledger) != LEDGER_KEYS:
        raise ExactClosureError("result ledger has missing or unexpected fields")
    fixed = {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": RUN_ID,
        "data_class": DATA_CLASS,
        "parent_result": {"path": PARENT_RESULT_REF, "sha256": PARENT_RESULT_SHA256},
        "parent_recurrence_excluded_count": PARENT_RECURRENCE_EXCLUDED_COUNT,
        "parent_resource_censored_count": PARENT_RESOURCE_CENSORED_COUNT,
        "parent_exact_pass_count": 0,
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "parent_boundary_layer": PARENT_RESOURCE_BOUNDARY,
        "dynamic_layer_ceiling": None,
        "terminal_check_order": [
            "evaluate complete detector and award any same-layer pass",
            "test exact post-saturation full joint-state recurrence",
        ],
        "global_minimality_claimed": False,
        "all_remaining_candidates_terminal": True,
    }
    for key, expected in fixed.items():
        if not strict_json_equal(ledger.get(key), expected):
            raise ExactClosureError(f"result ledger {key} mismatch")
    ordered = tuple(candidates)
    validate_continuation_manifest(ordered, parent_ledger)
    records = ledger.get("candidate_results")
    if type(records) is not list or len(records) != len(ordered):
        raise ExactClosureError("candidate result allocation mismatch")
    for candidate, record in zip(ordered, records):
        if type(record) is not dict:
            raise ExactClosureError("candidate result is not an object")
        if set(record) != {
            "candidate_id",
            "wolfram_rule_number",
            "atomic_n_l",
            "parent_candidate_index",
            "parent_record_sha256",
            "classification",
            "symbolic_certificate",
            "dynamic_continuation",
            "future_unreachable",
        }:
            raise ExactClosureError("candidate result has missing or unexpected fields")
        if record.get("candidate_id") != candidate["candidate_id"]:
            raise ExactClosureError("candidate result order mismatch")
        for key in (
            "wolfram_rule_number",
            "atomic_n_l",
            "parent_candidate_index",
            "parent_record_sha256",
        ):
            if not strict_json_equal(record.get(key), candidate[key]):
                raise ExactClosureError(f"candidate result {key} binding mismatch")
        certificate = record.get("symbolic_certificate")
        expected_certificate = analyze_local_impossibility(
            tuple(candidate["production_rows"])
        ).to_dict()
        if (
            type(certificate) is not dict
            or certificate.get("production_rows") != candidate["production_rows"]
            or certificate.get("rule_number") != candidate["wolfram_rule_number"]
            or not strict_json_equal(certificate, expected_certificate)
        ):
            raise ExactClosureError("candidate symbolic certificate binding mismatch")
        if record.get("future_unreachable") is not True:
            raise ExactClosureError("candidate lacks a terminal future proof")
        classification = record.get("classification")
        if classification == "symbolically_unreachable":
            if record.get("dynamic_continuation") is not None:
                raise ExactClosureError("symbolic result contains a dynamic continuation")
            if record.get("symbolic_certificate", {}).get("symbolically_unreachable") is not True:
                raise ExactClosureError("symbolic classification lacks its proof")
        elif classification in (
            "exact_pass_on_fixed_orbit",
            "recurrence_excluded_on_fixed_orbit",
        ):
            outcome = record.get("dynamic_continuation")
            if type(outcome) is not dict:
                raise ExactClosureError("dynamic classification lacks an outcome")
            if certificate.get("symbolically_unreachable") is not False:
                raise ExactClosureError("dynamically continued candidate was statically excluded")
            _validate_dynamic_outcome(outcome, candidate, classification)
        else:
            raise ExactClosureError("unknown candidate classification")
    expected_summary = _summary(records, parent_ledger)
    for key, expected in expected_summary.items():
        if not strict_json_equal(ledger.get(key), expected):
            raise ExactClosureError(f"result summary {key} mismatch")
