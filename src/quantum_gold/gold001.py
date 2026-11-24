"""GOLD-001: notebook gravity (busy cashier) and the gold number. See docs/ICP_GOLD_001_CONTRACT.md.
Usage: python gold001.py check   (validity only)   |   python gold001.py run   (all outcomes)
Writes ./gold001_out/*.csv and summary.txt in the current directory.
Model: coin-then-shift Dirac QCA; one notebook phi per cell; discrete Lagrangian
  L = sum 1/2(phi_{t+1}-phi_t)^2 - 1/2(phi_{x+1}-phi_x)^2 - kappa*eps*phi*S,  S = 2Re(R*L).
=> turn angle eps(1+kappa*phi); CASHIER: phi(t+1)=phi(x+1)+phi(x-1)-phi(t-1)-kappa*eps*S. Units hbar=tick=cell=1.
"""
import numpy as np, pandas as pd, sys, os
L=8192; X=np.arange(L); K=2*np.pi*np.fft.fftfreq(L); W=np.abs(K)
OUT='gold001_out'

def packet(xc, sigma, a, kick=0.0):
    phi=np.exp(-((K-kick)*sigma)**2); n,m=np.cos(a),np.sin(a); R=np.zeros(L,complex); Lc=np.zeros(L,complex)
    for i,kk in enumerate(K):
        Wm=np.diag([np.exp(-1j*kk),np.exp(1j*kk)])@np.array([[n,-1j*m],[-1j*m,n]])
        lam,V=np.linalg.eig(Wm); v=V[:,np.argmin(np.angle(lam))]; v=v*np.exp(-1j*np.angle(v[0]+v[1]))
        R[i]=phi[i]*v[0]; Lc[i]=phi[i]*v[1]
    R=np.fft.ifft(R*np.exp(-1j*K*xc)); Lc=np.fft.ifft(Lc*np.exp(-1j*K*xc))
    nrm=np.sqrt(np.sum(abs(R)**2+abs(Lc)**2)); return R/nrm, Lc/nrm

def S(p): return 2*np.real(np.conj(p['R'])*p['Lc'])
def stats(p):
    d=abs(p['R'])**2+abs(p['Lc'])**2; m=np.sum(X*d); return m, np.sqrt(np.sum((X-m)**2*d))

class World:
    def __init__(s, arm, kappa, species):
        s.arm=arm; s.k=kappa; s.sp=species; s.phi=np.zeros(L); s.phim=np.zeros(L); s.t=0
    def source(s):
        out=np.zeros(L)
        for p in s.sp:
            if p['src']: out+=p['n']*p['eps']*S(p)
        return s.k*out
    def lapsum(s,f): return (np.roll(f,1)+np.roll(f,-1)) if s.arm=='cashier' else 2*f
    def step(s):
        new=s.lapsum(s.phi)-s.phim-s.source(); s.phim,s.phi=s.phi,new; N=1+s.k*s.phi
        for p in s.sp:
            a=p['eps']*N; c,sn=np.cos(a),np.sin(a); R,Lc=p['R'],p['Lc']
            cR=c*R-1j*sn*Lc; cL=-1j*sn*R+c*Lc; p['R']=np.roll(cR,1); p['Lc']=np.roll(cL,-1)
        s.t+=1
    def unstep(s):
        N=1+s.k*s.phi
        for p in s.sp:
            a=p['eps']*N; c,sn=np.cos(a),np.sin(a); R=np.roll(p['R'],-1); Lc=np.roll(p['Lc'],1)
            p['R']=c*R+1j*sn*Lc; p['Lc']=1j*sn*R+c*Lc
        old=s.lapsum(s.phim)-s.phi-s.source(); s.phi,s.phim=s.phim,old; s.t-=1

# ---------------- frozen parameters ----------------
XE=2048
S1=dict(kappa=2e-3, epsE=1.0, sigE=150, g=1.5e-5, eps=[0.04,0.12,0.25], sig=200, D=[900,1400], T=3500)
S2=dict(kappa=2e-3, epsE=1.0, sigE=150, g=1.5e-5, D=1000, eps0=0.3, sig=100, delta=0.02,
        v=[0.05,0.1,0.2], t1=800, Th=1400, sig_alt=150)
