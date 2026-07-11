from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

import iota_rig
from component_bridge_causal_trace import component_labels, csv_bool, write_csv
from continuation import clone_world
from iota_rig import World, load_config
from phase_free_class_matrix import run_to_checkpoint
from phase_free_constraint_transport import ledger_error, pair_distances, pair_reachability
from phase_source_minimization_audit import clamp_stored_phase, discover_config, phase_source_patch
from predecessor_region_lineage import parse_coords, read_events, reconstruct_regions


CASE_FIELDNAMES = [
    "init_seed",
    "variant",
    "sample_index",
    "continuation_seed",
    "start_offset",
    "rebridge_offset",
    "horizon",
    "finding060_constraint_transport",
    "relation_reachable_at_rebridge",
    "expression_relation_lifetime",
    "singleton_address_loss_offset",
    "singleton_expression_loss_offset",
    "singleton_expression_survives_address_loss",
    "expression_survival_beyond_address_loss",
    "first_expression_relation_loss_offset",
    "second_rebridge_offset",
    "second_successor_cells",
    "second_successor_role_critical",
    "second_successor_disjoint",
    "second_strict_transport",
    "lineage_collision",
    "payload_zero_all_offsets",
    "ledger_exact_all_offsets",
]

TIMELINE_FIELDNAMES = [
    "init_seed",
    "variant",
    "sample_index",
    "start_offset",
    "offset",
    "large_lineage_size",
    "singleton_lineage_size",
    "singleton_original_address_active",
    "singleton_children_activated",
    "lineages_alive",
    "lineage_collision",
    "reachable_pair_fraction",
    "mean_shortest_path",
    "payload_nonzero",
    "ledger_error",
]

ANCESTRY_FIELDNAMES = [
    "init_seed",
    "variant",
    "sample_index",
    "start_offset",
    "offset",
    "lineage_role",
    "source",
    "target",
    "source_active_after",
    "target_depleted_before",
    "candidate_order",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Track prospective source-to-target expression lineages after Finding 060."
    )
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument(
        "--event-csv",
        default="output/findings/finding060/phase_free_constraint_transport_events.csv",
    )
    parser.add_argument("--config-dir", default="output/findings/configs")
    parser.add_argument("--checkpoint-tick", type=int, default=2048)
    parser.add_argument("--horizon", type=int, default=1024)
    parser.add_argument("--strict-only", action="store_true")
    parser.add_argument("--skip-equivalence-gate", action="store_true")
    return parser.parse_args()


def world_equal(left: World, right: World) -> bool:
    arrays = (
        "active",
        "A",
        "R",
        "V",
        "P",
        "latent_A",
        "angular_L",
        "previous_active",
        "previous_V",
        "vectors",
    )
    return (
        all(np.array_equal(getattr(left, name), getattr(right, name)) for name in arrays)
        and left.vector_behaviors == right.vector_behaviors
        and left.wrap == right.wrap
        and left.initial_total_A == right.initial_total_A
        and left.ledger_enabled == right.ledger_enabled
        and left.rng.bit_generator.state == right.rng.bit_generator.state
    )


def verify_hook_equivalence(
    checkpoint: World,
    cfg: dict[str, Any],
    variant: str,
    continuation_seed: int,
    horizon: int = 128,
) -> int:
    control = clone_world(checkpoint, continuation_seed)
    observed = clone_world(checkpoint, continuation_seed)
    observed_events: list[dict[str, Any]] = []
    with phase_source_patch(variant):
        clamp_stored_phase(control, variant)
        clamp_stored_phase(observed, variant)
        for _ in range(int(horizon)):
            iota_rig.HARD_TRANSFER_TRACE_HOOK = None
            iota_rig.step(control, cfg)
            clamp_stored_phase(control, variant)
            iota_rig.HARD_TRANSFER_TRACE_HOOK = observed_events.append
            iota_rig.step(observed, cfg)
            clamp_stored_phase(observed, variant)
            iota_rig.HARD_TRANSFER_TRACE_HOOK = None
            if not world_equal(control, observed):
                raise RuntimeError("hard-transfer trace hook changed simulation state")
    return len(observed_events)


def lineage_relation(
    world: World,
    lineages: list[set[tuple[int, int, int]]],
) -> tuple[bool, float, float | str]:
    alive = len(lineages) == 2 and all(lineages)
    labels, _, _, _ = component_labels(world.active, bool(world.wrap), "cube26")
    reachability, _ = pair_reachability(labels, lineages)
    distances = pair_distances(world.active, lineages, bool(world.wrap))
    finite = [float(value) for value in distances if value is not None]
    mean_distance: float | str = "" if not finite else float(sum(finite) / len(finite))
    return alive, reachability, mean_distance


