"""rig.py - state-based cue writer for the AI Test rig (Eos over OSC).

Instead of typing commands per cue, a show describes the WHOLE desired stage state for each
cue (intensity, colour, beam params, XYZ aim, strobe per channel). rig.Show diffs that against
what the console already has and sends only the changes, grouped into as few command lines as
possible, then records the cue. Tracking-safe: untouched params just carry over.

    from rig import *
    S = Show(list_no=5)
    S.I(V, 100); S.C(V, 120); S.aim(V, lambda c,x,y,z: (x, y, 30))
    S.cue(12.345, 0, "label", focus=0.5)
    S.events()       # writes timecode event list (same number as cue list)
"""
import ast, json, math, os, re, sys, time, copy

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# ---------------------------------------------------------------- rig geometry
POS = {}
for line in open(os.path.join(ROOT, "patch.txt")):
    a, p = line.split(" ", 1)
    m = re.match(r"/eos/out/get/patch/(\d+)/1/augment3d/position", a)
    if m:
        v = ast.literal_eval(p.strip())
        POS[int(m.group(1))] = tuple(v[2:5])

R = lambda a, b: list(range(a, b + 1))
OHF, OHM, OHB = R(101, 110), R(111, 120), R(121, 130)       # SolaFrame overhead rows y=0,4,8 (z 9.9)
OH = OHF + OHM + OHB
VL, VR = R(131, 140), R(141, 150)                           # SolaFrame floor chevron (z 1)
V = VL + VR
SP = OH + V                                                 # all 50 spots
WF, WB = R(201, 210), R(211, 220)                           # SolaPix overhead rows y=2,6
WOH = WF + WB
WFL = R(221, 230)                                           # SolaPix floor line y=0
TL, TR = R(231, 239), R(240, 248)                           # SolaPix side towers 3x3
TW = TL + TR
WASH = WOH + WFL + TW
ALL = SP + WASH
LEFT = [c for c in ALL if POS[c][0] < 0]
RIGHT = [c for c in ALL if POS[c][0] > 0]
odd = lambda L: L[0::2]
even = lambda L: L[1::2]
by_x = lambda L: sorted(L, key=lambda c: POS[c][0])
X = lambda c: POS[c][0]
Y = lambda c: POS[c][1]
Z = lambda c: POS[c][2]


def spec(chs):
    chs = sorted(set(chs))
    out, i = [], 0
    while i < len(chs):
        j = i
        while j + 1 < len(chs) and chs[j + 1] == chs[j] + 1:
            j += 1
        out.append(f"{chs[i]}" if i == j else f"{chs[i]} Thru {chs[j]}")
        i = j + 1
    return "Chan " + " + ".join(out)


def fmt(v):
    if isinstance(v, float):
        v = round(v, 1)
        if v == int(v):
            v = int(v)
    return v


