"""Algorithmically independent replay for role-succession result ledgers.

This module intentionally imports neither the production dynamics nor the
production detector/runner.  Transition, cone, intervention, digest, and
streaming checkpoint logic are re-spelled below.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from functools import lru_cache
from typing import Any, Iterable, Optional

from .protocol import (
    BASE_CONTRACT_VERSION,
    CANONICAL_ORIGIN,
    CANDIDATE_COUNT,
    CAUSAL_ENDPOINT_LAG,
    DETECTOR_ID,
    DATA_CLASS,
    DYNAMIC_CANDIDATE_COUNT,
    EMBEDDING_CYCLE_SIZES,
    FORMATION_HORIZON,
    GRAMMAR_ID,
    MAX_LAYERS_PER_CANDIDATE,
    PRIMARY_CONE_SATURATION_LAYER,
    PRIMARY_CYCLE_SIZE,
    PROTOCOL_VERSION,
    REGISTERED_WORKER_PROCESSES,
    RESULT_ENDPOINT,
    RUN_ID,
    SEARCH_ID,
    SHELL_SIZES,
    SIGNATURE_ORDER,
)


TRACE_PREFIX = b"IOTA-MIR-ROLE-SUCCESSION-TRACE-V1\x00"
SYMMETRY_AUDIT_LAST_LAYER = FORMATION_HORIZON + CAUSAL_ENDPOINT_LAG
TERMINAL_STATUSES = {
    "exact_pass_on_fixed_orbit",
    "recurrence_excluded_on_fixed_orbit",
    "resource_censored_before_recurrence",
}


class IndependentVerificationError(ValueError):
    pass


def _independent_verification_payload(
    payload: tuple[dict[str, Any], dict[str, Any], tuple[str, ...]],
) -> None:
    """Top-level spawn-safe adapter for one independent candidate replay."""

    record, candidate, rows = payload
    _verify_dynamic_candidate(record, candidate, rows)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _candidate_sha256(candidate: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(candidate).encode("ascii")).hexdigest()


def _expected_rows() -> tuple[tuple[str, ...], ...]:
    output: list[tuple[str, ...]] = []
    for count in range(len(SIGNATURE_ORDER) + 1):
        output.extend(itertools.combinations(SIGNATURE_ORDER, count))
    return tuple(output)


def _candidate_id(rows: tuple[str, ...]) -> str:
    suffix = "NONE" if not rows else "-".join(rows)
    return f"MIR-RS-P2-L{len(rows)}-{suffix}"


def _reflected_rows(rows: tuple[str, ...]) -> tuple[str, ...]:
    reflected = {signature[::-1] for signature in rows}
    return tuple(signature for signature in SIGNATURE_ORDER if signature in reflected)


def _wolfram_code(rows: tuple[str, ...]) -> int:
    return sum(1 << int(signature, 2) for signature in rows)


@lru_cache(maxsize=16, typed=True)
def _mask(cycle_size: int) -> int:
    if type(cycle_size) is not int or cycle_size < 4:
        raise IndependentVerificationError("cycle size is invalid")
    return (1 << cycle_size) - 1


def _require_state(state: int, cycle_size: int) -> int:
    if type(state) is not int or not 0 <= state <= _mask(cycle_size):
        raise IndependentVerificationError("state is outside its fixed-width ring")
    return state


def _event(state: int, locus: int, cycle_size: int) -> int:
    _require_state(state, cycle_size)
    if type(locus) is not int:
        raise IndependentVerificationError("locus must be an integer")
    return (state >> (locus % cycle_size)) & 1


@lru_cache(maxsize=256)
def _anf_terms(rows: tuple[str, ...]) -> tuple[int, ...]:
    """Compile a truth table to algebraic-normal-form monomials.

    This is deliberately independent of the production engine's OR of exact
    minterm masks.  The verifier applies the three-variable Boolean Möbius
    transform, then evaluates the resulting polynomial over aligned ring
    bitplanes with XOR/AND operations.
    """

    if (
        any(type(signature) is not str for signature in rows)
        or tuple(signature for signature in SIGNATURE_ORDER if signature in set(rows))
        != rows
    ):
        raise IndependentVerificationError("production rows are not canonical")
    coefficients = [int(f"{value:03b}" in rows) for value in range(8)]
    for variable_bit in (0b001, 0b010, 0b100):
        for monomial in range(8):
            if monomial & variable_bit:
                coefficients[monomial] ^= coefficients[monomial ^ variable_bit]
    return tuple(index for index, coefficient in enumerate(coefficients) if coefficient)


def _rotate_left(state: int, distance: int, cycle_size: int, mask: int) -> int:
    shift = distance % cycle_size
    if shift == 0:
        return state
    return ((state << shift) | (state >> (cycle_size - shift))) & mask


def _rotate_right(state: int, distance: int, cycle_size: int, mask: int) -> int:
    shift = distance % cycle_size
    if shift == 0:
        return state
    return ((state >> shift) | (state << (cycle_size - shift))) & mask


def _transition(state: int, rows: tuple[str, ...], cycle_size: int) -> int:
    """Independent bit-parallel ANF transition on the fixed ring."""

    _require_state(state, cycle_size)
    terms = _anf_terms(rows)
    mask = _mask(cycle_size)
    predecessor_values = _rotate_left(state, 1, cycle_size, mask)
    successor_values = _rotate_right(state, 1, cycle_size, mask)
    output = 0
    for monomial in terms:
        term = mask
        if monomial & 0b100:
            term &= predecessor_values
        if monomial & 0b010:
            term &= state
        if monomial & 0b001:
            term &= successor_values
        output ^= term
    return output & mask


def _translate(state: int, offset: int, cycle_size: int) -> int:
    _require_state(state, cycle_size)
    shift = offset % cycle_size
    if shift == 0:
        return state
    return ((state << shift) | (state >> (cycle_size - shift))) & _mask(cycle_size)


def _reflect(state: int, cycle_size: int) -> int:
    _require_state(state, cycle_size)
    output = 0
    for locus in range(cycle_size):
        if _event(state, locus, cycle_size):
            output |= 1 << ((-locus) % cycle_size)
    return output


def _graph_distance(locus: int, origin: int, cycle_size: int) -> int:
    forward = (locus - origin) % cycle_size
    return min(forward, cycle_size - forward)


def _in_cone(locus: int, origin: int, layer: int, cycle_size: int) -> bool:
    return _graph_distance(locus, origin, cycle_size) <= layer


@lru_cache(maxsize=512)
def _ordered_anchors(origin: int, cycle_size: int) -> tuple[int, ...]:
    return tuple(
        sorted(
            range(cycle_size),
            key=lambda locus: (
                _graph_distance(locus, origin, cycle_size),
                (locus - origin) % cycle_size,
            ),
        )
    )


def _role_mask_unchecked(
    state: int,
    baseline: int,
    cycle_size: int,
    mask: int,
) -> int:
    predecessor_values = _rotate_left(state, 1, cycle_size, mask)
    successor_values = _rotate_right(state, 1, cycle_size, mask)
    second_successor_values = _rotate_right(state, 2, cycle_size, mask)
    baseline_successor_values = _rotate_right(baseline, 1, cycle_size, mask)
    return (
        state
        & successor_values
        & (predecessor_values ^ mask)
        & (second_successor_values ^ mask)
        & (baseline ^ mask)
        & (baseline_successor_values ^ mask)
    ) & mask


@lru_cache(maxsize=1024)
def _cone_mask_at_radius(origin: int, radius: int, cycle_size: int) -> int:
    if radius >= cycle_size // 2:
        return _mask(cycle_size)
    output = 0
    for locus in range(cycle_size):
        if _graph_distance(locus, origin, cycle_size) <= radius:
            output |= 1 << locus
    return output


def _cone_mask(origin: int, layer: int, cycle_size: int) -> int:
    return _cone_mask_at_radius(
        origin,
        min(layer, cycle_size // 2),
        cycle_size,
    )


@lru_cache(maxsize=1024)
def _eligible_anchor_mask_at_radius(
    origin: int,
    radius: int,
    cycle_size: int,
) -> int:
    mask = _mask(cycle_size)
    cone = _cone_mask_at_radius(origin, radius, cycle_size)
    return cone & _rotate_right(cone, 1, cycle_size, mask)


def _eligible_anchor_mask(origin: int, layer: int, cycle_size: int) -> int:
    return _eligible_anchor_mask_at_radius(
        origin,
        min(layer, cycle_size // 2),
        cycle_size,
    )


def _role(state: int, baseline: int, anchor: int, cycle_size: int) -> bool:
    _require_state(state, cycle_size)
    _require_state(baseline, cycle_size)
    if type(anchor) is not int:
        raise IndependentVerificationError("anchor must be an integer")
    roles = _role_mask_unchecked(state, baseline, cycle_size, _mask(cycle_size))
    return bool(roles & (1 << (anchor % cycle_size)))


def _successor(
    next_seeded: int,
    next_baseline: int,
    anchor: int,
    origin: int,
    next_layer: int,
    cycle_size: int,
) -> Optional[int]:
    roles = _role_mask_unchecked(
        next_seeded,
        next_baseline,
        cycle_size,
        _mask(cycle_size),
    ) & _eligible_anchor_mask(origin, next_layer, cycle_size)
    for displacement in (0, 1):
        candidate = (anchor + displacement) % cycle_size
        if roles & (1 << candidate):
            return candidate
    return None


def _replace_three(
    state: int,
    anchor: int,
    values: tuple[int, int, int],
    cycle_size: int,
) -> int:
    output = state
    for offset, value in enumerate(values):
        bit = 1 << ((anchor + offset) % cycle_size)
        output = output | bit if value else output & ~bit
    return output


def _outward_values(
    state: int,
    rows: tuple[str, ...],
    anchor: int,
    cycle_size: int,
) -> tuple[int, int]:
    natural = tuple(_event(state, anchor + offset, cycle_size) for offset in range(3))
    if natural != (1, 1, 0) or _event(state, anchor + 3, cycle_size) != 0:
        raise IndependentVerificationError("intervention precondition is absent")
    sham = _replace_three(state, anchor, (0, 1, 1), cycle_size)
    breaking = _replace_three(state, anchor, (1, 0, 1), cycle_size)
    for _ in range(2):
        sham = _transition(sham, rows, cycle_size)
        breaking = _transition(breaking, rows, cycle_size)
    return (
        _event(sham, anchor + 3, cycle_size),
        _event(breaking, anchor + 3, cycle_size),
    )


def _signed_offset(locus: int, origin: int, cycle_size: int) -> int:
    offset = (locus - origin) % cycle_size
    return offset if offset <= cycle_size // 2 else offset - cycle_size


def _state_hex(state: int, cycle_size: int) -> str:
    _require_state(state, cycle_size)
    return f"{state:0{(cycle_size + 3) // 4}x}"


def _independent_assessment(
    seeded: int,
    baseline: int,
    rows: tuple[str, ...],
    layer: int,
    *,
    origin: int,
    cycle_size: int,
) -> dict[str, Any]:
    """Independent spelling of the four nested detector stages."""

    _require_state(seeded, cycle_size)
    _require_state(baseline, cycle_size)
    if type(layer) is not int or layer < 1:
        raise IndependentVerificationError("detector layer must be positive")
    if type(origin) is not int or not 0 <= origin < cycle_size:
        raise IndependentVerificationError("origin must be a cycle locus")
    mask = _mask(cycle_size)
    role_anchors = _role_mask_unchecked(
        seeded,
        baseline,
        cycle_size,
        mask,
    ) & _eligible_anchor_mask(origin, layer, cycle_size)
    if role_anchors == 0:
        return {
            "first_role": None,
            "first_successor": None,
            "first_intervention_eligible": None,
            "first_complete_pass": None,
        }

    next_seeded = _transition(seeded, rows, cycle_size)
    next_baseline = _transition(baseline, rows, cycle_size)
    successor_roles = _role_mask_unchecked(
        next_seeded,
        next_baseline,
        cycle_size,
        mask,
    ) & _eligible_anchor_mask(origin, layer + 1, cycle_size)
    endpoint_cone = _cone_mask(origin, layer + 2, cycle_size)
    first_role: Optional[dict[str, int]] = None
    first_successor: Optional[dict[str, int]] = None
    first_eligible: Optional[dict[str, int]] = None
    for anchor in _ordered_anchors(origin, cycle_size):
        if not role_anchors & (1 << anchor):
            continue
        if first_role is None:
            first_role = {"layer": layer, "anchor": anchor}
        successor = None
        for displacement in (0, 1):
            candidate = (anchor + displacement) % cycle_size
            if successor_roles & (1 << candidate):
                successor = candidate
                break
        if successor is None:
            continue
        if first_successor is None:
            first_successor = {
                "layer": layer,
                "anchor": anchor,
                "successor_anchor": successor,
            }
        endpoint = (anchor + 3) % cycle_size
        if not endpoint_cone & (1 << endpoint):
            continue
        if seeded & (1 << endpoint):
            continue
        if first_eligible is None:
            first_eligible = {
                "layer": layer,
                "anchor": anchor,
                "successor_anchor": successor,
            }
        sham, breaking = _outward_values(seeded, rows, anchor, cycle_size)
        if sham == breaking:
            continue
        return {
            "first_role": first_role,
            "first_successor": first_successor,
            "first_intervention_eligible": first_eligible,
            "first_complete_pass": {
                "layer": layer,
                "anchor": anchor,
                "signed_anchor": _signed_offset(anchor, origin, cycle_size),
                "successor_anchor": successor,
                "successor_displacement": (successor - anchor) % cycle_size,
                "sham_future": sham,
                "breaking_future": breaking,
                "seeded_state_hex": _state_hex(seeded, cycle_size),
                "baseline_state_hex": _state_hex(baseline, cycle_size),
            },
        }
    return {
        "first_role": first_role,
        "first_successor": first_successor,
        "first_intervention_eligible": first_eligible,
        "first_complete_pass": None,
    }


def _trace_domain(candidate: dict[str, Any]) -> bytes:
    identifier = candidate.get("candidate_id")
    if type(identifier) is not str or not identifier:
        raise IndependentVerificationError("candidate id is invalid")
    return f"{SEARCH_ID}\0{identifier}\0{_candidate_sha256(candidate)}".encode("ascii")


def _new_digest(candidate: dict[str, Any]) -> "hashlib._Hash":
    domain = _trace_domain(candidate)
    digest = hashlib.sha256()
    digest.update(TRACE_PREFIX)
    digest.update(len(domain).to_bytes(8, "big"))
    digest.update(domain)
    return digest


def _update_digest(
    digest: "hashlib._Hash",
    layer: int,
    seeded: int,
    baseline: int,
    cycle_size: int = PRIMARY_CYCLE_SIZE,
) -> None:
    layer_bytes = str(layer).encode("ascii")
    width = (cycle_size + 7) // 8
    digest.update(len(layer_bytes).to_bytes(8, "big"))
    digest.update(layer_bytes)
    digest.update(seeded.to_bytes(width, "big"))
    digest.update(baseline.to_bytes(width, "big"))


def _verify_covariance(
    previous: tuple[int, int],
    current: tuple[int, int],
    rows: tuple[str, ...],
) -> None:
    reflection_rows = _reflected_rows(rows)
    for prior_state, next_state in zip(previous, current):
        for offset in range(PRIMARY_CYCLE_SIZE):
            actual = _transition(
                _translate(prior_state, offset, PRIMARY_CYCLE_SIZE),
                rows,
                PRIMARY_CYCLE_SIZE,
            )
            expected = _translate(next_state, offset, PRIMARY_CYCLE_SIZE)
            if actual != expected:
                raise IndependentVerificationError("translation covariance replay failed")
        actual_reflection = _transition(
            _reflect(prior_state, PRIMARY_CYCLE_SIZE),
            reflection_rows,
            PRIMARY_CYCLE_SIZE,
        )
        if actual_reflection != _reflect(next_state, PRIMARY_CYCLE_SIZE):
            raise IndependentVerificationError("reflection covariance replay failed")


def _bounded_stage(value: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    return value if value is not None and value["layer"] <= FORMATION_HORIZON else None


def _pre_wrap_record(
    first_role: Optional[dict[str, Any]],
    first_successor: Optional[dict[str, Any]],
    first_eligible: Optional[dict[str, Any]],
    first_pass: Optional[dict[str, Any]],
) -> dict[str, Any]:
    role = _bounded_stage(first_role)
    successor = _bounded_stage(first_successor)
    eligible = _bounded_stage(first_eligible)
    complete = _bounded_stage(first_pass)
    return {
        "formation_horizon": FORMATION_HORIZON,
        "role_by_H29": role is not None,
        "successor_by_H29": successor is not None,
        "intervention_eligible_by_H29": eligible is not None,
        "pass_by_H29": complete is not None,
        "first_role": role,
        "first_successor": successor,
        "first_intervention_eligible": eligible,
        "first_complete_pass": complete,
    }


def _compact_size_pass(pass_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "layer": pass_record["layer"],
        "signed_anchor": pass_record["signed_anchor"],
        "successor_displacement": pass_record["successor_displacement"],
        "sham_future": pass_record["sham_future"],
        "breaking_future": pass_record["breaking_future"],
    }


def _size_control_record(
    rows: tuple[str, ...],
    primary_pass: dict[str, Any],
    cycle_size: int,
) -> dict[str, Any]:
    terminal = primary_pass["layer"]
    seeded = 1 << CANONICAL_ORIGIN
    baseline = 0
    if any(
        _role(seeded, baseline, anchor, cycle_size)
        for anchor in range(cycle_size)
    ):
        raise IndependentVerificationError("registered initial state already contains the role")
    first_pass: Optional[dict[str, Any]] = None
    for layer in range(1, terminal + 1):
        seeded = _transition(seeded, rows, cycle_size)
        baseline = _transition(baseline, rows, cycle_size)
        assessment = _independent_assessment(
            seeded,
            baseline,
            rows,
            layer,
            origin=CANONICAL_ORIGIN,
            cycle_size=cycle_size,
        )
        if first_pass is None and assessment["first_complete_pass"] is not None:
            first_pass = _compact_size_pass(assessment["first_complete_pass"])
    primary_compact = _compact_size_pass(primary_pass)
    matches = first_pass == primary_compact
    required = terminal <= FORMATION_HORIZON
    return {
        "cycle_size": cycle_size,
        "evaluated_through_layer": terminal,
        "first_complete_pass": first_pass,
        "matches_primary_witness": matches,
        "pre_wrap_agreement_required": required,
        "exact_pre_wrap_agreement": matches if required else None,
    }


def _verify_dynamic_candidate(
    record: dict[str, Any],
    candidate: dict[str, Any],
    rows: tuple[str, ...],
) -> None:
    last_layer = record.get("last_assessed_layer")
    if type(last_layer) is not int or not 1 <= last_layer <= MAX_LAYERS_PER_CANDIDATE:
        raise IndependentVerificationError("terminal layer is invalid")
    seeded = 1 << CANONICAL_ORIGIN
    baseline = 0
    if any(
        _role(seeded, baseline, anchor, PRIMARY_CYCLE_SIZE)
        for anchor in range(PRIMARY_CYCLE_SIZE)
    ):
        raise IndependentVerificationError("registered initial state already contains the role")
    digest = _new_digest(candidate)
    _update_digest(digest, 0, seeded, baseline)
    first_role = None
    first_successor = None
    first_eligible = None
    first_pass = None
    checkpoint: Optional[tuple[int, int]] = None
    checkpoint_layer: Optional[int] = None
    checkpoint_power = 1
    checkpoint_distance = 0
    first_checkpoint_repeat: Optional[tuple[int, int, int, int, int]] = None
    claimed_checkpoint_state: Optional[tuple[int, int]] = None
    recurrence = record.get("recurrence")
    claimed_checkpoint_layer = (
        recurrence.get("checkpoint_layer") if type(recurrence) is dict else None
    )

    for layer in range(1, last_layer + 1):
        previous = (seeded, baseline)
        seeded = _transition(seeded, rows, PRIMARY_CYCLE_SIZE)
        baseline = _transition(baseline, rows, PRIMARY_CYCLE_SIZE)
        current = (seeded, baseline)
        if layer <= SYMMETRY_AUDIT_LAST_LAYER:
            _verify_covariance(previous, current, rows)
        _update_digest(digest, layer, seeded, baseline)
        assessment = _independent_assessment(
            seeded,
            baseline,
            rows,
            layer,
            origin=CANONICAL_ORIGIN,
            cycle_size=PRIMARY_CYCLE_SIZE,
        )
        if first_role is None and assessment["first_role"] is not None:
            first_role = assessment["first_role"]
        if first_successor is None and assessment["first_successor"] is not None:
            first_successor = assessment["first_successor"]
        if first_eligible is None and assessment["first_intervention_eligible"] is not None:
            first_eligible = assessment["first_intervention_eligible"]
        if assessment["first_complete_pass"] is not None:
            first_pass = assessment["first_complete_pass"]
            if layer != last_layer:
                raise IndependentVerificationError("trace continued after first complete pass")
            continue

        if layer == PRIMARY_CONE_SATURATION_LAYER:
            checkpoint = current
            checkpoint_layer = layer
            checkpoint_power = 1
            checkpoint_distance = 0
        elif layer > PRIMARY_CONE_SATURATION_LAYER:
            if checkpoint is None or checkpoint_layer is None:
                raise IndependentVerificationError("checkpoint schedule was not initialized")
            checkpoint_distance += 1
            if current == checkpoint:
                if first_checkpoint_repeat is None:
                    first_checkpoint_repeat = (
                        checkpoint_layer,
                        layer,
                        checkpoint_distance,
                        seeded,
                        baseline,
                    )
                if layer != last_layer:
                    raise IndependentVerificationError("trace continued after checkpoint equality")
            elif checkpoint_distance == checkpoint_power:
                checkpoint = current
                checkpoint_layer = layer
                checkpoint_power *= 2
                checkpoint_distance = 0
        if layer == claimed_checkpoint_layer:
            claimed_checkpoint_state = current

    if record.get("trace_sha256") != digest.hexdigest():
        raise IndependentVerificationError("trace digest differs under independent replay")
    comparisons = (
        ("first role", record.get("first_role"), first_role),
        ("first successor", record.get("first_successor"), first_successor),
        (
            "first intervention eligibility",
            record.get("first_intervention_eligible"),
            first_eligible,
        ),
        ("first complete pass", record.get("first_complete_pass"), first_pass),
    )
    for label, claimed, reproduced in comparisons:
        if claimed != reproduced:
            raise IndependentVerificationError(f"{label} differs under independent replay")
    expected_pre = _pre_wrap_record(first_role, first_successor, first_eligible, first_pass)
    if record.get("pre_wrap_classification") != expected_pre:
        raise IndependentVerificationError("pre-wrap classification differs under replay")
    pass_by_horizon = first_pass is not None and first_pass["layer"] <= FORMATION_HORIZON
    if record.get("pass_by_H29") is not pass_by_horizon:
        raise IndependentVerificationError("bounded pass flag differs under replay")
    expected_bounded = "pass_by_H29" if pass_by_horizon else "right_censored_T_proto_gt_29"
    if record.get("bounded_status") != expected_bounded:
        raise IndependentVerificationError("bounded status differs under replay")

    audit = record.get("transition_symmetry_audit")
    expected_audit = {
        "translation_offsets": list(range(PRIMARY_CYCLE_SIZE)),
        "last_audited_layer": min(last_layer, SYMMETRY_AUDIT_LAST_LAYER),
        "translation_covariance_exact": True,
        "reflection_covariance_exact": True,
        "reflected_production_rows": list(_reflected_rows(rows)),
    }
    if audit != expected_audit:
        raise IndependentVerificationError("symmetry audit record differs")

    status = record.get("evaluation_status")
    if status == "exact_pass_on_fixed_orbit":
        if first_pass is None or record.get("t_proto_exact") != first_pass["layer"]:
            raise IndependentVerificationError("exact pass terminal record differs")
        expected_controls = [
            _size_control_record(rows, first_pass, cycle_size)
            for cycle_size in EMBEDDING_CYCLE_SIZES
        ]
        if record.get("cross_size_controls") != expected_controls:
            raise IndependentVerificationError("cross-size controls differ under replay")
        if pass_by_horizon and any(
            control["exact_pre_wrap_agreement"] is not True
            for control in expected_controls
        ):
            raise IndependentVerificationError("mandatory pre-wrap embedding failed")
        expected_localized = pass_by_horizon and all(
            control["exact_pre_wrap_agreement"] is True
            for control in expected_controls
        )
        if record.get("localized_interpretation") is not expected_localized:
            raise IndependentVerificationError("localized classification differs")
    elif status == "recurrence_excluded_on_fixed_orbit":
        if first_pass is not None or type(recurrence) is not dict:
            raise IndependentVerificationError("recurrence terminal claim conflicts with replay")
        if claimed_checkpoint_state is None:
            raise IndependentVerificationError("claimed checkpoint state was not visited")
        if claimed_checkpoint_state != (seeded, baseline):
            raise IndependentVerificationError("claimed recurrence states are unequal")
        expected_repeat = (
            recurrence["checkpoint_layer"],
            recurrence["repeat_layer"],
            recurrence["period"],
            seeded,
            baseline,
        )
        if first_checkpoint_repeat != expected_repeat:
            raise IndependentVerificationError("checkpoint recurrence differs under replay")
        state = {
            "seeded_state_hex": _state_hex(seeded, PRIMARY_CYCLE_SIZE),
            "baseline_state_hex": _state_hex(baseline, PRIMARY_CYCLE_SIZE),
        }
        if recurrence.get("checkpoint_state") != state or recurrence.get("repeat_state") != state:
            raise IndependentVerificationError("recurrence state encoding differs")
        if record.get("cross_size_controls") != [] or record.get("localized_interpretation") is not False:
            raise IndependentVerificationError("nonpass contains pass-only controls")
    elif status == "resource_censored_before_recurrence":
        if first_pass is not None or first_checkpoint_repeat is not None:
            raise IndependentVerificationError("resource censor missed a terminal event")
        if last_layer != MAX_LAYERS_PER_CANDIDATE:
            raise IndependentVerificationError("resource censor stopped before the fixed ceiling")
        if record.get("cross_size_controls") != [] or record.get("localized_interpretation") is not False:
            raise IndependentVerificationError("resource censor contains pass-only controls")
    else:
        raise IndependentVerificationError("unknown dynamic terminal status")


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    dynamic = results[1:]
    stage_counts = {
        "role": sum(row["pre_wrap_classification"]["role_by_H29"] for row in dynamic),
        "successor": sum(
            row["pre_wrap_classification"]["successor_by_H29"] for row in dynamic
        ),
        "intervention_eligible": sum(
            row["pre_wrap_classification"]["intervention_eligible_by_H29"]
            for row in dynamic
        ),
        "complete_pass": sum(row["pass_by_H29"] for row in dynamic),
    }
    exact = [row for row in dynamic if row["evaluation_status"] == "exact_pass_on_fixed_orbit"]
    resource = [row for row in dynamic if row["evaluation_status"] == "resource_censored_before_recurrence"]
    localized = [row["candidate_id"] for row in dynamic if row["localized_interpretation"]]
    finite = [
        row["candidate_id"]
        for row in exact
        if row["t_proto_exact"] > FORMATION_HORIZON
    ]
    if stage_counts["successor"] == 0:
        mechanism = "pre_wrap_succession_repair_falsified"
    elif stage_counts["complete_pass"] == 0:
        mechanism = "succession_bottleneck_moved_without_pre_wrap_proto_object"
    else:
        mechanism = "one_or_more_pre_wrap_successors"
    construction = (
        "localized_development_falsification_survived"
        if localized
        else "no_localized_pre_wrap_construction"
    )
    if exact:
        completion = (
            "complete_all_candidate_endpoints_resolved"
            if not resource
            else "existential_pass_with_resource_censoring"
        )
        conclusion = "one_or_more_exact_passes"
    elif resource:
        completion = "incomplete_resource_censored"
        conclusion = "resource_censored_incomplete"
    else:
        completion = "complete_all_candidate_endpoints_resolved"
        conclusion = "all_dynamic_candidates_recurrence_excluded"
    ranking = "no_exact_passer"
    winners: list[str] = []
    if exact:
        best_law = min(row["atomic_n_l"] for row in exact)
        blocked = any(
            row["evaluation_status"] == "resource_censored_before_recurrence"
            and row["atomic_n_l"] < best_law
            for row in dynamic
        )
        if blocked:
            ranking = "blocked_by_lower_shell_resource_censoring"
        else:
            shell = [row for row in exact if row["atomic_n_l"] == best_law]
            best_time = min(row["t_proto_exact"] for row in shell)
            winners = [row["candidate_id"] for row in shell if row["t_proto_exact"] == best_time]
            ranking = "resolved_within_frozen_family"
    return {
        "completion_status": completion,
        "exact_family_conclusion": conclusion,
        "pre_wrap_mechanism_conclusion": mechanism,
        "pre_wrap_construction_conclusion": construction,
        "pre_wrap_stage_counts": stage_counts,
        "exact_pass_candidate_ids": [row["candidate_id"] for row in exact],
        "localized_candidate_ids": localized,
        "finite_ring_exposed_candidate_ids": finite,
        "minimum_law_ranking_status": ranking,
        "minimum_law_winner_candidate_ids": winners,
    }


def verify_ledger_independently(
    ledger: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
    *,
    worker_processes: int = 1,
) -> None:
    """Recompute all 255 canonical joint orbits and conditional size controls."""

    canonical_candidates = tuple(candidates)
    rows_by_candidate = _expected_rows()
    results = ledger.get("candidate_results")
    if (
        len(canonical_candidates) != CANDIDATE_COUNT
        or len(rows_by_candidate) != CANDIDATE_COUNT
        or type(results) is not list
        or len(results) != CANDIDATE_COUNT
    ):
        raise IndependentVerificationError("candidate allocation mismatch")
    fixed = {
        "base_contract_version": BASE_CONTRACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "run_id": RUN_ID,
        "grammar_id": GRAMMAR_ID,
        "detector": DETECTOR_ID,
        "data_class": DATA_CLASS,
        "endpoint": RESULT_ENDPOINT,
        "primary_cycle_size": PRIMARY_CYCLE_SIZE,
        "embedding_cycle_sizes": list(EMBEDDING_CYCLE_SIZES),
        "canonical_origin": CANONICAL_ORIGIN,
        "formation_horizon": FORMATION_HORIZON,
        "causal_endpoint_lag": CAUSAL_ENDPOINT_LAG,
        "cone_saturation_layer": PRIMARY_CONE_SATURATION_LAYER,
        "max_layers_per_candidate": MAX_LAYERS_PER_CANDIDATE,
        "all_nonempty_candidates_processed": True,
        "shell_stopping_used": False,
    }
    for key, expected in fixed.items():
        if ledger.get(key) != expected or type(ledger.get(key)) is not type(expected):
            raise IndependentVerificationError(f"ledger {key} mismatch")
    expected_capacity = {
        "normalized_n_p": 2,
        "input_ports": ["predecessor", "self", "successor"],
        "relation_incidence_reads_per_site": 2,
        "local_signature_fan_in": 3,
        "truth_table_row_capacity": 8,
        "scheduler": "synchronous_atomic_layer",
        "seed": "one_event_at_origin_0",
        "comparator": "all_zero_evolved_under_same_rule",
        "topology": "oriented_periodic_cycle",
    }
    expected_allocation = {
        "candidate_count": CANDIDATE_COUNT,
        "dynamic_candidate_count": DYNAMIC_CANDIDATE_COUNT,
        "shell_sizes": list(SHELL_SIZES),
        "enumeration_order": "increasing_N_L_then_lexicographic_signature_tuple",
    }
    if ledger.get("primitive_capacity") != expected_capacity:
        raise IndependentVerificationError("ledger primitive capacity mismatch")
    if ledger.get("candidate_allocation") != expected_allocation:
        raise IndependentVerificationError("ledger candidate allocation mismatch")
    if ledger.get("trace_digest_encoding") != (
        "sha256_domain_separated_decimal_length_layer_fixed_width_seeded_"
        "fixed_width_comparator_including_layer_0"
    ):
        raise IndependentVerificationError("ledger trace encoding mismatch")
    expected_shells = tuple(
        sum(1 for rows in rows_by_candidate if len(rows) == count)
        for count in range(9)
    )
    if expected_shells != SHELL_SIZES:
        raise IndependentVerificationError("independent enumerator shell sizes differ")
    row_family = set(rows_by_candidate)
    if any(_reflected_rows(rows) not in row_family for rows in rows_by_candidate):
        raise IndependentVerificationError("candidate family is not reflection closed")
    if type(worker_processes) is not int or worker_processes not in (
        1,
        REGISTERED_WORKER_PROCESSES,
    ):
        raise IndependentVerificationError("verification worker allocation is not frozen")

    replay_payloads: list[
        tuple[dict[str, Any], dict[str, Any], tuple[str, ...]]
    ] = []
    for index, (candidate, rows, record) in enumerate(
        zip(canonical_candidates, rows_by_candidate, results)
    ):
        if candidate.get("candidate_id") != _candidate_id(rows):
            raise IndependentVerificationError("candidate manifest order mismatch")
        if record.get("candidate_id") != _candidate_id(rows):
            raise IndependentVerificationError("result candidate order mismatch")
        if record.get("candidate_sha256") != _candidate_sha256(candidate):
            raise IndependentVerificationError("result candidate hash mismatch")
        if record.get("production_rows") != list(rows):
            raise IndependentVerificationError("result production rows mismatch")
        if (
            type(record.get("atomic_n_l")) is not int
            or record.get("atomic_n_l") != len(rows)
            or type(record.get("wolfram_rule_number")) is not int
            or record.get("wolfram_rule_number") != _wolfram_code(rows)
        ):
            raise IndependentVerificationError("result complexity metadata mismatch")
        if index == 0:
            if record.get("evaluation_status") != "analytically_excluded":
                raise IndependentVerificationError("zero-row candidate was not excluded")
            continue
        replay_payloads.append((record, candidate, rows))

    if worker_processes == 1:
        for payload in replay_payloads:
            _independent_verification_payload(payload)
    else:
        try:
            with ProcessPoolExecutor(
                max_workers=REGISTERED_WORKER_PROCESSES,
                mp_context=get_context("spawn"),
            ) as executor:
                completions = tuple(
                    executor.map(
                        _independent_verification_payload,
                        replay_payloads,
                        chunksize=1,
                    )
                )
        except IndependentVerificationError:
            raise
        except Exception as exc:
            raise IndependentVerificationError(
                "independent verification worker pool failed"
            ) from exc
        if len(completions) != DYNAMIC_CANDIDATE_COUNT or any(
            completion is not None for completion in completions
        ):
            raise IndependentVerificationError(
                "independent verification worker allocation mismatch"
            )

    expected_summary = _summarize(results)
    for key, expected in expected_summary.items():
        if ledger.get(key) != expected:
            raise IndependentVerificationError(f"aggregate {key} differs independently")
