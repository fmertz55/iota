# Handoff: re-derive the node rule from the premises (ledger Section 9) — 2026-11-26
Start the new thread from this note. It supersedes HANDOFF_FILLED_VACUUM_2026-11-25.md for next steps.
Document of record: docs/ICP_CONSTRUCTION_LEDGER.md (v0.2). Read its Sections 1, 4, 5 and 8 before anything else.

## 1. Lane rules (user, binding)
- The research question: is an information-first universe feasible, and does it give rise to the familiar physics we
  experience? Information is the substrate; what physics calls mass and energy must appear as properties of
  coherences, never as primitives.
- Ledger working rules (Section 8) are binding: ledger first; reasons are principles, not outcomes; feature tests
  fixed in advance and reported as scores over the whole constant range; no patch rules; scans are characterisation
  only; known physics names and checks, never chooses; prior work informs and is counted (borrowed pieces enter as
  outcome-chosen until derived); corrections stay public; prior-art gate before any paper.
- Penalty rule (P3): no bag of data held away from a node's own degrees of freedom.
- Vocabulary: Iota terms (clock, push-resistance, drift toward slow clocks); standard names only as a reviewer's
  dictionary (ledger Section 3).
- Style: slow, one stone at a time; KISS options with "my pick" and the honest risk; the user picks; silence during
  long runs, report once; foundational docs give a physics statement plus a Scientific-American-level lay version.

## 2. Where things stand
- QP-002 frozen and passed (tag qp-002-v0.1-frozen): held pairs in the empty vacuum, exact pair clock law.
- EXPLORE-QP-3 (filled vacuum, fork a; committed 66c5440 and 462bf55): the all-R vacuum mixes away anything local;
  only conserved counts last, spread evenly; one extra slot is never held at any theta; theta = 0 and pi mix slower and
  leave a ring-wide alternating wave. Corrected in public: the theta = 0 / pi vacua are identical at N = 8, 12 only.
- Method audit (user): the line had drifted into fitting (adding and tuning pieces until quasi-particles appeared).
  Response: the construction ledger (v0.1 = 7ef6342; v0.2 adds the research question, the July 2026 Dirac result as
  "verified as a construction, not derived", and the prior-work rule).
- Ledger tally: 2 hand-set constants (mu, theta) plus the edge both-full phase fixed at +1; 5 structural choices;
  2 starting states. Only the ring (C8) is principle-derived. C1-C4 (two slots, plain switches, tick order, mu) were
  borrowed from the direct Dirac QCA (Bisio, D'Ariano, Tosini), whose target was Dirac motion.
- Emergent and unasked (ledger 6.4): the colour count C = N_P - N_Q (P = R at even nodes + L at odd nodes) obeys
  C(t+1) = -C(t) and is mirror-odd (checked by code, N = 6-12): a handedness-like conserved count.
- Feature scorecard: quantum = built in; relativity-like = partly; chirality = partly built in, partly emergent;
  angular momentum = cannot test in 1D; gravity = fails its precondition (no record that falls off with distance).

## 3. The task (ledger Section 9; the user's decision to start it)
Re-derive the node and tick from the premises alone and count every free choice they leave open.
Outcome (a): the borrowed Dirac node is the simplest choice, so C1-C4 move from outcome-chosen to principle-derived
and the Dirac clock law becomes a result. Outcome (b): it is not, and we learn exactly how much of route B was
imported. Either outcome is reported.

## 4. Proposed small steps (the user picks each)
1. Fix the premise list first. P1-P3 do not say the rule is reversible, the same at every node, or mirror-symmetric,
   and the Dirac derivation used homogeneity, locality, unitarity, parity and time reversal. Decide, from Iota's
   principles (not from the outcome), which of these are premises and which are choices. KISS this with a pick.
2. Pen and paper: with those premises, list the possible rules from the smallest node upward (1 slot, 2 slots, ...),
   and which free choices each leaves (schedule, which slots pair across an edge, both-full phases, constants).
3. Short numerical check of the hand results on small rings.
4. Update the ledger (v0.3): move pieces between kinds only where the derivation earns it; keep the change log.
Prior work may inform steps 1-2 (e.g. known results on which one-dimensional quantum cellular automata are possible),
cited and counted per rule 7; any search only when the user asks.

## 5. Parked (not lost)
Why theta = 0 and pi mix slower (and the N divisible-by-4 effect); what the colour count means; derive the edge-held
pair law cos(clock) = (1-mu^2)/(1+mu^2) cos K and the pair-size rule 1/(2 mu sin(theta/2)); capture (two separate
coherences becoming held) has never been shown; the thinner-background idea is withdrawn pending the ledger.

## 6. Workflow facts
- Repo folders are read-only to code: the agent writes in the workspace, then host.save_to_folder (one file per call;
  replaces=<sha256> for edits). JSON is refused: seals go as a printf line plus expected sha256 for the user to run.
- The user commits, tags and pushes; the agent supplies the commands (no # comments on pasted zsh lines). Check
  git status before committing. Never sweep the deliberately untracked files (MIR-REVERSIBLE-*/jobs, run.log, ORDER
  results.json, REACH-002, paper_order/ci.py, shadow_paper LaTeX byproducts).
- Exact many-coherence runs: N = 12 is the 8 GB limit; save after every run; one run per process.
