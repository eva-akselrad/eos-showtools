# Examples

Four complete shows, in the order they were built. Each one taught something, and the docs
record what.

| Folder | Song | Cue / event list | Cues | Technique |
|---|---|---|---|---|
| [volatile_reaction](volatile_reaction) | *Volatile Reaction*, Kevin MacLeod | 5 / 5 | 164 | Beat-tracked cue stack, XYZ aiming, hand-picked hits |
| [bangarang](bangarang) | *Bangarang*, Skrillex ft. Sirah | 5 / 5 | 635 | Exact grid, continuous beat-locked motion, pixel patterns, laser-style beams |
| [arena](arena) | *This Is Your Arena* | 6 / 6 | 102 + effect library | Event-driven; real Eos step, absolute and relative effects, palettes, overrides, fanned delays |
| [latency_test](latency_test) | none | 5 / 5 | 31 | Measures your Reaper → Eos latency |
| [union](union) | Union mashup (Party Till We Die x Doop) | 7 / 7 | 314 | Stadium show at Subaru Park: venue model scaled from its mesh, fixtures chosen + patched, positions computed from geometry |
| [stage](stage) | none | none | none | Builds the Augment3d stage itself: deck, truss grid, towers, fixture positions |

**Audio is not included.** Each README says where the track comes from. Convert it to WAV, and
the analysis files, cue sheets and markers in the folder still line up with it. You only need
to re-run the analysis if you change the scripts.

## Running an example

```powershell
python examples\<name>\show.py --dry            # cue sheet, no console needed
python examples\<name>\show.py                  # WIPES that cue list + event list, then records
python reaper_load.py load --wav <song.wav> --markers examples\<name>\markers.txt --expect "<your project>"
python runtest.py examples\<name> --list <N> --dur <seconds> [screenshot times...]
```

> ⚠️ Recording wipes the example's cue list and event list in the **currently open show
> file**. Use a scratch show, or **Save As** first.

## The rig these were written for

| Channels | Fixture | Placement |
|---|---|---|
| 101–130 | 30 × High End SolaFrame 3000 (Standard, Pan 630) | 3 overhead truss rows |
| 131–150 | 20 × SolaFrame 3000 | floor chevron |
| 201–220 | 20 × High End SolaPix 19 (Base + Pixel) | 2 overhead rows |
| 221–230 | 10 × SolaPix 19 | floor line |
| 231–248 | 18 × SolaPix 19 | two 3×3 side towers |

To use a different rig, change the group definitions in `rig.py` and regenerate `patch.txt`.
Patterns written as functions of position (wipes, rings, fans) adapt by themselves.
