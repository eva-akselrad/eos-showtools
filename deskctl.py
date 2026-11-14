"""deskctl - small desktop control tool for driving Eos / Reaper.

Usage (python deskctl.py <cmd> ...):
  windows                         list visible top-level windows (hwnd, rect, title)
  shot OUT.png [--win TITLE] [--scale 0.6] [--region x0 y0 x1 y1]
                                  screenshot whole screen, one window, or a region
  focus TITLE                     bring window whose title contains TITLE to front
  winrect TITLE x y w h           move/resize a window
  max TITLE | restore TITLE | min TITLE
  click x y [--right] [--double]  mouse click at screen coords (physical pixels)
  drag x0 y0 x1 y1
  move x y
  scroll x y N                    N>0 up, N<0 down (wheel notches)
  type "text"                     type unicode text into focused window
  key COMBO [COMBO...]            e.g. key enter   key ctrl+s   key alt+tab  key f5
  pos                             print current cursor position
All coordinates are physical screen pixels (process is DPI aware).
"""
import ctypes
import sys
import time
from ctypes import wintypes

import win32con
import win32gui
import win32process
from PIL import ImageGrab

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

user32 = ctypes.windll.user32

# ---------------- SendInput plumbing ----------------
ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class _U(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def _send(*inputs):
    arr = (INPUT * len(inputs))(*inputs)
    user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))


def _mouse(flags, data=0):
    i = INPUT(type=0)
    i.u.mi = MOUSEINPUT(0, 0, data, flags, 0, 0)
    return i


def _kb(vk=0, scan=0, flags=0):
    i = INPUT(type=1)
    i.u.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
    return i


KEYUP, UNICODE, EXTENDED = 0x2, 0x4, 0x1
VK = {
    "enter": 0x0D, "return": 0x0D, "tab": 0x09, "esc": 0x1B, "escape": 0x1B, "space": 0x20,
    "backspace": 0x08, "delete": 0x2E, "del": 0x2E, "insert": 0x2D, "home": 0x24, "end": 0x23,
    "pageup": 0x21, "pagedown": 0x22, "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "ctrl": 0x11, "control": 0x11, "shift": 0x10, "alt": 0x12, "win": 0x5B,
    "plus": 0xBB, "minus": 0xBD, "period": 0xBE, "comma": 0xBC, "slash": 0xBF,
}
for n in range(1, 25):
    VK[f"f{n}"] = 0x6F + n
EXT_KEYS = {0x2E, 0x2D, 0x24, 0x23, 0x21, 0x22, 0x25, 0x26, 0x27, 0x28, 0x5B}


def _vk_for(name):
    name = name.lower()
    if name in VK:
        return VK[name]
    if len(name) == 1:
        r = user32.VkKeyScanW(ord(name))
        if r != -1:
            return r & 0xFF
    raise SystemExit(f"unknown key: {name}")


def key_combo(combo):
    vks = [_vk_for(p) for p in combo.split("+")]
    downs = [_kb(v, 0, EXTENDED if v in EXT_KEYS else 0) for v in vks]
    ups = [_kb(v, 0, KEYUP | (EXTENDED if v in EXT_KEYS else 0)) for v in reversed(vks)]
    _send(*downs)
    time.sleep(0.03)
    _send(*ups)
    time.sleep(0.03)


def hold(combo, seconds):
    """hold a key (or combo) down for `seconds` (smooth camera moves in Augment3d)"""
    vks = [_vk_for(p) for p in combo.split("+")]
    _send(*[_kb(v, 0, EXTENDED if v in EXT_KEYS else 0) for v in vks])
    time.sleep(float(seconds))
    _send(*[_kb(v, 0, KEYUP | (EXTENDED if v in EXT_KEYS else 0)) for v in reversed(vks)])


def type_text(text, delay=0.005):
    for ch in text:
        if ch == "\n":
            key_combo("enter")
            continue
        _send(_kb(0, ord(ch), UNICODE), _kb(0, ord(ch), UNICODE | KEYUP))
        time.sleep(delay)


def move(x, y):
    user32.SetCursorPos(int(x), int(y))


def click(x, y, right=False, double=False):
    move(x, y)
    time.sleep(0.05)
    down, up = (0x8, 0x10) if right else (0x2, 0x4)
    for _ in range(2 if double else 1):
        _send(_mouse(down), _mouse(up))
        time.sleep(0.06)


