# Handoff: node-only quasi-particles, next = filled vacuum (fork a) — 2026-11-25 (evening)
Start the new thread from this note. Supersedes HANDOFF_NODE_RULE_QP_2026-11-25.md for next steps (its sections 1-4
still hold). Exploratory record: output/minimal_realization/EXPLORE-QP-2/NOTES.md. Frozen: QP-002 (below).

## 1. Lane rules (user, binding) — unchanged, read first
- Premise: a lattice of N nodes, each with its own degrees of freedom, that only exchange information with neighbours,
  should give quantum behaviour and, at scale, relativity-like behaviour. The lattice is accepted as the substrate.
- Penalty rule: any bag of data held away from a node's own degrees of freedom is a penalty flag (extra notebook layers,
  hand-supplied values or slopes, mean-field summaries). Do not stack layers to solve problems.
- Iota follows its own rules. Known physics is never a design target or a reason to change a rule. No mass, energy,
  inertia, force, "falling". Use: clock (turns per tick), push-resistance (kick / speed gained), drift toward slow clocks.
- No prior-art hunting unless the user asks (a prior-art gate is required before any paper).
- Style: slow, methodical, one stone at a time ("we can't skip over something a reviewer will see"). Quick
  exploratory probe, then a frozen contract (code + seal + tag) before any claim. KISS lay summaries with "my pick"
  and the honest risk; the user picks; silence during long runs, report once at the end.

## 2. The rule (zero flags) — unchanged
Frozen direct Dirac QCA: node = two yes/no slots (R, L). Tick = edge exchange on (L_x, R_{x-1}), one-coherence block
[[-i mu, n],[n, -i mu]], n = sqrt(1-mu^2), both-full untouched; then in-node swap R_x <-> L_x, both-full gets
e^{i theta}. Constants mu (supplied) and theta. Frozen code: src/quantum_gold/qp002.py (layers, two_coherence,
full_circuit_two, k_block, held_pair, validity).

## 3. Done today
- EXPLORE-QP-2 step 4 (commit 951c161): smooth limit; the held pair spreads as mu shrinks and stays held.
- QP-002 FROZEN and PASSED (tag qp-002-v0.1-frozen, commit f8f8940; contract docs/ICP_QP_002_CONTRACT.md, seal
  specs/icp_quantum_gold/qp002_seal.json; results output/quantum_gold/QP-002/RESULTS.md). V1-V4, H-HELD, H-LAW,
  H-SPREAD, H-SIZE all pass on unseen grids: held pairs at all 495 settings; exact law
  cos(clock) = (1-mu^2) cos K - mu^2 cos(theta) to max 1.3e-9 (median 3.6e-15); pair 4.2x wider at mu 0.06 than 0.24;
  size -> 1/(2 mu sin(theta/2)) nodes (within 0.2% at mu 0.06, approached from below). Descriptive: at theta >= 0.6 pi
  the pair is widest at top pair speed (K = pi). Tag note: first push of the tag hit 951c161 by mistake, moved to
  f8f8940 before any run (recorded in RESULTS.md).
- Still open/parked: derive the size rule (fit only so far); derive the edge-held pair law
  cos(clock) = (1-mu^2)/(1+mu^2) cos K (step 5, parked); theta near pi untested.

## 4. The user's decision: rule fork = (a)
A non-empty vacuum means: SAME rule, only the STARTING STATE changes — every node starts with one slot full.
No new rule, no new bag. Rejected for now: (b) start from the rule's settled filled state (extra computing step,
may be too calm), (c) a fill/drain rule (breaks conservation of full slots; a rule change to solve a problem).
Why: in an empty vacuum nothing outside a pair can change, so no shadow, no drift toward slow clocks, and free
coherences can never become held. A full vacuum gives the leftover somewhere to go. Working hypothesis: forming a
quasi-particle and leaving a shadow may be the same event.

## 5. Next small steps (proposed; the user picks each)
1. Choose which slot is full at each node (a design question for the user, KISSed): all R; all L; or alternating
   R/L. Each is node-local and adds no flag. Agent's leaning: present the three with a pick before coding.
2. Probe 1, vacuum alone: exact many-coherence run on a small ring (N = 8-12 nodes; half filling, N full slots in
   2N; dimension C(2N, N), 2.7 M at N = 12, fits 8 GB as sparse/state-vector evolution, not full matrices). Questions:
   does the full vacuum stay put or churn; how fast does a change spread (cone); does a one-node change leave a
   record that survives (reversibility check: run forward then back).
3. Probe 2: put a disturbance (e.g. one extra full slot, or one emptied slot) into the full vacuum and watch whether
   something held forms and what it leaves behind. Only after probe 1.
Cautions: exact runs stop near 12 nodes, so pairs must be small (use mu ~ 0.5-0.8, where QP-002 pairs are ~1 node).
Larger runs need an approximation validated on these small exact cases, or remote compute. Prior-art gate before any
paper (Thirring QCA bound states; the pair law may be known).

## 6. Workflow facts
- Repo folders are read-only to code: agent writes in the workspace, then host.save_to_folder, one file per call.
  save_to_folder refuses JSON: the agent gives the seal as a `printf '...' > specs/.../x_seal.json` line plus the
  expected sha256, and the user runs it. Put no `# comments` on pasted zsh lines (zsh reads them as arguments).
- The user commits, tags and pushes; the agent supplies the git commands. If a `git add` fails, nothing is committed,
  so check before tagging. Frozen runs use `git show <tag>:<path>` with sha256 checked against the seal.
- Many untracked files in iota are deliberately left untracked (MIR-REVERSIBLE-*/jobs, run.log, ORDER results.json,
  REACH-002, paper_order/ci.py, shadow_paper LaTeX byproducts): never sweep them into commits.
