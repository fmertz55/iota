"""MIR-REVERSIBLE-ORDER-003: is the order held ONLY by the background (timing included), and can a later traveller read
it back out?

Cases: every ORDER-002 touched, valid, persistent background-only case (7 eligible pairs), re-run with the frozen
order2.py machinery (same world, same readouts).
Part T (timing): at each readout Delta + RT,
  target-direction movers: sorted (species, position) equal in AB and BA;
  reader-direction movers: assessable only if they are exactly {alpha, beta} (one each) in both orders; then each
  reader's displacement from its own free flight (same slot) must be equal in AB and BA.
  timing_ok = both hold at all readouts (no reader-direction movers in either order also counts as assessable).
Part R (read-back): third reader gamma (every reader-side species) in slot 3 = slot 1 translated by 2g. Read-back in
(case, gamma) iff gamma touched in both orders and the mover species multiset differs between AB+gamma and BA+gamma
at every readout 2 Delta + RT.
See docs/ICP_MIR_REVERSIBLE_ORDER_003_CONTRACT.md.
"""
import hashlib, json, os, subprocess, sys, time
os.environ.setdefault('OMP_NUM_THREADS', '1')
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import minimal_realization_reversible.order2 as O2
TAG = 'mir-reversible-order-003-v0.1-frozen'
P_ = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_ORDER_003_CONTRACT.md'] + [P_ + f for f in ('order3.py', 'order2.py', 'species1.py',
          'inventory1.py', 'collide2.py', 'vacuum_collide.py')] + ['output/minimal_realization/MIR-REVERSIBLE-ORDER-002/RESULT.md']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/order3_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-ORDER-003'; SRC = OM / 'MIR-REVERSIBLE-ORDER-002/results.json'
NCTRL = 100
X0, RT = O2.X0, O2.RT


def runs_at(R, objs, times):
    """Readouts (movers, background, positions) of one world at the given ticks."""
    p, c = O2.world(R, objs); t = 0; out = []; first = None
    for T in times:
        p, c = O2.run(R, p, c, T - t); t = T; out.append(O2.readout(R, p, c, T))
        if first is None: first = (p, c)
    return out, first


def state_at(R, objs, T):
    return O2.run(R, *O2.world(R, objs), T)


def one(R, x, by, side, readers):
    X, al, be = by[x['X']], by[x['al']], by[x['be']]; tau, d, De = x['tauX'], x['d'], x['Delta']
    sh = int(X['v'] * De); tg = (X, tau, X0)
    slot = lambda o, k: (o, o['phase'] + k * De, X0 - side * d + k * sh)
    TT = [De + r for r in RT]; T3 = [2 * De + r for r in RT]
    out = dict(X=x['X'], al=x['al'], be=x['be'], tauX=tau, d=d, Delta=De, side=side)
    try:
        W = {'AB': [tg, slot(al, 0), slot(be, 1)], 'BA': [tg, slot(be, 0), slot(al, 1)]}
        ro = {k: runs_at(R, v, TT)[0] for k, v in W.items()}
        out['repro'] = [[list(r[0]), list(r[1])] for r in ro['AB']], [[list(r[0]), list(r[1])] for r in ro['BA']]
        # Part T
        rd = 1 if side == 1 else -1
        tdir_ok = all(sorted(q for q in a[2] if q[1] == -rd) == sorted(q for q in b[2] if q[1] == -rd) for a, b in zip(ro['AB'], ro['BA']))
        free = {}
        for o in (al, be):
            for k in (0, 1):
                free[(o['id'], k)] = [[q[2] for q in r[2] if q[0] == o['id']] for r in runs_at(R, [slot(o, k)], TT)[0]]
        def rshift(nm, first, second):
            sh_ = []
            for i, r in enumerate(ro[nm]):
                rdm = [q for q in r[2] if q[1] == rd]
                if not rdm: sh_.append('none'); continue
                if sorted(q[0] for q in rdm) != sorted([al['id'], be['id']]): return None
                pos = {q[0]: q[2] for q in rdm}
                sh_.append((pos[first['id']] - free[(first['id'], 0)][i][0], pos[second['id']] - free[(second['id'], 1)][i][0]))
            return sh_
        sAB = rshift('AB', al, be); sBA = rshift('BA', be, al)
        if sAB is None or sBA is None: rd_state = 'unassessable'
        else:
            # alpha's shift in AB (slot 1) vs in BA (slot 2), beta likewise
            eq = all((a == 'none' and b == 'none') or (a != 'none' and b != 'none' and a[0] == b[1] and a[1] == b[0])
                     for a, b in zip(sAB, sBA))
            rd_state = 'equal' if eq else 'differ'
        out.update(tdir_ok=bool(tdir_ok), reader_timing=rd_state, timing_ok=bool(tdir_ok) and rd_state == 'equal')
        # Part R
        base = {k: state_at(R, v, T3[0]) for k, v in W.items()}
        rb = []
        for g in readers:
            res = {}
            for k, v in W.items():
                r3, (P3, C3) = runs_at(R, v + [slot(g, 2)], T3)
                dp, dc, off = R.dev(g, g['phase'] + 2 * De, T3[0]); a = X0 - side * d + 2 * sh + off
                ps, cs = base[k][0].copy(), base[k][1].copy(); ps[a:a + len(dp)] ^= dp; cs[a:a + len(dc)] ^= dc
                res[k] = ([r[0] for r in r3], not (np.array_equal(ps, P3) and np.array_equal(cs, C3)))
            touched = res['AB'][1] and res['BA'][1]
            diff = all(a != b for a, b in zip(res['AB'][0], res['BA'][0]))
            rb.append(dict(g=g['id'], touched=bool(touched), readback=bool(touched and diff)))
        out['R'] = rb; out['valid'] = True
    except ValueError as e:
        out.update(valid=False, err=str(e))
    return out


