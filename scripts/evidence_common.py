from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_registry(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError:
        return json.loads(text)
    value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise ValueError(f"registry must contain an object: {path}")
    return value


def load_gc001() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    claim = next(item for item in claims["claims"] if item["id"] == "GC-001")
    summary_path = ROOT / claim["evidence"][0]
    event_path = ROOT / claim["evidence"][1]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    with event_path.open(newline="", encoding="utf-8") as handle:
        events = list(csv.DictReader(handle))
    return claim, summary, events


def load_gc002() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    claim = next(item for item in claims["claims"] if item["id"] == "GC-002")
    summary_path = ROOT / claim["evidence"][0]
    case_path = ROOT / claim["evidence"][1]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    with case_path.open(newline="", encoding="utf-8") as handle:
        cases = list(csv.DictReader(handle))
    return claim, summary, cases


def load_gc003() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    claim = next(item for item in claims["claims"] if item["id"] == "GC-003")
    summary_path = ROOT / claim["evidence"][0]
    case_path = ROOT / claim["evidence"][1]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    with case_path.open(newline="", encoding="utf-8") as handle:
        cases = list(csv.DictReader(handle))
    return claim, summary, cases


def load_gc004() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    claim = next(item for item in claims["claims"] if item["id"] == "GC-004")
    summary_path = ROOT / claim["evidence"][0]
    aggregate_path = ROOT / claim["evidence"][2]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    with aggregate_path.open(newline="", encoding="utf-8") as handle:
        aggregate = list(csv.DictReader(handle))
    return claim, summary, aggregate


def load_gc005() -> tuple[dict[str, Any], dict[str, Any]]:
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    claim = next(item for item in claims["claims"] if item["id"] == "GC-005")
    summary_path = ROOT / claim["evidence"][0]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return claim, summary


def load_gc006() -> tuple[dict[str, Any], dict[str, Any]]:
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    claim = next(item for item in claims["claims"] if item["id"] == "GC-006")
    summary_path = ROOT / claim["evidence"][0]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return claim, summary


def load_gc007() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    claim = next(item for item in claims["claims"] if item["id"] == "GC-007")
    summary = json.loads((ROOT / claim["evidence"][0]).read_text(encoding="utf-8"))
    replay = json.loads((ROOT / claim["evidence"][3]).read_text(encoding="utf-8"))
    return claim, summary, replay


def load_gc008() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    claim = next(item for item in claims["claims"] if item["id"] == "GC-008")
    same_state = json.loads((ROOT / claim["evidence"][0]).read_text(encoding="utf-8"))
    screen = json.loads((ROOT / claim["evidence"][2]).read_text(encoding="utf-8"))
    independent = json.loads((ROOT / claim["evidence"][4]).read_text(encoding="utf-8"))
    return claim, same_state, screen, independent


def load_gc009() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    claim = next(item for item in claims["claims"] if item["id"] == "GC-009")
    freeze = json.loads((ROOT / claim["evidence"][0]).read_text(encoding="utf-8"))
    summary = json.loads((ROOT / claim["evidence"][2]).read_text(encoding="utf-8"))
    with (ROOT / claim["evidence"][3]).open(newline="", encoding="utf-8") as handle:
        replays = list(csv.DictReader(handle))
    return claim, freeze, summary, replays


def load_gc010() -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
]:
    claims = load_registry(ROOT / "evidence" / "claims.yaml")
    claim = next(item for item in claims["claims"] if item["id"] == "GC-010")
    summary = json.loads((ROOT / claim["evidence"][0]).read_text(encoding="utf-8"))
    tables: list[list[dict[str, str]]] = []
    for relative in claim["evidence"][1:5]:
        with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
            tables.append(list(csv.DictReader(handle)))
    assignments, depths, sources, selector_hashes = tables
    return claim, summary, assignments, depths, sources, selector_hashes


def strict_events(events: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in events if row["constraint_transport"] == "1"]


def evidence_metrics(
    summary: dict[str, Any], events: list[dict[str, str]]
) -> dict[str, Any]:
    strict = strict_events(events)
    return {
        "class_b_events": int(summary["events"]),
        "role_bearing_predecessor_events": sum(
            int(row["predecessor_bridge_role_critical"]) for row in events
        ),
        "strict_transport_events": len(strict),
        "strict_positive_seed_count": len({row["init_seed"] for row in strict}),
        "all_payload_zero": bool(summary["all_payload_zero"]),
        "all_ledger_exact": bool(summary["all_ledger_exact"]),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)
