import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import time, sys
from eosctl import Eos
e = Eos()
e.run("Group 101 Out")
e.run("Chan 131 Thru 150 Full"); e.run("Chan 131 Thru 150 Hue 200 Saturation 100"); e.run("Chan 131 Thru 150 Zoom 5")
x, y, z = map(float, sys.argv[1:4])
for c in range(131, 151):
    e.send(f"/eos/chan/{c}/param/x_focus/y_focus/z_focus", x, y, z)
    time.sleep(0.02)
e.run("Chan 101 Thru 110 Full"); e.run("Chan 101 Thru 110 Hue 30 Saturation 100"); e.run("Chan 101 Thru 110 Zoom 5")
for c in range(101, 111):
    e.send(f"/eos/chan/{c}/param/x_focus/y_focus/z_focus", 0.0, 4.0, 0.0)
time.sleep(1.5)

