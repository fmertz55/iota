# Minimal Informational Realization v0.1 Draft

This directory contains the machine-readable start of the minimum-realization
program.

- `candidate.schema.json` declares the candidate record.
- `lower_shell_null.json` records the excluded `N_P=1`, `N_L=0` shell.
- `proto_object_detector.json` records the common development detector.
- `search_plan.json` records completed shells, the next shell, and blockers that
  prevent ranked outcome generation.

Validate candidate manifests with:

```bash
python3 scripts/validate_minimal_realization.py <candidate.json> [...]
```

The validator enforces the literal surface-law grammar and the currently
machine-checkable accounting rules. Human semantic audit remains necessary to
detect a compound operation hidden behind an atomic-looking name.
