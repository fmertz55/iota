# Findings

## Finding 001: Valence-2 Coherent Percolation

Under soft conservation, one active iota with `range_range=[7,7]`, `amplitude_coupling=1.0`, and `range_coupling=1.0` transitions from trace-limited propagation to single-component coherent growth when `constants.valence` increases from `1` to `2`.

This finding does not claim stable chemistry-like structure. It establishes a phase change from capped traces to connected percolation.

### Conditions

- `init.active_iotas`: 1
- `init.range_range`: `[7,7]`
- `constants.amplitude_coupling`: 1.0
- `constants.range_coupling`: 1.0
- `constants.conservation`: `soft`
- `run.stop_active_iotas`: 30000

### Evidence

| Experiment | Valence | Requested Ticks | Final Tick | Final Active | Largest Coherence | Coherence Count |
|---:|---:|---:|---:|---:|---:|---:|
| 67 | 1 | 8 | 8 | 5 | 3 | 3 |
| 68 | 1 | 16 | 16 | 8 | 3 | 6 |
| 69 | 1 | 32 | 32 | 10 | 3 | 8 |
| 70 | 1 | 64 | 64 | 10 | 3 | 8 |
| 71 | 1 | 128 | 128 | 12 | 3 | 10 |
| 72 | 1 | 256 | 256 | 13 | 3 | 11 |
| 60 | 2 | 8 | 8 | 36 | 36 | 1 |
| 61 | 2 | 16 | 16 | 160 | 160 | 1 |
| 62 | 2 | 32 | 32 | 621 | 621 | 1 |
| 63 | 2 | 64 | 64 | 3695 | 3695 | 1 |
| 64 | 2 | 128 | 128 | 19766 | 19766 | 1 |
| 65 | 2 | 256 | 160 | 30232 | 30232 | 1 |

### Artifacts

- `output/findings/finding_001_valence_percolation.png`
- `output/findings/finding_001_valence_percolation.csv`

### Interpretation

`valence=1` remains trace-limited: active count grows slightly and largest coherence stays capped at 3.

`valence=2` enters coherent percolation: every recorded active iota belongs to one connected component, and active count rises rapidly until the early-stop threshold is reached.

### Next Question

Determine whether valence-2 percolation is merely connected expansion or whether it contains stable morphology. Candidate metrics:

- surface-area-to-volume proxy
- bounding box dimensions
- cycle or loop count
- payload/vector diversity inside the giant component
- growth-rate fit across early ticks