def drag(x0, y0, x1, y1, steps=20, button="left", mods=""):
    """mouse drag; button left|right|middle; mods like "alt" or "ctrl+shift" held during the drag
    (Augment3d: right = look around, alt+right = orbit, middle / ctrl+right = pan)"""
    btn = {"left": (0x2, 0x4), "right": (0x8, 0x10), "middle": (0x20, 0x40)}[button]
    mk = [_vk_for(m) for m in mods.split("+") if m]
    move(x0, y0)
    time.sleep(0.05)
    if mk:
        _send(*[_kb(v) for v in mk]); time.sleep(0.03)
    _send(_mouse(btn[0]))
    for s in range(1, steps + 1):
        move(x0 + (x1 - x0) * s / steps, y0 + (y1 - y0) * s / steps)
        time.sleep(0.015)
    _send(_mouse(btn[1]))
    if mk:
        time.sleep(0.03); _send(*[_kb(v, 0, KEYUP) for v in reversed(mk)])


def scroll(x, y, n):
    move(x, y)
    _send(_mouse(0x800, ctypes.c_uint32(int(n) * 120).value))


# ---------------- windows ----------------
def list_windows():
    out = []

    def cb(h, _):
        if win32gui.IsWindowVisible(h):
            t = win32gui.GetWindowText(h)
            if t.strip():
                _, pid = win32process.GetWindowThreadProcessId(h)
                out.append((h, win32gui.GetWindowRect(h), pid, t))
        return True

    win32gui.EnumWindows(cb, None)
    return out


def find_window(title):
    t = title.lower()
    for h, r, pid, name in list_windows():
        if t in name.lower():
            return h
    raise SystemExit(f"no window matching: {title}")


def focus(title):
    h = find_window(title)
    if win32gui.GetForegroundWindow() == h:
        return h            # already in front: no Alt tap (Alt+mouse orbits the Augment3d camera)
    move(1915, 1075)        # park the cursor outside any 3D viewport before the Alt tap
    if win32gui.IsIconic(h):
        win32gui.ShowWindow(h, win32con.SW_RESTORE)
    # alt tap lets SetForegroundWindow succeed from a background process
    _send(_kb(0x12), _kb(0x12, 0, KEYUP))
    try:
        win32gui.SetForegroundWindow(h)
    except Exception:
        win32gui.BringWindowToTop(h)
    time.sleep(0.25)
    return h


def shot(out, win=None, scale=1.0, region=None):
    bbox = None
    if win:
        h = focus(win)
        bbox = win32gui.GetWindowRect(h)
    if region:
        bbox = tuple(region)
    img = ImageGrab.grab(bbox=bbox, all_screens=True)
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    img.save(out)
    off = bbox[:2] if bbox else (0, 0)
    print(f"saved {out} size={img.size} origin={off} scale={scale}  "
          f"(screen = origin + image_px/scale)")


def main(a):
    if not a:
        print(__doc__)
        return
    cmd, rest = a[0], a[1:]
    if cmd == "windows":
        for h, r, pid, t in list_windows():
            print(f"{h:>10} {r} pid={pid} {t}")
    elif cmd == "shot":
        out, win, scale, region = rest[0], None, 1.0, None
        i = 1
        while i < len(rest):
            if rest[i] == "--win":
                win = rest[i + 1]; i += 2
            elif rest[i] == "--scale":
                scale = float(rest[i + 1]); i += 2
            elif rest[i] == "--region":
                region = [int(v) for v in rest[i + 1:i + 5]]; i += 5
            else:
                i += 1
        shot(out, win, scale, region)
    elif cmd == "focus":
        focus(rest[0]); print("focused")
    elif cmd == "winrect":
        h = find_window(rest[0])
        win32gui.ShowWindow(h, win32con.SW_RESTORE)
        x, y, w, hh = map(int, rest[1:5])
        win32gui.MoveWindow(h, x, y, w, hh, True)
    elif cmd in ("max", "restore", "min"):
        h = find_window(rest[0])
        win32gui.ShowWindow(h, {"max": win32con.SW_MAXIMIZE, "restore": win32con.SW_RESTORE,
                                "min": win32con.SW_MINIMIZE}[cmd])
    elif cmd == "click":
        click(int(rest[0]), int(rest[1]), "--right" in rest, "--double" in rest)
    elif cmd == "hold":
        hold(rest[0], rest[1])
    elif cmd == "drag":
        btn = rest[rest.index("--button") + 1] if "--button" in rest else "left"
        mods = rest[rest.index("--mods") + 1] if "--mods" in rest else ""
        drag(*map(int, rest[:4]), button=btn, mods=mods)
    elif cmd == "move":
        move(int(rest[0]), int(rest[1]))
    elif cmd == "scroll":
        scroll(int(rest[0]), int(rest[1]), int(rest[2]))
    elif cmd == "type":
        type_text(" ".join(rest))
    elif cmd == "key":
        for c in rest:
            key_combo(c)
    elif cmd == "pos":
        p = wintypes.POINT(); user32.GetCursorPos(ctypes.byref(p)); print(p.x, p.y)
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])


