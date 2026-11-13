"""Builds the 'Volatile Reaction' light show into Eos cue list 5 + timecode event list 5.

Everything is timed off analysis.json (beat grid of the song), so cues land on the music.
python show.py            -> build cues + events
python show.py --dry      -> just print the cue sheet
"""
import json, math, sys, time, ast, re, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, ROOT)
from eosctl import Eos

LIST = 5
DRY = "--dry" in sys.argv
A = json.load(open(os.path.join(HERE, "analysis.json")))
BEATS = A["beats"]
PH = A["downbeat_phase"]


def beat(bar, b=0):
    """time (s) of beat b (0..3, may be fractional) of bar (1-based)"""
    i = PH + 4 * (bar - 1) + int(b)
    t = BEATS[min(i, len(BEATS) - 1)]
    frac = b - int(b)
    if frac:
        t += frac * (BEATS[min(i + 1, len(BEATS) - 1)] - BEATS[min(i, len(BEATS) - 1)])
    return t


SPB = 60.0 / 152.0  # seconds per beat

# ---------------------------------------------------------------- rig
POS = {}
for line in open(os.path.join(ROOT, "patch.txt")):
    a, p = line.split(" ", 1)
    m = re.match(r"/eos/out/get/patch/(\d+)/1/augment3d/position", a)
    if m:
        v = ast.literal_eval(p.strip())
        POS[int(m.group(1))] = tuple(v[2:5])

R = lambda a, b: list(range(a, b + 1))
OHF, OHM, OHB = R(101, 110), R(111, 120), R(121, 130)
OH = OHF + OHM + OHB
VL, VR = R(131, 140), R(141, 150)
V = VL + VR
SP = OH + V
WF, WB, WFL = R(201, 210), R(211, 220), R(221, 230)
WOH = WF + WB
TL, TR = R(231, 239), R(240, 248)
TW = TL + TR
WASH = WOH + WFL + TW
ALL = SP + WASH
LEFT = [c for c in ALL if POS[c][0] < 0]
RIGHT = [c for c in ALL if POS[c][0] > 0]
odd = lambda L: L[0::2]
even = lambda L: L[1::2]


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


# ---------------------------------------------------------------- console io
E = None if DRY else Eos()
NCMD = 0


def run(t):
    global NCMD
    NCMD += 1
    if DRY:
        return
    E.run(t, pause=0.035)


def osc(addr, *a):
    if DRY:
        return
    E.send(addr, *a)
    time.sleep(0.008)


def lv(chs, l):
    if chs:
        run(f"{spec(chs)} At {l}" if l not in ("Full", "Out") else f"{spec(chs)} {l}")


def col(chs, h, s=100):
    if chs:
        run(f"{spec(chs)} Hue {int(h) % 360} Saturation {int(s)}")


def par(chs, name, v):
    if chs:
        run(f"{spec(chs)} {name} {v}")


def strobe(chs, v):
    """SolaFrame only: -2 open, 1..13 strobe speed"""
    chs = [c for c in chs if c < 200]
    if chs:
        run(spec(chs))
        osc("/eos/param/shutter_strobe", float(v))


def aim(chs, fn):
    for c in chs:
        x, y, z = fn(c, *POS[c])
        osc(f"/eos/chan/{c}/param/x_focus/y_focus/z_focus", float(x), float(y), float(z))


def fx(chs, n):
    if chs:
        run(f"{spec(chs)} Effect {n}")


def fxstop(chs):
    if chs:
        run(f"{spec(chs)} Effect")


# ---- focus targets (x right, y upstage, z up; audience at y<0)
T_UP = lambda c, x, y, z: (x, y, z + 30)                         # straight up
T_CATH = lambda c, x, y, z: (0, 6, 24)                           # cathedral apex
T_FANUP = lambda c, x, y, z: (x * 3.2, y + 4, z + 24)            # fan outward to sky
T_FLOOR = lambda c, x, y, z: (0, 4, 0)                           # converge centre stage
T_FLOORSPREAD = lambda c, x, y, z: (x * 0.9, 3, 0)               # straight-ish down
T_AUD = lambda c, x, y, z: (x * 1.6, -18, 3)                     # into the audience
T_AUDC = lambda c, x, y, z: (0, -18, 4)                          # all into audience centre (blinder)
T_CROSS = lambda c, x, y, z: (-x * 1.6, y - 2, max(z - 9, 0) if z > 5 else z + 18)  # X crossing
T_SKYCROSS = lambda c, x, y, z: (-x * 2.4, y + 2, 26)            # floor beams crossing in the sky
T_LEFT = lambda c, x, y, z: (-16, y - 6, (z + 14) if z < 5 else 1)
T_RIGHT = lambda c, x, y, z: (16, y - 6, (z + 14) if z < 5 else 1)
T_AUDLOW = lambda c, x, y, z: (x * 2.0, -14, 0)
T_DOWN = lambda c, x, y, z: (x, y, 0)


