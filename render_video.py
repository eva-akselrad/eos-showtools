"""render_video.py - render a timecoded show to an MP4 (picture + the song) by playing it for real.

    python render_video.py examples/union --list 7 --wav "C:\\...\\Union Mashup v2.wav" [--out out\\union.mp4]
                           [--start 0] [--dur 133] [--fps 30] [--width 1280] [--pre 1.0] [--crf 20]

How it stays in sync
  1. Every captured frame of the Augment3d area (config.VIEW_BBOX) is stamped with time.perf_counter().
  2. Reaper is started through reaper/play_sync.lua, which logs (time_precise, audible play position).
     Both clocks are the Windows QPC clock, so each frame's exact SONG TIME is known.
  3. Frames are written to ffmpeg on a fixed 30 fps timeline: each output frame shows the newest capture
     at or before that instant (dropped/duplicated as needed) - no drift, no guessing.
  4. The song WAV is muxed from the same song-time origin, so sound and picture line up to < 1 frame
     (minus Augment3d's own render delay, ~0.1 s, which a real rig would not have).

Like runtest.py it needs exactly one Reaper running with the show's project open, Eos in Live on the
Augment3d tab, and the event list's External on. It also prints the cue-fire timing report.
"""
import argparse, json, os, subprocess, sys, time
from PIL import ImageGrab
import config, deskctl
from eosctl import Eos
from runtest import launch

FFMPEG = "ffmpeg"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("showdir"); ap.add_argument("--list", type=int, default=5); ap.add_argument("--wav", required=True)
    ap.add_argument("--out"); ap.add_argument("--start", type=float, default=0.0, help="song time to start the video")
    ap.add_argument("--dur", type=float, help="video length (default: to the end of the song)")
    ap.add_argument("--fps", type=int, default=30); ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--pre", type=float, default=1.0, help="seconds of picture before --start")
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--av-offset", type=float, default=0.07,
                    help="delay the audio by this much to match Augment3d's render lag (measured ~70 ms)")
    a = ap.parse_args()
    name = os.path.basename(os.path.normpath(a.showdir))
    out = a.out or config.out_path(f"{name}_render.mp4")
    song_len = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.wav],
                                    capture_output=True, text=True).stdout or 0)
    end_t = a.start + (a.dur or (song_len - a.start))
    bx = config.VIEW_BBOX
    W = a.width - a.width % 2
    H = int(W * (bx[3] - bx[1]) / (bx[2] - bx[0])) // 2 * 2

    latest = {"img": None}                      # each output frame is grabbed AT its song-time instant

    # ---- start playback (same sync method as runtest.py)
    e = Eos(); e.send("/eos/subscribe", 1); time.sleep(0.4); e.drain()
    sync_file = os.path.join(config.REAPER_DIR, "play_sync.txt")
    if os.path.exists(sync_file):
        os.remove(sync_file)
    if a.start > 0:     # play_sync.lua plays from the edit cursor at 0; for a later start, offset via job file
        print("note: --start > 0 renders from 0 and trims")
    deskctl.focus(config.EOS_WINDOW)
    launch("play_sync.lua")
    time.sleep(0.7); deskctl.focus(config.EOS_WINDOW); deskctl.move(1915, 1075)
    w0 = time.time()
    offset = None
    while offset is None:
        if time.time() - w0 > 18:
            sys.exit("no sync data from Reaper")
        if os.path.exists(sync_file):
            try:
                rows = [tuple(map(float, l.split())) for l in open(sync_file) if l.strip()]
                rows = [r for r in rows if r[1] > 0.05]
                if len(rows) > 5:
                    offs = sorted(p - s for p, s in rows); offset = offs[len(offs) // 2]
            except (OSError, ValueError):
                pass
        time.sleep(0.01)
    deskctl.focus(config.EOS_WINDOW)

    # ---- writer: fixed-rate timeline in SONG time from (start - pre) to end
    raw = out + ".video.mp4"
    ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{bx[2] - bx[0]}x{bx[3] - bx[1]}",
                           "-r", str(a.fps), "-i", "-", "-vf", f"scale={W}:{H}", "-c:v", "libx264", "-preset", "veryfast", "-crf", str(a.crf),
                           "-pix_fmt", "yuv420p", raw], stdin=subprocess.PIPE)
    t_first = a.start - a.pre
    fired = []; k = 0; dup = 0
    while True:
        song_t = t_first + k / a.fps
        if song_t > end_t:
            break
        target_perf = song_t + offset
        while time.perf_counter() < target_perf:
            for t, addr, p in e.drain():
                if addr.startswith(f"/eos/out/event/cue/{a.list}/") and addr.endswith("/fire"):
                    fired.append((t, float(addr.split("/")[-2])))
            time.sleep(0.001)
        if time.perf_counter() - target_perf > 1.0 / a.fps and latest["img"] is not None:
            img = latest["img"]; dup += 1            # running late: repeat the last frame to stay on time
        else:
            img = ImageGrab.grab(bbox=bx).tobytes()  # full size; ffmpeg scales (PIL resize is too slow)
            latest["img"] = img
        ff.stdin.write(img)
        k += 1
    ff.stdin.close(); ff.wait()
    launch("stop.lua")

    # ---- mux the song: picture frame 0 = song time t_first
    delay_ms = max(0, int(round((a.av_offset - t_first) * 1000)))
    afilter = f"adelay={delay_ms}|{delay_ms}" if delay_ms else "anull"
    ss = max(0.0, t_first - a.av_offset)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", raw, "-ss", f"{ss:.3f}", "-i", a.wav,
                    "-filter:a", afilter, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    os.remove(raw)

    # ---- report
    d_wall_perf = time.time() - time.perf_counter()
    cues = {q["n"]: q for q in json.load(open(os.path.join(a.showdir, "cues.json")))}
    seen = {}
    for tw, n in fired:
        seen.setdefault(int(n), tw - d_wall_perf - offset)
    errs = sorted(seen[n] - q["t"] for n, q in cues.items() if n in seen)
    if errs:
        print(f"cues fired {len(seen)} of {len(cues)}; fire error ms min {errs[0]*1000:.0f} median "
              f"{errs[len(errs)//2]*1000:.0f} max {errs[-1]*1000:.0f}")
    print(f"frames {k} @ {a.fps} fps, held-over frames {dup} ({100 * dup / max(k, 1):.1f}%)")
    print(out, f"{os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()




