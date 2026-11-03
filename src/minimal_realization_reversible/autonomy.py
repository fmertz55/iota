"""MIR-REVERSIBLE-AUTONOMY-001: cut each frozen core out and re-run it alone."""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from minimal_realization_reversible.engine import step
from minimal_realization_reversible.core import clusters
N, K, W, M = 256, 64, 8, 2
TAG = 'mir-reversible-autonomy-001-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_AUTONOMY_CONTRACT.md', 'src/minimal_realization_reversible/engine.py',
          'src/minimal_realization_reversible/core.py', 'src/minimal_realization_reversible/autonomy.py']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/autonomy_seal.json'
PARENT = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-CORE-001/results.json'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}


def pairs(w, seed, layers):
    p, c = [0] * N, [0] * N
    for k, ch in enumerate(seed): c[k] = int(ch)
    q, r = [0] * N, [0] * N
    for _ in range(layers):
        p, c = step(w, p, c, 2); q, r = step(w, q, r, 2)
    return (p, c), (q, r)


def follow(w, sp, cp, start):
    """Track from cluster overlapping `start` for K ticks; return (ok, drift, isolated)."""
    (p, c), (q, r) = sp, cp
    cl = clusters([a ^ b for a, b in zip(c, r)])
    cur = next((e for e in cl if e[1] - e[0] + 1 <= W and e[0] <= start[1] and e[1] >= start[0]), None)
    if cur is None: return False, None, None
    s0, iso = cur[0], len(cl) == 1
    for _ in range(K):
        p, c = step(w, p, c, 2); q, r = step(w, q, r, 2)
        cl = clusters([a ^ b for a, b in zip(c, r)])
        iso = iso and len(cl) == 1
        nxt = [e for e in cl if e[1] - e[0] + 1 <= W and e[0] <= cur[1] + 1 and e[1] >= cur[0] - 1]
        if not nxt: return False, None, None
        cur = nxt[0]
    return True, cur[0] - s0, iso


def test(w, seed, core):
    ts = core['t0'] + K                        # mature core = end of the frozen track
    (p, c), (q, r) = pairs(w, seed, ts)
    lo, hi = core['end']
    win = {i % N for i in range(lo - M, hi + M + 1)}
    tp = [p[i] if i in win else q[i] for i in range(N)]   # transplant: core window, both layers,
    tc = [c[i] if i in win else r[i] for i in range(N)]   # into the matched vacuum
    ok, drift, iso = follow(w, (tp, tc), (q, r), (lo, hi))
    same = ok and drift is not None and (drift == 0 == core['drift'] or drift * core['drift'] > 0) \
        and abs(drift - core['drift']) <= 8
    return dict(autonomous=ok, drift_alone=drift, isolated_alone=iso, same_object=bool(same))


def cls(core):
    v = abs(core['drift'])
    return 'light' if v == 64 else ('still' if v <= 2 else 'sub-light')


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    hits = [x for x in json.load(open(PARENT))['candidates'] if x['core'] and x['core']['control_C384_agrees']]
    rows = [dict(wolfram=x['wolfram'], n_l=x['n_l'], seed=x['seed'], cls=cls(x['core']),
                 drift_orig=x['core']['drift'], **test(x['wolfram'], x['seed'], x['core'])) for x in hits]
    summ = {}
    for k in ['light', 'sub-light', 'still']:
        g = [r for r in rows if r['cls'] == k]
        summ[k] = dict(n=len(g), autonomous=sum(r['autonomous'] for r in g),
                       same_object=sum(r['same_object'] for r in g))
    cand = sorted((r for r in rows if r['cls'] != 'light' and r['same_object']),
                  key=lambda r: (r['n_l'], r['wolfram'], len(r['seed']), r['seed']))
    summ['candidates'] = [(r['wolfram'], r['seed'], r['drift_orig'], r['drift_alone'], r['isolated_alone']) for r in cand]
    dst = ROOT / 'output/minimal_realization/MIR-REVERSIBLE-AUTONOMY-001/results.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(dict(summary=summ, rows=rows), indent=1) + '\n')
    print(json.dumps(summ))

if __name__ == '__main__':
    main()
