"""choreo.py - geometry engine for the Union show.

Per-fixture targets computed from fixture positions:
  - pitch-canvas formations: 40 Excalibur spots drawn on the grass (letters, stars, rings, the crest),
    each fixture assigned to a reachable target by an optimal assignment (Hungarian) so beams
    don't cross needlessly and nothing exceeds the tilt limit of an upright head.
  - sky formations: pillars, fans, crosses, converging points
  - deterministic "random" (seeded) selections for strobes, sparkle and pick-offs
Pitch frame: centre (0,0,0), long axis X (+X east), +Y north, 104 x 64 m. Press box: south stand.
"""
import json, math, os, random
import numpy as np
from scipy.optimize import linear_sum_assignment

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = json.load(open(os.path.join(HERE, "rig.json")))
POS = {int(c): tuple(p) for c, p in RIG["pos"].items()}
R = lambda a, b: list(range(a, b + 1))
EN, ES = R(301, 320), R(321, 340); E = EN + ES
JN, JS, JW, JE = R(401, 412), R(413, 424), R(425, 428), R(429, 432); J = JN + JS + JW + JE; JR = JN + JS
HN, HS, HW, HE = R(501, 510), R(511, 520), R(521, 526), R(527, 532); H = HN + HS + HW + HE
ALL = E + J + H
MAX_DOWN = 43.0          # deg below horizontal an upright Proteus can reach (tilt 135 from vertical)
PITCH_HL, PITCH_HW = 52.0, 32.0


def down_angle(c, t):
    x, y, z = POS[c]
    d = math.hypot(t[0] - x, t[1] - y)
    return math.degrees(math.atan2(z - t[2], d))


def assign(fixtures, targets, penalty=1e4):
    """optimal fixture->target assignment; unreachable pairs get a big cost.
    len(targets) may be < len(fixtures): leftovers get None."""
    C = np.zeros((len(fixtures), len(targets)))
    for i, c in enumerate(fixtures):
        for j, t in enumerate(targets):
            x, y, z = POS[c]
            C[i, j] = math.dist((x, y), (t[0], t[1])) + (penalty if down_angle(c, t) > MAX_DOWN else 0)
    ri, cj = linear_sum_assignment(C)
    out = {c: None for c in fixtures}
    for i, j in zip(ri, cj):
        out[fixtures[i]] = targets[j]
    return out


# ------------------------------------------------------------------ pitch drawings (x, y on grass)
def ring(n, r, cx=0, cy=0, rot=0):
    return [(cx + r * math.cos(rot + 2 * math.pi * k / n), cy + r * math.sin(rot + 2 * math.pi * k / n), 0) for k in range(n)]


def star(n_pts=5, r_out=26, r_in=10, n=40, rot=math.pi / 2):
    """outline of a star, n points evenly along the perimeter"""
    verts = []
    for k in range(2 * n_pts):
        r = r_out if k % 2 == 0 else r_in
        a = rot + math.pi * k / n_pts
        verts.append((r * math.cos(a), r * math.sin(a)))
    return along(verts + [verts[0]], n)


def along(poly, n):
    """n points evenly spaced along a polyline"""
    seg = [math.dist(poly[i], poly[i + 1]) for i in range(len(poly) - 1)]
    L = sum(seg); out = []
    for k in range(n):
        d = L * k / n; i = 0
        while i < len(seg) - 1 and d > seg[i]:
            d -= seg[i]; i += 1
        f = d / seg[i] if seg[i] else 0
        out.append((poly[i][0] + f * (poly[i + 1][0] - poly[i][0]), poly[i][1] + f * (poly[i + 1][1] - poly[i][1]), 0))
    return out


# block letters on a 4 x 6 grid (strokes as polylines), drawn readable from the SOUTH press box
LETTERS = {
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "O": [[(0, 0), (0, 6), (4, 6), (4, 0), (0, 0)]],
    "P": [[(0, 0), (0, 6), (4, 6), (4, 3), (0, 3)]],
    "U": [[(0, 6), (0, 0), (4, 0), (4, 6)]],
    "N": [[(0, 0), (0, 6), (4, 0), (4, 6)]],
    "I": [[(2, 0), (2, 6)]],
}


def word(text, n=40, height=26.0, gap=1.6):
    """points spelling `text` across the pitch (letters 6 units tall -> `height` m)"""
    s = height / 6.0
    strokes, x = [], 0.0
    for ch in text:
        for st in LETTERS[ch]:
            strokes.append([(x + px, py) for px, py in st])
        x += 4 + gap
    width = x - gap
    lens = [sum(math.dist(st[i], st[i + 1]) for i in range(len(st) - 1)) for st in strokes]
    total = sum(lens); pts = []
    alloc = [max(2, round(n * L / total)) for L in lens]
    while sum(alloc) > n: alloc[alloc.index(max(alloc))] -= 1
    while sum(alloc) < n: alloc[alloc.index(max(alloc))] += 1
    for st, k in zip(strokes, alloc):
        for p in along(st, k) if len(st) > 2 or k > 2 else along(st + [st[-1]], k):
            pts.append(((p[0] - width / 2) * s, (p[1] - 3) * s, 0))
    return pts[:n]


def snake(t, n=40, length=90.0, amp=9.0, waves=1.6):
    """the rattlesnake: a sinuous line slithering east across the pitch; t = phase 0..1"""
    head = -PITCH_HL + (2 * PITCH_HL + length) * t - length / 2
    return [(head - length * k / n, amp * math.sin(2 * math.pi * (waves * k / n - 2 * t)), 0) for k in range(n)]


def shield(n=40):
    """the Union crest outline (a shield) on the pitch"""
    poly = [(-20, 22), (20, 22), (20, 2), (12, -14), (0, -24), (-12, -14), (-20, 2), (-20, 22)]
    return along(poly, n)


def to_sky(pts, z):
    return [(x, y, z) for x, y, _ in pts]


def rng(seed):
    return random.Random(seed)
