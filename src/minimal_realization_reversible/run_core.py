"""Run MIR-REVERSIBLE-CORE-001 (refuses unless frozen tag and seal match)."""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.core import run, track, SEEDS
TAG = 'mir-reversible-core-001-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_CORE_CONTRACT.md', 'src/minimal_realization_reversible/engine.py',
          'src/minimal_realization_reversible/core.py', 'src/minimal_realization_reversible/run_core.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/core_seal.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}

def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    rows = []
    for w in range(256):
        for s in SEEDS:
            r = track(run(w, s))
            if r:
                c = track(run(w, s, n=384))
                r['control_C384_agrees'] = c == r
            rows.append(dict(wolfram=w, n_l=bin(w).count('1'), seed=s, core=r))
    hit = [x for x in rows if x['core'] and x['core']['control_C384_agrees']]
    prim = [x for x in hit if x['seed'] == '1']
    key = lambda x: (x['n_l'], x['core']['t0'], x['wolfram'], len(x['seed']), x['seed'])
    summ = dict(primary_pass=len(prim), primary_wolfram=sorted({x['wolfram'] for x in prim}),
                secondary_pass_rules=len({x['wolfram'] for x in hit}),
                secondary_pairs=len(hit),
                kinds={k: sum(x['core']['kind'] == k for x in hit) for k in ['isolated_object', 'core_with_radiation']},
                primary_winner=min(prim, key=key) if prim else None,
                secondary_winner=min(hit, key=key) if hit else None)
    dst = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-CORE-001/results.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(dict(summary=summ, candidates=rows), indent=1) + '\n')
    print(json.dumps(summ))

if __name__ == '__main__':
    main()
