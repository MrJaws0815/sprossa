#!/usr/bin/env python3
"""Rendert die Reel-Frames aus manifest.json zu MP4s (1080x1920, H.264, stumm).

Das Manifest liefert pro Frame Datei, Dauer und Bewegungsrichtung. Daraus wird
eine ffmpeg-Filterkette mit Ken-Burns-Zoom und Überblendungen gebaut.

Aufruf:
  python3 scripts/render_reel_manifest.py <manifest.json> <out_dir> [--fps 25] [--fade 0.5]
"""
import argparse
import json
import os
import subprocess
import sys
from collections import OrderedDict

W, H = 1080, 1920


def build(reel_frames, fps, fade, bg="FAF6EF"):
    parts = []
    durs = []
    for i, fr in enumerate(reel_frames):
        d = float(fr.get("dur", 3.0))
        durs.append(d)
        frames = max(1, int(round(d * fps)))
        if fr.get("motion") == "out":
            z = "if(lte(zoom,1.0),1.06,max(1.001,zoom-0.00055))"
        else:
            z = "min(zoom+0.00055,1.06)"
        parts.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},setsar=1,"
            f"zoompan=z='{z}':d={frames}:s={W}x{H}:fps={fps},"
            f"format=yuv420p[v{i}]"
        )
    n = len(reel_frames)
    if n == 1:
        return ";".join(parts) + ";[v0]null[out]", durs
    chain = []
    prev = "v0"
    offset = durs[0] - fade
    for i in range(1, n):
        out = f"x{i}" if i < n - 1 else "out"
        chain.append(f"[{prev}][v{i}]xfade=transition=fade:duration={fade}:offset={offset:.3f}[{out}]")
        prev = out
        offset += durs[i] - fade
    return ";".join(parts + chain), durs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("out_dir")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--fade", type=float, default=0.5)
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--preset", default="medium")
    args = ap.parse_args()

    frames = json.load(open(args.manifest, encoding="utf-8"))
    groups = OrderedDict()
    for fr in frames:
        groups.setdefault(fr["reel"], []).append(fr)

    os.makedirs(args.out_dir, exist_ok=True)
    for reel, frs in groups.items():
        frs.sort(key=lambda x: x["index"])
        missing = [f["file"] for f in frs if not os.path.exists(f["file"])]
        if missing:
            sys.exit(f"{reel}: fehlende Frames: {missing[:3]}")
        filt, durs = build(frs, args.fps, args.fade)
        total = sum(durs) - (len(durs) - 1) * args.fade
        out = os.path.join(args.out_dir, f"{reel}.mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        for f in frs:
            cmd += ["-loop", "1", "-t", f"{float(f.get('dur', 3.0)):.3f}", "-i", f["file"]]
        cmd += ["-filter_complex", filt, "-map", "[out]", "-t", f"{total:.2f}",
                "-r", str(args.fps), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", str(args.crf), "-preset", args.preset,
                "-movflags", "+faststart", "-an", out]
        print(f"[{reel}] {len(frs)} Frames, {total:.1f}s -> {out}", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-1200:], file=sys.stderr)
            sys.exit(1)
        print(f"[{reel}] OK {os.path.getsize(out)/1024/1024:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
