#!/usr/bin/env bash
# Every story join is a SHARED FRAME (one continuous camera flight). Last frame of A must equal first frame of B.
# Usage: scripts/boundary-check.sh   (all joins)   |   scripts/boundary-check.sh A B
# Compares PNG frames (full renders, else previews) at SSIM >= 0.99, else the encoded 1920 tiers at >= 0.97 (encode noise).
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
pairs=(); if [ $# -eq 2 ]; then pairs=("$1>$2"); else pairs=("${SHARED_JOINS[@]}"); fi
fail=0
for p in "${pairs[@]}"; do
  a="${p%%>*}"; b="${p##*>}"
  IFS='|' read -r _ ba _ la da _ <<<"$(scene_row "$a")"; IFS='|' read -r _ bb fb _ db _ <<<"$(scene_row "$b")"
  A=""; for root in "assets-src/render/$da" "assets-src/render/preview/$ba"; do f=$(printf "%s/%04d.png" "$root" "$la"); [ -f "$f" ] && { A=$f; break; }; done
  B=""; for root in "assets-src/render/$db" "assets-src/render/preview/$bb"; do f=$(printf "%s/%04d.png" "$root" "$fb"); [ -f "$f" ] && { B=$f; break; }; done
  min=0.99; src=png
  if [ -z "$A" ] || [ -z "$B" ] || [ "$(dirname "$A" | grep -c preview)" != "$(dirname "$B" | grep -c preview)" ]; then
    if [ -f "public/media/${a}_1920.mp4" ] && [ -f "public/media/${b}_1920.mp4" ]; then
      ffmpeg -v error -y -sseof -0.05 -i "public/media/${a}_1920.mp4" -update 1 -frames:v 1 "$tmp/a.png"
      ffmpeg -v error -y -i "public/media/${b}_1920.mp4" -frames:v 1 "$tmp/b.png"; A="$tmp/a.png"; B="$tmp/b.png"; min=0.97; src=encoded
    else echo "skip  $a > $b (no frames yet)"; continue; fi
  fi
  s=$(ffmpeg -v info -i "$A" -i "$B" -lavfi ssim -f null - 2>&1 | grep -o 'All:[0-9.]*' | cut -d: -f2)
  if awk "BEGIN{exit !($s>=$min)}"; then echo "OK    $a > $b  SSIM $s [$src]"; else echo "FAIL  $a > $b  SSIM $s [$src] needs >= $min (fix B's first frame with blender/boundary_camera.py)"; fail=1; fi
done
exit $fail
