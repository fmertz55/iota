from __future__ import annotations

import argparse
import copy
import csv
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import geometry_from_mask, write_csv
from continuation import clone_world
from experiment_db import artifact_hash
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from iota_rig import World, load_config
from phase_free_class_matrix import run_to_checkpoint
from phase_free_constraint_transport import ledger_error
from phase_source_minimization_audit import clamp_stored_phase, phase_source_patch
from predecessor_region_lineage import parse_coords


RADIUS = 6
DEFAULT_MANIFEST = Path(
    "output/findings/finding074/pre_articulation_channel_manifest.csv"
)
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding075/successor_graph_role_development"
)
FROZEN_F074_MANIFEST_SHA256 = (
    "1ffcac698b397dc956e0ff0b22398fb8c7a3241f7d65e39cfa46feb77733af5c"
)

FIELDS = [
    "channel_id",
    "init_seed",
    "sample_index",
    "precursor_offset",
    "precursor_source",
    "factual_target",
    "factual_radial_signature",
    "factual_role_signature",
    "candidate_pool",
    "radial_matched_candidates",
    "role_preserving_candidates",
    "role_breaking_candidates",
    "role_preserving_target",
    "role_preserving_distance",
    "role_breaking_target",
    "role_breaking_distance",
    "paired_match_available",
    "payload_zero",
    "ledger_exact",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit factual graph-role match support without causal outcomes."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def coord(value: str) -> tuple[int, int, int]:
    parts = tuple(int(part) for part in value.split(":"))
    if len(parts) != 3:
        raise ValueError(f"invalid coordinate {value}")
    return parts


def coord_text(value: tuple[int, int, int] | None) -> str:
    return "" if value is None else ":".join(str(part) for part in value)


def config_for_seed(canonical: dict[str, Any], seed: int) -> dict[str, Any]:
    cfg = copy.deepcopy(canonical)
    cfg.setdefault("init", {})["seed"] = int(seed)
    cfg.setdefault("experiment", {})["objective"] = (
        f"finding075_graph_role_development_seed{seed}"
    )
    return cfg


def wrapped_delta(left: int, right: int, size: int, wrap: bool) -> int:
    distance = abs(int(left) - int(right))
    return min(distance, size - distance) if wrap else distance


def chebyshev(
    left: tuple[int, int, int],
    right: tuple[int, int, int],
    size: int,
    wrap: bool,
) -> int:
    return max(
        wrapped_delta(a, b, size, wrap) for a, b in zip(left, right, strict=True)
    )


def nearby_coords(
    anchor: tuple[int, int, int], size: int, wrap: bool, radius: int
) -> list[tuple[int, int, int]]:
    output: set[tuple[int, int, int]] = set()
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx == dy == dz == 0:
                    continue
                raw = tuple(anchor[i] + (dx, dy, dz)[i] for i in range(3))
                if wrap:
                    output.add(tuple(value % size for value in raw))
                elif all(0 <= value < size for value in raw):
                    output.add(raw)
    return sorted(output)


def active_cube_neighbors(
    world: World, target: tuple[int, int, int]
) -> list[tuple[int, int, int]]:
    size = int(world.size)
    output: list[tuple[int, int, int]] = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                raw = (target[0] + dx, target[1] + dy, target[2] + dz)
                if world.wrap:
                    candidate = tuple(value % size for value in raw)
                elif not all(0 <= value < size for value in raw):
                    continue
                else:
                    candidate = raw
                if bool(world.active[candidate]):
                    output.append(candidate)
    return sorted(output)


def adjacency_degrees(
    neighbors: list[tuple[int, int, int]], size: int, wrap: bool
) -> tuple[int, ...]:
    return tuple(
        sorted(
            sum(
                other != node and chebyshev(node, other, size, wrap) <= 1
                for other in neighbors
            )
            for node in neighbors
        )
    )


def signatures(
    world: World, target: tuple[int, int, int]
) -> tuple[tuple[int, int], tuple[Any, ...]]:
    geometry = geometry_from_mask(world.active, target, bool(world.wrap))
    neighbors = active_cube_neighbors(world, target)
    shell_two = sum(
        bool(world.active[cell])
        and chebyshev(target, cell, int(world.size), bool(world.wrap)) == 2
        for cell in nearby_coords(target, int(world.size), bool(world.wrap), 2)
    )
    radial = (int(geometry["cube26_neighbors"]), int(shell_two))
    role = (
        int(geometry["face6_neighbors"]),
        int(geometry["face18_neighbors"]),
        int(geometry["face6_components"]),
        int(geometry["cube26_components"]),
        adjacency_degrees(neighbors, int(world.size), bool(world.wrap)),
    )
    return radial, role


def compact_signature(value: tuple[Any, ...]) -> str:
    return json.dumps(value, separators=(",", ":"))


def audit_channel(
    manifest: dict[str, str], checkpoint: World, cfg: dict[str, Any]
) -> dict[str, Any]:
    world = clone_world(checkpoint, int(manifest["continuation_seed"]))
    precursor_offset = int(manifest["precursor_offset"])
    target = coord(manifest["precursor_target"])
    source = coord(manifest["precursor_source"])
    forbidden = {
        source,
        target,
        coord(manifest["original_bridge"]),
        *parse_coords(manifest["successor_bridge_cells"]),
    }
    payload_zero = True
    exact = True
    with phase_source_patch(manifest["variant"]):
        clamp_stored_phase(world, manifest["variant"])
        for _ in range(1, precursor_offset):
            payload_zero &= int(np.count_nonzero(world.P)) == 0
            exact &= ledger_error(world) == 0.0
            iota_rig.step(world, cfg)
            clamp_stored_phase(world, manifest["variant"])
    payload_zero &= int(np.count_nonzero(world.P)) == 0
    exact &= ledger_error(world) == 0.0
    if bool(world.active[target]) or int(world.latent_A[target]) > 0:
        raise RuntimeError(f"{manifest['channel_id']} factual target is not depleted pre-step")
    factual_radial, factual_role = signatures(world, target)
    candidates: list[tuple[tuple[int, int, int], tuple[int, int], tuple[Any, ...], int]] = []
    for candidate in nearby_coords(target, int(world.size), bool(world.wrap), RADIUS):
        if candidate in forbidden:
            continue
        if bool(world.active[candidate]) or int(world.latent_A[candidate]) > 0:
            continue
        radial, role = signatures(world, candidate)
        distance = chebyshev(target, candidate, int(world.size), bool(world.wrap))
        candidates.append((candidate, radial, role, distance))
    radial_matches = [item for item in candidates if item[1] == factual_radial]
    preserving = [item for item in radial_matches if item[2] == factual_role]
    breaking = [item for item in radial_matches if item[2] != factual_role]
    preserving.sort(key=lambda item: (item[3], item[0]))
    breaking.sort(key=lambda item: (item[3], item[0]))
    preserve = preserving[0] if preserving else None
    disrupt = breaking[0] if breaking else None
    return {
        "channel_id": manifest["channel_id"],
        "init_seed": int(manifest["init_seed"]),
        "sample_index": int(manifest["sample_index"]),
        "precursor_offset": precursor_offset,
        "precursor_source": coord_text(source),
        "factual_target": coord_text(target),
        "factual_radial_signature": compact_signature(factual_radial),
        "factual_role_signature": compact_signature(factual_role),
        "candidate_pool": len(candidates),
        "radial_matched_candidates": len(radial_matches),
        "role_preserving_candidates": len(preserving),
        "role_breaking_candidates": len(breaking),
        "role_preserving_target": "" if preserve is None else coord_text(preserve[0]),
        "role_preserving_distance": "" if preserve is None else preserve[3],
        "role_breaking_target": "" if disrupt is None else coord_text(disrupt[0]),
        "role_breaking_distance": "" if disrupt is None else disrupt[3],
        "paired_match_available": int(preserve is not None and disrupt is not None),
        "payload_zero": int(payload_zero),
        "ledger_exact": int(exact),
    }


def run_seed_job(job: tuple[str, int, list[dict[str, str]]]) -> list[dict[str, Any]]:
    config_path, seed, manifests = job
    canonical = load_config(config_path)
    cfg = config_for_seed(canonical, seed)
    checkpoint = run_to_checkpoint(
        cfg, manifests[0]["variant"], int(manifests[0]["checkpoint_tick"])
    )
    output: list[dict[str, Any]] = []
    for manifest in manifests:
        row = audit_channel(manifest, checkpoint, cfg)
        output.append(row)
        print(
            f"f075 development {row['channel_id']} radial={row['radial_matched_candidates']} "
            f"preserve={row['role_preserving_candidates']} break={row['role_breaking_candidates']} "
            f"paired={row['paired_match_available']}",
            flush=True,
        )
    return output


def main() -> None:
    args = parse_args()
    if artifact_hash(args.manifest) != FROZEN_F074_MANIFEST_SHA256:
        raise RuntimeError("Finding 074 factual manifest changed")
    if not 1 <= int(args.workers) <= 4:
        raise ValueError("--workers must be 1..4")
    manifest = read_csv(args.manifest)
    grouped: dict[int, list[dict[str, str]]] = {}
    for row in manifest:
        grouped.setdefault(int(row["init_seed"]), []).append(row)
    jobs = [
        (str(args.canonical_config), seed, rows)
        for seed, rows in sorted(grouped.items())
    ]
    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=int(args.workers)) as executor:
        for rows in executor.map(run_seed_job, jobs):
            results.extend(rows)
    results.sort(key=lambda row: row["channel_id"])
    cases_path = args.output_prefix.with_name(args.output_prefix.name + "_cases.csv")
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.json")
    write_csv(cases_path, FIELDS, results)
    summary = {
        "finding": "075-development",
        "confirmatory_outcomes_run": False,
        "source_cohort": "Finding 074 observed development cohort only",
        "manifest": str(args.manifest),
        "manifest_sha256": artifact_hash(args.manifest),
        "channels": len(results),
        "radius": RADIUS,
        "channels_with_radial_match": sum(
            int(row["radial_matched_candidates"]) > 0 for row in results
        ),
        "channels_with_role_preserving_match": sum(
            int(row["role_preserving_candidates"]) > 0 for row in results
        ),
        "channels_with_role_breaking_match": sum(
            int(row["role_breaking_candidates"]) > 0 for row in results
        ),
        "channels_with_paired_matches": sum(
            int(row["paired_match_available"]) for row in results
        ),
        "all_payload_zero": all(int(row["payload_zero"]) for row in results),
        "all_ledgers_exact": all(int(row["ledger_exact"]) for row in results),
        "cases_csv": str(cases_path),
        "cases_sha256": artifact_hash(cases_path),
        "worker_processes": int(args.workers),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
