from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

import independent_persistence_screen as reusable
from component_bridge_causal_trace import write_csv
from experiment_db import artifact_hash
from expression_handoff_branch_ensemble import build_branch_state
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from iota_rig import World, load_config, vector_step
from local_affordance_screen import (
    CONFIRMATION_SEEDS,
    DISCOVERY_SEEDS,
    configure_reusable,
)
from phase_free_class_matrix import run_to_checkpoint


RADII = (1, 2, 3)
VECTOR_STATES = 64
DEFAULT_OUTPUT_PREFIX = Path("output/findings/finding071/local_affordance")
INTRINSIC_FIELDS = [
    "source_A",
    "source_R",
    "source_angular_L",
    "source_step_squared_norm",
    "source_step_l1_norm",
    *[f"source_V_{index:02d}" for index in range(VECTOR_STATES)],
]
ENVIRONMENT_BASE_FIELDS = [
    "active_count",
    "depleted_count",
    "latent_count",
    "active_A_sum",
    "active_R_sum",
    "active_abs_angular_L_sum",
    "active_same_V_count",
    "active_step_sq_1_count",
    "active_step_sq_2_count",
    "active_step_sq_3_count",
    "active_behavior_move_count",
    "active_behavior_reflect_count",
    "active_behavior_diffuse_count",
]
ENVIRONMENT_FIELDS = [
    f"r{radius}_{name}"
    for radius in RADII
    for name in ENVIRONMENT_BASE_FIELDS
]
WHOLE_FIELDS = [
    "whole_active_count",
    "whole_latent_count",
    "whole_active_A_sum",
    "whole_active_R_sum",
    "whole_active_abs_angular_L_sum",
]
ID_FIELDS = [
    "source_id",
    "split",
    "init_seed",
    "sample_index",
    "event_start_offset",
    "branch_offset",
    "singleton_original",
]
FEATURE_FIELDS = [*ID_FIELDS, *INTRINSIC_FIELDS, *ENVIRONMENT_FIELDS, *WHOLE_FIELDS]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract frozen pre-outcome Finding 071 local features."
    )
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument(
        "--screen-summary",
        type=Path,
        default=Path("output/findings/finding071/local_affordance_screen_summary.json"),
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=Path(
            "output/findings/finding071/"
            "local_affordance_screen_source_manifest.csv"
        ),
    )
    parser.add_argument(
        "--transport-csv",
        type=Path,
        default=Path(
            "output/findings/finding071/"
            "local_affordance_screen_transport_events.csv"
        ),
    )
    parser.add_argument(
        "--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG
    )
    parser.add_argument("--expected-source-manifest-sha256", required=True)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def selected_sources(args: argparse.Namespace) -> list[dict[str, str]]:
    summary = json.loads(args.screen_summary.read_text(encoding="utf-8"))
    actual_hash = artifact_hash(args.source_manifest)
    checks = {
        "complete": summary.get("screen_complete") is True,
        "prospective": summary.get(
            "protocol_frozen_before_affordance_responses"
        )
        is True,
        "uninspected": summary.get(
            "affordance_branch_or_veto_outcomes_inspected_for_selection"
        )
        is False,
        "support": summary.get("source_support_gate_met") is True,
        "hash_argument": actual_hash == args.expected_source_manifest_sha256,
        "hash_summary": actual_hash
        == summary["artifacts"]["source_manifest_csv"]["sha256"],
    }
    if not all(checks.values()):
        raise RuntimeError(f"Finding 071 source freeze failed: {checks}")
    sources = [
        row
        for row in read_csv(args.source_manifest)
        if int(row["frozen_source_selected"]) == 1
    ]
    if len(sources) != int(summary["frozen_primary_sources"]):
        raise RuntimeError("Finding 071 frozen source count changed")
    return sources


