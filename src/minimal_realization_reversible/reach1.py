"""MIR-REVERSIBLE-REACH-001: does one background-held order record condition a succession of later encounters?
Cases: ORDER-003 cases with timing_ok and >= 1 read-back (588), plus its 100 RCA54 control cases. Worlds AB / BA as in
ORDER-002 plus K = 6 fresh travellers g_1..g_K in slots 2..K+1 (slot s = slot 1 translated by s*g); g_i = reader-side
species sorted by id, cycled. For each i a separate world holds travellers 1..i; readout at (i+1) Delta + 1600.
increment_i = mover-species multiset change from world(1..i-1) to world(1..i). Traveller i is AFFECTED iff its increment
differs between AB and BA. reach = number of affected travellers. bg_i = background words differ between AB and BA.
See docs/ICP_MIR_REVERSIBLE_REACH_001_CONTRACT.md."""
import hashlib, json, os, subprocess, sys
os.environ.setdefault('OMP_NUM_THREADS', '1')
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'src'))
import minimal_realization_reversible.order2 as O2
TAG = 'mir-reversible-reach-001-v0.1-frozen'
SEALED = ['docs/ICP_MIR_REVERSIBLE_REACH_001_CONTRACT.md'] + ['src/minimal_realization_reversible/' + f for f in ('reach1.py', 'order2.py', 'order3.py', 'species1.py', 'inventory1.py', 'collide2.py', 'vacuum_collide.py')]
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/reach1_seal.json'; OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-REACH-001'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
K = 6


def one(R, x, by, readers):
    X, al, be = by[x['X']], by[x['al']], by[x['be']]; tau, d, De, side = x['tauX'], x['d'], x['Delta'], x['side']
    sh = int(X['v'] * De); tg = (X, tau, O2.X0)
    slot = lambda o, k: (o, o['phase'] + k * De, O2.X0 - side * d + k * sh)
    gs = [readers[i % len(readers)] for i in range(K)]
    base = {'AB': [tg, slot(al, 0), slot(be, 1)], 'BA': [tg, slot(be, 0), slot(al, 1)]}
    M = {}; B = {}
    try:
        for nm, objs in base.items():
            M[nm] = []; B[nm] = []
            for i in range(K + 1):
                T = (i + 1) * De + 1600; w = objs + [slot(gs[k], k + 2) for k in range(i)]
                mv, bg, _ = O2.readout(R, *O2.run(R, *O2.world(R, w), T), T); M[nm].append(Counter(mv)); B[nm].append(bg)
    except ValueError as e:
        return dict(valid=False, err=str(e))
    inc = lambda nm, i: (tuple(sorted((M[nm][i] - M[nm][i - 1]).items())), tuple(sorted((M[nm][i - 1] - M[nm][i]).items())))
    aff = [inc('AB', i) != inc('BA', i) for i in range(1, K + 1)]
    bgd = [B['AB'][i] != B['BA'][i] for i in range(K + 1)]
    return dict(valid=True, affected=aff, reach=sum(aff), bg_diff=bgd)


def job(a):
    lab, w, species, cases = a; R = O2.Rule(w, species); by = {o['id']: o for o in R.sp}; out = []
    for x in cases:
        rd = sorted([o for o in R.sp if o['v'] * x['side'] > 0], key=lambda o: o['id']); out.append(one(R, x, by, rd))
    return dict(lab=lab, rows=out)


def load():
    S = {f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}": r for r in json.load(open(OM / 'MIR-REVERSIBLE-SPECIES-001/results.json'))['rules']}
    by = {}
    for f in sorted((OM / 'MIR-REVERSIBLE-ORDER-003/jobs').glob('*.json')):
        r = json.loads(f.read_text()); lab = r['lab']
        for x in r['rows']:
            if not x.get('valid'): continue
            if lab == '250c' or (x['timing_ok'] and any(g['readback'] for g in x['R'])): by.setdefault(lab, []).append(x)
    J = []
    for lab, cs in by.items():
        w, sp = (O2.CONTROL, O2.control_species()) if lab == '250c' else (S[lab]['wolfram'], S[lab]['species'])
        for i in range(0, len(cs), 25): J.append((lab, w, sp, cs[i:i + 25]))
    return J


def main():
    if sys.argv[1:] == ['seal']: SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    J = load()
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
    T = {}
    for lab, rs in rows.items():
        V = [x for x in rs if x['valid']]; n = len(V)
        T[lab] = dict(n=len(rs), valid=n, mean_reach=sum(x['reach'] for x in V) / n if n else None,
                      reach_hist=dict(Counter(x['reach'] for x in V)), affected_by_i=[sum(x['affected'][i] for x in V) for i in range(K)],
                      bg_by_i=[sum(x['bg_diff'][i] for x in V) for i in range(K + 1)], bg_end=sum(x['bg_diff'][K] for x in V) / n if n else None)
    E = [l for l in T if l != '250c']; c = T.get('250c', {})
    S = dict(V_C=c.get('valid', 0) >= 50 and c.get('mean_reach') == 0, valid_frac=min(T[l]['valid'] / T[l]['n'] for l in T))
    S['valid'] = S['V_C'] and S['valid_frac'] >= 0.8
    f = lambda ok: 'invalid' if not S['valid'] else 'supported' if ok else 'not_supported'
    S['H_R_pass'] = [l for l in E if T[l]['mean_reach'] > 1]; S['H_P_pass'] = [l for l in E if T[l]['bg_end'] >= 0.25]
    S['H_R'] = f(len(S['H_R_pass']) >= 4); S['H_P'] = f(len(S['H_P_pass']) >= 4); S['table'] = T
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S), indent=1) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V_C', 'valid_frac', 'H_R', 'H_P', 'H_R_pass', 'H_P_pass')}))


if __name__ == '__main__': main()
