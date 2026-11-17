"""MIR-REVERSIBLE-CLOCK-002: CLOCK-001's question with sub-light clocks crossing a genuinely non-vacuum domain.
Only rule 37 qualifies (scan of the active rules: the only shadow domain that is neither time-shifted vacuum nor
unstructured is 37's period-2 (0, 3) domain). Tracker, probes, entry conditions and kappa definitions: clock1.py, unchanged.
Medium per side: the first collision in scan order (X in first 4 L species, reader in first 4 R species, phase m,
d in 24..39 step 3; T = 600) that leaves no movers, one background component, and a non-vacuum domain on that side.
Control: 147 (both sides), as in CLOCK-001. See docs/ICP_MIR_REVERSIBLE_CLOCK_002_CONTRACT.md.
"""
import hashlib, json, math, os, subprocess, sys
os.environ.setdefault('OMP_NUM_THREADS', '1')
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction as Fr
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import minimal_realization_reversible.order2 as O2
import minimal_realization_reversible.clock1 as C1
TAG = 'mir-reversible-clock-002-v0.1.1-frozen'
P_ = 'src/minimal_realization_reversible/'
SEALED = ['docs/ICP_MIR_REVERSIBLE_CLOCK_002_CONTRACT.md'] + [P_ + f for f in ('clock2.py', 'clock1.py', 'order2.py', 'species1.py',
          'inventory1.py', 'collide2.py', 'vacuum_collide.py')] + ['output/minimal_realization/MIR-REVERSIBLE-SPECIES-001/results.json']
SEAL = ROOT / 'specs/icp_minimal_realization_reversible/clock2_seal.json'
OM = ROOT / 'output/minimal_realization'; OUT = OM / 'MIR-REVERSIBLE-CLOCK-002'
dig = lambda: {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SEALED}
X0 = O2.X0


def medium_maker(R, side, T=600):
    Ls = [o for o in R.sp if o['v'] < 0]; Rs = [o for o in R.sp if o['v'] > 0]
    for X in Ls[:4]:
        for a in Rs[:4]:
            for m in range(X['P'] // R.pv):
                for d in range(24, 40, 3):
                    objs = [(X, X['phase'] + m * R.pv, X0), (a, a['phase'], X0 - d)]
                    try: p, c = O2.run(R, *O2.world(R, objs), T)
                    except ValueError: continue
                    mv, bg, _ = O2.readout(R, p, c, T)
                    if bg and not mv and len(bg) == 1:
                        doms = eval(bg[0])
                        if doms and doms[0] != ('nodom',):
                            dm = doms[0] if side == 1 else doms[-1]
                            if isinstance(dm, tuple) and len(dm) == 3 and dm[1] != 'vac': return objs, (X['id'], a['id'], m, d), dm
    return None, None, None


def job(a):
    lab, w, species, side, control = a
    R = O2.Rule(w, species)
    if control:
        objs, key, bg = C1.shadow_maker(R); doms = eval(bg[0]); dm = doms[0] if side == 1 else doms[-1]
    else:
        objs, key, dm = medium_maker(R, side)
    if objs is None: return dict(lab=lab, side=side, err='no medium')
    sp = sorted([o for o in R.sp if o['v'] * side > 0], key=lambda o: o['id']); rows = []
    for o in sp:
        for TL in C1.TLS:
            for j in C1.JS:
                r = C1.transit(R, objs, o, side, dm[0], TL, j); r.update(sp=o['id'], TL=TL, j=j, v=str(o['v'])); rows.append(r)
    return dict(lab=lab, side=side, shadow=key, medium=repr(dm), n_species=len(sp), rows=rows)


def main():
    if sys.argv[1:] == ['seal']:
        SEAL.write_text(json.dumps(dig(), indent=1, sort_keys=True) + '\n'); return
    S = {f"{r['wolfram']}{'s' if r['role'].endswith('silent') else ''}": r for r in json.load(open(OM / 'MIR-REVERSIBLE-SPECIES-001/results.json'))['rules']}
    J = [('37', 37, S['37']['species'], s, False) for s in (1, -1)] + [('147', 147, S['147']['species'], s, True) for s in (1, -1)]
    subprocess.run(['git', '-C', str(ROOT), 'rev-parse', TAG], check=True, capture_output=True)
    assert json.loads(SEAL.read_text()) == dig(), 'seal mismatch'
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(4) as ex: res = list(ex.map(job, J))
    T = C1.analyse(res)
    for r in res:
        k = f"{r['lab']}{'L' if r['side'] == 1 else 'R'}"; loc = [x for x in r['rows'] if x['type'] == 'localized']
        T[k]['loc_by_species'] = {s: sorted({(x['kf'], x['kv']) for x in loc if x['sp'] == s}) for s in sorted({x['sp'] for x in loc})}
        T[k]['loc_speeds_vac'] = sorted({x['v'] for x in loc})
    ctrl = [T['147L'], T['147R']]; med = {k: T[k] for k in ('37L', '37R')}
    Sm = dict(V_lag=all(t['loc_species'] >= 2 and t['loc_kf'] == ['1'] and t['loc_kv'] == ['1'] for t in ctrl))
    el = {k: t for k, t in med.items() if t['loc_species'] >= 2}
    Sm['U_eligible'] = sorted(el); Sm['valid'] = Sm['V_lag'] and len(el) >= 1
    Sm['H_U_pass'] = sorted(k for k, t in el.items() if len(t['loc_kf']) == 1 and len(t['loc_kv']) == 1)
    Sm['H_M_pass'] = sorted(k for k, t in el.items() if t['loc_metric'] and len(t['loc_kf']) == 1)
    Sm['H_S_pass'] = sorted(k for k, t in el.items() if t['loc_kf'] != ['1'] or t['loc_kv'] != ['1'])
    v = lambda ps: 'invalid' if not Sm['valid'] else 'supported' if len(ps) == len(el) else 'not_supported'
    Sm['H_U'] = v(Sm['H_U_pass']); Sm['H_M'] = v(Sm['H_M_pass']); Sm['H_S'] = v(Sm['H_S_pass'])
    Sm['table'] = T
    (OUT / 'results.json').write_text(json.dumps(dict(summary=Sm, jobs=res), indent=1, default=str) + '\n')
    print(json.dumps({k: Sm[k] for k in ('valid', 'V_lag', 'U_eligible', 'H_S', 'H_U', 'H_M', 'H_S_pass', 'H_U_pass')}))


if __name__ == '__main__':
    main()
