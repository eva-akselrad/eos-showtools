"""Run Eos commands live, then capture a burst of Augment3d frames (full-width tab) into a sheet.
python dev/fxshot.py name nframes interval "cmd1" "cmd2" ...
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from eosctl import Eos
from PIL import ImageGrab, Image, ImageDraw
import deskctl
import config
SC = config.OUT_DIR
BBOX = config.VIEW_BBOX
name, n, iv = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
e = Eos()
deskctl.focus(config.EOS_WINDOW)
for c in sys.argv[4:]:
    e.run(c, pause=0.06)
time.sleep(1.2)
ims = []
for i in range(n):
    t = time.time()
    im = ImageGrab.grab(bbox=BBOX).resize((464, 216))
    ImageDraw.Draw(im).text((4, 2), str(i), fill=(255, 255, 0))
    ims.append(im)
    time.sleep(max(0, iv - (time.time() - t)))
cols = 4
sheet = Image.new("RGB", (464 * cols, 216 * ((n + cols - 1) // cols)))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * 464, (i // cols) * 216))
out = os.path.join(SC, name + ".png"); sheet.save(out); print(out)

