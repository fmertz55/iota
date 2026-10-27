"""Registered stage runners.  Imported by the CLI only after its gates pass.

The parallel unit is one complete run; results are collected in canonical
(increasing seed or run-index) order; nothing is written until a whole result
is assembled and validated.  There are no grid, run-count, or worker
overrides at the registered entry points.
"""

from __future__ import annotations

import math
import multiprocessing
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable, Sequence

import numpy as np

from . import calibration_models, classifier, l0_engine
from .estimators import (
    EvaluatedPoint,
    PointEvaluation,
    bracket_search,
    evaluate_point,
    exponent_estimates,
    static_tail_estimate,
    static_tail_point,
    t_min_for,
    threshold_estimate,
)
from .ledger import point_trace_sha256
from .protocol import LAW_ID, REGISTERED_WORKER_PROCESSES, SEARCH_ID, spec
from .rng import bootstrap_stream, control_string


SECONDS_PER_HOUR = 3600.0


class ResourceCeiling(RuntimeError):
    pass


def per_point_ceiling_seconds() -> float:
    envelope = spec("iota_spreading.json")["resource_envelope"]
    return float(envelope["per_point_wall_clock_ceiling_hours"]) * SECONDS_PER_HOUR


# ----------------------------------------------------------------------------
# Worker tasks (module level so spawn workers can import them)
# ----------------------------------------------------------------------------


def _calibration_task(task: tuple[str, float, int]) -> dict[str, Any]:
    model_id, control, run_index = task
    return calibration_models.run_registered(model_id, control, run_index)


def _iota_task(task: tuple[float, int, int]) -> dict[str, Any]:
    rho, run_seed, horizon = task
    return l0_engine.run(rho, run_seed, horizon)


def run_tasks(
    function: Callable[[Any], dict[str, Any]],
    tasks: Sequence[Any],
    *,
    workers: int,
    ceiling_seconds: float,
) -> list[dict[str, Any]]:
    """Run tasks on spawn workers, collecting in task order.

    Raises ResourceCeiling (after terminating the pool) when the wall clock
    for this point exceeds the ceiling; partial results are discarded.
    """

    start = time.monotonic()
    results: list[dict[str, Any]] = []
    context = multiprocessing.get_context("spawn")
    with context.Pool(processes=workers) as pool:
        for record in pool.imap(function, tasks, chunksize=1):
            results.append(record)
            if time.monotonic() - start > ceiling_seconds:
                pool.terminate()
                raise ResourceCeiling("per-point wall-clock ceiling exceeded")
    return results


# ----------------------------------------------------------------------------
# Point evaluation
# ----------------------------------------------------------------------------


@dataclass
class ModelPlan:
    model_id: str
    dimension_key: str
    coarse_grid: list[float]
    bisection_steps: int
    runs_coarse: int
    runs_bisection: int
    runs_final: int
    horizon: int
    midpoint_kind: str
    expected_class: str | None
    static: bool


def calibration_plan(model_id: str) -> ModelPlan:
    from .protocol import calibration_model

    model = calibration_model(model_id)
    dimension = "1p1" if model["lattice"]["spatial_dimension"] == 1 else "3d"
    return ModelPlan(
        model_id=model_id,
        dimension_key=dimension,
        coarse_grid=list(model["coarse_grid"]),
        bisection_steps=model["bisection_steps"],
        runs_coarse=model["runs_per_coarse_point"],
        runs_bisection=model["runs_per_bisection_point"],
        runs_final=model["runs_at_final_point"],
        horizon=model["horizon_layers"],
        midpoint_kind="arithmetic",
        expected_class=model["expected_class"],
        static=model.get("static_gate") is not None,
    )


def iota_plan() -> ModelPlan:
    grid = spec("iota_spreading.json")["control_grid"]
    return ModelPlan(
        model_id=LAW_ID,
        dimension_key="3d",
        coarse_grid=list(grid["coarse"]),
        bisection_steps=6,
        runs_coarse=grid["runs_per_coarse_point"],
        runs_bisection=grid["runs_per_bisection_point"],
        runs_final=grid["runs_at_final_point"],
        horizon=grid["horizon_ticks"],
        # iota_spreading.json says arithmetic; see SPEC_QUESTIONS.md Q-EST-6.
        midpoint_kind="arithmetic",
        expected_class=None,
        static=True,
    )


