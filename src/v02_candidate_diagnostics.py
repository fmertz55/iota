from __future__ import annotations

import argparse
import copy
import csv
import json
from collections import Counter, deque
from pathlib import Path
from typing import Any

import numpy as np

from iota_rig import candidate_neighbor_steps, init_world, load_config, save_world_state, step
from metrics import collect_metrics


COUNT_KEYS = {
    "exchanges",
    "secondary_exchanges",
    "payload_changes",
    "deactivation_events",
    "amplitude_transfers",
    "failed_transfer_gates",
    "secondary_vector_kicks",
    "residual_participations",
    "depleted_reactivations",
}


METRIC_FIELDNAMES = [
    "tick",
    "active_iotas",
    "depleted_cells",
    "total_A",
    "active_A",
    "latent_A",
    "ledger_error",
    "amplitude_transfers",
    "failed_transfer_gates",
    "secondary_vector_kicks",
    "residual_participations",
    "deactivation_events",
    "largest_coherence_face6",
    "coherence_ratio_face6",
    "coherence_count_face6",
    "top5_component_coverage_face6",
    "top20_component_coverage_face6",
    "component_size_entropy_face6",
    "largest_coherence_face18",
    "coherence_ratio_face18",
    "coherence_count_face18",
    "top5_component_coverage_face18",
    "top20_component_coverage_face18",
    "component_size_entropy_face18",
    "largest_coherence_cube26",
    "coherence_ratio_cube26",
    "coherence_count_cube26",
    "top5_component_coverage_cube26",
    "top20_component_coverage_cube26",
    "component_size_entropy_cube26",
]


STRUCTURE_FIELDNAMES = [
    "tick",
    "connectivity",
    "mask",
    "cell_count",
    "component_count",
    "largest_component",
    "top1_fraction",
    "top5_coverage",
    "top20_coverage",
    "component_size_entropy",
    "component_size_slope",
    "component_size_1",
    "component_size_2",
    "component_size_3",
    "active_cells_adjacent_to_depleted",
    "active_adjacent_to_depleted_fraction",
    "depleted_cells_adjacent_to_active",
    "depleted_adjacent_to_active_fraction",
    "top_active_component_adjacent_to_depleted",
    "top_active_component_adjacent_to_depleted_fraction",
    "top_active_payload_entropy",
    "top_active_vector_entropy",
    "top_active_dominant_payload",
    "top_active_dominant_payload_fraction",
    "top_active_bbox_density",
]


def entropy_from_counts(counts: np.ndarray) -> float:
    total = float(np.sum(counts))
    if total <= 0:
        return 0.0
    probabilities = counts[counts > 0].astype(np.float64) / total
    return float(-np.sum(probabilities * np.log2(probabilities)))


def component_hierarchy_stats(sizes: list[int], cell_count: int) -> dict[str, float]:
    if cell_count <= 0 or not sizes:
        return {
            "top1_fraction": 0.0,
            "top5_coverage": 0.0,
            "top20_coverage": 0.0,
            "component_size_entropy": 0.0,
            "component_size_slope": 0.0,
        }
    values = np.array(sizes, dtype=np.float64)
    probabilities = values / float(cell_count)
    entropy = float(-np.sum(probabilities * np.log2(probabilities)))
    if len(values) >= 2:
        ranks = np.arange(1, len(values) + 1, dtype=np.float64)
        slope = float(np.polyfit(np.log(ranks), np.log(values), 1)[0])
    else:
        slope = 0.0
    return {
        "top1_fraction": float(values[0] / cell_count),
        "top5_coverage": float(np.sum(values[:5]) / cell_count),
        "top20_coverage": float(np.sum(values[:20]) / cell_count),
        "component_size_entropy": entropy,
        "component_size_slope": slope,
    }


def components_for_mask(
    mask: np.ndarray,
    connectivity: str,
    wrap: bool,
) -> list[frozenset[tuple[int, int, int]]]:
    size = int(mask.shape[0])
    remaining = {tuple(int(value) for value in coord) for coord in np.argwhere(mask)}
    neighbors = tuple(
        (int(dx), int(dy), int(dz))
        for dx, dy, dz in candidate_neighbor_steps(connectivity)
    )
    components: list[frozenset[tuple[int, int, int]]] = []
    while remaining:
        start = remaining.pop()
        coords = [start]
        queue: deque[tuple[int, int, int]] = deque([start])
        while queue:
            x, y, z = queue.popleft()
            for dx, dy, dz in neighbors:
                nx, ny, nz = x + dx, y + dy, z + dz
                if wrap:
                    nx %= size
                    ny %= size
                    nz %= size
                elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
                    continue
                neighbor = (nx, ny, nz)
                if neighbor not in remaining:
                    continue
                remaining.remove(neighbor)
                coords.append(neighbor)
                queue.append(neighbor)
        components.append(frozenset(coords))
    components.sort(key=len, reverse=True)
    return components


