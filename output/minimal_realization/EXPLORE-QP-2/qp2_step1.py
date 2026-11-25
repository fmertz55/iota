"""EXPLORE-QP-2 step 1 (exploratory, not frozen). One settled QP-001 pocket writes its own cashier notebook.
Vocabulary: clock = turns per tick; no mass/energy. Rule = QP-001 (no hand-set slope) + GOLD-001 cashier carried
over literally as ONE shared handshake term: turning angle chi*(1+k*phi); it writes the glue (gam*(1+k*phi)*S) and
the cashier (k*chi*S). Cashier: marks passed to neighbours at 1 cell/tick, no spring, starts blank.
The cashier therefore touches turning only (not glue spring / glue mark-passing): a choice on open question 1.
Question: does the pocket stay held and still while its cashier fills in? Does the cashier stay inside the cone?"""
import numpy as np, pandas as pd, sys
sys.path.insert(0, '.')
from qp001 import settle, L, X, x0

def run(st, a0, G, mu, c, k, T, every=50, back=False):
    R, Lc = st['R'].copy(), st['Lc'].copy(); chi = st['chi'].copy(); chim = chi.copy()
    phi = np.zeros(L); phim = np.zeros(L); gam = G*mu**2
    d0 = abs(R)**2+abs(Lc)**2; w0 = np.sqrt(np.sum((X-x0)**2*d0)); edge = 6*w0
    rows = []; cone = 0.0; om = []
    for t in range(T+1):
        if t % every == 0:
            d = abs(R)**2+abs(Lc)**2; m = np.sum(X*d); w = np.sqrt(np.sum((X-m)**2*d))
            held = np.sum(d[np.abs(X-x0) <= edge])
            rows.append(dict(t=t, x=m-x0, w=w, held=held, norm=d.sum(), N_centre=1+k*phi[x0],
                             clock=np.mean(om[-every:]) if om else np.nan))
            out = np.abs(X-x0) > edge+t+2
            if out.any(): cone = max(cone, np.max(abs(phi[out])))
        if t == T: break
        S = 2*np.real(np.conj(R)*Lc)
        lap = np.roll(chi, -1)-2*chi+np.roll(chi, 1)
        chin = 2*chi-chim+c**2*lap-mu**2*(chi-a0)-gam*(1+k*phi)*S
        phin = np.roll(phi, 1)+np.roll(phi, -1)-phim-k*chi*S
        chim, chi = chi, chin; phim, phi = phi, phin
        a = chi*(1+k*phi); cc, sn = np.cos(a), np.sin(a)
        R2 = np.roll(cc*R-1j*sn*Lc, 1); L2 = np.roll(-1j*sn*R+cc*Lc, -1)
        om.append(-np.angle(np.sum(np.conj(R)*R2+np.conj(Lc)*L2))); R, Lc = R2, L2
    rev = np.nan
    if back:   # exact reversal check
        for t in range(T):
            a = chi*(1+k*phi); cc, sn = np.cos(a), np.sin(a)
            Ru = np.roll(R, -1); Lu = np.roll(Lc, 1); R = cc*Ru+1j*sn*Lu; Lc = 1j*sn*Ru+cc*Lu
            S = 2*np.real(np.conj(R)*Lc)
            lap = np.roll(chim, -1)-2*chim+np.roll(chim, 1)
            chip = 2*chim-chi+c**2*lap-mu**2*(chim-a0)-gam*(1+k*phim)*S
            phip = np.roll(phim, 1)+np.roll(phim, -1)-phi-k*chim*S
            chi, chim = chim, chip; phi, phim = phim, phip
        rev = max(np.max(abs(R-st['R'])), np.max(abs(Lc-st['Lc'])), np.max(abs(phi)), np.max(abs(chi-st['chi'])))
    return pd.DataFrame(rows), cone, rev

if __name__ == '__main__':
    a0, G, c = 0.16, 0.4, 0.985; mu = a0/2; T = int(round(600/a0))
    st = settle(a0, G, mu, c, width0=4.6/(a0*G))
    out = []; tabs = {}
    for k in [0.0, 2e-3, 1e-2, 3e-2]:
        df, cone, rev = run(st, a0, G, mu, c, k, T, back=True); tabs[k] = df
        last = df.iloc[-1]; first = df.iloc[0]
        out.append(dict(k=k, T=T, settled_clock=st['Omega'], width0=first.w, drift=last.x, width_change=last.w-first.w,
                        held_T=last.held, norm_err=abs(last.norm-1), N_centre_T=last.N_centre,
                        clock_early=df.clock.iloc[2], clock_late=last.clock, cone_leak=cone, reversal_err=rev))
        df.to_csv(f'qp2_step1_series_k{k}.csv', index=False)
    res = pd.DataFrame(out); res.to_csv('qp2_step1.csv', index=False)
    pd.set_option('display.width', 250); print(res.to_string())
