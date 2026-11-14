"""a3d_inspector.py - type values into the Augment3d Edit Mode Inspector (UI automation).

Augment3d objects (decks, truss, scenery) have no command-line syntax, so they are positioned
by typing into the Inspector fields. Field screen coordinates assume the layout used while
building the stage: 1920x1080, Augment3d tab full width, Edit Mode on, Inspector panel dragged
up so its top sits at y~185 (see docs/augment3d.md). Recalibrate FIELD_Y / AXIS_X if yours differs.

    python a3d_inspector.py size 20 10 1          # set Size X Y Z (metres)
    python a3d_inspector.py position 0 4 0        # Position X Y Z ('-' = leave unchanged)
    python a3d_inspector.py rotation - - 90
    python a3d_inspector.py name "Stage Deck"
    python a3d_inspector.py shot                  # screenshot the Inspector to out/inspector.png
    python a3d_inspector.py size 21 0.3 0.3 --layout truss    # truss objects (no Scale row)
"""
import sys, time
import deskctl, config

LAYOUTS = {  # Inspector rows differ by object type: truss objects have no Scale row
    "mesh":  {"position": 458, "rotation": 494, "scale": 528, "size": 579, "world": 612},
    "truss": {"position": 458, "rotation": 494, "size": 544, "world": 578},
}
FIELD_Y = LAYOUTS["mesh"]
AXIS_X = {"x": 1645, "y": 1735, "z": 1825}
NAME_XY = (1720, 253)
REGION = (1530, 60, 1870, 890)


def set_field(x, y, value):
    deskctl.click(x, y, double=True)
    time.sleep(0.12)
    deskctl.key_combo("ctrl+a")
    deskctl.type_text(str(value))
    deskctl.key_combo("enter")
    time.sleep(0.25)


def set_vec(field, vals):
    for axis, v in zip("xyz", vals):
        if v not in ("-", None):
            set_field(AXIS_X[axis], FIELD_Y[field], v)


def shot():
    out = config.out_path("inspector.png")
    deskctl.shot(out, region=REGION)
    return out


def main():
    global FIELD_Y
    a = sys.argv[1:]
    if "--layout" in a:
        i = a.index("--layout"); FIELD_Y = LAYOUTS[a[i + 1]]; del a[i:i + 2]
    if not a:
        print(__doc__); return
    deskctl.focus(config.EOS_WINDOW)
    if a[0] in LAYOUTS["mesh"]:
        set_vec(a[0], a[1:4])
    elif a[0] == "name":
        set_field(*NAME_XY, a[1])
    elif a[0] == "shot":
        pass
    deskctl.move(1915, 1075)
    print(shot())


if __name__ == "__main__":
    main()