def event_for(
    source: dict[str, str], transports: list[dict[str, str]]
) -> dict[str, str]:
    matches = [
        row
        for row in transports
        if int(row["init_seed"]) == int(source["init_seed"])
        and int(row["sample_index"]) == int(source["sample_index"])
        and int(row["start_offset"]) == int(source["start_offset"])
        and int(row["rebridge_offset"]) == int(source["rebridge_offset"])
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Finding 071 event join failed for {source['source_id']}")
    return matches[0]


def coord_text(coord: tuple[int, int, int]) -> str:
    return ":".join(str(value) for value in coord)


def local_coord(
    source: tuple[int, int, int],
    delta: tuple[int, int, int],
    size: int,
    wrap: bool,
) -> tuple[int, int, int] | None:
    target = tuple(source[index] + delta[index] for index in range(3))
    if wrap:
        return tuple(value % size for value in target)
    if all(0 <= value < size for value in target):
        return target
    return None


def environment_features(
    world: World, source: tuple[int, int, int], radius: int
) -> dict[str, float | int]:
    values: dict[str, float | int] = {
        name: 0 for name in ENVIRONMENT_BASE_FIELDS
    }
    source_v = int(world.V[source]) % VECTOR_STATES
    seen: set[tuple[int, int, int]] = set()
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx == dy == dz == 0:
                    continue
                target = local_coord(
                    source, (dx, dy, dz), world.size, bool(world.wrap)
                )
                if target is None or target in seen:
                    continue
                seen.add(target)
                if bool(world.active[target]):
                    target_v = int(world.V[target]) % VECTOR_STATES
                    values["active_count"] += 1
                    values["active_A_sum"] += int(world.A[target])
                    values["active_R_sum"] += int(world.R[target])
                    values["active_abs_angular_L_sum"] += abs(
                        float(world.angular_L[target])
                    )
                    values["active_same_V_count"] += int(target_v == source_v)
                    step = vector_step(
                        world,
                        target_v,
                        int(world.A[target]),
                        int(world.R[target]),
                        int(world.P[target]),
                    )
                    squared_norm = sum(int(value) ** 2 for value in step[:3])
                    if squared_norm in {1, 2, 3}:
                        values[f"active_step_sq_{squared_norm}_count"] += 1
                    values[f"active_behavior_{step[3]}_count"] += 1
                elif int(world.latent_A[target]) > 0:
                    values["latent_count"] += 1
                else:
                    values["depleted_count"] += 1
    return values


def feature_row(
    source: dict[str, str],
    event: dict[str, str],
    world: World,
    singleton_original: tuple[int, int, int],
) -> dict[str, Any]:
    seed = int(source["init_seed"])
    split = "discovery" if seed in DISCOVERY_SEEDS else "confirmation"
    if seed not in DISCOVERY_SEEDS and seed not in CONFIRMATION_SEEDS:
        raise RuntimeError("Finding 071 source escaped the frozen split")
    source_v = int(world.V[singleton_original]) % VECTOR_STATES
    step = vector_step(
        world,
        source_v,
        int(world.A[singleton_original]),
        int(world.R[singleton_original]),
        int(world.P[singleton_original]),
    )[:3]
    row: dict[str, Any] = {
        "source_id": source["source_id"],
        "split": split,
        "init_seed": seed,
        "sample_index": int(source["sample_index"]),
        "event_start_offset": int(source["start_offset"]),
        "branch_offset": int(source["rebridge_offset"]),
        "singleton_original": coord_text(singleton_original),
        "source_A": int(world.A[singleton_original]),
        "source_R": int(world.R[singleton_original]),
        "source_angular_L": float(world.angular_L[singleton_original]),
        "source_step_squared_norm": sum(int(value) ** 2 for value in step),
        "source_step_l1_norm": sum(abs(int(value)) for value in step),
    }
    for index in range(VECTOR_STATES):
        row[f"source_V_{index:02d}"] = int(index == source_v)
    for radius in RADII:
        for name, value in environment_features(
            world, singleton_original, radius
        ).items():
            row[f"r{radius}_{name}"] = value
    active = world.active.astype(bool)
    row.update(
        {
            "whole_active_count": int(np.count_nonzero(active)),
            "whole_latent_count": int(
                np.count_nonzero((~active) & (world.latent_A > 0))
            ),
            "whole_active_A_sum": int(world.A[active].sum()),
            "whole_active_R_sum": int(world.R[active].sum()),
            "whole_active_abs_angular_L_sum": float(
                np.abs(world.angular_L[active]).sum()
            ),
        }
    )
    return row


def main() -> None:
    args = parse_args()
    configure_reusable()
    sources = selected_sources(args)
    transports = read_csv(args.transport_csv)
    canonical = load_config(args.canonical_config)
    rows: list[dict[str, Any]] = []
    for source in sources:
        seed = int(source["init_seed"])
        event = event_for(source, transports)
        cfg = reusable.config_for_seed(canonical, seed)
        checkpoint = run_to_checkpoint(
            cfg, event["variant"], int(event["checkpoint_tick"])
        )
        world, _, _, singleton_original = build_branch_state(
            event, int(event["rebridge_offset"]), checkpoint, cfg
        )
        rows.append(feature_row(source, event, world, singleton_original))
        print(f"f071 features source={source['source_id']} seed={seed}", flush=True)

    prefix = args.output_prefix
    feature_path = prefix.with_name(prefix.name + "_features.csv")
    schema_path = prefix.with_name(prefix.name + "_feature_schema.json")
    write_csv(feature_path, FEATURE_FIELDS, rows)
    schema = {
        "finding": "071B",
        "features_extracted_before_affordance_responses": True,
        "source_manifest_sha256": artifact_hash(args.source_manifest),
        "radii": list(RADII),
        "vector_states": VECTOR_STATES,
        "intrinsic_fields": INTRINSIC_FIELDS,
        "environment_fields_by_radius": {
            str(radius): [
                f"r{radius}_{name}" for name in ENVIRONMENT_BASE_FIELDS
            ]
            for radius in RADII
        },
        "whole_world_descriptive_ceiling_fields": WHOLE_FIELDS,
        "translation_invariant": True,
        "coordinate_axis_rotation_reflection_invariant": True,
        "whole_world_features_eligible_for_primary_model": False,
        "sources": len(rows),
        "discovery_sources": sum(row["split"] == "discovery" for row in rows),
        "confirmation_sources": sum(
            row["split"] == "confirmation" for row in rows
        ),
        "features_csv": str(feature_path),
        "features_sha256": artifact_hash(feature_path),
        "affordance_response_outcomes_run": False,
    }
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(schema, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
