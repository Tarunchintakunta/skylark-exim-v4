#!/usr/bin/env bash
# Contact sheet for self-review: N evenly spaced frames (default 12) in a 4-wide grid, each tile 480 px, frame number burned in.
# Usage: scripts/contact-sheet.sh <video> <out.jpg> [N]
# Also: scripts/contact-sheet.sh --still <video> <frame_seconds> <out.png>   (one full-res still for zoomed inspection)
set -euo pipefail
if [ "${1:-}" = --still ]; then ffmpeg -v error -y -ss "$3" -i "$2" -frames:v 1 "$4"; echo "$4"; exit 0; fi
in="${1:?video}"; out="${2:?out.jpg}"; n="${3:-12}"
total=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$in")
step=$(( total / n )); [ $step -lt 1 ] && step=1
rows=$(( (n + 3) / 4 ))
ffmpeg -v error -y -i "$in" -vf "select='not(mod(n\,$step))',scale=480:-2,drawtext=text='f%{eif\:n*$step+1\:d}':x=8:y=8:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.5,tile=4x$rows" -frames:v 1 -q:v 3 "$out" 2>/dev/null \
 || ffmpeg -v error -y -i "$in" -vf "select='not(mod(n\,$step))',scale=480:-2,tile=4x$rows" -frames:v 1 -q:v 3 "$out"
echo "$out ($n frames of $total, every $step)"
