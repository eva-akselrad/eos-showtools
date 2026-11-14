"""a3d_place.py - set Augment3d fixture positions/orientations from a saved patch dump.

    python a3d_place.py [patch.txt] [--only 101-150,201-248] [--dry]

Reads the `/eos/out/get/patch/<chan>/1/augment3d/position` lines of an `eosctl.py patch` dump
(x, y, z in metres, then rotation about X, Y, Z in degrees) and types, in Patch:

    Chan 101 Position - 9 / 0 / 9.85
    Chan 131 Orientation 0 / 180 / 0

Syntax notes (Eos 3.3): the values MUST be space-separated around "/" ("5/5/5" is silently
dropped) and a negative value is typed "- 9". Setting a position adds the fixture to the
Augment3d model. Orientation 0/0/0 = hanging, pointing down; 180 about X or Y = pointing up.
Channels whose saved position is exactly 0,0,0 (never placed) are skipped.
"""
import ast, re, sys, time
import config
from eosctl import Eos


def num(v):
    v = round(float(v), 3)
    s = f"{abs(v):g}"
    return f"- {s}" if v < 0 else s


def triple(a, b, c):
    return f"{num(a)} / {num(b)} / {num(c)}"


def load(path):
    pos = {}
    for line in open(path):
        a, _, p = line.partition(" ")
        m = re.match(r"/eos/out/get/patch/(\d+)/1/augment3d/position", a)
        if m:
            v = ast.literal_eval(p.strip())
            pos[int(m.group(1))] = tuple(v[2:8])
    return pos


def parse_only(s):
    out = set()
    for part in s.split(","):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else "patch.txt"
    only = parse_only(sys.argv[sys.argv.index("--only") + 1]) if "--only" in sys.argv else None
    dry = "--dry" in sys.argv
    pos = {c: v for c, v in load(path).items() if any(abs(x) > 1e-6 for x in v[:3])}
    if only:
        pos = {c: v for c, v in pos.items() if c in only}
    e = None if dry else Eos()
    if e:
        e.run("Patch", pause=0.6)
    for c, (x, y, z, rx, ry, rz) in sorted(pos.items()):
        cmds = [f"Chan {c} Position {triple(x, y, z)}"]
        if any(abs(r) > 1e-6 for r in (rx, ry, rz)):
            cmds.append(f"Chan {c} Orientation {triple(rx, ry, rz)}")
        for cmd in cmds:
            if dry:
                print(cmd)
            else:
                e.run(cmd, pause=0.05)
    print("placed", len(pos), "fixtures")


if __name__ == "__main__":
    main()
