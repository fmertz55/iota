"""Strict design validation and pre-freeze access guards.

This module deliberately has no registered evaluator.  Its public guards
allow only the disclosed algebraic fixtures while the protocol remains a
draft and reject every registered scenario and refinement.
"""

from __future__ import annotations

import hashlib
import json
import os
from fractions import Fraction
from pathlib import Path
from typing import Any

from .protocol import (
    ALLOWED_FIXTURE_SIZES,
    ALLOWED_TARGET_FIXTURE_CUTOFF,
    CANDIDATE_ID,
    CONFIRMATION_SCENARIOS,
    CONFIRMATION_STATES,
    CONTRACT_REF,
    DESIGN_FILENAMES,
    DEVELOPMENT_SCENARIOS,
    DEVELOPMENT_STATES,
    FORBIDDEN_PRE_FREEZE_PATHS,
    INPUT_R_MAX,
    INPUT_R_MIN,
    IMPLEMENTATION_FILENAMES,
    PRECISION_BITS,
    PROTOCOL_VERSION,
    REGISTERED_OBSERVATION_TIMES,
    REGISTERED_SCENARIOS,
    REGISTERED_SIZES,
    SEARCH_ID,
    SPEC_DIR_REF,
    STATUS,
    TARGET_R_CUTOFF,
)


