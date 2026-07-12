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
from component_bridge_causal_trace import write_csv
from continuation import clone_world
from experiment_db import artifact_hash
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from iota_rig import World, load_config
from phase_free_class_matrix import run_to_checkpoint
from phase_free_constraint_transport import ledger_error
from phase_source_minimization_audit import clamp_stored_phase, phase_source_patch
from predecessor_region_lineage import parse_coords
from successor_graph_role_audit import (
    FROZEN_F074_MANIFEST_SHA256,
    active_cube_neighbors,
    compact_signature,
    config_for_seed,
    coord,
    coord_text,
    read_csv,
    signatures,
)


DEFAULT_MANIFEST = Path(
    "output/findings/finding074/pre_articulation_channel_manifest.csv"
)
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding075/successor_graph_rewire_development"
)

FIELDS = [
    "channel_id",
    "init_seed",
    "sample_index",
    "precursor_offset",
    "factual_target",
    "post_radial_signature",
    "post_role_signature",
    "active_neighbor_count",
    "depleted_neighbor_count",
    "swap_candidates",
    "role_preserving_swaps",
    "role_breaking_swaps",
    "preserve_donor",
    "preserve_receiver",
    "preserve_moves_protected_cell",
    "break_donor",
    "break_receiver",
    "break_moves_protected_cell",
    "paired_swap_available",
    "target_poststate_exact",
    "payload_zero",
    "ledger_exact",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit same-address topology-rewire support without outcomes."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def state_record(world: World, cell: tuple[int, int, int]) -> dict[str, Any]:
    return {
        "active": int(bool(world.active[cell])),
        "A": int(world.A[cell]),
        "R": int(world.R[cell]),
        "V": int(world.V[cell]),
        "P": int(world.P[cell]),
        "latent_A": int(world.latent_A[cell]),
        "angular_L": float(world.angular_L[cell]),
    }


def hypothetical_signature(
    world: World,
    donor: tuple[int, int, int],
    receiver: tuple[int, int, int],
    target: tuple[int, int, int],
) -> tuple[tuple[int, int], tuple[Any, ...]]:
    donor_active = bool(world.active[donor])
    receiver_active = bool(world.active[receiver])
    world.active[donor] = False
    world.active[receiver] = True
    try:
        return signatures(world, target)
    finally:
        world.active[donor] = donor_active
        world.active[receiver] = receiver_active


def signature_distance(left: tuple[Any, ...], right: tuple[Any, ...]) -> int:
    distance = 0
    for a, b in zip(left[:-1], right[:-1], strict=True):
        distance += int(a != b)
    left_degrees = left[-1]
    right_degrees = right[-1]
    distance += abs(len(left_degrees) - len(right_degrees))
    distance += sum(a != b for a, b in zip(left_degrees, right_degrees))
    return distance


def audit_channel(
    manifest: dict[str, str], checkpoint: World, cfg: dict[str, Any]
) -> dict[str, Any]:
    world = clone_world(checkpoint, int(manifest["continuation_seed"]))
    offset = int(manifest["precursor_offset"])
    target = coord(manifest["precursor_target"])
    source = coord(manifest["precursor_source"])
    target_expected = json.loads(manifest["factual_target_post_state"])
    protected = {
        source,
        coord(manifest["original_bridge"]),
        *parse_coords(manifest["successor_bridge_cells"]),
    }
    payload_zero = True
    exact = True
    with phase_source_patch(manifest["variant"]):
        clamp_stored_phase(world, manifest["variant"])
        for _ in range(1, offset + 1):
            payload_zero &= int(np.count_nonzero(world.P)) == 0
            exact &= ledger_error(world) == 0.0
            iota_rig.step(world, cfg)
            clamp_stored_phase(world, manifest["variant"])
    payload_zero &= int(np.count_nonzero(world.P)) == 0
    exact &= ledger_error(world) == 0.0
    target_exact = state_record(world, target) == target_expected
    if not target_exact:
        raise RuntimeError(f"{manifest['channel_id']} target post-state changed")
    radial, role = signatures(world, target)
    neighbors = active_cube_neighbors(world, target)
    all_neighbors: list[tuple[int, int, int]] = []
    size = int(world.size)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                raw = (target[0] + dx, target[1] + dy, target[2] + dz)
                if world.wrap:
                    cell = tuple(value % size for value in raw)
                elif not all(0 <= value < size for value in raw):
                    continue
                else:
                    cell = raw
                all_neighbors.append(cell)
    depleted = [
        cell
        for cell in sorted(set(all_neighbors))
        if not bool(world.active[cell]) and int(world.latent_A[cell]) == 0
    ]
    swaps: list[
        tuple[
            tuple[int, tuple[int, int, int], tuple[int, int, int]],
            tuple[int, int],
            tuple[Any, ...],
            tuple[int, int, int],
            tuple[int, int, int],
        ]
    ] = []
    for donor in neighbors:
        if donor == target:
            continue
        for receiver in depleted:
            new_radial, new_role = hypothetical_signature(
                world, donor, receiver, target
            )
            priority = (int(donor in protected), donor, receiver)
            swaps.append((priority, new_radial, new_role, donor, receiver))
    preserving = [item for item in swaps if item[1] == radial and item[2] == role]
    breaking = [item for item in swaps if item[1] == radial and item[2] != role]
    preserving.sort(key=lambda item: item[0])
    breaking.sort(
        key=lambda item: (
            item[0][0],
            signature_distance(role, item[2]),
            item[0][1],
            item[0][2],
        )
    )
    preserve = preserving[0] if preserving else None
    disrupt = breaking[0] if breaking else None
    return {
        "channel_id": manifest["channel_id"],
        "init_seed": int(manifest["init_seed"]),
        "sample_index": int(manifest["sample_index"]),
        "precursor_offset": offset,
        "factual_target": coord_text(target),
        "post_radial_signature": compact_signature(radial),
        "post_role_signature": compact_signature(role),
        "active_neighbor_count": len(neighbors),
        "depleted_neighbor_count": len(depleted),
        "swap_candidates": len(swaps),
        "role_preserving_swaps": len(preserving),
        "role_breaking_swaps": len(breaking),
        "preserve_donor": "" if preserve is None else coord_text(preserve[3]),
        "preserve_receiver": "" if preserve is None else coord_text(preserve[4]),
        "preserve_moves_protected_cell": (
            "" if preserve is None else int(preserve[3] in protected)
        ),
        "break_donor": "" if disrupt is None else coord_text(disrupt[3]),
        "break_receiver": "" if disrupt is None else coord_text(disrupt[4]),
        "break_moves_protected_cell": (
            "" if disrupt is None else int(disrupt[3] in protected)
        ),
        "paired_swap_available": int(preserve is not None and disrupt is not None),
        "target_poststate_exact": int(target_exact),
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
            f"f075 rewire {row['channel_id']} preserve={row['role_preserving_swaps']} "
            f"break={row['role_breaking_swaps']} paired={row['paired_swap_available']} "
            f"protected={row['preserve_moves_protected_cell']}/{row['break_moves_protected_cell']}",
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
    jobs = [(str(args.canonical_config), seed, rows) for seed, rows in sorted(grouped.items())]
    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=int(args.workers)) as executor:
        for rows in executor.map(run_seed_job, jobs):
            results.extend(rows)
    results.sort(key=lambda row: row["channel_id"])
    cases_path = args.output_prefix.with_name(args.output_prefix.name + "_cases.csv")
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.json")
    write_csv(cases_path, FIELDS, results)
    summary = {
        "finding": "075-rewire-development",
        "confirmatory_outcomes_run": False,
        "source_cohort": "Finding 074 observed development cohort only",
        "manifest": str(args.manifest),
        "manifest_sha256": artifact_hash(args.manifest),
        "channels": len(results),
        "channels_with_role_preserving_swap": sum(
            int(row["role_preserving_swaps"]) > 0 for row in results
        ),
        "channels_with_role_breaking_swap": sum(
            int(row["role_breaking_swaps"]) > 0 for row in results
        ),
        "channels_with_paired_swaps": sum(
            int(row["paired_swap_available"]) for row in results
        ),
        "paired_swaps_not_moving_protected_cells": sum(
            int(row["paired_swap_available"])
            and int(row["preserve_moves_protected_cell"]) == 0
            and int(row["break_moves_protected_cell"]) == 0
            for row in results
        ),
        "all_target_poststates_exact": all(
            int(row["target_poststate_exact"]) for row in results
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
