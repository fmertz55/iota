from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import local_affordance_screen as screen


FINDING = "079A"
INIT_SEEDS = tuple(range(553, 745))
CONTINUATION_SEED_BASE = 20_260_790
MINIMUM_FACTORIAL_CHANNELS = 20
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding079/factorial_acquisition"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Acquire new Finding 079 strict transports without causal outcomes."
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
    return f"finding079_factorial_acquisition_seed{int(seed)}"


def candidate_id(row: dict[str, Any]) -> str:
    return (
        f"f079-seed{int(row['init_seed']):03d}-"
        f"sample{int(row['sample_index']):02d}-"
        f"split{int(row['start_offset']):03d}-"
        f"rebridge{int(row['rebridge_offset']):03d}"
    )


def configure() -> None:
    screen.FINDING = FINDING
    screen.INIT_SEEDS = INIT_SEEDS
    screen.DISCOVERY_SEEDS = ()
    screen.CONFIRMATION_SEEDS = INIT_SEEDS
    screen.CONTINUATION_SEED_BASE = CONTINUATION_SEED_BASE
    screen.objective_for_seed = objective_for_seed
    screen.candidate_id = candidate_id


def main() -> None:
    args = parse_args()
    configure()
    summary = screen.run_screen(args)
    summary.update(
        {
            "finding": FINDING,
            "acquisition_batch": True,
            "new_outcome_free_initialization_seeds": len(INIT_SEEDS),
            "minimum_factorial_channels_before_intervention": MINIMUM_FACTORIAL_CHANNELS,
            "counterfactual_outcomes_run": False,
        }
    )
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.json")
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
