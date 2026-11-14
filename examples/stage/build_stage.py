"""build_stage.py - build the simple stage in Augment3d (deck + truss grid + side towers).

Fixtures are placed separately from the saved patch with:
    python a3d_place.py patch.txt --only 101-150,201-248

Objects (deck, truss) have no command-line syntax, so this drives Augment3d Edit Mode:
drag "Truss Square" from the Library into the viewport (the new object becomes the selection),
then type Name / Size / Rotation / Position into the Inspector (a3d_inspector.py).

Preconditions (see docs/augment3d.md#building-a-stage):
  - Augment3d tab full width, Edit Mode ON, Library: Stock > Truss expanded so "Truss Square"
    sits at LIB_TRUSS, Inspector panel dragged up (top at y~185).
  - The deck ("Staging2x1m" -> 20 x 10 x 1 m at -10,-1,0) was added the same way.

Truss Square pivot = its start (min x, local axes); length runs along local +X.
Rotation Z 90 turns it upstage (+Y); rotation Y -90 stands it up (+Z).

    python build_stage.py [--dry] [--only NAME_PREFIX]
"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import deskctl, config
import a3d_inspector as I

LIB_TRUSS = (120, 822)      # "Truss Square" in the Library list
DROP = (870, 600)           # where to drop it in the viewport
T = 0.3                     # truss section (m)
TRIM = 9.95                 # underside height of the overhead grid

# name, length, rotation (x, y, z), position (x, y, z) of the pivot
TRUSS = []
for y in (0, 2, 4, 6, 8):                                    # overhead runs, stage-wide
    TRUSS.append((f"Grid Y{y}", 21.0, (0, 0, 0), (-10.5, y - T / 2, TRIM)))
for x in (-10.5, 10.5 - T):                                  # side rails tying the grid together
    TRUSS.append((f"Grid Rail X{x:+.1f}", 8.6, (0, 0, 90), (x + T, -T / 2 - 0.15, TRIM)))
for x in (-10.8, 10.5):                                      # grid legs (4)
    for y in (-0.45, 8.15):
        TRUSS.append((f"Leg X{x:+.1f} Y{y:+.1f}", TRIM + T, (0, -90, 0), (x, y, 0)))
for side, x0 in (("L", -15.0), ("R", 10.8)):                  # 3x3 side towers
    TRUSS.append((f"Tower {side} Leg", 10.55, (0, -90, 0), (x0 if side == "L" else x0 + 4.2 - T, -0.45, 0)))
    for z in (6, 8, 10):
        TRUSS.append((f"Tower {side} Bar {z}", 4.2, (0, 0, 0), (x0, -T / 2, z + 0.12)))


def add(name, length, rot, pos, dry=False):
    print(f"{name:22s} len {length:5.2f} rot {rot} pos {tuple(round(p, 2) for p in pos)}")
    if dry:
        return
    deskctl.drag(*LIB_TRUSS, *DROP)
    time.sleep(1.2)
    I.FIELD_Y = I.LAYOUTS["truss"]
    I.set_field(*I.NAME_XY, name)
    I.set_vec("size", (length, T, T))
    I.set_vec("rotation", rot)
    I.set_vec("position", pos)


def main():
    dry = "--dry" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else ""
    if not dry:
        deskctl.focus(config.EOS_WINDOW)
    for spec in TRUSS:
        if spec[0].startswith(only):
            add(*spec, dry=dry)
    deskctl.move(1915, 1075)


if __name__ == "__main__":
    main()
