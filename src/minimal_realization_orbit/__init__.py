"""Exact-orbit falsification tools for the frozen MIR reference grammar."""

from .engine import (
    CONE_SATURATION_LAYER,
    MAX_LAYERS_PER_CANDIDATE,
    ExactOrbitOutcome,
    LayerAssessment,
    evaluate_candidate_exact_orbit,
    evaluate_detector_layer,
    trace_joint_orbit,
)

__all__ = [
    "CONE_SATURATION_LAYER",
    "MAX_LAYERS_PER_CANDIDATE",
    "ExactOrbitOutcome",
    "LayerAssessment",
    "evaluate_candidate_exact_orbit",
    "evaluate_detector_layer",
    "trace_joint_orbit",
]
