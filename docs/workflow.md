# Workflow: song → measured show

This is the exact sequence used for the example shows. Times are for a ~3 minute track with
~600 cues.

```
 song.mp3 ─ffmpeg─► song.wav ─analyze2/onsets─► analysis.json ─slotgrid─► analysis_slots.json
                                                    │
             (look development: dev/lookdev.py, dev/fxshot.py, dev/zoomspec.py)
                                                    ▼
                         examples/<song>/show.py  (+ build_fx.py for effects/palettes)
                                                    │  rig.Show → OSC → Eos
                                                    ▼
             cue list N + event list N in Eos      cues.json + markers.txt
                                                    │
                       reaper_load.py load ─► audio + markers in Reaper
                                                    │
                                runtest.py ─► per-cue timing error + Augment3d contact sheet
```

## 1. Get the audio

```powershell
ffmpeg -i "Song.mp3" -ar 48000 -ac 2 "Song.wav"
```
In PowerShell, use `Copy-Item -LiteralPath` for file names with `[brackets]`. Plain `Copy-Item`
treats them as wildcards and silently copies nothing.

## 2. Analyse

### Songs with a steady beat (EDM, pop)

```powershell
python analyze2.py Song.wav examples\song\analysis.json 110 0
python slotgrid.py Song.wav examples\song\analysis.json        # prints the tracker view
python dev\zoomspec.py Song.wav examples\song\analysis.json out\z.png 20 34 60 74
```

- `110` is a BPM *hint*. The analyser fits the real tempo and, when it lands within 0.06 BPM of
  an integer, snaps to it. Produced music almost always has an integer BPM. The fitted 110.033
  instead of 110.000 put Bangarang's grid 50 ms late by the final drop.
- `0` forces the bar phase (which beat is "1"). Check it on the spectrogram: drops land on a bar
  line. The automatic phase picks the beat with the most low end, which half-time dubstep fools.
- **Read the tracker view.** It shows, per 16th note, where the kick, snare, hats and loudness
  sit. That's how the Bangarang show knows the drop groove is half-time, with chops on 16ths.

### Songs without a grid (cinematic, sound design)

```powershell
python onsets.py Song.wav examples\song\onsets.json
python dev\zoomspec.py Song.wav examples\song\analysis.json out\z.png 0 13 13 26
```

`onsets.py` lists every event with its strength and loudness change, and tags `IMPACT` / `hit`.
Look for **pulse trains**: evenly spaced onsets. Their spacing is the hidden clock to set
effect rates from. In *This Is Your Arena* it was 0.1481 s.

## 3. Develop looks

Before writing hundreds of cues, check how a look actually renders:

```powershell
python dev\lookdev.py beams "S.I(V,100); S.C(V,120); S.P(SP,'Zoom',15); S.aim(V, lambda c,x,y,z:(-x*2.5,y-2,14))"
python dev\fxshot.py wipe 8 0.06 "Chan 201 Thru 248 Full" "Recall_From Effect 830"
```

Both write contact sheets into `out/`. Lessons learned are in [augment3d.md](augment3d.md). One
example: SolaFrame Zoom 7 renders as a blob and Zoom 15 as a laser-thin beam.

## 4. Write the show

A show is a Python file that builds the state for each cue and records it:

```python
from rig import *
S = Show(list_no=6, latency=0.125, outdir=HERE)
S.I(ALL, 0); S.cue(0.0, 0, "Preset")
S.I(V, 100); S.C(V, 0, 0); S.aim(V, lambda c, x, y, z: (x * 3, y, 22))
S.cue(B(48), 0, "DROP", focus=0)
...
S.events(); S.save()
```

- **Simple shows:** use `rig.Show` setters only. See [rig-api.md](rig-api.md).
- **Effect-driven shows:** first build an effect and palette library (`build_fx.py`, see
  [effects.md](effects.md)). Then queue raw command lines that reference those effects and
  palettes, as `examples/arena/show.py` does.

Always dry-run first: it prints the cue sheet and counts.

```powershell
python examples\song\show.py --dry
```

## 5. Record into Eos

```powershell
python examples\song\show.py
```

- **What it does:** wipes the show's cue list and event list, records every cue (label and
  category times included), writes the events, then writes `cues.json` and `markers.txt`.
- **Speed:** about 1 cue/s with continuous motion (Bangarang: 635 cues in ~10 min). Arena:
  102 cues in ~2 min.
- **New event list?** Set its Type to MIDI Timecode and turn External on (see
  [setup.md](setup.md#3-reaper--eos-timecode-mtc)).

## 6. Load Reaper

```powershell
python reaper_load.py status                           # which project is open?
python reaper_load.py open "C:\...\Show-files\aidemo - Song.rpp"
python reaper_load.py load --wav Song.wav --markers examples\song\markers.txt `
       --track "Show Audio - Song" --take "Song - Artist" --expect "aidemo - Song"
python reaper_load.py extend-timecode --seconds 240    # if the song is longer than the TC item
```

`load` **writes into and saves whatever project is open**. That's why it insists on `--expect`.
Keep one `.rpp` per show.

## 7. Measure

```powershell
python eostry.py "Go_To_Cue 6 / 1 Time 0"
python runtest.py examples\song --list 6 --dur 50  0.5 9.3 30.05 40.2
```

Read the error distribution and the worst offenders, then look at the contact sheet in `out/`.

| Symptom | Fix |
|---|---|
| Median far from 0 | Adjust `latency` |
| A single cue far off | It's on the wrong transient: check the tracker view or `onsets.json` |
| Frames black or stale | See [troubleshooting.md](troubleshooting.md) |

## 8. Iterate and save

- **Iterate:** edit the show script, then rerun it. It rebuilds the cue list from scratch.
- **Save:** use **File → Save As** in Eos under a new name so the original show file stays
  untouched.