def advance_lineages(
    before: list[set[tuple[int, int, int]]],
    world: World,
    events: list[dict[str, Any]],
) -> tuple[
    list[set[tuple[int, int, int]]],
    bool,
    list[int],
    list[dict[str, Any]],
]:
    claims: dict[tuple[int, int, int], set[int]] = {}
    claim_events: dict[tuple[tuple[int, int, int], int], dict[str, Any]] = {}
    child_counts = [0 for _ in before]
    for event in events:
        if not bool(event["target_activated"]):
            continue
        source = tuple(event["source"])
        target = tuple(event["target"])
        for index, lineage in enumerate(before):
            if source in lineage:
                claims.setdefault(target, set()).add(index)
                claim_events[(target, index)] = event
    collisions = {target for target, owners in claims.items() if len(owners) > 1}
    after: list[set[tuple[int, int, int]]] = []
    inherited: list[dict[str, Any]] = []
    for index, lineage in enumerate(before):
        retained = {coord for coord in lineage if bool(world.active[coord])}
        children = {
            target
            for target, owners in claims.items()
            if target not in collisions and owners == {index}
        }
        child_counts[index] = len(children)
        for target in sorted(children):
            event = claim_events[(target, index)]
            inherited.append(
                {
                    "lineage_index": index,
                    "source": tuple(event["source"]),
                    "target": target,
                    "source_active_after": bool(world.active[tuple(event["source"])]),
                    "target_depleted_before": bool(event["target_depleted"]),
                    "candidate_order": int(event["candidate_order"]),
                }
            )
        after.append(retained | children)
    return after, bool(collisions), child_counts, inherited


def causal_gained_cells_for_lineages(
    previous_active: np.ndarray,
    world: World,
    lineages: list[set[tuple[int, int, int]]],
) -> set[tuple[int, int, int]]:
    gained = {
        tuple(int(value) for value in coord)
        for coord in np.argwhere(world.active & ~previous_active)
    }
    causal: set[tuple[int, int, int]] = set()
    lineage_cells = set().union(*lineages) if lineages else set()
    for coord in gained - lineage_cells:
        removed = world.active.copy()
        removed[coord] = False
        labels, _, _, _ = component_labels(removed, bool(world.wrap), "cube26")
        reachability, _ = pair_reachability(labels, lineages)
        if reachability < 1.0:
            causal.add(coord)
    return causal


def coords_text(coords: set[tuple[int, int, int]]) -> str:
    return ";".join(":".join(str(value) for value in coord) for coord in sorted(coords))


