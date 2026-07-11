from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import component_labels, csv_bool, write_csv
from continuation import clone_world
from expression_handoff_branch_ensemble import (
    SOURCE_EVENTS,
    build_branch_state,
    fisher_exact_two_sided,
    select_source_events,
)
from expression_lineage_transport import advance_lineages, lineage_relation
from iota_rig import (
    World,
    active_neighbor_coords,
    candidate_neighbor_steps,
    load_config,
    vector_step,
)
from phase_free_class_matrix import run_to_checkpoint
from phase_free_constraint_transport import ledger_error
from phase_source_minimization_audit import clamp_stored_phase, discover_config, phase_source_patch


FEATURES = (
    "time_from_rebridge",
    "singleton_lineage_size",
    "source_A",
    "source_R",
    "source_V",
    "source_angular_L",
    "face6_active_neighbors",
    "face18_active_neighbors",
    "cube26_active_neighbors",
    "cube26_depleted_neighbors",
    "cube26_latent_neighbors",
    "source_removal_component_delta",
    "primary_target_active",
    "primary_target_depleted",
    "primary_target_latent",
    "range_active_targets",
    "range_depleted_targets",
    "range_latent_targets",
    "lineage_reachable",
    "lineage_shortest_path",
)

DATASET_FIELDNAMES = [
    "init_seed",
    "event_start_offset",
    "branch_offset",
    "branch_sample",
    "branch_seed",
    "split",
    "terminal_offset",
    *FEATURES,
    "handoff_success",
    "predicted_handoff",
    "lineage_collision",
    "payload_zero_all_offsets",
    "ledger_exact_all_offsets",
]

PER_SOURCE_FIELDNAMES = [
    "split",
    "init_seed",
    "event_start_offset",
    "rows",
    "positives",
    "negatives",
    "true_positive",
    "false_positive",
    "true_negative",
    "false_negative",
    "accuracy",
    "sensitivity",
    "specificity",
    "balanced_accuracy",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Learn and hold out a one-feature prospective expression-continuation rule."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument(
        "--event-csv",
        default="output/findings/finding060/phase_free_constraint_transport_events.csv",
    )
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--train-samples", type=int, default=16)
    parser.add_argument("--horizon", type=int, default=128)
    parser.add_argument("--branch-seed-base", type=int, default=2026071100)
    return parser.parse_args()


def target_coord(
    source: tuple[int, int, int],
    delta: tuple[int, int, int],
    size: int,
    wrap: bool,
) -> tuple[int, int, int] | None:
    target = tuple(int(source[index] + delta[index]) for index in range(3))
    if wrap:
        return tuple(value % size for value in target)
    if all(0 <= value < size for value in target):
        return target
    return None


def target_status(world: World, target: tuple[int, int, int]) -> tuple[int, int, int]:
    active = int(bool(world.active[target]))
    latent = int((not active) and int(world.latent_A[target]) > 0)
    depleted = int((not active) and int(world.latent_A[target]) <= 0)
    return active, depleted, latent


def terminal_features(
    world: World,
    lineages: list[set[tuple[int, int, int]]],
    singleton_index: int,
    singleton_original: tuple[int, int, int],
    time_from_rebridge: int,
) -> dict[str, float]:
    source = singleton_original
    a = int(world.A[source])
    r = int(world.R[source])
    v = int(world.V[source]) % len(world.vectors)
    p = int(world.P[source])
    primary = vector_step(world, v, a, r, p)
    primary_target = target_coord(
        source,
        (int(primary[0]), int(primary[1]), int(primary[2])),
        world.size,
        bool(world.wrap),
    )
    primary_status = (0, 0, 0) if primary_target is None else target_status(world, primary_target)

    range_active = 0
    range_depleted = 0
    range_latent = 0
    seen: set[tuple[int, int, int]] = set()
    for raw_delta in candidate_neighbor_steps("cube26"):
        delta = tuple(int(value) for value in raw_delta)
        distance = math.sqrt(sum(value * value for value in delta))
        if distance > max(r, 1):
            continue
        target = target_coord(source, delta, world.size, bool(world.wrap))
        if target is None or target in seen:
            continue
        seen.add(target)
        active, depleted, latent = target_status(world, target)
        range_active += active
        range_depleted += depleted
        range_latent += latent

    labels, _, component_count, _ = component_labels(
        world.active, bool(world.wrap), "cube26"
    )
    removed = world.active.copy()
    removed[source] = False
    _, _, removed_count, _ = component_labels(removed, bool(world.wrap), "cube26")
    alive, reachability, shortest_path = lineage_relation(world, lineages)
    return {
        "time_from_rebridge": float(time_from_rebridge),
        "singleton_lineage_size": float(len(lineages[singleton_index])),
        "source_A": float(a),
        "source_R": float(r),
        "source_V": float(v),
        "source_angular_L": float(world.angular_L[source]),
        "face6_active_neighbors": float(
            len(active_neighbor_coords(world, source, "face6"))
        ),
        "face18_active_neighbors": float(
            len(active_neighbor_coords(world, source, "face18"))
        ),
        "cube26_active_neighbors": float(
            len(active_neighbor_coords(world, source, "cube26"))
        ),
        "cube26_depleted_neighbors": float(range_depleted),
        "cube26_latent_neighbors": float(range_latent),
        "source_removal_component_delta": float(removed_count - component_count),
        "primary_target_active": float(primary_status[0]),
        "primary_target_depleted": float(primary_status[1]),
        "primary_target_latent": float(primary_status[2]),
        "range_active_targets": float(range_active),
        "range_depleted_targets": float(range_depleted),
        "range_latent_targets": float(range_latent),
        "lineage_reachable": float(alive and reachability == 1.0),
        "lineage_shortest_path": float(shortest_path) if shortest_path != "" else -1.0,
    }


