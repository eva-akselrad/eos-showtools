# Latency test

Measures how late Eos fires timecode events compared with the audio you hear from Reaper.

```powershell
python examples\latency_test\show.py              # WIPES cue list 5 + event list 5 (or --list N)
python runtest.py examples\latency_test --list 5 --dur 17
```

The show is a blackout plus 30 cues toggling the overhead washes every 0.5 s. A few cues are
offset by 11 or 22 ms so they don't all sit on frame boundaries. Its events are written with
**zero** latency compensation.

The reported **median fire error** is your system's latency. Reference result:

```
cues fired 31 of 31
fire error (song time at fire - planned), ms:  min 89  p10 97  median 117  p90 184  max 190
```

So the other shows use `latency=0.125`. Put your value in `SHOWTOOLS_LATENCY` or pass
`Show(latency=…)`. Background is in [docs/timing.md](../../docs/timing.md).
