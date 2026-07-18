#!/usr/bin/env python3

"""Expose the sealed direct-QCA pi-sector reducer defect without mutating evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import mpmath as mp


ROOT = Path(__file__).resolve().parents[1]
RESULT_BASE = (
    ROOT / "output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001"
)
PROTOCOL_PATH = (
    ROOT / "specs/icp_quantum_dirac_symmetry_qca/v0.1-draft/protocol.json"
)
EXPECTED_SHA256 = {
    "protocol": "dc0e718dd176c1d831df50a34750aec3294dc0e97e3ae75a13113ff9a96022b6",
    "development": "89d7c65a37bf8d38fea3a87b7f656c02cae57664fcf6b53b725fb8ace7c228c4",
    "confirmation": "be5a9f85770e1d201abbc269c26da25d821f11f67db364c434473b5c70517e65",
}
REGISTERED_SIZES = (320, 640, 1280)
THRESHOLD = mp.mpf("1e-24")


def signed_mode(index: int, n_sites: int) -> int:
    return index if index <= n_sites // 2 else index - n_sites


def buggy_sector(n_sites: int) -> list[int]:
    return [
        signed_mode(index, n_sites)
        for index in range(n_sites)
        if 4 * abs(signed_mode(index, n_sites)) >= 3 * n_sites
    ]


def intended_sector(n_sites: int) -> list[int]:
    return [
        signed_mode(index, n_sites)
        for index in range(n_sites)
        if 8 * abs(signed_mode(index, n_sites)) >= 3 * n_sites
    ]


def checked_json(path: Path, expected_sha256: str) -> dict:
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_sha256:
        raise RuntimeError(
            f"content-addressed input mismatch for {path}: "
            f"expected {expected_sha256}, got {actual}"
        )
    return json.loads(data)


def analytic_tail(ledger: dict, scenario_id: str) -> str:
    scenario = next(
        item for item in ledger["scenario_results"] if item["scenario_id"] == scenario_id
    )
    return scenario["pi_sector"]["analytic_probability_upper"]


def corrected_rough_control() -> mp.mpf:
    """Recompute the disclosed non-gating rough control with the intended sector."""

    n_sites = 320
    delta = mp.mpf(1) / 20
    mu = delta / 3
    normalization = mp.sqrt(1 - mu * mu)
    state = [mp.mpc(0) for _ in range(2 * n_sites)]
    for site in range(n_sites):
        state[2 * site] = 1 / mp.sqrt(n_sites)
    for _ in range(40):
        for site in range(n_sites):
            potential = mp.mpf(1) / 8 if site < n_sites // 2 else -mp.mpf(1) / 8
            phase = mp.exp(-1j * delta * potential)
            state[2 * site] *= phase
            state[2 * site + 1] *= phase
        updated = [mp.mpc(0) for _ in state]
        for site in range(n_sites):
            updated[2 * site] = (
                normalization * state[2 * ((site - 1) % n_sites)]
                - 1j * mu * state[2 * site + 1]
            )
            updated[2 * site + 1] = (
                -1j * mu * state[2 * site]
                + normalization * state[2 * ((site + 1) % n_sites) + 1]
            )
        state = updated

    probability = mp.mpf(0)
    for index in range(n_sites):
        signed = signed_mode(index, n_sites)
        if 8 * abs(signed) < 3 * n_sites:
            continue
        right = mp.fsum(
            state[2 * site] * mp.exp(-2j * mp.pi * index * site / n_sites)
            for site in range(n_sites)
        ) / mp.sqrt(n_sites)
        left = mp.fsum(
            state[2 * site + 1]
            * mp.exp(-2j * mp.pi * index * site / n_sites)
            for site in range(n_sites)
        ) / mp.sqrt(n_sites)
        probability += abs(right) ** 2 + abs(left) ** 2
    return probability


def main() -> int:
    with mp.workdps(110):
        protocol = checked_json(PROTOCOL_PATH, EXPECTED_SHA256["protocol"])
        zone_edge = protocol["tail_and_zone_edge"]
        if (
            zone_edge["pi_sector"] != "abs(q)>=3pi/4"
            or zone_edge["coarsest_pi_sector_mode_abs_min"] != 120
            or zone_edge["registered_pi_sector_probability_max"] != "1e-24"
        ):
            raise RuntimeError("frozen protocol no longer matches the audited pi sector")
        ledgers = {
            stage: checked_json(
                RESULT_BASE / f"{stage}_results_v0.4.json", EXPECTED_SHA256[stage]
            )
            for stage in ("development", "confirmation")
        }
        buggy_counts = {str(size): len(buggy_sector(size)) for size in REGISTERED_SIZES}
        intended_counts = {
            str(size): len(intended_sector(size)) for size in REGISTERED_SIZES
        }
        if any(buggy_counts.values()):
            raise RuntimeError("sealed predicate was expected to expose an empty sector")
        if min(abs(mode) for mode in intended_sector(320)) != 120:
            raise RuntimeError("intended coarsest pi-sector boundary is not mode 120")

        h2_tail = analytic_tail(ledgers["development"], "DEV-DIRECT-POTENTIAL-H2")
        h3_tail = analytic_tail(ledgers["confirmation"], "HOLDOUT-DIRECT-POTENTIAL-H3")
        if mp.mpf(h2_tail) > THRESHOLD or mp.mpf(h3_tail) > THRESHOLD:
            raise RuntimeError("pre-outcome analytic leakage bound exceeds its gate")

        report = {
            "status": "post_result_pi_sector_defect_reproduced",
            "evidence_use": "audit_only_not_a_registered_outcome",
            "intended_definition": "abs(q) >= 3*pi/4, equivalently 8*abs(r) >= 3*N",
            "sealed_implemented_predicate": "4*abs(r) >= 3*N",
            "buggy_sector_mode_counts": buggy_counts,
            "intended_sector_mode_counts": intended_counts,
            "coarsest_intended_mode_abs_min": 120,
            "analytic_probability_uppers": {
                "DEV-DIRECT-POTENTIAL-H2": h2_tail,
                "HOLDOUT-DIRECT-POTENTIAL-H3": h3_tail,
            },
            "registered_threshold": "1e-24",
            "content_addressed_inputs": EXPECTED_SHA256,
            "corrected_non_gating_rough_control": mp.nstr(
                corrected_rough_control(), 80, strip_zeros=False
            ),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
