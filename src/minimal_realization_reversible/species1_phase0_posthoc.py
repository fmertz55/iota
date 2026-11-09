"""POST HOC (not part of the frozen SPECIES-001 protocol). The frozen readout yield_phase0 counts species whose
minimum-width representative was found at vacuum phase 0; the contract described it as "the same curve at phase 0
only". This script computes the described quantity: species reachable from phase-0 seeds, by smallest phase-0 seed
width, with the frozen species1 functions unchanged. Output: MIR-REVERSIBLE-SPECIES-001/posthoc_phase0_yield.json."""
import json, sys
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction as Fr
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'src'))
import minimal_realization_reversible.species1 as SP
import minimal_realization_reversible.shadow6 as S6
from minimal_realization_reversible.vacuum_collide import table


def job(j):
    w, role = j[0], j[4]; tab = table(w); active = role.endswith('active'); best = {}; orb = {}
    for s, d, pat in SP.accept(tab, 0):
        if active and not (2 < abs(d) < 116): continue
        if pat not in orb: orb[pat] = SP.orbit_of(tab, pat, SP.TS)
        r = orb[pat]
        if r is None or r[1] == 0 or abs(Fr(r[1], r[0])) < SP.C2.VMIN: continue
        i = SP.sid(r[2]); best[i] = min(best.get(i, 99), SP.seed_width(s))
    return f"{w}{'s' if role.endswith('silent') else ''}", {wd: sum(b <= wd for b in best.values()) for wd in SP.WIDTHS}


if __name__ == '__main__':
    with ProcessPoolExecutor(4) as ex: rows = dict(ex.map(job, S6.pairs()))
    (SP.OUT / 'posthoc_phase0_yield.json').write_text(json.dumps(rows, indent=1) + '\n')
    for k, v in rows.items(): print(k, [v[wd] for wd in range(4, 9)])
