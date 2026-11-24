# GOLD-001 results (v0.1, tag gold-001-v0.1-frozen, commit 7d9ad9d) — 2026-11-24
Run: `python gold001.py run` on the tagged file (sha256 13d46936… matches seal); 46 s. Data: stage1/2/3.csv, summary.txt.
## Verdict: all validity checks and all 9 hypotheses PASS.
| Check | Result | Rule |
|---|---|---|
| V1 | round trip 9.1e-13 (cashier), 5.6e-11 (memory); field outside cone exactly 0 | < 1e-9; 0 |
| H1-SLOW | N(lump) < N(test) < 1 at every sample, 6/6 | all 6 |
| H1-FALL | lambda 0.991-0.998; max displacement before news 9.4e-4 cell | [0.97, 1.03]; <= 0.01 |
| H1-MEM | memory moves 0.14%, 0.006%, 0.004% of cashier at D = 1400; N(lump) = -1.47 | < 2%; < 0 |
| V2 | invariant 6.7e-16; r_space_clock 0.998/0.994/0.966; cutoff share <= 6e-26 | < 1e-10; >= 0.95; < 1e-2 |
| H2-GOLD | G = 2.17e-4, 8.79e-4, 3.81e-3 after recombination | > 1e-10 |
| H2-SCALE | slope of G vs max separation = 2.10 | [1.6, 2.6] |
| H2-WL | worldline formula within 7.1% (max), 7/7 | <= 10% |
| H2-SPLIT | max |r_total - r_space_clock*r_note| = 3.1e-6 | <= 1e-3 |
| V3 | closure 2.2e-10 | < 1e-6 |
| H3 | G_3D = 5.9e-56 for kappa = 1e-6, 1e-3, 1 (identical) | < 1e-30 |
## Descriptive
- Stage 1 universality: displacement at D = 900 is 52.27 / 52.30 / 51.55 cells for eps 0.04 / 0.12 / 0.25.
- Fringe loss at v = 0.2 (1D lattice units): recombination 3.4%, clock (delta 0.02) about 31%, notebook 0.38%.
  r_total factorises into atom part x notebook part to 3e-6.
- G during the hold exceeds G after recombination by only 3-28%: most of the record is not dressing that the field
  hands back, it stays in the notebook (radiated / proper-time record).
- theta with and without the clock agrees within 1e-2 rad; sigma 150 vs 100 changes G by 4%.
- Stage 3: kappa drops out entirely (tick from 1.9e-43 s to 1.9e-37 s gives the same G_3D).
## Reading (revised 2026-11-24 after user review)
At the substrate's own scale (turn rates and handshake near lattice scale) the busy-cashier notebook gives
gravity-like behaviour (universal fall, causal, reversible) and a genuine which-path record that survives
recombination, separable from the clock part, of size up to 0.4% fringe loss. That is the finding.
Stage 3 is a CONDITIONAL extrapolation, not a finding: IF a slow-turning composite (a future quasi-particle) sources
the notebook by simple addition of its parts, its record shrinks with its total turn rate and would be ~6e-56 for an
object like Rb-87. No quasi-particle exists yet, so this bridge is untested. Heavy memory is confirmed dead as a
gravity source. Open question for the gold line: how do the notebook records of many coherences combine when they
bind into one quasi-particle (simple addition, cancellation, or internal records)?