def T_WAVE(phase):
    return lambda c, x, y, z: (x * 1.2, y + 3, 20 + 8 * math.sin(phase + x * 0.5)) if z < 5 else \
        (x * 1.1, y - 2 + 5 * math.sin(phase + x * 0.45), 0)


def T_SWEEP(ang):
    """everything points the same direction (searchlight sweep). ang in deg, 0 = straight up/down"""
    s = math.sin(math.radians(ang))
    return lambda c, x, y, z: (x + 22 * s, y - 4, z + 22) if z < 5 else (x + 12 * s, y - 6, 0)


# ---------------------------------------------------------------- cue machinery
CUES = []  # (num, t, fade, label)
_n = [0]


def cue(t, fade, label, follow=None):
    _n[0] += 1
    n = _n[0]
    CUES.append((n, t, fade, label))
    if DRY:
        print(f"{n:4d} {t:8.3f}s  fade {fade:>5}  {label}")
        return
    time.sleep(0.15)
    cmd = f"Record Cue {LIST} / {n} Time {fade}"
    if follow:
        cmd += f" Follow {follow}"
    run(cmd)
    time.sleep(0.25)
    run(f"Cue {LIST} / {n} Label {label}")
    print(f"rec {n:4d} @{t:7.2f}s  {label}", flush=True)


def hue_cycle(i, base=0, step=60):
    return (base + i * step) % 360


