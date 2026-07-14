# MIR Role-Succession Protocol `0.1-draft`

This directory freezes the outcome-contingent `N_P=2` alternative grammar
under search ID `MIR-ROLE-SUCCESSION-001`.

The grammar is the complete 256-rule centered radius-one binary cellular-
automaton family, expressed as subsets of eight atomic production rows. It
uses one event schema plus the incoming and outgoing incidences of the same
charged oriented-cycle relation schema. The added successor-incidence read,
three-port fan-in, eight-row truth-table capacity, and per-site/per-layer update
accounting are reported explicitly.

The local role, forward successor offsets, matched intervention, and outward
endpoint are inherited from the failed reference test. The detector is
versioned because the seed cone is now bidirectional. `H_pre=29` is the largest
formation layer whose two-layer endpoint is strictly pre-wrap on `C64`.

No canonical candidate trajectory may be evaluated before the outcome-free
implementation and content-hash seal are committed. The only positive fixture
starts from a supplied synthetic dyad and is declared development data.

Files:

- `protocol.json`: endpoints, stopping rules, claims, and provenance.
- `grammar.json`: primitive accounting and complete candidate enumeration.
- `topology.json`: clock, relation, seed, cone, and resource envelope.
- `detector.json`: inherited local predicates and the pre-wrap classification.
- `development_fixtures.json`: disclosed synthetic tests only.
- `partitions.json`: primary and conditional cross-size data allocation.
- `result.schema.json`: canonical result transport schema.

The normative cross-field checks live in the sealed Python validator and
independent replay implementation. JSON Schema alone is not the scientific
validator.

Frozen command surface:

```bash
python3 -m src.minimal_realization_role_succession.cli audit
python3 -m src.minimal_realization_role_succession.cli compile-candidates
python3 -m src.minimal_realization_role_succession.cli freeze-seal
python3 -m src.minimal_realization_role_succession.cli verify-seal
```

The first two commands inspect no candidate dynamics. `compile-candidates`
writes only the canonical 256-record description. `freeze-seal` writes a
disabled content-hash seal. The separately gated `open-development` and
`run-development` commands must not be used in the freeze commit.

Commit the freeze so that this commit first adds the outcome seal, then create
the annotated tag `mir-role-succession-001-v0.1-frozen` at that exact commit.
The opening command
rejects a missing tag, a lightweight tag, or a tag that does not select the
current `HEAD`; it also rejects a tag on a descendant that did not introduce
the seal. Intervening descendant commits cannot become the opening parent.

Post-freeze execution is linear:

```bash
python3 -m src.minimal_realization_role_succession.cli open-development
# commit only the open manifest
python3 -m src.minimal_realization_role_succession.cli run-development
# commit only the result as the direct child of opening
python3 -m src.minimal_realization_role_succession.cli verify-results
```

`verify-results` is deliberately post-commit. It rejects an uncommitted result,
a dirty worktree, a moved freeze tag, or any extra path in the opening/result
commits before independently replaying the ledger.

Production and independent replay each use the frozen four-process,
candidate-level worker allocation. Results are collected in canonical manifest
order and no worker writes a partial artifact; there is no worker-count CLI
override.
