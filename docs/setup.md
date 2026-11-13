# Setup

This page gets you from a fresh checkout to "Eos answers, Reaper plays, cues fire on timecode".
Every step was needed to build the example shows.

## 1. Python

```powershell
py -3.13 -m pip install -r requirements.txt
ffmpeg -version            # needed to convert MP3 -> WAV for analysis and Reaper
```

`requirements.txt` covers the following:
- `python-osc`: OSC encoding.
- `librosa`, `numpy`, `scipy`: analysis.
- `matplotlib`: spectrogram plots.
- `Pillow`: screenshots and contact sheets.
- `pywin32`: window control.

> Run the tools from the repo root, or use the examples as written: each example script adds the
> repo root to `sys.path` itself.

## 2. Eos: OSC over TCP

The tools talk to Eos on **TCP port 3032**. They use OSC 1.0 framing, where every packet is
prefixed with a 4-byte big-endian length.

1. In Eos: **Setup → System → Show Control → OSC**.
2. Enable **OSC RX** and **OSC TX**.
3. Make sure the TCP server is on. 3032 is the "OSC 1.0 / packet length" port. Port 3037 uses
   SLIP framing and is **not** supported by `eosctl.py`.
4. Test it:

```powershell
python eosctl.py ping                 # prints the /eos/out/ping reply
python eostry.py "Chan 101 Full" "Chan 101 Out"
```

`eostry.py` prints the command line as the console echoed it. That's the fastest way to check
any syntax.

### Dump your patch

`rig.py` builds its groups and geometry from the Augment3d positions in `patch.txt`:

```powershell
python eosctl.py patch > patch.txt
```

The groups in `rig.py` (OHF, OHM, OHB, VL, VR, WF, WB, WFL, TL, TR, …) are channel ranges of the
reference rig. **If your rig is different, edit the group definitions at the top of `rig.py`.**
The geometry helpers (`X()`, `Y()`, `Z()`, `columns()`, `rings()`, `levels_z()`, LEFT/RIGHT) work
from positions automatically. See [rig-api.md](rig-api.md#groups-and-geometry).

## 3. Reaper → Eos timecode (MTC)

The shows are triggered by **Eos event lists of type MIDI Timecode**, chasing timecode that
Reaper generates while the song plays.

The reference project (`aidemo.rpp`) is wired like this:

```
Reaper track 1: "Timecode Generator" item (Insert → SMPTE LTC/MTC Timecode Generator),
                30 fps, starting at 00:00:00:00, MIDI hardware output → loopMIDI port
                          │  MTC
                          ▼
loopMIDI virtual port ──► Eos MIDI input ──► Event list N (Type: MIDI Timecode, Source 1, 30 fps)
                                                │  events: "Time hh:mm:ss:ff → Cue N/x"
                                                ▼
                                           Cue list N
```

Checklist:
- **Timecode item length.** It must run past the end of the song. When it stops, Eos stops
  firing. The original demo item was only 180 s long; `python reaper_load.py extend-timecode --seconds 240`
  fixes that.
- **Event list type.** A new event list created from the command line defaults to **SMPTE**. Set
  it to **MIDI Timecode** in the Show Control display: click the list's *Type* cell, then press
  the *MIDI Timecode* softkey, then Enter. This is the one step that needs the UI. There's no
  command-line syntax for it.
- **External on.** `Event 6 / External` toggles External (the echo says *Enable* or *Disable*).
- **Turn off other event lists' External** if they would fire other shows on the same timecode.

## 4. Augment3d view

`runtest.py`, `look.py` and the `dev/` tools capture the screen rectangle in `config.VIEW_BBOX`.
The default `0,34,1858,898` is the full-width Augment3d tab on a 1920×1080 screen.
- **Set the rectangle** with `SHOWTOOLS_VIEW_BBOX` if your Augment3d sits elsewhere.
- **Stay in Live.** Augment3d shows **Blind** data while the console is in Blind, so captures go
  black or stale. See [augment3d.md](augment3d.md).
- **Keep it in front.** Eos must be the foreground window for captures. The tools refocus it.

## 5. `config.py`

All machine-specific values live in `config.py`. Each can be overridden with an environment
variable:

| Setting | Env var | Default |
|---|---|---|
| Eos host/port | `SHOWTOOLS_EOS_HOST`, `SHOWTOOLS_EOS_PORT` | `127.0.0.1`, `3032` |
| Eos window title (substring) | `SHOWTOOLS_EOS_WINDOW` | `Eos : 1` |
| Reaper executable | `SHOWTOOLS_REAPER` | `C:\Program Files\REAPER (x64)\reaper.exe` |
| Output folder for images/logs | `SHOWTOOLS_OUT` | `<repo>/out` (git-ignored) |
| Augment3d capture rectangle | `SHOWTOOLS_VIEW_BBOX` | `0,34,1858,898` |
| Timecode latency compensation | `SHOWTOOLS_LATENCY` | `0.125` s |

## 6. Measure your latency (do this once)

```powershell
python examples\latency_test\show.py           # WIPES cue list 5 + event list 5
python runtest.py examples\latency_test --list 5 --dur 17
```

The median *fire error* is how late Eos fires relative to what you hear. Use it as the
`latency` of your shows. See [timing.md](timing.md).
