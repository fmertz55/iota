from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from expression_handoff_branch_ensemble import build_branch_state, select_source_events
from iota_rig import World, load_config
from phase_free_class_matrix import run_to_checkpoint
from phase_source_minimization_audit import discover_config
from terminal_candidate_ledger import run_case


TARGET_SEED = 46
TARGET_START = 420
TARGET_BRANCH_OFFSET = 424
TARGET_SAMPLE = 78
TARGET_BRANCH_SEED = 2026081178
TARGET_TERMINAL_RELATIVE = 10
TARGET_SOURCE = (40, 17, 19)
TARGET_SUCCESSOR = (39, 17, 19)
TARGET_ORDER = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay one frozen Finding 066 gate decision.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--event-csv", default="output/findings/finding060/phase_free_constraint_transport_events.csv")
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--horizon", type=int, default=128)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matches = [(e, o) for e, o in select_source_events(Path(args.event_csv))
               if int(e["init_seed"]) == TARGET_SEED and int(e["start_offset"]) == TARGET_START]
    if len(matches) != 1 or matches[0][1] != TARGET_BRANCH_OFFSET:
        raise RuntimeError("frozen replay source not found")
    event, branch_offset = matches[0]
    cfg = load_config(discover_config(args.config_dir, TARGET_SEED))
    checkpoint: World = run_to_checkpoint(cfg, "takeover_only_vector_phase", args.checkpoint_tick)
    base = build_branch_state(event, branch_offset, checkpoint, cfg)
    baseline, _ = run_case(event, branch_offset, *base, TARGET_SAMPLE, TARGET_BRANCH_SEED, args.horizon, cfg)
    interventions: list[dict[str, Any]] = []

    def override(relative: int, row: dict[str, Any]) -> bool | None:
        if (relative == TARGET_TERMINAL_RELATIVE
                and tuple(row["source"]) == TARGET_SOURCE
                and tuple(row["target"]) == TARGET_SUCCESSOR
                and int(row["candidate_order"]) == TARGET_ORDER):
            interventions.append(dict(row))
            return True
        return None

    replay, _ = run_case(event, branch_offset, *base, TARGET_SAMPLE, TARGET_BRANCH_SEED, args.horizon, cfg, override)
    if len(interventions) != 1:
        raise RuntimeError(f"expected exactly one intervention, observed {len(interventions)}")
    result = {
        "frozen_intervention": {
            "branch_seed": TARGET_BRANCH_SEED,
            "terminal_offset": TARGET_BRANCH_OFFSET + TARGET_TERMINAL_RELATIVE + 1,
            "source": TARGET_SOURCE,
            "target": TARGET_SUCCESSOR,
            "candidate_order": TARGET_ORDER,
            "natural_gate_draw": interventions[0]["gate_draw"],
            "transfer_probability": interventions[0]["transfer_probability"],
            "natural_gate_passed": interventions[0]["natural_gate_passed"],
            "forced_gate_passed": True,
            "rng_draw_still_consumed": True,
        },
        "baseline": baseline,
        "intervention": replay,
        "handoff_flipped": int(baseline["handoff_success"]) == 0 and int(replay["handoff_success"]) == 1,
        "exactly_one_gate_overridden": True,
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
