"""Registered constants for ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001."""

from __future__ import annotations


PROTOCOL_VERSION = "0.1-draft"
SEARCH_ID = "ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001"
CANDIDATE_ID = "QDIR-PRODUCT-WALK-001"
STATUS = "outcome_free_implementation_complete_not_frozen"
FREEZE_TAG = "icp-quantum-dirac-role-recovery-001-v0.2-frozen"
COMPLETION_TAG = "icp-quantum-dirac-role-recovery-001-v0.2-complete"

SPEC_DIR_REF = "specs/icp_quantum_dirac_role_recovery/v0.1-draft"
CONTRACT_REF = "docs/ICP_QUANTUM_DIRAC_ROLE_RECOVERY_CONTRACT.md"
EXPERIMENT_DIR_REF = (
    "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001"
)
OUTCOME_SEAL_REF = f"{EXPERIMENT_DIR_REF}/outcome_seal_v0.2.json"
DEVELOPMENT_OPEN_REF = f"{EXPERIMENT_DIR_REF}/development_open_manifest_v0.2.json"
CONFIRMATION_OPEN_REF = f"{EXPERIMENT_DIR_REF}/confirmation_open_manifest_v0.2.json"
DEVELOPMENT_RESULT_REF = (
    "output/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001/"
    "development_results_v0.2.json"
)
CONFIRMATION_RESULT_REF = (
    "output/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001/"
    "confirmation_results_v0.2.json"
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
INDEPENDENT_DPS = 110
PRIMARY_LIBRARY_VERSION = "0.9.0"
INDEPENDENT_LIBRARY_VERSION = "1.3.0"

ABSOLUTE_DISTANCE_THRESHOLDS = {
    256: "0.20",
    512: "0.10",
    1024: "0.05",
}
REFINEMENT_RATIO = "0.60"
REFINEMENT_MARGIN = "1e-8"
NEAR_ZERO_THRESHOLD = "1e-10"

POSITION_TV_MAX = "0.05"
MOMENTUM_TV_MAX = "0.05"
TOTAL_CURRENT_ERROR_MAX = "0.10"
LOCAL_CURRENT_L1_MAX = "0.10"
INFIDELITY_MAX = "0.0025"
ZITTER_CURRENT_SUP_MAX = "0.10"
NUMERICAL_NORM_RESIDUAL_MAX = "1e-12"
INDEPENDENT_STATE_DISAGREEMENT_MAX = "1e-11"
PARITY_NUMERICAL_RESIDUAL_MAX = "1e-12"
TIME_REVERSAL_FINE_MAX = "0.10"

DEVELOPMENT_STATES = (
    "DEV-STATE-POS",
    "DEV-STATE-NEG",
    "DEV-STATE-INTERFERENCE",
    "DEV-STATE-ZITTER",
)
CONFIRMATION_STATES = (
    "HOLDOUT-STATE-POS",
    "HOLDOUT-STATE-NEG",
    "HOLDOUT-STATE-INTERFERENCE",
    "HOLDOUT-STATE-ZITTER",
)

MANIFEST_REFS = (
    f"{EXPERIMENT_DIR_REF}/candidate_manifest.json",
    f"{EXPERIMENT_DIR_REF}/scenario_manifest.json",
    f"{EXPERIMENT_DIR_REF}/state_manifest.json",
    f"{EXPERIMENT_DIR_REF}/partition_manifest.json",
)

ALLOWED_FIXTURE_SIZES = (8, 16)
FORBIDDEN_PRE_FREEZE_PATHS = (
    OUTCOME_SEAL_REF,
    DEVELOPMENT_OPEN_REF,
    CONFIRMATION_OPEN_REF,
    DEVELOPMENT_RESULT_REF,
    CONFIRMATION_RESULT_REF,
)
