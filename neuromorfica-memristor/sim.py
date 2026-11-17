import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
Ron,Roff,D,mu,Rs=100.0,16000.0,10e-9,1e-15,1000.0
dt=1e-3
def run(segs,w0=0.0):
    w=w0; T=[];R=[];I=[];V=[];t=0
    for v,dur in segs:
        for _ in range(int(round(dur/dt))):
            x=w/D; Rm=x*Ron+(1-x)*Roff; i=v/(Rs+Rm)
            T.append(t);R.append(Rm);I.append(i);V.append(v)
            w=min(max(w+dt*mu*Ron*i/D,0),D); t+=dt
    x=w/D; return np.array(T),np.array(R),np.array(I),np.array(V),w
segsA=[(0,1),(1,2),(0,10)]
segsB=[(0,1),(5,2),(0,10)]
TA,RA,IA,VA,wA=run(segsA); TB,RB,IB,VB,wB=run(segsB)
# reset after B
TC,RC,IC,VC,wC=run([(-5,4),(0,4)],w0=wB)
def at(T,R,t): return R[np.searchsorted(T,t)]
for n,T,R in [('A',TA,RA),('B',TB,RB)]:
    print(n,'inicio',at(T,R,0.5),'fim pulso',at(T,R,2.999),'apos 10s sem entrada',R[-1])
print('C reset: fim -5V',at(TC,RC,3.999),'apos 4s', RC[-1])
# also 3 pulses of 1V (repetition)
TD,RD,ID,VD,wD=run([(0,1)]+[(1,2),(0,2)]*3+[(0,5)])
print('D 3 pulsos 1V final',RD[-1])
fig,ax=plt.subplots(2,1,figsize=(8,5.2),sharex=True)
ax[0].plot(TA,VA,label='Condição A: 1 V',color='#2a7ab0');ax[0].plot(TB,VB,'--',label='Condição B: 5 V',color='#c0392b')
ax[0].set_ylabel('Estímulo (V)');ax[0].legend(loc='upper right',fontsize=8);ax[0].grid(alpha=.3)
ax[1].plot(TA,RA/1000,color='#2a7ab0');ax[1].plot(TB,RB/1000,'--',color='#c0392b')
ax[1].axvspan(3,13,color='#eee');ax[1].text(7.5,8,'entrada retirada (0 V)',ha='center',fontsize=8)
ax[1].set_ylabel('R do memristor (kΩ)');ax[1].set_xlabel('Tempo (s)');ax[1].grid(alpha=.3)
fig.suptitle('Previsão do modelo HP (mesmas equações do Falstad) — não é captura do Falstad',fontsize=9)
plt.tight_layout();plt.savefig('fig_ensaios.png',dpi=160)
fig,ax=plt.subplots(figsize=(8,2.6))
ax.plot(TD,RD/1000,color='#2a7ab0');ax.set_ylabel('R (kΩ)');ax.set_xlabel('Tempo (s)');ax.grid(alpha=.3)
ax.set_title('Condição D: 3 pulsos de 1 V (2 s) com pausas de 2 s — efeito cumulativo',fontsize=9)
plt.tight_layout();plt.savefig('fig_pulsos.png',dpi=160)
