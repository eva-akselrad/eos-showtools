# Volatile Reaction: the first show

- **Track:** *"Volatile Reaction"*, Kevin MacLeod ([incompetech.com](https://incompetech.com)),
  licensed under Creative Commons: By Attribution 4.0. Free download from incompetech. Public use
  requires the credit line.
- **Length / tempo:** 2:45, 152 BPM
- **Eos:** cue list 5, event list 5, **164 cues**
- **Analysis:** `analyze.py` (first generation). Beats, downbeat phase, per-bar energy, section
  boundaries, strong hits

## Structure

| Bars | Section | Look |
|---|---|---|
| 1–6 | Intro | Blue "cathedral": 20 floor beams converge high above the stage |
| 7–19 | Build | Magenta gobo + prism, warming, a cue on each hit in the drum run |
| 18–19 | Riser | White surge, strobe, 3 stabs, then **suck-out blackout** before the drop |
| 20–37 | Chorus 1 | White blinder drop, colour/position change every 2 bars, L/R bumps |
| 38–46 | Verse 2 | Teal searchlight sweeps |
| 47–60 | Section E | Purple waves; three hits slam left, right, centre |
| 61–65 | Breakdown | Lone centre beam → cathedral ignites with accelerating strobe |
| 66–73 | Staccato | **One cue per detected hit** |
| 74–85 | Build 2 → riser 3 | Searchlights, whitening, full strobe, suck-out |
| 86–101 | Final chorus | Gold blinder, colour every 2 bars, row chases across the trusses |
| 102– | End | White hit, then floor beams fade to blue |

## What it introduced

- **XYZ focus aiming.** Every beam shape is a function of fixture position (`T_CATH`,
  `T_FANUP`, `T_CROSS`, `T_WAVE(phase)`, `T_SWEEP(angle)` …), sent as
  `/eos/chan/N/param/x_focus/y_focus/z_focus`.
- **Timecode from Reaper (MTC) into an Eos event list**, with events generated from the
  analysis.
- **Measurement:** the first `runtest.py` fired 163/164 cues automatically, all within ±50 ms of
  each other. The whole show sat on a constant +0.38 s offset, which turned out to be the
  harness's own Reaper launch delay. The later version of `runtest.py` measures against
  Reaper's audible play position instead.

## What it got wrong (and the next show fixed)

- The per-beat librosa grid jitters, so some cues felt early or late. Fixed in Bangarang by
  `analyze2.py`, which snaps to an exact BPM.
- No latency compensation: Eos fires ~117 ms after the audio is heard. Fixed by
  `latency=0.125`.
- Mostly static looks between cues.

## Files

- `show.py`: the show. Uses `eosctl` directly, before `rig.py` existed. `--dry` prints the cue
  sheet.
- `analysis.json`: `analyze.py` output.
- `cues.json`, `markers.txt`: cue sheet and Reaper markers.
