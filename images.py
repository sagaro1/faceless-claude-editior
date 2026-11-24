"""Generate background images for a storyboard.

usage: python images.py <storyboard.json> <out_dir> [--provider cloudflare|pollinations] [--force]

storyboard.json: {"style": "...", "backgrounds": {"<id>": "<scene prompt>", ...}, "shots": [...]}
Cloudflare (best free option) needs CF_ACCOUNT_ID and CF_API_TOKEN in faceless/.env.
"""
import argparse, base64, json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent


def load_env():
    for env in (ROOT / "keys/.env", ROOT / ".env"):
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    if v.strip():
                        os.environ.setdefault(k.strip(), v.strip().strip('"'))


def cloudflare(prompt, seed):
    acc, tok = os.environ.get("CF_ACCOUNT_ID"), os.environ.get("CF_API_TOKEN")
    if not acc or not tok:
        sys.exit("CF_ACCOUNT_ID / CF_API_TOKEN missing in faceless/.env")
    url = f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    body = json.dumps({"prompt": prompt, "steps": 8}).encode()  # flux-1-schnell on CF rejects "seed"
    req = urllib.request.Request(url, body, {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code}: {e.read().decode(errors='replace')[:400]}") from None
    return base64.b64decode(data["result"]["image"])


def pollinations(prompt, seed):
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
           + f"?width=1024&height=1024&model=flux&nologo=true&seed={seed}")
    with urllib.request.urlopen(url, timeout=180) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("out")
    ap.add_argument("--provider", default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    load_env()
    provider = args.provider or ("cloudflare" if os.environ.get("CF_API_TOKEN") else "pollinations")
    gen = {"cloudflare": cloudflare, "pollinations": pollinations}[provider]

    sb = json.loads(Path(args.storyboard).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for i, (bid, scene) in enumerate(sb["backgrounds"].items()):
        dst = out / f"{bid}.jpg"
        if dst.exists() and not args.force:
            continue
        prompt = f"{scene}. {sb['style']}"
        for attempt in range(3):
            try:
                dst.write_bytes(gen(prompt, 1000 + i))
                print(f"[{provider}] {bid}.jpg")
                break
            except Exception as e:
                print(f"  retry {bid}: {e}")
                time.sleep(5)
        else:
            sys.exit(f"failed to generate {bid}")


if __name__ == "__main__":
    main()
