"""Story voiceover: Kokoro TTS (free, local) -> word timings (faster-whisper) -> mouth cues (Rhubarb).

usage: python story_voice.py <script.txt> <out_dir> [--voice am_puck] [--speed 1.05] [--max-gap 0.2]
writes: voice.mp3, voice.wav, timeline.json {duration, words[], mouth[]}
"""
import argparse, json, subprocess, sys, wave
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).parent
KOKORO = ROOT / "tools/kokoro"
RHUBARB = ROOT / "tools/Rhubarb-Lip-Sync-1.13.0-Windows/rhubarb.exe"


def synth(text, voice, speed, max_gap):
    """Synthesize line by line, joining with short fixed gaps (fast, no dead air)."""
    from kokoro_onnx import Kokoro
    k = Kokoro(str(KOKORO / "kokoro-v1.0.onnx"), str(KOKORO / "voices-v1.0.bin"))
    lang = "en-gb" if voice.startswith("b") else "en-us"
    parts, sr = [], 24000
    for line in [l.strip() for l in text.splitlines() if l.strip()]:
        audio, sr = k.create(line, voice=voice, speed=speed, lang=lang)
        audio = trim_silence(audio, sr)
        parts += [audio, np.zeros(int(sr * max_gap), dtype=audio.dtype)]
    return np.concatenate(parts[:-1]), sr


def trim_silence(a, sr, thresh=0.01):
    idx = np.where(np.abs(a) > thresh)[0]
    if not len(idx):
        return a
    pad = int(sr * 0.03)
    return a[max(idx[0] - pad, 0): idx[-1] + pad]


def word_times(wav16):
    from faster_whisper import WhisperModel
    with wave.open(str(wav16)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(a, word_timestamps=True, language="en")
    return [{"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)} for s in segs for w in s.words]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("out")
    ap.add_argument("--voice", default="am_puck")
    ap.add_argument("--speed", type=float, default=1.05)
    ap.add_argument("--max-gap", type=float, default=0.2)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    text = Path(args.script).read_text(encoding="utf-8").strip()

    audio, sr = synth(text, args.voice, args.speed, args.max_gap)
    wav, wav16, mp3 = out / "voice.wav", out / "voice16k.wav", out / "voice.mp3"
    sf.write(wav, audio, sr)
    run = lambda *a: subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, a)], check=True)
    run("-i", wav, "-b:a", "192k", mp3)
    run("-i", wav, "-ar", "16000", "-ac", "1", wav16)

    words = word_times(wav16)

    dialog = out / "dialog.txt"
    dialog.write_text(text, encoding="utf-8")
    cue_file = out / "mouth.json"
    res = subprocess.run([str(RHUBARB), "-f", "json", "-r", "phonetic", "--extendedShapes", "GHX",
                          "-d", str(dialog), "-o", str(cue_file), str(wav16)], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"rhubarb failed: {res.stderr[-600:]}")
    mouth = json.loads(cue_file.read_text(encoding="utf-8"))["mouthCues"]

    dur = len(audio) / sr
    (out / "timeline.json").write_text(json.dumps({"duration": dur, "words": words, "mouth": mouth}, indent=1))
    wpm = len(words) / dur * 60
    print(f"duration {dur:.2f}s, {len(words)} words ({wpm:.0f} wpm), {len(mouth)} mouth cues")


if __name__ == "__main__":
    main()
