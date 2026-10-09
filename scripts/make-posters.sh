#!/usr/bin/env bash
# Posters: first frame (pixel-identical handoff poster -> video) and last frame (shown when scrolling back up into a clip).
# assets-src/video/<id>.mp4 -> public/media/<id>_{1920,1280,960}.webp + <id>_end_{1280,960}.webp
# Budgets: 1920 <= 180 KB, 1280 <= 110 KB, 960 <= 70 KB (quality steps down until under).
# Usage: scripts/make-posters.sh [id ...]
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
SRC="${SRC:-assets-src/video}"; OUT="${OUT:-public/media}"; mkdir -p "$OUT"
ids=("$@"); if [ ${#ids[@]} -eq 0 ]; then for f in "$SRC"/*.mp4; do ids+=("$(basename "$f" .mp4)"); done; fi
shot(){ # in out width max_kb seek_args...
  local in=$1 o=$2 w=$3 max=$4; shift 4; local q
  for q in 78 72 66 60 54; do
    ffmpeg -v error -y "$@" -i "$in" -frames:v 1 -update 1 -vf "scale=$w:-2:flags=lanczos" -c:v libwebp -quality $q "$o"
    [ $(( $(fsize "$o")/1024 )) -le "$max" ] && break
  done; }
for id in "${ids[@]}"; do
  in="$SRC/$id.mp4"; [ -f "$in" ] || { echo "skip $id"; continue; }
  shot "$in" "$OUT/${id}_1920.webp" 1920 180
  shot "$in" "$OUT/${id}_1280.webp" 1280 110
  shot "$in" "$OUT/${id}_960.webp" 960 70
  shot "$in" "$OUT/${id}_end_1280.webp" 1280 110 -sseof -0.05
  shot "$in" "$OUT/${id}_end_960.webp" 960 70 -sseof -0.05
  echo "$id posters: $(for f in "$OUT/${id}"_{1920,1280,960,end_1280,end_960}.webp; do printf "%s=%sKB " "$(basename "$f" .webp | sed "s/^${id}_//")" $(( $(fsize "$f")/1024 )); done)"
done