def adjacency_counts(
    active_mask: np.ndarray,
    depleted_mask: np.ndarray,
    connectivity: str,
    wrap: bool,
    top_active_component: frozenset[tuple[int, int, int]] | None,
) -> dict[str, float]:
    size = int(active_mask.shape[0])
    neighbors = tuple(
        (int(dx), int(dy), int(dz))
        for dx, dy, dz in candidate_neighbor_steps(connectivity)
    )
    active_adjacent: set[tuple[int, int, int]] = set()
    depleted_adjacent: set[tuple[int, int, int]] = set()
    top_active_adjacent: set[tuple[int, int, int]] = set()
    for coord in np.argwhere(active_mask):
        x, y, z = (int(value) for value in coord)
        active_coord = (x, y, z)
        for dx, dy, dz in neighbors:
            nx, ny, nz = x + dx, y + dy, z + dz
            if wrap:
                nx %= size
                ny %= size
                nz %= size
            elif not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
                continue
            if not bool(depleted_mask[nx, ny, nz]):
                continue
            depleted_coord = (nx, ny, nz)
            active_adjacent.add(active_coord)
            depleted_adjacent.add(depleted_coord)
            if top_active_component is not None and active_coord in top_active_component:
                top_active_adjacent.add(active_coord)
    active_count = int(np.count_nonzero(active_mask))
    depleted_count = int(np.count_nonzero(depleted_mask))
    top_count = len(top_active_component or ())
    return {
        "active_cells_adjacent_to_depleted": float(len(active_adjacent)),
        "active_adjacent_to_depleted_fraction": float(len(active_adjacent) / active_count) if active_count else 0.0,
        "depleted_cells_adjacent_to_active": float(len(depleted_adjacent)),
        "depleted_adjacent_to_active_fraction": float(len(depleted_adjacent) / depleted_count) if depleted_count else 0.0,
        "top_active_component_adjacent_to_depleted": float(len(top_active_adjacent)),
        "top_active_component_adjacent_to_depleted_fraction": float(len(top_active_adjacent) / top_count) if top_count else 0.0,
    }


def top_active_content_stats(world: Any, component: frozenset[tuple[int, int, int]] | None) -> dict[str, float]:
    if not component:
        return {
            "top_active_payload_entropy": 0.0,
            "top_active_vector_entropy": 0.0,
            "top_active_dominant_payload": 0.0,
            "top_active_dominant_payload_fraction": 0.0,
            "top_active_bbox_density": 0.0,
        }
    coords = np.array(list(component), dtype=np.int32)
    xs = coords[:, 0]
    ys = coords[:, 1]
    zs = coords[:, 2]
    payloads = world.P[xs, ys, zs].astype(np.int64)
    vectors = world.V[xs, ys, zs].astype(np.int64) % len(world.vectors)
    payload_counts = np.bincount(payloads, minlength=8)
    vector_counts = np.bincount(vectors, minlength=len(world.vectors))
    dominant_payload = int(np.argmax(payload_counts))
    bbox_volume = (
        int(xs.max() - xs.min() + 1)
        * int(ys.max() - ys.min() + 1)
        * int(zs.max() - zs.min() + 1)
    )
    return {
        "top_active_payload_entropy": entropy_from_counts(payload_counts),
        "top_active_vector_entropy": entropy_from_counts(vector_counts),
        "top_active_dominant_payload": float(dominant_payload),
        "top_active_dominant_payload_fraction": float(payload_counts[dominant_payload] / len(component)),
        "top_active_bbox_density": float(len(component) / bbox_volume) if bbox_volume else 0.0,
    }


def structure_rows(world: Any, tick: int) -> list[dict[str, Any]]:
    active_mask = world.active
    depleted_mask = (~world.active) & (world.latent_A == 0)
    rows: list[dict[str, Any]] = []
    for connectivity in ("face6", "face18", "cube26"):
        active_components = components_for_mask(active_mask, connectivity, world.wrap)
        top_active_component = active_components[0] if active_components else None
        content_stats = top_active_content_stats(world, top_active_component)
        adjacency = adjacency_counts(
            active_mask,
            depleted_mask,
            connectivity,
            world.wrap,
            top_active_component,
        )
        for mask_name, components, cell_count in (
            ("active", active_components, int(np.count_nonzero(active_mask))),
            (
                "depleted",
                components_for_mask(depleted_mask, connectivity, world.wrap),
                int(np.count_nonzero(depleted_mask)),
            ),
        ):
            sizes = [len(component) for component in components]
            row = {
                "tick": tick,
                "connectivity": connectivity,
                "mask": mask_name,
                "cell_count": cell_count,
                "component_count": len(components),
                "largest_component": sizes[0] if sizes else 0,
                "component_size_1": sizes[0] if len(sizes) > 0 else 0,
                "component_size_2": sizes[1] if len(sizes) > 1 else 0,
                "component_size_3": sizes[2] if len(sizes) > 2 else 0,
                **component_hierarchy_stats(sizes, cell_count),
            }
            if mask_name == "active":
                row.update(adjacency)
                row.update(content_stats)
            else:
                row.update({key: "" for key in adjacency})
                row.update({key: "" for key in content_stats})
            rows.append(row)
    return rows


