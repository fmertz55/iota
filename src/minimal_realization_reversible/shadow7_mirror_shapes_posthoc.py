"""Post hoc (not frozen) for SHADOW-007: are shadow shapes (carriers erased, translation-normalised) closed under reflection?"""
import sys, math, json
sys.path.insert(0,'src')
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import minimal_realization_reversible.shadow7 as S7, minimal_realization_reversible.shadow6 as S6
import minimal_realization_reversible.shadow as S1
from minimal_realization_reversible.vacuum_collide import step
from minimal_realization_reversible import collide2 as C2
from collections import Counter
def mrule(w):
    t=S7.table(w); return sum(int(t[4*(i&1)+(i&2)+(i>>2)])<<i for i in range(8))
def shp(p,c,a,b,mir=False):
    d=[(i,0) for i in np.flatnonzero(p^a)]+[(i,1) for i in np.flatnonzero(c^b)]
    if not d: return ()
    if mir: d=[(-i,l) for i,l in d]
    m=min(i for i,_ in d); return tuple(sorted((i-m,l) for i,l in d))
def run(j):
    S1.N=S7.N; w,role=j[0],j[4]; tab,Rs,Ls=S7.lists(j)
    close=min(R['v']-L['v'] for R in Rs for L in Ls); T=math.ceil(552/close)+300
    V=C2.vac_seq(tab,T+C2.PMAX+4); X0=S7.X0
    sh,cen=[],[]
    for ri in range(len(Rs)):
      for li in range(len(Ls)):
        for off in S7.OFFS:
            U=S7.place([(Rs[ri]['seed'],X0),(Ls[li]['seed'],X0+off)])
            for _ in range(T): U=step(tab,*U)
            objs,resid=S1.objects(tab,*U,V,T); p,c=U[0].copy(),U[1].copy()
            for x in objs:
                a,b=x['span']; p[a-2:b+3]=V[T]; c[a-2:b+3]=V[T+1]
            sh.append((shp(p,c,V[T],V[T+1]),shp(p,c,V[T],V[T+1],True)))
            d=np.flatnonzero((p^V[T])|(c^V[T+1])); cen.append((d.min()+d.max())/2 if d.size else None)
    S=Counter(s for s,_ in sh); M=Counter(m for _,m in sh)
    nonempty=[s for s,_ in sh if s]
    closed=sum(1 for s,m in sh if s and m in S)
    achiral_self=sum(1 for s,m in sh if s and s==m)
    return dict(w=w,role=role,residue=len(nonempty),distinct_shapes=len([k for k in S if k]),
                runs_whose_mirror_shape_occurs=closed,self_mirror_runs=achiral_self,
                multiset_mirror_closed=(S==M))
if __name__=='__main__':
    jobs=[j for j in S6.pairs() if mrule(j[0])==j[0]]
    with ProcessPoolExecutor(6) as ex:
        rows=list(ex.map(run,jobs))
    json.dump(rows,open(S7.OUT/"posthoc_mirror_shapes.json","w"),indent=1); print(len(rows))
