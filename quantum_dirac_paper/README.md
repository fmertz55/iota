# Quantum-Dirac manuscripts

This directory contains dedicated technical and plain-language manuscripts for the qualified two-registration
quantum-Dirac result. The free one-excitation blocks of the registered updates
are exact-time-frame-related after post-result mass-angle remapping; neither
paper claims two inequivalent architecture classes. They are separate from the
constraint-lineage paper in `paper/`.

Build from the repository root:

```bash
python -m pip install --requirement quantum_dirac_paper/requirements.txt
make quantum-dirac-paper
```

The build:

1. checks the SHA-256 of all four content-addressed v0.4 ledgers;
2. regenerates five vector figures, derived tables, and a provenance manifest;
3. validates the archived direct-QCA seal, schemas, bindings, independent
   verification receipt, and disclosed post-result pi-sector defect; and
4. compiles the technical
   `output/pdf/quantum_dirac_operational_role_manuscript.pdf` and figure-free
   lay `output/pdf/quantum_dirac_layperson_companion.pdf` with `latexmk` when
   available, then writes a SHA-256 file and build manifest for each plus a
   shared machine-readable pi-sector audit.

The driver defaults `SOURCE_DATE_EPOCH` to the result commit time
and suppresses volatile pdfTeX metadata. A caller may supply a different
integer epoch explicitly; the selected value and exact tool versions are
recorded in the build manifest.

The lay companion is `lay_main.tex` and contains no figures. Numeric plots in
the technical manuscript consume canonical JSON only. Conceptual and analytic figures are
labelled separately in their captions and in
`generated/figure_manifest.json`.
