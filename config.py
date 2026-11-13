"""config.py - every machine-specific setting in one place.

Each value can be overridden with an environment variable, so nothing personal is hard-coded
in the tools. Example (PowerShell):

    $env:SHOWTOOLS_REAPER = "D:\\Apps\\REAPER\\reaper.exe"
    $env:SHOWTOOLS_OUT    = "D:\\scratch\\showtools"

| Setting        | Env var                 | Default                                        |
|----------------|-------------------------|------------------------------------------------|
| EOS_HOST       | SHOWTOOLS_EOS_HOST      | 127.0.0.1                                      |
| EOS_PORT       | SHOWTOOLS_EOS_PORT      | 3032 (Eos OSC TCP, OSC 1.0 length framing)     |
| EOS_WINDOW     | SHOWTOOLS_EOS_WINDOW    | "Eos : 1" (substring of the Eos window title)  |
| REAPER_EXE     | SHOWTOOLS_REAPER        | C:\\Program Files\\REAPER (x64)\\reaper.exe    |
| OUT_DIR        | SHOWTOOLS_OUT           | <repo>/out  (screenshots, contact sheets)      |
| VIEW_BBOX      | SHOWTOOLS_VIEW_BBOX     | 0,34,1858,898 (Augment3d area on screen, px)   |
| LATENCY        | SHOWTOOLS_LATENCY       | 0.125 s (fire timecode events this much early) |
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
REAPER_DIR = os.path.join(ROOT, "reaper")


def _env(name, default):
    return os.environ.get(name, default)


EOS_HOST = _env("SHOWTOOLS_EOS_HOST", "127.0.0.1")
EOS_PORT = int(_env("SHOWTOOLS_EOS_PORT", "3032"))
EOS_WINDOW = _env("SHOWTOOLS_EOS_WINDOW", "Eos : 1")
REAPER_EXE = _env("SHOWTOOLS_REAPER", r"C:\Program Files\REAPER (x64)\reaper.exe")
OUT_DIR = _env("SHOWTOOLS_OUT", os.path.join(ROOT, "out"))
VIEW_BBOX = tuple(int(v) for v in _env("SHOWTOOLS_VIEW_BBOX", "0,34,1858,898").split(","))
LATENCY = float(_env("SHOWTOOLS_LATENCY", "0.125"))

os.makedirs(OUT_DIR, exist_ok=True)


def out_path(name):
    """path for a generated image/report inside OUT_DIR"""
    return os.path.join(OUT_DIR, name)
