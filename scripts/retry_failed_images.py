#!/usr/bin/env python3
"""Zweiter Durchgang für die Rezepte ohne brauchbares Bild.

Aenderungen gegenueber dem ersten Lauf:
- schlanker Prompt (kein Zutaten-Overload, der das Modell verwirrt)
- viermal so viele Varianten (4 statt 2) mit neuen Seeds
- Bewertung direkt im Anschluss

    python3 scripts/retry_failed_images.py
"""
import base64
import io
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

OUT = Path("/home/mrjaws/monatsmenue/tmp/comfy_batch")
SCORES = OUT / "scores.json"
RESULTS = OUT / "results.json"
COMFY = "http://127.0.0.1:8188"
CKPT = "RealVisXL_V5.0_fp16.safetensors"

NEG = ("text, watermark, logo, signature, people, hands, blurry, plastic, cartoon, "
       "illustration, painting, ugly, deformed, low quality, dark, collage")

KEY = [l.split("=", 1)[1].strip().strip('"').strip("'")
       for l in Path("/home/mrjaws/.hermes/profiles/sprossa-pm/.env").read_text().splitlines()
       if l.startswith("OPENROUTER_API_KEY=")][0]


def prompt_for(title: str) -> str:
    clean = title.split("–")[0].split("(")[0].strip(" ,-")
    return (f"{clean}, the dish itself on a ceramic plate, traditional home cooking, "
            "professional food photography, natural window light, shallow depth of field, "
            "rustic wooden table, appetizing, high detail")


def submit(prompt: str, seed: int, prefix: str) -> str:
    wf = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 768, "batch_size": 1}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["1", 1]}},
        "5": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 30, "cfg": 5.0,
                                                   "sampler_name": "dpmpp_2m", "scheduler": "karras",
                                                   "denoise": 1.0, "model": ["1", 0], "positive": ["3", 0],
                                                   "negative": ["4", 0], "latent_image": ["2", 0]}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": prefix}},
    }
    body = json.dumps({"prompt": wf, "client_id": str(uuid.uuid4())}).encode()
    req = urllib.request.Request(f"{COMFY}/prompt", data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=90))["prompt_id"]


def fetch(pid: str, dest: Path) -> bool:
    for _ in range(120):
        time.sleep(3)
        try:
            h = json.load(urllib.request.urlopen(f"{COMFY}/history/{pid}", timeout=20))
        except Exception:
            continue
        if not h:
            continue
        if h[pid]["status"].get("status_str") != "success":
            return False
        for o in h[pid].get("outputs", {}).values():
            for img in o.get("images", []):
                q = urllib.parse.urlencode({"filename": img["filename"],
                                            "subfolder": img.get("subfolder", ""), "type": "output"})
                dest.write_bytes(urllib.request.urlopen(f"{COMFY}/view?{q}", timeout=60).read())
                return True
        return False
    return False


def score(title: str, files: list[Path]) -> dict:
    cw, ch, pad = 430, 322, 6
    sheet = Image.new("RGB", (len(files) * (cw + pad) + pad, ch + 2 * pad), "#111")
    for i, f in enumerate(files):
        sheet.paste(Image.open(f).convert("RGB").resize((cw, ch), Image.LANCZOS),
                    (pad + i * (cw + pad), pad))
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=86)
    b64 = base64.b64encode(buf.getvalue()).decode()
    p = (f"Vier Food-Fotos, nummeriert. Gericht: {title}\n\n"
         "Note 1-6 je Bild (1=sehr gut, 6=unbrauchbar) fuer eine Familien-App. "
         "Kriterien: appetitlich, passendes Gericht, keine Stoerfaktoren.\n"
         "Antworte knapp:\n1: Note X\n2: Note X\n3: Note X\n4: Note X\nBESTE: <Nr>")
    body = {"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": [
        {"type": "text", "text": p},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}],
        "max_tokens": 300}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t = json.load(urllib.request.urlopen(req, timeout=180))["choices"][0]["message"]["content"]
    m = re.search(r"BESTE:\s*(\d+)", t)
    best = max(1, min(int(m.group(1)) if m else 1, len(files)))
    nm = re.search(rf"(?m)^\s*{best}\s*:\s*Note\s*([1-6])", t)
    return {"note": int(nm.group(1)) if nm else 3, "best": str(files[best - 1]), "raw": t[:200]}


def main() -> int:
    scores = json.loads(SCORES.read_text())
    results = json.loads(RESULTS.read_text())
    todo = [k for k, v in scores.items() if not v.get("note") or v["note"] > 3]
    print(f"{len(todo)} Rezepte im zweiten Durchgang", flush=True)

    for n, rid in enumerate(todo, 1):
        title = results[rid]["title"]
        prompt = prompt_for(title)
        files = []
        try:
            for v in range(1, 5):
                dest = OUT / f"{rid}_r{v}.png"
                if dest.exists():
                    files.append(dest)
                    continue
                pid = submit(prompt, 9000 + v * 271 + n, f"retry_{rid[:8]}_{v}")
                if fetch(pid, dest):
                    files.append(dest)
            if not files:
                print(f"[{n}/{len(todo)}] {title[:40]} keine Bilder", flush=True)
                continue
            sc = score(title, files)
            scores[rid] = sc
            results[rid]["files"] = [str(f) for f in files]
            print(f"[{n}/{len(todo)}] {title[:40]:42s} Note {sc['note']}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[{n}/{len(todo)}] {title[:40]} ERROR {type(e).__name__}: {str(e)[:80]}", flush=True)

    SCORES.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
    RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    notes = [v["note"] for v in scores.values() if v.get("note")]
    print("\nNoten gesamt:", dict(sorted(Counter(notes).items())))
    print("brauchbar (<=3):", sum(1 for x in notes if x <= 3), "von", len(scores))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