# ---------------------------------------------------------------- show writer
class Show:
    def __init__(self, list_no=5, dry=False, fps=30, latency=0.0, outdir="."):
        self.list = list_no
        self.dry = dry
        self.fps = fps
        self.latency = latency      # seconds to fire events early (console chase latency)
        self.outdir = outdir
        self.cues = []
        self.ncmd = 0
        self.e = None
        if not dry:
            from eosctl import Eos
            self.e = Eos()
            self.e.send("/eos/subscribe", 0)
        # what the console has (None = unknown -> always send)
        self.cur = {c: {} for c in ALL}
        self.tgt = {c: {} for c in ALL}

    # ---------- low level io
    def run(self, t, pause=0.03):
        """send a raw command line (+Enter) now. Bypasses the state model: use for palettes,
        effects, delays and anything rig does not track."""
        self.ncmd += 1
        if not self.dry:
            self.e.run(t, pause=pause)

    def osc(self, addr, *a):
        """send a raw OSC message now"""
        self.ncmd += 1
        if not self.dry:
            self.e.send(addr, *a)
            time.sleep(0.006)

    # ---------- state setters (only change self.tgt)
    def set(self, chs, k, v):
        """target value v for state key k on channels chs (applied at the next flush/cue)"""
        for c in chs:
            self.tgt[c][k] = v

    def I(self, chs, v):
        """intensity 0-100, or v(chan, x, y, z) -> 0..100 per channel (pixel patterns)"""
        if callable(v):
            for c in chs:
                self.tgt[c]["I"] = max(0, min(100, int(round(v(c, *POS[c])))))
        else:
            self.set(chs, "I", int(round(v)))

    def C(self, chs, h, s=100):
        """colour as hue (deg) + saturation (0-100), or h(chan, x, y, z) -> (hue, sat)"""
        if callable(h):
            for c in chs:
                hh, ss = h(c, *POS[c])
                self.tgt[c]["HS"] = (int(round(hh)) % 360, int(round(ss)))
        else:
            self.set(chs, "HS", (int(round(h)) % 360, int(round(s))))

    def P(self, chs, name, v):
        """any other parameter by its command-line name, e.g. P(SP, "Zoom", 15), P(SP, "Gobo_Select", 3)"""
        self.set(chs, name, v)

    def strobe(self, chs, v):
        """SolaFrame shutter strobe (spots only): -2 = open, 1..13 = strobe speed.
        Sent via OSC /eos/param because negative numbers misparse on the command line."""
        self.set([c for c in chs if c < 200], "strobe", float(v))

    def aim(self, chs, fn):
        """XYZ focus target in metres: a tuple, or fn(chan, x, y, z) -> (tx, ty, tz) using the
        fixture position (x right, y upstage, z up; the audience is at y < 0)"""
        for c in chs:
            x, y, z = fn(c, *POS[c]) if callable(fn) else fn
            self.tgt[c]["xyz"] = (round(float(x), 2), round(float(y), 2), round(float(z), 2))

    def get(self, c, k, d=None):
        return self.tgt[c].get(k, d)

    # ---------- diff + send
    def flush(self):
        """diff target vs console state and send only the changes: one command line per
        (parameter, value) group, then one OSC message per changed XYZ"""
        groups = {}
        xyz = []
        for c in ALL:
            t, cu = self.tgt[c], self.cur[c]
            for k, v in t.items():
                if cu.get(k) == v:
                    continue
                if k == "xyz":
                    xyz.append((c, v))
                else:
                    groups.setdefault((k, v), []).append(c)
        # intensity / colour / params as grouped command lines
        for (k, v), chs in sorted(groups.items(), key=lambda kv: (kv[0][0] != "I", str(kv[0]))):
            if k == "I":
                self.run(f"{spec(chs)} {'Full' if v >= 100 else 'Out' if v <= 0 else 'At ' + str(v)}")
            elif k == "HS":
                self.run(f"{spec(chs)} Hue {v[0]} Saturation {v[1]}")
            elif k == "strobe":
                self.run(spec(chs))
                self.osc("/eos/param/shutter_strobe", float(v))
            else:
                self.run(f"{spec(chs)} {k} {fmt(v)}")
        for c, (x, y, z) in xyz:
            self.osc(f"/eos/chan/{c}/param/x_focus/y_focus/z_focus", x, y, z)
        for c in ALL:
            self.cur[c].update(copy.deepcopy(self.tgt[c]))

    def cue(self, t, fade=0, label="", focus=None, color=None, beam=None):
        """flush, then Record Cue <list>/<n> at song time t (s). fade = cue (intensity) time;
        focus/color/beam = category times (None = same as fade). Returns the cue number."""
        self.flush()
        n = len(self.cues) + 1
        self.cues.append(dict(n=n, t=round(float(t), 4), fade=fade, focus=focus, color=color, label=label))
        if self.dry:
            return n
        time.sleep(0.08)
        self.run(f"Record Cue {self.list} / {n} Time {fmt(fade)}", pause=0.12)
        if focus is not None and focus != fade:
            self.run(f"Cue {self.list} / {n} Focus Time {fmt(focus)}")
        if color is not None and color != fade:
            self.run(f"Cue {self.list} / {n} Color Time {fmt(color)}")
        if beam is not None and beam != fade:
            self.run(f"Cue {self.list} / {n} Beam Time {fmt(beam)}")
        if label:
            self.run(f"Cue {self.list} / {n} Label {label[:30]}")
        if n % 10 == 0:
            print(f"rec {n:4d} @{t:7.2f}s  {label}", flush=True)
        return n

    def preview(self):
        """apply the target state live without recording (for look development)"""
        self.flush()

    # ---------- housekeeping
    def wipe(self):
        """delete this list's cues + events"""
        self.run(f"Delete Cue {self.list} / 1 Thru 1999 Enter", pause=1.5)
        self.run(f"Event {self.list} / 1 Thru 1999 Delete Enter", pause=1.5)

    def frame(self, t):
        """timecode frame for song time t, fired `latency` seconds early"""
        return int(round((t - self.latency) * self.fps))

    def events(self):
        """write Event <list>/<n> Time hh:mm:ss:ff Cue <list>/<n> for every recorded cue
        (never two events on the same frame)"""
        last = -1
        for q in self.cues:
            f = max(self.frame(q["t"]), last + 1)    # never two events on one frame
            last = f
            hh, mm, ss, ff = f // (3600 * self.fps), (f // (60 * self.fps)) % 60, (f // self.fps) % 60, f % self.fps
            q["frame"] = f
            self.run(f"Event {self.list} / {q['n']} Time {hh:02d}:{mm:02d}:{ss:02d}:{ff:02d} Cue {self.list} / {q['n']}", pause=0.025)
        print("events:", len(self.cues))

    def save(self):
        """write cues.json (n, t, fade, focus, color, label, frame) and markers.txt for Reaper"""
        json.dump(self.cues, open(os.path.join(self.outdir, "cues.json"), "w"), indent=0)
        with open(os.path.join(self.outdir, "markers.txt"), "w") as f:
            for q in self.cues:
                f.write(f"{q['t']:.3f}\tQ{q['n']} {q['label']}\n")