def configure(args: argparse.Namespace) -> dict[str, Any]:
    cfg = copy.deepcopy(load_config(args.config))
    cfg["simulation_version"] = "iota-rig-v0.2.0"
    cfg.setdefault("init", {})["seed"] = int(args.seed)
    cfg["init"]["active_iotas"] = int(args.active_iotas)
    constants = cfg.setdefault("constants", {})
    constants["conservation"] = "hard"
    constants["deactivation"] = "exhaustion"
    constants["amplitude_coupling"] = float(args.amplitude_coupling)
    constants["vacuum_amplitude"] = int(args.vacuum_amplitude)
    constants["valence"] = int(args.valence)
    constants["bond_probability"] = float(args.bond_probability)
    cfg.setdefault("run", {})["ticks"] = int(args.ticks)
    return cfg


def accumulate_counts(pending: dict[str, float], extras: dict[str, float]) -> None:
    for key, value in extras.items():
        numeric = float(value)
        if key in COUNT_KEYS:
            pending[key] = float(pending.get(key, 0.0)) + numeric
        else:
            pending[key] = numeric


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def parse_sample_ticks(args: argparse.Namespace) -> list[int]:
    if args.sample_ticks:
        return sorted({int(value) for value in args.sample_ticks if 0 <= int(value) <= int(args.ticks)})
    ticks = set(range(0, int(args.ticks) + 1, int(args.sample_every)))
    ticks.add(int(args.ticks))
    return sorted(ticks)


def main() -> None:
    args = parse_args()
    cfg = configure(args)
    output_prefix = Path(args.output_prefix)
    sample_ticks = parse_sample_ticks(args)
    sample_tick_set = set(sample_ticks)
    world = init_world(cfg)
    pending_extras: dict[str, float] = {}
    metric_rows: list[dict[str, Any]] = []
    structural_rows: list[dict[str, Any]] = []
    final_tick = int(args.ticks)
    early_stop_reason = ""

    for tick in range(0, int(args.ticks) + 1):
        if tick in sample_tick_set:
            metric = collect_metrics(world, tick, pending_extras)
            pending_extras = {}
            metric_rows.append(metric)
            structural_rows.extend(structure_rows(world, tick))
        if tick == int(args.ticks):
            break
        extras = step(world, cfg)
        accumulate_counts(pending_extras, extras)
        active_count = int(world.active.sum())
        if int(args.stop_active_iotas) > 0 and active_count >= int(args.stop_active_iotas):
            final_tick = tick + 1
            early_stop_reason = f"active_iotas >= {args.stop_active_iotas}"
            metric = collect_metrics(world, final_tick, pending_extras)
            pending_extras = {}
            metric_rows.append(metric)
            structural_rows.extend(structure_rows(world, final_tick))
            break

    final_state_path = output_prefix.with_suffix(".npz")
    save_world_state(
        world,
        final_state_path,
        {
            "final_tick": final_tick,
            "early_stop_reason": early_stop_reason,
            "seed": args.seed,
            "amplitude_coupling": args.amplitude_coupling,
            "vacuum_amplitude": args.vacuum_amplitude,
            "valence": args.valence,
            "active_iotas": args.active_iotas,
            "bond_probability": args.bond_probability,
        },
    )
    metrics_path = output_prefix.with_name(output_prefix.name + "_metrics.csv")
    structures_path = output_prefix.with_name(output_prefix.name + "_structures.csv")
    summary_path = output_prefix.with_suffix(".json")
    write_csv(metrics_path, METRIC_FIELDNAMES, metric_rows)
    write_csv(structures_path, STRUCTURE_FIELDNAMES, structural_rows)
    summary = {
        "config": {
            "seed": args.seed,
            "amplitude_coupling": args.amplitude_coupling,
            "vacuum_amplitude": args.vacuum_amplitude,
            "valence": args.valence,
            "active_iotas": args.active_iotas,
            "bond_probability": args.bond_probability,
            "ticks": args.ticks,
            "stop_active_iotas": args.stop_active_iotas,
        },
        "final_tick": final_tick,
        "early_stop_reason": early_stop_reason,
        "metrics_path": metrics_path.as_posix(),
        "structures_path": structures_path.as_posix(),
        "final_state_path": final_state_path.as_posix(),
        "sample_ticks": sample_ticks,
        "final_metric": metric_rows[-1] if metric_rows else {},
        "final_structure_rows": [
            row for row in structural_rows if int(row["tick"]) == final_tick
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v0.2 candidate and compute active/depleted front diagnostics.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--amplitude-coupling", type=float, required=True)
    parser.add_argument("--vacuum-amplitude", type=int, required=True)
    parser.add_argument("--valence", type=int, required=True)
    parser.add_argument("--active-iotas", type=int, required=True)
    parser.add_argument("--bond-probability", type=float, default=1.0)
    parser.add_argument("--ticks", type=int, default=2048)
    parser.add_argument("--sample-every", type=int, default=256)
    parser.add_argument("--sample-ticks", type=int, nargs="+", default=None)
    parser.add_argument("--stop-active-iotas", type=int, default=0)
    parser.add_argument("--output-prefix", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    main()