def _resource_censored(t_min: int, runs: int) -> PointEvaluation:
    return PointEvaluation(
        t_min=t_min,
        t_max=None,
        criticality="resource_censored",
        slope_s=None,
        slope_ci95=None,
        ladder=[],
        censored_run_fraction=0.0,
        runs=runs,
    )


def exploration_summary(control: float, records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    absorbed = [r for r in records if r["absorbed_at"] is not None]
    values = [r["E"] for r in absorbed if r.get("E") is not None]
    stranded = [r["stranded_amplitude"] for r in absorbed if r.get("stranded_amplitude") is not None]
    return {
        "control_value": control,
        "absorbed_runs": len(absorbed),
        "median_E": float(statistics.median(values)) if values else None,
        "fraction_E_below_1": (sum(1 for v in values if v < 1) / len(values)) if values else None,
        "mean_stranded_amplitude": (sum(stranded) / len(stranded)) if stranded else None,
    }


class PointRunner:
    """Evaluates points of one model and remembers per-point data."""

    def __init__(
        self,
        plan: ModelPlan,
        *,
        seed_block: Callable[[int, float, int], list[int]],
        task_for: Callable[[float, int], Any],
        task_function: Callable[[Any], dict[str, Any]],
        workers: int = REGISTERED_WORKER_PROCESSES,
        ceiling_seconds: float | None = None,
    ) -> None:
        self.plan = plan
        self.seed_block = seed_block
        self.task_for = task_for
        self.task_function = task_function
        self.workers = workers
        self.ceiling = per_point_ceiling_seconds() if ceiling_seconds is None else ceiling_seconds
        self.t_min = t_min_for(plan.dimension_key)
        self.static_by_point: dict[int, dict[str, Any]] = {}
        self.exploration: list[dict[str, Any]] = []
        self.max_residual = 0

    def evaluate(self, control: float, role: str, index: int, runs: int | None = None) -> EvaluatedPoint:
        plan = self.plan
        if runs is None:
            runs = plan.runs_coarse if role == "coarse" else plan.runs_bisection
        seeds = self.seed_block(index, control, runs)
        tasks = [self.task_for(control, seed) for seed in seeds]
        try:
            records = run_tasks(self.task_function, tasks, workers=self.workers, ceiling_seconds=self.ceiling)
        except ResourceCeiling:
            evaluation = _resource_censored(self.t_min, runs)
            return EvaluatedPoint(control, role, evaluation, {"seeds": seeds, "trace": None})
        domain = f"{SEARCH_ID}\0{plan.model_id}\0{role}\0{control_string(control)}"
        trace = point_trace_sha256(domain, zip(seeds, records))
        evaluation = evaluate_point(
            records,
            t_min=self.t_min,
            horizon=plan.horizon,
            boot_rng=bootstrap_stream(plan.model_id, control, f"{role}:criticality"),
        )
        extra: dict[str, Any] = {"seeds": seeds, "trace": trace}
        if plan.static:
            extra["static"] = static_tail_point(
                records, boot_rng=bootstrap_stream(plan.model_id, control, f"{role}:static_tail")
            )
        if plan.model_id == LAW_ID:
            self.exploration.append(exploration_summary(control, records))
            residuals = [int(r["ledger_residual"]) for r in records]
            self.max_residual = max([self.max_residual, *residuals])
        return EvaluatedPoint(control, role, evaluation, extra)


def point_entry(point: EvaluatedPoint) -> dict[str, Any]:
    seeds = point.extra["seeds"]
    entry = {
        "control_value": point.control,
        "role": point.role,
        "runs": len(seeds),
        "seed_first": seeds[0],
        "seed_last": seeds[-1],
        **point.evaluation.summary(),
    }
    if point.extra.get("trace") is not None:
        entry["ledger_trace_sha256"] = point.extra["trace"]
    return entry


def assemble_model_result(
    runner: PointRunner, search, final: EvaluatedPoint | None
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    plan = runner.plan
    points = list(search.points) + ([final] if final is not None else [])
    result: dict[str, Any] = {
        "model_id": plan.model_id,
        "terminal_status": search.terminal_status,
        "brackets": search.brackets,
        "final_control_value": search.final_control,
        "points": [point_entry(p) for p in points],
        "exponents": None,
    }
    estimates = None
    if final is not None and search.final_bracket is not None:
        lo, hi = search.final_bracket
        if final.evaluation.criticality in ("window_too_short", "resource_censored"):
            result["terminal_status"] = final.evaluation.criticality
        estimates = exponent_estimates(final.evaluation, lo.evaluation, hi.evaluation)
        result["crossover_in_window"] = final.evaluation.crossover_in_window
        if plan.static:
            result["static_tail"] = static_tail_estimate(
                final.extra["static"], lo.extra.get("static"), hi.extra.get("static")
            )
    result["exponents"] = estimates
    classification = classifier.classify(estimates, plan.dimension_key) if estimates else None
    if classification is not None:
        result["per_class"] = classification["per_class"]
        result["hyperscaling"] = classification["hyperscaling"]
        result["verdict"] = classification["verdict"]
    else:
        result["verdict"] = "indeterminate"
    return result, classification


# ----------------------------------------------------------------------------
# Stage C
# ----------------------------------------------------------------------------


def _calibration_runner(model_id: str, **kwargs) -> PointRunner:
    plan = calibration_plan(model_id)
    used: dict[str, int] = {}

    def seed_block(index: int, control: float, runs: int) -> list[int]:
        key = control_string(control)
        start = used.get(key, 0)
        used[key] = start + runs
        return list(range(start, start + runs))

    return PointRunner(
        plan,
        seed_block=seed_block,
        task_for=lambda control, run_index: (model_id, control, run_index),
        task_function=_calibration_task,
        **kwargs,
    )


def calibration_model_result(model_id: str, **kwargs) -> dict[str, Any]:
    from .protocol import calibration_model

    runner = _calibration_runner(model_id, **kwargs)
    plan = runner.plan
    search = bracket_search(runner.evaluate, plan.coarse_grid, plan.bisection_steps, plan.midpoint_kind)
    final = None
    if search.final_control is not None:
        final = runner.evaluate(search.final_control, "final", -1, runs=plan.runs_final)
    result, classification = assemble_model_result(runner, search, final)
    model = calibration_model(model_id)
    gate = model.get("threshold_gate")
    if gate is not None and search.final_bracket is not None:
        reference = _resolve_reference(gate["reference"])
        estimate = threshold_estimate(*search.final_bracket)["value"]
        result["threshold_gate"] = {
            "reference": reference,
            "estimate": estimate,
            "tolerance": gate["absolute_tolerance"],
            "passes": abs(estimate - reference) <= gate["absolute_tolerance"],
        }
    else:
        result["threshold_gate"] = None
    result["prediction_outcome"] = classifier.calibration_prediction(
        plan.expected_class, result.get("verdict") if classification else None
    )
    return result


def _resolve_reference(dotted: str) -> float:
    value: Any = spec("reference_classes.json")
    for part in dotted.split("."):
        value = value[part]
    return float(value)


def calibration_gates_pass(result: dict[str, Any]) -> tuple[bool, list[str]]:
    """Every calibration model returns its class, threshold, and static exponent."""

    failures = []
    for model_result in result["models"]:
        from .protocol import calibration_model

        model = calibration_model(model_result["model_id"])
        if model_result.get("terminal_status") not in ("classified",):
            failures.append(f"{model['model_id']}: terminal status {model_result.get('terminal_status')}")
        if model_result.get("verdict") != model["expected_class"]:
            failures.append(f"{model['model_id']}: verdict {model_result.get('verdict')}")
        gate = model_result.get("threshold_gate")
        if model.get("threshold_gate") is not None and not (gate and gate.get("passes")):
            failures.append(f"{model['model_id']}: threshold gate")
        static_gate = model.get("static_gate")
        if static_gate is not None:
            tail = model_result.get("static_tail") or {}
            estimate = (tail.get("tau_minus_2") or {}).get("value")
            if estimate is None or abs(estimate - static_gate["reference"]) > static_gate["absolute_tolerance"]:
                failures.append(f"{model['model_id']}: static gate")
    return (not failures), failures


def run_calibration(**kwargs) -> list[dict[str, Any]]:
    return [calibration_model_result(model_id, **kwargs) for model_id in calibration_models.MODEL_IDS]


# ----------------------------------------------------------------------------
# Stage S and K
# ----------------------------------------------------------------------------


def _iota_runner(first_seed: int, horizon: int, **kwargs) -> PointRunner:
    def seed_block(index: int, control: float, runs: int) -> list[int]:
        start = first_seed + 25000 * index
        return list(range(start, start + runs))

    return PointRunner(
        iota_plan(),
        seed_block=seed_block,
        task_for=lambda rho, run_seed: (rho, run_seed, horizon),
        task_function=_iota_task,
        **kwargs,
    )


FINAL_GRID_INDEX = 16


def development_model_result(**kwargs) -> dict[str, Any]:
    partitions = spec("partitions.json")["iota_development"]
    plan = iota_plan()
    runner = _iota_runner(partitions["run_seed_range"]["first"], plan.horizon, **kwargs)
    return iota_search_result(runner)


def iota_search_result(runner: PointRunner) -> dict[str, Any]:
    """Coarse grid, bisection, final point, H1 to H3 for one IOTA runner."""

    plan = runner.plan
    search = bracket_search(runner.evaluate, plan.coarse_grid, plan.bisection_steps, plan.midpoint_kind)
    final = None
    if search.final_control is not None:
        final = runner.evaluate(search.final_control, "final", FINAL_GRID_INDEX, runs=plan.runs_final)
    result, classification = assemble_model_result(runner, search, final)
    result["exploration"] = runner.exploration
    result["ledger_max_abs_residual"] = runner.max_residual
    hypotheses: dict[str, Any] | None = None
    if search.final_bracket is not None:
        rho_c = threshold_estimate(*search.final_bracket)
        h1 = classifier.h1_outcome(rho_c["value"], rho_c["total_se"])
        hypotheses = {
            "H1_threshold": h1,
            "H2_dynamic_class": classifier.h2_outcome(h1, classification),
            "H3_static_tail": classifier.h3_outcome(h1, result.get("static_tail")),
            "rho_c": rho_c,
        }
        if h1 == "instrument_failure":
            result["terminal_status"] = "instrument_failure"
    result["hypotheses"] = hypotheses
    result["prediction_outcome"] = development_prediction_outcome(hypotheses)
    return result


def development_prediction_outcome(hypotheses: dict[str, Any] | None) -> str:
    """The H2 prediction outcome; the non-epidemic label is indeterminate (Q-S-2)."""

    if hypotheses is None:
        return "not_applicable"
    h2 = hypotheses["H2_dynamic_class"]
    return h2 if h2 in ("supported", "falsified", "not_applicable") else "indeterminate"


def confirmation_model_result(frozen: dict[str, Any], development: dict[str, Any], **kwargs) -> dict[str, Any]:
    """Single use at the three development-frozen rho values (Q-K-1)."""

    partitions = spec("partitions.json")["iota_confirmation"]
    plan = iota_plan()
    runs = partitions["runs_per_point"]
    runner = _iota_runner(partitions["run_seed_range"]["first"], plan.horizon, **kwargs)
    lower = runner.evaluate(frozen["lower"], "confirmation_lower", 0, runs=runs)
    final = runner.evaluate(frozen["final"], "confirmation_final", 1, runs=runs)
    upper = runner.evaluate(frozen["upper"], "confirmation_upper", 2, runs=runs)

    class _Search:
        points = [lower, upper]
        brackets = [[lower.control, upper.control]]
        final_bracket = (lower, upper)
        final_control = final.control
        terminal_status = "classified"

    result, classification = assemble_model_result(runner, _Search, final)
    endpoints_ok = (
        lower.evaluation.criticality == "subcritical"
        and upper.evaluation.criticality in ("supercritical", "no_absorption_observed")
    )
    rho_c = threshold_estimate(lower, upper)
    h1 = classifier.h1_outcome(rho_c["value"], rho_c["total_se"])
    hypotheses = {
        "H1_threshold": h1,
        "H2_dynamic_class": classifier.h2_outcome(h1, classification),
        "H3_static_tail": classifier.h3_outcome(h1, result.get("static_tail")),
        "rho_c": rho_c,
    }
    result["hypotheses"] = hypotheses
    result["exploration"] = runner.exploration
    result["ledger_max_abs_residual"] = runner.max_residual
    dev = development["hypotheses"] or {}
    agrees = endpoints_ok and h1 == dev.get("H1_threshold")
    if h1 == "equal":
        agrees = agrees and hypotheses["H2_dynamic_class"] == dev.get("H2_dynamic_class")
        agrees = agrees and hypotheses["H3_static_tail"] == dev.get("H3_static_tail")
    result["prediction_outcome"] = "supported" if agrees else "falsified"
    return result
