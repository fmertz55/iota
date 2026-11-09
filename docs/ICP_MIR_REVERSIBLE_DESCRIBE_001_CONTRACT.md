# MIR-REVERSIBLE-DESCRIBE-001: does the description D rebuild the shadow, cell by cell, into its future? (v0.1)

Status: **frozen at tag `mir-reversible-describe-001-v0.1-frozen`**. 2026-11-09. Code: `describe1.py` (imports the frozen
`wall1.py` and `inventory1.py`; `runs()` is a verbatim copy of `wall1.job` up to the wall targets, plus one change
below). Line: PREDICT (handoff 2026-11-09h, step 2). Parent: WALL-001/002 (valid).

## Question
PREDICT will ask whether a compact description D of a shadow predicts its responses to new probes. That only makes
sense if D is first a complete coordinate system: from D alone (plus a dictionary of wall and domain types) every cell
of both layers must be rebuilt, and D must carry its own time, so that D read once, advanced by its free law, still
rebuilds the shadow later. Where this fails, the failures list what the language misses, and the language must be
fixed before any prediction test (user rule 4: completeness including time is tested, not assumed).

## The language D (frozen)
- Global: the absolute tick (vacuum clock).
- Per wall: WALL-001's descriptor (sub = the orbit of its local window, wall cells plus MW = 8 flank cells, up to
  rotation; clock = orbit phase; place = space-time intercept; speed v; period P <= 96), measured in the BUILD window
  [tw, tw + WT), WT = 192.
- Per domain: its record (spatial period s, orbit-canonical species or vacuum lag) and its phase, the s-cell pattern
  aligned to x = 0 mod s, read at the last exact snapshot tL (< tw) from the frozen decomposition.
- Dictionaries: wall orbits keyed by sub; domain orbits generated from the aligned pattern by the rule on an s-aligned
  ring. Both are type tables, shared across runs; their sizes are reported.
- One change from WALL-001: the walls of rigid-mover components are tracked too, since the whole residue must be
  described. WALL-001's run classes (none, open, dis, movers, followed) are kept and checked (V0).

## Rebuild and test
At tick t, from D only: ambient vacuum everywhere; each domain's pattern advanced from tL to t, painted between its two
walls' predicted edges; each wall's window at phase j = (t - clock) mod P, at position place + v (t - j) + dx_j,
painted on top. Compared with q = 2p + c (both layers) on every cell of the ring at every tick of the FUTURE window
[tw + WT, tw + 2 WT). That window is not used to build D. A run is **exact** if every cell matches at every tick.
Mismatched cells are classed as wall (inside a predicted window), interior (inside a predicted domain, outside
windows) or outside (debris: covered by neither). Runs with class open or dis have no D (language failure, reported
by class); runs with class none are empty after erasure and are not counted.

What is not a test, by construction: at the build window the wall windows are the measured windows themselves. The
test is the future: domain interiors must evolve as pure domains, walls as exact orbits on straight space-time lines,
with nothing else present (no hidden defect, debris or drift), for 192 further ticks.

## Validity controls (frozen; invalid if any fails)
- V0: per pair, n and the run classes equal WALL-001's stored values, all 28 pairs.
- V1: no edge hit and no wall lost or unclosed (build or future window) in the eligible pairs.
- V_S (sensitivity; the claim must fail for a wrong D): for the first 4 exact runs of every pair, (a) the first
  wall's place + 1 and (b) for P > 1 its clock + 1 with place - v (same integer path, wrong orbit phase) must each give
  a non-exact rebuild. Every eligible pair must have at least one control.

## Hypothesis (frozen)
- **H_D (D is lossless, including time)**: in every one of the 7 WALL-001 eligible pairs (147 201 22s 26s 58s 82s 114s),
  every described run (class followed or movers) is exact. Supported only if all 7 pass. Prior: likely in the eligible
  pairs (their walls all closed in WALL-001), unknown elsewhere. Rule 91 exposed and excluded.
- Kill criterion (pre-registered): if H_D is not supported, PREDICT-001 is not started. The failures (class, cell
  class, first failing tick) define a revised language v0.2, tested by a new contract.
- Descriptive, all 28 pairs: described and exact runs, run classes, failure cell classes, first failing tick, number of
  walls, distinct wall orbits, distinct domain states, mean non-vacuum cells per exact run.

## Exposure (before freezing; disclosed)
- Stored WALL-001 values for all pairs (n, run classes, eligible set, edge hits, lost and unclosed walls: rule 37 has 30
  unclosed walls; 143 171 213 241 151 233 37 have open runs; 154 182 186 have disordered runs).
- Calibration, full output, rule 91 (exposed): run classes followed 64, none 192 (equal to WALL-001); all 64 described
  runs exact; controls 4/4 fail for place and for clock; 160 walls, 8 distinct wall orbits, 3 domain states; mean
  3755 non-vacuum cells. 25 s per pair. A first calibration crashed on the clock control (a clock + 1 alone puts a
  wall with fractional speed off the lattice); fixed before freezing by the place - v compensation above.
- Smoke on null 5 printed validity only: run classes none 192, movers 64; controls 4/4 fail (this shows some of its
  movers runs are exact); no edge hit or untracked wall. No other pair was run.

## Limits
The domain phase is read from cells (that is how D is measured); D's size is reported as type counts, not as a
minimal code length. MW = 8 flank cells inside each window means a defect within 8 cells of a wall is absorbed into
that wall's type. The future window is 192 ticks, two full periods of the longest allowed wall orbit. D is complete for
free evolution only; responses to probes are PREDICT's question.

## Prior art (do not claim)
Domain/particle decompositions of CA space-time (Hanson & Crutchfield 1992, 1997) and particle-level models that run
without the cells (Hordijk, Crutchfield & Mitchell 1996, 1998; addendum 2026-11-09). Candidate contribution: an exact,
cell-by-cell, future-window completeness test of such a description in a reversible substrate, with sensitivity
controls.
