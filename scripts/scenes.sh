#!/usr/bin/env bash
# Single source of truth for every Blender clip in Skylark Exim v4 (sourced by the other scripts). Must match docs/SCENES.md + docs/STORYBOARD.md.
# Row: clip id | .blend name (assets-src/blender/<blend>.blend) | first frame | last frame | render dir (assets-src/render/<dir>) | light kind
# light kind sets the brightness floor in check-clip.sh: ext (daylight exterior) | int (interior) | cold (cold store, cool and darker) | dawn (dawn sea/pond)
# Clips of one .blend are one continuous camera flight split into chapters; neighbours SHARE their boundary frame (it is in both clips).
SCENES=(
  "v-table|table|1|216|table|int"
  "v-reefer|reefer|1|192|reefer|ext"
  "v-port|port|1|264|port|ext"
  "v-cold|plant-cold|1|192|plant-cold|cold"
  "v-pack|plant-cold|192|383|plant-cold|int"
  "v-freeze|plant-cold|383|574|plant-cold|cold"
  "v-qc|plant-line|1|192|plant-line|int"
  "v-grade|plant-line|192|383|plant-line|int"
  "v-peel|plant-line|383|574|plant-line|int"
  "v-wash|plant-line|574|765|plant-line|int"
  "v-truck|truck|1|216|truck|ext"
  "v-pond|pond|1|216|pond|dawn"
  "v-sea|sea|1|264|sea|dawn"
  # Products fallback only (used as scrub video if a live GLB cannot pass QUALITY_GATES G-PROD): 360-degree turntables
  "prod-tuna|prod-tuna|1|120|prod-tuna|ext"
  "prod-prawn|prod-prawn|1|120|prod-prawn|ext"
  "prod-swordfish|prod-swordfish|1|120|prod-swordfish|ext"
)
# The story order (scroll order). Every neighbour pair is a SHARED-FRAME join: the site swaps clips with no crossfade, so the
# camera reads as one continuous flight (Zoi-style). scripts/boundary-check.sh enforces SSIM >= 0.99 on PNG frames.
STORY=(v-table v-reefer v-port v-cold v-pack v-freeze v-qc v-grade v-peel v-wash v-truck v-pond v-sea)
SHARED_JOINS=()
for ((i=0; i<${#STORY[@]}-1; i++)); do SHARED_JOINS+=("${STORY[$i]}>${STORY[$((i+1))]}"); done
# Single-frame stills rendered in Blender (render-still.sh): id|blend|frame|out name
STILLS=(
  "markets-map|map|1|markets-map"
  "og-image|table|1|og-image"
)
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
scene_row(){ local r; for r in "${SCENES[@]}"; do [ "${r%%|*}" = "$1" ] && { echo "$r"; return 0; }; done; return 1; }
blend_rows(){ local r i b f l d k; for r in "${SCENES[@]}"; do IFS='|' read -r i b f l d k <<<"$r"; if [ "$b" = "$1" ]; then echo "$r"; fi; done; return 0; }
blend_range(){ local lo=999999 hi=0 r i b f l d k; while read -r r; do [ -z "$r" ] && continue; IFS='|' read -r i b f l d k <<<"$r"; if [ "$f" -lt "$lo" ]; then lo=$f; fi; if [ "$l" -gt "$hi" ]; then hi=$l; fi; done < <(blend_rows "$1"); echo "$lo $hi"; }
fsize(){ stat -f%z "$1" 2>/dev/null || stat -c%s "$1"; }
