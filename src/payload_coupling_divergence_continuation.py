from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from iota_rig import init_world, load_config, step
from metrics import collect_metrics
from payload_coupling_bracket_4096_sweep import probe_config
from payload_coupling_divergence_trace import (
    HIGH_COUPLING,
    HIGH_LABEL,
    LOW_COUPLING,
    LOW_LABEL,
    trace_step,
)


DIVERGENCE_TICK = 337
DIVERGENCE_TARGET = (41, 43, 23)
DIVERGENCE_LOW_V = 0
DIVERGENCE_HIGH_V = 31
MAX_TICKS = 4096
CHECKPOINTS = {337, 512, 768, 1024, 1280, 1536, 1792, 2048, 2304, 2560, 2816, 3072, 3328, 3584, 3840, 4096}
OUTPUT_DIR = Path("output/findings")


def make_worlds() -> dict[str, tuple[Any, dict[str, Any]]]:
    base_cfg = load_config("config.yaml")
    low_cfg = probe_config(base_cfg, LOW_LABEL, LOW_COUPLING)
    high_cfg = probe_config(base_cfg, HIGH_LABEL, HIGH_COUPLING)
    return {
        "low_natural": (init_world(low_cfg), low_cfg),
        "high_natural": (init_world(high_cfg), high_cfg),
        "low_force_high_vector": (init_world(low_cfg), low_cfg),
        "high_force_low_vector": (init_world(high_cfg), high_cfg),
    }


def metric_row(label: str, coupling: float, tick: int, world: Any) -> dict[str, Any]:
    metric = collect_metrics(world, tick)
    return {
        "label": label,
        "coupling": coupling,
        "tick": tick,
        "active_iotas": metric["active_iotas"],
        "largest_coherence": metric["largest_coherence"],
        "coherence_ratio": metric["coherence_ratio"],
        "coherence_count": metric["coherence_count"],
        "component_size_1": metric["component_size_1"],
        "component_size_2": metric["component_size_2"],
        "component_size_3": metric["component_size_3"],
        "top5_component_coverage": metric["top5_component_coverage"],
        "top20_component_coverage": metric["top20_component_coverage"],
        "component_size_entropy": metric["component_size_entropy"],
        "divergence_target_V": int(world.V[DIVERGENCE_TARGET]),
        "divergence_target_active": bool(world.active[DIVERGENCE_TARGET]),
        "divergence_target_A": int(world.A[DIVERGENCE_TARGET]),
        "divergence_target_R": int(world.R[DIVERGENCE_TARGET]),
        "divergence_target_P": int(world.P[DIVERGENCE_TARGET]),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    worlds = make_worlds()
    rows: list[dict[str, Any]] = []

    for tick in range(1, MAX_TICKS + 1):
        for label, (world, cfg) in worlds.items():
            if tick <= DIVERGENCE_TICK:
                trace_step(world, cfg, tick)
            else:
                step(world, cfg)

        if tick == DIVERGENCE_TICK:
            worlds["low_force_high_vector"][0].V[DIVERGENCE_TARGET] = DIVERGENCE_HIGH_V
            worlds["high_force_low_vector"][0].V[DIVERGENCE_TARGET] = DIVERGENCE_LOW_V

        if tick in CHECKPOINTS:
            for label, (world, cfg) in worlds.items():
                rows.append(
                    metric_row(
                        label,
                        float(cfg["constants"]["cross_payload_coupling"]),
                        tick,
                        world,
                    )
                )
            print(
                "tick="
                f"{tick} "
                f"low={rows[-4]['active_iotas']}/{rows[-4]['coherence_ratio']:.3f} "
                f"high={rows[-3]['active_iotas']}/{rows[-3]['coherence_ratio']:.3f} "
                f"low_forced={rows[-2]['active_iotas']}/{rows[-2]['coherence_ratio']:.3f} "
                f"high_forced={rows[-1]['active_iotas']}/{rows[-1]['coherence_ratio']:.3f}"
            )

    csv_path = OUTPUT_DIR / "finding_018_payload_coupling_divergence_continuation.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    final_rows = [row for row in rows if int(row["tick"]) == MAX_TICKS]
    summary = {
        "divergence_tick": DIVERGENCE_TICK,
        "divergence_target": DIVERGENCE_TARGET,
        "natural_low_coupling": LOW_COUPLING,
        "natural_high_coupling": HIGH_COUPLING,
        "forced_vector_test": {
            "low_force_high_vector": f"set V{DIVERGENCE_TARGET}={DIVERGENCE_HIGH_V} after tick {DIVERGENCE_TICK}",
            "high_force_low_vector": f"set V{DIVERGENCE_TARGET}={DIVERGENCE_LOW_V} after tick {DIVERGENCE_TICK}",
        },
        "final_rows": final_rows,
    }
    json_path = OUTPUT_DIR / "finding_018_payload_coupling_divergence_continuation.json"
    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
