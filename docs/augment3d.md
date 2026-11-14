# Augment3d notes

Augment3d is the only "stage" these shows have been seen on, and it renders some things very
differently from real fixtures. Everything below was found with `dev/lookdev.py` and
`dev/fxshot.py` contact sheets.

## Beams

| Setting | Result |
|---|---|
| SolaFrame **Zoom 15** | Crisp, thin, laser-like beams. **Use this for "laser" looks** |
| SolaFrame Zoom 7 (the minimum) | Renders as a soft, wide glow. It looks *wider* than 15 |
| SolaFrame Zoom 30 | Chunkier beams; still defined |
| Zoom 45–55 | Washy cones |
| **Iris 100** = open, Iris 0 = closed (dark) | Iris 30–40 is visibly dim |
| Edge 0 vs 100 | Little visible difference |
| SolaPix Zoom 5 | Narrow wash columns. Overhead washes pointed straight down make a "pixel curtain" |
| SolaFrame shutter strobe 1–13 | Renders as strobe. **SolaPix strobe values show no visible strobe**: build strobes from fast intensity cues or step effects instead |
| SolaPix *Pixel Mask* | Not rendered |

## Aiming

- XYZ focus (`/eos/chan/N/param/x_focus/y_focus/z_focus`) puts beams exactly where you mean them.
  Coordinates: x right, y upstage, z up. The camera and audience are at y < 0.
- **Don't aim washes or towers at the camera.** The whole frame washes out to one colour. Aim
  them across the stage, down, or up.
- Overhead spots fanned *toward* the audience floor (`(x·2.1, y − 9, 0)`) read well from the
  front camera and look like beams coming at you. Keep them for hits.
- Moves complete within ~1.5 s, so Augment3d doesn't seem to simulate slow motors. Sub-second
  sweeps still look like sweeps.

## Display gotchas

- **Blind mode shows Blind data.** If the console is in Blind (for example after the effect
  list or Show Control), Augment3d shows the blind cue, which is usually black. Go back to
  Live before watching.
- **Occlusion pauses rendering.** When another window (Reaper) covers Eos, Augment3d stops
  rendering, and it needs several seconds to resume after Eos is back in front. The harness
  waits 7 s before starting playback for this reason.
- **Selected channels are outlined** in orange. Select a non-visual channel (`Chan 1`) before
  capturing. On this rig that is the Augment3d virtual server, which may also move the camera
  toward it.
- **Camera:** the wheel zooms (`deskctl.py scroll x y n`). Taps of Alt with the cursor over the
  viewport can move the camera, so `deskctl.focus()` parks the cursor first. The default
  capture box assumes the full-width *38 Augment3d* tab.
- **The Live key switches workspace page.** Afterwards, click back to the page and tab that hold
  Augment3d.

## Building a stage

Fixtures can be placed from the command line in Patch, using `a3d_place.py`:
`Chan N Position x / y / z` and `Orientation rx / ry / rz`, with spaces around `/` and `- 9`
for negative values. Objects (decks, truss, scenery) can only be placed through Edit Mode.
`a3d_inspector.py` types into the Inspector, and `examples/stage/build_stage.py` builds a
complete deck + truss grid + towers that way. See [examples/stage](../examples/stage).
