"""fxlib.py - build real Eos effects, palettes and presets from code (via typed command lines).

Discovered syntax (Eos 3.3, typed into /eos/newcmd from the Blind effect list):
  Effect 830 Create Type StepBased|Absolute       (create; needs [Effect][Effect] list open)
  Effect 830 Step 1 Thru 10 ##                     (create steps; second Enter confirms)
  Effect 830 Step 3 Chan 101 + 105 Thru 107        (channels in a step)
  Effect 830 Step 1 Thru 10 StepTime 0.15 | InTime 0 | Dwell 0.1 | DecayTime 0.3 | OnState 100 | OffState 0
  Effect 831 Action 1 Thru 4 ##  / Action 1 Color_Palette 61 / Action 2 @ 50 / Action 1 Thru 4 Time 0 / Dwell 0.3
  Effect 830 Attributes Random_Groups | Bounce | Reverse ...   (toggles)
  Effect 830 Grouping 2 / Trail 50 / Entry Cascade / BPM 135 / Label NAME
  Live:  Recall_From Effect 830   (run a step effect on its embedded channels)
         Chan ... Effect 831      (apply absolute/relative effect to a selection, selection order = distribution)
         Effect 830 BPM 270       (cue-level override, recorded into the cue)
         Chan ... Effect          (stop effects on those channels)
"""
import time
from rig import *


class FX:
    def __init__(self, show):
        self.S = show

    def run(self, t, pause=0.06):
        self.S.run(t, pause=pause)

    def confirm(self):
        if not self.S.dry:
            self.S.e.send("/eos/cmd", "#")
            time.sleep(0.08)

    def open_list(self):
        if self.S.dry:
            return
        for _ in range(2):
            self.S.e.send("/eos/key/effect", 1.0); self.S.e.send("/eos/key/effect", 0.0); time.sleep(0.35)

    def delete(self, a, b):
        self.run(f"Delete Effect {a} Thru {b}", pause=0.4); self.confirm(); self.confirm()

    # ---------------------------------------------------------- step effects
    def step(self, n, label, steps, step_time, in_t=0.0, dwell=None, decay=0.0, on=100, off=0, attrs=(), bpm=None):
        self.run(f"Effect {n}", 0.15)
        """steps: list of channel lists (one per step)"""
        dwell = step_time if dwell is None else dwell
        self.run(f"Effect {n} Create Type StepBased", 0.25)
        self.run(f"Effect {n} Step 1 Thru {len(steps)}", 0.25); self.confirm()
        for i, chs in enumerate(steps):
            if chs:
                self.run(f"Effect {n} Step {i + 1} {spec(chs)}", 0.05)
        self.run(f"Effect {n}", 0.15)
        rng = f"Effect {n} Step 1 Thru {len(steps)}"
        self.run(f"{rng} StepTime {step_time:.2f}")
        self.run(f"{rng} InTime {in_t:.2f}")
        self.run(f"{rng} Dwell {dwell:.2f}")
        self.run(f"{rng} DecayTime {decay:.2f}")
        self.run(f"{rng} OnState {on}")
        self.run(f"{rng} OffState {off}")
        for a in attrs:
            self.run(f"Effect {n} Attributes {a}")
        if bpm:
            self.run(f"Effect {n} BPM {bpm}")
        self.run(f"Effect {n} Label {label}")

    # ---------------------------------------------------------- absolute effects
    def absolute(self, n, label, levels, time_s, dwell, attrs=(), grouping=None, trail=None):
        """levels: list like ['Color_Palette 61', '@ 0', 'Focus_Palette 62']"""
        self.run(f"Effect {n} Create Type Absolute", 0.25)
        self.run(f"Effect {n} Action 1 Thru {len(levels)}", 0.25); self.confirm()
        for i, lv in enumerate(levels):
            self.run(f"Effect {n} Action {i + 1} {lv}")
        self.run(f"Effect {n}", 0.15)
        rng = f"Effect {n} Action 1 Thru {len(levels)}"
        self.run(f"{rng} Time {time_s:.2f}")
        self.run(f"{rng} Dwell {dwell:.2f}")
        for a in attrs:
            self.run(f"Effect {n} Attributes {a}")
        if grouping:
            self.run(f"Effect {n} Grouping {grouping}")
        if trail is not None:
            self.run(f"Effect {n} Trail {trail}")
        self.run(f"Effect {n} Label {label}")


# ---------------------------------------------------------- geometry helpers (front view)
def columns(chs, width=3.0, x0=-15.0):
    """split fixtures into vertical columns left->right"""
    n = int(30 // width) + 1
    cols = [[] for _ in range(n)]
    for c in chs:
        cols[int((X(c) - x0) // width)].append(c)
    return [c for c in cols if c]


def rings(chs, width=3.0):
    """centre-out rings by |x|"""
    n = int(15 // width) + 1
    r = [[] for _ in range(n)]
    for c in chs:
        r[min(n - 1, int(abs(X(c)) // width))].append(c)
    return [c for c in r if c]


def levels_z(chs):
    """bottom -> top tiers"""
    tiers = {}
    for c in chs:
        z = Z(c)
        k = 0 if z < 3 else 1 if z < 7 else 2 if z < 9 else 3
        tiers.setdefault(k, []).append(c)
    return [tiers[k] for k in sorted(tiers)]