def replay(
    args: argparse.Namespace,
    event: dict[str, str],
    checkpoint: World,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    seed = int(event["init_seed"])
    variant = event["variant"]
    sample = int(event["sample_index"])
    continuation_seed = int(event["continuation_seed"])
    start_offset = int(event["start_offset"])
    rebridge_offset = int(event["rebridge_offset"])
    prior_bridge = parse_coords(event["successor_bridge_cells"])
    world = clone_world(checkpoint, continuation_seed)
    snapshots: dict[int, World] = {}
    regions: list[set[tuple[int, int, int]]] = []
    lineages: list[set[tuple[int, int, int]]] = []
    terminated = [False, False]
    singleton_original: tuple[int, int, int] | None = None
    singleton_address_loss: int | str = ""
    singleton_expression_loss: int | str = ""
    relation_lifetime = 0
    relation_loss: int | str = ""
    loss_seen = False
    second_rebridge: int | str = ""
    second_successor: set[tuple[int, int, int]] = set()
    collision = False
    payload_zero = True
    ledger_exact = True
    timeline: list[dict[str, Any]] = []
    ancestry: list[dict[str, Any]] = []
    previous_active = world.active.copy()
    reachable_at_rebridge = False
    children_into_current = [0, 0]

    try:
        with phase_source_patch(variant):
            clamp_stored_phase(world, variant)
            for offset in range(int(args.horizon) + 1):
                payload_zero = payload_zero and int(np.count_nonzero(world.P)) == 0
                ledger_exact = ledger_exact and ledger_error(world) == 0.0
                if offset in {start_offset - 1, start_offset}:
                    snapshots[offset] = clone_world(world, continuation_seed)
                if offset == start_offset:
                    regions, reconstructed = reconstruct_regions(
                        snapshots[start_offset - 1], snapshots[start_offset]
                    )
                    if reconstructed != parse_coords(event["original_bridge_cells"]):
                        raise RuntimeError("original bridge reconstruction mismatch")

                if offset == rebridge_offset:
                    lineages = [
                        {coord for coord in region if bool(world.active[coord])}
                        for region in regions
                    ]
                    if len(lineages) != 2:
                        raise RuntimeError("expression-lineage gate requires two predecessor regions")
                    singleton_index = min(range(2), key=lambda index: len(regions[index]))
                    if len(regions[singleton_index]) != 1:
                        raise RuntimeError("expression-lineage gate requires singleton predecessor")
                    singleton_original = next(iter(regions[singleton_index]))
                    alive, reachability, _ = lineage_relation(world, lineages)
                    reachable_at_rebridge = alive and reachability == 1.0

                if lineages and offset >= rebridge_offset:
                    singleton_index = min(range(2), key=lambda index: len(regions[index]))
                    alive, reachability, mean_distance = lineage_relation(world, lineages)
                    if (
                        singleton_address_loss == ""
                        and singleton_original is not None
                        and not bool(world.active[singleton_original])
                    ):
                        singleton_address_loss = offset
                    if singleton_expression_loss == "" and not lineages[singleton_index]:
                        singleton_expression_loss = offset
                    relation_alive = alive and reachability == 1.0 and not collision
                    if relation_loss == "" and relation_alive:
                        relation_lifetime += 1
                    elif relation_loss == "" and not relation_alive:
                        relation_loss = offset
                        loss_seen = alive and not collision
                    elif (
                        loss_seen
                        and not collision
                        and second_rebridge == ""
                        and relation_alive
                    ):
                        candidate = causal_gained_cells_for_lineages(
                            previous_active, world, lineages
                        )
                        if candidate:
                            second_rebridge = offset
                            second_successor = candidate

                    timeline.append(
                        {
                            "init_seed": seed,
                            "variant": variant,
                            "sample_index": sample,
                            "start_offset": start_offset,
                            "offset": offset,
                            "large_lineage_size": len(lineages[1 - singleton_index]),
                            "singleton_lineage_size": len(lineages[singleton_index]),
                            "singleton_original_address_active": csv_bool(
                                singleton_original is not None
                                and bool(world.active[singleton_original])
                            ),
                            "singleton_children_activated": children_into_current[
                                singleton_index
                            ],
                            "lineages_alive": csv_bool(alive),
                            "lineage_collision": csv_bool(collision),
                            "reachable_pair_fraction": reachability,
                            "mean_shortest_path": mean_distance,
                            "payload_nonzero": int(np.count_nonzero(world.P)),
                            "ledger_error": ledger_error(world),
                        }
                    )

                if offset < int(args.horizon):
                    previous_active = world.active.copy()
                    events: list[dict[str, Any]] = []
                    iota_rig.HARD_TRANSFER_TRACE_HOOK = events.append
                    iota_rig.step(world, cfg)
                    iota_rig.HARD_TRANSFER_TRACE_HOOK = None
                    clamp_stored_phase(world, variant)
                    if lineages and offset >= rebridge_offset:
                        next_lineages, collided, child_counts, inherited = advance_lineages(
                            lineages, world, events
                        )
                        singleton_index = min(
                            range(2), key=lambda index: len(regions[index])
                        )
                        for inheritance in inherited:
                            ancestry.append(
                                {
                                    "init_seed": seed,
                                    "variant": variant,
                                    "sample_index": sample,
                                    "start_offset": start_offset,
                                    "offset": offset + 1,
                                    "lineage_role": (
                                        "singleton"
                                        if inheritance["lineage_index"] == singleton_index
                                        else "large"
                                    ),
                                    "source": coords_text({inheritance["source"]}),
                                    "target": coords_text({inheritance["target"]}),
                                    "source_active_after": csv_bool(
                                        inheritance["source_active_after"]
                                    ),
                                    "target_depleted_before": csv_bool(
                                        inheritance["target_depleted_before"]
                                    ),
                                    "candidate_order": inheritance["candidate_order"],
                                }
                            )
                        collision = collision or collided
                        for index in range(2):
                            if terminated[index]:
                                next_lineages[index] = set()
                            elif not next_lineages[index]:
                                terminated[index] = True
                        lineages = next_lineages
                        children_into_current = child_counts
    finally:
        iota_rig.HARD_TRANSFER_TRACE_HOOK = None

    singleton_survives = (
        singleton_address_loss != ""
        and (
            singleton_expression_loss == ""
            or int(singleton_expression_loss) > int(singleton_address_loss)
        )
    )
    survival_beyond = (
        0
        if not singleton_survives
        else (
            int(args.horizon) - int(singleton_address_loss) + 1
            if singleton_expression_loss == ""
            else int(singleton_expression_loss) - int(singleton_address_loss)
        )
    )
    successor_critical = bool(second_successor)
    successor_disjoint = bool(second_successor) and not bool(prior_bridge & second_successor)
    second_strict = bool(
        second_rebridge != ""
        and successor_critical
        and successor_disjoint
        and not collision
        and payload_zero
        and ledger_exact
    )
    case = {
        "init_seed": seed,
        "variant": variant,
        "sample_index": sample,
        "continuation_seed": continuation_seed,
        "start_offset": start_offset,
        "rebridge_offset": rebridge_offset,
        "horizon": int(args.horizon),
        "finding060_constraint_transport": event["constraint_transport"],
        "relation_reachable_at_rebridge": csv_bool(reachable_at_rebridge),
        "expression_relation_lifetime": relation_lifetime,
        "singleton_address_loss_offset": singleton_address_loss,
        "singleton_expression_loss_offset": singleton_expression_loss,
        "singleton_expression_survives_address_loss": csv_bool(singleton_survives),
        "expression_survival_beyond_address_loss": survival_beyond,
        "first_expression_relation_loss_offset": relation_loss,
        "second_rebridge_offset": second_rebridge,
        "second_successor_cells": coords_text(second_successor),
        "second_successor_role_critical": csv_bool(successor_critical),
        "second_successor_disjoint": csv_bool(successor_disjoint),
        "second_strict_transport": csv_bool(second_strict),
        "lineage_collision": csv_bool(collision),
        "payload_zero_all_offsets": csv_bool(payload_zero),
        "ledger_exact_all_offsets": csv_bool(ledger_exact),
    }
    return case, timeline, ancestry


def main() -> None:
    args = parse_args()
    events = read_events(Path(args.event_csv), bool(args.strict_only))
    keys = sorted({(int(row["init_seed"]), row["variant"]) for row in events})
    configs: dict[int, dict[str, Any]] = {}
    checkpoints: dict[tuple[int, str], World] = {}
    for seed, variant in keys:
        if seed not in configs:
            configs[seed] = load_config(discover_config(args.config_dir, seed))
        print(f"checkpoint seed={seed} variant={variant}", flush=True)
        checkpoints[(seed, variant)] = run_to_checkpoint(
            configs[seed], variant, int(args.checkpoint_tick)
        )

    equivalence_passed = False
    equivalence_event_count = 0
    if events and not args.skip_equivalence_gate:
        first = events[0]
        key = (int(first["init_seed"]), first["variant"])
        equivalence_event_count = verify_hook_equivalence(
            checkpoints[key],
            configs[key[0]],
            key[1],
            int(first["continuation_seed"]),
        )
        equivalence_passed = True
        print(
            f"instrumentation equivalence passed events={equivalence_event_count}",
            flush=True,
        )

    cases: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    ancestry: list[dict[str, Any]] = []
    for event in events:
        key = (int(event["init_seed"]), event["variant"])
        case, rows, inheritance_rows = replay(
            args, event, checkpoints[key], configs[key[0]]
        )
        cases.append(case)
        timeline.extend(rows)
        ancestry.extend(inheritance_rows)
        print(
            f"event seed={case['init_seed']} sample={case['sample_index']} "
            f"offset={case['start_offset']} expression_lifetime={case['expression_relation_lifetime']} "
            f"survives_address_loss={case['singleton_expression_survives_address_loss']} "
            f"second_transport={case['second_strict_transport']}",
            flush=True,
        )

    prefix = Path(args.output_prefix)
    case_path = prefix.with_name(prefix.name + "_cases.csv")
    timeline_path = prefix.with_name(prefix.name + "_timeline.csv")
    ancestry_path = prefix.with_name(prefix.name + "_ancestry.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    write_csv(case_path, CASE_FIELDNAMES, cases)
    write_csv(timeline_path, TIMELINE_FIELDNAMES, timeline)
    write_csv(ancestry_path, ANCESTRY_FIELDNAMES, ancestry)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "cases": len(cases),
        "strict_input_cases": sum(int(row["finding060_constraint_transport"]) for row in cases),
        "singleton_expression_survival_cases": sum(
            int(row["singleton_expression_survives_address_loss"]) for row in cases
        ),
        "second_strict_transport_cases": sum(int(row["second_strict_transport"]) for row in cases),
        "lineage_collision_cases": sum(int(row["lineage_collision"]) for row in cases),
        "instrumentation_equivalence_passed": equivalence_passed,
        "instrumentation_equivalence_event_count": equivalence_event_count,
        "all_payload_zero": all(int(row["payload_zero_all_offsets"]) for row in cases),
        "all_ledger_exact": all(int(row["ledger_exact_all_offsets"]) for row in cases),
        "case_csv": str(case_path),
        "timeline_csv": str(timeline_path),
        "ancestry_csv": str(ancestry_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
