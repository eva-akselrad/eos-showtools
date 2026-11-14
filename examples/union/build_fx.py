"""Build the UNION palette + effect library (run once before show.py).

Colour palettes 71-76, focus palettes 71-78 (Excaliburs) and 81-84 (Rayzors), step effects 880-886,
absolute effects 890-892, relative focus 895. Everything is built from fixture positions in rig.json.
    python build_fx.py [pal|fx] [--dry]
"""
import json, math, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import rig
from rig import Show, spec
from fxlib import FX

RIG = json.load(open(os.path.join(HERE, "rig.json")))
rig.use_rig({int(c): p for c, p in RIG["pos"].items()})
POS = rig.POS
R = lambda a, b: list(range(a, b + 1))
EN, ES = R(301, 320), R(321, 340); E = EN + ES
JN, JS, JW, JE = R(401, 412), R(413, 424), R(425, 428), R(429, 432); J = JN + JS + JW + JE
RN, RS, RW, RE = R(501, 510), R(511, 520), R(521, 526), R(527, 532); RY = RN + RS + RW + RE
ALL = E + J + RY
BEAT = 60 / 128.0

# Union colours: navy, gold, light blue (+ white, deep blue, warm white)
CPS = {71: ("Union Navy", 222, 95), 72: ("Union Gold", 42, 72), 73: ("Union Light Blue", 200, 62),
       74: ("White", 0, 0), 75: ("Deep Blue", 232, 100), 76: ("Warm Gold", 35, 55)}

# Excalibur focus palettes (beams on the roof)
FPE = {
    71: ("Sky Fan", lambda c, x, y, z: (x * 1.8, y * 1.6, 80)),
    72: ("Sky Cross", lambda c, x, y, z: (-x * 0.3, -y * 1.5, 60)),
    73: ("Centre Spot", lambda c, x, y, z: (0, 0, 0)),
    74: ("Crown", lambda c, x, y, z: (0, 0, 55)),
    75: ("Sweep West", lambda c, x, y, z: (x - 60, y * 1.3, 55)),
    76: ("Sweep East", lambda c, x, y, z: (x + 60, y * 1.3, 55)),
    77: ("Pillars", lambda c, x, y, z: (x, y, 90)),
    78: ("Pitch Lines", lambda c, x, y, z: (x, -y * 0.25, 0)),
}
# Rayzor focus palettes (ground ring around the pitch)
FPR = {
    81: ("Ring Up", lambda c, x, y, z: (x * 1.05, y * 1.05, 40)),
    82: ("Tent", lambda c, x, y, z: (0, 0, 32)),
    83: ("Ring Out", lambda c, x, y, z: (x * 1.6, y * 1.6, 30)),
    84: ("Into Stands", lambda c, x, y, z: (x * 1.5, y * 1.5, 10)),
}


def ring_order(chs):
    return sorted(chs, key=lambda c: math.atan2(POS[c][1], POS[c][0]))


def columns(chs, n=10):
    xs = sorted(chs, key=lambda c: POS[c][0])
    return [xs[i * len(xs) // n:(i + 1) * len(xs) // n] for i in range(n)]


DRY = "--dry" in sys.argv
S = Show(list_no=7, dry=DRY)
F = FX(S)


def palettes():
    S.run("Live", 0.4)
    S.run(f"{spec(ALL)} Home", 0.3)
    for n, (lab, h, s) in CPS.items():
        S.run(f"{spec(ALL)} Hue {h} Saturation {s}")
        S.run(f"{spec(ALL)} Record Color_Palette {n}", 0.3); F.confirm()
        S.run(f"Color_Palette {n} Label {lab}")
    for n, (lab, fn) in FPE.items():
        S.aim(E, fn); S.flush(); time.sleep(0.2)
        S.run(f"{spec(E)} Record Focus_Palette {n}", 0.3); F.confirm()
        S.run(f"Focus_Palette {n} Label {lab}")
    for n, (lab, fn) in FPR.items():
        S.aim(RY, fn); S.flush(); time.sleep(0.2)
        S.run(f"{spec(RY)} Record Focus_Palette {n}", 0.3); F.confirm()
        S.run(f"Focus_Palette {n} Label {lab}")


def effects():
    F.open_list()
    F.delete(870, 899)
    rnd = random.Random(1850)   # Philadelphia Union founded 2008, Sons of Ben 2007 - but 1850 sounds nice
    F.step(880, "RATTLESNAKE", [[c] for c in ring_order(RY)], 0.06, dwell=0.04, decay=0.35)
    F.step(881, "SIDE SLAM N-S", [EN + JN + RN, ES + JS + RS], BEAT, dwell=0.18, decay=0.2)
    F.step(882, "ROOF WIPE W-E", columns(E + JN + JS), 0.06, dwell=0.04, decay=0.25)
    F.step(883, "JDC STROBE", [J, [1]], 0.06, dwell=0.03, decay=0.0)
    F.step(884, "SPARKLE", [rnd.sample(E + J, 8) for _ in range(16)], 0.05, dwell=0.03, decay=0.06,
           attrs=["Random_Groups"])
    F.step(885, "ENDS PING", [JW + RW, JE + RE], BEAT, dwell=0.15, decay=0.2)
    F.step(886, "13 STARS", [rnd.sample(E + J + RY, 13) for _ in range(13)], 0.09, dwell=0.05, decay=0.2,
           attrs=["Random_Groups"])
    F.absolute(890, "NAVY-GOLD", ["Color_Palette 71", "Color_Palette 72"], 0.0, BEAT)
    F.absolute(891, "SKY SNAP", ["Focus_Palette 71", "Focus_Palette 72"], 0.12, BEAT * 2 - 0.12)
    F.absolute(892, "SKY SWEEP", ["Focus_Palette 75", "Focus_Palette 76"], BEAT * 4, 0.0)
    S.run("Effect 901 Copy_To Effect 895", 0.4); F.confirm(); S.run("Effect 895 Label SKY CIRCLE")
    S.run("Live", 0.5)


if __name__ == "__main__":
    what = next((a for a in sys.argv[1:] if not a.startswith("--")), "all")
    if what in ("all", "pal"):
        palettes()
    if what in ("all", "fx"):
        effects()
    print("commands:", S.ncmd)
