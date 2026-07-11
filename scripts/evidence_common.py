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
