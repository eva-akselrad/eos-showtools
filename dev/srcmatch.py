"""srcmatch.py - find where each source song appears inside a mashup (chroma+onset cross-correlation).
python srcmatch.py mashup.wav source1.mp3 [source2.mp3 ...]
For every 4 s window of the mashup prints the best-matching source + its time offset + score."""
import sys, numpy as np, librosa
sr, hop = 11025, 256
def feat(f):
    y, _ = librosa.load(f, sr=sr, mono=True)
    C = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    C = C / (np.linalg.norm(C, axis=0, keepdims=True) + 1e-9)
    return C
M = feat(sys.argv[1]); srcs = [(f, feat(f)) for f in sys.argv[2:]]
fps = sr / hop; W = int(4 * fps)
for s0 in range(0, M.shape[1] - W, int(2 * fps)):
    w = M[:, s0:s0 + W]
    best = []
    for f, S in srcs:
        # correlate window against every offset in the source (cosine, summed over frames)
        sc = np.array([np.sum(w * S[:, o:o + W]) / W for o in range(0, S.shape[1] - W, 2)])
        o = int(np.argmax(sc)) * 2
        best.append((sc.max(), f.split("\\")[-1][:22], o / fps))
    best.sort(reverse=True)
    b = best[0]
    print(f"{s0 / fps:6.1f}s  {b[1]:22s} @ {b[2]:6.1f}s  score {b[0]:.2f}   | 2nd {best[1][1][:12]} {best[1][0]:.2f}" if len(best) > 1 else "")
