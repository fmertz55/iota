# Reviewer Guide

This repository is a live research compendium. The README states the organizing hypothesis and the strongest claim supported at the current commit. Machine-readable registries connect that claim to definitions, evidence, analysis code, and manuscript values.

## Read only

1. Start with the [organizing hypothesis](../README.md#iota-rig) and the
   [minimal informational realization contract](ICP_MINIMAL_INFORMATIONAL_REALIZATION_CONTRACT.md).
2. Inspect the preregistered minimal-realization
   [development result](../output/minimal_realization/MIR-REFERENCE-SEARCH-001/development_results.json)
   and its
   [post-result literature record](literature/minimal_realization_result_followup_2026-07-13.md).
3. Read the [current evidence frontier](../README.md#current-evidence-frontier),
   from foundational GC-001 through bounded causal GC-010.
4. Inspect the [Finding 070 independent synthesis](../output/findings/finding070/independent_persistence_replication_summary.json)
   and [branch assignments](../output/findings/finding070/independent_persistence_replication_assignments.csv).
5. Audit the [selector-hash chain](../output/findings/finding070/independent_persistence_replication_selector_hashes.csv)
   against the staged artifacts in `output/findings/finding070/`.
6. Read the [working paper](../paper/main.tex).

No execution is required for this path.

## Quick verification

From the repository root:

```bash
make verify
```

This regenerates the evidence-facing files and validates that:

- every claim and definition ID is unique;
- every referenced local artifact exists;
- registered claim counts match their source data;
- strict events and sequential selector chains satisfy their registered causal
  and provenance criteria;
- generated paper values and tables are current;
- evidence manifests contain current SHA-256 hashes; and
- registered minimal-realization candidates satisfy the machine-checkable
  primitive, atomic-law, and clock grammar.

The verification does not rerun the underlying simulations or interventions.

To independently recompute the complete `MIR-REFERENCE-SEARCH-001`
development ledger and verify its canonical bytes, run:

```bash
python3 -m src.minimal_realization.cli verify-development-results \
  --open-seal experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/development_open_manifest.json
```

That verifier checks all 15 dynamic candidates over offsets `0..47`; it also
checks that reserved offsets `48..63` were not accessed.

## Build the paper

```bash
make paper
```

The PDF is written to `build/paper/main.pdf`. A TeX distribution providing `latexmk` and `pdflatex` is required.

## Extend the experiment

Use the installation and run instructions in the main README. New findings should retain raw evidence, register bounded claims in `evidence/claims.yaml`, update canonical terms in `evidence/definitions.yaml`, and regenerate the compendium. Failed and superseded claims should remain in history with an explicit status rather than being silently removed.

## Evidence identity

Each file in [`evidence/manifests/`](../evidence/manifests/) records the byte
count and SHA-256 digest of the artifacts supporting one registered claim. Git
identifies the code, freeze chronology, and narrative state; the manifests
identify the exact evidence content consumed by the paper build.

Finding 069 additionally exposes its staged provenance directly through the
[selector hashes](../output/findings/finding069/sequential_realization_cut_selector_hashes.csv),
[per-depth aggregates](../output/findings/finding069/sequential_realization_cut_depths.csv),
and [analysis implementation](../src/sequential_realization_cut.py). Its depth
is prefix-minimal only for the frozen retained-amplitude event-order policy; it
is not a graph-theoretic minimum over arbitrary interventions.

The chain is independently replicated in Finding 070; see its
[selector hashes](../output/findings/finding070/independent_persistence_replication_selector_hashes.csv),
[depth aggregates](../output/findings/finding070/independent_persistence_replication_depths.csv),
and [synthesis implementation](../src/summarize_independent_persistence.py).
