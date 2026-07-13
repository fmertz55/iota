# Minimal Informational Realization v0.2 Draft

This directory is the outcome-free preregistration for the first deterministic
reference search. Version `0.2-draft` supersedes `v0.1-draft` after an audit
showed that the earlier `N_P=1` starting shell left the interaction topology
uncharged and that its causal endpoint duplicated role persistence.

The reference grammar has one binary event channel, one charged directed
predecessor channel, four possible exact two-bit production rows, a fixed
64-locus directed cycle, and no randomness. It searches the 16 production-row
subsets in increasing law count. The proto-object is an attributed isolated
active dyad with one-tick succession and a matched-intervention effect two
layers later outside the intervention window.

This is an `H=16`-bounded pilot. A nonpass is recorded as `T_proto > 16`; it is
not evidence that the candidate can never form a proto-object. The pilot may
identify the best bounded candidate, not certify an unbounded minimum-law
construction.

The files are:

- `candidate.schema.json`: structured reference-candidate schema;
- `operator_alphabet.json`: the only admitted atomic operator and fan-in;
- `topology.json`: charged cycle topology, schedule, seed, and resources;
- `causal_cone.json`: horizon, baseline, and attribution rule;
- `proto_object_detector.json`: exact role and causal-test specification;
- `detector_fixtures.json`: analytic detector-development cases, including one
  disclosed in-grammar two-layer intervention response but no seeded search or
  ranked result;
- `partitions.json`: development and sealed translation allocations;
- `lower_shell_exclusions.json`: grammar-relative analytic exclusions;
- `lower_shell_null.json`: the excluded `N_P=2, N_L=0` candidate;
- `search_plan.json`: exhaustive budget, stopping rule, and remaining seal; and
- `result.schema.json`: the closed development-result ledger schema.

`search_plan.json` remains immutably `outcomes_sealed`. The registered
development search may run only after `open-development` creates the development-open
manifest from a clean outcome-free preregistration commit and that new manifest
is itself committed. The held-out allocation has no runner in this version.

Outcome-safe checks and compilation:

```bash
python3 -m src.minimal_realization.cli audit \
  --spec-dir specs/icp_minimal_realization/v0.2-draft
python3 -m src.minimal_realization.cli compile \
  --spec-dir specs/icp_minimal_realization/v0.2-draft \
  --output experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/development_candidates.jsonl
python3 -m src.minimal_realization.cli verify-seal \
  --seal experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/outcome_sealed_manifest.json
```

The package exposes a commit-gated development-only runner with no candidate,
translation, horizon, or output overrides. It intentionally exposes no
held-out-run command.

After the outcome seal and all of its bound files are committed from a clean
worktree, the only opening sequence is:

```bash
python3 -m src.minimal_realization.cli open-development \
  --seal experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/outcome_sealed_manifest.json
# Commit the generated development_open_manifest.json before continuing.
python3 -m src.minimal_realization.cli run-development \
  --open-seal experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/development_open_manifest.json
python3 -m src.minimal_realization.cli verify-development-results \
  --open-seal experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/development_open_manifest.json
```

The run and verifier are permanently restricted to development translations
`0..47`; neither exposes a reserved offset or output-path argument. Offsets
`48..63` are algebraically implied by exact translation equivariance and cannot
serve as independent confirmation.
