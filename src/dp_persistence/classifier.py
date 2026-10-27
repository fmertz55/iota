"""Classifier and hypothesis outcomes (estimators.json classification,
iota_spreading.json hypotheses), primary implementation.

Every reference value and tolerance is read from the spec at runtime.
"""

from __future__ import annotations

from typing import Any

from .protocol import spec


EXPONENT_KEYS = ("delta", "theta_or_eta", "z")


def _reference(class_id: str) -> dict[str, Any]:
    return spec("reference_classes.json")["classes"][class_id]


def reference_exponent(class_id: str, key: str) -> float:
    exponents = _reference(class_id)["exponents"]
    if key == "theta_or_eta":
        key = "eta" if "eta" in exponents else "theta"
    return float(exponents[key]["value"])


def registered_classes(dimension_key: str) -> list[str]:
    classification = spec("estimators.json")["classification"]
    return list(classification[f"registered_classes_{dimension_key}"])


def tolerance(dimension_key: str, key: str) -> float:
    table = spec("estimators.json")["classification"]["absolute_tolerances"][dimension_key]
    if key == "theta_or_eta" and "theta_or_eta" not in table:
        key = "theta"
    return float(table[key])


def hyperscaling_threshold() -> float:
    # estimators.json consistency_checks: "|...| <= 0.10"
    text = spec("estimators.json")["consistency_checks"]["DP"]
    return float(text.rsplit("<=", 1)[1])


def per_exponent(estimate: dict[str, float], reference: float, tol: float) -> str:
    gap = abs(estimate["value"] - reference)
    if gap <= tol:
        return "agrees"
    if gap > tol + 2.0 * estimate["total_se"]:
        return "disagrees"
    return "indeterminate"


def hyperscaling(class_id: str, estimates: dict[str, dict[str, float]]) -> dict[str, Any]:
    """DP: theta - (d/z - 2 delta); DyP: eta - (d/z - 2 delta - 1)."""

    d = float(_reference(class_id)["spatial_dimension"])
    delta = estimates["delta"]["value"]
    activity = estimates["theta_or_eta"]["value"]
    z = estimates["z"]["value"]
    predicted = d / z - 2.0 * delta
    if class_id.startswith("DyP"):
        predicted -= 1.0
    residual = activity - predicted
    return {"residual": residual, "passes": abs(residual) <= hyperscaling_threshold()}


def verdict_from_per_class(per_class: dict[str, str]) -> str:
    matches = [c for c, status in per_class.items() if status == "match"]
    if len(matches) == 1 and all(
        status == "excluded" for c, status in per_class.items() if c != matches[0]
    ):
        return matches[0]
    if per_class and all(status == "excluded" for status in per_class.values()):
        return "none_of_registered"
    return "indeterminate"


def classify(estimates: dict[str, dict[str, float]], dimension_key: str) -> dict[str, Any]:
    per_exp: dict[str, dict[str, str]] = {}
    per_class: dict[str, str] = {}
    checks: dict[str, dict[str, Any]] = {}
    for class_id in registered_classes(dimension_key):
        statuses = {
            key: per_exponent(
                estimates[key],
                reference_exponent(class_id, key),
                tolerance(dimension_key, key),
            )
            for key in EXPONENT_KEYS
        }
        per_exp[class_id] = statuses
        if all(s == "agrees" for s in statuses.values()):
            status = "match"
        elif any(s == "disagrees" for s in statuses.values()):
            status = "excluded"
        else:
            status = "indeterminate"
        checks[class_id] = hyperscaling(class_id, estimates)
        if status == "match" and not checks[class_id]["passes"]:
            status = "indeterminate"
        per_class[class_id] = status
    return {
        "per_exponent": per_exp,
        "per_class": per_class,
        "hyperscaling": checks,
        "verdict": verdict_from_per_class(per_class),
    }


# ----------------------------------------------------------------------------
# Hypotheses H1 to H3
# ----------------------------------------------------------------------------


def _percolation_threshold() -> float:
    return float(spec("reference_classes.json")["thresholds"]["simple_cubic_site_percolation_z6"]["p_c"])


def _h1_tolerance() -> float:
    text = spec("iota_spreading.json")["hypotheses"]["H1_threshold"]["outcomes"]["equal"]
    return float(text.rsplit("<=", 1)[1])


def h1_outcome(rho_c: float, se: float) -> str:
    p_c = _percolation_threshold()
    tol = _h1_tolerance()
    gap = rho_c - p_c
    if abs(gap) <= tol:
        return "equal"
    if gap > tol + 2.0 * se:
        return "budget_shifted"
    if gap < -tol - 2.0 * se:
        return "instrument_failure"
    return "indeterminate"


def h2_outcome(h1: str, classification: dict[str, Any] | None) -> str:
    if h1 != "equal":
        return "not_applicable"
    if classification is None:
        return "indeterminate"
    dyp = classification["per_exponent"]["DyP_3"]
    if dyp["delta"] == "agrees" and dyp["theta_or_eta"] == "agrees" and dyp["z"] == "disagrees":
        return "percolation_statics_non_epidemic_dynamics"
    verdict = classification["verdict"]
    if verdict == "DyP_3":
        return "supported"
    if verdict in ("DP_3p1", "none_of_registered"):
        return "falsified"
    return "indeterminate"


def static_reference() -> float:
    return float(spec("reference_classes.json")["classes"]["DyP_3"]["exponents"]["static_tau"]["value"]) - 2.0


def static_tolerance() -> float:
    return float(spec("iota_spreading.json")["hypotheses"]["H3_static_cluster_tail"]["tolerance"])


def h3_outcome(h1: str, static_tail: dict[str, Any] | None) -> str:
    if h1 != "equal":
        return "not_applicable"
    if static_tail is None or static_tail.get("status") != "estimated":
        return "indeterminate"
    estimate = static_tail["tau_minus_2"]
    gap = abs(estimate["value"] - static_reference())
    tol = static_tolerance()
    if gap <= tol:
        return "supported"
    if gap > tol + 2.0 * estimate["total_se"]:
        return "falsified"
    return "indeterminate"


def calibration_prediction(expected_class: str, verdict: str | None) -> str:
    if verdict is None or verdict == "indeterminate":
        return "indeterminate"
    return "supported" if verdict == expected_class else "falsified"
