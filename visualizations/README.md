# IOTA Manim visualizations

This directory contains the Manim explainer production for IOTA / ICP.

The canonical scene and narration specification is [`narration/script.md`](narration/script.md). It defines twelve independently renderable scenes, the reusable component set, normalized real-run data contract, and development order.

The shared semantic system is defined in [`VISUAL_GRAMMAR.md`](VISUAL_GRAMMAR.md), with reusable palette, typography, geometry, state, and timing constants in [`config/theme.py`](config/theme.py).

## Structure

- `scenes/` — one module per scene
- `components/` — reusable visual objects
- `config/` — shared theme and video settings
- `data/` — selected-run manifest and normalized frames
- `narration/` — canonical production script
- `renders/` — generated output

## First milestone

Build a rough animatic for scenes 1–6 with placeholder typography and simple dots. Apply the visual grammar consistently before introducing real-run data or visual polish.
