"""look.py - screenshot the Augment3d area into a contact sheet (no console commands sent).

    python look.py NAME [N] [INTERVAL]
      NAME      output file name (written to config.OUT_DIR/NAME.png)
      N         number of frames (default 1)
      INTERVAL  seconds between frames (default 0.5)

The capture area is config.VIEW_BBOX (set SHOWTOOLS_VIEW_BBOX if your Augment3d tab is elsewhere).
For "run these commands, then capture" use dev/fxshot.py; for a timed run use runtest.py.
"""
import ctypes, sys, time
from PIL import ImageGrab, Image
import config

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)   # physical pixels, matches deskctl
except Exception:
    pass


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    name = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    iv = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    imgs = []
    for _ in range(n):
        imgs.append(ImageGrab.grab(bbox=config.VIEW_BBOX))
        time.sleep(iv)
    w, h = 464, int(464 * (config.VIEW_BBOX[3] - config.VIEW_BBOX[1]) / (config.VIEW_BBOX[2] - config.VIEW_BBOX[0]))
    cols = min(n, 4)
    sheet = Image.new("RGB", (w * cols, h * ((n + cols - 1) // cols)))
    for i, im in enumerate(imgs):
        sheet.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
    out = config.out_path(name + ".png")
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
