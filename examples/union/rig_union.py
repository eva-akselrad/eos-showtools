"""rig_union.py - the Subaru Park rig: fixture positions computed from the stadium mesh.

World frame (after aligning the model, see README): pitch centre = (0, 0, 0) on the grass,
long axis = X (west end at -X has the scoreboard tower), +Y = the north long side.

    python rig_union.py --dry      print positions
    python rig_union.py            place fixtures in Patch (Position + Orientation) and write rig.json

Channels
  301-340  Elation Proteus Excalibur   20 per long side, upright on top of the roof leading edge
  401-424  GLP JDC2 IP (M1)            12 per long side, between the Excaliburs on the same edge
  425-428  GLP JDC2 IP                 west scoreboard tower face, facing the pitch
  429-432  GLP JDC2 IP                 east stand top, facing the pitch
  501-520  Elation Proteus Rayzor 760  10 per long side, pitch perimeter at ground, pointing up
  521-532  Elation Proteus Rayzor 760  6 per end, pitch perimeter at ground, pointing up
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))

# roof leading edge, measured from the mesh: x -> (|y| north, |y| south, underside z)
ROOF = {-55: (36.7, 37.4, 19.0), -50: (36.7, 37.4, 19.0), -45: (36.7, 37.4, 20.3), -40: (34.8, 35.5, 24.2),
        -35: (34.7, 35.4, 24.8), -30: (34.5, 35.2, 25.3), -25: (34.4, 35.1, 25.7), -20: (34.3, 35.0, 26.2),
        -15: (34.2, 34.9, 26.5), -10: (34.1, 34.7, 26.8), -5: (34.1, 34.7, 27.1), 0: (34.1, 34.7, 27.2)}
for k in list(ROOF):
    ROOF[-k] = ROOF[k]
RX = sorted(ROOF)


def roof(x, side):
    """(y, z) of the hanging point under the roof leading edge at x; side +1 north / -1 south"""
    yN = np.interp(x, RX, [ROOF[k][0] for k in RX])
    yS = np.interp(x, RX, [ROOF[k][1] for k in RX])
    z = np.interp(x, RX, [ROOF[k][2] for k in RX])
    return (side * ((yN if side > 0 else yS) + 0.3), z - 0.7)


def build():
    pos, ori, kind = {}, {}, {}
    xs = np.linspace(-52, 52, 20)
    for i, side in enumerate((1, -1)):                    # Excaliburs
        for j, x in enumerate(xs):
            c = 301 + i * 20 + j
            y, z = roof(x, side)        # upright on top of the roof edge (searchlight position)
            pos[c] = (round(float(x), 2), round(float(y), 2), round(float(z) + 2.2, 2)); ori[c] = (180, 0, 0); kind[c] = "EXC"
    xj = (xs[:-1] + xs[1:]) / 2                            # 19 gaps -> use 12 evenly
    xj = xj[np.round(np.linspace(0, len(xj) - 1, 12)).astype(int)]
    for i, side in enumerate((1, -1)):                    # JDC2 on the roof edges
        for j, x in enumerate(xj):
            c = 401 + i * 12 + j
            y, z = roof(x, side)
            pos[c] = (round(float(x), 2), round(float(y), 2), round(float(z) + 0.2, 2)); ori[c] = (0, 0, 0); kind[c] = "JDC"
    for j, y in enumerate((-6, -2, 2, 6)):                # scoreboard tower face (west), facing +X
        c = 425 + j; pos[c] = (-64.0, float(y), 22.0); ori[c] = (0, 90, 0); kind[c] = "JDC"
    for j, y in enumerate((-15, -5, 5, 15)):              # east stand top, facing -X
        c = 429 + j; pos[c] = (63.0, float(y), 9.2); ori[c] = (0, -90, 0); kind[c] = "JDC"
    for i, side in enumerate((1, -1)):                    # Rayzors, long sides
        for j, x in enumerate(np.linspace(-45, 45, 10)):
            c = 501 + i * 10 + j; pos[c] = (round(float(x), 2), side * 32.3, 0.3); ori[c] = (180, 0, 0); kind[c] = "RAY"
    for i, ex in enumerate((-52.6, 52.6)):                # Rayzors, ends
        for j, y in enumerate(np.linspace(-25, 25, 6)):
            c = 521 + i * 6 + j; pos[c] = (ex, round(float(y), 2), 0.3); ori[c] = (180, 0, 0); kind[c] = "RAY"
    return pos, ori, kind


def main():
    pos, ori, kind = build()
    json.dump({"pos": pos, "ori": ori, "kind": kind}, open(os.path.join(HERE, "rig.json"), "w"), indent=0)
    if "--dry" in sys.argv:
        for c in sorted(pos):
            print(c, kind[c], pos[c], ori[c])
        return
    from eosctl import Eos
    from a3d_place import triple
    e = Eos()
    e.run("Patch", pause=0.6)
    for c in sorted(pos):
        e.run(f"Chan {c} Position {triple(*pos[c])}", pause=0.04)
        e.run(f"Chan {c} Orientation {triple(*ori[c])}", pause=0.04)
    e.run("Live", pause=0.4)
    print("placed", len(pos))


if __name__ == "__main__":
    main()

