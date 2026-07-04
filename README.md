# Iota Rig

A minimal octal-first iota universe test rig.

Default iota state:

```text
Iota = (A, R, V, P)
A = amplitude, octal 0..7
R = range, octal 0..7
V = vector, 0..63, representable as octal 00..77
P = payload, octal 0..7
```

The grid defaults to `64 x 64 x 64` and can be raised toward `256 x 256 x 256` if memory and runtime allow.

The default baseline is stamped in `config.yaml` as:

```yaml
simulation_version: iota-rig-v0.1.1
experiment:
  objective: Single active iota baseline
```

For the default `64^3` grid with one active iota, the initial density is:

```text
1 / 262144 = 0.000381%
```

The config keeps `init.total_iotas` and `init.initial_density` as `auto`; the runner resolves and logs them for each experiment.

Vector state `V` remains a 64-state octal field. With the default `cube26` mode, those states are interpreted as:

```text
0-25   move
26-51  reflect
52-63  diffuse
```

## Install

```bash
cd /Users/douglasclark/iota
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python src/iota_rig.py --config config.yaml --objective "Baseline active_iotas=1"
```

If `--objective` is omitted, the runner uses `experiment.objective` from `config.yaml`.

The SQLite database lives at:

```text
data/iota_lab.db
```

Each run creates a numbered experiment:

```text
data/iota_lab.db
experiments/IOTA-000001.md
output/IOTA-000001/
output/experiments/
output/dashboard/index.html
```

You get:

- `metrics.csv`
- `active_over_time.png`
- `metrics_timeseries.png`
- `slice_*.png`
- `scatter_*.png`
- `dashboard/index.html`

`metrics.csv`, the database, and the dashboard include `coherence_ratio`, defined as:

```text
largest_coherence / active_iotas
```

This is the normalized aggregation signal to watch when active iotas grow faster than coherent structures.

## Dashboard

Open the generated dashboard directly:

```bash
open output/dashboard/index.html
```

Or serve the repo locally:

```bash
python3 -m http.server 8000
```

Then visit:

```text
http://localhost:8000/output/dashboard/
```

The dashboard is static HTML generated from `data/iota_lab.db`. It refreshes every 15 seconds and is regenerated at each snapshot interval during a run, so it can be used during a run or after it completes.

The SQLite database stores:

- `experiments`
- `parameters`
- `metrics`
- `observations`
- `parameter_diffs`
- `summary_metrics`
- `config_snapshots`
- `artifacts`

## Artifact retention

PNG files stay on disk; the database stores artifact metadata, paths, hashes, byte counts, and retention state. This keeps experiment queries fast while still making generated evidence auditable.

Default retention keeps the initial snapshot, final snapshot, every fourth intermediate snapshot, comparison plots, and CSV metrics:

```yaml
artifacts:
  keep_initial: true
  keep_final: true
  keep_every_n_snapshots: 4
  delete_unregistered: false
```

For large sweeps, lower `run.snapshot_every` only when you need dense visual evidence. Metrics are recorded every tick regardless of PNG retention.

## Modules

```text
src/iota_rig.py           # core simulation and universe snapshots
src/experiment_db.py      # SQLite schema, config hashes, parameter diffs
src/experiment_runner.py  # create experiment, run simulation, record outputs
src/metrics.py            # coherence, entropy, run plots, experiment plots
```

## Experiment safety

Every new run compares its flattened user-configured inputs against the previous experiment in `data/iota_lab.db`.

If one parameter changed, the run records:

```text
Changed parameter: init.active_iotas 64 -> 128
```

After the baseline, the runner refuses to start unless exactly one controlled parameter changed. This prevents duplicate runs and multi-parameter changes from entering the lab history as normal experiments.

The protocol is documented in `docs/experimental_protocol.md`.

Every experiment also records `simulation_version`, so results from changed simulation rules can be separated from controlled parameter sweeps.

Version changes are lineage boundaries: use a new baseline or an explicit equivalence gate before comparing across `simulation_version` values. Future branching experiments should use an explicit parent experiment rather than relying only on chronological order.

## First experiments

Try these initial active iota counts:

```yaml
active_iotas: 1
active_iotas: 2
active_iotas: 4
active_iotas: 8
active_iotas: 16
```

For the first density sweep, keep all other parameters fixed and change only `init.active_iotas`:

```text
IOTA-000001 active_iotas=1
IOTA-000002 active_iotas=2
IOTA-000003 active_iotas=4
IOTA-000004 active_iotas=8
IOTA-000005 active_iotas=16
```

For the next interaction sweep, vary only amplitude coupling and repeat each value across seeds:

```bash
python src/parameter_sweep.py constants.amplitude_coupling \
  0.05 0.10 0.15 0.20 0.25 0.50 \
  --seeds 42 43 44 \
  --objective "Amplitude coupling sweep"
```

The sweep runner starts from the latest recorded config snapshot in `data/iota_lab.db` and walks values/seeds in a serpentine order so each recorded experiment still changes exactly one controlled parameter. Use `--base file` when a rule or metadata change in `config.yaml` must be the sweep baseline instead.

Try these vector modes:

```yaml
mode: cube6
mode: cube26
mode: random64
```

Try these decay modes:

```yaml
decay_mode: none
decay_mode: inverse
decay_mode: inverse_square
decay_mode: exponential
```

## Valence

`constants.valence` controls the maximum number of simultaneous productive relationships an active iota can maintain after local candidate scoring. It is not direct copying: candidates are scored by the existing influence rule, then conservation, decay, payload transfer, and rounding still decide what persists.

```yaml
constants:
  valence: 1
  bond_probability: 0.0
```

The original v0.1.0 behavior is equivalent to `valence: 1`.

`constants.bond_probability` gates non-primary productive relationship slots after candidate scoring. The primary vector target remains deterministic; each additional valence slot independently admits the next highest-scored candidate, then the existing conservation, payload, vector-inheritance, and rounding rules apply unchanged. This is a ranked, directed, state-dependent edge-occupation rule, not ordinary independent bond percolation.

## First big question

Could the initial non-dark iota count be one?

Yes, as a testable hypothesis. A single active iota is the cleanest possible seed. The rig should ask whether one seed can create persistent, propagating, structured non-dark activity under simple exchange rules.

If one seed dies, freezes, or creates only trivial symmetry, increase to 8, then 64. If structure appears only after many active seeds, that tells us the model requires initial diversity rather than a single primordial informational asymmetry.