S3=dict(m=1.443e-25, dz=1.4e-6, dv=0.019, kappas=[1e-6,1e-3,1.0])   # Rb-87; Amit et al. PRL 123, 083601
FOLMAN_RES=1e-2   # visibility change resolvable in Folman-class SGI (order of magnitude)

def lump(P):
    RE,LE=packet(XE,P['sigE'],P['epsE']); Sb=np.sum(2*np.real(np.conj(RE)*LE))
    nE=2*P['g']/(P['kappa']**2*P['epsE']*Sb); return RE,LE,nE

# ---------------- stage 1 ----------------
def stage1(check):
    P=S1; k=P['kappa']; RE,LE,nE=lump(P); res={}; v={}
    pk={(e,D):packet(XE+D,P['sig'],e) for e in P['eps'] for D in P['D']}
    def mk(arm,test,lump_on=True):
        sp=[dict(R=RE.copy(),Lc=LE.copy(),eps=P['epsE'],n=nE,src=True)] if lump_on else []
        R,Lc=pk[test]; sp.append(dict(R=R.copy(),Lc=Lc.copy(),eps=test[0],n=1,src=True)); return World(arm,k,sp)
    for arm in ['cashier','memory']:
        w=mk(arm,(P['eps'][1],P['D'][0]))
        for _ in range(1500): w.step()
        for _ in range(1500): w.unstep()
        v['rev_'+arm]=max(np.max(abs(w.sp[0]['R']-RE)),np.max(abs(w.phi)),np.max(abs(w.phim)))
    Wc=900; Rc,Lcc=RE.copy(),LE.copy(); Rc[np.abs(X-XE)>Wc]=0; Lcc[np.abs(X-XE)>Wc]=0
    w=World('cashier',k,[dict(R=Rc,Lc=Lcc,eps=P['epsE'],n=nE,src=True)]); dist=np.abs((X-XE+L//2)%L-L//2); cone=0
    for t in range(1,1201):
        w.step()
        if t%100==0: cone=max(cone,np.max(abs(w.phi[dist>Wc+t+1])))
    v['cone']=cone
    if check: return v,None
    def run(arm,test,lump_on=True):
        w=mk(arm,test,lump_on); rows=[]
        for t in range(P['T']+1):
            if t%25==0:
                m,s=stats(w.sp[-1]); xi=int(round(m))
                rows.append(dict(t=t,N_lump=1+k*w.phi[XE],x=m,w=s,N_test=1+k*w.phi[xi],dNdx=k*(w.phi[xi+50]-w.phi[xi-50])/100))
            if t<P['T']: w.step()
        return pd.DataFrame(rows)
    rows=[]
    for e in P['eps']:
        for D in P['D']:
            c=run('cashier',(e,D),False)
            for arm in ['cashier','memory']:
                d=run(arm,(e,D)); dx=(d.x-c.x).values; t=d.t.values; win=t>=D+500
                p=np.cumsum(-e*d.dNdx.values)*25; xp=np.cumsum(p/np.tan(e*d.N_test.values))*25
                lam=np.linalg.lstsq(np.vstack([np.ones(win.sum()),t[win],xp[win]]).T,dx[win],rcond=None)[0][2] if arm=='cashier' else np.nan
                after=t>=D
                rows.append(dict(arm=arm,eps=e,D=D,disp_T=dx[-1],lam=lam,
                    slow_ok=bool(np.all(d.N_lump.values[after]<d.N_test.values[after]) and np.all(d.N_test.values[after]<1)),
                    disp_before=np.max(abs(dx[t<=D-600])),N_lump_T=d.N_lump.iloc[-1]))
    return v,pd.DataFrame(rows)

# ---------------- stage 2 ----------------
def notebook_G(da):       # da = Fourier amplitudes a_k of the difference field; excludes k=0 and k=pi
    ok=(W>1e-12)&(W<np.pi-1e-12); g=np.abs(da[ok])**2/(4*np.sin(W[ok])); uv=(W[ok]>np.pi/2)
    return g.sum(), (g[uv].sum()/g.sum() if g.sum()>0 else 0.0)
def amp(u,vm): return np.fft.fft(u,norm='ortho')-np.exp(1j*W)*np.fft.fft(vm,norm='ortho')

def kick_for(v,a):        # momentum giving group velocity v: cos w = cos a cos k
    ks=np.linspace(0,1.2,200001); w=np.arccos(np.cos(a)*np.cos(ks)); vg=np.cos(a)*np.sin(ks)/np.sin(w)
    return ks[np.argmin(abs(vg-v))]

def interferometer(P,v,delta,sig):
    k=P['kappa']; RE,LE,nE=lump(P); x0=XE+P['D']; e0=P['eps0']; t1,Th=P['t1'],P['Th']; T=2*t1+Th
    clocks=[e0] if delta==0 else [e0+delta,e0-delta]; sp=[dict(R=RE.copy(),Lc=LE.copy(),eps=P['epsE'],n=nE,src=True)]
    br={}
    for c,e in enumerate(clocks):
        R,Lc=packet(x0,sig,e)
        for b in 'AB':
            p=dict(R=R.copy(),Lc=Lc.copy(),eps=e,n=1,src=False); sp.append(p); br[(b,c)]=p
    w=World('cashier',k,sp); kk={c:kick_for(v,e) for c,e in enumerate(clocks)}
    dphi={c:[np.zeros(L),np.zeros(L)] for c in range(len(clocks))}   # [phi_t, phi_{t-1}] of difference field
    traj={(b,c):[] for (b,c) in br}; q={(b,c):[] for (b,c) in br}; Gt=[]
    sched={0:+1,t1:-1,t1+Th:-1,2*t1+Th:+1}
    for t in range(T+1):
        if t in sched:
            for c in range(len(clocks)):
                ph=np.exp(1j*sched[t]*kk[c]*X); br[('B',c)]['R']*=ph; br[('B',c)]['Lc']*=ph
        for (b,c),p in br.items():
            m,s=stats(p); traj[(b,c)].append((m,s)); q[(b,c)].append(k*clocks[c]*np.sum(S(p)))
        if t==T: break
        for c in range(len(clocks)):          # difference notebook field, same leapfrog, source k*eps*(S_B - S_A)
            u,um=dphi[c]; src=k*clocks[c]*(S(br[('B',c)])-S(br[('A',c)]))
            dphi[c]=[np.roll(u,1)+np.roll(u,-1)-um-src,u]
        if t%100==99: Gt.append((t+1,notebook_G(amp(*dphi[0]))[0]))
        w.step()
    out=dict(v=v,delta=delta,sigma=sig,kick=kk[0])
    Oc=[]; Gc=[]
    for c in range(len(clocks)):
        A,B=br[('A',c)],br[('B',c)]
        Oc.append(np.sum(np.conj(A['R'])*B['R']+np.conj(A['Lc'])*B['Lc'])); G,uvf=notebook_G(amp(*dphi[c])); Gc.append(G)
        if c==0: out.update(uv_frac=uvf)
    out['r_space_clock']=abs(np.mean(Oc)); out['theta']=np.angle(np.mean(Oc))
    out['r_note']=float(np.exp(-np.mean(Gc))); out['G']=float(np.mean(Gc))
    out['r_total']=abs(np.mean([o*np.exp(-g) for o,g in zip(Oc,Gc)]))
    out['dh_max']=max(abs(np.array(traj[('B',0)])[:,0]-np.array(traj[('A',0)])[:,0]))
    out['G_hold_max']=max(g for _,g in Gt) if Gt else np.nan
    # worldline (bridge) formula: point charges q_j(t) at centroids, Gaussian form factor of measured width
    Gw=[]
    for c in range(len(clocks)):
        da=np.zeros(L,complex)
        for t in range(T):
            acc=np.zeros(L,complex)
            for sgn,b in [(1,'B'),(-1,'A')]:
                m,s=traj[(b,c)][t]; acc+=sgn*q[(b,c)][t]*np.exp(-1j*K*m-0.5*(K*s)**2)
            da-=np.exp(-1j*W*(T-1-t))*acc/np.sqrt(L)
        Gw.append(notebook_G(da)[0])
    out['G_worldline']=float(np.mean(Gw))
    return out

def free_invariant_check():
    rng=np.random.default_rng(1); u=np.convolve(rng.normal(size=L),np.ones(40)/40,'same'); um=np.roll(u,3)
    G0=notebook_G(amp(u,um))[0]
    for _ in range(2000): u,um=np.roll(u,1)+np.roll(u,-1)-um,u
    return abs(notebook_G(amp(u,um))[0]/G0-1)

def stage2(check):
    P=S2; v={'free_invariant':free_invariant_check()}
    if check:
        o=interferometer(P,P['v'][0],0.0,P['sig']); v.update(r_space_ok=o['r_space_clock'],uv_frac=o['uv_frac']); return v,None
    rows=[interferometer(P,vv,0.0,P['sig']) for vv in P['v']]
    rows+=[interferometer(P,vv,P['delta'],P['sig']) for vv in P['v']]
    rows.append(interferometer(P,P['v'][1],0.0,P['sig_alt']))
    return v,pd.DataFrame(rows)

# ---------------- stage 3 (3D continuum, same rule, ruler) ----------------
def stage3():
    hbar=1.054571817e-34; c=2.99792458e8; Gn=6.67430e-11; mP=np.sqrt(hbar*c/Gn); tP=np.sqrt(hbar*Gn/c**5)
    m,dz,dv=S3['m'],S3['dz'],S3['dv']; a=dv**2/dz; T1=dz/dv              # closed loop: +a, -a (2T1), +a
    def Aw(w):   # Fourier transform of relative acceleration (+a, -a for 2T1, +a), in light-seconds/s^2
        e=lambda n: np.exp(1j*w*n*T1)
        return (a/c)*((e(1)-1)-(e(3)-e(1))+(e(4)-e(3)))/(1j*w)
    rows=[]
    for kap in S3['kappas']:
        tau=np.sqrt(4*np.pi)*tP/kap; wmax=np.pi/tau                              # ruler: G fixes tick given kappa
        ws=np.logspace(np.log10(1e-4/T1),np.log10(min(wmax,1e5/T1)),400001)
        I=np.trapezoid(abs(Aw(ws))**2/ws,ws)                                     # = int w^3 |dX(w)|^2 dw, dX = -A/w^2
        G3=(m/mP)**2/(6*np.pi)*I
        rows.append(dict(kappa=kap,tick_s=tau,G3D=G3,closure_rel=abs(Aw(np.array([1e-6/T1]))[0])/(a*T1/c),T_total=4*T1))
    return pd.DataFrame(rows)

if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'check'; os.makedirs(OUT,exist_ok=True)
    v1,r1=stage1(mode=='check'); v2,r2=stage2(mode=='check')
    print('VALIDITY stage1',{k:float(x) for k,x in v1.items()}); print('VALIDITY stage2',{k:float(x) for k,x in v2.items()})
    if mode=='check': sys.exit()
    r3=stage3(); r1.to_csv(f'{OUT}/stage1.csv',index=False); r2.to_csv(f'{OUT}/stage2.csv',index=False); r3.to_csv(f'{OUT}/stage3.csv',index=False)
    with open(f'{OUT}/summary.txt','w') as f:
        for n,r in [('stage1',r1),('stage2',r2),('stage3',r3)]: f.write(n+'\n'+r.to_string()+'\n\n')
        f.write(f'validity1 {v1}\nvalidity2 {v2}\n')
    print(open(f'{OUT}/summary.txt').read())
