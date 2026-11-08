import sys, json, numpy as np
sys.path.insert(0,'src')
import minimal_realization_reversible.shadow7 as S7, minimal_realization_reversible.shadow6 as S6
from minimal_realization_reversible.vacuum_collide import table, step
from minimal_realization_reversible import collide2 as C2
N=2048; X=1024
def mirror_rule(w):
    t=table(w); return sum(int(t[4*(i&1)+(i&2)+(i>>2)])<<i for i in range(8))
def orbitset(tab, seed, V, t0=300, t1=700):
    pp,cc=seed; p=np.zeros(N,np.uint8); c=np.zeros(N,np.uint8)
    p[X:X+len(pp)]^=np.array(pp,np.uint8); c[X:X+len(cc)]^=np.array(cc,np.uint8)
    out=set()
    for t in range(t1):
        if t>=t0:
            d=[(i,0) for i in np.flatnonzero(p^V[t])]+[(i,1) for i in np.flatnonzero(c^V[t+1])]
            if d:
                m=min(i for i,_ in d); out.add((V[t],V[t+1],tuple(sorted((i-m,l) for i,l in d))))
        p,c=step(tab,p,c)
    return out
def mir(S):
    o=set()
    for a,b,d in S:
        M=max(i for i,_ in d); o.add((a,b,tuple(sorted((M-i,l) for i,l in d))))
    return o
res=json.load(open('output/minimal_realization/MIR-REVERSIBLE-SHADOW-007/results.json'))
R={(r['wolfram'],r['role']):r for r in res['rules']}
rows=[]
for j in S6.pairs():
    w,role=j[0],j[4]; tab,Rs,Ls=S7.lists(j); V=C2.vac_seq(tab,800)
    oR=[orbitset(tab,o['seed'],V) for o in Rs]; oL=[orbitset(tab,o['seed'],V) for o in Ls]
    pair=[mir(a)==b for a,b in zip(oR,oL)]
    anyL=[any(mir(a)==b for b in oL) for a in oR]
    r=R[(w,role)]['C']
    rows.append(dict(w=w,role=role,mw=mirror_rule(w),sym=mirror_rule(w)==w,vR=[str(o['v']) for o in Rs],vL=[str(o['v']) for o in Ls],
        paired_by_index=pair,R_has_mirror_in_L=anyL,only=round(r['only'],3),fa=round(r['footprint_a'],3),fb=round(r['footprint_b'],3),joint=round(r['joint'],3)))
    print(rows[-1],flush=True)
json.dump(rows,open('output/minimal_realization/MIR-REVERSIBLE-SHADOW-007/posthoc_mirror_check.json','w'),indent=1)
