"""Dialogue voiceover: each speaker gets their own Kokoro voice, each line gets word timings + mouth cues.

script format, one line each:   SPEAKER: text      (parentheticals like "(laughs)" are stripped)
usage: python dialogue_voice.py <script.txt> <out_dir> [--gap 0.18]
writes: voice.mp3, timeline.json {duration, lines[], words[], mouth{SPEAKER: cues[]}}
"""
import argparse, json, re, subprocess, sys, wave
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).parent
KOKORO = ROOT / "tools/kokoro"
RHUBARB = ROOT / "tools/Rhubarb-Lip-Sync-1.13.0-Windows/rhubarb.exe"

# speaker -> (kokoro voice, speed)
VOICES = {
    "NARRATOR": ("am_puck", 1.22),
    "LEO": ("bm_george", 1.18),     # posh rich guy
    "BAKER": ("am_santa", 1.15),    # big jolly baker
    "SAM": ("am_liam", 1.25),       # young friendly neighbour
    "ENGINEER": ("am_liam", 1.2),   # young nervous engineer
    "BOSS": ("am_fenrir", 1.12),    # gruff angry boss
    "WATERMELON": ("am_michael", 1.08),  # big gentle underdog
    "PINEAPPLE": ("af_bella", 1.15),     # sassy queen
}

# broadcast-style voice chain: compression, presence boost, Shorts loudness
VOICE_FX = ("highpass=f=80,acompressor=threshold=-22dB:ratio=3.5:attack=4:release=60:makeup=4,"
            "equalizer=f=3200:t=q:w=1.2:g=3.5,equalizer=f=180:t=q:w=1:g=1.5,loudnorm=I=-14:TP=-1.5:LRA=6")


def trim(a, sr, thresh=0.01):
    idx = np.where(np.abs(a) > thresh)[0]
    if not len(idx):
        return a
    pad = int(sr * 0.03)
    return a[max(idx[0] - pad, 0): idx[-1] + pad]


def squeeze_pauses(a, sr, max_pause=0.09, thresh=0.012):
    """Shorten Kokoro's internal pauses (commas, full stops) so lines flow fast."""
    win = int(sr * 0.01)
    loud = np.array([np.abs(a[i:i + win]).max() > thresh for i in range(0, len(a), win)])
    keep, run = [], 0
    for i, is_loud in enumerate(loud):
        run = 0 if is_loud else run + 1
        if is_loud or run * 0.01 <= max_pause:
            keep.append(a[i * win:(i + 1) * win])
    return np.concatenate(keep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("out")
    ap.add_argument("--gap", type=float, default=0.05)
    ap.add_argument("--tempo", type=float, default=1.0, help="multiplies every voice's speed")
    args = ap.parse_args()
    out = Path(args.out)
    tmp = out / "lines"
    tmp.mkdir(parents=True, exist_ok=True)

    lines = []
    for raw in Path(args.script).read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*([A-Z]+)\s*:\s*(.+)", raw)
        if m and m.group(1) == "PAUSE":  # "PAUSE: 0.8" = extra silence for on-screen action
            if lines:
                lines[-1]["pause_after"] = float(m.group(2))
        elif m:
            text = re.sub(r"\([^)]*\)", "", m.group(2)).strip()
            lines.append({"speaker": m.group(1), "text": text})

    from kokoro_onnx import Kokoro
    from faster_whisper import WhisperModel
    k = Kokoro(str(KOKORO / "kokoro-v1.0.onnx"), str(KOKORO / "voices-v1.0.bin"))
    whisper = WhisperModel("small", device="cpu", compute_type="int8")

    sr, cursor, chunks, words, mouth = 24000, 0.0, [], [], {}
    for i, ln in enumerate(lines):
        voice, speed = VOICES.get(ln["speaker"], VOICES["NARRATOR"])
        speed *= args.tempo
        audio, sr = k.create(ln["text"], voice=voice, speed=speed, lang="en-gb" if voice.startswith("b") else "en-us")
        audio = squeeze_pauses(trim(audio, sr), sr)
        dur = len(audio) / sr
        ln.update(start=round(cursor, 3), end=round(cursor + dur, 3))

        wav16 = tmp / f"{i:02d}.wav"
        sf.write(tmp / f"{i:02d}_24k.wav", audio, sr)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp / f"{i:02d}_24k.wav"), "-ar", "16000", "-ac", "1", str(wav16)], check=True)

        with wave.open(str(wav16)) as w:
            a16 = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        segs, _ = whisper.transcribe(a16, word_timestamps=True, language="en")
        heard = [w for s in segs for w in s.words]
        script_words = ln["text"].split()
        nrm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
        same = len(heard) == len(script_words) and sum(nrm(h.word) == nrm(s) for h, s in zip(heard, script_words)) >= 0.6 * len(script_words)
        if same:  # whisper timings, script spelling
            spans = [(h.start, h.end) for h in heard]
        else:     # whisper misheard / hallucinated: spread words by length over the line
            print(f"   (line {i}: whisper mismatch, using proportional timing)")
            weights = np.array([len(nrm(s)) + 2 for s in script_words], float)
            edges = np.concatenate([[0], np.cumsum(weights)]) / weights.sum() * dur
            spans = list(zip(edges[:-1], edges[1:]))
        for sw, (a, b) in zip(script_words, spans):
            words.append({"text": sw, "start": round(cursor + a, 3), "end": round(cursor + b, 3), "line": i})

        dialog = tmp / f"{i:02d}.txt"
        dialog.write_text(ln["text"], encoding="utf-8")
        cue_file = tmp / f"{i:02d}_mouth.json"
        res = subprocess.run([str(RHUBARB), "-f", "json", "-r", "phonetic", "--extendedShapes", "GHX",
                              "-d", str(dialog), "-o", str(cue_file), str(wav16)], capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"rhubarb failed on line {i}: {res.stderr[-400:]}")
        for c in json.loads(cue_file.read_text(encoding="utf-8"))["mouthCues"]:
            mouth.setdefault(ln["speaker"], []).append(
                {"start": round(cursor + c["start"], 3), "end": round(cursor + c["end"], 3), "value": c["value"]})

        gap = args.gap if i + 1 < len(lines) and lines[i + 1]["speaker"] == ln["speaker"] else args.gap + 0.07
        gap += ln.pop("pause_after", 0)
        chunks += [audio, np.zeros(int(sr * gap), dtype=audio.dtype)]
        cursor += dur + gap
        print(f"{i:2d} {ln['speaker']:8s} {ln['start']:6.2f}-{ln['end']:6.2f}  {ln['text']}")

    full = np.concatenate(chunks[:-1])
    sf.write(out / "voice.wav", full, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "voice.wav"), "-af", VOICE_FX,
                    "-ar", "44100", "-b:a", "192k", str(out / "voice.mp3")], check=True)
    duration = len(full) / sr
    (out / "timeline.json").write_text(json.dumps({"duration": duration, "lines": lines, "words": words, "mouth": mouth}, indent=1))
    print(f"duration {duration:.2f}s, {len(lines)} lines, {len(words)} words")


if __name__ == "__main__":
    main()
