# Compute estimate (outcome-free)

Date: `2026-10-29`. Machine: the owner's MacBook Air. Registered workers: 4.

This is a resource estimate, not an outcome. Nothing was timed near any
threshold:

- every timed run used ρ = 1 or p = 1 (fully fresh medium or certain
  transmission), where the outcome is trivial and activity is largest;
- every timed run used the disposable seed domain `TIMING-ONLY`, which cannot
  collide with a registered seed;
- each model ran at most 3 times, at its registered lattice size;
- only wall-clock time and active-unit counts were recorded, and all timing
  output was discarded.

The estimator costs were timed on synthetic power-law ledgers.

## Measured costs

Per-run cost is modelled as setup F + c0 × ticks + c1 × (work), where work is
the summed active units. Fits used runs at horizons 1, 8 and up to censoring.
For L0 they used a per-tick regression on frontier size, and for the 3-D models
c0 is set to a conservative 0.05 ms. The column "p = 1 run" is the measured cost
of one complete run up to censoring at ρ = 1 or p = 1.

| Model | p = 1 run | c0 per tick | c1 per unit | Setup |
|---|---|---|---|---|
| IOTA-MIN-L0 (64³) | 38 ms, 44 ticks | 0.06 ms | 0.41 µs per frontier site | 3 ms + C search ≤ 54 ms |
| DK bond / site (4096) | 152 ms, 2044 layers | 0.010 ms | 0.063 µs | 0.1 ms |
| Bond DP 3+1 (64³) | 40 ms, 28 layers | 0.05 ms | 0.17 µs | 0.2 ms |
| One-tick SIR (64³) | 4 ms, 28 generations | 0.05 ms | 0.13 µs | 0.2 ms |
| Site BFS (64³) | 7 ms, 28 generations | 0.05 ms | 0.17 µs | 1.4 ms |

Estimator, per point of 20,000 runs: the criticality test with 1000 bootstrap
resamples takes 1.9 s, and the static tail takes 1.4 s. Both are negligible.

## Per-run upper bounds

A run stops at censoring, so all activity stays within Chebyshev distance 28 of
the seed: at most 57³ = 185,193 sites in 3-D. In 1-D, at most 2045 sites of one
parity are within reach.

- **IOTA-MIN-L0: at most 1.0 s.** Each frontier site sends exactly once per tick,
  and each send lands on a site activated in that tick, which receives at most
  6. So work ≤ 6 × 185,193. Ticks ≤ 8192.
- **SIR: at most 0.23 s. BFS: at most 0.24 s.** Each site is active in exactly
  one generation, so work ≤ 185,193. Ticks ≤ 4096.
- **Domany–Kinzel: at most 1.14 s.** This assumes 2045 active sites in every one
  of 8192 layers, which no near-critical run approaches. At criticality, the
  literature exponents (δ = 0.1595, θ = 0.3137) give an expected cost of about
  30 ms per run.
- **Bond DP 3+1: no useful hard bound.** Activity is not self-limiting, and a
  saturated box for 4096 layers would cost about 127 s, which is unphysical.
  The literature exponents (δ = 0.736, θ = 0.11) give an expected cost of about
  17 ms per run at criticality. The p = 1 run, which fills its ball densely
  until censoring, costs 40 ms.

## Stage projections (4 workers)

The column "× 2" doubles each bound as a safety margin. The last column gives
the per-run cost that would trip the 12 h per-point ceiling at the largest
point.

| Stage / model | Runs | Bound | × 2 | Largest point (× 2) | Ceiling trips above |
|---|---|---|---|---|---|
| C: DK bond | 460,000 | 36.5 h | 73 h | 100,000 runs: 15.9 h | 1.73 s/run |
| C: DK site | 460,000 | 36.5 h | 73 h | 100,000 runs: 15.9 h | 1.73 s/run |
| C: bond DP 3+1 | 84,000 | 5.8 h at 1 s/run | — | 20,000 runs: 1.4 h at 1 s/run | 8.64 s/run |
| C: SIR | 84,000 | 1.3 h | 2.7 h | 20,000 runs: 0.64 h | 8.64 s/run |
| C: BFS | 76,000 | 1.3 h | 2.5 h | 20,000 runs: 0.66 h | 8.64 s/run |
| S: IOTA-MIN-L0 | 64,000 | 4.5 h | 8.9 h | 20,000 runs: 2.8 h | 8.64 s/run |
| K: IOTA-MIN-L0 | 60,000 | 4.2 h | 8.4 h | 20,000 runs: 2.8 h | 8.64 s/run |

Expected Stage C time lies between two estimates:

- every run costs the critical estimate: about 1 h per DK model;
- every run costs as much as the measured p = 1 run: about 4.9 h per DK model.

Each 3-D model takes well under 1 h on either estimate, so Stage C should take
roughly 2–10 h in all. That excludes the Python process start-up for each point
(seconds).

### Risk

The only bound that crosses a ceiling is the DK final point under the 2× margin.
That bound assumes every one of 100,000 runs keeps about 2045 active sites for
8192 layers. At criticality the mean activity is of order 10 sites, so the
expected final point takes about 12 minutes.

The realistic risk is the host, not the workload. Results are written once, at
the end of a stage, and there is no checkpointing. If the machine sleeps or
throttles long enough, a point becomes `resource_censored`, which fails the
calibration gate and ends this version. Run every stage plugged in, with the
lid open (unless clamshell mode is set up), under `caffeinate -dimsu`.
