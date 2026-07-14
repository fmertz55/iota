# MIR Role-Succession Exact Closure `0.1-draft`

This directory freezes the outcome-blind continuation of the ten unresolved
`MIR-ROLE-SUCCESSION-001` candidates under search ID
`MIR-ROLE-SUCCESSION-EXACT-001`.

The continuation changes no grammar or detector. It first applies one of two
generic exact local certificates: a homogeneous-comparator obstruction when
`f(000)=1`, or exhaustive evaluation of all eight causal contexts on offsets
`-2..+5` when `f(000)=0`. Only a candidate with at least one surviving joint
local context is replayed from layer zero through the parent boundary and then
continued without a layer ceiling to exact pass or exact recurrence.

No registered certificate classification, local-context table, or state after
layer `1,000,000` may be generated before the freeze. Outcome-free tests use
only nonregistered rules and disclosed synthetic contexts.

Files:

- `protocol.json`: parent binding, exact candidate derivation, certificate,
  continuation, controls, decision rules, and provenance.
- `result.schema.json`: transparent continuation-result transport schema.

The normative cross-field checks live in the sealed production validator and
the separately expressed independent verifier. JSON Schema alone is not the
scientific validator.

Frozen command surface:

```bash
python3 -m src.minimal_realization_role_succession_exact.cli compile-candidates
python3 -m src.minimal_realization_role_succession_exact.cli seal-outcomes
python3 -m src.minimal_realization_role_succession_exact.cli verify-seal
```

All three commands perform no registered certificate evaluation and no
candidate dynamics. `seal-outcomes` writes a disabled content-hash seal. The
opening and production commands are unavailable until the annotated freeze tag
exists at the exact seal-introduction commit.

Post-freeze execution is linear:

```bash
python3 -m src.minimal_realization_role_succession_exact.cli open-outcomes
# commit only the open manifest
python3 -m src.minimal_realization_role_succession_exact.cli run
# commit only the result as the direct child of opening
python3 -m src.minimal_realization_role_succession_exact.cli verify-results
```

The freeze commit must be the direct child of parent result commit
`9b83fc8e1c9f0a034d6240677c9220bbcafa04cf` and carry annotated tag
`mir-role-succession-exact-001-v0.1-frozen`. Opening and result are its next two
direct children and may each add only their registered artifact.

Production and independent replay each use the frozen four-process,
candidate-level allocation. A run is serialized only after all ten resolutions
and every triggered `C96`/`C128` control complete. Interruption produces no
result and no resource-censored classification.