class SymmetryQCASpecError(ValueError):
    """Raised when a draft artifact or request violates the outcome boundary."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SymmetryQCASpecError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise SymmetryQCASpecError(f"non-finite JSON constant {value!r} is forbidden")


def load_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SymmetryQCASpecError(f"{path}: {exc}") from exc


def parse_fraction(value: str) -> Fraction:
    if type(value) is not str or not value:
        raise SymmetryQCASpecError("exact rational must be a nonempty string")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise SymmetryQCASpecError(f"invalid exact rational {value!r}") from exc


def _validate_protocol(protocol: Any) -> None:
    expected = {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": STATUS,
        "registered_outcome_authorized": False,
        "production_implementation_present": True,
        "run_command_enabled": False,
    }
    if type(protocol) is not dict:
        raise SymmetryQCASpecError("protocol must be an object")
    for key, value in expected.items():
        if protocol.get(key) != value:
            raise SymmetryQCASpecError(f"protocol {key} mismatch")
    target = protocol.get("target")
    if type(target) is not dict:
        raise SymmetryQCASpecError("protocol target is missing")
    if target.get("observation_times") != list(REGISTERED_OBSERVATION_TIMES):
        raise SymmetryQCASpecError("observation times differ from the contract")
    refinements = target.get("refinements")
    if type(refinements) is not list or [
        item.get("n_sites") for item in refinements
    ] != list(REGISTERED_SIZES):
        raise SymmetryQCASpecError("refinement sizes differ from the contract")
    rationale = protocol.get("primary_metric", {}).get("threshold_rationale_status")
    if rationale != (
        "outward-rounded analytic absolute-gate certificate present; "
        "refinement ratios and observables remain outcome gates"
    ):
        raise SymmetryQCASpecError("threshold certificate status mismatch")


def _validate_candidate(candidate: Any) -> None:
    if type(candidate) is not dict:
        raise SymmetryQCASpecError("candidate must be an object")
    if candidate.get("search_id") != SEARCH_ID:
        raise SymmetryQCASpecError("candidate search id mismatch")
    if candidate.get("candidate_id") != CANDIDATE_ID:
        raise SymmetryQCASpecError("candidate id mismatch")
    if candidate.get("status") != "prospective_outcomes_forbidden":
        raise SymmetryQCASpecError("candidate status does not forbid outcomes")
    substrate = candidate.get("substrate")
    if type(substrate) is not dict or substrate.get("sites") != list(REGISTERED_SIZES):
        raise SymmetryQCASpecError("candidate substrate sizes mismatch")
    if candidate.get("gate_order") != [
        "scalar_phase_if_active",
        "edge_scatter",
        "on_site_swap",
    ]:
        raise SymmetryQCASpecError("candidate gate order mismatch")
    if candidate.get("logical_step") != (
        "A B_mu P_V with rightmost operation first and P_V omitted when inactive"
    ):
        raise SymmetryQCASpecError("candidate logical step mismatch")
    arithmetic = candidate.get("arithmetic")
    if type(arithmetic) is not dict or arithmetic.get("precision_bits") != PRECISION_BITS:
        raise SymmetryQCASpecError("candidate precision mismatch")
    if arithmetic.get("binary64_registered_dynamics_allowed") is not False:
        raise SymmetryQCASpecError("candidate permits binary64 registered dynamics")


def _validate_target(target: Any) -> None:
    if type(target) is not dict:
        raise SymmetryQCASpecError("target must be an object")
    if target.get("search_id") != SEARCH_ID:
        raise SymmetryQCASpecError("target search id mismatch")
    fourier = target.get("fourier")
    if type(fourier) is not dict:
        raise SymmetryQCASpecError("target Fourier declaration is missing")
    if (fourier.get("input_r_min"), fourier.get("input_r_max")) != (
        INPUT_R_MIN,
        INPUT_R_MAX,
    ):
        raise SymmetryQCASpecError("target input band mismatch")
    if (fourier.get("reference_r_min"), fourier.get("reference_r_max")) != (
        -TARGET_R_CUTOFF,
        TARGET_R_CUTOFF,
    ):
        raise SymmetryQCASpecError("target reference band mismatch")


def _validate_scenarios(scenarios: Any, partitions: Any) -> None:
    if type(scenarios) is not dict or type(partitions) is not dict:
        raise SymmetryQCASpecError("scenario or partition artifact is invalid")
    if scenarios.get("search_id") != SEARCH_ID or partitions.get("search_id") != SEARCH_ID:
        raise SymmetryQCASpecError("scenario or partition search id mismatch")
    development = scenarios.get("development")
    confirmation = scenarios.get("confirmation")
    if type(development) is not list or type(confirmation) is not list:
        raise SymmetryQCASpecError("scenario lists are missing")
    if [item.get("id") for item in development] != list(DEVELOPMENT_SCENARIOS):
        raise SymmetryQCASpecError("development scenario order mismatch")
    if [item.get("id") for item in confirmation] != list(CONFIRMATION_SCENARIOS):
        raise SymmetryQCASpecError("confirmation scenario order mismatch")
    if partitions.get("development_scenarios") != list(DEVELOPMENT_SCENARIOS):
        raise SymmetryQCASpecError("development partition mismatch")
    if partitions.get("confirmation_scenarios") != list(CONFIRMATION_SCENARIOS):
        raise SymmetryQCASpecError("confirmation partition mismatch")
    if partitions.get("confirmation_single_use") is not True:
        raise SymmetryQCASpecError("confirmation must be single use")
    for scenario in development + confirmation:
        for start, end, mass in scenario.get("mass", []):
            if not parse_fraction(start) < parse_fraction(end):
                raise SymmetryQCASpecError("mass interval is empty or reversed")
            if abs(parse_fraction(mass)) > Fraction(3, 5):
                raise SymmetryQCASpecError("mass exceeds the declared strict margin")
        for item in scenario.get("potential", []):
            if type(item) is not list or len(item) != 5:
                raise SymmetryQCASpecError("potential tuple must have five entries")
            start, end, harmonic, amplitude, phase = item
            if not parse_fraction(start) < parse_fraction(end):
                raise SymmetryQCASpecError("potential interval is empty or reversed")
            if type(harmonic) is not int or harmonic not in (2, 3):
                raise SymmetryQCASpecError("potential harmonic is outside the draft")
            parse_fraction(amplitude)
            if phase not in ("0", "pi/2"):
                raise SymmetryQCASpecError("potential phase is outside the draft")


def _validate_states(states: Any, partitions: Any) -> None:
    if type(states) is not dict or states.get("search_id") != SEARCH_ID:
        raise SymmetryQCASpecError("state artifact search id mismatch")
    development = states.get("development")
    confirmation = states.get("confirmation")
    if type(development) is not list or type(confirmation) is not list:
        raise SymmetryQCASpecError("state lists are missing")
    if [item.get("id") for item in development] != list(DEVELOPMENT_STATES):
        raise SymmetryQCASpecError("development state order mismatch")
    if [item.get("id") for item in confirmation] != list(CONFIRMATION_STATES):
        raise SymmetryQCASpecError("confirmation state order mismatch")
    if partitions.get("development_states") != list(DEVELOPMENT_STATES):
        raise SymmetryQCASpecError("development state partition mismatch")
    if partitions.get("confirmation_states") != list(CONFIRMATION_STATES):
        raise SymmetryQCASpecError("confirmation state partition mismatch")
    allowed_types = {"positive", "negative", "positive_interference", "energy_mixture"}
    allowed_phases = {"2pi/7", "2pi/5", "-pi/6", "3pi/7"}
    for state in development + confirmation:
        if state.get("type") not in allowed_types:
            raise SymmetryQCASpecError("state type is outside the draft")
        if "packets" in state:
            packets = state["packets"]
            if type(packets) is not list or len(packets) != 2:
                raise SymmetryQCASpecError("interference state requires two packets")
            for packet in packets:
                if type(packet) is not list or len(packet) != 3:
                    raise SymmetryQCASpecError("state packet must have three entries")
                parse_fraction(packet[0])
                if parse_fraction(packet[1]) <= 0:
                    raise SymmetryQCASpecError("state width must be positive")
                parse_fraction(packet[2])
        else:
            parse_fraction(state["r0"])
            if parse_fraction(state["width"]) <= 0:
                raise SymmetryQCASpecError("state width must be positive")
            parse_fraction(state["x0"])
        if "relative_phase" in state and state["relative_phase"] not in allowed_phases:
            raise SymmetryQCASpecError("state phase is outside the draft")
    if states.get("serialized_amplitudes_allowed") is not False:
        raise SymmetryQCASpecError("serialized state amplitudes must be forbidden")


def _validate_maps(maps: Any) -> None:
    if type(maps) is not dict or maps.get("search_id") != SEARCH_ID:
        raise SymmetryQCASpecError("maps artifact search id mismatch")
    if set(maps) != {"maps_version", "search_id", "E", "M", "Phi"}:
        raise SymmetryQCASpecError("maps artifact has missing or unexpected sections")
    if maps["E"].get("aliasing_forbidden") is not True:
        raise SymmetryQCASpecError("encoding must forbid aliasing")
    if "pi_sector_probability" not in maps["M"].get("outputs", []):
        raise SymmetryQCASpecError("measurement map omits pi-sector accounting")
    if maps["Phi"].get("target_schedule_sampling") != "left endpoint of every macrostep":
        raise SymmetryQCASpecError("intervention sampling convention mismatch")


def _validate_fixtures(fixtures: Any) -> None:
    if type(fixtures) is not dict or fixtures.get("search_id") != SEARCH_ID:
        raise SymmetryQCASpecError("fixture artifact search id mismatch")
    allowed = fixtures.get("allowed")
    if type(allowed) is not list or len(allowed) != 5:
        raise SymmetryQCASpecError("fixture allowlist must contain five entries")
    candidate_sizes = sorted(
        {item["N"] for item in allowed if "N" in item}
    )
    if candidate_sizes != list(ALLOWED_FIXTURE_SIZES):
        raise SymmetryQCASpecError("fixture size allowlist mismatch")
    if fixtures.get("forbidden_registered_sizes") != list(REGISTERED_SIZES):
        raise SymmetryQCASpecError("registered-size rejection list mismatch")
    required = fixtures.get("required_rejections")
    if type(required) is not list or "enabled_draft_production" not in required:
        raise SymmetryQCASpecError("draft-production rejection is missing")


def _validate_threshold_certificate(certificate: Any) -> None:
    if type(certificate) is not dict or certificate.get("search_id") != SEARCH_ID:
        raise SymmetryQCASpecError("threshold certificate search id mismatch")
    if certificate.get("status") != "outward_analytic_absolute_gate_certificate":
        raise SymmetryQCASpecError("threshold certificate status mismatch")
    if certificate.get("precision_bits") != PRECISION_BITS:
        raise SymmetryQCASpecError("threshold certificate precision mismatch")
    if certificate.get("registered_propagation_performed") is not False:
        raise SymmetryQCASpecError("threshold certificate performed a registered run")
    refinements = certificate.get("refinements")
    if type(refinements) is not list or [item.get("n_sites") for item in refinements] != list(REGISTERED_SIZES):
        raise SymmetryQCASpecError("threshold certificate refinement order mismatch")
    if not all(
        item.get("direct_absolute_gate_certified") is True
        and item.get("potential_absolute_gate_certified") is True
        for item in refinements
    ):
        raise SymmetryQCASpecError("threshold certificate does not prove every absolute gate")


def _validate_forbidden_paths(root: Path) -> None:
    existing = [path for path in FORBIDDEN_PRE_FREEZE_PATHS if (root / path).exists()]
    if existing:
        raise SymmetryQCASpecError(
            "draft contains forbidden seal/open/result artifacts: " + ", ".join(existing)
        )


def audit_design(
    root: Path | None = None, *, allow_lifecycle_artifacts: bool = False
) -> dict[str, Any]:
    root = repository_root() if root is None else root.resolve()
    spec_dir = root / SPEC_DIR_REF
    if not spec_dir.is_dir() or spec_dir.is_symlink():
        raise SymmetryQCASpecError("specification directory is missing")
    bindings: dict[str, str] = {}
    for filename in DESIGN_FILENAMES:
        path = spec_dir / filename
        if not path.is_file() or path.is_symlink():
            raise SymmetryQCASpecError(f"design file is missing: {filename}")
        bindings[filename] = sha256_file(path)
    contract = root / CONTRACT_REF
    if not contract.is_file() or contract.is_symlink():
        raise SymmetryQCASpecError("human-readable contract is missing")
    protocol = load_json(spec_dir / "protocol.json")
    candidate = load_json(spec_dir / "candidate.json")
    target = load_json(spec_dir / "target.json")
    scenarios = load_json(spec_dir / "scenarios.json")
    states = load_json(spec_dir / "states.json")
    partitions = load_json(spec_dir / "partitions.json")
    maps = load_json(spec_dir / "maps.json")
    fixtures = load_json(spec_dir / "algebraic_fixtures.json")
    threshold_certificate = load_json(spec_dir / "threshold_certificate.json")
    _validate_protocol(protocol)
    _validate_candidate(candidate)
    _validate_target(target)
    _validate_scenarios(scenarios, partitions)
    _validate_states(states, partitions)
    _validate_maps(maps)
    _validate_fixtures(fixtures)
    _validate_threshold_certificate(threshold_certificate)
    implementation_dir = root / "src/quantum_dirac_symmetry_qca"
    implementation_bindings: dict[str, str] = {}
    for filename in IMPLEMENTATION_FILENAMES:
        path = implementation_dir / filename
        if not path.is_file() or path.is_symlink():
            raise SymmetryQCASpecError(f"implementation file is missing: {filename}")
        implementation_bindings[filename] = sha256_file(path)
    if not allow_lifecycle_artifacts:
        _validate_forbidden_paths(root)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": STATUS,
        "design_files": bindings,
        "contract_sha256": sha256_file(contract),
        "registered_outcomes_forbidden": True,
        "production_implementation_present": True,
        "implementation_files": implementation_bindings,
        "threshold_interval_certificate_present": True,
    }


def guard_pre_freeze_candidate(
    *, n_sites: int, scenario_id: str | None = None
) -> None:
    if type(n_sites) is not int or n_sites <= 0:
        raise SymmetryQCASpecError("fixture lattice size must be a positive integer")
    if n_sites in REGISTERED_SIZES:
        raise SymmetryQCASpecError("registered lattice evaluation is forbidden")
    if n_sites not in ALLOWED_FIXTURE_SIZES:
        raise SymmetryQCASpecError("lattice is not in the disclosed fixture set")
    if scenario_id is not None:
        if scenario_id in REGISTERED_SCENARIOS:
            raise SymmetryQCASpecError("registered scenario evaluation is forbidden")
        raise SymmetryQCASpecError("undeclared scenario evaluation is forbidden")


def guard_pre_freeze_target(*, cutoff: int, scenario_id: str | None = None) -> None:
    if type(cutoff) is not int or cutoff != ALLOWED_TARGET_FIXTURE_CUTOFF:
        raise SymmetryQCASpecError("target fixture is restricted to cutoff 3")
    if scenario_id is not None:
        if scenario_id in REGISTERED_SCENARIOS:
            raise SymmetryQCASpecError("registered scenario evaluation is forbidden")
        raise SymmetryQCASpecError("undeclared scenario evaluation is forbidden")


def write_canonical_json_once(path: Path, value: Any) -> None:
    """Atomically create canonical ASCII JSON without ever overwriting bytes."""

    if path.exists():
        raise SymmetryQCASpecError(f"refusing to overwrite artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (canonical_json(value) + "\n").encode("ascii")
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise SymmetryQCASpecError(f"stale temporary file exists: {temporary}")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        temporary.unlink()
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
