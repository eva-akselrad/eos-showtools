"""tempomap.py - piecewise constant-tempo grid for mashups / edits.
python tempomap.py song.wav out.json  start:end:bpm_hint [start:end:bpm_hint ...]
Fits each segment's kick peaks (low-band flux, 5.8 ms) to t = t0 + k*period with outlier rejection.
Writes {"segments":[{"start","end","t0","period","bpm","resid_ms"}...]}."""
import sys, json, numpy as np, librosa, scipy.signal as sg
wav, out = sys.argv[1], sys.argv[2]
segs = [tuple(map(float, s.split(":"))) for s in sys.argv[3:]]
y, sr = librosa.load(wav, sr=22050, mono=True); hop = 128
S = np.abs(librosa.stft(y, n_fft=1024, hop_length=hop)); fr = librosa.fft_frequencies(sr=sr, n_fft=1024)
B = np.log(S[fr < 150].sum(0) + 1e-6); d = np.maximum(0, np.diff(B, prepend=B[0])); ft = np.arange(len(d)) * hop / sr
pk, _ = sg.find_peaks(d, height=np.percentile(d, 93), distance=int(0.3 * sr / hop)); kt = ft[pk]
res = []
for lo, hi, bpm in segs:
    t = kt[(kt >= lo) & (kt < hi)]; p = 60 / bpm
    best = None                                   # scan tempo +-1.5 BPM: maximise phase coherence
    for b in np.arange(bpm - 1.5, bpm + 1.5, 0.005):
        z = np.mean(np.exp(2j * np.pi * t / (60 / b)))
        if best is None or abs(z) > best[0]:
            best = (abs(z), 60 / b, z)
    p = best[1]; t0 = (np.angle(best[2]) / (2 * np.pi)) % 1 * p
    for _ in range(8):
        k = np.round((t - t0) / p); r = t - (t0 + k * p); ok = np.abs(r) < 0.035
        A = np.c_[np.ones(ok.sum()), k[ok]]; t0, p = np.linalg.lstsq(A, t[ok], rcond=None)[0]
    k = np.round((t - t0) / p); r = t - (t0 + k * p); ok = np.abs(r) < 0.035
    t0 = t0 - np.floor((t0 - lo) / p) * p          # first grid beat at/after segment start
    res.append(dict(start=lo, end=hi, t0=round(float(t0), 4), period=float(p), bpm=round(60 / p, 3),
                    used=int(ok.sum()), n=len(t), resid_ms=round(float(np.median(np.abs(r[ok]))) * 1000, 1)))
    print(res[-1])
json.dump(dict(segments=res), open(out, "w"), indent=1)

