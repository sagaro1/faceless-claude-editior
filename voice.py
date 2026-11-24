"""Generate voiceover + word timings (Edge TTS, free) and mouth cues (Rhubarb).

usage: python voice.py <script.txt> <out_dir> [voice] [rate]
"""
import asyncio, json, subprocess, sys
from pathlib import Path

import edge_tts

RHUBARB = Path(__file__).parent / "tools/Rhubarb-Lip-Sync-1.13.0-Windows/rhubarb.exe"


async def tts(text, voice, rate, pitch, mp3):
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 1e7,
                    "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                })
    return words


def tighten(wav, words, max_gap):
    """Shorten every pause longer than max_gap (fast pacing); rewrite wav in place, shift word times."""
    import wave, array
    with wave.open(str(wav)) as w:
        params, sr = w.getparams(), w.getframerate()
        samples = array.array("h", w.readframes(w.getnframes()))
    pad = max_gap / 2
    keep, cursor, shift, new_words = [], 0.0, 0.0, []
    for i, wd in enumerate(words):
        if i > 0:
            prev_end = words[i - 1]["end"]
            if wd["start"] - prev_end > max_gap:
                cut_from, cut_to = prev_end + pad, wd["start"] - pad
                keep.append((cursor, cut_from))
                cursor = cut_to
                shift += cut_to - cut_from
        new_words.append({**wd, "start": wd["start"] - shift, "end": wd["end"] - shift})
    keep.append((cursor, None))
    outbuf = array.array("h")
    for a, b in keep:
        outbuf.extend(samples[int(a * sr): None if b is None else int(b * sr)])
    with wave.open(str(wav), "wb") as w:
        w.setparams(params)
        w.writeframes(outbuf.tobytes())
    return new_words


def loudness_cues(wav, fps=30):
    """Fallback lip sync: mouth openness from audio loudness per video frame."""
    import wave, array
    with wave.open(str(wav)) as w:
        sr = w.getframerate()
        samples = array.array("h", w.readframes(w.getnframes()))
    hop = sr // fps
    levels = []
    for i in range(0, len(samples), hop):
        seg = samples[i:i + hop]
        levels.append((sum(s * s for s in seg) / max(len(seg), 1)) ** 0.5)
    peak = sorted(levels)[int(len(levels) * 0.95)] or 1
    shapes = []
    for lv in levels:
        r = lv / peak
        shapes.append("X" if r < 0.08 else "B" if r < 0.3 else "C" if r < 0.6 else "D")
    cues, start = [], 0
    for i in range(1, len(shapes) + 1):
        if i == len(shapes) or shapes[i] != shapes[start]:
            cues.append({"start": start / fps, "end": i / fps, "value": shapes[start]})
            start = i
    return cues


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("out")
    ap.add_argument("--voice", default="en-US-ChristopherNeural")  # authoritative news-anchor tone
    ap.add_argument("--rate", default="+18%")
    ap.add_argument("--pitch", default="-4Hz")
    ap.add_argument("--rhubarb", action="store_true")
    ap.add_argument("--max-gap", type=float, default=0.25, help="longest pause kept between words (s)")
    args = ap.parse_args()
    sys.argv = [a for a in sys.argv if a != "--rhubarb"] + (["--rhubarb"] if args.rhubarb else [])
    script, out = Path(args.script), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    text = script.read_text(encoding="utf-8").strip()

    mp3, wav = out / "voice.mp3", out / "voice.wav"
    raw_mp3 = out / "voice_raw.mp3"
    words = asyncio.run(tts(text, args.voice, args.rate, args.pitch, raw_mp3))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw_mp3, "-ar", "24000", "-ac", "1", wav], check=True)
    words = tighten(wav, words, args.max_gap)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "192k", mp3], check=True)

    if "--rhubarb" in sys.argv:
        # Rhubarb: phonetic recognizer + dialog text for accurate mouth shapes
        dialog = out / "dialog.txt"
        dialog.write_text(text, encoding="utf-8")
        cue_file = out / "mouth.json"
        res = subprocess.run([str(RHUBARB), "-f", "json", "-r", "phonetic", "--extendedShapes", "GHX",
                              "-d", str(dialog), "-o", str(cue_file), str(wav)], capture_output=True, text=True)
        if res.returncode != 0 or not cue_file.exists():
            sys.exit(f"rhubarb failed ({res.returncode}): {res.stderr[-800:]}")
        cues = json.loads(cue_file.read_text(encoding="utf-8"))["mouthCues"]
    else:
        cues = loudness_cues(wav)

    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
                               capture_output=True, text=True, check=True).stdout)
    (out / "timeline.json").write_text(json.dumps({"duration": dur, "words": words, "mouth": cues}, indent=1))
    print(f"duration {dur:.2f}s, {len(words)} words, {len(cues)} mouth cues")


if __name__ == "__main__":
    main()
