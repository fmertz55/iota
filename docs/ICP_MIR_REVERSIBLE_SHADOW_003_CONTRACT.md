# MIR-REVERSIBLE-SHADOW-003 — does the probe itself carry the record? Is it robust? (v0.1-draft)

Status: **outcome-free; frozen at tag `mir-reversible-shadow-003-v0.1-frozen`**. 2026-11-04. Code: `shadow3.py`.
Parent: SHADOW-002 (footprint ratio 1.0 in 12/12 shadow rules, one collision pair per rule).

## Design
Same as SHADOW-002 (erase carriers at T=600, launch a free R-state probe from one fixed site outside
every shadow, run 1500 ticks; 64 offsets; exact entropies), except:
- Pairs: per rule, every combination of the first 2 right-movers and first 2 left-movers (|v| >= 1/8,
  catalogue order), so up to 4 pairs per rule. N = 8192.
- New readout, probe state: the resolved coherences (union-layer, exactly periodic, width <= 8) at the
  final tick whose span overlaps the region where the worlds with and without the probe differ. These
  are what the probe's passage leaves as coherences, described by species, state and position.
  Diffuse or unresolved change is excluded, so this is the carrier-level readout.
- Reported: footprint ratio and probe-state ratio = I(input; X | departing carriers) / H(input |
  departing carriers); and how often a coherence of the probe's own species is among them.

## Hypotheses (frozen)
- Control: pairs with no shadow must give 0 for both readouts, else invalid.
- H_R robust: footprint ratio = 1 in >= 90% of shadow pairs.
- H_P probe carries the record: probe-state ratio > 0 in >= half of shadow pairs.
- Descriptive: probe-state ratio distribution; how often the probe survives as its own species.
