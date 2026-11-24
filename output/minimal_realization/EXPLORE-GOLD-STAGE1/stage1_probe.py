"""GOLD rung 2, stage-1 QUICK PROBE (exploratory, NOT pre-registered).

Substrate: coin-then-shift Dirac QCA (as rung 1) + one notebook value phi_x per cell.
Handshake (one shared term, Lagrangian -kappa*eps*phi_x*S_x, S_x = 2Re(R*L) = turning activity):
  turn angle in cell x = eps*(1 + kappa*phi_x)              (notebook slows/speeds turning)
  notebook driven by  -kappa * sum_i n_i eps_i S_i(x)        (turning nudges notebook)
Arms (differ only in what a mark does afterwards):
  CASHIER : phi(t+1) = phi(x+1)+phi(x-1) - phi(t-1) - src     (marks passed to neighbours, 1 cell/tick)
  MEMORY  : phi(t+1) = 2 phi(t)          - phi(t-1) - src     (marks stay where written)
Stage 1 treats phi as a mean (classical) value sourced by a lump of n_E coherences; quantum notebook = stage 2.
"""
import numpy as np, pandas as pd, sys
L=8192; X=np.arange(L)

def packet(xc, sigma, a):
    k=2*np.pi*np.fft.fftfreq(L); phi=np.exp(-(k*sigma)**2)
    n,m=np.cos(a),np.sin(a); R=np.zeros(L,complex); Lc=np.zeros(L,complex)
    for i,kk in enumerate(k):
        W=np.diag([np.exp(-1j*kk),np.exp(1j*kk)])@np.array([[n,-1j*m],[-1j*m,n]])
        lam,V=np.linalg.eig(W); v=V[:,np.argmin(np.angle(lam))]; v=v*np.exp(-1j*np.angle(v[0]+v[1]))
        R[i]=phi[i]*v[0]; Lc[i]=phi[i]*v[1]
    R=np.fft.ifft(R*np.exp(-1j*k*xc)); Lc=np.fft.ifft(Lc*np.exp(-1j*k*xc))
    nrm=np.sqrt(np.sum(abs(R)**2+abs(Lc)**2)); return R/nrm, Lc/nrm

class World:
    def __init__(s, arm, kappa, species):
        # species: list of dict(R,Lc,eps,n,src)
        s.arm=arm; s.k=kappa; s.sp=species; s.phi=np.zeros(L); s.phim=np.zeros(L); s.t=0
    def source(s):
        out=np.zeros(L)
        for p in s.sp:
            if p['src']: out+=p['n']*p['eps']*2*np.real(np.conj(p['R'])*p['Lc'])
        return s.k*out
    def lapsum(s,f):
        return (np.roll(f,1)+np.roll(f,-1)) if s.arm=='cashier' else 2*f
    def step(s):
        new=s.lapsum(s.phi)-s.phim-s.source(); s.phim,s.phi=s.phi,new
        N=1+s.k*s.phi
        for p in s.sp:
            a=p['eps']*N; c,sn=np.cos(a),np.sin(a); R,Lc=p['R'],p['Lc']
            cR=c*R-1j*sn*Lc; cL=-1j*sn*R+c*Lc; p['R']=np.roll(cR,1); p['Lc']=np.roll(cL,-1)
        s.t+=1
    def unstep(s):
        N=1+s.k*s.phi
        for p in s.sp:
            a=p['eps']*N; c,sn=np.cos(a),np.sin(a)
            R=np.roll(p['R'],-1); Lc=np.roll(p['Lc'],1)
            p['R']=c*R+1j*sn*Lc; p['Lc']=1j*sn*R+c*Lc
        old=s.lapsum(s.phim)-s.phi-s.source(); s.phi,s.phim=s.phim,old; s.t-=1

def stats(p):
    d=abs(p['R'])**2+abs(p['Lc'])**2; m=np.sum(X*d); return m, np.sqrt(np.sum((X-m)**2*d))

