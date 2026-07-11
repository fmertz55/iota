# Reviewer Guide

This repository is a live research compendium. The README states the organizing hypothesis and the strongest claim supported at the current commit. Machine-readable registries connect that claim to definitions, evidence, analysis code, and manuscript values.

## Read only

1. Start with the [organizing hypothesis](../README.md#iota-rig).
2. Inspect [GC-001](../README.md#current-evidence-frontier).
3. Read the [working paper](../paper/main.tex).
4. Follow its evidence links to the Finding 060 source artifacts.

No execution is required for this path.

## Quick verification

From the repository root:

```bash
make verify
```

This regenerates the evidence-facing files and validates that:

- every claim and definition ID is unique;
- every referenced local artifact exists;
- the registered GC-001 counts match the source data;
- every strict event satisfies the registered causal criteria;
- generated paper values and tables are current;
- the evidence manifest contains current SHA-256 hashes.

The verification does not rerun the underlying simulations.

## Build the paper

```bash
make paper
```

The PDF is written to `build/paper/main.pdf`. A TeX distribution providing `latexmk` and `pdflatex` is required.

## Extend the experiment

Use the installation and run instructions in the main README. New findings should retain raw evidence, register bounded claims in `evidence/claims.yaml`, update canonical terms in `evidence/definitions.yaml`, and regenerate the compendium. Failed and superseded claims should remain in history with an explicit status rather than being silently removed.

## Evidence identity

`evidence/manifests/GC-001.json` records the byte count and SHA-256 digest of every artifact used for GC-001. Git identifies the code and narrative state; the manifest identifies the exact evidence content consumed by the paper build.
