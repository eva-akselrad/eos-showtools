"""Detailed song analysis -> bar table + json."""
import sys, json, os
import numpy as np, librosa, scipy.signal as sg

f, out = sys.argv[1], sys.argv[2]
y, sr = librosa.load(f, sr=22050, mono=True)
dur = len(y) / sr
hop = 512
yh, yp = librosa.effects.hpss(y)
oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
tempo, beats = librosa.beat.beat_track(onset_envelope=oenv, sr=sr, hop_length=hop, tightness=200)
bt = librosa.frames_to_time(beats, sr=sr, hop_length=hop)
tempo = float(np.atleast_1d(tempo)[0])

# low-band (kick/bass) energy per frame
S = np.abs(librosa.stft(y, hop_length=hop))
freqs = librosa.fft_frequencies(sr=sr)
low = S[freqs < 150].sum(0)
high = S[freqs > 4000].sum(0)
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
cent = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
ft = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)

# downbeat phase: which beat offset (0..3) has the most low-band energy
def at(arr, t):
    i = np.searchsorted(ft, t); return arr[min(i, len(arr) - 1)]
scores = [np.mean([at(low, bt[i]) for i in range(p, len(bt), 4)]) for p in range(4)]
phase = int(np.argmax(scores))
bars = bt[phase::4]

def seg(arr, a, b):
    m = (ft >= a) & (ft < b)
    return float(arr[m].mean()) if m.any() else 0.0

rows = []
for i, b0 in enumerate(bars):
    b1 = bars[i + 1] if i + 1 < len(bars) else dur
    rows.append(dict(bar=i + 1, t=round(float(b0), 3), rms=seg(rms, b0, b1), low=seg(low, b0, b1),
                     high=seg(high, b0, b1), cent=seg(cent, b0, b1), onset=seg(oenv, b0, b1)))
for k in ("rms", "low", "high", "cent", "onset"):
    mx = max(r[k] for r in rows) or 1
    for r in rows: r[k] = round(r[k] / mx, 3)

# structural boundaries via chroma+mfcc recurrence novelty
C = librosa.feature.chroma_cqt(y=yh, sr=sr, hop_length=hop)
M = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=13)
F = np.vstack([librosa.util.sync(C, beats), librosa.util.sync(M, beats)])
F = librosa.util.normalize(F, axis=1)
bounds = librosa.segment.agglomerative(F, 12)
bound_t = [round(float(bt[min(b, len(bt) - 1)]), 3) for b in bounds]

# strong hits: onset peaks well above local median
pk, _ = sg.find_peaks(oenv, height=np.percentile(oenv, 99), distance=int(0.25 * sr / hop))
hits = [round(float(ft[p]), 3) for p in pk]

json.dump(dict(file=os.path.basename(f), dur=dur, tempo=tempo, beats=[round(float(x), 3) for x in bt],
               downbeat_phase=phase, bars=rows, sections=bound_t, hits=hits), open(out, "w"), indent=1)

print(f"dur={dur:.2f}s tempo={tempo:.1f} beats={len(bt)} bars={len(bars)} phase={phase}")
print("sections:", bound_t)
print("hits:", hits)
print(" bar     t   rms  low  high cent  onset")
for r in rows:
    bar = "#" * int(r["rms"] * 30)
    print(f"{r['bar']:4d} {r['t']:6.2f} {r['rms']:.2f} {r['low']:.2f} {r['high']:.2f} {r['cent']:.2f} {r['onset']:.2f} {bar}")

