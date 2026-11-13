"""runtest.py - play a show from Reaper and MEASURE it.

    python runtest.py examples/arena --list 6 --dur 48.5  0.5 9.3 30.05 40.2
                      <show dir>      <cue list>  <stop at>  <song times to screenshot ...>

What it does
  1. Subscribes to Eos OSC and records every `/eos/out/event/cue/<list>/<n>/fire` message.
  2. Starts Reaper through reaper/play_sync.lua. That script waits 7 s (so this harness can put
     Eos/Augment3d back in front: Reaper raises its window when a script is launched and an
     occluded Augment3d pauses rendering), then plays from 0:00 and logs pairs of
     (Reaper high-resolution clock, audible play position) to reaper/play_sync.txt.
     Reaper's time_precise() and Python's perf_counter() both read the Windows QPC clock,
     so wall-clock time maps to *song time* exactly; launch delay never enters the measurement.
  3. Grabs Augment3d frames (config.VIEW_BBOX) at the requested song times.
  4. Reports, per cue: (song time at which Eos reported the fire) - (planned time in cues.json).

Output
  - console: fired count, missing cues, error distribution, worst offenders
  - <show dir>/fired.json   : [(song_time, cue_number), ...]
  - <OUT_DIR>/<show>_run.png: contact sheet of the frames

Safety: refuses to run unless exactly one Reaper is running, and closes a second instance if
`-nonewinst` spawns one (it occasionally does).
"""
import argparse, json, os, subprocess, sys, time
from PIL import ImageGrab, Image, ImageDraw
import config
from eosctl import Eos
import deskctl

TW_H = (464, 216)


def reaper_pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq reaper.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return {int(l.split(",")[1].strip('"')) for l in out.splitlines() if l.strip().startswith('"')}


def launch(script):
    before = reaper_pids()
    if len(before) != 1:
        sys.exit(f"expected exactly one running Reaper, found {sorted(before)}")
    subprocess.Popen([config.REAPER_EXE, "-nonewinst", os.path.join(config.REAPER_DIR, script)])
    time.sleep(0.5)
    extra = reaper_pids() - before
    if extra:
        for p in extra:
            subprocess.run(["taskkill", "/PID", str(p), "/F"], capture_output=True)
        sys.exit(f"Reaper started a second instance {sorted(extra)} (closed it); retry")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("showdir")
    ap.add_argument("shots", nargs="*", type=float, help="song times (s) to screenshot")
    ap.add_argument("--list", type=int, default=5, help="Eos cue list the show lives in")
    ap.add_argument("--dur", type=float, help="stop at this song time (default: last cue + 4 s)")
    a = ap.parse_args()

    cues = {q["n"]: q for q in json.load(open(os.path.join(a.showdir, "cues.json")))}
    dur = a.dur or max(q["t"] for q in cues.values()) + 4
    shots = sorted(a.shots)

    e = Eos()
    e.send("/eos/subscribe", 1)
    time.sleep(0.5); e.drain()
    sync_file = os.path.join(config.REAPER_DIR, "play_sync.txt")
    if os.path.exists(sync_file):
        os.remove(sync_file)
    deskctl.focus(config.EOS_WINDOW)
    launch("play_sync.lua")
    time.sleep(0.7); deskctl.focus(config.EOS_WINDOW)
    w0 = time.time()
    d_wall_perf = time.time() - time.perf_counter()   # eosctl stamps messages with time.time()

    fired, frames, si, offset = [], [], 0, None       # offset = perf_counter - song position
    while True:
        now_perf = time.perf_counter()
        if offset is None and time.time() - w0 > 7.6 and os.path.exists(sync_file):
            try:
                rows = [tuple(map(float, l.split())) for l in open(sync_file) if l.strip()]
                rows = [r for r in rows if r[1] > 0.05]
                if len(rows) > 5:
                    offs = sorted(p - s for p, s in rows)
                    offset = offs[len(offs) // 2]
                    deskctl.focus(config.EOS_WINDOW)
            except (OSError, ValueError):
                pass
        for t, addr, p in e.drain():
            if addr.startswith(f"/eos/out/event/cue/{a.list}/") and addr.endswith("/fire"):
                fired.append((t - d_wall_perf, float(addr.split("/")[-2])))
        if offset is not None:
            st = now_perf - offset
            if si < len(shots) and st >= shots[si]:
                frames.append((shots[si], ImageGrab.grab(bbox=config.VIEW_BBOX).resize(TW_H)))
                si += 1
            if st > dur:
                break
        elif time.time() - w0 > 18:
            break
        time.sleep(0.004)

    launch("stop.lua")
    if offset is None:
        sys.exit("no sync data from Reaper (did playback start? is the project open?)")

    seen = {}
    for tp, n in fired:
        seen.setdefault(int(n), tp - offset)
    errs = sorted((seen[n] - q["t"], n) for n, q in cues.items() if n in seen)
    missing = [n for n in cues if n not in seen and 1.0 < cues[n]["t"] < dur]
    print(f"cues fired {len(seen)} of {len(cues)}; missing (1 s < t < dur): {missing[:40]}")
    if errs:
        v = [x for x, _ in errs]
        print("fire error (song time at fire - planned), ms:  min %.0f  p10 %.0f  median %.0f  p90 %.0f  max %.0f"
              % tuple(1000 * v[int(k * (len(v) - 1))] for k in (0, 0.1, 0.5, 0.9, 1)))
        print("worst:", [(n, round(x * 1000)) for x, n in errs[:3] + errs[-3:]])
    json.dump([(round(tp - offset, 4), n) for tp, n in fired], open(os.path.join(a.showdir, "fired.json"), "w"))

    if frames:
        cols = 4
        sheet = Image.new("RGB", (TW_H[0] * cols, TW_H[1] * ((len(frames) + cols - 1) // cols)))
        for i, (t, im) in enumerate(frames):
            ImageDraw.Draw(im).text((6, 4), f"{t:.2f}s", fill=(255, 255, 0))
            sheet.paste(im, ((i % cols) * TW_H[0], (i // cols) * TW_H[1]))
        out = config.out_path(os.path.basename(os.path.normpath(a.showdir)) + "_run.png")
        sheet.save(out)
        print(out)


if __name__ == "__main__":
    main()
