#!/usr/bin/env python3
"""IG-Post 01: PNG-Renderings -> Instagram-JPEGs (1080x1350, 4:5, sRGB).

Instagram akzeptiert fuer Feed-Bilder JPEG; PNGs bleiben als Master liegen.
"""
from pathlib import Path
from PIL import Image

BASE = Path(__file__).resolve().parent.parent / "dist" / "social" / "ig-post-01"
SRC = BASE / "png"
DST = BASE / "jpg"
DST.mkdir(parents=True, exist_ok=True)

ORDER = ["01-cover", "02-szene", "03-plan", "04-woche", "05-statement", "06-cta"]
TARGET = (1080, 1350)

for name in ORDER:
    src = SRC / f"{name}.png"
    if not src.exists():
        raise SystemExit(f"fehlt: {src}")
    im = Image.open(src).convert("RGB")
    if im.size != TARGET:
        im = im.resize(TARGET, Image.LANCZOS)
    out = DST / f"{name}.jpg"
    im.save(out, "JPEG", quality=92, optimize=True, progressive=True, subsampling=0)
    print(f"{out.name}: {im.size[0]}x{im.size[1]} {out.stat().st_size / 1024:.0f} KB")

print("FERTIG", DST)
