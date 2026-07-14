"""Registered constants for ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001."""

from __future__ import annotations


PROTOCOL_VERSION = "0.1-draft"
SEARCH_ID = "ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001"
CANDIDATE_ID = "QDIR-PRODUCT-WALK-001"
STATUS = "outcome_free_design_active_not_frozen"
FREEZE_TAG = "icp-quantum-dirac-role-recovery-001-v0.1-frozen"

SPEC_DIR_REF = "specs/icp_quantum_dirac_role_recovery/v0.1-draft"
CONTRACT_REF = "docs/ICP_QUANTUM_DIRAC_ROLE_RECOVERY_CONTRACT.md"
EXPERIMENT_DIR_REF = (
    "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001"
)
OUTCOME_SEAL_REF = f"{EXPERIMENT_DIR_REF}/outcome_seal.json"
DEVELOPMENT_OPEN_REF = f"{EXPERIMENT_DIR_REF}/development_open_manifest.json"
CONFIRMATION_OPEN_REF = f"{EXPERIMENT_DIR_REF}/confirmation_open_manifest.json"
DEVELOPMENT_RESULT_REF = (
    "output/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001/"
    "development_results.json"
)
CONFIRMATION_RESULT_REF = (
    "output/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001/"
    "confirmation_results.json"
)

DESIGN_FILENAMES = (
    "protocol.json",
    "candidate.json",
    "target.json",
    "maps.json",
    "scenarios.json",
    "states.json",
    "partitions.json",
    "algebraic_fixtures.json",
    "design.schema.json",
    "result.schema.json",
    "open_manifest.schema.json",
    "literature_basis.md",
    "README.md",
)

REGISTERED_SIZES = (256, 512, 1024)
REGISTERED_DELTAS = ("1/16", "1/32", "1/64")
REGISTERED_OBSERVATION_TIMES = ("1/2", "1", "3/2", "2")
DEVELOPMENT_SCENARIOS = (
    "DEV-FREE-LIGHT",
    "DEV-FREE-HEAVY",
    "DEV-QUENCH-UP",
    "DEV-POTENTIAL-EVEN",
)
CONFIRMATION_SCENARIOS = (
    "HOLDOUT-QUENCH-DOWN",
    "HOLDOUT-POTENTIAL-ODD",
)
REGISTERED_SCENARIOS = DEVELOPMENT_SCENARIOS + CONFIRMATION_SCENARIOS

INPUT_R_MIN = -4
INPUT_R_MAX = 4
TARGET_R_CUTOFF = 64
PHYSICAL_LENGTH = 16
PHYSICAL_HORIZON = 2
PRECISION_BITS = 256
WORK_DPS = 90

ALLOWED_FIXTURE_SIZES = (8, 16)
FORBIDDEN_PRE_FREEZE_PATHS = (
    OUTCOME_SEAL_REF,
    DEVELOPMENT_OPEN_REF,
    CONFIRMATION_OPEN_REF,
    DEVELOPMENT_RESULT_REF,
    CONFIRMATION_RESULT_REF,
)
