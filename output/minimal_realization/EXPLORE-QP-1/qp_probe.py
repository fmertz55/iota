"""Quasi-particle quick probe (exploratory, NOT pre-registered), 1D mean field.
Coherence: coin-then-shift Dirac QCA, turn angle = N(x)*chi(x). No turn rate of its own.
Glue notebook chi (marks stay in the cell, with a spring to the vacuum's standing entry a0):
  chi(t+1) = 2chi - chi(t-1) - lapse^2 * [mu^2 (chi - a0) + gam * S],  S = 2Re(R*L), gam = g*n
  lapse = N(x) (arm 'all': gravity slows every clock incl. the glue spring) or 1 (arm 'coh': only turning).
Glue strength G = gam/mu^2 (static pocket: chi = a0 - G*S).
"""
import numpy as np, pandas as pd, sys
L=4096; X=np.arange(L); K=2*np.pi*np.fft.fftfreq(L); x0=L//2

def packet(xc,sigma,a):
    phi=np.exp(-(K*sigma)**2); n,m=np.cos(a),np.sin(a); R=np.zeros(L,complex); Lc=np.zeros(L,complex)
    for i,kk in enumerate(K):
        Wm=np.diag([np.exp(-1j*kk),np.exp(1j*kk)])@np.array([[n,-1j*m],[-1j*m,n]])
        lam,V=np.linalg.eig(Wm); v=V[:,np.argmin(np.angle(lam))]; v=v*np.exp(-1j*np.angle(v[0]+v[1]))
        R[i]=phi[i]*v[0]; Lc[i]=phi[i]*v[1]
    R=np.fft.ifft(R*np.exp(-1j*K*xc)); Lc=np.fft.ifft(Lc*np.exp(-1j*K*xc)); nr=np.sqrt(np.sum(abs(R)**2+abs(Lc)**2))
    return R/nr, Lc/nr

def run(a0,G,mu=0.5,sigma=20,g=0.0,arm='all',T=4000,every=20):
    R,Lc=packet(x0,sigma,max(a0,0.05)); N=1+g*(X-x0); lap=N if arm=='all' else np.ones(L)
    S=2*np.real(np.conj(R)*Lc); chi=a0-G*S; chim=chi.copy(); gam=G*mu**2; rows=[]; prev=None
    for t in range(T+1):
        if t%every==0 or t%every==1:
            d=abs(R)**2+abs(Lc)**2; m=np.sum(X*d); s=np.sqrt(np.sum((X-m)**2*d)); held=d[np.abs(X-m)<4*sigma].sum()
            if t%every==0: rows.append(dict(t=t,x=m,w=s,held=held,chi_min=chi.min())); prev=(R.copy(),Lc.copy())
            else:
                ov=np.sum(np.conj(prev[0])*R+np.conj(prev[1])*Lc); rows[-1]['Omega']=-np.angle(ov)
        if t==T: break
        S=2*np.real(np.conj(R)*Lc); new=2*chi-chim-lap**2*(mu**2*(chi-a0)+gam*S); chim,chi=chi,new
        a=N*chi; c,sn=np.cos(a),np.sin(a); cR=c*R-1j*sn*Lc; cL=-1j*sn*R+c*Lc; R=np.roll(cR,1); Lc=np.roll(cL,-1)
    return pd.DataFrame(rows)

if __name__=='__main__':
    out=[]
    for a0 in [0.0,0.2]:
        for G in [0,5,15,40,100]:
            d=run(a0,G); late=d[d.t>=2000]
            out.append(dict(a0=a0,G=G,held_T=d.held.iloc[-1],width_T=d.w.iloc[-1],width_0=d.w.iloc[0],
                            Omega=late.Omega.mean(),Omega_sd=late.Omega.std(),chi_min_T=d.chi_min.iloc[-1]))
    df=pd.DataFrame(out); df.to_csv('qp_hold.csv',index=False); print(df.round(4).to_string())


