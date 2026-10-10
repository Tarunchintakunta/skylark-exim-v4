#!/usr/bin/env bash
# Web GLBs: assets-src/models/<name>.glb -> public/models/<name>.glb (meshopt + quantization + WebP textures).
# HARD CAP 500 KB per file (QUALITY_GATES G-PROD). The script steps texture size 2048 -> 1024 -> 512 and then simplify ratio 0.5 -> 0.25
# until under the cap, never touching the silhouette more than needed. Prints tris and size.
# Usage: scripts/optimize-glb.sh [name ...]
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/scenes.sh
SRC="${SRC:-assets-src/models}"; OUT="${OUT:-public/models}"; CAP_KB="${CAP_KB:-500}"
GT="npx --yes @gltf-transform/cli@4"
mkdir -p "$OUT"
names=("$@"); if [ ${#names[@]} -eq 0 ]; then for f in "$SRC"/*.glb; do names+=("$(basename "$f" .glb)"); done; fi
rc=0
for n in "${names[@]}"; do
  in="$SRC/$n.glb"; o="$OUT/$n.glb"; [ -f "$in" ] || { echo "skip $n"; continue; }
  done_=0
  for spec in "2048 none" "1024 none" "1024 0.5" "512 0.5" "512 0.25"; do
    set -- $spec; tex=$1; simp=$2
    if [ "$simp" = none ]; then $GT optimize "$in" "$o" --compress meshopt --texture-compress webp --texture-size "$tex" --simplify false >/dev/null
    else $GT optimize "$in" "$o" --compress meshopt --texture-compress webp --texture-size "$tex" --simplify true --simplify-ratio "$simp" --simplify-error 0.001 >/dev/null; fi
    kb=$(( $(fsize "$o")/1024 )); [ "$kb" -le "$CAP_KB" ] && { done_=1; break; }
  done
  ext=$($GT inspect "$o" --format md 2>/dev/null | grep -o 'EXT_meshopt_compression' | head -1 || true)
  echo "$n  $(( $(fsize "$in")/1024 )) KB -> ${kb} KB (tex $tex, simplify $simp) ${ext:-!!no meshopt}"
  [ $done_ = 1 ] || { echo "  !! $n still over ${CAP_KB} KB: decimate in Blender (blender/clean_scan.py --ratio) and re-export"; rc=1; }
done
exit $rc
