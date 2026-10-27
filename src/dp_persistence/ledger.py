"""Result ledger: atomic writing, validation, and trace hashing."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

from .protocol import SEARCH_ID, load_spec_file, spec


SEEDS_PER_POINT = 25000
TRACE_PREFIX = b"ICP-DP-PERSISTENCE-001/run-trace/v1\0"
TRACE_ENCODING = (
    "sha256_prefix_domain_then_per_run_length_prefixed_canonical_json_"
    "in_increasing_run_seed_order"
)


class LedgerError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


# ----------------------------------------------------------------------------
# Trace hashing
# ----------------------------------------------------------------------------


TRACE_FIELDS = (
    "absorbed_at",
    "censored_at",
    "ticks_run",
    "S",
    "C",
    "E",
    "stranded_amplitude",
    "ledger_residual",
)


def run_trace_record(run_seed: int, record: dict[str, Any]) -> dict[str, Any]:
    trace = {"run_seed": int(run_seed)}
    for key in TRACE_FIELDS:
        if key in record:
            value = record[key]
            trace[key] = None if value is None else (float(value) if key == "E" else int(value))
    trace["n_t"] = [int(v) for v in record["n_t"]]
    trace["r2_sum_t"] = [int(v) for v in record["r2_sum_t"]]
    return trace


def point_trace_sha256(domain: str, runs: Iterable[tuple[int, dict[str, Any]]]) -> str:
    """Hash of every run of one evaluated point, in increasing seed order."""

    encoded_domain = domain.encode("ascii")
    digest = hashlib.sha256()
    digest.update(TRACE_PREFIX)
    digest.update(len(encoded_domain).to_bytes(8, "big"))
    digest.update(encoded_domain)
    previous = None
    for run_seed, record in runs:
        if previous is not None and run_seed <= previous:
            raise LedgerError("trace runs must be in strictly increasing seed order")
        previous = run_seed
        line = canonical_json(run_trace_record(run_seed, record)).encode("ascii")
        digest.update(len(line).to_bytes(8, "big"))
        digest.update(line)
    return digest.hexdigest()


# ----------------------------------------------------------------------------
# Atomic, exactly-once writing
# ----------------------------------------------------------------------------


def write_canonical_json_once(path: Path, value: dict[str, Any]) -> None:
    """Atomically publish canonical JSON without overwrite."""

    if path.exists():
        raise LedgerError(f"refusing to overwrite registered artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise LedgerError(f"refusing to overwrite stale temporary file: {temporary}")
    data = (canonical_json(value) + "\n").encode("ascii")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        temporary.unlink()
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------


def _schema_errors(ledger: dict[str, Any], root: Path | None) -> list[str]:
    import jsonschema

    schema = load_spec_file("result.schema.json", root)
    validator = jsonschema.Draft202012Validator(schema)
    return sorted(
        f"{'/'.join(str(p) for p in error.absolute_path)}: {error.message}"
        for error in validator.iter_errors(ledger)
    )


def _verdict_from(per_class: dict[str, str]) -> str:
    matches = [c for c, s in per_class.items() if s == "match"]
    if len(matches) == 1 and all(s == "excluded" for c, s in per_class.items() if c != matches[0]):
        return matches[0]
    if per_class and all(s == "excluded" for s in per_class.values()):
        return "none_of_registered"
    return "indeterminate"


def _seed_range(result_kind: str) -> tuple[int, int] | None:
    partitions = spec("partitions.json")
    if result_kind == "development":
        r = partitions["iota_development"]["run_seed_range"]
        return r["first"], r["last"]
    if result_kind == "confirmation":
        r = partitions["iota_confirmation"]["run_seed_range"]
        return r["first"], r["last"]
    return None


def _check_finite(value: Any, path: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise LedgerError(f"non-finite number at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            _check_finite(item, f"{path}/{key}")
    if isinstance(value, list):
        for i, item in enumerate(value):
            _check_finite(item, f"{path}/{i}")


def validate_result(ledger: dict[str, Any], *, root: Path | None = None) -> None:
    """Transport schema plus the sealed cross-field checks."""

    errors = _schema_errors(ledger, root)
    if errors:
        raise LedgerError("result schema violation: " + "; ".join(errors[:10]))
    _check_finite(ledger, "")
    if ledger["search_id"] != SEARCH_ID:
        raise LedgerError("search id mismatch")
    kind = ledger["result_kind"]
    if kind in ("development", "confirmation") and "predicted_classes" not in ledger:
        raise LedgerError(f"{kind} result requires predicted_classes")
    seed_range = _seed_range(kind)
    for model in ledger["models"]:
        model_id = model["model_id"]
        if kind != "calibration":
            if model_id != "IOTA-MIN-L0":
                raise LedgerError(f"{kind} result model must be IOTA-MIN-L0")
            if model.get("ledger_max_abs_residual") != 0:
                raise LedgerError("IOTA ledger residual must be present and exactly 0")
        if "verdict" in model and "per_class" in model:
            if model["verdict"] in ("DP_1p1", "DP_3p1", "DyP_3", "none_of_registered", "indeterminate"):
                expected = _verdict_from(model["per_class"])
                if model["verdict"] != expected:
                    raise LedgerError(
                        f"{model_id} verdict {model['verdict']!r} inconsistent with per_class ({expected!r})"
                    )
        hypotheses = model.get("hypotheses")
        if hypotheses:
            if hypotheses.get("H1_threshold") != "equal":
                for key in ("H2_dynamic_class", "H3_static_tail"):
                    if key in hypotheses and hypotheses[key] != "not_applicable":
                        raise LedgerError(f"{key} must be not_applicable unless H1 is equal")
        for point in model["points"]:
            first, last = point["seed_first"], point["seed_last"]
            if last - first + 1 != point["runs"]:
                raise LedgerError(f"{model_id} point seed span does not equal its run count")
            if seed_range is not None:
                if not (seed_range[0] <= first <= last <= seed_range[1]):
                    raise LedgerError(f"{model_id} point seeds lie outside the {kind} partition")
                if (first - seed_range[0]) % SEEDS_PER_POINT != 0 or point["runs"] > SEEDS_PER_POINT:
                    raise LedgerError(f"{model_id} point seeds do not start a registered block")
            elif first < 0:
                raise LedgerError(f"{model_id} calibration run index is negative")
