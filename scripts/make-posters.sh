#!/usr/bin/env bash
# Posters: first frame (pixel-identical handoff poster -> video) and last frame (shown when scrolling back up into a clip).
# assets-src/video/<id>.mp4 -> public/media/<id>_{1920,1280,960,720}.webp + <id>_end_{1280,960,720}.webp
# Budgets: 1920 <= 180 KB, 1280 <= 110 KB, 960 <= 70 KB, 720 <= 50 KB (quality steps down until under).
# Usage: scripts/make-posters.sh [id ...]
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
SRC="${SRC:-assets-src/video}"; OUT="${OUT:-public/media}"; mkdir -p "$OUT"
ids=("$@"); if [ ${#ids[@]} -eq 0 ]; then for f in "$SRC"/*.mp4; do ids+=("$(basename "$f" .mp4)"); done; fi
# ffmpeg builds without libwebp (e.g. Homebrew's default) fall back to PNG -> cwebp (brew install webp).
webp(){ local in=$1 o=$2 w=$3 q=$4; shift 4
  if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libwebp; then ffmpeg -v error -y "$@" -i "$in" -frames:v 1 -update 1 -vf "scale=$w:-2:flags=lanczos" -c:v libwebp -quality "$q" "$o"
  else ffmpeg -v error -y "$@" -i "$in" -frames:v 1 -update 1 -vf "scale=$w:-2:flags=lanczos" "$o.png" && cwebp -quiet -q "$q" "$o.png" -o "$o" && rm -f "$o.png"; fi; }
shot(){ # in out width max_kb seek_args...
  local in=$1 o=$2 w=$3 max=$4; shift 4; local q
  for q in 78 72 66 60 54; do
    webp "$in" "$o" "$w" "$q" "$@"
    [ $(( $(fsize "$o")/1024 )) -le "$max" ] && break
  done; }
for id in "${ids[@]}"; do
  in="$SRC/$id.mp4"; [ -f "$in" ] || { echo "skip $id"; continue; }
  shot "$in" "$OUT/${id}_1920.webp" 1920 180
  shot "$in" "$OUT/${id}_1280.webp" 1280 110
  shot "$in" "$OUT/${id}_960.webp" 960 70
  shot "$in" "$OUT/${id}_720.webp" 720 50
  shot "$in" "$OUT/${id}_end_1280.webp" 1280 110 -sseof -0.05
  shot "$in" "$OUT/${id}_end_960.webp" 960 70 -sseof -0.05
  shot "$in" "$OUT/${id}_end_720.webp" 720 50 -sseof -0.05
  echo "$id posters: $(for f in "$OUT/${id}"_{1920,1280,960,720,end_1280,end_960,end_720}.webp; do printf "%s=%sKB " "$(basename "$f" .webp | sed "s/^${id}_//")" $(( $(fsize "$f")/1024 )); done)"
done
