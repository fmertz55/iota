"""Frozen, outcome-free constants for MIR-ROLE-SUCCESSION-001.

This module contains design constants only.  Importing it must never evaluate a
candidate trajectory or inspect a result artifact.
"""

from __future__ import annotations


PROTOCOL_VERSION = "0.1-draft"
BASE_CONTRACT_VERSION = "0.2-draft"
SEARCH_ID = "MIR-ROLE-SUCCESSION-001"
RUN_ID = f"{SEARCH_ID}-DEVELOPMENT"
FREEZE_TAG = "mir-role-succession-001-v0.1-frozen"
GRAMMAR_ID = "MIR-CENTERED-INCIDENCE-PRODUCTION-ROW-V0.1"
DETECTOR_ID = "MIR-ISOLATED-DYAD-OUTWARD-EFFECT-CENTERED-V0.1"

PRIMARY_CYCLE_SIZE = 64
EMBEDDING_CYCLE_SIZES = (96, 128)
CANONICAL_ORIGIN = 0
FORMATION_HORIZON = 29
CAUSAL_ENDPOINT_LAG = 2
PRIMARY_CONE_SATURATION_LAYER = PRIMARY_CYCLE_SIZE // 2
MAX_RELATION_HOPS_PER_TICK = 1
MAX_LAYERS_PER_CANDIDATE = 1_000_000
REGISTERED_WORKER_PROCESSES = 4

INPUT_PORTS = ("predecessor", "self", "successor")
SIGNATURE_ORDER = tuple(f"{value:03b}" for value in range(8))
CANDIDATE_COUNT = 1 << len(SIGNATURE_ORDER)
DYNAMIC_CANDIDATE_COUNT = CANDIDATE_COUNT - 1
SHELL_SIZES = (1, 8, 28, 56, 70, 56, 28, 8, 1)

SUCCESSOR_ANCHOR_OFFSETS = (0, 1)
INTERVENTION_WINDOW_OFFSETS = (0, 1, 2)
NATURAL_INTERVENTION_WINDOW = (1, 1, 0)
ROLE_PRESERVING_SHAM = (0, 1, 1)
ROLE_BREAKING_ARM = (1, 0, 1)
EXTERNAL_ENDPOINT_OFFSET = 3

DATA_CLASS = "development_outcome_contingent"
RESULT_ENDPOINT = "first_complete_proto_object_or_exact_post_saturation_recurrence"

CANDIDATE_MANIFEST_REF = (
    "experiments/minimal_realization/MIR-ROLE-SUCCESSION-001/"
    "role_succession_candidates.jsonl"
)
OUTCOME_SEAL_REF = (
    "experiments/minimal_realization/MIR-ROLE-SUCCESSION-001/"
    "role_succession_outcome_seal.json"
)
OPEN_MANIFEST_REF = (
    "experiments/minimal_realization/MIR-ROLE-SUCCESSION-001/"
    "role_succession_open_manifest.json"
)
RESULT_PATH_REF = (
    "output/minimal_realization/MIR-ROLE-SUCCESSION-001/"
    "role_succession_results.json"
)
PARENT_EXACT_RESULT_REF = (
    "output/minimal_realization/MIR-EXACT-ORBIT-001/exact_orbit_results.json"
)
PARENT_EXACT_RESULT_SHA256 = (
    "e6d8ab89edd79422f9a6f5803447d52e642c6873f0275272c519fbd4487023cc"
)


def graph_distance(left: int, right: int, cycle_size: int) -> int:
    """Return shortest unsigned distance on a periodic cycle."""

    if type(cycle_size) is not int or cycle_size < 4:
        raise ValueError("cycle_size must be an integer of at least four")
    if type(left) is not int or type(right) is not int:
        raise TypeError("cycle loci must be integers")
    forward = (left - right) % cycle_size
    return min(forward, cycle_size - forward)


def cone_saturation_layer(cycle_size: int) -> int:
    """Layer at which a radius-one bidirectional cone covers the cycle."""

    if type(cycle_size) is not int or cycle_size < 4:
        raise ValueError("cycle_size must be an integer of at least four")
    return cycle_size // 2


def strict_pre_wrap_horizon(cycle_size: int) -> int:
    """Largest formation layer whose t+2 endpoint remains strictly pre-wrap."""

    if type(cycle_size) is not int or cycle_size < 2 * (CAUSAL_ENDPOINT_LAG + 1):
        raise ValueError("cycle_size is too small for the registered endpoint lag")
    # Solve 2 * (t + lag) < N over integer t without assuming N is even.
    return (cycle_size - 1) // 2 - CAUSAL_ENDPOINT_LAG


if strict_pre_wrap_horizon(PRIMARY_CYCLE_SIZE) != FORMATION_HORIZON:
    raise RuntimeError("primary formation horizon is not the frozen pre-wrap boundary")
