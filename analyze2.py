"""analyze2 - tighter song analysis for timecoded shows.

python analyze2.py song.wav out.json [bpm_hint]

- fits ONE constant-tempo grid to the tracked beats (EDM is quantised), so every
  beat/16th is placed from the fit, not from jittery per-beat tracking
- per-band transients (kick / snare-clap / hats / full) with their exact onset times
- every transient is tagged with the nearest 16th-note grid slot + offset in ms
- per-bar energy table (rms, low, high) for finding builds, drops and breakdowns
"""
import sys, json, os
import numpy as np, librosa, scipy.signal as sg

f, out = sys.argv[1], sys.argv[2]
hint = float(sys.argv[3]) if len(sys.argv) > 3 else 120.0
sr, hop = 22050, 128            # 5.8 ms resolution
y, _ = librosa.load(f, sr=sr, mono=True)
dur = len(y) / sr

S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
fr = librosa.fft_frequencies(sr=sr, n_fft=2048)
ft = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)


def band_onset(lo, hi):
    B = librosa.amplitude_to_db(S[(fr >= lo) & (fr < hi)], ref=np.max)
    d = np.maximum(0, np.diff(B, axis=1)).mean(0)
    return np.concatenate([[0], d])


full = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S, ref=np.max), sr=sr, hop_length=hop)
kick = band_onset(30, 130)
snare = band_onset(1500, 5000)
hats = band_onset(7000, 11000)

# --- beat grid -----------------------------------------------------------
tempo, beats = librosa.beat.beat_track(onset_envelope=full, sr=sr, hop_length=hop, start_bpm=hint, tightness=400)
bt = librosa.frames_to_time(beats, sr=sr, hop_length=hop)
period = 60.0 / hint
# refine: robust linear fit  t = t0 + k*period  using the tracked beats
k = np.round((bt - bt[0]) / period)
for _ in range(4):
    A = np.vstack([np.ones_like(k), k]).T
    sol, *_ = np.linalg.lstsq(A, bt, rcond=None)
    res = bt - A @ sol
    keep = np.abs(res) < 0.04
    A2 = A[keep]; sol, *_ = np.linalg.lstsq(A2, bt[keep], rcond=None)
    period = sol[1]
    k = np.round((bt - sol[0]) / period)
t0, period = sol
res = bt - (t0 + k * period)
bpm = 60 / period
# pull t0 back to first beat >= 0
t0 = t0 - np.floor(t0 / period) * period

# align grid to kick transients (sub-frame accuracy): shift so the median kick offset is 0
kp, _ = sg.find_peaks(kick, height=np.percentile(kick, 90), distance=int(0.12 * sr / hop))
kt = ft[kp]
off = ((kt - t0 + period / 2) % period) - period / 2
near = off[np.abs(off) < 0.05]
shift = float(np.median(near)) if len(near) else 0.0
t0 += shift

# --- precision pass: produced EDM is almost always an integer BPM. Snap, then find the
# grid phase by folding the transient (spectral-flux) curve modulo one 8th note at 4 ms
# resolution, and decide beat vs off-beat by where the low end (kick) energy sits.
if abs(bpm - round(bpm)) < 0.06:
    bpm = float(round(bpm)); period = 60.0 / bpm
    # small 23 ms window so the flux peak sits on the attack, not 40 ms early
    Ss = np.abs(librosa.stft(y, n_fft=512, hop_length=32))
    fts = librosa.frames_to_time(np.arange(Ss.shape[1]), sr=sr, hop_length=32)
    B = np.log(Ss.sum(0) + 1e-6); flux = np.maximum(0, np.diff(B, prepend=B[0]))
    q = period / 2
    ph = fts % q
    bins = np.arange(0, q, 0.004)
    h = np.array([flux[(ph >= x) & (ph < x + 0.004)].mean() for x in bins])
    p8 = bins[int(np.argmax(h))] - 0.004          # onset starts ~1 bin before the flux peak
    lowE = S[fr < 150].sum(0)
    cand = []
    for c in (p8, p8 + q):
        phb = (ft - c) % period
        cand.append(lowE[phb < period * 0.25].mean() / (lowE[(phb >= period * 0.5) & (phb < period * 0.75)].mean() + 1e-9))
    t0 = p8 if cand[0] >= cand[1] else p8 + q
    shift = 0.0
    print(f"precision grid: bpm {bpm} 8th-phase {p8:.4f}s  beat-vs-offbeat low ratio {cand[0]:.2f}/{cand[1]:.2f}")

