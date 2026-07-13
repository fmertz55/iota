from __future__ import annotations

import hashlib
from typing import Any, Iterable, Optional

from src.minimal_realization.detector import (
    LAST_REQUIRED_LAYER,
    canonical_initial_state,
    detect_proto_object,
    in_forward_cone,
    outward_future_values,
    role_at,
    successor_anchor,
)
from src.minimal_realization.dynamics import (
    CYCLE_SIZE,
    event_at,
    normalize_rows,
    run_trajectory,
    step,
)

from .runner import (
    CONE_SATURATION_LAYER,
    MAX_LAYERS_PER_CANDIDATE,
    PARENT_CENSORING_LAYER,
    SEARCH_ID,
    OrbitLedgerError,
    candidate_sha256,
    expected_candidate_rows,
)


def trace_domain(candidate: dict[str, Any]) -> bytes:
    candidate_id = candidate.get("candidate_id")
    if type(candidate_id) is not str or not candidate_id:
        raise OrbitLedgerError("candidate id is invalid for trace-domain binding")
    return (
        f"{SEARCH_ID}\0{candidate_id}\0{candidate_sha256(candidate)}"
    ).encode("ascii")


def _update_digest(
    digest: "hashlib._Hash",
    layer: int,
    seeded_state: int,
    baseline_state: int,
) -> None:
    layer_bytes = str(layer).encode("ascii")
    digest.update(len(layer_bytes).to_bytes(8, "big"))
    digest.update(layer_bytes)
    digest.update(seeded_state.to_bytes(8, "big"))
    digest.update(baseline_state.to_bytes(8, "big"))


def _new_trace_digest(candidate: dict[str, Any]) -> "hashlib._Hash":
    domain = trace_domain(candidate)
    digest = hashlib.sha256()
    digest.update(b"IOTA-MIR-EXACT-ORBIT-TRACE-V1\x00")
    digest.update(len(domain).to_bytes(8, "big"))
    digest.update(domain)
    return digest


def _parent_origin_record(rows: tuple[str, ...]) -> dict[str, Any]:
    production_rows = tuple(sorted(normalize_rows(rows)))
    seeded = run_trajectory(
        canonical_initial_state(0),
        production_rows,
        LAST_REQUIRED_LAYER,
    )
    baseline = run_trajectory(0, production_rows, LAST_REQUIRED_LAYER)
    result = detect_proto_object(seeded, baseline, production_rows, origin=0)
    return {
        "translation_offset": 0,
        "status": (
            "passed_by_H16" if result.passed else "right_censored_T_proto_gt_16"
        ),
        "t_proto": result.t_proto,
        "anchor": result.anchor,
        "anchor_offset_from_seed": result.anchor,
        "successor_anchor": result.successor_anchor,
        "successor_anchor_offset_from_seed": result.successor_anchor,
        "sham_future": result.sham_future,
        "breaking_future": result.breaking_future,
    }


def _assess_layer(
    seeded_state: int,
    baseline_state: int,
    rows: tuple[str, ...],
    layer: int,
) -> dict[str, Any]:
    """Independent spelling of the frozen layer predicate."""

    next_seeded = step(seeded_state, rows)
    next_baseline = step(baseline_state, rows)
    first_role: Optional[dict[str, int]] = None
    first_successor: Optional[dict[str, int]] = None
    first_eligible: Optional[dict[str, int]] = None

    for distance in range(CYCLE_SIZE):
        anchor = distance
        if not in_forward_cone(anchor, 0, layer):
            continue
        if not in_forward_cone(anchor + 1, 0, layer):
            continue
        if not role_at(seeded_state, baseline_state, anchor):
            continue
        if first_role is None:
            first_role = {"layer": layer, "anchor": anchor}
        successor = successor_anchor(
            next_seeded,
            next_baseline,
            anchor,
            origin=0,
            next_layer=layer + 1,
        )
        if successor is None:
            continue
        if first_successor is None:
            first_successor = {
                "layer": layer,
                "anchor": anchor,
                "successor_anchor": successor,
            }
        if not in_forward_cone(anchor + 3, 0, layer + 2):
            continue
        if event_at(seeded_state, anchor + 3) != 0:
            continue
        if first_eligible is None:
            first_eligible = {
                "layer": layer,
                "anchor": anchor,
                "successor_anchor": successor,
            }
        sham_future, breaking_future = outward_future_values(
            seeded_state,
            rows,
            anchor,
        )
        if sham_future != breaking_future:
            return {
                "first_role": first_role,
                "first_successor": first_successor,
                "first_intervention_eligible": first_eligible,
                "pass_witness": {
                    "layer": layer,
                    "anchor": anchor,
                    "successor_anchor": successor,
                    "sham_future": sham_future,
                    "breaking_future": breaking_future,
                    "seeded_state_hex": f"{seeded_state:016x}",
                    "baseline_state_hex": f"{baseline_state:016x}",
                },
            }
    return {
        "first_role": first_role,
        "first_successor": first_successor,
        "first_intervention_eligible": first_eligible,
        "pass_witness": None,
    }


