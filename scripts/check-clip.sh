#!/usr/bin/env bash
# Gate for encoded clips (QUALITY_GATES.md G-MEDIA): all 3 tiers + 5 posters exist, each mp4 <= 2,250 KB, GOP <= 6 with no B-frames,
# faststart (moov before mdat), no audio, 24 fps, frame count == scenes.sh range, mean luma >= floor (never dark/murky), no black/grey frames.
# Usage: scripts/check-clip.sh [id ...]   (no ids = every story clip)
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
floor(){ case "$1" in ext) echo 95;; int) echo 85;; cold) echo 72;; dawn) echo 70;; *) echo 85;; esac; }
ids=("$@"); [ ${#ids[@]} -eq 0 ] && ids=("${STORY[@]}")
rc=0
for id in "${ids[@]}"; do
  row=$(scene_row "$id") || { echo "unknown $id"; rc=1; continue; }
  IFS='|' read -r _ _ F L _ kind <<<"$row"; n=$(( L - F + 1 )); line="$id"
  for w in 1920 1280 960; do
    f="public/media/${id}_${w}.mp4"; [ -f "$f" ] || { line="$line  !!${w} missing"; rc=1; continue; }
    kb=$(( $(fsize "$f")/1024 )); [ "$kb" -gt 2250 ] && { line="$line  !!${w} ${kb}KB>2250"; rc=1; }
    types=$(ffprobe -v error -select_streams v:0 -show_entries frame=pict_type -of csv=p=0 "$f" | tr -d ',\n ')
    echo "$types" | grep -q B && { line="$line  !!${w} has B-frames"; rc=1; }
    maxgap=$(echo "$types" | awk '{n=split($0,a,""); g=0; m=0; for(i=1;i<=n;i++){ if(a[i]=="I"){ if(g>m)m=g; g=1 } else g++ } if(g>m)m=g; print m}')
    [ "$maxgap" -gt 6 ] && { line="$line  !!${w} GOP $maxgap>6"; rc=1; }
    cnt=${#types}; [ "$cnt" != "$n" ] && { line="$line  !!${w} frames $cnt!=$n"; rc=1; }
    fs=$(ffmpeg -v trace -i "$f" -f null -frames:v 1 - 2>&1 | grep -o "type:'\(moov\|mdat\)'" | head -1 || true); [ "$fs" = "type:'moov'" ] || { line="$line  !!${w} not faststart"; rc=1; }
    [ -n "$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$f")" ] && { line="$line  !!${w} has audio"; rc=1; }
    line="$line  ${w}:${kb}KB"
  done
  for p in 1920 1280 960 end_1280 end_960; do [ -f "public/media/${id}_${p}.webp" ] || { line="$line  !!poster $p missing"; rc=1; }; done
  m="public/media/${id}_960.mp4"
  if [ -f "$m" ]; then
    read -r y ymin < <(ffmpeg -v error -i "$m" -vf "scale=320:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null - | awk -F= '/YAVG/{s+=$2;n++; if(min==""||$2<min)min=$2} END{printf "%.0f %.0f\n", s/n, min}')
    line="$line  luma avg $y min $ymin (floor $(floor "$kind"))"
    [ "$y" -lt "$(floor "$kind")" ] && { line="$line  !!too dark: remove overlays, raise exposure/sun"; rc=1; }
    [ "$ymin" -lt 25 ] && { line="$line  !!a near-black frame exists"; rc=1; }
  fi
  echo "$line"
done
exit $rc
