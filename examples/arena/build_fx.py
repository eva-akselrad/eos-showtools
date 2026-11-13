"""Build the ARENA effect + palette library in Eos (run once before show.py).

Colour palettes 61-68, focus palettes 61-68 (spots), beam palettes 61-62,
step effects 830-840 (geometry-mapped chases), absolute effects 841-847 (palette chases),
relative focus effects 850-851 (copies of stock circle / figure 8).
Pulse clock of the track: 0.1481 s (triplet of 135 BPM).
"""
import os, sys, random, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from rig import *
from fxlib import FX, columns, rings, levels_z
sys.path.insert(0, os.path.join(HERE, "..", "bangarang"))

PULSE = 0.1481
DRY = "--dry" in sys.argv
S = Show(list_no=6, dry=DRY)
F = FX(S)

# ------------------------------------------------------------------ aim shapes for focus palettes
import math
fanV = lambda w: (lambda c, x, y, z: (x * (1 + 2.4 * w), y + 1.5, 22))
fanOH = lambda w: (lambda c, x, y, z: (x * (1 + 1.1 * w), y - 9 * w, 0))
scanV = lambda a: (lambda c, x, y, z: (x + 20 * math.sin(math.radians(a)), y + 1.5, 20))
scanOH = lambda a: (lambda c, x, y, z: (x + 13 * math.sin(math.radians(a)), y - 2, 0))
FPS = {
    61: ("Sky Fan", fanV(1.0), fanOH(1.0)),
    62: ("X Cross", lambda c, x, y, z: (-x * 2.4, y - 1, 14), lambda c, x, y, z: (-x * 1.3, y - 4, 0)),
    63: ("Sweep L", scanV(-45), scanOH(-40)),
    64: ("Sweep R", scanV(45), scanOH(40)),
    65: ("Tunnel", lambda c, x, y, z: (0, 5, 15), lambda c, x, y, z: (0, 3, 0)),
    66: ("Straight", lambda c, x, y, z: (x, y, 30), lambda c, x, y, z: (x, y, 0)),
    67: ("Audience", lambda c, x, y, z: (x * 1.5, -14, 7), lambda c, x, y, z: (x * 1.5, -12, 0)),
    68: ("Floor Fan", lambda c, x, y, z: (x * 1.4, y - 9, 3), lambda c, x, y, z: (x * 0.6, y + 2, 0)),
}
CPS = {61: ("Red", 0, 100), 62: ("White", 0, 0), 63: ("Cyan", 185, 100), 64: ("Amber", 28, 100),
       65: ("Magenta", 305, 100), 66: ("Blue", 235, 100), 67: ("Purple", 270, 100), 68: ("Green", 120, 100)}


def palettes():
    S.run("Live", 0.4)
    for n, (lab, h, s) in CPS.items():
        S.run(f"{spec(ALL)} Hue {h} Saturation {s}")
        S.run(f"{spec(ALL)} Record Color_Palette {n}", 0.3); F.confirm()
        S.run(f"Color_Palette {n} Label {lab}")
    for n, (lab, fv, fo) in FPS.items():
        S.aim(V, fv); S.aim(OH, fo); S.flush(); time.sleep(0.2)
        S.run(f"{spec(SP)} Record Focus_Palette {n}", 0.3); F.confirm()
        S.run(f"Focus_Palette {n} Label {lab}")
    # beam palettes
    S.run(f"{spec(SP)} Zoom 15 Iris 100 Edge 0 Gobo_Select 1 Beam_Fx_Select 1")
    S.run(f"{spec(SP)} Record Beam_Palette 61", 0.3); F.confirm(); S.run("Beam_Palette 61 Label Laser")
    S.run(f"{spec(SP)} Zoom 28 Beam_Fx_Select 3")
    S.run(f"{spec(SP)} Record Beam_Palette 62", 0.3); F.confirm(); S.run("Beam_Palette 62 Label Prism")
    S.run(f"{spec(SP)} Zoom 15 Beam_Fx_Select 1")


def effects():
    F.open_list()
    F.delete(801, 899)
    q = PULSE / 2
    allc = by_x(ALL)
    F.step(830, "WIPE L-R", columns(ALL), q, dwell=0.04, decay=0.22)
    F.step(831, "WIPE BOUNCE", columns(ALL), q, dwell=0.04, decay=0.22, attrs=["Bounce"])
    F.step(832, "CENTRE OUT", rings(ALL), q, dwell=0.04, decay=0.2)
    rnd = random.Random(7)
    F.step(833, "SPARKLE", [rnd.sample(ALL, 6) for _ in range(16)], 0.045, dwell=0.03, decay=0.05,
           attrs=["Random_Groups"])
    F.step(834, "STROBE ALL", [ALL, [1]], q / 2, dwell=0.025, decay=0.0)
    cols = columns(ALL)
    F.step(835, "STROBE ODD-EVEN", [sum(cols[0::2], []), sum(cols[1::2], [])], q, dwell=0.03, decay=0.02)
    F.step(836, "TIERS UP", levels_z(ALL), q, dwell=0.04, decay=0.18)
    F.step(837, "L-R SLAM", [LEFT, RIGHT], PULSE, dwell=0.08, decay=0.05)
    F.step(838, "CHEVRON RUN", [[c] for c in VL + VR], 0.035, dwell=0.03, decay=0.18, attrs=["Bounce"])
    F.step(839, "TRUSS RUN", columns(OH + WOH), q, dwell=0.04, decay=0.16)
    F.step(840, "TOWER STACK", levels_z(TW), PULSE, dwell=0.06, decay=0.12, attrs=["Bounce"])
    F.absolute(841, "RED-WHITE", ["Color_Palette 61", "Color_Palette 62"], 0.0, PULSE)
    F.absolute(842, "COLOUR RUN", ["Color_Palette 61", "Color_Palette 63", "Color_Palette 65",
                                   "Color_Palette 62", "Color_Palette 64", "Color_Palette 66"], 0.0, PULSE)
    F.absolute(845, "SNAP FAN-X", ["Focus_Palette 61", "Focus_Palette 62"], 0.06, PULSE * 2 - 0.06)
    F.absolute(846, "SEARCH L-R", ["Focus_Palette 63", "Focus_Palette 64"], PULSE * 6, 0.0)
    F.absolute(847, "SNAP 4 WAY", ["Focus_Palette 61", "Focus_Palette 65", "Focus_Palette 62",
                                   "Focus_Palette 68"], 0.05, PULSE - 0.05)
    S.run("Effect 901 Copy_To Effect 850", 0.4); F.confirm(); S.run("Effect 850 Label BEAM CIRCLE")
    S.run("Effect 903 Copy_To Effect 851", 0.4); F.confirm(); S.run("Effect 851 Label BEAM FIG8")
    S.run("Live", 0.5)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "all"
    if what in ("all", "pal"):
        palettes()
    if what in ("all", "fx"):
        effects()
    print("commands:", S.ncmd)
