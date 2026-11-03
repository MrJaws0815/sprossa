#!/usr/bin/env python3
"""
Sprossa – Footage-Generator.

Baut aus einer Liste von PNGs (Pins oder Reel-Keyframes) ein echtes Video:
jedes Bild bekommt eine langsame Kamerafahrt (Ken Burns), die Bilder werden
überblendet. Ergebnis: 1080×1920, H.264, MP4 – fertig für Instagram Reels
oder Pinterest Idea Pins.

Warum kein KI-Video: dieser Rechner hat keine GPU und nur ~3 GB freien RAM.
Ken-Burns-Motion aus den CI-konformen Layouts ist markensicher, lizenzfrei
und sieht bei Text-Overlays besser aus als generiertes Material.

Aufruf:
  python3 scripts/render_footage.py <out.mp4> <bild1.png> <bild2.png> ...
Optional:
  --seconds 3.0     Dauer pro Bild (Default 3.0)
  --fps 25
  --fade 0.6        Überblenddauer (Default 0.6)
  --bg FAF6EF       Hintergrund (Creme, CI-Farbe)

Beispiel:
  python3 scripts/render_footage.py dist/footage/strategische-pins.mp4 \
      dist/pins-strategisch/*.png
"""

import argparse
import os
import subprocess
import sys

W, H = 1080, 1920


def build_filter(n, seconds, fps, fade, bg):
    frames = int(seconds * fps)
    # Jedes Bild: auf 1080×1920 padden (Creme), dann langsame Kamerafahrt.
    # Abwechselnd rein- und rauszoomen, damit es nicht monoton wirkt.
    parts = []
    for i in range(n):
        if i % 2 == 0:
            z = f"min(zoom+0.00035,1.07)"
        else:
            z = f"if(lte(zoom,1.0),1.07,max(1.001,zoom-0.00035))"
        parts.append(
            f"[{i}:v]pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x{bg},"
            f"zoompan=z='{z}':d={frames}:s={W}x{H}:fps={fps},"
            f"format=yuv420p[v{i}]"
        )

    # Überblendkette
    if n == 1:
        return ";".join(parts) + ";[v0]null[out]"

    chain = []
    prev = "v0"
    offset = seconds - fade
    for i in range(1, n):
        out = f"x{i}" if i < n - 1 else "out"
        chain.append(
            f"[{prev}][v{i}]xfade=transition=fade:duration={fade}:offset={offset:.3f}[{out}]"
        )
        prev = out
        offset += seconds - fade
    return ";".join(parts + chain)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--seconds", type=float, default=3.0)
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--fade", type=float, default=0.6)
    ap.add_argument("--bg", default="FAF6EF")
    args = ap.parse_args()

    missing = [p for p in args.images if not os.path.exists(p)]
    if missing:
        sys.exit("Fehlt: " + ", ".join(missing))

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    cmd = ["ffmpeg", "-y"]
    for p in args.images:
        cmd += ["-loop", "1", "-i", p]

    filt = build_filter(len(args.images), args.seconds, args.fps, args.fade, args.bg)
    # Ohne -t läuft ffmpeg mit -loop-1-Inputs endlos weiter (hat 1,1 GB Müll
    # produziert). Gesamtdauer = Bilder × Dauer − Überblendungen.
    total = len(args.images) * args.seconds - (len(args.images) - 1) * args.fade
    cmd += [
        "-filter_complex", filt,
        "-map", "[out]",
        "-t", f"{total:.2f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "medium",
        "-movflags", "+faststart",
        args.output,
    ]

    print(f"Rendere {len(args.images)} Bilder → {args.output}")
    print(f"  {args.seconds}s pro Bild, {args.fps} fps, Überblendung {args.fade}s")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        sys.exit(1)

    size = os.path.getsize(args.output)
    dur = len(args.images) * args.seconds - (len(args.images) - 1) * args.fade
    print(f"Fertig: {args.output} ({size/1024/1024:.1f} MB, ca. {dur:.1f}s)")


if __name__ == "__main__":
    main()
