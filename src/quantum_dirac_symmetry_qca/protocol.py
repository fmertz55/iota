"""Outcome-free constants for the direct symmetry-derived Dirac-QCA draft."""

from __future__ import annotations


PROTOCOL_VERSION = "0.1-draft"
SEARCH_ID = "ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001"
CANDIDATE_ID = "QDIR-DIRECT-SYMMETRY-QCA-001"
STATUS = "outcome_free_execution_pipeline_reviewed_seal_ready_not_frozen"

SPEC_DIR_REF = "specs/icp_quantum_dirac_symmetry_qca/v0.1-draft"
CONTRACT_REF = "docs/ICP_QUANTUM_DIRAC_SYMMETRY_QCA_CONTRACT.md"
EXPERIMENT_DIR_REF = (
    "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001"
)
OUTCOME_SEAL_REF = f"{EXPERIMENT_DIR_REF}/outcome_seal_v0.2.json"
DEVELOPMENT_OPEN_REF = (
    f"{EXPERIMENT_DIR_REF}/development_open_manifest_v0.2.json"
)
CONFIRMATION_OPEN_REF = (
    f"{EXPERIMENT_DIR_REF}/confirmation_open_manifest_v0.2.json"
)
DEVELOPMENT_RESULT_REF = (
    "output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/"
    "development_results_v0.2.json"
)
CONFIRMATION_RESULT_REF = (
    "output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/"
    "confirmation_results_v0.2.json"
)
FREEZE_TAG = "icp-quantum-dirac-symmetry-qca-001-v0.2-frozen"

DESIGN_FILENAMES = (
    "protocol.json",
    "candidate.json",
    "target.json",
    "maps.json",
    "scenarios.json",
    "states.json",
    "partitions.json",
    "algebraic_fixtures.json",
    "threshold_certificate.json",
    "design.schema.json",
    "open_manifest.schema.json",
    "result.schema.json",
    "literature_basis.md",
    "README.md",
)

MANIFEST_FILENAMES = (
    "candidate_manifest.json",
    "scenario_manifest.json",
    "state_manifest.json",
    "partition_manifest.json",
)

IMPLEMENTATION_FILENAMES = (
    "authorization.py",
    "cli.py",
    "independent_verifier.py",
    "independent_registered.py",
    "independent_states.py",
    "ledger.py",
    "lifecycle.py",
    "manifest.py",
    "production.py",
    "reducers.py",
    "runner.py",
    "seal.py",
    "states.py",
)

REGISTERED_SIZES = (320, 640, 1280)
REGISTERED_DELTAS = ("1/20", "1/40", "1/80")
REGISTERED_OBSERVATION_TIMES = ("2/5", "4/5", "6/5", "8/5", "2")
DEVELOPMENT_SCENARIOS = (
    "DEV-DIRECT-FREE-POS",
    "DEV-DIRECT-FREE-NEG",
    "DEV-DIRECT-SIGN-QUENCH",
    "DEV-DIRECT-POTENTIAL-H2",
)
CONFIRMATION_SCENARIOS = (
    "HOLDOUT-DIRECT-MASS-PULSE",
    "HOLDOUT-DIRECT-POTENTIAL-H3",
)
REGISTERED_SCENARIOS = DEVELOPMENT_SCENARIOS + CONFIRMATION_SCENARIOS

DEVELOPMENT_STATES = (
    "DEV-DIRECT-STATE-POS",
    "DEV-DIRECT-STATE-NEG",
    "DEV-DIRECT-STATE-INTERFERENCE",
    "DEV-DIRECT-STATE-ZITTER",
)
CONFIRMATION_STATES = (
    "HOLDOUT-DIRECT-STATE-POS",
    "HOLDOUT-DIRECT-STATE-NEG",
    "HOLDOUT-DIRECT-STATE-INTERFERENCE",
    "HOLDOUT-DIRECT-STATE-ZITTER",
)

INPUT_R_MIN = -4
INPUT_R_MAX = 4
TARGET_R_CUTOFF = 72
PHYSICAL_LENGTH = 16
PHYSICAL_HORIZON = 2
PRECISION_BITS = 256
WORK_DPS = 90
INDEPENDENT_DPS = 110
PRIMARY_LIBRARY_VERSION = "0.9.0"
INDEPENDENT_LIBRARY_VERSION = "1.3.0"

ALLOWED_FIXTURE_SIZES = (6, 10)
ALLOWED_TARGET_FIXTURE_CUTOFF = 3
REJECTED_PARENT_SIZES = (256, 512, 1024)
FORBIDDEN_PRE_FREEZE_PATHS = (
    OUTCOME_SEAL_REF,
    DEVELOPMENT_OPEN_REF,
    CONFIRMATION_OPEN_REF,
    DEVELOPMENT_RESULT_REF,
    CONFIRMATION_RESULT_REF,
)

DIRECT_DISTANCE_THRESHOLDS = {
    320: "0.0040",
    640: "0.0012",
    1280: "0.0004",
}
POTENTIAL_DISTANCE_THRESHOLDS = {
    320: "0.020",
    640: "0.011",
    1280: "0.006",
}
DIRECT_REFINEMENT_RATIO = "0.35"
POTENTIAL_REFINEMENT_RATIO = "0.62"
REFINEMENT_MARGIN = "1e-10"
NEAR_ZERO_THRESHOLD = "1e-12"

POSITION_TV_MAX = "0.010"
MOMENTUM_TV_MAX = "0.010"
TOTAL_CURRENT_ERROR_MAX = "0.020"
LOCAL_CURRENT_L1_MAX = "0.020"
INFIDELITY_MAX = "0.0001"
ZITTER_CURRENT_SUP_MAX = "0.020"
PI_SECTOR_PROBABILITY_MAX = "1e-24"
NUMERICAL_NORM_RESIDUAL_MAX = "1e-12"
INDEPENDENT_STATE_DISAGREEMENT_MAX = "1e-11"
PARITY_NUMERICAL_RESIDUAL_MAX = "1e-12"
TIME_REVERSAL_FINE_MAX = "0.020"
