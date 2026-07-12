from __future__ import annotations

import argparse
import csv
import hashlib
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
from successor_graph_role_audit import config_for_seed, coord
from successor_graph_susceptibility import build_precursor_state, full_state_hash


DEFAULT_MANIFEST = Path(
    "output/findings/finding075/successor_graph_rewire_manifest.csv"
)
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding078/factorial_successor_accessibility"
)
FROZEN_MANIFEST_SHA256 = (
    "b1605fa59101839dbb79d9aca8522fbc8af2e0e65541835e60aea8eb3b5ae41d"
)
RADIUS = 2
RECEIVERS = ("preserving", "breaking")
RECEIVER_FIELDS = {
    "preserving": "rewire_preserve_receiver",
    "breaking": "rewire_break_receiver",
}
VARIANTS = ("topology_only", "marks_only", "joint")
REPAIR_CLASSES = {"component_bridge_cube26", "local_bridge_face6"}

ROW_FIELDS = [
    "paired_channel_id", "init_seed", "sample_index", "receiver_label", "variant",
    "donor", "receiver", "edge_count", "marked_edge_sha256", "successor_openness",
    "activation_targets", "repair_affordance", "repair_targets", "repair_sources",
    "active_count", "conserved_amplitude", "payload_zero", "ledger_exact",
    "active_mask_exact", "structural_multiset_exact", "marks_multiset_exact",
    "joint_full_swap_exact", "rng_neutral", "repeat_exact", "integrity_failure",
]
CHANNEL_FIELDS = [
    "paired_channel_id", "init_seed", "sample_index", "identifiable",
    "preserving_openness_interaction", "preserving_repair_interaction",
    "breaking_openness_interaction", "breaking_repair_interaction",
    "nonzero_factorial_interaction", "selected_receiver",
    "selected_openness_interaction", "selected_repair_interaction",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run preregistered Finding 078 factorial feasibility audit."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def coord_text(value: tuple[int, int, int]) -> str:
    return ":".join(str(part) for part in value)


def relative_coord(
    root: tuple[int, int, int], value: tuple[int, int, int], size: int, wrap: bool
) -> tuple[int, int, int]:
    output: list[int] = []
    for origin, point in zip(root, value, strict=True):
        delta = int(point) - int(origin)
        if wrap:
            half = size // 2
            delta = ((delta + half) % size) - half
        output.append(delta)
    return tuple(output)  # type: ignore[return-value]


def in_basin(relative: tuple[int, int, int]) -> bool:
    return max(abs(value) for value in relative) <= RADIUS


def structural_record(world: World, cell: tuple[int, int, int]) -> tuple[Any, ...]:
    return (
        int(bool(world.active[cell])),
        int(world.A[cell]),
        int(world.latent_A[cell]),
    )


def mark_record(world: World, cell: tuple[int, int, int]) -> tuple[Any, ...]:
    return (
        int(world.R[cell]),
        int(world.V[cell]),
        int(world.P[cell]),
        float(world.angular_L[cell]),
    )


def apply_structural(
    world: World, cell: tuple[int, int, int], value: tuple[Any, ...]
) -> None:
    world.active[cell] = bool(value[0])
    world.A[cell] = int(value[1])
    world.latent_A[cell] = int(value[2])


def apply_marks(world: World, cell: tuple[int, int, int], value: tuple[Any, ...]) -> None:
    world.R[cell] = np.uint8(value[0])
    world.V[cell] = np.uint8(value[1])
    world.P[cell] = np.uint8(value[2])
    world.angular_L[cell] = np.float32(value[3])


def build_factor_state(
    natural: World,
    donor: tuple[int, int, int],
    receiver: tuple[int, int, int],
    variant: str,
) -> World:
    world = clone_world(natural, 2026078000)
    donor_structural = structural_record(natural, donor)
    receiver_structural = structural_record(natural, receiver)
    donor_marks = mark_record(natural, donor)
    receiver_marks = mark_record(natural, receiver)
    if variant in {"topology_only", "joint"}:
        apply_structural(world, donor, receiver_structural)
        apply_structural(world, receiver, donor_structural)
    if variant in {"marks_only", "joint"}:
        apply_marks(world, donor, receiver_marks)
        apply_marks(world, receiver, donor_marks)
    return world


def conserved_amplitude(world: World) -> int:
    return int(
        np.sum(world.A[world.active], dtype=np.int64)
        + np.sum(world.latent_A[~world.active], dtype=np.int64)
    )


def float_value(value: float) -> float:
    return float(f"{float(value):.12g}")


def geometry_weights(cfg: dict[str, Any]) -> dict[str, float]:
    raw = cfg["constants"].get("angular_momentum_residual_geometry_weights", {}) or {}
    return {str(key): float(value) for key, value in raw.items()}


def enumerate_edges(
    world: World, cfg: dict[str, Any], root: tuple[int, int, int]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if float(cfg["constants"].get("bond_probability", 1.0)) != 1.0:
        raise RuntimeError("Finding 078 requires bond_probability=1.0")
    audit = clone_world(world, 2026078078)
    original_hash = full_state_hash(world)
    k_a = float(cfg["constants"].get("amplitude_coupling", 0.125))
    decay_mode = str(cfg["constants"].get("decay_mode", "inverse_square"))
    valence = max(1, int(cfg["constants"].get("valence", 1)))
    neighbor_mode = str(cfg["constants"].get("neighbor_mode", "cube26"))
    residual_probability = iota_rig.clamp_probability(
        float(cfg["constants"].get("residual_participation_probability", 0.0))
    )
    residual_secondary_only = bool(
        cfg["constants"].get("residual_participation_secondary_only", True)
    )
    angular_enabled = bool(cfg["constants"].get("angular_momentum_enabled", False))
    bias_enabled = angular_enabled and bool(
        cfg["constants"].get("angular_momentum_residual_bias_enabled", False)
    )
    angular_cap = float(cfg["constants"].get("angular_momentum_cap", 1.0))
    bias_strength = float(
        cfg["constants"].get("angular_momentum_residual_bias_strength", 0.0)
    )
    preserve_behavior = bool(
        cfg["constants"].get("angular_momentum_residual_bias_preserve_behavior", True)
    )
    mean_preserving = bool(
        cfg["constants"].get("angular_momentum_residual_bias_mean_preserving", False)
    )
    score_mode = str(
        cfg["constants"].get(
            "angular_momentum_residual_bias_score_mode", "source_L_alignment"
        )
    )
    old_l = audit.angular_L.astype(np.float32, copy=True)
    edges: list[dict[str, Any]] = []
    coords = np.argwhere(audit.active)
    for scheduler_rank, raw_source in enumerate(coords):
        source = tuple(int(value) for value in raw_source)
        x, y, z = source
        a = int(audit.A[source])
        r = int(audit.R[source])
        if a <= 0 or r == 0:
            continue
        v_idx = int(audit.V[source]) % len(audit.vectors)
        payload = int(audit.P[source])
        candidates = iota_rig.local_candidates(
            audit, x, y, z, v_idx, a, r, payload, decay_mode, valence, 1.0,
            neighbor_mode,
        )
        if bias_enabled and bias_strength > 0.0:
            iota_rig.apply_angular_momentum_residual_bias(
                audit, old_l, candidates, x, y, z, v_idx, a, r, payload,
                audit.active, audit.latent_A, k_a, residual_probability,
                residual_secondary_only, angular_cap, bias_strength,
                preserve_behavior, mean_preserving, score_mode, geometry_weights(cfg),
            )
        source_relative = relative_coord(root, source, audit.size, audit.wrap)
        for candidate in candidates:
            target = tuple(int(value) for value in candidate["target"])
            target_relative = relative_coord(root, target, audit.size, audit.wrap)
            if not (in_basin(source_relative) or in_basin(target_relative)):
                continue
            target_active = bool(audit.active[target])
            target_depleted = (not target_active) and int(audit.latent_A[target]) <= 0
            target_latent = (not target_active) and int(audit.latent_A[target]) > 0
            if target_active and int(audit.A[target]) >= a:
                continue
            if target_depleted and (
                residual_probability <= 0.0
                or (residual_secondary_only and int(candidate["order"]) == 0)
            ):
                continue
            influence = float(candidate["influence"])
            if influence <= 0.0:
                continue
            probability = iota_rig.clamp_probability(k_a * influence)
            if target_depleted:
                probability *= residual_probability
                probability *= float(candidate.get("residual_bias_multiplier", 1.0))
                probability = iota_rig.clamp_probability(probability)
            geometry = iota_rig.classify_residual_target_geometry(audit, target)
            edges.append(
                {
                    "scheduler_rank": scheduler_rank,
                    "source": source_relative,
                    "target": target_relative,
                    "candidate_order": int(candidate["order"]),
                    "candidate_step": tuple(int(value) for value in candidate["step"]),
                    "source_A": a,
                    "source_R": r,
                    "source_V": v_idx,
                    "source_L": float_value(old_l[source]),
                    "target_status": (
                        "active" if target_active else "depleted" if target_depleted else "latent"
                    ),
                    "target_R": int(audit.R[target]),
                    "target_V": int(audit.V[target]),
                    "target_L": float_value(old_l[target]),
                    "influence": float_value(influence),
                    "residual_bias_multiplier": float_value(
                        candidate.get("residual_bias_multiplier", 1.0)
                    ),
                    "transfer_probability": float_value(probability),
                    "geometry_class": str(geometry["class"]),
                    "inactive_activation": int(target_depleted or target_latent),
                    "repair_edge": int(
                        target_depleted
                        and int(candidate["order"]) != 0
                        and str(geometry["class"]) in REPAIR_CLASSES
                    ),
                }
            )
    edges.sort(key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
    encoded = json.dumps(edges, sort_keys=True, separators=(",", ":")).encode("utf-8")
    activation_edges = [row for row in edges if int(row["inactive_activation"])]
    repair_edges = [row for row in edges if int(row["repair_edge"])]
    metrics = {
        "edge_count": len(edges),
        "marked_edge_sha256": hashlib.sha256(encoded).hexdigest(),
        "successor_openness": float_value(
            sum(float(row["transfer_probability"]) for row in activation_edges)
        ),
        "activation_targets": len({tuple(row["target"]) for row in activation_edges}),
        "repair_affordance": float_value(
            sum(float(row["transfer_probability"]) for row in repair_edges)
        ),
        "repair_targets": len({tuple(row["target"]) for row in repair_edges}),
        "repair_sources": len({tuple(row["source"]) for row in repair_edges}),
        "rng_neutral": int(full_state_hash(world) == original_hash),
    }
    return edges, metrics


def arrays_exact(left: World, right: World, names: tuple[str, ...]) -> bool:
    return all(np.array_equal(getattr(left, name), getattr(right, name)) for name in names)


def run_channel_job(
    job: tuple[str, dict[str, str]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config_path, channel = job
    canonical = load_config(config_path)
    cfg = config_for_seed(canonical, int(channel["init_seed"]))
    checkpoint = run_to_checkpoint(
        cfg, channel["variant"], int(channel["checkpoint_tick"])
    )
    natural = build_precursor_state(channel, checkpoint, cfg)
    root = coord(channel["precursor_target"])
    donor = coord(channel["rewire_preserve_donor"])
    if donor != coord(channel["rewire_break_donor"]):
        raise RuntimeError("Finding 078 common donor changed")
    natural_edges, natural_metrics = enumerate_edges(natural, cfg, root)
    repeat_edges, repeat_metrics = enumerate_edges(natural, cfg, root)
    natural_repeat = natural_edges == repeat_edges and natural_metrics == repeat_metrics
    rows: list[dict[str, Any]] = []
    base_active = int(np.count_nonzero(natural.active))
    base_amplitude = conserved_amplitude(natural)
    rows.append(
        {
            "paired_channel_id": channel["paired_channel_id"],
            "init_seed": int(channel["init_seed"]),
            "sample_index": int(channel["sample_index"]),
            "receiver_label": "natural",
            "variant": "natural",
            "donor": coord_text(donor),
            "receiver": "",
            **natural_metrics,
            "active_count": base_active,
            "conserved_amplitude": base_amplitude,
            "payload_zero": int(np.count_nonzero(natural.P) == 0),
            "ledger_exact": int(ledger_error(natural) == 0.0),
            "active_mask_exact": 1,
            "structural_multiset_exact": 1,
            "marks_multiset_exact": 1,
            "joint_full_swap_exact": 1,
            "repeat_exact": int(natural_repeat),
            "integrity_failure": "",
        }
    )
    by_receiver: dict[str, dict[str, dict[str, Any]]] = {}
    for receiver_label in RECEIVERS:
        receiver = coord(channel[RECEIVER_FIELDS[receiver_label]])
        by_receiver[receiver_label] = {}
        full_swap = build_factor_state(natural, donor, receiver, "joint")
        for variant in VARIANTS:
            world = build_factor_state(natural, donor, receiver, variant)
            edges, metrics = enumerate_edges(world, cfg, root)
            edges_repeat, metrics_repeat = enumerate_edges(world, cfg, root)
            structural_pair_before = sorted(
                (structural_record(natural, donor), structural_record(natural, receiver))
            )
            structural_pair_after = sorted(
                (structural_record(world, donor), structural_record(world, receiver))
            )
            marks_pair_before = sorted((mark_record(natural, donor), mark_record(natural, receiver)))
            marks_pair_after = sorted((mark_record(world, donor), mark_record(world, receiver)))
            active_mask_exact = arrays_exact(world, natural, ("active",))
            joint_exact = arrays_exact(
                world, full_swap,
                ("active", "A", "latent_A", "R", "V", "P", "angular_L"),
            ) if variant == "joint" else True
            failure: list[str] = []
            if int(np.count_nonzero(world.active)) != base_active:
                failure.append("active_count")
            if conserved_amplitude(world) != base_amplitude:
                failure.append("conserved_amplitude")
            if structural_pair_before != structural_pair_after:
                failure.append("structural_multiset")
            if marks_pair_before != marks_pair_after:
                failure.append("marks_multiset")
            if variant == "marks_only" and not active_mask_exact:
                failure.append("marks_only_active_mask")
            if variant == "joint" and not joint_exact:
                failure.append("joint_swap")
            if edges != edges_repeat or metrics != metrics_repeat:
                failure.append("repeat")
            row = {
                "paired_channel_id": channel["paired_channel_id"],
                "init_seed": int(channel["init_seed"]),
                "sample_index": int(channel["sample_index"]),
                "receiver_label": receiver_label,
                "variant": variant,
                "donor": coord_text(donor),
                "receiver": coord_text(receiver),
                **metrics,
                "active_count": int(np.count_nonzero(world.active)),
                "conserved_amplitude": conserved_amplitude(world),
                "payload_zero": int(np.count_nonzero(world.P) == 0),
                "ledger_exact": int(ledger_error(world) == 0.0),
                "active_mask_exact": int(active_mask_exact),
                "structural_multiset_exact": int(structural_pair_before == structural_pair_after),
                "marks_multiset_exact": int(marks_pair_before == marks_pair_after),
                "joint_full_swap_exact": int(joint_exact),
                "repeat_exact": int(edges == edges_repeat and metrics == metrics_repeat),
                "integrity_failure": ";".join(failure),
            }
            rows.append(row)
            by_receiver[receiver_label][variant] = row

    interactions: dict[str, dict[str, float]] = {}
    natural_row = rows[0]
    identifiable = False
    for receiver_label in RECEIVERS:
        variants = by_receiver[receiver_label]
        identifiable |= bool(
            variants["topology_only"]["marked_edge_sha256"]
            != natural_row["marked_edge_sha256"]
            and variants["marks_only"]["marked_edge_sha256"]
            != natural_row["marked_edge_sha256"]
            and int(variants["marks_only"]["active_mask_exact"]) == 1
            and int(variants["topology_only"]["marks_multiset_exact"]) == 1
        )
        interactions[receiver_label] = {}
        for metric in ("successor_openness", "repair_affordance"):
            interactions[receiver_label][metric] = float_value(
                float(variants["joint"][metric])
                - float(variants["topology_only"][metric])
                - float(variants["marks_only"][metric])
                + float(natural_row[metric])
            )
    nonzero = any(
        abs(value) > 1e-12
        for receiver in interactions.values()
        for value in receiver.values()
    )
    selected = max(
        RECEIVERS,
        key=lambda label: (
            abs(interactions[label]["repair_affordance"]),
            abs(interactions[label]["successor_openness"]),
            int(label == "preserving"),
        ),
    )
    channel_row = {
        "paired_channel_id": channel["paired_channel_id"],
        "init_seed": int(channel["init_seed"]),
        "sample_index": int(channel["sample_index"]),
        "identifiable": int(identifiable),
        "preserving_openness_interaction": interactions["preserving"]["successor_openness"],
        "preserving_repair_interaction": interactions["preserving"]["repair_affordance"],
        "breaking_openness_interaction": interactions["breaking"]["successor_openness"],
        "breaking_repair_interaction": interactions["breaking"]["repair_affordance"],
        "nonzero_factorial_interaction": int(nonzero),
        "selected_receiver": selected,
        "selected_openness_interaction": interactions[selected]["successor_openness"],
        "selected_repair_interaction": interactions[selected]["repair_affordance"],
    }
    print(
        f"f078 {channel['paired_channel_id']} seed={channel['init_seed']} "
        f"identifiable={int(identifiable)} interaction={int(nonzero)} selected={selected}",
        flush=True,
    )
    return rows, channel_row


def main() -> None:
    args = parse_args()
    if artifact_hash(args.manifest) != FROZEN_MANIFEST_SHA256:
        raise RuntimeError("Finding 078 frozen Finding 075 manifest changed")
    if not 1 <= int(args.workers) <= 4:
        raise ValueError("--workers must be 1..4")
    channels = read_csv(args.manifest)
    jobs = [(str(args.canonical_config), channel) for channel in channels]
    rows: list[dict[str, Any]] = []
    channel_rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=int(args.workers)) as executor:
        for local_rows, channel_row in executor.map(run_channel_job, jobs):
            rows.extend(local_rows)
            channel_rows.append(channel_row)
    rows.sort(
        key=lambda row: (
            int(row["init_seed"]), row["receiver_label"], row["variant"]
        )
    )
    channel_rows.sort(key=lambda row: int(row["init_seed"]))
    states_path = args.output_prefix.with_name(args.output_prefix.name + "_states.csv")
    channels_path = args.output_prefix.with_name(args.output_prefix.name + "_channels.csv")
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.json")
    write_csv(states_path, ROW_FIELDS, rows)
    write_csv(channels_path, CHANNEL_FIELDS, channel_rows)
    integrity = all(
        not row["integrity_failure"]
        and int(row["payload_zero"]) == 1
        and int(row["ledger_exact"]) == 1
        and int(row["rng_neutral"]) == 1
        and int(row["repeat_exact"]) == 1
        for row in rows
    )
    identifiable = sum(int(row["identifiable"]) for row in channel_rows)
    interactions = sum(int(row["nonzero_factorial_interaction"]) for row in channel_rows)
    summary = {
        "finding": "078",
        "protocol": "developmental topology-by-state successor-accessibility feasibility",
        "finding075_outcomes_used": False,
        "channels": len(channel_rows),
        "factorial_states": len(rows),
        "expected_factorial_states": 175,
        "all_safety_and_repeat_checks_exact": integrity,
        "identifiable_channels": identifiable,
        "identifiable_required": 20,
        "nonzero_interaction_channels": interactions,
        "nonzero_interaction_required": 12,
        "finding078_feasibility_passed": bool(
            len(rows) == 175 and integrity and identifiable >= 20 and interactions >= 12
        ),
        "finding079_permitted": bool(
            len(rows) == 175 and integrity and identifiable >= 20 and interactions >= 12
        ),
        "receiver_selection_counts": {
            label: sum(row["selected_receiver"] == label for row in channel_rows)
            for label in RECEIVERS
        },
        "states_csv": str(states_path),
        "states_sha256": artifact_hash(states_path),
        "channels_csv": str(channels_path),
        "channels_sha256": artifact_hash(channels_path),
        "source_manifest": str(args.manifest),
        "source_manifest_sha256": artifact_hash(args.manifest),
        "worker_processes": int(args.workers),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
