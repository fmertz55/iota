from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from component_bridge_causal_trace import write_csv
from expression_handoff_branch_ensemble import (
    build_branch_state,
    fisher_exact_two_sided,
    select_source_events,
)
from iota_rig import World, load_config
from lineage_continuation_rule import (
    DATASET_FIELDNAMES,
    FEATURES,
    PER_SOURCE_FIELDNAMES,
    apply_model,
    confusion,
    run_endpoint,
    source_metrics,
    train_stump,
)
from phase_free_class_matrix import run_to_checkpoint
from phase_source_minimization_audit import discover_config


ELIGIBLE_FEATURES = tuple(
    feature for feature in FEATURES if feature != "singleton_lineage_size"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze a single-address death-tick child rule and test fresh branches."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument(
        "--discovery-dataset",
        default="output/findings/finding064/lineage_continuation_rule_dataset.csv",
    )
    parser.add_argument(
        "--event-csv",
        default="output/findings/finding060/phase_free_constraint_transport_events.csv",
    )
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--first-confirmation-sample", type=int, default=32)
    parser.add_argument("--confirmation-samples", type=int, default=32)
    parser.add_argument("--horizon", type=int, default=128)
    parser.add_argument("--branch-seed-base", type=int, default=2026071100)
    return parser.parse_args()


def load_discovery(path: Path) -> tuple[list[dict[str, Any]], int]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    training = [row for row in rows if row["split"] == "train"]
    eligible = [row for row in training if float(row["singleton_lineage_size"]) == 1.0]
    excluded = len(training) - len(eligible)
    if not eligible:
        raise RuntimeError("no eligible single-address discovery rows")
    return eligible, excluded


def main() -> None:
    args = parse_args()
    if int(args.first_confirmation_sample) != 32 or int(args.confirmation_samples) != 32:
        raise ValueError("Finding 065 preregistration requires fresh branch samples 32..63")

    discovery, discovery_excluded = load_discovery(Path(args.discovery_dataset))
    model = train_stump(discovery, ELIGIBLE_FEATURES)
    apply_model(discovery, model)
    discovery_metrics = confusion(discovery)
    model_record = {
        "feature": model["feature"],
        "threshold": model["threshold"],
        "direction": model["direction"],
        "eligible_features": list(ELIGIBLE_FEATURES),
        "discovery_rows": len(discovery),
        "discovery_excluded_preexisting_descendant_rows": discovery_excluded,
        "discovery_metrics": discovery_metrics,
    }
    print(
        f"frozen model {model_record['feature']} {model_record['direction']} "
        f"{model_record['threshold']} discovery_bal={discovery_metrics['balanced_accuracy']:.3f}",
        flush=True,
    )

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

    confirmation: list[dict[str, Any]] = []
    for source_index, (event, branch_offset) in enumerate(sources):
        seed = int(event["init_seed"])
        branch_world, lineages, singleton_index, singleton_original = build_branch_state(
            event, branch_offset, checkpoints[seed], configs[seed]
        )
        first = int(args.first_confirmation_sample)
        last = first + int(args.confirmation_samples)
        for branch_sample in range(first, last):
            branch_seed = int(args.branch_seed_base) + source_index * 10_000 + branch_sample
            row = run_endpoint(
                event,
                branch_offset,
                branch_world,
                lineages,
                singleton_index,
                singleton_original,
                branch_sample,
                branch_seed,
                int(args.horizon),
                0,
                configs[seed],
            )
            row["split"] = "confirmation"
            confirmation.append(row)
        print(f"confirmation seed={seed} event={event['start_offset']} rows={args.confirmation_samples}", flush=True)

    eligible = [
        row for row in confirmation if float(row["singleton_lineage_size"]) == 1.0
    ]
    excluded = [
        row for row in confirmation if float(row["singleton_lineage_size"]) != 1.0
    ]
    apply_model(confirmation, model_record)
    metrics = confusion(eligible)
    fisher_p = fisher_exact_two_sided(
        int(metrics["true_positive"]),
        int(metrics["false_negative"]),
        int(metrics["false_positive"]),
        int(metrics["true_negative"]),
    )
    per_source = source_metrics(eligible)

    prefix = Path(args.output_prefix)
    dataset_path = prefix.with_name(prefix.name + "_confirmation.csv")
    per_source_path = prefix.with_name(prefix.name + "_per_source.csv")
    model_path = prefix.with_name(prefix.name + "_model.json")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(dataset_path, DATASET_FIELDNAMES, confirmation)
    write_csv(per_source_path, PER_SOURCE_FIELDNAMES, per_source)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "model": model_record,
        "confirmation_rows": len(confirmation),
        "confirmation_eligible_single_address_rows": len(eligible),
        "confirmation_excluded_preexisting_descendant_rows": len(excluded),
        "confirmation_metrics": metrics,
        "confirmation_fisher_exact_two_sided_p": fisher_p,
        "per_source": per_source,
        "all_payload_zero": all(int(row["payload_zero_all_offsets"]) for row in confirmation),
        "all_ledger_exact": all(int(row["ledger_exact_all_offsets"]) for row in confirmation),
        "collision_rows": sum(int(row["lineage_collision"]) for row in confirmation),
        "confirmation_csv": str(dataset_path),
        "per_source_csv": str(per_source_path),
        "model_json": str(model_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"confirmation eligible={len(eligible)} excluded={len(excluded)} "
        f"bal={metrics['balanced_accuracy']:.3f} sensitivity={metrics['sensitivity']:.3f} "
        f"specificity={metrics['specificity']:.3f} p={fisher_p:.6g}",
        flush=True,
    )


if __name__ == "__main__":
    main()