if __name__=='__main__':
    # Prints the values in stage1_fall_summary.csv and stage1_fall_vs_lattice_law.csv
    xE=2048; epsE=1.2; sig=150; kap=1e-3
    RE,LE=packet(xE,sig,epsE); Sbar=np.sum(2*np.real(np.conj(RE)*LE))
    nE=2*1e-5/(kap**2*epsE*Sbar)          # lump size chosen so the cashier gradient is g = 1e-5
    pkt={(e,D):packet(xE+D,sig,e) for e in [0.05,0.1,0.2] for D in [800,1200]}
    def mk(arm,test,src_test=True,lump=True):
        sp=[dict(R=RE.copy(),Lc=LE.copy(),eps=epsE,n=nE,src=True)] if lump else []
        R,Lc=pkt[test]; sp.append(dict(R=R.copy(),Lc=Lc.copy(),eps=test[0],n=1,src=src_test))
        return World(arm,kap,sp)
    def run(arm,test,lump=True,src_test=True,T=4000,every=25):
        w=mk(arm,test,src_test,lump); rows=[]
        for t in range(T+1):
            if t%every==0:
                m,s=stats(w.sp[-1]); xi=int(round(m))
                rows.append(dict(t=t,N_lump=1+kap*w.phi[xE],x=m,w=s,N_test=1+kap*w.phi[xi],
                                 dNdx=kap*(w.phi[xi+50]-w.phi[xi-50])/100))
            if t<T: w.step()
        return pd.DataFrame(rows),w
    # reversibility: 1500 ticks forward then back
    for arm in ['cashier','memory']:
        w=mk(arm,(0.1,800))
        for _ in range(1500): w.step()
        for _ in range(1500): w.unstep()
        print(arm,'round-trip error',max(np.max(abs(w.sp[0]['R']-RE)),np.max(abs(w.phi))))
    # speed limit: compact-support lump, field must be exactly 0 outside the cone
    W=900; Rc,Lcc=RE.copy(),LE.copy(); Rc[np.abs(X-xE)>W]=0; Lcc[np.abs(X-xE)>W]=0
    w=World('cashier',kap,[dict(R=Rc,Lc=Lcc,eps=epsE,n=nE,src=True)]); dist=np.abs((X-xE+L//2)%L-L//2); v=0
    for t in range(1,1201):
        w.step()
        if t%100==0: v=max(v,np.max(abs(w.phi[dist>W+t+1])))
    print('max |phi| outside light cone',v)
    res={}
    for e in [0.05,0.1,0.2]:
        for D in [800,1200]:
            for arm in ['cashier','memory']: res[(arm,e,D)]=run(arm,(e,D))[0]
            res[('control',e,D)]=run('cashier',(e,D),lump=False)[0]
    rows=[];rows2=[]
    for (arm,e,D),d in res.items():
        if arm=='control': continue
        c=res[('control',e,D)]; dx=(d.x-c.x).values; t=d.t.values; win=t>=D+400
        acc=2*np.polyfit(t[win],dx[win],2)[0]; g=d.dNdx[win].mean()
        rows.append(dict(arm=arm,eps=e,D=D,accel=acc,dNdx=g,disp_T=dx[-1],width_change=(d.w-c.w).iloc[-1],
                         N_lump_T=d.N_lump.iloc[-1],N_test_T=d.N_test.iloc[-1]))
        if arm=='cashier':   # momentum law: dp/dt = -eps dN/dx, v = p / tan(eps N)
            p=np.cumsum(-e*d.dNdx.values)*25; xp=np.cumsum(p/np.tan(e*d.N_test.values))*25
            A=np.vstack([np.ones(win.sum()),t[win],xp[win]]).T
            rows2.append(dict(eps=e,D=D,lam=np.linalg.lstsq(A,dx[win],rcond=None)[0][2],dispT_meas=dx[-1],dispT_pred=xp[-1]))
    print(pd.DataFrame(rows).to_string()); print(pd.DataFrame(rows2).to_string())
