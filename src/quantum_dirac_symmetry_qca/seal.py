"""Disabled lifecycle preview for the incomplete direct-QCA protocol draft."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .protocol import FREEZE_TAG, SEARCH_ID, STATUS
from .spec import audit_design, repository_root


class SymmetryQCASealError(ValueError):
    """Raised when draft code is asked to create an outcome-bearing artifact."""


def preview_disabled_seal(root: Path | None = None) -> dict[str, Any]:
    """Summarize current bindings without creating or authorizing a seal."""

    root = repository_root() if root is None else root.resolve()
    audit = audit_design(root)
    return {
        "search_id": SEARCH_ID,
        "status": STATUS,
        "design_files": audit["design_files"],
        "contract_sha256": audit["contract_sha256"],
        "required_future_freeze_tag": FREEZE_TAG,
        "seal_ready": False,
        "run_command_enabled": False,
        "registered_outcomes_forbidden": True,
        "missing_prerequisites": [
            "production candidate and target implementations",
            "algorithmically independent registered verifier",
            "prospective manifests and lifecycle authorization",
        ],
    }


def write_outcome_seal(*_args: object, **_kwargs: object) -> None:
    raise SymmetryQCASealError(
        "this draft cannot write an outcome seal; complete and review every prerequisite first"
    )
