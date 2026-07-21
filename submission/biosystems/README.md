# IOTA BioSystems submission package

This directory contains the journal-facing support files for the full-length
article, “Constraint Transport and History-Dependent Successor Accessibility
in IOTA: An Information-First Finite Local Physics Model.”

The manuscript is an artificial-life application of IOTA's information-first
finite local physics research model; it does not classify IOTA itself as a
living system or validated physical substrate.

Build and validate the complete package from the repository root:

```console
make paper
python3 scripts/validate_iota_submission.py --artifacts
```

`make paper` regenerates and validates the registered evidence, validates the
submission sources, builds the manuscript with `latexmk`, and creates:

- `output/pdf/iota_constraint_transport_biosystems.pdf`
- `output/pdf/iota_constraint_transport_biosystems.pdf.sha256`
- `output/pdf/iota_constraint_transport_biosystems.build.json`
- `output/submission/iota_constraint_transport_biosystems_sources.zip`
- `output/submission/iota_constraint_transport_biosystems_sources.zip.sha256`

The source archive is deterministic when `SOURCE_DATE_EPOCH` is fixed. CI pins
the release epoch to `1784649139`; without an explicit value, the local build
uses the current Git commit timestamp. The ZIP is a curated package containing
only the manuscript TeX and bibliography, generated TeX evidence tables/macros,
and these BioSystems support files. It does not include repository history,
experimental bulk data, build products, or the separate Quantum–Dirac
manuscript.

The BioSystems manuscript is intentionally figure-free. The validator rejects
any uncommented `\includegraphics` command in its main file, sections, or
generated TeX dependencies. It also enforces the 250-word abstract maximum,
the one-to-seven keyword range, and the three-to-five highlights requirement
with no more than 85 characters per highlight.

Before journal upload, complete every human-confirmation item in
`checklist.md`, update repository/release links to an immutable DOI-backed
archive if available, and compare the uploaded proof against the stable PDF.
