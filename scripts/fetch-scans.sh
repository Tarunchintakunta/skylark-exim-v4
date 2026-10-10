#!/usr/bin/env bash
# Download the photoreal fish/shrimp scans listed in docs/ASSETS.md into assets-src/scans/ (git-ignored). No login needed.
# Then clean each with Blender: $BLENDER -b --python blender/clean_scan.py -- assets-src/scans/<f>.glb assets-src/models/<name>.glb [--ratio 0.3]
set -euo pipefail
cd "$(dirname "$0")/.."; mkdir -p assets-src/scans
B=https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs
get(){ [ -s "assets-src/scans/$1.glb" ] || curl -fL --retry 3 -o "assets-src/scans/$1.glb" "$B/$2"; echo "$1  $(( $(stat -f%z "assets-src/scans/$1.glb" 2>/dev/null || stat -c%s "assets-src/scans/$1.glb")/1024 )) KB"; }
get yellowfin-tuna   000-129/d4eeea976932414d91fc786ce6cec547.glb   # CC0, ffish.asia
get green-tiger-prawn 000-044/af273265e0324bc4a645ebad96c254df.glb  # CC0, ffish.asia
get tiger-prawn-aniljaco 000-146/9ea34d3bfbf24b13aa8a37115b1e6551.glb  # CC-BY 4.0, credit "aniljaco" in docs/LICENSES.md if used
get skipjack          000-157/9431157b2fce4ea9a72d9cfe3ce37a6d.glb  # CC0, ffish.asia
get greasyback-shrimp 000-050/8680087cf63643f48b6de895ca288df6.glb  # CC0, ffish.asia (crate filler only, never labelled as a product)
echo "Verify each licence on its Objaverse/Sketchfab page metadata before use; record it in docs/LICENSES.md."
