#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.minimal_realization_orbit.cli import (  # noqa: E402
    OPEN_SEAL_REF,
    OUTCOME_SEAL_REF,
    RESULT_PATH,
    _audit_protocol,
    command_verify_results,
    load_open_seal,
    repository_root,
    verify_outcome_seal,
)


def main() -> int:
    root = repository_root()
    _audit_protocol(root)
    outcome_seal = root / OUTCOME_SEAL_REF
    open_seal = root / OPEN_SEAL_REF
    result = root / RESULT_PATH
    if outcome_seal.exists():
        verify_outcome_seal(outcome_seal)
    if result.exists():
        command_verify_results(argparse.Namespace(open_seal=open_seal))
    elif open_seal.exists():
        load_open_seal(open_seal, require_clean=True)
    print(
        "PASS MIR-EXACT-ORBIT-001: protocol=0.1-draft "
        "joint_recurrence=post_cone_saturation resource_censoring=incomplete "
        f"result={'verified' if result.exists() else 'not_present'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
