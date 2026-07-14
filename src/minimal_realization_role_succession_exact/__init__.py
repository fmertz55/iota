"""Exact, outcome-blind closure tools for the role-succession search."""

from .local_impossibility import (
    CONTEXT_OFFSETS,
    EMPTY_LOCAL_PASS_CONTEXT_SET,
    HOMOGENEOUS_COMPARATOR_OBSTRUCTION,
    ContextIdentity,
    LocalContextAssessment,
    LocalImpossibilityCertificate,
    analyze_local_impossibility,
    evaluate_truth_table_bit,
)

__all__ = [
    "CONTEXT_OFFSETS",
    "EMPTY_LOCAL_PASS_CONTEXT_SET",
    "HOMOGENEOUS_COMPARATOR_OBSTRUCTION",
    "ContextIdentity",
    "LocalContextAssessment",
    "LocalImpossibilityCertificate",
    "analyze_local_impossibility",
    "evaluate_truth_table_bit",
]
