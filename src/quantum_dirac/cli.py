"""Outcome-safe command surface for the quantum-Dirac draft."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .manifest import validate_committed_manifests
from .seal import preview_disabled_seal
from .spec import QuantumDiracSpecError, audit_design, repository_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("audit-design")
    commands.add_parser("validate-manifests")
    commands.add_parser("preview-disabled-seal")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    root = repository_root() if arguments.root is None else arguments.root.resolve()
    try:
        if arguments.command == "audit-design":
            value = audit_design(root)
        elif arguments.command == "validate-manifests":
            value = validate_committed_manifests(root)
        elif arguments.command == "preview-disabled-seal":
            value = preview_disabled_seal(root)
        else:  # pragma: no cover
            raise QuantumDiracSpecError("unknown draft command")
    except (QuantumDiracSpecError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
