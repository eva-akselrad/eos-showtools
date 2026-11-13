import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
"""Probe parameter values on one channel: python probe.py CHAN param v1 v2 ..."""
import sys, time
from eosctl import Eos

e = Eos()
e.send("/eos/subscribe", 1); time.sleep(0.4)
ch, param, vals = sys.argv[1], sys.argv[2], sys.argv[3:]
e.run(f"Chan {ch}"); time.sleep(0.5); e.drain()
for v in vals:
    e.send(f"/eos/chan/{ch}/param/{param}", float(v)); time.sleep(0.4)
    m = e.drain()
    w = [p[0] for t, a, p in m if "/active/wheel/" in a and param.split("_")[0].lower() in p[0].lower()]
    print(v, "->", w[-1:] if w else [p for t, a, p in m][-3:])

