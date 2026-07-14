"""Strict outcome-free specification loading and audit helpers."""

from __future__ import annotations

import hashlib
import json
import math
import os
from fractions import Fraction
from pathlib import Path
from typing import Any

from .protocol import (
    ALLOWED_FIXTURE_SIZES,
    CANDIDATE_ID,
    CONFIRMATION_SCENARIOS,
    CONTRACT_REF,
    DESIGN_FILENAMES,
    DEVELOPMENT_SCENARIOS,
    FORBIDDEN_PRE_FREEZE_PATHS,
    INPUT_R_MAX,
    INPUT_R_MIN,
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


class QuantumDiracSpecError(ValueError):
    """Raised when a design artifact or evaluation request violates the draft."""


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
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise QuantumDiracSpecError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise QuantumDiracSpecError(f"non-finite JSON constant {value!r} is forbidden")


def load_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QuantumDiracSpecError(f"{path}: {exc}") from exc


def parse_fraction(value: str) -> Fraction:
    if type(value) is not str or not value:
        raise QuantumDiracSpecError("exact rational must be a nonempty string")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise QuantumDiracSpecError(f"invalid exact rational {value!r}") from exc
    return result


def parse_phase(value: str) -> tuple[Fraction, bool]:
    """Return (coefficient, includes_pi) for the frozen small phase grammar."""

    if value == "0":
        return Fraction(0), False
    if value == "pi/2":
        return Fraction(1, 2), True
    if value == "pi/3":
        return Fraction(1, 3), True
    if value == "pi/5":
        return Fraction(1, 5), True
    if value == "-pi/4":
        return Fraction(-1, 4), True
    raise QuantumDiracSpecError(f"phase is outside the frozen grammar: {value!r}")


def _require_exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise QuantumDiracSpecError(f"{label} keys differ from the frozen design")
    return value


def _require_design_files(root: Path) -> dict[str, str]:
    spec_dir = root / SPEC_DIR_REF
    if not spec_dir.is_dir() or spec_dir.is_symlink():
        raise QuantumDiracSpecError("registered specification directory is missing")
    bindings: dict[str, str] = {}
    for filename in DESIGN_FILENAMES:
        path = spec_dir / filename
        if not path.is_file() or path.is_symlink():
            raise QuantumDiracSpecError(f"registered design file is missing: {filename}")
        bindings[filename] = sha256_file(path)
    return bindings


def _validate_protocol(protocol: Any) -> None:
    if type(protocol) is not dict:
        raise QuantumDiracSpecError("protocol must be an object")
    expected = {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": STATUS,
        "registered_outcome_authorized": False,
        "production_implementation_present": False,
        "run_command_enabled": False,
    }
    for key, value in expected.items():
        if protocol.get(key) != value:
            raise QuantumDiracSpecError(f"protocol {key} mismatch")
    target = protocol.get("target")
    if type(target) is not dict:
        raise QuantumDiracSpecError("protocol target is missing")
    if target.get("input_dimension") != 18:
        raise QuantumDiracSpecError("target input dimension must be 18")
    if target.get("observation_times") != list(REGISTERED_OBSERVATION_TIMES):
        raise QuantumDiracSpecError("observation times differ from the contract")
    refinements = target.get("refinements")
    if (
        type(refinements) is not list
        or [item.get("n_sites") for item in refinements] != list(REGISTERED_SIZES)
    ):
        raise QuantumDiracSpecError("refinement sizes differ from the contract")


def _validate_candidate(candidate: Any) -> None:
    if type(candidate) is not dict:
        raise QuantumDiracSpecError("candidate must be an object")
    if candidate.get("search_id") != SEARCH_ID:
        raise QuantumDiracSpecError("candidate search id mismatch")
    if candidate.get("candidate_id") != CANDIDATE_ID:
        raise QuantumDiracSpecError("candidate id mismatch")
    if candidate.get("status") != "prospective_outcomes_forbidden":
        raise QuantumDiracSpecError("candidate status does not forbid outcomes")
    substrate = candidate.get("substrate")
    if type(substrate) is not dict or substrate.get("sites") != list(REGISTERED_SIZES):
        raise QuantumDiracSpecError("candidate substrate sizes mismatch")
    if candidate.get("gate_order") != [
        "scalar_phase_if_active",
        "mass_mix",
        "on_site_swap",
        "directed_edge_swap",
    ]:
        raise QuantumDiracSpecError("candidate gate order mismatch")
    arithmetic = candidate.get("arithmetic")
    if type(arithmetic) is not dict or arithmetic.get("precision_bits") != PRECISION_BITS:
        raise QuantumDiracSpecError("candidate precision mismatch")
    if arithmetic.get("binary64_registered_dynamics_allowed") is not False:
        raise QuantumDiracSpecError("candidate permits binary64 registered dynamics")


def _validate_scenarios(scenarios: Any, partitions: Any) -> None:
    if type(scenarios) is not dict or type(partitions) is not dict:
        raise QuantumDiracSpecError("scenario or partition artifact is invalid")
    development = scenarios.get("development")
    confirmation = scenarios.get("confirmation")
    if [item.get("id") for item in development] != list(DEVELOPMENT_SCENARIOS):
        raise QuantumDiracSpecError("development scenario order mismatch")
    if [item.get("id") for item in confirmation] != list(CONFIRMATION_SCENARIOS):
        raise QuantumDiracSpecError("confirmation scenario order mismatch")
    if partitions.get("development_scenarios") != list(DEVELOPMENT_SCENARIOS):
        raise QuantumDiracSpecError("development partition mismatch")
    if partitions.get("confirmation_scenarios") != list(CONFIRMATION_SCENARIOS):
        raise QuantumDiracSpecError("confirmation partition mismatch")
    if partitions.get("confirmation_single_use") is not True:
        raise QuantumDiracSpecError("confirmation must be single use")
    for scenario in development + confirmation:
        for start, end, mass in scenario["mass"]:
            if not parse_fraction(start) < parse_fraction(end):
                raise QuantumDiracSpecError("mass interval is empty or reversed")
            parse_fraction(mass)
        for start, end, amplitude, phase in scenario["potential"]:
            if not parse_fraction(start) < parse_fraction(end):
                raise QuantumDiracSpecError("potential interval is empty or reversed")
            parse_fraction(amplitude)
            parse_phase(phase)


def _validate_target(target: Any) -> None:
    if type(target) is not dict:
        raise QuantumDiracSpecError("target must be an object")
    fourier = target.get("fourier")
    if type(fourier) is not dict:
        raise QuantumDiracSpecError("target Fourier declaration is missing")
    if (fourier.get("input_r_min"), fourier.get("input_r_max")) != (
        INPUT_R_MIN,
        INPUT_R_MAX,
    ):
        raise QuantumDiracSpecError("target input band mismatch")
    if (fourier.get("reference_r_min"), fourier.get("reference_r_max")) != (
        -TARGET_R_CUTOFF,
        TARGET_R_CUTOFF,
    ):
        raise QuantumDiracSpecError("target reference band mismatch")


def _validate_forbidden_paths(root: Path) -> None:
    existing = [relative for relative in FORBIDDEN_PRE_FREEZE_PATHS if (root / relative).exists()]
    if existing:
        raise QuantumDiracSpecError(
            "draft contains forbidden freeze/open/result artifacts: " + ", ".join(existing)
        )


def audit_design(root: Path | None = None) -> dict[str, Any]:
    root = repository_root() if root is None else root.resolve()
    bindings = _require_design_files(root)
    if not (root / CONTRACT_REF).is_file():
        raise QuantumDiracSpecError("human-readable contract is missing")
    protocol = load_json(root / SPEC_DIR_REF / "protocol.json")
    candidate = load_json(root / SPEC_DIR_REF / "candidate.json")
    target = load_json(root / SPEC_DIR_REF / "target.json")
    scenarios = load_json(root / SPEC_DIR_REF / "scenarios.json")
    partitions = load_json(root / SPEC_DIR_REF / "partitions.json")
    _validate_protocol(protocol)
    _validate_candidate(candidate)
    _validate_target(target)
    _validate_scenarios(scenarios, partitions)
    _validate_forbidden_paths(root)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "search_id": SEARCH_ID,
        "status": STATUS,
        "design_files": bindings,
        "contract_sha256": sha256_file(root / CONTRACT_REF),
        "registered_outcomes_forbidden": True,
    }


def guard_pre_freeze_fixture(*, n_sites: int, scenario_id: str | None = None) -> None:
    if type(n_sites) is not int or n_sites <= 0:
        raise QuantumDiracSpecError("fixture lattice size must be a positive integer")
    if n_sites in REGISTERED_SIZES:
        raise QuantumDiracSpecError("registered lattice evaluation is forbidden before freeze")
    if n_sites not in ALLOWED_FIXTURE_SIZES:
        raise QuantumDiracSpecError("lattice is not in the disclosed fixture set")
    if scenario_id is not None:
        if scenario_id in REGISTERED_SCENARIOS:
            raise QuantumDiracSpecError("registered scenario evaluation is forbidden before freeze")
        raise QuantumDiracSpecError("undeclared scenario evaluation is forbidden before freeze")


def write_canonical_json_once(path: Path, value: Any) -> None:
    if path.exists():
        raise QuantumDiracSpecError(f"refusing to overwrite artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (canonical_json(value) + "\n").encode("ascii")
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise QuantumDiracSpecError(f"stale temporary file exists: {temporary}")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        temporary.unlink()
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


def finite_number(value: Any, label: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise QuantumDiracSpecError(f"{label} must be finite")
    return float(value)
