"""UNION - Philadelphia Union themed stadium show at Subaru Park (cue list 7 / event list 7).

Mashup of "Party Till We Die" (MAKJ & Timmy Trumpet ft. Andrew W.K.) and the Philadelphia Union
"Doop" song, 128.000 BPM, 4:26. Rig: 40 Proteus Excalibur beams on the roof edges, 32 GLP JDC2 IP
strobes, 32 Proteus Hybrid Max around the pitch (see rig_union.py). Union colours navy / gold /
light blue, built on the palette + effect library from build_fx.py.

    python show.py --dry      cue sheet
    python show.py            wipe list 7 + event list 7, record, write events
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import rig
from rig import Show, spec

RIG = json.load(open(os.path.join(HERE, "rig.json")))
rig.use_rig({int(c): p for c, p in RIG["pos"].items()})
A = json.load(open(os.path.join(HERE, "analysis.json")))
T0, P = A["t0"], A["period"]                  # 128 BPM grid
BAR1 = 2                                       # bar 1 starts on beat 2 (drop lands on a bar line)
beat = lambda b: T0 + b * P
bar = lambda n, b=0: beat(BAR1 + 4 * (n - 1) + b)

R = lambda a, b: list(range(a, b + 1))
EN, ES = R(301, 320), R(321, 340); E = EN + ES
JN, JS, JW, JE = R(401, 412), R(413, 424), R(425, 428), R(429, 432); J = JN + JS + JW + JE; JR = JN + JS
HN, HS, HW, HE = R(501, 510), R(511, 520), R(521, 526), R(527, 532); H = HN + HS + HW + HE
ALL = E + J + H
NORTH, SOUTH = EN + JN + HN, ES + JS + HS
WEST = [c for c in ALL if rig.POS[c][0] < -20]; EAST = [c for c in ALL if rig.POS[c][0] > 20]

NAVY, GOLD, LBLUE, WHITE, DEEP, WARM = 71, 72, 73, 74, 75, 76
F_FAN, F_CROSS, F_CENTRE, F_CROWN, F_SWW, F_SWE, F_PILLAR, F_LINES = 71, 72, 73, 74, 75, 76, 77, 78
R_UP, R_TENT, R_OUT, R_STANDS = 81, 82, 83, 84
SNAKE, SLAM, WIPE, STROBE, SPARK, PING, STARS = 880, 881, 882, 883, 884, 885, 886
NAVYGOLD, SKYSNAP, SKYSWEEP, CIRCLE = 890, 891, 892, 895

DRY = "--dry" in sys.argv
S = Show(list_no=7, dry=DRY, latency=0.125, outdir=HERE)
Q_ = []


def do(*c):
    Q_.extend(c)


def lv(chs, v):
    if chs:
        do(f"{spec(chs)} {'Full' if v >= 100 else 'Out' if v <= 0 else 'At ' + str(int(v))}")


def cp(chs, n):
    if chs:
        do(f"{spec(chs)} Color_Palette {n}")


def fp(chs, n):
    if chs:
        do(f"{spec(chs)} Focus_Palette {n}")


def fx(chs, n):
    if chs:
        do(f"{spec(chs)} Effect {n}")


def fxoff(chs=None):
    do(f"{spec(chs or ALL)} Effect")


def Q(t, label, fade=0, focus=None, color=None):
    global Q_
    for c in Q_:
        S.run(c, pause=0.035)
    Q_ = []
    S.cue(t, fade, label, focus=focus if focus is not None else fade, color=color if color is not None else 0)


def preset():
    S.run(f"{spec(ALL)} Effect", 0.1)
    S.run(f"{spec(ALL)} Home", 0.3)
    lv(ALL, 0); cp(ALL, NAVY); fp(E, F_PILLAR); fp(H, R_UP)
    Q(0.0, "PRESET - Subaru Park dark")


def intro():
    # 0.19 impact: the whole stadium flashes white, then sinks to navy
    lv(ALL, 100); cp(ALL, WHITE); fp(E, F_FAN); fp(H, R_TENT)
    Q(0.19, "IMPACT - stadium ignites")
    lv(ALL, 0); lv(JR, 35); cp(JR, NAVY); lv(E, 60); cp(E, NAVY); fp(E, F_PILLAR)
    do(f"{spec(E)} Delay 0 Thru 1.5")
    Q(0.55, "Navy pillars rise W-E", fade=1.5)
    for n in range(1, 7):                         # chords: gold / navy halves swap every bar
        g, nv = (NORTH, SOUTH) if n % 2 else (SOUTH, NORTH)
        cp([c for c in g if c in E + H], GOLD); cp([c for c in nv if c in E + H], NAVY)
        lv(H, 70); fp(H, R_UP if n % 2 else R_OUT); fp(E, F_FAN if n % 2 else F_CROSS)
        Q(bar(n), f"Intro bar {n} - gold {'N' if n % 2 else 'S'}", fade=0.6, focus=bar(n + 1) - bar(n))
    lv(ALL, 0); lv(E, 100); cp(E, GOLD); fp(E, F_CROWN); lv(J, 25); cp(J, GOLD)
    Q(bar(7), "TONE - golden crown", fade=1.2, focus=2.5)
    fx(E, SPARK)
    Q(bar(8), "crown sparkles")


def groove(b0, b1, name, cols=(NAVY, GOLD), stars=False):
    """per-bar groove: sky snaps on the downbeat, JDC hits on 2 & 4, rattlesnake on the ring"""
    fxoff(); lv(ALL, 0)
    lv(E, 100); cp(E, cols[0]); fx(E, SKYSNAP)
    lv(H, 100); cp(H, LBLUE); fp(H, R_TENT); fx(H, SNAKE)
    Q(bar(b0), f"{name} - snake + sky snap")
    for n in range(b0, b1 + 1):
        c = cols[(n - b0) % 2]
        for b in (1, 3):                           # backbeats: JDC side hit
            side = JN if (n + b) % 2 else JS
            lv(JR, 0); lv(side, 100); cp(side, WHITE)
            Q(bar(n, b), f"{name} bar {n} hit {b + 1}")
        lv(JR, 0)
        if n < b1:
            cp(E, cols[(n + 1 - b0) % 2])
            if stars and (n - b0) % 4 == 3:
                fx(J, STARS)
            Q(bar(n + 1), f"{name} bar {n + 1} - {'gold' if cols[(n + 1 - b0) % 2] == GOLD else 'colour'}")


def break_(n, name, nbars=2):
    fxoff(); lv(ALL, 0); lv(E, 70); cp(E, GOLD); fp(E, F_PILLAR); lv(JW + JE, 40); cp(JW + JE, NAVY)
    Q(bar(n), f"{name} - gold pillars", fade=0.8, focus=1.5)


def riser(b0, b1, name):
    """long build: sky sweep effect accelerating, sparkle growing, whitening, final 16ths"""
    fxoff(); lv(ALL, 0); lv(E, 80); cp(E, LBLUE); fx(E, SKYSWEEP); lv(H, 60); cp(H, NAVY); fp(H, R_UP)
    Q(bar(b0), f"{name} - sky sweep", fade=1.0)
    rates = [100, 100, 125, 125, 150, 150, 200, 200, 250, 300, 350, 400]
    for i, n in enumerate(range(b0 + 1, b1 - 1)):
        do(f"Effect {SKYSWEEP} Rate {rates[min(i, len(rates) - 1)]}")
        if i == 4:
            fx(J, SPARK); lv(J, 70); cp(J, WHITE)
        if i == 8:
            cp(E, WHITE); cp(H, LBLUE); fx(H, SNAKE)
        Q(bar(n), f"{name} bar {n} rate {rates[min(i, len(rates) - 1)]}")
    # last two bars: 8ths then 16ths, all converge on the crown
    fxoff(); lv(ALL, 100); cp(ALL, WHITE); fp(E, F_CROWN); fp(H, R_TENT)
    steps = [bar(b1 - 1, k / 2) for k in range(8)] + [bar(b1, k / 4) for k in range(12)]
    for i, t in enumerate(steps):
        lv(ALL, 100 if i % 2 == 0 else 15)
        Q(t, f"{name} roll {i + 1}")
    lv(ALL, 0)
    Q(bar(b1, 3), f"{name} SUCK OUT")


def drop(b0, b1, name, final=False):
    """the drops: white blinder on bar 1, then 4-bar blocks cycling techniques; a cue every beat"""
    fxoff(); lv(ALL, 100); cp(ALL, WHITE); fp(E, F_CENTRE); fp(H, R_TENT); fx(J, STROBE)
    Q(bar(b0), f"{name} - WHITE BLINDER")
    blocks = ["slam", "snake", "stars", "ping"] if not final else ["slam", "snake", "ping", "stars", "wipe"]
    for n in range(b0, b1 + 1):
        blk = blocks[((n - b0) // 4) % len(blocks)]
        k = (n - b0) % 4
        for b in range(4):
            if n == b0 and b == 0:
                continue
            first = (b == 0)
            if first or (n == b0 and b == 1):
                fxoff(); lv(ALL, 100)
                if blk == "slam":
                    cp(E, GOLD if k % 2 == 0 else NAVY); fx(E, SKYSNAP); cp(JR, WHITE); fx(JR, SLAM)
                    cp(H, LBLUE); fp(H, R_TENT if k % 2 == 0 else R_OUT)
                elif blk == "snake":
                    cp(E, NAVY); fx(E, NAVYGOLD); fp(E, F_FAN if k % 2 == 0 else F_CROSS)
                    cp(H, GOLD); fp(H, R_UP); fx(H, SNAKE); cp(J, GOLD); lv(J, 30)
                elif blk == "stars":
                    cp(E, GOLD); fp(E, F_CROWN if k % 2 == 0 else F_FAN); fx(ALL, STARS); cp(J + H, WHITE)
                elif blk == "ping":
                    cp(E, LBLUE); fx(E, SKYSWEEP); do(f"Effect {SKYSWEEP} Rate 200")
                    cp(J + H, GOLD); fx(JW + JE + HW + HE, PING); fp(H, R_STANDS)
                elif blk == "wipe":
                    cp(E + JR, GOLD); fx(E + JR, WIPE); cp(H, NAVY); fx(H, SNAKE); fp(H, R_TENT)
                if final and k == 0:
                    fx(JW + JE, STROBE); cp(JW + JE, WHITE)
                Q(bar(n, b), f"{name} bar {n} {blk}")
            else:
                # beat accents inside the block: Hybrid ring flips between up and tent on every beat
                if blk in ("slam", "stars"):
                    fp(H, R_TENT if b % 2 else R_UP)
                    Q(bar(n, b), f"{name} bar {n}.{b + 1} ring", focus=0.25)
                elif blk == "snake" and b == 2:
                    fp(E, F_CROSS if k % 2 == 0 else F_FAN)
                    Q(bar(n, b), f"{name} bar {n}.3 sky flip", focus=0.4)


def doop():
    """108.77 s: the DOOP. Hard silence then hit: the stadium becomes navy & gold, slow and proud."""
    fxoff(); lv(ALL, 0)
    Q(108.60, "SILENCE")
    lv(ALL, 100); cp(ALL, WHITE); fp(E, F_FAN); fp(H, R_TENT)
    Q(108.77, "DOOP! - full stadium")
    cp(NORTH, GOLD); cp(SOUTH, NAVY); cp(JW + JE + HW + HE, LBLUE); fp(E, F_PILLAR)
    Q(109.05, "Union split - gold north / navy south", fade=0.8, color=0.8, focus=1.2)
    fx(E, CIRCLE); do(f"Effect {CIRCLE} BPM 32"); do(f"{spec(E)} Delay 0 Thru 2")
    Q(bar(60), "Doop - sky circles", fade=0.5)
    for i, n in enumerate(range(62, 70, 2)):
        a, b = (NORTH, SOUTH) if i % 2 else (SOUTH, NORTH)
        cp(a, GOLD); cp(b, NAVY); fp(H, R_UP if i % 2 else R_OUT)
        Q(bar(n), f"Doop bar {n} - swap", fade=1.5, color=1.5, focus=bar(n + 2) - bar(n))


def build():
    preset()
    intro()                                              # bars 1-8
    groove(9, 22, "GROOVE A")
    break_(23, "BREAK A")
    riser(25, 40, "RISER")                               # bars 25-40 (pre-drop 39-40 is the roll)
    drop(41, 54, "DROP 1")
    fxoff(); lv(ALL, 0); lv(E, 100); cp(E, GOLD); fp(E, F_CROWN); lv(J, 30); cp(J, GOLD)
    Q(bar(55), "TONE 2 - golden crown", fade=0.8, focus=2.0)
    fx(E, SPARK)
    Q(bar(57), "crown sparkles")
    doop()                                               # 108.6 - 130.7
    groove(70, 72, "BASS IN", cols=(LBLUE, GOLD))
    break_(73, "CALM", 4)
    fx(E, CIRCLE); do(f"Effect {CIRCLE} BPM 64")
    Q(bar(75), "calm - sky circles")
    groove(77, 93, "GROOVE B", cols=(GOLD, LBLUE), stars=True)
    break_(94, "BREAK B", 3)
    groove(97, 99, "BASS BACK", cols=(NAVY, GOLD))
    riser(100, 103, "BUILD 2")
    drop(104, 134, "FINAL DROP", final=True)
    # outro: 252.6 - 266
    fxoff(); lv(ALL, 0); lv(E, 100); cp(E, GOLD); fp(E, F_PILLAR); lv(H, 60); cp(H, NAVY); fp(H, R_UP)
    Q(bar(135), "OUTRO - gold pillars", fade=1.5)
    cp(E, NAVY)
    Q(bar(137), "pillars to navy", fade=4, color=4)
    lv(ALL, 0)
    Q(bar(140), "Fade to black", fade=6)


if __name__ == "__main__":
    if not DRY:
        S.wipe()
    build()
    if not DRY:
        S.events()
    S.save()
    print("cues", len(S.cues), "commands", S.ncmd)
    if DRY and "--sheet" in sys.argv:
        for q in S.cues:
            print(f"{q['n']:4d} {q['t']:8.3f}  {q['label']}")
