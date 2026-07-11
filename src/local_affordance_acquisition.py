from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import local_affordance_screen as screen


FINDING = "072A"
INIT_SEEDS = tuple(range(233, 361))
CONTINUATION_SEED_BASE = 20_260_720
MINIMUM_NEW_SOURCES = 3
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding072/local_affordance_acquisition"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the frozen Finding 072 source-acquisition batch over seeds "
            "233..360 before any affordance response."
        )
    )
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument(
        "--canonical-config",
        type=Path,
        default=screen.reusable.DEFAULT_CANONICAL_CONFIG,
    )
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def objective_for_seed(seed: int) -> str:
    return f"finding072_local_affordance_acquisition_seed{int(seed)}"


def candidate_id(row: dict[str, Any]) -> str:
    return (
        f"f072-seed{int(row['init_seed']):03d}-"
        f"sample{int(row['sample_index']):02d}-"
        f"split{int(row['start_offset']):03d}-"
        f"rebridge{int(row['rebridge_offset']):03d}"
    )


def freeze_source_ids(rows: list[dict[str, Any]]) -> None:
    eligible_by_seed: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        if int(row["singleton_eligible"]) == 1:
            eligible_by_seed.setdefault(int(row["init_seed"]), []).append(row)
    selected = [
        min(
            candidates,
            key=lambda row: (
                int(row["sample_index"]),
                int(row["start_offset"]),
                int(row["rebridge_offset"]),
            ),
        )
        for _, candidates in sorted(eligible_by_seed.items())
    ]
    for source_index, row in enumerate(selected, start=1):
        row["frozen_source_selected"] = 1
        row["source_index"] = source_index
        row["source_id"] = f"f072-source-{source_index:03d}"


def configure() -> None:
    screen.FINDING = FINDING
    screen.INIT_SEEDS = INIT_SEEDS
    screen.DISCOVERY_SEEDS = ()
    screen.CONFIRMATION_SEEDS = INIT_SEEDS
    screen.CONTINUATION_SEED_BASE = CONTINUATION_SEED_BASE
    screen.objective_for_seed = objective_for_seed
    screen.candidate_id = candidate_id
    screen.freeze_source_ids = freeze_source_ids


def main() -> None:
    args = parse_args()
    configure()
    summary = screen.run_screen(args)
    summary.update(
        {
            "finding": FINDING,
            "acquisition_batch": True,
            "all_sources_assigned_to_confirmation": True,
            "minimum_new_sources": MINIMUM_NEW_SOURCES,
            "new_sources": int(summary["frozen_primary_sources"]),
            "acquisition_gate_met": int(summary["frozen_primary_sources"])
            >= MINIMUM_NEW_SOURCES,
            "affordance_responses_run": False,
        }
    )
    summary_path = args.output_prefix.with_name(
        args.output_prefix.name + "_summary.json"
    )
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
