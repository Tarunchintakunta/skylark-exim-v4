#!/usr/bin/env bash
# Render a single Blender still (markets map, OG image) at 1920x1080 (og: 1200x630) -> public/media/<name>_{1920,960}.webp (og -> public/og/og-image.jpg)
# Usage: scripts/render-still.sh <still id from scripts/scenes.sh STILLS>
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
id="${1:?still id}"; row=""; for r in "${STILLS[@]}"; do [ "${r%%|*}" = "$id" ] && row="$r"; done
[ -n "$row" ] || { echo "unknown still $id"; exit 1; }
IFS='|' read -r _ b fr name <<<"$row"; file="assets-src/blender/$b.blend"; tmp="assets-src/render/stills"; mkdir -p "$tmp" public/media public/og
w=1920; h=1080; [ "$id" = og-image ] && { w=1200; h=630; }
"$BLENDER" --factory-startup -b "$file" --python-expr "import bpy; s=bpy.context.scene; s.render.resolution_x=$w; s.render.resolution_y=$h; s.render.resolution_percentage=100; s.render.image_settings.file_format='PNG'; s.render.filepath='$PWD/$tmp/$name'" -f "$fr"
png=$(ls "$tmp/$name"*.png | head -1)
if [ "$id" = og-image ]; then ffmpeg -v error -y -i "$png" -q:v 3 public/og/og-image.jpg; echo "public/og/og-image.jpg $(( $(fsize public/og/og-image.jpg)/1024 )) KB"
else for tw in 1920 960; do ffmpeg -v error -y -i "$png" -vf "scale=$tw:-2" "$tmp/${name}_$tw.png" && cwebp -quiet -q 74 "$tmp/${name}_$tw.png" -o "public/media/${name}_$tw.webp"; echo "public/media/${name}_$tw.webp $(( $(fsize "public/media/${name}_$tw.webp")/1024 )) KB"; done; fi
