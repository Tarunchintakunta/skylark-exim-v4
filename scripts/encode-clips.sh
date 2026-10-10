#!/usr/bin/env bash
# Encode scroll-scrub clips: assets-src/video/<id>.mp4 -> public/media/<id>_1920.mp4, <id>_1280.mp4, <id>_960.mp4, <id>_720.mp4
# Scrub-friendly H.264: GOP 6 (keyint 6, no scene-cut keyframes), NO B-frames, faststart, no audio, yuv420p, 24 fps.
# Hard cap: EVERY tier file <= 2,250 KB. The script starts at a per-tier CRF and raises it (max 34, light denoise from 31) until under the cap.
# Usage: scripts/encode-clips.sh [id ...]   (no ids = every master in assets-src/video)    Env: SRC OUT FORCE=1 CAP_KB=2250 MAXCRF=34 ONLY="1280 960" (re-encode only these tiers)
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
SRC="${SRC:-assets-src/video}"; OUT="${OUT:-public/media}"; CAP_KB="${CAP_KB:-2250}"
command -v ffmpeg >/dev/null || { echo "ffmpeg not found (brew install ffmpeg)"; exit 1; }
mkdir -p "$OUT"
ids=("$@"); if [ ${#ids[@]} -eq 0 ]; then for f in "$SRC"/*.mp4; do ids+=("$(basename "$f" .mp4)"); done; fi
X264="-threads ${THREADS:-0} -c:v libx264 -preset slow -profile:v high -g 6 -keyint_min 6 -sc_threshold 0 -bf 0 -r 24 -pix_fmt yuv420p -movflags +faststart -an"
rc=0
for id in "${ids[@]}"; do
  in="$SRC/$id.mp4"; [ -f "$in" ] || { echo "skip $id: $in missing"; continue; }
  line="$id"
  for spec in "1920 24" "1280 25" "960 26" "720 27"; do
    set -- $spec; w=$1; crf=$2; o="$OUT/${id}_${w}.mp4"
    [ -n "${ONLY:-}" ] && ! echo " $ONLY " | grep -q " $w " && continue
    if [ -f "$o" ] && [ "${FORCE:-0}" != 1 ]; then line="$line  ${w}: $(( $(fsize "$o")/1024 )) KB (kept)"; continue; fi
    while :; do
      dn=""; [ "$crf" -ge 31 ] && dn=",hqdn3d=1.5:1.5:4:4"
      ffmpeg -v error -y -i "$in" -vf "scale=${w}:-2:flags=lanczos$dn" $X264 -crf "$crf" "$o"
      kb=$(( $(fsize "$o")/1024 ))
      [ "$kb" -le "$CAP_KB" ] && break
      [ "$crf" -ge "${MAXCRF:-34}" ] && break
      crf=$((crf+1))
    done
    flag=""; [ "$kb" -gt "$CAP_KB" ] && { flag=" !!OVER CAP"; rc=1; }
    line="$line  ${w}: ${kb} KB crf ${crf}${flag}"
  done
  echo "$line"
done
[ $rc = 0 ] || echo "Over cap at crf 34: simplify noisy detail (water foam, foliage, film grain) or shorten the clip in scripts/scenes.sh. Never ship over 2,250 KB."
exit $rc