nb = int((dur - t0) / period) + 1
grid = t0 + np.arange(nb) * period
# downbeat phase: beat offset with the most kick energy
def env_at(env, t):
    i = np.clip(np.searchsorted(ft, t), 0, len(env) - 1); return env[i]
low_e = S[fr < 130].sum(0)
sc = [np.mean([env_at(low_e, grid[i]) for i in range(p, nb, 4)]) for p in range(4)]
phase = int(np.argmax(sc)) if len(sys.argv) <= 4 else int(sys.argv[4])   # arg 4 overrides bar phase

# --- transients ---------------------------------------------------------
def picks(env, pct, mind):
    p, props = sg.find_peaks(env, height=np.percentile(env, pct), distance=max(1, int(mind * sr / hop)))
    h = props["peak_heights"]; h = h / (h.max() or 1)
    out = []
    for i, hh in zip(p, h):
        t = float(ft[i])
        q = (t - t0) / (period / 4)          # 16th slot
        qi = int(round(q)); qo = (t - (t0 + qi * period / 4)) * 1000
        out.append(dict(t=round(t, 4), s=round(float(hh), 3), q=qi, off_ms=round(qo, 1)))
    return out

trans = dict(kick=picks(kick, 92, 0.1), snare=picks(snare, 95, 0.1), hats=picks(hats, 93, 0.05),
             full=picks(full, 97, 0.08))

# --- bars ---------------------------------------------------------------
rms = librosa.feature.rms(S=S, frame_length=2048)[0]
hi_e = S[fr > 5000].sum(0)
mid_e = S[(fr > 300) & (fr < 3000)].sum(0)
bars = []
b0s = grid[phase::4]
for i, b0 in enumerate(b0s):
    b1 = b0s[i + 1] if i + 1 < len(b0s) else dur
    m = (ft >= b0) & (ft < b1)
    if not m.any():
        continue
    bars.append(dict(bar=i + 1, t=round(float(b0), 4), rms=float(rms[m].mean()), low=float(low_e[m].mean()),
                     mid=float(mid_e[m].mean()), high=float(hi_e[m].mean()),
                     kicks=sum(1 for x in trans["kick"] if b0 <= x["t"] < b1 and x["s"] > 0.3)))
for key in ("rms", "low", "mid", "high"):
    mx = max(b[key] for b in bars) or 1
    for b in bars:
        b[key] = round(b[key] / mx, 3)

json.dump(dict(file=os.path.basename(f), dur=dur, bpm=bpm, t0=t0, period=period, phase=phase, beats=[round(float(g), 4) for g in grid],
               bars=bars, trans=trans, beat_resid_ms=[round(float(r) * 1000, 1) for r in res]),
          open(out, "w"), indent=0)

print(f"dur={dur:.2f} bpm={bpm:.3f} (librosa {float(np.atleast_1d(tempo)[0]):.1f}) t0={t0:.4f} phase={phase} "
      f"grid-fit resid ms: med {np.median(np.abs(res))*1000:.1f} p90 {np.percentile(np.abs(res),90)*1000:.1f} kick-shift {shift*1000:.1f}ms")
for k_, v in trans.items():
    offs = np.array([x["off_ms"] for x in v])
    print(f"{k_:6} n={len(v):4d}  |off| median {np.median(np.abs(offs)):.1f} ms")
print(" bar      t    rms  low  mid  high  k")
for b in bars:
    print(f"{b['bar']:4d} {b['t']:7.2f} {b['rms']:.2f} {b['low']:.2f} {b['mid']:.2f} {b['high']:.2f} {b['kicks']:2d} " + "#" * int(b["rms"] * 30))

