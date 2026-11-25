# Handoff: node-only quasi-particles (route B) — 2026-11-25
Start a new thread from this note. Supersedes HANDOFF_QUASI_PARTICLE_2026-11-24.md for next steps.
Exploratory files: output/minimal_realization/EXPLORE-QP-2/ (NOTES.md has the full record).

## 1. Lane rules (user, binding)
- Premise: a lattice of N nodes, each with its own degrees of freedom, that only exchange information with neighbours,
  should give quantum behaviour and, at scale, relativity-like behaviour. The lattice is accepted as the substrate.
- Penalty rule: any bag of data held away from a node's own degrees of freedom is a penalty flag (extra notebook layers,
  hand-supplied values or slopes, mean-field summaries). Do not stack layers to solve problems.
- Iota follows its own rules. Known physics is never a design target or a reason to change a rule. No mass, energy,
  inertia, force, "falling". Use: clock (turns per tick), push-resistance (kick / speed gained), drift toward slow clocks.
- No prior-art hunting unless the user asks (but a prior-art gate is required before any paper).
- Style: slow, methodical steps; quick exploratory probe, then a frozen contract (code + seal + tag) before any claim.
  KISS lay summaries with "my pick"; silence during long runs; the user picks the next step.

## 2. The rule (zero flags)
Frozen direct Dirac QCA: node = two yes/no slots (R, L). Tick = edge exchange on (L_x, R_{x-1}), one-coherence block
[[-i mu, n],[n, -i mu]], n = sqrt(1-mu^2); then in-node swap R_x <-> L_x. One addition: phase e^{i theta} when both
slots of a node are full at the swap. Constants: mu (supplied) and theta. Code: EXPLORE-QP-2/b1_pair.py
(two_particle, k_blocks), b3_law.py (held_map, track).

## 3. What we have (exploratory, exact two-coherence sector, 1D)
- The frozen rule is already interacting (free only when both both-full phases are -1).
- Held pairs: hold together with no glue, keep one clock, stay held at every pair speed, top speed < 1 node/tick.
- Exact law: cos(clock at K) = n^2 cos K - mu^2 cos(theta) (median error 5e-15). At theta = pi/2 the pair is exactly a
  lone coherence with n -> n^2 (push-resistance = tan(own clock)). Smooth limit: pair clock = |cos(theta/2)| x two lone
  clocks; push-resistance = own clock for every theta.
- A second, theta-independent pair from the frozen edge step: cos(clock) = (1-mu^2)/(1+mu^2) cos K (not yet derived).
Not yet: pairs are ~1 node across; mu is supplied; only two coherences; no shadows and no drift toward slow clocks.

## 4. Key insight for what comes next
In an empty vacuum nothing outside a pair can change: an empty node stays empty. So (a) no shadow can be left, (b) no
drift toward slow clocks can be sourced, and (c) two free coherences can never become a held pair, because the rule
loses nothing and the leftover has nowhere to go. A non-empty vacuum gives the leftover somewhere to go. Working
hypothesis: forming a quasi-particle and leaving a shadow may be the same event.
Shadows were shown before in the classical reversible-CA substrate (SHADOW line); they must be re-shown in this rule.

## 5. Agreed path (user, 2026-11-25) and open steps
Firm up -> tweak rules -> bigger run (bigger quasi-particles + shadows) -> paper as a statement on the premise.
1. DONE: the exact law (item 1).
2. Smooth limit: does the pair stay tight as mu gets small, or spread?
3. Freeze steps 1-3 as a contract (code + seal + tag).
4. Rule fork, the user's decision from Iota's principles: what a non-empty vacuum means in our own terms.
5. Optional: derive the edge-held pair law.
Cautions: the bigger run is many-coherence quantum (exact runs stop near a dozen nodes on 8 GB once the vacuum is
filled): plan an approximation validated on small exact cases, or remote compute. Prior-art gate before the paper
(Thirring QCA bound states are the nearby road; the pair law may be known).

## 6. Workflow facts
Repo folders are read-only to code: write in the workspace, then host.save_to_folder, one file per call. The user
commits, tags and pushes; the agent supplies the git commands. Frozen runs use `git show <tag>:<path>` with the
sha256 checked against the seal (JSON seals are handed over as artifacts).
