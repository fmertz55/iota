# Iota Lab Experimental Protocol

## Core Rule

After the baseline experiment, exactly one controlled parameter changes per experiment.

## Controlled Parameters

A controlled parameter is any flattened configuration value recorded in the experiment snapshot, except operational metadata ignored by the lab runner:

- `experiment.id`
- `experiment.objective`
- `lab.database`
- `lab.experiments_dir`
- `run.output_dir`
- `simulation_version`

## Baseline

The first experiment in a new database establishes the baseline. It has no previous run to compare against, so it records no parameter diff.

## Rejection Conditions

The runner refuses to start an experiment after the baseline when:

- zero controlled parameters changed
- more than one controlled parameter changed

This keeps each run interpretable as a single intervention against the previous experiment.

## Versioning

Every experiment records `simulation_version`. Experiments from different simulation versions should be compared only when the rule changes between versions are understood and explicitly accepted.

## Artifact Retention

The database stores artifact metadata, not PNG bytes. Snapshot PNGs are retained according to the active `artifacts` configuration, while metrics remain in SQLite for every tick.

Default retention keeps the initial snapshot, final snapshot, every fourth intermediate snapshot, run plots, comparison plots, and CSV metrics.
