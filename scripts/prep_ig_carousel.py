#!/usr/bin/env python3
"""Konvertiert die gerenderten Carousel-Slides (PNG) in Instagram-taugliche JPEGs.

Instagram akzeptiert nur JPEG (kein PNG/WebP). Zielformat: 1080x1350 (4:5).
Quelle: dist/carousel/out/01-cover.png ... 06-cta.png
Ziel:   dist/carousel/jpg/01.jpg ... 06.jpg
"""
from pathlib import Path
from PIL import Image

SRC = Path(__file__).resolve().parent.parent / "dist" / "carousel" / "out"
DST = Path(__file__).resolve().parent.parent / "dist" / "carousel" / "jpg"
DST.mkdir(parents=True, exist_ok=True)

ORDER = [
    "01-cover.png",
    "02-problem.png",
    "03-wochenplan.png",
    "04-einkaufsliste.png",
    "05-warum.png",
    "06-cta.png",
]

TARGET = (1080, 1350)

for i, name in enumerate(ORDER, start=1):
    src = SRC / name
    if not src.exists():
        raise SystemExit(f"fehlt: {src}")
    im = Image.open(src).convert("RGB")
    if im.size != TARGET:
        # Seitenverhältnis ist bereits 4:5 -> reines Resampling
        im = im.resize(TARGET, Image.LANCZOS)
    out = DST / f"{i:02d}.jpg"
    im.save(out, "JPEG", quality=92, optimize=True, progressive=True)
    print(f"{out.name}: {im.size[0]}x{im.size[1]} {out.stat().st_size/1024:.0f} KB")

print("FERTIG", DST)
