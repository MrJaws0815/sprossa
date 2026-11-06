#!/usr/bin/env python3
"""Laedt Fraunces + Nunito (Latin-Subset) lokal nach dist/social/<target>/fonts/.

Warum: Rendering darf nicht davon abhaengen, ob Google Fonts beim Render-Lauf
erreichbar ist. Erzeugt fonts.css mit relativen url()-Pfaden.
"""
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "dist" / "social" / (sys.argv[1] if len(sys.argv) > 1 else "ig-post-01") / "fonts"
TARGET.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
CSS_URL = ("https://fonts.googleapis.com/css2?"
           "family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&"
           "family=Nunito:wght@400;600;700;800&display=swap")

req = urllib.request.Request(CSS_URL, headers={"User-Agent": UA})
css = urllib.request.urlopen(req, timeout=30).read().decode()

# Bloecke sind durch /* latin */ etc. kommentiert -> nur latin behalten.
blocks = re.findall(r"/\*\s*([a-z0-9-]+)\s*\*/\s*(@font-face\s*\{.*?\})", css, re.S)
keep = []
for subset, block in blocks:
    if subset != "latin":
        continue
    m_url = re.search(r"url\((https://[^)]+\.woff2)\)", block)
    if not m_url:
        continue
    url = m_url.group(1)
    name = url.rsplit("/", 1)[-1]
    local = TARGET / name
    if not local.exists():
        urllib.request.urlretrieve(url, local)
    block = block.replace(url, name)
    keep.append(block)

OUT = TARGET / "fonts.css"
OUT.write_text("\n".join(keep), encoding="utf-8")
print(f"{len(keep)} @font-face (latin) -> {OUT}")
