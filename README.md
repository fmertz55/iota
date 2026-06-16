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

Each run creates a numbered experiment:

```text
data/iota_lab.db
experiments/IOTA-000001.md
output/IOTA-000001/
```

You get:

- `metrics.csv`
- `active_over_time.png`
- `metrics_timeseries.png`
- `slice_*.png`
- `scatter_*.png`

The SQLite database stores:

- `experiments`
- `parameters`
- `metrics`
- `observations`
- `parameter_diffs`
- `summary_metrics`

## Experiment safety

Every new run compares its flattened config against the previous experiment in `data/iota_lab.db`.

If one parameter changed, the run records:

```text
Changed parameter: init.active_iotas 64 -> 128
```

If more than one parameter changed, the run refuses to start. Use `--force` only when you intentionally want to contaminate the one-parameter rule:

```bash
python src/iota_rig.py --config config.yaml --force --objective "Intentional multi-parameter run"
```

## First experiments

Try these initial active iota counts:

```yaml
active_iotas: 1
active_iotas: 2
active_iotas: 4
active_iotas: 8
active_iotas: 16
active_iotas: 32
active_iotas: 64
active_iotas: 128
active_iotas: 256
active_iotas: 512
```

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

## First big question

Could the initial non-dark iota count be one?

Yes, as a testable hypothesis. A single active iota is the cleanest possible seed. The rig should ask whether one seed can create persistent, propagating, structured non-dark activity under simple exchange rules.

If one seed dies, freezes, or creates only trivial symmetry, increase to 8, then 64. If structure appears only after many active seeds, that tells us the model requires initial diversity rather than a single primordial informational asymmetry.
