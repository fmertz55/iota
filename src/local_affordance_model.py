from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from component_bridge_causal_trace import write_csv
from realization_necessity import file_sha256


RESPONSE_FIELDS = [
    "natural_handoff_fraction",
    "mean_address_loss_delay_fraction",
    "depth1_alternate_handoff_fraction",
    "gate_failure_fraction",
    "source_exhaustion_fraction",
    "target_preemption_fraction",
]
PENALTIES = (0.1, 1.0, 10.0, 100.0)
RADII = (1, 2, 3)
PERMUTATION_SEED = 20_260_719
MONTE_CARLO_PERMUTATIONS = 100_000
PROFILE_FIELDS = [
    "source_id",
    "split",
    "init_seed",
    "natural_branches",
    "observed_address_losses",
    "unique_child_selectors",
    "depth1_veto_cases",
    "measurement_eligible",
    *RESPONSE_FIELDS,
]
PREDICTION_FIELDS = [
    "source_id",
    "init_seed",
    *[f"observed_{field}" for field in RESPONSE_FIELDS],
    *[f"local_{field}" for field in RESPONSE_FIELDS],
    *[f"intrinsic_{field}" for field in RESPONSE_FIELDS],
    *[f"null_{field}" for field in RESPONSE_FIELDS],
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fit or confirm the frozen Finding 071 affordance model."
    )
    parser.add_argument("--mode", choices=("fit", "evaluate"), required=True)
    parser.add_argument("--split", choices=("discovery", "confirmation"), required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--feature-schema", type=Path, required=True)
    parser.add_argument("--factual-summary", type=Path, required=True)
    parser.add_argument("--natural-cases", type=Path, required=True)
    parser.add_argument("--veto-summary", type=Path, required=True)
    parser.add_argument("--veto-cases", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--expected-model-sha256")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    schema = json.loads(args.feature_schema.read_text(encoding="utf-8"))
    factual = json.loads(args.factual_summary.read_text(encoding="utf-8"))
    veto = json.loads(args.veto_summary.read_text(encoding="utf-8"))
    checks = {
        "split_factual": factual.get("split") == args.split,
        "split_veto": veto.get("split") == args.split,
        "feature_hash": factual.get("feature_schema_sha256")
        == file_sha256(args.feature_schema),
        "selector_hash": factual.get("selectors_sha256")
        == veto.get("selector_sha256"),
        "factual_support": factual.get("measurement_support_gate_met") is True,
        "shams": veto.get("all_matched_shams_exact") is True,
        "selectors": veto.get("all_selectors_matched") is True,
        "identity": veto.get("all_selector_identities_exact") is True,
        "payload": veto.get("all_payload_zero") is True,
        "ledger": veto.get("all_ledger_exact") is True,
        "collisions": int(veto.get("collision_cases", -1)) == 0,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Finding 071 model input validation failed: {checks}")
    return schema, factual, veto


def assemble_profiles(
    args: argparse.Namespace,
    factual: dict[str, Any],
) -> list[dict[str, Any]]:
    natural = read_csv(args.natural_cases)
    veto = read_csv(args.veto_cases)
    eligible = set(factual["measurement_eligible_sources"])
    source_ids = sorted({row["source_id"] for row in natural})
    profiles: list[dict[str, Any]] = []
    for source_id in source_ids:
        natural_rows = [row for row in natural if row["source_id"] == source_id]
        veto_rows = [row for row in veto if row["source_id"] == source_id]
        observed = [row for row in natural_rows if row["outcome_class"] != "censored"]
        if not natural_rows:
            raise RuntimeError(f"Finding 071 source lacks natural rows: {source_id}")
        delays = [
            int(row["terminal_offset"]) - int(row["branch_offset"])
            for row in observed
        ]
        denominator = len(observed)
        veto_denominator = len(veto_rows)
        row = {
            "source_id": source_id,
            "split": args.split,
            "init_seed": int(natural_rows[0]["init_seed"]),
            "natural_branches": len(natural_rows),
            "observed_address_losses": denominator,
            "unique_child_selectors": int(
                factual["eligible_selectors_by_source"].get(source_id, 0)
            ),
            "depth1_veto_cases": veto_denominator,
            "measurement_eligible": int(source_id in eligible),
            "natural_handoff_fraction": (
                sum(int(item["handoff_success"]) for item in observed) / denominator
                if denominator
                else 0.0
            ),
            "mean_address_loss_delay_fraction": (
                float(np.mean(delays)) / 256.0 if delays else 0.0
            ),
            "depth1_alternate_handoff_fraction": (
                sum(item["stage_endpoint"] == "handoff" for item in veto_rows)
                / veto_denominator
                if veto_denominator
                else 0.0
            ),
            "gate_failure_fraction": (
                sum(item["outcome_class"] == "gate_failed" for item in observed)
                / denominator
                if denominator
                else 0.0
            ),
            "source_exhaustion_fraction": (
                sum(item["outcome_class"] == "source_exhausted" for item in observed)
                / denominator
                if denominator
                else 0.0
            ),
            "target_preemption_fraction": (
                sum(item["outcome_class"] == "target_preempted" for item in observed)
                / denominator
                if denominator
                else 0.0
            ),
        }
        profiles.append(row)
    return profiles


def feature_names(schema: dict[str, Any], radius: int | None) -> list[str]:
    names = list(schema["intrinsic_fields"])
    if radius is not None:
        for value in range(1, radius + 1):
            names.extend(schema["environment_fields_by_radius"][str(value)])
    return names


def matrices(
    features: list[dict[str, str]],
    profiles: list[dict[str, Any]],
    names: list[str],
) -> tuple[list[str], np.ndarray, np.ndarray]:
    feature_map = {row["source_id"]: row for row in features}
    rows = [row for row in profiles if int(row["measurement_eligible"]) == 1]
    missing = [row["source_id"] for row in rows if row["source_id"] not in feature_map]
    if missing:
        raise RuntimeError(f"Finding 071 profiles lack features: {missing}")
    ids = [row["source_id"] for row in rows]
    x = np.asarray(
        [[float(feature_map[source_id][name]) for name in names] for source_id in ids],
        dtype=float,
    )
    y = np.asarray(
        [[float(row[name]) for name in RESPONSE_FIELDS] for row in rows], dtype=float
    )
    return ids, x, y


def standardize(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = values.mean(axis=0)
    std = values.std(axis=0, ddof=0)
    keep = std > 1e-12
    safe = np.where(keep, std, 1.0)
    return (values - mean) / safe, mean, safe, keep


def ridge_fit(x: np.ndarray, y: np.ndarray, penalty: float) -> np.ndarray:
    return np.linalg.solve(
        x.T @ x + penalty * np.eye(x.shape[1]), x.T @ y
    )


def loo_error(x: np.ndarray, y: np.ndarray, penalty: float) -> float:
    errors: list[float] = []
    for holdout in range(len(x)):
        train = np.arange(len(x)) != holdout
        x_train, x_mean, x_std, x_keep = standardize(x[train])
        y_train, y_mean, y_std, _ = standardize(y[train])
        coefficients = ridge_fit(x_train[:, x_keep], y_train, penalty)
        x_test = (x[holdout] - x_mean) / x_std
        y_test = (y[holdout] - y_mean) / y_std
        prediction = x_test[x_keep] @ coefficients
        errors.append(float(np.mean((prediction - y_test) ** 2)))
    return float(np.mean(errors))


def fitted_record(
    names: list[str], x: np.ndarray, y: np.ndarray, penalty: float
) -> dict[str, Any]:
    x_standard, x_mean, x_std, x_keep = standardize(x)
    y_standard, y_mean, y_std, _ = standardize(y)
    coefficients = ridge_fit(x_standard[:, x_keep], y_standard, penalty)
    return {
        "input_feature_names": names,
        "retained_feature_names": [
            name for name, keep in zip(names, x_keep) if bool(keep)
        ],
        "x_mean": x_mean.tolist(),
        "x_std": x_std.tolist(),
        "x_keep": x_keep.astype(int).tolist(),
        "y_mean": y_mean.tolist(),
        "y_std": y_std.tolist(),
        "coefficients": coefficients.tolist(),
        "penalty": penalty,
    }


def predict(record: dict[str, Any], x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x_mean = np.asarray(record["x_mean"], dtype=float)
    x_std = np.asarray(record["x_std"], dtype=float)
    keep = np.asarray(record["x_keep"], dtype=bool)
    coefficients = np.asarray(record["coefficients"], dtype=float)
    standardized = ((x - x_mean) / x_std)[:, keep] @ coefficients
    y_mean = np.asarray(record["y_mean"], dtype=float)
    y_std = np.asarray(record["y_std"], dtype=float)
    return standardized, standardized * y_std + y_mean


def fit(args: argparse.Namespace, schema: dict[str, Any], factual: dict[str, Any], profiles: list[dict[str, Any]]) -> None:
    if args.split != "discovery":
        raise ValueError("Finding 071 fit mode requires the discovery split")
    features = [row for row in read_csv(args.features) if row["split"] == "discovery"]
    intrinsic_names = feature_names(schema, None)
    ids, intrinsic_x, y = matrices(features, profiles, intrinsic_names)
    if len(ids) < 6:
        raise RuntimeError("Finding 071 discovery measurement support failed")

    intrinsic_grid = [
        {"penalty": penalty, "loo_mse": loo_error(intrinsic_x, y, penalty)}
        for penalty in PENALTIES
    ]
    intrinsic_choice = min(
        intrinsic_grid, key=lambda row: (row["loo_mse"], -row["penalty"])
    )
    local_grid: list[dict[str, Any]] = []
    local_matrices: dict[int, np.ndarray] = {}
    for radius in RADII:
        names = feature_names(schema, radius)
        _, x, check_y = matrices(features, profiles, names)
        if not np.array_equal(y, check_y):
            raise RuntimeError("Finding 071 response ordering changed")
        local_matrices[radius] = x
        for penalty in PENALTIES:
            local_grid.append(
                {
                    "radius": radius,
                    "penalty": penalty,
                    "loo_mse": loo_error(x, y, penalty),
                }
            )
    local_choice = min(
        local_grid,
        key=lambda row: (row["loo_mse"], row["radius"], -row["penalty"]),
    )
    selected_radius = int(local_choice["radius"])
    model = {
        "finding": "071E",
        "protocol": "frozen multi-response local affordance ridge model",
        "confirmation_outcomes_run": False,
        "response_fields": RESPONSE_FIELDS,
        "minimum_sources_per_split": 6,
        "discovery_source_ids": ids,
        "discovery_sources": len(ids),
        "features_sha256": file_sha256(args.features),
        "feature_schema_sha256": file_sha256(args.feature_schema),
        "factual_summary_sha256": file_sha256(args.factual_summary),
        "natural_cases_sha256": file_sha256(args.natural_cases),
        "veto_summary_sha256": file_sha256(args.veto_summary),
        "veto_cases_sha256": file_sha256(args.veto_cases),
        "penalty_grid": list(PENALTIES),
        "radius_grid": list(RADII),
        "tie_break": "smaller radius then larger penalty",
        "intrinsic_grid": intrinsic_grid,
        "local_grid": local_grid,
        "selected_radius": selected_radius,
        "selected_penalty": float(local_choice["penalty"]),
        "selected_discovery_loo_mse": float(local_choice["loo_mse"]),
        "intrinsic_selected_penalty": float(intrinsic_choice["penalty"]),
        "intrinsic_discovery_loo_mse": float(intrinsic_choice["loo_mse"]),
        "local_model": fitted_record(
            feature_names(schema, selected_radius),
            local_matrices[selected_radius],
            y,
            float(local_choice["penalty"]),
        ),
        "intrinsic_model": fitted_record(
            intrinsic_names,
            intrinsic_x,
            y,
            float(intrinsic_choice["penalty"]),
        ),
    }
    prefix = args.output_prefix
    profiles_path = prefix.with_name(prefix.name + "_profiles.csv")
    model_path = prefix.with_name(prefix.name + "_model.json")
    write_csv(profiles_path, PROFILE_FIELDS, profiles)
    model["profiles_csv"] = str(profiles_path)
    model["profiles_sha256"] = file_sha256(profiles_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(
        json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(model, sort_keys=True), flush=True)


def permutation_pvalue(prediction: np.ndarray, observed: np.ndarray) -> tuple[float, int, str]:
    observed_mse = float(np.mean((prediction - observed) ** 2))
    n = len(observed)
    extreme = 0
    total = 0
    if n <= 9:
        iterator = itertools.permutations(range(n))
        method = "exact"
    else:
        rng = np.random.default_rng(PERMUTATION_SEED)
        permutations = [np.arange(n)]
        permutations.extend(rng.permutation(n) for _ in range(MONTE_CARLO_PERMUTATIONS))
        iterator = permutations
        method = "identity_plus_100000_frozen_permutations"
    for permutation in iterator:
        permuted = observed[np.asarray(permutation, dtype=int)]
        extreme += int(float(np.mean((prediction - permuted) ** 2)) <= observed_mse + 1e-15)
        total += 1
    return extreme / total, total, method


def evaluate(args: argparse.Namespace, schema: dict[str, Any], factual: dict[str, Any], profiles: list[dict[str, Any]]) -> None:
    if args.split != "confirmation" or args.model is None or args.expected_model_sha256 is None:
        raise ValueError("Finding 071 evaluate mode requires confirmation and a frozen model")
    if file_sha256(args.model) != args.expected_model_sha256:
        raise RuntimeError("Finding 071 frozen model hash changed")
    model = json.loads(args.model.read_text(encoding="utf-8"))
    if model.get("confirmation_outcomes_run") is not False:
        raise RuntimeError("Finding 071 model was not frozen before confirmation")
    features = [row for row in read_csv(args.features) if row["split"] == "confirmation"]
    local_names = model["local_model"]["input_feature_names"]
    intrinsic_names = model["intrinsic_model"]["input_feature_names"]
    ids, local_x, y = matrices(features, profiles, local_names)
    check_ids, intrinsic_x, check_y = matrices(features, profiles, intrinsic_names)
    if ids != check_ids or not np.array_equal(y, check_y) or len(ids) < 6:
        raise RuntimeError("Finding 071 confirmation matrix changed or lacks support")
    local_standard, local_raw = predict(model["local_model"], local_x)
    intrinsic_standard, intrinsic_raw = predict(model["intrinsic_model"], intrinsic_x)
    y_mean = np.asarray(model["local_model"]["y_mean"], dtype=float)
    y_std = np.asarray(model["local_model"]["y_std"], dtype=float)
    y_standard = (y - y_mean) / y_std
    null_standard = np.zeros_like(y_standard)
    null_raw = np.broadcast_to(y_mean, y.shape)
    local_mse = float(np.mean((local_standard - y_standard) ** 2))
    intrinsic_mse = float(np.mean((intrinsic_standard - y_standard) ** 2))
    null_mse = float(np.mean((null_standard - y_standard) ** 2))
    local_mae = np.mean(np.abs(local_standard - y_standard), axis=0)
    intrinsic_mae = np.mean(np.abs(intrinsic_standard - y_standard), axis=0)
    improved_dimensions = int(np.count_nonzero(local_mae < intrinsic_mae))
    pvalue, permutation_count, permutation_method = permutation_pvalue(
        local_standard, y_standard
    )
    gate_checks = {
        "source_support": len(ids) >= 6,
        "beats_intrinsic": local_mse < intrinsic_mse,
        "beats_null": local_mse < null_mse,
        "improves_two_dimensions": improved_dimensions >= 2,
        "permutation_p_at_most_0p05": pvalue <= 0.05,
    }
    prediction_rows: list[dict[str, Any]] = []
    profile_map = {row["source_id"]: row for row in profiles}
    for index, source_id in enumerate(ids):
        row: dict[str, Any] = {
            "source_id": source_id,
            "init_seed": profile_map[source_id]["init_seed"],
        }
        for field_index, field in enumerate(RESPONSE_FIELDS):
            row[f"observed_{field}"] = y[index, field_index]
            row[f"local_{field}"] = local_raw[index, field_index]
            row[f"intrinsic_{field}"] = intrinsic_raw[index, field_index]
            row[f"null_{field}"] = null_raw[index, field_index]
        prediction_rows.append(row)

    prefix = args.output_prefix
    profiles_path = prefix.with_name(prefix.name + "_profiles.csv")
    predictions_path = prefix.with_name(prefix.name + "_predictions.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(profiles_path, PROFILE_FIELDS, profiles)
    write_csv(predictions_path, PREDICTION_FIELDS, prediction_rows)
    summary = {
        "finding": "071F",
        "protocol": "held-out local affordance field confirmation",
        "frozen_model_path": str(args.model),
        "frozen_model_sha256": file_sha256(args.model),
        "confirmation_sources": len(ids),
        "confirmation_source_ids": ids,
        "selected_radius": model["selected_radius"],
        "selected_penalty": model["selected_penalty"],
        "local_standardized_mse": local_mse,
        "intrinsic_standardized_mse": intrinsic_mse,
        "null_standardized_mse": null_mse,
        "local_standardized_mae_by_response": dict(zip(RESPONSE_FIELDS, local_mae.tolist())),
        "intrinsic_standardized_mae_by_response": dict(
            zip(RESPONSE_FIELDS, intrinsic_mae.tolist())
        ),
        "dimensions_improved_over_intrinsic": improved_dimensions,
        "permutation_p_value": pvalue,
        "permutation_count": permutation_count,
        "permutation_method": permutation_method,
        "permutation_seed": None if permutation_method == "exact" else PERMUTATION_SEED,
        "gate_checks": gate_checks,
        "local_affordance_field_confirmation_passed": all(gate_checks.values()),
        "profiles_csv": str(profiles_path),
        "predictions_csv": str(predictions_path),
        "all_input_safety_checks_passed": True,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    args = parse_args()
    schema, factual, _ = validate_inputs(args)
    profiles = assemble_profiles(args, factual)
    if args.mode == "fit":
        fit(args, schema, factual, profiles)
    else:
        evaluate(args, schema, factual, profiles)


if __name__ == "__main__":
    main()
