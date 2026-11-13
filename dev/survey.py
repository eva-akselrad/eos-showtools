import sys, glob, os
import numpy as np, librosa

for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.mp3"))):
    y, sr = librosa.load(f, sr=22050, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    rms = librosa.feature.rms(y=y, hop_length=512)[0]
    t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
    win = 5.0
    bins = [rms[(t >= s) & (t < s + win)].mean() for s in np.arange(0, t[-1], win)]
    bins = np.array(bins) / max(bins)
    bar = "".join(" .:-=+*#%@"[min(9, int(b * 9.99))] for b in bins)
    print(f"{os.path.basename(f):28s} {float(np.atleast_1d(tempo)[0]):6.1f}bpm |{bar}|")
