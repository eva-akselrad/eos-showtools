# This Is Your Arena: a show built on real Eos effects

- **Track:** *This Is Your Arena* (not included; licence unknown; use your own copy)
- **Length:** 49.8 s, cinematic hype piece with no steady beat. Its rhythmic passages tick on a
  **0.1481 s pulse** (a triplet at 135 BPM)
- **Eos:** cue list 6, event list 6, **102 cues**, plus effects 830–851 and palettes CP/FP 61–68,
  BP 61–62
- **Measured:** 101/102 fired automatically (cue 1 is the 0:00 preset), −46 … +64 ms, median
  +4 ms

The brief: *"the most technically impressive light show possible… a ton of strobe, full-stage
chases… make and use some actual effects."*

## Build order

```powershell
python examples\arena\build_fx.py        # palettes + effect library (deletes effects 801-899 first)
python examples\arena\show.py            # wipes cue list 6 + event list 6, records 102 cues
```

Then set event list 6 to *MIDI Timecode* in Show Control, and turn External on.

## The effect library

See [docs/effects.md](../../docs/effects.md#the-arena-effect-library-examplesarenabuild_fxpy):
- **Step effects 830–840**, each one mapped to rig geometry: columns, rings, height tiers, the
  floor chevron, truss columns, tower stacks, random sparkle, strobes.
- **Absolute effects 841–847** that step through colour or focus palettes.
- **Relative focus effects 850–851.**

## Timeline (song seconds)

| Time | Event in the audio | Cue programming |
|---|---|---|
| 0.22 | Roar | Full white, spots to *Sky Fan* |
| 0.42 | Roar tails off | Red **search L-R** absolute effect; **fanned delay** peels the floor beams off left → right |
| 2.72 / 2.95 / 3.46 | Three hits | **Sparkle** burst, left half, right half |
| 3.70 | Riser | Red floor beams in **BEAM CIRCLE** (BPM override 67.5) |
| 4.72–5.16 | Four hits | Stepping across the rig in four blocks |
| 5.71 | Ticks | **TIERS UP** in red |
| 6.20 | **Impact** | Full white + SolaFrame strobe 13 |
| 6.76–7.21 | Pulses | Wash halves alternate, spots snap Sweep L ↔ R |
| 7.96 | | **CENTRE OUT** |
| 8.37 | **Impact** | Red *X Cross* + strobe |
| 9.13 / 9.26 / 9.42 | | Cyan sparkle, white tunnel impact, **L-R SLAM** |
| 10.15 | Pulse train | **TRUSS RUN** + **CHEVRON RUN** + **TOWER STACK** at once |
| 10.95 | Sustain | Cyan searchlights |
| 13.0 | Riser | Converge white over 1.9 s with a **fanned delay across the washes** |
| 14.99–15.42 | Four hits | Outer-left → inner-left → inner-right → outer-right |
| 15.62 | Pad | Purple circles (BPM 45), magenta towers |
| 17.33 / 17.90 | Ticking | Chevron + towers, then **Rate 180** override |
| 18.65 | Cluster | **STROBE ALL** |
| 19.35 → 19.82 → 20.05 | Silence → **big hit** → gap | Black → audience blinder + strobe → black |
| 20.66 / 20.84 | Restart | Red slam → **WIPE BOUNCE** + **SNAP FAN-X** |
| 21.73 | Soft ticks | Cyan sparkle at **Size 60**, blue search |
| 23.45 | Ambient | Blue **figure-8** (BPM 34) with a fanned delay across the spots |
| 25.84–29.30 | Hits | Tunnel, L, R, full, **TIERS**, **STROBE ODD-EVEN**, L, R |
| **29.97–31.89** | **14-pulse train** | **One cue per pulse**: wipe, ring, tier and odd/even patterns, white/red alternating, spots snapping Fan ↔ Cross, **COLOUR RUN** across the spots |
| 34.21 | **Mega impact** | Audience blinder + spot strobe + **STROBE ALL** washes |
| 35.79 → 36.06 | Gap → hit | Black → sparkle |
| 37.30 / 37.80 / 38.10 | Build | **CENTRE OUT** with Rate 100 → 160 → 240 |
| 38.92 | **Huge impact** | Full white sky fan + strobe |
| 39.05 | Pulses | **WIPE** at BPM 405, **SNAP FAN-X**, **COLOUR RUN** |
| **40.09–42.45** | **The roar** | **Full-stage strobe**: STROBE ALL + spot strobe + **SNAP 4 WAY** → red sparkle + colour run → strobe + snap → odd/even + 4-way |
| 42.46 – 43.67 | Pulses, slams, gap | L-R SLAM, red slam, white slam, black |
| 43.91 | Ticks | **TIERS UP** white, beams straight up |
| 44.85 → 47.0 | Tail | Final white sky fan → red over 1.5 s → fade out |

## Files

- `build_fx.py`: palettes + effects. `python build_fx.py pal` or `fx` builds one half.
- `show.py`: the show. It queues raw command lines (effects and palettes) and uses
  `rig.Show` for recording, strobe, XYZ and events.
- `onsets.json`: `onsets.py` output (the event list the timeline is built from).
- `analysis.json`, `analysis_slots.json`: grid analysis (tempo 134.8 BPM, unsnapped: there is
  no strict grid).
- `cues.json`, `markers.txt`
