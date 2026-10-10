#!/usr/bin/env bash
# PNG frames -> 1080p master assets-src/video/<id>.mp4 (crf 14, every frame of the range from scripts/scenes.sh).
# Then: scripts/encode-clips.sh <id> && scripts/make-posters.sh <id> && scripts/check-clip.sh <id>
# Usage: scripts/frames-to-master.sh [id ...]   (no ids = every clip whose frames all exist)
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
mkdir -p assets-src/video
ids=("$@"); if [ ${#ids[@]} -eq 0 ]; then for r in "${SCENES[@]}"; do ids+=("${r%%|*}"); done; fi
for id in "${ids[@]}"; do
  row=$(scene_row "$id") || { echo "unknown id $id"; exit 1; }
  IFS='|' read -r i b F L d k <<<"$row"; n=$(( L - F + 1 )); src="assets-src/render/$d"
  missing=0; for ((x=F; x<=L; x++)); do [ -f "$(printf "%s/%04d.png" "$src" "$x")" ] || missing=$((missing+1)); done
  if [ $missing -gt 0 ]; then echo "skip $id: $missing of $n frames missing in $src (scripts/render-scene.sh $b full)"; continue; fi
  ffmpeg -v error -y -framerate 24 -start_number "$F" -i "$src/%04d.png" -frames:v "$n" -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p "assets-src/video/$id.mp4"
  got=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "assets-src/video/$id.mp4")
  [ "$got" = "$n" ] && echo "$id  frames $F-$L ($n) -> assets-src/video/$id.mp4" || { echo "$id  !! frame count $got != $n"; exit 1; }
done
