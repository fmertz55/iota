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
from phase_free_constraint_transport import ledger_error
from phase_source_minimization_audit import clamp_stored_phase, phase_source_patch
from pre_articulation_channel_replay import (
    apply_state,
    hash_world,
    selector,
    selector_matches,
    state_record,
)
from predecessor_region_lineage import parse_coords
from successor_graph_role_audit import compact_signature, config_for_seed, coord, signatures


HORIZON = 128
VARIANTS = ("natural", "role_preserving", "role_breaking")
DEFAULT_CHANNEL_MANIFEST = Path(
    "output/findings/finding075/successor_graph_rewire_manifest.csv"
)
DEFAULT_BRANCH_MANIFEST = Path(
    "output/findings/finding075/successor_graph_branch_manifest.csv"
)
DEFAULT_OUTPUT_PREFIX = Path(
    "output/findings/finding075/successor_graph_susceptibility"
)
CHANNEL_MANIFEST_SHA256 = (
    "b1605fa59101839dbb79d9aca8522fbc8af2e0e65541835e60aea8eb3b5ae41d"
)
BRANCH_MANIFEST_SHA256 = (
    "4bff47df01e32d9313d48ca9b219051641b04af1cd28990140bc9d0b5db9a21b"
)

CONTROL_FIELDS = [
    "paired_channel_id", "init_seed", "sample_index", "control", "precursor_matches",
    "rebridge_matches", "selector_identity_exact", "split_reproduced",
    "rebridge_reproduced", "trajectory_sha256", "natural_sham_exact",
    "payload_zero", "ledger_exact", "integrity_failure",
]
BRANCH_FIELDS = [
    "paired_channel_id", "paired_channel_index", "init_seed", "sample_index",
    "variant", "branch_index", "branch_seed", "articulation_observed",
    "first_articulation_relative", "separation_lifetime", "first_closure_relative",
    "successor_activated", "successor_active_at_end", "component_count_end",
    "largest_component_end", "interface_union_end", "active_depleted_adjacency_end",
    "payload_zero", "ledger_exact", "integrity_failure",
]
CHANNEL_FIELDS = [
    "paired_channel_id", "paired_channel_index", "init_seed", "sample_index",
    "branches", "natural_articulations", "preserving_articulations",
    "breaking_articulations", "natural_rate", "preserving_rate", "breaking_rate",
    "preserve_over_break_discordances", "break_over_preserve_discordances",
    "branch_informative", "preserving_rate_higher", "preserving_strictly_closer_to_natural",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run frozen Finding 075 graph-role susceptibility branches."
    )
    parser.add_argument("--channel-manifest", type=Path, default=DEFAULT_CHANNEL_MANIFEST)
    parser.add_argument("--branch-manifest", type=Path, default=DEFAULT_BRANCH_MANIFEST)
    parser.add_argument("--canonical-config", type=Path, default=DEFAULT_CANONICAL_CONFIG)
    parser.add_argument("--output-prefix", type=Path, default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def full_state_hash(world: World) -> str:
    digest = hashlib.sha256()
    hash_world(digest, 0, world)
    return digest.hexdigest()


def gate_selector(row: dict[str, str], prefix: str) -> dict[str, Any]:
    return selector(row, prefix)


def run_factual_control(
    channel: dict[str, str], checkpoint: World, cfg: dict[str, Any], label: str
) -> dict[str, Any]:
    world = clone_world(checkpoint, int(channel["continuation_seed"]))
    precursor = gate_selector(channel, "precursor")
    rebridge = gate_selector(channel, "rebridge")
    split_offset = int(channel["split_offset"])
    rebridge_offset = int(channel["rebridge_offset"])
    target = coord(channel["precursor_target"])
    successor = parse_coords(channel["successor_bridge_cells"])
    selector_counts = {"precursor": 0, "rebridge": 0}
    selector_exact = True
    split_reproduced = False
    rebridge_reproduced = False
    payload_zero = True
    exact = True
    failures: list[str] = []
    digest = hashlib.sha256()

    try:
        with phase_source_patch(channel["variant"]):
            clamp_stored_phase(world, channel["variant"])
            for offset in range(1, rebridge_offset + 1):
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                pre_active = bool(world.active[target])
                pre_mask = world.active.copy() if offset == split_offset else None
                gate_ordinal = 0
                candidates: list[dict[str, Any]] = []

                def callback(candidate: dict[str, Any]) -> None:
                    nonlocal gate_ordinal, selector_exact
                    ordinal = gate_ordinal
                    gate_ordinal += 1
                    selected_name = ""
                    selected: dict[str, Any] | None = None
                    if offset == precursor["offset"] and ordinal == precursor["gate_ordinal"]:
                        selected_name, selected = "precursor", precursor
                    elif offset == rebridge["offset"] and ordinal == rebridge["gate_ordinal"]:
                        selected_name, selected = "rebridge", rebridge
                    if selected is None:
                        return None
                    matched, checks = selector_matches(candidate, selected)
                    selector_counts[selected_name] += 1
                    selector_exact &= matched
                    if not matched:
                        raise RuntimeError(f"{selected_name} selector changed: {checks}")
                    return None

                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = candidates.append
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = callback
                iota_rig.step(world, cfg)
                iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
                iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
                clamp_stored_phase(world, channel["variant"])
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                if offset in {precursor["offset"], split_offset, rebridge_offset}:
                    hash_world(digest, offset, world)
                if offset == split_offset and pre_mask is not None:
                    _, _, pre_count, _ = component_labels(pre_mask, bool(world.wrap), "cube26")
                    _, _, post_count, _ = component_labels(world.active, bool(world.wrap), "cube26")
                    split_reproduced = bool(
                        pre_active and not bool(world.active[target]) and post_count > pre_count
                    )
                if offset == rebridge_offset:
                    rebridge_reproduced = any(
                        candidate.get("status") == "succeeded"
                        and candidate.get("target_activated") is True
                        and tuple(candidate["target"]) in successor
                        for candidate in candidates
                    )
    except Exception as exc:
        failures.append(f"{type(exc).__name__}:{exc}")
    finally:
        iota_rig.HARD_TRANSFER_CANDIDATE_HOOK = None
        iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
    if selector_counts["precursor"] != 1:
        failures.append(f"precursor_matches={selector_counts['precursor']}")
    if selector_counts["rebridge"] != 1:
        failures.append(f"rebridge_matches={selector_counts['rebridge']}")
    return {
        "paired_channel_id": channel["paired_channel_id"],
        "init_seed": int(channel["init_seed"]),
        "sample_index": int(channel["sample_index"]),
        "control": label,
        "precursor_matches": selector_counts["precursor"],
        "rebridge_matches": selector_counts["rebridge"],
        "selector_identity_exact": int(selector_exact),
        "split_reproduced": int(split_reproduced),
        "rebridge_reproduced": int(rebridge_reproduced),
        "trajectory_sha256": digest.hexdigest(),
        "natural_sham_exact": "",
        "payload_zero": int(payload_zero),
        "ledger_exact": int(exact),
        "integrity_failure": ";".join(failures),
    }


def build_precursor_state(
    channel: dict[str, str], checkpoint: World, cfg: dict[str, Any]
) -> World:
    world = clone_world(checkpoint, int(channel["continuation_seed"]))
    precursor = gate_selector(channel, "precursor")
    target_expected = json.loads(channel["factual_target_post_state"])
    matches = 0
    exact_identity = True
    with phase_source_patch(channel["variant"]):
        clamp_stored_phase(world, channel["variant"])
        for offset in range(1, precursor["offset"] + 1):
            gate_ordinal = 0

            def callback(candidate: dict[str, Any]) -> None:
                nonlocal gate_ordinal, matches, exact_identity
                ordinal = gate_ordinal
                gate_ordinal += 1
                if offset == precursor["offset"] and ordinal == precursor["gate_ordinal"]:
                    matched, checks = selector_matches(candidate, precursor)
                    matches += 1
                    exact_identity &= matched
                    if not matched:
                        raise RuntimeError(f"precursor selector changed: {checks}")
                return None

            iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = callback
            iota_rig.step(world, cfg)
            iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
            clamp_stored_phase(world, channel["variant"])
    iota_rig.HARD_TRANSFER_GATE_OVERRIDE_HOOK = None
    target = coord(channel["precursor_target"])
    if matches != 1 or not exact_identity:
        raise RuntimeError("precursor state selector integrity failure")
    if state_record(world, target) != target_expected:
        raise RuntimeError("frozen precursor target post-state changed")
    if int(np.count_nonzero(world.P)) != 0 or ledger_error(world) != 0.0:
        raise RuntimeError("precursor state safety failure")
    return world


def swap_state(
    world: World, donor: tuple[int, int, int], receiver: tuple[int, int, int]
) -> bool:
    before = sorted(
        json.dumps(state_record(world, cell), sort_keys=True, separators=(",", ":"))
        for cell in (donor, receiver)
    )
    donor_state = state_record(world, donor)
    receiver_state = state_record(world, receiver)
    apply_state(world, donor, receiver_state)
    apply_state(world, receiver, donor_state)
    after = sorted(
        json.dumps(state_record(world, cell), sort_keys=True, separators=(",", ":"))
        for cell in (donor, receiver)
    )
    return before == after


def build_variant_states(
    channel: dict[str, str], precursor_world: World
) -> tuple[dict[str, World], dict[str, Any]]:
    target = coord(channel["precursor_target"])
    preserve_donor = coord(channel["rewire_preserve_donor"])
    break_donor = coord(channel["rewire_break_donor"])
    preserve_receiver = coord(channel["rewire_preserve_receiver"])
    break_receiver = coord(channel["rewire_break_receiver"])
    if preserve_donor != break_donor:
        raise RuntimeError("frozen preserving and breaking donors differ")
    natural = clone_world(precursor_world, int(channel["continuation_seed"]))
    preserving = clone_world(precursor_world, int(channel["continuation_seed"]))
    breaking = clone_world(precursor_world, int(channel["continuation_seed"]))
    preserve_multiset = swap_state(preserving, preserve_donor, preserve_receiver)
    break_multiset = swap_state(breaking, break_donor, break_receiver)
    natural_radial, natural_role = signatures(natural, target)
    preserve_radial, preserve_role = signatures(preserving, target)
    break_radial, break_role = signatures(breaking, target)
    expected_radial = channel["rewire_post_radial_signature"]
    expected_role = channel["rewire_post_role_signature"]
    checks = {
        "donor_common": preserve_donor == break_donor,
        "preserve_multiset": preserve_multiset,
        "break_multiset": break_multiset,
        "natural_radial": compact_signature(natural_radial) == expected_radial,
        "natural_role": compact_signature(natural_role) == expected_role,
        "preserve_radial": preserve_radial == natural_radial,
        "break_radial": break_radial == natural_radial,
        "preserve_role": preserve_role == natural_role,
        "break_role": break_role != natural_role,
        "active_count": len({int(np.count_nonzero(w.active)) for w in (natural, preserving, breaking)}) == 1,
        "ledger": all(ledger_error(w) == 0.0 for w in (natural, preserving, breaking)),
        "payload": all(int(np.count_nonzero(w.P)) == 0 for w in (natural, preserving, breaking)),
    }
    if not all(checks.values()):
        raise RuntimeError(f"frozen swap integrity failure: {checks}")
    return {
        "natural": natural,
        "role_preserving": preserving,
        "role_breaking": breaking,
    }, checks


def run_branch(
    channel: dict[str, str], cfg: dict[str, Any], variant: str, base: World,
    branch_index: int, branch_seed: int,
) -> dict[str, Any]:
    world = clone_world(base, branch_seed)
    target = coord(channel["precursor_target"])
    successor = parse_coords(channel["successor_bridge_cells"])
    payload_zero = True
    exact = True
    articulation = False
    articulation_relative: int | str = ""
    separation_lifetime = 0
    first_closure: int | str = ""
    separation_open = False
    baseline_count = 0
    successor_activated = False
    failures: list[str] = []
    try:
        with phase_source_patch(channel["variant"]):
            clamp_stored_phase(world, channel["variant"])
            for relative in range(1, HORIZON + 1):
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                pre_target = bool(world.active[target])
                pre_successor = {cell: bool(world.active[cell]) for cell in successor}
                pre_mask = world.active.copy()
                iota_rig.step(world, cfg)
                clamp_stored_phase(world, channel["variant"])
                payload_zero &= int(np.count_nonzero(world.P)) == 0
                exact &= ledger_error(world) == 0.0
                successor_activated |= any(
                    not pre_successor[cell] and bool(world.active[cell]) for cell in successor
                )
                target_died = pre_target and not bool(world.active[target])
                if target_died and not articulation:
                    _, _, pre_count, _ = component_labels(pre_mask, bool(world.wrap), "cube26")
                    _, _, post_count, _ = component_labels(world.active, bool(world.wrap), "cube26")
                    if post_count > pre_count:
                        articulation = True
                        articulation_relative = relative
                        separation_open = True
                        baseline_count = pre_count
                if separation_open:
                    _, _, count, _ = component_labels(world.active, bool(world.wrap), "cube26")
                    if count > baseline_count:
                        separation_lifetime += 1
                    else:
                        separation_open = False
                        first_closure = relative
    except Exception as exc:
        failures.append(f"{type(exc).__name__}:{exc}")
    _, _, component_count, largest = component_labels(world.active, bool(world.wrap), "cube26")
    interface = interface_metrics(world, "cube26")
    return {
        "paired_channel_id": channel["paired_channel_id"],
        "paired_channel_index": int(channel["paired_channel_index"]),
        "init_seed": int(channel["init_seed"]),
        "sample_index": int(channel["sample_index"]),
        "variant": variant,
        "branch_index": branch_index,
        "branch_seed": branch_seed,
        "articulation_observed": int(articulation),
        "first_articulation_relative": articulation_relative,
        "separation_lifetime": separation_lifetime,
        "first_closure_relative": first_closure,
        "successor_activated": int(successor_activated),
        "successor_active_at_end": int(any(bool(world.active[cell]) for cell in successor)),
        "component_count_end": component_count,
        "largest_component_end": largest,
        "interface_union_end": int(interface["interface_union_cells"]),
        "active_depleted_adjacency_end": float(interface["active_depleted_adjacency"]),
        "payload_zero": int(payload_zero),
        "ledger_exact": int(exact),
        "integrity_failure": ";".join(failures),
    }


def run_channel_job(
    job: tuple[str, dict[str, str], list[dict[str, str]]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    config_path, channel, assignments = job
    canonical = load_config(config_path)
    cfg = config_for_seed(canonical, int(channel["init_seed"]))
    checkpoint = run_to_checkpoint(cfg, channel["variant"], int(channel["checkpoint_tick"]))
    natural_control = run_factual_control(channel, checkpoint, cfg, "natural")
    sham_control = run_factual_control(channel, checkpoint, cfg, "sham")
    control_exact = int(
        natural_control["trajectory_sha256"] == sham_control["trajectory_sha256"]
    )
    natural_control["natural_sham_exact"] = control_exact
    sham_control["natural_sham_exact"] = control_exact
    precursor = build_precursor_state(channel, checkpoint, cfg)
    variant_states, checks = build_variant_states(channel, precursor)
    branches: list[dict[str, Any]] = []
    for assignment in assignments:
        for variant in VARIANTS:
            branches.append(
                run_branch(
                    channel, cfg, variant, variant_states[variant],
                    int(assignment["branch_index"]), int(assignment["branch_seed"]),
                )
            )
    print(
        f"f075 branches {channel['paired_channel_id']} seed={channel['init_seed']} "
        f"natural={sum(r['articulation_observed'] for r in branches if r['variant']=='natural')}/16 "
        f"preserve={sum(r['articulation_observed'] for r in branches if r['variant']=='role_preserving')}/16 "
        f"break={sum(r['articulation_observed'] for r in branches if r['variant']=='role_breaking')}/16 "
        f"errors={sum(bool(r['integrity_failure']) for r in branches)}",
        flush=True,
    )
    return [natural_control, sham_control], branches, checks


def binomial_upper_tail(successes: int, trials: int) -> float:
    if trials == 0:
        return 1.0
    return sum(math.comb(trials, value) for value in range(successes, trials + 1)) / (2 ** trials)


def main() -> None:
    args = parse_args()
    if artifact_hash(args.channel_manifest) != CHANNEL_MANIFEST_SHA256:
        raise RuntimeError("Finding 075 channel manifest changed")
    if artifact_hash(args.branch_manifest) != BRANCH_MANIFEST_SHA256:
        raise RuntimeError("Finding 075 branch manifest changed")
    if not 1 <= int(args.workers) <= 4:
        raise ValueError("--workers must be 1..4")
    channels = read_csv(args.channel_manifest)
    assignments = read_csv(args.branch_manifest)
    assignments_by_channel: dict[str, list[dict[str, str]]] = {}
    for row in assignments:
        assignments_by_channel.setdefault(row["paired_channel_id"], []).append(row)
    jobs = [
        (str(args.canonical_config), channel, sorted(
            assignments_by_channel[channel["paired_channel_id"]],
            key=lambda row: int(row["branch_index"]),
        ))
        for channel in channels
    ]
    controls: list[dict[str, Any]] = []
    branches: list[dict[str, Any]] = []
    swap_checks: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=int(args.workers)) as executor:
        for control_rows, branch_rows, checks in executor.map(run_channel_job, jobs):
            controls.extend(control_rows)
            branches.extend(branch_rows)
            swap_checks.append(checks)

    channel_rows: list[dict[str, Any]] = []
    favor = 0
    reverse = 0
    for channel in channels:
        channel_id = channel["paired_channel_id"]
        selected = [row for row in branches if row["paired_channel_id"] == channel_id]
        by_variant = {
            variant: sorted(
                [row for row in selected if row["variant"] == variant],
                key=lambda row: int(row["branch_index"]),
            )
            for variant in VARIANTS
        }
        counts = {
            variant: sum(int(row["articulation_observed"]) for row in rows)
            for variant, rows in by_variant.items()
        }
        local_favor = sum(
            int(preserve["articulation_observed"]) == 1
            and int(disrupt["articulation_observed"]) == 0
            for preserve, disrupt in zip(
                by_variant["role_preserving"], by_variant["role_breaking"], strict=True
            )
        )
        local_reverse = sum(
            int(preserve["articulation_observed"]) == 0
            and int(disrupt["articulation_observed"]) == 1
            for preserve, disrupt in zip(
                by_variant["role_preserving"], by_variant["role_breaking"], strict=True
            )
        )
        favor += local_favor
        reverse += local_reverse
        natural_rate = counts["natural"] / 16
        preserve_rate = counts["role_preserving"] / 16
        break_rate = counts["role_breaking"] / 16
        informative = preserve_rate != break_rate
        channel_rows.append(
            {
                "paired_channel_id": channel_id,
                "paired_channel_index": int(channel["paired_channel_index"]),
                "init_seed": int(channel["init_seed"]),
                "sample_index": int(channel["sample_index"]),
                "branches": 16,
                "natural_articulations": counts["natural"],
                "preserving_articulations": counts["role_preserving"],
                "breaking_articulations": counts["role_breaking"],
                "natural_rate": natural_rate,
                "preserving_rate": preserve_rate,
                "breaking_rate": break_rate,
                "preserve_over_break_discordances": local_favor,
                "break_over_preserve_discordances": local_reverse,
                "branch_informative": int(informative),
                "preserving_rate_higher": int(informative and preserve_rate > break_rate),
                "preserving_strictly_closer_to_natural": int(
                    abs(preserve_rate - natural_rate) < abs(break_rate - natural_rate)
                ),
            }
        )

    informative = [row for row in channel_rows if int(row["branch_informative"])]
    higher = sum(int(row["preserving_rate_higher"]) for row in informative)
    closer = sum(int(row["preserving_strictly_closer_to_natural"]) for row in channel_rows)
    p_value = binomial_upper_tail(favor, favor + reverse)
    controls_exact = all(
        int(row["selector_identity_exact"])
        and int(row["split_reproduced"])
        and int(row["rebridge_reproduced"])
        and int(row["natural_sham_exact"])
        and int(row["payload_zero"])
        and int(row["ledger_exact"])
        and not row["integrity_failure"]
        for row in controls
    )
    branches_exact = all(
        int(row["payload_zero"])
        and int(row["ledger_exact"])
        and not row["integrity_failure"]
        for row in branches
    )
    swaps_exact = all(all(checks.values()) for checks in swap_checks)
    direction_required = math.ceil((2 * len(informative)) / 3) if informative else 0
    closer_required = math.ceil((2 * len(channel_rows)) / 3)
    supported = bool(
        len(channel_rows) >= 12
        and controls_exact
        and branches_exact
        and swaps_exact
        and p_value < 0.05
        and len(informative) >= 8
        and higher >= direction_required
        and closer >= closer_required
    )

    controls_path = args.output_prefix.with_name(args.output_prefix.name + "_controls.csv")
    branches_path = args.output_prefix.with_name(args.output_prefix.name + "_branches.csv")
    channels_path = args.output_prefix.with_name(args.output_prefix.name + "_channels.csv")
    summary_path = args.output_prefix.with_name(args.output_prefix.name + "_summary.json")
    controls.sort(key=lambda row: (row["paired_channel_id"], row["control"]))
    branches.sort(key=lambda row: (
        row["paired_channel_id"], int(row["branch_index"]), VARIANTS.index(row["variant"])
    ))
    channel_rows.sort(key=lambda row: int(row["paired_channel_index"]))
    write_csv(controls_path, CONTROL_FIELDS, controls)
    write_csv(branches_path, BRANCH_FIELDS, branches)
    write_csv(channels_path, CHANNEL_FIELDS, channel_rows)
    summary = {
        "finding": "075E",
        "protocol": "common-RNG graph-role-conditioned articulation susceptibility",
        "channel_manifest": str(args.channel_manifest),
        "channel_manifest_sha256": artifact_hash(args.channel_manifest),
        "branch_manifest": str(args.branch_manifest),
        "branch_manifest_sha256": artifact_hash(args.branch_manifest),
        "channels": len(channel_rows),
        "branches_per_channel_variant": 16,
        "branch_outcomes": len(branches),
        "factual_controls": len(controls),
        "preserve_over_break_discordances": favor,
        "break_over_preserve_discordances": reverse,
        "discordant_pairs": favor + reverse,
        "one_sided_exact_mcnemar_p": p_value,
        "informative_channels": len(informative),
        "informative_channels_preserving_higher": higher,
        "informative_direction_required_two_thirds": direction_required,
        "channels_preserving_strictly_closer_to_natural": closer,
        "closer_required_two_thirds": closer_required,
        "all_factual_controls_exact": controls_exact,
        "all_branch_safety_exact": branches_exact,
        "all_swap_invariants_exact": swaps_exact,
        "graph_role_hypothesis_supported": supported,
        "finding076_permitted": supported,
        "controls_csv": str(controls_path),
        "controls_sha256": artifact_hash(controls_path),
        "branches_csv": str(branches_path),
        "branches_sha256": artifact_hash(branches_path),
        "channels_csv": str(channels_path),
        "channels_sha256": artifact_hash(channels_path),
        "worker_processes": int(args.workers),
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