# ================================================================= THE SHOW
def build():
    B = beat
    # ---------------- 0. preset: everything dark, beams preset in black
    run("Group 101 Effect")
    lv(ALL, "Out")
    strobe(SP, -2)
    par(SP, "Zoom", 5); par(SP, "Iris", 100); par(SP, "Edge", 0)
    par(SP, "Gobo_Select", 1); par(SP, "Beam_Fx_Select", 1)
    par(WASH, "Zoom", 5)
    col(ALL, 235, 100)
    aim(V, T_UP)
    aim(OH, T_FLOORSPREAD)
    aim(WASH, T_DOWN)
    cue(0.0, 0, "Preset - blackout")

    # ---------------- INTRO  bars 1-6 : drums + bass
    lv(V, 75); col(V, 235)
    cue(0.07, 0.15, "Ignition - floor beams up")
    aim(V, T_CATH); lv(V, 90); lv(WFL, 35); col(WFL, 255)
    cue(B(1), 8.5, "Cathedral closes over 9s")
    lv(OHB, 55); col(OHB, 195); aim(OHB, T_AUDLOW); par(OHB, "Zoom", 5)
    cue(B(4), 2.5, "Back truss cyan into house")
    # ---------------- BUILD  bars 7-19
    lv(WB, 45); col(WB, 285)
    lv(OHM, 70); col(OHM, 300); par(OHM, "Gobo_Select", 4); par(OHM, "Beam_Fx_Select", 3); aim(OHM, T_FLOORSPREAD)
    cue(B(7), 1.5, "Build - magenta gobo prism")
    aim(V, T_FANUP); col(V, 210)
    lv(OHF, 60); col(OHF, 270); aim(OHF, T_WAVE(0.5))
    cue(B(9), 3.0, "Fan opens, front truss into house")
    lv(TW, 45); col(TW, 235)
    aim(OHM, T_CROSS)
    cue(B(11), 2.0, "Towers on, mid truss crosses")
    aim(V, T_CATH)
    cue(B(12), 1.2, "Pull back to cathedral")
    # rapid hit run 19.41 - 21.73 : rows flash in sequence
    rows = [OHF, OHM, OHB, VL, VR, TW]
    hits = [h for h in A["hits"] if 19.3 < h < 21.8]
    for i, h in enumerate(hits):
        lv(SP + TW, 35)
        lv(rows[i % len(rows)], "Full"); col(rows[i % len(rows)], 0, 0)
        cue(h, 0, f"Hit run {i + 1}")
    # bar 15 warm build
    lv(SP, 80); col(SP, 25); col(WASH, 10); lv(WOH, 60); lv(TW, 70)
    aim(V, T_FANUP); aim(OH, T_FLOORSPREAD)
    cue(B(15), 1.0, "Warm build")
    aim(OH, T_FLOOR); aim(V, T_CATH); lv(ALL, 35); col(SP, 10)
    cue(B(17), 1.5, "Dip - everything converges")
    lv(ALL, 100); col(ALL, 0, 0); par(SP, "Zoom", 5); strobe(TW + V, 6)
    cue(B(18), 3.0, "RISER - white surge")
    for k in range(3):
        side = VL + TL + OHF[:5] if k % 2 == 0 else VR + TR + OHF[5:]
        lv(ALL, 15); lv(side, "Full")
        cue(B(19, k), 0, f"Pre-drop stab {k + 1}")
    strobe(SP, -2)
    lv(ALL, "Out")
    cue(B(19, 3), 0, "SUCK-OUT blackout")

    # ---------------- CHORUS 1  bars 20-37
    lv(ALL, "Full"); col(ALL, 0, 0); aim(SP, T_AUDC); aim(WASH, T_DOWN); par(SP, "Zoom", 5)
    cue(B(20), 0, "DROP - white blinder")
    chorus_cols = [(0, 25), (300, 0), (25, 0), (235, 300)]   # (spots, washes)
    pos_cycle = [(T_FANUP, T_CROSS), (T_SKYCROSS, T_FLOORSPREAD), (T_CATH, T_WAVE(0.8)), (T_WAVE(0), T_WAVE(1.5))]
    bar = 20
    blk = 0
    while bar <= 34:
        cs, cw = chorus_cols[(blk // 2) % 4]
        pv, po = pos_cycle[blk % 4]
        # downbeat: new positions/colours, washes punch full
        lv(SP, "Full"); lv(WASH, "Full")
        col(SP, cs); col(WASH, cw)
        col(odd(OHM), (cs + 180) % 360)
        aim(V, pv); aim(OH, po)
        par(OHM, "Beam_Fx_Select", 3 if blk % 2 else 1)
        cue(B(bar, 0 if bar > 20 else 1), 0.25 if bar > 20 else 0.4, f"Chorus1 bar {bar} - punch")
        # beat 2: washes decay
        lv(WOH, 40); lv(TW, 30)
        cue(B(bar, 1.5 if bar == 20 else 1), 0.35, f"Chorus1 bar {bar} - decay")
        # next bar: alternating sides bump on beat 1 and 3
        lv(WOH, 40); lv(LEFT, "Full"); lv([c for c in RIGHT if c in WASH], 25)
        cue(B(bar + 1, 0), 0, f"Chorus1 bar {bar + 1} - left")
        lv(RIGHT, "Full"); lv([c for c in LEFT if c in WASH], 25)
        cue(B(bar + 1, 2), 0, f"Chorus1 bar {bar + 1} - right")
        bar += 2
        blk += 1
    # bar 36: last punch, everything slams into the audience
    lv(ALL, "Full"); col(SP, 0, 0); col(WASH, 0); aim(SP, T_AUDC)
    cue(B(36), 0.2, "Chorus1 bar 36 - final punch")
    lv(WOH, 40); lv(TW, 30); col(SP, 0)
    cue(B(36, 1), 0.4, "Chorus1 bar 36 - decay")
    lv(ALL, 20); aim(V, T_CATH); aim(OH, T_FLOOR)
    cue(B(37), 1.4, "Chorus out - settle")

    # ---------------- VERSE 2  bars 38-46 : bass heavy, searchlights
    lv(ALL, "Out")
    lv(V, 85); col(V, 160); par(V, "Zoom", 5)
    lv(WFL, 55); col(WFL, 175)
    aim(V, T_SWEEP(-35))
    cue(B(38), 1.2, "Verse2 - teal searchlights L")
    for i, b in enumerate([40, 42, 44]):
        aim(V, T_SWEEP(35 if i % 2 == 0 else -35))
        if i == 0:
            lv(OHB, 60); col(OHB, 140); par(OHB, "Gobo_Select", 6); aim(OHB, T_FLOORSPREAD)
        if i == 1:
            lv(WB, 40); col(WB, 190)
        if i == 2:
            lv(OHM, 55); col(OHM, 120); aim(OHM, T_AUDLOW); par(OHM, "Beam_Fx_Select", 1)
        cue(B(b), 2.8, f"Verse2 - sweep {i + 2}")
    aim(V, T_CATH); lv(TW, 50); col(TW, 160)
    cue(B(46), 1.4, "Verse2 - gather")

    # ---------------- SECTION E bars 47-60 : purple / pink, overhead patterns
    lv(ALL, 70); col(SP, 275); col(WASH, 320); lv(WFL, 40)
    aim(OH, T_FLOORSPREAD); aim(V, T_FANUP); par(SP, "Gobo_Select", 1)
    cue(B(47), 0.6, "E - purple lift")
    for i, b in enumerate([48, 50, 52]):
        aim(OH, T_WAVE(i * 1.4)); aim(V, T_WAVE(i * 1.4 + 0.7))
        col(odd(SP), 275 + 25 * (i % 2)); col(even(SP), 320 - 25 * (i % 2))
        cue(B(b), 2.4, f"E - wave {i + 1}")
    # hits 81.73 / 82.5 / 83.29 / 86.38
    lv(ALL, 15); lv(LEFT, "Full"); col(LEFT, 0, 0); aim([c for c in SP if c in LEFT], T_RIGHT)
    cue(81.73, 0, "E hit 1 - left slams right")
    lv(ALL, 15); lv(RIGHT, "Full"); col(RIGHT, 0, 0); aim([c for c in SP if c in RIGHT], T_LEFT)
    cue(82.50, 0, "E hit 2 - right slams left")
    lv(ALL, 15); lv(V + OHM, "Full"); aim(V, T_CATH); aim(OHM, T_FLOOR)
    cue(83.29, 0, "E hit 3 - centre")
    lv(ALL, 70); col(SP, 300); col(WASH, 275); aim(OH, T_CROSS); aim(V, T_FANUP)
    cue(83.29 + 0.45, 0.8, "E - recover")
    lv(ALL, "Full"); col(ALL, 0, 0)
    cue(86.38, 0, "E hit 4 - full white")
    lv(ALL, 65); col(SP, 285); col(WASH, 330)
    cue(86.38 + 0.3, 0.6, "E - recover 2")
    par(SP, "Zoom", 5); aim(V, T_CATH); aim(OH, T_FLOOR); lv(SP, 100); lv(WASH, 50)
    cue(B(58), 4.5, "E - converge build")

    # ---------------- BREAKDOWN bars 61-65
    lv(ALL, "Out"); lv([105, 106], 80); col([105, 106], 0, 0); aim([105, 106], T_FLOOR)
    lv(WB, 12); col(WB, 240)
    cue(B(61), 0.8, "Breakdown - lone centre beam")
    lv([115, 116, 125, 126], 60); col([115, 116, 125, 126], 220, 40); aim([115, 116, 125, 126], T_FLOOR)
    cue(B(62), 1.5, "Breakdown - breath")
    lv(V, "Full"); col(V, 0, 0); aim(V, T_CATH); strobe(V, 3); lv(TW, 80); col(TW, 0, 0)
    cue(B(63), 3.0, "RISER 2 - cathedral ignites")
    strobe(V, 10)
    cue(B(64), 0.2, "RISER 2 - strobe accelerates", )
    strobe(SP, -2); lv(ALL, 70); col(SP, 300); col(WASH, 260); aim(V, T_FANUP); aim(OH, T_CROSS)
    cue(B(65), 0.4, "Release - magenta")

    # ---------------- STACCATO bars 66-73 : every hit gets a cue
    hits = [h for h in A["hits"] if 101.8 < h < 114.3]
    states = [
        (VL + WB[5:] + TL, lambda: aim(VL, T_SKYCROSS)),
        (VR + WB[:5] + TR, lambda: aim(VR, T_SKYCROSS)),
        (OHF + WF, lambda: aim(OHF, T_CROSS)),
        (OHM + OHB + WFL, lambda: aim(OHM + OHB, T_FLOOR)),
    ]
    palette = [0, 300, 25, 200]
    for i, h in enumerate(hits):
        on, f = states[i % 4]
        c = palette[(i // 8) % 4]
        lv(ALL, 8)
        lv(on, "Full"); col(on, c if i % 4 != 3 else (c + 180) % 360)
        f()
        cue(h, 0, f"Staccato {i + 1}")

    # ---------------- BUILD 2 bars 74-85
    lv(ALL, 40); col(SP, 210); col(WASH, 230); aim(V, T_FANUP); aim(OH, T_FLOORSPREAD)
    cue(B(74), 1.0, "Build2 - cool")
    for i, b in enumerate([75, 77, 79]):
        aim(V, T_SWEEP(-30 if i % 2 == 0 else 30)); aim(OH, T_WAVE(i))
        lv(ALL, 45 + 10 * i); col(SP, 210 - 20 * i)
        cue(B(b), 2.6, f"Build2 - sweep {i + 1}")
    lv(ALL, 75); col(SP, 190, 50); col(WASH, 200, 60); aim(V, T_CATH); aim(OH, T_AUDLOW)
    cue(B(81), 1.0, "Build2 - lift")
    lv(ALL, 90); col(ALL, 0, 20); aim(OH, T_FLOOR)
    cue(B(83), 3.0, "Build2 - whitening")
    lv(ALL, "Full"); col(ALL, 0, 0); strobe(SP, 12); par(SP, "Zoom", 5)
    cue(B(85), 1.5, "RISER 3 - full strobe")
    strobe(SP, -2); lv(ALL, "Out")
    cue(B(85, 3.5), 0, "SUCK-OUT 2")

    # ---------------- FINAL CHORUS bars 86-101
    lv(ALL, "Full"); col(ALL, 40, 70); aim(SP, T_AUDC); par(SP, "Beam_Fx_Select", 1)
    cue(B(86), 0, "FINAL DROP - gold blinder")
    final_pos = [(T_FANUP, T_FLOORSPREAD), (T_SKYCROSS, T_CROSS), (T_WAVE(0), T_WAVE(2)), (T_CATH, T_FLOOR)]
    for k, bar in enumerate(range(86, 102, 2)):
        hs = hue_cycle(k, 0, 45)
        pv, po = final_pos[k % 4]
        lv(SP, "Full"); lv(WASH, "Full")
        col(V, hs); col(OH, (hs + 180) % 360); col(WOH + WFL, (hs + 90) % 360); col(TW, hs, 60)
        aim(V, pv); aim(OH, po)
        par(OHM, "Beam_Fx_Select", 3 if k % 2 else 1)
        cue(B(bar, 1 if bar == 86 else 0), 0.25, f"Final bar {bar} - colour {k + 1}")
        lv(WOH, 45); lv(TW, 35)
        cue(B(bar, 2), 0.3, f"Final bar {bar} - decay")
        # chase across rows on the 2nd bar, 4 beats
        seq = [OHF, OHM, OHB, V]
        for j in range(4):
            lv(SP, 45); lv(seq[j], "Full")
            cue(B(bar + 1, j), 0, f"Final bar {bar + 1} - row chase {j + 1}")
        lv(SP, "Full")
    # ---------------- ENDING
    lv(ALL, "Full"); col(ALL, 0, 0); aim(SP, T_AUDC)
    cue(B(102), 0, "END HIT - white")
    lv(ALL, "Out"); lv(V, 70); col(V, 235); aim(V, T_UP)
    cue(B(102) + 0.4, 2.5, "Outro - floor beams fade to blue")
    lv(ALL, "Out")
    cue(163.0, 2.5, "Blackout")


def make_events():
    for n, t, fade, label in CUES:
        f = int(round(t * 30))
        hh, mm, ss, ff = f // 108000, (f // 1800) % 60, (f // 30) % 60, f % 30
        run(f"Event {LIST} / {n} Time {hh:02d}:{mm:02d}:{ss:02d}:{ff:02d} Cue {LIST} / {n}")
        time.sleep(0.03)
    print("events:", len(CUES))


if __name__ == "__main__":
    if not DRY:
        E.send("/eos/subscribe", 0)
        # fresh list / events
        run(f"Delete Cue {LIST} / 1 Thru 999 Enter")
        time.sleep(1.0)
        run(f"Event {LIST} / 1 Thru 999 Delete Enter")
        time.sleep(1.0)
    build()
    if "--noevents" not in sys.argv:
        make_events()
    json.dump([dict(n=n, t=round(t, 4), fade=fade, label=label) for n, t, fade, label in CUES],
              open(os.path.join(HERE, "cues.json"), "w"), indent=0)
    with open(os.path.join(HERE, "markers.txt"), "w") as f:
        for n, t, fade, label in CUES:
            f.write(f"{t:.3f}\tQ{n} {label}\n")
    print("cues", len(CUES), "commands", NCMD)


