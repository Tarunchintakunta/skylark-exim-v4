#!/usr/bin/env bash
# LAST-RESORT stop-gap (RENDER_PIPELINE §4): before a scene's first preview exists, build its master from one Blender
# still of the key frame with a slow transform zoom, so the chapter never shows a placeholder. Flag it in the PR.
# Usage: scripts/still-to-master.sh <id> <still.png> [zoom_end=1.08]
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
id=$1 png=$2 z=${3:-1.08}
IFS='|' read -r _ _ F L _ _ <<<"$(scene_row "$id")"; n=$(( L - F + 1 ))
mkdir -p assets-src/video
ffmpeg -v error -y -loop 1 -i "$png" -vf "scale=3840:2160:flags=lanczos,zoompan=z='1+($z-1)*on/$((n-1))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$n:s=1920x1080:fps=24" -frames:v "$n" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p "assets-src/video/$id.mp4"
echo "$id  STILL-GRADE master from $png ($n frames, zoom 1→$z). Replace with preview-to-master.sh when the preview lands."
