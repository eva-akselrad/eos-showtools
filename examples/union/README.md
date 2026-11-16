# Union: a Philadelphia Union show at Subaru Park

- **Venue:** Subaru Park, a [Mini Skyline](https://miniskyline.com) GLB built from OpenStreetMap, Overture Maps and open elevation data (see [Model credits](#model-credits)) imported into Augment3d at **Scale 10.4**, Rotation (−90, 0, 80), Position (69.9, −13.7, −2.94). That makes the pitch a true 104 × 64 m, centred on the world origin with its long axis on X.
- **Audio:** a mashup of *Party Till We Die* (MAKJ & Timmy Trumpet ft. Andrew W.K.) and the Philadelphia Union "Doop" song. 128.000 BPM, 4:26. Not included.
- **Eos:** cue list 7, event list 7 (MIDI timecode). **309 cues**, groups 701–740, palettes CP 71–76, FP 71–78 / 81–84, effects 880–895.
- **Measured (v3):** all 308 timed cues fired, −45 … +64 ms, median +7 ms.

![run](union_run.png)

## Rig (`rig_union.py` computes every position from the stadium mesh)

| Channels | Fixture | Where |
|---|---|---|
| 301–340 | 40 × Elation **Proteus Excalibur** (IP65 beam) | upright on top of the roof leading edge, 20 per long side; render beam angle 5° |
| 401–424 | 24 × GLP **JDC2 IP** (M1) | hung under the roof edge between the beams |
| 425–432 | 8 × JDC2 IP | west scoreboard tower face / east stand top |
| 501–532 | 32 × Elation **Proteus Hybrid Max** (Standard) | ring around the pitch at ground level; render beam angle 5° |

Why these:
- **Outdoor-rated:** all three are IP65.
- **Excaliburs:** long-throw beams, mounted upright so they can reach the sky. Hung under the roof, the tilt range clamps them below about 45°.
- **JDC2s:** strobes and blinders on the roof edge.
- **Hybrid Max ring:** builds a beam "tent" over the pitch. The Proteus Rayzor 760 was tried first, but its wide wash barely renders in Augment3d.

## Library (`build_fx.py`)

| | |
|---|---|
| Colour | 71 Union Navy · 72 Union Gold · 73 Union Light Blue · 74 White · 75 Deep Blue · 76 Warm Gold |
| Excalibur focus | 71 Sky Fan · 72 Sky Cross · 73 Centre Spot · 74 Crown · 75/76 Sweep W/E · 77 Pillars · 78 Pitch Lines |
| Ring focus | 81 Ring Up · 82 Tent · 83 Ring Out · 84 Into Stands |
| Step effects | 880 **RATTLESNAKE** (comet chase round the ring, after the snake on the crest) · 881 SIDE SLAM N-S · 882 ROOF WIPE W-E · 883 JDC STROBE · 884 SPARKLE · 885 ENDS PING · 886 **13 STARS** (13 random fixtures, after the crest's stars) |
| Absolute | 890 NAVY-GOLD · 891 SKY SNAP (fan ↔ cross) · 892 SKY SWEEP |
| Relative | 895 SKY CIRCLE |

## Show (v3, fixed audio, built for the press-box view)

The corrected audio is 2:13 with a **piecewise tempo map** (`tempomap.json`, built with `tempomap.py`):
- **0:00–0:51:** 128.007 BPM
- **0:53–1:39:** 143.29 BPM
- **1:39 on:** 143.19 BPM. The final drop is a separate edit that re-enters about a quarter-beat off the previous grid.

Each part's grid is fitted to the strong kick onsets with a median residual of 3–4 ms.

**Viewpoint.** The show is built for the press box: south stand, looking north. The south-roof
strobes hang directly above the press box, so they stay dark. All strobe work runs on
group 717 "STROBES VISIBLE FROM PRESS BOX" (north roof, scoreboard, east stand). Beams lean north
so they cross the frame.

**Design rules:**
- **No wavy motion.** Positions snap (focus 0–0.1 s) or hold.
- **One layer leads at a time.** Beams, strobes or ring takes the lead, with call-and-response north/south.
- **Random strobes.** Seeded random-group step effects: 887 JDC, 888 beams, 889 ring.

**Machine-only programming:**
- **Transient pops:** every detected hi-hat or clap in the grooves gets its own cue, which flashes one random visible strobe.
- **Beam stacking:** the risers add one new beam per 8th note, each aimed at its own random point in the sky. All 40 then snap to the crown and stutter in 16ths into a suck-out.
- **Teleports:** on drop downbeats all 40 beams snap to one computed convergence point in 3D (see `TELEPORT`).
- **13 stars:** the Doop melody. Each of the 13 sung notes, detected from the audio, pops one gold pillar.

| Time | Scene | What happens |
|---|---|---|
| 0:00.6 | Intro | One gold pillar per chord stab, stacking centre-out across the north roof |
| 0:06.3 | Tone | 40 beams snap to the crown + random strobe glitter |
| 0:08.2 | Groove A / A2 | North ↔ south beams answer on every beat (fan / flattened / X); hi-hat pops on the strobes |
| 0:21.3 | Break A | One solo beam snapping between four points |
| 0:23.2 | Riser | Ring tent + strobe bed, then a beam stacked per 8th, then a 16th stutter, suck-out at 0:37.0 |
| 0:38.2 | Drop 1 | White blinder + teleport; phrase A teleports / B strobes lead with ring hits / C call & response |
| 0:45.7 | Decay → Silence | Crown fades, half the beams, black at 0:51.3 |
| 0:53.2 | Doop | One gold beam in the silence, then 13 stars on the 13 sung notes |
| 1:02.0 | Claps | Strobe on every clap (north / ends), ring pick-offs |
| 1:05–1:15 | Bass in / out / back | Call & response with the ring, solo beam in the gap |
| 1:15.4 | Chorus | Drop phrases A/B/C |
| 1:27.1 | Break B | North beams alone; pops on the end strobes |
| 1:33.8 | Build 2 | Beam stacking again, suck-out at 1:39.55 |
| 1:39.75 | Final drop | Phrases A/B/C/D; D = everything: a teleport every beat, random strobes on strobes and ring |
| 2:06.6 | Outro | Gold pillars with pops, to navy, blackout at 2:11.6 |

## For refining by hand

- **Groups:** 701–740 are labelled and used in the cue commands. Beams: 701 all / 702 north / 703 south / 706 odd / 707 even. Strobes: 711–717. Ring: 721–727. 731/732 north/south side; 740 everything.
- **Cues:** every cue is labelled, and each section starts with a cue **Scene**.
- **Palettes:** CP 71–76, FP 71–78 / 81–84.
- **Effects:** 880–895, all labelled.
## Rebuild

```powershell
python examples\union\rig_union.py          # place fixtures (types must already be patched)
python examples\union\build_fx.py           # palettes + effects
python examples\union\show.py               # cue list 7 + event list 7
python reaper_load.py split-timecode --seconds 280   # MTC past 3:00 (see below)
```

**MTC past 3:00:** the Reaper SMPTE generator item stops generating after its original source
length (~3:00), even when the item is lengthened. `reaper/split_timecode.lua` adds a second
generator item from 2:50 whose timecode starts at 2:50. Eos chases straight across the join.


## Model credits

The stadium model (`subaru-park.glb`, "Landmark - Subaru Park") was made with
[Mini Skyline](https://miniskyline.com). **The model file itself is not included in this repo**;
only the show, the scripts and the full attribution it came with. Generate your own from Mini Skyline to rebuild the example.

- Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the
  [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/).
- Building, transportation and base-map data from [Overture Maps](https://docs.overturemaps.org/attribution/)
  (release 2026-09-23.1), © OpenStreetMap contributors, Overture Maps Foundation and theme source contributors.
- Elevation: Mapterhorn terrain tiles ([sources](https://mapterhorn.com/attribution/)), including Copernicus
  WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, and USGS.
- Ground colours: modified Copernicus Sentinel data / ESA WorldCover (CC BY 4.0).

The complete required credit text is in [`miniskylines_attribution.txt`](miniskylines_attribution.txt), and the
per-source licences are in [`miniskylines_sources.json`](miniskylines_sources.json).

Subaru Park's name and design may be protected by trademark or copyright. Mini Skyline and this project are not
affiliated with or endorsed by the stadium's owners or any team. The Philadelphia Union name and the songs
are used only to describe the example; no audio is included.
