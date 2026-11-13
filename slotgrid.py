"""slotgrid - per-16th-note feature grid, printed like a drum tracker.

python slotgrid.py song.wav analysis.json [beat_from beat_to]
writes <analysis>_slots.json : for every 16th slot  t, kick, snare, hats, full, rms, gap
 kick/snare/hats/full = onset strength in a +-25ms window around the slot (0..1 normalised)
 rms = loudness of the slot, gap = slot is much quieter than its neighbours (a stop / suck-out)
"""
import sys, json
import numpy as np, librosa

wav, an = sys.argv[1], sys.argv[2]
A = json.load(open(an))
sr, hop = 22050, 128
y, _ = librosa.load(wav, sr=sr, mono=True)
S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
fr = librosa.fft_frequencies(sr=sr, n_fft=2048)
ft = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)


def band(lo, hi):
    B = librosa.amplitude_to_db(S[(fr >= lo) & (fr < hi)] + 1e-9, ref=np.max)
    return np.concatenate([[0], np.maximum(0, np.diff(B, axis=1)).mean(0)])


env = dict(kick=band(30, 130), snare=band(1500, 5000), hats=band(7000, 11000), full=band(30, 11000))
rms = librosa.feature.rms(S=S, frame_length=2048)[0]
rms = rms / rms.max()
t0, per = A["t0"], A["period"]
n16 = int((len(y) / sr - t0) / (per / 4))
slots = []
for i in range(n16):
    t = t0 + i * per / 4
    m = (ft >= t - 0.025) & (ft <= t + 0.03)
    w = (ft >= t) & (ft < t + per / 4)
    d = dict(i=i, beat=i / 4, t=round(t, 4))
    for k, e in env.items():
        d[k] = float(e[m].max()) if m.any() else 0.0
    d["rms"] = float(rms[w].mean()) if w.any() else 0.0
    slots.append(d)
for k in env:
    v = np.array([s[k] for s in slots]); p = np.percentile(v, 99) or 1
    for s in slots:
        s[k] = round(min(1.0, s[k] / p), 3)
r = np.array([s["rms"] for s in slots])
for i, s in enumerate(slots):
    nb = r[max(0, i - 8):i + 9]
    s["gap"] = bool(s["rms"] < 0.35 * np.median(nb) and np.median(nb) > 0.15)
json.dump(slots, open(an.replace(".json", "_slots.json"), "w"))

b0 = int(float(sys.argv[3])) if len(sys.argv) > 3 else 0
b1 = int(float(sys.argv[4])) if len(sys.argv) > 4 else n16 // 4
ch = lambda v: " .:-=+*#%@"[min(9, int(v * 10))]
print("beat   time   | kick             | snare            | hats             | full             | rms              | gaps")
for b in range(b0 - b0 % 4, b1, 4):
    row = slots[b * 4:b * 4 + 16]
    if not row:
        break
    line = f"{b:4d} {row[0]['t']:7.2f} |"
    for k in ("kick", "snare", "hats", "full", "rms"):
        line += " " + "".join(ch(s[k]) for s in row) + " |"
    line += " " + "".join("X" if s["gap"] else "." for s in row)
    print(line)
