# Iota Rig

[![Research compendium](https://github.com/fmertz55/iota/actions/workflows/research-compendium.yml/badge.svg)](https://github.com/fmertz55/iota/actions/workflows/research-compendium.yml)

> **Organizing hypothesis**
>
> **Information is the change in the reachable caused by interaction.**

Iota Rig is an open, automation-first experimental program for making that
hypothesis precise, measurable, and falsifiable. The repository is both the lab
and the live record of the investigation: definitions, laws, experiments,
negative results, evidence, and interpretations are intended to evolve together
without erasing their history.

The hypothesis is not presented as an established law of physics. It is the root
question from which the experiments are derived:

> Can finite local interactions produce constraints on reachable futures that
> persist even when the local state that realizes them is replaced?

## From hypothesis to experiment

At permanent lattice address $x$, write an iota provisionally as

$$
I_x(t) = \left(x, A_x(t), E_x(t)\right),
$$

where $A_x(t)$ is its attribute state, $E_x(t)$ is its expression state, and
$N_{26}(x,t)$ is its 26-neighbor local field. A fixed local law $\mathcal{L}$
defines the generative kernel

$$
\left(A_x(t+1),E_x(t+1)\right)
=
\mathcal{L}\left(A_x(t),E_x(t),N_{26}(x,t)\right).
$$

For a state $s_t$, define the locally reachable next-state set

$$
\mathcal{R}_x(t+1\mid s_t)
=
\left\{(A',E') : (A',E')\text{ is admissible under }\mathcal{L}\right\}.
$$

When an interaction strictly reduces that set, its information contribution can
be measured as

$$
\Delta I_x
=
\log\frac{|\mathcal{R}_x^{\mathrm{prior}}(t+1)|}
{|\mathcal{R}_x^{\mathrm{posterior}}(t+1)|}.
$$

This cardinality expression covers reduction of the reachable. Measuring a
reshaping that preserves cardinality remains an open formal problem and will
require an additional set- or distribution-sensitive measure.

The transition equation is currently a proposed model kernel, not a claimed
fundamental equation of nature. The experiments below test observable
consequences that would be expected if the organizing hypothesis is useful.

## Current evidence frontier

The strongest current result is **Golden Claim GC-001: constraint transport**.

> In three controlled replay events across two seeds, payload-free Iota dynamics
> restored the same tracked connectivity relation through a causally necessary
> successor bridge having no cells in common with the predecessor bridge.

Finding 060 replayed all 36 previously identified Class B bridge-relocation
events. Twelve had a genuinely role-bearing predecessor bridge, and three passed
the strict transport test. In every strict positive:

- the tracked regions were connected before bridge loss;
- they were disconnected during the split;
- a disjoint successor bridge restored their reachability;
- removing that successor destroyed the restored reachability;
- pre- and post-event shortest-path length was $2$;
- payload was zero and the conservation ledger was exact.

This supports a bounded conclusion: in this event class, a relational
connectivity constraint can survive complete replacement of its local
realization. It does **not** yet establish general multi-region invariance,
indefinite persistence, uniqueness to one law, or a correspondence with physical
particles or the early universe.

### Inspect GC-001

- [Event-level evidence](output/findings/finding060/phase_free_constraint_transport_events.csv)
- [Aggregate evidence](output/findings/finding060/phase_free_constraint_transport_aggregate.csv)
- [Machine-readable summary](output/findings/finding060/phase_free_constraint_transport_summary.json)
- [Analysis implementation](src/phase_free_constraint_transport.py)
- [Experimental interpretation and next gate](SESSION_HANDOFF.md#finding-060-update)

The next gate follows the descendant regions after the three strict positives,
measures the lifetime of the restored relation, and tests for a second complete
bridge replacement. As new experiments land, this section should report the
strongest supported claim at that commit while Git history preserves earlier
states of the evidence.

## Reviewer paths

Choose the depth appropriate to your review:

- **Read only:** follow the claim and artifact links above, then read the
  [working paper](paper/main.tex).
- **Quick verify:** run `make verify` to regenerate the evidence-facing files
  and validate their claims against the source artifacts.
- **Build the paper:** run `make paper`; the PDF is written to
  `build/paper/main.pdf`.
- **Run new experiments:** follow the installation and operation instructions
  below.

The [reviewer guide](docs/reviewer_guide.md) explains what each path checks. The
canonical registries are [claims](evidence/claims.yaml) and
[definitions](evidence/definitions.yaml). Generated files are marked as such and
must not be edited by hand.

## Rig overview

The implementation began as a minimal octal-first iota universe test rig.

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
src/continuation.py       # shared continuation cloning and outcome classification
src/openness_timeline.py  # resampled-future openness timeline measurement
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

## Openness Timeline

The committor machinery from Finding 020 is now generalized into an openness instrument. At a saved state `s_t`, the runner launches independent future random continuations and estimates:

```text
O(t) = H(Pr(outcome class | s_t)) / log(3)
```

The three outcome classes are `absorber`, `high_dominant`, and `protected`, classified under an explicit component graph such as `cube26`. Low `O(t)` means the checkpoint has a nearly closed future under the sampled horizon; high `O(t)` means the future remains non-degenerate.

Development-scale run:

```bash
python src/openness_timeline.py \
  --config config.yaml \
  --seed 42 \
  --ticks 1024 \
  --checkpoint-every 256 \
  --horizon 512 \
  --samples 8 \
  --connectivity cube26
```

Paper-grade runs should increase `--samples`, `--horizon`, and lattice size only after the 64^3 protocol is stable. Outputs are written under `output/findings/`:

```text
finding_022_openness_timeline_raw.csv
finding_022_openness_timeline_summary.csv
finding_022_openness_timeline_summary.json
finding_022_openness_timeline_states/
```

Run seed `42` and seed `56` first. The runner is O(t)-first by default. Add `--with-persistence` only after the openness timeline itself is behaving; that second pass records a top-k component persistence proxy and `complexity_score = component_persistence * openness`. This is a measurement instrument, not a new law; it works against the current `iota-rig-v0.1.1` dynamics.

## Versioned v0.2 Direction

The current rig is an irreversible growth substrate. It can show grammar, nucleation, and path-dependent basin selection, but it cannot yet make mass/energy language falsifiable because it has no hard conserved ledger and no deactivation.

The proposed next law family is documented in:

```text
docs/IOTA_RIG_V0_2_LAW_SPEC.md
```

Hard conservation and exhaustion deactivation are implemented as an opt-in v0.2 law path. Do not silently add deactivation or hard conservation to existing v0.1 runs. They are version boundaries and should use a new `simulation_version`, a fresh baseline, and golden checks against the Finding 018 replay suite.

## First big question

Could the initial non-dark iota count be one?

Yes, as a testable hypothesis. A single active iota is the cleanest possible seed. The rig should ask whether one seed can create persistent, propagating, structured non-dark activity under simple exchange rules.

If one seed dies, freezes, or creates only trivial symmetry, increase to 8, then 64. If structure appears only after many active seeds, that tells us the model requires initial diversity rather than a single primordial informational asymmetry.
