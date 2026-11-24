# Faceless Video Editor

A code-based toolkit for vertical (9:16) faceless Shorts: cartoon dialogue stories, narrated shorts, and edits of AI video clips.

You write a short script, the scripts make the voices, timings and backgrounds, and **Remotion** (React) renders an MP4. The MP4 has animated characters, lip-sync, word-by-word captions, camera moves, SFX and music.

```
script.txt ──► dialogue_voice.py ──► timeline.json + voice.mp3 ─┐
storyboard.json ──► images.py / placeholder_bgs.py ──► bg/*.jpg ─┼─► Remotion (Engine.tsx) ──► short.mp4
sfx.py ──► sfx/*.wav ───────────────────────────────────────────┘
```

---

## 1. What to install

**Required:**

| Tool | Version | Why | Get it |
|---|---|---|---|
| **Node.js** | 18+ (tested 22) | Remotion renderer | https://nodejs.org |
| **Python** | 3.10+ (tested 3.13) | voice / image / SFX scripts | https://python.org |
| **FFmpeg + ffprobe** | 6+, on PATH | audio/video processing | Windows: https://www.gyan.dev/ffmpeg/builds/ · mac: `brew install ffmpeg` · Linux: `apt install ffmpeg` |
| **Git** | any | clone / fork | https://git-scm.com |

**Local tools.** They are too big for git, so download them into `tools/`:

| Tool | Needed for | Put it at |
|---|---|---|
| **Kokoro TTS model**: `kokoro-v1.0.onnx` + `voices-v1.0.bin` | free local voices (`dialogue_voice.py`, `story_voice.py`) | `tools/kokoro/` from https://github.com/thewh1teagle/kokoro-onnx/releases |
| **Rhubarb Lip Sync 1.13** | mouth movement for characters | `tools/Rhubarb-Lip-Sync-1.13.0-Windows/` from https://github.com/DanielSWolf/rhubarb-lip-sync/releases (use the macOS/Linux build and adjust the path in the scripts if needed) |
| **Blender 4.2** *(optional)* | `story3d.py` 3D renders | https://www.blender.org/download/ |

Check the required tools:

```bash
node --version
python --version
ffmpeg -version
ffprobe -version
```

## 2. Setup

```bash
git clone https://github.com/<you>/<repo>.git
cd <repo>

# Python
python -m venv .venv
# Windows: .venv\Scripts\activate    |    mac/linux: source .venv/bin/activate
pip install -r requirements.txt

# Remotion
cd video
npm install
npm run studio          # live preview in the browser: open "ExampleShort"
npm run render          # renders ExampleShort -> video/out/example.mp4
```

The example short's voice, backgrounds and SFX are included, so it renders right after `npm install`.

**API keys are optional;** the free tools work without any. To use the paid or cloud tools, copy `.env.example` to `.env.local` and fill in:

| Key | Used by |
|---|---|
| `ELEVENLABS_API_KEY` | ElevenLabs voices / SFX, if you add them |
| `CF_ACCOUNT_ID`, `CF_API_TOKEN` | `images.py`, free Cloudflare AI backgrounds (falls back to Pollinations without keys) |
| `GEMINI_API_KEY`, in `keys/.env` | `gemini_video.py`, Gemini video clips (billed) |

## 3. What's in the repo

```
.
├── dialogue_voice.py   # script -> one Kokoro voice per speaker + word timings + mouth cues -> timeline.json
├── story_voice.py      # single-narrator version (Kokoro + faster-whisper timings + Rhubarb)
├── voice.py            # same idea with free Microsoft Edge TTS
├── images.py           # storyboard backgrounds via AI (Cloudflare / Pollinations)
├── placeholder_bgs.py  # gradient placeholder backgrounds (no AI needed)
├── sfx.py              # synthesizes a licence-free SFX kit (whoosh, pop, slam, bed music...)
├── split_clip.py       # split a multi-shot AI video into shots with smooth slow-mo
├── gemini_video.py     # generate a clip with the Gemini video API
├── story3d.py          # Blender 3D renderer for storyboards
├── examples/example.txt
└── video/                       # Remotion project
    ├── src/Engine.tsx           # storyboard + timeline -> finished short (makeShort)
    ├── src/Character.tsx        # cartoon characters: outfits, expressions, poses, props, lip-sync
    ├── src/Root.tsx             # registers compositions
    ├── src/client/              # your PRIVATE compositions (git-ignored, see §6)
    └── public/example/, sfx/    # example short assets
```

## 4. Make your own short

**1. Write a script** at `examples/myshort.txt`, one line per speaker:
```
NARRATOR: Meet Sam. Sam just built his first video robot.
SAM: It writes, talks and edits all by itself!
BOSS: Then why is it still asleep?
```
Speakers map to Kokoro voices in the `VOICES` table at the top of `dialogue_voice.py`.

**2. Make the voice and timings:**
```bash
python dialogue_voice.py examples/myshort.txt video/public/myshort
```

**3. Write `video/public/myshort/storyboard.json`.** Copy `video/public/example/storyboard.json` and edit it.
- `backgrounds`: a scene id mapped to an image prompt.
- `shots`: each shot has a start time, a background, camera zoom/pan, characters and SFX.
- Time formats:
  - `@12.3`: absolute seconds
  - `1.5`: seconds after the shot starts
  - `w:word`: when that word is spoken
  - `L2` / `L2e`: start or end of line 2, counted from 0
- Characters have an `id` (outfit), a position `x`/`y`/`s`, plus `expr`, `pose`, `prop` and `face` (L or R). The available values are the types at the top of `Character.tsx`.

**4. Make the backgrounds:**
```bash
python images.py video/public/myshort/storyboard.json video/public/myshort/bg       # AI images
# or: python placeholder_bgs.py video/public/myshort/storyboard.json video/public/myshort/bg
```

**5. Register it** in `video/src/Root.tsx`, the same way as `ExampleShort`, then render:
```bash
cd video
npx remotion render src/index.ts MyShort out/myshort.mp4
ffmpeg -i out/myshort.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11" out/myshort_final.mp4   # social-media loudness
```

### Working with AI video clips (Kling / Veo / Gemini)

```bash
# find the cut points in a multi-shot clip
ffmpeg -i clip.mp4 -vf "select='gt(scene,0.2)',showinfo" -f null - 2>&1 | grep pts_time

# split into shots: NAME:START:END:SLOWDOWN:FREEZE_HOLD
python split_clip.py clip.mp4 video/public/myshort/clips A:0:2.1:1.5 B:2.1:4.6:2:0.5
```

## 5. Tips and gotchas

- **Low disk space on C:?** Remotion and FFmpeg write large temp files. Point them at another drive:
  - bash: `export TMP=D:/rtmp TEMP=D:/rtmp TMPDIR=D:/rtmp`
  - PowerShell: `$env:TMP="D:\rtmp"`
- **Emoji / Unicode print errors on Windows:** `set PYTHONIOENCODING=utf-8`.
- **Smooth slow-motion from 24 fps AI clips:** `minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:vsbmc=1`.

## 6. Keeping your own or client work private

- Put private compositions in `video/src/client/` as a file named `*Root.tsx` that exports `ClientCompositions`. `Root.tsx` loads it automatically if it exists, and a fork builds fine without it. This folder is git-ignored.
- To ignore private scripts or media without writing their names in the public `.gitignore`, list them in `.git/info/exclude`, which never leaves your machine.
- Run `git status` before every push.

## 7. Security

Never commit `.env`, `.env.local` or `keys/`; they are git-ignored. If a key leaks, rotate it immediately.
