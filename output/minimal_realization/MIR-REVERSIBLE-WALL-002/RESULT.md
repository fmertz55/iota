# MIR-REVERSIBLE-WALL-002: result (2026-11-09)

Frozen tag mir-reversible-wall-002-v0.1-frozen (38bbd89). Data: results.json, run.log. Run: 4 min 43 s, 4 workers.

## Frozen verdict: VALID. H_C0 not supported (0/7). H_S not supported (0/2).
- V0 (28/28 equal WALL-001), V1 (eligible set), V_L (translate lemma: 1728 checks, 0 failures), V_id, V_track pass.
- Lemma predictions hold: J_k = 0 in all 7 (the edges hold no age beyond the static wall inside a contact class);
  Q_off = 0 in 26s and 82s (gate-only: what only the edges hold there is species-pair information).
- H_C0 (record names no contact): c_off = 0.75-4.875 bits > 0 in all 7. H_S: 58s and 114s keep Q_off = 0.242 bit
  (contact phase) in the edges.

## Ledger (bits; exact; sp = species pair, phi = contact phase, k = translate = locked contact place+time)
| rule | rec | species c_sp | phase c_phi | age c_k | placement: contact given sp | placement: species | edge-only R_E | of which species J_sp | phase J_phi | age J_k |
|---|---|---|---|---|---|---|---|---|---|---|
| 147 | 3.5 | 1.0 | 0 | 2.5 | 2.5 | 0.066 | 0 | 0 | 0 | 0 |
| 201 | 2.469 | 0.594 | 0 | 1.875 | 1.875 | 0.022 | 0 | 0 | 0 | 0 |
| 22s | 1.047 | 0.297 | 0 | 0.75 | 0.75 | 0.172 | 0 | 0 | 0 | 0 |
| 26s | 2.469 | 0.594 | 0 | 1.875 | 1.875 | 0.011 | 0.584 | 0.584 | 0 | 0 |
| 58s | 6.314 | 1.439 | 0.5 | 4.375 | 4.391 | 0.027 | 1.413 | 1.171 | 0.242 | 0 |
| 82s | 2.469 | 0.594 | 0 | 1.875 | 1.875 | 0.011 | 0.584 | 0.584 | 0 | 0 |
| 114s | 5.689 | 1.439 | 0.5 | 3.75 | 3.766 | 0.027 | 1.413 | 1.171 | 0.242 | 0 |
"placement: contact given sp" = pl_off_given_sp = I(off; place | O, M, sp); "placement: species" = pl_sp = I(sp; place |
O, M). W_age = I(k; W | O, M, sp, phi) = c_k in all 7 (the static wall holds all of the record's age inside a class).
Other chain order (offset first): edges hold E_off_first = 0.334 (26s, 82s), 0.913 (58s, 114s) bit of offset and
Q_sp = 0.25 / 0.5 bit of species given the offset; 0 elsewhere.

## Reading
Split by channel, the record is mostly contact coordinate (c_off: 71-77%) with a species part (c_sp: 23-29%).
The static wall's placement carries the contact coordinate almost exclusively (it names the species by position only
0.01-0.17 bit). Inside a contact class it holds all the age the record has (W_age = c_k). What only the
moving outer walls hold is *which species pair collided* (all of it in 26s, 82s; 1.17 of 1.41 bit in 58s, 114s) plus
0.242 bit of contact phase in 58s and 114s, and never age. This corrects the 11-09e reading "when needs a moving edge":
in this ensemble the static wall holds *when-and-where* (one locked coordinate), and the edges hold *which*.
A separate place/age split is not in this ensemble's data; it follows from the lemma (contract, (c)): with place
varied independently, a static wall holds age only as k*tau mod P (<= log2 P: 1 bit for 26s/82s, 1.58 for 58s/114s),
while an edge's distance from the wall holds age without bound. That statement is derived, not measured.

## Lay version
After a collision, the fixed seam remembers which collision happened in the sense of where-and-when it happened. The
expanding edges add only who collided (and, in two rules, a little about the step the travellers were in). In this
setup "where" and "when" cannot be told apart. Symmetry says a fixed seam could only keep the time modulo its own
short beat, while the edges could keep it in full.
