# Bangarang: 635 cues of continuous, beat-locked motion

- **Track:** *Bangarang*, Skrillex ft. Sirah (commercial, not included; use your own copy)
- **Length / tempo:** 3:36, **110.000 BPM** (t0 = 0.4287 s)
- **Eos:** cue list 5, event list 5, **635 cues**, built in ~10 minutes
- **Measured:** −40 … +75 ms, median +14 ms (549 cues measured in the run that stopped at 3:00;
  see [timing.md](../../docs/timing.md))

The brief: *more energy, pixel-style effects, laser looks (with no lasers in the rig), much
more movement, better timing.*

## Structure (beats on the exact grid)

| Beats | Section | Programming |
|---|---|---|
| 0–16 | Intro synth stabs | Pixel twinkles on every detected 8th-note stab; two centre beams slowly open |
| 16–40 | Drums | Green laser fans scanning every beat; overheads join at 24, pixel wipes at 32; floor line pulses on the kick |
| 40–47 | Build 1 | Steps accelerate ¼ → ⅛ → 1/16; beams converge into a cone and whiten; towers fill like a VU meter; strobe ramps |
| 47 | — | **Suck-out** blackout |
| 48–112 | **Drop 1** | 2-bar cycles: half-time BOOM on beats 1 and 3, a cue every 8th for pixel chase + motion, extra stabs on strong off-grid 16ths |
| 112–114 | Stutter tail | Three crossing stabs, then out |
| 114–140 | Verse | Each kick of the 3-3-2 pattern jumps the pixel and swings red/amber beams |
| 140–143 | Build 2 | Red converge → white, strobe ramp, suck-out |
| 144–208 | **Drop 2** | As drop 1 + **laser zaps**: on each rising synth sweep (beats 151.5 + 16k), floor beams slam low with strobe, then fan to the sky |
| 208–241 | Four-on-the-floor | Rainbow: full-rig boom on every beat, checkerboard on the off-beats, beams scanning; 16th strobe into the breakdown |
| 241–272 | Breakdown | Deep-blue cathedral rotating slowly; white flash on the lone blip at beat 256.25 |
| 272–303 | Build 3 | Kicks return; ¼ → ⅛ → 1/16 steps, red → white, strobe ramp, suck-out |
| 304–368 | **Final drop** | Everything: complementary colours, strobing overheads on the boom, zaps every 16 beats |
| 368–388 | Outro | Last hit, then drifting purple sparkles fading to black |

## Techniques

- **Exact grid:** `analyze2.py` snapped 110.033 → 110.000 BPM and phase-locked to the
  transients. The tracker view (`slotgrid.py`) revealed the half-time drop groove.
- **Continuous motion without effects:** every cue's focus time = time to the next cue. The
  shapes (`scan`, `cone`, `wave`, `breathe`, `cross`) are animated by the phase within each bar
  and change every 2 bars.
- **Pixel patterns:** the 98 fixtures form a pixel grid in front view. Patterns are functions
  of position: `px_wipe`, `px_center`, `px_checker`, `px_sparkle`, `px_rows`, `px_vu`.
- **Laser look:** SolaFrame Zoom 15 (see [augment3d.md](../../docs/augment3d.md)).

## Files

- `show.py`: the show (`--dry` prints section counts; `--sheet` adds the full cue sheet)
- `analysis.json`, `analysis_slots.json`: `analyze2.py` + `slotgrid.py` output
- `cues.json`, `markers.txt`
