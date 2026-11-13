"""eosui.py - drive Eos softkeys/keys by label + run command lines, printing cmd echo + softkeys.
python eosui.py "cmd:Effect 820 Enter" "soft:Type" "soft:Step Based" "key:enter" ...
cmd:X  -> command line (no auto Enter unless X ends with #)
run:X  -> command line + Enter
soft:Label -> press the softkey whose current label matches
key:name   -> press a hard key (/eos/key/name)
"""
import sys, time
from eosctl import Eos
e = Eos(); e.send("/eos/subscribe", 1); time.sleep(0.5)
soft = {}
def pump():
    for t, a, p in e.drain():
        if a.startswith("/eos/out/softkey/") and p:
            soft[int(a.split("/")[-1])] = p[0]
        if a == "/eos/out/user/1/cmd":
            pump.cmd = p[0]
pump.cmd = ""
pump()
for c in sys.argv[1:]:
    kind, _, arg = c.partition(":")
    if kind == "cmd":
        e.send("/eos/cmd", arg)
    elif kind == "run":
        e.send("/eos/newcmd", arg + "#")
    elif kind == "key":
        e.send("/eos/key/" + arg, 1.0); e.send("/eos/key/" + arg, 0.0)
    elif kind == "soft":
        n = [k for k, v in soft.items() if v.strip().lower() == arg.lower()]
        if not n:
            print("  !! no softkey", arg, "have:", sorted(soft.items())); continue
        e.send(f"/eos/softkey/{n[0]}", 1.0); e.send(f"/eos/softkey/{n[0]}", 0.0)
    time.sleep(0.45); pump()
    print(f"{c!r:40} -> {pump.cmd!r}")
print("softkeys:", [v for k, v in sorted(soft.items())])
