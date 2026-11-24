"""Make gradient placeholder backgrounds (1024x1024) for any storyboard bg that has no image yet."""
import json, subprocess, sys
from pathlib import Path

PALETTE = ["#f4a259/#5b8e7d", "#e9c46a/#bc6c25", "#90e0ef/#0077b6", "#a7c957/#386641", "#80ed99/#22577a",
           "#457b9d/#1d3557", "#ffb703/#fb8500", "#adb5bd/#495057", "#14213d/#000814", "#3d405b/#1b1b2f"]

sb = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
for i, bid in enumerate(sb["backgrounds"]):
    dst = out / f"{bid}.jpg"
    if dst.exists():
        continue
    c0, c1 = PALETTE[i % len(PALETTE)].split("/")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", f"gradients=s=1024x1024:c0={c0}:c1={c1}:x0=0:y0=0:x1=1024:y1=1024:d=1",
                    "-frames:v", "1", str(dst)], check=True)
    print("placeholder", dst.name)
