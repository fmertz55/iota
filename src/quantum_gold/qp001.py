"""Settled pockets (exploratory tooling for QP-001). Vocabulary: clock = turns per tick; total ticking rate =
coherence clock + glue-notebook cycling; push-resistance = kick / speed gained. No energy or mass primitives.
Rule: coin-then-shift QCA, turn angle N*chi; glue notebook chi with mark-passing (speed c), spring mu to the
vacuum's standing entry a0, source gam*S, S = 2Re(R*L); gravity N slows coin, glue spring and glue mark-passing."""
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
L=4096; X=np.arange(L); K=2*np.pi*np.fft.fftfreq(L); x0=L//2

def W_matrix(a):
    c,s=np.cos(a),np.sin(a); I=np.arange(L)
    C=sp.bmat([[sp.diags(c),sp.diags(-1j*s)],[sp.diags(-1j*s),sp.diags(c)]],format='csr')
    Sr=sp.csr_matrix((np.ones(L),((I+1)%L,I)),shape=(L,L)); Sl=sp.csr_matrix((np.ones(L),((I-1)%L,I)),shape=(L,L))
    return sp.bmat([[Sr,None],[None,Sl]],format='csc')@C

def static_glue(S,a0,G,mu,c):
    return a0-np.real(np.fft.ifft(np.fft.fft(G*mu**2*S)/(c**2*(2-2*np.cos(K))+mu**2)))

def settle(a0,G,mu,c,width0,tol=1e-11,maxit=200):
    S=np.exp(-(X-x0)**2/(2*width0**2)); S/=S.sum(); chi=static_glue(S,a0,G,mu,c); Om=a0*0.98; psi=None
    for it in range(maxit):
        Wm=W_matrix(chi); lam,V=sla.eigs(Wm,k=6,sigma=np.exp(-1j*Om*0.999),v0=psi)
        best=None
        for j in range(V.shape[1]):
            v=V[:,j]/np.linalg.norm(V[:,j]); d=abs(v[:L])**2+abs(v[L:])**2; ipr=np.sum(d**2)
            Sj=2*np.real(np.conj(v[:L])*v[L:]); m=np.sum(X*d)
            score=ipr*(np.sum(Sj)>0)*(abs(m-x0)<L/8)
            if best is None or score>best[0]: best=(score,v,-np.angle(lam[j]),Sj)
        _,v,Om_new,Sn=best; psi=v
        chi_new=static_glue(Sn,a0,G,mu,c); err=np.max(abs(chi_new-chi)); chi=0.5*chi+0.5*chi_new; Om=Om_new
        if err<tol: break
    R,Lc=v[:L],v[L:]; ph=np.exp(-1j*np.angle(np.sum(R+Lc))); R,Lc=R*ph,Lc*ph
    d=abs(R)**2+abs(Lc)**2; m=np.sum(X*d); R=np.roll(R,int(round(x0-m))); Lc=np.roll(Lc,int(round(x0-m)))
    S=2*np.real(np.conj(R)*Lc); chi=static_glue(S,a0,G,mu,c)
    return dict(R=R,Lc=Lc,chi=chi,Omega=Om,iters=it+1,err=err)

def evolve(st,a0,G,mu,c,T,g=0.0,kick=0.0,every=50,omega_from=None):
    R,Lc,chi=st['R'].copy(),st['Lc'].copy(),st['chi'].copy(); chim=chi.copy(); gam=G*mu**2
    if kick: ph=np.exp(1j*kick*X); R,Lc=R*ph,Lc*ph
    N=1+g*(X-x0); Nh=1+g*(X+0.5-x0); rows=[]; om=[]
    for t in range(T+1):
        if t%every==0:
            d=abs(R)**2+abs(Lc)**2; m=np.sum(X*d); rows.append((t,m,np.sqrt(np.sum((X-m)**2*d))))
        if t==T: break
        S=2*np.real(np.conj(R)*Lc); flux=Nh*(np.roll(chi,-1)-chi)
        new=2*chi-chim+N*c**2*(flux-np.roll(flux,1))-N**2*(mu**2*(chi-a0)+gam*S); chim,chi=chi,new
        a=N*chi; cc,sn=np.cos(a),np.sin(a); R2=np.roll(cc*R-1j*sn*Lc,1); L2=np.roll(-1j*sn*R+cc*Lc,-1)
        if omega_from is not None and t>=omega_from: om.append(-np.angle(np.sum(np.conj(R)*R2+np.conj(Lc)*L2)))
        R,Lc=R2,L2
    out=np.array(rows); res=dict(t=out[:,0],x=out[:,1],w=out[:,2],R=R,Lc=Lc,chi=chi,chim=chim)
    if om: res['Omega']=np.mean(om)
    return res

def ticking_total(st_or_run,a0,G,mu,c,Omega):
    chi=st_or_run['chi']; chim=st_or_run.get('chim',chi); gam=G*mu**2
    return Omega+np.sum((chi-chim)**2+c**2*(np.roll(chi,-1)-chi)**2+mu**2*(chi-a0)**2)/(2*gam)

# ---------------- QP-001 frozen run ----------------
import pandas as pd, sys, os
A0=[0.16,0.08,0.04]; GS=[0.4,0.7]; C=0.985; GRAV=4e-6
def case(a0,G):
    mu=a0/2; T=int(round(600/a0)); w0=4.6/(a0*G)
    st=settle(a0,G,mu,C,width0=w0)
    r0=evolve(st,a0,G,mu,C,T,omega_from=T-500)
    rg=evolve(st,a0,G,mu,C,T,g=GRAV); dx=rg['x']-r0['x']; dr={}
    for f in (6,3):
        w=rg['t']>=T/f; dr[f]=-2*np.polyfit(rg['t'][w],dx[w],2)[0]/GRAV/(a0/np.tan(a0))
    k=0.025*a0; rk=evolve(st,a0,G,mu,C,T,kick=k); w=rk['t']>=T/4; v=np.polyfit(rk['t'][w],rk['x'][w],1)[0]
    tick=ticking_total(st,a0,G,mu,C,st['Omega']); push=k/v/tick/(np.tan(a0)/a0)
    return dict(a0=a0,G=G,mu=mu,T=T,settle_err=st['err'],still_drift=abs(r0['x'][-1]-r0['x'][0]),
                still_width_change=abs(r0['w'][-1]-r0['w'][0]),clock_settle=st['Omega'],clock_run=r0['Omega'],
                clock_rel_slowdown=1-st['Omega']/a0,ticking=tick,push_norm=push,drift_norm_w6=dr[6],drift_norm_w3=dr[3],
                link=dr[6]*push,width=r0['w'][0])
if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'check'; os.makedirs('qp001_out',exist_ok=True)
    if mode=='check':
        st=settle(A0[0],GS[0],A0[0]/2,C,width0=4.6/(A0[0]*GS[0])); r0=evolve(st,A0[0],GS[0],A0[0]/2,C,600)
        print('VALIDITY settle_err',st['err'],'drift',abs(r0['x'][-1]-r0['x'][0]),'width_change',abs(r0['w'][-1]-r0['w'][0])); sys.exit()
    df=pd.DataFrame([case(a0,G) for G in GS for a0 in A0]); df.to_csv('qp001_out/qp001.csv',index=False)
    open('qp001_out/summary.txt','w').write(df.to_string()); print(df.to_string())
