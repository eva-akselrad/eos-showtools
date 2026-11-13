import sys, json, numpy as np, librosa, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
f=sys.argv[1]; a=json.load(open(sys.argv[2])); out=sys.argv[3]
y,sr=librosa.load(f,sr=11025,mono=True)
S=librosa.amplitude_to_db(librosa.feature.melspectrogram(y=y,sr=sr,hop_length=256,n_mels=64),ref=np.max)
T=len(y)/sr; rows=4; seg=T/rows
fig,ax=plt.subplots(rows,1,figsize=(28,16))
for r in range(rows):
    a0,a1=r*seg,(r+1)*seg
    ax[r].imshow(S,aspect='auto',origin='lower',extent=[0,T,0,64],cmap='magma')
    ax[r].set_xlim(a0,a1)
    for b in a['bars']:
        if a0<=b['t']<=a1:
            ax[r].axvline(b['t'],color='cyan',lw=0.8); ax[r].text(b['t']+0.05,60,str(b['bar']),color='w',fontsize=9)
    ax[r].set_xticks(np.arange(int(a0),int(a1)+1,2))
plt.tight_layout(); plt.savefig(out,dpi=60)
