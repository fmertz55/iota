from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


FORBIDDEN_LAW_WORDS = re.compile(r"\b(and|but|or|else|otherwise)\b", re.IGNORECASE)
ID_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._-]*$")
PRIMITIVE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
LAW_ID_PATTERN = re.compile(r"^L[1-9][0-9]*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REFERENCE_SIGNATURES = ("00", "01", "10", "11")
V02_SPEC_DIR = Path(__file__).resolve().parents[1] / "specs/icp_minimal_realization/v0.2-draft"


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_object(value: Any, context: str) -> dict[str, Any]:
    require(type(value) is dict, f"{context}: must be an object")
    return value


def require_list(value: Any, context: str) -> list[Any]:
    require(type(value) is list, f"{context}: must be an array")
    return value


def require_string(value: Any, context: str, *, nonempty: bool = True) -> str:
    require(type(value) is str, f"{context}: must be a string")
    if nonempty:
        require(bool(value.strip()), f"{context}: must not be empty")
    return value


def require_integer(value: Any, context: str, *, minimum: int = 0) -> int:
    require(type(value) is int, f"{context}: must be an integer")
    require(value >= minimum, f"{context}: must be >= {minimum}")
    return value


def require_boolean(value: Any, context: str) -> bool:
    require(type(value) is bool, f"{context}: must be a boolean")
    return value


def require_exact_keys(
    value: dict[str, Any],
    required: Iterable[str],
    context: str,
    *,
    optional: Iterable[str] = (),
) -> None:
    required_set = set(required)
    allowed = required_set | set(optional)
    keys = set(value)
    missing = sorted(required_set - keys)
    extra = sorted(keys - allowed)
    require(not missing, f"{context}: missing keys {missing}")
    require(not extra, f"{context}: unexpected keys {extra}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValidationError(f"non-finite JSON number {value!r} is forbidden")


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(
                handle,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(str(exc)) from exc
    return require_object(data, str(path))


def _validate_reference(value: Any, context: str, expected_ref: str) -> str:
    reference = require_object(value, context)
    require_exact_keys(reference, {"ref", "sha256"}, context)
    require(reference["ref"] == expected_ref, f"{context}: expected ref {expected_ref!r}")
    digest = require_string(reference["sha256"], f"{context}.sha256")
    require(
        digest == "UNSEALED" or bool(SHA256_PATTERN.fullmatch(digest)),
        f"{context}.sha256: must be UNSEALED or 64 lowercase hexadecimal characters",
    )
    return digest


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_bound_digest(digest: str, filename: str, context: str) -> None:
    if digest == "UNSEALED":
        return
    try:
        actual = _sha256_file(V02_SPEC_DIR / filename)
    except OSError as exc:
        raise ValidationError(f"{context}: cannot resolve reference {filename!r}: {exc}") from exc
    require(digest == actual, f"{context}: digest does not match {filename!r}")


def _validate_v01(data: dict[str, Any], source: Path) -> tuple[int, int]:
    context = str(source)
    root_keys = {
        "contract_version",
        "candidate_id",
        "status",
        "primitive_accounting",
        "primitives",
        "laws",
        "clock",
        "substrate",
        "initial_condition",
        "proto_object_detector",
        "maps",
        "randomness",
        "data_class",
    }
    require_exact_keys(data, root_keys, context, optional={"exclusion_reason"})
    require(data["contract_version"] == "0.1-draft", f"{source}: wrong contract version")
    candidate_id = require_string(data["candidate_id"], f"{context}.candidate_id")
    require(bool(ID_PATTERN.fullmatch(candidate_id)), f"{source}: invalid candidate_id")
    require(data["status"] in {"development", "frozen", "analytically_excluded"}, f"{source}: invalid status")
    require(data["data_class"] in {"development", "held_out"}, f"{source}: invalid data_class")

    primitives = require_list(data["primitives"], f"{context}.primitives")
    primitive_ids: list[str] = []
    relation_count = 0
    exogenous_count = 0
    for index, raw_primitive in enumerate(primitives):
        p_context = f"{context}.primitives[{index}]"
        primitive = require_object(raw_primitive, p_context)
        require_exact_keys(primitive, {"id", "scope", "alphabet", "description"}, p_context)
        primitive_id = require_string(primitive["id"], f"{p_context}.id")
        require(bool(PRIMITIVE_ID_PATTERN.fullmatch(primitive_id)), f"{p_context}: invalid id")
        require(primitive["scope"] in {"dynamic", "relation", "exogenous"}, f"{p_context}: invalid scope")
        alphabet = require_list(primitive["alphabet"], f"{p_context}.alphabet")
        require(
            len(alphabet) == 2 and type(alphabet[0]) is int and type(alphabet[1]) is int and alphabet == [0, 1],
            f"{p_context}: primitive alphabet must be integer [0, 1]",
        )
        require_string(primitive["description"], f"{p_context}.description")
        primitive_ids.append(primitive_id)
        relation_count += int(primitive["scope"] == "relation")
        exogenous_count += int(primitive["scope"] == "exogenous")
    require(len(primitive_ids) == len(set(primitive_ids)), f"{source}: duplicate primitive id")

    accounting = require_object(data["primitive_accounting"], f"{context}.primitive_accounting")
    accounting_keys = {
        "normalized_n_p",
        "kind_count",
        "seed_nonquiescent_instances",
        "relation_kind_count",
        "candidate_supplied_bits",
    }
    require_exact_keys(accounting, accounting_keys, f"{context}.primitive_accounting")
    for key in accounting_keys:
        require_integer(accounting[key], f"{context}.primitive_accounting.{key}")
    require(accounting["kind_count"] == len(primitives), f"{source}: kind_count mismatch")
    require(accounting["relation_kind_count"] == relation_count, f"{source}: relation_kind_count mismatch")
    expected_n_p = len(primitives) + accounting["candidate_supplied_bits"]
    require(accounting["normalized_n_p"] == expected_n_p, f"{source}: normalized_n_p mismatch")

    laws = require_list(data["laws"], f"{context}.laws")
    law_ids: list[str] = []
    law_keys = {
        "id",
        "statement",
        "governed_degree",
        "local_input_signature",
        "next_state_effect",
        "duration_ticks",
        "branch_count",
        "write_count",
        "helper_references",
        "lookup_entries",
        "uses_continuant",
        "atomicity_attestation",
    }
    for index, raw_law in enumerate(laws):
        law_context = f"{context}.laws[{index}]"
        law = require_object(raw_law, law_context)
        require_exact_keys(law, law_keys, law_context)
        law_id = require_string(law["id"], f"{law_context}.id")
        require(bool(LAW_ID_PATTERN.fullmatch(law_id)), f"{law_context}: invalid law id")
        law_ids.append(law_id)
        for key in ("statement", "local_input_signature", "next_state_effect"):
            value = require_string(law[key], f"{law_context}.{key}")
            match = FORBIDDEN_LAW_WORDS.search(value)
            if match is not None:
                raise ValidationError(f"{law_context}.{key}: contains forbidden word {match.group(0)!r}")
        statement = law["statement"]
        require(statement.count(":=") == 1, f"{law_context}: statement must contain exactly one ':='")
        lhs, rhs = statement.split(":=", 1)
        require(bool(lhs.strip()) and bool(rhs.strip()), f"{law_context}: assignment sides must be nonempty")
        governed = require_string(law["governed_degree"], f"{law_context}.governed_degree")
        require(governed in primitive_ids, f"{law_context}: unknown governed degree")
        require_integer(law["duration_ticks"], f"{law_context}.duration_ticks")
        require(law["duration_ticks"] == 1, f"{law_context}: duration must be one tick")
        require_integer(law["branch_count"], f"{law_context}.branch_count")
        require(law["branch_count"] == 0, f"{law_context}: branches are compound")
        require_integer(law["write_count"], f"{law_context}.write_count")
        require(law["write_count"] == 1, f"{law_context}: law must write one degree")
        helpers = require_list(law["helper_references"], f"{law_context}.helper_references")
        require(helpers == [], f"{law_context}: helper reference is forbidden")
        require_integer(law["lookup_entries"], f"{law_context}.lookup_entries")
        require(law["lookup_entries"] == 0, f"{law_context}: lookup entries are compound")
        require_boolean(law["uses_continuant"], f"{law_context}.uses_continuant")
        require(law["uses_continuant"] is False, f"{law_context}: continuant is forbidden")
        require_boolean(law["atomicity_attestation"], f"{law_context}.atomicity_attestation")
        require(law["atomicity_attestation"] is True, f"{law_context}: atomicity not attested")
    require(len(law_ids) == len(set(law_ids)), f"{source}: duplicate law id")

    clock = require_object(data["clock"], f"{context}.clock")
    require_exact_keys(clock, {"tick_unit", "causal_layers_per_tick", "within_tick_cascade", "max_relation_hops_per_tick"}, f"{context}.clock")
    require(clock["tick_unit"] == "planck_time_provisional", f"{source}: wrong tick unit")
    require(type(clock["causal_layers_per_tick"]) is int and clock["causal_layers_per_tick"] == 1, f"{source}: tick must contain one causal layer")
    require(clock["within_tick_cascade"] is False, f"{source}: within-tick cascade is forbidden")
    require(type(clock["max_relation_hops_per_tick"]) is int and clock["max_relation_hops_per_tick"] == 1, f"{source}: tick exceeds one relation hop")

    substrate = require_object(data["substrate"], f"{context}.substrate")
    require_exact_keys(substrate, {"topology", "boundary", "scheduler"}, f"{context}.substrate")
    require(substrate["scheduler"] == "synchronous_atomic_layer", f"{source}: invalid scheduler")
    initial = require_object(data["initial_condition"], f"{context}.initial_condition")
    require_exact_keys(initial, {"description", "contains_proto_object", "description_bits"}, f"{context}.initial_condition")
    require(initial["contains_proto_object"] is False, f"{source}: initial state already contains a proto-object")
    require_integer(initial["description_bits"], f"{context}.initial_condition.description_bits")
    require(accounting["candidate_supplied_bits"] >= initial["description_bits"], f"{source}: initial description bits are uncharged")
    detector = require_object(data["proto_object_detector"], f"{context}.proto_object_detector")
    require_exact_keys(detector, {"version", "read_only", "minimum_persistence_ticks"}, f"{context}.proto_object_detector")
    require(detector["version"] == "0.1-draft", f"{source}: wrong detector version")
    require(detector["read_only"] is True, f"{source}: detector must be read-only")
    require(type(detector["minimum_persistence_ticks"]) is int and detector["minimum_persistence_ticks"] == 1, f"{source}: wrong persistence window")
    maps = require_object(data["maps"], f"{context}.maps")
    require_exact_keys(maps, {"initialization", "readout", "intervention"}, f"{context}.maps")
    for key in maps:
        require_string(maps[key], f"{context}.maps.{key}")
    randomness = require_object(data["randomness"], f"{context}.randomness")
    require_exact_keys(randomness, {"kind", "declared_law"}, f"{context}.randomness")
    require(randomness["kind"] in {"none", "finite_exogenous"}, f"{source}: invalid randomness kind")
    require_string(randomness["declared_law"], f"{context}.randomness.declared_law")
    if randomness["kind"] == "none":
        require(exogenous_count == 0, f"{source}: randomness none conflicts with exogenous primitive")
    else:
        require(exogenous_count > 0, f"{source}: finite_exogenous needs an exogenous primitive")
    if data["status"] == "analytically_excluded":
        require_string(data.get("exclusion_reason"), f"{context}.exclusion_reason")

    return accounting["normalized_n_p"], len(laws)


def _validate_v02(data: dict[str, Any], source: Path) -> tuple[int, int]:
    context = str(source)
    root_keys = {
        "contract_version",
        "grammar_id",
        "candidate_id",
        "status",
        "primitive_accounting",
        "primitives",
        "laws",
        "clock",
        "substrate",
        "initial_condition",
        "proto_object_detector",
        "maps",
        "randomness",
        "data_class",
    }
    require_exact_keys(data, root_keys, context, optional={"exclusion_reason"})
    require(data["contract_version"] == "0.2-draft", f"{source}: wrong contract version")
    require(data["grammar_id"] == "MIR-BOOLEAN-PRODUCTION-ROW-V0.2", f"{source}: wrong grammar id")
    candidate_id = require_string(data["candidate_id"], f"{context}.candidate_id")
    require(bool(ID_PATTERN.fullmatch(candidate_id)), f"{source}: invalid candidate_id")
    require(data["status"] in {"development", "frozen", "analytically_excluded"}, f"{source}: invalid status")
    require(data["data_class"] == "development", f"{source}: v0.2 has no held-out candidate runner")

    accounting = require_object(data["primitive_accounting"], f"{context}.primitive_accounting")
    expected_accounting = {
        "normalized_n_p": 2,
        "dynamic_kind_count": 1,
        "relation_kind_count": 1,
        "exogenous_kind_count": 0,
        "candidate_supplied_bits": 0,
        "seed_nonquiescent_instances": 1,
        "dynamic_storage_bits_per_layer": 64,
        "relation_instances": 64,
        "site_evaluations_per_layer": 64,
    }
    require_exact_keys(accounting, expected_accounting, f"{context}.primitive_accounting")
    for key, expected in expected_accounting.items():
        require(type(accounting[key]) is int, f"{context}.primitive_accounting.{key}: must be an integer")
        require(accounting[key] == expected, f"{context}.primitive_accounting.{key}: expected {expected}")
    derived_n_p = (
        accounting["dynamic_kind_count"]
        + accounting["relation_kind_count"]
        + accounting["exogenous_kind_count"]
        + accounting["candidate_supplied_bits"]
    )
    require(accounting["normalized_n_p"] == derived_n_p, f"{source}: normalized_n_p mismatch")

    primitives = require_list(data["primitives"], f"{context}.primitives")
    expected_primitives = [
        {"id": "event", "scope": "dynamic", "alphabet": [0, 1]},
        {"id": "predecessor", "scope": "relation", "alphabet": [0, 1]},
    ]
    require(primitives == expected_primitives, f"{source}: primitives must exactly match the frozen reference inventory")
    for index, primitive in enumerate(primitives):
        alphabet = primitive["alphabet"]
        require(type(alphabet[0]) is int and type(alphabet[1]) is int, f"{context}.primitives[{index}].alphabet: booleans are forbidden")

    laws = require_list(data["laws"], f"{context}.laws")
    require(len(laws) <= 4, f"{source}: at most four production rows are admissible")
    observed_signatures: list[str] = []
    law_keys = {"id", "operator", "signature", "governed_degree", "input_ports", "duration_ticks", "write_count"}
    for index, raw_law in enumerate(laws):
        law_context = f"{context}.laws[{index}]"
        law = require_object(raw_law, law_context)
        require_exact_keys(law, law_keys, law_context)
        signature = require_string(law["signature"], f"{law_context}.signature")
        require(signature in REFERENCE_SIGNATURES, f"{law_context}: invalid signature")
        require(law["id"] == f"L_{signature}", f"{law_context}: id must be L_{signature}")
        require(law["operator"] == "emit_one_if_signature", f"{law_context}: unregistered operator")
        require(law["governed_degree"] == "event", f"{law_context}: wrong governed degree")
        require(law["input_ports"] == ["self", "predecessor"], f"{law_context}: wrong input ports")
        require(type(law["duration_ticks"]) is int and law["duration_ticks"] == 1, f"{law_context}: duration must be one tick")
        require(type(law["write_count"]) is int and law["write_count"] == 1, f"{law_context}: write_count must be one")
        observed_signatures.append(signature)
    require(len(observed_signatures) == len(set(observed_signatures)), f"{source}: duplicate production signature")
    expected_order = sorted(observed_signatures, key=REFERENCE_SIGNATURES.index)
    require(observed_signatures == expected_order, f"{source}: laws are not in canonical signature order")

    clock = require_object(data["clock"], f"{context}.clock")
    expected_clock = {
        "tick_unit": "elementary_causal_layer",
        "causal_layers_per_tick": 1,
        "within_tick_cascade": False,
        "max_relation_hops_per_tick": 1,
    }
    require_exact_keys(clock, expected_clock, f"{context}.clock")
    require(clock == expected_clock, f"{source}: clock differs from the frozen elementary schedule")
    require(type(clock["causal_layers_per_tick"]) is int, f"{context}.clock.causal_layers_per_tick: booleans are forbidden")
    require(type(clock["within_tick_cascade"]) is bool, f"{context}.clock.within_tick_cascade: must be boolean")
    require(type(clock["max_relation_hops_per_tick"]) is int, f"{context}.clock.max_relation_hops_per_tick: booleans are forbidden")

    substrate_hash = _validate_reference(data["substrate"], f"{context}.substrate", "topology.json")
    _validate_bound_digest(substrate_hash, "topology.json", f"{context}.substrate.sha256")
    initial = require_object(data["initial_condition"], f"{context}.initial_condition")
    expected_initial = {
        "family": "single_active_translation",
        "canonical_origin": 0,
        "active_count": 1,
        "description_bits": 0,
        "contains_proto_object": False,
    }
    require_exact_keys(initial, expected_initial, f"{context}.initial_condition")
    require(initial == expected_initial, f"{source}: initial condition differs from the frozen family")
    require(type(initial["canonical_origin"]) is int, f"{context}.initial_condition.canonical_origin: must be integer")
    require(type(initial["active_count"]) is int, f"{context}.initial_condition.active_count: must be integer")
    require(type(initial["description_bits"]) is int, f"{context}.initial_condition.description_bits: must be integer")
    require(type(initial["contains_proto_object"]) is bool, f"{context}.initial_condition.contains_proto_object: must be boolean")
    require(accounting["candidate_supplied_bits"] >= initial["description_bits"], f"{source}: initial description bits are uncharged")

    detector = require_object(data["proto_object_detector"], f"{context}.proto_object_detector")
    require_exact_keys(detector, {"ref", "version", "sha256"}, f"{context}.proto_object_detector")
    require(detector["version"] == "0.2-draft", f"{source}: wrong detector version")
    detector_hash = _validate_reference(
        {"ref": detector["ref"], "sha256": detector["sha256"]},
        f"{context}.proto_object_detector",
        "proto_object_detector.json",
    )
    _validate_bound_digest(
        detector_hash,
        "proto_object_detector.json",
        f"{context}.proto_object_detector.sha256",
    )
    maps = require_object(data["maps"], f"{context}.maps")
    expected_maps = {
        "initialization": "single_active_translation",
        "readout": "MIR-ISOLATED-DYAD-OUTWARD-EFFECT-V0.2",
        "intervention": "matched_dyad_relocation",
    }
    require_exact_keys(maps, expected_maps, f"{context}.maps")
    require(maps == expected_maps, f"{source}: maps differ from the frozen reference maps")
    randomness = require_object(data["randomness"], f"{context}.randomness")
    expected_randomness = {"kind": "none", "exogenous_channel_count": 0}
    require_exact_keys(randomness, expected_randomness, f"{context}.randomness")
    require(randomness == expected_randomness, f"{source}: randomness is forbidden in v0.2")
    require(type(randomness["exogenous_channel_count"]) is int, f"{context}.randomness.exogenous_channel_count: must be integer")

    expected_candidate_id = (
        "MIR-P2-L0-NONE"
        if not observed_signatures
        else f"MIR-P2-L{len(observed_signatures)}-{'-'.join(observed_signatures)}"
    )
    require(candidate_id == expected_candidate_id, f"{source}: candidate_id must be {expected_candidate_id}")
    if not observed_signatures:
        require(
            data["status"] == "analytically_excluded",
            f"{source}: the zero-row candidate must be analytically_excluded",
        )
    else:
        require(
            data["status"] in {"development", "frozen"},
            f"{source}: a nonzero-row candidate cannot be analytically_excluded",
        )

    if data["status"] == "analytically_excluded":
        require_string(data.get("exclusion_reason"), f"{context}.exclusion_reason")
    else:
        require("exclusion_reason" not in data, f"{source}: non-excluded candidate has exclusion_reason")
    if data["status"] == "frozen":
        require(substrate_hash != "UNSEALED", f"{source}: frozen candidate has unsealed substrate hash")
        require(detector_hash != "UNSEALED", f"{source}: frozen candidate has unsealed detector hash")

    return accounting["normalized_n_p"], len(laws)


def validate_candidate(data: dict[str, Any], source: Path) -> tuple[int, int]:
    require(type(data) is dict, f"{source}: root must be an object")
    version = data.get("contract_version")
    if version == "0.1-draft":
        return _validate_v01(data, source)
    if version == "0.2-draft":
        return _validate_v02(data, source)
    raise ValidationError(f"{source}: unsupported contract version {version!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate minimal informational realization candidates.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for path in args.paths:
        try:
            data = load_json(path)
            n_p, n_l = validate_candidate(data, path)
        except (ValidationError, TypeError, AttributeError, KeyError) as exc:
            failed = True
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            continue
        print(f"PASS {path}: N_P={n_p} N_L={n_l} status={data['status']}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
