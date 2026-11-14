"""venue.py - Subaru Park geometry in Eos world coordinates.

The stadium mesh ("Landmark - Subaru Park" from a Mini Skyline GLB, glTF y-up, 1 unit = 1 m at
1:1000) is imported into Augment3d with Scale 10.4 (true size: pitch 104 x 64 m), Rotation
(-90, 0, ROT_Z) and Position POS. Measurements were made on the GLB in glTF coordinates
(`*1000` = metres at scale 10); `to_world()` maps them into Eos world coordinates.

Convention (calibrated with marker fixtures, see README): world = POS + Rz(ROT_Z) . (x, -z, y) * k
with k = SCALE/10 applied to glTF*1000 coordinates.
"""
import math

SCALE = 10.4
ROT_Z = 80.0
POS = (69.0, 0.0, 0.0)
K = SCALE / 10.0
MIRROR = 1           # set by calibration: +1 -> (x, -z, y);  -1 -> (x, z, y)
ZSIGN = 1            # set by calibration: sign of the yaw

# pitch opening measured on the mesh (glTF*1000 units, x/z plane)
PITCH_C = (1.20, 0.78)
PITCH_ANG = 81.62           # long axis, degrees from +x toward +z
PITCH_HALF = (49.9, 30.7)   # half length, half width
GROUND = 2.83               # lowest stand geometry at the pitch edge (glTF y*1000)


def to_world(gx, gy, gz):
    """glTF*1000 coordinates (x, y=up, z) -> Eos world metres"""
    lx, ly, lz = gx * K, (-gz if MIRROR > 0 else gz) * K, gy * K
    a = math.radians(ROT_Z * ZSIGN)
    wx = POS[0] + lx * math.cos(a) - ly * math.sin(a)
    wy = POS[1] + lx * math.sin(a) + ly * math.cos(a)
    return (wx, wy, POS[2] + lz)


def pitch_point(u, v, h=None):
    """point on the pitch: u along the long axis (-1..1), v across (-1..1), h height above grass"""
    a = math.radians(PITCH_ANG)
    ex, ez = math.cos(a), math.sin(a)
    gx = PITCH_C[0] + u * PITCH_HALF[0] * ex - v * PITCH_HALF[1] * ez
    gz = PITCH_C[1] + u * PITCH_HALF[0] * ez + v * PITCH_HALF[1] * ex
    return to_world(gx, GROUND + (h or 0) / K, gz)
