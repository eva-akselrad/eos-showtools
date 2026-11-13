# `rig.py`: the state-based cue writer

`rig.Show` lets a show describe **what the stage should look like** at each cue, not which
keys to press. It tracks what the console already has. When a cue is recorded, it sends only the
differences, grouped into as few command lines as possible, then records the cue with its
category times and label.

```python
import os, sys
sys.path.insert(0, "path/to/showtools")
from rig import *

S = Show(list_no=6, dry=False, latency=0.125, outdir=".")
S.wipe()                                   # delete cue list 6 + event list 6

S.I(ALL, 0); S.P(SP, "Zoom", 15); S.strobe(SP, -2)
S.cue(0.0, 0, "Preset")

S.I(V, 100); S.C(V, 120)                   # floor beams green
S.aim(V, lambda c, x, y, z: (x * 3.4, y + 1.5, 22))   # fan out to the sky
S.I(WASH, lambda c, x, y, z: 100 if abs(x) < 4 else 0)  # centre pixel bar
S.cue(26.61, 0, "DROP", focus=0.27)        # beams travel for one 8th note

S.events()                                 # timecode events, fired `latency` early
S.save()                                   # cues.json + markers.txt
```

## `Show(list_no=5, dry=False, fps=30, latency=0.0, outdir=".")`

| Arg | Meaning |
|---|---|
| `list_no` | Eos cue list **and** event list number used by `cue()`, `events()` and `wipe()` |
| `dry` | Don't connect or send anything. Count commands and build `cues` (use for `--dry` cue sheets) |
| `fps` | Event list frame rate (must match the event list, normally 30) |
| `latency` | Seconds to fire every event early. Measure it ([timing.md](timing.md)) |
| `outdir` | Where `save()` writes `cues.json` and `markers.txt` |

## State setters

They only change the *target* state. Nothing is sent until `flush()`, `cue()` or `preview()`.

| Method | State key | Notes |
|---|---|---|
| `I(chs, v)` | `I` | 0–100, or `v(c, x, y, z) -> level`, evaluated per channel: **pixel patterns** |
| `C(chs, hue, sat=100)` | `HS` | Hue in degrees, sat 0–100 (0 = white). Or `hue(c, x, y, z) -> (h, s)` |
| `P(chs, name, value)` | `name` | Any parameter by its command-line name: `Zoom`, `Iris`, `Edge`, `Gobo_Select`, `Beam_Fx_Select`, `Diffusion` … |
| `strobe(chs, v)` | `strobe` | SolaFrame shutter (spots only): `-2` open, `1…13` strobe speed. Sent over OSC |
| `aim(chs, fn_or_xyz)` | `xyz` | XYZ focus target in metres. `fn(c, x, y, z)` receives the fixture's own position |
| `set(chs, key, value)` | any | Low-level |
| `get(c, key)` | | Read a channel's target |

Positions come from `patch.txt` (Augment3d coordinates): **x** is stage right (+) / left (−),
**y** is upstage (+), **z** is up. The audience and the default camera are at **y < 0**.

## Sending and recording

| Method | Does |
|---|---|
| `flush()` | Diffs target against console and sends the changes. Intensity first, then colour, then other parameters, all grouped by value (one command line per value), then one OSC message per moved fixture |
| `cue(t, fade=0, label="", focus=None, color=None, beam=None)` | `flush()`, then `Record Cue L / n Time fade`, plus `Cue L / n Focus Time …` / `Color Time` / `Beam Time` when they differ, plus `Label` (≤30 chars). `t` is the **song time** in seconds. Returns the cue number |
| `preview()` | `flush()` without recording (look development) |
| `run(cmd)` / `osc(addr, *args)` | Raw command line / OSC, sent immediately and **not tracked**. Use for palettes, effects and delays (see the Arena show) |
| `wipe()` | `Delete Cue L / 1 Thru 1999`, `Event L / 1 Thru 1999 Delete` |
| `events()` | `Event L / n Time hh:mm:ss:ff Cue L / n` for every cue. Frame = `round((t − latency) × fps)`. If two cues land on one frame, the later one moves to the next frame |
| `save()` | `cues.json` (list of `{n, t, fade, focus, color, label, frame}`) and `markers.txt` (`seconds<TAB>Qn label`) |

### Continuous motion: the key trick

Every cue's **focus time equals the time to the next cue**. Each move then glides exactly until
the next 8th note or beat, so beams never stop and never drift off the grid. That's how the
Bangarang show moves for its entire length without a single free-running effect:

```python
for i, b in enumerate(steps):                  # steps = list of beat numbers
    nb = steps[i + 1]
    S.aim(V, scanV(42 * math.sin(2 * math.pi * phase(b))))
    S.cue(B(b), 0, f"step {i}", focus=round((nb - b) * P, 2))
```

### Things rig does not track

Palettes, effects, discrete delays and anything else you send with `run()` aren't in the state
model. Two consequences:
- **Effects override tracked values.** If an effect runs on a channel, a later `I()` that
  rig thinks is "already sent" won't stop it. Stop effects explicitly: `S.run("Chan … Effect")`.
- **Out-of-band changes go unnoticed.** If you change something with `run()` or by hand, rig
  still believes its old value. Either set the same thing through rig, or reset
  `S.cur[c].pop(key)` to force a resend.

## Groups and geometry

Defined at the top of `rig.py` for the reference rig. **Edit these channel ranges for yours.**
Everything else is computed from positions.

| Name | Channels | What |
|---|---|---|
| `OHF`, `OHM`, `OHB` | 101–110, 111–120, 121–130 | SolaFrame overhead rows at y = 0, 4, 8 (z ≈ 9.9) |
| `OH` | 101–130 | all overhead spots |
| `VL`, `VR`, `V` | 131–140, 141–150 | SolaFrame floor chevron (z = 1), left/right arms |
| `SP` | 101–150 | all 50 spots |
| `WF`, `WB`, `WOH` | 201–210, 211–220 | SolaPix overhead rows at y = 2, 6 |
| `WFL` | 221–230 | SolaPix floor line (y = 0, z = 1) |
| `TL`, `TR`, `TW` | 231–239, 240–248 | SolaPix side towers, 3 × 3 each |
| `WASH` | 201–248 | all 48 washes |
| `ALL` | 98 fixtures | |
| `LEFT`, `RIGHT` | by x < 0 / x > 0 | |
| `odd(L)`, `even(L)`, `by_x(L)` | helpers | alternate / sort by x |
| `X(c)`, `Y(c)`, `Z(c)`, `POS[c]` | | position lookups |
| `spec(chs)` | | `"Chan 101 Thru 110 + 131"`: compact channel list for the command line |

Pixel patterns are just functions of position, for example:

```python
px_wipe   = lambda p: (lambda c, x, y, z: 100 if abs(x - (-15 + 30 * p)) < 3.5 else 0)
px_checker = lambda k: (lambda c, x, y, z: 100 if (round((x + 14) / 2) + round(y / 2 + z / 2) + k) % 2 == 0 else 0)
S.I(WASH, px_wipe(step / 8))
```

The Bangarang example has a full set: wipe, centre-out, checker, sparkle, rows and a VU fill.

## Performance

Each `run()` waits 30 ms, and each XYZ OSC message 6 ms. Moving all 50 spots costs about 0.3 s
per cue. A 635-cue show with continuous motion records in about 10 minutes.
