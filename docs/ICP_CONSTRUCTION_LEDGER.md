# ICP Construction Ledger — the node rule (route B), declared and counted
Version 0.1 (draft for the user's edit), 2026-11-26. Scope: the live construction of the quasi-particle line
(QP-002, EXPLORE-QP-2, EXPLORE-QP-3). Earlier substrates (Iota Rig v0.2 stochastic laws; the classical reversible
cellular automata of MIR-REVERSIBLE-*) are out of scope and get their own ledger if they return to use.

Each entry gives the physics statement first, then **In plain terms** for a reader of Scientific American.

---

## 1. Why this ledger exists

**Physics.** The program's aim is the smallest set of rules from which basic features of the physical world follow:
quantum behaviour, relativity-like behaviour at scale, something like chirality, angular momentum, and gravity.
The README already requires that "fixed topology, laws, scheduling, and constants remain declared and counted
construction structure". After EXPLORE-QP-3 probe 3 the user flagged that this had slipped: quasi-particles had
become the goal, and pieces were added or tuned until they appeared. That is fitting. This ledger lists every piece
of the construction, where it came from, and whether it was chosen from a principle or for an outcome.

**In plain terms.** If you are allowed to keep adding rules, you can make a model do almost anything, and then the
model explains nothing. The test of a theory built from scratch is how little you had to put in. So we keep a public
list of everything we put in, and why, including the things we now think we should not have.

## 2. Three kinds of ingredient

- **Premise (P).** Assumed by the program; not up for tuning.
- **Principle-derived (D).** Follows from the premises plus a stated principle, chosen before seeing results.
- **Outcome-chosen (O).** Chosen, at least partly, because it produced (or was expected to produce) a wanted result.
  Every O entry is a fitting risk and counts against the construction.

**In plain terms.** Premises are the ground rules. Derived pieces are forced by the ground rules. Outcome-chosen
pieces are the ones a sceptic should circle in red.

## 3. Words we use, and their standard names

Iota's own vocabulary is used throughout. Standard names are given only so a physicist can check us; they are a
dictionary, not a design target.

| Iota term | Meaning here | Standard name (for reviewers) |
|---|---|---|
| slot | one yes/no degree of freedom at a node (R or L) | qubit / mode occupation n in {0, 1} |
| full slot | a slot in its "yes" state | occupied mode, one excitation |
| coherence | a pattern of amplitude carried by full slots | wave packet / quantum state of excitations |
| tick | one application of the rule to every node | one time step of a quantum cellular automaton (QCA) |
| clock | turns of a coherence's phase per tick | quasi-energy; in the smooth limit, the rest-frequency (Dirac mass term) |
| pair speed K | total phase-wind per node of a two-coherence state | total quasi-momentum |
| held | two coherences stay a finite number of nodes apart | bound state |
| push-resistance | kick given / speed gained | inertial mass |
| drift toward slow clocks | a coherence moving toward nodes where clocks run slow | gravitational free fall (equivalence-principle sense) |
| scrambled | local records become indistinguishable from random ones | local thermalization within conserved sectors |
| colour count | number of full slots in colour P minus colour Q (Section 6) | staggered (sublattice) chirality charge |

## 4. The premises

| ID | Premise | Kind |
|---|---|---|
| P1 | The world is a lattice of N nodes; each node has its own degrees of freedom. | P |
| P2 | Nodes exchange information only with their nearest neighbours. | P |
| P3 | No bag of data is held away from a node's own degrees of freedom (no notebook layers, no hand-supplied fields or slopes, no mean-field summaries). | P |
| P4 | Known physics is never a reason to choose or change a rule. | P |

**In plain terms.** The universe is a grid of tiny bookkeepers. Each one only talks to the ones next to it, keeps
its own books and nothing else, and we are not allowed to rig the rules to copy textbook physics.

## 5. The construction, piece by piece

### 5.1 The table

| ID | Piece | Physics statement | Origin | Kind |
|---|---|---|---|---|
| C1 | Two slots per node | node Hilbert space C^2_R (x) C^2_L | Dirac QCA (Bisio, D'Ariano, Tosini, arXiv:1212.2839, as cited in the repo's Dirac contract); whether two slots is the smallest choice P1-P3 allow is open (Section 9) | O (possibly D) |
| C2 | Slots are plain yes/no switches | hard-core qubit lift; no Jordan–Wigner sign | Dirac QCA contract ("hard-core qubit lift") | O (untested choice) |
| C3 | Tick order | U = A B_mu: edge scatter B_mu on disjoint pairs (L_x, R_{x-1}), then on-site SWAP A on (R_x, L_x); orientation fixed by sign convention | Dirac QCA | O |
| C4 | Constant mu | edge one-excitation block [[-i mu, n],[n, -i mu]], n = sqrt(1-mu^2); lone clock law cos(clock) = n cos k | Dirac QCA; supplied by hand | O |
| C5 | Full slots are never created or destroyed | every gate conserves sum of n; U(1) symmetry | inherited with C2-C4 | O (inherited) |
| C6 | Edge both-full phase = +1 | edge gate leaves the doubly-full edge unchanged | default of the frozen Dirac code; never varied | O (default) |
| C7 | Constant theta | on-site SWAP gives the doubly-full node a phase e^{i theta} | added in route B (2026-11-24/25), user-approved, as the one node-local place where two coherences can affect each other | O (principle-bounded) |
| C8 | Ring of N nodes | periodic boundary | convenience for exact runs | D |
| C9 | Starting state | empty vacuum (QP-002); all-R full vacuum (EXPLORE-QP-3, fork a) | chosen to let pairs form (empty) and to let the background take a record (full) | O |

### 5.2 Notes on each piece

**C1–C4, C6 (the inherited Dirac node).** The repo's own Dirac contract states the purpose plainly: to recover the
"bounded single-particle 1+1D Dirac operational role". The derivation it follows uses homogeneity, locality,
unitarity, parity and time reversal, which are close to our premises, but the target was Dirac motion. By P4 that
makes C1–C4 outcome-chosen until shown otherwise. The open question (Section 9) is whether the same node and tick
follow from P1–P3 alone as the simplest choice. If yes, they become D and the Dirac behaviour becomes a result.

*In plain terms.* We borrowed the basic machine from published work whose goal was to reproduce a famous equation of
quantum physics. That is useful engineering, but it means the machine's good behaviour is partly built in. We now
have to show the machine is the simplest one our ground rules allow, or admit that it was imported.

**C2 and C6 (the both-full choices).** For one coherence, nothing depends on them. For two or more, they decide how
coherences affect each other. A different but equally natural choice (fermionic signs, phase -1) would give a
different many-coherence world. The pair held by the edge step alone (EXPLORE-QP-2: cos(clock) = (1-mu^2)/(1+mu^2)
cos K, not derived) exists only because of C6.

*In plain terms.* When two bookkeepers' slots are both full, the rule has to say what happens, and the original
machine made a quiet default choice. Some of our "held pairs" exist only because of that default.

**C7 (theta).** The one-coherence law leaves the doubly-full phase free; theta fills that freedom on the in-node swap.
It adds no new data and no new place to store anything, so it passes P3. But it was added so that coherences could
hold each other, so it is outcome-motivated.

*In plain terms.* There was one blank left in the rulebook, and we filled it with a dial. The dial is honest (it adds
no hidden storage), but we reached for it because we wanted particles to stick together.

**C9 (starting state).** Not a rule, but a choice. The full vacuum was chosen because an empty one cannot record
anything outside a pair.

*In plain terms.* We also chose what the world looks like at the start, and we chose it with a goal in mind.

### 5.3 Retired pieces (penalty-flagged, no longer used)

| ID | Piece (QP-001, 2026-11-24) | Why retired |
|---|---|---|
| X1 | Glue notebook chi with its own speed (0.985), spring and source G | a bag held off the nodes (P3) |
| X2 | Hand-set slope g = 4e-6 slowing clocks: gravity put in by hand | a supplied field (P3) and a known-physics target (P4) |
| X3 | Vacuum standing entry a0 | hand-supplied value (P3) |
| X4 | Mean-field, one-coherence treatment | a summary held off the nodes (P3) |

QP-001's result is kept in the record: the pocket's drift toward slow clocks missed by exactly the glue's share of
ticking.

*In plain terms.* An earlier attempt got particles and a gravity-like pull, but only by adding a hidden layer of
bookkeeping and a hand-drawn slope. We kept the result and threw out the machinery.

### 5.4 Knob-turning log (characterisation, flagged)

| When | What | Status |
|---|---|---|
| EXPLORE-QP-3 probe 3 | theta scan, theta/pi = 0..1, looking for a held object | done; all results reported; flagged as outcome-seeking |
| proposed, not done | "thinner background" (partial filling) to make objects hold | withdrawn pending this ledger |

### 5.5 The count

- Rule constants supplied by hand: **2** (mu, theta). One more is fixed and never varied: the edge both-full phase (+1).
- Structural choices: **5** (two slots; plain switches; tick order and orientation; conservation of full slots; ring).
- Starting states used: **2** (empty; all-R full).
- Outcome-chosen entries: **C1-C7 and C9**. Only C8 (the ring) is principle-derived at present.

**In plain terms.** Today the honest score is 2 dials, 5 design decisions and 2 starting pictures. Almost all of it
was chosen with a goal in mind. That is the number we now have to bring down, or justify piece by piece.

## 6. What the construction gives that we did not put in

These are consequences of C1-C9 that nobody asked for. Results marked *exploratory* are not frozen.

1. **Strict light cone.** A change at one node reaches exactly one more node per tick in each direction, and nothing
   outside that cone changes at all (EXPLORE-QP-3 probe 1, machine zero). This is a direct consequence of P2 and the
   two-layer tick, not a discovery, but it is the lattice's built-in speed limit.
   *Plain:* there is a top speed, and it comes from the grid itself.
2. **Exact reversibility.** Every run here returns to its start when run backwards (fidelity 1.0).
   *Plain:* nothing is ever truly erased.
3. **Held pairs in the empty vacuum** (QP-002, frozen and passed): held at all 495 tested settings; exact law
   cos(clock) = (1-mu^2) cos K - mu^2 cos(theta) to max error 1.3e-9; size grows as 1/(2 mu sin(theta/2)) nodes in
   the smooth limit (fit, not derived). At theta = pi/2 the law reads cos(clock) = n^2 cos K, the lone-coherence law with
   n^2 in place of n (follows from the frozen law). Depends on C7 (outcome-chosen).
   *Plain:* two coherences can lock together and move as one, and the locked pair ticks by the same kind of law as a
   single one. But this needed the dial we added.
4. **A second conserved count with a handedness** (EXPLORE-QP-3; exact, by hand and by code). Colour the slots:
   P = {R at even nodes, L at odd nodes}, Q = the rest (even N). Every edge exchange stays within one colour, and the
   in-node swap trades P and Q. So the colour count C = N_P - N_Q obeys C(t+1) = -C(t): conserved up to a flip each
   tick, at every mu and theta. The mirror (R at node x <-> L at node -x) maps the rule onto itself (checked, error
   0.0 on N = 6-12) and sends P onto Q, so C is **mirror-odd**: it changes sign under reflection, as a handedness
   does. Only two linear conserved counts exist (total and C; search over N = 6-10).
   *Plain:* without being asked, the grid keeps track of a left-versus-right count that flips when you look at the
   world in a mirror. That is the first thing here that smells like chirality and was not put in on purpose.
5. **The full vacuum scrambles** (EXPLORE-QP-3, exploratory, N <= 12). At generic theta, any local change spreads
   and becomes indistinguishable from random, except for the conserved counts, which end up shared evenly (~1/N per
   node). One extra full slot is never held. At theta = 0 and pi, mixing is slower and a ring-wide node-alternating
   wave remains.
   *Plain:* a busy background remembers that something happened, but forgets where.

## 7. Feature scorecard (as of this ledger)

| Feature | Status | Evidence | Honest note |
|---|---|---|---|
| Quantum behaviour | **built in** | unitary, reversible QCA (C1-C5) | assumed through the borrowed machine, not derived |
| Relativity-like behaviour | **partly** | strict light cone; lone coherence follows the Dirac clock law at long wavelength | the clock law is the borrowed machine's design target |
| Chirality | **partly built in, partly emergent** | R/L slots (built in); mirror-odd colour count (emergent, item 6.4) | the emergent count needs even N and its meaning is not explored |
| Angular momentum | **cannot be tested** | 1D has no rotations | needs 2D or 3D; how the node extends into 2D is a new ledger entry and must be derived, not chosen to give spin |
| Gravity (drift toward slow clocks) | **fails its precondition** | empty vacuum keeps no record; full vacuum keeps only evenly spread counts (no fall-off with distance) | QP-001's version used a hand-drawn slope (retired) |
| Emergent clock (turn rate from trapped motion) | **partial** | pair clock follows from binding (item 6.3) | the lone clock is still set by hand (mu) |

**In plain terms.** We have a quantum, speed-limited world with a hint of handedness that appeared by itself. We do
not yet have rotation (the world is a line), and we do not have gravity: no version of this rule so far leaves a
trail around an object that something else could slide down.

## 8. Working rules from here on

1. **Ledger first.** No new piece is used before it has a row here with its origin and kind.
2. **Reasons are principles, not outcomes.** Outcome-chosen pieces may be used only if flagged and counted.
3. **Feature tests are fixed in advance.** Each target feature gets a pass/fail stated before any run, is run on a
   frozen rule over the whole range of its constants, and is reported as a score, not a best setting.
4. **No patch rules.** A failed feature sends us back to the premises and to this ledger, not to a rule aimed at the
   failure.
5. **Scans are characterisation only.** A constant scan is declared as such in advance and all results are reported.
6. **Known physics names what we see and checks it. It never chooses a rule.**
7. **Corrections stay public.** Retired pieces, wrong statements and their fixes stay in the record.
8. **Prior-art gate before any paper.**

## 9. Open decision (the user's)

Re-derive the node and tick from P1-P3 alone: write down every free choice the premises leave open (number of slots,
what counts as one exchange, order of operations, the doubly-full phases, the constants) and count them. Outcomes:
(a) the borrowed Dirac node is the simplest choice, so C1-C4 move from O to D and the Dirac clock law becomes a
result; or (b) it is not, and we learn exactly how much of route B was imported.

**In plain terms.** Before building anything else, we check whether the machine we borrowed is the one our own ground
rules would have produced anyway. If it is, our results stand on firmer ground. If it is not, better we find out than
a referee.

## 10. Sources in this repo

docs/ICP_QUANTUM_DIRAC_SYMMETRY_QCA_CONTRACT.md (origin of C1-C6); docs/ICP_QP_001_CONTRACT.md (X1-X4);
docs/ICP_QP_002_CONTRACT.md and output/quantum_gold/QP-002/RESULTS.md (item 6.3);
output/minimal_realization/EXPLORE-QP-2/NOTES.md (route B, theta, edge-held pair);
output/minimal_realization/EXPLORE-QP-3/NOTES.md (items 6.1, 6.2, 6.4, 6.5; probe 3; method audit);
docs/HANDOFF_FILLED_VACUUM_2026-11-25.md (fork a); README.md ("declared and counted").
