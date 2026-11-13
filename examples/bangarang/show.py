"""BANGARANG (Skrillex ft. Sirah) - timecoded light show for the AI Test rig.

python show.py --dry      print the cue sheet only
python show.py            wipe cue list 5 / event list 5, record everything, write events

Timing: exact 110.000 BPM grid locked to the drum transients (analysis.json, t0 = first beat),
per-16th onset map (analysis_slots.json) for hit placement, and events fired LATENCY seconds early
(measured: Eos fires ~117 ms after the audio is heard via Reaper MTC).

Movement: every beam move is a cue fade whose focus time == the time to the next cue, so motion
is continuous and lands exactly on the next 8th/beat (no free-running effects drifting off-beat).
"""
import json, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from rig import *

DRY = "--dry" in sys.argv
LATENCY = 0.125
A = json.load(open(os.path.join(HERE, "analysis.json")))
SL = json.load(open(os.path.join(HERE, "analysis_slots.json")))
T0, P = A["t0"], A["period"]
B = lambda b: T0 + b * P                       # time of beat b (float ok)
slot = lambda b: SL[int(round(b * 4))] if 0 <= int(round(b * 4)) < len(SL) else {}
rnd = random.Random(110)

S = Show(list_no=5, dry=DRY, latency=LATENCY, outdir=HERE)

# --------------------------------------------------------------- colours
WHITE = (0, 0)
GREEN, CYAN, BLUE, PURPLE, MAGENTA, RED, AMBER, LIME, PINK = 120, 185, 235, 270, 305, 0, 28, 95, 330


def col(chs, h, s=100):
    if isinstance(h, tuple):
        S.C(chs, h[0], h[1])
    else:
        S.C(chs, h, s)


# --------------------------------------------------------------- beam shapes  (aim functions)
def fanV(w):      # floor chevron fans out to the sky; w 0 = parallel up, 1 = wide
    return lambda c, x, y, z: (x * (1 + 2.4 * w), y + 1.5, 22)


def scanV(a):     # all floor beams parallel, angle a degrees (- = stage left)
    s = math.sin(math.radians(a))
    return lambda c, x, y, z: (x + 20 * s, y + 1.5, 20)


def crossV(k=1.0):  # left beams to right, right to left
    return lambda c, x, y, z: (-x * 2.4 * k, y - 1, 14)


def coneV(th, r=7):  # all converge on a point circling above the stage
    return lambda c, x, y, z: (r * math.cos(th), 5 + 3 * math.sin(th), 15)


def waveV(ph):
    return lambda c, x, y, z: (x * 1.5, y + 1.5 + 7 * math.sin(ph + x * 0.45), 20)


def lowV(c, x, y, z):  # beams laid down toward the front edge (zap start)
    return (x * 1.4, y - 9, 3)


def fanOH(w):     # overhead into the house floor; w 0 = straight down, 1 = wide fan to audience
    return lambda c, x, y, z: (x * (1 + 1.1 * w), y - 9 * w, 0)


def scanOH(a):
    s = math.sin(math.radians(a))
    return lambda c, x, y, z: (x + 13 * s, y - 2, 0)


def coneOH(th, r=5):
    return lambda c, x, y, z: (r * math.cos(th), 3 + 3 * math.sin(th), 0)


def waveOH(ph):
    return lambda c, x, y, z: (x, y - 3 + 6 * math.sin(ph + x * 0.5), 0)


def crossOH(k=1.0):
    return lambda c, x, y, z: (-x * 1.3 * k, y - 4, 0)


def towers_in(c, x, y, z):   # side towers fire across the stage, up
    return (-x * 0.5, 4, z + 6)


def towers_down(c, x, y, z):
    return (x * 0.55, 1, 0)


def woh_down(c, x, y, z):
    return (x, y - 1, 0)


def woh_fan(c, x, y, z):
    return (x * 1.6, y - 6, 0)


def wfl_up(c, x, y, z):
    return (x * 1.5, y + 3, 26)


def wfl_cross(c, x, y, z):
    return (-x * 1.8, y + 3, 18)


