#!/usr/bin/env bash
# Media weight of one full scroll (clips + posters + GLBs + map) per device tier, from public/. JS/CSS/fonts measured separately by the weight test.
# Budgets (TRD §9): desktop (1920 tier) <= 32 MB, laptop (1280) <= 22 MB, mobile (960) <= 14 MB for the whole scroll.
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
sz(){ [ -f "$1" ] && fsize "$1" || echo 0; }
rc=0
for spec in "1920 1280 33554432 desktop" "1280 1280 23068672 laptop" "960 960 14680064 mobile"; do
  set -- $spec; w=$1; pw=$2; cap=$3; name=$4; t=0; miss=""
  for id in "${STORY[@]}"; do
    c=$(sz "public/media/${id}_${w}.mp4"); [ "$c" = 0 ] && miss="$miss $id"
    t=$(( t + c + $(sz "public/media/${id}_${w}.webp") ))
  done
  for m in public/models/*.glb; do t=$(( t + $(sz "$m") )); done
  mw=1920; [ "$w" = 960 ] && mw=960; t=$(( t + $(sz "public/media/markets-map_${mw}.webp") ))
  flag=""; [ $t -gt $cap ] && { flag="  !! over budget"; rc=1; }
  echo "$name ($w): $(awk -v t="$t" 'BEGIN{printf "%.1f", t/1048576}') MB of $(( cap/1048576 )) MB$flag${miss:+  (missing:$miss)}"
done
exit $rc
