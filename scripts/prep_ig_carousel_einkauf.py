#!/usr/bin/env python3
"""Konvertiert die Rendern von Carousel 2 (Einkauf) in Instagram-taugliche JPEGs.

Instagram-Carousel: JPEG, 4:5 bis 1.91:1, Breite 320-1440 px, max 8 MB.
Quelle: dist/carousel/out-einkauf/*.png (1080x1350)
Ziel:   dist/carousel/jpg-einkauf/01.jpg ... 05.jpg
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "dist" / "carousel" / "out-einkauf"
DST = ROOT / "dist" / "carousel" / "jpg-einkauf"
TARGET = (1080, 1350)

DST.mkdir(parents=True, exist_ok=True)

files = sorted(SRC.glob("*.png"))
if not files:
    raise SystemExit(f"keine PNGs in {SRC}")

for i, src in enumerate(files, start=1):
    im = Image.open(src).convert("RGB")
    if im.size != TARGET:
        im = im.resize(TARGET, Image.LANCZOS)
    out = DST / f"{i:02d}.jpg"
    im.save(out, "JPEG", quality=92, optimize=True, progressive=True)
    kb = out.stat().st_size / 1024
    print(f"{out.name}: {im.size[0]}x{im.size[1]} {kb:.0f} KB  (aus {src.name})")
    if kb > 8000:
        raise SystemExit(f"{out.name} ist größer als 8 MB")

print(f"FERTIG: {len(files)} Dateien in {DST}")
