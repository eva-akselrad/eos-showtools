# Building Eos effects and palettes from code (`fxlib.py`)

The Eos effect editor looks like a softkey-and-grid UI, but **every field can be typed on the
command line**. To learn the syntax, I clicked each column once with `deskctl.py` and read the
echo with `eosui.py`. `fxlib.py` wraps it, so an effect is one Python call:

```python
from rig import *
from fxlib import FX, columns, rings, levels_z
S = Show(list_no=6)
F = FX(S)
F.open_list()                       # presses [Effect][Effect]: Blind effect list
F.step(830, "WIPE L-R", columns(ALL), step_time=0.07, dwell=0.04, decay=0.22)
F.absolute(845, "SNAP FAN-X", ["Focus_Palette 61", "Focus_Palette 62"], time_s=0.06, dwell=0.24)
S.run("Live")
```

## Command-line syntax (verified on Eos 3.3)

Run these from the **Blind effect list**: press `[Effect]` twice. In Live, `Effect 830 …` on
an effect that doesn't exist yet returns *Effect Does Not Exist*.

| Goal | Command line |
|---|---|
| create | `Effect 830 Create Type StepBased` / `… Type Absolute` |
| add steps / actions | `Effect 830 Step 1 Thru 10` → *Please Confirm* → Enter. Same for `Action 1 Thru 4` |
| channels in a step | `Effect 830 Step 3 Chan 101 + 105 Thru 107` |
| step timing | `Effect 830 Step 1 Thru 10 StepTime 0.07` · `InTime 0` · `Dwell 0.04` · `DecayTime 0.22` |
| step levels | `… OnState 100` · `… OffState 0` |
| absolute action level | `Effect 845 Action 1 Color_Palette 61` · `… Action 2 Focus_Palette 62` · `… Action 3 @ 50` |
| absolute timing | `Effect 845 Action 1 Thru 2 Time 0.06` · `… Dwell 0.24` |
| attributes (toggles) | `Effect 833 Attributes Random_Groups` · `Effect 831 Bounce` |
| distribution | `Effect 841 Grouping 2` · `Effect 841 Trail 50` · `Effect 841 Entry Cascade` |
| tempo | `Effect 830 BPM 135` (rescales the effect's own times) |
| label | `Effect 830 Label WIPE L-R` |
| copy a stock effect | `Effect 901 Copy_To Effect 850` + Enter |
| delete | `Delete Effect 801 Thru 899` → *Please Confirm* → send `#` with `/eos/cmd` (append), **not** `/eos/newcmd` |

### Gotchas (each one cost a rebuild)

1. **Times take at most 2 decimals.** `StepTime 0.074` is rejected silently: the field keeps its
   default. Use `0.07`, and set exact rates with BPM or Rate overrides in the cue.
2. **Select the effect before editing it.** Blind keeps the last edited effect and step as
   command-line context. `Effect 845 Action 1 Thru 2 Time 0.06` failed right after editing 830.
   It works after a bare `Effect 845`. `fxlib` does this automatically.
3. **Attributes toggle.** Running a build twice turns `Bounce` and `Random_Groups` back *off*.
   Delete the effects and rebuild instead (`F.delete(801, 899)`).
4. **Confirm with `/eos/cmd "#"`.** A new `/eos/newcmd` replaces the pending command and
   cancels the confirmation.
5. **One palette or reference per command line.** `Chan 201 Thru 248 Color_Palette 61 Zoom 5`
   didn't apply the palette. Split it into two command lines.

## Using effects in cues (Live)

| Goal | Command line |
|---|---|
| run a step effect on its embedded channels | `Recall_From Effect 830` |
| run it on a subset | `Chan 201 Thru 248 Effect 830` (channels must be in the effect) |
| apply absolute/relative to a selection | `Chan 131 Thru 140 + 150 Thru 141 Effect 842`: **selection order = distribution order** |
| cue-level tempo | `Effect 830 BPM 405` |
| cue-level speed | `Effect 832 Rate 160` (%) |
| cue-level size | `Effect 833 Size 60` (%) |
| stop effects | `Chan 101 Thru 248 Effect` (no number) |

Live changes to Rate, Size and BPM are **cue-level overrides**. They are recorded into the cue,
and the effect itself is not modified, as described in the Eos manual under *Editing Effects
Live*. An effect starts when the cue that applies it fires, so its phase is locked to that
timecode moment.

## Palettes from code

```python
S.run(f"{spec(ALL)} Hue 0 Saturation 100")
S.run(f"{spec(ALL)} Record Color_Palette 61"); F.confirm()
S.run("Color_Palette 61 Label Red")

S.aim(V, fanV(1.0)); S.aim(OH, fanOH(1.0)); S.flush()
S.run(f"{spec(SP)} Record Focus_Palette 61"); F.confirm()
S.run("Focus_Palette 61 Label Sky Fan")
```

Selecting channels before `Record …Palette` limits the palette to those channels. Cues can then
reference the palettes: `Chan 101 Thru 150 Focus_Palette 61`. Re-recording the palette later
re-aims every cue that uses it.

## Geometry helpers

| Helper | Returns |
|---|---|
| `columns(chs, width=3.0)` | fixtures split into front-view vertical columns, left → right (10 for this rig) |
| `rings(chs, width=3.0)` | centre-out rings by \|x\| |
| `levels_z(chs)` | height tiers, bottom → top (floor, tower 6 m, tower 8 m, trusses) |

Each one returns a list of channel lists, which is exactly what a step effect's `steps` wants.

## The Arena effect library (`examples/arena/build_fx.py`)

The pulse clock of the track is 0.1481 s, so `q` = 0.07 s (half a pulse).

| # | Name | Type | Built from | Timing |
|---|---|---|---|---|
| 830 | WIPE L-R | step | `columns(ALL)`: 10 steps | step q, dwell 0.04, decay 0.22 (comet tail) |
| 831 | WIPE BOUNCE | step | same + `Bounce` | |
| 832 | CENTRE OUT | step | `rings(ALL)` | step q, decay 0.2 |
| 833 | SPARKLE | step | 16 steps × 6 random fixtures, `Random_Groups` | step 0.045, dwell 0.03 |
| 834 | STROBE ALL | step | [ALL], [virtual ch 1] | step 0.035, dwell 0.025 |
| 835 | STROBE ODD-EVEN | step | odd columns / even columns | step q |
| 836 | TIERS UP | step | `levels_z(ALL)` | step q, decay 0.18 |
| 837 | L-R SLAM | step | LEFT / RIGHT | step 1 pulse |
| 838 | CHEVRON RUN | step | floor chevron one by one, `Bounce` | step 0.035 |
| 839 | TRUSS RUN | step | `columns(OH + WOH)` | step q |
| 840 | TOWER STACK | step | `levels_z(TW)`, `Bounce` | step 1 pulse |
| 841 | RED-WHITE | absolute | CP 61 ↔ CP 62 | time 0, dwell 1 pulse |
| 842 | COLOUR RUN | absolute | CP 61, 63, 65, 62, 64, 66 | time 0, dwell 1 pulse |
| 845 | SNAP FAN-X | absolute | FP 61 ↔ FP 62 | time 0.06, dwell 0.24 |
| 846 | SEARCH L-R | absolute | FP 63 ↔ FP 64 | time 6 pulses |
| 847 | SNAP 4 WAY | absolute | FP 61, 65, 62, 68 | time 0.05, dwell 0.1 |
| 850 | BEAM CIRCLE | focus (relative) | copy of 901 | BPM override per cue |
| 851 | BEAM FIG8 | focus (relative) | copy of 903 | BPM override per cue |

Palettes: **CP 61–68** Red, White, Cyan, Amber, Magenta, Blue, Purple, Green.
**FP 61–68** Sky Fan, X Cross, Sweep L, Sweep R, Tunnel, Straight, Audience, Floor Fan.
**BP 61** Laser (Zoom 15, Iris 100), **BP 62** Prism.

## What doesn't work (yet)

- **Event list Type** (SMPTE → MIDI Timecode) has no typed syntax. Use the Show Control
  display (see [setup.md](setup.md)).
- **SolaPix pixel masks / cell control.** The SolaPix 19 "Base + Pixel" mode exposes a
  *Pixel Mask* parameter, but Augment3d does not render it, and `Chan 201 Cell 3` reported an
  empty channel list. Pixel looks are therefore built from the 98 fixtures as a grid.
