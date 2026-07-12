# IOTA / ICP visual grammar

This grammar is the shared visual language for conceptual explanations and recorded-run playback. It is intentionally restrained: iotas are not particles, coherence is not merely proximity, and recorded evidence must remain visibly distinct from illustration.

## Core principles

1. **Relations carry the meaning.** A point alone is an iota; lines, branches, boundaries, and their changes communicate interaction and constraint.
2. **State is redundant.** Important states use color plus a second cue such as a ring, cross, line pattern, label, or motion. The video must remain legible in grayscale and for common color-vision differences.
3. **Motion has semantics.** Pulses mean interaction, disappearing branches mean reduced reachable futures, persistent links mean mutual dependence, and ghost marks mean historical location.
4. **Illustration and evidence never blur together.** Concept scenes use smooth idealized motion. Recorded-run scenes use stepped ticks, a frame, metadata, and persistent metrics.
5. **No particle imagery.** Avoid orbitals, lens flares, volumetric glow, trails suggesting travel, or atom-like arrangements.

## Canvas and typography

- Background: near-black blue, `#070A0F`.
- Primary text: soft white, `#F2F4F7`; secondary text: slate, `#8B95A5`.
- Headings are uppercase with generous spacing. Explanatory copy uses sentence case.
- Use Avenir Next for narrative text and Menlo for ticks, coordinates, filenames, and metrics. If unavailable, use a neutral sans-serif and monospace fallback without changing layout.
- Keep title-safe margins of 0.6 Manim units. Metrics occupy a fixed overlay region and never cover the run geometry.
- Text transitions should replace ideas in place when the argument changes; avoid stacking more than three claims at once.

## Visual vocabulary

| Meaning | Form | Color | Motion / behavior |
| --- | --- | --- | --- |
| Iota | Small solid dot; no halo by default | Soft white | Still until participating in an interaction |
| Interaction capability | One thin, faint circular field | Soft white at low opacity | Draw once; never pulse continuously |
| Active cell | Filled lattice cell or slightly larger dot | Blue `#56B4E9` | Appears on a recorded tick, without bloom |
| Inactive cell | Empty or very dim cell | Slate `#26303D` | Static; omit when density harms clarity |
| Possible future | Thin dashed branch | Muted slate | Draw outward; removed branches fade toward their tips |
| Interaction | Short expanding ring shared by participants | Yellow `#F0E442` | One expansion and fade, 0.35 seconds |
| Dependency | Solid line between interacting parts | Green `#009E73` | Persists only while mutual support is represented |
| Coherence | Connected dependency graph plus a soft boundary | Green `#009E73` | Boundary settles after links stabilize |
| Original bridge | Active cell with a single outer ring | Orange `#E69F00` | Brief indication before loss |
| Lost bridge | Empty location with dashed outline and cross | Gray `#AAB2BF` | No pulsing after the loss beat |
| Replacement bridge | Active cell with a double outer ring | Magenta `#CC79A7` | Draw rings only after reachability is restored |
| Warning / falsification boundary | Underline, rule, or small marker | Vermilion `#D55E00` | Reserved for caveats, never ordinary activity |

The palette is based on high-separation, color-vision-friendly hues. Bridge states must always retain their ring/cross distinctions when color is absent.

## Concept grammar

### Iota

Render an iota as the smallest meaningful mark in the film. A field circle indicates capability, not a force field or spatial extent. A sparse group should remain irregular until a lattice is explicitly introduced.

### Interaction and information

Before interaction, each participant owns several faint dashed future branches. At interaction, use one shared pulse, then remove disallowed branches. The surviving branches do not brighten: information is the changed reachable set, not a newly emitted object.

### Coherence

Proximity alone never denotes coherence. At least two visible dependency links must join the structure. A soft boundary may appear only after those links become mutually supporting. When coherence ends, links disappear before or with the boundary.

### Persistence

Preserve a relational motif while replacing some constituent cells. Use replacement transforms for participants and keep one geometric relation stable. The viewer should be able to point to what survived without relying on a label.

### Constraint transport

The original and replacement bridges are disjoint visual sets. Show the original bridge with single rings, its loss with dashed crosses at the old locations, and the replacement with double rings. Never morph the old cells directly into the new ones; that implies carrier persistence. The semantic sequence is:

`connected → original bridge lost → split → different bridge restores reachability`

## Recorded-run grammar

Every evidence scene includes a thin viewport frame, a `RECORDED RUN` tag, current tick, and source metadata. Playback advances in discrete steps. Interpolation may move the camera, but it must not invent intermediate cell states.

Overlay order is fixed:

1. Tick and phase at upper left.
2. Active count and component count at upper right.
3. Bridge status at lower left.
4. Source artifact identifier at lower right.

Phase labels are `PRE-SPLIT`, `BRIDGE LOSS`, `SPLIT`, `REBRIDGING`, and `TRANSPORT COMPLETE`. A phase changes only on a manifest-defined tick. Metrics are monospaced and update with the frame.

Component boundaries are thin neutral contours. They must not reuse coherence green, because a measured connected component and the explanatory concept of coherence are related but not identical claims.

## Motion and timing

- Ordinary entrance or replacement: 0.60 seconds.
- Quick metric/tick update: 0.25 seconds.
- Conceptual emphasis: 1.00 second.
- Interaction pulse: 0.35 seconds, exactly once per represented event.
- Evidence freeze at split and rebridge: at least 1.50 seconds before narration resumes.
- Use linear timing for tick playback and eased timing for conceptual diagrams.
- Camera motion is slow and sparse. Do not zoom during the critical split/rebridge ticks.

## Scene continuity

- Scenes 1–5 share dot scale and conceptual-space styling.
- Scene 6 introduces the lattice and bridge marks used by recorded playback.
- Scene 7 changes mode visibly: smooth conceptual geometry resolves into a framed, stepped data viewport.
- Scenes 8–9 preserve cell scale, camera orientation, colors, and overlay positions so replay reads as the same event.
- Scene 10 removes the viewport before interpretation, preventing claims text from looking like measured output.
- Scene 12 returns to the opening field, now with one visibly persistent relational structure.

## Claim boundaries

Use labels consistent with the repository's operational definitions:

- An iota in the rig is a stationary lattice address with local state, not a moving particle.
- Information is represented as interaction-induced change in the reachable set.
- Coherence in measured output means connected active structure under declared connectivity; the explanatory dependency graph is a visual interpretation.
- A bridge is a set of active cells whose removal changes reachability between tracked regions.
- Strict constraint transport requires restored reachability through a causally necessary successor bridge disjoint from the predecessor bridge.

Never use wave-function, matter, energy, or consciousness imagery as if the current run established those phenomena. The Quantum House remains a destination marker, not an achieved state.

## Implementation rule

All scenes and reusable components import semantic values from `config/theme.py`. No scene may hard-code a semantic color, bridge marker, base font size, or standard duration. Temporary layout-specific measurements are allowed locally.