def run_endpoint(
    event: dict[str, str],
    branch_offset: int,
    branch_world: World,
    branch_lineages: list[set[tuple[int, int, int]]],
    singleton_index: int,
    singleton_original: tuple[int, int, int],
    branch_sample: int,
    branch_seed: int,
    horizon: int,
    train_samples: int,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    world = clone_world(branch_world, branch_seed)
    lineages = [set(lineage) for lineage in branch_lineages]
    terminated = [False, False]
    collision = False
    payload_zero = True
    ledger_exact = True
    try:
        with phase_source_patch(event["variant"]):
            clamp_stored_phase(world, event["variant"])
            for relative in range(horizon):
                payload_zero = payload_zero and int(np.count_nonzero(world.P)) == 0
                ledger_exact = ledger_exact and ledger_error(world) == 0.0
                pre_features = terminal_features(
                    world,
                    lineages,
                    singleton_index,
                    singleton_original,
                    relative,
                )
                events: list[dict[str, Any]] = []
                iota_rig.HARD_TRANSFER_TRACE_HOOK = events.append
                iota_rig.step(world, cfg)
                iota_rig.HARD_TRANSFER_TRACE_HOOK = None
                clamp_stored_phase(world, event["variant"])
                next_lineages, collided, _, _ = advance_lineages(
                    lineages, world, events
                )
                collision = collision or collided
                for index in range(2):
                    if terminated[index]:
                        next_lineages[index] = set()
                    elif not next_lineages[index]:
                        terminated[index] = True
                if not bool(world.active[singleton_original]):
                    return {
                        "init_seed": int(event["init_seed"]),
                        "event_start_offset": int(event["start_offset"]),
                        "branch_offset": branch_offset,
                        "branch_sample": branch_sample,
                        "branch_seed": branch_seed,
                        "split": "train" if branch_sample < train_samples else "test",
                        "terminal_offset": branch_offset + relative + 1,
                        **pre_features,
                        "handoff_success": csv_bool(
                            bool(next_lineages[singleton_index]) and not collision
                        ),
                        "predicted_handoff": "",
                        "lineage_collision": csv_bool(collision),
                        "payload_zero_all_offsets": csv_bool(payload_zero),
                        "ledger_exact_all_offsets": csv_bool(ledger_exact),
                    }
                lineages = next_lineages
    finally:
        iota_rig.HARD_TRANSFER_TRACE_HOOK = None
    raise RuntimeError(
        f"censored endpoint seed={event['init_seed']} event={event['start_offset']} sample={branch_sample}"
    )


def confusion(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(int(row["handoff_success"]) == 1 and int(row["predicted_handoff"]) == 1 for row in rows)
    fp = sum(int(row["handoff_success"]) == 0 and int(row["predicted_handoff"]) == 1 for row in rows)
    tn = sum(int(row["handoff_success"]) == 0 and int(row["predicted_handoff"]) == 0 for row in rows)
    fn = sum(int(row["handoff_success"]) == 1 and int(row["predicted_handoff"]) == 0 for row in rows)
    sensitivity = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return {
        "rows": len(rows),
        "positives": tp + fn,
        "negatives": tn + fp,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "accuracy": (tp + tn) / len(rows) if rows else 0.0,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "balanced_accuracy": 0.5 * (sensitivity + specificity),
    }


def predict(value: float, threshold: float, direction: str) -> int:
    if direction == "le_positive":
        return int(value <= threshold)
    return int(value > threshold)


def train_stump(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for feature in FEATURES:
        values = sorted({float(row[feature]) for row in rows})
        thresholds = [values[0] - 1e-9, values[-1] + 1e-9]
        thresholds.extend(
            0.5 * (left + right) for left, right in zip(values, values[1:])
        )
        for threshold in sorted(set(thresholds)):
            for direction in ("gt_positive", "le_positive"):
                trial = [
                    {**row, "predicted_handoff": predict(float(row[feature]), threshold, direction)}
                    for row in rows
                ]
                metric = confusion(trial)
                candidates.append(
                    {
                        "feature": feature,
                        "threshold": threshold,
                        "direction": direction,
                        **metric,
                    }
                )
    return sorted(
        candidates,
        key=lambda row: (
            -float(row["balanced_accuracy"]),
            str(row["feature"]),
            float(row["threshold"]),
            str(row["direction"]),
        ),
    )[0]


def apply_model(rows: list[dict[str, Any]], model: dict[str, Any]) -> None:
    for row in rows:
        row["predicted_handoff"] = predict(
            float(row[model["feature"]]),
            float(model["threshold"]),
            str(model["direction"]),
        )


def source_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    keys = sorted(
        {
            (str(row["split"]), int(row["init_seed"]), int(row["event_start_offset"]))
            for row in rows
        }
    )
    for split, seed, event_start in keys:
        selected = [
            row
            for row in rows
            if row["split"] == split
            and int(row["init_seed"]) == seed
            and int(row["event_start_offset"]) == event_start
        ]
        output.append(
            {
                "split": split,
                "init_seed": seed,
                "event_start_offset": event_start,
                **confusion(selected),
            }
        )
    return output


def main() -> None:
    args = parse_args()
    if int(args.samples) != 32 or int(args.train_samples) != 16:
        raise ValueError("Finding 064 preregistration requires 32 samples and 16 training samples")
    sources = select_source_events(Path(args.event_csv))
    seeds = sorted({int(event["init_seed"]) for event, _ in sources})
    configs = {
        seed: load_config(discover_config(args.config_dir, seed)) for seed in seeds
    }
    checkpoints: dict[int, World] = {}
    for seed in seeds:
        print(f"checkpoint seed={seed} variant=takeover_only_vector_phase", flush=True)
        checkpoints[seed] = run_to_checkpoint(
            configs[seed], "takeover_only_vector_phase", int(args.checkpoint_tick)
        )

    rows: list[dict[str, Any]] = []
    for source_index, (event, branch_offset) in enumerate(sources):
        seed = int(event["init_seed"])
        branch_world, lineages, singleton_index, singleton_original = build_branch_state(
            event, branch_offset, checkpoints[seed], configs[seed]
        )
        for branch_sample in range(int(args.samples)):
            branch_seed = int(args.branch_seed_base) + source_index * 10_000 + branch_sample
            rows.append(
                run_endpoint(
                    event,
                    branch_offset,
                    branch_world,
                    lineages,
                    singleton_index,
                    singleton_original,
                    branch_sample,
                    branch_seed,
                    int(args.horizon),
                    int(args.train_samples),
                    configs[seed],
                )
            )
        print(f"features seed={seed} event={event['start_offset']} rows={args.samples}", flush=True)

    training = [row for row in rows if row["split"] == "train"]
    testing = [row for row in rows if row["split"] == "test"]
    model = train_stump(training)
    apply_model(rows, model)
    training_metrics = confusion(training)
    testing_metrics = confusion(testing)
    test_fisher = fisher_exact_two_sided(
        int(testing_metrics["true_positive"]),
        int(testing_metrics["false_negative"]),
        int(testing_metrics["false_positive"]),
        int(testing_metrics["true_negative"]),
    )
    per_source = source_metrics(rows)

    prefix = Path(args.output_prefix)
    dataset_path = prefix.with_name(prefix.name + "_dataset.csv")
    per_source_path = prefix.with_name(prefix.name + "_per_source.csv")
    model_path = prefix.with_name(prefix.name + "_model.json")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(dataset_path, DATASET_FIELDNAMES, rows)
    write_csv(per_source_path, PER_SOURCE_FIELDNAMES, per_source)
    model_record = {
        "feature": model["feature"],
        "threshold": model["threshold"],
        "direction": model["direction"],
        "training_metrics": training_metrics,
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "rows": len(rows),
        "training_rows": len(training),
        "testing_rows": len(testing),
        "features": list(FEATURES),
        "model": model_record,
        "held_out_metrics": testing_metrics,
        "held_out_fisher_exact_two_sided_p": test_fisher,
        "per_source": per_source,
        "all_payload_zero": all(int(row["payload_zero_all_offsets"]) for row in rows),
        "all_ledger_exact": all(int(row["ledger_exact_all_offsets"]) for row in rows),
        "collision_rows": sum(int(row["lineage_collision"]) for row in rows),
        "dataset_csv": str(dataset_path),
        "per_source_csv": str(per_source_path),
        "model_json": str(model_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"model {model_record['feature']} {model_record['direction']} "
        f"{model_record['threshold']} train_bal={training_metrics['balanced_accuracy']:.3f} "
        f"test_bal={testing_metrics['balanced_accuracy']:.3f} p={test_fisher:.6g}",
        flush=True,
    )


if __name__ == "__main__":
    main()
