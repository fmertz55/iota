"""Run MIR-REVERSIBLE-001 (refuses unless frozen tag and seal match)."""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.engine import evaluate
TAG = 'mir-reversible-001-v0.1-frozen'
SEALED = ['docs/ICP_MINIMAL_INFORMATIONAL_REALIZATION_REVERSIBLE_CONTRACT.md',
          'src/minimal_realization_reversible/engine.py',
          'src/minimal_realization_reversible/run.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/seal.json'

def digests():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}

def signed(a, n):
    return a if a <= n // 2 else a - n

def main():
    if sys.argv[1:] == ['seal']:
        SEAL.parent.mkdir(parents=True, exist_ok=True)
        SEAL.write_text(json.dumps(digests(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == digests(), 'seal mismatch'
    rows = []
    for w in range(256):
        r = evaluate(w, 64, 2)
        rec = dict(wolfram=w, n_l=bin(w).count('1'), **{k: v for k, v in r.items()})
        p = r['first_complete_pass']
        rec['localized'] = False
        if p:
            ctl = {n: evaluate(w, n, 2, horizon=29)['first_complete_pass'] for n in (96, 128)}
            rec['controls'] = ctl
            rec['localized'] = all(c and c[0] == p[0] and signed(c[1], n) == signed(p[1], 64)
                                   for n, c in ctl.items())
        rows.append(rec)
    loc = sorted((r for r in rows if r['localized']),
                 key=lambda r: (r['n_l'], r['first_complete_pass'][0], r['wolfram']))
    stage = {k: sum(r[k] is not None for r in rows) for k in
             ['first_role', 'first_successor', 'first_intervention_eligible', 'first_complete_pass']}
    out = dict(search_id='MIR-REVERSIBLE-001', tag=TAG, stage_counts=stage,
               localized_pass_count=len(loc), winner=loc[0] if loc else None,
               localized_wolfram=[r['wolfram'] for r in loc], candidates=rows)
    dst = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-001/results.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps({k: out[k] for k in ['stage_counts', 'localized_pass_count', 'localized_wolfram']}))
    if loc: print('winner', {k: loc[0][k] for k in ['wolfram', 'n_l', 'first_complete_pass']})

if __name__ == '__main__':
    main()
