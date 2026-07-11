from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

DEPTH_PATTERN = re.compile(r"^depth(?P<depth>\d{3})_summary\.json$")
VALID_ENDPOINTS = {"handoff", "lineage_loss", "source_survival_censored"}
F068_SELECTOR_SHA256 = "9e4a70d8d0b829b4a4b288da69b8a740c398b5c161a0e5a26a7605015e8c8cb0"
F068_REPLAY_SHA256 = "cbba811983592c635a85529ceac467b3fb9d7d27de5fb585d4f56ddaaf728cb1"

DEPTH_FIELDS = [
    "depth",
    "risk_set",
    "cuts",
    "handoffs",
    "source_survival_censored",
    "conditional_cut_fraction_of_risk",
    "conditional_cut_fraction_of_resolved",
    "conditional_handoff_fraction_of_risk",
    "conditional_source_censor_fraction_of_risk",
    "cumulative_cuts",
    "cumulative_source_survival_censored",
    "cumulative_survivors",
    "cumulative_cut_fraction",
    "cumulative_source_censor_fraction",
    "cumulative_survivor_fraction",
    "next_selectors",
]

SOURCE_FIELDS = [
    "depth",
    "cohort",
    "source_id",
    "init_seed",
    "event_start_offset",
    "initial_branches",
    "risk_set",
    "cuts",
    "handoffs",
    "source_survival_censored",
    "conditional_cut_fraction_of_risk",
    "conditional_cut_fraction_of_resolved",
    "cumulative_cuts",
    "cumulative_source_survival_censored",
    "cumulative_survivors",
]

HASH_FIELDS = [
    "depth",
    "summary_path",
    "summary_sha256",
    "cases_path",
    "cases_sha256",
    "selector_chain_length",
    "current_selector_path",
    "current_selector_sha256",
    "parent_chain_sha256",
    "next_selector_path",
    "next_selector_sha256",
    "next_selector_rows",
    "current_depth_veto_run",
    "next_depth_veto_run",
    "expected_replays_path",
    "expected_replays_sha256",
]

