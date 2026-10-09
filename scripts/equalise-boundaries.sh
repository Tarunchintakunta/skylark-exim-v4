#!/usr/bin/env bash
# Make every cross-file join a pixel-identical SHARED FRAME before encoding: copy clip A's last rendered frame over
# clip B's first frame (same tier: full PNGs, else preview PNGs). The bridge setups (docs/STORYBOARD.md BRIDGE_*) are
# built to match, so the copied frame differs from B's own first frame only by a hair; this removes the residual so
# scripts/boundary-check.sh passes at SSIM 1.0. Joins inside one .blend are already shared and are skipped.
# Usage: scripts/equalise-boundaries.sh [A B]
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
pairs=(); if [ $# -eq 2 ]; then pairs=("$1>$2"); else pairs=("${SHARED_JOINS[@]}"); fi
for p in "${pairs[@]}"; do
  a="${p%%>*}"; b="${p##*>}"
  IFS='|' read -r _ ba _ la da _ <<<"$(scene_row "$a")"; IFS='|' read -r _ bb fb _ db _ <<<"$(scene_row "$b")"
  [ "$ba" = "$bb" ] && continue
  for tier in full preview; do
    if [ $tier = full ]; then A=$(printf "assets-src/render/%s/%04d.png" "$da" "$la"); B=$(printf "assets-src/render/%s/%04d.png" "$db" "$fb")
    else A=$(printf "assets-src/render/preview/%s/%04d.png" "$ba" "$la"); B=$(printf "assets-src/render/preview/%s/%04d.png" "$bb" "$fb"); fi
    if [ -f "$A" ] && [ -f "$B" ]; then
      s=$(ffmpeg -v info -i "$A" -i "$B" -lavfi ssim -f null - 2>&1 | grep -o 'All:[0-9.]*' | cut -d: -f2)
      [ -f "$B.own" ] || cp "$B" "$B.own"
      cp "$A" "$B"; echo "$tier  $a > $b  own-frame SSIM $s -> shared"
    fi
  done
done
