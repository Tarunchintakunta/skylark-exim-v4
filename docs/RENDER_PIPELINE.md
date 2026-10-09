# RENDER_PIPELINE.md

## 1. Tools on Tarun's Mac
Blender (4.2 LTS or newer; scripts handle EEVEE Next and 5.x EEVEE) at `/Applications/Blender.app` (override `BLENDER=`), the Blender MCP connector (for building scenes interactively), ffmpeg/ffprobe (`brew install ffmpeg`), Node 20+, `npx @gltf-transform/cli@4`, Ghostscript (`brew install ghostscript`) for the PDF, Playwright browsers. Check each at the start and log versions in NIGHT_LOG.md. MPFB2 add-on for people (install from the Blender extensions platform, free).

## 2. Settings (blender/render_settings.py)
EEVEE · 1920×1080 · 24 fps · 64 samples · motion blur 0.5 · ray tracing half-res · AgX with look by kind (ext Medium High Contrast, int/cold Base Contrast, dawn Medium Low Contrast) · PNG 8-bit · output `assets-src/render/<blend>/####.png` · overwrite off (resume-safe) · compositor off (no overlays). Frame ranges come from `scripts/scenes.sh`.

## 3. The loop per scene
1. Build in Blender via MCP using linked library assets (ASSET_LIBRARY). Save `assets-src/blender/<blend>.blend`. Apply `render_settings.py`.
2. Bridges: in the earlier scene, `write_boundary(A, B, frame=last, objects=[...])`; in the later scene `read_boundary(A, B, frame=1)` (`blender/boundary_camera.py`).
3. `python blender/scene_audit.py` inside Blender (MCP) → fix every flag (flat materials, intersections, floating objects, polycount).
4. Preview in the background: `scripts/render-scene.sh <blend> preview > logs/<blend>-preview.log 2>&1 &` → `docs/renders/<blend>-preview.mp4` + `<blend>-sheet.jpg`.
5. Self-review (QUALITY_GATES procedure) → `docs/reviews/<blend>-rN.md`. Iterate ≤ 4 rounds.
6. Self-approved → queue the full render (one full render at a time; Blender uses all cores): `scripts/render-scene.sh <blend> full > logs/<blend>-full.log 2>&1 &`. Resume-safe if interrupted.
7. While it renders, build the next scene in Blender (MCP work is light enough to run alongside, but do not start a second headless render).
8. When frames are complete: `scripts/frames-to-master.sh <ids>` → `scripts/encode-clips.sh <ids>` → `scripts/make-posters.sh <ids>` → `scripts/check-clip.sh <ids>` → `scripts/boundary-check.sh`.
9. Commit the encoded tiers + posters on the scene's PR branch (`public/media/`), plus preview/sheet/review files in `docs/renders`, `docs/reviews`.

## 4. Never-a-placeholder rule
Order of what each chapter shows, best available first: full render → **preview-grade** master (`scripts/preview-to-master.sh <id>`, upscaled 960×540 preview, flagged in PR + NIGHT_LOG) → (only before a scene's first preview exists) a Blender still render of the scene's key frame with slow transform zoom. Never a grey box, text tag or AI/stock image.

## 5. Time plan (estimate, log real numbers)
- Previews: 2,712 frames × ~1–2 s ≈ 45–90 min total across all scenes.
- Full renders: 2,712 frames × ~6–12 s ≈ 4.5–9 h. Overnight you will NOT finish everything at full quality if modelling also takes hours. Render in priority order: v-table, v-port, v-reefer, v-sea, v-pond, v-truck, v-cold/v-pack/v-freeze, v-qc/v-grade/v-peel/v-wash. If the measured full-frame time × remaining frames exceeds the time left before 07:00 IST, drop full samples to 32 and/or render at 1600×900 (the encode scales to tiers anyway) and say so in the report.
- Keep the Mac awake: `caffeinate` is built into render-scene.sh; also run `caffeinate -dims &` at the start of the night.

## 6. Products
`scripts/fetch-scans.sh` → `Blender -b --python blender/clean_scan.py -- assets-src/scans/<f>.glb assets-src/models/<name>-src.glb` → hand fixes in Blender (fins, blotches) → export `assets-src/models/<name>.glb` → `scripts/optimize-glb.sh <name>` → G-PROD gates with turntable stills.

## 7. Stills
`scripts/render-still.sh markets-map` and `scripts/render-still.sh og-image`.