ASSIGNMENT_FIELDS = [
    "cohort",
    "source_id",
    "init_seed",
    "event_start_offset",
    "branch_sample",
    "branch_seed",
    "last_observed_depth",
    "depths_tested",
    "selectors_vetoed",
    "selector_target_sequence",
    "unique_selector_targets",
    "repeated_selector_targets",
    "consecutive_same_target_events",
    "selector_offset_sequence",
    "first_selector_offset",
    "last_selector_offset",
    "selector_offset_span",
    "maximum_interselector_delay",
    "cut_depth",
    "cut_depth_label",
    "assignment_status",
    "right_censored",
    "censoring_type",
    "source_survival_censored_depth",
    "handoff_beyond_observed_max",
    "terminal_offset_at_assignment",
    "address_loss_delay_at_assignment",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and summarize committed Finding 069 sequential-veto stages."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("output/findings/finding069"),
        help="Directory containing depthNNN_summary.json and depthNNN_cases.csv.",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=Path("output/findings/finding069/sequential_realization_cut"),
        help="Prefix for aggregate CSV and JSON artifacts.",
    )
    parser.add_argument(
        "--through-depth",
        type=int,
        help="Summarize a contiguous prefix even if later stage files are present.",
    )
    parser.add_argument(
        "--protocol-max-depth",
        type=int,
        default=8,
        help="Prospectively declared maximum veto depth.",
    )
    parser.add_argument(
        "--fixed-followup-offsets",
        type=int,
        default=128,
        help="Fixed follow-up after the committed Finding 068 address-loss offset.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Write validated artifacts without printing the full summary JSON.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    """Write deterministic, flushed CSVs using the repository's artifact convention."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def write_json(path: Path, value: dict[str, Any]) -> None:
    """Write deterministic, flushed JSON artifacts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_bool(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes"}:
            return True
        if normalized in {"0", "false", "no"}:
            return False
    raise ValueError(f"{field} is not boolean: {value!r}")


def fraction(numerator: int, denominator: int) -> float | str:
    return numerator / denominator if denominator else ""


def branch_key(row: dict[str, Any]) -> tuple[str, str, int, int, int, int]:
    """Return the complete immutable branch identity used by the protocol."""
    return (
        str(row["cohort"]),
        str(row["source_id"]),
        int(row["init_seed"]),
        int(row["event_start_offset"]),
        int(row["branch_sample"]),
        int(row["branch_seed"]),
    )


def selector_offset(row: dict[str, Any]) -> int:
    """Normalize the Finding 068 selector and later selector schemas."""
    value = row.get("selector_offset") or row.get("natural_terminal_offset")
    if value in {None, ""}:
        raise RuntimeError(f"selector lacks an offset: {branch_key(row)}")
    return int(value)


def source_key(row: dict[str, Any]) -> tuple[str, str, int, int]:
    return (
        str(row["cohort"]),
        str(row["source_id"]),
        int(row["init_seed"]),
        int(row["event_start_offset"]),
    )


def resolve_artifact(recorded: str, input_dir: Path, repo_root: Path) -> Path:
    path = Path(recorded)
    candidates = [path] if path.is_absolute() else [repo_root / path, input_dir / path.name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"recorded artifact does not exist: {recorded}")


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())


def discover_stages(input_dir: Path, through_depth: int | None) -> list[tuple[int, Path]]:
    discovered: list[tuple[int, Path]] = []
    for path in input_dir.glob("depth*_summary.json"):
        match = DEPTH_PATTERN.fullmatch(path.name)
        if match is None:
            continue
        depth = int(match.group("depth"))
        if through_depth is None or depth <= through_depth:
            discovered.append((depth, path))
    discovered.sort()
    if not discovered:
        raise RuntimeError(f"no depthNNN_summary.json artifacts found in {input_dir}")
    observed = [depth for depth, _ in discovered]
    expected = list(range(1, observed[-1] + 1))
    if observed != expected:
        raise RuntimeError(f"sequential depths are not contiguous: {observed}")
    if through_depth is not None and observed[-1] != through_depth:
        raise RuntimeError(
            f"requested --through-depth {through_depth}, but discovered only through {observed[-1]}"
        )
    return discovered


def nonzero_counts(values: Counter[str]) -> dict[str, int]:
    return {key: value for key, value in sorted(values.items()) if value}


def validate_case_safety(
    row: dict[str, str], depth: int, fixed_followup_offsets: int
) -> None:
    checks = {
        "depth": int(row["depth"]) == depth,
        "selectors_expected": int(row["selectors_expected"]) == depth,
        "selectors_matched": int(row["selectors_matched"]) == depth,
        "selector_identity": as_bool(
            row["all_selector_identities_exact"], "all_selector_identities_exact"
        ),
        "collision_free": not as_bool(row["lineage_collision"], "lineage_collision"),
        "payload_zero": as_bool(
            row["payload_zero_all_offsets"], "payload_zero_all_offsets"
        ),
        "ledger_exact": as_bool(
            row["ledger_exact_all_offsets"], "ledger_exact_all_offsets"
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(
            f"depth {depth} branch {branch_key(row)} failed safety validation: {checks}"
        )
    endpoint = row["stage_endpoint"]
    if endpoint not in VALID_ENDPOINTS:
        raise RuntimeError(f"depth {depth} has unknown endpoint {endpoint!r}")
    endpoint_handoff = endpoint == "handoff"
    if as_bool(row["handoff"], "handoff") != endpoint_handoff:
        raise RuntimeError(f"depth {depth} branch {branch_key(row)} endpoint/handoff mismatch")
    loss_observed = as_bool(row["address_loss_observed"], "address_loss_observed")
    if endpoint in {"handoff", "lineage_loss"} and not loss_observed:
        raise RuntimeError(f"depth {depth} branch {branch_key(row)} lacks address loss")
    if endpoint == "source_survival_censored" and loss_observed:
        raise RuntimeError(f"depth {depth} source-censored branch reports address loss")
    delay = row["address_loss_delay_from_depth1_natural"]
    if loss_observed:
        if delay == "" or not 0 <= int(delay) <= fixed_followup_offsets:
            raise RuntimeError(
                f"depth {depth} branch {branch_key(row)} has invalid follow-up delay {delay!r}"
            )
    elif delay != "":
        raise RuntimeError(
            f"depth {depth} branch {branch_key(row)} has a delay without address loss"
        )


def load_stage(
    depth: int,
    summary_path: Path,
    input_dir: Path,
    repo_root: Path,
    fixed_followup_offsets: int,
) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if int(summary.get("depth", -1)) != depth:
        raise RuntimeError(f"{summary_path} declares depth {summary.get('depth')!r}")
    cases_path = input_dir / f"depth{depth:03d}_cases.csv"
    if not cases_path.is_file():
        raise FileNotFoundError(cases_path)
    if "cases_csv" in summary and Path(summary["cases_csv"]).name != cases_path.name:
        raise RuntimeError(f"depth {depth} summary points at the wrong cases artifact")
    cases = read_csv(cases_path)
    if len(cases) != int(summary["input_branches"]):
        raise RuntimeError(
            f"depth {depth} input count mismatch: cases={len(cases)} "
            f"summary={summary['input_branches']}"
        )
    keys = [branch_key(row) for row in cases]
    if len(keys) != len(set(keys)):
        raise RuntimeError(f"depth {depth} contains duplicate branch rows")
    for row in cases:
        validate_case_safety(row, depth, fixed_followup_offsets)
    case_by_key = {branch_key(row): row for row in cases}

    endpoints = Counter(row["stage_endpoint"] for row in cases)
    if nonzero_counts(endpoints) != {
        str(key): int(value) for key, value in sorted(summary["stage_endpoints"].items())
    }:
        raise RuntimeError(f"depth {depth} endpoint counts disagree with its summary")
    handoff_keys = {branch_key(row) for row in cases if row["stage_endpoint"] == "handoff"}
    if int(summary["next_selectors"]) != len(handoff_keys):
        raise RuntimeError(f"depth {depth} next-selector count does not equal handoffs")

    summary_checks = {
        "all_selectors_matched": as_bool(
            summary["all_selectors_matched"], "all_selectors_matched"
        ),
        "all_selector_identities_exact": as_bool(
            summary["all_selector_identities_exact"], "all_selector_identities_exact"
        ),
        "all_payload_zero": as_bool(summary["all_payload_zero"], "all_payload_zero"),
        "all_ledger_exact": as_bool(summary["all_ledger_exact"], "all_ledger_exact"),
        "collision_cases": int(summary["collision_cases"]) == 0,
        "current_depth_veto_run": as_bool(
            summary.get("current_depth_veto_run", True), "current_depth_veto_run"
        ),
        "next_depth_veto_run": not as_bool(
            summary.get("next_depth_veto_run", False), "next_depth_veto_run"
        ),
        "transient_child_lineage_losses": int(
            summary.get("transient_child_lineage_losses", -1)
        )
        == sum(
            row["stage_endpoint"] == "lineage_loss"
            and as_bool(row["next_child_observed"], "next_child_observed")
            for row in cases
        ),
        "child_bearing_source_censoring": int(
            summary.get("child_bearing_source_censoring", -1)
        )
        == sum(
            row["stage_endpoint"] == "source_survival_censored"
            and as_bool(row["next_child_observed"], "next_child_observed")
            for row in cases
        ),
    }
    if not all(summary_checks.values()):
        raise RuntimeError(f"depth {depth} summary failed safety validation: {summary_checks}")

    selector_chain = summary.get("selector_chain")
    if not isinstance(selector_chain, list) or len(selector_chain) != depth:
        raise RuntimeError(f"depth {depth} selector chain length is not {depth}")
    selector_hashes: list[str] = []
    for item in selector_chain:
        selector_path = resolve_artifact(str(item["path"]), input_dir, repo_root)
        actual_hash = file_sha256(selector_path)
        expected_hash = str(item["sha256"])
        if actual_hash != expected_hash:
            raise RuntimeError(f"selector hash mismatch at depth {depth}: {selector_path}")
        selector_hashes.append(expected_hash)
    computed_chain_hash = hashlib.sha256("|".join(selector_hashes).encode("ascii")).hexdigest()
    if computed_chain_hash != summary["parent_chain_sha256"]:
        raise RuntimeError(f"depth {depth} parent selector-chain hash changed")
    if depth == 1 and selector_hashes != [F068_SELECTOR_SHA256]:
        raise RuntimeError("depth 1 does not use the committed Finding 068 selector hash")

    current_selector_path = resolve_artifact(
        str(selector_chain[-1]["path"]), input_dir, repo_root
    )
    current_selector_rows = read_csv(current_selector_path)
    current_selector_keys = [branch_key(row) for row in current_selector_rows]
    if len(current_selector_keys) != len(set(current_selector_keys)):
        raise RuntimeError(f"depth {depth} current selector contains duplicate branches")
    if set(current_selector_keys) != set(keys):
        raise RuntimeError(f"depth {depth} current selector risk set differs from cases")
    current_selector_by_key = {
        branch_key(row): row for row in current_selector_rows
    }

    next_selector_path = resolve_artifact(
        str(summary["next_selectors_csv"]), input_dir, repo_root
    )
    next_selector_hash = file_sha256(next_selector_path)
    if next_selector_hash != summary["next_selectors_sha256"]:
        raise RuntimeError(f"depth {depth} next-selector hash changed")
    next_selector_rows = read_csv(next_selector_path)
    if len(next_selector_rows) != int(summary["next_selectors"]):
        raise RuntimeError(f"depth {depth} next-selector row count changed")
    next_selector_keys = [branch_key(row) for row in next_selector_rows]
    if len(next_selector_keys) != len(set(next_selector_keys)):
        raise RuntimeError(f"depth {depth} next selectors contain duplicate branches")
    if set(next_selector_keys) != handoff_keys:
        raise RuntimeError(f"depth {depth} next selectors do not equal handoff survivors")
    for row in next_selector_rows:
        key = branch_key(row)
        parent_case = case_by_key[key]
        offset = selector_offset(row)
        checks = {
            "depth": int(row["depth"]) == depth + 1,
            "selection_rule": row["selection_rule_version"]
            == "f069-first-next-inherited-child-v1",
            "parent_chain": row["parent_chain_sha256"] == computed_chain_hash,
            "offset_equation": offset
            == int(row["branch_offset"]) + int(row["terminal_relative"]) + 1,
            "case_target": row["target"] == parent_case["next_child_target"],
            "case_relative": int(row["terminal_relative"])
            == int(parent_case["next_child_relative"]),
            "case_offset": offset == int(parent_case["next_child_offset"]),
            "case_multiplicity": int(row["natural_child_multiplicity"])
            == int(parent_case["next_child_multiplicity"]),
            "source_in_lineage": as_bool(
                row["source_in_focal_lineage"], "source_in_focal_lineage"
            ),
            "unique_join": as_bool(
                row["unique_inheritance_join"], "unique_inheritance_join"
            ),
            "join_verified": as_bool(
                row["inheritance_join_verified"], "inheritance_join_verified"
            ),
            "natural_pass": as_bool(row["natural_gate_passed"], "natural_gate_passed"),
            "target_activated": as_bool(row["target_activated"], "target_activated"),
            "payload_zero": as_bool(row["payload_zero"], "payload_zero"),
            "ledger_exact": as_bool(row["ledger_exact"], "ledger_exact"),
            "collision_free": not as_bool(row["lineage_collision"], "lineage_collision"),
        }
        if not all(checks.values()):
            raise RuntimeError(
                f"depth {depth} next selector {branch_key(row)} failed validation: {checks}"
            )

    expected_replays_path: Path | None = None
    expected_replays_hash = ""
    expected_replays = summary.get("expected_replays")
    if depth == 1 and expected_replays is None:
        raise RuntimeError("depth 1 lacks the committed Finding 068 replay reference")
    if expected_replays is not None:
        expected_replays_path = resolve_artifact(
            str(expected_replays["path"]), input_dir, repo_root
        )
        expected_replays_hash = file_sha256(expected_replays_path)
        if expected_replays_hash != str(expected_replays["sha256"]):
            raise RuntimeError(f"depth {depth} Finding 068 replay hash changed")
        if depth == 1 and expected_replays_hash != F068_REPLAY_SHA256:
            raise RuntimeError("depth 1 does not use the committed Finding 068 replay hash")

    return {
        "depth": depth,
        "summary": summary,
        "summary_path": summary_path.resolve(),
        "summary_sha256": file_sha256(summary_path),
        "cases": cases,
        "cases_path": cases_path.resolve(),
        "cases_sha256": file_sha256(cases_path),
        "keys": set(keys),
        "handoff_keys": handoff_keys,
        "selector_hashes": selector_hashes,
        "current_selector_path": current_selector_path,
        "current_selector_rows": current_selector_rows,
        "current_selector_by_key": current_selector_by_key,
        "next_selector_path": next_selector_path,
        "next_selector_hash": next_selector_hash,
        "next_selector_rows": next_selector_rows,
        "expected_replays_path": expected_replays_path,
        "expected_replays_hash": expected_replays_hash,
    }


def validate_stage_chain(stages: list[dict[str, Any]]) -> None:
    metadata: dict[tuple[str, str, int, int, int, int], tuple[Any, ...]] = {}
    for index, stage in enumerate(stages):
        depth = int(stage["depth"])
        if index:
            previous = stages[index - 1]
            if stage["keys"] != previous["handoff_keys"]:
                missing = previous["handoff_keys"] - stage["keys"]
                unexpected = stage["keys"] - previous["handoff_keys"]
                raise RuntimeError(
                    f"depth {depth} risk set is not exactly prior handoffs; "
                    f"missing={len(missing)} unexpected={len(unexpected)}"
                )
            expected_chain = previous["selector_hashes"] + [previous["next_selector_hash"]]
            if stage["selector_hashes"] != expected_chain:
                raise RuntimeError(f"depth {depth} selector chain does not extend depth {depth - 1}")
            for key in stage["keys"]:
                prior_selector = previous["current_selector_by_key"][key]
                current_selector = stage["current_selector_by_key"][key]
                prior_order = (
                    selector_offset(prior_selector),
                    int(prior_selector["gate_ordinal"]),
                )
                current_order = (
                    selector_offset(current_selector),
                    int(current_selector["gate_ordinal"]),
                )
                if current_order <= prior_order:
                    raise RuntimeError(
                        f"depth {depth} selector order did not advance for {key}: "
                        f"{prior_order} -> {current_order}"
                    )
        for row in stage["cases"]:
            key = branch_key(row)
            values = (
                row["cohort"],
                row["source_id"],
                int(row["init_seed"]),
                int(row["event_start_offset"]),
                int(row["branch_sample"]),
            )
            if key in metadata and metadata[key] != values:
                raise RuntimeError(f"branch metadata changed at depth {depth}: {key}")
            metadata[key] = values


def build_depth_rows(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    initial = len(stages[0]["cases"])
    cumulative_cuts = 0
    cumulative_source_censored = 0
    output: list[dict[str, Any]] = []
    for stage in stages:
        endpoints = Counter(row["stage_endpoint"] for row in stage["cases"])
        risk = len(stage["cases"])
        cuts = endpoints["lineage_loss"]
        handoffs = endpoints["handoff"]
        source_censored = endpoints["source_survival_censored"]
        cumulative_cuts += cuts
        cumulative_source_censored += source_censored
        if cumulative_cuts + cumulative_source_censored + handoffs != initial:
            raise RuntimeError(f"depth {stage['depth']} cumulative accounting is not exact")
        resolved = cuts + handoffs
        output.append({
            "depth": stage["depth"],
            "risk_set": risk,
            "cuts": cuts,
            "handoffs": handoffs,
            "source_survival_censored": source_censored,
            "conditional_cut_fraction_of_risk": fraction(cuts, risk),
            "conditional_cut_fraction_of_resolved": fraction(cuts, resolved),
            "conditional_handoff_fraction_of_risk": fraction(handoffs, risk),
            "conditional_source_censor_fraction_of_risk": fraction(source_censored, risk),
            "cumulative_cuts": cumulative_cuts,
            "cumulative_source_survival_censored": cumulative_source_censored,
            "cumulative_survivors": handoffs,
            "cumulative_cut_fraction": fraction(cumulative_cuts, initial),
            "cumulative_source_censor_fraction": fraction(cumulative_source_censored, initial),
            "cumulative_survivor_fraction": fraction(handoffs, initial),
            "next_selectors": int(stage["summary"]["next_selectors"]),
        })
    return output


def build_source_rows(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    initial_counts = Counter(source_key(row) for row in stages[0]["cases"])
    cumulative_cuts: Counter[tuple[str, str, int, int]] = Counter()
    cumulative_source_censored: Counter[tuple[str, str, int, int]] = Counter()
    output: list[dict[str, Any]] = []
    for stage in stages:
        grouped: dict[tuple[str, str, int, int], list[dict[str, str]]] = {}
        for row in stage["cases"]:
            grouped.setdefault(source_key(row), []).append(row)
        for key in sorted(initial_counts):
            rows = grouped.get(key, [])
            endpoints = Counter(row["stage_endpoint"] for row in rows)
            cuts = endpoints["lineage_loss"]
            handoffs = endpoints["handoff"]
            source_censored = endpoints["source_survival_censored"]
            cumulative_cuts[key] += cuts
            cumulative_source_censored[key] += source_censored
            if cumulative_cuts[key] + cumulative_source_censored[key] + handoffs != initial_counts[key]:
                raise RuntimeError(
                    f"depth {stage['depth']} source accounting is not exact for {key}"
                )
            resolved = cuts + handoffs
            output.append({
                "depth": stage["depth"],
                "cohort": key[0],
                "source_id": key[1],
                "init_seed": key[2],
                "event_start_offset": key[3],
                "initial_branches": initial_counts[key],
                "risk_set": len(rows),
                "cuts": cuts,
                "handoffs": handoffs,
                "source_survival_censored": source_censored,
                "conditional_cut_fraction_of_risk": fraction(cuts, len(rows)),
                "conditional_cut_fraction_of_resolved": fraction(cuts, resolved),
                "cumulative_cuts": cumulative_cuts[key],
                "cumulative_source_survival_censored": cumulative_source_censored[key],
                "cumulative_survivors": handoffs,
            })
    return output


def build_hash_rows(
    stages: list[dict[str, Any]], repo_root: Path
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for stage in stages:
        summary = stage["summary"]
        output.append({
            "depth": stage["depth"],
            "summary_path": display_path(stage["summary_path"], repo_root),
            "summary_sha256": stage["summary_sha256"],
            "cases_path": display_path(stage["cases_path"], repo_root),
            "cases_sha256": stage["cases_sha256"],
            "selector_chain_length": len(stage["selector_hashes"]),
            "current_selector_path": display_path(stage["current_selector_path"], repo_root),
            "current_selector_sha256": stage["selector_hashes"][-1],
            "parent_chain_sha256": summary["parent_chain_sha256"],
            "next_selector_path": display_path(stage["next_selector_path"], repo_root),
            "next_selector_sha256": stage["next_selector_hash"],
            "next_selector_rows": len(stage["next_selector_rows"]),
            "current_depth_veto_run": int(
                as_bool(summary.get("current_depth_veto_run", True), "current_depth_veto_run")
            ),
            "next_depth_veto_run": int(
                as_bool(summary.get("next_depth_veto_run", False), "next_depth_veto_run")
            ),
            "expected_replays_path": (
                display_path(stage["expected_replays_path"], repo_root)
                if stage["expected_replays_path"] is not None
                else ""
            ),
            "expected_replays_sha256": stage["expected_replays_hash"],
        })
    return output


def build_assignments(
    stages: list[dict[str, Any]], protocol_max_depth: int
) -> list[dict[str, Any]]:
    histories: dict[
        tuple[str, str, int, int, int, int], list[dict[str, str]]
    ] = {
        branch_key(row): [] for row in stages[0]["cases"]
    }
    selector_histories: dict[
        tuple[str, str, int, int, int, int], list[dict[str, str]]
    ] = {key: [] for key in histories}
    for stage in stages:
        for row in stage["cases"]:
            histories[branch_key(row)].append(row)
        for key, row in stage["current_selector_by_key"].items():
            selector_histories[key].append(row)

    max_depth = int(stages[-1]["depth"])
    protocol_cap_reached = max_depth == protocol_max_depth
    output: list[dict[str, Any]] = []
    for key in sorted(histories):
        rows = histories[key]
        selectors = selector_histories[key]
        if len(selectors) != len(rows):
            raise RuntimeError(
                f"branch {key} has {len(rows)} cases but {len(selectors)} selectors"
            )
        first = rows[0]
        last = rows[-1]
        targets = [str(row["target"]) for row in selectors]
        offsets = [selector_offset(row) for row in selectors]
        gaps = [current - previous for previous, current in zip(offsets, offsets[1:])]
        if any(gap < 0 for gap in gaps):
            raise RuntimeError(f"branch {key} has decreasing selector offsets")
        consecutive_same_target = sum(
            current == previous for previous, current in zip(targets, targets[1:])
        )
        endpoint = last["stage_endpoint"]
        cut_depth: int | str = ""
        source_censor_depth: int | str = ""
        handoff_beyond = 0
        right_censored = 0
        censoring_type = ""
        if endpoint == "lineage_loss":
            cut_depth = int(last["depth"])
            cut_label = str(cut_depth)
            status = "observed_cut"
        elif endpoint == "source_survival_censored":
            source_censor_depth = int(last["depth"])
            cut_label = f"source-censored@{source_censor_depth}"
            status = "source_survival_censored"
            right_censored = 1
            censoring_type = "fixed_address_followup"
        elif endpoint == "handoff":
            cut_label = f">{max_depth}"
            handoff_beyond = 1
            right_censored = 1
            if protocol_cap_reached:
                status = "right_censored_above_protocol_max"
                censoring_type = "protocol_depth_cap"
            else:
                status = "pending_deeper_replay"
                censoring_type = "partial_depth_sequence"
        else:  # guarded by validation
            raise RuntimeError(endpoint)
        output.append({
            "cohort": first["cohort"],
            "source_id": first["source_id"],
            "init_seed": int(first["init_seed"]),
            "event_start_offset": int(first["event_start_offset"]),
            "branch_sample": int(first["branch_sample"]),
            "branch_seed": int(first["branch_seed"]),
            "last_observed_depth": int(last["depth"]),
            "depths_tested": len(rows),
            "selectors_vetoed": len(selectors),
            "selector_target_sequence": "|".join(targets),
            "unique_selector_targets": len(set(targets)),
            "repeated_selector_targets": len(targets) - len(set(targets)),
            "consecutive_same_target_events": consecutive_same_target,
            "selector_offset_sequence": "|".join(str(value) for value in offsets),
            "first_selector_offset": offsets[0],
            "last_selector_offset": offsets[-1],
            "selector_offset_span": offsets[-1] - offsets[0],
            "maximum_interselector_delay": max(gaps, default=0),
            "cut_depth": cut_depth,
            "cut_depth_label": cut_label,
            "assignment_status": status,
            "right_censored": right_censored,
            "censoring_type": censoring_type,
            "source_survival_censored_depth": source_censor_depth,
            "handoff_beyond_observed_max": handoff_beyond,
            "terminal_offset_at_assignment": last["terminal_offset"],
            "address_loss_delay_at_assignment": last[
                "address_loss_delay_from_depth1_natural"
            ],
        })
    return output


def main() -> None:
    args = parse_args()
    if args.protocol_max_depth < 1:
        raise ValueError("--protocol-max-depth must be positive")
    if args.fixed_followup_offsets < 1:
        raise ValueError("--fixed-followup-offsets must be positive")
    if args.through_depth is not None and args.through_depth < 1:
        raise ValueError("--through-depth must be positive")
    input_dir = args.input_dir.resolve()
    repo_root = Path(__file__).resolve().parents[1]
    discovered = discover_stages(input_dir, args.through_depth)
    if discovered[-1][0] > args.protocol_max_depth:
        raise RuntimeError(
            f"observed depth {discovered[-1][0]} exceeds protocol maximum "
            f"{args.protocol_max_depth}"
        )
    stages = [
        load_stage(
            depth,
            path,
            input_dir,
            repo_root,
            args.fixed_followup_offsets,
        )
        for depth, path in discovered
    ]
    validate_stage_chain(stages)

    depth_rows = build_depth_rows(stages)
    source_rows = build_source_rows(stages)
    hash_rows = build_hash_rows(stages, repo_root)
    assignments = build_assignments(stages, args.protocol_max_depth)

    prefix = args.output_prefix
    depth_path = prefix.with_name(prefix.name + "_depths.csv")
    source_path = prefix.with_name(prefix.name + "_sources.csv")
    hash_path = prefix.with_name(prefix.name + "_selector_hashes.csv")
    assignment_path = prefix.with_name(prefix.name + "_assignments.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(depth_path, DEPTH_FIELDS, depth_rows)
    write_csv(source_path, SOURCE_FIELDS, source_rows)
    write_csv(hash_path, HASH_FIELDS, hash_rows)
    write_csv(assignment_path, ASSIGNMENT_FIELDS, assignments)

    statuses = Counter(row["assignment_status"] for row in assignments)
    cut_depth_distribution = Counter(row["cut_depth_label"] for row in assignments)
    observed_cut_depth_counts = {
        str(depth): sum(row["cut_depth"] == depth for row in assignments)
        for depth in range(1, int(stages[-1]["depth"]) + 1)
    }
    max_depth = int(stages[-1]["depth"])
    last_handoffs = int(depth_rows[-1]["handoffs"])
    protocol_complete = max_depth == args.protocol_max_depth or last_handoffs == 0
    all_case_rows = [row for stage in stages for row in stage["cases"]]
    observed_delays = [
        int(row["address_loss_delay_from_depth1_natural"])
        for row in all_case_rows
        if row["address_loss_delay_from_depth1_natural"] != ""
    ]
    finding068_selector = stages[0]["summary"]["selector_chain"][0]
    first_replays_path = stages[0]["expected_replays_path"]
    summary = {
        "protocol": "validated aggregate of nested sequential ancestry-realization vetoes",
        "estimand": (
            "sequential retained-amplitude veto depth under the frozen first-child policy; "
            "not a globally minimal graph-theoretic cut"
        ),
        "input_dir": display_path(input_dir, repo_root),
        "observed_depths": [int(stage["depth"]) for stage in stages],
        "max_observed_depth": max_depth,
        "protocol_max_depth": args.protocol_max_depth,
        "fixed_followup_offsets": args.fixed_followup_offsets,
        "protocol_complete": protocol_complete,
        "partial_depth_sequence": not protocol_complete,
        "initial_branches": len(stages[0]["cases"]),
        "source_states": len({source_key(row) for row in stages[0]["cases"]}),
        "initialization_seeds": len(
            {int(row["init_seed"]) for row in stages[0]["cases"]}
        ),
        "observed_cuts": statuses["observed_cut"],
        "source_survival_censored": statuses["source_survival_censored"],
        "right_censored_above_protocol_max": statuses[
            "right_censored_above_protocol_max"
        ],
        "survivors_above_observed_max": last_handoffs,
        "assignment_status": dict(sorted(statuses.items())),
        "cut_depth_distribution": dict(sorted(cut_depth_distribution.items())),
        "observed_cut_depth_counts": observed_cut_depth_counts,
        "distinct_selector_events_vetoed": sum(
            int(row["selectors_vetoed"]) for row in assignments
        ),
        "selector_override_executions": sum(
            int(row["depth"]) * int(row["risk_set"]) for row in depth_rows
        ),
        "branches_with_reused_selector_targets": sum(
            int(row["repeated_selector_targets"]) > 0 for row in assignments
        ),
        "repeated_selector_target_events": sum(
            int(row["repeated_selector_targets"]) for row in assignments
        ),
        "consecutive_same_target_events": sum(
            int(row["consecutive_same_target_events"]) for row in assignments
        ),
        "maximum_selector_offset_span": max(
            int(row["selector_offset_span"]) for row in assignments
        ),
        "maximum_interselector_delay": max(
            int(row["maximum_interselector_delay"]) for row in assignments
        ),
        "maximum_observed_address_loss_delay": max(observed_delays, default=None),
        "collision_cases": sum(
            int(stage["summary"]["collision_cases"]) for stage in stages
        ),
        "transient_child_lineage_losses": sum(
            int(stage["summary"]["transient_child_lineage_losses"])
            for stage in stages
        ),
        "child_bearing_source_censoring": sum(
            int(stage["summary"]["child_bearing_source_censoring"])
            for stage in stages
        ),
        "finding068_selector_manifest": {
            "path": str(finding068_selector["path"]),
            "sha256": str(finding068_selector["sha256"]),
        },
        "finding068_expected_replays": {
            "path": (
                display_path(first_replays_path, repo_root)
                if first_replays_path is not None
                else ""
            ),
            "sha256": stages[0]["expected_replays_hash"],
        },
        "all_depths_contiguous": True,
        "all_risk_sets_nested": True,
        "all_selector_chains_verified": True,
        "all_selector_hashes_verified": True,
        "all_safety_checks_passed": True,
        "depths_csv": display_path(depth_path, repo_root),
        "sources_csv": display_path(source_path, repo_root),
        "selector_hashes_csv": display_path(hash_path, repo_root),
        "assignments_csv": display_path(assignment_path, repo_root),
        "depth_aggregate": depth_rows,
    }
    write_json(summary_path, summary)
    if not args.quiet:
        print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
