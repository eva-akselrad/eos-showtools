"""Preview looks live in Augment3d and screenshot them into one contact sheet.

python dev/lookdev.py name "code for look 1" "code for look 2" ...
Each code string runs with `S` (a live rig.Show) and everything from rig in scope, then S.preview().
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from rig import *
import deskctl
from PIL import ImageGrab, Image, ImageDraw

import config
SC = config.OUT_DIR
FULL = "--full" in sys.argv
args = [a for a in sys.argv[1:] if a != "--full"]
name, looks = args[0], args[1:]
S = Show(dry=False)
deskctl.focus(config.EOS_WINDOW)
ims = []
for i, code in enumerate(looks):
    exec(code)
    S.preview()
    time.sleep(1.6)
    im = ImageGrab.grab(bbox=config.VIEW_BBOX).resize((928, 432) if FULL else (464, 216))
    ImageDraw.Draw(im).text((6, 4), f"{i + 1}", fill=(255, 255, 0))
    ims.append(im)
W, H = ims[0].size
cols = 1 if FULL else min(3, len(ims))
sheet = Image.new("RGB", (W * cols, H * ((len(ims) + cols - 1) // cols)))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * W, (i // cols) * H))
out = os.path.join(SC, name + ".png")
sheet.save(out)
print(out)



