"""Shared visual grammar for the IOTA / ICP Manim explainer.

Keep semantic color assignments in this module. Scenes and playback components
should import these names instead of embedding color literals.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    background: str = "#070A0F"
    foreground: str = "#F2F4F7"
    muted: str = "#8B95A5"
    inactive: str = "#26303D"
    iota: str = "#D7DEE8"
    active: str = "#56B4E9"
    interaction: str = "#F0E442"
    coherence: str = "#009E73"
    original_bridge: str = "#E69F00"
    lost_bridge: str = "#AAB2BF"
    replacement_bridge: str = "#CC79A7"
    warning: str = "#D55E00"


@dataclass(frozen=True)
class Typography:
    # Manim/Pango will use the first installed family supplied by a component.
    heading_font: str = "Avenir Next"
    body_font: str = "Avenir Next"
    metric_font: str = "Menlo"
    title_size: int = 54
    heading_size: int = 38
    body_size: int = 28
    annotation_size: int = 22
    metric_size: int = 20


@dataclass(frozen=True)
class Geometry:
    iota_radius: float = 0.055
    active_iota_radius: float = 0.075
    field_stroke_width: float = 1.2
    relation_stroke_width: float = 2.0
    bridge_stroke_width: float = 3.0
    component_boundary_width: float = 1.5
    cell_gap_ratio: float = 0.12


@dataclass(frozen=True)
class Timing:
    quick: float = 0.25
    standard: float = 0.60
    deliberate: float = 1.00
    title_hold: float = 1.25
    evidence_freeze: float = 1.50
    pulse_duration: float = 0.35


PALETTE = Palette()
TYPE = Typography()
GEOMETRY = Geometry()
TIMING = Timing()

# Non-color cues are mandatory for role-bearing bridge states.
STATE_STYLES = {
    "inactive": {"color": PALETTE.inactive, "opacity": 0.32, "mark": "none"},
    "iota": {"color": PALETTE.iota, "opacity": 0.82, "mark": "dot"},
    "active": {"color": PALETTE.active, "opacity": 1.0, "mark": "filled"},
    "coherence": {"color": PALETTE.coherence, "opacity": 1.0, "mark": "linked"},
    "original_bridge": {
        "color": PALETTE.original_bridge,
        "opacity": 1.0,
        "mark": "single_ring",
    },
    "lost_bridge": {
        "color": PALETTE.lost_bridge,
        "opacity": 0.45,
        "mark": "dashed_cross",
    },
    "replacement_bridge": {
        "color": PALETTE.replacement_bridge,
        "opacity": 1.0,
        "mark": "double_ring",
    },
}
