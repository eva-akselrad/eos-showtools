"""onsets.py - list every audible event in a song with strength + character (for non-grid tracks).
python onsets.py song.wav out.json"""
import sys, json, numpy as np, librosa
y, sr = librosa.load(sys.argv[1], sr=22050, mono=True)
hop = 64
S = np.abs(librosa.stft(y, n_fft=1024, hop_length=hop))
fr = librosa.fft_frequencies(sr=sr, n_fft=1024)
ft = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)
env = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S, ref=np.max), sr=sr, hop_length=hop)
on = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=hop, backtrack=True, delta=0.08, wait=6)
rms = librosa.feature.rms(S=S, frame_length=1024)[0]; rms /= rms.max()
low = S[fr < 150].sum(0); low /= low.max()
hi = S[fr > 4000].sum(0); hi /= hi.max()
pk = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=hop, backtrack=False, delta=0.08, wait=6)
ev = []
for a, p in zip(on, pk):
    t = float(ft[a]); w0 = (ft >= t - 0.15) & (ft < t - 0.01); w1 = (ft >= t) & (ft < t + 0.12)
    r0 = float(rms[w0].mean()) if w0.any() else 0; r1 = float(rms[w1].max())
    ev.append(dict(t=round(t, 3), s=round(float(env[p] / env.max()), 3), r0=round(r0, 3), r1=round(r1, 3),
                   low=round(float(low[w1].max()), 3), hi=round(float(hi[w1].max()), 3)))
json.dump(dict(events=ev, rms=[round(float(x), 3) for x in rms[::8]], rms_dt=hop * 8 / sr), open(sys.argv[2], "w"))
for e in ev:
    tag = ("IMPACT" if e["r1"] > 0.55 and e["r1"] - e["r0"] > 0.25 else "hit" if e["s"] > 0.35 else "")
    print(f"{e['t']:7.3f} s={e['s']:.2f} rms {e['r0']:.2f}->{e['r1']:.2f} low {e['low']:.2f} hi {e['hi']:.2f} {tag}")
