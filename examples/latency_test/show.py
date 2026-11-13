"""Latency test - measure how late Eos fires timecode events relative to the audio you hear.

Builds 31 cues in cue list 5 (a blackout + 30 overhead-wash on/off toggles every 0.5 s, with
small deliberate sub-frame offsets) and event list 5 with latency compensation set to ZERO.
Then run:

    python runtest.py examples/latency_test --list 5 --dur 17

The median "fire error" it prints is your system's Reaper -> MTC -> Eos latency. On the machine
these shows were built on it was ~117 ms (Reaper WaveOut output buffer + MTC quarter-frame
decode), with roughly +/-50 ms jitter, which is why the other examples use latency=0.125.
Put your measured value in SHOWTOOLS_LATENCY or pass Show(latency=...).

WARNING: wipes cue list 5 and event list 5 in the open show (use --list N to pick another).
    python show.py [--dry] [--list N]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from rig import *

LIST = int(sys.argv[sys.argv.index("--list") + 1]) if "--list" in sys.argv else 5
S = Show(list_no=LIST, dry="--dry" in sys.argv, latency=0.0, outdir=HERE)
if not S.dry:
    S.wipe()
S.I(ALL, 0)
S.cue(0.0, 0, "blk")
for k in range(30):
    t = 1.0 + k * 0.5 + (k % 3) * 0.011
    S.I(WOH, 100 if k % 2 == 0 else 0)
    S.cue(t, 0, f"t{k}")
if not S.dry:
    S.events()
S.save()
print("cues", len(S.cues))
