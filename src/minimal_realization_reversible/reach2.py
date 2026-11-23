"""MIR-REVERSIBLE-REACH-002: is REACH-001's reach carried by the background alone, or by earlier travellers' products?
Same cases, travellers and slots as REACH-001 (reach1.load, K = 6). FRESH world i = AB (or BA) + traveller i alone in
slot i + 1 (no earlier travellers, hence no products). Readout at (i+1) Delta + 1600, also in the base world (no
traveller). increment_i = mover-species change base -> fresh. Fresh traveller i is AFFECTED iff its increment differs
between AB and BA. fresh_reach = number affected. See docs/ICP_MIR_REVERSIBLE_REACH_002_CONTRACT.md."""
import hashlib, json, os, subprocess, sys
os.environ.setdefault('OMP_NUM_THREADS', '1')
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
ROOT = Path(os.environ.get('IOTA_ROOT', Path(__file__).resolve().parents[2])); sys.path.insert(0, str(ROOT / 'src'))
import minimal_realization_reversible.order2 as O2
import minimal_realization_reversible.reach1 as R1
TAG = 'mir-reversible-reach-002-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_REACH_002_CONTRACT.md'] + ['src/minimal_realization_reversible/' + f for f in ('reach2.py', 'reach1.py', 'order2.py', 'species1.py', 'inventory1.py', 'collide2.py', 'vacuum_collide.py')]
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/reach2_seal.json'; OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-REACH-002'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
K = R1.K


def one(R, x, by, readers):
    X, al, be = by[x['X']], by[x['al']], by[x['be']]; tau, d, De, side = x['tauX'], x['d'], x['Delta'], x['side']
    sh = int(X['v'] * De); tg = (X, tau, O2.X0)
    slot = lambda o, k: (o, o['phase'] + k * De, O2.X0 - side * d + k * sh)
    gs = [readers[i % len(readers)] for i in range(K)]
    base = {'AB': [tg, slot(al, 0), slot(be, 1)], 'BA': [tg, slot(be, 0), slot(al, 1)]}
    TT = [(i + 1) * De + 1600 for i in range(1, K + 1)]
    inc = {}
    try:
        for nm, objs in base.items():
            p, c = O2.world(R, objs); t = 0; B = []
            for T in TT:
                p, c = O2.run(R, p, c, T - t); t = T; B.append(Counter(O2.readout(R, p, c, T)[0]))
            inc[nm] = []
            for i in range(1, K + 1):
                T = TT[i - 1]; F = Counter(O2.readout(R, *O2.run(R, *O2.world(R, objs + [slot(gs[i - 1], i + 1)]), T), T)[0])
                inc[nm].append((tuple(sorted((F - B[i - 1]).items())), tuple(sorted((B[i - 1] - F).items()))))
    except ValueError as e:
        return dict(valid=False, err=str(e))
    aff = [a != b for a, b in zip(inc['AB'], inc['BA'])]
    return dict(valid=True, affected=aff, fresh_reach=sum(aff))


def job(a):
    lab, w, species, cases = a; R = O2.Rule(w, species); by = {o['id']: o for o in R.sp}; out = []
    for x in cases:
        rd = sorted([o for o in R.sp if o['v'] * x['side'] > 0], key=lambda o: o['id']); out.append(one(R, x, by, rd))
    return dict(lab=lab, rows=out)


def main():
    if sys.argv[1:] == ['digest']: print(json.dumps(dig(), indent=1, sort_keys=True)); return
    J = R1.load()
    if sys.argv[1:] == ['check']:
        r = job((J[0][0], J[0][1], J[0][2], J[0][3][:1])); print(J[0][0], len(J), r['rows'][0].get('valid')); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    CK = OUT / 'jobs'; CK.mkdir(parents=True, exist_ok=True); ck = lambda j, i: CK / f'{j[0]}_{i}.json'
    todo = [(i, j) for i, j in enumerate(J) if not ck(j, i).exists()]
    with ProcessPoolExecutor(4) as ex:
        for (i, j), r in zip(todo, ex.map(job, [j for _, j in todo])): ck(j, i).write_text(json.dumps(r))
    rows = {}
    for i, j in enumerate(J): rows.setdefault(j[0], []).extend(json.loads(ck(j, i).read_text())['rows'])
    seq = json.loads((OM / 'MIR-REVERSIBLE-REACH-001/results.json').read_text())['summary']['table']
    T = {}
    for lab, rs in rows.items():
        V = [x for x in rs if x['valid']]; n = len(V)
        T[lab] = dict(n=len(rs), valid=n, mean_fresh=sum(x['fresh_reach'] for x in V) / n if n else None,
                      mean_seq=seq[lab]['mean_reach'], affected_by_i=[sum(x['affected'][i] for x in V) for i in range(K)])
    E = [l for l in T if l != '250c']; c = T.get('250c', {})
    S = dict(V_C=c.get('valid', 0) >= 50 and c.get('mean_fresh') == 0, valid_frac=min(T[l]['valid'] / T[l]['n'] for l in T))
    S['valid'] = S['V_C'] and S['valid_frac'] >= 0.8
    f = lambda ok: 'invalid' if not S['valid'] else 'supported' if ok else 'not_supported'
    S['H_D_pass'] = [l for l in E if T[l]['mean_fresh'] > 1]
    S['H_E_pass'] = [l for l in E if T[l]['mean_fresh'] >= 0.8 * T[l]['mean_seq']]
    S['H_D'] = f(len(S['H_D_pass']) >= 4); S['H_E'] = f(len(S['H_E_pass']) >= 4); S['table'] = T
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S), indent=1) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V_C', 'valid_frac', 'H_D', 'H_E', 'H_D_pass', 'H_E_pass')}))


if __name__ == '__main__': main()
