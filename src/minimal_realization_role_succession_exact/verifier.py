"""Independent verification for MIR-ROLE-SUCCESSION-EXACT-001.

The static certificate is recomputed as a Boolean algebraic-normal-form
polynomial rather than the runner's direct truth-table lookup.  Any dynamic
survivor is replayed with the separately expressed ANF transition and detector
from the already sealed parent verifier.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Optional

from src.minimal_realization_role_succession.manifest import read_jsonl as read_parent_candidates
from src.minimal_realization_role_succession.runner import strict_json_equal
from src.minimal_realization_role_succession.verifier import (
    _independent_assessment,
    _new_digest,
    _size_control_record,
    _state_hex,
    _transition,
    _update_digest,
)

from .local_impossibility import CERTIFICATE_VERSION
from .manifest import load_and_validate_parent, validate_continuation_manifest
from .protocol import (
    CANONICAL_ORIGIN,
    CONE_SATURATION_LAYER,
    EMBEDDING_CYCLE_SIZES,
    PARENT_RESOURCE_BOUNDARY,
    PRIMARY_CYCLE_SIZE,
)
from .runner import validate_result_ledger


class ExactIndependentVerificationError(ValueError):
    pass


SIGNATURES = tuple(f"{value:03b}" for value in range(8))
OFFSETS = tuple(range(-2, 6))
ROLE_OFFSETS = (-1, 0, 1, 2)
ROLE_PATTERN = (0, 1, 1, 0)


@lru_cache(maxsize=256)
def _anf_coefficients(rows: tuple[str, ...]) -> tuple[int, ...]:
    if tuple(signature for signature in SIGNATURES if signature in set(rows)) != rows:
        raise ExactIndependentVerificationError("certificate rows are not canonical")
    coefficients = [int(f"{index:03b}" in rows) for index in range(8)]
    for variable in (1, 2, 4):
        for monomial in range(8):
            if monomial & variable:
                coefficients[monomial] ^= coefficients[monomial ^ variable]
    return tuple(coefficients)


def _anf_bit(rows: tuple[str, ...], left: int, center: int, right: int) -> int:
    inputs = (right, center, left)
    output = 0
    for monomial, coefficient in enumerate(_anf_coefficients(rows)):
        if not coefficient:
            continue
        term = 1
        for bit_index, value in enumerate(inputs):
            if monomial & (1 << bit_index):
                term &= value
        output ^= term
    return output


def _next_bit(rows: tuple[str, ...], state: dict[int, int], offset: int) -> int:
    return _anf_bit(rows, state[offset - 1], state[offset], state[offset + 1])


def _endpoint(
    rows: tuple[str, ...],
    formation: dict[int, int],
    arm: tuple[int, int, int],
) -> int:
    state = dict(formation)
    state.update(zip((0, 1, 2), arm))
    first = {offset: _next_bit(rows, state, offset) for offset in (2, 3, 4)}
    return _anf_bit(rows, first[2], first[3], first[4])


def _identity(context: dict[str, Any]) -> dict[str, Any]:
    return {"context_id": context["context_id"], "bitstring": context["bitstring"]}


def independent_local_certificate(rows: Iterable[str]) -> dict[str, Any]:
    selected = set(rows)
    canonical = tuple(signature for signature in SIGNATURES if signature in selected)
    if selected - set(SIGNATURES):
        raise ExactIndependentVerificationError("unknown production row")
    next_comparator = _anf_bit(canonical, 0, 0, 0)
    obstruction = next_comparator == 1
    contexts: list[dict[str, Any]] = []
    for far_left in (0, 1):
        for far_right in (0, 1):
            for second_far_right in (0, 1):
                formation = {
                    -2: far_left,
                    -1: 0,
                    0: 1,
                    1: 1,
                    2: 0,
                    3: 0,
                    4: far_right,
                    5: second_far_right,
                }
                bitstring = "".join(str(formation[offset]) for offset in OFFSETS)
                raw = []
                for displacement in (0, 1):
                    pattern = tuple(
                        _next_bit(canonical, formation, displacement + relative)
                        for relative in ROLE_OFFSETS
                    )
                    if pattern == ROLE_PATTERN:
                        raw.append(displacement)
                attributed = [] if obstruction else list(raw)
                sham = _endpoint(canonical, formation, (0, 1, 1))
                breaking = _endpoint(canonical, formation, (1, 0, 1))
                causal = sham != breaking
                joint = list(attributed) if causal else []
                contexts.append(
                    {
                        "context_id": int(bitstring, 2),
                        "bitstring": bitstring,
                        "bits_by_offset": {
                            str(offset): formation[offset] for offset in OFFSETS
                        },
                        "raw_seeded_successor_displacements": raw,
                        "attributed_successor_displacements": attributed,
                        "raw_seeded_succession_capable": bool(raw),
                        "succession_capable": bool(attributed),
                        "sham_endpoint_bit": sham,
                        "breaking_endpoint_bit": breaking,
                        "causal_capable": causal,
                        "joint_pass_capable_displacements": joint,
                        "joint_pass_capable": bool(joint),
                    }
                )
    raw_contexts = [_identity(c) for c in contexts if c["raw_seeded_succession_capable"]]
    successor_contexts = [_identity(c) for c in contexts if c["succession_capable"]]
    causal_contexts = [_identity(c) for c in contexts if c["causal_capable"]]
    joint_contexts = [_identity(c) for c in contexts if c["joint_pass_capable"]]
    unreachable = not joint_contexts
    route: Optional[str] = None
    statement: Optional[str] = None
    if unreachable and obstruction:
        route = "homogeneous_comparator_obstruction"
        statement = (
            "An attributed formation role forces the homogeneous comparator "
            "bit to 0; selected row 000 maps it to 1 at the next layer, "
            "blocking attribution of every raw seeded successor."
        )
    elif unreachable:
        route = "empty_local_pass_context_set"
        statement = (
            "None of the eight exhaustive radius-one contexts jointly has "
            "an attributed next-layer successor and a two-layer matched-arm "
            "endpoint difference."
        )
    return {
        "certificate_version": CERTIFICATE_VERSION,
        "production_rows": list(canonical),
        "rule_number": sum(1 << int(signature, 2) for signature in canonical),
        "context_offsets": list(OFFSETS),
        "fixed_role_offsets": list(ROLE_OFFSETS),
        "fixed_role_pattern": list(ROLE_PATTERN),
        "endpoint_guard_offset": 3,
        "endpoint_guard_value": 0,
        "successor_displacements": [0, 1],
        "formation_comparator_bit": 0,
        "next_comparator_bit": next_comparator,
        "comparator_obstruction": obstruction,
        "proof_route": route,
        "proof_statement": statement,
        "symbolically_unreachable": unreachable,
        "context_universe": contexts,
        "raw_seeded_succession_capable_contexts": raw_contexts,
        "succession_capable_contexts": successor_contexts,
        "causal_capable_contexts": causal_contexts,
        "joint_pass_capable_contexts": joint_contexts,
    }


def _independent_dynamic(
    continuation: dict[str, Any],
    parent_record: dict[str, Any],
    parent_candidate: dict[str, Any],
    claimed: dict[str, Any],
) -> None:
    terminal = claimed.get("last_assessed_layer")
    if type(terminal) is not int or terminal <= PARENT_RESOURCE_BOUNDARY:
        raise ExactIndependentVerificationError("dynamic terminal layer is invalid")
    rows = tuple(continuation["production_rows"])
    seeded = 1 << CANONICAL_ORIGIN
    baseline = 0
    digest = _new_digest(parent_candidate)
    _update_digest(digest, 0, seeded, baseline)
    checkpoint: Optional[tuple[int, int]] = None
    checkpoint_layer: Optional[int] = None
    checkpoint_power = 1
    checkpoint_distance = 0
    first_role = first_successor = first_eligible = first_pass = None
    boundary_state: Optional[tuple[int, int]] = None
    reproduced_recurrence = None
    for layer in range(1, terminal + 1):
        seeded = _transition(seeded, rows, PRIMARY_CYCLE_SIZE)
        baseline = _transition(baseline, rows, PRIMARY_CYCLE_SIZE)
        current = (seeded, baseline)
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
            if layer != terminal:
                raise ExactIndependentVerificationError("dynamic trace continued after pass")
        else:
            if layer == CONE_SATURATION_LAYER:
                checkpoint = current
                checkpoint_layer = layer
                checkpoint_power = 1
                checkpoint_distance = 0
            elif layer > CONE_SATURATION_LAYER:
                if checkpoint is None or checkpoint_layer is None:
                    raise ExactIndependentVerificationError("checkpoint was not initialized")
                checkpoint_distance += 1
                if current == checkpoint:
                    if layer != terminal:
                        raise ExactIndependentVerificationError(
                            "dynamic trace continued after recurrence"
                        )
                    state = {
                        "seeded_state_hex": _state_hex(seeded, PRIMARY_CYCLE_SIZE),
                        "comparator_state_hex": _state_hex(baseline, PRIMARY_CYCLE_SIZE),
                    }
                    reproduced_recurrence = {
                        "cone_saturation_layer": CONE_SATURATION_LAYER,
                        "checkpoint_layer": checkpoint_layer,
                        "repeat_layer": layer,
                        "period": checkpoint_distance,
                        "checkpoint_state": dict(state),
                        "repeat_state": dict(state),
                        "exact_full_state_equality": True,
                    }
                elif checkpoint_distance == checkpoint_power:
                    checkpoint = current
                    checkpoint_layer = layer
                    checkpoint_power *= 2
                    checkpoint_distance = 0
        if layer == PARENT_RESOURCE_BOUNDARY:
            boundary_state = current
            prefix = claimed.get("prefix_replay")
            expected_prefix = {
                "boundary_layer": PARENT_RESOURCE_BOUNDARY,
                "parent_trace_sha256": parent_record["trace_sha256"],
                "exact_match": True,
                "boundary_seeded_state_hex": _state_hex(seeded, PRIMARY_CYCLE_SIZE),
                "boundary_comparator_state_hex": _state_hex(baseline, PRIMARY_CYCLE_SIZE),
                "brent_checkpoint_layer": checkpoint_layer,
                "brent_checkpoint_seeded_state_hex": _state_hex(
                    int(checkpoint[0]), PRIMARY_CYCLE_SIZE
                ),
                "brent_checkpoint_comparator_state_hex": _state_hex(
                    int(checkpoint[1]), PRIMARY_CYCLE_SIZE
                ),
                "brent_power": checkpoint_power,
                "brent_distance": checkpoint_distance,
            }
            if digest.copy().hexdigest() != parent_record["trace_sha256"]:
                raise ExactIndependentVerificationError("parent prefix trace differs")
            if not strict_json_equal(prefix, expected_prefix):
                raise ExactIndependentVerificationError("prefix certificate differs")
    if boundary_state is None:
        raise ExactIndependentVerificationError("parent boundary was not reached")
    if first_pass is None and reproduced_recurrence is None:
        raise ExactIndependentVerificationError("dynamic trace lacks an exact terminal")
    if first_pass is not None and reproduced_recurrence is not None:
        raise ExactIndependentVerificationError("dynamic trace has two terminal events")
    expected = {
        "classification": (
            "exact_pass_on_fixed_orbit"
            if first_pass is not None
            else "recurrence_excluded_on_fixed_orbit"
        ),
        "prefix_replay": claimed["prefix_replay"],
        "last_assessed_layer": terminal,
        "first_role": first_role,
        "first_successor": first_successor,
        "first_intervention_eligible": first_eligible,
        "first_complete_pass": first_pass,
        "recurrence": reproduced_recurrence,
        "full_trace_sha256": digest.hexdigest(),
        "cross_size_controls": (
            [
                _size_control_record(rows, first_pass, cycle_size)
                for cycle_size in EMBEDDING_CYCLE_SIZES
            ]
            if first_pass is not None
            else []
        ),
    }
    if not strict_json_equal(claimed, expected):
        raise ExactIndependentVerificationError("dynamic continuation differs under replay")


def verify_ledger_independently(
    root: Path,
    ledger: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
) -> None:
    parent = load_and_validate_parent(root)
    ordered = tuple(candidates)
    validate_continuation_manifest(ordered, parent)
    validate_result_ledger(ledger, ordered, parent)
    parent_candidate_binding = parent["candidate_manifest"]
    parent_candidates = read_parent_candidates(root / parent_candidate_binding["path"])
    parent_results = parent["candidate_results"]
    for continuation, record in zip(ordered, ledger["candidate_results"]):
        expected_certificate = independent_local_certificate(
            tuple(continuation["production_rows"])
        )
        if not strict_json_equal(record["symbolic_certificate"], expected_certificate):
            raise ExactIndependentVerificationError(
                f"{continuation['candidate_id']}: symbolic certificate differs under ANF replay"
            )
        if record["classification"] == "symbolically_unreachable":
            if expected_certificate["joint_pass_capable_contexts"]:
                raise ExactIndependentVerificationError("false symbolic exclusion")
            continue
        index = continuation["parent_candidate_index"]
        _independent_dynamic(
            continuation,
            parent_results[index],
            parent_candidates[index],
            record["dynamic_continuation"],
        )
