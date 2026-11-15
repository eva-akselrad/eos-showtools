"""UNION v3 - Philadelphia Union stadium show at Subaru Park, built for the PRESS BOX view
(south stand, looking north across the pitch). Cue list 7 / event list 7.

Audio: mashup of "Party Till We Die" (MAKJ & Timmy Trumpet ft. Andrew W.K.) and the Union "Doop"
song, 2:13. Piecewise tempo map (tempomap.json): 128.007 BPM to 0:51, then 143.29 BPM, then the
final-drop edit at 143.19 BPM.

Design rules (from the LD's notes on v2):
  * no wavy motion - positions SNAP (focus time <= 0.1 s) or hold
  * layers take turns leading: beams / strobes / ring - never everything doing the same thing
  * call & response north vs south, solos, contrast between sections
  * random strobes: seeded random-group step effects 887/888/889
Machine-only programming:
  * TRANSIENT POPS - every detected hi-hat / clap transient in the audio fires its own cue that pops
    a random strobe (seeded, never the same fixture twice in a row)
  * BEAM STACKING - risers add one beam per 8th note, each to its own random sky direction
  * TELEPORTS - on drop downbeats all 40 beams snap to one computed 3D convergence point
  * 13 STARS - the Doop melody: one gold pillar per sung note (onsets from the audio)

Everything uses the labelled groups 701-740 (build_fx.py groups) so it can be refined by hand.
Each section starts with a cue Scene label.
    python show.py --dry [--sheet]   |   python show.py
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import rig
from rig import Show, spec
import choreo as C

rig.use_rig({int(c): p for c, p in json.load(open(os.path.join(HERE, "rig.json")))["pos"].items()})
POS = rig.POS
TM = json.load(open(os.path.join(HERE, "tempomap.json")))["segments"]
AN = json.load(open(os.path.join(HERE, "analysis.json")))


def grid(seg, first_bar_beat):
    s = TM[seg]
    return lambda n, b=0: s["t0"] + (first_bar_beat + 4 * (n - 1) + b) * s["period"]


BAR_P1, BAR_P2, BAR_P3 = grid(0, 1), grid(1, 1), grid(2, 0)
bar = BAR_P1
BPM = 128.0
BEAT_FX = (881, 885, 890, 891, 892)

E, EN, ES, J, JN, JS, JW, JE, H, HN, HS, HW, HE = (C.E, C.EN, C.ES, C.J, C.JN, C.JS, C.JW, C.JE,
                                                   C.H, C.HN, C.HS, C.HW, C.HE)
JR = JN + JS
JV = JN + JW + JE        # strobes the press box looks AT (the south-roof JDCs hang right above the press box: kept dark)
ALL = C.ALL
# group numbers (build_fx.py groups) - used whenever a command addresses exactly that set
GROUPS = {701: E, 702: EN, 703: ES, 706: E[0::2], 707: E[1::2], 711: J, 712: JN, 713: JS, 714: JW, 715: JE,
          716: JR, 717: JV, 721: H, 722: HN, 723: HS, 724: HW, 725: HE, 726: HN + HS, 727: HW + HE,
          731: EN + JN + HN, 732: ES + JS + HS, 740: ALL}
GKEY = {tuple(sorted(v)): k for k, v in GROUPS.items()}


def sel(chs):
    k = GKEY.get(tuple(sorted(chs)))
    return f"Group {k}" if k else spec(chs)


NAVY, GOLD, LBLUE, WHITE, DEEP, WARM = 71, 72, 73, 74, 75, 76
R_UP, R_TENT, R_OUT, R_STANDS = 81, 82, 83, 84
SNAKE, SLAM, WIPE, STROBE, SPARK, PING, STARS = 880, 881, 882, 883, 884, 885, 886
RSTROBE_J, RSTROBE_E, RSTROBE_H = 887, 888, 889
NAVYGOLD, SKYSNAP, SKYSWEEP, CIRCLE = 890, 891, 892, 895

DRY = "--dry" in sys.argv
S = Show(list_no=7, dry=DRY, latency=0.125, outdir=HERE)
Q_ = []


def do(*c):
    Q_.extend(c)


def lv(chs, v):
    if chs:
        do(f"{sel(chs)} {'Full' if v >= 100 else 'Out' if v <= 0 else 'At ' + str(int(v))}")


def cp(chs, n):
    if chs:
        do(f"{sel(chs)} Color_Palette {n}")


def fp(chs, n):
    if chs:
        do(f"{sel(chs)} Focus_Palette {n}")


def fx(chs, n):
    if chs:
        do(f"{sel(chs)} Effect {n}")
        if n in BEAT_FX and abs(BPM - 128.0) > 0.5:
            do(f"Effect {n} BPM {BPM:.1f}")


def fxoff(chs=None):
    do(f"{sel(chs or ALL)} Effect")


def aim(chs, fn):
    """per-fixture XYZ (tracked by rig, sent at record time)"""
    for c in chs:
        S.aim([c], fn(c, *POS[c]) if callable(fn) else fn)


def Q(t, label, fade=0, focus=0.08, color=0, scene=None):
    global Q_
    for c in Q_:
        S.run(c, pause=0.035)
    Q_ = []
    n = S.cue(t, fade, label, focus=focus, color=color)
    if scene and not DRY:
        S.run(f"Cue {S.list} / {n} Scene {scene}", pause=0.05)
    return n


# ---------------------------------------------------------------- beam shapes (snap targets)
SH_PILLAR = lambda c, x, y, z: (x, y, z + 60)
SH_FAN = lambda c, x, y, z: (x * 1.8, y * 1.7, 75)                       # north fans up/back, south fans over us
SH_OVER = lambda c, x, y, z: (x * 1.1, 55 if y < 0 else y * 1.6, 32 if y < 0 else 70)  # south beams flatten across the pitch (reads from press box)
SH_X = lambda c, x, y, z: (-x * 0.9, -y * 1.3, 55)                     # north->south sky, south->north sky
SH_CROWN = lambda c, x, y, z: (0, 4, 52)
SH_LINES = lambda c, x, y, z: (x, -y * 0.2, 0)                         # beams lay lines across the pitch
TELEPORT = [(0, 10, 30), (-34, 14, 26), (34, 14, 26), (0, 26, 22), (-18, 4, 34), (18, 4, 34), (0, 12, 18),
            (-44, 22, 30), (44, 22, 30)]          # convergence points kept below ~34 m so they sit in the press-box frame


def shape(chs, fn):
    aim(chs, fn)


# ---------------------------------------------------------------- transient pops
def transients(t0, t1, kinds=("hats", "snare"), smin=0.2, gap=0.11):
    ev = sorted({round(x["t"], 3) for k in kinds for x in AN["trans"][k] if t0 <= x["t"] < t1 and x["s"] >= smin})
    out = []
    for t in ev:
        if not out or t - out[-1] >= gap:
            out.append(t)
    return out


def pops(t0, t1, pool, name, colour=WHITE, kinds=("hats", "snare"), smin=0.2, k=(1, 2), base=0, seed=1):
    """one cue per transient: a random 1-2 fixtures from `pool` flash Full, the previous ones drop to base"""
    rnd = C.rng(seed); last = []
    for i, t in enumerate(transients(t0, t1, kinds, smin)):
        pick = rnd.sample([c for c in pool if c not in last] or pool, rnd.choice(k))
        lv(last, base); lv(pick, 100); cp(pick, colour)
        Q(t, f"{name} pop {i + 1}", focus=0)
        last = pick
    lv(last, base)


def fixed(t, label, **kw):
    return Q(t, label, **kw)


# ================================================================ SECTIONS
def preset():
    S.run(f"{spec(ALL)} Effect", 0.1)
    S.run(f"{spec(ALL)} Home", 0.3)
    lv(ALL, 0); cp(ALL, NAVY); shape(E, SH_PILLAR); fp(H, R_UP)
    Q(0.0, "PRESET - Subaru Park dark", scene="Preset")


def intro():
    """chord stabs: one gold pillar pops on per stab, stacking across the north roof, then the crown"""
    stabs = transients(0.5, 6.2, ("full", "snare", "hats"), 0.3, 0.3)
    order = sorted(EN, key=lambda c: abs(POS[c][0]))                    # centre out
    for i, t in enumerate(stabs[:len(order)]):
        on = order[:i + 1]
        lv(on, 100); cp(on, GOLD if i % 2 == 0 else WARM); shape([order[i]], SH_PILLAR)
        Q(t, f"Intro stab {i + 1} - pillar {order[i]}", scene="Intro" if i == 0 else None)
    lv(E, 100); cp(EN, GOLD); cp(ES, LBLUE); shape(E, SH_CROWN); lv(JN, 30); cp(JN, GOLD)
    Q(bar(4), "TONE - 40 beams snap to the crown", scene="Tone")
    fx(JV, RSTROBE_J); lv(JV, 35); cp(JV, WHITE)
    Q(bar(4, 2), "crown + random strobe glitter")


def groove_callresp(b0, b1, name, ca=GOLD, cb=LBLUE, ring=False, seed=10):
    """north and south beams answer each other on every beat; strobes pop on hats; ring optional"""
    fxoff(); lv(ALL, 0)
    t0, t1 = bar(b0), bar(b1 + 1)
    beats = [bar(n, b) for n in range(b0, b1 + 1) for b in range(4)]
    rnd = C.rng(seed)
    if ring:
        lv(H, 70); cp(H, LBLUE); fp(H, R_TENT)
    first = True
    pts = transients(t0, t1)
    events = sorted([(t, "beat", i) for i, t in enumerate(beats)] + [(t, "pop", 0) for t in pts
                    if all(abs(t - bt) > 0.09 for bt in beats)])
    last = []
    for t, kind, i in events:
        if kind == "beat":
            north = (i % 2 == 0)
            side, other = (EN, ES) if north else (ES, EN)
            lv(other, 0); lv(side, 100); cp(side, ca if north else cb)
            shape(side, SH_FAN if north else SH_OVER) if (i // 4) % 2 == 0 else shape(side, SH_X)
            lv(last, 0); last = []
            Q(t, f"{name} beat {i + 1} {'N' if north else 'S'}", scene=name if first else None)
            first = False
        else:
            pick = rnd.sample(JV, 1)
            lv(last, 0); lv(pick, 100); cp(pick, WHITE); last = pick
            Q(t, f"{name} hat pop")
    lv(last, 0)


def solo_break(b0, name, nb=2):
    """everything out except ONE beam: it snaps between 4 positions, one per beat (solo)"""
    fxoff(); lv(ALL, 0)
    star = 310
    for k in range(nb * 4):
        lv([star], 100); cp([star], GOLD if k % 2 == 0 else WHITE)
        S.aim([star], [(-40, 50, 40), (40, 50, 40), (0, 0, 30), (0, 60, 70)][k % 4])
        Q(bar(b0, k), f"{name} solo beam {k + 1}", scene=name if k == 0 else None)


def stacking_riser(b0, b_end, name, suck_beat, seed=20):
    """bars b0..b_end-2: ring tent + random strobe build; then ONE NEW BEAM PER 8TH, each to its own
    random sky point; last bar 16th-note full-rig stutters; suck-out"""
    rnd = C.rng(seed)
    fxoff(); lv(ALL, 0); lv(H, 50); cp(H, NAVY); fp(H, R_TENT); fx(JV, RSTROBE_J); lv(JV, 35); cp(JV, WHITE)
    Q(bar(b0), f"{name} - ring tent + strobe bed", fade=0.8, scene=name)
    order = rnd.sample(E, len(E))
    eighths = [bar(n, k / 2) for n in range(b0 + 1, b_end) for k in range(8)]
    step = max(1, len(eighths) // len(order))
    on = []
    for i, c in enumerate(order):
        t = eighths[min(i * step, len(eighths) - 1)] if i * step < len(eighths) else None
        if t is None:
            break
        on.append(c)
        lv([c], 100); cp([c], WHITE if i > 30 else LBLUE)
        S.aim([c], (rnd.uniform(-70, 70), rnd.uniform(-10, 80), rnd.uniform(30, 90)))
        if i in (10, 20, 30):
            do(f"Effect {RSTROBE_J} Rate {100 + 60 * (i // 10)}")
        Q(t, f"{name} stack beam {i + 1} ({c})")
    fxoff(); lv(ALL, 100); cp(ALL, WHITE); shape(E, SH_CROWN); fp(H, R_TENT)
    k = 0
    while k / 4 < suck_beat:
        lv(ALL, 100 if k % 2 == 0 else 10)
        Q(bar(b_end, k / 4), f"{name} stutter {k + 1}", focus=0)
        k += 1
    lv(ALL, 0)
    Q(bar(b_end, suck_beat), f"{name} SUCK OUT")


def drop(b0, b1, name, final=False, seed=30):
    """drops: WHITE BLINDER + TELEPORT on bar 1, then 4-bar phrases where ONE layer leads:
       A beams teleport each downbeat (strobes random bed)
       B strobes lead: random strobe JDC+beams, beams parked in X, ring tent pulses on beats 1+3
       C call & response N/S per beat in navy/gold, ring snake
       D (final only) everything: teleports every beat, random strobes, ring pulses"""
    rnd = C.rng(seed)
    fxoff(); lv(E + H + JN, 100); cp(ALL, WHITE); aim(E, TELEPORT[0]); fp(H, R_TENT); fx(JN, STROBE)
    Q(bar(b0), f"{name} - WHITE BLINDER", scene=name)
    phases = ["A", "B", "C"] + (["D"] if final else [])
    for n in range(b0, b1 + 1):
        ph = phases[((n - b0) // 4) % len(phases)]
        if final and n >= b1 - 1:
            ph = "D"
        k = (n - b0) % 4
        for b in range(4):
            if n == b0 and b == 0:
                continue
            t = bar(n, b)
            if ph == "A":
                if b == 0:
                    fxoff(); lv(ALL, 0); lv(E, 100); cp(E, GOLD if k % 2 == 0 else LBLUE)
                    aim(E, TELEPORT[(n - b0) % len(TELEPORT)]); fx(JV, RSTROBE_J); lv(JV, 35); cp(JV, WHITE)
                    Q(t, f"{name} {n} A teleport")
                elif b == 2:
                    lv(E[0::2], 100); lv(E[1::2], 30)
                    Q(t, f"{name} {n}.3 A half", focus=0)
                else:
                    lv(E, 100)
                    Q(t, f"{name} {n}.{b + 1} A", focus=0)
            elif ph == "B":
                lead = (b == 0 and k == 0)
                if lead:                       # phrase start: strobes take the lead
                    fxoff(); lv(ALL, 0); lv(E, 70); cp(E, LBLUE); shape(E, SH_X); fx(E, RSTROBE_E)
                    lv(JV, 45); cp(JV, WHITE); fx(JV, RSTROBE_J); cp(H, GOLD); fp(H, R_TENT)
                lv(H, 100 if b in (0, 2) else 0)          # ring hits on 1 and 3
                what = "strobes lead" if lead else ("ring hit" if b in (0, 2) else "ring off")
                Q(t, f"{name} {n}.{b + 1} B {what}", focus=0.08 if lead else 0)
            elif ph == "C":
                if b == 0 and k == 0:
                    fxoff(); lv(ALL, 0); lv(H, 80); cp(H, LBLUE); fp(H, R_UP); fx(H, SNAKE)
                north = (b % 2 == 0)
                side, other = (EN, ES) if north else (ES, EN)
                lv(other, 0); lv(side, 100); cp(side, GOLD if north else LBLUE)
                shape(side, SH_FAN if north else SH_OVER)
                Q(t, f"{name} {n}.{b + 1} C {'N' if north else 'S'}")
            else:  # D: everything
                if b == 0:
                    fxoff(); lv(E + H, 100); lv(JV, 50); cp(E, WHITE if k % 2 else GOLD); cp(H, LBLUE); cp(JV, WHITE)
                    fx(JV, RSTROBE_J); fx(H, RSTROBE_H)
                aim(E, TELEPORT[rnd.randrange(len(TELEPORT))])
                Q(t, f"{name} {n}.{b + 1} D teleport")


def doop():
    """0:53 silence -> one gold beam; 0:55 the Doop melody: 13 STARS - one gold pillar per sung note;
    0:62 claps: strobe on every clap alternating N/S, ring pick-offs"""
    fxoff(); lv(ALL, 0); lv([310], 100); cp([310], GOLD); shape([310], SH_PILLAR)
    Q(53.18, "Silence - one gold beam", fade=2.0, scene="Doop")
    ON = json.load(open(os.path.join(HERE, "onsets.json")))["events"]
    def onset_times(a, b, gap):
        out = []
        for e in ON:
            if a <= e["t"] < b and (not out or e["t"] - out[-1] >= gap):
                out.append(e["t"])
        return out
    notes = onset_times(55.2, 61.9, 0.3)[:13]                    # the sung "doop" notes
    stars = sorted(E[0::3], key=lambda c: (POS[c][1] < 0, POS[c][0]))[:13]
    for i, t in enumerate(notes):
        on = stars[:i + 1]
        lv(on, 100); cp(on, GOLD if i % 2 == 0 else WHITE); shape([stars[i]], SH_PILLAR)
        Q(t, f"Doop star {i + 1}/13")
    claps = onset_times(61.9, 65.2, 0.3)
    for i, t in enumerate(claps):
        side = JN if i % 2 == 0 else JW + JE
        lv(JV, 0); lv(side, 100); cp(JV, WHITE)
        lv(H, 0); lv([H[(i * 7) % len(H)], H[(i * 7 + 16) % len(H)]], 100); cp(H, GOLD)
        Q(t, f"Doop clap {i + 1}", scene="Claps" if i == 0 else None)


def build():
    global bar, BPM
    preset()
    bar, BPM = BAR_P1, 128.0                                   # ---- PART 1  128 BPM
    intro()                                                    # 0:00.6
    groove_callresp(5, 8, "GROOVE A", GOLD, LBLUE, seed=11)     # 0:08.2
    groove_callresp(9, 11, "GROOVE A2", WHITE, LBLUE, ring=True, seed=12)
    solo_break(12, "BREAK A", 1)                               # 0:21.3
    stacking_riser(13, 20, "RISER", suck_beat=1.5, seed=21)    # 0:23.2 - 0:37.0
    drop(21, 24, "DROP 1", seed=31)                            # 0:38.2
    fxoff(); lv(ALL, 0); lv(E, 60); cp(E, GOLD); shape(E, SH_CROWN); lv(H, 30); cp(H, NAVY); fp(H, R_TENT)
    Q(bar(25), "Drop 1 decays - crown", fade=1.5, scene="Decay")
    lv(E[1::2], 0); lv(H, 0)
    Q(bar(26), "decay - half the beams", fade=2.5)
    lv(ALL, 0)
    Q(51.25, "SILENCE", fade=1.5, scene="Silence")
    bar, BPM = BAR_P2, 143.3                                    # ---- PART 2  143.3 BPM
    doop()                                                     # 0:53.2 - 1:05.3
    groove_callresp(8, 9, "BASS IN", LBLUE, GOLD, ring=True, seed=13)     # 1:05.3
    solo_break(10, "BASS OUT", 2)                              # 1:08.7
    groove_callresp(12, 13, "BASS BACK", GOLD, LBLUE, seed=14)  # 1:12.0
    drop(14, 20, "CHORUS", seed=32)                            # 1:15.4 - 1:27.1
    fxoff(); lv(ALL, 0); lv(EN, 100); cp(EN, GOLD); shape(EN, SH_FAN); fx(JN, RSTROBE_J); lv(JN, 50)
    Q(bar(21), "BREAK B - north answers alone", scene="Break B")
    pops(bar(21), bar(23), JW + JE, "BREAK B", WHITE, seed=41)
    groove_callresp(23, 24, "BASS AGAIN", LBLUE, GOLD, ring=True, seed=15)  # 1:30.4
    stacking_riser(25, 28, "BUILD 2", suck_beat=1.75, seed=22)  # 1:33.8 - 1:39.6
    bar, BPM = BAR_P3, 143.2                                    # ---- PART 3  final drop
    drop(1, 16, "FINAL DROP", final=True, seed=33)             # 1:39.75 - 2:06.6
    fxoff(); lv(ALL, 0); lv(E, 100); cp(E, GOLD); shape(E, SH_PILLAR); lv(H, 50); cp(H, NAVY); fp(H, R_UP)
    Q(bar(17), "OUTRO - gold pillars", scene="Outro")
    pops(bar(17), 130.5, E, "OUTRO", GOLD, kinds=("full", "snare"), smin=0.3, base=100, seed=42)
    cp(E, NAVY)
    Q(130.6, "pillars to navy", fade=1.0, color=1.0)
    lv(ALL, 0)
    Q(131.6, "BLACKOUT", fade=1.2, scene="End")


if __name__ == "__main__":
    if not DRY:
        S.wipe()
    build()
    # monotonic + spacing check (events need >= 1 frame between cues)
    ts = [q["t"] for q in S.cues]
    bad = [(S.cues[i]["n"], ts[i], ts[i + 1]) for i in range(len(ts) - 1) if ts[i + 1] <= ts[i]]
    if bad:
        sys.exit(f"non-increasing cue times: {bad[:8]}")
    if not DRY:
        S.events()
    S.save()
    print("cues", len(S.cues), "commands", S.ncmd)
    if DRY and "--sheet" in sys.argv:
        for q in S.cues:
            print(f"{q['n']:4d} {q['t']:8.3f}  {q['label']}")