# ---- in-session variants (kick, fall, travelling glue) ----
import pandas as pd
q=__import__("qp_probe")
def run2(a0,G,mu=0.1,sigma=20,g=0.0,arm='all',T=4000,kick=0.0,every=20):
    R,Lc=q.packet(q.x0,sigma,a0); X=q.X; L=q.L
    if kick: ph=np.exp(1j*kick*X); R=R*ph; Lc=Lc*ph
    N=1+g*(X-q.x0); lap=N if arm=='all' else np.ones(L)
    S=2*np.real(np.conj(R)*Lc); chi=a0-G*S; chim=chi.copy(); gam=G*mu**2; rows=[]
    for t in range(T+1):
        if t%every==0:
            d=abs(R)**2+abs(Lc)**2; m=np.sum(X*d); rows.append(dict(t=t,x=m,held=d[np.abs(X-m)<4*sigma].sum()))
        if t==T: break
        S=2*np.real(np.conj(R)*Lc); new=2*chi-chim-lap**2*(mu**2*(chi-a0)+gam*S); chim,chi=chi,new
        a=N*chi; c,sn=np.cos(a),np.sin(a); cR=c*R-1j*sn*Lc; cL=-1j*sn*R+c*Lc; R=np.roll(cR,1); Lc=np.roll(cL,-1)
    return pd.DataFrame(rows)

def run3(a0,G,mu=0.1,sigma=20,g=0.0,arm='all',T=4000,kick=0.0,glue='pass',c=0.99,every=20,omega=False):
    R,Lc=q.packet(q.x0,sigma,a0); X=q.X; L=q.L
    if kick: ph=np.exp(1j*kick*X); R=R*ph; Lc=Lc*ph
    N=1+g*(X-q.x0); lap2=N**2 if arm=='all' else np.ones(L)
    S=2*np.real(np.conj(R)*Lc); gam=G*mu**2
    if glue=='pass':   # static Yukawa response so the start is near-stationary
        ker=1/(c**2*(2-2*np.cos(q.K))+mu**2); chi=a0-np.real(np.fft.ifft(np.fft.fft(gam*S)*ker))
    else: chi=a0-G*S
    chim=chi.copy(); rows=[]; prev=None
    for t in range(T+1):
        if t%every==0:
            d=abs(R)**2+abs(Lc)**2; m=np.sum(X*d); rows.append(dict(t=t,x=m,held=d[np.abs(X-m)<4*sigma].sum())); prev=(R,Lc)
        if t==T: break
        S=2*np.real(np.conj(R)*Lc)
        lapterm=c**2*(np.roll(chi,1)+np.roll(chi,-1)-2*chi) if glue=='pass' else 0
        new=2*chi-chim+lap2*(lapterm-mu**2*(chi-a0)-gam*S); chim,chi=chi,new
        a=N*chi; cc,sn=np.cos(a),np.sin(a); cR=cc*R-1j*sn*Lc; cL=-1j*sn*R+cc*Lc; R=np.roll(cR,1); Lc=np.roll(cL,-1)
        if t%every==0 and t>=2000 and omega: rows[-1]['Omega']=-np.angle(np.sum(np.conj(prev[0])*R+np.conj(prev[1])*Lc))
    return pd.DataFrame(rows)

def probe(G,mu,c):
    d=run3(0.2,G,mu=mu,c=c,omega=True); Om=d.Omega.dropna().mean()
    dk=run3(0.2,G,mu=mu,c=c,kick=0.01); v=np.polyfit(dk.t[dk.t>500],dk.x[dk.t>500],1)[0]
    d0=run3(0.2,G,mu=mu,c=c); f={}
    for arm in ['all','coh']:
        d1=run3(0.2,G,mu=mu,c=c,g=1e-5,arm=arm); dx=d1.x-d0.x; w=d1.t>=500; f[arm]=-2*np.polyfit(d1.t[w],dx[w],2)[0]/1e-5
    return dict(G=G,mu=mu,held_T=d.held.iloc[-1],clock=Om,push_over_clock=0.01/v/Om,fall_all=f['all'],fall_coh=f['coh'])
