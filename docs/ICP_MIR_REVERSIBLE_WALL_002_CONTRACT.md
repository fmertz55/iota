# MIR-REVERSIBLE-WALL-002: what do the walls' bits name: which species, the contact phase, or the age? (v0.1)

Status: **frozen at tag `mir-reversible-wall-002-v0.1-frozen`**. 2026-11-09. Code: `wall2.py` (imports the frozen
`wall1.py`; `runs()` is a verbatim copy of `wall1.job` up to the per-run lists, plus the offset). Parent: WALL-001
(valid; H_1 3/7, H_T 3/7, H_I 0/7). Handoff 2026-11-09e, open direction 2, chosen over the two-axis run.

## Question
WALL-001 read its ledger as "a stationary wall remembers *where*; *when* needs a moving edge". In its ensemble, though,
place and time are locked. Inside one contact class c = (species pair sp, contact phase phi = off mod Delta_sp), the
inputs are exact space-time translates (PHASE-001 V1): translate k makes contact k*tau later and v_R*k*tau to the right
(tau = lcm(p_R, p_L, p_vac)). So the static wall's "placement" is equally contact-time information. The question here
is what the bits of the record and of the edge-only part actually name: **which species collided (sp), the contact
phase (phi), or the age (k)?**

## Lemma (derived before running; checked as V_L)
By exact covariance (WALL-001 V2) and age-aligned erasure, a translate k of class c, observed at the common tick tw,
has for every tracked wall of speed u: sub_k = sub_0, clock_k = (clock_0 + k*tau) mod P, place_k = place_0 +
k*tau*(v_R - u). Consequences:
(a) Inside a class the static wall's place pins k (v_R*tau != 0), so with one static wall in every shadow run,
J_k = I(k; walls | O, M, W, sp, phi) = 0 exactly: **the edges hold no age beyond the static wall inside a class.**
(b) In a gate-only rule (PHASE-001: one phase class per species pair leaves residue: 26s, 82s), phi is fixed by
(sp, residue present), so J_phi = 0 too: whatever only the edges hold there is species-pair information.
(c) (Not tested; stated for the write-up.) In an ensemble that also translates both carriers by a, the static wall's
place = contact place + a class constant, and it holds age only as k*tau mod P (<= log2 P bits), whereas an edge's
distance from the static wall holds age without bound. Running that ensemble would mainly retest ring invariance.

## Design
Same inputs, erasure, tracking, descriptors and keys (O, M, W = static wall state, A = all wall states, place = static
wall placement) as WALL-001, all 28 pairs. Labels per input: sp, off, phi, k = (off - off0(sp, phi)) / Delta_sp.
Readouts (exact; H = empirical entropy over the uniform distinct inputs):
- Record channels: c_sp = H(sp | O, M); c_off = H(off | O, M, sp) = c_phi + c_k, with c_phi = H(phi | O, M, sp) and
  c_k = H(k | O, M, sp, phi); other order: c_off_first = H(off | O, M), c_sp_given_off.
- Placement split: pl = I(in; place | O, M) = pl_off + pl_sp_given_off = pl_sp + pl_off_given_sp.
- Edge-only part: R_E = r_W - r_allwalls = I(in; A | O, M, W) = J_sp + J_phi + J_k (J_sp = I(sp; A | O, M, W),
  J_phi = I(phi; A | O, M, W, sp), J_k = I(k; A | O, M, W, sp, phi)); Q_off = I(off; A | O, M, W, sp) = J_phi + J_k;
  Q_sp = I(sp; A | O, M, W, off); E_off_first = I(off; A | O, M, W).
- W_age = I(k; W | O, M, sp, phi).

## Validity controls (frozen; invalid if any fails)
- V0: n, rec, r_W, r_place, r_allwalls equal WALL-001's stored values (|diff| < 1e-12), all 28 pairs.
- V1: the WALL-001 eligible set equals 147 201 22s 26s 58s 82s 114s.
- V_L (lemma): in every eligible pair, every input satisfies the translate law against the lowest-offset member of its
  class (same run label / wall keys, sub, P, speed; clock and place as above).
- V_id: every chain-rule identity above holds to 1e-9 in all 28 pairs.
- V_track: no lost, unclosed, speed-mismatched or edge-hit wall in eligible pairs.

## Hypotheses (frozen; tolerance 1e-9; 91 exposed and excluded)
- **H_C0 (the record names no contact, only species)**: c_off < 1e-9, i.e. given the outgoing ledger and movers, the
  offset is fixed once the species pair is known. Eligible pairs (7); threshold >= 4. Prior: uncertain, leaning not
  supported (outgoing positions at a fixed tick encode the offset, but phase-dependent displacements can alias;
  exposed 91 has c_off = 1.125).
- **H_S (what only the edges hold is which-species)**: Q_off < 1e-9 in both of 58s and 114s, the eligible pairs with an
  edge-only part and more than one phase class. Prior: uncertain.
- Predictions (lemma; reported, not verdicts): J_k < 1e-9 in all 7; Q_off < 1e-9 in 26s and 82s. A failure with V_L
  passing would mean a code error in the ledger and is reported as such.
- Descriptive: all channel numbers; W_age (lemma: equals c_k).

## Exposure (before freezing; disclosed)
- Stored WALL-001 values for all pairs (rec, r_W, r_place, r_allwalls, eligible set, which pairs have an edge-only
  part: 26s 82s 58s 114s) and PHASE-001's H_C and gate classes.
- Calibration, full output, rule 91 (exposed): rec 1.5 = c_sp 0.375 + c_off 1.125 (c_phi 0.125, c_k 1.0); pl 0.75
  (pl_off 0.625, pl_sp_given_off 0.125); R_E 0.625 = J_sp 0 + J_phi 0.125 + J_k 0.5 (91's J_k > 0 because half its
  shadow runs have no static wall); Q_sp 0; W_age 0.5. V_L 242 checks, 0 failures.
- Smoke on 26, 58 and null 5 printed validity only (V_L 248 checks each, 0 failures; covariance controls pass; no lost,
  edge-hit or unclosed walls; identities hold). No channel value was printed for any unexposed pair.

## Limits
Channels are labels of one 1-parameter input family per species pair; "age" here is k, defined only inside a class.
The chain-rule splits are order-dependent; both orders are reported where it matters. H_S rests on two pairs.
The record is conditioned on O read at a fixed absolute tick, so contact time partly lives in O itself.

## Prior art (do not claim)
Space-time translation covariance of CA defects is standard. Candidate contribution: an exact ledger saying which
collision channel (species, phase, age) each bit of a reversible collision record names, and where it is stored.
