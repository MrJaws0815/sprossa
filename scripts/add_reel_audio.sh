#!/usr/bin/env bash
# Bettet eine lizenzfreie Musikspur in die KW46-Reels ein.
# Lautheit auf -14 LUFS (Instagram-Empfehlung), Fade in/out, Video bleibt unberuehrt.
set -euo pipefail

REELS=/home/mrjaws/monatsmenue/dist/reels/kw46
AUDIO=/home/mrjaws/monatsmenue/dist/reels/audio-raw
OUT=/home/mrjaws/monatsmenue/dist/reels/kw46-mit-ton
mkdir -p "$OUT"

# Variante A = ruhig, B = rhythmischer
declare -A TRACK=( [A]="$AUDIO/mixkit-529.mp3" [B]="$AUDIO/mixkit-963.mp3" )
declare -A START=( [A]=6 [B]=4 )   # Einstieg in den Track, Intro ueberspringen

for reel in "$REELS"/*.mp4; do
  base=$(basename "$reel" .mp4)
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$reel")
  for v in A B; do
    out="$OUT/${base}--$v.mp4"
    fade_out=$(python3 -c "print(max(0, float('$dur') - 1.2))")
    ffmpeg -y -v error -i "$reel" -ss "${START[$v]}" -i "${TRACK[$v]}" \
      -filter_complex "[1:a]atrim=0:${dur},asetpts=N/SR/TB,afade=t=in:st=0:d=0.6,afade=t=out:st=${fade_out}:d=1.2,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" \
      -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$out"
    adur=$(ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$out")
    printf '%-40s video=%ss audio=%s\n' "$(basename "$out")" "${dur%.*}" "${adur:-KEIN-AUDIO}"
  done
done
