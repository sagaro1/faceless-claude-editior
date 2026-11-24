"""Synthesize a small free SFX kit (no downloads, no licences). usage: python sfx.py <out_dir>"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(d, attack=0.003, decay=8.0):
    x = t(d)
    return np.minimum(x / attack, 1) * np.exp(-x * decay)


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def norm(x, peak=0.9):
    return x / (np.abs(x).max() + 1e-9) * peak


def step():
    d = 0.12
    thump = np.sin(2 * np.pi * 90 * t(d)) * env(d, decay=40)
    scuff = lowpass(rng.normal(size=len(t(d))), 12) * env(d, decay=55)
    return norm(thump + scuff * 0.8, 0.6)


def bell():
    d = 1.6
    x = sum(a * np.sin(2 * np.pi * f * t(d)) for f, a in [(1318, 1), (2637, 0.4), (3951, 0.15)])
    second = np.zeros_like(x)
    off = int(0.11 * SR)
    second[off:] = (np.sin(2 * np.pi * 1760 * t(d))[: len(x) - off]) * env(d - 0.11, decay=4)[: len(x) - off]
    return norm(x * env(d, decay=4) + second * 0.8, 0.5)


def creak():
    d = 0.7
    x = t(d)
    f = 180 + 120 * np.sin(2 * np.pi * 2.2 * x) + 60 * x
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    am = 0.6 + 0.4 * np.sin(2 * np.pi * 23 * x)
    return norm(lowpass(saw * am, 6) * np.minimum(x / 0.05, 1) * np.exp(-x * 2.5), 0.45)


def slam():
    d = 0.45
    boom = np.sin(2 * np.pi * 70 * t(d)) * env(d, decay=12)
    slap = rng.normal(size=len(t(d))) * env(d, decay=60)
    return norm(boom + slap * 0.5, 0.95)


def knock():
    d = 0.18
    body = np.sin(2 * np.pi * 160 * t(d)) * env(d, decay=30)
    click = lowpass(rng.normal(size=len(t(d))), 4) * env(d, decay=90)
    return norm(body + click * 0.6, 0.9)


def pop():
    d = 0.18
    x = t(d)
    return norm(np.sin(2 * np.pi * (500 + 900 * x / d) * x) * env(d, decay=22), 0.5)


def whoosh():
    d = 0.5
    x = t(d)
    noise = rng.normal(size=len(x))
    shape = np.sin(np.pi * x / d) ** 2
    k = (4 + 30 * (1 - x / d)).astype(int)
    out = np.array([noise[max(0, i - k[i]): i + 1].mean() for i in range(len(x))])
    return norm(out * shape, 0.45)


def fire():
    d = 3.0
    x = t(d)
    roar = lowpass(rng.normal(size=len(x)), 40) * 0.5
    crackle = np.zeros_like(x)
    for p in rng.integers(0, len(x) - 400, 90):
        crackle[p: p + 400] += rng.normal(size=400) * np.exp(-np.arange(400) / 40) * rng.uniform(0.3, 1)
    fade = np.minimum(x / 0.2, 1) * np.minimum((d - x) / 0.4, 1)
    return norm((roar + crackle) * fade, 0.55)


def sting():
    d = 2.2
    x = t(d)
    boom = np.sin(2 * np.pi * (55 - 15 * x / d) * x) * np.exp(-x * 1.6)
    hit = lowpass(rng.normal(size=len(x)), 20) * np.exp(-x * 6)
    return norm(boom + hit * 0.6, 0.9)


def bed(seconds=60, bpm=120):
    """Upbeat playful storytelling loop: kick, offbeat hats, bass, pizzicato arpeggio (Am-F-C-G)."""
    beat = 60 / bpm
    n = int(SR * seconds)
    mix = np.zeros(n)

    def add(sig, at):
        i = int(at * SR)
        if i < n:
            mix[i:i + len(sig)] += sig[: n - i]

    def pluck(freq, d=0.28, amp=0.25):
        x = t(d)
        tone = np.sin(2 * np.pi * freq * x) + 0.35 * np.sin(2 * np.pi * 2 * freq * x) + 0.12 * np.sin(2 * np.pi * 3 * freq * x)
        return tone * np.exp(-x * 14) * np.minimum(x / 0.004, 1) * amp

    kick_x = t(0.25)
    kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-kick_x * 30)) * kick_x) * np.exp(-kick_x * 14) * 0.9
    hat = lowpass(rng.normal(size=int(SR * 0.05)), 1) * env(0.05, decay=90) * 0.12
    hat = hat - lowpass(hat, 8)  # crude highpass
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 196.0, 261.63), (196.0, 246.94, 293.66)]
    bass = [110.0, 87.31, 65.41, 98.0]
    bars = int(seconds / (beat * 4)) + 1
    for b in range(bars):
        c = b % 4
        for q in range(4):
            at = (b * 4 + q) * beat
            add(kick, at)
            add(hat * 4, at + beat / 2)
            add(pluck(bass[c], 0.4, 0.5), at)
        for e in range(8):  # eighth-note arpeggio, up and back
            note = chords[c][[0, 1, 2, 1, 0, 1, 2, 1][e]] * 2
            add(pluck(note, 0.22, 0.18), (b * 4) * beat + e * beat / 2)
    return norm(mix, 0.8)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in [("step", step), ("bell", bell), ("creak", creak), ("slam", slam), ("knock", knock),
                     ("pop", pop), ("whoosh", whoosh), ("fire", fire), ("sting", sting), ("bed", bed)]:
        sf.write(out / f"{name}.wav", fn().astype(np.float32), SR)
        print(name)
