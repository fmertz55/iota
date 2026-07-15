# ICP Quantum-Dirac Paper Visualization Audit

Date: `2026-07-15`

Status: **figure plan complete; no second-architecture registered figures authorized**

## Audit result

The repository does not currently contain reusable paper figures for the
quantum-Dirac manuscript. The `visualizations/` directory is a production
scaffold for a separate 12-scene IOTA/constraint-transport explainer. It has a
visual grammar, narration outline, and theme constants, but no implemented
scenes, normalized data, or rendered assets. The existing `paper/` manuscript
is likewise a separate constraint-transport paper and contains tables but no
quantum-Dirac figure source.

The quantum paper therefore needs a new, compact figure system. Some principles
from `visualizations/VISUAL_GRAMMAR.md` should carry over—especially the visible
separation of illustration from evidence, redundant color/shape encoding, and
the ban on particle-like imagery. Its dark video palette, bridge vocabulary,
recorded-run overlays, and current narration should not be reused as the paper
style.

## Existing material: reuse decision

| Existing item | State | Decision for quantum paper |
|---|---|---|
| `visualizations/scenes/`, `components/`, `data/`, `renders/` | placeholders only | nothing to reuse |
| `VISUAL_GRAMMAR.md` | complete for IOTA video | reuse evidence/illustration and accessibility principles only |
| `config/theme.py` | dark-screen video theme | do not use for print figures |
| `narration/script.md` | conceptual IOTA/constraint-transport outline | do not adapt as quantum-paper narration; several claims are broader than the bounded quantum result |
| `paper/main.tex` and sections | separate constraint-lineage manuscript | do not insert quantum figures or sections |
| parent v0.4 result ledgers | immutable structured data | authoritative source for verified product-walk result plots |
| direct-QCA audits and threshold certificate | analytic, outcome-free | authoritative source for analytic circuit/spectrum/bound figures |
| direct-QCA result ledgers | nonexistent by design | no direct empirical panel until a valid registered disposition |

## Required main-paper figures

### Figure 1 — The construction question and comparison maps

Purpose: make the claim legible before any numerical plot.

Recommended form: a three-part schematic:

```text
bounded Dirac target --E/Phi--> local informational architecture --M--> matched observables
```

Show the supplied structure below the flow—quantum primitive, lattice, clock,
constants, precision, and intervention class—and the tested outputs above it.
The figure must visually separate what was supplied from what was constructed.

Source/status: conceptual contract diagram; safe to build now.

Placement: introduction or methods overview.

### Figure 2 — Two genuinely different local architectures

Purpose: establish architectural breadth rather than parameter variation.

Recommended form: aligned two-panel circuit/timeline diagram on the same cell
pair and the same left-to-right time axis.

- Product walk: potential phase when active, mass mix, on-site SWAP, directed
  edge SWAP; free depth 3 and active depth 4.
- Direct symmetry QCA: potential phase when active, edge scatter, on-site SWAP;
  free depth 2 and active depth 3.

Annotate local Hilbert dimension 4, storage `2N`, causal radius one, and gate
work per macrostep. Use distinct gate shapes as well as color. Include the
hard-core `|11>` phase only as a concise callout, not a many-particle diagram.

Source/status: analytic circuit declarations; safe to build now.

Placement: candidate construction section.

### Figure 3 — Certified convergence across refinement

Purpose: show the primary operational evidence and distinguish convergence
orders.

Recommended form: two aligned log-log facets with lattice spacing on the
horizontal axis and certified operator-distance upper bound on the vertical
axis.

- Product-walk facet: plot all six immutable v0.4 scenario series at
  `delta=1/16,1/32,1/64`, with frozen absolute gates and a first-order guide.
- Direct-QCA facet: after its valid result, plot the six new series at
  `delta=1/20,1/40,1/80`, using separate direct-only and potential-split gate
  lines plus second- and first-order guides.

Do not populate the direct facet from the threshold certificate. The
certificate is rationale, not outcome. Before a valid direct result, use only a
clearly labeled empty layout in internal mockups; omit the facet from any
public evidence figure.

Source/status: parent panel can be built now from immutable ledgers; comparison
figure waits for direct disposition.

Placement: primary results.

### Figure 4 — Operational witness comparison

Purpose: show that the claim is not based on one matrix norm or visual
resemblance.

Recommended form: shared-scale small multiples for position TV, momentum TV,
total-current error, local-current L1 error, infidelity, and Zitterbewegung
current-series error. Each mark is an outward upper bound; each panel includes
its frozen gate. Use scenario/state identifiers in accessible metadata or the
supplement rather than crowding the main plot.

The main paper should show maxima by architecture and partition; the supplement
should show every state/scenario/time record. Do not use radar charts because
the units and gates differ.

