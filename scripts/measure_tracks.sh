#!/usr/bin/env bash
# Misst integrierte Loudness (LUFS) und True Peak der Kandidaten.
set -euo pipefail
cd /home/mrjaws/monatsmenue/dist/reels/audio-raw
for f in *.mp3; do
  out=$(ffmpeg -hide_banner -nostats -i "$f" -af loudnorm=I=-14:TP=-1.5:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  i=$(printf '%s' "$out" | grep '"input_i"' | grep -oE '\-?[0-9.]+')
  tp=$(printf '%s' "$out" | grep '"input_tp"' | grep -oE '\-?[0-9.]+')
  lra=$(printf '%s' "$out" | grep '"input_lra"' | grep -oE '\-?[0-9.]+')
  printf '%-18s I=%s LUFS  TP=%s dB  LRA=%s\n' "$f" "$i" "$tp" "$lra"
done
