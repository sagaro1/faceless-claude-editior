"""Generate one video clip with Gemini Omni (API, BILLED per second if billing is on).

usage: python gemini_video.py <clip_id> "<prompt>" --image start.jpg [--image ref2.jpg] [--model gemini-omni-1.2-flash]
writes input/clips/<clip_id>.mp4 ; raw JSON response (minus video bytes) is saved next to it for debugging.
Key: GEMINI_API_KEY in keys/.env
"""
import argparse, base64, json, mimetypes, os, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent


def key():
    for line in (ROOT / "keys/.env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("GEMINI_API_KEY missing in keys/.env")


def post(url, body):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:2000]}")


ap = argparse.ArgumentParser()
ap.add_argument("clip")
ap.add_argument("prompt")
ap.add_argument("--image", action="append", default=[])
ap.add_argument("--model", default="gemini-omni-1.2-flash")
ap.add_argument("--modality", default="VIDEO")
a = ap.parse_args()

parts = []
for img in a.image:
    mime = mimetypes.guess_type(img)[0] or "image/jpeg"
    parts.append({"inlineData": {"mimeType": mime, "data": base64.b64encode(Path(img).read_bytes()).decode()}})
parts.append({"text": a.prompt})
body = {"contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"responseModalities": [a.modality]}}

url = f"https://generativelanguage.googleapis.com/v1beta/models/{a.model}:generateContent?key={key()}"
print("generating", a.clip, "with", a.model, "...", flush=True)
res = post(url, body)

out_dir = ROOT / "input/clips"
out_dir.mkdir(parents=True, exist_ok=True)
saved = None
for cand in res.get("candidates", []):
    for p in cand.get("content", {}).get("parts", []):
        d = p.get("inlineData") or p.get("inline_data")
        if d and d.get("mimeType", "").startswith("video"):
            saved = out_dir / f"{a.clip}.mp4"
            saved.write_bytes(base64.b64decode(d["data"]))
            d["data"] = f"<{len(d['data'])} b64 chars>"
        elif p.get("fileData"):
            print("fileData:", p["fileData"])
        elif "text" in p:
            print("text:", p["text"][:500])
(out_dir / f"{a.clip}_response.json").write_text(json.dumps(res, indent=1)[:20000], encoding="utf-8")
print("usage:", res.get("usageMetadata"))
print("saved:", saved or "NO VIDEO in response")
