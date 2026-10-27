"""Seed derivation for ICP-DP-PERSISTENCE-001.

Every stream is numpy PCG64 seeded with the integer formed by the first 8
big-endian bytes of SHA-256 over an ASCII domain string whose fields are
separated by NUL.  Calibration, IOTA, bootstrap, and timing domains differ in
their field structure, so no two can collide.
"""

from __future__ import annotations

import hashlib

import numpy as np

from .protocol import SEARCH_ID


IOTA_STREAM_KINDS = ("medium", "dynamics")
BOOTSTRAP_TAG = "bootstrap"
TIMING_DOMAIN = "TIMING-ONLY"


def domain_seed(*fields: str) -> int:
    """Integer seed from the NUL-joined ASCII domain string."""

    for field in fields:
        if type(field) is not str or "\0" in field:
            raise ValueError("domain fields must be NUL-free strings")
    domain = "\0".join(fields).encode("ascii")
    return int.from_bytes(hashlib.sha256(domain).digest()[:8], "big")


def generator(seed: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(seed))


def control_string(value: float) -> str:
    """Decimal string of a control value (shortest round-trip repr).

    See SPEC_QUESTIONS.md Q-RNG-1.
    """

    value = float(value)
    if not np.isfinite(value):
        raise ValueError("control value must be finite")
    return repr(value)


def calibration_seed(model_id: str, control: float, run_index: int) -> int:
    if type(run_index) is not int or run_index < 0:
        raise ValueError("run index must be a nonnegative int")
    return domain_seed(SEARCH_ID, model_id, control_string(control), str(run_index))


def calibration_stream(model_id: str, control: float, run_index: int) -> np.random.Generator:
    """The single stream of one calibration run (see Q-RNG-2)."""

    return generator(calibration_seed(model_id, control, run_index))


def iota_seed(kind: str, run_seed: int) -> int:
    if kind not in IOTA_STREAM_KINDS:
        raise ValueError(f"unknown IOTA stream kind {kind!r}")
    if type(run_seed) is not int or run_seed < 0:
        raise ValueError("run seed must be a nonnegative int")
    return domain_seed(SEARCH_ID, kind, str(run_seed))


def iota_streams(run_seed: int) -> tuple[np.random.Generator, np.random.Generator]:
    """(medium, dynamics) streams of one IOTA run."""

    return generator(iota_seed("medium", run_seed)), generator(iota_seed("dynamics", run_seed))


def bootstrap_stream(model_id: str, control: float, purpose: str) -> np.random.Generator:
    """Domain-separated bootstrap stream for one evaluated point.

    ``purpose`` distinguishes resampling uses, e.g. 'criticality' or
    'static_tail'.  The tag field makes it disjoint from every simulation
    domain (see Q-RNG-3).
    """

    return generator(
        domain_seed(SEARCH_ID, BOOTSTRAP_TAG, model_id, control_string(control), purpose)
    )


def timing_streams(run_index: int) -> tuple[np.random.Generator, np.random.Generator]:
    """Disposable streams for resource timing; never a registered domain."""

    return (
        generator(domain_seed(TIMING_DOMAIN, "medium", str(run_index))),
        generator(domain_seed(TIMING_DOMAIN, "dynamics", str(run_index))),
    )
