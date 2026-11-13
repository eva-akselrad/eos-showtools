# Timing: getting cues on the music

The examples land every timecoded cue within about **±60 ms** of its target sound, with a
median of +4 to +14 ms. Four things make that possible.

## 1. An exact beat grid (`analyze2.py`)

librosa's per-beat tracker jitters by ±50 ms, which is visible as sloppy cues. Produced music
runs on a fixed clock, so `analyze2.py`:

1. fits one constant tempo through all the tracked beats (robust least squares)
2. **snaps to an integer BPM** when within 0.06
3. finds the grid phase by folding spectral flux modulo one 8th note. It uses a 23 ms analysis
   window: a 93 ms window puts the flux peak 40 ms *before* the real attack
4. picks beat vs off-beat by where the low end sits.

Result for Bangarang: 110.000 BPM, t0 = 0.4287 s. The 8th-note phase agreed within 4 ms across
all four sections of the song. The unsnapped fit (110.033 BPM) drifted 50 ms by the final drop.

**Always eyeball the downbeat** with `dev/zoomspec.py`. Half-time grooves fool the automatic
bar phase, so force it with the 4th argument.

## 2. Cues on real sounds, not just the grid

- `slotgrid.py` gives each 16th note an onset strength per band. Shows place extra cues on
  strong off-grid 16ths (the Bangarang drops) and blackouts on detected gaps.
- For songs with no grid, `onsets.py` gives the event list directly (*This Is Your Arena*).
  Evenly spaced trains reveal a pulse clock to set effect rates from.

## 3. Latency compensation

Measured with `examples/latency_test`. Eos reported each event firing **~117 ms after the audio
was heard**, with about ±50 ms of jitter.
- **Where the delay comes from:** Reaper's output buffer (WaveOut, ~46 ms) plus MTC decoding.
  Eos needs several quarter-frame messages to assemble a full timecode position.
- **How the shows correct for it:** every event is written `latency = 0.125 s` early:
  `frame = round((t − latency) × 30)`.
- **Your system will differ.** Run the latency test and set `SHOWTOOLS_LATENCY` or
  `Show(latency=…)`.

**30 fps quantisation:** events can only sit on 33 ms frames. Two cues can't share a frame, so
`rig.Show.events()` pushes the later one to the next frame. Cues on consecutive 16th notes at
135 BPM (111 ms apart) are fine.

**Augment3d adds its own render delay** of roughly 100 ms. A hit can *look* late in the
visualiser even when the console fired on time. On real fixtures that delay isn't there, so
the shows don't compensate for it.

## 4. Measuring, not guessing: how `runtest.py` measures

The first version started Reaper and assumed playback began "now". The launch delay of
`reaper.exe` (~0.4 s) then appeared as a constant error. The current method:

1. `reaper/play_sync.lua` logs pairs of (`reaper.time_precise()`, `reaper.GetPlayPosition()`)
   every UI tick, flushing every line. `GetPlayPosition` is the **audible** position.
2. Both `time_precise()` and Python's `time.perf_counter()` read the Windows
   QueryPerformanceCounter. The median of `perf − position` gives the offset that maps any
   instant to song time.
3. Eos's `/eos/out/event/cue/<list>/<n>/fire` messages are stamped on arrival. Each cue's error
   is (song time at fire) − (planned time).

The fire error therefore includes Eos's MTC chase latency (which latency compensation cancels)
and its jitter. It does **not** include Augment3d render time.

Results:

| Show | Cues | Fired | Error min / median / max |
|---|---|---|---|
| Volatile Reaction (first harness) | 164 | 163* | ±50 ms around a constant +0.38 s harness offset |
| Bangarang | 635 | 549** | −40 / +14 / +75 ms |
| This Is Your Arena | 102 | 101* | −46 / +4 / +64 ms |

\* Cue 1 sits at 0:00 and is already active when playback starts.
\** Playback stopped at 3:00 because the Timecode Generator item ended there. It was then extended to 4:00.
