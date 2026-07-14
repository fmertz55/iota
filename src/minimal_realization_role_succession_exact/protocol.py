"""Outcome-free constants for MIR-ROLE-SUCCESSION-EXACT-001.

Importing this module does not evaluate a registered rule.  The continuation
first attempts a state-independent local impossibility proof and invokes an
uncapped orbit replay only when that proof leaves a logically possible pass
context.
"""

from __future__ import annotations


PROTOCOL_VERSION = "0.1-draft"
SEARCH_ID = "MIR-ROLE-SUCCESSION-EXACT-001"
RUN_ID = f"{SEARCH_ID}-DEVELOPMENT"
FREEZE_TAG = "mir-role-succession-exact-001-v0.1-frozen"
DATA_CLASS = "development_outcome_contingent_exact_closure"

PARENT_SEARCH_ID = "MIR-ROLE-SUCCESSION-001"
PARENT_RESULT_REF = (
    "output/minimal_realization/MIR-ROLE-SUCCESSION-001/"
    "role_succession_results.json"
)
PARENT_RESULT_SHA256 = (
    "1af33377789c117c913c0a5a613f2f102e2a5511f720714a609739c5d362a6f5"
)
PARENT_RESULT_COMMIT = "9b83fc8e1c9f0a034d6240677c9220bbcafa04cf"
PARENT_RESOURCE_BOUNDARY = 1_000_000
PARENT_RECURRENCE_EXCLUDED_COUNT = 245
PARENT_RESOURCE_CENSORED_COUNT = 10

PRIMARY_CYCLE_SIZE = 64
EMBEDDING_CYCLE_SIZES = (96, 128)
CANONICAL_ORIGIN = 0
CONE_SATURATION_LAYER = 32
FORMATION_HORIZON = 29
SUCCESSOR_OFFSETS = (0, 1)
LOCAL_CONTEXT_OFFSETS = tuple(range(-2, 6))
LOCAL_CONTEXT_COUNT = 8
REGISTERED_WORKER_PROCESSES = 4

OUTCOME_SEAL_REF = (
    "experiments/minimal_realization/MIR-ROLE-SUCCESSION-EXACT-001/"
    "role_succession_exact_outcome_seal.json"
)
CANDIDATE_MANIFEST_REF = (
    "experiments/minimal_realization/MIR-ROLE-SUCCESSION-EXACT-001/"
    "role_succession_exact_candidates.jsonl"
)
OPEN_MANIFEST_REF = (
    "experiments/minimal_realization/MIR-ROLE-SUCCESSION-EXACT-001/"
    "role_succession_exact_open_manifest.json"
)
RESULT_PATH_REF = (
    "output/minimal_realization/MIR-ROLE-SUCCESSION-EXACT-001/"
    "role_succession_exact_results.json"
)
SPEC_DIR_REF = "specs/icp_minimal_realization_role_succession_exact/v0.1-draft"
RESULT_SCHEMA_REF = f"{SPEC_DIR_REF}/result.schema.json"
CONTRACT_REF = (
    "docs/ICP_MINIMAL_INFORMATIONAL_REALIZATION_ROLE_SUCCESSION_EXACT_CONTRACT.md"
)
SOURCE_DIR_REF = "src/minimal_realization_role_succession_exact"
TEST_DIR_REF = "tests/minimal_realization_role_succession_exact"

SYMBOLIC_ROUTES = (
    "homogeneous_comparator_obstruction",
    "empty_local_pass_context_set",
)
DYNAMIC_TERMINAL_STATUSES = (
    "exact_pass_on_fixed_orbit",
    "recurrence_excluded_on_fixed_orbit",
)
TERMINAL_CLASSIFICATIONS = (
    "symbolically_unreachable",
    *DYNAMIC_TERMINAL_STATUSES,
)


def opening_condition() -> str:
    return (
        "add the complete disabled outcome seal in a commit whose parent lacks "
        f"it; tag that exact commit with annotated {FREEZE_TAG}; then add only "
        "the open manifest in its direct child"
    )