# shape menus: (name, V(phase), OH(phase)) - phase runs 0..1 over one bar
SHAPES = [
    ("scan", lambda p: scanV(42 * math.sin(2 * math.pi * p)), lambda p: scanOH(-38 * math.sin(2 * math.pi * p))),
    ("cone", lambda p: coneV(2 * math.pi * p), lambda p: coneOH(-2 * math.pi * p)),
    ("wave", lambda p: waveV(2 * math.pi * p), lambda p: waveOH(2 * math.pi * p)),
    ("breathe", lambda p: fanV(0.5 + 0.5 * math.sin(2 * math.pi * p)), lambda p: fanOH(0.5 - 0.5 * math.sin(2 * math.pi * p))),
    ("cross", lambda p: crossV(math.cos(2 * math.pi * p)), lambda p: crossOH(math.cos(2 * math.pi * p))),
]

# --------------------------------------------------------------- pixel patterns over the washes
# 'front view' pixel space: u = x (-14..14).  Overhead wash rows y=2 / y=6, floor line, towers z=6/8/10
PIXEL = WASH


def px_wipe(p, width=3.5, rev=False):          # vertical bar sweeping L->R
    pos = -15 + 30 * p
    if rev:
        pos = -pos
    return lambda c, x, y, z: 100 if abs(x - pos) < width else 0


def px_center(p, width=3):                       # rings from the centre out
    r = 15 * p
    return lambda c, x, y, z: 100 if abs(abs(x) - r) < width else 0


def px_checker(k):
    return lambda c, x, y, z: 100 if (int(round((x + 14) / 2)) + int(round(y / 2 + z / 2)) + k) % 2 == 0 else 0


def px_sparkle(n, seed):
    on = set(random.Random(seed).sample(PIXEL, n))
    return lambda c, x, y, z: 100 if c in on else 0


def px_rows(k):                                  # alternating rows / tower levels
    return lambda c, x, y, z: 100 if (int(round(y / 4)) + int(round(z / 2)) + k) % 2 == 0 else 0


def px_vu(level):                                # towers fill up, overhead fills from the sides inward
    return lambda c, x, y, z: 100 if ((c in TW and (z - 5) / 5.5 <= level) or (c in WOH + WFL and (14 - abs(x)) / 14 <= level)) else 0


PIXPATS = [
    lambda s: px_wipe(s / 8),
    lambda s: px_center((s % 4) / 4),
    lambda s: px_checker(s),
    lambda s: px_sparkle(14, s * 7 + 3),
    lambda s: px_wipe(s / 8, rev=True),
    lambda s: px_rows(s),
]


# --------------------------------------------------------------- helpers
def step(b, label, fade=0, nxt=None, color=None):
    """record a cue at beat b; focus time = until next step so motion is continuous"""
    ft = round((nxt - b) * P, 2) if nxt is not None else 0
    S.cue(B(b), fade, label, focus=ft, color=color if color is not None else 0)


def blackout():
    S.I(ALL, 0)


def base_beams():
    S.strobe(SP, -2)
    S.P(SP, "Zoom", 15); S.P(SP, "Iris", 100); S.P(SP, "Edge", 0)
    S.P(SP, "Gobo_Select", 1); S.P(SP, "Beam_Fx_Select", 1); S.P(SP, "Diffusion", 0)
    S.P(WASH, "Zoom", 5)


# ================================================================ SECTIONS
def preset():
    blackout(); base_beams()
    col(ALL, BLUE)
    S.aim(V, fanV(0.2)); S.aim(OH, fanOH(0.0)); S.aim(WOH, woh_down); S.aim(WFL, wfl_up); S.aim(TW, towers_in)
    S.cue(0.0, 0, "Preset blackout")


