# Troubleshooting

Every entry here happened while building the examples.

| Symptom | Cause | Fix |
|---|---|---|
| `Error: Syntax Error` on `Record Cue 5/1` | Eos needs spaces around `/` | `Record Cue 5 / 1` |
| Strobe value `-2` arrives as `- 20` | Negative numbers misparse on the command line | `osc:/eos/param/shutter_strobe -2` (rig does this) |
| Effect timing fields stay at defaults | More than 2 decimals (`0.074`) | Round to hundredths; use BPM/Rate for precision |
| `Time - Error: Syntax Error` editing an effect | Blind kept a *different* effect/step as context | Send `Effect <n>` alone first |
| Bounce or Random switched **off** after a rebuild | Attributes toggle | Delete effects (`F.delete`) before rebuilding |
| *Please Confirm* never confirms | Sent `#` with `/eos/newcmd` (replaces the command) | Send `#` with `/eos/cmd` |
| Palette applied but colour wrong (washes green) | `Color_Palette 61 Zoom 5` on one line | One palette per command line |
| `Effect Does Not Exist` | Creating effects from Live | Open the effect list: `[Effect][Effect]` (Blind) |
| Timecode test fires **0 cues** | New event list is SMPTE | Show Control: Type → *MIDI Timecode* |
| Cues stop firing partway through the song | Reaper's Timecode Generator item ends | `python reaper_load.py extend-timecode --seconds 240` |
| Cues fire but Augment3d is **black** | Console in Blind (Augment3d shows Blind) | Go to Live |
| Typed `Chan 101` becomes `Event 6 / 101` | Blind event-list context | Go to Live |
| Early frames of a run look **frozen or wrong** | Augment3d paused while Reaper was in front; or the sync log wasn't flushed | Current harness: 7 s pre-roll, refocus Eos, flushed log |
| Contact sheet shows **Reaper** instead of the stage | Launching a ReaScript raises Reaper | `runtest.py` refocuses Eos; `deskctl.py focus "Eos : 1"` |
| A second Reaper (with nag dialogs) appears | `reaper.exe -nonewinst` missed the running instance | `runtest.py` / `reaper_load.py` detect and close it; retry |
| Song + markers landed in the **wrong project** | `reaper_song.lua` writes into and saves whatever is open | Use `reaper_load.py load --expect …`; restore from Reaper's `Backups\*.rpp-bak` |
| `Copy-Item` copied nothing | `[brackets]` in the file name are wildcards | `Copy-Item -LiteralPath` |
| Analysis says 110.033 BPM, cues drift late | Unsnapped tempo | `analyze2.py` snaps automatically when within 0.06 |
| Downbeats half a bar off | Half-time groove fooled the bar phase | Force it: `analyze2.py song.wav out.json 110 0` |
| Augment3d camera "moves" between captures | Usually it doesn't: different fixtures are lit. Otherwise the Alt tap or `Chan 1` selection | `deskctl.focus` parks the cursor; compare against a lit-rig frame |
| Clicking an Eos tab does nothing useful | The Live key changed the workspace page | Click the page icon at the top (e.g. 128,16), then the tab |
