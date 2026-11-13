"""Run each argument as an Eos command line and print the console's response."""
import sys, time
from eosctl import Eos

e = Eos()
e.send("/eos/subscribe", 1)
time.sleep(0.4)
e.drain()
for c in sys.argv[1:]:
    if c.startswith("osc:"):
        parts = c[4:].split(" ")
        args = [float(x) for x in parts[1:]]
        e.send(parts[0], *args)
    elif c.startswith("key:"):
        e.send("/eos/key/" + c[4:], 1.0); e.send("/eos/key/" + c[4:], 0.0)
    else:
        e.run(c)
    time.sleep(0.5)
    m = e.drain()
    cmd = [p[0] for t, a, p in m if a == "/eos/out/user/1/cmd"]
    print(f"{c!r:45} -> {cmd[-1] if cmd else '(no cmd echo)'}")
