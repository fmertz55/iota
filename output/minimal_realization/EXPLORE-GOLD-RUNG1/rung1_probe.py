"""GOLD rung 1 quick probe (exploratory, NOT pre-registered).

Dirac QCA (local coin [[cos a, -i sin a], [-i sin a, cos a]] then shift R->+1, L->-1;
same local coin and dispersion cos w = cos a cos k as iota's direct_qca_step).
Turn angle a(x) = eps * N(x), with a hand-placed tick-rate field N(x) = 1 + g (x - x0).
Internal clock: a coherence in equal superposition of two turn rates eps0 +/- delta.
Interferometer: two branches at heights x0 -/+ dh/2, evolved separately (linearity),
ideal recombiner = translation by dh; overlap O = <a|T_dh b> = r e^{i theta}.
Also: free-fall acceleration vs turn rate.
"""
import numpy as np, itertools, pandas as pd
L=8192; X=np.arange(L); x0=L//2

def packet(xc, sigma, eps_loc):
    k=2*np.pi*np.fft.fftfreq(L); phi=np.exp(-(k*sigma)**2)
    n,m=np.cos(eps_loc),np.sin(eps_loc); R=np.zeros(L,complex); Lc=np.zeros(L,complex)
    for i,kk in enumerate(k):
        W=np.diag([np.exp(-1j*kk),np.exp(1j*kk)])@np.array([[n,-1j*m],[-1j*m,n]])
        lam,V=np.linalg.eig(W); v=V[:,np.argmin(np.angle(lam))]; v=v*np.exp(-1j*np.angle(v[0]+v[1]))
        R[i]=phi[i]*v[0]; Lc[i]=phi[i]*v[1]
    R=np.fft.ifft(R*np.exp(-1j*k*xc)); Lc=np.fft.ifft(Lc*np.exp(-1j*k*xc))
    nrm=np.sqrt(np.sum(abs(R)**2+abs(Lc)**2)); return R/nrm, Lc/nrm

def evolve(R,Lc,ang,T_list):
    n,m=np.cos(ang),np.sin(ang); out={}; t=0
    for T in T_list:
        while t<T:
            cR=n*R-1j*m*Lc; cL=-1j*m*R+n*Lc; R=np.roll(cR,1,axis=-1); Lc=np.roll(cL,-1,axis=-1); t+=1
        out[T]=(R.copy(),Lc.copy())
    return out

def interferometer(eps0,dl,g,dh,Ts,sigma=150):
    N=1+g*(X-x0); xa=x0-dh//2; xb=xa+dh; epsc=[eps0+dl,eps0-dl]
    R=np.zeros((2,2,L),complex); Lc=np.zeros_like(R); ang=np.zeros((2,2,L))
    for bi,xc in enumerate([xa,xb]):
        for ci,e in enumerate(epsc):
            R[bi,ci],Lc[bi,ci]=packet(xc,sigma,e*N[xc]); ang[bi,ci]=e*N
    s=evolve(R,Lc,ang,Ts); rows=[]
    for T in Ts:
        Rr,Ll=s[T]
        Oc=[np.sum(np.conj(Rr[0,c])*np.roll(Rr[1,c],-dh)+np.conj(Ll[0,c])*np.roll(Ll[1,c],-dh)) for c in range(2)]
        O=0.5*(Oc[0]+Oc[1])
        rows.append(dict(eps0=eps0,delta=dl,g=g,dh=dh,T=T,x=g*dh*T,r=abs(O),theta=np.angle(O),r0=abs(Oc[0]),r1=abs(Oc[1])))
    return rows

if __name__=='__main__':
    rows=[]
    for eps0,dl,g,dh in itertools.product([0.1,0.2,0.3],[0.0,0.02,0.05],[2e-6,5e-6,1e-5],[50,100,200,400]):
        if dl<=eps0/2: rows+=interferometer(eps0,dl,g,dh,list(range(250,4001,250)))
    df=pd.DataFrame(rows); df['r_zych']=abs(np.cos(df.delta*df.x))
    df['dth']=np.angle(np.exp(1j*(df.theta+df.eps0*df.x)))
    print('max|r-r_zych|',(df.r-df.r_zych).abs().max(),' max|theta-pred|',df.dth.abs().max())
    cr=pd.DataFrame(interferometer(0.3,0.15,1e-5,400,list(range(100,8001,100))))
    print('collapse: min r',cr.r.min(),'at gΔhT',cr.loc[cr.r.idxmin(),'x'])
    g=1e-5; Ts=list(range(0,3001,100))
    for eps in [0.05,0.1,0.2,0.4,0.8,1.2]:
        N=1+g*(X-x0); R,Lc=packet(x0,150,eps); s=evolve(R,Lc,eps*N,Ts)
        xs=[np.sum(X*(abs(s[T][0])**2+abs(s[T][1])**2)) - x0 for T in Ts]
        print(f'eps={eps} a/g={2*np.polyfit(Ts,xs,2)[0]/g:+.4f} pred={-eps/np.tan(eps):+.4f}')
