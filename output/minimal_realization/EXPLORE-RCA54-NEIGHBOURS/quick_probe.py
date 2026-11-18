import sys, json, math
sys.path.insert(0,'/Users/douglasclark/iota/src')
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction as Fr
import numpy as np
import minimal_realization_reversible.order2 as O2
import minimal_realization_reversible.species1 as SPc
from minimal_realization_reversible.vacuum_collide import table
from minimal_realization_reversible import collide2 as C2
def species(w):
    tab=table(w); pv=SPc.vac_period(tab); sp={}
    for k in range(pv):
        orb={}
        for s,dft,pat in SPc.accept(tab,k):
            if pat not in orb: orb[pat]=SPc.orbit_of(tab,pat,k+SPc.TS)
            r=orb[pat]
            if r is None or r[1]==0 or abs(Fr(r[1],r[0]))<C2.VMIN: continue
            if pv>1 and not (2<abs(dft)<116): continue
            i=SPc.sid(r[2]); wd=SPc.seed_width(s)
            if i not in sp or (wd,k,s)<(sp[i]['width'],sp[i]['phase'],sp[i]['seed']):
                sp[i]=dict(id=i,v=str(Fr(r[1],r[0])),P=r[0],width=wd,phase=k,seed=s)
    return sorted(sp.values(),key=lambda x:(x['width'],x['phase'],x['seed']))
def job(a):
    w,side,n=a; sp=species(w)
    R=O2.Rule(w,sp); G,pairs=O2.grid(R,side)
    if not pairs or len(G)==0: return dict(w=w,side=side,nsp=len(sp),note='no pairs')
    by={o['id']:o for o in R.sp}; rng=np.random.default_rng([7,w,side+1]); rows=[]
    for gi in sorted(rng.choice(len(G),size=min(n,len(G)),replace=False)):
        X,pi,tau,d,De=G[gi]; al,be=pairs[pi]
        x=O2.case(R,by[X],tau,al,be,d,De,side,slot_check=False); rows.append(x)
    s=O2.summary(rows)
    return dict(w=w,side=side,nsp=len(sp),vs=sorted({o['v'] for o in sp})[:4],valid=s['valid'],touched=s['touched'],
                order=s['bits_order'],bg=s['bits_bg'],bg_only=s['bits_bg_only'],bg_any=s['counts'].get('bg_any',0))
if __name__=='__main__':
    J=[(250^(1<<k),side,50) for k in range(8) for side in (1,-1)]+[(250,1,50)]
    with ProcessPoolExecutor(5) as ex:
        for r in ex.map(job,J): print(json.dumps(r,default=str),flush=True)
