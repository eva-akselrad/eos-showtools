"""eosctl - talk to ETC Eos over OSC/TCP (port 3032, OSC 1.0 "packet length" framing).

Eos listens for OSC on TCP 3032 when OSC is enabled in Setup > System > Show Control (OSC RX/TX).
On TCP, every OSC packet is prefixed with a 4-byte big-endian length. Port 3037 uses SLIP
framing instead and is NOT supported here.

Python API
    from eosctl import Eos
    e = Eos()                         # connect (host/port from config.py)
    e.run("Chan 101 Thru 110 Full")   # type a command line + Enter
    e.cmd("Chan 101", new=True)       # type without Enter (# = Enter inside the text)
    e.send("/eos/chan/101/param/x_focus/y_focus/z_focus", 1.0, 4.0, 0.0)   # raw OSC
    e.send("/eos/subscribe", 1)       # ask Eos to stream state (cue fires, wheels, softkeys ...)
    msgs = e.drain()                  # [(time.time(), address, [args])] received since last drain
    e.request("/eos/get/cue/6/count") # send + collect replies until quiet
    e.count("fx"); e.items("cp")      # list-style getters (/eos/get/<target>/count|index/N)

Every received message is stamped with time.time() on arrival (used by runtest.py).

CLI:
  python eosctl.py ping
  python eosctl.py cmd "Chan 1 Full Enter"        (sends to command line, '#' == Enter)
  python eosctl.py get /eos/get/patch/count       (prints all replies for ~1s)
  python eosctl.py patch                          (dump the patch)
  python eosctl.py list <target> [count]          target = group|preset|cp|fp|bp|ip|fx|cuelist|macro|cue/1 ...
  python eosctl.py watch [secs]                   print everything Eos sends
"""
import socket, struct, sys, threading, time, json
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_message import OscMessage
from pythonosc.osc_bundle import OscBundle


class Eos:
    def __init__(self, host=None, port=None):
        import config
        host = host or config.EOS_HOST
        port = port or config.EOS_PORT
        self.s = socket.create_connection((host, port), timeout=5)
        self.s.settimeout(None)
        self.msgs = []
        self.lock = threading.Lock()
        self.alive = True
        threading.Thread(target=self._rx, daemon=True).start()

    def _rx(self):
        buf = b""
        while self.alive:
            try:
                d = self.s.recv(65536)
            except OSError:
                break
            if not d:
                break
            buf += d
            while len(buf) >= 4:
                n = struct.unpack(">I", buf[:4])[0]
                if len(buf) < 4 + n:
                    break
                pkt, buf = buf[4:4 + n], buf[4 + n:]
                self._handle(pkt)

    def _handle(self, pkt):
        try:
            if pkt.startswith(b"#bundle"):
                for c in OscBundle(pkt):
                    self._handle(c.dgram if hasattr(c, "dgram") else c)
                return
            m = OscMessage(pkt)
            with self.lock:
                self.msgs.append((time.time(), m.address, list(m.params)))
        except Exception as e:
            with self.lock:
                self.msgs.append((time.time(), "!parse", [str(e)]))

    def send(self, addr, *args):
        """send one OSC message (args: int/float/str), length-framed for TCP"""
        b = OscMessageBuilder(address=addr)
        for a in args:
            b.add_arg(a)
        d = b.build().dgram
        self.s.sendall(struct.pack(">I", len(d)) + d)

    def drain(self):
        """return and clear all messages received so far: [(arrival time, address, args)]"""
        with self.lock:
            m, self.msgs = self.msgs, []
        return m

    def wait(self, pred, timeout=2.0):
        """block until a received message satisfies pred(address, args); returns it or None"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            with self.lock:
                for i, (t, a, p) in enumerate(self.msgs):
                    if pred(a, p):
                        return a, p
            time.sleep(0.01)
        return None

    def request(self, addr, *args, settle=0.3, timeout=3.0):
        """send then collect replies until quiet for `settle` s."""
        self.drain()
        self.send(addr, *args)
        out, t0, last = [], time.time(), time.time()
        while time.time() - t0 < timeout:
            m = self.drain()
            if m:
                out += m; last = time.time()
            elif out and time.time() - last > settle:
                break
            time.sleep(0.01)
        return out

    def cmd(self, text, new=True):
        """type into the command line. append '#' to execute (Enter)."""
        self.send("/eos/newcmd" if new else "/eos/cmd", text)

    def run(self, text, pause=0.05):
        """type a full command line and press Enter (appends #). Underscored softkey names work as
        text, e.g. "Copy_To", "Go_To_Cue", "Color_Palette". Use spaces around "/": "Cue 5 / 1"."""
        t = text.strip()
        if not t.endswith("#"):
            t += "#"
        self.cmd(t)
        time.sleep(pause)

    def count(self, target):
        r = self.request(f"/eos/get/{target}/count")
        for t, a, p in r:
            if a.endswith("/count") and p:
                return int(p[0])
        return 0

    def items(self, target, n=None):
        n = self.count(target) if n is None else n
        res = []
        for i in range(n):
            r = self.request(f"/eos/get/{target}/index/{i}", settle=0.15)
            res.append([(a, p) for t, a, p in r if "/eos/out/get/" in a])
        return res

    def close(self):
        self.alive = False
        self.s.close()


def main(a):
    e = Eos()
    if not a:
        print(__doc__); return
    c = a[0]
    if c == "ping":
        print(e.request("/eos/ping"))
    elif c == "cmd":
        e.run(" ".join(a[1:])); time.sleep(0.3)
        for m in e.drain():
            if "cmd" in m[1] or "error" in m[1].lower():
                print(m)
    elif c == "get":
        for m in e.request(a[1], *a[2:]):
            print(m[1], m[2])
    elif c == "patch":
        for it in e.items("patch"):
            for addr, p in it:
                print(addr, p)
    elif c == "list":
        n = int(a[2]) if len(a) > 2 else None
        for it in e.items(a[1], n):
            for addr, p in it:
                print(addr, p)
    elif c == "watch":
        secs = float(a[1]) if len(a) > 1 else 5
        t0 = time.time()
        while time.time() - t0 < secs:
            for m in e.drain():
                print(round(m[0] - t0, 2), m[1], m[2])
            time.sleep(0.05)
    e.close()


if __name__ == "__main__":
    main(sys.argv[1:])

