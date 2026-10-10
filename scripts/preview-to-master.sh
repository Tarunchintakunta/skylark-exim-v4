#!/usr/bin/env bash
# STOP-GAP ONLY: when a full render is not finished by morning, build the master from the self-approved 960x540 preview frames
# (upscaled with lanczos) so the chapter still shows the real moving scene, never a placeholder. The PR and NIGHT_LOG must say "preview-grade".
# Usage: scripts/preview-to-master.sh <id> [id ...]
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
mkdir -p assets-src/video
for id in "$@"; do
  row=$(scene_row "$id") || { echo "unknown id $id"; exit 1; }
  IFS='|' read -r i b F L d k <<<"$row"; n=$(( L - F + 1 )); src="assets-src/render/preview/$b"
  [ -f "$(printf "%s/%04d.png" "$src" "$L")" ] || { echo "skip $id: preview frames missing in $src"; continue; }
  ffmpeg -v error -y -framerate 24 -start_number "$F" -i "$src/%04d.png" -frames:v "$n" -vf "scale=1920:1080:flags=lanczos" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p "assets-src/video/$id.mp4"
  echo "$id  PREVIEW-GRADE master from $src ($n frames). Replace with frames-to-master.sh when the full render lands."
done