def job(a):
    lab, w, species, cases, mode = a
    R = O2.Rule(w, species); by = {o['id']: o for o in R.sp}; t0 = time.time(); rows = []
    for x in (cases[:3] if mode == 'smoke' else cases):
        side = x['side']; readers = sorted([o for o in R.sp if o['v'] * side > 0], key=lambda o: o['id'])
        rows.append(one(R, x, by, side, readers))
    return dict(lab=lab, rows=rows, secs=time.time() - t0)


def load_cases():
    J = json.load(open(SRC)); S = {f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}": r for r in
                                   json.load(open(OM / 'MIR-REVERSIBLE-SPECIES-001/results.json'))['rules']}
    out = []
    for lab in O2.ELIGIBLE:
        cs = [dict(x, ref=(x['AB'], x['BA'])) for j in J['jobs'] if j['lab'] == lab for x in j['rows']
              if x['valid'] and O2.classify(x)['touched'] and O2.classify(x)['bg_only']]
        out.append((lab, S[lab]['wolfram'], S[lab]['species'], cs))
    ctrl = [dict(x, ref=(x['AB'], x['BA'])) for j in J['jobs'] if j['lab'] == '250c' for x in j['rows']
            if x['valid'] and O2.classify(x)['touched']][:NCTRL]
    out.append(('250c', O2.CONTROL, O2.control_species(), ctrl))
    return out


def chunks(L):
    """Split each rule's cases into pieces of <= 40 for load balance and checkpoints."""
    J = []
    for lab, w, sp, cs in L:
        for i in range(0, max(len(cs), 1), 40): J.append((lab, w, sp, cs[i:i + 40], i))
    return J


def verdicts(rows_by):
    T = {}
    for lab, rows in rows_by.items():
        V = [x for x in rows if x.get('valid')]
        tc = Counter(x['reader_timing'] for x in V)
        rb = [r for x in V for r in x['R']]
        T[lab] = dict(cases=len(rows), valid=len(V), timing_ok=sum(x['timing_ok'] for x in V), tdir_ok=sum(x['tdir_ok'] for x in V),
                      reader_timing=dict(tc), pairs_g=len(rb), g_touched=sum(r['touched'] for r in rb),
                      readback=sum(r['readback'] for r in rb), cases_readback=sum(any(r['readback'] for r in x['R']) for x in V),
                      both=sum(x['timing_ok'] and any(r['readback'] for r in x['R']) for x in V),
                      repro_ok=sum(x['repro_ok'] for x in V))
    return T


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    L = load_cases()
    if sys.argv[1:2] == ['smoke']:
        J = [(lab, w, sp, cs, 'smoke') for lab, w, sp, cs in L]
        with ProcessPoolExecutor(5) as ex:
            for r in ex.map(job, J):
                print(r['lab'], 'secs', round(r['secs'], 1), 'n', len(r['rows']), 'valid', sum(x.get('valid', False) for x in r['rows']))
        print({lab: len(cs) for lab, _, _, cs in L}); return
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True); CK = OUT / 'jobs'; CK.mkdir(exist_ok=True)
    J = chunks(L); ck = lambda j: CK / f"{j[0]}_{j[4]}.json"
    todo = [j for j in J if not ck(j).exists()]
    with ProcessPoolExecutor(5) as ex:
        for j, r in zip(todo, ex.map(job, [(a, b, c, d, 'full') for a, b, c, d, _ in todo])):
            for x, src in zip(r['rows'], j[3]):   # V0: coarse AB/BA outcomes identical to ORDER-002's
                x['repro_ok'] = bool(x.get('valid', False)) and json.loads(json.dumps(list(x['repro']))) == json.loads(json.dumps(list(src['ref'])))
            ck(j).write_text(json.dumps(r, default=str))
    rows_by = {}
    for j in J: rows_by.setdefault(j[0], []).extend(json.loads(ck(j).read_text())['rows'])
    T = verdicts(rows_by); E = O2.ELIGIBLE; c = T['250c']
    S = dict(V0_repro=all(T[l]['repro_ok'] == T[l]['valid'] == T[l]['cases'] for l in T),
             V_C=c['valid'] == c['cases'] and c['readback'] == 0 and c['tdir_ok'] == c['valid'] and
                 c['reader_timing'].get('differ', 0) == 0 and c['g_touched'] >= 100)
    S['valid'] = S['V0_repro'] and S['V_C']
    S['H_T_pass'] = [l for l in E if T[l]['timing_ok'] > 0]
    S['H_R_pass'] = [l for l in E if T[l]['readback'] > 0]
    S['H_RT_pass'] = [l for l in E if T[l]['both'] > 0]
    v = lambda ps, k: 'invalid' if not S['valid'] else 'supported' if len(ps) >= k else 'not_supported'
    S['H_T'] = v(S['H_T_pass'], 4); S['H_R'] = v(S['H_R_pass'], 4); S['H_RT'] = v(S['H_RT_pass'], 3); S['table'] = T
    (OUT / 'results.json').write_text(json.dumps(dict(summary=S), indent=1, default=str) + '\n')
    print(json.dumps({k: S[k] for k in ('valid', 'V0_repro', 'V_C', 'H_T', 'H_R', 'H_RT')}), S['H_T_pass'], S['H_R_pass'], S['H_RT_pass'])


dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}

if __name__ == '__main__':
    main()
