#!/usr/bin/env bash
# Soften a cross-file join whose bridge frames don't match natively: after equalise-boundaries.sh has made B's first
# frame A's last, blend A's last frame into B's next N-1 frames with falling weight (a 1/6 s dissolve inside B), so
# the shared frame stays pixel-identical and B's own frames take over gradually. Originals are kept as ####.png.own.
# Usage: scripts/soften-join.sh <clip A> <clip B> [N=4]   (full-render PNGs only)
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
IFS='|' read -r _ _ _ la da _ <<<"$(scene_row "$1")"; IFS='|' read -r _ _ fb _ db _ <<<"$(scene_row "$2")"
N="${3:-4}"; A=$(printf "assets-src/render/%s/%04d.png" "$da" "$la")
for ((k=1; k<N; k++)); do
  B=$(printf "assets-src/render/%s/%04d.png" "$db" $((fb+k)))
  [ -f "$B.own" ] || cp "$B" "$B.own"
  w=$(awk -v k=$k -v n=$N 'BEGIN{printf "%.3f", 1-k/n}')
  ffmpeg -v error -y -i "$A" -i "$B.own" -filter_complex "[0][1]blend=all_expr='A*$w+B*(1-$w)'" -frames:v 1 -update 1 "$B.tmp.png" && mv "$B.tmp.png" "$B"
  echo "$2 frame $((fb+k)): $w of $1's last frame"
done
