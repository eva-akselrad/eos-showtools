# Tools reference

Every script runs from the repo root. Paths and window titles come from [`config.py`](../config.py)
(see [setup.md](setup.md#5-configpy)).

- [Console I/O](#console-io): `eosctl.py`, `eostry.py`, `eosui.py`
- [Show writing](#show-writing): `rig.py`, `fxlib.py`
- [Analysis](#analysis): `analyze2.py`, `slotgrid.py`, `onsets.py`, `analyze.py`
- [Playback and measurement](#playback-and-measurement): `runtest.py`, `reaper_load.py`, `reaper/*.lua`
- [Desktop and visuals](#desktop-and-visuals): `deskctl.py`, `look.py`
- [dev/](#dev): look development and probes

---

## Console I/O

### `eosctl.py`

OSC-over-TCP client for Eos. Port 3032, 4-byte big-endian length framing. A background thread
receives everything Eos sends and timestamps it.

**CLI**
```
python eosctl.py ping                       reply to /eos/ping
python eosctl.py cmd "Chan 101 Full"        run a command line (Enter appended), print the echo
python eosctl.py get /eos/get/cue/6/count   send any OSC address, print replies for ~1 s
python eosctl.py patch > patch.txt          dump the patch (labels, types, Augment3d positions)
python eosctl.py list fx                    list a target: cp fp bp ip preset fx group macro sub cuelist cue/6 ...
python eosctl.py watch 10                   print everything Eos sends for 10 s
```

**Python**
```python
from eosctl import Eos
e = Eos()                                   # host/port from config
e.run("Chan 101 Thru 110 Full")             # newcmd + '#' (Enter), then sleep `pause`
e.cmd("Chan 101 ", new=True)                # /eos/newcmd without Enter; new=False appends (/eos/cmd)
e.send("/eos/chan/101/param/x_focus/y_focus/z_focus", 1.0, 4.0, 0.0)
e.send("/eos/subscribe", 1)                 # stream state: cue fires, wheels, softkeys, cmd line
msgs = e.drain()                            # [(time.time(), "/eos/out/...", [args])]
e.wait(lambda a, p: a.endswith("/fire"))    # block until a matching message arrives
e.request("/eos/get/fx/count")              # send, collect replies until quiet
e.count("cp"); e.items("fp")                # /eos/get/<t>/count and /index/N
```

Useful addresses (all verified):

| Address | Purpose |
|---|---|
| `/eos/newcmd "text#"` | replace the command line and run it (`#` = Enter) |
| `/eos/cmd "text"` | append to the command line (use `"#"` to confirm a *Please Confirm* prompt) |
| `/eos/key/<name>` (1.0 then 0.0) | hard key. Verified: `live`, `effect` (press twice = effect list in Blind), `enter`, `displays` |
| `/eos/softkey/<n>` | press softkey *n* (`eosui.py` maps labels → numbers) |
| `/eos/param/<name> value` | set a parameter on the **selected** channels (use for negative values) |
| `/eos/chan/<n>/param/x_focus/y_focus/z_focus x y z` | aim one fixture at a point in metres |
| `/eos/cue/<list>/<cue>/fire` | fire a cue with its own timing (what an event does) |
| `/eos/out/event/cue/<list>/<cue>/fire` | **sent by Eos** when a cue fires (subscribe first) |
| `/eos/get/patch/count`, `/eos/get/cue/<l>/<c>` | query show data |

### `eostry.py`

Run command lines and print exactly what the console echoed. **Use this to check every new
piece of syntax before putting it in a show.**
```
python eostry.py "Cue 5 / 1 Focus Time 0.5" "osc:/eos/param/shutter_strobe -2" "key:live"
```
Prefixes: `osc:` sends a raw OSC message (numbers become floats), and `key:` presses a hard key.
Everything else is a command line with Enter.

### `eosui.py`

Drives features that only exist as softkeys, such as the event list *Type*. It reads the live
softkey labels and presses them by name.
```
python eosui.py "run:Effect 820" "soft:Type" "soft:StepBased" "key:enter"
```
`run:` is a command line with Enter, `cmd:` is a command line without Enter (`#` inside = Enter),
`soft:<label>` presses a softkey, and `key:<name>` presses a hard key. After each step it prints
the command-line echo, and at the end the current softkey labels.

---

## Show writing

### `rig.py`

The state-based cue writer and the rig's groups and geometry. Full reference:
[rig-api.md](rig-api.md).

### `fxlib.py`

Builds Eos effects (step and absolute), palettes and effect attributes from typed commands, plus
geometry helpers for chase steps (`columns`, `rings`, `levels_z`). Full reference:
[effects.md](effects.md).

---

## Analysis

### `analyze2.py`

```
python analyze2.py song.wav out.json [bpm_hint] [bar_phase]
```

1. Tracks beats with librosa, then fits **one constant-tempo grid** with an iterative robust
   linear fit.
2. If the BPM is within 0.06 of an integer, **snaps to it**. It then finds the grid phase by
   folding spectral flux (23 ms window) modulo one 8th note at 4 ms resolution. Beat vs off-beat
   is decided by where the low end sits.
3. Detects per-band transients: kick (30–130 Hz), snare (1.5–5 kHz), hats (7–11 kHz) and full
   band. Each one is tagged with its nearest 16th slot and offset in ms.
4. Builds a per-bar energy table (rms, low, mid, high, kick count) and prints it.

Output JSON keys: `dur bpm t0 period phase beats[] bars[] trans{kick,snare,hats,full}[] beat_resid_ms[]`.
Beat *k* is at `t0 + k*period`. Bar *b* (1-based) starts at beat `phase + 4*(b-1)`.

### `slotgrid.py`

```
python slotgrid.py song.wav analysis.json [beat_from beat_to]
```

Writes `analysis_slots.json`: one entry per 16th note with `t kick snare hats full rms gap`.
Onset strengths are normalised 0–1, taken from a ±25 ms window. `gap` marks a slot much quieter
than its neighbours (a stop or a suck-out). It prints a **drum-tracker view**, one row per bar
and one character per 16th (` .:-=+*#%@` = 0…1):

```
beat   time   | kick             | snare            | ...
  48   26.61 | %. :...=... .=.  | --..::-:=:-*+.-. | ...    <- drop: kick on 1, chops on 12-13
```

### `onsets.py`

```
python onsets.py song.wav out.json
```

For tracks without a grid. It lists every onset (backtracked to its attack) with strength,
loudness before/after, low-end and high-end content, and tags `IMPACT` (big jump in loudness)
or `hit`. Evenly spaced runs reveal the track's pulse clock.

### `analyze.py`

The first-generation analyser, kept because `examples/volatile_reaction` uses its output
format (`beats`, `downbeat_phase`, `sections`, `hits`). Prefer `analyze2.py` for new work: this
one does not snap the tempo.

---

## Playback and measurement

### `runtest.py`

```
python runtest.py <show dir> [song times to screenshot...] --list N [--dur S]
```

Plays the show from Reaper, measures every cue fire, and captures Augment3d at the given song
times. It needs `<show dir>/cues.json`. How the measurement works is explained in
[timing.md](timing.md#how-runtestpy-measures).

Output:
- `cues fired X of Y`
- a fire-error distribution
- the worst offenders
- `<show dir>/fired.json`
- `out/<show>_run.png`

It refuses to run unless exactly one Reaper is running, and it closes any extra instance that
`-nonewinst` spawns.

### `reaper_load.py`

A safe front-end for the ReaScripts in `reaper/`:
```
python reaper_load.py status
python reaper_load.py open  "C:\path\project.rpp"
python reaper_load.py load  --wav song.wav --markers examples\x\markers.txt --track "Show Audio - X" --take "X - Artist" --expect "aidemo - X"
python reaper_load.py extend-timecode --seconds 240
python reaper_load.py play | stop
```

`load` deletes the project's markers, (re)uses the `Show Audio*` track, places the WAV at 0:00,
mutes the demo's leftover tracks, adds one marker per cue, and **saves the open project**. It
refuses to run unless `--expect` matches the open project's title.

### `reaper/*.lua`

| Script | Job file keys | Does |
|---|---|---|
| `reaper_song.lua` | `wav track take markers log` | load song + markers, save |
| `open_project.lua` | `rpp` | open a project without a save prompt (discards unsaved changes) |
| `extend_timecode.lua` | `seconds log` | lengthen the Timecode Generator item, save |
| `play_sync.lua` | (none) | wait 7 s, play from 0, log `(time_precise, GetPlayPosition)` to `play_sync.txt` (flushed each line) |
| `play.lua` / `stop.lua` | (none) | transport |

The job file is `reaper/reaper_job.txt` (git-ignored; see `reaper_job.example.txt`).
`reaper_load.py` writes it for you.

---

## Desktop and visuals

### `deskctl.py`

A DPI-aware desktop control CLI and module that uses SendInput, win32gui and PIL.
```
python deskctl.py windows                         list top-level windows (hwnd, rect, pid, title)
python deskctl.py shot out.png [--win TITLE] [--scale 0.5] [--region x0 y0 x1 y1]
python deskctl.py focus "Eos : 1"
python deskctl.py click 1082 916 [--right] [--double]
python deskctl.py scroll 900 450 3                (positive = wheel up = Augment3d zoom in)
python deskctl.py type "text" | key ctrl+s | move x y | drag x0 y0 x1 y1 | pos
python deskctl.py winrect TITLE x y w h | max TITLE | restore TITLE | min TITLE
```

`focus()` does nothing if the window is already in front. Otherwise it parks the cursor in the
screen corner before the Alt tap Windows needs to allow a focus change. This keeps the Alt tap
from reaching Augment3d's camera controls with the cursor over the viewport.

### `look.py`

```
python look.py NAME [N] [INTERVAL]      -> out/NAME.png
```

Screenshot the Augment3d area, optionally as a sequence of frames.

---

## dev/

| Script | Use |
|---|---|
| `dev/lookdev.py NAME "code" ["code" ...] [--full]` | Each code string runs with a live `rig.Show` named `S`, which is then previewed and captured. Makes fast A/B contact sheets of looks. |
| `dev/fxshot.py NAME N INTERVAL "cmd" ...` | Runs command lines, then captures N frames at INTERVAL. Use it for effects and chases. |
| `dev/probe.py CHAN param v1 v2 ...` | Sets a parameter to several values and prints how the console labels each one. Finds ranges, e.g. SolaFrame zoom 7–55 and Iris 100 = open. |
| `dev/xyztest.py X Y Z` | Aims the floor beams at a point to check XYZ orientation. |
| `dev/zoomspec.py song.wav analysis.json out.png t0 t1 [t0 t1 ...]` | Mel spectrogram strips with **beat numbers** and an RMS curve, for finding drops and gaps by eye. |
| `dev/specplot.py song.wav analysis.json out.png` | Whole-song spectrogram in 4 rows with bar numbers. |
| `dev/survey.py FOLDER` | Tempo survey of the candidate MP3s in a folder. |
