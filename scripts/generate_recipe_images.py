#!/usr/bin/env python3
"""Vollausbau: Rezeptbilder mit ComfyUI (RealVisXL) generieren.

Pro Rezept zwei Varianten; das Vision-Modell waehlt spaeter die bessere.
Fortschritt in tmp/comfy_batch/results.json — ein Abbruch ist unschaedlich.

    python3 scripts/generate_recipe_images.py --limit 5
    python3 scripts/generate_recipe_images.py
"""
import argparse
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

COMFY = "http://127.0.0.1:8188"
CKPT = "RealVisXL_V5.0_fp16.safetensors"
OUT = Path("/home/mrjaws/monatsmenue/tmp/comfy_batch")
RESULTS = OUT / "results.json"
DB = "sprossa-test-db"

NEG = ("text, watermark, logo, signature, people, hands, blurry, plastic, cartoon, "
       "illustration, painting, ugly, deformed, low quality, dark")

STYLE = ("professional food photography, natural window light, shallow depth of field, "
         "ceramic plate, rustic wooden table, appetizing, high detail")


def load_recipes() -> list[dict]:
    sql = ("SELECT r.id, r.title, "
           "COALESCE(string_agg(i.name, ', ' ORDER BY i.name), '') "
           "FROM recipes r LEFT JOIN recipe_ingredients ri ON ri.recipe_id = r.id "
           "LEFT JOIN ingredients i ON i.id = ri.ingredient_id "
           "GROUP BY r.id, r.title ORDER BY r.title;")
    res = subprocess.run(
        ["docker", "exec", DB, "psql", "-U", "sprossa", "-d", "sprossa_test", "-t", "-A", "-F", "|", "-c", sql],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        raise SystemExit(res.stderr[:300])
    out = []
    for line in res.stdout.strip().splitlines():
        if line.count("|") >= 2:
            rid, title, ing = line.split("|", 2)
            out.append({"id": rid.strip(), "title": title.strip(),
                        "ingredients": [x.strip() for x in ing.split(",") if x.strip()]})
    return out


def prompt_for(rec: dict) -> str:
    title = rec["title"].split("–")[0].split("(")[0].strip(" ,-")
    # Drei markante Zutaten, laengste zuerst (meist die Hauptzutat)
    ings = sorted(rec["ingredients"], key=len, reverse=True)[:3]
    return f"{title}, with {', '.join(ings)}, {STYLE}" if ings else f"{title}, {STYLE}"


def submit(prompt: str, seed: int, prefix: str) -> str:
    wf = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 768, "batch_size": 1}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["1", 1]}},
        "5": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 28, "cfg": 5.5,
                                                   "sampler_name": "dpmpp_2m", "scheduler": "karras",
                                                   "denoise": 1.0, "model": ["1", 0], "positive": ["3", 0],
                                                   "negative": ["4", 0], "latent_image": ["2", 0]}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": prefix}},
    }
    body = json.dumps({"prompt": wf, "client_id": str(uuid.uuid4())}).encode()
    req = urllib.request.Request(f"{COMFY}/prompt", data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=90))["prompt_id"]


def wait_and_fetch(pid: str, dest: Path) -> bool:
    for _ in range(120):
        time.sleep(3)
        try:
            h = json.load(urllib.request.urlopen(f"{COMFY}/history/{pid}", timeout=20))
        except Exception:
            continue
        if not h:
            continue
        st = h[pid]["status"]
        if st.get("status_str") != "success":
            return False
        for o in h[pid].get("outputs", {}).values():
            for img in o.get("images", []):
                q = urllib.parse.urlencode({"filename": img["filename"],
                                            "subfolder": img.get("subfolder", ""), "type": "output"})
                data = urllib.request.urlopen(f"{COMFY}/view?{q}", timeout=60).read()
                dest.write_bytes(data)
                return True
        return False
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--varianten", type=int, default=2)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    recipes = load_recipes()
    if args.limit:
        recipes = recipes[: args.limit]

    done = sum(1 for v in results.values() if v.get("status") == "ok")
    print(f"{len(recipes)} Rezepte · bereits fertig: {done}", flush=True)

    for n, rec in enumerate(recipes, 1):
        rid = rec["id"]
        if results.get(rid, {}).get("status") == "ok":
            continue
        prompt = prompt_for(rec)
        files = []
        try:
            for v in range(1, args.varianten + 1):
                dest = OUT / f"{rid}_{v}.png"
                if dest.exists():
                    files.append(str(dest))
                    continue
                pid = submit(prompt, 4000 + v * 137 + n, f"rec_{rid[:8]}_{v}")
                if wait_and_fetch(pid, dest):
                    files.append(str(dest))
            if files:
                results[rid] = {"title": rec["title"], "status": "ok",
                                "prompt": prompt, "files": files}
                print(f"[{n}/{len(recipes)}] {rec['title'][:42]:44s} {len(files)} Bilder", flush=True)
            else:
                results[rid] = {"title": rec["title"], "status": "failed", "prompt": prompt}
                print(f"[{n}/{len(recipes)}] {rec['title'][:42]:44s} FEHLER", flush=True)
        except Exception as e:  # noqa: BLE001
            results[rid] = {"title": rec["title"], "status": "error", "detail": str(e)[:200]}
            print(f"[{n}/{len(recipes)}] {rec['title'][:42]:44s} ERROR {type(e).__name__}", flush=True)
        RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for v in results.values() if v.get("status") == "ok")
    print(f"\nFertig: {ok} von {len(results)} Rezepten mit Bildern")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
