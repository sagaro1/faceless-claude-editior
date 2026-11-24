"""Split a multi-shot AI clip (Kling / Veo / Gemini) into separate shots and slow each one down smoothly
(motion interpolation), with an optional freeze-frame hold at the end.

usage: python split_clip.py <src.mp4> <out_dir> NAME:START:END[:SLOW[:HOLD]] [NAME:START:END...] [--fps 30]
  e.g. python split_clip.py input/clip.mp4 video/public/myshort/clips A:0:2.1:1.5 B:2.1:4.6:2:0.5
  SLOW = slow-down factor (1 = real speed), HOLD = seconds to freeze the last frame.
Find cut points with:  ffmpeg -i clip.mp4 -vf "select='gt(scene,0.2)',showinfo" -f null - 2>&1 | grep pts_time
"""
import argparse, subprocess
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("segs", nargs="+")
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--trim", type=float, default=1 / 24, help="seconds trimmed off each side so blended cut frames don't leak in")
args = ap.parse_args()

out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
for seg in args.segs:
    parts = seg.split(":")
    name, a, b = parts[0], float(parts[1]) + args.trim, float(parts[2]) - args.trim
    k = float(parts[3]) if len(parts) > 3 else 1.0
    hold = float(parts[4]) if len(parts) > 4 else 0.0
    vf = (f"setpts={k}*(PTS-STARTPTS),"
          f"minterpolate=fps={args.fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
          + (f",tpad=stop_mode=clone:stop_duration={hold}" if hold else ""))
    dst = out / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", args.src,
                    "-vf", vf, "-an", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", str(dst)], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dst)],
                               capture_output=True, text=True).stdout)
    print(f"{name}: {b - a:.2f}s x{k} -> {dur:.2f}s")
