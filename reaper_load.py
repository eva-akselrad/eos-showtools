"""reaper_load.py - drive the RUNNING Reaper instance from Python (safely).

Reaper runs ReaScripts in an existing instance with `reaper.exe -nonewinst script.lua`. This
wrapper writes the job file the Lua scripts read (reaper/reaper_job.txt), launches the script,
and guards against the two failure modes met while building the example shows:

  1. the wrong project being open  -> `load` refuses unless the open project's window title
     contains --expect (or you pass --force). Loading writes markers + audio into whatever
     project is open and SAVES it.
  2. -nonewinst starting a second Reaper -> detected via the process list; the extra instance
     is closed and the command fails, so you can retry.

Commands
  python reaper_load.py status
  python reaper_load.py open  "C:\\path\\to\\project.rpp"
  python reaper_load.py load  --wav song.wav --markers examples/x/markers.txt \
                              --track "Show Audio - Song" --take "Song - Artist" --expect "aidemo"
  python reaper_load.py extend-timecode [--seconds 240]
  python reaper_load.py play | stop
"""
import argparse, os, subprocess, sys, time
import config

LUA = lambda name: os.path.join(config.REAPER_DIR, name)
JOB = os.path.join(config.REAPER_DIR, "reaper_job.txt")


def reaper_windows():
    """[(pid, title)] of running reaper.exe processes (main window titles)"""
    ps = ("Get-Process reaper -ErrorAction SilentlyContinue | "
          "ForEach-Object { \"$($_.Id)`t$($_.MainWindowTitle)\" }")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        if "\t" in line:
            pid, title = line.split("\t", 1)
            rows.append((int(pid), title))
    return rows


def run_script(name, wait=2.0):
    before = {p for p, _ in reaper_windows()}
    if len(before) != 1:
        sys.exit(f"need exactly one running Reaper, found {len(before)}: {reaper_windows()}")
    subprocess.Popen([config.REAPER_EXE, "-nonewinst", LUA(name)])
    time.sleep(0.6)
    extra = {p for p, _ in reaper_windows()} - before
    if extra:
        for p in extra:
            subprocess.run(["taskkill", "/PID", str(p), "/F"], capture_output=True)
        sys.exit(f"Reaper started a second instance {sorted(extra)} instead of using the running one "
                 f"(closed it). Retry.")
    time.sleep(wait)


def write_job(**kv):
    with open(JOB, "w") as f:
        for k, v in kv.items():
            f.write(f"{k}={v}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    o = sub.add_parser("open"); o.add_argument("rpp")
    l = sub.add_parser("load")
    l.add_argument("--wav", required=True); l.add_argument("--markers", required=True)
    l.add_argument("--track", default="Show Audio"); l.add_argument("--take", default="")
    l.add_argument("--expect", help="substring the open project's title must contain")
    l.add_argument("--force", action="store_true")
    e = sub.add_parser("extend-timecode"); e.add_argument("--seconds", type=float, default=240)
    sub.add_parser("play"); sub.add_parser("stop")
    a = ap.parse_args()

    if a.cmd == "status":
        for pid, title in reaper_windows():
            print(pid, title)
        return
    if a.cmd == "open":
        write_job(rpp=os.path.abspath(a.rpp))
        run_script("open_project.lua", 3)
    elif a.cmd == "load":
        titles = [t for _, t in reaper_windows()]
        if not a.force and (not a.expect or not any(a.expect in t for t in titles)):
            sys.exit(f"open project is {titles}; pass --expect <part of its name> (or --force) to "
                     f"confirm it is the project you want to write into")
        log = os.path.join(config.OUT_DIR, "reaper_log.txt")
        write_job(wav=os.path.abspath(a.wav), track=a.track, take=a.take or os.path.basename(a.wav),
                  markers=os.path.abspath(a.markers), log=log)
        run_script("reaper_song.lua", 4)
        print(open(log).read() if os.path.exists(log) else "no log written")
    elif a.cmd == "extend-timecode":
        log = os.path.join(config.OUT_DIR, "reaper_log.txt")
        write_job(seconds=a.seconds, log=log)
        run_script("extend_timecode.lua", 3)
        print(open(log).read() if os.path.exists(log) else "no log written")
    elif a.cmd == "play":
        run_script("play.lua", 0.5)
    elif a.cmd == "stop":
        run_script("stop.lua", 0.5)
    for pid, title in reaper_windows():
        print("reaper:", pid, title)


if __name__ == "__main__":
    main()
