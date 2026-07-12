from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import component_labels, interface_metrics, write_csv
from continuation import clone_world
from experiment_db import artifact_hash
from independent_geometry_screen import DEFAULT_CANONICAL_CONFIG
from iota_rig import World, load_config
from phase_free_class_matrix import run_to_checkpoint
from phase_free_constraint_transport import active_coords, ledger_error, pair_reachability
from phase_source_minimization_audit import clamp_stored_phase, phase_source_patch
from predecessor_region_lineage import parse_coords, reconstruct_regions


FOLLOWUP = 256
VARIANTS = (
    "natural",
    "sham",
    "erase_precursor_gate",
    "erase_inherited_memory",
    "transplant_poststate",
    "veto_first_rebridge",
)
DEFAULT_MANIFEST = Path(
    "output/findings/finding074/pre_articulation_channel_manifest.csv"
)
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding074/pre_articulation_channel_replay"
)
FROZEN_MANIFEST_SHA256 = (
    "1ffcac698b397dc956e0ff0b22398fb8c7a3241f7d65e39cfa46feb77733af5c"
)

RESULT_FIELDS = [
    "channel_id",
    "init_seed",
    "sample_index",
    "continuation_seed",
    "variant",
    "precursor_offset",
    "natural_split_offset",
    "natural_rebridge_offset",
    "endpoint_offset",
    "precursor_selector_matches",
    "rebridge_selector_matches",
    "selector_identity_exact",
    "intervention_count",
    "intervention_applied",
    "intervention_ledger_error",
    "transplant_prestate_exact",
    "transplant_untouched_on_step",
    "natural_split_occurs",
    "first_split_offset",
    "split_lifetime",
    "relation_separated_at_natural_split",
    "relation_separation_lifetime",
    "first_relation_closure_offset",
    "successor_bridge_realized_at_natural_rebridge",
    "successor_bridge_active_at_natural_rebridge",
    "alternate_closure",
    "alternate_closure_offset",
    "component_count_delta_at_natural_split",
    "largest_component_delta_at_natural_split",
    "max_component_count_delta",
    "max_largest_component_delta",
    "component_count_at_128",
    "component_count_at_256",
    "largest_component_at_128",
    "largest_component_at_256",
    "interface_union_at_128",
    "interface_union_at_256",
    "active_depleted_adjacency_at_128",
    "active_depleted_adjacency_at_256",
    "component_count_divergence_128",
    "component_count_divergence_256",
    "largest_component_divergence_128",
    "largest_component_divergence_256",
    "interface_union_divergence_128",
    "interface_union_divergence_256",
    "active_depleted_adjacency_divergence_128",
    "active_depleted_adjacency_divergence_256",
    "trajectory_sha256",
    "natural_sham_trajectory_exact",
    "payload_zero",
    "ledger_exact",
    "integrity_failure",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run frozen Finding 074 pre-articulation paired interventions."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def coord(value: str) -> tuple[int, int, int]:
    parts = tuple(int(part) for part in value.split(":"))
    if len(parts) != 3:
        raise ValueError(f"invalid coordinate: {value}")
    return parts


def config_for_seed(canonical: dict[str, Any], seed: int) -> dict[str, Any]:
    cfg = copy.deepcopy(canonical)
    cfg.setdefault("init", {})["seed"] = int(seed)
    cfg.setdefault("experiment", {})["objective"] = (
        f"finding074_pre_articulation_replay_seed{seed}"
    )
    return cfg


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


def state_exact(world: World, cell: tuple[int, int, int], expected: dict[str, Any]) -> bool:
    return state_record(world, cell) == expected


def apply_state(world: World, cell: tuple[int, int, int], state: dict[str, Any]) -> None:
    world.active[cell] = bool(state["active"])
    world.A[cell] = int(state["A"])
    world.R[cell] = np.uint8(state["R"])
    world.V[cell] = np.uint8(state["V"])
    world.P[cell] = np.uint8(state["P"])
    world.latent_A[cell] = int(state["latent_A"])
    world.angular_L[cell] = np.float32(state["angular_L"])


def hash_world(digest: Any, offset: int, world: World) -> None:
    digest.update(int(offset).to_bytes(4, "little", signed=False))
    for name in ("active", "A", "R", "V", "P", "latent_A", "angular_L"):
        array = np.ascontiguousarray(getattr(world, name))
        digest.update(name.encode("ascii"))
        digest.update(array.dtype.str.encode("ascii"))
        digest.update(array.tobytes())
    digest.update(
        json.dumps(
            world.rng.bit_generator.state, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    )


def selector(row: dict[str, str], prefix: str) -> dict[str, Any]:
    return {
        "offset": int(row[f"{prefix}_offset"] if prefix == "precursor" else row["rebridge_offset"]),
        "gate_ordinal": int(row[f"{prefix}_gate_ordinal"]),
        "source": coord(row[f"{prefix}_source"]),
        "target": coord(row[f"{prefix}_target"]),
        "candidate_order": int(row[f"{prefix}_candidate_order"]),
        "candidate_step": coord(row[f"{prefix}_candidate_step"]),
        "available_A_before": int(row[f"{prefix}_available_A_before"]),
        "transfer_probability": float(row[f"{prefix}_transfer_probability"]),
        "gate_draw": float(row[f"{prefix}_gate_draw"]),
    }


def selector_matches(candidate: dict[str, Any], frozen: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    checks = {
        "source": tuple(candidate["source"]) == frozen["source"],
        "target": tuple(candidate["target"]) == frozen["target"],
        "candidate_order": int(candidate["candidate_order"]) == frozen["candidate_order"],
        "candidate_step": tuple(candidate["candidate_step"]) == frozen["candidate_step"],
        "available_A_before": int(candidate["available_A_before"]) == frozen["available_A_before"],
        "transfer_probability": float(candidate["transfer_probability"]) == frozen["transfer_probability"],
        "gate_draw": float(candidate["gate_draw"]) == frozen["gate_draw"],
        "natural_gate_passed": bool(candidate["natural_gate_passed"]),
    }
    return all(checks.values()), checks


def component_point(world: World) -> tuple[np.ndarray, dict[str, Any]]:
    labels, _, count, largest = component_labels(
        world.active, bool(world.wrap), "cube26"
    )
    return labels, {
        "component_count": count,
        "largest_component": largest,
    }


def add_interface_point(world: World, point: dict[str, Any]) -> None:
    interface = interface_metrics(world, "cube26")
    point.update(
        {
            "interface_union": int(interface["interface_union_cells"]),
            "active_depleted_adjacency": float(
                interface["active_depleted_adjacency"]
            ),
        }
    )


def relation_status(
    world: World,
    regions: list[set[tuple[int, int, int]]],
    labels: np.ndarray,
) -> tuple[bool, float]:
    descendants = [active_coords(world.active, region) for region in regions]
    alive = bool(descendants) and all(descendants)
    reachability, _ = pair_reachability(labels, descendants)
    return alive, reachability


def scalar_digest_point(
    digest: Any,
    offset: int,
    world: World,
    point: dict[str, Any],
    original: tuple[int, int, int],
    successor: set[tuple[int, int, int]],
) -> None:
    payload = {
        "offset": offset,
        "component_count": point.get("component_count", ""),
        "largest_component": point.get("largest_component", ""),
        "original_active": int(bool(world.active[original])),
        "original_A": int(world.A[original]),
        "successor_active": sum(bool(world.active[cell]) for cell in successor),
        "rng": world.rng.bit_generator.state,
    }
    digest.update(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def endpoint_point(world: World) -> dict[str, Any]:
    _, point = component_point(world)
    add_interface_point(world, point)
    return {
        **point,
    }


def run_variant(
    manifest: dict[str, str],
    checkpoint: World,
    cfg: dict[str, Any],
    variant: str,
    frozen_regions: list[set[tuple[int, int, int]]] | None,
) -> tuple[dict[str, Any], list[set[tuple[int, int, int]]], dict[int, dict[str, Any]]]:
    split_offset = int(manifest["split_offset"])
    rebridge_offset = int(manifest["rebridge_offset"])
    precursor = selector(manifest, "precursor")
    rebridge = selector(manifest, "rebridge")
    original = coord(manifest["original_bridge"])
    successor = parse_coords(manifest["successor_bridge_cells"])
    transplant = coord(manifest["transplant_target"])
    target_pre = json.loads(manifest["factual_target_pre_state"])
    target_post = json.loads(manifest["factual_target_post_state"])
    transplant_pre = json.loads(manifest["transplant_pre_state"])
    endpoint = split_offset + FOLLOWUP
    world = clone_world(checkpoint, int(manifest["continuation_seed"]))
    payload_zero = True
    exact = True
    integrity_failures: list[str] = []
    selector_counts = {"precursor": 0, "rebridge": 0}
    selector_exact = True
    intervention_count = 0
    intervention_ledger_error: float | str = ""
    transplant_prestate_exact: int | str = ""
    transplant_untouched: int | str = ""
    transplant_exact_before_step: int | str = ""
    split_pre_world: World | None = None
    regions = frozen_regions
    first_split: int | str = ""
    split_lifetime = 0
    split_open = False
    split_baseline_count = 0
    relation_started = False
    relation_lifetime = 0
    first_closure: int | str = ""
    alternate_closure: int | str = ""
    alternate_closure_offset: int | str = ""
    successor_realized = False
    successor_active_rebridge = False
    baseline_point: dict[str, Any] | None = None
    max_component_delta = 0
    max_largest_delta = 0
    split_component_delta: int | str = ""
    split_largest_delta: int | str = ""
    points: dict[int, dict[str, Any]] = {}
    digest = hashlib.sha256()

    def override(offset: int, ordinal: int, candidate: dict[str, Any]) -> bool | None:
        nonlocal selector_exact, intervention_count
        selected_name = ""
        selected: dict[str, Any] | None = None
        if offset == precursor["offset"] and ordinal == precursor["gate_ordinal"]:
            selected_name, selected = "precursor", precursor
        if (
            variant in {"natural", "sham", "veto_first_rebridge"}
            and offset == rebridge["offset"]
            and ordinal == rebridge["gate_ordinal"]
        ):
            selected_name, selected = "rebridge", rebridge
        if selected is None:
            return None
        matched, checks = selector_matches(candidate, selected)
        selector_counts[selected_name] += 1
        selector_exact &= matched
        if not matched:
            raise RuntimeError(
                f"{manifest['channel_id']} {variant} {selected_name} identity changed: {checks}"
            )
        if variant == "erase_precursor_gate" and selected_name == "precursor":
            intervention_count += 1
            return False
        if variant == "veto_first_rebridge" and selected_name == "rebridge":
            intervention_count += 1
            return False
        return None

    try:
        with phase_source_patch(manifest["variant"]):
            clamp_stored_phase(world, manifest["variant"])
            hash_world(digest, 0, world)
            for offset in range(1, endpoint + 1):
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                pre_active_original = bool(world.active[original])
                pre_point: dict[str, Any] | None = None
                if offset >= precursor["offset"] and pre_active_original:
                    _, pre_point = component_point(world)
                if offset == split_offset:
                    split_pre_world = clone_world(world, int(manifest["continuation_seed"]))
                    if pre_point is None:
                        _, pre_point = component_point(world)
                    baseline_point = pre_point
                if offset == precursor["offset"] and variant == "transplant_poststate":
                    transplant_exact_before_step = int(
                        state_exact(world, transplant, transplant_pre)
                    )
                gate_ordinal = 0
                candidates: list[dict[str, Any]] = []

                def gate_callback(candidate: dict[str, Any]) -> bool | None:
                    nonlocal gate_ordinal
                    ordinal = gate_ordinal
                    gate_ordinal += 1
                    return override(offset, ordinal, candidate)

                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = candidates.append
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = gate_callback
                iota_rig.step(world, cfg)
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
                clamp_stored_phase(world, manifest["variant"])

                if offset == precursor["offset"] and variant in {
                    "erase_inherited_memory", "transplant_poststate"
                }:
                    if not state_exact(world, precursor["target"], target_post):
                        integrity_failures.append("factual_target_poststate_changed")
                    if variant == "erase_inherited_memory":
                        world.R[precursor["target"]] = np.uint8(target_pre["R"])
                        world.V[precursor["target"]] = np.uint8(target_pre["V"])
                        world.P[precursor["target"]] = np.uint8(target_pre["P"])
                        world.angular_L[precursor["target"]] = np.float32(target_pre["angular_L"])
                    else:
                        transplant_prestate_exact = int(
                            bool(transplant_exact_before_step)
                        )
                        # The selected site must remain untouched by the natural precursor step.
                        transplant_untouched = int(
                            state_exact(world, transplant, transplant_pre)
                        )
                        apply_state(world, precursor["target"], target_pre)
                        apply_state(world, transplant, target_post)
                    intervention_count += 1
                    intervention_ledger_error = ledger_error(world)

                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                post_point: dict[str, Any] | None = None
                if offset >= split_offset or (
                    pre_active_original and not bool(world.active[original])
                ):
                    labels, post_point = component_point(world)
                else:
                    labels = np.empty((0,), dtype=np.int8)
                scalar_digest_point(
                    digest,
                    offset,
                    world,
                    {} if post_point is None else post_point,
                    original,
                    successor,
                )
                if offset in {
                    precursor["offset"],
                    split_offset,
                    rebridge_offset,
                    split_offset + 128,
                    split_offset + 256,
                }:
                    hash_world(digest, offset, world)
                if offset in {split_offset + 128, split_offset + 256}:
                    point = endpoint_point(world)
                    points[offset - split_offset] = point
                if baseline_point is not None and offset >= split_offset:
                    if post_point is None:
                        raise RuntimeError("missing post-split component point")
                    max_component_delta = max(
                        max_component_delta,
                        int(post_point["component_count"] - baseline_point["component_count"]),
                    )
                    max_largest_delta = max(
                        max_largest_delta,
                        int(post_point["largest_component"] - baseline_point["largest_component"]),
                    )
                if offset == split_offset:
                    if pre_point is None or post_point is None:
                        raise RuntimeError("missing natural-split component measurement")
                    split_component_delta = int(
                        post_point["component_count"] - pre_point["component_count"]
                    )
                    split_largest_delta = int(
                        post_point["largest_component"] - pre_point["largest_component"]
                    )

                # The future articulation may have earlier activation/death cycles.
                # Its frozen precursor defines the start of this causal channel.
                original_died = (
                    offset >= precursor["offset"]
                    and pre_active_original
                    and not bool(world.active[original])
                )
                if original_died and (pre_point is None or post_point is None):
                    raise RuntimeError("missing component point at original-address death")
                split_now = original_died and (
                    int(post_point["component_count"]) > int(pre_point["component_count"])
                )
                if first_split == "" and offset >= precursor["offset"] and split_now:
                    first_split = offset
                    split_open = True
                    split_baseline_count = int(pre_point["component_count"])
                if split_open:
                    if int(post_point["component_count"]) > split_baseline_count:
                        split_lifetime += 1
                    else:
                        split_open = False

                if offset == split_offset and regions is None:
                    if split_pre_world is None:
                        raise RuntimeError("missing factual split pre-state")
                    regions, reconstructed = reconstruct_regions(split_pre_world, world)
                    if reconstructed != {original} or len(regions) < 2:
                        raise RuntimeError(
                            f"{manifest['channel_id']} predecessor reconstruction changed"
                        )
                if regions is not None and offset >= split_offset:
                    if post_point is None or labels.size == 0:
                        raise RuntimeError("missing relation component labels")
                    alive, reachability = relation_status(world, regions, labels)
                    separated = alive and reachability < 1.0
                    if offset == split_offset:
                        relation_started = separated
                    if relation_started and separated and first_closure == "":
                        relation_lifetime += 1
                    elif relation_started and first_closure == "":
                        first_closure = offset
                        if not any(bool(world.active[cell]) for cell in successor):
                            alternate_closure = 1
                            alternate_closure_offset = offset

                activated_successor = [
                    candidate
                    for candidate in candidates
                    if candidate.get("status") == "succeeded"
                    and candidate.get("target_activated") is True
                    and tuple(candidate["target"]) in successor
                ]
                if offset == rebridge_offset:
                    successor_realized = bool(activated_successor)
                    successor_active_rebridge = any(bool(world.active[cell]) for cell in successor)
    except Exception as exc:
        integrity_failures.append(f"{type(exc).__name__}:{exc}")
    finally:
        iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
        iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None

    if selector_counts["precursor"] != 1:
        integrity_failures.append(f"precursor_selector_matches={selector_counts['precursor']}")
    if variant in {"natural", "sham", "veto_first_rebridge"} and selector_counts["rebridge"] != 1:
        integrity_failures.append(f"rebridge_selector_matches={selector_counts['rebridge']}")
    expected_interventions = int(variant not in {"natural", "sham"})
    if intervention_count != expected_interventions:
        integrity_failures.append(f"intervention_count={intervention_count}")
    if regions is None:
        regions = []

    point128 = points.get(128, {})
    point256 = points.get(256, {})
    result = {
        "channel_id": manifest["channel_id"],
        "init_seed": int(manifest["init_seed"]),
        "sample_index": int(manifest["sample_index"]),
        "continuation_seed": int(manifest["continuation_seed"]),
        "variant": variant,
        "precursor_offset": precursor["offset"],
        "natural_split_offset": split_offset,
        "natural_rebridge_offset": rebridge_offset,
        "endpoint_offset": endpoint,
        "precursor_selector_matches": selector_counts["precursor"],
        "rebridge_selector_matches": selector_counts["rebridge"],
        "selector_identity_exact": int(selector_exact),
        "intervention_count": intervention_count,
        "intervention_applied": int(intervention_count == expected_interventions),
        "intervention_ledger_error": intervention_ledger_error,
        "transplant_prestate_exact": transplant_prestate_exact,
        "transplant_untouched_on_step": transplant_untouched,
        "natural_split_occurs": int(first_split == split_offset),
        "first_split_offset": first_split,
        "split_lifetime": split_lifetime,
        "relation_separated_at_natural_split": int(relation_started),
        "relation_separation_lifetime": relation_lifetime,
        "first_relation_closure_offset": first_closure,
        "successor_bridge_realized_at_natural_rebridge": int(successor_realized),
        "successor_bridge_active_at_natural_rebridge": int(successor_active_rebridge),
        "alternate_closure": alternate_closure,
        "alternate_closure_offset": alternate_closure_offset,
        "component_count_delta_at_natural_split": split_component_delta,
        "largest_component_delta_at_natural_split": split_largest_delta,
        "max_component_count_delta": max_component_delta,
        "max_largest_component_delta": max_largest_delta,
        "component_count_at_128": point128.get("component_count", ""),
        "component_count_at_256": point256.get("component_count", ""),
        "largest_component_at_128": point128.get("largest_component", ""),
        "largest_component_at_256": point256.get("largest_component", ""),
        "interface_union_at_128": point128.get("interface_union", ""),
        "interface_union_at_256": point256.get("interface_union", ""),
        "active_depleted_adjacency_at_128": point128.get("active_depleted_adjacency", ""),
        "active_depleted_adjacency_at_256": point256.get("active_depleted_adjacency", ""),
        "component_count_divergence_128": "",
        "component_count_divergence_256": "",
        "largest_component_divergence_128": "",
        "largest_component_divergence_256": "",
        "interface_union_divergence_128": "",
        "interface_union_divergence_256": "",
        "active_depleted_adjacency_divergence_128": "",
        "active_depleted_adjacency_divergence_256": "",
        "trajectory_sha256": digest.hexdigest(),
        "natural_sham_trajectory_exact": "",
        "payload_zero": int(payload_zero),
        "ledger_exact": int(exact),
        "integrity_failure": ";".join(integrity_failures),
    }
    return result, regions, points


def run_channel_job(job: tuple[str, str, dict[str, str]]) -> list[dict[str, Any]]:
    config_path, _, manifest = job
    canonical = load_config(config_path)
    cfg = config_for_seed(canonical, int(manifest["init_seed"]))
    checkpoint = run_to_checkpoint(
        cfg, manifest["variant"], int(manifest["checkpoint_tick"])
    )
    natural, regions, natural_points = run_variant(
        manifest, checkpoint, cfg, "natural", None
    )
    results = [natural]
    for variant in VARIANTS[1:]:
        result, _, points = run_variant(manifest, checkpoint, cfg, variant, regions)
        for relative in (128, 256):
            natural_point = natural_points.get(relative, {})
            point = points.get(relative, {})
            for field in ("component_count", "largest_component", "interface_union"):
                result[f"{field}_divergence_{relative}"] = (
                    ""
                    if field not in point or field not in natural_point
                    else point[field] - natural_point[field]
                )
            field = "active_depleted_adjacency"
            result[f"{field}_divergence_{relative}"] = (
                ""
                if field not in point or field not in natural_point
                else point[field] - natural_point[field]
            )
        results.append(result)
    sham = next(row for row in results if row["variant"] == "sham")
    trajectory_exact = int(sham["trajectory_sha256"] == natural["trajectory_sha256"])
    natural["natural_sham_trajectory_exact"] = trajectory_exact
    sham["natural_sham_trajectory_exact"] = trajectory_exact
    print(
        f"f074 replay {manifest['channel_id']} seed={manifest['init_seed']} "
        f"pattern={next(r for r in results if r['variant']=='erase_precursor_gate')['natural_split_occurs']}/"
        f"{next(r for r in results if r['variant']=='erase_inherited_memory')['natural_split_occurs']}/"
        f"{next(r for r in results if r['variant']=='transplant_poststate')['natural_split_occurs']} "
        f"veto_lifetime={next(r for r in results if r['variant']=='veto_first_rebridge')['split_lifetime']} "
        f"errors={sum(bool(r['integrity_failure']) for r in results)}",
        flush=True,
    )
    return results


def main() -> None:
    args = parse_args()
    if not 1 <= int(args.workers) <= 4:
        raise ValueError("--workers must be 1..4")
    if artifact_hash(args.manifest) != FROZEN_MANIFEST_SHA256:
        raise RuntimeError("Finding 074 frozen factual manifest changed")
    manifest = read_csv(args.manifest)
    if len(manifest) < 6 or not all(int(row["selected_channel"]) for row in manifest):
        raise RuntimeError("Finding 074 intervention support gate is not met")
    jobs = [(str(args.canonical_config), str(args.manifest), row) for row in manifest]
    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=int(args.workers)) as executor:
        for rows in executor.map(run_channel_job, jobs):
            results.extend(rows)

    by_channel = {
        channel: {row["variant"]: row for row in results if row["channel_id"] == channel}
        for channel in sorted({row["channel_id"] for row in results})
    }
    pattern_channels: list[str] = []
    durable_channels: list[str] = []
    separated_128: list[str] = []
    natural_factual_exact = True
    sham_exact = True
    for channel, rows in by_channel.items():
        natural = rows["natural"]
        sham = rows["sham"]
        erase = rows["erase_precursor_gate"]
        memory = rows["erase_inherited_memory"]
        transplant = rows["transplant_poststate"]
        veto = rows["veto_first_rebridge"]
        natural_factual_exact &= bool(
            natural["natural_split_occurs"]
            and natural["successor_bridge_realized_at_natural_rebridge"]
            and not natural["integrity_failure"]
        )
        sham_exact &= bool(
            sham["natural_sham_trajectory_exact"]
            and sham["natural_split_occurs"]
            and sham["successor_bridge_realized_at_natural_rebridge"]
            and not sham["integrity_failure"]
        )
        if (
            not erase["natural_split_occurs"]
            and not transplant["natural_split_occurs"]
            and bool(memory["natural_split_occurs"])
        ):
            pattern_channels.append(channel)
        if int(veto["split_lifetime"]) > int(natural["split_lifetime"]):
            durable_channels.append(channel)
        if int(veto["relation_separation_lifetime"]) >= 128:
            separated_128.append(channel)

    all_safe = all(
        int(row["payload_zero"])
        and int(row["ledger_exact"])
        and not row["integrity_failure"]
        for row in results
    )
    pattern_seeds = sorted(
        {
            int(by_channel[channel]["natural"]["init_seed"])
            for channel in pattern_channels
        }
    )
    required = math.ceil((2 * len(by_channel)) / 3)
    unique_vetoes = len(by_channel)
    durability_required = math.ceil((2 * unique_vetoes) / 3)
    support = bool(
        len(by_channel) >= 6
        and natural_factual_exact
        and sham_exact
        and len(pattern_channels) >= required
        and len(pattern_seeds) >= 4
        and all_safe
    )
    durability = bool(
        all_safe
        and len(durable_channels) >= durability_required
        and bool(separated_128)
    )

    result_path = args.output_prefix.with_name(args.output_prefix.name + "_results.csv")
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.json")
    results.sort(key=lambda row: (row["channel_id"], VARIANTS.index(row["variant"])))
    write_csv(result_path, RESULT_FIELDS, results)
    summary = {
        "finding": "074B",
        "protocol": "frozen paired pre-articulation channel intervention",
        "manifest": str(args.manifest),
        "manifest_sha256": artifact_hash(args.manifest),
        "selected_channels": len(by_channel),
        "variants_per_channel": len(VARIANTS),
        "replay_rows": len(results),
        "natural_factual_exact_all_channels": natural_factual_exact,
        "natural_sham_exact_all_channels": sham_exact,
        "pattern_definition": "erase split=0, transplant split=0, memory split=1 at frozen natural offset",
        "pattern_channels": len(pattern_channels),
        "pattern_channel_ids": pattern_channels,
        "pattern_required_two_thirds": required,
        "pattern_initialization_seeds": pattern_seeds,
        "all_intervention_safety_checks_exact": all_safe,
        "coherence_conditioned_transition_geometry_supported": support,
        "unique_rebridge_vetoes": unique_vetoes,
        "vetoes_extending_natural_split_lifetime": len(durable_channels),
        "durability_required_two_thirds": durability_required,
        "veto_separation_at_least_128_channels": separated_128,
        "durability_extension_supported": durability,
        "results_csv": str(result_path),
        "results_sha256": "written-after-summary-placeholder",
        "canonical_config": str(args.canonical_config),
        "canonical_config_sha256": artifact_hash(args.canonical_config),
        "worker_processes": int(args.workers),
    }
    summary["results_sha256"] = artifact_hash(result_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