Source/status: parent values exist; cross-architecture figure waits for direct
disposition.

Placement: primary or secondary results depending on journal length.

### Figure 5 — Direct-QCA spectrum and bounded claim domain

Purpose: show why low-momentum success and whole-zone equivalence are different
claims.

Recommended form: two analytic panels.

1. Quasienergy bands `omega/pi` against `q/pi` for representative disclosed
   nonregistered mass values, with the registered low-momentum window shaded,
   both zero and π gaps labeled, and no suggestion that the entire band is the
   continuum Dirac spectrum.
2. A magnified comparison of the `q≈0` cone with the `q≈-pi` partner, labeling
   the exact relation `U_mu(-pi+p)=-U_-mu(p)` and the opposite-mass
   pseudodoubler after the Floquet phase shift.

Use line style and direct labels in addition to color. The pseudodoubler should
be a warning annotation, not a decorative second cone.

Source/status: exact analytic audit; safe to build now and not a registered
outcome.

Placement: limitations/global-spectrum section.

### Figure 6 — Evidence and claim boundary

Purpose: make the manuscript safe to socialize outside the specialist
audience.

Recommended form: a compact nested-domain diagram or claim ladder:

```text
verified: bounded single-particle role for product walk
tested next: same role for direct symmetry QCA
not established: whole zone, fermionic many-particle QFT, ontology, uniqueness, minimality
```

This should distinguish verified, active, and excluded claims with labels and
line patterns, not traffic-light color alone.

Source/status: conceptual synthesis; safe to build now. A simplified version
should accompany the lay companion or graphical abstract.

Placement: discussion/limitations or socialization materials.

## Supplementary figures

| ID | Content | Source/status |
|---|---|---|
| S1 | full-space edge scatter and on-site SWAP action on `|00>,|01>,|10>,|11>`; hard-core versus determinant `|11>` phase | analytic; build now |
| S2 | scenario timelines, observation times, and development/confirmation separation for both architectures | frozen parent plus prospective direct design; build now with status labels |
| S3 | target cutoff and π-sector interaction-order/tail construction | analytic threshold certificate; build now |
| S4 | direct potential certificate with intermediate bands `13,17,20` and leakage penalties | analytic; build now |
| S5 | lifecycle provenance from implementation through freeze/open/result/replay | parent verified; direct template must remain marked pending |
| S6 | every witness/scenario/time value and Zitterbewegung time series | parent available; direct waits for result |
| S7 | post-primary failure controls | waits for direct registered disposition |

## Build order

1. Build Figures 1, 2, 5, and 6 from contracts and analytic audits.
2. Add the product-walk panel of Figure 3 directly from the immutable v0.4
   ledgers using a checked extraction script.
3. Build S2–S5, keeping every direct lifecycle or outcome field visibly
   prospective.
4. After a valid direct result, generate—not manually transcribe—the second
   panels of Figures 3 and 4 plus S6–S7 from the canonical ledgers.
5. Run a figure-only hostile-reader audit before manuscript integration.

## Data and provenance rules

- Every numeric figure must be generated from canonical JSON, never copied from
  prose or a terminal display.
- The figure build should record input paths and SHA-256 hashes in a sidecar
  manifest.
- Analytic illustrations must say `ANALYTIC` in the caption; registered result
  plots must say `REGISTERED RESULT`; prospective layouts must say `PENDING — NO
  OUTCOME` and must not appear in a submitted evidence figure.
- Outward upper bounds are plotted at their serialized upper value. Midpoints
  must not replace certified bounds.
- Cross-architecture panels must retain separate registered domains and gates;
  do not normalize both to a percent-of-gate score as the only view.
- Candidate and target curves need independent line styles and direct labels.
- Preserve exact scenario order and never omit a failed scenario from a maximum
  or aggregate.

## Print and accessibility specification

- Author figures as vector PDF/SVG with script-generated source.
- Design first for a white journal page and grayscale printing; the existing
  near-black video theme is unsuitable.
- Use at most two persistent series colors per panel, backed by solid/dashed
  lines, marker shapes, hatching, or labels.
- Keep final-size text at least 7 points and ordinary strokes at least 0.6
  points.
- Avoid glow, particle trails, atom/orbital imagery, 3D perspective, radar
  charts, and decorative lattice backgrounds.
- Captions must state whether a figure is analytic, registered, or conceptual
  and must name the bounded domain relevant to its claim.

## Minimum viable submission set

For a technical paper after the second architecture reaches a valid
disposition, the minimum defensible main set is Figures 1, 2, 3, 5, and 6.
Figure 4 may move to the supplement if space is tight, but the paper must still
report the witness gates in a table. If the second experiment ends without a
valid result, Figures 3 and 4 must show only the verified parent data; the direct
protocol and failure/incompletion boundary should be explained without
outcome-like marks.

