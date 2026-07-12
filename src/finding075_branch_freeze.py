from __future__ import annotations

import csv
import json
from pathlib import Path

from component_bridge_causal_trace import write_csv
from experiment_db import artifact_hash


SOURCE = Path("output/findings/finding075/successor_graph_rewire_manifest.csv")
OUTPUT = Path("output/findings/finding075/successor_graph_branch_manifest.csv")
SUMMARY = Path("output/findings/finding075/successor_graph_branch_freeze_summary.json")
SOURCE_SHA256 = "b1605fa59101839dbb79d9aca8522fbc8af2e0e65541835e60aea8eb3b5ae41d"
BRANCHES_PER_CHANNEL = 16
BRANCH_SEED_BASE = 2_026_075_000
FIELDS = [
    "paired_channel_id", "paired_channel_index", "init_seed", "sample_index",
    "precursor_offset", "split_offset", "branch_index", "branch_seed",
    "variants", "outcomes_run",
]


def main() -> None:
    if artifact_hash(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("Finding 075 paired-channel manifest changed")
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        channels = list(csv.DictReader(handle))
    rows = []
    for channel in channels:
        channel_index = int(channel["paired_channel_index"])
        for branch_index in range(BRANCHES_PER_CHANNEL):
            rows.append(
                {
                    "paired_channel_id": channel["paired_channel_id"],
                    "paired_channel_index": channel_index,
                    "init_seed": int(channel["init_seed"]),
                    "sample_index": int(channel["sample_index"]),
                    "precursor_offset": int(channel["precursor_offset"]),
                    "split_offset": int(channel["split_offset"]),
                    "branch_index": branch_index,
                    "branch_seed": BRANCH_SEED_BASE + channel_index * 100 + branch_index,
                    "variants": "natural;role_preserving;role_breaking",
                    "outcomes_run": 0,
                }
            )
    write_csv(OUTPUT, FIELDS, rows)
    summary = {
        "finding": "075D",
        "protocol": "frozen common-RNG articulation susceptibility branches",
        "source_manifest": str(SOURCE),
        "source_manifest_sha256": artifact_hash(SOURCE),
        "channels": len(channels),
        "branches_per_channel": BRANCHES_PER_CHANNEL,
        "branch_assignments": len(rows),
        "variants_per_assignment": 3,
        "causal_outcomes_run": False,
        "branch_manifest": str(OUTPUT),
        "branch_manifest_sha256": artifact_hash(OUTPUT),
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