def intro():
    """beats 0-16: synth stabs. Pixel twinkles on every stab, two centre beams slowly open."""
    # the 8th-grid positions where the synth actually hits
    stabs = [b for b in [k / 2 for k in range(0, 32)] if max(slot(b).get("full", 0), slot(b).get("snare", 0)) >= 0.4]
    centre = [140, 141]
    S.I(centre, 70); col(centre, BLUE); S.aim(centre, fanV(0))
    for i, b in enumerate(stabs):
        nb = stabs[i + 1] if i + 1 < len(stabs) else 16
        S.I(WOH + TW, 0)
        S.I(WOH + TW, px_sparkle(3 + i // 6, 1000 + i))
        col(WOH + TW, (WHITE if i % 4 == 0 else (BLUE, 60)))
        if i == len(stabs) // 2:
            S.I([135, 136, 145, 146], 60); col([135, 136, 145, 146], BLUE)
        S.aim(V, fanV(min(1, b / 16)))
        step(b, f"Intro stab {i + 1}", fade=0, nxt=nb)
    return stabs


def drums():
    """beats 16-40: drums + bass. Green laser layers build up, kick-locked pixel chase."""
    for k, b in enumerate(range(16, 40)):
        bar = (b - 16) // 4
        S.I(WOH + TW, 0)
        S.I(V, 100); col(V, GREEN if bar % 2 == 0 else LIME)
        shp = SHAPES[(bar // 2) % 3]
        S.aim(V, shp[1](((b - 16) % 4) / 4))
        if b >= 24:   # overhead joins
            S.I(OH, 85); col(OH, CYAN); S.aim(OH, shp[2](((b - 16) % 4) / 4))
        if b >= 32:   # pixels join
            S.I(WOH + TW, px_wipe(((b - 32) % 4) / 4 + 0.12, 4.5)); col(WOH + TW, BLUE)
        # kick on the beat -> floor line pulse
        S.I(WFL, 100 if b % 2 == 0 else 35); col(WFL, GREEN)
        step(b, f"Drums b{b} {shp[0]}", fade=0, nxt=b + 1)


def build1():
    """beats 40-47: riser. Steps accelerate 1/4 -> 1/8 -> 1/16, beams converge + whiten, strobe."""
    beats = [40, 41, 42, 43, 44, 44.5, 45, 45.5, 46, 46.25, 46.5, 46.75]
    for i, b in enumerate(beats):
        nb = beats[i + 1] if i + 1 < len(beats) else 47
        prog = i / len(beats)
        S.I(SP, 100); col(SP, (GREEN, int(100 - 100 * prog)))
        S.aim(V, coneV(2 * math.pi * prog * 2, r=7 - 6 * prog)); S.aim(OH, coneOH(-2 * math.pi * prog * 2, r=5 - 4 * prog))
        S.I(WASH, 0); S.I(WASH, px_vu(prog)); col(WASH, (0, 0))
        if b >= 45:
            S.strobe(SP, 6 + int(7 * (b - 45) / 2))
        step(b, f"Build1 {i + 1}", fade=0, nxt=nb)
    S.strobe(SP, -2); blackout()
    S.cue(B(47), 0, "SUCK OUT")


def drop(b0, b1, name, pals, zaps=(), final=False):
    """the drops: 2-bar cycles, half-time booms on beats 1 & 3, a cue every 8th for pixel chase +
    continuous beam motion, extra stabs on off-grid 16th transients, laser zaps."""
    steps = [b0 + k / 2 for k in range(int((b1 - b0) * 2))]
    # 16th-note transients that fall between the 8ths -> stabs
    stabs = [b0 + k / 4 for k in range(int((b1 - b0) * 4)) if k % 2 == 1 and slot(b0 + k / 4).get("full", 0) >= 0.62]
    allb = sorted(set(steps) | set(stabs))
    shape_i = 0
    for i, b in enumerate(allb):
        nb = allb[i + 1] if i + 1 < len(allb) else b1
        rel = b - b0
        cyc = int(rel // 8)                     # which 2-bar cycle
        c8 = int(round((rel % 8) * 2))          # 8th index in cycle 0..15
        pal = pals[cyc % len(pals)]
        hue_a, hue_b = pal
        shape = SHAPES[(cyc + (2 if final else 0)) % len(SHAPES)]
        ph = (rel % 4) / 4                      # phase within the bar (motion cycle = 1 bar)
        is_stab = b in stabs and b not in steps
        zap = any(abs(b - z) < 0.01 for z in zaps)
        after_zap = any(0.4 < b - z < 2.01 for z in zaps)

        # ---- beams: continuous motion
        S.I(SP, 100)
        S.strobe(SP, -2)
        col(V, hue_a if c8 < 8 else hue_b); col(OH, hue_b if c8 < 8 else hue_a)
        S.aim(V, shape[1](ph)); S.aim(OH, shape[2](ph))
        if final:
            col(odd(OH), (hue_a + 180) % 360)
        # ---- pixels: chase pattern changes every 2 bars, steps every 8th
        pat = PIXPATS[(cyc + (3 if final else 0)) % len(PIXPATS)]
        S.I(WASH, 0)
        S.I(WASH, pat(c8))
        col(WASH, hue_b if c8 % 4 < 2 else hue_a)
        fade = 0
        label = f"{name} c{cyc + 1}.{c8}"
        # ---- accents (half time: boom on beats 1 and 3 of every bar)
        if c8 in (0, 8):
            S.I(WASH, 100); col(WASH, WHITE if c8 == 0 else hue_a)
            S.I(OH, 100); col(OH, WHITE)
            label += " BOOM"
        elif c8 in (4, 12):
            S.I(TW + WFL, 100); col(TW + WFL, WHITE); col(V, WHITE)
            label += " hit"
        if is_stab:
            S.I(WASH, 0); S.I(TW + WFL, 100); col(TW + WFL, WHITE)
            S.I(OH, 30)
            label = f"{name} stab {b:.2f}"
        if zap:          # rising laser zap: floor beams slam low + strobe, then fan to the sky
            S.aim(V, lowV); col(V, WHITE); S.strobe(V, 13)
            S.I(WASH, 0); S.I(OH, 0)
            label = f"{name} ZAP"
        elif after_zap and not is_stab:
            S.aim(V, fanV(min(1.0, (b - [z for z in zaps if 0.4 < b - z < 2.01][0]) / 1.5)))
            col(V, WHITE)
        if final and c8 == 0:
            S.strobe(OH, 12)
        step(b, label, fade=fade, nxt=nb)


def verse():
    """beats 114-140: 3-3-2 kick pattern. Red/amber, each kick jumps the pixel and swings the beams."""
    kicks = []
    for k in range(114 * 4, 140 * 4):
        b = k / 4
        s = SL[k]
        if s.get("kick", 0) >= 0.55 and (not kicks or b - kicks[-1] >= 0.5):
            kicks.append(b)
    if kicks[0] > 114.01:
        kicks.insert(0, 114)
    for i, b in enumerate(kicks):
        nb = kicks[i + 1] if i + 1 < len(kicks) else 140
        side = 1 if i % 2 == 0 else -1
        S.I(SP, 0)
        S.I(V, 100); col(V, RED if (i // 8) % 2 == 0 else AMBER)
        S.aim(V, scanV(side * 35))
        if b >= 122:
            S.I(OH, 80); col(OH, AMBER); S.aim(OH, scanOH(-side * 30))
        S.I(WASH, 0)
        pos = (i % 10) / 10
        S.I(WOH + WFL, px_wipe(pos, 2.2, rev=(i // 10) % 2 == 1)); col(WOH + WFL, RED)
        S.I(TW, 100 if i % 2 == 0 else 0); col(TW, AMBER)
        step(b, f"Verse kick {i + 1}", fade=0, nxt=nb)
    return kicks


def build2():
    """beats 140-143: short riser into drop 2"""
    beats = [140, 141, 141.5, 142, 142.5, 142.75]
    for i, b in enumerate(beats):
        nb = beats[i + 1] if i + 1 < len(beats) else 143
        p = (i + 1) / len(beats)
        S.I(ALL, int(40 + 60 * p)); col(ALL, (RED, int(100 - 100 * p)))
        S.aim(V, coneV(math.pi * 2 * p, 6 * (1 - p) + 0.5)); S.aim(OH, coneOH(-math.pi * 2 * p, 4 * (1 - p) + 0.5))
        S.strobe(SP, 4 + i * 2)
        step(b, f"Build2 {i + 1}", fade=0, nxt=nb)
    S.strobe(SP, -2); blackout()
    S.cue(B(143), 0, "SUCK OUT 2")


def fourfloor():
    """beats 208-241: four-on-the-floor. Rainbow pixel chase, beams scan every beat, boom every beat."""
    blackout()
    beats = [208 + k / 2 for k in range(0, 64)]
    for i, b in enumerate(beats):
        nb = beats[i + 1] if i + 1 < len(beats) else 240
        bar = int((b - 208) // 4)
        on_beat = (b * 2) % 2 == 0
        hue = (bar * 45) % 360
        S.strobe(SP, -2)
        S.I(V, 100); col(V, hue); S.aim(V, scanV(40 if (int(b) % 2 == 0) == on_beat else -40) if bar < 4 else waveV(math.pi * (b - 208)))
        S.I(OH, 100 if on_beat else 60); col(OH, (hue + 180) % 360); S.aim(OH, coneOH(math.pi * (b - 208) / 2))
        S.I(WASH, 0)
        if on_beat:
            S.I(WOH + WFL + TW, 100); col(WASH, hue)
        else:
            S.I(WASH, px_checker(i)); col(WASH, (hue + 120) % 360)
        step(b, f"4floor bar {bar + 1} {'beat' if on_beat else 'and'}", fade=0, nxt=nb)
    # last bar 240: 16th strobe ramp then cut
    for k in range(4):
        b = 240 + k / 4
        S.I(ALL, 100 if k % 2 == 0 else 0); col(ALL, WHITE)
        step(b, f"4floor end {k + 1}", fade=0, nxt=b + 0.25)
    blackout()
    S.cue(B(241.25), 0, "BREAKDOWN cut")


def breakdown():
    """beats 241-272: air. Deep blue cathedral that slowly rotates; flash at the blip (256.25)."""
    pts = [(242, "breath"), (246, "rotate 1"), (250, "rotate 2"), (254, "rotate 3")]
    S.I(V, 70); col(V, BLUE); S.aim(V, coneV(0, 3)); S.I(WOH, 15); col(WOH, PURPLE)
    S.cue(B(242), 2.5, "Breakdown - cathedral", focus=2.5)
    for k, (b, lab) in enumerate(pts[1:]):
        S.aim(V, coneV(2 * math.pi * (k + 1) / 4, 3 + k))
        S.cue(B(b), 3.0, f"Breakdown {lab}", focus=round(4 * P, 2))
    S.I(ALL, 100); col(ALL, WHITE); S.aim(V, fanV(1)); S.aim(OH, fanOH(1))
    S.cue(B(256.25), 0, "Breakdown BLIP flash")
    S.I(ALL, 0); S.I(V, 60); col(V, PURPLE); S.aim(V, coneV(math.pi, 4)); S.I(TW, 25); col(TW, BLUE)
    S.cue(B(256.75), 1.5, "Breakdown after blip", focus=1.5)
    for k, b in enumerate([260, 264, 268]):
        S.aim(V, coneV(math.pi + 2 * math.pi * (k + 1) / 3, 4 + k)); S.I(V, 60 + 10 * k)
        S.I(OH, 20 + 15 * k); col(OH, BLUE); S.aim(OH, coneOH(-math.pi * k / 2, 2))
        S.cue(B(b), 3.5, f"Breakdown swell {k + 1}", focus=round(4 * P, 2))


def build3():
    """beats 272-303: kicks return; tension climbs. Quarter notes -> 8ths -> 16ths, red -> white."""
    beats = [272 + k for k in range(0, 24)] + [296 + k / 2 for k in range(12)] + [302 + k / 4 for k in range(4)]
    for i, b in enumerate(beats):
        nb = beats[i + 1] if i + 1 < len(beats) else 303
        p = (b - 272) / 31
        sat = int(100 - 100 * max(0, (p - 0.5) * 2))
        S.I(V, 100); col(V, (RED, sat))
        S.aim(V, scanV(40 * math.sin(math.pi * (b - 272) / 2)) if b < 288 else coneV(math.pi * (b - 272), 7 * (1 - p) + 0.5))
        S.I(OH, int(30 + 70 * p)); col(OH, (MAGENTA, sat)); S.aim(OH, fanOH(1 - p))
        S.I(WASH, 0); S.I(WASH, px_vu(p)); col(WASH, (RED, sat))
        on = (b == int(b))
        S.I(WFL, 100 if on else 30)
        if b >= 296:
            S.strobe(SP, int(5 + 8 * (b - 296) / 7))
        step(b, f"Build3 {i + 1}", fade=0, nxt=nb)
    S.strobe(SP, -2); blackout()
    S.cue(B(303), 0, "SUCK OUT 3")


def outro():
    """beats 368.5-388: the last stabs fade away."""
    S.strobe(SP, -2)
    S.I(ALL, 100); col(ALL, WHITE); S.aim(SP, fanV(1)); S.aim(OH, fanOH(1))
    S.cue(B(368.5), 0, "OUT - last hit")
    S.I(ALL, 0); S.I(V, 60); col(V, BLUE); S.aim(V, fanV(0.3)); S.I(WOH, 20); col(WOH, PURPLE)
    S.cue(B(369), 2.0, "Outro - settle", focus=2.0)
    for k, b in enumerate([372, 376, 380]):
        S.I(V, 50 - 12 * k); S.aim(V, scanV(25 if k % 2 == 0 else -25))
        S.I(WOH, 0); S.I(WOH, px_sparkle(4, 900 + k)); col(WOH, PURPLE)
        S.cue(B(b), 2.0, f"Outro drift {k + 1}", focus=round(4 * P, 2))
    blackout()
    S.cue(B(385), 4.0, "Fade to black")


def build():
    preset()
    intro()
    drums()
    build1()
    drop(48, 112, "DROP1", [(GREEN, MAGENTA), (CYAN, PINK), (LIME, PURPLE), (GREEN, RED)])
    # drop 1 tail: stutter kicks at 112, 112.5, 113 then out
    S.I(ALL, 0); S.I(V, 100); col(V, WHITE); S.aim(V, crossV(1))
    S.cue(B(112), 0, "Drop1 tail 1")
    S.I(V, 0); S.I(OH, 100); col(OH, WHITE); S.aim(OH, crossOH(1))
    S.cue(B(112.5), 0, "Drop1 tail 2")
    S.I(ALL, 100); col(ALL, WHITE)
    S.cue(B(113), 0, "Drop1 tail 3")
    blackout()
    S.cue(B(113.5), 0.3, "Drop1 out")
    verse()
    build2()
    drop(144, 208, "DROP2", [(CYAN, MAGENTA), (BLUE, WHITE), (PURPLE, CYAN), (MAGENTA, GREEN)],
         zaps=[151.5, 167.5, 183.5, 199.5])
    fourfloor()
    breakdown()
    build3()
    drop(304, 368, "FINAL", [(RED, CYAN), (MAGENTA, GREEN), (AMBER, BLUE), (GREEN, PINK), (CYAN, RED),
                             (PURPLE, AMBER), (BLUE, LIME), (PINK, CYAN)],
         zaps=[311.5, 327.5, 343.5, 359.5], final=True)
    outro()


if __name__ == "__main__":
    if not DRY:
        S.wipe()
    build()
    if DRY:
        for q in S.cues[:]:
            pass
        import collections
        print("cues:", len(S.cues), "commands:", S.ncmd)
        sec = collections.Counter(q["label"].split()[0] for q in S.cues)
        print(sec)
        if "--sheet" in sys.argv:
            for q in S.cues:
                print(f"{q['n']:4d} {q['t']:8.3f} f{q['fade']} fo{q['focus']}  {q['label']}")
    else:
        S.events()
    S.save()
    print("done", len(S.cues))