def _verify_dynamic_candidate(
    record: dict[str, Any],
    candidate: dict[str, Any],
    rows: tuple[str, ...],
) -> None:
    last_layer = record["last_evaluated_layer"]
    if type(last_layer) is not int or not 17 <= last_layer <= MAX_LAYERS_PER_CANDIDATE:
        raise OrbitLedgerError("independent replay received an invalid terminal layer")
    seeded_state = canonical_initial_state(0)
    baseline_state = 0
    digest = _new_trace_digest(candidate)
    _update_digest(digest, 0, seeded_state, baseline_state)
    first_role = None
    first_successor = None
    first_eligible = None
    first_pass = None
    post_saturation_seen: dict[tuple[int, int], int] = {}
    first_table_repeat: Optional[tuple[int, int]] = None
    checkpoint_state: Optional[tuple[int, int]] = None
    checkpoint_layer: Optional[int] = None
    checkpoint_power = 1
    checkpoint_distance = 0
    first_checkpoint_repeat: Optional[tuple[int, int, int, int, int]] = None
    claimed_checkpoint_state: Optional[tuple[int, int]] = None
    recurrence = record.get("recurrence")
    claimed_checkpoint_layer = (
        recurrence.get("checkpoint_layer")
        if type(recurrence) is dict
        else None
    )

    for layer in range(1, last_layer + 1):
        seeded_state = step(seeded_state, rows)
        baseline_state = step(baseline_state, rows)
        _update_digest(digest, layer, seeded_state, baseline_state)
        assessment = _assess_layer(seeded_state, baseline_state, rows, layer)
        if first_role is None and assessment["first_role"] is not None:
            first_role = assessment["first_role"]
        if first_successor is None and assessment["first_successor"] is not None:
            first_successor = assessment["first_successor"]
        if first_eligible is None and assessment["first_intervention_eligible"] is not None:
            first_eligible = assessment["first_intervention_eligible"]
        if assessment["pass_witness"] is not None:
            first_pass = assessment["pass_witness"]
            if layer != last_layer:
                raise OrbitLedgerError("result continued after an independently reproduced first pass")
            continue
        if layer >= CONE_SATURATION_LAYER:
            state = (seeded_state, baseline_state)
            prior = post_saturation_seen.get(state)
            if prior is not None:
                if first_table_repeat is None:
                    first_table_repeat = (prior, layer)
            else:
                post_saturation_seen[state] = layer
        if layer == CONE_SATURATION_LAYER:
            checkpoint_state = (seeded_state, baseline_state)
            checkpoint_layer = layer
            checkpoint_power = 1
            checkpoint_distance = 0
        elif layer > CONE_SATURATION_LAYER:
            if checkpoint_state is None or checkpoint_layer is None:
                raise OrbitLedgerError("independent recurrence checkpoint is missing")
            checkpoint_distance += 1
            if (seeded_state, baseline_state) == checkpoint_state:
                if first_checkpoint_repeat is None:
                    first_checkpoint_repeat = (
                        checkpoint_layer,
                        layer,
                        checkpoint_distance,
                        seeded_state,
                        baseline_state,
                    )
                if layer != last_layer:
                    raise OrbitLedgerError(
                        "result continued after the first registered checkpoint equality"
                    )
            elif checkpoint_distance == checkpoint_power:
                checkpoint_state = (seeded_state, baseline_state)
                checkpoint_layer = layer
                checkpoint_power *= 2
                checkpoint_distance = 0
        if layer == claimed_checkpoint_layer:
            claimed_checkpoint_state = (seeded_state, baseline_state)

    if record["trace_sha256"] != digest.hexdigest():
        raise OrbitLedgerError("candidate trace digest differs under independent replay")
    if record["first_role"] != first_role:
        raise OrbitLedgerError("first role witness differs under independent replay")
    if record["first_successor"] != first_successor:
        raise OrbitLedgerError("first succession witness differs under independent replay")
    if record["first_intervention_eligible"] != first_eligible:
        raise OrbitLedgerError("first intervention witness differs under independent replay")

    status = record["evaluation_status"]
    if status == "exact_pass_on_fixed_orbit":
        if first_pass is None or record["pass_witness"] != first_pass:
            raise OrbitLedgerError("pass witness differs under independent replay")
        if record["t_proto_exact"] != first_pass["layer"]:
            raise OrbitLedgerError("pass time differs under independent replay")
    elif status == "recurrence_excluded_on_fixed_orbit":
        if first_pass is not None:
            raise OrbitLedgerError("recurrence result contains an independently reproduced pass")
        if type(recurrence) is not dict or claimed_checkpoint_state is None:
            raise OrbitLedgerError("recurrence certificate is incomplete")
        repeat_state = (seeded_state, baseline_state)
        if claimed_checkpoint_state != repeat_state:
            raise OrbitLedgerError("claimed recurrence states are not exactly equal")
        expected_state = {
            "seeded_state_hex": f"{seeded_state:016x}",
            "baseline_state_hex": f"{baseline_state:016x}",
        }
        if recurrence["checkpoint_state"] != expected_state or recurrence["repeat_state"] != expected_state:
            raise OrbitLedgerError("recurrence certificate state bytes differ")
        expected_checkpoint_repeat = (
            recurrence["checkpoint_layer"],
            recurrence["repeat_layer"],
            recurrence["period"],
            seeded_state,
            baseline_state,
        )
        if first_checkpoint_repeat != expected_checkpoint_repeat:
            raise OrbitLedgerError("registered checkpoint recurrence differs under independent replay")
        if first_table_repeat is None:
            raise OrbitLedgerError("independent state table found no post-saturation recurrence")
    elif status == "resource_censored_before_recurrence":
        if first_pass is not None:
            raise OrbitLedgerError("resource-censored result contains an independently reproduced pass")
        if first_checkpoint_repeat is not None:
            raise OrbitLedgerError("resource-censored result missed a registered checkpoint recurrence")
    else:
        raise OrbitLedgerError("independent replay received an unknown status")


def verify_ledger_independently(
    ledger: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
    parent_result: dict[str, Any],
) -> None:
    canonical_candidates = tuple(candidates)
    candidate_results = ledger.get("candidate_results")
    parent_results = parent_result.get("candidate_results")
    if (
        len(canonical_candidates) != 16
        or type(candidate_results) is not list
        or len(candidate_results) != 16
        or type(parent_results) is not list
        or len(parent_results) != 16
    ):
        raise OrbitLedgerError("independent verifier candidate allocation mismatch")
    for index, rows in enumerate(expected_candidate_rows()[1:], start=1):
        parent_origin = parent_results[index]["translations"][0]
        if _parent_origin_record(rows) != parent_origin:
            raise OrbitLedgerError(
                "independent H=16 reproduction differs from parent ledger"
            )
    for index, (candidate, rows, record) in enumerate(
        zip(canonical_candidates, expected_candidate_rows(), candidate_results)
    ):
        if index == 0:
            continue
        _verify_dynamic_candidate(record, candidate, rows)
