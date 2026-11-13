"""THIS IS YOUR ARENA - event-driven timecode show, cue list 6 / event list 6.

Built on a real Eos effect + palette library (build_fx.py):
  step effects 830-840 (geometry-mapped chases), absolute palette effects 841-847,
  relative focus effects 850/851, colour palettes 61-68, focus palettes 61-68, beam palettes 61-62.
Every cue sits on a measured audio event (onsets.json); pulse trains use the track's 0.1481 s clock.
python show.py --dry | python show.py
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from rig import *
from fxlib import columns, rings, levels_z

DRY = "--dry" in sys.argv
LIST = 6
S = Show(list_no=LIST, dry=DRY, latency=0.125, outdir=HERE)
PULSE = 0.1481

# ---------------------------------------------------------------- vocabulary
C = lambda chs: spec(chs)
COLS = columns(ALL)                     # 10 front-view columns L->R
RINGS = rings(ALL)
TIERS = levels_z(ALL)
LO, LI = [c for c in ALL if X(c) < -6], [c for c in ALL if -6 <= X(c) < 0]
RI, RO = [c for c in ALL if 0 <= X(c) < 6], [c for c in ALL if X(c) >= 6]
RED, WHITE, CYAN, AMBER, MAG, BLUE, PURP, GREEN = 61, 62, 63, 64, 65, 66, 67, 68
FAN, CROSS, SWL, SWR, TUNNEL, STRAIGHT, AUD, FLOOR = 61, 62, 63, 64, 65, 66, 67, 68
cmds = []


def do(*c):
    cmds.extend(c)


def lv(chs, v):
    if chs:
        do(f"{C(chs)} {'Full' if v >= 100 else 'Out' if v <= 0 else 'At ' + str(int(v))}")


def cp(chs, n):
    if chs:
        do(f"{C(chs)} Color_Palette {n}")


def fp(chs, n):
    if chs:
        do(f"{C(chs)} Focus_Palette {n}")


def fx(chs, n):
    if chs:
        do(f"{C(chs)} Effect {n}")


def fxoff(chs=ALL):
    do(f"{C(chs)} Effect")


def strobe(chs, v):
    S.strobe([c for c in chs if c < 200], v)


def Q(t, label, fade=0, focus=None, color=None):
    """record everything queued in `cmds` as a cue at song time t"""
    global cmds
    for c in cmds:
        S.run(c, pause=0.035)
    cmds = []
    S.cue(t, fade, label, focus=focus if focus is not None else fade, color=color if color is not None else 0)


def blackout():
    fxoff(); lv(ALL, 0); strobe(SP, -2)


# ================================================================ THE SHOW
def preset():
    S.run("Chan 1 Thru 999 Effect", 0.1)
    lv(ALL, 0)
    do(f"{C(SP)} Beam_Palette 61")
    cp(SP, WHITE); fp(SP, STRAIGHT)
    do(f"{C(WASH)} Zoom 5"); cp(WASH, RED)
    S.aim(WOH, lambda c, x, y, z: (x, y - 1, 0))
    S.aim(WFL, lambda c, x, y, z: (x * 1.5, y + 3, 26))
    S.aim(TW, lambda c, x, y, z: (-x * 0.5, 4, z + 6))
    strobe(SP, -2)
    Q(0.0, "PRESET")


def intro():                                   # 0 - 4.6
    lv(ALL, 100); cp(ALL, WHITE); fp(SP, FAN)
    Q(0.218, "ROAR - arena ignites")
    lv(WASH, 0); lv(SP, 75); cp(SP, RED); fx(SP, 846)
    do(f"{C(V)} Delay 0 Thru 0.6")            # fanned discrete delays: floor beams peel off L->R
    Q(0.42, "Red searchlights", fade=1.2, focus=1.0)
    lv(TW, 100); cp(TW, WHITE)
    Q(1.12, "Tower flick")
    lv(TW, 0)
    Q(1.30, "flick out", fade=0.5)
    cp(WASH, WHITE); fx(ALL, 833); cp(SP, WHITE)
    Q(2.72, "HIT sparkle burst")
    fxoff(); lv(ALL, 0); lv(LEFT, 100); cp(LEFT, WHITE)
    Q(2.946, "HIT left")
    lv(ALL, 0); lv(RIGHT, 100); cp(RIGHT, WHITE)
    Q(3.46, "HIT right")
    lv(ALL, 0); lv(V, 60); cp(V, RED); fp(V, FAN); fx(V, 850); do("Effect 850 BPM 67.5")
    Q(3.70, "Red circle breathe", fade=0.6)


def hits_a():                                  # 4.7 - 10.9
    steps = [(4.717, TL + [c for c in OH if X(c) < -5]), (4.870, [c for c in OH + WOH if -5 <= X(c) < 0]),
             (5.013, [c for c in OH + WOH if 0 <= X(c) < 5]), (5.155, TR + [c for c in OH if X(c) >= 5])]
    for i, (t, chs) in enumerate(steps):
        fxoff(V); lv(ALL, 0); lv(chs, 100); cp(chs, WHITE)
        Q(t, f"Step hit {i + 1}")
    lv(ALL, 0); cp(ALL, RED); fx(ALL, 836)
    Q(5.712, "TIERS rise red")
    fxoff(); lv(ALL, 100); cp(ALL, WHITE); fp(SP, FAN); strobe(SP, 13)
    Q(6.197, "IMPACT 1 - white strobe")
    strobe(SP, -2); lv(WASH, 0); lv(SP, 85); cp(SP, RED); fp(SP, CROSS)
    Q(6.42, "into red cross", fade=0.3, focus=0.3)
    for i, t in enumerate([6.763, 6.920, 7.065, 7.207]):
        side = LEFT if i % 2 == 0 else RIGHT
        lv(WASH, 0); lv([c for c in side if c in WASH], 100); cp(WASH, WHITE)
        fp(SP, SWL if i % 2 == 0 else SWR)
        Q(t, f"Pulse snap {i + 1}", focus=0.12)
    lv(WASH, 0); cp(ALL, WHITE); fx(ALL, 832)
    Q(7.956, "CENTRE OUT")
    fxoff(); lv(ALL, 100); cp(ALL, RED); fp(SP, CROSS); strobe(SP, 10)
    Q(8.368, "IMPACT 2 - red cross strobe")
    strobe(SP, -2); lv(ALL, 0)
    Q(8.62, "drop out", fade=0.35)
    lv(WASH, 0); cp(WASH, CYAN); fx(WASH, 833)
    Q(9.131, "cyan sparkle")
    fxoff(); lv(ALL, 100); cp(ALL, WHITE); fp(SP, TUNNEL)
    Q(9.256, "IMPACT 3 - white tunnel")
    fx(ALL, 837)
    Q(9.42, "L-R SLAM")
    fxoff(); lv(ALL, 0); lv(SP, 35); cp(SP, RED); fp(SP, STRAIGHT)
    Q(9.85, "breath", fade=0.25, focus=0.25)
    lv(ALL, 0); cp(OH + WOH, WHITE); fx(OH + WOH, 839); cp(V, RED); fx(V, 838); cp(TW, RED); fx(TW, 840)
    fp(SP, FAN)
    Q(10.150, "TRUSS RUN + CHEVRON + TOWERS")


def riser_a():                                 # 10.9 - 17.3
    fxoff(); lv(SP, 100); cp(SP, CYAN); fx(SP, 846); lv(WOH, 30); cp(WOH, BLUE); lv(TW + WFL, 0)
    Q(10.95, "Cyan searchlights", fade=0.8)
    fxoff(OH); lv(OH, 100); cp(OH, WHITE); fp(OH, STRAIGHT)
    Q(12.832, "OH flash")
    fxoff(); lv(ALL, 100); cp(ALL, WHITE); fp(SP, TUNNEL)
    do(f"{C(by_x(WASH))} Delay 0 Thru 1.2")   # washes join in a fanned sweep during the riser
    Q(13.0, "RISER - converge white", fade=1.9, focus=1.9)
    for i, (t, chs) in enumerate([(14.991, LO), (15.128, LI), (15.256, RI), (15.424, RO)]):
        lv(ALL, 15); lv(chs, 100)
        Q(t, f"Riser hit {i + 1}")
    lv(ALL, 0); lv(SP, 80); cp(SP, PURP); fp(SP, FAN); fx(SP, 850); do("Effect 850 BPM 45")
    lv(TW, 40); cp(TW, MAG)
    Q(15.62, "Purple circles", fade=0.8)
    fxoff(SP); lv(SP, 0); cp(V, RED); fx(V, 838); cp(TW, RED); fx(TW, 840); fp(V, FAN)
    Q(17.328, "TICKING - chevron + towers")
    do("Effect 838 Rate 180"); do("Effect 840 Rate 180"); cp(OH, RED); fx(OH, 839)
    Q(17.903, "ticking faster")
    fxoff(); cp(ALL, WHITE); fx(ALL, 834); strobe(SP, 13)
    Q(18.651, "STROBE ALL")
    blackout()
    Q(19.35, "silence")
    lv(ALL, 100); cp(ALL, WHITE); fp(SP, AUD); strobe(SP, 13)
    Q(19.815, "BIG HIT - audience blinder")
    blackout()
    Q(20.05, "gap", fade=0.15)


def section_d():                               # 20.6 - 29.9
    lv(ALL, 100); cp(ALL, RED); fp(SP, CROSS)
    Q(20.657, "RESTART - red slam")
    cp(WASH, WHITE); fx(WASH, 831); fx(SP, 845); cp(SP, RED)
    Q(20.843, "WIPE BOUNCE + SNAP FAN-X")
    fxoff(); lv(ALL, 0); cp(WASH, CYAN); fx(WASH, 833); do("Effect 833 Size 60")
    lv(SP, 70); cp(SP, BLUE); fx(SP, 846)
    Q(21.731, "Ticking - cyan glitter, blue search", fade=0.3)
    fxoff(); lv(ALL, 0); lv(SP, 60); cp(SP, BLUE); fp(SP, FAN); fx(SP, 851); do("Effect 851 BPM 34")
    lv(WOH, 20); cp(WOH, PURP)
    do(f"{C(by_x(SP))} Delay 0 Thru 0.8")
    Q(23.45, "Ambient figure-8", fade=1.0)
    fxoff(); lv(ALL, 0); lv(OH, 100); cp(OH, WHITE); fp(OH, TUNNEL)
    Q(25.838, "OH tunnel hit")
    lv(ALL, 0); lv(LEFT, 100); cp(LEFT, WHITE)
    Q(26.285, "hi L")
    lv(ALL, 0); lv(RIGHT, 100); cp(RIGHT, WHITE)
    Q(26.535, "hi R")
    lv(ALL, 100); cp(ALL, WHITE); fp(SP, FAN)
    Q(27.019, "HIT full")
    lv(ALL, 40); cp(ALL, RED)
    Q(27.16, "red settle", fade=0.4)
    cp(ALL, RED); fx(ALL, 836)
    Q(27.603, "TIERS red")
    fxoff(); cp(ALL, WHITE); fx(ALL, 835)
    Q(28.482, "STROBE ODD-EVEN")
    fxoff(); lv(ALL, 0); lv(LEFT, 100)
    Q(28.958, "hit L")
    lv(ALL, 0); lv(RIGHT, 100)
    Q(29.071, "hit R")
    lv(ALL, 15); cp(ALL, RED)
    Q(29.30, "red low", fade=0.4)


def pulse_showcase():                          # 29.965 - 31.9 : a cue on every pulse of the train
    t0 = 29.965
    pats = []
    for k in range(10):
        pats.append(COLS[k] + (COLS[k + 1] if k + 1 < len(COLS) else []))
    seq = [("wipe", p) for p in pats[:5]] + [("ring", r) for r in RINGS[::-1]] + [("tier", t) for t in TIERS] \
          + [("odd", sum(COLS[0::2], [])), ("even", sum(COLS[1::2], []))]
    n = 14
    fx(SP, 842)
    for k in range(n):
        name, chs = seq[k % len(seq)]
        lv(WASH, 0); lv([c for c in chs if c in WASH], 100)
        cp(WASH, WHITE if k % 2 == 0 else RED)
        lv(SP, 100)
        fp(SP, FAN if k % 2 == 0 else CROSS)
        if k == 0:
            fx(SP, 842)
        Q(t0 + k * PULSE, f"PULSE {k + 1} {name}", focus=0.1)
    fxoff(); lv(ALL, 30); cp(ALL, RED)
    Q(32.10, "pulse out", fade=0.3)


def climax():                                  # 32.4 - 47.5
    cp(ALL, WHITE); fx(ALL, 833)
    Q(32.482, "sparkle burst")
    fxoff(); lv(ALL, 0); lv(OH, 100); fp(OH, CROSS)
    Q(33.234, "OH cross")
    lv(OH, 0); lv(V, 100); fp(V, FAN)
    Q(33.628, "V fan")
    lv(ALL, 100); cp(ALL, WHITE); fp(SP, AUD); strobe(SP, 13); fx(WASH, 834)
    Q(34.209, "MEGA IMPACT - blinder + strobe")
    fxoff(); strobe(SP, -2); lv(WASH, 0); lv(SP, 60); cp(SP, RED); fp(SP, TUNNEL)
    Q(34.55, "red tunnel", fade=0.8, focus=1.0)
    lv(TL, 100); cp(TL, RED)
    Q(34.984, "TL")
    lv(TL, 0); lv(TR, 100); cp(TR, RED)
    Q(35.193, "TR")
    blackout()
    Q(35.79, "gap")
    cp(ALL, WHITE); fx(ALL, 833)
    Q(36.058, "sparkle")
    fxoff(); lv(ALL, 0); lv(OH, 100); fp(OH, STRAIGHT)
    Q(36.748, "OH")
    lv(OH, 0); lv(V, 100); fp(V, FAN)
    Q(37.097, "V")
    lv(ALL, 0); cp(ALL, WHITE); fx(ALL, 832)
    Q(37.30, "CENTRE OUT build")
    do("Effect 832 Rate 160")
    Q(37.80, "build faster")
    do("Effect 832 Rate 240")
    Q(38.10, "build fastest")
    fxoff(); lv(ALL, 0); lv(LEFT, 100); cp(LEFT, WHITE)
    Q(38.333, "pickup L")
    lv(ALL, 0); lv(RIGHT, 100)
    Q(38.638, "pickup R")
    lv(ALL, 0); lv(V + TW, 100)
    Q(38.748, "pickup C")
    lv(ALL, 100); cp(ALL, WHITE); fp(SP, FAN); strobe(SP, 13)
    Q(38.922, "HUGE IMPACT")
    strobe(SP, -2); cp(WASH, WHITE); fx(WASH, 830); do("Effect 830 BPM 405"); fx(SP, 845); fx(SP + [], 842)
    Q(39.05, "WIPE + SNAP + COLOUR RUN")
    # ---- 40.1 - 42.45 : the roar. full stage strobe climax
    fxoff(); lv(ALL, 100); cp(ALL, WHITE); fx(WASH, 834); strobe(SP, 13); fx(SP, 847)
    Q(40.09, "ROAR - FULL STAGE STROBE")
    fx(WASH, 833); cp(WASH, RED); fx(SP, 842)
    Q(40.68, "roar - red glitter, colour run")
    fx(WASH, 834); cp(WASH, WHITE); fx(SP, 845)
    Q(41.27, "roar - strobe, snap")
    fx(WASH, 835); fx(SP, 847); cp(SP, WHITE)
    Q(41.86, "roar - odd/even, 4-way snap")
    fxoff(); strobe(SP, -2); cp(ALL, WHITE); fx(ALL, 837)
    Q(42.455, "L-R SLAM")
    fxoff(); lv(ALL, 100); cp(ALL, RED)
    Q(43.323, "red slam")
    cp(ALL, WHITE)
    Q(43.479, "white slam")
    blackout()
    Q(43.67, "gap")
    cp(ALL, WHITE); fp(SP, STRAIGHT); fx(ALL, 836)
    Q(43.912, "TIERS rising")
    fxoff(); lv(WASH, 0); lv(SP, 100); cp(SP, WHITE); fp(SP, FAN)
    Q(44.85, "FINAL POSE - sky fan", fade=0.3, focus=0.3)
    cp(SP, RED)
    Q(45.5, "fan to red", fade=1.5, color=1.5)
    lv(SP, 0)
    Q(47.0, "fade out", fade=0.8)


def build():
    preset(); intro(); hits_a(); riser_a(); section_d(); pulse_showcase(); climax()


if __name__ == "__main__":
    if not DRY:
        S.wipe()
    build()
    if not DRY:
        S.events()
        S.run("Chan 1", 0.1)
    S.save()
    print("cues", len(S.cues), "commands", S.ncmd)
    if DRY:
        for q in S.cues:
            print(f"{q['n']:3d} {q['t']:7.3f}  {q['label']}")

