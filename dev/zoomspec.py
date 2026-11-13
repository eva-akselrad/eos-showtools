"""zoomed spectrogram with beat numbers: python dev/zoomspec.py wav analysis.json out.png t0 t1 [t0 t1 ...]"""
import sys, json, numpy as np, librosa, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
f=sys.argv[1]; a=json.load(open(sys.argv[2])); out=sys.argv[3]; rng=list(map(float,sys.argv[4:]))
y,sr=librosa.load(f,sr=22050,mono=True)
S=librosa.amplitude_to_db(librosa.feature.melspectrogram(y=y,sr=sr,hop_length=128,n_mels=80),ref=np.max)
T=len(y)/sr; n=len(rng)//2
rms=librosa.feature.rms(y=y,hop_length=128)[0]; tt=np.arange(len(rms))*128/sr
fig,ax=plt.subplots(n,1,figsize=(28,4.2*n))
ax=np.atleast_1d(ax)
for r in range(n):
    a0,a1=rng[2*r],rng[2*r+1]
    ax[r].imshow(S,aspect='auto',origin='lower',extent=[0,T,0,80],cmap='magma')
    m=(tt>=a0)&(tt<=a1); ax[r].plot(tt[m],rms[m]/rms.max()*78,color='lime',lw=1)
    ax[r].set_xlim(a0,a1)
    for i,b in enumerate(a['beats']):
        if a0<=b<=a1:
            ax[r].axvline(b,color='cyan' if i%4==3 else 'gray',lw=0.9 if i%4==3 else 0.5); ax[r].text(b+0.02,74,str(i),color='w',fontsize=9)
    ax[r].set_xticks(np.arange(int(a0),int(a1)+1,1))
plt.tight_layout(); plt.savefig(out,dpi=55)
