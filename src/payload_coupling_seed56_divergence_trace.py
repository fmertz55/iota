from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from iota_rig import init_world, load_config
from metrics import collect_metrics
from payload_coupling_bracket_4096_sweep import probe_config
from payload_coupling_divergence_trace import (
    HIGH_COUPLING,
    HIGH_LABEL,
    LOW_COUPLING,
    LOW_LABEL,
    MAX_TICKS,
    compact_event,
    semantic_signature,
    trace_step,
    write_event_pair,
)


SEED = 56
OUTPUT_DIR = Path("output/findings")


def seed_config(base_cfg: dict[str, Any], label: str, coupling: float) -> dict[str, Any]:
    cfg = probe_config(base_cfg, label, coupling)
    cfg["experiment"]["objective"] = "Seed-56 payload coupling divergence trace"
    cfg["experiment"]["variant"] = (
        "A_4774_256_cube26_2_nuclei_medium_payload_4_vs_0"
        f"_cross_{label}_seed_{SEED}_divergence_trace"
    )
    cfg["experiment"]["seed_ensemble"] = "42_71"
    cfg["init"]["seed"] = SEED
    return cfg


def metric_snapshot(tick: int, low_world: Any, high_world: Any) -> dict[str, Any]:
    low_metrics = collect_metrics(low_world, tick)
    high_metrics = collect_metrics(high_world, tick)
    return {
        "tick": tick,
        "low_active_iotas": low_metrics["active_iotas"],
        "low_largest_coherence": low_metrics["largest_coherence"],
        "low_coherence_ratio": low_metrics["coherence_ratio"],
        "low_coherence_count": low_metrics["coherence_count"],
        "high_active_iotas": high_metrics["active_iotas"],
        "high_largest_coherence": high_metrics["largest_coherence"],
        "high_coherence_ratio": high_metrics["coherence_ratio"],
        "high_coherence_count": high_metrics["coherence_count"],
    }


def state_signature(event: dict[str, Any]) -> tuple[Any, ...]:
    return (
        event["actor"],
        event["target"],
        event["subtype"],
        event["target_pre_active"],
        event["payload_multiplier_class"],
        event["inter_component_bridge"],
        event["creates_new_active"],
        event["next_A_round"],
        event["next_R_round"],
        event["next_P"],
        event["next_V"],
    )


def main() -> None:
    base_cfg = load_config("config.yaml")
    low_cfg = seed_config(base_cfg, LOW_LABEL, LOW_COUPLING)
    high_cfg = seed_config(base_cfg, HIGH_LABEL, HIGH_COUPLING)
    low_world = init_world(low_cfg)
    high_world = init_world(high_cfg)
    first_numeric_cross_event: dict[str, Any] | None = None
    first_gate_divergence: dict[str, Any] | None = None
    first_state_divergence: dict[str, Any] | None = None
    metric_checkpoints: list[dict[str, Any]] = []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for tick in range(1, MAX_TICKS + 1):
        low_events = trace_step(low_world, low_cfg, tick)
        high_events = trace_step(high_world, high_cfg, tick)
        for event_index in range(max(len(low_events), len(high_events))):
            low_event = low_events[event_index] if event_index < len(low_events) else None
            high_event = high_events[event_index] if event_index < len(high_events) else None
            if (
                first_numeric_cross_event is None
                and low_event is not None
                and high_event is not None
                and low_event["payload_multiplier_class"] == "cross_payload"
                and high_event["payload_multiplier_class"] == "cross_payload"
                and abs(float(low_event["influence"]) - float(high_event["influence"])) > 0.0
            ):
                first_numeric_cross_event = {
                    "tick": tick,
                    "event_index": event_index,
                    "low": compact_event(low_event),
                    "high": compact_event(high_event),
                }
            if (
                first_gate_divergence is None
                and low_event is not None
                and high_event is not None
                and semantic_signature(low_event) != semantic_signature(high_event)
            ):
                first_gate_divergence = {
                    "tick": tick,
                    "event_index": event_index,
                    "low": compact_event(low_event),
                    "high": compact_event(high_event),
                    "low_signature": semantic_signature(low_event) if low_event is not None else None,
                    "high_signature": semantic_signature(high_event) if high_event is not None else None,
                }
            if low_event is None or high_event is None or state_signature(low_event) != state_signature(high_event):
                first_state_divergence = {
                    "tick": tick,
                    "event_index": event_index,
                    "low": compact_event(low_event),
                    "high": compact_event(high_event),
                    "low_signature": state_signature(low_event) if low_event is not None else None,
                    "high_signature": state_signature(high_event) if high_event is not None else None,
                }
                write_event_pair(
                    OUTPUT_DIR / "finding_019_seed56_payload_coupling_first_state_divergence.csv",
                    low_event,
                    high_event,
                )
                break
        if first_state_divergence is not None:
            metric_checkpoints.append(metric_snapshot(tick, low_world, high_world))
            break
        if tick % 256 == 0:
            metric_checkpoints.append(metric_snapshot(tick, low_world, high_world))
            print(
                f"tick={tick} active_low={int(low_world.active.sum())} "
                f"active_high={int(high_world.active.sum())}"
            )

    result = {
        "seed": SEED,
        "low_coupling": LOW_COUPLING,
        "high_coupling": HIGH_COUPLING,
        "first_numeric_cross_event": first_numeric_cross_event,
        "first_gate_divergence": first_gate_divergence,
        "first_state_divergence": first_state_divergence,
        "final_tick_checked": tick,
        "low_active_at_stop": int(low_world.active.sum()),
        "high_active_at_stop": int(high_world.active.sum()),
        "metric_checkpoints": metric_checkpoints,
    }
    (OUTPUT_DIR / "finding_019_seed56_payload_coupling_divergence_trace.json").write_text(
        json.dumps(result, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
