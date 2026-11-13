# Eos OSC / command-line cookbook

Every line here was sent to Eos 3.3 (offline, with Augment3d) and the echo was checked with
`eostry.py` or `eosui.py`. The ✗ lines are syntax that **looked** right but failed.

## Command-line basics over OSC

- `/eos/newcmd "<text>#"` replaces the command line. `#` means Enter.
- `/eos/cmd "<text>"` appends to it. Use this to answer *Please Confirm* with `"#"`.
- Underscored names stand for softkeys and multi-word keys: `Copy_To`, `Go_To_Cue`,
  `Recall_From`, `Color_Palette`, `Focus_Palette`, `Beam_Palette`, `Gobo_Select`,
  `Beam_Fx_Select`, `Random_Groups`.

## Cues and lists

| ✓ Works | ✗ Fails |
|---|---|
| `Record Cue 5 / 1 Time 0` | `Record Cue 5/1` (no spaces around `/` → syntax error) |
| `Cue 5 / 1 Label Drop` | |
| `Cue 5 / 1 Focus Time 0.5` · `Color Time 0.2` · `Intensity Time 0` · `Beam Time 1` (category times) | |
| `Delete Cue 5 / 1 Thru 999 Enter` | |
| `Go_To_Cue 5 / 1` · `Go_To_Cue 5 / 1 Time 0` · `Go_To_Cue Out` | |
| OSC `/eos/cue/6/3/fire` (fires with the cue's own timing, like an event does) | |

Plain `Go_To_Cue` uses the console's *Go To Cue* default time. Add `Time 0` for an instant jump.

## Channels and parameters

| ✓ Works | Notes |
|---|---|
| `Chan 101 Thru 110 + 131 At 50` · `… Full` · `… Out` | |
| `Chan 101 Thru 110 Hue 200 Saturation 100` | Converts to CMY or RGB per fixture |
| `Chan 101 Thru 150 Zoom 15 Iris 100 Edge 0` | Several parameters in one line are fine. Palettes are not (see effects.md) |
| `Chan … Gobo_Select 4` · `Beam_Fx_Select 3` | |
| `Chan 101 Thru 110 At 10 Thru 100` | Fans a level across the selection |
| `Chan 111 Thru 120 Full Delay 0 Thru 1` | **Fanned discrete delays** (echo: `Delay 0:00 Thru 0:01`) |
| `Chan 121 Thru 130 Full Time 0 Delay 0 Thru 1` | Discrete time + fanned delay |
| OSC `/eos/param/shutter_strobe -2` | Applies to the *selected* channels. **Negative numbers misparse on the command line** (`Shutter_Strobe -2` became `- 20`), so send them over OSC |
| OSC `/eos/param/pixel_mask 30` | Accepted, but not rendered by Augment3d |
| OSC `/eos/chan/101/param/x_focus/y_focus/z_focus 1.0 4.0 0.0` | Aim one fixture at a point in metres |

| ✗ Fails | |
|---|---|
| `Chan 201 Cell 3` / `Chan 201.5` | "Channel List is Empty" for SolaPix Base+Pixel, even though the *Cell* softkey exists |
| `Chan 201 Part 2` | Syntax error |

## Palettes

`Chan <list> Record Color_Palette 61` then confirm, then `Color_Palette 61 Label Red`.
Focus and beam palettes work the same way. Apply one with `Chan … Focus_Palette 61`.

## Effects

See [effects.md](effects.md) for the full table. In brief:
- **Build:** `Effect 830 Create Type StepBased`, then `Step 1 Thru 10` + confirm, then
  `Step 3 Chan …`, then `StepTime` / `InTime` / `Dwell` / `DecayTime` / `OnState` / `OffState`
  (2 decimals max).
- **Run:** `Recall_From Effect 830`, or `Chan … Effect 842`.
- **Override in the cue:** `Effect 830 BPM 405` / `Rate 200` / `Size 60`.
- **Stop:** `Chan … Effect`.

## Event lists (timecode)

| ✓ Works | ✗ Fails |
|---|---|
| `Event 5 / 1 Time 00:00:26:18 Cue 5 / 49` | `Event 5 / Type MIDI` |
| `Event 5 / 1 Thru 999 Delete Enter` | `Event 5 / FrameRate 30` |
| `Event 5 / Source 1` | |
| `Event 5 / External` (toggles; echo says Enable or Disable) · `Event 5 / Internal` | |
| `Event 5 / Label Bangarang` | |
| `Cue 5 / Execute Timecode 5` | |

The **Type** must be set in Show Control: click the Type cell, press the *MIDI Timecode*
softkey, then Enter. New lists default to SMPTE, 30 fps.

## Querying

| Address | Reply |
|---|---|
| `/eos/get/patch/count` then `/eos/get/patch/index/N` | Fixture list, notes, Augment3d position/beam (what `eosctl.py patch` dumps) |
| `/eos/get/cue/6/count`, `/eos/get/cue/6/3` | Cue fields: label, up/down/focus/colour/beam times in ms … |
| `/eos/get/cuelist/count` | Cue lists (label, mode …) |
| `/eos/get/fx/count`, `/eos/get/fx/index/N` | Effects: number in the address `/eos/out/get/fx/<num>/list/…`, then label, type, entry, exit … |
| `/eos/get/cp|fp|bp|ip|preset|group|macro|sub/...` | Palettes and other targets |
| subscribe, then select a channel | `/eos/out/active/wheel/<n>`: every parameter of the selection with its current value. The quickest way to learn a fixture's parameter names |

## Keys and modes

- `/eos/key/live` returns to Live, but **also switches the workspace page**, so the Augment3d
  tab disappears.
  - **Same thing from the command line:** typing `Live` does the same, so plan to reselect the
    page and tab afterwards (`deskctl.py click`).
- `/eos/key/effect` pressed twice opens the effect list in **Blind**.
- **Blind changes what Augment3d shows.** While the console is in Blind, Augment3d shows Blind
  data, not output. **Always return to Live before watching or measuring.**
- **Event context swallows channel numbers.** In Blind with the event list focused, a typed
  `Chan 101` becomes `Event 6 / 101`. That's another reason to get back to Live.
